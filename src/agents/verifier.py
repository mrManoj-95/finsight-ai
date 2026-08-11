import json
from agents.state import AgentState
from agents.llm_clients import get_deepseek_llm

llm = get_deepseek_llm()

VERIFY_PROMPT = """You are a strict fact-checker. Given a draft answer and the source
context it was built from, identify any numeric claim in the draft that is NOT directly
supported by the context (i.e., hallucinated or approximated without basis).

Draft answer:
{draft}

Source context (facts + excerpts):
{context}

Respond with ONLY valid JSON, no markdown fences, no commentary:
{{"verified": true/false, "unsupported_claims": ["..."], "notes": "..."}}"""

def verify_node(state: AgentState) -> AgentState:
    context = "\n".join(f"{f['metric']}:{f.get('fiscal_period')}={f['value']}" for f in state["extracted_facts"])
    context += "\n" + "\n".join(c["text"][:500] for c in state["retrieved_chunks"])

    resp = llm.invoke(VERIFY_PROMPT.format(draft=state["draft_answer"], context=context))
    raw = resp.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(raw)
        state["verified"] = result["verified"]
        state["verification_notes"] = result.get("notes", "")
    except json.JSONDecodeError:
        # Fail closed: if the verifier's own output is unparseable, don't silently mark verified
        state["verified"] = False
        state["verification_notes"] = "Verifier response was not valid JSON — treated as unverified."
    return state


def should_retry(state: AgentState) -> str:
    state["retry_count"] = state.get("retry_count", 0) + 1
    if state["verified"] or state["retry_count"] >= 2:
        return "finalize"
    return "synthesize"