# pump_detector.py

import pandas as pd


def is_pump_signal(
    df: pd.DataFrame,
    volume_lookback: int = 30,
    volume_multiplier: float = 3.0,
    body_ratio: float = 0.6,
    min_change_pct: float = 0.015,  # ≥ 1.5% աճ վերջին մոմում
    ma_fast: int = 5,
    ma_mid: int = 10,
    ma_slow: int = 30,
):
    """
    Վերադարձնում է (is_pump: bool, info: dict)

    df – 1m կամ 5m timeframe,
    պարտադիր սյունակներ՝ 'open', 'high', 'low', 'close', 'volume'
    """

    # բավարար քանդլների քանակ
    min_len = max(50, volume_lookback + 2, ma_slow + 2)
    if df is None or len(df) < min_len:
        return False, {"reason": "not_enough_candles", "len": len(df) if df is not None else 0}

    last = df.iloc[-1]

    # 1) Volume spike
    vol_window = df["volume"].iloc[-(volume_lookback + 1):-1]
    avg_vol = vol_window.mean()
    last_vol = last["volume"]

    vol_spike = last_vol > avg_vol * volume_multiplier

    # 2) Strong green candle
    candle_size = last["high"] - last["low"]
    body = last["close"] - last["open"]

    is_green = body > 0
    big_body = candle_size > 0 and body >= candle_size * body_ratio

    price_change_pct = 0.0
    if last["open"] > 0:
        price_change_pct = (last["close"] - last["open"]) / last["open"]

    enough_change = price_change_pct >= min_change_pct

    strong_candle = is_green and big_body and enough_change

    # 3) MA explosion (MA5 > MA10 > MA30, բոլորը աճի մեջ)
    closes = df["close"]

    ma_fast_series = closes.rolling(ma_fast).mean()
    ma_mid_series = closes.rolling(ma_mid).mean()
    ma_slow_series = closes.rolling(ma_slow).mean()

    ma_f = ma_fast_series.iloc[-1]
    ma_m = ma_mid_series.iloc[-1]
    ma_s = ma_slow_series.iloc[-1]

    ma_f_prev = ma_fast_series.iloc[-2]
    ma_m_prev = ma_mid_series.iloc[-2]
    ma_s_prev = ma_slow_series.iloc[-2]

    ma_order = ma_f > ma_m > ma_s
    ma_rising = (ma_f > ma_f_prev) and (ma_m > ma_m_prev) and (ma_s > ma_s_prev)

    ma_explosion = ma_order and ma_rising

    is_pump = vol_spike and strong_candle and ma_explosion

    info = {
        "vol_spike": bool(vol_spike),
        "last_vol": float(last_vol),
        "avg_vol": float(avg_vol),
        "strong_candle": bool(strong_candle),
        "price_change_pct": float(price_change_pct),
        "ma_explosion": bool(ma_explosion),
        "ma_fast": float(ma_f),
        "ma_mid": float(ma_m),
        "ma_slow": float(ma_s),
    }

    return is_pump, info


def build_pump_long_trade(
    df: pd.DataFrame,
    tp1_pct: float = 0.05,   # +5%
    tp2_pct: float = 0.10,   # +10%
    sl_lookback: int = 5,    # վերջին 5 մոմի low-երից մինիմում
):
    """
    Վերադարձնում է LONG trade-ի պարամետրերը.
    {
        "entry": ...,
        "tp1": ...,
        "tp2": ...,
        "sl": ...
    }
    """
    last = df.iloc[-1]
    entry = float(last["close"])

    tp1 = entry * (1 + tp1_pct)
    tp2 = entry * (1 + tp2_pct)

    recent_lows = df["low"].iloc[-(sl_lookback + 1):-1]
    sl = float(recent_lows.min())

    return {
        "entry": entry,
        "tp1": float(tp1),
        "tp2": float(tp2),
        "sl": sl,
    }
