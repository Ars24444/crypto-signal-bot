import requests
import pandas as pd
import time
from get_top_symbols import get_top_volatile_symbols

def get_data(symbol, interval='1h', limit=100):
    url = 'https://api.binance.com/api/v3/klines'
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    time.sleep(0.3)
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None

    data = response.json()
    if not isinstance(data, list):
        return None

    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df

def get_data_15m(symbol, limit=100):
    return get_data(symbol, interval="15m", limit=limit)

# data_fetcher.py -ի մեջ, որտեղ մյուս get_data-ներն են

def get_data_1m(symbol: str):
    """
    Վերադարձնում է 1m timeframe-ի df տվյալ տվյալ symbol-ի համար.
    Պետք է վերադարձնի pandas DataFrame սյունակներով՝
    ['open', 'high', 'low', 'close', 'volume']
    """
    return get_data(symbol, interval="1m")  # եթե քո get_data-ն interval է ընդունում

def get_active_usdt_symbols():
    return get_top_volatile_symbols(limit=100)


