from flask import Flask
from threading import Thread
from run_signal_logic import send_signals  # ✔️ import from logic, not from main

app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Bot is alive"

@app.route('/run')
def run_manual():
    try:
        send_signals(force=True)
        return "✅ Signal sent"
    except Exception as e:
        return f"❌ Error occurred: {e}"

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()
