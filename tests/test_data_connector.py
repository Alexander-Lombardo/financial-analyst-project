"""Tests for OptionsDataConnector."""

import pytest
from datetime import datetime, date

from options_builder.data_connector import (
    OptionsDataConnector,
    UnderlyingQuote,
    OptionQuote,
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
