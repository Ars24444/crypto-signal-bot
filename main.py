from flask import Flask
import threading
from run_signal_logic import send_signals
send_signals(force=True)
from check_signal_result_runner import check_recent_signal_results

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "🟢 Crypto Signal Bot is online.", 200

@app.route("/run", methods=["GET"])
def run():
    threading.Thread(target=send_signals).start()
    return "✅ Signal execution started!", 200

@app.route("/check_result", methods=["GET"])
def check_result():
    threading.Thread(target=check_recent_signal_results).start()
    return "✅ Trade result check started!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
