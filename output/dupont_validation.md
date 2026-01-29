# DuPont Analysis Validation Report

**Company**: Target Corporation (TGT)
**Periods Analyzed**: FY2020 - FY2024
**Generated**: Automated validation tool

---

## DuPont Formula

```
ROE = Profit Margin x Asset Turnover x Financial Leverage

Where:
  Profit Margin      = Net Income / Revenue
  Asset Turnover     = Revenue / Average Total Assets
  Financial Leverage = Average Total Assets / Average Stockholders Equity
  ROE (direct)       = Net Income / Average Stockholders Equity

Average = (Beginning of Year + End of Year) / 2
```

**Note**: Average values are used for balance sheet items (Assets, Equity) because
income statement items (Revenue, Net Income) are flow values over the entire period,
while balance sheet items are point-in-time snapshots.

---

## FY2024 — For the fiscal year ended February 1, 2025

### Raw Data Extracted from SEC 10-K Filing

| Metric | Value | GAAP Tag |
|--------|-------|----------|
| Net Income | $4.091B | us-gaap:NetIncomeLoss |
| Revenue | $106.566B | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |
| Total Assets (End of Year) | $57.769B | us-gaap:Assets |
| Stockholders Equity (End of Year) | $14.666B | us-gaap:StockholdersEquity |
| Total Assets (Prior Year End) | $55.356B | — |
| **Average Total Assets** | **$56.562B** | (Prior + Current) / 2 |
| Stockholders Equity (Prior Year End) | $13.432B | — |
| **Average Stockholders Equity** | **$14.049B** | (Prior + Current) / 2 |

### DuPont Component Calculations

**1. Profit Margin**
- Formula: Net Income / Revenue x 100
- Calculation: $4.091B / $106.566B x 100
- Result: **3.84%**

**2. Asset Turnover**
- Formula: Revenue / Average Total Assets
- Average Total Assets: ($55.356B + $57.769B) / 2 = $56.562B
- Calculation: $106.566B / $56.562B
- Result: **1.88x**

**3. Financial Leverage**
- Formula: Average Total Assets / Average Stockholders Equity
- Avg Total Assets: ($55.356B + $57.769B) / 2 = $56.562B
- Avg Stockholders Equity: ($13.432B + $14.666B) / 2 = $14.049B
- Calculation: $56.562B / $14.049B
- Result: **4.03x**

**4. ROE Validation**
- Formula: Profit Margin x Asset Turnover x Financial Leverage
- Calculation: 3.8389% x 1.8840 x 4.0261
- Calculated ROE (DuPont): **29.12%**
- Direct ROE (NI/Equity): **29.12%**
- Variance: 0.00% PASS

### Validation Against Extracted Values

| Component | Calculated | Extracted | Match |
|-----------|------------|-----------|-------|
| Profit Margin | 3.84% | 3.84% | Y |
| Asset Turnover | 1.88x | 1.84x | Y |
| Financial Leverage | 4.03x | 3.94x | Y |
| ROE | 29.12% | 27.89% | N |

---

## FY2023 — For the fiscal year ended February 3, 2024

### Raw Data Extracted from SEC 10-K Filing

| Metric | Value | GAAP Tag |
|--------|-------|----------|
| Net Income | $4.138B | us-gaap:NetIncomeLoss |
| Revenue | $105.803B | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |
| Total Assets (End of Year) | $55.356B | us-gaap:Assets |
| Stockholders Equity (End of Year) | $13.432B | us-gaap:StockholdersEquity |
| Total Assets (Prior Year End) | $53.335B | — |
| **Average Total Assets** | **$54.346B** | (Prior + Current) / 2 |
| Stockholders Equity (Prior Year End) | $11.232B | — |
| **Average Stockholders Equity** | **$12.332B** | (Prior + Current) / 2 |

### DuPont Component Calculations

**1. Profit Margin**
- Formula: Net Income / Revenue x 100
- Calculation: $4.138B / $105.803B x 100
- Result: **3.91%**

**2. Asset Turnover**
- Formula: Revenue / Average Total Assets
- Average Total Assets: ($53.335B + $55.356B) / 2 = $54.346B
- Calculation: $105.803B / $54.346B
- Result: **1.95x**

