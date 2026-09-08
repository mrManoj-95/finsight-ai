# FinSight AI — Project Status

Working reference for where this repo actually stands. `FinSight_AI_Build_Guide.md`
is the tutorial/spec this was built from; this file tracks what's *done* vs
*in flight* vs *not started*, plus decisions that diverged from the guide.
Update this as phases move, don't let it drift into a second copy of the guide.

## What it is

Multi-agent RAG system over SEC filings (10-K/10-Q) + FMP fundamentals.
Planner → Retriever → Table-QA → Synthesizer → Verifier, on LangGraph, with a
hybrid (vector + Postgres FTS + reranker) retrieval layer and a numeric
fact-checking guardrail (Verifier runs on a different LLM provider than the
Synthesizer, deliberately, so it isn't grading its own homework).

## Phase status

| Phase | Guide scope | Status |
|---|---|---|
| 0 — Scaffolding | venv, pyproject `-e .`, docker pgvector, `.env` | ✅ committed (`47d2c6f`) |
| 1 — Ingestion | EDGAR client, section parser, chunker, run_ingest | ✅ committed (`0d199d4`) |
| 2 — Retrieval | pgvector schema, HF embeddings, hybrid BM25+vector+reranker | ✅ committed (`c8cc255`) |
| 2.3a — financial_facts loader | Links FMP data into `financial_facts` table | 🔶 in progress, uncommitted (`load_financial_facts.py`, `check_facts_linkage.py`) |
| 3 — Multi-agent graph | planner/retriever/table-qa/synthesizer/verifier on LangGraph | ✅ committed (`30bf90a`) |
| 3.5 — Multi-provider LLM routing | DeepSeek (plan+verify) / Gemini (retrieve+table-qa) / Kimi (synthesize) | ✅ done as part of Phase 3 |
| 4 — Eval harness | golden set, category-routed scoring, recall@k, query logging | 🔶 in progress — `src/eval/build_golden_set.py` + `data/eval/` exist, `run_eval.py`/`retrieval_eval.py`/`logger.py` not yet added |
| 5 — API + frontend + deploy | FastAPI, Streamlit, Dockerfile, hosting | ⬜ not started |

## Uncommitted changes right now

- `requirements.txt` — added `ragas==0.1.14`, `datasets==2.20.0` for Phase 4.
- `src/ingestion/market_data.py` — migrated FMP calls from the retired `v3`
  API to `stable` (`symbol=` query param instead of path segment), added
  `_check_fmp_error()` since FMP returns error bodies on HTTP 200.
  **Known gap vs. the guide:** the guide's finished version puts the FMP key
  in a request header (`HEADERS = {"apikey": ...}`) to keep it out of logged
  URLs; the current diff still passes `apikey` as a query param. Worth fixing
  before this gets treated as "done."
- `src/ingestion/load_financial_facts.py`, `src/ingestion/check_facts_linkage.py`
  (new, untracked) — Phase 2.3a's `financial_facts` populator. Only
  `get_income_statement` is used; `get_earnings_transcript`'s `stable`
  migration is unverified (per the guide's own caveat).
- `src/eval/`, `data/eval/` (new, untracked) — Phase 4 golden-set builder
  output/scaffolding.

## Key design decisions worth remembering

- **Lexical search runs natively in Postgres** (`tsvector` GENERATED column +
  GIN index), not an in-memory `rank_bm25` index — no cache to rebuild, every
  replica sees the same index, new chunks searchable immediately on insert.
- **Hybrid retrieval fuses via Reciprocal Rank Fusion** (vector + lexical run
  independently, not lexical-reranks-vector), `k=60`, then a cross-encoder
  reranks the fused top-30 down to `top_k`.
- **Financial tables never get flattened into prose chunks** — numbers live
  in `financial_facts` as exact values so the Verifier can check against a
  real source of truth instead of an LLM's re-derivation of a number.
- **Verifier fails closed**: unparseable verifier output → `verified=False`,
  never silently passed through.
- **Per-provider temperature is `.env`-configurable** via `_resolve_temperature()`
  — some reasoning-tuned model variants reject any temperature override except
  their own default (e.g. Kimi's `kimi-k3` wants `temperature=1`).
- Ticker universe for now: `AAPL`, `MSFT`, `NVDA` (`TICKERS` constant, repeated
  across `run_ingest.py` / `load_financial_facts.py` / `build_golden_set.py` —
  keep them in sync if this expands).

## Running things

```powershell
docker compose up -d                          # pgvector
python -m retrieval.db                        # create schema
python -m ingestion.run_ingest                # EDGAR → data/processed/chunks.jsonl
python -m retrieval.embed_and_load            # embed + insert into pgvector
python -m ingestion.load_financial_facts      # FMP → financial_facts table
python -m agents.run                          # ask a question end-to-end
pytest tests/ -v
```

## Not started yet (Phase 4 remainder + Phase 5)

- `src/eval/run_eval.py` (category-routed scoring), `retrieval_eval.py`
  (recall@k), `logger.py` (query_log table) — guide has these fully spec'd,
  none exist in `src/eval/` yet beyond `build_golden_set.py`.
- FastAPI backend, Streamlit frontend + eval dashboard, Dockerfile, deployment.
