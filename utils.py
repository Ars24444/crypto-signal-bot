from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import requests
import pandas as pd

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

def is_strong_signal(df, btc_change_pct=0):
    if df is None or len(df) < 30:
        return None

    close = df['close']
    volume = df['volume']

    ma10 = SMAIndicator(close, window=10).sma_indicator()
    ma30 = SMAIndicator(close, window=30).sma_indicator()
    rsi = RSIIndicator(close, window=14).rsi()

    last_ma10 = ma10.iloc[-1]
    last_ma30 = ma30.iloc[-1]
    last_rsi = rsi.iloc[-1]
    last_volume = volume.iloc[-1]
    avg_volume = volume[-20:].mean()

    last_open = df['open'].iloc[-1]
    last_close = df['close'].iloc[-1]
    is_bullish = last_close > last_open
    is_bearish = last_close < last_open

    entry = last_close
    signal = None
    score = 0

    if (
        last_volume > 1.2 * avg_volume and
        last_ma10 > last_ma30 and
        last_rsi > 55 and
        is_bullish
    ):
        signal = "LONG"
    elif (
        last_volume > 1.2 * avg_volume and
        last_ma10 < last_ma30 and
        last_rsi < 45 and
        is_bearish
    ):
        signal = "SHORT"
    else:
        return None
    # Avoid coins with no trend
    if abs(last_ma10 - last_ma30) < 0.002:
        return None

    if signal == "LONG":
        if last_ma10 > last_ma30: score += 1
        if last_rsi > 60: score += 1
        if last_volume > 1.5 * avg_volume: score += 1
        if is_bullish: score += 1
        if btc_change_pct > 0: score += 1

    elif signal == "SHORT":
        if last_ma10 < last_ma30: score += 1
        if last_rsi < 40: score += 1
        if last_volume > 1.5 * avg_volume: score += 1
        if is_bearish: score += 1
        if btc_change_pct < 0: score += 1

    if score >= 4:
        return signal, last_rsi, last_ma10, last_ma30, entry, score
    else:
        return None
