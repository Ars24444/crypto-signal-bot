# volume_filter.py
from ta.trend import SMAIndicator
from ta.volatility import AverageTrueRange
import pandas as pd

def volume_filter(df: pd.DataFrame):
    """
    Returns (ok: bool, reason: str, bonus: int)
    """
    try:
        if df is None or len(df) < 50:
            return False, "insufficient data", 0

        v = df["volume"].astype(float)
        c = df["close"].astype(float)
        h = df["high"].astype(float)
        l = df["low"].astype(float)

        vol_sma20 = SMAIndicator(v, window=20).sma_indicator().iloc[-1]
        recent3_vol = v.iloc[-3:].mean()
        if vol_sma20 <= 0:
            return False, "vol_sma20 <= 0", 0

        ratio = recent3_vol / vol_sma20
        atr14 = AverageTrueRange(h, l, c, window=14).average_true_range().iloc[-1]
        last_range = float(h.iloc[-1] - l.iloc[-1])

        vol_ok = ratio >= 1.25
        expansion_ok = last_range >= 0.8 * atr14

        if not vol_ok:
            return False, f"volume weak (ratio={ratio:.2f})", 0
        if not expansion_ok:
            return False, f"range too small vs ATR ({last_range:.6f} < {0.8*atr14:.6f})", 0

        bonus = 1 if ratio >= 1.6 and last_range >= 1.0 * atr14 else 0
        return True, f"volume ok (ratio={ratio:.2f})", bonus

    except Exception as e:
        return False, f"volume filter error: {e}", 0
