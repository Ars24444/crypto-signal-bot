import requests
import pandas as pd
import numpy as np

from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from btc_filter import check_btc_influence
from orderbook_filter import is_orderbook_safe
from whitelist_manager import is_whitelisted
from get_top_symbols import get_top_volatile_symbols
from safe_candle_checker import is_safe_last_candle  
from trade_volume_filter import has_sufficient_trades  

# ✅ Optional: For extra orderbook structure
def get_orderbook_strength(symbol, limit=5):
    try:
        url = f"https://api.binance.com/api/v3/depth"
        params = {"symbol": symbol.upper(), "limit": limit}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        bids = sum([float(bid[1]) for bid in data["bids"]])
        asks = sum([float(ask[1]) for ask in data["asks"]])

        if bids == 0:
            return "weak"

        ratio = asks / bids
        if ratio > 2:
            return "bearish"
        elif ratio < 0.5:
            return "bullish"
        else:
            return "neutral"
    except:
        return "unknown"

def get_data(symbol, interval='1h', limit=100):
    url = 'https://api.binance.com/api/v3/klines'
    params = {"symbol": symbol, "interval": interval, "limit": limit}
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

def get_active_usdt_symbols():
    return get_top_volatile_symbols(limit=100)
    def is_strong_signal(df, btc_change_pct=0, btc_rsi=0, symbol=""):
    score = 0
    if df is None or len(df) < 30:
        return None

    if not has_sufficient_trades(symbol):
        print(f"⛔️ {symbol} skipped: insufficient trades")
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

    if np.isnan(last_ma10) or np.isnan(last_ma30) or last_ma10 == 0 or last_ma30 == 0:
        return None

    avg_volume = volume[-20:-5].mean()
    current_volume = volume.iloc[-1]

    # ✅ Low price filter (reject tiny coins)
    if last_close < 0.005:
        print(f"⛔️ {symbol} skipped: too low price ({last_close:.6f})")
        return None

    # ✅ Tiny movement filter (reject flat movers)
    intraday_range = high.iloc[-1] - low.iloc[-1]
    if intraday_range < last_close * 0.005:
        print(f"⛔️ {symbol} skipped: too small price range")
        return None

    # ✅ Weak volume filter
    if current_volume < avg_volume * 1.5:
        print(f"⛔️ {symbol} skipped: weak volume ({current_volume:.0f} < 1.5x avg {avg_volume:.0f})")
        return None

    # Weak market + weak volume = penalty
    if abs(btc_change_pct) < 0.3 and current_volume < 0.15 * avg_volume:
        score -= 1
        print(f"⚠️ {symbol} penalized -1 due to weak volume in calm market")

    bullish_candles = last_close > last_open and prev_close > prev_open
    bearish_candles = last_close < last_open and prev_close < prev_open

    direction = None
    score = 0

    # RSI direction
    if last_rsi < 40:
        direction = "SHORT"
        score += 1
    elif 55 < last_rsi < 70:
        direction = "LONG"
        score += 1
    else:
        return None

    # ✅ Check BTC influence
    if not check_btc_influence(signal_type=direction):
        return None

    # BTC penalty
    btc_penalty = 0
    if direction == "SHORT" and btc_change_pct > 2.5 and btc_rsi > 70:
        btc_penalty = 1
        print(f"⚠️ {symbol} SHORT penalized due to strong BTC uptrend")
    elif direction == "LONG" and btc_change_pct < -2.5 and btc_rsi < 30:
        btc_penalty = 1
        print(f"⚠️ {symbol} LONG penalized due to strong BTC downtrend")

    # BTC dumping bonus
    if direction == "SHORT" and btc_change_pct < -2.0:
        score += 1
        print(f"{symbol} ➕ BTC dumping ({btc_change_pct:.2f}%) – bonus for SHORT")

    # ✅ MA trend check
    if (direction == "LONG" and last_ma10 > last_ma30) or (direction == "SHORT" and last_ma10 < last_ma30):
        score += 1
    else:
        print(f"⚠️ {symbol} – MA trend not matched for {direction}")
        return None

    # Volume confirmation
    score += 1

    # Candle structure
    if (direction == "LONG" and bullish_candles) or (direction == "SHORT" and bearish_candles):
        score += 1
    else:
        return None

    # BTC directional bonus
    if (direction == "LONG" and btc_change_pct > 0.5) or (direction == "SHORT" and btc_change_pct < -0.5):
        score += 1

    score -= btc_penalty

    # RSI rejection
    if direction == "LONG" and last_rsi >= 70:
        return None
    if direction == "SHORT" and last_rsi <= 30:
        return None

    # Last candle confirmation
    if direction == "LONG" and last_close < last_open:
        return None
    if direction == "SHORT" and last_close > last_open:
        return None

    if not is_safe_last_candle(df, signal_type=direction):
        return None

    # ✅ TP/SL using ATR
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
        print(f"🔎 Debug: {symbol} rejected — score too low ({score})")
        return None

    print(f"🔍 {symbol} | DIR: {direction} | Score: {score}/5 | RSI: {last_rsi:.2f} | MA10: {last_ma10:.4f} / MA30: {last_ma30:.4f} | Vol: {current_volume:.2f} | BTC: {btc_change_pct:.2f}%")

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
