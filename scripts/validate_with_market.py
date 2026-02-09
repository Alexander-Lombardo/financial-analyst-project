#!/usr/bin/env python3
"""Validate options pricing engine against live market data.

Fetches real option quotes and verifies that our Black-Scholes and Monte Carlo
prices fall within the market bid/ask spread.
"""

import argparse
import sys
from datetime import datetime

import yfinance as yf

from options_builder import black_scholes, mc_european


def get_risk_free_rate() -> float:
    """Get current risk-free rate (3-month T-bill proxy).

    Uses ^IRX (13-week T-bill) or falls back to 5%.
    """
    try:
        tbill = yf.Ticker("^IRX")
        rate = tbill.info.get('regularMarketPrice', 5.0) / 100
        return rate
    except Exception:
        return 0.05


def validate_option(ticker: str, option_type: str = 'call', min_dte: int = 1) -> dict:
    """Validate pricing against a live option quote.

    Parameters:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'SPY')
        option_type: 'call' or 'put'
        min_dte: Minimum days to expiration (default: 1)

    Returns:
        dict with comparison results including pass/fail status
    """
    stock = yf.Ticker(ticker)

    # Get current stock price
    info = stock.info
    S = info.get('regularMarketPrice') or info.get('currentPrice')
    if S is None:
        raise ValueError(f"Could not get current price for {ticker}")

    # Get expiration with at least min_dte days
    expirations = stock.options
    if not expirations:
        raise ValueError(f"No options available for {ticker}")

    today = datetime.now().date()
    exp_date = None
    for exp in expirations:
        exp_dt = datetime.strptime(exp, '%Y-%m-%d').date()
        if (exp_dt - today).days >= min_dte:
            exp_date = exp
            break

    if exp_date is None:
        raise ValueError(f"No expirations with at least {min_dte} DTE for {ticker}")

    # Get option chain
    chain = stock.option_chain(exp_date)
    options = chain.calls if option_type == 'call' else chain.puts

    if options.empty:
        raise ValueError(f"No {option_type} options available for {ticker}")

    # Find ATM option (closest to current price)
    options = options.copy()
    options['moneyness'] = abs(options['strike'] - S)
    atm = options.loc[options['moneyness'].idxmin()]

    K = float(atm['strike'])
    bid = float(atm['bid'])
    ask = float(atm['ask'])
    iv = float(atm['impliedVolatility'])

    # Skip if no valid quotes
    if bid <= 0 or ask <= 0 or iv <= 0:
        raise ValueError(f"Invalid market data for {ticker} (bid={bid}, ask={ask}, iv={iv})")

    # Calculate T in years
    exp = datetime.strptime(exp_date, '%Y-%m-%d').date()
    today = datetime.now().date()
    days_to_expiry = (exp - today).days

    if days_to_expiry <= 0:
        raise ValueError(f"Option has expired or expires today")

    T = days_to_expiry / 365

    r = get_risk_free_rate()

    # Calculate theoretical prices
    bsm_call, bsm_put = black_scholes(S, K, T, r, iv)
    mc_result = mc_european(S, K, T, r, iv, num_paths=100000, seed=42)

    theoretical = bsm_call if option_type == 'call' else bsm_put
    mc_price = mc_result['call'] if option_type == 'call' else mc_result['put']
    mc_std_error = mc_result['call_std_error'] if option_type == 'call' else mc_result['put_std_error']

    mid = (bid + ask) / 2
    within_spread = bid <= theoretical <= ask
    mc_within_3se = abs(mc_price - theoretical) <= 3 * mc_std_error

    # Also check if within reasonable tolerance of mid (5% or $0.10)
    diff_from_mid = abs(theoretical - mid)
    tolerance = max(0.05 * mid, 0.10)
    within_tolerance = diff_from_mid <= tolerance

    return {
        'ticker': ticker,
        'type': option_type,
        'expiration': exp_date,
        'S': S,
        'K': K,
        'T': T,
        'r': r,
        'iv': iv,
        'bid': bid,
        'ask': ask,
        'mid': mid,
        'bsm': theoretical,
        'mc': mc_price,
        'mc_std_error': mc_std_error,
        'within_spread': within_spread,
        'within_tolerance': within_tolerance,
        'mc_within_3se': mc_within_3se,
        'status': 'PASS' if within_spread else 'FAIL',
    }


def format_result(result: dict) -> str:
    """Format validation result for display."""
    lines = [
        "=" * 60,
        "Options Pricing Engine - Market Validation",
        "=" * 60,
        "",
        f"Ticker: {result['ticker']}",
        f"Type: {result['type']}",
        f"Underlying: ${result['S']:.2f}",
        f"Strike: ${result['K']:.2f}",
        f"Expiration: {result['expiration']} (T={result['T']:.3f} years)",
        f"Risk-free rate: {result['r']*100:.2f}%",
        f"Implied Volatility: {result['iv']*100:.1f}%",
        "",
        "Market Prices:",
        f"  Bid: ${result['bid']:.2f}",
        f"  Ask: ${result['ask']:.2f}",
        f"  Mid: ${result['mid']:.2f}",
        "",
        "Theoretical Prices:",
        f"  Black-Scholes: ${result['bsm']:.2f}",
        f"  Monte Carlo:   ${result['mc']:.2f} +/- ${result['mc_std_error']:.2f}",
        "",
    ]

    if result['within_spread']:
        lines.append(f"Result: PASS - BSM price within bid/ask spread")
    else:
        diff = result['bsm'] - result['mid']
        if result['within_tolerance']:
            lines.append(f"Result: FAIL - BSM price outside spread but within 5% of mid (diff: ${diff:+.2f})")
        else:
            lines.append(f"Result: FAIL - BSM price outside bid/ask spread (diff from mid: ${diff:+.2f})")

    if result['mc_within_3se']:
        lines.append(f"        MC price within 3 std errors of BSM (models agree)")
    else:
        lines.append(f"        WARNING: MC price differs from BSM by more than 3 std errors")

    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate options pricing engine against live market data"
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        default=['SPY'],
        help='Ticker symbols to validate (default: SPY)'
    )
    parser.add_argument(
        '--type',
        choices=['call', 'put', 'both'],
        default='both',
        help='Option type to validate (default: both)'
    )
    parser.add_argument(
        '--min-dte',
        type=int,
        default=1,
        help='Minimum days to expiration (default: 1)'
    )

    args = parser.parse_args()

    option_types = ['call', 'put'] if args.type == 'both' else [args.type]

    all_passed = True
    results = []

    for ticker in args.tickers:
        for opt_type in option_types:
            try:
                result = validate_option(ticker, opt_type, min_dte=args.min_dte)
                results.append(result)
                print(format_result(result))
                print()

                if result['status'] != 'PASS':
                    all_passed = False

            except Exception as e:
                print(f"ERROR validating {ticker} {opt_type}: {e}")
                print()
                all_passed = False

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if all_passed:
        print("\nAll validations PASSED")
        return 0
    else:
        print("\nSome validations FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
