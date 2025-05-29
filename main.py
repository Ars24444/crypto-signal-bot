from flask import Flask
import threading

from run_signal_logic import send_signals  # ✅ bring signal logic from new file

app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive"

@app.route('/run')
def run_manual():
    try:
        threading.Thread(target=send_signals).start()
        return "Started", 200
    except Exception as e:
        return f"Error occurred: {e}", 500

if __name__ == '__main__':
    app.run()
