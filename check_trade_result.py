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

        highs = [float(candle[2]) for candle in data]
        lows = [float(candle[3]) for candle in data]

        for high, low in zip(highs, lows):
            if signal_type == "LONG":
                if low <= sl:
                    return "SL"
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
        return "UNKNOWN"
    except Exception as e:
        print(f"Error checking result for {symbol}: {e}")
        return "ERROR"
