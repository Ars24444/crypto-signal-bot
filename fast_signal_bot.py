import os
import time
from datetime import datetime

from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from data_fetcher import get_data, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from signal_logger import log_sent_signal
from save_signal_result import save_signal_result
from check_trade_result import check_trade_result
from blacklist_manager import is_blacklisted, add_to_blacklist, get_blacklist_reason

# Կարող ես նույն token / chat_id-ը օգտագործել, ինչ run_signal_logic.py-ի մեջ է
TELEGRAM_TOKEN = "7842956033:AAGK_mRt_ADxZg3rbD82DAFQCb5X9AL0Wv8"
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)


def detect_fast_signal(df):
    """
    Ագրեսիվ սիգնալի լոգիկա volatile մոնետների համար (SCALP ռեժիմ):
    Վերադարձնում է ("LONG" կամ "SHORT", entry, tp1, tp2, sl)
    կամ (None, None, None, None, None)
    """

    if df is None or len(df) < 60:
        return None, None, None, None, None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    close = last["close"]
    open_ = last["open"]
    high = last["high"]
    low = last["low"]
    volume = last["volume"]

    # MA10 / MA30
    df["ma10"] = df["close"].rolling(window=10).mean()
    df["ma30"] = df["close"].rolling(window=30).mean()
    ma10 = df["ma10"].iloc[-1]
    ma30 = df["ma30"].iloc[-1]

    # RSI (14)
    rsi = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]

    # Volume spike (թույլացրած)
    avg_vol = df["volume"].rolling(window=20).mean().iloc[-1]
    if avg_vol is None or avg_vol == 0:
        return None, None, None, None, None

    volume_spike = volume > avg_vol * 1.2  # նախկին 2x-ից շատ ավելի թույլ

    # ATR (TP/SL-ի համար)
    atr = AverageTrueRange(
        high=df["high"], low=df["low"], close=df["close"], window=14
    ).average_true_range().iloc[-1]

    if atr is None or atr == 0:
        return None, None, None, None, None

    # Price move %
    move_down = (close - open_) / open_ <= -0.015  # >= 1.5% ուժեղ կարմիր
    move_up = (close - open_) / open_ >= 0.015     # >= 1.5% ուժեղ կանաչ

    # -------- SHORT սիգնալ (dump catcher, SCALP) --------
    if move_down and volume_spike:
        down_trend = (ma10 < ma30) or (close < ma10)
        rsi_ok = rsi >= 50  # dump-ի սկիզբ, RSI դեռ բարձր

        if down_trend and rsi_ok:
            entry = float(close)

            # 🔹 Պրոֆ TP-ներ (hybrid: % + ATR)
            # TP1 ≈ -2…2.5%, TP2 ≈ -4…5%
            tp1_percent = entry * 0.978          # -2.2%
            tp2_percent = entry * 0.958          # -4.2%

            tp1_atr = entry - 1.2 * float(atr)
            tp2_atr = entry - 2.0 * float(atr)

            # SHORT-ում TP-ն պետք է լինի entry-ից ցածր → վերցնում ենք առավել "հեռուն գնացած" safe տարբերակը
            tp1 = max(tp1_percent, tp1_atr)
            tp2 = max(tp2_percent, tp2_atr)

            # 🔹 Պրոֆ SL (hybrid, capped)
            # max ~1.8% վերևից, բայց հաշվի է առնում ATR-ը
            sl_percent_cap = entry * 1.018       # +1.8% քեփ
            sl_atr = entry + 0.8 * float(atr)    # volatility allowance

            sl = min(sl_percent_cap, sl_atr)

            return "SHORT", float(entry), float(tp1), float(tp2), float(sl)

    # -------- LONG սիգնալ (pump catcher / strong bounce, SCALP) --------
    if move_up and volume_spike:
        up_trend = (ma10 > ma30) or (close > ma10)
        rsi_ok = rsi <= 50  # pullback-ից հետո pump

        if up_trend and rsi_ok:
            entry = float(close)

            # 🔹 Պրոֆ TP-ներ LONG-ի համար
            tp1_percent = entry * 1.022          # +2.2%
            tp2_percent = entry * 1.042          # +4.2%

            tp1_atr = entry + 1.2 * float(atr)
            tp2_atr = entry + 2.0 * float(atr)

            # LONG-ում TP-ն պետք է լինի entry-ից վերև → վերցնում ենք խելոք conservative տարբերակը
            tp1 = min(tp1_percent, tp1_atr)
            tp2 = min(tp2_percent, tp2_atr)

            # 🔹 Պրոֆ SL (կապում ենք 1.8% քեփով ու ATR-ով)
            sl_percent_cap = entry * 0.982       # -1.8%
            sl_atr = entry - 0.8 * float(atr)

            sl = max(sl_percent_cap, sl_atr)

            return "LONG", float(entry), float(tp1), float(tp2), float(sl)

    return None, None, None, None, None


