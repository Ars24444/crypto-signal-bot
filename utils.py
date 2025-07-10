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
from data_fetcher import get_data
from volume_filter import get_volume_strength

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


__all__ = [
    "get_data", 
    "get_data_15m", 
    "get_orderbook_strength", 
    "get_active_usdt_symbols"
]

def is_strong_signal(df, btc_change_pct=0, btc_rsi=0, symbol=""):
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

    # ✅ Price too low protection
    if last_close < 0.0001 or high.iloc[-1] < 0.0001 or low.iloc[-1] < 0.0001:
        print(f"⛔️ {symbol} rejected: price too small (< 0.0001)")
        return None

    # ✅ Invalid MA values
    if np.isnan(last_ma10) or np.isnan(last_ma30) or last_ma10 <= 0 or last_ma30 <= 0:
        print(f"⛔️ {symbol} rejected: invalid MA values")
        return None
    if round(last_ma10, 5) == round(last_ma30, 5):
        print(f"⛔️ {symbol} rejected: MA10 and MA30 are equal ({last_ma10})")
        return None

    avg_volume = volume[-20:-5].mean()
    current_volume = volume.iloc[-1]

    direction = None
    score = 0

    range_pct = (high.iloc[-1] - low.iloc[-1]) / low.iloc[-1] * 100
    if range_pct < 0.2:
        print(f"⛔️ {symbol} skipped: too small price range ({range_pct:.2f}%)")
        return None
    elif range_pct < 0.5:
        print(f"⚠️ {symbol} low range ({range_pct:.2f}%), score not added")
    else:
        score += 1

    if abs(btc_change_pct) < 0.3 and current_volume < 0.05 * avg_volume:
        print(f"⚠️ {symbol} skipped: weak volume in calm market")
        return None

    bullish_candles = last_close > last_open and prev_close > prev_open
    bearish_candles = last_close < last_open and prev_close < prev_open

    if last_rsi < 40:
        direction = "SHORT"
        score += 1
    elif 55 < last_rsi < 70:
        direction = "LONG"
        score += 1
    else:
        print(f"⚠️ {symbol} RSI not in valid range: {last_rsi:.2f}")
        return None

    volume_info = get_volume_strength(symbol)
    if volume_info:
        ratio = volume_info["ratio"]
        if direction == "LONG":
            if ratio < 0.35:
                print(f"❌ {symbol} rejected: very weak buyers (ratio {ratio:.2f})")
                return None
            elif 0.35 <= ratio < 0.5:
                print(f"⚠️ {symbol} weak buyer ratio ({ratio:.2f}), no score added")
            elif 0.5 <= ratio < 0.6:
                print(f"✅ {symbol} buyer ratio decent ({ratio:.2f}), score +1")
                score += 1
            elif ratio >= 0.6:
                print(f"✅ {symbol} strong buyer ratio ({ratio:.2f}), score +2")
                score += 2
        elif direction == "SHORT":
            if ratio > 0.65:
                print(f"❌ {symbol} rejected: very weak sellers (ratio {1 - ratio:.2f})")
                return None
            elif 0.5 < ratio <= 0.65:
                print(f"⚠️ {symbol} weak seller ratio ({1 - ratio:.2f}), no score added")
            elif 0.4 < ratio <= 0.5:
                print(f"✅ {symbol} seller ratio decent ({1 - ratio:.2f}), score +1")
                score += 1
            elif ratio <= 0.4:
                print(f"✅ {symbol} strong seller ratio ({1 - ratio:.2f}), score +2")
                score += 2

    if not check_btc_influence(btc_change_pct, direction):
        return None

    orderbook_strength = get_orderbook_strength(symbol)
    if direction == "LONG" and orderbook_strength == "bearish":
        print(f"📉 {symbol} rejected due to strong sell wall (orderbook bearish)")
        return None
    if direction == "SHORT" and orderbook_strength == "bullish":
        print(f"📈 {symbol} rejected due to strong buy wall (orderbook bullish)")
        return None

    btc_penalty = 0
    if direction == "SHORT" and btc_change_pct > 2.5 and btc_rsi > 70:
        btc_penalty = 1
        print(f"⚠️ {symbol} SHORT penalized due to strong BTC uptrend")
    elif direction == "LONG" and btc_change_pct < -2.5 and btc_rsi < 30:
        btc_penalty = 1
        print(f"⚠️ {symbol} LONG penalized due to strong BTC downtrend")
    if direction == "SHORT" and btc_change_pct < -2.0:
        score += 1

    if (direction == "LONG" and last_ma10 > last_ma30) or (direction == "SHORT" and last_ma10 < last_ma30):
        score += 1
    else:
        print(f"⚠️ {symbol} – MA trend not matched for {direction}")
        return None

    if current_volume > 0.1 * avg_volume:
        score += 1
    else:
        print(f"⚠️ {symbol} – weak volume, score not added")

    if (direction == "LONG" and bullish_candles) or (direction == "SHORT" and bearish_candles):
        score += 1
    else:
        print(f"⚠️ {symbol} – candle structure weak")
        return None

    if (direction == "LONG" and btc_change_pct > 0.5) or (direction == "SHORT" and btc_change_pct < -0.5):
        score += 1

    score -= btc_penalty

    if direction == "LONG" and last_rsi >= 70:
        print(f"⚠️ {symbol} LONG rejected: RSI too high ({last_rsi:.2f})")
        return None
    if direction == "SHORT" and last_rsi <= 30:
        print(f"⚠️ {symbol} SHORT rejected: RSI too low ({last_rsi:.2f})")
        return None
    if direction == "LONG" and last_close < last_open:
        print(f"⚠️ {symbol} LONG rejected: last candle is red")
        return None
    if direction == "SHORT" and last_close > last_open:
        print(f"⚠️ {symbol} SHORT rejected: last candle is green")
        return None

    if not is_safe_last_candle(df, signal_type=direction):
        print(f"⚠️ {symbol} rejected by last candle safety filter")
        return None

    # ✅ ATR-based TP/SL
    atr = AverageTrueRange(high, low, close).average_true_range().iloc[-1]
    entry = last_close
    tp1 = entry + 1.2 * atr if direction == "LONG" else entry - 1.2 * atr
    tp2 = entry + 2.0 * atr if direction == "LONG" else entry - 2.0 * atr
    sl = entry - 1.0 * atr if direction == "LONG" else entry + 1.0 * atr

    # ✅ Reject if TP or SL are unrealistically close
    if abs(tp1 - tp2) < 0.0001 or abs(entry - tp1) < 0.0001 or abs(entry - sl) < 0.0001:
        print(f"⛔️ {symbol} rejected: TP or SL too close to entry")
        return None

    if score < 4:
        print(f"🔎 Debug: {symbol} rejected — score too low ({score})")
        print(f"🔍 {symbol} | DIR: {direction} | Score: {score}/5 | RSI: {last_rsi:.2f} | MA10: {last_ma10:.4f} / MA30: {last_ma30:.4f} | Vol: {current_volume:.2f} | BTC: {btc_change_pct:.2f}%")
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
