import requests
import pandas as pd
import time
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange


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
    if df is None or len(df) < 40:
        return None

    # Real trade activity filter (futures)
    if symbol and not has_minimum_long_short_trades(symbol):
        print(f"{symbol} skipped due to low real trade activity")
        return None

    close = df["close"]
    volume = df["volume"]

    ma10_series = SMAIndicator(close, window=10).sma_indicator()
    ma30_series = SMAIndicator(close, window=30).sma_indicator()
    rsi_series = RSIIndicator(close, window=14).rsi()

    last_close = float(close.iloc[-1])
    last_open = float(df["open"].iloc[-1])
    prev_open = float(df["open"].iloc[-2])
    prev_close = float(df["close"].iloc[-2])

    last_rsi = float(rsi_series.iloc[-1])
    last_ma10 = float(ma10_series.iloc[-1])
    last_ma30 = float(ma30_series.iloc[-1])
    current_volume = float(volume.iloc[-1])
    avg_volume = float(volume[-10:].mean())

    bearish_candles = last_close < last_open and prev_close < prev_open
    bullish_candles = last_close > last_open and prev_close > prev_open

    def calc_score(signal_type: str) -> int:
        score = 0

        # 1) Trend (MA10 / MA30)
        if signal_type == "LONG":
            if last_close > last_ma10 > last_ma30:
                score += 2
            elif last_close > last_ma30:
                score += 1
        else:  # SHORT
            if last_close < last_ma10 < last_ma30:
                score += 2
            elif last_close < last_ma30:
                score += 1

        # 2) RSI pullback գոտի
        if signal_type == "LONG":
            # իդեալական long pullback
            if 35 <= last_rsi <= 45:
                score += 2
            elif 30 <= last_rsi < 35 or 45 < last_rsi <= 50:
                score += 1
        else:  # SHORT
            if 55 <= last_rsi <= 65:
                score += 2
            elif 50 <= last_rsi < 55 or 65 < last_rsi <= 70:
                score += 1

        # 3) Վերջին 2 մոմի ուղղությունը
        if signal_type == "LONG" and bullish_candles:
            score += 1
        elif signal_type == "SHORT" and bearish_candles:
            score += 1

        # 4) Volume confirmation
        if current_volume >= avg_volume * 1.15:
            score += 2
        elif current_volume >= avg_volume * 1.05:
            score += 1

        # 5) BTC filter – շուկան չպետք է լինի մեզ կտրուկ դեմ
        btc_ok = True
        if signal_type == "LONG":
            # BTC շատ չընկնի, RSI-ն ոչ շատ թույլ
            if btc_change_pct < -0.7 or btc_rsi < 40:
                btc_ok = False
        else:  # SHORT
            if btc_change_pct > 0.7 or btc_rsi > 60:
                btc_ok = False

        if not btc_ok:
            return -999  # հատուկ, որ չընտրի էս կողմը
        else:
            score += 1

        return score

    long_score = calc_score("LONG")
    short_score = calc_score("SHORT")

    print(
        f"📊 {symbol} scores -> LONG: {long_score}, SHORT: {short_score} | "
        f"RSI={last_rsi:.1f}, MA10={last_ma10:.4f}, MA30={last_ma30:.4f}, "
        f"vol={current_volume:.0f}/{avg_volume:.0f}, BTCΔ={btc_change_pct:.2f}%, BTC_RSI={btc_rsi:.1f}",
        flush=True
    )

    best_type = None
    best_score = 0

    # ընտրում ենք առավելագույն score ունեցող ուղղությունը
    if long_score >= short_score and long_score >= 5:
        best_type = "LONG"
        best_score = long_score
    elif short_score > long_score and short_score >= 5:
        best_type = "SHORT"
        best_score = short_score

    if best_type is None:
        return None

    return {
        "type": best_type,
        "rsi": last_rsi,
        "ma10": last_ma10,
        "ma30": last_ma30,
        "entry": last_close,
        "score": int(best_score),
    }
