import time
import requests
import pandas as pd
from typing import Optional

from get_top_symbols import get_top_volatile_symbols


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
REQUEST_TIMEOUT = 5        # seconds
REQUEST_DELAY = 0.2        # anti-rate-limit
MAX_RETRIES = 3


def get_data(
    symbol: str,
    interval: str = "1h",
    limit: int = 100
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from Binance and return DataFrame with:
    ['open', 'high', 'low', 'close', 'volume']
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            time.sleep(REQUEST_DELAY)

            response = requests.get(
                BINANCE_KLINES_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code != 200:
                print(
                    f"⚠️ Binance HTTP {response.status_code} for {symbol} {interval}",
                    flush=True,
                )
                continue

            data = response.json()
            if not isinstance(data, list) or len(data) == 0:
                print(f"⚠️ Empty data for {symbol} {interval}", flush=True)
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

            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            return df

        except requests.exceptions.RequestException as e:
            print(
                f"❌ Request error ({attempt}/{MAX_RETRIES}) {symbol} {interval}: {e}",
                flush=True,
            )
            time.sleep(0.5)

        except Exception as e:
            print(
                f"❌ Unexpected error {symbol} {interval}: {e}",
                flush=True,
            )
            return None

    return None


# ================= TIMEFRAME HELPERS =================

def get_data_15m(symbol: str, limit: int = 100) -> Optional[pd.DataFrame]:
    return get_data(symbol, interval="15m", limit=limit)


def get_data_1m(symbol: str, limit: int = 200) -> Optional[pd.DataFrame]:
    return get_data(symbol, interval="1m", limit=limit)


# ================= SYMBOL LIST =================

def get_active_usdt_symbols(limit: int = 100):
    """
    Returns top volatile USDT symbols.
    (Naming kept for compatibility with existing bot logic)
    """
    return get_top_volatile_symbols(limit=limit)
