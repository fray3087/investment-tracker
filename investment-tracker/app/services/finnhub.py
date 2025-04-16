import os
import requests
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

def get_stock_quote(symbol):
    url = f"{FINNHUB_BASE_URL}/quote"
    params = {
        "symbol": symbol,
        "token": FINNHUB_API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def search_symbol(query):
    url = f"{FINNHUB_BASE_URL}/search"
    params = {
        "q": query,
        "token": FINNHUB_API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get('result', [])
