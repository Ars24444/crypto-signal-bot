import time
import requests
import pandas as pd

# Get price history from Binance
def get_price_history(symbol, interval='1h', limit=5):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
    return df

# Check if TP1, TP2 or SL was hit within the next few hours
def check_trade_result(symbol, entry_low, entry_high, tp1, tp2, sl, hours_to_check=3):
    df = get_price_history(symbol, interval='1h', limit=hours_to_check)
    result = None
    for i in range(len(df)):
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']

        # For SHORT trade
        if low <= tp2:
            result = f"✅ TP2 Hit (within {i+1}h)"
            break
        elif low <= tp1:
            result = f"✅ TP1 Hit (within {i+1}h)"
            break
        elif high >= sl:
            result = f"❌ SL Hit (within {i+1}h)"
            break
    if not result:
        result = "⏳ No TP/SL Hit Yet"
    return result
