from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange

from data_fetcher import get_data_15m
from utils import is_strong_signal


def process_symbol_signal(symbol: str):
    """
    Մշակում է մեկ symbol-ի սիգնալը
    Օգտագործում է 15m data, is_strong_signal scoring,
    volume filter և ATR-ի վրա հիմնված TP/SL:
    Վերադարձնում է dict կամ None
    """

    try:
        df = get_data_15m(symbol)

        if df is None or len(df) < 80:
            return None

        # ====== Բաղադրիչներ ======
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        last_close = close.iloc[-1]

        # Բազային սիգնալ utils.py-ից
        signal_type, base_score = is_strong_signal(df)

        if signal_type is None or base_score < 3:
            return None

        # ====== Volume filter ======
        avg_vol = volume.iloc[-30:].mean()
        last_vol = volume.iloc[-1]

        if avg_vol == 0:
            return None

        vol_ratio = last_vol / avg_vol

        # Պահանջենք գոնե 1.15x միջինից
        if vol_ratio < 1.15:
            return None

        # Եթե շատ ուժեղ volume է, մի քիչ բոնուս տանք score-ին
        extra_score = 0
        if vol_ratio >= 1.5:
            extra_score += 1

        # ====== ATR հաշվարկ և TP/SL ======
        atr = AverageTrueRange(
            high=high,
            low=low,
            close=close,
            window=14
        ).average_true_range().iloc[-1]

        # Եթե ATR-ը անհասկանալի փոքր կամ մեծ է, ավելի լավ է skip անել
        if atr <= 0:
            return None

        # ATR multipliers – 11.11–ին մոտեցումն
        sl_mult = 1.5
        tp_mult = 2.2

        sl_distance = atr * sl_mult
        tp_distance = atr * tp_mult

        if signal_type == "LONG":
            sl = last_close - sl_distance
            tp = last_close + tp_distance
        else:  # SHORT
            sl = last_close + sl_distance
            tp = last_close - tp_distance

        # ====== Վերջնական score ======
        total_score = base_score + extra_score
        if total_score > 5:
            total_score = 5

        # Միայն ուժեղներն ենք վերադարձնում
        if total_score < 4:
            return None

        return {
            "symbol": symbol,
            "type": signal_type,
            "score": total_score,
            "tp": float(round(tp, 6)),
            "sl": float(round(sl, 6)),
        }

    except Exception as e:
        print(f"⚠️ Error in process_symbol_signal for {symbol}: {e}", flush=True)
        return None
