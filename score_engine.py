# score_engine.py

def calculate_signal_score(
    trend_15m,
    pullback_5m,
    volume_ok,
    rsi_5m,
    ma_clean,
    volatility_ok
):
    score = 0
    reasons = []

    if trend_15m:
        score += 3
        reasons.append("15m trend aligned")

    if pullback_5m:
        score += 2
        reasons.append("5m pullback")

    if volume_ok:
        score += 2
        reasons.append("Volume expansion")

    if 38 <= rsi_5m <= 62:
        score += 1
        reasons.append("RSI sweet zone")

    if ma_clean:
        score += 1
        reasons.append("Clean MA structure")

    if volatility_ok:
        score += 1
        reasons.append("Volatility OK")

    return score, reasons
