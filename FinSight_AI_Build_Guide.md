# FinSight AI — Phased Build Guide (VS Code + Git)

This guide walks you through building FinSight AI in 6 phases. Each phase ends with a working, demoable increment and a git commit/push. Total timeline: 10-12 weeks part-time.

---

## Phase 0: Project Setup & Environment (Day 1)

### 0.1 Create project structure

**PowerShell:**
```powershell
mkdir finsight-ai
cd finsight-ai
git init

# Create nested folders (PowerShell has no brace expansion, so list them explicitly)
$folders = "src\ingestion","src\retrieval","src\agents","src\eval","src\api",`
           "tests","data\raw","data\processed","notebooks","docs"
foreach ($f in $folders) { New-Item -ItemType Directory -Force -Path $f | Out-Null }

# Create empty files (touch equivalent)
New-Item -ItemType File -Force -Path README.md, .gitignore, requirements.txt, .env.example | Out-Null
```

> Tip: if you'd rather avoid PowerShell quirks for scaffolding, install **Git Bash** (bundled with Git for Windows) and run bash commands there just for setup steps, then switch back to the VS Code PowerShell terminal for everything else. Either works — this guide gives native PowerShell so you don't have to switch.

### 0.2 `.gitignore`

```
__pycache__/
*.pyc
.env
venv/
.venv/
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep
.DS_Store
*.log
.vscode/settings.json
```

**PowerShell:**
```powershell
New-Item -ItemType File -Force -Path data\raw\.gitkeep, data\processed\.gitkeep | Out-Null
```

### 0.3 Python environment

**PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> If you get an error like *"running scripts is disabled on this system,"* PowerShell's execution policy is blocking the activation script. Fix it once (per user, no admin needed) with:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> Then re-run `.\venv\Scripts\Activate.ps1`. You'll know it worked when your prompt shows `(venv)` at the start.

`requirements.txt` (Phase 0 baseline — you'll add more per phase):

```
requests==2.32.3
python-dotenv==1.0.1
pydantic==2.8.2
sqlalchemy==2.0.32
psycopg2-binary==2.9.9
pgvector==0.3.2
```

```powershell
pip install -r requirements.txt
```

### 0.3a Make `src/` importable everywhere (`pyproject.toml`)

Every module in this project imports its siblings with a bare path — `from retrieval.hybrid_search import hybrid_search`, `from agents.llm_clients import get_deepseek_llm`, and so on, with no `src.` prefix. For those imports to resolve, `src/` itself needs to be on Python's import path, from **any** working directory and **any** entry point (a script you run directly, pytest, uvicorn, all of it) — not just whichever folder happens to be your current directory when you type a command.

The correct fix is to make the project pip-installable in editable mode, using the standard Python "src layout" pattern:

`pyproject.toml` (project root):
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "finsight-ai"
version = "0.1.0"
requires-python = ">=3.11"

[tool.setuptools.packages.find]
where = ["src"]
```

Install it once (with your venv active):
```powershell
pip install -e .
```

`-e` means *editable* — this doesn't copy your code anywhere; it registers `src/`'s contents on the Python path via a link, so any change you make to a `.py` file under `src/` is picked up immediately, with no reinstall needed. After this, `ingestion`, `retrieval`, `agents`, `eval`, and `api` are all importable as top-level packages, from anywhere: a script run directly, `pytest`, `uvicorn`, all of it, consistently.

**This changes how you run everything for the rest of the guide** — every run command from here on drops the `src.` prefix:
```powershell
# Not this:  python -m src.ingestion.run_ingest
python -m ingestion.run_ingest
```
Any earlier command in this guide written as `python -m src.xxx.yyy` should be read as `python -m xxx.yyy` — the guide has been corrected throughout, but if you're referencing an old copy/paste, that's the rule to apply.

> **Why not just set `PYTHONPATH=src` instead?** That works too, but it's a per-shell environment variable you'd have to remember to set every time you open a new terminal, and tools like pytest/uvicorn don't always inherit it the way you'd expect. `pip install -e .` registers the path permanently for that venv, so it's set-once-and-forget rather than something you re-apply per session — the same reason real Python projects use this pattern instead of ad hoc `PYTHONPATH` juggling.

### 0.4 VS Code setup

Install extensions: **Python**, **Pylance**, **Docker**, **Even Better TOML**, **GitLens**.

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}\\venv\\Scripts\\python.exe",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```
> On Windows the venv's Python binary lives at `venv\Scripts\python.exe`, not `venv/bin/python` (that path is macOS/Linux only). If VS Code doesn't pick it up automatically, open the Command Palette (`Ctrl+Shift+P`) → **Python: Select Interpreter** → choose the one under `.\venv\Scripts\python.exe`.

### 0.5 Postgres + pgvector via Docker

`docker-compose.yml`:
```yaml
version: "3.9"
services:
  db:
    image: ankane/pgvector
    restart: always
    environment:
      POSTGRES_USER: finsight
      POSTGRES_PASSWORD: finsight
      POSTGRES_DB: finsight
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

```powershell
docker compose up -d
```

`.env.example`:
```
DATABASE_URL=postgresql://finsight:finsight@localhost:5432/finsight
SEC_EDGAR_USER_AGENT="YourName your.email@example.com"
FMP_API_KEY=your_financial_modeling_prep_key
HF_TOKEN=your_huggingface_token
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=finsight-ai

# --- Multi-provider LLM routing (see Phase 3.5) ---
# DeepSeek — Planner + Verifier agents
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_TEMPERATURE=0

# Gemini — Retriever query-expansion + Table QA reasoning
GEMINI_API_KEY=your_gemini_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0

# Kimi (Moonshot AI) — Synthesizer agent
MOONSHOT_API_KEY=your_moonshot_key
MOONSHOT_BASE_URL=https://api.moonshot.ai/v1
MOONSHOT_MODEL=kimi-k2.6
# Defaults to 1 in code if this is left unset — some Kimi model variants (esp.
# "thinking"/reasoning-tuned ones like kimi-k3) reject any temperature other than
# 1, per the API's own error message. If you're on a variant that accepts a
# different value, override it explicitly here.
MOONSHOT_TEMPERATURE=1
```

> **Model name churn warning:** these providers ship new model IDs frequently (e.g. DeepSeek retired `deepseek-chat`/`deepseek-reasoner` in favor of `deepseek-v4-flash`/`deepseek-v4-pro` in July 2026; Kimi has moved through K2.5 → K2.6 → K3 in the same window). Putting the model name in `.env` instead of hardcoding it in source means a provider-side rename never requires a code change — just update one line and restart. Check each provider's console/docs before you start Phase 3.5 in case names have shifted again.

Copy to `.env` and fill in real values (never commit `.env`):

```powershell
Copy-Item .env.example .env
```

### 0.6 README skeleton

Write a placeholder README with project name, one-line pitch, and an "Architecture" section you'll fill in later — recruiters skim READMEs first.

### ✅ Phase 0 commit

```powershell
git add .
git commit -m "Phase 0: project scaffolding, docker pgvector, env config"
```

Create a GitHub repo named `finsight-ai`, then:
```powershell
git remote add origin https://github.com/<you>/finsight-ai.git
git branch -M main
git push -u origin main
```

---

## Phase 1: Data Ingestion (Weeks 1-2)

**Goal:** Pull real SEC filings + earnings transcripts + market data into structured, chunked form ready for embedding.

### 1.1 Add dependencies

```
beautifulsoup4==4.12.3
lxml==5.2.2
pandas==2.2.2
sec-edgar-downloader==5.0.2
tiktoken==0.7.0
```

### 1.2 `src/ingestion/edgar_client.py`

```python
"""Pull 10-K / 10-Q filings from SEC EDGAR (free, no key required, but requires a User-Agent)."""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

HEADERS = {"User-Agent": os.getenv("SEC_EDGAR_USER_AGENT", "FinSightAI dev@example.com")}
EDGAR_BASE = "https://www.sec.gov"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


def get_cik_for_ticker(ticker: str) -> str:
    """Map a ticker to its 10-digit zero-padded CIK using SEC's ticker map."""
    resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS)
    resp.raise_for_status()
    for entry in resp.json().values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker {ticker} not found")


