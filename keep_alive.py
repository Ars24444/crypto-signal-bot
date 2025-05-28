from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive"

@app.route('/run')
def run_manual():
    try:
        from main import send_signals
        send_signals()
        return "Signal sent"
    except Exception as e:
        return f"Error occurred: {e}"

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()
