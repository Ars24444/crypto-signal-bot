import os
from datetime import datetime
from telegram import Bot

from signal_logger import get_recent_signals
from check_trade_result import check_trade_result


# ================= CONFIG =================
TELEGRAM_TOKEN = "8388716002:AAGyOsF_t3ciOtjugKNQX2e5t7R3IxLWte4"
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)


def check_recent_signal_results():
    print("📊 Checking recent signal results...", flush=True)

    recent_signals = get_recent_signals(minutes=60)

    if not recent_signals:
        msg = "📭 No recent signals to check (last 60 min)."
        print(msg)
        bot.send_message(chat_id=CHAT_ID, text=msg)
        return

    results = []
    success = 0
    fail = 0
    pending = 0

    for signal in recent_signals:
        try:
            ts = signal.get("timestamp")
            if not ts:
                continue

            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"⚠️ Invalid timestamp format: {ts}")
                continue

            signal_time_ms = int(dt.timestamp() * 1000)

            result = check_trade_result(
                symbol=signal["symbol"],
                signal_type=signal["type"],
                entry=signal["entry"],
                tp1=signal["tp1"],
                tp2=signal["tp2"],
                sl=signal["sl"],
                signal_time_ms=signal_time_ms,
            )

            if result == "TP1" or result == "TP2":
                success += 1
            elif result == "SL":
                fail += 1
            else:
                pending += 1

            results.append(
                f"{signal['symbol']} {signal['type']} → {result}"
            )

        except Exception as e:
            print(f"❌ Error checking {signal.get('symbol')}: {e}", flush=True)

    # ================= SUMMARY MESSAGE =================
    message = (
        "🧪 Signal Results (last 60 min)\n\n"
        f"✅ Wins: {success}\n"
        f"❌ Losses: {fail}\n"
        f"⏳ Pending: {pending}\n\n"
        "Details:\n"
        + "\n".join(results[:15])  # limit spam
    )

    bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )
