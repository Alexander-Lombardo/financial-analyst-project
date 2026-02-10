"""Tests for OptionsDataConnector."""

import pytest
from datetime import datetime, date

from options_builder.data_connector import (
    OptionsDataConnector,
    UnderlyingQuote,
    OptionQuote,
    OptionLeg,
    OptionChainRow,
    OptionChainGrid,
)


class TestUnderlyingQuote:
    """Tests for underlying price fetching."""

    def test_get_underlying_returns_quote(self):
        """Should return UnderlyingQuote with price."""
        connector = OptionsDataConnector()
        # Use SPY as it's highly liquid
        quote = connector.get_underlying('SPY')

        assert isinstance(quote, UnderlyingQuote)
        assert quote.ticker == 'SPY'
        assert quote.price > 0
        assert isinstance(quote.timestamp, datetime)

    def test_invalid_ticker_raises(self):
        """Should raise ValueError for invalid ticker."""
        connector = OptionsDataConnector()
        with pytest.raises(ValueError):
            connector.get_underlying('INVALIDTICKER123')


class TestExpirations:
    """Tests for expiration date fetching."""

    def test_get_expirations_returns_list(self):
        """Should return list of expiration dates."""
        connector = OptionsDataConnector()
        expirations = connector.get_expirations('SPY')

        assert isinstance(expirations, list)
        assert len(expirations) > 0
        # Should be YYYY-MM-DD format
        assert all(len(exp) == 10 for exp in expirations)


class TestOptionChain:
    """Tests for option chain fetching."""

    def test_get_chain_returns_quotes(self):
        """Should return list of OptionQuote objects."""
        connector = OptionsDataConnector()
        expirations = connector.get_expirations('SPY')
        chain = connector.get_option_chain('SPY', expirations[0])

        assert isinstance(chain, list)
        assert len(chain) > 0
        assert all(isinstance(q, OptionQuote) for q in chain)

    def test_filter_by_type(self):
        """Should filter by option type."""
        connector = OptionsDataConnector()
        expirations = connector.get_expirations('SPY')

        calls = connector.get_option_chain('SPY', expirations[0], 'call')
        puts = connector.get_option_chain('SPY', expirations[0], 'put')

        assert all(q.option_type == 'call' for q in calls)
        assert all(q.option_type == 'put' for q in puts)

    def test_quote_fields_populated(self):
        """Should populate all quote fields."""
        connector = OptionsDataConnector()
        expirations = connector.get_expirations('SPY')
        chain = connector.get_option_chain('SPY', expirations[0], 'call')

        # Find an ATM option (should have good liquidity)
        quote = connector.get_underlying('SPY')
        atm = min(chain, key=lambda q: abs(q.strike - quote.price))

        assert atm.strike > 0
        assert atm.bid >= 0
        assert atm.ask >= 0
        assert isinstance(atm.expiration, date)


class TestRiskFreeRate:
    """Tests for risk-free rate fetching."""

    def test_returns_positive_rate(self):
        """Should return a positive rate."""
        connector = OptionsDataConnector()
        rate = connector.get_risk_free_rate()

        assert rate > 0
        assert rate < 0.20  # Sanity check: less than 20%


class TestOptionLegProperties:
    """Tests for OptionLeg computed properties."""

    def test_mid_price(self):
        leg = OptionLeg(strike=100, last=5.0, bid=4.8, ask=5.2, open_interest=100)
        assert leg.mid_price == 5.0

    def test_spread(self):
        leg = OptionLeg(strike=100, last=5.0, bid=4.8, ask=5.2, open_interest=100)
        assert leg.spread == pytest.approx(0.4)

    def test_spread_pct(self):
        leg = OptionLeg(strike=100, last=5.0, bid=4.8, ask=5.2, open_interest=100)
        assert leg.spread_pct == pytest.approx(0.08)  # 0.4 / 5.0

    def test_is_liquid_true(self):
        leg = OptionLeg(strike=100, last=5.0, bid=4.8, ask=5.2, open_interest=100)
        assert leg.is_liquid(max_spread_pct=0.50) is True

    def test_is_liquid_zero_bid(self):
        leg = OptionLeg(strike=100, last=5.0, bid=0, ask=5.2, open_interest=100)
        assert leg.is_liquid() is False

    def test_is_liquid_wide_spread(self):
        leg = OptionLeg(strike=100, last=5.0, bid=1.0, ask=9.0, open_interest=100)
        # spread = 8, mid = 5, spread_pct = 1.6 > 0.50
        assert leg.is_liquid(max_spread_pct=0.50) is False


