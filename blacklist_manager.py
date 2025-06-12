import json
import time
import os
import threading

BLACKLIST_FILE = "blacklist.json"
_lock = threading.Lock()

# Duration in seconds for each reason
REASON_DURATIONS = {
    "SL_hit": 2 * 60 * 60,         # 2 hours
    "multiple_SL": 4 * 60 * 60,    # 4 hours
    "scam_like": 6 * 60 * 60,      # 6 hours
    "manual": 12 * 60 * 60,        # 12 hours
    "Unknown": 1 * 60 * 60         # default 1 hour
}

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return {}
    with _lock:
        try:
            with open(BLACKLIST_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load blacklist: {e}")
            return {}

def save_blacklist(blacklist):
    with _lock:
        try:
            with open(BLACKLIST_FILE, "w") as f:
                json.dump(blacklist, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save blacklist: {e}")

def add_to_blacklist(symbol, reason="Unknown"):
    blacklist = load_blacklist()
    duration = REASON_DURATIONS.get(reason, REASON_DURATIONS["Unknown"])
    
    blacklist[symbol] = {
        "time": int(time.time()),
        "reason": reason,
        "duration": duration
    }
    save_blacklist(blacklist)
    print(f"🚫 Added {symbol} to blacklist for {duration // 3600}h | Reason: {reason}")

def is_blacklisted(symbol):
    blacklist = load_blacklist()
    if symbol not in blacklist:
        return False
    entry = blacklist[symbol]
    elapsed = time.time() - entry.get("time", 0)
    duration = entry.get("duration", REASON_DURATIONS["Unknown"])

    if elapsed > duration:
        print(f"🧹 Removed {symbol} from blacklist (expired)")
        del blacklist[symbol]
        save_blacklist(blacklist)
        return False
    return True

def get_blacklist_reason(symbol):
    data = load_blacklist()
    if symbol in data and isinstance(data[symbol], dict):
        return data[symbol].get("reason", "Unknown")
    return None
