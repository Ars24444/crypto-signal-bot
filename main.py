import os
from flask import Flask
from keep_alive import keep_alive
from get_top_symbols import get_top_volatile_symbols
from get_symbols import get_klines
from telegram import Bot
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import pandas as pd
import datetime


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)


@app.route('/')
def home():
    return "I'm alive"


@app.route('/run', methods=['GET'])
def run_manual():
    try:
        send_signals()
        return "Signal sent", 200
    except Exception as e:
        return f"Error occurred: {e}", 200


def is_strong_move(df):
    sma10 = SMAIndicator(close=df['Close'], window=10).sma_indicator()
    sma30 = SMAIndicator(close=df['Close'], window=30).sma_indicator()
    rsi = RSIIndicator(close=df['Close'], window=14).rsi()

    avg_volume = df['Volume'].iloc[-11:-1].mean()
    current_volume = df['Volume'].iloc[-1]

    last_ma10 = sma10.iloc[-1]
    last_ma30 = sma30.iloc[-1]
    last_rsi = rsi.iloc[-1]
    price = df['Close'].iloc[-1]

    strong_long = (current_volume > 1.4 * avg_volume and last_ma10 > last_ma30
                   and 58 <= last_rsi <= 75 and price > last_ma10)

    strong_short = (current_volume > 1.4 * avg_volume and last_ma10 < last_ma30
                    and 25 <= last_rsi <= 42 and price < last_ma10)

    return strong_long or strong_short


def analyze_symbol(symbol, df):
    sma10 = SMAIndicator(close=df['Close'], window=10).sma_indicator()
    sma30 = SMAIndicator(close=df['Close'], window=30).sma_indicator()
    rsi = RSIIndicator(close=df['Close'], window=14).rsi()

    last_ma10 = sma10.iloc[-1]
    last_ma30 = sma30.iloc[-1]
    last_rsi = rsi.iloc[-1]
    price = df['Close'].iloc[-1]

    message = f"{symbol} (1h)\nRSI: {last_rsi:.2f}\nMA10: {last_ma10:.2f}, MA30: {last_ma30:.2f}\n"

    if last_ma10 > last_ma30 and last_rsi > 60:
        entry_low = price * 0.98
        entry_high = price
        tp1 = price * 1.04
        tp2 = price * 1.08
        sl = price * 0.97
        message += f"Signal: LONG\nEntry: {entry_low:.4f} – {entry_high:.4f}\nTP1: {tp1:.4f}\nTP2: {tp2:.4f}\nSL: {sl:.4f}"
        return message

    elif last_ma10 < last_ma30 and last_rsi < 40:
        entry_low = price
        entry_high = price * 1.02
        tp1 = price * 0.96
        tp2 = price * 0.92
        sl = price * 1.03
        message += f"Signal: SHORT\nEntry: {entry_low:.4f} – {entry_high:.4f}\nTP1: {tp1:.4f}\nTP2: {tp2:.4f}\nSL: {sl:.4f}"
        return message

    return None


def get_strong_symbols():
    symbols = get_top_volatile_symbols(limit=50)
    strong = []

    for symbol in symbols:
        df = get_klines(symbol)
        if df is None or len(df) < 30:
            continue
        if is_strong_move(df):
            strong.append((symbol, df))
        if len(strong) >= 8:
            break

    return strong


def send_signals():
    strong_symbols = get_strong_symbols()

    if not strong_symbols:
        from datetime import timedelta
        now = datetime.datetime.now(datetime.timezone(timedelta(hours=4)))
        message = f"[{now.strftime('%H:%M')}] No strong signals found."
        bot.send_message(chat_id=CHAT_ID, text=message)
        return

    for symbol, df in strong_symbols:
        try:
            signal = analyze_symbol(symbol, df)
            if signal:
                bot.send_message(chat_id=CHAT_ID, text=signal)
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
