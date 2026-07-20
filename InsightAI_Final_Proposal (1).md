# InsightAI — Enterprise Business Analyst Copilot
### Agentic RAG + SQL Agent + Web Search + Source-Conflict Reconciliation + Confidence-Scored, Critiqued Recommendations

**Prepared by:** Sukhman Arora
**Duration:** 3 weeks + 3-day buffer
**Effort:** ~5-6 hours/day

---

## 1. Executive Summary

InsightAI is an AI-powered Business Analyst Copilot that answers complex business questions by combining three sources — company documents (PDFs/reports/SOPs), sales/customer databases (SQL), and live web information (market trends, competitor news) — and reasoning across them instead of answering from one source at a time.

Four features differentiate it from standard multi-source RAG demos:

1. **Source-Conflict Reconciler** — when documents, SQL data, and web sources point to different explanations for the same business question, the system explicitly surfaces the disagreement and reasons about how the causes compound, instead of silently blending them into one paragraph
2. **Confidence-Scored Recommendations** — every recommendation is tagged HIGH/MEDIUM/LOW confidence based on how many independent sources support it and how directly the evidence ties to the claim
3. **Recommendation Critique Step** — before the report is finalized, a critique pass checks each recommendation for missing risks, downsides, or stale evidence
4. **AI Decision Simulator ("What-If" Scenario Analysis)** — after receiving recommendations, the user can ask hypothetical questions ("what if we increase marketing by 15%?") and get back a structured, evidence-grounded, explicitly qualitative analysis: expected benefits, possible risks, stated assumptions, and a confidence level — reusing the Business Reasoning Agent, Confidence Scorer, and Critique Agent rather than adding a new subsystem

---

## 2. Problem Statement

Business analysts spend hours switching between SQL dashboards, internal documents, and market research to answer questions like "why did sales drop" or "which region has the highest churn." Existing AI tools typically pull from a single source and present findings with uniform confidence, regardless of whether they're backed by hard data or a single speculative article — and when sources actually disagree, most tools blend them into a falsely coherent narrative rather than surfacing the conflict.

**Core question this project answers:** Can a multi-source business AI system reason honestly about disagreement between sources and calibrate its own confidence — rather than presenting a single, artificially smooth answer?

---

## 3. Example Interactions

- *"Why did laptop sales drop in Q2?"* → SQL shows conversion rate fell 8%, the Q2 report cites a launch delay, web search shows a competitor price cut in the same window → system explains these aren't mutually exclusive and reasons about how they compound
- *"Generate an executive report for the CEO"* → full report with confidence-tagged recommendations and critique notes on each
- *"Which region has the highest churn and why?"* → SQL analysis + document context + confidence-scored root causes
- *"What if we increase marketing spend by 15%?"* → structured scenario analysis: expected benefits, possible risks, stated assumptions, confidence level — grounded in historical SQL trends and market context, explicitly labeled qualitative/directional, not a statistical forecast

---

## 4. System Architecture

```
User Query
      │
      ▼
LangGraph Router
      │
 ┌────┼───────────────┐
 ▼    ▼               ▼
Document RAG      SQL Agent     Web Search
 │                  │              │
 └──────────┬───────┴──────────────┘
            ▼
 Information Fusion Agent
 + Source-Conflict Reconciler (NEW)
   → detects disagreement between doc/SQL/web
   → explains how differing causes compound
   → does NOT silently blend conflicting signals
            ▼
 Business Reasoning Agent
            ▼
 Report Generation Agent
            ▼
 Confidence Scorer (NEW)
   → tags each recommendation HIGH/MEDIUM/LOW
     based on source count + evidence directness
            ▼
 Recommendation Critique Agent (NEW)
   → checks each recommendation for missing
     risks, downsides, or stale evidence
   → flags or revises before finalizing
            ▼
 Guardrails & Citation Check
            ▼
 Streamlit Dashboard
 + trace panel (which sources used per answer)
 + conflict flags + confidence tags + critique notes
 + Scenario Analysis panel (What-If queries)
```

**AI Decision Simulator flow (branches off the same core agents, no new subsystem):**
```
"What if we increase marketing by 15%?"
        │
        ▼
Router detects: hypothetical/scenario query
        │
        ▼
Retrieve grounding evidence (same RAG+SQL+Web sources —
e.g., historical marketing spend vs sales correlation from SQL,
industry benchmarks from web, budget constraints from docs)
        │
        ▼
Business Reasoning Agent (new prompt mode) reasons through:
Expected Benefits / Possible Risks / Stated Assumptions / Confidence
        │
        ▼
Confidence Scorer (existing) — higher confidence if grounded in
real historical SQL correlation, lower if no precedent exists
        │
        ▼
Critique Agent (existing) — checks assumptions are reasonable,
flags any false certainty
        │
        ▼
Dashboard: Scenario Analysis panel, explicitly labeled
"qualitative/directional — not a statistical forecast"
```

