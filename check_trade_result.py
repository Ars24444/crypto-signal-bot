import requests
from blacklist_manager import add_to_blacklist  
from result_logger import log_trade_result
from update_signal_result import update_signal_result  

# ✅ Fetch 1-minute candles after signal timestamp
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
        print(f"❌ Error fetching 1m data for {symbol}")
        return []

    return data

# ✅ Determine result: TP1, TP2, SL, or NO HIT
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
                    print(f"❌ {symbol} (LONG): SL hit")
                    update_signal_result(symbol, signal_time_ms, "SL")
                    add_to_blacklist(symbol, reason="SL_hit")
                    log_trade_result(symbol, signal_type, "SL")
                    return "SL"
                if high >= tp2:
                    print(f"✅ {symbol} (LONG): TP2 hit")
                    update_signal_result(symbol, signal_time_ms, "TP2")
                    log_trade_result(symbol, signal_type, "TP2")
                    return "TP2"
                if high >= tp1:
                    tp1_hit = True

            elif signal_type == "SHORT":
                if high >= sl:
                    print(f"❌ {symbol} (SHORT): SL hit")
                    update_signal_result(symbol, signal_time_ms, "SL")
                    add_to_blacklist(symbol, reason="SL_hit")
                    log_trade_result(symbol, signal_type, "SL")
                    return "SL"
                if low <= tp2:
                    print(f"✅ {symbol} (SHORT): TP2 hit")
                    update_signal_result(symbol, signal_time_ms, "TP2")
                    log_trade_result(symbol, signal_type, "TP2")
                    return "TP2"
                if low <= tp1:
                    tp1_hit = True

        if tp1_hit:
            print(f"✅ {symbol}: TP1 hit")
            update_signal_result(symbol, signal_time_ms, "TP1")
            log_trade_result(symbol, signal_type, "TP1")
            return "TP1"

        print(f"📭 {symbol}: No hit")
        update_signal_result(symbol, signal_time_ms, "NO HIT")
        log_trade_result(symbol, signal_type, "NO_HIT")
        return "NO HIT"

    except Exception as e:
        print(f"❌ Error checking result for {symbol}: {e}")
        return "ERROR"
