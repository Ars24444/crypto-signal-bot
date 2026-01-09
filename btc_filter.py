# btc_filter.py

from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from data_fetcher import get_data_15m


def btc_allows_trade(direction: str):
    """
    Master BTC filter.
    Returns (bool, reason)
    """

    try:
        btc_df = get_data_15m("BTCUSDT")
        if btc_df is None or len(btc_df) < 50:
            return False, "BTC data unavailable"

        close = btc_df["close"]
        high = btc_df["high"]
        low = btc_df["low"]

        # ===== Indicators =====
        rsi = RSIIndicator(close, window=14).rsi().iloc[-1]

        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]

        atr_series = AverageTrueRange(high, low, close, window=14).average_true_range()
        atr = atr_series.iloc[-1]
        atr_ma = atr_series.rolling(20).mean().iloc[-1]

        last_candle_pct = abs((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)

        # ===== HARD BLOCKS =====
        if rsi > 70 or rsi < 30:
            return False, "BTC RSI extreme"

        if atr > atr_ma * 1.5:
            return False, "BTC volatility spike"

        if last_candle_pct > 1.2:
            return False, "BTC sudden candle"

        # ===== TREND DIRECTION =====
        if direction == "LONG":
            if ema20 <= ema50:
                return False, "BTC trend against LONG"
            if not (45 <= rsi <= 60):
                return False, "BTC RSI not ideal for LONG"

        if direction == "SHORT":
            if ema20 >= ema50:
                return False, "BTC trend against SHORT"
            if not (40 <= rsi <= 55):
                return False, "BTC RSI not ideal for SHORT"

        return True, "BTC OK"

    except Exception as e:
        return False, f"BTC filter error: {e}"
