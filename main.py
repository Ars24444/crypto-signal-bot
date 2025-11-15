from flask import Flask
import threading
from telegram import Bot

from run_signal_logic import send_signals
from generate_summary import generate_summary
from signal_logger import send_winrate_to_telegram

TELEGRAM_TOKEN = "7842956033:AAGK_mRt_ADxZg3rbD82DAFQCb5X9AL0Wv8"
CHAT_ID = 5398864436                      

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)  # ✅ OK

@app.route("/", methods=["GET"])
def home():
    return "🟢 Flask is working!", 200

@app.route("/run", methods=["GET"])
def run_signals_route():
    # ⬆️ անունը փոխեցի, որ չբացատվի send_signals ֆունկցիայի հետ
    threading.Thread(target=send_signals).start()  # ✅ async
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

if name == "__main__":  # ✅ OK
    app.run(host="0.0.0.0", port=10000)
