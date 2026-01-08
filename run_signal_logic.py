import os
from datetime import datetime

from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from data_fetcher import get_data, get_data_15m, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from signal_logger import log_sent_signal
from blacklist_manager import is_blacklisted, get_blacklist_reason
from utils import is_strong_signal


# ================= CONFIG =================
TELEGRAM_BOT_TOKEN = "8388716002:AAGyOsF_t3ciOtjugKNQX2e5t7R3IxLWte4"
CHAT_ID = 5398864436

DEBUG = True

bot = Bot(token=TELEGRAM_BOT_TOKEN)


# ================= MAIN SIGNAL FUNCTION =================
def send_signals(force: bool = False):
    now = datetime.utcnow()

    # ✅ TELEGRAM TEST MESSAGE (ԱՄԵՆԱԿԱՐԵՎՈՐԸ)
    try:
        bot.send_message(
            chat_id=CHAT_ID,
            text=f"🟢 Bot is alive\n/run triggered\nUTC time: {now.strftime('%H:%M')}",
        )
    except Exception as e:
        print("❌ Telegram test message failed:", e, flush=True)

    print("🚀 Signal scan started", flush=True)

    messages = []
    used_symbols = set()
    top_score = -1
    top_pick = None

    # ================= BTC FILTER =================
    try:
        btc_df = get_data_15m("BTCUSDT")
        if btc_df is None or len(btc_df) < 40:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ BTC data unavailable")
            return

        btc_close = btc_df["close"]
        btc_rsi = RSIIndicator(btc_close, window=14).rsi().iloc[-1]

        btc_last = btc_close.iloc[-1]
        btc_prev = btc_close.iloc[-2]
        btc_change_pct = (btc_last - btc_prev) / btc_prev * 100

    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"❌ BTC load error: {e}")
        return

    # ================= SYMBOL LIST =================
    symbols = get_top_volatile_symbols(limit=200)
    active_symbols = get_active_usdt_symbols()

    # ================= SIGNAL SCAN =================
    for symbol in symbols:
        if symbol in used_symbols or not symbol.endswith("USDT") or symbol not in active_symbols:
            continue

        if is_blacklisted(symbol):
            continue

        df = get_data(symbol)
        if df is None or len(df) < 50:
            continue

        result = is_strong_signal(
            df,
            btc_change_pct=btc_change_pct,
            btc_rsi=btc_rsi,
            symbol=symbol,
        )

        if not result:
            continue

        signal = result["type"]
        entry = result["entry"]
        score = result["score"]
        rsi = result["rsi"]
        ma10 = result["ma10"]
        ma30 = result["ma30"]

        atr = AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        ).average_true_range().iloc[-1]

        if signal == "LONG":
            tp1 = round(entry + atr * 1.5, 4)
            tp2 = round(entry + atr * 2.5, 4)
            sl = round(entry - atr, 4)
        else:
            tp1 = round(entry - atr * 1.5, 4)
            tp2 = round(entry - atr * 2.5, 4)
            sl = round(entry + atr, 4)

        emoji = "🔥🔥🔥" if score >= 6 else "🔥"

        message = (
            f"{emoji} {symbol} (1H)\n\n"
            f"Signal: {signal}\n"
            f"Score: {score}/7\n"
            f"RSI: {rsi:.2f}\n"
            f"MA10: {ma10:.4f} | MA30: {ma30:.4f}\n\n"
            f"Entry: {entry:.4f}\n"
            f"TP1: {tp1}\n"
            f"TP2: {tp2}\n"
            f"SL: {sl}"
        )

        messages.append(message)
        used_symbols.add(symbol)

        if score > top_score:
            top_score = score
            top_pick = symbol

        if len(messages) >= 5:
            break

    # ================= TELEGRAM SEND =================
    if not messages:
        bot.send_message(
            chat_id=CHAT_ID,
            text="❌ No signals found. Bot scan completed.",
        )
        return

    for msg in messages:
        bot.send_message(chat_id=CHAT_ID, text=msg)


# ================= ENTRY POINT =================
if __name__ == "__main__":
    send_signals(force=True)
