import json
import os

def update_signal_result(symbol, signal_time_ms, result, filepath="signal_results.json"):
    if not os.path.exists(filepath):
        print("⚠️ signal_results.json file not found.")
        return

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read {filepath}: {e}")
        return

    updated = False
    for item in data:
        if (
            item.get("symbol") == symbol and
            abs(item.get("signal_time_ms", 0) - signal_time_ms) < 60_000  # 1 րոպե տարբերություն
        ):
            item["result"] = result
            updated = True
            break

    if updated:
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
            print(f"✅ Updated result for {symbol}: {result}")
        except Exception as e:
            print(f"❌ Failed to write to {filepath}: {e}")
    else:
        print(f"⚠️ No matching signal found to update for {symbol}")
