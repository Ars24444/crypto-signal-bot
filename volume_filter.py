import requests

def get_volume_strength(symbol: str):
    """
    Returns:
      {
        "buy_volume": float,   # notional (qty * price)
        "sell_volume": float,  # notional (qty * price)
        "ratio": float         # buy_notional / total
      }
      or None on failure.
    """
    try:
        url = "https://fapi.binance.com/fapi/v1/aggTrades"
        params = {"symbol": symbol, "limit": 1000}
        headers = {"User-Agent": "signal-bot/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"⚠️ aggTrades HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        if not isinstance(data, list):
            print(f"⚠️ Unexpected aggTrades payload: {data}")
            return None

        buy_notional = 0.0
        sell_notional = 0.0

        for t in data:
            qty = float(t.get("q", 0.0))
            price = float(t.get("p", 0.0))
            if qty <= 0 or price <= 0:
                continue
            notional = qty * price

            if t.get("m", False):
                sell_notional += notional
            else:
                buy_notional += notional

        total = buy_notional + sell_notional
        if total <= 0:
            return None

        ratio = buy_notional / total
        return {
            "buy_volume": round(buy_notional, 2),
            "sell_volume": round(sell_notional, 2),
            "ratio": round(ratio, 3)
        }

    except Exception as e:
        print(f"❌ Error in get_volume_strength: {e}")
        return None
