from agents.graph import build_graph

app = build_graph()

def ask(question: str):
    result = app.invoke({
        "question": question, "ticker": None, "sub_tasks": [],
        "retrieved_chunks": [], "extracted_facts": [], "draft_answer": "",
        "verified": False, "verification_notes": "", "final_answer": "", "citations": [],
        "retry_count": 0,
    })
    return result["final_answer"]

if __name__ == "__main__":
    print(ask("How did AAPL's gross margin trend over the last 4 quarters and what did management attribute it to?"))