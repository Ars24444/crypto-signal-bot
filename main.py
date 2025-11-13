import os
import time
from datetime import datetime

from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from data_fetcher import get_data, get_data_15m, get_active_usdt_symbols
from run_signal_logic import process_symbol_signal
from signal_logger import log_sent_signal
from save_signal_result import save_signal_result
from blacklist_manager import is_blacklisted
from utils import btc_filter_pass

TELEGRAM_TOKEN = "7842956033:AAGK_mRt_ADxZg3rbD82DAFQCb5X9AL0Wv8"
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)


def send_signals(force=False):
    print("🚀 Starting signal scan...", flush=True)

    # BTC FILTER
    btc_pass, btc_reason = btc_filter_pass(force=force)
    if not btc_pass:
        print(f"⛔️ BTC filter blocked signals: {btc_reason}", flush=True)
        return {"status": "blocked", "reason": btc_reason}

    # Load symbols
    print("📌 Loading active USDT symbols...", flush=True)
    symbols = get_active_usdt_symbols()
    if not symbols:
        print("❌ No symbols fetched!")
        return {"status": "error", "details": "symbols empty"}

    strong_signals = []

    for symbol in symbols:
        try:
            if is_blacklisted(symbol):
                continue

            result = process_symbol_signal(symbol)

            if result and result["score"] >= 4:
                strong_signals.append(result)

        except Exception as e:
            print(f"⚠️ Error scanning {symbol}: {e}", flush=True)
            continue

    if not strong_signals:
        print("😐 No strong signals found.")
        return {"status": "no_signals"}

    # SORT BY SCORE
    strong_signals.sort(key=lambda x: x["score"], reverse=True)

    sent = 0

    for signal in strong_signals[:5]:  # send top 5
        try:
            text = (
                f"📈 *{signal['symbol']} — {signal['type']}*\n"
                f"Score: {signal['score']}/5\n"
                f"Time: {datetime.utcnow()}\n\n"
                f"TP/SL: {signal['tp']}/{signal['sl']}"
            )

            bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode="Markdown"
            )

            log_sent_signal(signal["symbol"], signal["type"], signal["score"])

            save_signal_result(
                signal["symbol"],
                signal["type"],
                "SENT"
            )

            sent += 1
            time.sleep(1)

        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}", flush=True)
            continue

    print(f"✅ Signals sent: {sent}", flush=True)
    return {"status": "done", "sent": sent}
