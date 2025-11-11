from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

def check_btc_influence_df(btc_df, side: str):
    """
    side: 'LONG' or 'SHORT'
    Returns (allow: bool, reason: str, bonus: int)
      - allow=False → block the signal
      - bonus ∈ {0,1} → add 1 extra point to score if BTC strongly supports the signal
    """
    try:
        if btc_df is None or len(btc_df) < 20:
            return True, "BTC data missing – allow", 0

        closes = btc_df["close"].astype(float)
        rsi = float(RSIIndicator(closes, window=14).rsi().iloc[-1])
        ema10 = float(EMAIndicator(closes, window=10).ema_indicator().iloc[-1])
        ema30 = float(EMAIndicator(closes, window=30).ema_indicator().iloc[-1])

        # last ~2 hours (8 × 15m candles)
        win = 8 if len(closes) >= 9 else len(closes) - 1
        change_pct = (closes.iloc[-1] - closes.iloc[-1 - win]) / closes.iloc[-1 - win] * 100.0

        # 1) Calm zone → allow
        if abs(change_pct) < 0.4:
            return True, f"BTC calm ({change_pct:.2f}%)", 0

        # 2) Shock guard → block if last candle moves >1.2%
        last_ret = (closes.iloc[-1] / closes.iloc[-2] - 1.0) * 100.0
        if abs(last_ret) > 1.2:
            return False, f"BTC shock move {last_ret:.2f}%", 0

        # 3) Directional guardrails (RSI + trend + direction)
        if side == "LONG":
            if change_pct <= -0.6 or rsi >= 70 or ema10 < ema30:
                return False, f"Block LONG: Δ{change_pct:.2f}% | RSI {rsi:.1f} | EMA10<EMA30={ema10<ema30}", 0
        else:  # SHORT
            if change_pct >= 0.6 or rsi <= 30 or ema10 > ema30:
                return False, f"Block SHORT: Δ{change_pct:.2f}% | RSI {rsi:.1f} | EMA10>EMA30={ema10>ema30}", 0

        # 4) Alignment bonus (add +1 if BTC trend strongly matches)
        bonus = 0
        if side == "LONG" and change_pct > 0 and ema10 > ema30 and 40 <= rsi <= 65:
            bonus = 1
        if side == "SHORT" and change_pct < 0 and ema10 < ema30 and 35 <= rsi <= 60:
            bonus = 1

        return True, f"BTC align Δ{change_pct:.2f}% | RSI {rsi:.1f}", bonus

    except Exception as e:
        return True, f"BTC filter error: {e}", 0
