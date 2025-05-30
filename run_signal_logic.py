from utils import get_data, is_strong_signal
from get_top_symbols import get_top_volatile_symbols
from telegram import Bot
import os

TELEGRAM_TOKEN = '7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs'
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)

def send_signals(force=False):
    try:
        print("Signal function started")

        btc_df = get_data("BTCUSDT")
        btc_change_pct = (btc_df["close"].iloc[-1] - btc_df["close"].iloc[-4]) / btc_df["close"].iloc[-4] * 100

        symbols = get_top_volatile_symbols(limit=100)
        used_symbols = set()
        count = 0

        top_score = -1
        top_pick = None
        messages = []

        for symbol in symbols:
            if not symbol.endswith("USDT"):
                continue
            if symbol in used_symbols:
                continue

            print(f"Checking {symbol}")
            df = get_data(symbol)
            if df is None or len(df) < 50:
                print(f"{symbol} skipped due to insufficient data.")
                continue

            result = is_strong_signal(df, btc_change_pct)
            if not result:
                if not force:
                    print(f"{symbol} has no strong signal.")
                continue

            signal, rsi, ma10, ma30, entry = result

            score = 0
            if signal == "LONG":
                if ma10 > ma30: score += 1
                if rsi > 60: score += 1
            elif signal == "SHORT":
                if ma10 < ma30: score += 1
                if rsi < 40: score += 1

            if score > top_score:
                top_score = score
                top_pick = symbol

            entry_low = round(entry * 0.995, 4)
            entry_high = round(entry * 1.005, 4)
            tp1 = round(entry * (1.06 if signal == "LONG" else 0.94), 4)
            tp2 = round(entry * (1.1 if signal == "LONG" else 0.9), 4)
            sl = round(entry * (0.99 if signal == "LONG" else 1.01), 4)

            message = (
                f"📊 {symbol} (1h)\n"
                f"Signal: {signal}\n"
                f"RSI: {rsi:.2f}\n"
                f"MA10: {ma10:.2f}, MA30: {ma30:.2f}\n"
                f"Entry: {entry_low} – {entry_high}\n"
                f"TP1: {tp1}\n"
                f"TP2: {tp2}\n"
                f"SL: {sl}"
            )

            messages.append((symbol, message))
            used_symbols.add(symbol)
            count += 1

            if count >= 8:
                break

        if count > 0:
            for symbol, msg in messages:
                if symbol == top_pick:
                    msg = "🔝 TOP PICK\n" + msg
                bot.send_message(chat_id=CHAT_ID, text=msg)
        else:
            bot.send_message(chat_id=CHAT_ID, text="📭 No strong signals found. Market is calm.")

    except Exception as e:
        print(f"❌ ERROR in send_signals: {e}")
