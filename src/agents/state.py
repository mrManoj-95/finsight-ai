from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    question: str
    ticker: Optional[str]
    sub_tasks: List[str]
    retrieved_chunks: List[dict]
    extracted_facts: List[dict]   # numbers pulled from tables, with source
    draft_answer: str
    verified: bool
    verification_notes: str
    final_answer: str
    citations: List[dict]
    retry_count: int              # caps the synthesize<->verify loop