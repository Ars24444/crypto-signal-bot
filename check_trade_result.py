import requests

def get_1m_data(symbol, start_time, minutes=180):
    url = "https://api.binance.com/api/v3/klines"
    interval = "1m"
    limit = minutes

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "limit": limit
    }

    response = requests.get(url, params=params)
    data = response.json()

    if not isinstance(data, list):
        print("❌ Error fetching 1m data")
        return []

    return data

def check_trade_result(symbol, signal_type, entry, tp1, tp2, sl, signal_time_ms):
    try:
        candles = get_1m_data(symbol, signal_time_ms, minutes=180)

        tp1_hit = False
        tp2_hit = False

        for candle in candles:
            high = float(candle[2])
            low = float(candle[3])

            if signal_type == "LONG":
                if low <= sl:
                    return "SL"
                if high >= tp2:
                    return "TP2"
                if high >= tp1:
                    tp1_hit = True

            elif signal_type == "SHORT":
                if high >= sl:
                    return "SL"
                if low <= tp2:
                    return "TP2"
                if low <= tp1:
                    tp1_hit = True

        if tp1_hit:
            return "TP1"

        return "NO HIT"

    except Exception as e:
        print(f"❌ Error checking result with 1m for {symbol}: {e}")
        return "ERROR"
