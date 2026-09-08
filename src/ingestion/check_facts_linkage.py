"""
Diagnostic: checks whether any single source_doc_id in financial_facts is
being cited as the source for multiple, widely-spread fiscal periods — a
sign that nearest_filing_doc_id's "any filing dated on/after this period"
logic may be linking a fact to a filing that doesn't actually report on
that period, just happens to be dated after it.
"""
from retrieval.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT ticker, source_doc_id, COUNT(DISTINCT fiscal_period) AS distinct_periods,
               STRING_AGG(DISTINCT fiscal_period, ', ') AS periods
        FROM financial_facts
        GROUP BY ticker, source_doc_id
        ORDER BY ticker, distinct_periods DESC
    """)).all()

for r in rows:
    print(r)