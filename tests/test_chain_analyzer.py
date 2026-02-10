"""Tests for chain analyzer."""

import pytest
from datetime import date

from options_builder.chain_analyzer import (
    ChainAnalyzer,
    PricedOption,
    PricedChainRow,
    PricedChain,
)
from options_builder.data_connector import (
    OptionLeg,
    OptionChainRow,
    OptionChainGrid,
)


class TestPricedOption:
    """Tests for PricedOption dataclass."""

    def test_creation(self):
        opt = PricedOption(
            strike=100.0, option_type='call',
            bid=4.8, ask=5.2, mid_price=5.0,
            open_interest=1000, volume=500,
            implied_volatility=0.25,
            delta=0.55, gamma=0.02, theta=-0.05, vega=0.20,
            model_price=5.05
        )
        assert opt.strike == 100.0
        assert opt.implied_volatility == 0.25
        assert opt.delta == 0.55


class TestChainAnalyzer:
    """Tests for ChainAnalyzer."""

    def test_price_leg_call(self):
        analyzer = ChainAnalyzer(risk_free_rate=0.05)
        leg = OptionLeg(strike=100, last=5.0, bid=4.8, ask=5.2, open_interest=100)

        priced = analyzer._price_leg(leg, 'call', S=100.0, T=0.1, r=0.05)

        assert priced is not None
        assert priced.implied_volatility > 0
        assert -1 <= priced.delta <= 1
        assert priced.gamma >= 0
        assert priced.vega >= 0

    def test_price_leg_put(self):
        analyzer = ChainAnalyzer(risk_free_rate=0.05)
        leg = OptionLeg(strike=100, last=3.0, bid=2.8, ask=3.2, open_interest=100)

        priced = analyzer._price_leg(leg, 'put', S=100.0, T=0.1, r=0.05)

        assert priced is not None
        assert priced.implied_volatility > 0
        assert -1 <= priced.delta <= 0  # Put delta is negative

    def test_price_leg_zero_price_returns_none(self):
        analyzer = ChainAnalyzer(risk_free_rate=0.05)
        leg = OptionLeg(strike=100, last=0, bid=0, ask=0, open_interest=100)

        priced = analyzer._price_leg(leg, 'call', S=100.0, T=0.1, r=0.05)

        assert priced is None

    def test_analyze_grid(self):
        analyzer = ChainAnalyzer(risk_free_rate=0.05)

        rows = [
            OptionChainRow(
                strike=95.0,
                call=OptionLeg(strike=95, last=8.0, bid=7.8, ask=8.2, open_interest=100),
                put=OptionLeg(strike=95, last=1.5, bid=1.3, ask=1.7, open_interest=150)
            ),
            OptionChainRow(
                strike=100.0,
                call=OptionLeg(strike=100, last=5.0, bid=4.8, ask=5.2, open_interest=200),
                put=OptionLeg(strike=100, last=3.0, bid=2.8, ask=3.2, open_interest=250)
            ),
            OptionChainRow(
                strike=105.0,
                call=OptionLeg(strike=105, last=2.5, bid=2.3, ask=2.7, open_interest=100),
                put=OptionLeg(strike=105, last=6.0, bid=5.8, ask=6.2, open_interest=120)
            ),
        ]
        grid = OptionChainGrid(
            ticker='TEST',
            expiration=date(2026, 3, 20),
            underlying_price=100.0,
            rows=rows
        )

        priced = analyzer.analyze(grid)

        assert priced.ticker == 'TEST'
        assert priced.underlying_price == 100.0
        assert priced.risk_free_rate == 0.05
        assert len(priced) == 3
        assert len(priced.calls()) == 3
        assert len(priced.puts()) == 3

    def test_analyze_skips_illiquid(self):
        analyzer = ChainAnalyzer(risk_free_rate=0.05)

        rows = [
            OptionChainRow(
                strike=100.0,
                call=OptionLeg(strike=100, last=0, bid=0, ask=0, open_interest=0),
                put=OptionLeg(strike=100, last=3.0, bid=2.8, ask=3.2, open_interest=100)
            ),
        ]
        grid = OptionChainGrid(
            ticker='TEST',
            expiration=date(2026, 3, 20),
            underlying_price=100.0,
            rows=rows
        )

        priced = analyzer.analyze(grid)

        assert priced.rows[0].call is None
        assert priced.rows[0].put is not None


class TestPricedChain:
    """Tests for PricedChain dataclass."""

    @pytest.fixture
    def sample_priced_chain(self):
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
        ]
        return PricedChain(
            ticker='TEST',
            expiration=date(2026, 3, 20),
            underlying_price=100.0,
            time_to_maturity=0.1,
            risk_free_rate=0.05,
            rows=rows
        )

    def test_len(self, sample_priced_chain):
        assert len(sample_priced_chain) == 2

    def test_strikes(self, sample_priced_chain):
        assert sample_priced_chain.strikes() == [95.0, 100.0]

    def test_calls(self, sample_priced_chain):
        calls = sample_priced_chain.calls()
        assert len(calls) == 2
        assert all(c.option_type == 'call' for c in calls)

    def test_puts(self, sample_priced_chain):
        puts = sample_priced_chain.puts()
        assert len(puts) == 2
        assert all(p.option_type == 'put' for p in puts)

    def test_get_strike(self, sample_priced_chain):
        row = sample_priced_chain.get_strike(100.0)
        assert row is not None
        assert row.strike == 100.0

    def test_get_strike_not_found(self, sample_priced_chain):
        row = sample_priced_chain.get_strike(999.0)
        assert row is None

    def test_atm_strike(self, sample_priced_chain):
        assert sample_priced_chain.atm_strike() == 100.0
