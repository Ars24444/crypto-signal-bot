from utils import get_data, is_strong_signal, get_active_usdt_symbols
from get_top_symbols import get_top_volatile_symbols
from telegram import Bot
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from blacklist_manager import is_blacklisted, add_to_blacklist
from check_trade_result import check_trade_result
import os

TELEGRAM_TOKEN = '7842956033:AAFCHreV97rJH11mhNQUhY3thpA_LpS5tLs'
CHAT_ID = 5398864436

bot = Bot(token=TELEGRAM_TOKEN)

def is_strong_signal(df, btc_change_pct=0, btc_rsi=0, symbol=""):
    if df is None or len(df) < 30:
        return None

    close = df['close']
    volume = df['volume']
    high = df['high']
    low = df['low']
    current_price = close.iloc[-1]

    # Indicators
    ma10 = SMAIndicator(close, window=10).sma_indicator().iloc[-1]
    ma30 = SMAIndicator(close, window=30).sma_indicator().iloc[-1]
    rsi = RSIIndicator(close).rsi().iloc[-1]

    avg_volume = volume[:-5].mean()
    current_volume = volume.iloc[-1]

    # ATR
    atr = AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1]
    atr_pct = atr / current_price * 100

    # 3-candle price change check
    recent_change_pct = abs(close.iloc[-1] - close.iloc[-4]) / close.iloc[-4] * 100
    if recent_change_pct > 2 * atr_pct:
        return None  # too pumped or dumped

    # Scoring
    score = 0
    if current_volume > 1.2 * avg_volume:
        score += 1
    if ma10 > ma30:
        score += 1
    if ma10 < ma30:
        score += 1
    if rsi > 60:
        score += 1
    if rsi < 40:
        score += 1
    if btc_change_pct > -0.5 and ma10 > ma30:
        score += 1
    if btc_change_pct < 0.5 and ma10 < ma30:
        score += 1

    # Determine LONG or SHORT
    signal_type = None
    if ma10 > ma30 and rsi > 60:
        signal_type = "LONG"
    elif ma10 < ma30 and rsi < 40:
        signal_type = "SHORT"

    if score >= 4 and signal_type:
        return {
            "type": signal_type,
            "score": score,
            "entry": current_price,
            "tp1": None,
            "tp2": None,
            "sl": None,
            "rsi": rsi,
            "ma10": ma10,
            "ma30": ma30
        }
    else:
        return None
