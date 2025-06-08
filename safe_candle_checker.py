def is_safe_last_candle(df, signal_type="LONG"):
    if df is None or len(df) < 2:
        return False

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Calculate candle size and body size
    candle_size = last['high'] - last['low']
    body_size = abs(last['close'] - last['open'])
    upper_wick = last['high'] - max(last['close'], last['open'])
    lower_wick = min(last['close'], last['open']) - last['low']

    # Avoid long top wick in LONG signals
    if signal_type == "LONG":
        if upper_wick > body_size * 1.5:
            return False

    # Avoid long bottom wick in SHORT signals
    if signal_type == "SHORT":
        if lower_wick > body_size * 1.5:
            return False

    # Avoid extremely large candles (e.g., pumps)
    avg_candle_size = (df['high'] - df['low']).iloc[-20:-1].mean()
    if candle_size > 2.5 * avg_candle_size:
        return False

    return True
