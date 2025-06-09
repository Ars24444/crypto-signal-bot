import requests
import pandas as pd

def check_trade_result(symbol, signal_type, entry, tp1, tp2, sl, interval='1h', candles_to_check=3):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": candles_to_check
        }
        response = requests.get(url, params=params)
        data = response.json()

        for candle in data:
            high = float(candle[2])
            low = float(candle[3])

            if signal_type == "LONG":
                # Check if SL is hit first
                if low <= sl:
                    return "SL"
                # Then check TP2 and TP1
                elif high >= tp2:
                    return "TP2"
                elif high >= tp1:
                    return "TP1"

            elif signal_type == "SHORT":
                if high >= sl:
                    return "SL"
                elif low <= tp2:
                    return "TP2"
                elif low <= tp1:
                    return "TP1"

        return "NO HIT"
    except Exception as e:
        print(f"Error checking result for {symbol}: {e}")
        return "ERROR"
