import requests

def is_orderbook_safe(symbol, min_depth_usdt=10000, max_spread_pct=1.2, min_spread_pct=0.01):
    try:
        url = f"https://api.binance.com/api/v3/depth"
        params = {"symbol": symbol, "limit": 20}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        bids = data.get("bids", [])
        asks = data.get("asks", [])
        if not bids or not asks:
            return False

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        spread_pct = (best_ask - best_bid) / best_bid * 100

        if spread_pct < min_spread_pct or spread_pct > max_spread_pct:
            return False

        def total_depth(order_list):
            return sum(float(price) * float(qty) for price, qty in order_list[:10])

        bid_depth = total_depth(bids)
        ask_depth = total_depth(asks)

        if bid_depth < min_depth_usdt or ask_depth < min_depth_usdt:
            return False

        return True
    except Exception as e:
        print(f"⚠️ Orderbook check failed for {symbol}: {e}")
        return False
