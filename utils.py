import requests
import pandas as pd
import numpy as np

from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

def get_data(symbol, interval='1h', limit=100):
    url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None

    data = response.json()
    if not isinstance(data, list):
        return None

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

def is_strong_signal(df, btc_change_pct=0, btc_rsi=0, symbol=""):
    if df is None or len(df) < 30:
        return None

    close = df['close']
    open_ = df['open']
    volume = df['volume']
    high = df['high']
    low = df['low']

    last_close = close.iloc[-1]
    last_open = open_.iloc[-1]
    prev_close = close.iloc[-2]
    prev_open = open_.iloc[-2]
    last_rsi = RSIIndicator(close).rsi().iloc[-1]
    last_ma10 = SMAIndicator(close, window=10).sma_indicator().iloc[-1]
    last_ma30 = SMAIndicator(close, window=30).sma_indicator().iloc[-1]
    avg_volume = volume[-20:-5].mean()
    current_volume = volume.iloc[-1]

    bullish_candles = last_close > last_open and prev_close > prev_open
    bearish_candles = last_close < last_open and prev_close < prev_open

    direction = None
    score = 0

    if last_rsi < 35:
        direction = "SHORT"
        score += 1
    elif last_rsi > 65 and last_rsi < 70:
        direction = "LONG"
        score += 1
    else:
        return None

    if (direction == "LONG" and last_ma10 > last_ma30) or (direction == "SHORT" and last_ma10 < last_ma30):
        score += 1

    if current_volume > 1.2 * avg_volume and current_volume < 3.5 * avg_volume:
        score += 1

    if (direction == "LONG" and bullish_candles) or (direction == "SHORT" and bearish_candles):
        score += 1

    if (direction == "LONG" and btc_change_pct >= -0.5) or (direction == "SHORT" and btc_change_pct <= 0.5):
        score += 1

    if direction == "LONG" and last_rsi >= 70:
        return None
    if direction == "SHORT" and last_rsi <= 30:
        return None

    if direction == "LONG" and btc_change_pct > 2.5 and btc_rsi > 65:
        return None
    if direction == "SHORT" and btc_change_pct < -2.5 and btc_rsi < 35:
        return None

    if direction == "LONG" and last_close < last_open:
        return None
    if direction == "SHORT" and last_close > last_open:
        return None

    try:
        from safe_candle_checker import is_safe_last_candle
        if not is_safe_last_candle(df, signal_type=direction):
            return None
    except:
        pass

    atr = AverageTrueRange(high, low, close).average_true_range().iloc[-1]
    entry = last_close

    if direction == "LONG":
        tp1 = entry + 1.2 * atr
        tp2 = entry + 2.0 * atr
        sl = entry - 1.0 * atr
    else:
        tp1 = entry - 1.2 * atr
        tp2 = entry - 2.0 * atr
        sl = entry + 1.0 * atr

    if score < 4:
        return None

    return {
        "type": direction,
        "entry": round(entry, 4),
        "tp1": round(tp1, 4),
        "tp2": round(tp2, 4),
        "sl": round(sl, 4),
        "score": score,
        "rsi": round(last_rsi, 2),
        "ma10": round(last_ma10, 4),
        "ma30": round(last_ma30, 4)
    }
def get_active_usdt_symbols():
    from get_top_symbols import get_top_volatile_symbols
    return get_top_volatile_symbols(limit=100)
