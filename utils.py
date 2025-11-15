import requests
import pandas as pd
import time
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator


# ------------ Historical kline data ------------
def get_data(symbol, interval='1h', limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df


# ------------ Active USDT symbols ------------
def get_active_usdt_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()

    symbols = []
    for s in data["symbols"]:
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
            symbols.append(s["symbol"])
    return symbols


# ------------ Futures trade activity filter ------------
def has_minimum_long_short_trades(symbol, min_each=50):
    """
    Վերադարձնում է True, եթե վերջին 15 րոպեում կա
    առնվազն min_each long և min_each short գործարք:
    """
    url = "https://fapi.binance.com/fapi/v1/aggTrades"
    end_time = int(time.time() * 1000)
    start_time = end_time - (15 * 60 * 1000)

    params = {
        "symbol": symbol,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000
    }

    try:
        response = requests.get(url, params=params)
        trades = response.json()

        # Binance երբեմն dict է վերադարձնում error-ով
        if not isinstance(trades, list):
            print(f"{symbol} skipped: unexpected response (not a list): {trades}")
            return False

        long_count = 0
        short_count = 0

        for trade in trades:
            if trade["m"]:
                short_count += 1
            else:
                long_count += 1

        return long_count >= min_each and short_count >= min_each

    except Exception as e:
        print(f"Error fetching trade data for {symbol}: {e}")
        return False


# ------------ Main signal strength function ------------
def is_strong_signal(df, btc_change_pct=0, btc_rsi=50, symbol=None):
    """
    Վերադարձնում է dict, եթե սիգնալը ուժեղ է, հակառակ դեպքում None.

    Վերադարձվող dict.
    {
        "type": "LONG" կամ "SHORT",
        "rsi": float,
        "ma10": float,
        "ma30": float,
        "entry": float,   # ընթացիկ close
        "score": int
    }
    """
    if df is None or len(df) < 30:
        return None

    # Real trade activity filter (futures)
    if symbol and not has_minimum_long_short_trades(symbol):
        print(f"{symbol} skipped due to low real trade activity")
        return None

    close = df["close"]
    volume = df["volume"]

    ma10 = SMAIndicator(close, window=10).sma_indicator()
    ma30 = SMAIndicator(close, window=30).sma_indicator()
    rsi = RSIIndicator(close, window=14).rsi()

    last_close = close.iloc[-1]
    last_open = df["open"].iloc[-1]
    prev_open = df["open"].iloc[-2]
    prev_close = df["close"].iloc[-2]

    last_rsi = rsi.iloc[-1]
    last_ma10 = ma10.iloc[-1]
    last_ma30 = ma30.iloc[-1]
    current_volume = volume.iloc[-1]
    avg_volume = volume[-10:].mean()

    bearish_candles = last_close < last_open and prev_close < prev_open
    bullish_candles = last_close > last_open and prev_close > prev_open
    last_candle_direction = "UP" if last_close > last_open else "DOWN"

    score = 0
    direction = None

    # ---------- 1) RSI direction ----------
    if last_rsi < 35:
        score += 1
        direction = "SHORT"
    elif last_rsi > 65:
        score += 1
        direction = "LONG"

    # Եթե RSI-ով ուղղություն չունենք, մնացածը իմաստ չկա
    if direction is None:
        return None
