"""Tests for strategy template factory functions."""

import pytest
import numpy as np
from datetime import date

from options_builder.templates import (
    bull_call_spread,
    bear_call_spread,
    bull_put_spread,
    bear_put_spread,
    long_straddle,
    short_straddle,
    long_strangle,
    short_strangle,
    iron_condor,
    iron_butterfly,
)
from options_builder.data_manager import DataManager
from options_builder.chain_analyzer import PricedChain, PricedChainRow, PricedOption


@pytest.fixture
def sample_dm():
    """DataManager with sample chain for testing templates."""
    dm = DataManager()
    rows = [
        PricedChainRow(
            strike=490.0,
            call=PricedOption(
                strike=490.0, option_type='call',
                bid=14.80, ask=15.20, mid_price=15.0,
                open_interest=400, volume=150,
                implied_volatility=0.24, delta=0.75,
                gamma=0.015, theta=-0.03, vega=0.16,
                model_price=15.02
            ),
            put=PricedOption(
                strike=490.0, option_type='put',
                bid=1.30, ask=1.70, mid_price=1.5,
                open_interest=500, volume=100,
                implied_volatility=0.24, delta=-0.25,
                gamma=0.015, theta=-0.02, vega=0.16,
                model_price=1.52
            )
        ),
        PricedChainRow(
            strike=495.0,
            call=PricedOption(
                strike=495.0, option_type='call',
                bid=9.80, ask=10.20, mid_price=10.0,
                open_interest=500, volume=200,
                implied_volatility=0.22, delta=0.65,
                gamma=0.02, theta=-0.04, vega=0.18,
                model_price=10.05
            ),
            put=PricedOption(
                strike=495.0, option_type='put',
                bid=2.30, ask=2.70, mid_price=2.5,
                open_interest=600, volume=150,
                implied_volatility=0.22, delta=-0.35,
                gamma=0.02, theta=-0.03, vega=0.18,
                model_price=2.52
            )
        ),
        PricedChainRow(
            strike=500.0,
            call=PricedOption(
                strike=500.0, option_type='call',
                bid=4.80, ask=5.20, mid_price=5.0,
                open_interest=1000, volume=500,
                implied_volatility=0.20, delta=0.50,
                gamma=0.03, theta=-0.05, vega=0.20,
                model_price=5.02
            ),
            put=PricedOption(
                strike=500.0, option_type='put',
                bid=4.80, ask=5.20, mid_price=5.0,
                open_interest=1200, volume=400,
                implied_volatility=0.20, delta=-0.50,
                gamma=0.03, theta=-0.04, vega=0.20,
                model_price=5.01
            )
        ),
        PricedChainRow(
            strike=505.0,
            call=PricedOption(
                strike=505.0, option_type='call',
                bid=2.30, ask=2.70, mid_price=2.5,
                open_interest=800, volume=300,
                implied_volatility=0.18, delta=0.35,
                gamma=0.02, theta=-0.03, vega=0.15,
                model_price=2.48
            ),
            put=PricedOption(
                strike=505.0, option_type='put',
                bid=9.80, ask=10.20, mid_price=10.0,
                open_interest=400, volume=100,
                implied_volatility=0.18, delta=-0.65,
                gamma=0.02, theta=-0.04, vega=0.15,
                model_price=9.98
            )
        ),
        PricedChainRow(
            strike=510.0,
            call=PricedOption(
                strike=510.0, option_type='call',
                bid=1.30, ask=1.70, mid_price=1.5,
                open_interest=600, volume=200,
                implied_volatility=0.17, delta=0.25,
                gamma=0.015, theta=-0.02, vega=0.12,
                model_price=1.48
            ),
            put=PricedOption(
                strike=510.0, option_type='put',
                bid=14.80, ask=15.20, mid_price=15.0,
                open_interest=300, volume=80,
                implied_volatility=0.17, delta=-0.75,
                gamma=0.015, theta=-0.03, vega=0.12,
                model_price=14.98
            )
        ),
    ]
    chain = PricedChain(
        ticker='SPY',
        expiration=date(2026, 3, 20),
        underlying_price=500.0,
        time_to_maturity=0.1,
        risk_free_rate=0.05,
        rows=rows
    )
    dm.add_chain(chain)
    return dm


