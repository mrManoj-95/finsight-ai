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
from datetime import datetime, timedelta

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


def nearest_filing_doc_id(conn, ticker: str, period_end: str, max_days_after: int = 100):
    """Finds the ingested filing that actually REPORTS on this specific
    period — not just any filing dated after it. SEC large-accelerated
    filers must file 10-Qs within ~40 days and 10-Ks within ~60 days of
    period end; max_days_after=100 gives buffer without accepting a filing
    from an unrelated, much later quarter. Returns None (skip) if nothing
    qualifies within the window, rather than mislinking."""
    period_end_date = datetime.strptime(period_end, "%Y-%m-%d").date()
    cutoff_date = period_end_date + timedelta(days=max_days_after)
    row = conn.execute(text("""
        SELECT doc_id FROM chunks
        WHERE ticker = :ticker AND filing_date >= :period_end AND filing_date <= :cutoff
        ORDER BY filing_date ASC LIMIT 1
    """), {"ticker": ticker, "period_end": period_end, "cutoff": cutoff_date}).first()
    return row[0] if row else None


def load_facts_for_ticker(ticker: str) -> int:
    statements = get_income_statement(ticker, period="quarter", limit=5)
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