---
name: financial-metrics
description: Explain, verify, or modify financial-ratio calculations. TRIGGER on questions about ROE, ROA, DuPont, inventory turnover, CCC, TTM, balance-sheet averaging, or "why is X different this quarter". Focus on `financial_analyzer.py` — specifically `_avg_balance`, `_ttm_sum`, and the `_calculate_*` methods.
---

# Financial ratio calculations

All ratios that mix income-statement and balance-sheet items follow two rules:
1. **Balance-sheet items are time-averaged** between the current period and the
   conventionally-prior period. "Prior" means the previous 10-K for annual
   ratios, or the previous filing of any type for quarterly ratios.
2. **Income-statement items are annualized via TTM** for 10-Q periods: sum
   current quarter + prior 3 quarterly filings. If fewer than 3 prior quarters
   exist, fall back to `×4` and flag `ttm_basis="approximated"`.

## Where this lives

- `_avg_balance(metric, current, filing_type)` — two-period average; returns
  `(value, is_averaged)`.
- `_ttm_sum(metric, current)` — trailing-twelve-months sum; returns
  `(value, basis)` where basis is `"ttm"`, `"approximated"`, or `"unavailable"`.
- `_prior_balance(metric, filing_type)` — convention-aware lookup of the prior
  balance-sheet value.

## Ratios that use these helpers

| Ratio | File / Func | BS averaged | TTM income |
|---|---|---|---|
| Inventory Turnover, DSI | `_calculate_inventory_metrics` | inventory | COGS |
| ROE, ROA, DuPont | `_calculate_debt_metrics` | equity, assets | net income, revenue |
| Asset Turnover, DSO, DPO | `_calculate_efficiency_metrics` | assets, receivables, payables | revenue, COGS |

## Sanity checks

- DuPont identity: `ROE == profit_margin × asset_turnover × financial_leverage`.
  Both sides should be within ~0.1 percentage points for any period with
  averaged inputs. Validate via `dupont_roe_validation` in the timeseries JSON.
- TTM basis: look at `cogs_ttm_basis` / `revenue_ttm_basis` in
  `efficiency_metrics` — a value of `"approximated"` means <4 quarters of
  history available.
- `inventory_averaged: false` on the first period is expected.

## Golden files

- `tests/fixtures/baseline_target_analysis.json` and
  `baseline_target_timeseries.json` — pre-averaging baseline snapshot. Use for
  regression comparison after changes.

## Key files

- `financial_analyzer.py:76-153` — averaging and TTM helpers
- `financial_analyzer.py:666-709` — inventory metrics
- `financial_analyzer.py:797-850` — ROE/ROA/DuPont
- `financial_analyzer.py:896-977` — efficiency metrics