class TestOptionLeg:
    """Tests for OptionLeg dataclass."""

    def test_option_leg_creation(self):
        """Should create OptionLeg with all fields."""
        leg = OptionLeg(
            strike=100.0,
            last=5.50,
            bid=5.40,
            ask=5.60,
            open_interest=1000,
            volume=500,
            implied_volatility=0.25
        )

        assert leg.strike == 100.0
        assert leg.last == 5.50
        assert leg.bid == 5.40
        assert leg.ask == 5.60
        assert leg.open_interest == 1000
        assert leg.volume == 500
        assert leg.implied_volatility == 0.25

    def test_option_leg_defaults(self):
        """Should have defaults for optional fields."""
        leg = OptionLeg(
            strike=100.0,
            last=5.50,
            bid=5.40,
            ask=5.60,
            open_interest=1000
        )

        assert leg.volume == 0
        assert leg.implied_volatility == 0.0


class TestOptionChainRow:
    """Tests for OptionChainRow dataclass."""

    def test_row_with_both_legs(self):
        """Should create row with call and put legs."""
        call = OptionLeg(strike=100, last=5.0, bid=4.9, ask=5.1, open_interest=100)
        put = OptionLeg(strike=100, last=3.0, bid=2.9, ask=3.1, open_interest=200)

        row = OptionChainRow(strike=100.0, call=call, put=put)

        assert row.strike == 100.0
        assert row.call is not None
        assert row.put is not None
        assert row.call.last == 5.0
        assert row.put.last == 3.0

    def test_row_with_missing_leg(self):
        """Should allow None for missing legs."""
        row = OptionChainRow(strike=100.0, call=None, put=None)

        assert row.call is None
        assert row.put is None


class TestOptionChainGrid:
    """Tests for OptionChainGrid dataclass."""

    @pytest.fixture
    def sample_grid(self):
        """Create a sample grid for testing."""
        rows = []
        for strike in [95, 100, 105]:
            call = OptionLeg(strike=strike, last=10-strike/20, bid=9.5-strike/20,
                           ask=10.5-strike/20, open_interest=100)
            put = OptionLeg(strike=strike, last=strike/20-2, bid=strike/20-2.5,
                          ask=strike/20-1.5, open_interest=150)
            rows.append(OptionChainRow(strike=float(strike), call=call, put=put))

        return OptionChainGrid(
            ticker='TEST',
            expiration=date(2026, 3, 20),
            underlying_price=100.0,
            rows=rows
        )

    def test_grid_len(self, sample_grid):
        """Should return number of rows."""
        assert len(sample_grid) == 3

    def test_grid_strikes(self, sample_grid):
        """Should return list of strikes."""
        strikes = sample_grid.strikes()
        assert strikes == [95.0, 100.0, 105.0]

    def test_grid_calls(self, sample_grid):
        """Should return all call legs."""
        calls = sample_grid.calls()
        assert len(calls) == 3
        assert all(isinstance(c, OptionLeg) for c in calls)

    def test_grid_puts(self, sample_grid):
        """Should return all put legs."""
        puts = sample_grid.puts()
        assert len(puts) == 3
        assert all(isinstance(p, OptionLeg) for p in puts)

    def test_get_strike(self, sample_grid):
        """Should get row by strike price."""
        row = sample_grid.get_strike(100.0)
        assert row is not None
        assert row.strike == 100.0

    def test_get_strike_not_found(self, sample_grid):
        """Should return None for non-existent strike."""
        row = sample_grid.get_strike(999.0)
        assert row is None

    def test_atm_strike(self, sample_grid):
        """Should find closest strike to underlying."""
        # Underlying is 100, so ATM strike should be 100
        assert sample_grid.atm_strike() == 100.0

    def test_atm_strike_between(self):
        """Should find closest strike when underlying is between strikes."""
        rows = [
            OptionChainRow(strike=95.0),
            OptionChainRow(strike=100.0),
            OptionChainRow(strike=105.0),
        ]
        grid = OptionChainGrid(
            ticker='TEST',
            expiration=date(2026, 3, 20),
            underlying_price=102.0,  # Closer to 100 than 105
            rows=rows
        )
        assert grid.atm_strike() == 100.0

    def test_display(self, sample_grid):
        """Should return formatted display string."""
        display = sample_grid.display()
        assert 'TEST' in display
        assert '100.0' in display or '100.00' in display
        assert 'CALLS' in display
        assert 'PUTS' in display

    def test_display_with_limit(self, sample_grid):
        """Should limit number of strikes displayed."""
        display = sample_grid.display(num_strikes=2)
        # Should still work with limited strikes
        assert 'TEST' in display


