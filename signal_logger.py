import json
import os

def log_sent_signal(symbol, signal_info):
    filename = "signal_log.json"

    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[symbol] = {
        "type": signal_info["type"],
        "entry": signal_info["entry"],
        "tp1": signal_info["tp1"],
        "tp2": signal_info["tp2"],
        "sl": signal_info["sl"],
        "checked": False
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
