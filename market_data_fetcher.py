#!/usr/bin/env python3
"""
Market Data Fetcher for Pillar 5: Valuation & Market Sentiment

Fetches stock prices and valuation metrics from Yahoo Finance API.
Includes caching to avoid rate limits and graceful fallback.

Usage:
    from market_data_fetcher import MarketDataFetcher
    fetcher = MarketDataFetcher()
    prices = fetcher.get_current_prices()
    metrics = fetcher.get_valuation_metrics()
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import yfinance as yf
import pandas as pd


class MarketDataFetcher:
    """
    Fetches market data from Yahoo Finance for Target and retail peers.

    Provides:
    - Current stock prices
    - Historical price data
    - Valuation metrics (P/E, P/S, EV/EBITDA, Dividend Yield)
    - Peer comparison data

    Features:
    - Caching to avoid rate limits
    - Graceful fallback to cached data if API fails
    - Configurable ticker list
    """

    # Default retail peer tickers
    DEFAULT_TICKERS = ['TGT', 'WMT', 'COST', 'AMZN', 'KR']

    # Cache settings
    CACHE_FILE = Path('data/market_data_cache.json')
    PRICE_CACHE_TTL_HOURS = 1  # Current prices cache TTL
    HISTORY_CACHE_TTL_HOURS = 24  # Historical data cache TTL

    def __init__(self, tickers: List[str] = None):
        """
        Initialize the market data fetcher.

        Args:
            tickers: List of stock ticker symbols. Defaults to Target + retail peers.
        """
        self.tickers = tickers or self.DEFAULT_TICKERS
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cached data from file."""
        if self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        # Ensure data directory exists
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CACHE_FILE, 'w') as f:
            json.dump(self._cache, f, indent=2, default=str)

    def _is_cache_valid(self, cache_key: str, ttl_hours: int) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False

        cached_time = self._cache[cache_key].get('timestamp')
        if not cached_time:
            return False

        try:
            cached_dt = datetime.fromisoformat(cached_time)
            return datetime.now() - cached_dt < timedelta(hours=ttl_hours)
        except (ValueError, TypeError):
            return False

    def get_current_prices(self, force_refresh: bool = False) -> Dict[str, float]:
        """
        Get current stock prices for all tickers.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            Dict mapping ticker to current price.
            Example: {'TGT': 145.32, 'WMT': 178.45, ...}
        """
        cache_key = 'current_prices'

        if not force_refresh and self._is_cache_valid(cache_key, self.PRICE_CACHE_TTL_HOURS):
            return self._cache[cache_key]['data']

        prices = {}
        try:
            for ticker in self.tickers:
                stock = yf.Ticker(ticker)
                info = stock.info
                # Try multiple price fields (different availability)
                price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                if price:
                    prices[ticker] = round(float(price), 2)

            # Cache the results
            self._cache[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'data': prices
            }
            self._save_cache()

        except Exception as e:
            print(f"Warning: Failed to fetch current prices: {e}")
            # Return cached data if available
            if cache_key in self._cache:
                return self._cache[cache_key].get('data', {})

        return prices

    def get_historical_prices(self, ticker: str = 'TGT', period: str = '5y') -> pd.DataFrame:
        """
        Get historical price data for a ticker.

        Args:
            ticker: Stock ticker symbol. Defaults to TGT.
            period: Time period for history. Options: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
        """
        cache_key = f'history_{ticker}_{period}'

        if self._is_cache_valid(cache_key, self.HISTORY_CACHE_TTL_HOURS):
            # Reconstruct DataFrame from cached data
            cached_data = self._cache[cache_key]['data']
            return pd.DataFrame(cached_data)

        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)

            # Cache the results (convert to serializable format)
            self._cache[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'data': history.reset_index().to_dict(orient='list')
            }
            self._save_cache()

            return history

        except Exception as e:
            print(f"Warning: Failed to fetch historical prices for {ticker}: {e}")
            # Return cached data if available
            if cache_key in self._cache:
                cached_data = self._cache[cache_key].get('data', {})
                return pd.DataFrame(cached_data)
            return pd.DataFrame()

    def get_valuation_metrics(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Get valuation metrics for all tickers.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            Dict mapping ticker to valuation metrics.
            Example: {
                'TGT': {
                    'price': 145.32,
                    'market_cap_billion': 67.5,
                    'pe_ratio': 15.2,
                    'forward_pe': 12.8,
                    'ps_ratio': 0.63,
                    'ev_ebitda': 8.5,
                    'dividend_yield_percent': 2.85,
                    'payout_ratio_percent': 43.2
                },
                ...
            }
        """
        cache_key = 'valuation_metrics'

        if not force_refresh and self._is_cache_valid(cache_key, self.PRICE_CACHE_TTL_HOURS):
            return self._cache[cache_key]['data']

        metrics = {}
        try:
            for ticker in self.tickers:
                stock = yf.Ticker(ticker)
                info = stock.info

                # Extract valuation metrics
                price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                market_cap = info.get('marketCap', 0)

                metrics[ticker] = {
                    'name': info.get('shortName', ticker),
                    'price': round(float(price), 2) if price else None,
                    'market_cap_billion': round(market_cap / 1e9, 2) if market_cap else None,
                    'pe_ratio': info.get('trailingPE'),
                    'forward_pe': info.get('forwardPE'),
                    'ps_ratio': info.get('priceToSalesTrailing12Months'),
                    'pb_ratio': info.get('priceToBook'),
                    'ev_ebitda': info.get('enterpriseToEbitda'),
                    'ev_revenue': info.get('enterpriseToRevenue'),
                    'dividend_yield_percent': round(info.get('trailingAnnualDividendYield', 0) * 100, 2) if info.get('trailingAnnualDividendYield') else None,
                    'payout_ratio_percent': round(info.get('payoutRatio', 0) * 100, 2) if info.get('payoutRatio') else None,
                    'beta': info.get('beta'),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                    'revenue_growth_percent': round(info.get('revenueGrowth', 0) * 100, 2) if info.get('revenueGrowth') else None
                }

            # Cache the results
            self._cache[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'data': metrics
            }
            self._save_cache()

        except Exception as e:
            print(f"Warning: Failed to fetch valuation metrics: {e}")
            # Return cached data if available
            if cache_key in self._cache:
                return self._cache[cache_key].get('data', {})

        return metrics

    def get_peer_comparison(self) -> Dict:
        """
        Get peer comparison data formatted for visualization.

        Returns:
            Dict with company data for scatter plot:
            {
                'companies': [
                    {'ticker': 'TGT', 'name': 'Target', 'pe_ratio': 15.2, 'revenue_growth': 2.5, ...},
                    ...
                ],
                'averages': {
                    'pe_ratio': 18.5,
                    'revenue_growth': 3.2
                }
            }
        """
        metrics = self.get_valuation_metrics()

        companies = []
        pe_ratios = []
        revenue_growths = []

        for ticker, data in metrics.items():
            company = {
                'ticker': ticker,
                'name': data.get('name', ticker),
                'pe_ratio': data.get('pe_ratio'),
                'ps_ratio': data.get('ps_ratio'),
                'ev_ebitda': data.get('ev_ebitda'),
                'dividend_yield_percent': data.get('dividend_yield_percent'),
                'revenue_growth_percent': data.get('revenue_growth_percent'),
                'market_cap_billion': data.get('market_cap_billion'),
                'price': data.get('price')
            }
            companies.append(company)

            if data.get('pe_ratio'):
                pe_ratios.append(data['pe_ratio'])
            if data.get('revenue_growth_percent'):
                revenue_growths.append(data['revenue_growth_percent'])

        return {
            'companies': companies,
            'averages': {
                'pe_ratio': round(sum(pe_ratios) / len(pe_ratios), 2) if pe_ratios else None,
                'revenue_growth_percent': round(sum(revenue_growths) / len(revenue_growths), 2) if revenue_growths else None
            },
            'timestamp': datetime.now().isoformat()
        }

    def get_target_valuation_summary(self) -> Dict:
        """
        Get a summary of Target's valuation for quick reference.

        Returns:
            Dict with Target's key valuation metrics and peer comparison.
        """
        metrics = self.get_valuation_metrics()
        target_data = metrics.get('TGT', {})

        # Calculate peer averages (excluding Target)
        peer_pe = []
        peer_ps = []
        peer_ev_ebitda = []

        for ticker, data in metrics.items():
            if ticker != 'TGT':
                if data.get('pe_ratio'):
                    peer_pe.append(data['pe_ratio'])
                if data.get('ps_ratio'):
                    peer_ps.append(data['ps_ratio'])
                if data.get('ev_ebitda'):
                    peer_ev_ebitda.append(data['ev_ebitda'])

        avg_peer_pe = round(sum(peer_pe) / len(peer_pe), 2) if peer_pe else None
        avg_peer_ps = round(sum(peer_ps) / len(peer_ps), 2) if peer_ps else None
        avg_peer_ev_ebitda = round(sum(peer_ev_ebitda) / len(peer_ev_ebitda), 2) if peer_ev_ebitda else None

        # Determine valuation status
        target_pe = target_data.get('pe_ratio')
        valuation_status = 'N/A'
        if target_pe and avg_peer_pe:
            if target_pe < avg_peer_pe * 0.8:
                valuation_status = 'Undervalued'
            elif target_pe > avg_peer_pe * 1.2:
                valuation_status = 'Overvalued'
            else:
                valuation_status = 'Fair Value'

        return {
            'target': target_data,
            'peer_averages': {
                'pe_ratio': avg_peer_pe,
                'ps_ratio': avg_peer_ps,
                'ev_ebitda': avg_peer_ev_ebitda
            },
            'valuation_status': valuation_status,
            'pe_discount_percent': round((1 - target_pe / avg_peer_pe) * 100, 1) if target_pe and avg_peer_pe else None
        }

    def get_quarter_end_price(self, ticker: str, date_str: str) -> Optional[float]:
        """
        Get stock price for a specific date (or closest trading day).

        Args:
            ticker: Stock ticker symbol.
            date_str: Date string in YYYY-MM-DD format.

        Returns:
            Closing price for that date, or None if not available.
        """
        try:
            # Get historical data covering the date range
            history = self.get_historical_prices(ticker, '5y')
            if history.empty:
                return None

            # Convert target date to datetime
            target_date = pd.to_datetime(date_str)

            # Handle both index-based and column-based date formats
            if 'Date' in history.columns:
                # Column-based (from cache) - dates may be strings with timezone info
                # Convert to datetime, handling mixed timezone strings
                dates = []
                for d in history['Date']:
                    try:
                        # Parse and convert to naive datetime (drop timezone)
                        dt = pd.to_datetime(d)
                        if hasattr(dt, 'tz') and dt.tz is not None:
                            dt = dt.tz_localize(None)
                        dates.append(dt)
                    except Exception:
                        dates.append(pd.NaT)
                history_dates = pd.Series(dates, index=history.index)
            else:
                # Index-based (from fresh API call) - convert to Series for consistent handling
                idx = history.index
                dates = []
                for d in idx:
                    try:
                        dt = pd.to_datetime(d)
                        if hasattr(dt, 'tz') and dt.tz is not None:
                            dt = dt.tz_localize(None)
                        dates.append(dt)
                    except Exception:
                        dates.append(pd.NaT)
                history_dates = pd.Series(dates, index=range(len(dates)))

            # Make target date timezone-naive if needed
            if hasattr(target_date, 'tz') and target_date.tz is not None:
                target_date = target_date.tz_localize(None)

            # Filter to dates on or before target
            valid_mask = history_dates <= target_date
            if not valid_mask.any():
                return None

            # Find index of closest date
            valid_indices = history_dates[valid_mask].index.tolist()
            closest_idx = valid_indices[-1]  # Last valid index (most recent before target)

            # Get the closing price
            price = history.iloc[closest_idx]['Close']

            return round(float(price), 2)

        except Exception as e:
            print(f"Warning: Failed to get price for {ticker} on {date_str}: {e}")
            return None

    def get_historical_pe_for_quarters(self, quarters_data: List[Dict]) -> Dict[str, Dict]:
        """
        Calculate historical P/E ratios for specified quarters.

        Args:
            quarters_data: List of dicts with:
                - 'period': e.g., 'Q3 2024'
                - 'quarter_end_date': e.g., '2024-10-31'
                - 'ttm_net_income_billion': trailing 12-month net income in billions

        Returns:
            Dict mapping period to P/E data:
            {
                'Q3 2024': {
                    'stock_price': 142.67,
                    'ttm_eps': 8.85,
                    'pe_ratio': 16.1,
                    'quarter_end_date': '2024-10-31'
                }
            }
        """
        # Get shares outstanding (use current - assume relatively stable)
        try:
            stock = yf.Ticker('TGT')
            shares_outstanding = stock.info.get('sharesOutstanding', 460_000_000)
        except Exception:
            shares_outstanding = 460_000_000  # Fallback: ~460M shares

        shares_billion = shares_outstanding / 1e9

        results = {}
        for q in quarters_data:
            period = q['period']
            date_str = q['quarter_end_date']
            ttm_net_income = q.get('ttm_net_income_billion')

            if ttm_net_income is None or ttm_net_income <= 0:
                continue

            # Get stock price for quarter end
            price = self.get_quarter_end_price('TGT', date_str)
            if price is None:
                continue

            # Calculate TTM EPS and P/E
            ttm_eps = ttm_net_income / shares_billion
            pe_ratio = price / ttm_eps if ttm_eps > 0 else None

            results[period] = {
                'stock_price': price,
                'ttm_eps': round(ttm_eps, 2),
                'pe_ratio': round(pe_ratio, 2) if pe_ratio else None,
                'quarter_end_date': date_str
            }

        return results

    def get_relative_performance(self, ticker: str = 'TGT',
                                   benchmarks: List[str] = None,
                                   period: str = '3y') -> pd.DataFrame:
        """
        Get total return comparison: ticker vs benchmarks (e.g., S&P 500, Retail ETF).

        Args:
            ticker: Stock ticker symbol. Defaults to TGT.
            benchmarks: List of benchmark tickers. Defaults to ['SPY', 'XRT'].
            period: Time period for history. Options: 1y, 2y, 3y, 5y.

        Returns:
            DataFrame with columns: Date, ticker, and each benchmark
            Values are cumulative returns indexed to 100 at start.
        """
        if benchmarks is None:
            benchmarks = ['SPY', 'XRT']

        cache_key = f'relative_perf_{ticker}_{"-".join(benchmarks)}_{period}'

        if self._is_cache_valid(cache_key, self.HISTORY_CACHE_TTL_HOURS):
            cached_data = self._cache[cache_key]['data']
            return pd.DataFrame(cached_data)

        try:
            all_tickers = [ticker] + benchmarks
            result_data = {'Date': None}

            # Get price history for all tickers
            for t in all_tickers:
                stock = yf.Ticker(t)
                history = stock.history(period=period)

                if history.empty:
                    continue

                # Calculate cumulative returns indexed to 100
                prices = history['Close']
                returns = (prices / prices.iloc[0]) * 100

                if result_data['Date'] is None:
                    result_data['Date'] = returns.index.tolist()

                result_data[t] = returns.values.tolist()

            # Create DataFrame
            df = pd.DataFrame(result_data)

            # Cache results
            self._cache[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'data': df.to_dict(orient='list')
            }
            self._save_cache()

            return df

        except Exception as e:
            print(f"Warning: Failed to get relative performance: {e}")
            if cache_key in self._cache:
                return pd.DataFrame(self._cache[cache_key].get('data', {}))
            return pd.DataFrame()

    def get_rolling_beta(self, ticker: str = 'TGT',
                         benchmark: str = 'SPY',
                         window: int = 60,
                         period: str = '3y') -> pd.DataFrame:
        """
        Calculate rolling beta vs benchmark (e.g., S&P 500).

        Beta measures the stock's sensitivity to market movements.
        Beta > 1 = more volatile than market
        Beta < 1 = less volatile than market
        Beta < 0 = moves opposite to market

        Args:
            ticker: Stock ticker symbol. Defaults to TGT.
            benchmark: Benchmark ticker. Defaults to SPY (S&P 500).
            window: Rolling window in trading days. Defaults to 60 (~3 months).
            period: Time period for history.

        Returns:
            DataFrame with columns: Date, Beta
        """
        cache_key = f'rolling_beta_{ticker}_{benchmark}_{window}_{period}'

        if self._is_cache_valid(cache_key, self.HISTORY_CACHE_TTL_HOURS):
            cached_data = self._cache[cache_key]['data']
            return pd.DataFrame(cached_data)

        try:
            # Get price history for both tickers
            stock = yf.Ticker(ticker)
            bench = yf.Ticker(benchmark)

            stock_history = stock.history(period=period)
            bench_history = bench.history(period=period)

            if stock_history.empty or bench_history.empty:
                return pd.DataFrame()

            # Calculate daily returns
            stock_returns = stock_history['Close'].pct_change().dropna()
            bench_returns = bench_history['Close'].pct_change().dropna()

            # Align the two series
            aligned = pd.concat([stock_returns, bench_returns], axis=1, join='inner')
            aligned.columns = ['stock', 'bench']

            # Calculate rolling beta: Cov(stock, bench) / Var(bench)
            rolling_cov = aligned['stock'].rolling(window=window).cov(aligned['bench'])
            rolling_var = aligned['bench'].rolling(window=window).var()
            rolling_beta = rolling_cov / rolling_var

            # Create result DataFrame
            df = pd.DataFrame({
                'Date': rolling_beta.index.tolist(),
                'Beta': rolling_beta.values.tolist()
            })

            # Cache results
            self._cache[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'data': df.to_dict(orient='list')
            }
            self._save_cache()

            return df

        except Exception as e:
            print(f"Warning: Failed to calculate rolling beta: {e}")
            if cache_key in self._cache:
                return pd.DataFrame(self._cache[cache_key].get('data', {}))
            return pd.DataFrame()

    def get_historical_pe_for_ticker(self, ticker: str, quarter_end_dates: List[str]) -> Dict[str, float]:
        """
        Get approximate historical P/E for any ticker at specified dates.

        Uses price ratio scaling: Historical P/E ≈ Current P/E × (Historical Price / Current Price)
        This approximation assumes EPS is relatively stable over the period.

        Args:
            ticker: Stock ticker symbol (e.g., 'WMT', 'COST').
            quarter_end_dates: List of dates in YYYY-MM-DD format.

        Returns:
            Dict mapping date to estimated P/E ratio:
            {'2024-10-31': 15.2, '2024-07-31': 14.8, ...}
        """
        try:
            # Get current P/E and price from valuation metrics
            metrics = self.get_valuation_metrics()
            ticker_data = metrics.get(ticker, {})

            current_pe = ticker_data.get('pe_ratio')
            current_price = ticker_data.get('price')

            if not current_pe or not current_price:
                print(f"Warning: Missing current P/E or price for {ticker}")
                return {}

            results = {}
            for date_str in quarter_end_dates:
                hist_price = self.get_quarter_end_price(ticker, date_str)
                if hist_price and hist_price > 0:
                    # Scale P/E by price ratio (assumes stable EPS)
                    # Historical P/E ≈ Current P/E × (Historical Price / Current Price)
                    hist_pe = current_pe * (hist_price / current_price)
                    results[date_str] = round(hist_pe, 2)

            return results

        except Exception as e:
            print(f"Warning: Failed to get historical P/E for {ticker}: {e}")
            return {}


def main():
    """Test the market data fetcher."""
    print("=" * 60)
    print("Market Data Fetcher - Test Run")
    print("=" * 60)

    fetcher = MarketDataFetcher()

    # Test current prices
    print("\n1. Current Stock Prices:")
    print("-" * 40)
    prices = fetcher.get_current_prices()
    for ticker, price in prices.items():
        print(f"   {ticker}: ${price:.2f}")

    # Test valuation metrics
    print("\n2. Valuation Metrics:")
    print("-" * 40)
    metrics = fetcher.get_valuation_metrics()
    for ticker, data in metrics.items():
        pe = data.get('pe_ratio', 'N/A')
        ps = data.get('ps_ratio', 'N/A')
        div_yield = data.get('dividend_yield_percent', 'N/A')
        pe_str = f"{pe:.2f}" if isinstance(pe, (int, float)) else pe
        ps_str = f"{ps:.2f}" if isinstance(ps, (int, float)) else ps
        div_str = f"{div_yield:.2f}%" if isinstance(div_yield, (int, float)) else div_yield
        print(f"   {ticker}: P/E={pe_str}, P/S={ps_str}, Div Yield={div_str}")

    # Test peer comparison
    print("\n3. Peer Comparison:")
    print("-" * 40)
    comparison = fetcher.get_peer_comparison()
    print(f"   Average P/E: {comparison['averages']['pe_ratio']}")
    print(f"   Average Revenue Growth: {comparison['averages']['revenue_growth_percent']}%")

    # Test Target summary
    print("\n4. Target Valuation Summary:")
    print("-" * 40)
    summary = fetcher.get_target_valuation_summary()
    print(f"   Status: {summary['valuation_status']}")
    if summary['pe_discount_percent']:
        print(f"   P/E Discount vs Peers: {summary['pe_discount_percent']:.1f}%")

    # Test historical prices
    print("\n5. Historical Prices (last 5 entries):")
    print("-" * 40)
    history = fetcher.get_historical_prices('TGT', '1y')
    if not history.empty:
        print(history.tail().to_string())

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