def send_fast_signals(force=False):
    """
    FAST bot - volatile coins hunter (SCALP)
    """
    print("🚀 FAST bot started", flush=True)
    start_time = time.time()

    signals_sent = 0

    try:
        active_symbols = get_active_usdt_symbols()
        print(f"🧾 Active symbols: {len(active_symbols)}", flush=True)

        try:
            top_symbols = get_top_volatile_symbols(active_symbols, limit=40)
        except TypeError:
            # Եթե get_top_volatile_symbols-ը չի սպասում arguments
            top_symbols = get_top_volatile_symbols()

        print(f"🔥 FAST scan symbols: {len(top_symbols)}", flush=True)

        for symbol in top_symbols:
            if not symbol.endswith("USDT"):
                continue

            if is_blacklisted(symbol):
                print(f"⛔️ {symbol} is blacklisted ({get_blacklist_reason(symbol)})", flush=True)
                continue

            # 📌 Ուղղված է try/except-ի սխալ սինտաքսը
            try:
                df = get_data(symbol)  # եթե get_data-ն default-ով արդեն 1m է
            except TypeError:
                df = get_data(symbol, interval="1m")

            if df is None or len(df) < 60:
                print(f"⚠️ Not enough data for {symbol}", flush=True)
                continue

            signal_type, entry, tp1, tp2, sl = detect_fast_signal(df)

            if signal_type is None:
                continue

            signals_sent += 1

            signal_time_ms = int(time.time() * 1000)

            result_check = check_trade_result(
                symbol=symbol,
                signal_type=signal_type,
                entry=entry,
                tp1=tp1,
                tp2=tp2,
                sl=sl,
                signal_time_ms=signal_time_ms
            )

            log_sent_signal(
                symbol=symbol,
                data={
                    "type": signal_type,
                    "entry": entry,
                    "tp1": tp1,
                    "tp2": tp2,
                    "sl": sl,
                    "mode": "FAST"
                },
                result=result_check
            )

            msg = (
                "⚡️ <b>FAST BOT (1m)</b>\n"
                "——————————————\n"
                f"Symbol: <b>{symbol}</b> [FAST]\n"
                f"Type: <b>{signal_type}</b>\n"
                f"Entry: <code>{entry:.6f}</code>\n"
                f"TP1: <code>{tp1:.6f}</code>\n"
                f"TP2: <code>{tp2:.6f}</code>\n"
                f"SL: <code>{sl:.6f}</code>\n"
                "——————————————\n"
                f"Mode: <b>FAST / 1m volatility</b>\n"
                f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )

            try:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=msg,
                    parse_mode="HTML"
                )
                print(f"📤 FAST signal sent: {symbol} {signal_type}", flush=True)
            except Exception as e:
                print(f"❌ Error sending FAST signal for {symbol}: {e}", flush=True)

            time.sleep(0.2)

        if signals_sent == 0 and force:
            try:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text="📭 FAST bot: No opportunities found right now."
                )
            except Exception as e:
                print(f"❌ Error sending 'no fast signals' message: {e}", flush=True)

        duration = time.time() - start_time
        print(f"✅ FAST bot finished. Signals sent: {signals_sent}. Time: {duration:.2f}s", flush=True)

    except Exception as e:
        print(f"💥 FAST bot crashed: {e}", flush=True)
