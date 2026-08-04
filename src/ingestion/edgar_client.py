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