def get_recent_filings(cik: str, form_types=("10-K", "10-Q"), limit=4):
    resp = requests.get(SUBMISSIONS_URL.format(cik=cik), headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    recent = data["filings"]["recent"]
    filings = []
    for i, form in enumerate(recent["form"]):
        if form in form_types:
            filings.append({
                "accessionNumber": recent["accessionNumber"][i],
                "form": form,
                "filingDate": recent["filingDate"][i],
                "primaryDocument": recent["primaryDocument"][i],
            })
        if len(filings) >= limit:
            break
    return filings


def download_filing(cik: str, accession_number: str, primary_document: str, out_dir="data/raw"):
    acc_nodash = accession_number.replace("-", "")
    url = f"{EDGAR_BASE}/Archives/edgar/data/{int(cik)}/{acc_nodash}/{primary_document}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(out_dir) / f"{cik}_{accession_number}.htm"
    out_path.write_bytes(resp.content)
    return out_path
```

### 1.3 `src/ingestion/section_parser.py`

Parse 10-K HTML into labeled sections (Item 1A Risk Factors, Item 7 MD&A, financial statements) instead of flat text — this is what makes retrieval precise later.

```python
"""Split a 10-K/10-Q HTML document into labeled Items using regex on Item headers."""
import re
from bs4 import BeautifulSoup

ITEM_PATTERN = re.compile(r"item\s+(\d+[a-c]?)\.?\s*[-–—]?\s*", re.IGNORECASE)

def extract_text(html_path) -> str:
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def split_into_items(raw_text: str) -> dict:
    """Returns {item_number: text} e.g. {'1A': '...', '7': '...'}"""
    matches = list(ITEM_PATTERN.finditer(raw_text))
    sections = {}
    for i, m in enumerate(matches):
        item_num = m.group(1).upper()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        chunk = raw_text[start:end].strip()
        if len(chunk) > 200:  # filter noise/TOC entries
            sections.setdefault(item_num, "")
            sections[item_num] += "\n" + chunk
    return sections
```

### 1.4 `src/ingestion/market_data.py`

Pull fundamentals + price data via Financial Modeling Prep (free tier) for numeric ground truth used later by the verifier agent.

**Uses FMP's `stable` API, not the deprecated `v3` legacy tier.** FMP retired the `v3` endpoints for any account without a subscription predating August 31, 2025 — a new/free-tier key gets `{"Error Message": "Legacy Endpoint..."}` on every `v3` call, regardless of the key's validity or which auth method is used. The ticker moves from the URL path into a `symbol=` query parameter under `stable`; confirmed working against a real response before writing this version (see decision log D-027) rather than assumed from docs alone.

**Auth via header, not URL query parameter.** FMP's docs support both, but a URL query parameter puts the key in the request URL itself — which gets written into web server access logs, browser history, and proxy logs in a way a request header doesn't. Since this project already keeps every other credential in `.env` rather than hardcoded, keeping the key out of logged URLs too is the same reasoning applied consistently, not a new pattern.

**Fail loudly on FMP's error responses — they come back as HTTP 200, not a 4xx.** `resp.raise_for_status()` only catches HTTP-level failures; FMP returns `{"Error Message": "..."}` with a perfectly normal 200 status, so an invalid/rate-limited/deprecated-endpoint request would otherwise flow downstream silently as if it were valid data — exactly the kind of confusing, hard-to-trace symptom that's costlier to debug later than to fail clearly at the source.

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()
FMP_KEY = os.getenv("FMP_API_KEY")
BASE = "https://financialmodelingprep.com/stable"
HEADERS = {"apikey": FMP_KEY}


def _check_fmp_error(data):
    """FMP returns error bodies with a 200 status, so raise_for_status()
    never catches them. Check explicitly and fail loudly with a clear
    message rather than letting an error dict silently masquerade as data."""
    if isinstance(data, dict) and "Error Message" in data:
        raise RuntimeError(f"FMP API error: {data['Error Message']}")
    return data


def get_income_statement(ticker: str, period="quarter", limit=8):
    url = f"{BASE}/income-statement"
    resp = requests.get(url, params={"symbol": ticker, "period": period, "limit": limit}, headers=HEADERS)
    resp.raise_for_status()
    return _check_fmp_error(resp.json())


def get_earnings_transcript(ticker: str, year: int, quarter: int):
    url = f"{BASE}/earning-call-transcript"
    resp = requests.get(url, params={"symbol": ticker, "year": year, "quarter": quarter}, headers=HEADERS)
    resp.raise_for_status()
    return _check_fmp_error(resp.json())
```

> **Not yet independently verified:** `get_earnings_transcript`'s endpoint/params are updated to match the same `v3`→`stable` migration pattern confirmed for income statements, but — unlike income statement — no real response has been pulled from it yet in this build, since nothing currently calls it (`load_financial_facts.py` only uses income statements). Test it directly in Postman the same way before relying on it, rather than assuming the pattern transfers perfectly.

### 1.5 Chunking strategy — `src/ingestion/chunker.py`

Key design decision: **narrative text** gets token-based chunking with overlap; **financial tables** are kept intact as structured JSON rows (never flattened into prose), so Table QA and the verifier agent can do exact-match numeric checks later.

```python
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens=400, overlap=50):
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        start += max_tokens - overlap
    return chunks


def build_chunk_records(ticker, form, filing_date, item_num, text, doc_id):
    chunks = chunk_text(text)
    return [
        {
            "doc_id": doc_id,
            "ticker": ticker,
            "form": form,
            "filing_date": filing_date,
            "item": item_num,
            "chunk_index": i,
            "text": c,
        }
        for i, c in enumerate(chunks)
    ]
```

### 1.6 Ingestion pipeline script — `src/ingestion/run_ingest.py`

Ties it together: for a list of tickers, download filings → parse sections → chunk → save to `data/processed/chunks.jsonl` (Phase 2 will embed and load these into pgvector).

```python
import json
from pathlib import Path
from ingestion.edgar_client import get_cik_for_ticker, get_recent_filings, download_filing
from ingestion.section_parser import extract_text, split_into_items
from ingestion.chunker import build_chunk_records

TICKERS = ["AAPL", "MSFT", "NVDA"]  # start small, expand later

def run():
    out_path = Path("data/processed/chunks.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as out_f:
        for ticker in TICKERS:
            cik = get_cik_for_ticker(ticker)
            filings = get_recent_filings(cik, limit=2)
            for filing in filings:
                path = download_filing(cik, filing["accessionNumber"], filing["primaryDocument"])
                raw_text = extract_text(path)
                sections = split_into_items(raw_text)
                doc_id = f"{ticker}_{filing['accessionNumber']}"
                for item_num, text in sections.items():
                    records = build_chunk_records(
                        ticker, filing["form"], filing["filingDate"], item_num, text, doc_id
                    )
                    for r in records:
                        out_f.write(json.dumps(r) + "\n")
            print(f"Ingested {ticker}")

if __name__ == "__main__":
    run()
```

Run it:
```powershell
python -m ingestion.run_ingest
```

Verify (PowerShell has no `wc -l`, use `Measure-Object`):
```powershell
(Get-Content data\processed\chunks.jsonl | Measure-Object -Line).Lines
```
Should show hundreds of chunk records.

### ✅ Phase 1 commit

```powershell
git add .
git commit -m "Phase 1: SEC EDGAR + FMP ingestion pipeline, section-aware chunking"
git push
```

Update README with a "Data Sources" section documenting EDGAR + FMP usage.

---

## Phase 2: Retrieval Layer — Hybrid Search on pgvector (Weeks 3-4)

**Goal:** Embed chunks, store in Postgres/pgvector, and build hybrid (BM25 + vector) retrieval with reranking.

### 2.1 Add dependencies

```
sentence-transformers==3.0.1
```

> `rank-bm25` is deliberately **not** in this list — lexical search runs natively in Postgres (Section 2.4) rather than as a Python in-memory index, so there's no separate BM25 library dependency in production.

### 2.2 DB schema — `src/retrieval/db.py`

```python
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    form TEXT NOT NULL,
    filing_date DATE,
    item TEXT,
    chunk_index INT,
    text TEXT NOT NULL,
    embedding vector(768),
    text_search tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS chunks_ticker_idx ON chunks (ticker);

CREATE INDEX IF NOT EXISTS chunks_fts_idx ON chunks USING GIN (text_search);

CREATE TABLE IF NOT EXISTS financial_facts (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    fiscal_period TEXT NOT NULL,
    metric TEXT NOT NULL,
    value NUMERIC,
    source_doc_id TEXT,
    UNIQUE (ticker, fiscal_period, metric)
);
"""

def init_db():
    with engine.connect() as conn:
        for stmt in DDL.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
        conn.commit()

if __name__ == "__main__":
    init_db()
    print("DB initialized.")
```

```powershell
python -m retrieval.db
```

### 2.3 Embedding + load — `src/retrieval/embed_and_load.py`

Uses a Hugging Face sentence-transformers model (`BAAI/bge-base-en-v1.5`, 768-dim) — this is your Hugging Face **Sentence Similarity** task integration.

```python
import json
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from retrieval.db import engine

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

def load_chunks(path="data/processed/chunks.jsonl"):
    with open(path) as f:
        return [json.loads(line) for line in f]

def embed_and_insert(batch_size=32):
    records = load_chunks()
    texts = [r["text"] for r in records]
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)

    with engine.connect() as conn:
        for r, emb in zip(records, embeddings):
            conn.execute(
                text("""
                    INSERT INTO chunks (doc_id, ticker, form, filing_date, item, chunk_index, text, embedding)
                    VALUES (:doc_id, :ticker, :form, :filing_date, :item, :chunk_index, :text, :embedding)
                """),
                {
                    "doc_id": r["doc_id"], "ticker": r["ticker"], "form": r["form"],
                    "filing_date": r["filing_date"], "item": r["item"],
                    "chunk_index": r["chunk_index"], "text": r["text"],
                    "embedding": str(emb.tolist()),
                },
            )
        conn.commit()
    print(f"Inserted {len(records)} chunks.")

if __name__ == "__main__":
    embed_and_insert()
```

Run it:
```powershell
python -m retrieval.embed_and_load
```

### 2.3a Populate `financial_facts` — `src/ingestion/load_financial_facts.py`

**This step was missing from earlier phases — a real gap, not something to skip.** Phase 2.2 created the `financial_facts` table; Phase 1.4's `market_data.py` wrote functions to *fetch* structured data from FMP; nothing ever connected the two. Without this step, `financial_facts` stays empty, which silently degrades everything downstream that depends on it — the Table QA agent's `extract_facts_node` (Phase 3.6) has been returning zero structured facts on every run, the eval harness's `numeric_lookup`/`trend` scoring has nothing to check against, and `build_golden_set.py` (Phase 4.2a) has nothing to generate from. Run this **after** `embed_and_load.py`, since it needs `chunks` (specifically `filing_date`) to link each fact to the filing that actually reports it.

```python
"""
Populates financial_facts from FMP's structured income statement data.
Links each fact to the nearest ingested filing whose filing_date is on or
after the fiscal period's end date — that's the filing that would actually
report on this quarter. Facts with no matching ingested filing are skipped
rather than linked to the wrong doc_id.
"""
from ingestion.market_data import get_income_statement
from retrieval.db import engine
from sqlalchemy import text

TICKERS = ["AAPL", "MSFT", "NVDA"]  # match Phase 1's ingestion list


def fiscal_period_label(fiscal_year: str, period: str) -> str:
    """FMP's stable API gives an explicit 'fiscalYear' field, separate from
    the calendar year embedded in 'date' (the period-end date). Use
    fiscalYear directly rather than deriving the year from date[:4] — those
    two diverge right at fiscal-year boundaries (e.g. AAPL's Q1 FY2027
    period-end date falls in December 2026, but fiscalYear correctly reads
    "2027"); deriving from date[:4] would have silently mislabeled that
    quarter as "2026Q1" instead of "2027Q1"."""
    quarter = "Q4" if period.upper() == "FY" else period.upper()
    return f"{fiscal_year}{quarter}"


def nearest_filing_doc_id(conn, ticker: str, period_end: str):
    row = conn.execute(text("""
        SELECT doc_id FROM chunks
        WHERE ticker = :ticker AND filing_date >= :period_end
        ORDER BY filing_date ASC LIMIT 1
    """), {"ticker": ticker, "period_end": period_end}).first()
    return row[0] if row else None


def load_facts_for_ticker(ticker: str) -> int:
    statements = get_income_statement(ticker, period="quarter", limit=8)
    inserted = 0
    with engine.connect() as conn:
        for stmt in statements:
            period_label = fiscal_period_label(stmt["fiscalYear"], stmt.get("period", ""))
            doc_id = nearest_filing_doc_id(conn, ticker, stmt["date"])
            if doc_id is None:
                continue  # no ingested filing covers this period — skip, don't mislink

            metrics = {
                "revenue": stmt.get("revenue"),
                "grossProfit": stmt.get("grossProfit"),
                "netIncome": stmt.get("netIncome"),
                "operatingIncome": stmt.get("operatingIncome"),
            }
            if stmt.get("revenue") and stmt.get("grossProfit"):
                metrics["grossMarginRatio"] = round(stmt["grossProfit"] / stmt["revenue"] * 100, 2)

            for metric, value in metrics.items():
                if value is None:
                    continue
                conn.execute(text("""
                    INSERT INTO financial_facts (ticker, fiscal_period, metric, value, source_doc_id)
                    VALUES (:ticker, :period, :metric, :value, :doc_id)
                    ON CONFLICT (ticker, fiscal_period, metric)
                    DO UPDATE SET value = EXCLUDED.value, source_doc_id = EXCLUDED.source_doc_id
                """), {"ticker": ticker, "period": period_label, "metric": metric,
                       "value": value, "doc_id": doc_id})
                inserted += 1
        conn.commit()
    return inserted


def main():
    total = 0
    errors = []
    for ticker in TICKERS:
        try:
            n = load_facts_for_ticker(ticker)
            print(f"{ticker}: upserted {n} facts")
            total += n
        except RuntimeError as e:
            # A key/rate-limit/rotation issue on FMP's side shouldn't abort
            # the whole batch — report it clearly and keep going with the
            # other tickers, then surface a summary at the end.
            print(f"{ticker}: FAILED — {e}")
            errors.append((ticker, str(e)))
    print(f"Total: {total} facts in financial_facts")
    if errors:
        print(f"\n{len(errors)} ticker(s) failed and were skipped:")
        for ticker, msg in errors:
            print(f"  {ticker}: {msg}")


if __name__ == "__main__":
    main()
```

Run it:
```powershell
python -m ingestion.load_financial_facts
```

Then re-verify with the diagnostic query from before — `financial_facts rows:` should now be non-zero. **Only after this** should you re-run `python -m eval.build_golden_set` — it was correctly implemented against an empty table, so it did exactly what it should have (produced nothing), the same way `hybrid_search` correctly returning `[]` on an empty `chunks` table earlier in this build wasn't a retrieval bug, it was accurately reflecting the state of the data underneath it.

### 2.4 Hybrid retrieval — `src/retrieval/hybrid_search.py`

**Correctness note (read this before copying the code):** the lexical retrieval pass must run **independently over the full corpus**, not as a re-ranking of vector search's candidates — otherwise it can never surface a chunk that dense embeddings missed. See the earlier design discussion above if you're wondering why this matters.

**Where the lexical index lives:** rather than building and caching a BM25 index in application memory (which duplicates per-process, goes stale across replicas, and has to be rebuilt from scratch on every restart), lexical search runs directly against the `text_search` GIN index created in the schema above — Postgres owns and incrementally maintains it, the same way it owns the vector index, and every replica of your API queries the same persisted index with no cache-refresh logic required at all.

```python
from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy import text
from retrieval.db import engine

embed_model = SentenceTransformer("BAAI/bge-base-en-v1.5")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def vector_search(query: str, ticker: str = None, k: int = 20):
    q_emb = embed_model.encode(query, normalize_embeddings=True).tolist()
    filter_clause = "AND ticker = :ticker" if ticker else ""
    sql = f"""
        SELECT id, doc_id, ticker, form, item, chunk_index, text,
               1 - (embedding <=> :q_emb) AS score
        FROM chunks
        WHERE 1=1 {filter_clause}
        ORDER BY embedding <=> :q_emb
        LIMIT :k
    """
    params = {"q_emb": str(q_emb), "k": k}
    if ticker:
        params["ticker"] = ticker
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


def lexical_search(query: str, ticker: str = None, k: int = 20):
    """Independent full-corpus lexical search via Postgres's native full-text
    search — queries the persisted GIN index directly, no in-memory index to
    build, cache, or refresh. websearch_to_tsquery accepts natural-language-ish
    input (handles quoted phrases, OR, - for exclusion) rather than requiring
    the stricter to_tsquery syntax."""
    filter_clause = "AND ticker = :ticker" if ticker else ""
    sql = f"""
        SELECT id, doc_id, ticker, form, item, chunk_index, text,
               ts_rank(text_search, websearch_to_tsquery('english', :query)) AS bm25_score
        FROM chunks
        WHERE text_search @@ websearch_to_tsquery('english', :query) {filter_clause}
        ORDER BY bm25_score DESC
        LIMIT :k
    """
    params = {"query": query, "k": k}
    if ticker:
        params["ticker"] = ticker
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


def reciprocal_rank_fusion(result_lists: list, k: int = 60, id_key: str = "id"):
    """RRF: score(doc) = sum over lists of 1 / (k + rank_in_that_list).
    A doc appearing near the top of BOTH lists gets boosted; a doc unique to
    just one list (e.g. an exact keyword hit vector search missed) still surfaces
    instead of being silently dropped. k=60 is the standard constant from the
    original RRF paper / most production hybrid-search implementations."""
    fused_scores = {}
    doc_lookup = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            doc_id = doc[id_key]
            doc_lookup[doc_id] = doc
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + rank + 1)
    ranked_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)
    return [{**doc_lookup[i], "rrf_score": fused_scores[i]} for i in ranked_ids]


def hybrid_search(query: str, ticker: str = None, top_k: int = 8):
    vec_results = vector_search(query, ticker=ticker, k=20)
    lex_results = lexical_search(query, ticker=ticker, k=20)

    fused = reciprocal_rank_fusion([vec_results, lex_results])[:30]

    if not fused:
        # No candidates from either retriever — a legitimate outcome (empty/unpopulated
        # corpus, an obscure query, a ticker with no ingested filings), not an error.
        # Returning [] here lets callers (agents, eval harness, API) treat "nothing found"
        # as a normal case they can branch on, instead of an exception to catch.
        return []

    # Cross-encoder reranks the fused candidate pool for final precision
    pairs = [(query, r["text"]) for r in fused]
    rerank_scores = reranker.predict(pairs)
    for r, s in zip(fused, rerank_scores):
        r["rerank_score"] = float(s)

    return sorted(fused, key=lambda x: x["rerank_score"], reverse=True)[:top_k]
```

Notice what disappeared compared to the in-memory version: no `BM25Index` class, no `refresh_bm25_index()`, no admin endpoint needed to keep it fresh, no `rank_bm25` dependency in production. New chunks are searchable the instant they're inserted, from every replica, with zero extra code — because `text_search` is a `GENERATED ALWAYS AS ... STORED` column (Phase 2.2), Postgres computes and indexes it automatically on every insert.

**One honest caveat — `ts_rank` is not literally the BM25 formula.** Postgres's full-text ranking is a TF-based scoring function in a similar spirit to BM25 (frequency + optional length normalization) but not identical to Okapi BM25's exact term-saturation and IDF terms. For most hybrid-search use cases the practical difference is small — it's still a legitimate independent lexical signal that RRF fuses with vector search. If you want the literal BM25 formula running inside Postgres (worth knowing exists, not required for this project), the `pg_search` extension from ParadeDB implements true BM25 scoring as a Postgres extension, alongside `pgvector`, in the same database — that's the closest thing to "best of both worlds, one system" for a team that's decided vector+lexical-in-one-database is worth the tradeoff over a separate search engine.

**When would a separate search engine (OpenSearch/Elasticsearch) actually be justified instead?** When lexical query volume/complexity outgrows what a single Postgres instance's GIN index can serve at acceptable latency, or when you need search features Postgres FTS doesn't have (fuzzy matching at scale, faceted search, complex relevance tuning). Until you have evidence of that, adding a second system means a second thing to keep in sync with your source of truth, a second thing to monitor, and a second failure mode — that operational cost should be justified by a measured need, not adopted preemptively because "that's what big companies use."

### 2.5 Quick sanity test — `tests/test_retrieval.py`

Two separate tests, deliberately: one checks the function never crashes regardless of what's in the database (this is the one that would have caught the `IndexError` before it reached you as a confusing stack trace), the other checks result *shape* but skips cleanly — with a clear message — if the database isn't populated yet, instead of failing in a way that looks like a code bug when it's actually just missing data.

```python
import pytest
from retrieval.hybrid_search import hybrid_search

def test_hybrid_search_never_raises_on_empty_or_populated_corpus():
    """Should always return a list — empty if there's no data/no match, populated
    otherwise — and never raise, regardless of what's currently in the database."""
    results = hybrid_search("what are the main risk factors", ticker="AAPL", top_k=5)
    assert isinstance(results, list)

def test_hybrid_search_result_shape_when_data_exists():
    """Only meaningful once Phase 1 ingestion + Phase 2.3 embedding have actually run —
    skips with a clear reason instead of failing confusingly on an empty DB."""
    results = hybrid_search("what are the main risk factors", ticker="AAPL", top_k=5)
    if not results:
        pytest.skip("No AAPL chunks in the database yet — run `python -m ingestion.run_ingest` "
                     "then `python -m retrieval.embed_and_load` before this test is meaningful.")
    assert "text" in results[0]
    assert "rerank_score" in results[0]
```

```powershell
pytest tests/test_retrieval.py -v
```

### ✅ Phase 2 commit

```powershell
git add .
git commit -m "Phase 2: pgvector schema, HF sentence-transformers embeddings, hybrid BM25+vector+reranker retrieval"
git push
```

---

## Phase 3: Multi-Agent Orchestration with LangGraph (Weeks 5-7)

**Goal:** Planner → Retriever → Table-QA → Verifier → Synthesizer agent graph that answers questions with grounded, cited, numerically-verified answers.

### 3.1 Add dependencies

```
langgraph==0.2.14
langchain==0.2.14
langchain-openai==0.1.22
langchain-core==0.2.33
```

### 3.2 Multi-provider LLM client factory — `src/agents/llm_clients.py`

**Design decision:** DeepSeek, Kimi (Moonshot), and Gemini all expose an OpenAI-compatible `chat/completions` endpoint, so one `ChatOpenAI`-based client factory (`llm_clients.py`) covers all three, differing only by `base_url`, `model`, and API key — pulled from environment variables, not hardcoded. *(A native-Anthropic `ChatAnthropic` client for Claude was evaluated for this Synthesizer slot and reverted back to Kimi — see decision log D-015/D-016 if you're curious about that detour; the client factory below reflects the current, active setup.)*

Each agent gets the model best suited to its job, not just the cheapest one everywhere:
- **DeepSeek → Planner & Verifier.** Both are structured-reasoning tasks (decompose a question; audit a draft for unsupported numbers) where DeepSeek's strong reasoning-per-dollar is a good fit, and keeping the guardrail on a different provider than the answer-writer avoids a single provider's blind spots grading its own homework.
- **Gemini 2.5 Flash → Retriever query-expansion & Table QA.** Fast + cheap, good at short structured-extraction and query-rewriting tasks, and a large context window helps when reasoning over big table dumps.
- **Kimi (Moonshot) → Synthesizer.** Long-context strength is valuable here since the synthesizer sees the most concatenated context (chunks + facts) of any agent, and Kimi's models are strong at long-form, well-cited writing.

**A real constraint worth building for from the start, not bolting on after hitting it:** some model variants — particularly "thinking"/reasoning-tuned ones, which is exactly the kind of model you might reach for on a Synthesizer that needs to reason over a lot of concatenated context — reject any explicit `temperature` override and only accept their default (`400 invalid temperature: only 1 is allowed for this model`). Hardcoding `temperature=0` everywhere, as a first pass naturally does, breaks the moment you're on one of these models. The fix: make temperature per-provider configurable via `.env`, with a sentinel value that means "don't pass temperature at all" rather than trying to guess the one allowed numeric value:

```python
import os
from functools import lru_cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def _resolve_temperature(env_var: str, default: float) -> float:
    """Reads a per-provider temperature override from .env, falling back to
    `default` if unset. Returns a concrete float — always, never None.

    NOTE ON AN APPROACH THAT DOESN'T WORK HERE: it's tempting to try to
    "omit" temperature entirely for a model that rejects overrides, by
    passing temperature=None. On this project's pinned langchain-openai
    version, that fails differently but just as hard: `pydantic.v1.error_
    wrappers.ValidationError: temperature — none is not an allowed value`.
    This version's ChatOpenAI declares `temperature: float` (not
    `Optional[float]`), so None isn't a valid value for the field at all —
    it never reaches the point of building a request. Don't reach for None
    here; it's a dead end on this stack.

    The actual fix is simpler than either of the previous attempts: a
    "this model rejects a custom temperature" error from an OpenAI-
    compatible API is telling you the one value it *does* accept — usually
    literally "only 1 is allowed" — so just send that value explicitly."""
    raw = os.getenv(env_var)
    if raw is None:
        return default
    return float(raw)


@lru_cache(maxsize=None)
def get_deepseek_llm() -> ChatOpenAI:
    """Planner + Verifier — structured reasoning / guardrail tasks."""
    return ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=_resolve_temperature("DEEPSEEK_TEMPERATURE", default=0),
    )


@lru_cache(maxsize=None)
def get_gemini_llm() -> ChatOpenAI:
    """Retriever query-expansion + Table QA reasoning."""
    return ChatOpenAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
        temperature=_resolve_temperature("GEMINI_TEMPERATURE", default=0),
    )


@lru_cache(maxsize=None)
def get_kimi_llm() -> ChatOpenAI:
    """Synthesizer — long-context, well-cited final answer writing.
    Defaults to temperature=1 because Kimi's reasoning-tuned model variants
    (e.g. kimi-k3) reject any other value outright, per the API's own error
    message ("only 1 is allowed for this model"). Override MOONSHOT_TEMPERATURE
    in .env if you're on a variant that accepts a different value."""
    return ChatOpenAI(
        model=os.getenv("MOONSHOT_MODEL", "kimi-k2.6"),
        api_key=os.getenv("MOONSHOT_API_KEY"),
        base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
        temperature=_resolve_temperature("MOONSHOT_TEMPERATURE", default=1),
    )
```

> `@lru_cache` means each client is constructed once per process, not once per request — a small but real detail worth mentioning if asked about performance/cost in an interview (avoids re-creating HTTP client objects on every graph invocation).

> **If you hit `invalid temperature: only ... is allowed for this model` again on a different provider/model:** read the exact value the error message specifies and set that provider's `*_TEMPERATURE` env var to it — the whole point of `_resolve_temperature` is that this class of model-specific quirk becomes a one-line config change, not a code change, the same reasoning already applied to model names and base URLs. Don't reach for `temperature=None` as a "safer" alternative — depending on your installed `langchain-openai` version, that can fail Pydantic validation before the request is even built, which is a harder failure than the one you started with.

> **JSON-mode caveat:** the planner and verifier prompts below expect strict JSON back. Not every provider guarantees valid JSON the same way OpenAI's `response_format={"type":"json_object"}` does — DeepSeek supports a JSON-output mode, Gemini has `response_mime_type`, and Kimi follows OpenAI's `response_format` fairly closely, but behavior can drift. Wrap every `json.loads()` call in a try/except with one retry-with-a-stricter-prompt fallback before you rely on this in a demo (see the hardened `plan_node` below) — this is exactly the kind of "it worked on one provider but broke on another" bug worth writing up in `interview_notes.md`.

### 3.3 Shared state — `src/agents/state.py`

```python
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
```

### 3.4 Planner agent (DeepSeek) — `src/agents/planner.py`

```python
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
```

### 3.5 Retriever agent (Gemini query expansion + hybrid search) — `src/agents/retriever.py`

Gemini's job here is small but useful: rewrite each sub-task into 1-2 alternate phrasings before hitting hybrid search, which measurably improves recall on filing language that doesn't match everyday phrasing (e.g. "profit margin" → "gross margin," "cost of revenue"). This is the kind of query-expansion step you can A/B test in your eval harness (Phase 4) to show a concrete recall@k improvement.

```python
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
```

> **Tradeoff to note in your interview notes:** query expansion triples retrieval calls per sub-task. Measure whether the recall gain (Phase 4) actually justifies the added latency/cost before keeping it — this is a real "did the added complexity earn its keep" decision, and it's fine if your answer ends up being "I measured it and turned it off because the recall gain was marginal." That's a stronger story than blindly keeping every feature.

### 3.6 Table/numeric extraction agent (Gemini reasoning + SQL ground truth) — `src/agents/table_qa.py`

Structured facts still come straight from the `financial_facts` table (exact numbers, no LLM in the loop for the ground-truth path — never let an LLM "reason" its way to a number when you already have it verbatim in a database). Gemini's role is narrower and specific: when a question asks about a metric that *isn't* pre-loaded into `financial_facts` (e.g. a one-off number only mentioned in prose within a filing), Gemini does light structured extraction over the retrieved chunks to pull a candidate number — which then still has to pass through the DeepSeek verifier before it reaches the user.

```python
import json
from sqlalchemy import text
from retrieval.db import engine
from agents.state import AgentState
from agents.llm_clients import get_gemini_llm

llm = get_gemini_llm()

EXTRACT_PROMPT = """Extract any specific financial figures (numbers, percentages, dollar
amounts) mentioned in this filing excerpt, along with what each figure refers to.
Respond with ONLY a JSON list, no commentary:
[{{"metric": "...", "value": "...", "context": "..."}}]
If no figures are present, return [].

Excerpt: {excerpt}"""

def extract_facts_node(state: AgentState) -> AgentState:
    ticker = state.get("ticker")
    db_facts = []
    if ticker:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT metric, value, fiscal_period, source_doc_id FROM financial_facts WHERE ticker = :t ORDER BY fiscal_period DESC LIMIT 12"),
                {"t": ticker},
            ).mappings().all()
        db_facts = [dict(r) for r in rows]

    # Only run the LLM extraction pass over a couple of chunks to control cost —
    # this is a supplementary signal, not the primary source of truth.
    llm_facts = []
    for chunk in state.get("retrieved_chunks", [])[:3]:
        try:
            resp = llm.invoke(EXTRACT_PROMPT.format(excerpt=chunk["text"][:1500]))
            raw = resp.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            extracted = json.loads(raw)
            for e in extracted:
                e["source_doc_id"] = chunk["doc_id"]
                e["fiscal_period"] = None
            llm_facts.extend(extracted)
        except Exception:
            continue  # extraction is best-effort; never let it break the pipeline

    state["extracted_facts"] = db_facts + llm_facts
    return state
```

### 3.7 Synthesizer agent (Kimi) — `src/agents/synthesizer.py`

```python
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
```

### 3.8 Verifier agent (DeepSeek, guardrail) — `src/agents/verifier.py`

Deliberately kept on a **different provider than the synthesizer** (Kimi writes, DeepSeek checks) — a same-provider verifier is more likely to rubber-stamp its own model family's phrasing/reasoning patterns. Cross-provider verification is a legitimate LLMOps design choice worth calling out explicitly in an interview.

```python
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
```

> Note the **fail-closed** default on the JSON-parse failure path: if the verifier itself breaks, the answer is treated as *unverified* rather than silently passed through. This is the single most interview-worthy line in the whole verifier — it's the difference between a guardrail that fails safe and one that fails open.

### 3.8 Wire the graph — `src/agents/graph.py`

```python
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
```

> **Note:** add a `retry_count` field to `AgentState` and cap retries at 2 to avoid infinite loops — this is exactly the kind of production detail interviewers ask about.

### 3.9 Run it — `src/agents/run.py`

```python
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
```

Run it:
```powershell
python -m agents.run
```
```

### ✅ Phase 3 commit

```powershell
git add .
git commit -m "Phase 3: LangGraph multi-agent pipeline (planner/retriever/table-qa/synthesizer/verifier)"
git push
```

---

## Phase 4: Evaluation Harness & LLMOps (Weeks 8-10)

**Goal:** A golden dataset + automated scoring for retrieval quality, faithfulness, and numeric accuracy — plus cost/latency logging. This is the phase that separates a "demo" from a portfolio piece hiring managers trust.

### 4.1 Add dependencies

```
ragas==0.1.14
datasets==2.20.0
```

### 4.2 Build a golden eval set — `data/eval/golden_set.jsonl`

**Schema:**

```json
{"id": "gs-001", "question": "What was AAPL's gross margin in Q2 FY2024?", "ticker": "AAPL", "category": "numeric_lookup", "ground_truth_answer": "46.6%", "ground_truth_doc_id": "AAPL_0000320193-24-000069", "ground_truth_item": "financial_statements", "expected_metric": "grossMarginRatio", "expected_period": "2024Q2"}
```

| Field | Why it's there |
|---|---|
| `id` | stable reference when discussing a specific failing case later, in `interview_notes.md` or debugging |
| `question` / `ticker` | the query itself |
| `category` | routes to the right scoring method — see 4.3, this is the fix for a real gap the original single `numeric_match` function had |
| `ground_truth_answer` | what `run_eval.py` checks the final answer against, for `numeric_lookup` rows |
| `ground_truth_doc_id` / `ground_truth_item` | what `retrieval_eval.py`'s `recall_at_k` checks retrieval against — the exact chunk identity, not fuzzy text matching |
| `expected_metric` / `expected_period` | optional, for your own filtering/debugging later — not consumed by either script today |

**How many, and what mix — composition matters more than raw count.** 50-75 rows is a reasonable, achievable target (a few focused hours, not a weekend project), but a pile of near-identical "what was the gross margin" questions tests one narrow thing repeatedly. Aim for something closer to this spread:

- **~40% `numeric_lookup`** — single metric, single period, pulled straight from a financial statement. Your bread-and-butter accuracy test.
- **~20% `trend`** — spans multiple periods/quarters, requires the Synthesizer to actually reason across several `financial_facts` rows rather than parrot one number.
- **~15% `qualitative`** — pulled from MD&A / Risk Factors narrative text, no single "correct" number. Needs different scoring — see 4.3.
- **~15% `lexical_stress`** — questions specifically phrased around exact tickers, exact dollar figures, or exact item numbers (e.g. "what does Item 1A say about supply chain risk"), deliberately designed to test the case hybrid search's RRF fusion exists for — see the earlier design discussion on why vector-only search under-weights exact tokens. This category is what actually validates that fix wasn't wasted effort.
- **~10% `unanswerable`** — a question about a ticker/metric you know isn't in your ingested corpus. `ground_truth_answer` for these should be something like `"insufficient information"` — this category tests whether the Verifier correctly refuses to fabricate an answer rather than always testing whether it produces a *correct* one.

**Process for hand-labeling:**
1. Only write questions against tickers/filings you've actually ingested (`TICKERS = ["AAPL", "MSFT", "NVDA"]` from Phase 1, 2 filings each per `get_recent_filings(cik, limit=2)`) — a question about data that was never ingested will always score 0% recall, which tells you nothing about retrieval quality and everything about a golden-set authoring mistake. This is the same failure mode as the empty-database crash from earlier in this build, just showing up as a silent wrong number instead of a loud exception.
2. For `numeric_lookup`/`trend` rows: open the actual filing (or query your own `financial_facts` table, since that's the same ground truth the Table QA agent uses), find the number, and record the exact `doc_id` it came from — `SELECT doc_id, item FROM chunks WHERE ticker='AAPL' AND text LIKE '%gross margin%'` is a fast way to find the right `ground_truth_doc_id`/`ground_truth_item` pair directly from your own ingested data rather than hunting through the raw filing by hand.
3. For `qualitative` rows: paraphrase the *substance* you expect, don't copy filing text verbatim into `ground_truth_answer` — exact-string matching doesn't work for narrative answers anyway (see 4.3's scoring split).
4. For `unanswerable` rows: pick something plausible-sounding but genuinely absent (a metric you know wasn't in the two filings you ingested, or a ticker outside your three) — this is what actually tests the fail-closed verifier behavior on real input, not just the JSON-parse-failure path it was originally built for.

This manual labeling effort is itself a resume line ("built and hand-labeled a 60-example golden evaluation dataset across 5 question categories, including adversarial and unanswerable cases").

### 4.2a Script-assisted golden set generation — `src/eval/build_golden_set.py`

**What this script does and doesn't do — read this before running it.** `numeric_lookup` and `trend` rows can be generated automatically, because `financial_facts` was populated directly from Financial Modeling Prep's structured API in Phase 1 — independent of anything the RAG/agent pipeline itself computes, so using it as ground truth isn't circular; it's the same lookup a human would do by hand, just faster. `unanswerable` candidates can also be generated automatically, by finding metric/ticker combinations that genuinely don't exist in the ingested data. **`qualitative` and `lexical_stress` rows are deliberately NOT auto-generated** — those need a human to read actual narrative filing text and use judgment about what makes a good, realistic question. A script inventing both the question and the "correct" answer for a judgment-based category would produce a golden set that isn't actually independent of the system it's meant to check. The script surfaces candidate source chunks for those two categories and stops there — writing the actual rows is still on you.

```python
"""
Semi-automated golden set builder for FinSight AI's eval harness.
Run with: python -m eval.build_golden_set

Auto-generates: numeric_lookup, trend, unanswerable rows (safe — sourced
from financial_facts, independent of the RAG pipeline being evaluated).

Does NOT auto-generate: qualitative, lexical_stress rows — writes candidate
source chunks to data/eval/qualitative_candidates.md instead, for you to
read and hand-write questions against.
"""
import json
import random
from collections import defaultdict
from sqlalchemy import text
from retrieval.db import engine

OUT_PATH = "data/eval/golden_set.jsonl"
CANDIDATES_PATH = "data/eval/qualitative_candidates.md"


def _find_item_for_fact(ticker: str, doc_id: str, metric: str):
    """Best-effort lookup of which chunk Item a fact's number likely lives in,
    by searching chunks for the metric name. Returns None — not a guess — if
    the search is ambiguous (zero or multiple matching items), since a wrong
    ground_truth_item silently breaks recall@k rather than failing loudly."""
    keyword = metric.replace("Ratio", "").replace("_", " ").strip()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT item FROM chunks
            WHERE doc_id = :doc_id AND ticker = :ticker AND text ILIKE :kw
        """), {"doc_id": doc_id, "ticker": ticker, "kw": f"%{keyword}%"}).all()
    items = [r[0] for r in rows]
    return items[0] if len(items) == 1 else None


def generate_numeric_lookup_rows(limit_per_ticker: int = 8) -> list:
    with engine.connect() as conn:
        facts = conn.execute(text("""
            SELECT ticker, metric, value, fiscal_period, source_doc_id
            FROM financial_facts ORDER BY ticker, fiscal_period DESC
        """)).mappings().all()

    by_ticker = defaultdict(list)
    for f in facts:
        by_ticker[f["ticker"]].append(f)

    rows = []
    for ticker, ticker_facts in by_ticker.items():
        for f in ticker_facts[:limit_per_ticker]:
            item = _find_item_for_fact(ticker, f["source_doc_id"], f["metric"])
            metric_display = f["metric"].replace("Ratio", "").replace("_", " ").strip()
            rows.append({
                "id": f"gs-num-{ticker}-{f['metric']}-{f['fiscal_period']}",
                "question": f"What was {ticker}'s {metric_display} in {f['fiscal_period']}?",
                "ticker": ticker,
                "category": "numeric_lookup",
                "ground_truth_answer": str(f["value"]),
                "ground_truth_doc_id": f["source_doc_id"],
                "ground_truth_item": item,
                "expected_metric": f["metric"],
                "expected_period": f["fiscal_period"],
                "needs_review": item is None,
            })
    return rows


def generate_trend_rows(min_periods: int = 4, limit_per_ticker: int = 3) -> list:
    with engine.connect() as conn:
        facts = conn.execute(text("""
            SELECT ticker, metric, value, fiscal_period, source_doc_id
            FROM financial_facts ORDER BY ticker, metric, fiscal_period
        """)).mappings().all()

    by_ticker_metric = defaultdict(list)
    for f in facts:
        by_ticker_metric[(f["ticker"], f["metric"])].append(f)

    rows, count_per_ticker = [], defaultdict(int)
    for (ticker, metric), series in by_ticker_metric.items():
        if len(series) < min_periods or count_per_ticker[ticker] >= limit_per_ticker:
            continue
        recent = series[-min_periods:]
        metric_display = metric.replace("Ratio", "").replace("_", " ").strip()
        rows.append({
            "id": f"gs-trend-{ticker}-{metric}",
            "question": f"How did {ticker}'s {metric_display} trend over the last {min_periods} quarters?",
            "ticker": ticker,
            "category": "trend",
            # Heuristic ground truth: "start|end" — scored by checking both
            # endpoint values appear in the answer (see trend_match in 4.3),
            # not by matching a full trend description, which is too brittle
            # for free-form synthesis output.
            "ground_truth_answer": f"{recent[0]['value']}|{recent[-1]['value']}",
            "ground_truth_doc_id": recent[-1]["source_doc_id"],
            "ground_truth_item": _find_item_for_fact(ticker, recent[-1]["source_doc_id"], metric),
            "expected_metric": metric,
            "expected_period": f"{recent[0]['fiscal_period']}..{recent[-1]['fiscal_period']}",
            "needs_review": True,  # heuristic ground truth — always sanity-check by hand
        })
        count_per_ticker[ticker] += 1
    return rows


def generate_unanswerable_rows(n: int = 6) -> list:
    """Finds a metric that exists for SOME ticker but not others, and asks
    about it for a ticker where it's genuinely absent from the ingested
    corpus — not just an obscure phrasing of something that does exist."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT DISTINCT ticker, metric FROM financial_facts")).all()
    all_metrics = {r[1] for r in rows}
    by_ticker = defaultdict(set)
    for ticker, metric in rows:
        by_ticker[ticker].add(metric)

    candidates = []
    for ticker, present in by_ticker.items():
        for metric in list(all_metrics - present)[:2]:
            metric_display = metric.replace("Ratio", "").replace("_", " ").strip()
            candidates.append({
                "id": f"gs-unans-{ticker}-{metric}",
                "question": f"What was {ticker}'s {metric_display}?",
                "ticker": ticker,
                "category": "unanswerable",
                "ground_truth_answer": "insufficient information",
                "ground_truth_doc_id": None,
                "ground_truth_item": None,
                "expected_metric": metric,
                "expected_period": None,
                "needs_review": True,  # confirm genuinely absent, not just an ingestion gap worth fixing instead
            })
    random.shuffle(candidates)
    return candidates[:n]


