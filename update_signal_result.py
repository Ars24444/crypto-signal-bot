import json
import os

def update_signal_result(symbol, signal_time_ms, result, filepath="signal_results.json"):
    if not os.path.exists(filepath):
        return

    with open(filepath, "r") as f:
        data = json.load(f)

    for item in data:
        if (
            item["symbol"] == symbol and
            abs(item["signal_time_ms"] - signal_time_ms) < 60_000  # 1 րոպե տարբերություն թույլ ենք տալիս
        ):
            item["result"] = result
            break

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
