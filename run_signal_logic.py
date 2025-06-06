from utils import get_data, is_strong_signal, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from blacklist_manager import is_blacklisted, add_to_blacklist
from check_trade_result import check_trade_result
import os

TELEGRAM_TOKEN = '7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs'
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)
def send_signals(force=False):
    print("Signal function started")

    btc_df = get_data("BTCUSDT")
    btc_change_pct = (btc_df["close"].iloc[-1] - btc_df["close"].iloc[-4]) / btc_df["close"].iloc[-4] * 100
    btc_rsi = RSIIndicator(btc_df["close"]).rsi().iloc[-1]

    symbols = get_top_volatile_symbols(limit=100)
    active_usdt_symbols = get_active_usdt_symbols()
    used_symbols = set()
    count = 0

    top_score = -1
    top_pick = None
    messages = []

    for symbol in symbols:
        if is_blacklisted(symbol) or not symbol.endswith("USDT") or symbol not in active_usdt_symbols or symbol in used_symbols:
            continue

        df = get_data(symbol)
        if df is None or len(df) < 50:
            continue

        result = is_strong_signal(df, btc_change_pct, btc_rsi, symbol=symbol)
        print("✅ Raw result:", result)

        # Skip if score < 4 or signal is None or not LONG/SHORT
        if (
            not result or
            result["score"] < 4 or
            result["type"] not in ["LONG", "SHORT"]
        ):
            print(f"{symbol} skipped due to weak score or missing signal: {result}")
            continue

        signal = result["type"]
        entry = result["entry"]
        tp1 = result["tp1"]
        tp2 = result["tp2"]
        sl = result["sl"]
        score = result["score"]
        rsi = result["rsi"]
        ma10 = result["ma10"]
        ma30 = result["ma30"]

        emoji = "🔥🔥🔥" if score == 5 else "🔥"

        if score > top_score:
            top_score = score
            top_pick = symbol

        entry_low = round(entry * 0.995, 4)
        entry_high = round(entry * 1.005, 4)

        atr = AverageTrueRange(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            window=14
        ).average_true_range().iloc[-1]

        if signal == "LONG":
            sl = round(entry_high * 0.985, 4)
            tp1 = round(entry + atr, 4)
            tp2 = round(entry + 2 * atr, 4)
        else:
            sl = round(entry_low * 1.015, 4)
            tp1 = round(entry - atr, 4)
            tp2 = round(entry - 2 * atr, 4)

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

        trade_result = check_trade_result(
            symbol=symbol,
            entry_low=entry_low,
            entry_high=entry_high,
            tp1=tp1,
            tp2=tp2,
            sl=sl,
            hours_to_check=3
        )
        if trade_result.startswith("❌ SL"):
            add_to_blacklist(symbol)

        if count >= 8:
            break

    try:
        if messages:
            for symbol, msg in messages:
                if symbol == top_pick:
                    msg = "🔝 TOP PICK\n" + msg
                print(f"📤 Sending signal for {symbol}:\n{msg}\n")
                bot.send_message(chat_id=CHAT_ID, text=msg)
        else:
            print("📭 No strong signals found. Market is calm.")
            bot.send_message(chat_id=CHAT_ID, text="📩 No strong signals found. Market is calm.")
    except Exception as e:
        print("ERROR in send_signals:", e)