def suggest_narrative_candidates(items=("1A", "7"), limit: int = 10):
    """Writes candidate narrative chunks to a markdown file for YOU to read
    and turn into qualitative/lexical_stress rows by hand. Deliberately does
    NOT write to golden_set.jsonl directly."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT ticker, doc_id, item, chunk_index, text FROM chunks
            WHERE item = ANY(:items) ORDER BY random() LIMIT :limit
        """), {"items": list(items), "limit": limit}).mappings().all()

    with open(CANDIDATES_PATH, "w") as f:
        for r in rows:
            f.write(f"## {r['ticker']} — {r['doc_id']} — Item {r['item']} (chunk {r['chunk_index']})\n\n")
            f.write(r["text"][:1200] + "\n\n---\n\n")
    print(f"Wrote {len(rows)} narrative candidates to {CANDIDATES_PATH} — "
          "read these and hand-write qualitative/lexical_stress rows from them.")


def main():
    numeric_rows = generate_numeric_lookup_rows()
    trend_rows = generate_trend_rows()
    unanswerable_rows = generate_unanswerable_rows()
    all_rows = numeric_rows + trend_rows + unanswerable_rows

    with open(OUT_PATH, "w") as f:
        for row in all_rows:
            f.write(json.dumps(row) + "\n")

    flagged = [r for r in all_rows if r.get("needs_review")]
    print(f"Wrote {len(all_rows)} auto-generated rows to {OUT_PATH}")
    print(f"  {len(numeric_rows)} numeric_lookup, {len(trend_rows)} trend, {len(unanswerable_rows)} unanswerable")
    print(f"  {len(flagged)} rows flagged needs_review: true — check these before trusting the set")

    suggest_narrative_candidates()
    print(f"Still needed by hand: qualitative and lexical_stress rows (~30% of a "
          f"well-balanced set) — see {CANDIDATES_PATH}")


