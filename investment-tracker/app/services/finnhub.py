# app/services/finnhub.py
import os
import requests

FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

def get_stock_quote(symbol):
    """
    Recupera il prezzo attuale e altri dati di quote per un simbolo.
    Ad esempio, per "AAPL" o "SWDA.MI".
    """
    url = f"{FINNHUB_BASE_URL}/quote"
    params = {
        "symbol": symbol,
        "token": FINNHUB_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        # Qui puoi implementare un meccanismo di retry o logging
        response.raise_for_status()

def get_stock_profile(symbol):
    """
    Recupera il profilo dell'azienda per un simbolo.
    Ad esempio, include il nome, il settore e altre info.
    """
    url = f"{FINNHUB_BASE_URL}/stock/profile2"
    params = {
        "symbol": symbol,
        "token": FINNHUB_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_stock_statistics(symbol):
    """
    Recupera statistiche fondamentali del titolo.
    Finnhub offre vari endpoint; puoi adattare in base alle tue necessità.
    """
    url = f"{FINNHUB_BASE_URL}/stock/metric"
    params = {
        "symbol": symbol,
        "metric": "all",
        "token": FINNHUB_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()