class TestBullCallSpread:
    """Tests for bull_call_spread template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        assert strategy is not None
        assert len(strategy) == 2
        assert strategy.name == 'Bull Call Spread'

    def test_leg_structure(self, sample_dm):
        strategy = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        # Long lower strike call
        long_leg = strategy.get_leg(500.0, 'call')
        assert long_leg is not None
        assert long_leg.is_long
        assert long_leg.quantity == 1

        # Short higher strike call
        short_leg = strategy.get_leg(505.0, 'call')
        assert short_leg is not None
        assert short_leg.is_short
        assert short_leg.quantity == -1

    def test_is_debit_spread(self, sample_dm):
        strategy = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        assert strategy.is_debit
        # Long 500C: pay ask 5.20 × 100 = 520
        # Short 505C: receive bid 2.30 × 100 = -230
        # Net: 290 (debit)
        assert strategy.net_premium == pytest.approx(290.0)

    def test_positive_delta(self, sample_dm):
        """Bull call spread should have positive (bullish) delta."""
        strategy = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        # Long 500C delta: 0.50 × 1 × 100 = 50
        # Short 505C delta: 0.35 × -1 × 100 = -35
        # Total: 15
        assert strategy.total_delta == pytest.approx(15.0)

    def test_bounded_pnl(self, sample_dm):
        """Max profit and loss should be bounded."""
        strategy = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        # Max profit = spread width - net debit = 500 - 290 = 210
        assert strategy.max_profit == pytest.approx(210.0)

        # Max loss = net debit = 290
        assert strategy.max_loss == pytest.approx(290.0)

    def test_pnl_profile(self, sample_dm):
        """P&L constant below lower strike and above upper strike."""
        strategy = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        prices = np.array([480.0, 490.0, 510.0, 520.0])
        pnl = strategy.calculate_pnl(prices)

        # Below 500: max loss
        assert pnl[0] == pnl[1]

        # Above 505: max profit
        assert pnl[2] == pnl[3]

    def test_single_breakeven(self, sample_dm):
        strategy = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        breakevens = strategy.breakeven_points
        assert len(breakevens) == 1
        # Breakeven = lower strike + net debit per share = 500 + 2.90 = 502.90
        assert breakevens[0] == pytest.approx(502.9, rel=0.01)

    def test_invalid_strikes_raises(self, sample_dm):
        with pytest.raises(ValueError):
            bull_call_spread(
                sample_dm, 'SPY', date(2026, 3, 20), 505.0, 500.0
            )

    def test_missing_option_returns_none(self, sample_dm):
        result = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 999.0
        )
        assert result is None

    def test_quantity_multiplier(self, sample_dm):
        strategy = bull_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0, quantity=2
        )

        assert strategy.get_leg(500.0, 'call').quantity == 2
        assert strategy.get_leg(505.0, 'call').quantity == -2
        assert strategy.net_premium == pytest.approx(580.0)  # 290 × 2


class TestBearCallSpread:
    """Tests for bear_call_spread template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = bear_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        assert strategy is not None
        assert len(strategy) == 2
        assert strategy.name == 'Bear Call Spread'

    def test_leg_structure(self, sample_dm):
        strategy = bear_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        # Short lower strike call
        short_leg = strategy.get_leg(500.0, 'call')
        assert short_leg.is_short
        assert short_leg.quantity == -1

        # Long higher strike call
        long_leg = strategy.get_leg(505.0, 'call')
        assert long_leg.is_long
        assert long_leg.quantity == 1

    def test_is_credit_spread(self, sample_dm):
        strategy = bear_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        assert strategy.is_credit
        # Short 500C: receive bid 4.80 × 100 = -480
        # Long 505C: pay ask 2.70 × 100 = 270
        # Net: -210 (credit)
        assert strategy.net_premium == pytest.approx(-210.0)

    def test_negative_delta(self, sample_dm):
        """Bear call spread should have negative (bearish) delta."""
        strategy = bear_call_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0, 505.0
        )

        # Short 500C delta: 0.50 × -1 × 100 = -50
        # Long 505C delta: 0.35 × 1 × 100 = 35
        # Total: -15
        assert strategy.total_delta == pytest.approx(-15.0)