if __name__ == "__main__":
    main()
```

Run it:
```powershell
python -m eval.build_golden_set
```

**Before trusting the output:**
1. Open `golden_set.jsonl` and check every row with `"needs_review": true` — these are rows where the item-lookup was ambiguous (or absent for `unanswerable`/heuristic for `trend`) and could be silently wrong if you skip this step.
2. Open `data/eval/qualitative_candidates.md` and hand-write the `qualitative` and `lexical_stress` rows the script deliberately left for you — append them to `golden_set.jsonl` in the same schema.
3. This is still real hand-labeling work, just scoped correctly — the script eliminated the tedious lookup/formatting labor for the ~60% of the set that's mechanically derivable from data you already trust, and left the ~40% that requires actual judgment for you. Worth being precise about this split if it comes up in an interview: "I automated generating ground truth for retrieval-style questions since that's just structured lookup, but kept qualitative question authoring manual, because auto-generating both the question and its own grading criterion for a judgment call would make the eval set circular" is a stronger answer than claiming full automation.

**Scoring by category, not one function for everything:** the original `numeric_match` does simple substring containment, which works fine for `"46.6%" in answer_text` but is meaningless for a qualitative narrative answer — there's no single correct string to search for. Route scoring by the `category` field instead of applying one grading method to every row.

```python
import json
import time
from agents.graph import build_graph

