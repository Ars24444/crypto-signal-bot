import requests

def get_top_volatile_symbols(limit=100, min_volume_usdt=800000):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    data = response.json()

    symbols = []

    for d in data:
        symbol = d['symbol']
        quote_volume = float(d.get('quoteVolume', 0))
        price_change_pct = abs(float(d.get('priceChangePercent', 0)))

        if (
            not symbol.endswith("USDT") or
            "UP" in symbol or
            "DOWN" in symbol or
            "BULL" in symbol or
            "BEAR" in symbol or
            "BUSD" in symbol
        ):
            continue

        if quote_volume < min_volume_usdt:
            continue

        symbols.append({
            "symbol": symbol,
            "priceChangePercent": price_change_pct
        })

    sorted_symbols = sorted(symbols, key=lambda x: x['priceChangePercent'], reverse=True)

    return [s['symbol'] for s in sorted_symbols[:limit]]
