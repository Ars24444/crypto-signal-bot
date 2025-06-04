from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import requests
import pandas as pd

# ✅ Get historical kline data from Binance
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

# ✅ Enhanced scoring system for LONG/SHORT detection
def is_strong_signal(df, btc_change_pct=0):
    if df is None or len(df) < 30:
        return None

    close = df['close']
    volume = df['volume']

    ma10 = SMAIndicator(close, window=10).sma_indicator()
    ma30 = SMAIndicator(close, window=30).sma_indicator()
    rsi = RSIIndicator(close, window=14).rsi()

    last_close = close.iloc[-1]
    last_rsi = rsi.iloc[-1]
    last_ma10 = ma10.iloc[-1]
    last_ma30 = ma30.iloc[-1]
    current_volume = volume.iloc[-1]
    avg_volume = volume.iloc[-30:-1].mean()

    # Candlestick structure
    last_open = df['open'].iloc[-1]
    prev_open = df['open'].iloc[-2]
    prev_close = df['close'].iloc[-2]

    bearish_candles = last_close < last_open and prev_close < prev_open
    bullish_candles = last_close > last_open and prev_close > prev_open

    score = 0
    direction = None

    # --- Conditions (scoring) ---
    if last_rsi < 35:
        score += 1
        direction = 'SHORT'
    elif last_rsi > 65:
        score += 1
        direction = 'LONG'

    if abs(last_ma10 - last_ma30) / last_ma30 > 0.007:
        score += 1

    if current_volume > 1.3 * avg_volume:
        score += 1

    if direction == 'SHORT' and bearish_candles:
        score += 1
    elif direction == 'LONG' and bullish_candles:
        score += 1

    if direction == 'SHORT' and btc_change_pct <= 0:
        score += 1
    elif direction == 'LONG' and btc_change_pct >= 0:
        score += 1

    # --- Final filter ---
    if score >= 4 and direction:
        return direction, round(last_rsi, 2), round(last_ma10, 4), round(last_ma30, 4), last_close, score

    return None

# ✅ Get only active USDT pairs from Binance
def get_active_usdt_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()

    symbols = []
    for s in data["symbols"]:
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
            symbols.append(s["symbol"])
    return symbols
