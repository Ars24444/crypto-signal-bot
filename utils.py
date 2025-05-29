import requests
import pandas as pd

def get_klines(symbol, interval="1h", limit=100):
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


def get_top_volatile_symbols(limit=30):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        df["priceChangePercent"] = df["priceChangePercent"].astype(float)
        df["quoteVolume"] = df["quoteVolume"].astype(float)
        df = df[df["symbol"].str.endswith("USDT")]
        df = df.sort_values(by=["quoteVolume", "priceChangePercent"], ascending=False)
        top_symbols = df.head(limit)["symbol"].tolist()
        return top_symbols
    except Exception as e:
        print("Error fetching top symbols:", e)
        return []


def is_strong_signal(df):
    try:
        from ta.trend import SMAIndicator
        from ta.momentum import RSIIndicator

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
            last_rsi > 58
        )

        short_condition = (
             current_volume > 1.2 * avg_volume and
             last_ma10 < last_ma30 and
             last_rsi < 42
        ) 

        if long_condition:
            return "LONG", last_rsi, last_ma10, last_ma30, price
        elif short_condition:
            return "SHORT", last_rsi, last_ma10, last_ma30, price
        else:
            return None
    except Exception as e:
        print("Error in signal calculation:", e)
        return None
