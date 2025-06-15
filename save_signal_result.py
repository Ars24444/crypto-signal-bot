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
        "timestamp": datetime.utcnow().isoformat(),
        "result": None  # default value, later updated by update_signal_result
    }

    file_path = "signal_results.json"

    # Read existing data safely
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to read existing signal_results.json: {e}")
            data = []
    else:
        data = []

    # Append the new result
    data.append(result)

    # Save back to file
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Signal result saved: {symbol}")
    except Exception as e:
        print(f"❌ Failed to save signal result for {symbol}: {e}")
