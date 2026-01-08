import time
import requests
from functools import lru_cache

BINANCE_BASE = "https://api.binance.com/api/v3"
DEBUG = True


# ================= CACHE =================
@lru_cache(maxsize=1)
def get_existing_usdt_symbols():
    url = f"{BINANCE_BASE}/exchangeInfo"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        symbols = {
            s["symbol"]
            for s in data["symbols"]
            if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
        }

        if DEBUG:
            print(f"📦 exchangeInfo: {len(symbols)} USDT symbols loaded", flush=True)

        return symbols

    except Exception as e:
        print(f"⚠️ exchangeInfo error: {e}", flush=True)
        return set()


# ================= ACTIVE SYMBOL CHECK =================
def is_symbol_active_by_trades(
    symbol,
    interval="15m",
    lookback=3,
    min_volume=50,
):
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
            if DEBUG:
                print(f"❌ {symbol} activity check failed (HTTP {r.status_code})", flush=True)
            return False

        data = r.json()
        if not isinstance(data, list) or len(data) < lookback:
            if DEBUG:
                print(f"❌ {symbol} activity check failed (bad data)", flush=True)
            return False

        total_volume = sum(float(k[5]) for k in data)
        total_buy = sum(float(k[9]) for k in data)

        if total_volume < min_volume:
            if DEBUG:
                print(f"❌ {symbol} inactive: low volume ({total_volume:.1f})", flush=True)
            return False

        buy_ratio = total_buy / total_volume

        if buy_ratio < 0.02 or buy_ratio > 0.98:
            if DEBUG:
                print(
                    f"❌ {symbol} inactive: extreme buy ratio ({buy_ratio:.2f})",
                    flush=True,
                )
            return False

        if DEBUG:
            print(f"✅ {symbol} active (vol={total_volume:.1f}, buy_ratio={buy_ratio:.2f})", flush=True)

        return True

    except Exception as e:
        if DEBUG:
            print(f"❌ {symbol} activity error: {e}", flush=True)
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

        if DEBUG:
            print(f"📊 24h tickers loaded: {len(data)}", flush=True)

    except Exception as e:
        print(f"⚠️ ticker error: {e}", flush=True)
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

    if DEBUG:
        print(f"🧮 Candidates after filters: {len(candidates)}", flush=True)

    candidates.sort(key=lambda x: x[1], reverse=True)
    top_symbols = [s for s, _ in candidates[:limit]]

    if DEBUG:
        print(f"🚀 Top volatile symbols selected: {len(top_symbols)}", flush=True)

    active_symbols = []
    for symbol in top_symbols[:60]:  # API cap
        if is_symbol_active_by_trades(symbol):
            active_symbols.append(symbol)

    if DEBUG:
        print(f"🎯 Active symbols after activity check: {len(active_symbols)}", flush=True)

    return active_symbols
