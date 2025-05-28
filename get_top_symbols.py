import requests
import pandas as pd


def get_top_volatile_symbols(limit=50):
    url = 'https://api.binance.com/api/v3/ticker/24hr'
    response = requests.get(url)

    if response.status_code != 200:
        return []

    df = pd.DataFrame(response.json())
    df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'],
                                             errors='coerce')
    df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')

    df = df[df['symbol'].str.endswith('USDT')]

    exclude = ['BTCUSDT', 'ETHUSDT', 'BUSDUSDT', 'USDCUSDT']
    df = df[~df['symbol'].isin(exclude)]
    df = df[df['quoteVolume'] > 10000000]

    df = df.sort_values(by='priceChangePercent', ascending=False)

    return df.head(limit)['symbol'].tolist()