class TestBullPutSpread:
    """Tests for bull_put_spread template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = bull_put_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 500.0
        )

        assert strategy is not None
        assert len(strategy) == 2
        assert strategy.name == 'Bull Put Spread'

    def test_leg_structure(self, sample_dm):
        strategy = bull_put_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 500.0
        )

        # Long lower strike put
        long_leg = strategy.get_leg(495.0, 'put')
        assert long_leg.is_long
        assert long_leg.quantity == 1

        # Short higher strike put
        short_leg = strategy.get_leg(500.0, 'put')
        assert short_leg.is_short
        assert short_leg.quantity == -1

    def test_is_credit_spread(self, sample_dm):
        strategy = bull_put_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 500.0
        )

        assert strategy.is_credit
        # Long 495P: pay ask 2.70 × 100 = 270
        # Short 500P: receive bid 4.80 × 100 = -480
        # Net: -210 (credit)
        assert strategy.net_premium == pytest.approx(-210.0)

    def test_positive_delta(self, sample_dm):
        """Bull put spread should have positive (bullish) delta."""
        strategy = bull_put_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 500.0
        )

        # Long 495P delta: -0.35 × 1 × 100 = -35
        # Short 500P delta: -0.50 × -1 × 100 = 50
        # Total: 15
        assert strategy.total_delta == pytest.approx(15.0)


class TestBearPutSpread:
    """Tests for bear_put_spread template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = bear_put_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 500.0
        )

        assert strategy is not None
        assert len(strategy) == 2
        assert strategy.name == 'Bear Put Spread'

    def test_leg_structure(self, sample_dm):
        strategy = bear_put_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 500.0
        )

        # Short lower strike put
        short_leg = strategy.get_leg(495.0, 'put')
        assert short_leg.is_short

        # Long higher strike put
        long_leg = strategy.get_leg(500.0, 'put')
        assert long_leg.is_long

    def test_is_debit_spread(self, sample_dm):
        strategy = bear_put_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 500.0
        )

        assert strategy.is_debit
        # Short 495P: receive bid 2.30 × 100 = -230
        # Long 500P: pay ask 5.20 × 100 = 520
        # Net: 290 (debit)
        assert strategy.net_premium == pytest.approx(290.0)

    def test_negative_delta(self, sample_dm):
        """Bear put spread should have negative (bearish) delta."""
        strategy = bear_put_spread(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 500.0
        )

        # Short 495P delta: -0.35 × -1 × 100 = 35
        # Long 500P delta: -0.50 × 1 × 100 = -50
        # Total: -15
        assert strategy.total_delta == pytest.approx(-15.0)


