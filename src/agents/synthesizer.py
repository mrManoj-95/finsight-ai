from agents.state import AgentState
from agents.llm_clients import get_kimi_llm

llm = get_kimi_llm()

SYNTH_PROMPT = """Answer the question using ONLY the provided context. Every numeric
claim MUST be traceable to either the retrieved filing excerpts or the financial facts
table. Cite sources inline as [doc_id:item] for text or [metric:fiscal_period] for numbers.
If you cannot support a claim with the given context, say so explicitly — do not guess.

Question: {question}

Filing excerpts:
{chunks}

Financial facts (verified numeric data):
{facts}

Write a concise, cited answer:"""

def synthesize_node(state: AgentState) -> AgentState:
    chunks_str = "\n---\n".join(
        f"[{c['doc_id']}:{c['item']}] {c['text'][:800]}" for c in state["retrieved_chunks"]
    )
    facts_str = "\n".join(
        f"[{f['metric']}:{f.get('fiscal_period')}] = {f['value']} (source: {f['source_doc_id']})"
        for f in state["extracted_facts"]
    )
    resp = llm.invoke(SYNTH_PROMPT.format(question=state["question"], chunks=chunks_str, facts=facts_str))
    state["draft_answer"] = resp.content
    return state