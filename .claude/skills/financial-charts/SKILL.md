---
name: financial-charts
description: Add, modify, or debug Plotly charts. TRIGGER when the user asks to tweak a chart, add a new one, adjust axis scaling, fix a missing-data glitch, or re-brand chart colors. Scope is `visualize_data.py` — all 24 `create_*` chart builders.
---

# Chart conventions

## Branding pulled from data

Every chart function receives the `data` (timeseries) dict as its first
argument. Company identity and brand color live in `data['metadata']`:

- `_company(data)` — short company name for titles (e.g., "Target")
- `_primary_rgb(data)` — CSS rgb() string for brand primary color
- `data['metadata']['ticker']` — uppercase ticker
- `data['metadata']['_detailed_path']` — path to `<TICKER>_analysis.json`
  (used by the two risk charts that need the detailed JSON)

Do **not** hardcode "Target:", "TGT", or `RGBColor(204, 0, 0)` — pull from
metadata.

## Period sort key

Use `sec_data_fetcher.period_sort_key` anywhere you need chronological order.
It places the annual 10-K AFTER the fiscal year's Q3 (which is chronologically
correct since the 10-K period-of-report is dated in the year-end month).

## Unit conventions on y-axes

Prefer one of:
- `"$ Billions"` or `"$B"` for dollar amounts
- `"%"` or `"<metric> %"` for ratios/margins
- `"x"` (or `"(x)"`) for turnover/coverage ratios
- `"days"` for DSI/DSO/DPO/CCC

Be consistent within a single chart.

## Missing-data handling

When an array has `None` values, pass `connectgaps=False` so lines don't
interpolate across gaps. Don't silently filter out periods.

## Output contract

`export_chart(fig, "output/chart_<name>.html")` writes both the HTML and a PNG
(via kaleido) for deck embedding.

## Adding a new chart

1. Write `create_<name>_chart(data)` following the existing patterns
2. Call it from `run_charts()` in the `main()` region
3. Add an entry to `CHART_CONFIG` in `create_presentation.py` under the right
   pillar so it lands in the deck

## Key files

- `visualize_data.py` — all 24 chart builders, helpers at top of file
- `sec_data_fetcher.py:9-37` — `period_sort_key`