class TestLongStraddle:
    """Tests for long_straddle template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = long_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        assert strategy is not None
        assert len(strategy) == 2
        assert strategy.name == 'Long Straddle'

    def test_leg_structure(self, sample_dm):
        strategy = long_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        call_leg = strategy.get_leg(500.0, 'call')
        put_leg = strategy.get_leg(500.0, 'put')

        assert call_leg.is_long
        assert put_leg.is_long
        assert call_leg.strike == put_leg.strike

    def test_is_debit(self, sample_dm):
        strategy = long_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        assert strategy.is_debit
        # Long 500C: pay ask 5.20 × 100 = 520
        # Long 500P: pay ask 5.20 × 100 = 520
        # Net: 1040 (debit)
        assert strategy.net_premium == pytest.approx(1040.0)

    def test_near_zero_delta(self, sample_dm):
        """ATM straddle should have near-zero delta."""
        strategy = long_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        # Long 500C delta: 0.50 × 1 × 100 = 50
        # Long 500P delta: -0.50 × 1 × 100 = -50
        # Total: 0
        assert strategy.total_delta == pytest.approx(0.0)

    def test_long_gamma_and_vega(self, sample_dm):
        """Long straddle should be long gamma and vega."""
        strategy = long_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        assert strategy.total_gamma > 0
        assert strategy.total_vega > 0

    def test_two_breakevens(self, sample_dm):
        """Straddle has breakevens on both sides."""
        strategy = long_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        breakevens = strategy.breakeven_points
        assert len(breakevens) == 2
        # Lower breakeven = strike - premium per share
        # Upper breakeven = strike + premium per share
        assert breakevens[0] < 500.0
        assert breakevens[1] > 500.0


class TestShortStraddle:
    """Tests for short_straddle template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = short_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        assert strategy is not None
        assert len(strategy) == 2
        assert strategy.name == 'Short Straddle'

    def test_leg_structure(self, sample_dm):
        strategy = short_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        call_leg = strategy.get_leg(500.0, 'call')
        put_leg = strategy.get_leg(500.0, 'put')

        assert call_leg.is_short
        assert put_leg.is_short

    def test_is_credit(self, sample_dm):
        strategy = short_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        assert strategy.is_credit
        # Short 500C: receive bid 4.80 × 100 = -480
        # Short 500P: receive bid 4.80 × 100 = -480
        # Net: -960 (credit)
        assert strategy.net_premium == pytest.approx(-960.0)

    def test_short_gamma_and_vega(self, sample_dm):
        """Short straddle should be short gamma and vega."""
        strategy = short_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        assert strategy.total_gamma < 0
        assert strategy.total_vega < 0

    def test_unlimited_loss(self, sample_dm):
        """Short straddle has unlimited loss potential."""
        strategy = short_straddle(
            sample_dm, 'SPY', date(2026, 3, 20), 500.0
        )

        assert strategy.max_loss is None  # Unlimited


class TestLongStrangle:
    """Tests for long_strangle template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = long_strangle(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 505.0
        )

        assert strategy is not None
        assert len(strategy) == 2
        assert strategy.name == 'Long Strangle'

    def test_leg_structure(self, sample_dm):
        strategy = long_strangle(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 505.0
        )

        put_leg = strategy.get_leg(495.0, 'put')
        call_leg = strategy.get_leg(505.0, 'call')

        assert put_leg.is_long
        assert call_leg.is_long

    def test_is_debit(self, sample_dm):
        strategy = long_strangle(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 505.0
        )

        assert strategy.is_debit
        # Long 495P: pay ask 2.70 × 100 = 270
        # Long 505C: pay ask 2.70 × 100 = 270
        # Net: 540 (debit)
        assert strategy.net_premium == pytest.approx(540.0)

    def test_invalid_strikes_raises(self, sample_dm):
        with pytest.raises(ValueError):
            long_strangle(
                sample_dm, 'SPY', date(2026, 3, 20), 505.0, 495.0
            )

    def test_near_zero_delta(self, sample_dm):
        """Symmetric strangle should have near-zero delta."""
        strategy = long_strangle(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 505.0
        )

        # Long 495P delta: -0.35 × 1 × 100 = -35
        # Long 505C delta: 0.35 × 1 × 100 = 35
        # Total: 0
        assert strategy.total_delta == pytest.approx(0.0)


class TestShortStrangle:
    """Tests for short_strangle template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = short_strangle(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 505.0
        )

        assert strategy is not None
        assert len(strategy) == 2
        assert strategy.name == 'Short Strangle'

    def test_leg_structure(self, sample_dm):
        strategy = short_strangle(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 505.0
        )

        put_leg = strategy.get_leg(495.0, 'put')
        call_leg = strategy.get_leg(505.0, 'call')

        assert put_leg.is_short
        assert call_leg.is_short

    def test_is_credit(self, sample_dm):
        strategy = short_strangle(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 505.0
        )

        assert strategy.is_credit
        # Short 495P: receive bid 2.30 × 100 = -230
        # Short 505C: receive bid 2.30 × 100 = -230
        # Net: -460 (credit)
        assert strategy.net_premium == pytest.approx(-460.0)

    def test_unlimited_loss(self, sample_dm):
        """Short strangle has unlimited loss potential."""
        strategy = short_strangle(
            sample_dm, 'SPY', date(2026, 3, 20), 495.0, 505.0
        )

        assert strategy.max_loss is None  # Unlimited


