import json
from sqlalchemy import text
from retrieval.db import engine
from agents.state import AgentState
from agents.llm_clients import get_gemini_llm

llm = get_gemini_llm()

EXTRACT_PROMPT = """Extract any specific financial figures (numbers, percentages, dollar
amounts) mentioned in this filing excerpt, along with what each figure refers to.
Respond with ONLY a JSON list, no commentary:
[{{"metric": "...", "value": "...", "context": "..."}}]
If no figures are present, return [].

Excerpt: {excerpt}"""

def extract_facts_node(state: AgentState) -> AgentState:
    ticker = state.get("ticker")
    db_facts = []
    if ticker:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT metric, value, fiscal_period, source_doc_id FROM financial_facts WHERE ticker = :t ORDER BY fiscal_period DESC LIMIT 12"),
                {"t": ticker},
            ).mappings().all()
        db_facts = [dict(r) for r in rows]

    # Only run the LLM extraction pass over a couple of chunks to control cost —
    # this is a supplementary signal, not the primary source of truth.
    llm_facts = []
    for chunk in state.get("retrieved_chunks", [])[:3]:
        try:
            resp = llm.invoke(EXTRACT_PROMPT.format(excerpt=chunk["text"][:1500]))
            raw = resp.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            extracted = json.loads(raw)
            for e in extracted:
                e["source_doc_id"] = chunk["doc_id"]
                e["fiscal_period"] = None
            llm_facts.extend(extracted)
        except Exception:
            continue  # extraction is best-effort; never let it break the pipeline

    state["extracted_facts"] = db_facts + llm_facts
    return state