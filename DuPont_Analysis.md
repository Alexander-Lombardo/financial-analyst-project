# DuPont Analysis: Comparison with Return on Equity

## Overview

DuPont Analysis decomposes Return on Equity (ROE) into three multiplicative components to reveal what's driving shareholder returns. Rather than viewing ROE as a single number, DuPont breaks it down to show whether returns come from operational efficiency, asset utilization, or financial leverage.

**Formula**: ROE = Profit Margin × Asset Turnover × Financial Leverage

| Component | Formula | Measures |
|-----------|---------|----------|
| Profit Margin | Net Income / Revenue | Operational efficiency |
| Asset Turnover | Revenue / Total Assets | Asset utilization |
| Financial Leverage | Total Assets / Stockholders' Equity | Debt usage |

## ROE vs DuPont: Key Differences

| Aspect | Simple ROE | DuPont Analysis |
|--------|-----------|-----------------|
| Formula | Net Income / Equity | PM × AT × FL |
| Insight | Single number | Three drivers |
| Use Case | Quick comparison | Root cause analysis |
| Limitations | Hides composition | Requires more data |

## Why DuPont Matters

Two companies with identical 15% ROE could achieve it very differently:

- **Company A**: High margins (10%), low leverage (1.5×)
- **Company B**: Low margins (3%), high leverage (5×)

Simple ROE hides this risk difference. DuPont reveals that Company B's returns depend heavily on debt financing, which introduces greater financial risk.

## Implementation Reference

This project calculates DuPont components in:

- `financial_analyzer.py:799-821` - ROE and DuPont component calculations
- `visualize_data.py:2236-2335` - DuPont visualization function

### Calculation Details

From the codebase implementation:

```python
# ROE = (Net Income / Stockholders' Equity) × 100%
roe = (net_income / stockholders_equity) * 100

# Component 1: Profit Margin (as decimal)
profit_margin = net_profit_margin_percent / 100

# Component 2: Asset Turnover = Revenue / Total Assets
asset_turnover = net_sales / total_assets

# Component 3: Financial Leverage = Total Assets / Stockholders Equity
financial_leverage = total_assets / stockholders_equity

# Validation: ROE should equal Profit Margin × Asset Turnover × Financial Leverage
calculated_roe = profit_margin * asset_turnover * financial_leverage * 100
```
