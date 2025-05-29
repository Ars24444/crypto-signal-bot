import pandas as pd
from get_symbols import get_klines
from get_top_symbols import get_top_volatile_symbols
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from telegram import Bot

CHAT_ID = 5398864436
TELEGRAM_TOKEN = '7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs'
bot = Bot(token=TELEGRAM_TOKEN)

def is_strong_signal(df):
    sma10 = SMAIndicator(close=df['Close'], window=10).sma_indicator()
    sma30 = SMAIndicator(close=df['Close'], window=30).sma_indicator()
    rsi = RSIIndicator(close=df['Close'], window=14).rsi()

    avg_volume = df['Volume'].iloc[-111:-1].mean()
    current_volume = df['Volume'].iloc[-1]
    last_ma10 = sma10.iloc[-1]
    last_ma30 = sma30.iloc[-1]
    last_rsi = rsi.iloc[-1]
    price = df['Close'].iloc[-1]

    long_condition = current_volume > 1.4 * avg_volume and last_ma10 > last_ma30 and last_rsi > 65
    short_condition = current_volume > 1.4 * avg_volume and last_ma10 < last_ma30 and last_rsi < 35

    if long_condition:
        return "LONG", last_rsi, last_ma10, last_ma30, price
    elif short_condition:
        return "SHORT", last_rsi, last_ma10, last_ma30, price
    else:
        return None

def send_signals():
    symbols = get_top_volatile_symbols(limit=15)
    used_symbols = set()
    count = 0

    for symbol in symbols:
        if symbol in used_symbols:
            continue

        df = get_klines(symbol)
        if df is None or len(df) < 50:
            continue

        result = is_strong_signal(df)
        if not result:
            continue

        signal, rsi, ma10, ma30, entry = result

        tp1 = round(entry * (1.06 if signal == "LONG" else 0.94), 4)
        tp2 = round(entry * (1.1 if signal == "LONG" else 0.9), 4)
        sl = round(entry * (0.99 if signal == "LONG" else 1.01), 4)
        entry_low = round(entry * 0.995, 4)
        entry_high = round(entry * 1.005, 4)

        message = f"""{symbol} (1h)
RSI: {rsi:.2f}
MA10: {ma10:.2f}, MA30: {ma30:.2f}
Signal: {signal}
Entry: {entry_low} – {entry_high}
TP1: {tp1}
TP2: {tp2}
SL: {sl}"""

        bot.send_message(chat_id=CHAT_ID, text=message)
        used_symbols.add(symbol)
        count += 1
        if count >= 8:
            break

    if count == 0:
        print("No strong signals found")
