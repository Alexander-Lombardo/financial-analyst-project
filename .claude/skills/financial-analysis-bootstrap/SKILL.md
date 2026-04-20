---
name: financial-analysis-bootstrap
description: Scaffold and run the financial-analysis pipeline for a new company. TRIGGER when the user says "analyze <Company>", "run this on <TICKER>", or asks to generate a deck for a specific company that does not yet have a config/<ticker>.yaml. Creates the config, runs the three-stage pipeline, and surfaces the deck.
---

# Bootstrap a new company analysis

This project is a generic financial-analysis pipeline. Every stage is driven by a
`config/<ticker>.yaml`. When the user asks to analyze a company that doesn't
already have a config, follow these steps:

## 1. Confirm inputs

Collect, or look up if known:
- Ticker symbol (e.g., `COST`)
- SEC CIK (10 digits with leading zeros). If unknown, look it up at
  https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=<name>&type=10-K
- Fiscal year-end month (calendar month of the 10-K period-of-report)
- Fiscal year convention (`starts_in` for retail/Target-style, `ends_in` for
  everyone else — default by year_end_month ≤ 3)
- Brand color (ask the user or pick a reasonable default)

## 2. Write the config

Create `config/<ticker lowercase>.yaml`. Copy `config/_schema.yaml` as the
template and fill every field. Example shape (see `config/target.yaml` and
`config/walmart.yaml` for working examples).

## 3. Run the pipeline

```bash
python run_analysis.py --config config/<ticker>.yaml
```

The pipeline will:
1. Download 10 years of 10-Ks and 12 quarters of 10-Qs from SEC EDGAR to
   `data/<company>/`
2. Parse XBRL, compute ~30 metrics, write `output/<TICKER>_analysis.json` and
   `_timeseries.json`
3. Generate 24 Plotly charts (HTML + PNG)
4. Build the deck at `output/<TICKER>_Financial_Analysis.pptx`

## 4. Surface the output

Open the deck path and the directory listing of charts. If anything failed,
route the user to the appropriate narrower skill:
- XBRL tags missing: `sec-xbrl-extract`
- Metric looks wrong: `financial-metrics`
- Chart scaling/layout issue: `financial-charts`
- Slide layout issue: `financial-deck`

## Files to read first

- `config_loader.py` — the config dataclass and fiscal calendar helpers
- `run_analysis.py` — pipeline orchestrator
- `config/target.yaml`, `config/walmart.yaml` — reference configs
