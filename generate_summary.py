import json
import time
from datetime import datetime

def generate_summary(filepath="sent_signals_log.json"):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return "📭 No results file found."
    except json.JSONDecodeError:
        return "⚠️ Error reading results file."

    now = time.time()
    three_hours_ago = now - 3 * 3600

    recent = []
    for d in data:
        try:
            timestamp = datetime.fromisoformat(d.get("timestamp")).timestamp()
            if timestamp >= three_hours_ago:
                recent.append(d)
        except Exception:
            continue

    total = len(recent)
    tp1 = sum(1 for d in recent if d.get("result") == "TP1")
    tp2 = sum(1 for d in recent if d.get("result") == "TP2")
    sl  = sum(1 for d in recent if d.get("result") == "SL")

    if total == 0:
        return "📭 No recent signals to summarize in the last 3 hours."

    winrate = ((tp1 + tp2) / total) * 100

    return (
        f"📊 Last {total} Signals Performance\n"
        f"✅ TP1: {tp1} | 🏁 TP2: {tp2} | ❌ SL: {sl} | 🤷‍♂️ No Hit: {total - tp1 - tp2 - sl}\n"
        f"🏆 Win Rate: {winrate:.2f}%"
    )
