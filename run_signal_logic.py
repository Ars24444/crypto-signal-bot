import os
import time
from datetime import datetime

from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from data_fetcher import get_data, get_data_15m, get_active_usdt_symbols, get_data_1m
from get_top_symbols import get_top_volatile_symbols
from signal_logger import log_sent_signal
from save_signal_result import save_signal_result
from check_trade_result import check_trade_result
from blacklist_manager import is_blacklisted, add_to_blacklist, get_blacklist_reason
from pump_detector import is_pump_signal, build_pump_long_trade
from utils import is_strong_signal

TELEGRAM_TOKEN = "7842956033:AAE_M7bhnydjIlTYZzQatz4BunMz2_vi-nw"
CHAT_ID = 5398864436
bot = Bot(token=TELEGRAM_TOKEN)


# -----------------------------------------------------
# PUMP DETECTOR MODULE (runs every minute)
# -----------------------------------------------------
def check_pump_and_send(symbol):
    try:
        df_1m = get_data_1m(symbol)
        if df_1m is None or len(df_1m) < 60:
            return

        is_pump, info = is_pump_signal(df_1m)
        if not is_pump:
            return

        trade = build_pump_long_trade(df_1m)

        entry = trade["entry"]
        tp1 = trade["tp1"]
        tp2 = trade["tp2"]
        sl = trade["sl"]

        message = (
            "🚀🔥 PUMP LONG SIGNAL (1m)\n\n"
            f"Symbol: *{symbol}*\n"
            f"Timeframe: 1m\n\n"
            f"Entry: `{entry:.6f}`\n"
            f"TP1: {tp1:.6f} (+5%)\n"
            f"TP2: {tp2:.6f} (+10%)\n"
            f"SL: `{sl:.6f}`\n\n"
            f"📈 Volume spike: {info['last_vol']:.0f} vs avg {info['avg_vol']:.0f}\n"
            f"📊 Last candle change: {info['price_change_pct']*100:.2f}%\n"
        )

        bot.send_message(chat_id=CHAT_ID, text=message)

        log_sent_signal(
            symbol,
            {
                "type": "LONG_PUMP",
                "entry": entry,
                "tp1": tp1,
                "tp2": tp2,
                "sl": sl,
            },
            result="pending",
        )

    except Exception as e:
        print(f"[PUMP ERROR] {symbol}: {e}", flush=True)


