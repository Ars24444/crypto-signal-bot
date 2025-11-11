def safe_candle_ok(df, signal_type="LONG"):
    if df is None or len(df) < 20:
        return False

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Calculate candle properties
    candle_size = last['high'] - last['low']
    body_size = abs(last['close'] - last['open'])
    upper_wick = last['high'] - max(last['close'], last['open'])
    lower_wick = min(last['close'], last['open']) - last['low']

    # Avoid LONG entries with long upper wick
    if signal_type == "LONG" and upper_wick > body_size * 1.5:
        print("❌ Rejected LONG: long upper wick")
        return False

    # Avoid SHORT entries with long lower wick
    if signal_type == "SHORT" and lower_wick > body_size * 1.5:
        print("❌ Rejected SHORT: long lower wick")
        return False

    # Reject if candle is abnormally large (possible manipulation/pump)
    avg_candle_size = (df['high'] - df['low']).iloc[-20:-1].mean()
    if candle_size > 2.5 * avg_candle_size:
        print("❌ Rejected: abnormal candle size")
        return False

    return True
