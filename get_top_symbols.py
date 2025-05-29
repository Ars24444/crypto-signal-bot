import requests

def get_top_volatile_symbols(limit=50):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    data = response.json()

    # Filter only real USDT trading pairs
    usdt_pairs = [d for d in data if d['symbol'].endswith('USDT') and not d['symbol'].endswith('BUSDUSDT')]

    # Calculate absolute price change percent
    for d in usdt_pairs:
        try:
            d['priceChangePercent'] = abs(float(d['priceChangePercent']))
        except:
            d['priceChangePercent'] = 0

    # Sort by volatility (descending)
    sorted_data = sorted(usdt_pairs, key=lambda x: x['priceChangePercent'], reverse=True)

    # Return only the top N symbols
    return [d['symbol'] for d in sorted_data[:limit]]
