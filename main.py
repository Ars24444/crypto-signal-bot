from flask import Flask
import threading
from run_signal_logic import send_signals

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "🟢 Crypto Signal Bot is online. Use /run to start.", 200

@app.route("/run", methods=["GET"])
def run():
    threading.Thread(target=send_signals).start()
    return "✅ Signal execution started!", 200

if name == "__main__":
    app.run(host="0.0.0.0", port=10000)
