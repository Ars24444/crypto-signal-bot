import numpy as np
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator

DEBUG = True  # production-ում կարող ես դարձնել False


def has_minimum_long_short_trades(symbol):
    # placeholder, հետո կարող ես իրական logic դնել
    return True


def is_strong_signal(df, btc_change_pct=0, btc_rsi=50, symbol=None):
    # ================= BASIC CHECKS =================
    if df is None or len(df) < 40:
        if DEBUG:
            print(f"❌ {symbol} rejected: not enough candles", flush=True)
        return None

    if symbol and not has_minimum_long_short_trades(symbol):
        if DEBUG:
            print(f"❌ {symbol} rejected: low trade activity", flush=True)
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

    # ================= BTC FILTER =================
    allow_long = not (btc_change_pct < -0.7 or btc_rsi < 40)
    allow_short = not (btc_change_pct > 0.7 or btc_rsi > 60)

    if not allow_long and not allow_short:
        if DEBUG:
            print(
                f"❌ {symbol} rejected by BTC filter "
                f"(BTCΔ={btc_change_pct:.2f}%, BTC_RSI={btc_rsi:.1f})",
                flush=True,
            )
        return None

    # ================= SCORING =================
    def score_long():
        score = 0

        if last_close > ma10 > ma30:
            score += 2
        elif last_close > ma30:
            score += 1

        if 35 <= rsi <= 45:
            score += 2
        elif 30 <= rsi < 35 or 45 < rsi <= 50:
            score += 1

        if bullish_candles:
            score += 1

        if avg_volume > 0:
            if current_volume >= avg_volume * 1.15:
                score += 2
            elif current_volume >= avg_volume * 1.05:
                score += 1

        return score

    def score_short():
        score = 0

        if last_close < ma10 < ma30:
            score += 2
        elif last_close < ma30:
            score += 1

        if 55 <= rsi <= 65:
            score += 2
        elif 50 <= rsi < 55 or 65 < rsi <= 70:
            score += 1

        if bearish_candles:
            score += 1

        if avg_volume > 0:
            if current_volume >= avg_volume * 1.15:
                score += 2
            elif current_volume >= avg_volume * 1.05:
                score += 1

        return score

    long_score = score_long() if allow_long else -1
    short_score = score_short() if allow_short else -1

    if DEBUG:
        print(
            f"📊 {symbol} | LONG={long_score} SHORT={short_score} "
            f"| RSI={rsi:.1f} MA10={ma10:.4f} MA30={ma30:.4f} "
            f"| vol={current_volume:.0f}/{avg_volume:.0f} "
            f"| BTCΔ={btc_change_pct:.2f}% BTC_RSI={btc_rsi:.1f}",
            flush=True,
        )

    # ================= FINAL DECISION =================
    MIN_SCORE = 5
    MIN_DIFF = 1

    reasons = []

    if long_score < MIN_SCORE:
        reasons.append(f"LONG score too low ({long_score})")

    if short_score < MIN_SCORE:
        reasons.append(f"SHORT score too low ({short_score})")

    # --- both too weak ---
    if long_score < MIN_SCORE and short_score < MIN_SCORE:
        if DEBUG:
            print(
                f"❌ {symbol} rejected: low score "
                f"(LONG={long_score}, SHORT={short_score})",
                flush=True,
            )
        return {
            "type": "NONE",
            "long_score": long_score,
            "short_score": short_score,
            "reasons": reasons,
        }

    # --- accept LONG ---
    if long_score >= MIN_SCORE and long_score > short_score + MIN_DIFF:
        if DEBUG:
            print(f"🔥 {symbol} ACCEPTED: LONG score={long_score}", flush=True)
        return {
            "type": "LONG",
            "rsi": rsi,
            "ma10": ma10,
            "ma30": ma30,
            "entry": last_close,
            "score": long_score,
        }

    # --- accept SHORT ---
    if short_score >= MIN_SCORE and short_score > long_score + MIN_DIFF:
        if DEBUG:
            print(f"🔥 {symbol} ACCEPTED: SHORT score={short_score}", flush=True)
        return {
            "type": "SHORT",
            "rsi": rsi,
            "ma10": ma10,
            "ma30": ma30,
            "entry": last_close,
            "score": short_score,
        }

    # --- conflict ---
    reasons.append("Score conflict between LONG and SHORT")

    if DEBUG:
        print(
            f"❌ {symbol} rejected: score conflict "
            f"(LONG={long_score}, SHORT={short_score})",
            flush=True,
        )

    return {
        "type": "NONE",
        "long_score": long_score,
        "short_score": short_score,
        "reasons": reasons,
    }
