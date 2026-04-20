---
name: sec-xbrl-extract
description: Help with SEC XBRL tag extraction. TRIGGER when the user asks about XBRL tags, GAAP taxonomy mappings, missing metrics, or "why didn't X get extracted for <company>". Focus on `financial_analyzer.py` `GAAP_MAPPINGS` and the `_extract_xbrl_value` extractor (modern iXBRL + legacy XML).
---

# Debug and extend XBRL extraction

## The data flow

1. `sec_data_fetcher.py` downloads filings into
   `data/<company>/sec-edgar-filings/<TICKER>/(10-K|10-Q)/<accession>/`
2. The primary XBRL file is `primary-document.html` (modern iXBRL) plus
   `full-submission.txt` (legacy XML for older filings).
3. `FinancialAnalyzer._extract_vital_signs` iterates `GAAP_MAPPINGS` and calls
   `_extract_xbrl_value(soup, gaap_tag, raw_content)` for each.

## GAAP_MAPPINGS in `financial_analyzer.py`

The mapping goes: `us-gaap:<TagName>` → friendly field name (stored as
`<name>_billion` after conversion).

Common issues:
- Different companies use different canonical tags for the same concept (e.g.
  `Revenues` vs `SalesRevenueNet` vs `RevenueFromContractWithCustomerExcludingAssessedTax`).
- When a metric comes back as None for a specific company, open a sample
  filing from `data/<company>/.../primary-document.html`, search for the
  concept's tag, and add the tag alias to `GAAP_MAPPINGS`.
- Dimensional tags (with `<segment>` in the context) are deliberately
  deprioritized in favor of consolidated tags.

## How to diagnose a missing metric

1. Load the timeseries JSON: `output/<TICKER>_timeseries.json`
2. Find the None or null in the relevant metric series
3. Open the filing directory for that period under `data/<company>/`
4. Grep for any likely tag name variants:
   ```
   Grep pattern="name=\"us-gaap:[A-Z]*Capex" in the filing
   ```
5. Add the discovered tag to `GAAP_MAPPINGS` with the existing friendly name
6. Re-run the analysis stage only: `python financial_analyzer.py --config <cfg>`

## Key files

- `financial_analyzer.py:329-383` — GAAP_MAPPINGS dict
- `financial_analyzer.py:435-558` — `_extract_xbrl_value` (iXBRL + legacy XML)
- `xbrl_parser.py` — additional XBRL helpers
