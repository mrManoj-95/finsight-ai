import os
import requests
from dotenv import load_dotenv

load_dotenv()
FMP_KEY = os.getenv("FMP_API_KEY")
BASE = "https://financialmodelingprep.com/stable"



def _check_fmp_error(data):
    """FMP returns error bodies with a 200 status, so raise_for_status()
    never catches them. Check explicitly and fail loudly with a clear
    message rather than letting an error dict silently masquerade as data."""
    if isinstance(data, dict) and "Error Message" in data:
        raise RuntimeError(f"FMP API error: {data['Error Message']}")
    return data


def get_income_statement(ticker: str, period="quarter", limit=8):
    url = f"{BASE}/income-statement"
    resp = requests.get(url, params={"symbol": ticker, "period": period, "limit": limit, "apikey": FMP_KEY})
    resp.raise_for_status()
    return _check_fmp_error(resp.json())


def get_earnings_transcript(ticker: str, year: int, quarter: int):
    url = f"{BASE}/earning-call-transcript"
    resp = requests.get(url, params={"symbol": ticker, "year": year, "quarter": quarter, "apikey": FMP_KEY})
    resp.raise_for_status()
    return _check_fmp_error(resp.json())