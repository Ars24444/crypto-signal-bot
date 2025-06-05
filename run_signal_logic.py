from utils import get_data, is_strong_signal, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from telegram import Bot
from blacklist_manager import is_blacklisted, add_to_blacklist
from check_trade_result import check_trade_result
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
        active_usdt_symbols = get_active_usdt_symbols()
        used_symbols = set()
        count = 0

        top_score = -1
        top_pick = None
        messages = []

        for symbol in symbols:
            if is_blacklisted(symbol):
                print(f"{symbol} is temporarily blacklisted")
                continue
            if not symbol.endswith("USDT"):
                continue
            if symbol not in active_usdt_symbols:
                print(f"{symbol} is not active — skipping.")
                continue
            if symbol in used_symbols:
                continue

            print(f"Checking {symbol}")
            df = get_data(symbol)
            if df is None or len(df) < 50:
                print(f"{symbol} skipped due to insufficient data.")
                continue

            result = is_strong_signal(df, btc_change_pct, symbol=symbol)
            if not result:
                if not force:
                    print(f"{symbol} has no strong signal.")
                continue

            signal, rsi, ma10, ma30, entry, score = result

            # Add emoji based on score
            if score == 5:
                emoji = "🔥🔥🔥"
            elif score == 4:
                emoji = "🔥"
            else:
                emoji = "⚠️"

            if score > top_score:
                top_score = score
                top_pick = symbol

            entry_low = round(entry * 0.995, 4)
            entry_high = round(entry * 1.005, 4)
            tp1 = round(entry * (1.06 if signal == "LONG" else 0.94), 4)
            tp2 = round(entry * (1.1 if signal == "LONG" else 0.9), 4)
            sl = round(entry * (0.99 if signal == "LONG" else 1.01), 4)

            message = (
                f"{emoji} {symbol} (1h)\n"
                f"Signal: {signal}\n"
                f"Score: {score}/5\n"
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

            # ✅ Check TP/SL result and blacklist if SL hit
            trade_result = check_trade_result(
                symbol=symbol,
                entry_low=entry_low,
                entry_high=entry_high,
                tp1=tp1,
                tp2=tp2,
                sl=sl,
                hours_to_check=3
            )
            print(f"{symbol} result: {trade_result}")
            if trade_result.startswith("❌ SL"):
                add_to_blacklist(symbol)

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