---

## 5. Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| Backend | FastAPI |
| UI | Streamlit |
| Vector Database | Qdrant |
| Document Parsing | PyMuPDF |
| SQL | SQLite/PostgreSQL |
| Web Search | Tavily or SerpAPI |
| LLM | OpenRouter |
| Cache | Redis |
| Evaluation | RAGAS |

---

## 6. Core Features

**Document Intelligence** — search/summarize reports, policies, retrieve relevant sections
**SQL Business Agent** — natural language → SQL, execute, explain results
**Market Research Agent** — competitor news, market trend summaries with references
**Multi-Source Reasoning + Conflict Reconciliation** — combines and honestly reconciles internal docs, database, and web research
**Executive Report Generator** — Executive Summary, Key Findings, Risks, Opportunities, Recommendations (confidence-tagged, critiqued), References

---

## 7. Evaluation

Measured across baseline vs full pipeline:
- Answer Faithfulness (RAGAS)
- Context Precision / Recall
- SQL Accuracy
- Source Coverage
- Hallucination Rate
- Latency
- **Conflict Detection Rate (NEW)** — % of test queries with genuinely conflicting sources that the system correctly flags rather than silently blends
- **Confidence Calibration (NEW)** — spot-check whether HIGH-confidence recommendations actually hold up against ground truth more often than LOW-confidence ones

---

## 8. 3-Week Build Plan

**Week 1 — Foundations: Document RAG + SQL Agent**
- Day 1-2: Repo/env setup, synthetic business dataset (sales DB, sample reports/SOPs as PDFs), Qdrant + hybrid search setup
- Day 3-4: Document RAG chain (retrieval + reranking)
- Day 5-6: SQL Agent (NL→SQL, execution, explanation)
- Day 7: Test both independently on sample business questions

**Week 2 — Router, Web Search, Fusion + Conflict Reconciler**
- Day 1: LangGraph router — decides which source(s) a query needs
- Day 2-3: Web search integration (Tavily/SerpAPI) + Market Research Agent
- Day 4-5: Information Fusion Agent + **Source-Conflict Reconciler** (detect disagreement across the 3 sources, explain compounding causes)
- Day 6-7: Business Reasoning Agent, end-to-end integration test

**Week 3 — Report Generation, Confidence Scoring, Critique, Decision Simulator, Polish**
- Day 1-2: Executive Report Generator
- Day 3: **Confidence Scorer** (HIGH/MEDIUM/LOW tagging per recommendation)
- Day 4: **Recommendation Critique Agent** (risk/downside/staleness check)
- Day 5: **AI Decision Simulator** — scenario-query detection in router, new reasoning prompt mode (Benefits/Risks/Assumptions/Confidence), wired to existing Confidence Scorer + Critique Agent
- Day 6: Streamlit dashboard (Executive Summary cards, Source Breakdown, SQL charts, Recommendation cards, Scenario Analysis panel, trace panel), Redis caching
- Day 7: RAGAS evaluation run + conflict-detection/confidence-calibration checks, design rationale write-up, demo rehearsal

**Buffer: 3 days** — reserved for SQL agent edge cases or fusion agent debugging, the two highest-risk components.

---

## 9. Ratings

| Factor | Rating (/10) |
|---|---|
| Overall | 9.2 |
| Difficulty | 8.9 |
| Feasibility (3 weeks, 5-6 hrs/day) | 8.2 |
| Industry Relevance | 9 |
| Resume Strength | 9.2 |
| Uniqueness | 9.0 |
| Demo Appeal | 8.8 |

---

## 10. Resume Bullet

"Built an enterprise-grade AI Business Analyst Copilot (LangGraph, Hybrid RAG, SQL Agent, web search) with a source-conflict reconciliation layer, a confidence-scored and self-critiqued recommendation engine, and an AI Decision Simulator for evidence-grounded what-if scenario analysis — generating citation-backed executive reports across documents, databases, and live market research."

## 11. Talking Points
**Why these four features:** Most multi-source AI tools optimize for producing one smooth-sounding answer. The real failure mode in business analytics tools is false confidence — blending disagreeing sources into a clean narrative, stating every recommendation with the same certainty regardless of evidence strength, and only ever answering what's explicitly asked. These four features directly target that: surfacing conflict instead of hiding it, scoring confidence instead of assuming it, critiquing recommendations before they reach a decision-maker, and letting decision-makers explore hypotheticals with transparent, evidence-grounded (not falsely precise) reasoning.

**On the Decision Simulator specifically:** It's explicitly qualitative/directional reasoning, not statistical forecasting — the UI labels it as such. This is a deliberate scope choice: it avoids the "fake precision" trap of dressing up LLM speculation as a real predictive model, while still giving decision-makers a structured way to think through hypotheticals with stated assumptions and grounded confidence.