app = build_graph()

def load_golden_set(path="data/eval/golden_set.jsonl"):
    with open(path) as f:
        return [json.loads(line) for line in f]


def numeric_match(answer_text: str, expected_value: str) -> bool:
    return expected_value.replace("%", "").strip() in answer_text.replace("%", "")


def trend_match(answer_text: str, expected_value: str) -> bool:
    """For 'trend' rows: ground_truth_answer is 'start|end' (see
    build_golden_set.py's generate_trend_rows). Passes if BOTH endpoint
    values appear somewhere in the answer. Weaker than numeric_match — it
    doesn't verify direction or intermediate quarters — but still real
    automated signal rather than punting every trend row to manual review."""
    parts = [p.replace("%", "").strip() for p in expected_value.split("|")]
    text_clean = answer_text.replace("%", "")
    return all(p in text_clean for p in parts)


def unanswerable_match(answer_text: str) -> bool:
    """For 'unanswerable' rows: pass if the system admits it can't answer,
    rather than fabricating something. Deliberately permissive phrase list —
    the point is catching confident fabrication, not grading exact wording."""
    refusal_phrases = ["insufficient information", "cannot find", "not available",
                        "no data", "unable to determine", "not covered in"]
    return any(phrase in answer_text.lower() for phrase in refusal_phrases)


