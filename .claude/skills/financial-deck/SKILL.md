---
name: financial-deck
description: Modify PowerPoint slide layouts, pillar structure, or summary copy. TRIGGER when the user asks about the deck — slide order, pillar summaries, thesis rating logic, title/executive slide content, or chart embedding behavior. Scope is `create_presentation.py`.
---

# Deck structure

The deck has 37 slides:
- 3 intro slides: title, executive summary, investment thesis
- 5 pillar section dividers + 24 chart slides + 5 pillar summary slides

All 5 pillars share the same shape: a banner slide, N chart slides, then a
"Key Takeaways" summary slide.

## Data-driven copy

`build_pillar_summaries(timeseries, cfg)` computes the 4 bullets per pillar
from actual metric values (not hardcoded prose). Helpers:
- `_first_last(series)` — first and last non-None in a series
- `_min_max(series)` — min/max across the window
- `_latest(series)` — most recent non-None value

If you need to add a new finding, compute it from `timeseries['metrics'][...]`
and emit a `(title, detail)` tuple.

## Investment thesis

`generate_thesis(data, timeseries)` scores four measurable signals and emits
BUY / HOLD / SELL:
- operating margin (latest)
- debt/EBITDA (latest)
- interest coverage (latest)
- ROE (latest)

Signals are collected into `positives` and `negatives` lists and rendered on
the thesis slide. Thresholds live in the function — adjust them if benchmarks
differ by industry.

## Branding

All color sites use `_rgb(cfg, 'primary')` or `_rgb(cfg, 'accent')`. Never
hardcode `RGBColor(...)` with literal RGB values; pull from the config.

## Chart slide embedding

`_add_chart_slide` looks for a PNG next to the HTML. PNG generation requires
`kaleido` (installed via `requirements.txt`). If the PNG is missing, the slide
falls back to a hyperlink-only layout.

## Key files

- `create_presentation.py` (all of it)
- `config_loader.py:Branding` — the dataclass carrying color tuples
