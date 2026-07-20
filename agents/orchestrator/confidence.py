"""
InsightAI - Rule-based confidence scoring.

Deliberately NOT an LLM call - asking a model to self-assess confidence is
unreliable (we saw the Web synthesizer add ungrounded "this is consistent
across sources" commentary on its own in Week 2 Day 3, exactly the kind of
uncalibrated self-confidence talk we want to avoid). Instead, confidence is
computed from objective signals already present in the orchestrator state -
same inputs always produce the same score, and every score is explainable.
"""

def compute_confidence(
    conflict_detected: bool,
    rag_result: dict | None,
    sql_result: dict | None,
    web_result: dict | None,
) -> dict:
    """
    Returns: {"score": float (0-1), "label": str, "reasons": list[str]}
    """
    score = 1.0
    reasons = []

    sources_used = sum(1 for r in (rag_result, sql_result, web_result) if r is not None)

    # --- Conflict is the strongest negative signal ---
    if conflict_detected:
        score -= 0.45
        reasons.append("Sources disagreed on at least one fact")

    # --- Single-source answers are inherently less corroborated ---
    if sources_used == 1:
        score -= 0.15
        reasons.append("Only one source was consulted (no cross-corroboration)")
    elif sources_used >= 2 and not conflict_detected:
        reasons.append(f"{sources_used} sources were consulted and agreed")

    # --- SQL-specific signals ---
    if sql_result:
        if sql_result.get("error"):
            score -= 0.35
            reasons.append("SQL query failed after all retry attempts")
        elif sql_result.get("row_count", 0) == 0:
            score -= 0.25
            reasons.append("SQL query ran successfully but found no matching data")
        elif sql_result.get("attempts", 1) > 1:
            score -= 0.10
            reasons.append("SQL query required a retry before succeeding")

    # --- Web-specific signals ---
    if web_result:
        if web_result.get("error"):
            score -= 0.35
            reasons.append("Web search failed")
        elif len(web_result.get("sources", [])) == 0:
            score -= 0.25
            reasons.append("Web search returned no usable sources")

    # --- RAG-specific signals: weak retrieval match ---
    if rag_result:
        chunks = rag_result.get("retrieved_chunks", [])
        if not chunks:
            score -= 0.25
            reasons.append("No relevant internal documents were found")
        else:
            top_score = chunks[0].get("score", 0)
            # Reranker scores are model-specific; this threshold is a starting
            # point calibrated loosely against observed Week 1 test scores -
            # revisit if the reranker model changes.
            if top_score < 0.3:
                score -= 0.15
                reasons.append("Best-matching internal document chunk was a weak match")

    # --- Nothing found anywhere ---
    if sources_used == 0:
        score = 0.0
        reasons = ["No agents were invoked or all returned nothing (out-of-scope or total failure)"]

    score = max(0.0, min(1.0, score))

    if score >= 0.75:
        label = "High"
    elif score >= 0.45:
        label = "Medium"
    else:
        label = "Low"

    return {"score": round(score, 2), "label": label, "reasons": reasons}