def score_row(row: dict, answer_text: str):
    """Returns True/False for automatically-scorable categories, None for
    categories that need a human (or a separate LLM-judge pass) to grade —
    counting a None as a failure would understate accuracy on exactly the
    rows that are hardest to automate, so these are reported separately."""
    category = row.get("category", "numeric_lookup")
    if category == "numeric_lookup":
        return numeric_match(answer_text, row["ground_truth_answer"])
    if category == "trend":
        return trend_match(answer_text, row["ground_truth_answer"])
    if category == "unanswerable":
        return unanswerable_match(answer_text)
    return None  # "qualitative" and any other category: needs manual/LLM-judge review


def run_eval():
    golden = load_golden_set()
    results = []
    for row in golden:
        start = time.time()
        state = app.invoke({
            "question": row["question"], "ticker": row["ticker"], "sub_tasks": [],
            "retrieved_chunks": [], "extracted_facts": [], "draft_answer": "",
            "verified": False, "verification_notes": "", "final_answer": "", "citations": [],
            "retry_count": 0,
        })
        latency = time.time() - start

        results.append({
            "id": row.get("id"),
            "category": row.get("category", "numeric_lookup"),
            "question": row["question"],
            "answer": state["final_answer"],
            "verified": state["verified"],
            "auto_correct": score_row(row, state["final_answer"]),
            "latency_sec": round(latency, 2),
            "num_chunks_retrieved": len(state["retrieved_chunks"]),
        })

    scorable = [r for r in results if r["auto_correct"] is not None]
    needs_review = [r for r in results if r["auto_correct"] is None]
    accuracy = sum(r["auto_correct"] for r in scorable) / len(scorable) if scorable else 0
    verified_rate = sum(r["verified"] for r in results) / len(results)
    avg_latency = sum(r["latency_sec"] for r in results) / len(results)

    print(f"Auto-scorable accuracy ({len(scorable)}/{len(results)} rows): {accuracy:.1%}")
    print(f"Needs manual/LLM-judge review: {len(needs_review)} rows (qualitative category)")
    print(f"Verified rate: {verified_rate:.1%}")
    print(f"Avg latency: {avg_latency:.2f}s")

    with open("data/eval/eval_results.json", "w") as f:
        json.dump({
            "summary": {"accuracy": accuracy, "verified_rate": verified_rate,
                        "avg_latency": avg_latency, "scorable_rows": len(scorable),
                        "needs_review_rows": len(needs_review)},
            "rows": results,
        }, f, indent=2)

