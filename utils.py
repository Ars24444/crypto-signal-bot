from flask import Flask
import threading
from telegram import Bot
from generate_summary import generate_summary
from signal_logger import send_winrate_to_telegram

TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)  # ✅ FIXED HERE

@app.route("/", methods=["GET"])
def home():
    return "🟢 Flask is working!", 200

@app.route("/run", methods=["GET"])
def run_signals():
    threading.Thread(target=send_signals).start()  # ✅ optional for async behavior
    return "✅ Signal execution started!", 200

@app.route("/send-summary", methods=["GET"])
def send_summary():
    try:
        message = generate_summary()
        bot.send_message(chat_id=CHAT_ID, text=message)
        return "📤 Summary sent", 200
    except Exception as e:
        return f"❌ Error: {e}", 500

@app.route("/winrate", methods=["GET"])
def winrate():
    try:
        threading.Thread(target=send_winrate_to_telegram).start()
        return "✅ Winrate sent!", 200
    except Exception as e:
        return f"❌ Error: {e}", 500
 def is_strong_signal(rsi, ma10, ma30, volume_spike, safe_candle):
    """
    Returns True եթե սիգնալը ուժեղ է, այլ դեպքում False.
    """
    try:
        return (
            rsi >= 60 and
            ma10 > ma30 and
            volume_spike and
            safe_candle
        )
    except Exception as e:
        print(f"❌ is_strong_signal error: {e}")
        return False       
        
if __name__ == "__main__":  # ✅ FIXED HERE TOO
    app.run(host="0.0.0.0", port=10000)
