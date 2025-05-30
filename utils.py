import requests
import pandas as pd
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator

def get_data(symbol, interval='1h', limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def get_binance_spot_symbols():
    try:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(url, timeout=10)
        data = response.json()
        symbols = [s["symbol"] for s in data["symbols"] if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"]
        return symbols
    except Exception as e:
        print("Error fetching Binance spot symbols:", e)
        return []

def get_top_volatile_symbols(limit=100):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        df["priceChangePercent"] = df["priceChangePercent"].astype(float)
        df["quoteVolume"] = df["quoteVolume"].astype(float)
        df = df[df["symbol"].str.endswith("USDT")]

        valid_symbols = get_binance_spot_symbols()
        df = df[df["symbol"].isin(valid_symbols)]
        # Reduce volume filter to get more symbols
        df = df[df["quoteVolume"] > 300000]

        # Debug: print how many symbols passed the filter
        print(f"Passed symbols (volume > 300k): {len(df)}")

        df = df.sort_values(by=["quoteVolume", "priceChangePercent"], ascending=False)
        top_symbols = df.head(limit)["symbol"].tolist()
        return top_symbols
    except Exception as e:
        print("Error fetching top symbols:", e)
        return []

def is_strong_signal(df):
    try:
        close = df["close"]
        volume = df["volume"]

        ma10 = SMAIndicator(close, window=10).sma_indicator()
        ma30 = SMAIndicator(close, window=30).sma_indicator()
        rsi = RSIIndicator(close, window=14).rsi()

        current_volume = volume.iloc[-1]
        avg_volume = volume.iloc[-20:].mean()
        last_ma10 = ma10.iloc[-1]
        last_ma30 = ma30.iloc[-1]
        last_rsi = rsi.iloc[-1]
        price = close.iloc[-1]

        long_condition = (
            current_volume > 1.2 * avg_volume and
            last_ma10 > last_ma30 and
            last_rsi > 60
        )

        short_condition = (
            current_volume > 1.2 * avg_volume and
            last_ma10 < last_ma30 and
            last_rsi < 40
        )

        if long_condition:
            signal = "LONG"
        elif short_condition:
            signal = "SHORT"
        else:
            return None

        # Scoring
        score = 0
        if 45 <= last_rsi <= 65:
            score += 20
        if abs(last_ma10 - last_ma30) / last_ma30 > 0.05:
            score += 30
        if current_volume > 1.2 * avg_volume:
            score += 30

        if score < 60:
            print(f"⚠️ Skipped low-score signal: {score}")
            return None

        return signal, last_rsi, last_ma10, last_ma30, price
    except Exception as e:
        print("Error in signal calculation:", e)
        return None
