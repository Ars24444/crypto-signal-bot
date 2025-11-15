import requests
import pandas as pd
import time
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator

# Get historical kline data from Binance
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

# Get only active USDT trading pairs from Binance
def get_active_usdt_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()

    symbols = []
    for s in data["symbols"]:
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
            symbols.append(s["symbol"])
    return symbols

# Check if there are at least N long and N short trades in last 15min from Binance Futures
def has_minimum_long_short_trades(symbol, min_each=50):
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

        if not isinstance(trades, list):
            print(f"{symbol} skipped: unexpected response (not a list): {trades}")
            return False

        long_count = 0
        short_count = 0

        for trade in trades:
            if trade['m']:
                short_count += 1
            else:
                long_count += 1

        return long_count >= min_each and short_count >= min_each

    except Exception as e:
        print(f"Error fetching trade data for {symbol}: {e}")
        return False

# Main signal detection function
def is_strong_signal(df, btc_change_pct=0, btc_rsi=50, symbol=None):
    if df is None or len(df) < 30:
        return None

    if symbol and not has_minimum_long_short_trades(symbol):
        print(f"{symbol} skipped due to low real trade activity")
        return None

    close = df['close']
    volume = df['volume']
    ma10 = SMAIndicator(close, window=10).sma_indicator()
    ma30 = SMAIndicator(close, window=30).sma_indicator()
    rsi = RSIIndicator(close, window=14).rsi()

    last_close = close.iloc[-1]
    last_open = df['open'].iloc[-1]
    prev_open = df['open'].iloc[-2]
    prev_close = df['close'].iloc[-2]

    last_rsi = rsi.iloc[-1]
    last_ma10 = ma10.iloc[-1]
    last_ma30 = ma30.iloc[-1]
    current_volume = volume.iloc[-1]
    avg_volume = volume[-10:].mean()

    bearish_candles = last_close < last_open and prev_close < prev_open
    bullish_candles = last_close > last_open and prev_close > prev_open
    last_candle_direction = 'UP' if last_close > last_open else 'DOWN'

    score = 0
    direction = None

    if last_rsi < 35:
        score += 1
        direction = 'SHORT'
    elif last_rsi > 65:
        score += 1
        direction = 'LONG'

    if abs(last_ma10 - last_ma30) / last_ma30 > 0.007:
        score += 1

    if current_volume > 1.3 * avg_volume and current_volume < 3.0 * avg_volume:
        score += 1

    if direction == 'SHORT' and bearish_candles:
        score += 1
    elif direction == 'LONG' and bullish_candles:
        score += 1

    if direction == 'SHORT' and btc_change_pct <= 0:
        score += 1
    elif direction == 'LONG' and btc_change_pct >= 0:
        score += 1

    if direction == 'SHORT' and last_candle_direction == 'UP':
        print(f"{symbol} skipped: SHORT contradicts green candle")
        return None
    elif direction == 'LONG' and last_candle_direction == 'DOWN':
        print(f"{symbol} skipped: LONG contradicts red candle")
        return None

    if btc_change_pct > 1.2 and direction == 'SHORT':
        print(f"{symbol} skipped due to BTC uptrend blocking SHORT")
        return None
    elif btc_change_pct < -1.2 and direction == 'LONG':
        print(f"{symbol} skipped due to BTC downtrend blocking LONG")
        return None

    if btc_change_pct < -2.5 and btc_rsi < 35 and direction == 'SHORT':
        print(f"{symbol} skipped: BTC oversold, SHORT blocked")
        return None
    if btc_change_pct > 2.5 and btc_rsi > 65 and direction == 'LONG':
        print(f"{symbol} skipped: BTC overbought, LONG blocked")
        return None

    if score >= 4 and direction:
        return direction, round(last_rsi, 2), round(last_ma10, 4), round(last_ma30, 4), last_close, score

    return None
