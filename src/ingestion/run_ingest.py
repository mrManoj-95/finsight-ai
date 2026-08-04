import json
from pathlib import Path
from src.ingestion.edgar_client import get_cik_for_ticker, get_recent_filings, download_filing
from src.ingestion.section_parser import extract_text, split_into_items
from src.ingestion.chunker import build_chunk_records

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