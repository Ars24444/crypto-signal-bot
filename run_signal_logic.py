from utils import get_klines, get_top_volatile_symbols, is_strong_signal
from telegram import Bot
import os

TELEGRAM_TOKEN = '7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs'
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)
def send_signals():
    try:
        print("Signal function started")
        
        symbols = get_top_volatile_symbols(limit=30)
        used_symbols = set()
        count = 0

        for symbol in symbols:
            if not symbol.endswith("USDT"):
                continue
            if symbol in used_symbols:
                continue

            print(f"Checking {symbol}")
            df = get_klines(symbol)
            if df is None or len(df) < 50:
                print(f"{symbol} skipped due to insufficient data.")
                continue

            result = is_strong_signal(df)
            if not result:
                print(f"{symbol} has no strong signal.")
                continue

            signal, rsi, ma10, ma30, entry = result
            tp1 = round(entry * (1.06 if signal == "LONG" else 0.94), 4)
            tp2 = round(entry * (1.1 if signal == "LONG" else 0.9), 4)
            sl = round(entry * (0.99 if signal == "LONG" else 1.01), 4)
            entry_low = round(entry * 0.995, 4)
            entry_high = round(entry * 1.005, 4)

            message = f"""📊 {symbol} (1h)
RSI: {rsi:.2f}
MA10: {ma10:.2f}, MA30: {ma30:.2f}
Signal: {signal}
Entry: {entry_low} – {entry_high}
TP1: {tp1}
TP2: {tp2}
SL: {sl}"""

            bot.send_message(chat_id=CHAT_ID, text=message)
            print(f"Sent signal for {symbol} ({signal})")

            used_symbols.add(symbol)
            count += 1
            if count >= 8:
                break

        if count == 0:
            print("No strong signals found")

    except Exception as e:
        print(f"❌ ERROR in send_signals: {e}")

