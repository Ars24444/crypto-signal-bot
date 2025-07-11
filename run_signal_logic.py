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

TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"
CHAT_ID = 5398864436
bot = Bot(token=TELEGRAM_TOKEN)

def send_signals(force=False):
    print("🚀 Signal function started", flush=True)

    try:
        print("🔍 Trying to load BTC data...", flush=True)
        btc_df = get_data_15m("BTCUSDT")
        print(f"🔍 BTC data loaded: {len(btc_df)} rows", flush=True)

        if btc_df is None or len(btc_df) < 10:
            print("❌ BTC data fetch failed or insufficient", flush=True)
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Signal bot: BTC data unavailable. Skipping signal check.")
            return

        btc_change_pct = (btc_df["close"].iloc[-1] - btc_df["close"].iloc[-3]) / btc_df["close"].iloc[-3] * 100
        btc_rsi = RSIIndicator(btc_df["close"]).rsi().iloc[-1]
        print(f"📊 BTC change: {btc_change_pct:.2f}% | BTC RSI: {btc_rsi:.2f}", flush=True)

    except Exception as e:
        print("❌ Error loading BTC data:", e, flush=True)
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Signal bot: Failed to load BTC data.")
        return

    symbols = get_top_volatile_symbols(limit=200)
    active_usdt_symbols = get_active_usdt_symbols()
    used_symbols = set()
    count = 0
    top_score = -1
    top_pick = None
    messages = []

    for symbol in symbols:
        if symbol in used_symbols or not symbol.endswith("USDT") or symbol not in active_usdt_symbols:
            continue

        if is_blacklisted(symbol):
            print(f"⛔️ Skipping {symbol} — blacklisted ({get_blacklist_reason(symbol)})", flush=True)
            continue

        df = get_data(symbol)
        if df is None or len(df) < 50 or df["close"].iloc[-1] == 0:
            print(f"⚠️ Skipping {symbol} – invalid data", flush=True)
            continue

        result = is_strong_signal(df, btc_change_pct, btc_rsi, symbol=symbol)
        if not result:
            print(f"🔎 Debug: {symbol} rejected by signal filter", flush=True)
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

        if score < 4:
            print(f"⚠️ {symbol} skipped – score too low: {score}", flush=True)
            continue

        signal_time = datetime.utcnow()
        signal_time_ms = int(signal_time.timestamp() * 1000)

        result_check = check_trade_result(
            symbol=symbol,
            signal_type=signal,
            entry=entry,
            tp1=tp1,
            tp2=tp2,
            sl=sl,
            signal_time_ms=signal_time_ms
        )
        
        log_sent_signal(
            symbol=symbol,
            data={
                "type": signal,
                "entry": entry,
                "tp1": tp1,
                "tp2": tp2,
                "sl": sl
            },
            result=result_check
        )

        print("\n📊 Signal Analysis Breakdown:", flush=True)
        print(f"🔹 Symbol: {symbol}", flush=True)
        print(f"🔹 Type: {signal}", flush=True)
        print(f"🔹 RSI: {rsi}", flush=True)
        print(f"🔹 MA Trend: MA10 > MA30 = {ma10 > ma30}", flush=True)
        print(f"🔹 Volume Spike: {df['volume'].iloc[-1]} > avg = {df['volume'].iloc[-1] > df['volume'][-20:-5].mean()}", flush=True)
        candle_type = "Bullish" if signal == "LONG" and df['close'].iloc[-1] > df['open'].iloc[-1] else "Bearish" if signal == "SHORT" and df['close'].iloc[-1] < df['open'].iloc[-1] else "Weak"
        print(f"🔹 Candle: {candle_type}", flush=True)
        print(f"🔹 BTC Trend Match: {'✅' if (signal == 'LONG' and btc_change_pct > 0) or (signal == 'SHORT' and btc_change_pct < 0) else '❌'}", flush=True)
        print(f"🔹 Final Score: {score}", flush=True)
        print(f"🔹 Result: {result_check}", flush=True)

        emoji = "🔥🔥🔥" if score == 5 else "🔥"
        message = (
            f"{emoji} {symbol} (1h)\n"
            f"Signal: {signal}\n"
            f"Score: {score}/5\n"
            f"RSI: {rsi:.2f}\n"
            f"MA10: {ma10:.2f}, MA30: {ma30:.2f}\n"
            f"Entry: {round(entry * 0.998, 4)} – {round(entry * 1.002, 4)}\n"
            f"TP1: {tp1}\n"
            f"TP2: {tp2}\n"
            f"SL: {sl}\n"
            f"🧪 Result: {result_check}"
        )

        messages.append((symbol, message))
        used_symbols.add(symbol)
        count += 1

        if score > top_score:
            top_score = score
            top_pick = symbol

        if count >= 8:
            break

    try:
        if messages:
            for symbol, msg in messages:
                if symbol == top_pick:
                    msg = "🔝 TOP PICK\n" + msg
                print(f"\n📤 Sending signal for {symbol}:\n{msg}\n", flush=True)
                bot.send_message(chat_id=CHAT_ID, text=msg)
        else:
            print("📭 No strong signals found. Market is calm.", flush=True)
            bot.send_message(chat_id=CHAT_ID, text="📩 No strong signals found. Market is calm.")
    except Exception as e:
        print("❌ ERROR in send_signals:", e, flush=True)
