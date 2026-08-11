import json
from agents.state import AgentState
from agents.llm_clients import get_deepseek_llm

llm = get_deepseek_llm()

PLANNER_PROMPT = """You are a financial research planner. Break the user's question
into 1-3 concrete retrieval sub-tasks (specific enough to search a 10-K/10-Q index).
Also extract the ticker symbol if mentioned.
Respond with ONLY valid JSON, no markdown fences, no commentary:
{{"ticker": "...", "sub_tasks": ["...", "..."]}}

Question: {question}"""

def plan_node(state: AgentState) -> AgentState:
    resp = llm.invoke(PLANNER_PROMPT.format(question=state["question"]))
    raw = resp.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: treat the whole question as a single sub-task rather than crash the graph
        parsed = {"ticker": None, "sub_tasks": [state["question"]]}
    state["ticker"] = parsed.get("ticker")
    state["sub_tasks"] = parsed.get("sub_tasks", [state["question"]])
    return state