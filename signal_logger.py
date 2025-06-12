import json
import os
import requests

LOG_FILE = "sent_signals_log.json"

TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"
CHAT_ID = 5398864436

def send_winrate_to_telegram(last_n=20):
    if not os.path.exists(LOG_FILE):
        print("❌ Log file not found.")
        return

    with open(LOG_FILE, "r") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            print("❌ Failed to read JSON log.")
            return

    if len(logs) == 0:
        print("📭 No signal logs to analyze.")
        return

    recent = logs[-last_n:]
    total = len(recent)

    tp1_hits = sum(1 for s in recent if s.get("result") == "TP1")
    tp2_hits = sum(1 for s in recent if s.get("result") == "TP2")
    sl_hits = sum(1 for s in recent if s.get("result") == "SL")
    no_hits = sum(1 for s in recent if s.get("result") == "NO HIT")

    wins = tp1_hits + tp2_hits
    win_rate = (wins / total) * 100 if total > 0 else 0

    message = (
        f"📊 *Last {total} Signals Performance*\n"
        f"✅ TP1: {tp1_hits} | 🏁 TP2: {tp2_hits} | ❌ SL: {sl_hits} | 🤷‍♂️ No Hit: {no_hits}\n"
        f"🏆 *Win Rate:* {win_rate:.2f}%"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("✅ Win rate sent to Telegram.")
    else:
        print(f"❌ Failed to send: {response.status_code} {response.text}")
