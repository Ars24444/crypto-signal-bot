import os
import time
from datetime import datetime

from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from data_fetcher import get_data, get_data_15m, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from signal_logger import log_sent_signal
from save_signal_result import save_signal_result
from check_trade_result import check_trade_result
from blacklist_manager import is_blacklisted, add_to_blacklist, get_blacklist_reason
from utils import is_strong_signal

TELEGRAM_TOKEN = "7842956033:AAGK_mRt_ADxZg3rbD82DAFQCb5X9AL0Wv8"
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)

def send_signals(force=False):
    print("🚀 Signal function started", flush=True)

    try:
        print("🔍 Loading BTC data...", flush=True)
        btc_df = get_data_15m("BTCUSDT")

        if btc_df is None:
            print("❌ Failed to load BTC data", flush=True)
            return {"status": "error", "details": "BTC data fetch failed"}

        print("📊 BTC data loaded. Checking filters...", flush=True)

        # BTC TREND FILTER
        btc_rsi = RSIIndicator(btc_df["close"], window=14).rsi().iloc[-1]
        btc_change = (btc_df["close"].iloc[-1] - btc_df["close"].iloc[-2]) / btc_df["close"].iloc[-2] * 100

        if not force:
            if btc_rsi > 75 or btc_rsi < 25:
                print("⛔️ BTC RSI filter blocked signals", flush=True)
                return {"blocked": "btc_rsi"}

            if abs(btc_change) > 3:
                print("⛔️ BTC % change filter blocked signals", flush=True)
                return {"blocked": "btc_change"}

        print("⚡️ Fetching active USDT symbols...", flush=True)
        symbols = get_active_usdt_symbols()

        if not symbols:
            print("❌ No symbols fetched", flush=True)
            return {"no_symbols": True}

        print(f"📌 Total symbols fetched: {len(symbols)}", flush=True)

        strong_signals = []

        for symbol in symbols:
            try:
                if is_blacklisted(symbol):
                    continue

                df = get_data(symbol)

                if df is None or len(df) < 70:
                    continue

                signal_type, score = is_strong_signal(df)

                if signal_type is not None:
                    strong_signals.append((symbol, signal_type, score))

            except Exception as e:
                print(f"⚠️ Error processing {symbol}: {e}", flush=True)
                continue

        if not strong_signals:
            print("😐 No strong signals found", flush=True)
            return {"signals": 0}

        print(f"🔥 Strong signals found: {len(strong_signals)}", flush=True)

        # SORT BY SCORE
        strong_signals.sort(key=lambda x: x[2], reverse=True)

        sent_counter = 0

        for symbol, signal_type, score in strong_signals[:5]:
            try:
                msg = f"📈 *{symbol} – {signal_type}*\nScore: {score}/5\nTime: {datetime.utcnow()}"

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=msg,
                    parse_mode="Markdown"
                )

                log_sent_signal(symbol, signal_type, score)
                save_signal_result(symbol, signal_type, "SENT")

                sent_counter += 1

                time.sleep(1)

            except Exception as e:
                print(f"❌ Failed to send message for {symbol}: {e}", flush=True)
                continue

        print(f"✅ Signals sent: {sent_counter}", flush=True)
        return {"sent": sent_counter}

    except Exception as e:
        print(f"🔥 Global error in send_signals: {e}", flush=True)
        return {"error": str(e)}
