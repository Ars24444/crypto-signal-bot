import requests

def get_active_symbols_by_trades(symbols, interval='15m', limit=1, min_buy_volume=50, min_sell_volume=50):
    """
    Returns symbols with at least the given buy and sell volume in the latest 15m candle.
    """
    active_symbols = []
    for symbol in symbols:
        try:
            url = 'https://api.binance.com/api/v3/klines'
            params = {'symbol': symbol, 'interval': interval, 'limit': limit}
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                kline = data[0]
                total_volume = float(kline[5])
                buy_volume = float(kline[9])
                sell_volume = total_volume - buy_volume

                if buy_volume >= min_buy_volume and sell_volume >= min_sell_volume:
                    active_symbols.append(symbol)
        except Exception as e:
            print(f"Error checking {symbol}: {e}")
    return active_symbols


def get_top_volatile_symbols(limit=100, min_volume_usdt=1000000):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    data = response.json()

    symbols = []

    for d in data:
        symbol = d['symbol']
        quote_volume = float(d.get('quoteVolume', 0))
        price_change_pct = abs(float(d.get('priceChangePercent', 0)))

        # Filter only clean USDT spot pairs
        if (
            not symbol.endswith("USDT") or
            "UP" in symbol or
            "DOWN" in symbol or
            "BULL" in symbol or
            "BEAR" in symbol or
            "BUSD" in symbol or
            "1000" in symbol or
            "TRY" in symbol or
            "EUR" in symbol
        ):
            continue

        if quote_volume < min_volume_usdt:
            continue

        symbols.append({
            "symbol": symbol,
            "priceChangePercent": price_change_pct
        })

    # Sort by volatility
    sorted_symbols = sorted(symbols, key=lambda x: x['priceChangePercent'], reverse=True)
    volatile_symbols = [s['symbol'] for s in sorted_symbols[:limit]]

    # Filter by buy/sell volume in last 15m
    active_symbols = get_active_symbols_by_trades(volatile_symbols)
    return active_symbols
