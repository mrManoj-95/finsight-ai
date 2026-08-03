# FinSight AI 📈🤖
> **Multi-Agent Financial Intelligence & SEC Filing RAG Platform with Numeric Verification Guardrails**

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20pgvector-blue)
![Orchestration](https://img.shields.io/badge/Agentic-LangGraph-orange)
![Observability](https://img.shields.io/badge/LLMOps-LangSmith-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📌 One-Line Pitch
**FinSight AI** is an enterprise-grade equity research and FP&A intelligence agent that ingests SEC filings (10-K/10-Q) and earnings call transcripts to deliver verifiable, citation-grounded financial analysis using **Hybrid RAG**, **LangGraph Multi-Agent Orchestration**, and **Numeric Fact-Checking Guardrails**.

---

## 🏗️ System Architecture

```text
[ Analyst Query ] ──► [ Planner Agent (DeepSeek-R1) ]
                               │
                               ▼ (Sub-task Plan)
                     [ LangGraph State Machine ]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 [ Hybrid RAG Retriever ]              [ Table QA Agent ]
 (pgvector + BM25 + Reranker)          (Structured Financials)
            │                                     │
            └──────────────────┬──────────────────┘
                               │ Context & Numeric Claims
                               ▼
                   [ Verifier Agent (Guardrail) ]
                   (Cross-checks claims vs source tables)
                               │
                     Is Numeric Match Valid?
                      ├── YES ──► [ Synthesizer Agent (Kimi / Gemini) ] ──► [ Final Audit Report ]
                      └── NO  ──► [ Loop back to Retriever ] (Cyclic Correction)