import json
import time
import os

RESULTS_FILE = "signal_results.json"

def save_result(symbol, signal_type, entry, tp1, tp2, sl, result):
    data = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    data.append({
        "symbol": symbol,
        "type": signal_type,
        "entry": entry,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "result": result,
        "timestamp": time.time()
    })

    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)
