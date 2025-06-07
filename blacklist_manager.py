import json
import time
import os
import threading

BLACKLIST_FILE = "blacklist.json"
BLACKLIST_DURATION = 6 * 60 * 60  # 6 hours in seconds
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
                json.dump(blacklist, f)
        except Exception as e:
            print(f"⚠️ Failed to save blacklist: {e}")

def add_to_blacklist(symbol):
    blacklist = load_blacklist()
    blacklist[symbol] = int(time.time())
    save_blacklist(blacklist)
    print(f"🚫 Added {symbol} to blacklist for {BLACKLIST_DURATION//3600}h")

def is_blacklisted(symbol):
    blacklist = load_blacklist()
    if symbol not in blacklist:
        return False
    elapsed = time.time() - blacklist[symbol]
    if elapsed > BLACKLIST_DURATION:
        del blacklist[symbol]
        save_blacklist(blacklist)
        return False
    return True
