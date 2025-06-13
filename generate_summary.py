import json
import time

def generate_summary(filepath="signal_results.json"):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return "📭 No results file found."
    except json.JSONDecodeError:
        return "⚠️ Error reading results file."

    three_hours_ago = time.time() - 3 * 3600
    recent = [d for d in data if d.get("timestamp", 0) >= three_hours_ago]
    total = len(recent)
    tp1 = sum(1 for d in recent if d.get("result") == "TP1")
    tp2 = sum(1 for d in recent if d.get("result") == "TP2")
    sl  = sum(1 for d in recent if d.get("result") == "SL")

    if total == 0:
        return "📭 No recent signals to summarize in the last 3 hours."

    winrate = ((tp1 + tp2) / total) * 100

    return (
        f"📊 Signal Summary (Last 3h)\n"
        f"✅ TP1 hit: {tp1}\n"
        f"💥 TP2 hit: {tp2}\n"
        f"🛑 SL hit: {sl}\n"
        f"🎯 Winrate: {winrate:.1f}%"
    )
