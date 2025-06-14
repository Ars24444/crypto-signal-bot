import json
import os
from datetime import datetime

def save_signal_result(symbol, signal_type, entry_zone, tp1, tp2, sl, signal_time_ms):
    result = {
        "symbol": symbol,
        "signal_type": signal_type,
        "entry_zone": entry_zone,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "signal_time_ms": signal_time_ms,
        "timestamp": datetime.utcnow().isoformat()
    }

    file_path = "signal_results.json"

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(result)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
