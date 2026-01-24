# DSA US Market Data Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add FinnhubFetcher for US stocks and update YfinanceFetcher to handle US stock codes correctly.

**Architecture:** Create new FinnhubFetcher following existing Strategy Pattern. Update YfinanceFetcher's code conversion to detect US stocks. Register FinnhubFetcher in the manager.

**Tech Stack:** Python 3.9+, finnhub-python, yfinance, pandas, tenacity

---

## Prerequisites

Before starting, ensure:

- [x] Finnhub API key available (user's existing key)
- [x] `finnhub-python` package installed: `pip install finnhub-python`
- [x] DSA project cloned at `/Users/ray/Documents/projects/daily_stock_analysis`

---

## Task 1: Add Finnhub Configuration

**Files:**

- Modify: `/Users/ray/Documents/projects/daily_stock_analysis/.env`
- Modify: `/Users/ray/Documents/projects/daily_stock_analysis/.env.example`

**Step 1: Add FINNHUB_API_KEY to .env.example**

Add to `.env.example`:

```bash
# US Market Data (Finnhub)
FINNHUB_API_KEY=your_finnhub_api_key_here
```

**Step 2: Add actual key to .env**

Add to `.env`:

```bash
FINNHUB_API_KEY=<actual_key>
```

**Step 3: Verify configuration loads**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('FINNHUB_API_KEY:', 'SET' if os.getenv('FINNHUB_API_KEY') else 'MISSING')"
```

Expected: `FINNHUB_API_KEY: SET`

**Step 4: Commit**

```bash
git add .env.example
git commit -m "config: add FINNHUB_API_KEY to .env.example"
```

**GATE: Do not proceed to Task 2 until Step 3 shows FINNHUB_API_KEY: SET**

---

## Task 2: Create FinnhubFetcher Test File

**Files:**

- Create: `/Users/ray/Documents/projects/daily_stock_analysis/tests/test_finnhub_fetcher.py`

**Step 1: Write the test file**

```python
# -*- coding: utf-8 -*-
"""
Tests for FinnhubFetcher - US Market Data Source
"""

import os
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Will be imported after implementation
# from data_provider.finnhub_fetcher import FinnhubFetcher
from data_provider.base import DataFetchError, STANDARD_COLUMNS


class TestFinnhubFetcherCodeDetection:
    """Test US stock code detection logic"""

    def test_is_us_stock_valid_tickers(self):
        """Valid US tickers should be detected"""
        from data_provider.finnhub_fetcher import FinnhubFetcher
        fetcher = FinnhubFetcher()

        assert fetcher._is_us_stock("AAPL") == True
        assert fetcher._is_us_stock("NVDA") == True
        assert fetcher._is_us_stock("GOOGL") == True
        assert fetcher._is_us_stock("A") == True  # Single letter valid
        assert fetcher._is_us_stock("BRK.B") == True  # With dot

    def test_is_us_stock_cn_codes(self):
        """CN stock codes should not be detected as US"""
        from data_provider.finnhub_fetcher import FinnhubFetcher
        fetcher = FinnhubFetcher()

        assert fetcher._is_us_stock("600519") == False
        assert fetcher._is_us_stock("000001") == False
        assert fetcher._is_us_stock("300750") == False
        assert fetcher._is_us_stock("688001") == False

    def test_is_us_stock_edge_cases(self):
        """Edge cases for stock detection"""
        from data_provider.finnhub_fetcher import FinnhubFetcher
        fetcher = FinnhubFetcher()

        assert fetcher._is_us_stock("ABCDEF") == False  # 6 letters = too long
        assert fetcher._is_us_stock("") == False
        assert fetcher._is_us_stock("123") == False


class TestFinnhubFetcherDataFetch:
    """Test data fetching from Finnhub API"""

    @pytest.fixture
    def fetcher(self):
        from data_provider.finnhub_fetcher import FinnhubFetcher
        return FinnhubFetcher()

    @pytest.fixture
    def mock_candles_response(self):
        """Mock Finnhub candles API response"""
        return {
            'c': [150.0, 151.5, 152.0],  # close
            'h': [152.0, 153.0, 154.0],  # high
            'l': [149.0, 150.0, 151.0],  # low
            'o': [150.5, 151.0, 151.5],  # open
            'v': [1000000, 1100000, 1200000],  # volume
            't': [1706140800, 1706227200, 1706313600],  # timestamps
            's': 'ok'
        }

    def test_normalize_data_columns(self, fetcher, mock_candles_response):
        """Normalized data should have standard columns"""
        df = fetcher._normalize_candles(mock_candles_response, "AAPL")

        for col in STANDARD_COLUMNS:
            assert col in df.columns, f"Missing column: {col}"

    def test_normalize_data_values(self, fetcher, mock_candles_response):
        """Normalized data should have correct values"""
        df = fetcher._normalize_candles(mock_candles_response, "AAPL")

        assert len(df) == 3
        assert df['close'].iloc[0] == 150.0
        assert df['high'].iloc[0] == 152.0
        assert df['volume'].iloc[0] == 1000000

    @pytest.mark.skipif(
        not os.getenv('FINNHUB_API_KEY'),
        reason="FINNHUB_API_KEY not set"
    )
    def test_fetch_real_data_aapl(self, fetcher):
        """Integration test: fetch real AAPL data"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        df = fetcher._fetch_raw_data("AAPL", start_date, end_date)

        assert not df.empty
        assert 'close' in df.columns or 'c' in df.columns


class TestFinnhubFetcherIntegration:
    """Integration tests with real API (requires FINNHUB_API_KEY)"""

    @pytest.mark.skipif(
        not os.getenv('FINNHUB_API_KEY'),
        reason="FINNHUB_API_KEY not set"
    )
    def test_get_daily_data_aapl(self):
        """Full flow: get AAPL daily data with indicators"""
        from data_provider.finnhub_fetcher import FinnhubFetcher
        fetcher = FinnhubFetcher()

        df = fetcher.get_daily_data("AAPL", days=30)

        assert not df.empty
        assert 'close' in df.columns
        assert 'ma5' in df.columns  # Technical indicator from base class
        assert len(df) >= 5  # At least some data
```

**Step 2: Run test to verify it fails (module not found)**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -m pytest tests/test_finnhub_fetcher.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'data_provider.finnhub_fetcher'`

**Step 3: Commit test file**

```bash
git add tests/test_finnhub_fetcher.py
git commit -m "test: add FinnhubFetcher tests (TDD)"
```

**GATE: Do not proceed until tests fail with "No module named 'data_provider.finnhub_fetcher'"**

---

## Task 3: Implement FinnhubFetcher

**Files:**

- Create: `/Users/ray/Documents/projects/daily_stock_analysis/data_provider/finnhub_fetcher.py`

**Step 1: Write the FinnhubFetcher implementation**

```python
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
```

**Step 2: Run tests to verify code detection tests pass**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -m pytest tests/test_finnhub_fetcher.py::TestFinnhubFetcherCodeDetection -v
```

Expected: All 3 code detection tests PASS

**Step 3: Run normalization tests**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -m pytest tests/test_finnhub_fetcher.py::TestFinnhubFetcherDataFetch -v -k "not real_data"
```

Expected: Normalization tests PASS

**Step 4: Run integration test (requires API key)**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -m pytest tests/test_finnhub_fetcher.py::TestFinnhubFetcherIntegration -v
```

Expected: Integration test PASS (or SKIP if no API key)

**Step 5: Commit**

```bash
git add data_provider/finnhub_fetcher.py
git commit -m "feat: add FinnhubFetcher for US stock data"
```

**GATE: Do not proceed until all tests pass**

---

## Task 4: Update YfinanceFetcher for US Stock Detection

**Files:**

- Modify: `/Users/ray/Documents/projects/daily_stock_analysis/data_provider/yfinance_fetcher.py`
- Create: `/Users/ray/Documents/projects/daily_stock_analysis/tests/test_yfinance_us_stocks.py`

**Step 1: Write test for US stock code handling**

Create `tests/test_yfinance_us_stocks.py`:

```python
# -*- coding: utf-8 -*-
"""
Tests for YfinanceFetcher US stock code handling
"""

import pytest
from data_provider.yfinance_fetcher import YfinanceFetcher


class TestYfinanceUSCodeConversion:
    """Test US stock code detection in YfinanceFetcher"""

    @pytest.fixture
    def fetcher(self):
        return YfinanceFetcher()

    def test_us_stock_no_suffix(self, fetcher):
        """US stocks should not get .SS or .SZ suffix"""
        assert fetcher._convert_stock_code("AAPL") == "AAPL"
        assert fetcher._convert_stock_code("NVDA") == "NVDA"
        assert fetcher._convert_stock_code("GOOGL") == "GOOGL"
        assert fetcher._convert_stock_code("A") == "A"

    def test_us_stock_with_dot(self, fetcher):
        """US stocks with dot suffix should be preserved"""
        assert fetcher._convert_stock_code("BRK.B") == "BRK.B"
        assert fetcher._convert_stock_code("BRK.A") == "BRK.A"

    def test_cn_stock_still_works(self, fetcher):
        """CN stocks should still get correct suffix"""
        assert fetcher._convert_stock_code("600519") == "600519.SS"
        assert fetcher._convert_stock_code("000001") == "000001.SZ"
        assert fetcher._convert_stock_code("300750") == "300750.SZ"
        assert fetcher._convert_stock_code("688001") == "688001.SS"

    def test_already_formatted_preserved(self, fetcher):
        """Already formatted codes should be preserved"""
        assert fetcher._convert_stock_code("600519.SS") == "600519.SS"
        assert fetcher._convert_stock_code("000001.SZ") == "000001.SZ"
```

**Step 2: Run test to see current behavior (should fail for US stocks)**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -m pytest tests/test_yfinance_us_stocks.py -v
```

Expected: `test_us_stock_no_suffix` FAILS (AAPL becomes AAPL.SZ)

**Step 3: Update _convert_stock_code in yfinance_fetcher.py**

Modify `/Users/ray/Documents/projects/daily_stock_analysis/data_provider/yfinance_fetcher.py`:

Find the `_convert_stock_code` method and replace with:

```python
    def _convert_stock_code(self, stock_code: str) -> str:
        """
        转换股票代码为 Yahoo Finance 格式

        Yahoo Finance 格式：
        - US stocks: AAPL, NVDA, BRK.B (no suffix)
        - 沪市：600519.SS (Shanghai Stock Exchange)
        - 深市：000001.SZ (Shenzhen Stock Exchange)

        Args:
            stock_code: 原始代码，如 '600519', '000001', 'AAPL'

        Returns:
            Yahoo Finance 格式代码
        """
        import re

        code = stock_code.strip()

        # Already has exchange suffix - return as-is
        if '.SS' in code.upper() or '.SZ' in code.upper():
            return code.upper()

        # US stock pattern: 1-5 uppercase letters, optional .X suffix
        # Examples: AAPL, NVDA, BRK.B, A
        if re.match(r'^[A-Za-z]{1,5}(\.[A-Za-z])?$', code):
            return code.upper()  # US stock, no suffix needed

        # 去除可能的后缀
        code = code.replace('.SH', '').replace('.sh', '')

        # CN stock: 6 digits, add exchange suffix
        if code.startswith(('600', '601', '603', '688')):
            return f"{code}.SS"
        elif code.startswith(('000', '002', '300')):
            return f"{code}.SZ"
        else:
            logger.warning(f"无法确定股票 {code} 的市场，默认使用深市")
            return f"{code}.SZ"
```

**Step 4: Run tests to verify fix**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -m pytest tests/test_yfinance_us_stocks.py -v
```

Expected: All tests PASS

**Step 5: Run existing yfinance tests to ensure no regression**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -m pytest tests/ -k "yfinance" -v --ignore=tests/test_yfinance_us_stocks.py
```

Expected: Existing tests still pass (or skip if no network)

**Step 6: Commit**

```bash
git add data_provider/yfinance_fetcher.py tests/test_yfinance_us_stocks.py
git commit -m "feat: update YfinanceFetcher to detect US stock codes"
```

**GATE: Do not proceed until all yfinance tests pass**

---

## Task 5: Register FinnhubFetcher in Package

**Files:**

- Modify: `/Users/ray/Documents/projects/daily_stock_analysis/data_provider/__init__.py`

**Step 1: Read current **init**.py**

Check current exports in `data_provider/__init__.py`.

**Step 2: Add FinnhubFetcher export**

Add to `data_provider/__init__.py`:

```python
from .finnhub_fetcher import FinnhubFetcher
```

And add to `__all__` list:

```python
__all__ = [
    # ... existing ...
    'FinnhubFetcher',
]
```

**Step 3: Verify import works**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -c "from data_provider import FinnhubFetcher; print('FinnhubFetcher imported successfully')"
```

Expected: `FinnhubFetcher imported successfully`

**Step 4: Commit**

```bash
git add data_provider/__init__.py
git commit -m "feat: export FinnhubFetcher from data_provider package"
```

**GATE: Import must succeed before proceeding**

---

## Task 6: End-to-End Verification

**Files:**

- None (verification only)

**Step 1: Test FinnhubFetcher standalone**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -c "
from data_provider import FinnhubFetcher
f = FinnhubFetcher()
if f.client:
    df = f.get_daily_data('AAPL', days=5)
    print(f'AAPL: {len(df)} days')
    print(df[['date', 'close', 'volume']].tail(3))
else:
    print('API key not set, skipping')
"
```

Expected: AAPL data with 5 days of prices

**Step 2: Test YfinanceFetcher with US stock**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -c "
from data_provider import YfinanceFetcher
f = YfinanceFetcher()
df = f.get_daily_data('NVDA', days=5)
print(f'NVDA via yfinance: {len(df)} days')
print(df[['date', 'close', 'volume']].tail(3))
"
```

Expected: NVDA data with 5 days of prices

**Step 3: Test CN stock still works**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -c "
from data_provider import YfinanceFetcher
f = YfinanceFetcher()
df = f.get_daily_data('600519', days=5)
print(f'600519 (Maotai): {len(df)} days')
print(df[['date', 'close']].tail(3))
"
```

Expected: 600519 data (may be delayed but should work)

**Step 4: Run full test suite**

Run:

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
python -m pytest tests/ -v --ignore=tests/.venv
```

Expected: All tests pass

**Step 5: Final commit with verification note**

```bash
git add -A
git commit -m "test: verify US market data fetching end-to-end

Verified:
- FinnhubFetcher fetches AAPL data
- YfinanceFetcher handles NVDA as US stock
- CN stocks (600519) still work correctly
"
```

---

## Summary

| Task | Description | Verification |
|------|-------------|--------------|
| 1 | Add Finnhub config | `FINNHUB_API_KEY: SET` |
| 2 | Create tests (TDD) | Tests fail with "no module" |
| 3 | Implement FinnhubFetcher | All tests pass |
| 4 | Update YfinanceFetcher | US codes don't get .SZ suffix |
| 5 | Register in package | Import succeeds |
| 6 | End-to-end verification | AAPL, NVDA, 600519 all work |

**Total commits:** 6
**Estimated time:** 2-3 hours

---

*Plan created: 2026-01-24*

---

## Implementation Status (2026-01-24)

### Support Added

- **FinnhubFetcher**: Implemented and registered (Priority 1).
- **YfinanceFetcher**: Updated to support US stocks (e.g. AAPL, GOOGL) without suffix (Priority 4).
- **Fund Mode Compatibility**: Updated `DataFetcherManager` to allow US stock fetchers even when `DEFAULT_STOCK_TYPE=fund`.

### Issues & Workarounds

- **Finnhub API 403 Forbidden**: The provided API key does not support the `stock/candles` endpoint (likely Basic plan).
  - **Impact**: `FinnhubFetcher` is active but fails to retrieve historical data.
  - **Fallback**: System automatically falls back to `YfinanceFetcher`, which is working correctly for US stocks.
- **Yfinance MultiIndex**: Fixed an issue where newer `yfinance` versions returned MultiIndex columns, causing normalization failures.

### Verification

- Validated with `tests/verify_end_to_end.py` and `tests/show_google_data.py`.
- US stocks (GOOGL, NVDA) successfully fetched via Yfinance.
- CN stocks (600519) continued to work via Yfinance (fallback).
