import json
import os
from datetime import datetime

RESULTS_FILE = "results.json"

def log_trade_result(symbol, signal_type, result):
    data = []

    # Load existing results
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load results.json: {e}")
            data = []

    # Append new result
    data.append({
        "symbol": symbol,
        "type": signal_type,
        "result": result,
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Save back to file
    try:
        with open(RESULTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to write to results.json: {e}")