if __name__ == "__main__":
    run_eval()
```

**On the `qualitative` category's `None` scores:** don't let these just sit unscored forever — either review them by hand (fine at 15% of a 60-row set, that's ~9 rows) or add an LLM-judge pass later (a separate call that grades the answer against `ground_truth_answer` for semantic equivalence rather than exact match) once you're comfortable with the pattern. Reporting them separately from the auto-scored accuracy, rather than silently excluding them or counting them as failures, is the honest way to present this — a portfolio eval harness that only measures the easy-to-grade 85% of questions is quietly grading its own homework.



### 4.4 Retrieval-specific metrics (recall@k) — `src/eval/retrieval_eval.py`

**Correctness note (fixing a real gap in the original version):** the first-pass version of this function checked `row["expected_period"] in r.get("text", "")` — fragile substring matching against free text — OR'd with `r.get("item") == row.get("expected_item")`, where `expected_item` never actually existed in the golden set schema. That second comparison was silently always `None == None`-or-`None == something`, which could produce false hits rather than a clean failure. Recall@k should check **exact chunk identity** (did the retrieved set contain the specific chunk the answer actually lives in), not a fuzzy text guess:

```python
import json
from retrieval.hybrid_search import hybrid_search

def load_golden_set(path="data/eval/golden_set.jsonl"):
    with open(path) as f:
        return [json.loads(l) for l in f]