class TestGetChainGrid:
    """Tests for get_chain_grid method (integration tests with live data)."""

    def test_returns_grid(self):
        """Should return OptionChainGrid object."""
        connector = OptionsDataConnector()
        expirations = connector.get_expirations('SPY')
        grid = connector.get_chain_grid('SPY', expirations[0])

        assert isinstance(grid, OptionChainGrid)
        assert grid.ticker == 'SPY'
        assert isinstance(grid.expiration, date)
        assert grid.underlying_price > 0

    def test_grid_has_rows(self):
        """Should have multiple rows with strikes."""
        connector = OptionsDataConnector()
        expirations = connector.get_expirations('SPY')
        grid = connector.get_chain_grid('SPY', expirations[0])

        assert len(grid) > 0
        assert len(grid.strikes()) > 0

    def test_grid_rows_have_legs(self):
        """Should have call and put legs for most strikes."""
        connector = OptionsDataConnector()
        expirations = connector.get_expirations('SPY')
        grid = connector.get_chain_grid('SPY', expirations[0])

        # At least some rows should have both legs
        rows_with_both = [r for r in grid.rows if r.call and r.put]
        assert len(rows_with_both) > 0

    def test_leg_data_populated(self):
        """Should populate leg data correctly."""
        connector = OptionsDataConnector()
        expirations = connector.get_expirations('SPY')
        grid = connector.get_chain_grid('SPY', expirations[0])

        # Find ATM row
        atm_row = grid.get_strike(grid.atm_strike())
        assert atm_row is not None

        if atm_row.call:
            assert atm_row.call.strike > 0
            assert atm_row.call.open_interest >= 0

        if atm_row.put:
            assert atm_row.put.strike > 0
            assert atm_row.put.open_interest >= 0


class TestTimeToMaturity:
    """Tests for time to maturity calculation."""

    def test_time_to_maturity_future(self):
        grid = OptionChainGrid(
            ticker='TEST',
            expiration=date(2026, 3, 20),
            underlying_price=100.0,
            rows=[]
        )
        # Calculate from a fixed reference date
        ttm = grid.time_to_maturity(from_date=date(2026, 2, 10))
        assert ttm == pytest.approx(38 / 365.0)

    def test_time_to_maturity_expired(self):
        grid = OptionChainGrid(
            ticker='TEST',
            expiration=date(2026, 1, 1),
            underlying_price=100.0,
            rows=[]
        )
        ttm = grid.time_to_maturity(from_date=date(2026, 2, 10))
        assert ttm == 0  # Expired, should be 0


class TestFilterLiquid:
    """Tests for liquidity filtering."""

    def test_filter_removes_zero_bid(self):
        rows = [
            OptionChainRow(
                strike=100.0,
                call=OptionLeg(strike=100, last=5, bid=0, ask=5.2, open_interest=100),
                put=OptionLeg(strike=100, last=3, bid=2.8, ask=3.2, open_interest=100)
            )
        ]
        grid = OptionChainGrid(ticker='TEST', expiration=date(2026, 3, 20),
                               underlying_price=100.0, rows=rows)

        filtered = grid.filter_liquid()
        assert filtered.rows[0].call is None  # Removed
        assert filtered.rows[0].put is not None  # Kept

    def test_filter_removes_wide_spread(self):
        rows = [
            OptionChainRow(
                strike=100.0,
                call=OptionLeg(strike=100, last=5, bid=1, ask=9, open_interest=100),
                put=OptionLeg(strike=100, last=3, bid=2.8, ask=3.2, open_interest=100)
            )
        ]
        grid = OptionChainGrid(ticker='TEST', expiration=date(2026, 3, 20),
                               underlying_price=100.0, rows=rows)

        filtered = grid.filter_liquid(max_spread_pct=0.50)
        assert filtered.rows[0].call is None  # Wide spread removed
        assert filtered.rows[0].put is not None

    def test_filter_removes_empty_rows(self):
        rows = [
            OptionChainRow(
                strike=100.0,
                call=OptionLeg(strike=100, last=5, bid=0, ask=5, open_interest=100),
                put=OptionLeg(strike=100, last=3, bid=0, ask=3, open_interest=100)
            )
        ]
        grid = OptionChainGrid(ticker='TEST', expiration=date(2026, 3, 20),
                               underlying_price=100.0, rows=rows)

        filtered = grid.filter_liquid()
        assert len(filtered) == 0  # Both legs illiquid, row removed
