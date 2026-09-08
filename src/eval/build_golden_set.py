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


def load_existing_manual_rows(path=OUT_PATH) -> list:
    """Preserve any hand-labeled qualitative/lexical_stress rows already in
    the output file. Without this, main()'s write-mode overwrite would
    silently delete real labeling work on every re-run — auto-generated
    categories (numeric_lookup/trend/unanswerable) are cheap to regenerate
    from scratch each time, but a human's judgment calls are not, and a
    script can't reconstruct them if lost."""
    import os
    if not os.path.exists(path):
        return []
    manual = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("category") in ("qualitative", "lexical_stress"):
                manual.append(row)
    return manual


def main():
    manual_rows = load_existing_manual_rows()
    numeric_rows = generate_numeric_lookup_rows()
    trend_rows = generate_trend_rows()
    unanswerable_rows = generate_unanswerable_rows()
    all_rows = numeric_rows + trend_rows + unanswerable_rows + manual_rows

    with open(OUT_PATH, "w") as f:
        for row in all_rows:
            f.write(json.dumps(row) + "\n")

    flagged = [r for r in all_rows if r.get("needs_review")]
    print(f"Wrote {len(all_rows)} rows to {OUT_PATH}")
    print(f"  {len(numeric_rows)} numeric_lookup, {len(trend_rows)} trend, "
          f"{len(unanswerable_rows)} unanswerable, {len(manual_rows)} preserved hand-labeled "
          f"(qualitative/lexical_stress)")
    print(f"  {len(flagged)} rows flagged needs_review: true — check these before trusting the set")

    suggest_narrative_candidates()
    if not manual_rows:
        print(f"Still needed by hand: qualitative and lexical_stress rows (~30% of a "
              f"well-balanced set) — see {CANDIDATES_PATH}")


if __name__ == "__main__":
    main()