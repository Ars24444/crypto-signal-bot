import numpy as np
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator


def has_minimum_long_short_trades(symbol):
    try:
        return True
    except:
        return True


def is_strong_signal(df, btc_change_pct=0, btc_rsi=50, symbol=None):
    if df is None or len(df) < 40:
        return None

    if symbol and not has_minimum_long_short_trades(symbol):
        return None

    close = df["close"]
    volume = df["volume"]
    open_price = df["open"]

    ma10 = SMAIndicator(close, window=10).sma_indicator().iloc[-1]
    ma30 = SMAIndicator(close, window=30).sma_indicator().iloc[-1]
    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]

    last_close = float(close.iloc[-1])
    last_open = float(open_price.iloc[-1])
    prev_open = float(open_price.iloc[-2])
    prev_close = float(close.iloc[-2])

    current_volume = float(volume.iloc[-1])
    avg_volume = float(volume[-10:].mean())

    bullish_candles = last_close > last_open and prev_close > prev_open
    bearish_candles = last_close < last_open and prev_close < prev_open

    # ================= BTC FILTER (EARLY EXIT) =================
    if btc_change_pct < -0.7 or btc_rsi < 40:
        allow_long = False
    else:
        allow_long = True

    if btc_change_pct > 0.7 or btc_rsi > 60:
        allow_short = False
    else:
        allow_short = True

    def score_long():
        score = 0

        # Trend
        if last_close > ma10 > ma30:
            score += 2
        elif last_close > ma30:
            score += 1

        # RSI pullback
        if 35 <= rsi <= 45:
            score += 2
        elif 30 <= rsi < 35 or 45 < rsi <= 50:
            score += 1

        # Candles
        if bullish_candles:
            score += 1

        # Volume (only if liquid)
        if avg_volume > 0:
            if current_volume >= avg_volume * 1.15:
                score += 2
            elif current_volume >= avg_volume * 1.05:
                score += 1

        return score

    def score_short():
        score = 0

        # Trend
        if last_close < ma10 < ma30:
            score += 2
        elif last_close < ma30:
            score += 1

        # RSI pullback
        if 55 <= rsi <= 65:
            score += 2
        elif 50 <= rsi < 55 or 65 < rsi <= 70:
            score += 1

        # Candles
        if bearish_candles:
            score += 1

        # Volume
        if avg_volume > 0:
            if current_volume >= avg_volume * 1.15:
                score += 2
            elif current_volume >= avg_volume * 1.05:
                score += 1

        return score

    long_score = score_long() if allow_long else -1
    short_score = score_short() if allow_short else -1

    print(
        f"📊 {symbol} | LONG={long_score} SHORT={short_score} "
        f"| RSI={rsi:.1f} MA10={ma10:.4f} MA30={ma30:.4f} "
        f"| vol={current_volume:.0f}/{avg_volume:.0f} "
        f"| BTCΔ={btc_change_pct:.2f}% BTC_RSI={btc_rsi:.1f}",
        flush=True,
    )

    # ================= FINAL DECISION =================
    MIN_SCORE = 5
    MIN_DIFF = 1  # spread protection

    if long_score >= MIN_SCORE and long_score > short_score + MIN_DIFF:
        return {
            "type": "LONG",
            "rsi": rsi,
            "ma10": ma10,
            "ma30": ma30,
            "entry": last_close,
            "score": long_score,
        }

    if short_score >= MIN_SCORE and short_score > long_score + MIN_DIFF:
        return {
            "type": "SHORT",
            "rsi": rsi,
            "ma10": ma10,
            "ma30": ma30,
            "entry": last_close,
            "score": short_score,
        }

    return None
