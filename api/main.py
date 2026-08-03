"""
InsightAI - FastAPI backend.
Wraps the existing orchestrator/agent logic (unchanged) as REST endpoints
for the custom dashboard frontend. All ingestion happens once at startup,
mirroring the @st.cache_resource pattern from the Streamlit version.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingestion.parser import parse_directory
from ingestion.chunker import chunk_document
from ingestion.vector_store import get_client, ensure_collection, upsert_chunks
from ingestion.sparse import BM25Index
from ingestion.embeddings import get_provider
from agents.orchestrator.graph import build_orchestrator_graph
from agents.agentic.agent import build_agent_tools
from agents.agentic.graph_loop import run_agentic_query_v2
from agents.orchestrator.confidence import compute_confidence
from agents.orchestrator.critique import critique_answer
from agents.orchestrator.synthesizer import detect_conflict
from agents.simulator.decision_simulator import run_decision_simulator
from agents.sql_agent.executor import execute_sql
from agents.sql_agent.validator import validate_sql

resources = {}  # populated at startup, shared across requests


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[api] Ingesting documents and building indices...")

    docs = parse_directory("data/raw")
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunk_document(d, chunk_size=120, chunk_overlap=20))
    texts = [c.text for c in all_chunks]

    provider = get_provider()
    provider.fit_if_needed(texts)
    dense_vectors = provider.embed_texts(texts)

    bm25 = BM25Index()
    bm25.fit(texts)
    sparse_vectors = [bm25.encode(t) for t in texts]

    client = get_client()
    ensure_collection(client)
    upsert_chunks(client, all_chunks, dense_vectors, sparse_vectors)

    resources["workflow_app"] = build_orchestrator_graph(bm25, provider, client)
    resources["agent_tools"] = build_agent_tools(bm25, provider, client)
    resources["chunk_count"] = len(all_chunks)

    print(f"[api] Ready. Indexed {len(all_chunks)} chunks.")
    yield
    client.close()


app = FastAPI(title="InsightAI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your actual frontend domain once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/response models ---

class QueryRequest(BaseModel):
    question: str
    mode: str = "workflow"  # "workflow" or "agent"


class SimulateRequest(BaseModel):
    question: str


# --- Helper: normalize Agent mode output to match Workflow mode's shape ---

def extract_agent_results(tool_calls_made: list[dict]):
    rag_result = sql_result = web_result = None
    for call in tool_calls_made or []:
        if call["tool"] == "query_sales_database":
            sql_result = call["result"]
        elif call["tool"] == "search_web":
            web_result = call["result"]
        elif call["tool"] == "search_internal_documents":
            rag_result = call["result"]
    return rag_result, sql_result, web_result


# --- Endpoints ---

@app.get("/api/health")
def health():
    return {"status": "ok", "chunks_indexed": resources.get("chunk_count", 0)}


@app.post("/api/query")
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty")

    if req.mode == "workflow":
        result = resources["workflow_app"].invoke({
            "query": req.question, "agents_needed": [],
            "rag_result": None, "sql_result": None, "web_result": None,
            "final_answer": None, "conflict_detected": None, "conflict_summary": None,
            "confidence": None, "critique": None,
        })
        return {
            "mode": "workflow",
            "answer": result.get("final_answer"),
            "agents_used": result.get("agents_needed", []),
            "conflict_detected": result.get("conflict_detected", False),
            "conflict_summary": result.get("conflict_summary"),
            "confidence": result.get("confidence"),
            "critique": result.get("critique"),
            "web_sources": (result.get("web_result") or {}).get("sources", []),
        }

    elif req.mode == "agent":
        agent_result = run_agentic_query_v2(req.question, resources["agent_tools"])
        answer = agent_result.get("answer")
        tool_calls_made = agent_result.get("tool_calls_made", [])
        iterations = agent_result.get("iterations", 0)

        if iterations == 0:
            confidence = {"score": 1.0, "label": "High", "reasons": ["Correctly declined — out of scope."]}
            critique = {"has_issues": False, "severity": "none", "findings": [], "verdict": "N/A — out of scope"}
            conflict = {"conflict_detected": False, "conflict_summary": None}
            web_result = None
        elif not tool_calls_made:
            confidence = {"score": 0.1, "label": "Low", "reasons": ["No tool was called despite the question being in-scope."]}
            critique = {"has_issues": True, "severity": "severe", "findings": ["No tool results back this answer."], "verdict": "Answer is ungrounded."}
            conflict = {"conflict_detected": False, "conflict_summary": None}
            web_result = None
        else:
            rag_result, sql_result, web_result = extract_agent_results(tool_calls_made)
            conflict = detect_conflict(rag_result, sql_result, web_result)
            confidence = compute_confidence(conflict["conflict_detected"], rag_result, sql_result, web_result)
            critique = critique_answer(req.question, answer, rag_result, sql_result, web_result)

        return {
            "mode": "agent",
            "answer": answer,
            "tool_trace": tool_calls_made,
            "iterations": iterations,
            "conflict_detected": conflict.get("conflict_detected", False),
            "conflict_summary": conflict.get("conflict_summary"),
            "confidence": confidence,
            "critique": critique,
            "web_sources": (web_result or {}).get("sources", []),
        }

    raise HTTPException(400, "mode must be 'workflow' or 'agent'")


@app.post("/api/simulate")
def simulate(req: SimulateRequest):
    result = run_decision_simulator(req.question)
    if result.get("error"):
        raise HTTPException(400, result["error"])
    return result


@app.get("/api/insights")
def insights():
    """Precomputed aggregates for the standing Insights dashboard page."""
    queries = {
        "revenue_by_category": '''SELECT C.CategoryName, SUM(OD.UnitPrice*OD.Quantity*(1-OD.Discount)) AS Revenue
                                    FROM "Order Details" OD JOIN Products P ON OD.ProductID=P.ProductID
                                    JOIN Categories C ON P.CategoryID=C.CategoryID
                                    GROUP BY C.CategoryName ORDER BY Revenue DESC''',
        "revenue_by_country": '''SELECT O.ShipCountry, SUM(OD.UnitPrice*OD.Quantity*(1-OD.Discount)) AS Revenue
                                   FROM "Order Details" OD JOIN Orders O ON OD.OrderID=O.OrderID
                                   GROUP BY O.ShipCountry ORDER BY Revenue DESC LIMIT 10''',
        "top_employees": '''SELECT E.FirstName || ' ' || E.LastName AS Name,
                                    SUM(OD.UnitPrice*OD.Quantity*(1-OD.Discount)) AS Revenue
                             FROM "Order Details" OD JOIN Orders O ON OD.OrderID=O.OrderID
                             JOIN Employees E ON O.EmployeeID=E.EmployeeID
                             GROUP BY E.EmployeeID ORDER BY Revenue DESC LIMIT 5''',
    }
    output = {}
    for key, sql in queries.items():
        validated = validate_sql(sql)
        result = execute_sql(validated)
        output[key] = result["rows"]
    return output