# -----------------------------------------------------
# MAIN BOT: HOURLY SIGNALS + PUMP DETECTOR
# -----------------------------------------------------
def send_signals(force: bool = False):
    print("🚀 Signal function started", flush=True)

    # Current minute for hourly filter
    now = datetime.utcnow()
    current_minute = now.minute

    top_score = -1
    top_pick = None
    count = 0
    messages = []
    
    # -----------------------------------------------------
    # LOAD BTC
    # -----------------------------------------------------
    try:
        print("🔍 Loading BTC 15m...", flush=True)
        btc_df = get_data_15m("BTCUSDT")

        if btc_df is None or len(btc_df) < 40:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ BTC data unavailable.")
            return

        btc_close = btc_df["close"]
        btc_rsi_series = RSIIndicator(btc_close, window=14).rsi()

        btc_last = float(btc_close.iloc[-1])
        btc_prev = float(btc_close.iloc[-2])
        btc_change_pct = (btc_last - btc_prev) / btc_prev * 100
        btc_rsi = float(btc_rsi_series.iloc[-1])

        print(f"📊 BTC change: {btc_change_pct:.2f}% | BTC RSI: {btc_rsi:.2f}", flush=True)

    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Failed to load BTC data.")
        return

    # -----------------------------------------------------
    # SYMBOL LIST
    # -----------------------------------------------------
    symbols = get_top_volatile_symbols(limit=200)
    active_usdt_symbols = get_active_usdt_symbols()
    used_symbols = set()

   # --------------------- SIGNAL SCAN ---------------------
    for symbol in symbols:
        if (
            symbol in used_symbols
            or not symbol.endswith("USDT")
            or symbol not in active_usdt_symbols
        ):
            continue

        # --------------------------------------------------
        # 🔥 PUMP DETECTOR – ԱՇԽԱՏՈՒՄ Է ԱՄԵՆ ՌՈՊԵ
        # --------------------------------------------------
        try:
            check_pump_and_send(symbol)
        except Exception as e:
            print(f"[PUMP ERROR] {symbol}: {e}", flush=True)

        # ---------------- Skip blacklisted ----------------
        if is_blacklisted(symbol):
            print(
                f"⛔️ Skipping {symbol} — blacklisted ({get_blacklist_reason(symbol)})",
                flush=True,
            )
            continue

        # --------------------------------------------------
        # ⏰ TIME FILTER – ՀԻՄՆԱԿԱՆ 1H ՍԻԳՆԱԼՆԵՐԻ ՀԱՄԱՐ
        # pump-ը արդեն ստուգել ենք, էդ պատճառով սա
        # ԱՐԳԵԼՈՒՄ Է ՄԻԱՅՆ 1H լոգիկան, ՈՉ թե pump-ը
        # --------------------------------------------------
        if not force and current_minute != 0:
            # ոչ ամբողջ ժամ է → 1h սիգնալ չենք հաշվում
            continue

        # ---------------- LOAD 1H DATA ----------------
        df = get_data(symbol)
        if df is None or len(df) < 50 or df["close"].iloc[-1] == 0:
            print(f"⚠️ Skipping {symbol} – invalid DF", flush=True)
            continue
       # ------------- MAIN FILTER – STRONG SIGNAL -------------
        result = is_strong_signal(
            df,
            btc_change_pct=btc_change_pct,
            btc_rsi=btc_rsi,
            symbol=symbol,
        )

        if not result:
            print(f"🔎 Debug: {symbol} rejected by signal filter", flush=True)
            continue

        # ----------- UNPACK RESULT -----------
        signal = result["type"]   # "LONG" or "SHORT"
        entry = result["entry"]
        score = result["score"]
        rsi = result["rsi"]
        ma10 = result["ma10"]
        ma30 = result["ma30"]

        # ----------- ATR TP/SL -----------
        atr = AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        ).average_true_range().iloc[-1]

        if signal == "LONG":
            tp1 = round(entry + atr * 1.5, 4)
            tp2 = round(entry + atr * 2.5, 4)
            sl = round(entry - atr * 1.0, 4)
        else:
            tp1 = round(entry - atr * 1.5, 4)
            tp2 = round(entry - atr * 2.5, 4)
            sl = round(entry + atr * 1.0, 4)

        # ----------- BUILD MESSAGE -----------
        message = (
            f"🔥 {symbol} (1h)\n\n"
            f"Signal: {signal}\n"
            f"Score: {score}/7\n"
            f"RSI: {rsi:.2f}\n"
            f"MA10: {ma10:.4f}, MA30: {ma30:.4f}\n"
            f"Entry: {entry:.4f}\n"
            f"TP1: {tp1:.4f}\n"
            f"TP2: {tp2:.4f}\n"
            f"SL: {sl:.4f}\n"
        )

        bot.send_message(chat_id=CHAT_ID, text=message)

        # ----------- TIME STAMP -----------
        signal_time = datetime.utcnow()
        signal_time_ms = int(signal_time.timestamp() * 1000)

        # ----------- RESULT CHECK -----------
        result_check = check_trade_result(
            symbol=symbol,
            signal_type=signal,
            entry=entry,
            tp1=tp1,
            tp2=tp2,
            sl=sl,
            signal_time_ms=signal_time_ms,
        )

        # ----------- LOG SAVE -----------
        log_sent_signal(
            symbol=symbol,
            data={
                "type": signal,
                "entry": entry,
                "tp1": tp1,
                "tp2": tp2,
                "sl": sl,
            },
            result=result_check,
        )
        
         # ------------ DEBUG PRINTS --------------
        print("\n📊 Signal Analysis Breakdown:", flush=True)
        print(f"🔹 Symbol: {symbol}", flush=True)
        print(f"🔹 Type: {signal}", flush=True)
        print(f"🔹 RSI: {rsi:.2f}", flush=True)
        print(f"🔹 MA10: {ma10:.4f}", flush=True)
        print(f"🔹 MA30: {ma30:.4f}", flush=True)
        print(
            f"🔹 BTC Δ: {btc_change_pct:.2f}% | BTC RSI: {btc_rsi:.1f}",
            flush=True,
        )
        print(f"🔹 Final Score: {score}/7", flush=True)
        print(f"🔹 Result: {result_check}", flush=True)

        # ------------ TELEGRAM MESSAGE --------------
        emoji = "🔥🔥🔥" if score >= 6 else "🔥"
        message = (
            f"{emoji} {symbol} (1h)\n"
            f"Signal: {signal}\n"
            f"Score: {score}/7\n"
            f"RSI: {rsi:.2f}\n"
            f"MA10: {ma10:.4f}, MA30: {ma30:.4f}\n"
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


    # ------------ TELEGRAM SEND ALL SIGNALS --------------
    try:
        if messages:
            for symbol, msg in messages:
                if symbol == top_pick:
                    msg = "🔝 TOP PICK\n" + msg
                print(f"\n📤 Sending signal for {symbol}:\n{msg}\n", flush=True)
                bot.send_message(chat_id=CHAT_ID, text=msg)
        else:
            print("📭 No strong signals found.", flush=True)
            bot.send_message(
                chat_id=CHAT_ID,
                text="📩 No strong signals found. Market is calm.",
            )
    except Exception as e:
        print("❌ ERROR in send_signals:", e, flush=True)
