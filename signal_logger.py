import json
import os
from datetime import datetime

LOG_FILE = "sent_signals_log.json"

def log_sent_signal(symbol, data, result="NO HIT"):
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        "symbol": symbol,
        "timestamp": timestamp,
        "type": data["type"],
        "entry": data["entry"],
        "tp1": data["tp1"],
        "tp2": data["tp2"],
        "sl": data["sl"],
        "result": result
    }

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def get_recent_signals(minutes=60):
    from datetime import timedelta
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            return []

    recent = []
    for entry in logs:
        entry_time = datetime.strptime(entry["timestamp"], '%Y-%m-%d %H:%M:%S')
        if entry_time > cutoff_time:
            recent.append(entry)
    return recent
