# -*- coding: utf-8 -*-
"""
===================================
FinnhubFetcher - US Market Data Source (Priority 1 for US stocks)
===================================

Data source: Finnhub API (https://finnhub.io)
Features: Real-time US stock quotes, historical candles
Rate limit: 60 calls/minute (free tier)

Key strategy:
1. Detect US stock codes (1-5 uppercase letters)
2. Use Finnhub candles endpoint for historical data
3. Fallback to quote endpoint for real-time single quotes
"""

import logging
import os
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any

import pandas as pd
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .base import BaseFetcher, DataFetchError, RateLimitError, STANDARD_COLUMNS

logger = logging.getLogger(__name__)


class FinnhubFetcher(BaseFetcher):
    """
    Finnhub API data source for US stocks

    Priority: 1 (high priority for US stocks only)
    Data source: Finnhub API

    Key features:
    - US stock detection via ticker pattern
    - Historical candles with OHLCV data
    - Rate limit handling with exponential backoff

    Note:
    - Only handles US stocks (1-5 uppercase letters)
    - Returns None for CN/HK stocks (let other fetchers handle)
    """

    name = "FinnhubFetcher"
    priority = 1  # High priority for US stocks

    # Pattern for US stock tickers: 1-5 uppercase letters, optional .X suffix
    US_TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}(\.[A-Z])?$')

    def __init__(self):
        """Initialize FinnhubFetcher with API client"""
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self._client = None

        if not self.api_key:
            logger.warning("FINNHUB_API_KEY not set - FinnhubFetcher will be disabled")

    @property
    def client(self):
        """Lazy initialization of Finnhub client"""
        if self._client is None and self.api_key:
            import finnhub
            self._client = finnhub.Client(api_key=self.api_key)
        return self._client

    def _is_us_stock(self, stock_code: str) -> bool:
        """
        Check if stock code is a US ticker

        US tickers: 1-5 uppercase letters, optional dot suffix (BRK.B)
        CN tickers: 6 digits

        Args:
            stock_code: Stock code to check

        Returns:
            True if US stock, False otherwise
        """
        if not stock_code:
            return False

        code = stock_code.strip().upper()
        return bool(self.US_TICKER_PATTERN.match(code))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical candles from Finnhub API

        Args:
            stock_code: US stock ticker (e.g., 'AAPL')
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'

        Returns:
            DataFrame with OHLCV data
        """
        # Skip non-US stocks
        if not self._is_us_stock(stock_code):
            raise DataFetchError(f"FinnhubFetcher only handles US stocks, not: {stock_code}")

        if not self.client:
            raise DataFetchError("FINNHUB_API_KEY not configured")

        # Convert dates to timestamps
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())

        logger.debug(f"Fetching Finnhub candles for {stock_code}: {start_date} to {end_date}")

        try:
            # Finnhub stock candles endpoint
            candles = self.client.stock_candles(
                symbol=stock_code.upper(),
                resolution='D',  # Daily
                _from=start_ts,
                to=end_ts
            )

            if candles.get('s') != 'ok':
                raise DataFetchError(f"Finnhub returned no data for {stock_code}")

            return self._normalize_candles(candles, stock_code)

        except Exception as e:
            if 'API limit reached' in str(e):
                raise RateLimitError(f"Finnhub rate limit: {e}")
            if isinstance(e, DataFetchError):
                raise
            raise DataFetchError(f"Finnhub API error: {e}") from e

    def _normalize_candles(self, candles: Dict[str, Any], stock_code: str) -> pd.DataFrame:
        """
        Normalize Finnhub candles response to standard format

        Finnhub format:
        - c: list of close prices
        - h: list of high prices
        - l: list of low prices
        - o: list of open prices
        - v: list of volumes
        - t: list of timestamps
        - s: status ('ok' or 'no_data')

        Returns:
            DataFrame with STANDARD_COLUMNS
        """
        df = pd.DataFrame({
            'date': pd.to_datetime(candles['t'], unit='s'),
            'open': candles['o'],
            'high': candles['h'],
            'low': candles['l'],
            'close': candles['c'],
            'volume': candles['v'],
        })

        # Calculate derived fields
        df['pct_chg'] = df['close'].pct_change() * 100
        df['pct_chg'] = df['pct_chg'].fillna(0).round(2)

        # Estimate amount (Finnhub doesn't provide)
        df['amount'] = df['volume'] * df['close']

        # Add stock code
        df['code'] = stock_code.upper()

        return df

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        Standard normalization (required by base class)

        For Finnhub, normalization happens in _normalize_candles,
        so this is a pass-through.
        """
        return df


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.DEBUG)

    fetcher = FinnhubFetcher()

    if fetcher.client:
        try:
            df = fetcher.get_daily_data('AAPL', days=10)
            print(f"Fetched {len(df)} days of AAPL data")
            print(df.tail())
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("FINNHUB_API_KEY not set")
