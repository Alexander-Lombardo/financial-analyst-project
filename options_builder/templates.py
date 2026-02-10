"""Strategy template factory functions for common option strategies.

Quick-builder functions that create complete multi-leg option strategies
with a single function call. Each template handles leg construction,
validation, and strategy naming automatically.
"""

from datetime import date
from typing import Optional

from options_builder.data_manager import DataManager
from options_builder.strategy import OptionStrategy


# =============================================================================
# Vertical Spreads (2-leg)
# =============================================================================

def bull_call_spread(
    dm: DataManager,
    ticker: str,
    expiration: date,
    lower_strike: float,
    upper_strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create a bull call spread (debit spread).

    Structure: Long lower strike call, short higher strike call.
    Outlook: Moderately bullish
    Max Profit: (upper - lower strike) × 100 - net debit
    Max Loss: Net debit paid

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        lower_strike: Lower strike price (long call)
        upper_strike: Upper strike price (short call)
        quantity: Number of spreads (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    if lower_strike >= upper_strike:
        raise ValueError("lower_strike must be less than upper_strike")

    opt = dm.lookup_option(ticker, expiration, lower_strike, 'call')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Bull Call Spread'
    )

    if not strategy.add_leg_from_lookup(dm, lower_strike, 'call', quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, upper_strike, 'call', -quantity):
        return None

    return strategy


def bear_call_spread(
    dm: DataManager,
    ticker: str,
    expiration: date,
    lower_strike: float,
    upper_strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create a bear call spread (credit spread).

    Structure: Short lower strike call, long higher strike call.
    Outlook: Moderately bearish to neutral
    Max Profit: Net credit received
    Max Loss: (upper - lower strike) × 100 - net credit

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        lower_strike: Lower strike price (short call)
        upper_strike: Upper strike price (long call)
        quantity: Number of spreads (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    if lower_strike >= upper_strike:
        raise ValueError("lower_strike must be less than upper_strike")

    opt = dm.lookup_option(ticker, expiration, lower_strike, 'call')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Bear Call Spread'
    )

    if not strategy.add_leg_from_lookup(dm, lower_strike, 'call', -quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, upper_strike, 'call', quantity):
        return None

    return strategy


def bull_put_spread(
    dm: DataManager,
    ticker: str,
    expiration: date,
    lower_strike: float,
    upper_strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create a bull put spread (credit spread).

    Structure: Long lower strike put, short higher strike put.
    Outlook: Moderately bullish to neutral
    Max Profit: Net credit received
    Max Loss: (upper - lower strike) × 100 - net credit

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        lower_strike: Lower strike price (long put)
        upper_strike: Upper strike price (short put)
        quantity: Number of spreads (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    if lower_strike >= upper_strike:
        raise ValueError("lower_strike must be less than upper_strike")

    opt = dm.lookup_option(ticker, expiration, lower_strike, 'put')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Bull Put Spread'
    )

    if not strategy.add_leg_from_lookup(dm, lower_strike, 'put', quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, upper_strike, 'put', -quantity):
        return None

    return strategy


def bear_put_spread(
    dm: DataManager,
    ticker: str,
    expiration: date,
    lower_strike: float,
    upper_strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create a bear put spread (debit spread).

    Structure: Short lower strike put, long higher strike put.
    Outlook: Moderately bearish
    Max Profit: (upper - lower strike) × 100 - net debit
    Max Loss: Net debit paid

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        lower_strike: Lower strike price (short put)
        upper_strike: Upper strike price (long put)
        quantity: Number of spreads (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    if lower_strike >= upper_strike:
        raise ValueError("lower_strike must be less than upper_strike")

    opt = dm.lookup_option(ticker, expiration, lower_strike, 'put')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Bear Put Spread'
    )

    if not strategy.add_leg_from_lookup(dm, lower_strike, 'put', -quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, upper_strike, 'put', quantity):
        return None

    return strategy


# =============================================================================
# Neutral Strategies (2-leg)
# =============================================================================

def long_straddle(
    dm: DataManager,
    ticker: str,
    expiration: date,
    strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create a long straddle.

    Structure: Long call + long put at same strike.
    Outlook: Expecting large move in either direction (high volatility)
    Max Profit: Unlimited on upside, (strike - premium) × 100 on downside
    Max Loss: Total premium paid

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        strike: Strike price for both legs (typically ATM)
        quantity: Number of straddles (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    opt = dm.lookup_option(ticker, expiration, strike, 'call')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Long Straddle'
    )

    if not strategy.add_leg_from_lookup(dm, strike, 'call', quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, strike, 'put', quantity):
        return None

    return strategy


def short_straddle(
    dm: DataManager,
    ticker: str,
    expiration: date,
    strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create a short straddle.

    Structure: Short call + short put at same strike.
    Outlook: Expecting low volatility, price stays near strike
    Max Profit: Total premium received
    Max Loss: Unlimited on upside, (strike - premium) × 100 on downside

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        strike: Strike price for both legs (typically ATM)
        quantity: Number of straddles (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    opt = dm.lookup_option(ticker, expiration, strike, 'call')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Short Straddle'
    )

    if not strategy.add_leg_from_lookup(dm, strike, 'call', -quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, strike, 'put', -quantity):
        return None

    return strategy


def long_strangle(
    dm: DataManager,
    ticker: str,
    expiration: date,
    put_strike: float,
    call_strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create a long strangle.

    Structure: Long OTM put + long OTM call at different strikes.
    Outlook: Expecting large move in either direction (high volatility)
    Max Profit: Unlimited on upside, (put_strike - premium) × 100 on downside
    Max Loss: Total premium paid

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        put_strike: Put strike price (typically below current price)
        call_strike: Call strike price (typically above current price)
        quantity: Number of strangles (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    if put_strike >= call_strike:
        raise ValueError("put_strike must be less than call_strike")

    opt = dm.lookup_option(ticker, expiration, put_strike, 'put')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Long Strangle'
    )

    if not strategy.add_leg_from_lookup(dm, put_strike, 'put', quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, call_strike, 'call', quantity):
        return None

    return strategy


def short_strangle(
    dm: DataManager,
    ticker: str,
    expiration: date,
    put_strike: float,
    call_strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create a short strangle.

    Structure: Short OTM put + short OTM call at different strikes.
    Outlook: Expecting low volatility, price stays between strikes
    Max Profit: Total premium received
    Max Loss: Unlimited on upside, (put_strike - premium) × 100 on downside

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        put_strike: Put strike price (typically below current price)
        call_strike: Call strike price (typically above current price)
        quantity: Number of strangles (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    if put_strike >= call_strike:
        raise ValueError("put_strike must be less than call_strike")

    opt = dm.lookup_option(ticker, expiration, put_strike, 'put')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Short Strangle'
    )

    if not strategy.add_leg_from_lookup(dm, put_strike, 'put', -quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, call_strike, 'call', -quantity):
        return None

    return strategy


# =============================================================================
# Advanced Spreads (4-leg)
# =============================================================================

def iron_condor(
    dm: DataManager,
    ticker: str,
    expiration: date,
    put_long_strike: float,
    put_short_strike: float,
    call_short_strike: float,
    call_long_strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create an iron condor (credit spread).

    Structure: Bull put spread + bear call spread.
    - Long OTM put (wing)
    - Short put (closer to ATM)
    - Short call (closer to ATM)
    - Long OTM call (wing)

    Outlook: Neutral, expecting low volatility
    Max Profit: Net credit received
    Max Loss: Width of wider spread × 100 - net credit

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        put_long_strike: Long put strike (lowest)
        put_short_strike: Short put strike
        call_short_strike: Short call strike
        call_long_strike: Long call strike (highest)
        quantity: Number of iron condors (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    if not (put_long_strike < put_short_strike < call_short_strike < call_long_strike):
        raise ValueError(
            "Strikes must be ordered: put_long < put_short < call_short < call_long"
        )

    opt = dm.lookup_option(ticker, expiration, put_long_strike, 'put')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Iron Condor'
    )

    # Bull put spread (lower strikes)
    if not strategy.add_leg_from_lookup(dm, put_long_strike, 'put', quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, put_short_strike, 'put', -quantity):
        return None

    # Bear call spread (upper strikes)
    if not strategy.add_leg_from_lookup(dm, call_short_strike, 'call', -quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, call_long_strike, 'call', quantity):
        return None

    return strategy


def iron_butterfly(
    dm: DataManager,
    ticker: str,
    expiration: date,
    put_long_strike: float,
    middle_strike: float,
    call_long_strike: float,
    quantity: int = 1
) -> Optional[OptionStrategy]:
    """
    Create an iron butterfly (credit spread).

    Structure: Short straddle + long strangle wings.
    - Long OTM put (wing)
    - Short ATM put
    - Short ATM call
    - Long OTM call (wing)

    Outlook: Neutral, expecting very low volatility
    Max Profit: Net credit received (at middle strike)
    Max Loss: Width of spread × 100 - net credit

    Args:
        dm: DataManager with option chain data
        ticker: Underlying symbol
        expiration: Expiration date
        put_long_strike: Long put strike (lowest, wing)
        middle_strike: ATM strike for short straddle
        call_long_strike: Long call strike (highest, wing)
        quantity: Number of iron butterflies (default 1)

    Returns:
        OptionStrategy if all legs found, None otherwise
    """
    if not (put_long_strike < middle_strike < call_long_strike):
        raise ValueError(
            "Strikes must be ordered: put_long < middle < call_long"
        )

    opt = dm.lookup_option(ticker, expiration, middle_strike, 'call')
    if opt is None:
        return None
    underlying_price = opt['underlying_price']

    strategy = OptionStrategy(
        ticker=ticker,
        expiration=expiration,
        underlying_price=underlying_price,
        name='Iron Butterfly'
    )

    # Long put wing
    if not strategy.add_leg_from_lookup(dm, put_long_strike, 'put', quantity):
        return None

    # Short straddle at middle strike
    if not strategy.add_leg_from_lookup(dm, middle_strike, 'put', -quantity):
        return None
    if not strategy.add_leg_from_lookup(dm, middle_strike, 'call', -quantity):
        return None

    # Long call wing
    if not strategy.add_leg_from_lookup(dm, call_long_strike, 'call', quantity):
        return None

    return strategy