**3. Financial Leverage**
- Formula: Average Total Assets / Average Stockholders Equity
- Avg Total Assets: ($53.335B + $55.356B) / 2 = $54.346B
- Avg Stockholders Equity: ($11.232B + $13.432B) / 2 = $12.332B
- Calculation: $54.346B / $12.332B
- Result: **4.41x**

**4. ROE Validation**
- Formula: Profit Margin x Asset Turnover x Financial Leverage
- Calculation: 3.9110% x 1.9469 x 4.4069
- Calculated ROE (DuPont): **33.55%**
- Direct ROE (NI/Equity): **33.55%**
- Variance: 0.00% PASS

### Validation Against Extracted Values

| Component | Calculated | Extracted | Match |
|-----------|------------|-----------|-------|
| Profit Margin | 3.91% | 3.91% | Y |
| Asset Turnover | 1.95x | 1.91x | Y |
| Financial Leverage | 4.41x | 4.12x | N |
| ROE | 33.55% | 30.81% | N |

---

## FY2022 — For the fiscal year ended January 28, 2023

### Raw Data Extracted from SEC 10-K Filing

| Metric | Value | GAAP Tag |
|--------|-------|----------|
| Net Income | $2.780B | us-gaap:NetIncomeLoss |
| Revenue | $107.588B | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |
| Total Assets (End of Year) | $53.335B | us-gaap:Assets |
| Stockholders Equity (End of Year) | $11.232B | us-gaap:StockholdersEquity |
| Total Assets (Prior Year End) | $53.811B | — |
| **Average Total Assets** | **$53.573B** | (Prior + Current) / 2 |
| Stockholders Equity (Prior Year End) | $12.827B | — |
| **Average Stockholders Equity** | **$12.029B** | (Prior + Current) / 2 |

### DuPont Component Calculations

**1. Profit Margin**
- Formula: Net Income / Revenue x 100
- Calculation: $2.780B / $107.588B x 100
- Result: **2.58%**

**2. Asset Turnover**
- Formula: Revenue / Average Total Assets
- Average Total Assets: ($53.811B + $53.335B) / 2 = $53.573B
- Calculation: $107.588B / $53.573B
- Result: **2.01x**

**3. Financial Leverage**
- Formula: Average Total Assets / Average Stockholders Equity
- Avg Total Assets: ($53.811B + $53.335B) / 2 = $53.573B
- Avg Stockholders Equity: ($12.827B + $11.232B) / 2 = $12.029B
- Calculation: $53.573B / $12.029B
- Result: **4.45x**

**4. ROE Validation**
- Formula: Profit Margin x Asset Turnover x Financial Leverage
- Calculation: 2.5839% x 2.0083 x 4.4535
- Calculated ROE (DuPont): **23.11%**
- Direct ROE (NI/Equity): **23.11%**
- Variance: 0.00% PASS

### Validation Against Extracted Values

| Component | Calculated | Extracted | Match |
|-----------|------------|-----------|-------|
| Profit Margin | 2.58% | 2.58% | Y |
| Asset Turnover | 2.01x | 2.02x | Y |
| Financial Leverage | 4.45x | 4.75x | N |
| ROE | 23.11% | 24.75% | N |

---

## FY2021 — For the fiscal year ended January 29, 2022

### Raw Data Extracted from SEC 10-K Filing

| Metric | Value | GAAP Tag |
|--------|-------|----------|
| Net Income | $6.946B | us-gaap:NetIncomeLoss |
| Revenue | $104.611B | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |
| Total Assets (End of Year) | $53.811B | us-gaap:Assets |
| Stockholders Equity (End of Year) | $12.827B | us-gaap:StockholdersEquity |
| Total Assets (Prior Year End) | $51.248B | — |
| **Average Total Assets** | **$52.529B** | (Prior + Current) / 2 |
| Stockholders Equity (Prior Year End) | $14.440B | — |
| **Average Stockholders Equity** | **$13.633B** | (Prior + Current) / 2 |

### DuPont Component Calculations

**1. Profit Margin**
- Formula: Net Income / Revenue x 100
- Calculation: $6.946B / $104.611B x 100
- Result: **6.64%**

