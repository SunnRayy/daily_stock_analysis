# Fund Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Enable the system to fetch and analyze open-ended fund data (e.g. 000751) and support treating `STOCK_LIST` codes as funds by default via configuration.

**Architecture:**

1. Add `DEFAULT_STOCK_TYPE` configuration to switch between 'stock' and 'fund' modes.
2. Extend `AkshareFetcher` to support open-ended funds using `ak.fund_open_fund_info_em`.
3. Normalize fund data (Net Value) into OHLCV format (filling Open=High=Low=Close=NAV, Volume=0).
4. Adapt `StockTrendAnalyzer` to handle zero-volume data gracefully.

**Tech Stack:** Python, Pandas, Akshare

---

### Task 1: Add Fund Configuration

**Files:**

- Modify: `config.py`
- Modify: `.env`

**Step 1: Write the failing test**

Create `tests/test_fund_config.py`:

```python
import os
from config import Config

def test_fund_config_defaults():
    # Test default is stock
    Config.reset_instance()
    if 'DEFAULT_STOCK_TYPE' in os.environ:
        del os.environ['DEFAULT_STOCK_TYPE']
    conf = Config.get_instance()
    assert conf.stock_type == "stock"

def test_fund_config_env():
    # Test checking env var
    os.environ['DEFAULT_STOCK_TYPE'] = 'fund'
    Config.reset_instance()
    conf = Config.get_instance()
    assert conf.stock_type == "fund"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_fund_config.py -v`
Expected: FAIL (AttributeError: 'Config' object has no attribute 'stock_type')

**Step 3: Write minimal implementation**

In `config.py`:

```python
# In Config class
    # ... inside class Config ...
    # === System Configuration ===
    stock_type: str = "stock"  # 'stock' or 'fund'

# In _load_from_env method
    return cls(
        # ... existing args ...
        stock_type=os.getenv('DEFAULT_STOCK_TYPE', 'stock').lower(),
    )
```

(Note: You need to add `stock_type` field to `Config` dataclass and populate it in `_load_from_env`)

In `.env`:

```text
# Default Asset Type (stock/fund)
DEFAULT_STOCK_TYPE=fund
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_fund_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add config.py .env tests/test_fund_config.py
git commit -m "feat: add DEFAULT_STOCK_TYPE configuration"
```

---

### Task 2: Implement Fund Data Fetcher

**Files:**

- Modify: `data_provider/akshare_fetcher.py`
- Test: `tests/test_fund_fetcher.py`

**Step 1: Write the failing test**

Create `tests/test_fund_fetcher.py`:

```python
import pandas as pd
from unittest.mock import patch, MagicMock
from data_provider.akshare_fetcher import AkshareFetcher
from config import Config

def test_fetch_fund_data():
    # Mock Config to return 'fund' type
    with patch('config.Config.get_instance') as mock_conf:
        mock_conf.return_value.stock_type = 'fund'
        # Also need to mock other config values if needed by fetcher init
        
        # Instantiate fetcher
        fetcher = AkshareFetcher()
        
        # Mock akshare fund info
        mock_df = pd.DataFrame({
            '净值日期': ['2023-01-01', '2023-01-02'],
            '单位净值': [1.0, 1.1],
            '日增长率': [0.0, 10.0]
        })
        
        with patch('akshare.fund_open_fund_info_em', return_value=mock_df) as mock_ak:
            df = fetcher.get_history('000751', '2023-01-01', '2023-01-02')
            
            # Verify akshare call
            mock_ak.assert_called_with(symbol='000751', indicator='单位净值走势')
            
            # Verify result format
            assert 'close' in df.columns
            assert 'volume' in df.columns
            assert df.iloc[0]['close'] == 1.0
            assert df.iloc[0]['volume'] == 0
            assert df.iloc[1]['close'] == 1.1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_fund_fetcher.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

In `data_provider/akshare_fetcher.py`:

1. Import `get_config`
2. Add `_is_fund_mode` logic using `get_config().stock_type == 'fund'`
3. The `_fetch_raw_data` method calls `get_history` (wait, BaseFetcher calls `get_history` which calls `_fetch_raw_data`).
   So we modify `_fetch_raw_data`.

```python
from config import get_config

# ... inside AkshareFetcher ...

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        config = get_config()
        # Default to fund if configured, unless it looks like ETF/HK/Stock specific override?
        # Actually user said "stock_list in .env are funds".
        # So if config.stock_type == 'fund', we treat it as fund unless we know otherwise.
        
        if config.stock_type == 'fund' and not _is_etf_code(stock_code) and not _is_hk_code(stock_code):
             return self._fetch_open_fund_data(stock_code, start_date, end_date)
        
        return super()._fetch_raw_data(stock_code, start_date, end_date) 
        # Wait, if we are inside _fetch_raw_data, we shouldn't call super() if we are the leaf class. 
        # We should use existing logic:
        # if _is_hk_code... elif _is_etf_code... else _fetch_stock_data
        
        # New logic:
        if _is_hk_code(stock_code):
            return self._fetch_hk_data(stock_code, start_date, end_date)
        elif _is_etf_code(stock_code):
            return self._fetch_etf_data(stock_code, start_date, end_date)
        elif config.stock_type == 'fund':
            return self._fetch_open_fund_data(stock_code, start_date, end_date)
        else:
            return self._fetch_stock_data(stock_code, start_date, end_date)

    def _fetch_open_fund_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        import akshare as ak
        # ... logic to fetch and normalize ...
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_fund_fetcher.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add data_provider/akshare_fetcher.py tests/test_fund_fetcher.py
git commit -m "feat: implement open-ended fund data fetching"
```

---

### Task 3: Handle Zero Volume in Analyzer

**Files:**

- Modify: `stock_analyzer.py`
- Test: `tests/test_analyzer_fund.py`

**Step 1: Write the failing test**

Create `tests/test_analyzer_fund.py`:

```python
import pandas as pd
from stock_analyzer import StockTrendAnalyzer, VolumeStatus

def test_analyze_zero_volume_fund():
    # Construct data with 0 volume
    df = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', periods=30),
        'close': [1.0 + i*0.01 for i in range(30)],
        'volume': [0] * 30
    })
    df['open'] = df['close']
    df['high'] = df['close']
    df['low'] = df['close']
    
    analyzer = StockTrendAnalyzer()
    result = analyzer.analyze(df, '000751')
    
    # Volume status should be NORMAL or skipped
    assert result.volume_status == VolumeStatus.NORMAL
    assert result.volume_ratio_5d == 0.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_analyzer_fund.py -v`

**Step 3: Write minimal implementation**

In `stock_analyzer.py`:

```python
    def _analyze_volume(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        # Check if volume is all zero (funds)
        if df['volume'].sum() == 0:
            result.volume_status = VolumeStatus.NORMAL
            result.volume_trend = "基金无量能数据"
            return
            
        # ... existing logic ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_analyzer_fund.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add stock_analyzer.py tests/test_analyzer_fund.py
git commit -m "fix: handle zero volume for fund analysis"
```

---

### Task 4: Verify with Real Fund

**Files:**

- Run: `main.py` (or wrapper)

**Step 1: Run verification**

Run the system with `DEFAULT_STOCK_TYPE=fund` in `.env` and `STOCK_LIST=000751`.

```bash
# Update .env first (Task 1 should have done this, but verify)
python3 main.py
```

**Step 2: Check output**

Check `Insight.md` for `000751` analysis.

**Step 3: Commit**

```bash
git commit --allow-empty -m "chore: verify fund analysis with 000751"
```
