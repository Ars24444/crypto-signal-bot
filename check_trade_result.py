import json
import os
from utils import get_data
from telegram import Bot

TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)

def check_trade_result():
    if not os.path.exists("signal_log.json"):
        print("No signal log found.")
        return

    with open("signal_log.json", "r") as f:
        signals = json.load(f)

    results = []

    for symbol, info in signals.items():
        if info.get("checked"):
            continue  # Already checked

        df = get_data(symbol)
        if df is None or len(df) < 2:
            continue

        future_df = df.iloc[-2:]  # check last 2 candles
        high = future_df["high"].max()
        low = future_df["low"].min()

        entry = info["entry"]
        tp1 = info["tp1"]
        tp2 = info["tp2"]
        sl = info["sl"]
        signal_type = info["type"]

        result = "❓ Unknown"
        if signal_type == "LONG":
            if sl != 0 and low <= sl:
                result = "❌ SL hit"
            elif tp2 != 0 and high >= tp2:
                result = "🏁 TP2 hit"
            elif tp1 != 0 and high >= tp1:
                result = "✅ TP1 hit"
        elif signal_type == "SHORT":
            if sl != 0 and high >= sl:
                result = "❌ SL hit"
            elif tp2 != 0 and low <= tp2:
                result = "🏁 TP2 hit"
            elif tp1 != 0 and low <= tp1:
                result = "✅ TP1 hit"

        text = f"📊 {symbol} (1h) Result: {result}\nEntry: {entry}, TP1: {tp1}, TP2: {tp2}, SL: {sl}"
        print(text)
        bot.send_message(chat_id=CHAT_ID, text=text)

        signals[symbol]["checked"] = True  # Mark as checked

    with open("signal_log.json", "w") as f:
        json.dump(signals, f, indent=2)
