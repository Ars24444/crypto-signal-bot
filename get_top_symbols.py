import time
import requests
from functools import lru_cache

BINANCE_BASE = "https://api.binance.com/api/v3"


# ================= CACHE =================
@lru_cache(maxsize=1)
def get_existing_usdt_symbols():
    url = f"{BINANCE_BASE}/exchangeInfo"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return {
            s["symbol"]
            for s in data["symbols"]
            if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
        }
    except Exception as e:
        print(f"⚠️ exchangeInfo error: {e}")
        return set()


# ================= ACTIVE SYMBOL CHECK =================
def is_symbol_active_by_trades(
    symbol,
    interval="15m",
    lookback=3,
    min_volume=50,
):
    """
    Lightweight activity check using few candles only
    """
    try:
        url = f"{BINANCE_BASE}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": lookback,
        }

        time.sleep(0.15)
        r = requests.get(url, params=params, timeout=5)
        if r.status_code != 200:
            return False

        data = r.json()
        if not isinstance(data, list) or len(data) < lookback:
            return False

        total_volume = sum(float(k[5]) for k in data)
        total_buy = sum(float(k[9]) for k in data)

        if total_volume < min_volume:
            return False

        buy_ratio = total_buy / total_volume

        # block extreme manipulation only
        if buy_ratio < 0.02 or buy_ratio > 0.98:
            return False

        return True

    except Exception:
        return False


# ================= MAIN SYMBOL SELECTOR =================
def get_top_volatile_symbols(
    limit=120,
    min_volume_usdt=500_000,
    min_price_change=4.0,
):
    try:
        r = requests.get(f"{BINANCE_BASE}/ticker/24hr", timeout=10)
        if r.status_code != 200:
            return []

        data = r.json()
    except Exception as e:
        print(f"⚠️ ticker error: {e}")
        return []

    valid_symbols = get_existing_usdt_symbols()

    blacklist_keywords = {
        "UP", "DOWN", "BULL", "BEAR",
        "BUSD", "TRY", "EUR", "FDUSD",
        "1000", "TUSD"
    }

    candidates = []

    for d in data:
        symbol = d.get("symbol")
        if not symbol or symbol not in valid_symbols:
            continue

        if not symbol.endswith("USDT"):
            continue

        if any(x in symbol for x in blacklist_keywords):
            continue

        quote_volume = float(d.get("quoteVolume", 0))
        price_change = abs(float(d.get("priceChangePercent", 0)))

        if quote_volume < min_volume_usdt:
            continue

        if price_change < min_price_change:
            continue

        candidates.append((symbol, price_change))

    # sort by volatility
    candidates.sort(key=lambda x: x[1], reverse=True)
    top_symbols = [s for s, _ in candidates[:limit]]

    # lightweight activity check (NOT for all)
    active_symbols = []
    for symbol in top_symbols[:60]:  # cap API usage
        if is_symbol_active_by_trades(symbol):
            active_symbols.append(symbol)

    return active_symbols
