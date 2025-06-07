import time
import requests
import pandas as pd

def get_price_history(symbol, interval='1h', limit=5):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        return df
    except Exception as e:
        print(f"⚠️ Error fetching price history for {symbol}: {e}")
        return None

def check_trade_result(symbol, entry_low, entry_high, tp1, tp2, sl, hours_to_check=3):
    df = get_price_history(symbol, interval='1h', limit=hours_to_check)
    if df is None or len(df) == 0:
        return "⚠️ No data to check"

    is_short = tp1 < entry_low and tp2 < tp1  # crude logic to detect short vs long

    for i in range(len(df)):
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']

        if is_short:
            if low <= tp2:
                return f"✅ TP2 Hit (within {i+1}h)"
            elif low <= tp1:
                return f"✅ TP1 Hit (within {i+1}h)"
            elif high >= sl:
                return f"❌ SL Hit (within {i+1}h)"
        else:
            if high >= tp2:
                return f"✅ TP2 Hit (within {i+1}h)"
            elif high >= tp1:
                return f"✅ TP1 Hit (within {i+1}h)"
            elif low <= sl:
                return f"❌ SL Hit (within {i+1}h)"

    return "⏳ No TP/SL Hit Yet"
