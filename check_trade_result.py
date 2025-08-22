import requests
from blacklist_manager import add_to_blacklist
from result_logger import log_trade_result
from update_signal_result import update_signal_result

PRIORITY_SL_FIRST = True  

def get_1m_data(symbol, start_time_ms, minutes=360):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1m", "startTime": int(start_time_ms), "limit": int(minutes)}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            print(f"❌ get_1m_data {symbol}: HTTP {r.status_code} -> {r.text[:120]}")
            return []
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"❌ get_1m_data {symbol} error: {e}")
        return []

def _touched_zone(low, high, zlow, zhigh):
    return not (high < zlow or low > zhigh)

def check_trade_result(symbol, signal_type, entry, tp1, tp2, sl, signal_time_ms):
    # entry կարող է լինել float կամ (low, high)
    if isinstance(entry, (list, tuple)) and len(entry) == 2:
        entry_low, entry_high = float(entry[0]), float(entry[1])
    else:
        entry_low = entry_high = float(entry)

    candles = get_1m_data(symbol, signal_time_ms, minutes=360)
    if not candles:
        print(f"📭 {symbol}: NO DATA")
        update_signal_result(symbol, signal_time_ms, "NO DATA")
        log_trade_result(symbol, signal_type, "NO_DATA")
        return "NO DATA"

    entered = False
    tp1_hit = False

    for c in candles:
        high = float(c[2]); low = float(c[3])

        # 1) սպասում ենք մինչև գինը մտնի Entry Zone
        if not entered:
            if _touched_zone(low, high, entry_low, entry_high):
                entered = True
                continue
            else:
                continue

        # 2) ներսում ենք՝ ստուգումներ ըստ հերթականության
        if signal_type == "LONG":
            checks = [("SL", low <= sl), ("TP2", high >= tp2), ("TP1", high >= tp1)]
            if not PRIORITY_SL_FIRST:
                checks = [("TP2", high >= tp2), ("TP1", high >= tp1), ("SL", low <= sl)]
        else:  # SHORT
            checks = [("SL", high >= sl), ("TP2", low <= tp2), ("TP1", low <= tp1)]
            if not PRIORITY_SL_FIRST:
                checks = [("TP2", low <= tp2), ("TP1", low <= tp1), ("SL", high >= sl)]

        for label, cond in checks:
            if not cond:
                continue
            if label == "SL":
                if tp1_hit:
                    print(f"🟡 {symbol}: TP1 earlier, later SL -> keep TP1")
                    update_signal_result(symbol, signal_time_ms, "TP1")
                    log_trade_result(symbol, signal_type, "TP1")
                    return "TP1"
                print(f"❌ {symbol} ({signal_type}): SL hit")
                update_signal_result(symbol, signal_time_ms, "SL")
                add_to_blacklist(symbol, reason="SL_hit")
                log_trade_result(symbol, signal_type, "SL")
                return "SL"
            if label == "TP2":
                print(f"✅ {symbol} ({signal_type}): TP2 hit")
                update_signal_result(symbol, signal_time_ms, "TP2")
                log_trade_result(symbol, signal_type, "TP2")
                return "TP2"
            if label == "TP1":
                tp1_hit = True

    if tp1_hit:
        print(f"✅ {symbol}: TP1 hit (no TP2 later)")
        update_signal_result(symbol, signal_time_ms, "TP1")
        log_trade_result(symbol, signal_type, "TP1")
        return "TP1"

    print(f"📭 {symbol}: No hit")
    update_signal_result(symbol, signal_time_ms, "NO HIT")
    log_trade_result(symbol, signal_type, "NO_HIT")
    return "NO HIT"
