"""
Config loader for company-specific pipeline settings.

A single CompanyConfig object is loaded once at the top of the pipeline and
threaded through every stage (fetcher, analyzer, charts, deck).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional

import yaml


@dataclass
class FiscalCalendar:
    """
    year_end_month is the calendar month that CONTAINS the fiscal year-end
    (i.e., the month the 10-K's period-of-report falls in).
      - Target / Walmart: month 2 (period-end Feb 1, fiscal year closes Jan 31)
      - Apple: month 9 (period-end last Saturday of September)
      - Most calendar-year companies: month 12

    convention controls how fiscal years are labeled:
      - "starts_in" (retail): FY2024 STARTS Feb 2024, ends Feb 2025. A 10-K dated
        Feb-2025 is FY2024. Used by Target, Walmart, Kroger.
      - "ends_in" (standard): FY2024 ENDS Sep 2024, started Oct 2023. A 10-K dated
        Sep-2024 is FY2024. Used by Apple, Costco, most companies.

    If convention is omitted, we default to "starts_in" for year_end_month<=3
    (retail) and "ends_in" otherwise.
    """
    year_end_month: int
    year_end_day: int
    convention: str = "starts_in"

    def quarter_for_period_end(self, year: int, month: int) -> Tuple[int, Optional[int]]:
        """
        Return (fiscal_year, fiscal_quarter). fiscal_quarter is None for annual
        periods (10-K) and 1/2/3 for 10-Qs. (Companies generally don't publish a
        Q4 10-Q; the 10-K covers the full year.)
        """
        m = self.year_end_month

        # Is this the annual / year-end month? Then it's a 10-K period.
        if month == m:
            if self.convention == "starts_in":
                return year - 1, None
            return year, None

        # Quarterly: position within fiscal year (1..11 for Q1..Q3 months).
        # Q1 = months m+1..m+3, Q2 = m+4..m+6, Q3 = m+7..m+9.
        pos = (month - m - 1) % 12  # 0..10 for non-annual months
        quarter = pos // 3 + 1  # 1, 2, 3, 4
        if quarter > 3:
            # This would be a Q4 10-Q, which usually doesn't exist; treat as annual.
            quarter = None

        # Fiscal year label
        if self.convention == "starts_in":
            # FY starts month m+1 of calendar year FY. So any quarter-end after m
            # in calendar year Y belongs to FY=Y.
            fiscal_year = year if month > m else year - 1
        else:  # ends_in
            # FY ends month m of calendar year FY. Any quarter-end in or before
            # month m belongs to FY=Y; after belongs to FY=Y+1.
            fiscal_year = year if month <= m else year + 1

        return fiscal_year, quarter

    def format_period_label(self, year: int, month: int) -> str:
        """
        Generate a period label like 'FY2024' or 'Q1 2025' from a period end date.
        """
        fy, q = self.quarter_for_period_end(year, month)
        if q is None:
            return f"FY{fy}"
        return f"Q{q} {fy}"


@dataclass
class Branding:
    primary_color_rgb: Tuple[int, int, int]
    accent_color_rgb: Tuple[int, int, int]


@dataclass
class Download:
    num_10k: int = 10
    num_10q: int = 12


@dataclass
class CompanyConfig:
    name: str
    short_name: str
    ticker: str
    cik: str
    fiscal_calendar: FiscalCalendar
    branding: Branding
    data_dir: str
    peers: List[str] = field(default_factory=list)
    download: Download = field(default_factory=Download)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CompanyConfig":
        path = Path(path)
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        company = raw["company"]
        fc = raw["fiscal_calendar"]
        br = raw["branding"]
        dl = raw.get("download", {}) or {}

        year_end_month = int(fc["year_end_month"])
        convention = fc.get("convention")
        if convention is None:
            convention = "starts_in" if year_end_month <= 3 else "ends_in"

        return cls(
            name=company["name"],
            short_name=company["short_name"],
            ticker=company["ticker"].upper(),
            cik=str(company["cik"]).zfill(10),
            fiscal_calendar=FiscalCalendar(
                year_end_month=year_end_month,
                year_end_day=int(fc["year_end_day"]),
                convention=convention,
            ),
            branding=Branding(
                primary_color_rgb=tuple(br["primary_color_rgb"]),
                accent_color_rgb=tuple(br["accent_color_rgb"]),
            ),
            peers=list(raw.get("peers") or []),
            download=Download(
                num_10k=int(dl.get("num_10k", 10)),
                num_10q=int(dl.get("num_10q", 12)),
            ),
            data_dir=raw.get("data_dir", f"data/{company['ticker']}"),
        )

    def output_path(self, suffix: str) -> str:
        """Compose output path like 'output/{TICKER}_{suffix}'."""
        return f"output/{self.ticker}_{suffix}"
