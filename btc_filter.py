from data_fetcher import get_data


BTC_CALM_THRESHOLD = 0.6   # %
BTC_LOOKBACK_CANDLES = 10 # 15m × 10 = ~2.5h


def check_btc_influence(signal_type="LONG"):
    """
    Checks whether BTC trend supports the given signal direction.
    Returns True if BTC is calm or aligned; False if BTC contradicts signal.
    """

    try:
        btc_df = get_data("BTCUSDT", interval="15m", limit=BTC_LOOKBACK_CANDLES)
        if btc_df is None or len(btc_df) < BTC_LOOKBACK_CANDLES:
            print("⚠️ BTC data unavailable for influence filter — allowing signal.")
            return True

        start_price = float(btc_df["open"].iloc[0])
        end_price = float(btc_df["close"].iloc[-1])
        btc_change_pct = (end_price - start_price) / start_price * 100

        print(f"🟠 BTC ~2.5h change: {btc_change_pct:.2f}%")

        # ✅ BTC calm → allow all
        if abs(btc_change_pct) < BTC_CALM_THRESHOLD:
            return True

        # ❌ BTC strong UP → block SHORT
        if btc_change_pct >= BTC_CALM_THRESHOLD and signal_type == "SHORT":
            print("❌ BTC uptrend blocks SHORT signal")
            return False

        # ❌ BTC strong DOWN → block LONG
        if btc_change_pct <= -BTC_CALM_THRESHOLD and signal_type == "LONG":
            print("❌ BTC downtrend blocks LONG signal")
            return False

        return True

    except Exception as e:
        print("❌ BTC influence filter error:", e)
        return True  # Fail-safe
