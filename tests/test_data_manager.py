"""Tests for DataManager."""

import pytest
import pandas as pd
from datetime import date

from options_builder.data_manager import DataManager
from options_builder.chain_analyzer import (
    PricedChain,
    PricedChainRow,
    PricedOption,
)


@pytest.fixture
def sample_priced_chain():
    """Create a sample PricedChain for testing."""
    rows = [
        PricedChainRow(
            strike=95.0,
            call=PricedOption(
                strike=95.0, option_type='call',
                bid=7.8, ask=8.2, mid_price=8.0,
                open_interest=100, volume=50,
                implied_volatility=0.22, delta=0.65,
                gamma=0.02, theta=-0.04, vega=0.18,
                model_price=8.05
            ),
            put=PricedOption(
                strike=95.0, option_type='put',
                bid=1.3, ask=1.7, mid_price=1.5,
                open_interest=150, volume=30,
                implied_volatility=0.22, delta=-0.35,
                gamma=0.02, theta=-0.03, vega=0.18,
                model_price=1.52
            )
        ),
        PricedChainRow(
            strike=100.0,
            call=PricedOption(
                strike=100.0, option_type='call',
                bid=4.8, ask=5.2, mid_price=5.0,
                open_interest=200, volume=100,
                implied_volatility=0.20, delta=0.50,
                gamma=0.03, theta=-0.05, vega=0.20,
                model_price=5.02
            ),
            put=PricedOption(
                strike=100.0, option_type='put',
                bid=2.8, ask=3.2, mid_price=3.0,
                open_interest=250, volume=80,
                implied_volatility=0.20, delta=-0.50,
                gamma=0.03, theta=-0.04, vega=0.20,
                model_price=3.01
            )
        ),
        PricedChainRow(
            strike=105.0,
            call=PricedOption(
                strike=105.0, option_type='call',
                bid=2.3, ask=2.7, mid_price=2.5,
                open_interest=80, volume=40,
                implied_volatility=0.18, delta=0.35,
                gamma=0.02, theta=-0.03, vega=0.15,
                model_price=2.48
            ),
            put=PricedOption(
                strike=105.0, option_type='put',
                bid=5.8, ask=6.2, mid_price=6.0,
                open_interest=120, volume=60,
                implied_volatility=0.18, delta=-0.65,
                gamma=0.02, theta=-0.04, vega=0.15,
                model_price=5.98
            )
        ),
    ]
    return PricedChain(
        ticker='TEST',
        expiration=date(2026, 3, 20),
        underlying_price=100.0,
        time_to_maturity=0.1,
        risk_free_rate=0.05,
        rows=rows
    )


class TestDataManagerInit:
    """Tests for DataManager initialization."""

    def test_init_empty(self):
        dm = DataManager()
        assert len(dm) == 0
        assert dm.get_cache_keys() == []


