import requests

def get_active_symbols_by_trades(symbols, interval='15m', limit=1, min_buy_volume=20, min_sell_volume=20):
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

            # ✅ Reject if any value is zero
            if close == 0 or open_ == 0 or high == 0 or low == 0 or volume == 0:
                continue

            if taker_buy_volume >= min_buy_volume and taker_sell_volume >= min_sell_volume:
                active_symbols.append(symbol)
        except Exception as e:
            print(f"⚠️ Error checking {symbol}: {e}")
    return active_symbols

def get_top_volatile_symbols(limit=200, min_volume_usdt=300_000):
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
    for d in data:
        symbol = d['symbol']
        quote_volume = float(d.get('quoteVolume', 0))
        price_change_pct = abs(float(d.get('priceChangePercent', 0)))

        if (
            not symbol.endswith("USDT") or
            any(x in symbol for x in ["UP", "DOWN", "BULL", "BEAR", "BUSD", "TRY", "EUR", "1000"]) or
            quote_volume < min_volume_usdt or
            price_change_pct < 3
        ):
            continue

        symbols.append({
            "symbol": symbol,
            "priceChangePercent": price_change_pct
        })

    sorted_symbols = sorted(symbols, key=lambda x: x['priceChangePercent'], reverse=True)
    volatile_symbols = [s['symbol'] for s in sorted_symbols[:limit]]

    return get_active_symbols_by_trades(volatile_symbols)
