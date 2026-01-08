from flask import Flask
from threading import Thread
from run_signal_logic import send_signals

app = Flask(__name__)


@app.route("/")
def home():
    return "🟢 Bot is alive", 200


@app.route("/run")
def run_manual():
    try:
        Thread(
            target=send_signals,
            kwargs={"force": True},
            daemon=True
        ).start()

        return "✅ Signal execution started", 200

    except Exception as e:
        return f"❌ Error occurred: {e}", 500


def keep_alive():
    Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=8080,
            debug=False,
            use_reloader=False
        ),
        daemon=True
    ).start()
