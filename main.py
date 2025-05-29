from flask import Flask
from run_signal_logic import send_signals
import sys
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "I'm alive"

@app.route("/run")
def run_manual():
    try:
        print("➡️ Entered /run route")
        sys.stdout.flush()

        send_signals()

        print("✅ Finished send_signals()")
        sys.stdout.flush()

        return "Started", 200
    except Exception as e:
        print(f"❌ Error in /run route: {e}")
        sys.stdout.flush()
        return f"Error occurred: {e}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
