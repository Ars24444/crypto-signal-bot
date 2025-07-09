import requests

def get_volume_strength(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/aggTrades"
        params = {
            "symbol": symbol,
            "limit": 1000
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if not isinstance(data, list):
            print(f"⚠️ Unexpected response for volume: {data}")
            return None

        buy_volume = 0
        sell_volume = 0

        for trade in data:
            qty = float(trade['q'])
            if trade['m']:
                sell_volume += qty
            else:
                buy_volume += qty

        total_volume = buy_volume + sell_volume
        if total_volume == 0:
            return None

        ratio = buy_volume / total_volume
        return {
            "buy_volume": round(buy_volume, 2),
            "sell_volume": round(sell_volume, 2),
            "ratio": round(ratio, 2)  # >0.5 means buyers dominate
        }

    except Exception as e:
        print(f"❌ Error in get_volume_strength: {e}")
        return None
