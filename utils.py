from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

def safe_candle(df):
    """
    Վերջին մոմի անվտանգության ստուգում
    """
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    candle_size = last["high"] - last["low"]

    if candle_size == 0:
        return False

    body_ratio = body / candle_size

    # Avoid long wicks & micro candles
    return body_ratio >= 0.35


def btc_filter_pass(force=False):
    """
    BTC filter — RSI + %change
    force=True → skip
    """
    from data_fetcher import get_data_15m

    if force:
        return True, "forced"

    df = get_data_15m("BTCUSDT")

    if df is None or len(df) < 50:
        return False, "btc_data_error"

    close = df["close"]

    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
    change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100

    if rsi > 75:
        return False, "rsi_high"

    if rsi < 25:
        return False, "rsi_low"

    if abs(change) > 3:
        return False, "btc_volatile"

    return True, "ok"


def is_strong_signal(df):
    """
    11.11-ի սիգնալների scoring logic:
    - EMA10/EMA30 trend
    - RSI
    - Price momentum
    - Candle shape
    """

    if df is None or len(df) < 70:
        return None, 0

    close = df["close"]
    open_ = df["open"]
    high = df["high"]
    low = df["low"]

    # Indicators
    ema10 = EMAIndicator(close, window=10).ema_indicator().iloc[-1]
    ema30 = EMAIndicator(close, window=30).ema_indicator().iloc[-1]
    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]

    last_close = close.iloc[-1]
    prev_close = close.iloc[-2]

    score = 0
    signal_type = None

    #=============== LONG ===============
    if last_close > ema10 and ema10 > ema30:
        score += 1  # trend

        if rsi < 68:
            score += 1

        if last_close > prev_close:
            score += 1  # momentum

        if safe_candle(df):
            score += 1

        if score >= 3:
            signal_type = "LONG"

    #=============== SHORT ===============
    short_score = 0

    if last_close < ema10 and ema10 < ema30:
        short_score += 1

        if rsi > 32:
            short_score += 1

        if last_close < prev_close:
            short_score += 1

        if safe_candle(df):
            short_score += 1

        if short_score >= 3:
            signal_type = "SHORT"
            score = short_score

    if signal_type is None:
        return None, 0

    return signal_type, score
