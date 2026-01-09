import os
from datetime import datetime

from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from data_fetcher import get_data, get_data_15m, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from blacklist_manager import is_blacklisted
from score_engine import calculate_signal_score
from btc_filter import btc_allows_trade


# ================= CONFIG =================
TELEGRAM_BOT_TOKEN = "8388716002:AAGyOsF_t3ciOtjugKNQX2e5t7R3IxLWte4"
CHAT_ID = 5398864436

DEBUG = True
bot = Bot(token=TELEGRAM_BOT_TOKEN)


# ================= MAIN SIGNAL FUNCTION =================
def send_signals(force: bool = False):
    now = datetime.utcnow()

    # Telegram alive message
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

    # ================= BTC DATA CHECK =================
    btc_df = get_data_15m("BTCUSDT")
    if btc_df is None or len(btc_df) < 50:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ BTC data unavailable")
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

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # ===== Indicators =====
        rsi_5m = RSIIndicator(close, window=14).rsi().iloc[-1]

        ma10 = close.rolling(10).mean().iloc[-1]
        ma30 = close.rolling(30).mean().iloc[-1]

        trend_15m_ok = ma10 > ma30
        ma_structure_ok = ma10 > ma30

        volume_ok = volume.iloc[-1] > volume.rolling(20).mean().iloc[-1] * 1.3

        atr_series = AverageTrueRange(high, low, close, window=14).average_true_range()
        atr = atr_series.iloc[-1]
        atr_ma = atr_series.rolling(20).mean().iloc[-1]
        atr_ok = atr < atr_ma * 1.5

        # simple pullback (Step 3-ում կխստացնենք)
        pullback_confirmed = close.iloc[-1] > ma10 and close.iloc[-2] < ma10

        # ===== SCORE ENGINE =====
        score, reasons = calculate_signal_score(
            trend_15m=trend_15m_ok,
            pullback_5m=pullback_confirmed,
            volume_ok=volume_ok,
            rsi_5m=rsi_5m,
            ma_clean=ma_structure_ok,
            volatility_ok=atr_ok
        )

        if score < 8:
            if DEBUG:
                print(f"{symbol} REJECTED | SCORE {score} | {reasons}", flush=True)
            continue

        # ===== SIGNAL DIRECTION =====
        signal = "LONG" if trend_15m_ok else "SHORT"

        # ===== BTC MASTER FILTER =====
        btc_ok, btc_reason = btc_allows_trade(signal)
        if not btc_ok:
            if DEBUG:
                print(f"{symbol} REJECTED | BTC FILTER | {btc_reason}", flush=True)
            continue

        # ===== ENTRY & TARGETS =====
        entry = close.iloc[-1]

        if signal == "LONG":
            tp1 = round(entry * 1.025, 4)
            tp2 = round(entry * 1.05, 4)
            sl = round(entry * 0.99, 4)
        else:
            tp1 = round(entry * 0.975, 4)
            tp2 = round(entry * 0.95, 4)
            sl = round(entry * 1.01, 4)

        message = (
            f"🔥🔥 A+ SIGNAL (1H)\n\n"
            f"{symbol}\n"
            f"Direction: {signal}\n"
            f"Score: {score}/10\n\n"
            f"Entry: {entry:.4f}\n"
            f"TP1: {tp1}\n"
            f"TP2: {tp2}\n"
            f"SL: {sl}\n\n"
            f"Reason:\n- " + "\n- ".join(reasons)
        )

        messages.append(message)
        used_symbols.add(symbol)

        if len(messages) >= 5:
            break

    # ================= TELEGRAM SEND =================
    if not messages:
        bot.send_message(
            chat_id=CHAT_ID,
            text="❌ No A+ signals found. BTC or market conditions not ideal.",
        )
        return

    for msg in messages:
        bot.send_message(chat_id=CHAT_ID, text=msg)
