import os
import requests
from dotenv import load_dotenv

load_dotenv()
FMP_KEY = os.getenv("FMP_API_KEY")
BASE = "https://financialmodelingprep.com/api/v3"


def get_income_statement(ticker: str, period="quarter", limit=8):
    url = f"{BASE}/income-statement/{ticker}"
    resp = requests.get(url, params={"period": period, "limit": limit, "apikey": FMP_KEY})
    resp.raise_for_status()
    return resp.json()


def get_earnings_transcript(ticker: str, year: int, quarter: int):
    url = f"{BASE}/earning_call_transcript/{ticker}"
    resp = requests.get(url, params={"year": year, "quarter": quarter, "apikey": FMP_KEY})
    resp.raise_for_status()
    return resp.json()