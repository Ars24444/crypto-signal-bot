import time
import requests
import pandas as pd


BINANCE_URL = "https://api.binance.com/api/v3/klines"


def get_data(symbol, interval="1h", limit=100):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }

    try:
        time.sleep(0.2)  # anti rate-limit

        response = requests.get(
            BINANCE_URL,
            params=params,
            timeout=5
        )

        if response.status_code != 200:
            print(f"⚠️ Binance HTTP {response.status_code} for {symbol}")
            return None

        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            return None

        df = pd.DataFrame(
            data,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "num_trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )

        df[["open", "high", "low", "close", "volume"]] = df[
            ["open", "high", "low", "close", "volume"]
        ].astype(float)

        # 🔑 VERY IMPORTANT
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        return df

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error for {symbol}: {e}")
        return None

