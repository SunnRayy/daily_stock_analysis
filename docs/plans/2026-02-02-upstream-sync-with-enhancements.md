# Upstream Sync with Local Enhancements — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Resolve merge conflicts by accepting upstream changes, then re-add fund mode support with Tushare as primary data source while preserving local yfinance improvements.

**Architecture:** Accept upstream's `DataFetcherManager` refactoring. Modify `_init_default_fetchers()` to prioritize Tushare when configured. Re-add fund mode conditional logic.

**Tech Stack:** Python, Git

---

## Task 1: Resolve Merge Conflicts — Accept Upstream

**Step 1: Accept upstream for documentation files**

```bash
cd /Users/ray/Documents/projects/daily_stock_analysis
git checkout --theirs README.md docs/CHANGELOG.md docs/README_EN.md docs/README_CHT.md
```

**Step 2: Accept upstream for core source files**

```bash
git checkout --theirs src/market_analyzer.py src/core/pipeline.py data_provider/base.py
```

**Step 3: Keep local yfinance improvements**

```bash
git checkout --ours data_provider/yfinance_fetcher.py
```

**Step 4: Stage all resolved files**

```bash
git add -A
```

**Step 5: Verify no remaining conflicts**

```bash
git diff --check
```

Expected: No output (no conflict markers remaining)

---

## Task 2: Re-Add Fund Mode Support to `base.py`

**Files:**

- Modify: `data_provider/base.py:302-379`

**Step 1: View current upstream code**

Verify `_init_default_fetchers()` method structure after accepting upstream.

**Step 2: Add fund mode logic**

In `data_provider/base.py`, modify `_init_default_fetchers()` to add fund mode support:

```python
def _init_default_fetchers(self) -> None:
    """
    Initialize default data source list.

    Priority (with Tushare as primary when configured):
    - If TUSHARE_TOKEN configured: Tushare (Priority 0)
    - Fund mode: Prioritize AkshareFetcher for funds + Finnhub/Yfinance for US
    - Stock mode: Full fetcher chain
    """
    from .efinance_fetcher import EfinanceFetcher
    from .akshare_fetcher import AkshareFetcher
    from .tushare_fetcher import TushareFetcher
    from .pytdx_fetcher import PytdxFetcher
    from .baostock_fetcher import BaostockFetcher
    from .yfinance_fetcher import YfinanceFetcher
    from .finnhub_fetcher import FinnhubFetcher
    from src.config import get_config
    
    config = get_config()

    # Fund mode: Different fetcher priority
    if getattr(config, 'default_stock_type', 'stock') == 'fund':
        self._fetchers = [
            FinnhubFetcher(),    # US Stocks
            AkshareFetcher(),    # Funds (primary)
            YfinanceFetcher(),   # Fallback
        ]
        self._fetchers.sort(key=lambda f: f.priority)
        logger.info("Fund mode: AkshareFetcher (funds) + Finnhub/Yfinance (US)")
        return

    # Stock mode: Full chain with Tushare prioritized if configured
    efinance = EfinanceFetcher()
    akshare = AkshareFetcher()
    tushare = TushareFetcher()  # Auto-adjusts priority based on Token
    pytdx = PytdxFetcher()
    baostock = BaostockFetcher()
    yfinance = YfinanceFetcher()
    finnhub = FinnhubFetcher()

    self._fetchers = [
        finnhub,
        efinance,
        akshare,
        tushare,
        pytdx,
        baostock,
        yfinance,
    ]

    # Sort by priority (Tushare self-adjusts to 0 if Token configured)
    self._fetchers.sort(key=lambda f: f.priority)

    priority_info = ", ".join([f"{f.name}(P{f.priority})" for f in self._fetchers])
    logger.info(f"Initialized {len(self._fetchers)} data sources: {priority_info}")
```

**Step 3: Commit fund mode restoration**

```bash
git add data_provider/base.py
git commit -m "feat: restore fund mode support in DataFetcherManager"
```

---

## Task 3: Commit Merge Resolution

**Step 1: Create merge commit**

```bash
git commit -m "chore: sync upstream/main with local enhancements

- Accept upstream DataFetcherManager refactoring
- Accept ASTRBOT notification channel
- Preserve local yfinance MultiIndex handling improvements
- Restore fund mode support with Tushare priority"
```

---

## Task 4: Local Verification

**Step 1: Check Python syntax**

```bash
python -m py_compile src/config.py src/analyzer.py data_provider/*.py
```

Expected: No output (no syntax errors)

**Step 2: Verify imports**

```bash
python -c "from src.config import get_config; from data_provider import DataFetcherManager; print('Imports OK')"
```

Expected: `Imports OK`

**Step 3: Quick smoke test**

```bash
python -c "
from data_provider.base import DataFetcherManager
dm = DataFetcherManager()
print(f'Fetchers: {dm.available_fetchers}')
"
```

Expected: List of fetcher names including TushareFetcher

---

## Task 5: Push to Origin

**Step 1: Push changes**

```bash
git push origin main
```

**Step 2: Check GitHub Actions status**

```bash
gh repo set-default SunnRayy/daily_stock_analysis
gh run list --limit 3
```

---

## Summary

| Task | Action |
|------|--------|
| 1 | Resolve conflicts: accept upstream, keep local yfinance |
| 2 | Re-add fund mode to `_init_default_fetchers()` |
| 3 | Commit merge |
| 4 | Verify syntax and imports |
| 5 | Push and check CI |
