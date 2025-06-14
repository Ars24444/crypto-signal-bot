import json
import os
from datetime import datetime

RESULTS_FILE = "results.json"

def log_trade_result(symbol, signal_type, result):
    data = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = []

    data.append({
        "symbol": symbol,
        "type": signal_type,
        "result": result,
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)
