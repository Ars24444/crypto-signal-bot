from utils import get_data

def check_btc_influence(signal_type="LONG"):
    
    try:
        btc_df = get_data("BTCUSDT", interval="15m", limit=10)
        if btc_df is None or len(btc_df) < 10:
            print("⚠️ BTC data unavailable for filter.")
            return True  

        start_price = btc_df["open"].iloc[0]
        end_price = btc_df["close"].iloc[-1]
        btc_change_pct = (end_price - start_price) / start_price * 100

        print(f"📉 BTC 2h Change: {btc_change_pct:.2f}%")

        if abs(btc_change_pct) < 0.6:
            return True  # neutral

        if btc_change_pct >= 0.6 and signal_type == "SHORT":
            print("❌ Rejected due to BTC uptrend conflicting with SHORT signal.")
            return False

        if btc_change_pct <= -0.6 and signal_type == "LONG":
            print("❌ Rejected due to BTC downtrend conflicting with LONG signal.")
            return False

        return True

    except Exception as e:
        print("❌ BTC influence filter error:", e)
        return True
