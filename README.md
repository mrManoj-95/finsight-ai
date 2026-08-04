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

## 📂 Data Sources & Ingestion Infrastructure

FinSight AI combines official regulatory filings with real-time market data APIs to provide grounding and lineage across both qualitative MD&A discussions and numeric financial statements:

| Source | Provider / Protocol | Purpose & Extracted Assets | Ingestion Method |
| :--- | :--- | :--- | :--- |
| **SEC EDGAR API** | U.S. Securities and Exchange Commission | • Official 10-K (Annual) & 10-Q (Quarterly) Filings<br>• Item 1A Risk Factors & Item 7 MD&A Narrative<br>• Income Statements, Balance Sheets & Cash Flow Tables | REST API via `sec-edgar-downloader` with automated User-Agent header rate-limiting compliance. |
| **Financial Modeling Prep (FMP)** | Financial Modeling Prep API | • Real-time Ticker Metrics & Key Ratios (P/E, EV/EBITDA)<br>• Earnings Call Transcripts & Management Q&A<br>• Consensus Guidance vs. Historical Actuals | REST Endpoints parsed into structured JSON payloads for Table QA tools. |

### Data Parsing & Lineage Pipeline
1. **Document Extraction:** HTML/XML filings downloaded from EDGAR are stripped of non-semantic tags while preserving tabular HTML nodes.
2. **Section Splitting:** Filings are split into standard item sections (e.g., `Item 1A`, `Item 7`) using custom regex parsers.
3. **Structured Table Isolation:** Financial tables are converted to Markdown/JSON formats to preserve cell coordinates (Row/Column indices) for exact-match verification during auditing passes.