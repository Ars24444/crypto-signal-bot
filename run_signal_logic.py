import os
from datetime import datetime

import pandas as pd
from telegram import Bot
from btc_filter import check_btc_influence_df
from volume_filter as vf
from safe_candle_checker import safe_candle_ok
from orderbook_filter import orderbook_filter
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator, SMAIndicator

from data_fetcher import get_data, get_data_15m, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from signal_logger import log_sent_signal
from check_trade_result import check_trade_result
from blacklist_manager import is_blacklisted, get_blacklist_reason

# ----------------------- Config -----------------------
TELEGRAM_TOKEN = "AAGK_mRt_ADxZg3rbD82DAFQCb5X9AL0Wv8"
CHAT_ID = 5398864436
bot = Bot (token=TELEGRAM_TOKEN)


MAX_SIGNALS = 8
MIN_SCORE = 4
VOL_SPIKE_RATIO = 1.3  # volume must be > 1.3× SMA20
# -----------------------------------------------------


def analyze_signal(df: pd.DataFrame, btc_change_pct: float, btc_rsi: float, symbol: str):
    """
    Returns dict or None:
    {
        'type': 'LONG'/'SHORT',
        'entry': float,
        'tp1': float, 'tp2': float, 'sl': float,
        'score': int,
        'rsi': float, 'ma10': float, 'ma30': float
    }
    """
    try:
        closes = df["close"].astype(float)
        opens = df["open"].astype(float)
        highs = df["high"].astype(float)
        lows = df["low"].astype(float)
        vols = df["volume"].astype(float)
    except Exception:
        return None

    if len(df) < 50 or closes.iloc[-1] == 0:
        return None

    # Indicators
    ema10 = EMAIndicator(close=closes, window=10).ema_indicator().iloc[-1]
    ema30 = EMAIndicator(close=closes, window=30).ema_indicator().iloc[-1]
    rsi_now = RSIIndicator(close=closes, window=14).rsi().iloc[-1]
    vol_sma20 = SMAIndicator(close=vols, window=20).sma_indicator().iloc[-1]
    atr14 = AverageTrueRange(high=highs, low=lows, close=closes, window=14).average_true_range().iloc[-1]

    last_close = float(closes.iloc[-1])
    last_open = float(opens.iloc[-1])
    last_high = float(highs.iloc[-1])
    last_low = float(lows.iloc[-1])
    last_vol = float(vols.iloc[-1])

    score = 0
    reasons = []

    # 1) Trend filter (EMA10 vs EMA30)
    if ema10 > ema30:
        long_ok, short_ok = True, False
        score += 1
        reasons.append("Trend: EMA10>EMA30 (long bias)")
    elif ema10 < ema30:
        long_ok, short_ok = False, True
        score += 1
        reasons.append("Trend: EMA10<EMA30 (short bias)")
    else:
        long_ok = short_ok = False
        reasons.append("Trend: flat")

    # 2) Volume spike
    vol_spike = last_vol > (vol_sma20 * VOL_SPIKE_RATIO) if vol_sma20 and vol_sma20 > 0 else False
    if vol_spike:
        score += 1
        reasons.append(f"Volume spike {last_vol:.0f}>{vol_sma20*VOL_SPIKE_RATIO:.0f}")
    else:
        reasons.append("Volume normal")

    # 3) RSI confirmation
    long_rsi_ok = 32 <= rsi_now <= 60
    short_rsi_ok = 40 <= rsi_now <= 70
    rsi_pass = (long_ok and long_rsi_ok) or (short_ok and short_rsi_ok)
    if rsi_pass:
        score += 1
        reasons.append(f"RSI ok {rsi_now:.1f}")
    else:
        reasons.append(f"RSI weak {rsi_now:.1f}")

    # 4) Candle quality
    bullish = last_close > last_open and (last_close - last_open) > 0.003 * last_close and (last_high - last_close) < 0.4 * (last_close - last_open)
    bearish = last_close < last_open and (last_open - last_close) > 0.003 * last_close and (last_close - last_low) < 0.4 * (last_open - last_close)

    candle_pass = (long_ok and bullish) or (short_ok and bearish)
    if candle_pass:
        score += 1
        reasons.append("Candle strong")
    else:
        reasons.append("Candle weak")

    # 5) BTC alignment & guardrails
    btc_align = (long_ok and btc_change_pct >= -0.3 and btc_rsi < 70) or (short_ok and btc_change_pct <= 0.3 and btc_rsi > 30)
    if btc_align:
        score += 1
        reasons.append(f"BTC align Δ{btc_change_pct:.2f}% | RSI {btc_rsi:.1f}")
    else:
        reasons.append(f"BTC misalign Δ{btc_change_pct:.2f}% | RSI {btc_rsi:.1f}")

    if score < MIN_SCORE:
        return None

    # Decide direction
    if long_ok and (not short_ok or bullish or rsi_now <= 55):
        side = "LONG"
        entry = last_close
        sl = max(last_low, entry - 1.0 * atr14)
        tp1 = entry + 1.5 * atr14
        tp2 = entry + 2.2 * atr14
    else:
        side = "SHORT"
        entry = last_close
        sl = min(last_high, entry + 1.0 * atr14)
        tp1 = entry - 1.5 * atr14
        tp2 = entry - 2.2 * atr14

    # Clamp numbers to sensible precision
    def r4(x): 
        try:
            return round(float(x), 6)
        except Exception:
            return float(x)

    return {
        "type": side,
        "entry": r4(entry),
        "tp1": r4(tp1),
        "tp2": r4(tp2),
        "sl": r4(sl),
        "score": int(score),
        "rsi": float(rsi_now),
        "ma10": float(ema10),
        "ma30": float(ema30),
        "reasons": reasons,
    }


