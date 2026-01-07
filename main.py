from flask import Flask
import threading
from telegram import Bot

from run_signal_logic import send_signals
from generate_summary import generate_summary
from signal_logger import send_winrate_to_telegram
from fast_signal_bot import send_fast_signals

TELEGRAM_BOT_TOKEN=8388716002:AAGy0sF_t3ciOtjugKNQ2e5t7R3IxlWte4
CHAT_ID=5398864436


bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "🟢 Flask is working!", 200


@app.route("/run", methods=["GET"])
def run_signals_route():
    threading.Thread(target=send_signals).start()
    return "✅ Signal execution started!", 200


@app.route("/run-fast", methods=["GET"])
def run_fast_signals_route():
    threading.Thread(target=send_fast_signals).start()
    return "✅ FAST bot started!", 200


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
