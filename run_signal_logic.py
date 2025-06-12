from utils import get_data, is_strong_signal, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from blacklist_manager import is_blacklisted, add_to_blacklist
from check_trade_result import check_trade_result
from signal_logger import log_sent_signal
from datetime import datetime
import os

TELEGRAM_TOKEN = "7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs"
CHAT_ID = 5398864436
bot = Bot(token=TELEGRAM_TOKEN)

def send_signals(force=False):
    print("🚀 Signal function started")

    btc_df = get_data_15m("BTCUSDT")
    btc_change_pct = (btc_df["close"].iloc[-1] - btc_df["close"].iloc[-3]) / btc_df["close"].iloc[-3] * 100
    btc_rsi = RSIIndicator(btc_df["close"]).rsi().iloc[-1]
    print(f"📊 BTC change: {btc_change_pct:.2f}% | BTC RSI: {btc_rsi:.2f}")

    symbols = get_top_volatile_symbols(limit=200)
    print(f"🔍 Checking {len(symbols)} coins from top volatile list")
    active_usdt_symbols = get_active_usdt_symbols()
    used_symbols = set()
    count = 0

    top_score = -1
    top_pick = None
    messages = []

    for symbol in symbols:
        if symbol in used_symbols or not symbol.endswith("USDT") or symbol not in active_usdt_symbols or is_blacklisted(symbol):
            print(f"⏩ Skipping {symbol} – inactive or blacklisted")
            continue

        df = get_data(symbol)
        if df is None or len(df) < 50 or df["close"].iloc[-1] == 0:
            print(f"⚠️ Skipping {symbol} – invalid data")
            continue

        result = is_strong_signal(df, btc_change_pct, btc_rsi, symbol=symbol)
        if not result:
            print(f"🔎 Debug: {symbol} rejected by signal filter")
            continue

        signal = result["type"]
        entry = result["entry"]
        score = result["score"]
        rsi = result["rsi"]
        ma10 = result["ma10"]
        ma30 = result["ma30"]

        if score < 4 or signal not in ["LONG", "SHORT"]:
            continue

        entry_low = round(df["low"].iloc[-1] * 0.999, 4)
        entry_high = round(df["high"].iloc[-1] * 1.001, 4)

        if signal == "LONG":
            sl = round(entry * 0.988, 4)
            tp1 = round(entry * 1.03, 4)
            tp2 = round(entry * 1.05, 4)
        else:
            sl = round(entry * 1.012, 4)
            tp1 = round(entry * 0.97, 4)
            tp2 = round(entry * 0.95, 4)

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

        print("\n📊 Signal Analysis Breakdown:")
        print(f"🔹 Symbol: {symbol}")
        print(f"🔹 Type: {signal}")
        print(f"🔹 RSI: {rsi}")
        print(f"🔹 MA Trend: MA10 > MA30 = {ma10 > ma30}")
        print(f"🔹 Volume Spike: {df['volume'].iloc[-1]} > avg*1.5 = {df['volume'].iloc[-1] > 1.5 * df['volume'][-20:-5].mean()}")
        candle_type = "Bullish" if signal == "LONG" and df['close'].iloc[-1] > df['open'].iloc[-1] else "Bearish" if signal == "SHORT" and df['close'].iloc[-1] < df['open'].iloc[-1] else "Weak"
        print(f"🔹 Candle: {candle_type}")
        print(f"🔹 BTC Trend Match: {'✅' if (signal == 'LONG' and btc_change_pct > 0) or (signal == 'SHORT' and btc_change_pct < 0) else '❌'}")
        print(f"🔹 Final Score: {score}")
        print(f"🔹 Result: {result_check}")

        if score > top_score:
            top_score = score
            top_pick = symbol

        emoji = "🔥🔥🔥" if score == 5 else "🔥"
        message = (
            f"{emoji} {symbol} (1h)\n"
            f"Signal: {signal}\n"
            f"Score: {score}/5\n"
            f"RSI: {rsi:.2f}\n"
            f"MA10: {ma10:.2f}, MA30: {ma30:.2f}\n"
            f"Entry: {entry_low} – {entry_high}\n"
            f"TP1: {tp1}\n"
            f"TP2: {tp2}\n"
            f"SL: {sl}\n"
            f"🧪 Result: {result_check}"
        )

        messages.append((symbol, message))
        used_symbols.add(symbol)
        count += 1

        if count >= 8:
            break

    try:
        if messages:
            for symbol, msg in messages:
                if symbol == top_pick:
                    msg = "🔝 TOP PICK\n" + msg
                print(f"\n📤 Sending signal for {symbol}:\n{msg}\n")
                bot.send_message(chat_id=CHAT_ID, text=msg)
        else:
            print("📭 No strong signals found.Market is calm.")
            bot.send_message(chat_id=CHAT_ID, text="📩 No strong signals found. Market is calm.")
    except Exception as e:
        print("❌ ERROR in send_signals:", e)
                  
