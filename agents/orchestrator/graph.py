"""
InsightAI - LangGraph orchestrator wiring together Document RAG, SQL, and
Web Search agents behind an LLM-based router.

Note: the Document RAG agent (Week 1) isn't a plain f(state) node - it needs
bm25/provider/client injected via closure, so it's compiled as its own
sub-graph and invoked as a unit rather than added as a bare node function.
"""

from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from agents.orchestrator.router import route_question, VALID_AGENTS
from agents.sql_agent.node import sql_agent_node   
from agents.web_agent.node import web_agent_node 

from ingestion.rag_agent import build_document_rag_graph
from agents.orchestrator.synthesizer import synthesize_final_answer
from agents.orchestrator.confidence import compute_confidence
from agents.orchestrator.critique import critique_answer
from core.text_utils import ensure_prose

class OrchestratorState(TypedDict):
    query: str
    agents_needed: list[str]
    rag_result: Optional[dict]
    sql_result: Optional[dict]
    web_result: Optional[dict]
    final_answer: Optional[str]   
    conflict_detected: Optional[bool]     
    conflict_summary: Optional[str] 
    confidence:Optional[dict]
    critique:Optional[dict]

def router_node(state: OrchestratorState) -> OrchestratorState:
    agents_needed = route_question(state["query"])
    print(f"[orchestrator] Routing to: {agents_needed}")
    return {"agents_needed": agents_needed}


def route_decision(state: OrchestratorState) -> list[str]:
    mapping = {"document_rag": "rag_agent", "sql": "sql_agent", "web": "web_agent"}
     
    agents_needed = state.get("agents_needed", [])

    node_names = [mapping[a] for a in agents_needed if a in mapping]
    if not node_names:
        return ["out_of_scope"]   
    return node_names 


def out_of_scope_node(state: OrchestratorState) -> OrchestratorState:
    return {
        "final_answer": (
            "I'm InsightAI, a business analyst assistant scoped to Northwind Traders' sales data, "
            "internal reports, and directly relevant market context. That question is outside what "
            "I'm able to help with here."
        ),
        "conflict_detected": False,
        "conflict_summary": None,
        "confidence": {"score": 1.0, "label": "High", "reasons": ["Correctly declined — out of scope"]},
        "critique": {"has_issues": False, "severity": "none", "findings": [], "verdict": "N/A — out of scope"},
    }
def confidence_and_critique_node(state: OrchestratorState) -> OrchestratorState:
    confidence = compute_confidence(
        state.get("conflict_detected", False),
        state.get("rag_result"), state.get("sql_result"), state.get("web_result"),
    )
    critique = critique_answer(
        state["query"], state["final_answer"],
        state.get("rag_result"), state.get("sql_result"), state.get("web_result"),
    )
    return {"confidence": confidence, "critique": critique}

def synthesis_node(state: OrchestratorState) -> OrchestratorState:
    result = synthesize_final_answer(
        state["query"],
        state.get("rag_result"),
        state.get("sql_result"),
        state.get("web_result"),
    )

    result["answer"] = ensure_prose(result["answer"], state["query"]) 
    return {
        "final_answer": result["answer"],
        "conflict_detected": result["conflict_detected"],
        "conflict_summary": result["conflict_summary"],
    }



def build_orchestrator_graph(bm25,provider, qdrant_client):

    rag_subgraph = build_document_rag_graph(bm25, provider, qdrant_client)

    def rag_agent_node(state: OrchestratorState) -> OrchestratorState:
        rag_output = rag_subgraph.invoke({"query": state["query"], "retrieved_chunks": [], "answer": ""})
        return {"rag_result": rag_output} 


    graph = StateGraph(OrchestratorState)
    graph.add_node("router", router_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("sql_agent", sql_agent_node)
    graph.add_node("web_agent", web_agent_node)
    graph.add_node("out_of_scope", out_of_scope_node)
    graph.add_node("merge", merge_node)
    graph.add_node("synthesize", synthesis_node) 
    graph.add_node("confidence_critique",confidence_and_critique_node)
    

    graph.set_entry_point("router")
    
    graph.add_conditional_edges(
        "router", route_decision,
        {"rag_agent": "rag_agent", "sql_agent": "sql_agent", "web_agent": "web_agent",
         "out_of_scope": "out_of_scope"},
    )

    graph.add_edge("rag_agent", "merge")
    graph.add_edge("sql_agent", "merge")
    graph.add_edge("web_agent", "merge")
    graph.add_edge("out_of_scope", END)    
    graph.add_edge("merge", "synthesize")             
    graph.add_edge("synthesize","confidence_critique")
    graph.add_edge("confidence_critique", END)  
         

    return graph.compile()

def merge_node(state: OrchestratorState) -> OrchestratorState:
    return {}  