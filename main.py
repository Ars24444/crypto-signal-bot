import os
import threading
from flask import Flask
from telegram import Bot

from run_signal_logic import send_signals
from generate_summary import generate_summary
from signal_logger import send_winrate_to_telegram
from fast_signal_bot import send_fast_signals


# ================= ENV CONFIG =================
TELEGRAM_BOT_TOKEN = "8388716002:AAGyOsF_t3ciOtjugKNQX2e5t7R3IxLWte4"
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)


# ================= ROUTES =================
@app.route("/", methods=["GET"])
def home():
    return "🟢 Flask is working!", 200


@app.route("/run", methods=["GET"])
def run_signals_route():
    # 1H SIGNALS (աշխատում է :00-ին cron-ով)
    threading.Thread(
        target=send_signals,
        daemon=True
    ).start()
    return "✅ 1H Signal execution started!", 200


@app.route("/run-fast", methods=["GET"])
def run_fast_signals_route():
    # FAST / SCALPING BOT (եթե օգտագործվում է)
    threading.Thread(
        target=send_fast_signals,
        daemon=True
    ).start()
    return "⚡ FAST bot started!", 200


@app.route("/send-summary", methods=["GET"])
def send_summary():
    try:
        message = generate_summary()
        bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )
        return "📤 Summary sent", 200
    except Exception as e:
        return f"❌ Error: {e}", 500


@app.route("/winrate", methods=["GET"])
def winrate():
    try:
        threading.Thread(
            target=send_winrate_to_telegram,
            daemon=True
        ).start()
        return "📊 Winrate sent!", 200
    except Exception as e:
        return f"❌ Error: {e}", 500


# ================= ENTRY POINT =================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