def recall_at_k(golden_rows, k=5):
    hits = 0
    for row in golden_rows:
        results = hybrid_search(row["question"], ticker=row["ticker"], top_k=k)
        found = any(
            r.get("doc_id") == row["ground_truth_doc_id"]
            and r.get("item") == row["ground_truth_item"]
            for r in results
        )
        hits += int(found)
    return hits / len(golden_rows)

if __name__ == "__main__":
    golden = load_golden_set()
    print(f"Recall@5: {recall_at_k(golden, k=5):.1%}")
```

This is what actually lets you measure the "before/after" recall numbers referenced back in `interview_notes.md`'s tradeoffs table — run this once against the naive vector-only search, once against the fixed hybrid+RRF version, and you have a real, defensible number instead of a placeholder.

Track this over time as you tune chunk size, embedding model, or reranker — **this before/after comparison is your best resume metric** ("improved recall@5 from 61% to 84%").

### 4.5 Logging / observability — `src/eval/logger.py`

Simple Postgres-based query log (cheap alternative/complement to LangSmith):

```python
from sqlalchemy import text
from retrieval.db import engine

DDL = """
CREATE TABLE IF NOT EXISTS query_log (
    id SERIAL PRIMARY KEY,
    question TEXT,
    ticker TEXT,
    final_answer TEXT,
    verified BOOLEAN,
    latency_sec NUMERIC,
    num_chunks INT,
    created_at TIMESTAMP DEFAULT now()
);
"""

def init_log_table():
    with engine.connect() as conn:
        conn.execute(text(DDL))
        conn.commit()

def log_query(question, ticker, answer, verified, latency, num_chunks):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO query_log (question, ticker, final_answer, verified, latency_sec, num_chunks)
            VALUES (:q, :t, :a, :v, :l, :n)
        """), {"q": question, "t": ticker, "a": answer, "v": verified, "l": latency, "n": num_chunks})
        conn.commit()
```

Wire `log_query` into `src/agents/run.py` after each `ask()` call. Also enable LangSmith tracing (set the `.env` vars from Phase 0) for free trace visualization during development.

### ✅ Phase 4 commit

```powershell
git add .
git commit -m "Phase 4: golden eval dataset, automated eval harness (accuracy/verified-rate/latency), recall@k, query logging"
git push
```

**Deliverable to screenshot for your portfolio:** run `python -m eval.run_eval` and save the printed summary + `eval_results.json` — this is your proof-of-quality artifact.

---

## Phase 5: API + Frontend + Deployment (Weeks 11-12)

**Goal:** Ship it as a usable product with a clean demo link.

### 5.1 Add dependencies

```
fastapi==0.112.0
uvicorn==0.30.5
streamlit==1.37.1
```

### 5.2 FastAPI backend — `src/api/main.py`

```python
from fastapi import FastAPI
from pydantic import BaseModel
import time
from agents.graph import build_graph
from eval.logger import log_query, init_log_table

app = FastAPI(title="FinSight AI")
graph_app = build_graph()
init_log_table()

class QueryRequest(BaseModel):
    question: str
    ticker: str | None = None

@app.post("/query")
def query(req: QueryRequest):
    start = time.time()
    state = graph_app.invoke({
        "question": req.question, "ticker": req.ticker, "sub_tasks": [],
        "retrieved_chunks": [], "extracted_facts": [], "draft_answer": "",
        "verified": False, "verification_notes": "", "final_answer": "", "citations": [],
        "retry_count": 0,
    })
    latency = time.time() - start
    log_query(req.question, req.ticker, state["final_answer"], state["verified"], latency, len(state["retrieved_chunks"]))
    return {
        "answer": state["final_answer"],
        "verified": state["verified"],
        "sources": [{"doc_id": c["doc_id"], "item": c["item"]} for c in state["retrieved_chunks"]],
        "latency_sec": round(latency, 2),
    }

@app.get("/health")
def health():
    return {"status": "ok"}
```

Run locally: `uvicorn api.main:app --reload`

### 5.3 Streamlit frontend — `src/frontend/app.py`

```python
import streamlit as st
import requests

st.set_page_config(page_title="FinSight AI", layout="wide")
st.title("📊 FinSight AI — Financial Research Assistant")

ticker = st.text_input("Ticker (optional)", "AAPL")
question = st.text_area("Ask a research question", "How did gross margin trend over the last 4 quarters?")

if st.button("Ask"):
    with st.spinner("Researching..."):
        resp = requests.post("http://localhost:8000/query", json={"question": question, "ticker": ticker})
        data = resp.json()
    st.markdown(f"### Answer {'✅' if data['verified'] else '⚠️'}")
    st.write(data["answer"])
    st.caption(f"Latency: {data['latency_sec']}s")
    with st.expander("Sources"):
        for s in data["sources"]:
            st.write(f"- {s['doc_id']} [{s['item']}]")
```

Run: `streamlit run src/frontend/app.py`

### 5.4 Eval dashboard tab (bonus, high resume value)

Add a second Streamlit page reading `data/eval/eval_results.json` and plotting accuracy/latency trends over multiple eval runs (save each run with a timestamped filename) — this is literally a BI dashboard on your own LLM system, a perfect bridge from your background.

### 5.5 Deployment

- Backend: Fly.io or Render (Dockerfile below)
- DB: Supabase (has pgvector built in) or Render Postgres
- Frontend: Streamlit Community Cloud (free) pointed at your deployed API

`Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> Same reasoning as Phase 0.3a applies inside the container: `pyproject.toml` + `pip install -e .` is copied and run here too, so the container resolves `from retrieval...`/`from agents...` imports exactly the same way your local dev environment does — one consistent import mechanism everywhere the code runs, not a special case for Docker.

### 5.6 Final README

Include: architecture diagram (draw.io or excalidraw export as PNG), eval metrics table, tech stack, "how to run locally," and a link to the live demo.

### ✅ Phase 5 commit (final)

```powershell
git add .
git commit -m "Phase 5: FastAPI backend, Streamlit frontend + eval dashboard, Dockerfile, deployment docs"
git tag v1.0
git push
git push --tags
```
> Note: `&&` chaining only works in PowerShell 7+. If you're on the default Windows PowerShell 5.1, run commands on separate lines (as above) or use `;` instead of `&&`.

---

## Suggested Git Workflow Throughout

Use feature branches per phase if you want a cleaner history for interviewers browsing your repo:

```powershell
git checkout -b phase-1-ingestion
# ... work ...
git commit -m "..."
git checkout main
git merge phase-1-ingestion
git push
```

Squash-merge if you want a tidy `main` history; keep the branches around so reviewers can see incremental design decisions.

## What to Screenshot for Your Portfolio/Resume

1. The eval harness output (accuracy %, verified rate, latency)
2. The LangGraph graph visualization (LangGraph has a built-in `.get_graph().draw_mermaid_png()`)
3. The Streamlit UI answering a real question with citations
4. A recall@k before/after comparison table from your retrieval tuning