def send_signals(force: bool = False):
    print("🚀 Signal function started", flush=True)

    # ---------- BTC context ----------
    try:
        print("🔍 Trying to load BTC data...", flush=True)
        btc_df = get_data_15m("BTCUSDT")
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

    # ---------- Universe ----------
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
        if df is None or len(df) < 50 or df.get("close", pd.Series([0])).iloc[-1] == 0:
            print(f"⚠️ Skipping {symbol} – invalid data", flush=True)
            continue

        result = analyze_signal(df, btc_change_pct, btc_rsi, symbol)
        if not result:
            print(f"🔎 Debug: {symbol} rejected by signal filters", flush=True)
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
        # --- BTC filter ---
        allow, btc_reason, btc_bonus = check_btc_influence_df(btc_df, signal)
        if not allow:
            print(f"❌ {symbol} rejected by BTC: {btc_reason}", flush=True)
            continue
        score = min(5, score + btc_bonus)
        print(f"✅ BTC ok: {btc_reason} (+{btc_bonus})", flush=True)

        # --- Volume filter ---
        v_ok, v_reason, v_bonus = volume_filter(df)
        if not v_ok:
            print(f"❌ {symbol} rejected by volume: {v_reason}", flush=True)
            continue
        score = min(5, score + v_bonus)
        print(f"✅ volume ok: {v_reason} (+{v_bonus})", flush=True)

        # --- Candle safety ---
        c_ok, c_reason = safe_candle_ok(df, signal)
        if not c_ok:
            print(f"❌ {symbol} rejected by candle: {c_reason}", flush=True)
            continue
        print(f"✅ candle ok: {c_reason}", flush=True)

        # --- Orderbook dominance ---
        ob_ok, ob_reason = orderbook_filter(symbol, signal)
        if not ob_ok:
            print(f"❌ {symbol} rejected by orderbook: {ob_reason}", flush=True)
            continue
        print(f"✅ orderbook ok: {ob_reason}", flush=True)

        # extra guardrail
        if score < MIN_SCORE:
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
            data={"type": signal, "entry": entry, "tp1": tp1, "tp2": tp2, "sl": sl, "score": score},
            result=result_check
        )

        # ---------- DEBUG BLOCK ----------
        print("\n📊 Signal Analysis Breakdown:", flush=True)
        print(f"🔹 Symbol: {symbol}", flush=True)
        print(f"🔹 Type: {signal}", flush=True)
        print(f"🔹 RSI: {rsi:.2f}", flush=True)
        print(f"🔹 MA Trend: EMA10({ma10:.4f}) > EMA30({ma30:.4f}) = {ma10 > ma30}", flush=True)
        vol_avg = df['volume'][-20:-5].mean() if 'volume' in df and len(df) >= 25 else 0
        print(f"🔹 Volume Spike: {df['volume'].iloc[-1]} > avg={vol_avg} -> {df['volume'].iloc[-1] > vol_avg if vol_avg else False}", flush=True)
        candle_type = "Bullish" if signal == "LONG" and df['close'].iloc[-1] > df['open'].iloc[-1] else "Bearish" if signal == "SHORT" and df['close'].iloc[-1] < df['open'].iloc[-1] else "Weak"
        print(f"🔹 Candle: {candle_type}", flush=True)
        print(f"🔹 BTC Trend Match: {'✅' if (signal == 'LONG' and btc_change_pct > 0) or (signal == 'SHORT' and btc_change_pct < 0) else '❌'}", flush=True)
        print(f"🔹 Final Score: {score}", flush=True)
        print(f"🔹 Result: {result_check}", flush=True)
        for r in result.get("reasons", []):
            print(f"   • {r}", flush=True)

        emoji = "🔥🔥🔥" if score >= 5 else "🔥"
        msg = (
            f"{emoji} {symbol} (1h)\n"
            f"Signal: {signal}\n"
            f"Score: {score}/5\n"
            f"RSI: {rsi:.2f}\n"
            f"EMA10: {ma10:.4f}, EMA30: {ma30:.4f}\n"
            f"Entry: {round(entry * 0.998, 6)} – {round(entry * 1.002, 6)}\n"
            f"TP1: {tp1}\n"
            f"TP2: {tp2}\n"
            f"SL: {sl}\n"
            f"🧪 Result: {result_check}"
        )

        messages.append((symbol, msg))
        used_symbols.add(symbol)
        count += 1

        if score > top_score:
            top_score = score
            top_pick = symbol

        if count >= MAX_SIGNALS:
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


if __name__ == "__main__":
    send_signals()
