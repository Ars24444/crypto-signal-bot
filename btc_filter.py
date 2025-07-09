from data_fetcher import get_data

def check_btc_influence(btc_change_pct, signal_type="LONG"):
    """
    Checks whether the current BTC market trend supports the given signal direction.
    Returns True if market is neutral or supportive; False if trend contradicts the signal.
    """
    try:
        btc_df = get_data("BTCUSDT", interval="15m", limit=10)
        if btc_df is None or len(btc_df) < 10:
            print("⚠️ BTC data unavailable for filter.")
            return True  # Allow signal if BTC data is missing

        start_price = btc_df["open"].iloc[0]
        end_price = btc_df["close"].iloc[-1]
        btc_change_pct = (end_price - start_price) / start_price * 100

        print(f"📉 BTC 2.5h Change: {btc_change_pct:.2f}%")

        # ✅ Allow signal if BTC is calm
        if abs(btc_change_pct) < 0.6:
            return True

        # ❌ Block SHORT if BTC is going UP strongly
        if btc_change_pct >= 0.6 and signal_type == "SHORT":
            print("❌ Rejected due to BTC uptrend conflicting with SHORT signal.")
            return False

        # ❌ Block LONG if BTC is going DOWN strongly
        if btc_change_pct <= -0.6 and signal_type == "LONG":
            print("❌ Rejected due to BTC downtrend conflicting with LONG signal.")
            return False

        return True

    except Exception as e:
        print("❌ BTC influence filter error:", e)
        return True  # Fail-safe: allow signal
