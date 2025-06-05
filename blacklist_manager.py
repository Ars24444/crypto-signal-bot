import json
import time
import os

BLACKLIST_FILE = "blacklist.json"
BLACKLIST_DURATION = 6 * 60 * 60  # 6 hours in seconds

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return {}
    with open(BLACKLIST_FILE, "r") as f:
        return json.load(f)

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(blacklist, f)

def add_to_blacklist(symbol):
    blacklist = load_blacklist()
    blacklist[symbol] = int(time.time())
    save_blacklist(blacklist)

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
