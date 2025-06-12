import json
import time
import os
import threading

BLACKLIST_FILE = "blacklist.json"
BLACKLIST_DURATION = 6 * 60 * 60  # 6 hours
_lock = threading.Lock()

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
    blacklist[symbol] = {
        "time": int(time.time()),
        "reason": reason
    }
    save_blacklist(blacklist)
    print(f"🚫 Added {symbol} to blacklist for {BLACKLIST_DURATION // 3600}h | Reason: {reason}")

def is_blacklisted(symbol):
    blacklist = load_blacklist()
    if symbol not in blacklist:
        return False
    entry = blacklist[symbol]
    if isinstance(entry, dict):
        elapsed = time.time() - entry.get("time", 0)
    else:
        # fallback for old format
        elapsed = time.time() - entry
    if elapsed > BLACKLIST_DURATION:
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
