import requests

def get_volume_strength(symbol, interval="1h", limit=1):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()

    if not isinstance(data, list) or len(data) == 0:
        print(f"❌ Failed to fetch kline data for {symbol}")
        return None

    candle = data[0]
    total_volume = float(candle[5])              
    taker_buy_volume = float(candle[10])         
    taker_sell_volume = total_volume - taker_buy_volume

    return {
        "total": total_volume,
        "buy": taker_buy_volume,
        "sell": taker_sell_volume,
        "ratio": taker_buy_volume / total_volume if total_volume > 0 else 0
    }
