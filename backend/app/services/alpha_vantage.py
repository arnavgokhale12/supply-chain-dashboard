"""Alpha Vantage API client with rate limiting."""
from __future__ import annotations

import time
from collections import deque
from datetime import date

import requests

from backend.app.core.config import settings


class AlphaVantageClient:
    """Client for Alpha Vantage API with built-in rate limiting."""

    BASE_URL = "https://www.alphavantage.co/query"
    RATE_LIMIT = 5  # calls per minute on free tier
    RATE_WINDOW = 60  # seconds

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.alpha_vantage_api_key
        if not self.api_key:
            raise RuntimeError("ALPHA_VANTAGE_API_KEY missing in .env")
        self.call_times: deque[float] = deque(maxlen=self.RATE_LIMIT)

    def _wait_for_rate_limit(self) -> None:
        """Block until we can make another call within rate limit."""
        if len(self.call_times) >= self.RATE_LIMIT:
            oldest = self.call_times[0]
            wait_time = self.RATE_WINDOW - (time.time() - oldest)
            if wait_time > 0:
                print(f"Rate limit reached, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
        self.call_times.append(time.time())

    def get_daily_adjusted(
        self, symbol: str, outputsize: str = "full"
    ) -> list[dict[str, float | date]]:
        """
        Fetch daily prices for a symbol.

        Args:
            symbol: Stock/ETF symbol (e.g., "SPY", "NVDA")
            outputsize: "compact" (100 days) or "full" (20+ years)

        Returns:
            List of dicts with keys: date, close, adjusted_close, volume
        """
        self._wait_for_rate_limit()

        # Use TIME_SERIES_DAILY (free) instead of DAILY_ADJUSTED (premium)
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": self.api_key,
        }

        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
        if "Note" in data:
            raise RuntimeError(f"Alpha Vantage rate limit: {data['Note']}")
        if "Information" in data:
            raise ValueError(f"Alpha Vantage: {data['Information']}")
        if "Time Series (Daily)" not in data:
            raise ValueError(f"Unexpected response format for {symbol}: {list(data.keys())}")

        time_series = data["Time Series (Daily)"]
        results = []

        for date_str, values in time_series.items():
            close_price = float(values["4. close"])
            results.append({
                "date": date.fromisoformat(date_str),
                "close": close_price,
                "adjusted_close": close_price,  # Use close as adjusted (no splits data in free tier)
                "volume": int(values["5. volume"]),
            })

        # Sort by date ascending
        results.sort(key=lambda x: x["date"])
        return results


def fetch_symbol_prices(symbol: str) -> list[dict]:
    """
    Convenience function to fetch prices for a symbol.

    Returns list of dicts with: date, close, adjusted_close, volume
    """
    client = AlphaVantageClient()
    return client.get_daily_adjusted(symbol)
