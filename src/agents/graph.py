from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.planner import plan_node
from agents.retriever import retrieve_node
from agents.table_qa import extract_facts_node
from agents.synthesizer import synthesize_node
from agents.verifier import verify_node, should_retry

def finalize_node(state: AgentState) -> AgentState:
    state["final_answer"] = state["draft_answer"]
    if not state["verified"]:
        state["final_answer"] += f"\n\n⚠️ Verification notes: {state['verification_notes']}"
    return state

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("extract_facts", extract_facts_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("verify", verify_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "extract_facts")
    graph.add_edge("extract_facts", "synthesize")
    graph.add_edge("synthesize", "verify")
    graph.add_conditional_edges("verify", should_retry, {
        "synthesize": "synthesize",  # max 1 retry in practice — add a counter to avoid infinite loop
        "finalize": "finalize",
    })
    graph.add_edge("finalize", END)
    return graph.compile()