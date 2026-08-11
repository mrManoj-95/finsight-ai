import json
from retrieval.hybrid_search import hybrid_search
from agents.state import AgentState
from agents.llm_clients import get_gemini_llm

llm = get_gemini_llm()

EXPANSION_PROMPT = """Rewrite this financial research query into 2 alternate phrasings
that might match different wording in an SEC filing (e.g. synonyms for financial terms).
Respond with ONLY a JSON list of strings, no commentary: ["...", "..."]

Query: {query}"""

def expand_query(query: str) -> list:
    try:
        resp = llm.invoke(EXPANSION_PROMPT.format(query=query))
        raw = resp.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        variants = json.loads(raw)
        return [query] + variants[:2]
    except Exception:
        # Query expansion is an enhancement, not a dependency — fail open to the original query
        return [query]

def retrieve_node(state: AgentState) -> AgentState:
    all_chunks = []
    for task in state["sub_tasks"]:
        for variant in expand_query(task):
            results = hybrid_search(variant, ticker=state.get("ticker"), top_k=5)
            all_chunks.extend(results)
    # dedupe by chunk id
    seen = set()
    deduped = []
    for c in all_chunks:
        if c["id"] not in seen:
            seen.add(c["id"])
            deduped.append(c)
    state["retrieved_chunks"] = deduped
    return state