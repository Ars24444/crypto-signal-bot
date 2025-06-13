from flask import Flask
import threading
from telegram import Bot
from generate_summary import generate_summary

TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route("/send-summary", methods=["GET"])
def send_summary():
    try:
        message = generate_summary()
        bot.send_message(chat_id=CHAT_ID, text=message)
        return "📤 Summary sent", 200
    except Exception as e:
        return f"❌ Error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