class TestIronCondor:
    """Tests for iron_condor template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = iron_condor(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=490.0,
            put_short_strike=495.0,
            call_short_strike=505.0,
            call_long_strike=510.0
        )

        assert strategy is not None
        assert len(strategy) == 4
        assert strategy.name == 'Iron Condor'

    def test_leg_structure(self, sample_dm):
        strategy = iron_condor(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=490.0,
            put_short_strike=495.0,
            call_short_strike=505.0,
            call_long_strike=510.0
        )

        # Put spread (bull put)
        assert strategy.get_leg(490.0, 'put').is_long
        assert strategy.get_leg(495.0, 'put').is_short

        # Call spread (bear call)
        assert strategy.get_leg(505.0, 'call').is_short
        assert strategy.get_leg(510.0, 'call').is_long

    def test_is_credit(self, sample_dm):
        strategy = iron_condor(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=490.0,
            put_short_strike=495.0,
            call_short_strike=505.0,
            call_long_strike=510.0
        )

        assert strategy.is_credit

    def test_near_zero_delta(self, sample_dm):
        """Iron condor should be roughly delta neutral."""
        strategy = iron_condor(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=490.0,
            put_short_strike=495.0,
            call_short_strike=505.0,
            call_long_strike=510.0
        )

        # Should be close to zero (market neutral)
        assert abs(strategy.total_delta) < 20.0

    def test_bounded_risk(self, sample_dm):
        """Iron condor has defined max profit and loss."""
        strategy = iron_condor(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=490.0,
            put_short_strike=495.0,
            call_short_strike=505.0,
            call_long_strike=510.0
        )

        assert strategy.max_profit is not None
        assert strategy.max_loss is not None

        # Max profit = net credit received
        assert strategy.max_profit == pytest.approx(-strategy.net_premium)

    def test_pnl_profile(self, sample_dm):
        """Iron condor has max profit in middle, losses on wings."""
        strategy = iron_condor(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=490.0,
            put_short_strike=495.0,
            call_short_strike=505.0,
            call_long_strike=510.0
        )

        prices = np.array([480.0, 500.0, 520.0])
        pnl = strategy.calculate_pnl(prices)

        # Max profit in middle
        assert pnl[1] > pnl[0]
        assert pnl[1] > pnl[2]

    def test_invalid_strikes_raises(self, sample_dm):
        with pytest.raises(ValueError):
            iron_condor(
                sample_dm, 'SPY', date(2026, 3, 20),
                put_long_strike=495.0,  # Wrong order
                put_short_strike=490.0,
                call_short_strike=505.0,
                call_long_strike=510.0
            )

    def test_short_gamma_and_vega(self, sample_dm):
        """Iron condor should be short gamma and vega."""
        strategy = iron_condor(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=490.0,
            put_short_strike=495.0,
            call_short_strike=505.0,
            call_long_strike=510.0
        )

        assert strategy.total_gamma < 0
        assert strategy.total_vega < 0


class TestIronButterfly:
    """Tests for iron_butterfly template."""

    def test_creates_correct_legs(self, sample_dm):
        strategy = iron_butterfly(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=495.0,
            middle_strike=500.0,
            call_long_strike=505.0
        )

        assert strategy is not None
        assert len(strategy) == 4
        assert strategy.name == 'Iron Butterfly'

    def test_leg_structure(self, sample_dm):
        strategy = iron_butterfly(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=495.0,
            middle_strike=500.0,
            call_long_strike=505.0
        )

        # Long put wing
        assert strategy.get_leg(495.0, 'put').is_long

        # Short straddle at middle
        assert strategy.get_leg(500.0, 'put').is_short
        assert strategy.get_leg(500.0, 'call').is_short

        # Long call wing
        assert strategy.get_leg(505.0, 'call').is_long

    def test_is_credit(self, sample_dm):
        strategy = iron_butterfly(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=495.0,
            middle_strike=500.0,
            call_long_strike=505.0
        )

        assert strategy.is_credit

    def test_near_zero_delta(self, sample_dm):
        """Iron butterfly at ATM should be delta neutral."""
        strategy = iron_butterfly(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=495.0,
            middle_strike=500.0,
            call_long_strike=505.0
        )

        assert abs(strategy.total_delta) < 10.0

    def test_bounded_risk(self, sample_dm):
        """Iron butterfly has defined max profit and loss."""
        strategy = iron_butterfly(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=495.0,
            middle_strike=500.0,
            call_long_strike=505.0
        )

        assert strategy.max_profit is not None
        assert strategy.max_loss is not None

    def test_max_profit_at_middle_strike(self, sample_dm):
        """Max profit achieved when price equals middle strike."""
        strategy = iron_butterfly(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=495.0,
            middle_strike=500.0,
            call_long_strike=505.0
        )

        prices = np.array([495.0, 500.0, 505.0])
        pnl = strategy.calculate_pnl(prices)

        # Max profit at middle strike
        assert pnl[1] >= pnl[0]
        assert pnl[1] >= pnl[2]

    def test_invalid_strikes_raises(self, sample_dm):
        with pytest.raises(ValueError):
            iron_butterfly(
                sample_dm, 'SPY', date(2026, 3, 20),
                put_long_strike=500.0,  # Same as middle
                middle_strike=500.0,
                call_long_strike=505.0
            )


class TestTemplateIntegration:
    """Integration tests for template functions."""

    def test_all_templates_export_from_init(self):
        """All templates should be importable from options_builder."""
        from options_builder import (
            bull_call_spread,
            bear_call_spread,
            bull_put_spread,
            bear_put_spread,
            long_straddle,
            short_straddle,
            long_strangle,
            short_strangle,
            iron_condor,
            iron_butterfly,
        )
        assert callable(bull_call_spread)
        assert callable(iron_condor)

    def test_greeks_aggregate_correctly(self, sample_dm):
        """Verify Greeks sum correctly across all legs."""
        strategy = iron_condor(
            sample_dm, 'SPY', date(2026, 3, 20),
            put_long_strike=490.0,
            put_short_strike=495.0,
            call_short_strike=505.0,
            call_long_strike=510.0
        )

        # Manually calculate expected totals
        expected_delta = sum(leg.net_delta for leg in strategy.legs)
        expected_gamma = sum(leg.net_gamma for leg in strategy.legs)
        expected_theta = sum(leg.net_theta for leg in strategy.legs)
        expected_vega = sum(leg.net_vega for leg in strategy.legs)

        assert strategy.total_delta == pytest.approx(expected_delta)
        assert strategy.total_gamma == pytest.approx(expected_gamma)
        assert strategy.total_theta == pytest.approx(expected_theta)
        assert strategy.total_vega == pytest.approx(expected_vega)

    def test_ticker_case_insensitive(self, sample_dm):
        """Ticker should be case-insensitive."""
        strategy = bull_call_spread(
            sample_dm, 'spy', date(2026, 3, 20), 500.0, 505.0
        )
        assert strategy is not None
        assert strategy.ticker == 'spy'
