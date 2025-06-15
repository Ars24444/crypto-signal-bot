import json

def generate_winrate(filepath="signal_results.json", lookback=20):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return "📭 No results file found."
    except json.JSONDecodeError:
        return "⚠️ Error reading results file."

    recent = data[-lookback:] if len(data) >= lookback else data
    total = len(recent)
    if total == 0:
        return "📭 No recent signals found."

    tp1 = sum(1 for d in recent if d.get("result") == "TP1")
    tp2 = sum(1 for d in recent if d.get("result") == "TP2")
    sl  = sum(1 for d in recent if d.get("result") == "SL")
    wins = tp1 + tp2

    winrate = (wins / total) * 100 if total > 0 else 0

    return (
        f"📊 Last {total} signals:\n"
        f"✅ TP1 hit: {tp1}\n"
        f"💥 TP2 hit: {tp2}\n"
        f"🛑 SL hit: {sl}\n"
        f"🎯 Winrate: {winrate:.1f}%"
    )
