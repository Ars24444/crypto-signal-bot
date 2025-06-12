import requests
import time

def has_sufficient_trades(symbol, min_trades=50):
    try:
        url = "https://fapi.binance.com/fapi/v1/aggTrades"
        end_time = int(time.time() * 1000)
        start_time = end_time - (15 * 60 * 1000)  # last 15 minutes

        params = {
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1000
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        buy_trades = 0
        sell_trades = 0

        for trade in data:
            if trade["m"]:  # If 'm' is True, buyer is the market maker → sell
                sell_trades += 1
            else:
                buy_trades += 1

        total_trades = buy_trades + sell_trades

        return buy_trades >= min_trades and sell_trades >= min_trades

    except Exception as e:
        print(f"Error fetching futures trades for {symbol}: {e}")
        return False
