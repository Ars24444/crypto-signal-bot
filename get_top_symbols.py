import requests

def get_active_symbols_by_trades(symbols, interval='15m', limit=1, min_buy_volume=20, min_sell_volume=20):
    """
    Filters the given symbols based on recent taker buy/sell volume on the 15-minute timeframe.
    Only returns symbols with healthy trading activity and no strong imbalance.
    """
    active_symbols = []
    for symbol in symbols:
        try:
            url = 'https://api.binance.com/api/v3/klines'
            params = {'symbol': symbol, 'interval': interval, 'limit': limit}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code != 200:
                continue

            data = response.json()
            if not data or not isinstance(data, list):
                continue

            kline = data[0]
            open_ = float(kline[1])
            high = float(kline[2])
            low = float(kline[3])
            close = float(kline[4])
            volume = float(kline[5])
            taker_buy_volume = float(kline[9])
            taker_sell_volume = volume - taker_buy_volume

            # Skip bad data
            if close == 0 or open_ == 0 or high == 0 or low == 0 or volume == 0:
                continue

            # Reject weak or unbalanced volumes
            if taker_buy_volume < min_buy_volume or taker_sell_volume < min_sell_volume:
                continue

            ratio = taker_buy_volume / volume
            if ratio < 0.05 or ratio > 0.95:
                continue

            active_symbols.append(symbol)

        except Exception as e:
            print(f"⚠️ Error checking {symbol}: {e}")
            continue

    return active_symbols


def get_top_volatile_symbols(limit=200, min_volume_usdt=500_000):
    """
    Returns the most volatile and high-volume USDT pairs on Binance,
    filtered by price change percentage and quote volume (USD).
    """
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []

        data = response.json()
    except Exception as e:
        print(f"⚠️ Error fetching tickers: {e}")
        return []

    symbols = []
    blacklist_keywords = ["UP", "DOWN", "BULL", "BEAR", "BUSD", "TRY", "EUR", "1000", "TUSD", "FDUSD"]

    for d in data:
        symbol = d.get('symbol')
        quote_volume = float(d.get('quoteVolume', 0))
        price_change_pct = abs(float(d.get('priceChangePercent', 0)))

        if (
            not symbol.endswith("USDT") or
            any(x in symbol for x in blacklist_keywords) or
            quote_volume < min_volume_usdt or
            price_change_pct < 4.5
        ):
            continue

        symbols.append({
            "symbol": symbol,
            "priceChangePercent": price_change_pct
        })

    # Sort by price change percentage descending
    sorted_symbols = sorted(symbols, key=lambda x: x['priceChangePercent'], reverse=True)
    volatile_symbols = [s['symbol'] for s in sorted_symbols[:limit]]

    # Final active trade volume check
    return get_active_symbols_by_trades(volatile_symbols)