class TestDataManagerAddChain:
    """Tests for adding chains to DataManager."""

    def test_add_chain(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        assert len(dm) == 1
        assert ('TEST', date(2026, 3, 20)) in dm

    def test_add_chain_creates_dataframe(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        df = dm.get_chain('TEST', date(2026, 3, 20))
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6  # 3 strikes x 2 types

    def test_add_chain_overwrites_existing(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)
        dm.add_chain(sample_priced_chain)

        assert len(dm) == 1  # Still only one chain

    def test_add_multiple_chains(self, sample_priced_chain):
        dm = DataManager()

        chain1 = sample_priced_chain
        chain2 = PricedChain(
            ticker='TEST',
            expiration=date(2026, 4, 17),  # Different expiration
            underlying_price=100.0,
            time_to_maturity=0.2,
            risk_free_rate=0.05,
            rows=sample_priced_chain.rows
        )

        dm.add_chain(chain1)
        dm.add_chain(chain2)

        assert len(dm) == 2


class TestDataManagerGetChain:
    """Tests for getting chain data."""

    def test_get_chain_found(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        df = dm.get_chain('TEST', date(2026, 3, 20))
        assert df is not None
        assert len(df) == 6

    def test_get_chain_not_found(self):
        dm = DataManager()
        df = dm.get_chain('MISSING', date(2026, 3, 20))
        assert df is None

    def test_get_chain_case_insensitive(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        df = dm.get_chain('test', date(2026, 3, 20))
        assert df is not None


class TestDataManagerGetCallsPuts:
    """Tests for getting calls and puts separately."""

    def test_get_calls(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        calls = dm.get_calls('TEST', date(2026, 3, 20))
        assert calls is not None
        assert len(calls) == 3
        assert all(calls['type'] == 'call')

    def test_get_puts(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        puts = dm.get_puts('TEST', date(2026, 3, 20))
        assert puts is not None
        assert len(puts) == 3
        assert all(puts['type'] == 'put')

    def test_get_calls_not_found(self):
        dm = DataManager()
        calls = dm.get_calls('MISSING', date(2026, 3, 20))
        assert calls is None


class TestDataManagerLookup:
    """Tests for option lookup."""

    def test_lookup_option_call(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        opt = dm.lookup_option('TEST', date(2026, 3, 20), 100.0, 'call')
        assert opt is not None
        assert opt['strike'] == 100.0
        assert opt['type'] == 'call'
        assert opt['delta'] == 0.50
        assert opt['iv'] == 0.20

    def test_lookup_option_put(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        opt = dm.lookup_option('TEST', date(2026, 3, 20), 100.0, 'put')
        assert opt is not None
        assert opt['strike'] == 100.0
        assert opt['type'] == 'put'
        assert opt['delta'] == -0.50

    def test_lookup_option_not_found_strike(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        opt = dm.lookup_option('TEST', date(2026, 3, 20), 999.0, 'call')
        assert opt is None

    def test_lookup_option_not_found_chain(self):
        dm = DataManager()
        opt = dm.lookup_option('MISSING', date(2026, 3, 20), 100.0, 'call')
        assert opt is None


class TestDataManagerStrikes:
    """Tests for strike price retrieval."""

    def test_get_strikes(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        strikes = dm.get_strikes('TEST', date(2026, 3, 20))
        assert strikes == [95.0, 100.0, 105.0]

    def test_get_strikes_not_found(self):
        dm = DataManager()
        strikes = dm.get_strikes('MISSING', date(2026, 3, 20))
        assert strikes == []


class TestDataManagerFilters:
    """Tests for filtering methods."""

    def test_filter_by_delta_calls(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        # Get calls with delta between 0.4 and 0.6
        df = dm.filter_by_delta('TEST', date(2026, 3, 20), 0.4, 0.6, 'call')
        assert df is not None
        assert len(df) == 1
        assert df.iloc[0]['strike'] == 100.0

    def test_filter_by_delta_all_types(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        # Get all options with delta in range -0.55 to 0.55
        # 95P: -0.35, 100C: 0.50, 100P: -0.50, 105C: 0.35 are all in range
        df = dm.filter_by_delta('TEST', date(2026, 3, 20), -0.55, 0.55)
        assert df is not None
        assert len(df) == 4

    def test_filter_by_liquidity(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        # Filter by open interest >= 150
        df = dm.filter_by_liquidity('TEST', date(2026, 3, 20), min_oi=150)
        assert df is not None
        assert len(df) == 3  # 95P (150), 100C (200), 100P (250)

    def test_filter_by_liquidity_spread(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        # All options in sample have ~5-16% spread, filter for tight spreads
        df = dm.filter_by_liquidity('TEST', date(2026, 3, 20), max_spread_pct=0.10)
        assert df is not None
        # Should filter out some options with wider spreads


class TestDataManagerCache:
    """Tests for cache management."""

    def test_clear_cache_all(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        dm.clear_cache()
        assert len(dm) == 0

    def test_clear_cache_by_ticker(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        chain2 = PricedChain(
            ticker='OTHER',
            expiration=date(2026, 3, 20),
            underlying_price=50.0,
            time_to_maturity=0.1,
            risk_free_rate=0.05,
            rows=[]
        )
        dm.add_chain(chain2)

        dm.clear_cache(ticker='TEST')
        assert len(dm) == 1
        assert ('OTHER', date(2026, 3, 20)) in dm

    def test_contains(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        assert ('TEST', date(2026, 3, 20)) in dm
        assert ('MISSING', date(2026, 3, 20)) not in dm


class TestDataManagerDataFrame:
    """Tests for DataFrame structure and content."""

    def test_dataframe_columns(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        df = dm.get_chain('TEST', date(2026, 3, 20))
        expected_cols = [
            'ticker', 'expiration', 'type', 'strike',
            'bid', 'ask', 'mid', 'iv',
            'delta', 'gamma', 'theta', 'vega',
            'open_interest', 'volume', 'model_price',
            'underlying_price', 'time_to_maturity', 'risk_free_rate'
        ]
        assert list(df.columns) == expected_cols

    def test_dataframe_values(self, sample_priced_chain):
        dm = DataManager()
        dm.add_chain(sample_priced_chain)

        df = dm.get_chain('TEST', date(2026, 3, 20))

        # Check a specific row
        call_100 = df[(df['strike'] == 100.0) & (df['type'] == 'call')].iloc[0]
        assert call_100['ticker'] == 'TEST'
        assert call_100['bid'] == 4.8
        assert call_100['ask'] == 5.2
        assert call_100['mid'] == 5.0
        assert call_100['iv'] == 0.20
        assert call_100['delta'] == 0.50
        assert call_100['underlying_price'] == 100.0
