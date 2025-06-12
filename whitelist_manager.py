import json
import os
import threading

WHITELIST_FILE = "whitelist.json"
_lock = threading.Lock()

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return set()
    with _lock:
        try:
            with open(WHITELIST_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()

def save_whitelist(whitelist):
    with _lock:
        try:
            with open(WHITELIST_FILE, "w") as f:
                json.dump(list(whitelist), f, indent=2)
        except:
            pass

def add_to_whitelist(symbol):
    whitelist = load_whitelist()
    whitelist.add(symbol)
    save_whitelist(whitelist)
    print(f"🌟 Added {symbol} to whitelist (TP2 hit)")

def is_whitelisted(symbol):
    return symbol in load_whitelist()