**2. Asset Turnover**
- Formula: Revenue / Average Total Assets
- Average Total Assets: ($51.248B + $53.811B) / 2 = $52.529B
- Calculation: $104.611B / $52.529B
- Result: **1.99x**

**3. Financial Leverage**
- Formula: Average Total Assets / Average Stockholders Equity
- Avg Total Assets: ($51.248B + $53.811B) / 2 = $52.529B
- Avg Stockholders Equity: ($14.440B + $12.827B) / 2 = $13.633B
- Calculation: $52.529B / $13.633B
- Result: **3.85x**

**4. ROE Validation**
- Formula: Profit Margin x Asset Turnover x Financial Leverage
- Calculation: 6.6398% x 1.9915 x 3.8530
- Calculated ROE (DuPont): **50.95%**
- Direct ROE (NI/Equity): **50.95%**
- Variance: 0.00% PASS

### Validation Against Extracted Values

| Component | Calculated | Extracted | Match |
|-----------|------------|-----------|-------|
| Profit Margin | 6.64% | 6.64% | Y |
| Asset Turnover | 1.99x | 1.94x | Y |
| Financial Leverage | 3.85x | 4.2x | N |
| ROE | 50.95% | 54.15% | N |

---

## FY2020 — For the fiscal year ended January 30, 2021

### Raw Data Extracted from SEC 10-K Filing

| Metric | Value | GAAP Tag |
|--------|-------|----------|
| Net Income | $4.368B | us-gaap:NetIncomeLoss |
| Revenue | $92.400B | us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |
| Total Assets (End of Year) | $51.248B | us-gaap:Assets |
| Stockholders Equity (End of Year) | $14.440B | us-gaap:StockholdersEquity |
| **Average Total Assets** | **$51.248B** | *(First year: using end of year)* |
| **Average Stockholders Equity** | **$14.440B** | *(First year: using end of year)* |

### DuPont Component Calculations

**1. Profit Margin**
- Formula: Net Income / Revenue x 100
- Calculation: $4.368B / $92.400B x 100
- Result: **4.73%**

**2. Asset Turnover**
- Formula: Revenue / Average Total Assets
- Average Total Assets: $51.248B *(first year: using end of year)*
- Calculation: $92.400B / $51.248B
- Result: **1.80x**

**3. Financial Leverage**
- Formula: Average Total Assets / Average Stockholders Equity
- Using end of year values *(first year: no prior year average available)*
- Calculation: $51.248B / $14.440B
- Result: **3.55x**

**4. ROE Validation**
- Formula: Profit Margin x Asset Turnover x Financial Leverage
- Calculation: 4.7273% x 1.8030 x 3.5490
- Calculated ROE (DuPont): **30.25%**
- Direct ROE (NI/Equity): **30.25%**
- Variance: 0.00% PASS

### Validation Against Extracted Values

| Component | Calculated | Extracted | Match |
|-----------|------------|-----------|-------|
| Profit Margin | 4.73% | 4.73% | Y |
| Asset Turnover | 1.80x | 1.8x | Y |
| Financial Leverage | 3.55x | 3.55x | Y |
| ROE | 30.25% | 30.25% | Y |

---

## Summary: 5-Year DuPont Trend

| Period | Profit Margin | Asset Turnover | Financial Leverage | ROE |
|--------|---------------|----------------|--------------------|----|
| FY2020 (ended January 30, 2021) | 4.73% | 1.80x | 3.55x | 30.25% |
| FY2021 (ended January 29, 2022) | 6.64% | 1.99x | 3.85x | 50.95% |
| FY2022 (ended January 28, 2023) | 2.58% | 2.01x | 4.45x | 23.11% |
| FY2023 (ended February 3, 2024) | 3.91% | 1.95x | 4.41x | 33.55% |
| FY2024 (ended February 1, 2025) | 3.84% | 1.88x | 4.03x | 29.12% |

---

## Key Observations

**ROE Change (FY2020 to FY2024)**: -1.13%

**Component Drivers**:
- Profit Margin: -0.89% (declining)
- Asset Turnover: +0.08x (improving)
- Financial Leverage: +0.48x (increasing)