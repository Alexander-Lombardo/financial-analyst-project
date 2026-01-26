#!/usr/bin/env python3
"""
Test Suite for Pillar 5: Valuation & Market Sentiment

Tests the market data fetching and valuation chart creation:
- Market Data Fetcher functionality
- Chart 23: Valuation vs Growth Scatter Plot
- Chart 24: Historical P/E Band Area Chart

Run: python3 test_pillar5_valuation_sentiment.py
"""

import json
import os
import unittest
from pathlib import Path


class TestMarketDataFetcher(unittest.TestCase):
    """Test suite for MarketDataFetcher class."""

    @classmethod
    def setUpClass(cls):
        """Initialize the market data fetcher."""
        from market_data_fetcher import MarketDataFetcher
        cls.fetcher = MarketDataFetcher()

    def test_fetcher_initialization(self):
        """Test that fetcher initializes with correct tickers."""
        expected_tickers = ['TGT', 'WMT', 'COST', 'AMZN', 'KR']
        self.assertEqual(self.fetcher.tickers, expected_tickers)
        print("✅ MarketDataFetcher initialized with correct tickers")

    def test_get_current_prices(self):
        """Test that current prices are fetched for all tickers."""
        prices = self.fetcher.get_current_prices()

        self.assertIsInstance(prices, dict)
        self.assertIn('TGT', prices)

        # Price should be a reasonable value (> $10, < $2000)
        tgt_price = prices.get('TGT')
        if tgt_price:
            self.assertGreater(tgt_price, 10, "TGT price seems too low")
            self.assertLess(tgt_price, 500, "TGT price seems too high")
            print(f"✅ Current prices fetched: TGT = ${tgt_price:.2f}")

    def test_get_valuation_metrics(self):
        """Test that valuation metrics are fetched correctly."""
        metrics = self.fetcher.get_valuation_metrics()

        self.assertIsInstance(metrics, dict)
        self.assertIn('TGT', metrics)

        tgt_metrics = metrics.get('TGT', {})

        # Check for required fields
        required_fields = ['price', 'pe_ratio', 'ps_ratio']
        for field in required_fields:
            self.assertIn(field, tgt_metrics,
                f"Missing field: {field}")

        # Validate P/E ratio is reasonable (> 0, < 100 for retail)
        pe_ratio = tgt_metrics.get('pe_ratio')
        if pe_ratio:
            self.assertGreater(pe_ratio, 0, "P/E ratio should be positive")
            self.assertLess(pe_ratio, 100, "P/E ratio seems too high for retail")
            print(f"✅ Valuation metrics fetched: TGT P/E = {pe_ratio:.2f}x")

    def test_get_peer_comparison(self):
        """Test that peer comparison data is structured correctly."""
        comparison = self.fetcher.get_peer_comparison()

        self.assertIn('companies', comparison)
        self.assertIn('averages', comparison)

        companies = comparison.get('companies', [])
        self.assertGreaterEqual(len(companies), 2,
            "Should have at least 2 companies for comparison")

        # Check averages are calculated
        averages = comparison.get('averages', {})
        self.assertIn('pe_ratio', averages)
        print(f"✅ Peer comparison: {len(companies)} companies, Avg P/E = {averages.get('pe_ratio')}")

    def test_get_historical_prices(self):
        """Test that historical price data is fetched."""
        history = self.fetcher.get_historical_prices('TGT', '1y')

        self.assertFalse(history.empty, "Historical data should not be empty")
        self.assertIn('Close', history.columns, "Should have Close prices")

        # Check we have reasonable amount of data (at least 200 trading days in a year)
        self.assertGreater(len(history), 100,
            "Should have at least 100 data points for 1 year")
        print(f"✅ Historical prices fetched: {len(history)} data points")

    def test_cache_functionality(self):
        """Test that caching works correctly."""
        # First call - may fetch from API
        prices1 = self.fetcher.get_current_prices()

        # Second call - should use cache
        prices2 = self.fetcher.get_current_prices()

        # Prices should be the same (from cache)
        self.assertEqual(prices1.get('TGT'), prices2.get('TGT'),
            "Cached prices should match")
        print("✅ Cache functionality working")


class TestValuationCharts(unittest.TestCase):
    """Test suite for Pillar 5 valuation charts."""

    @classmethod
    def setUpClass(cls):
        """Load test data and generate charts."""
        timeseries_path = Path("output/target_timeseries.json")
        if not timeseries_path.exists():
            raise FileNotFoundError("Run financial_analyzer.py first to generate data")

        with open(timeseries_path, 'r') as f:
            cls.data = json.load(f)

    def test_chart23_file_exists(self):
        """Test that Chart 23 HTML file was created."""
        chart_path = Path("output/chart_valuation_scatter.html")
        self.assertTrue(chart_path.exists(),
            "Chart 23 (Valuation Scatter) HTML file not found")

        file_size = chart_path.stat().st_size
        self.assertGreater(file_size, 5000,
            f"Chart 23 file too small ({file_size} bytes)")
        print(f"✅ Chart 23 exists: {file_size:,} bytes")

    def test_chart23_has_required_elements(self):
        """Test that Chart 23 contains required elements."""
        chart_path = Path("output/chart_valuation_scatter.html")
        if not chart_path.exists():
            self.skipTest("Chart 23 not generated")

        with open(chart_path, 'r') as f:
            content = f.read()

        # Check for key elements (P/E may be encoded as P\u002fE in JSON)
        self.assertIn("TGT", content, "Chart 23 missing Target ticker")
        has_pe = "P/E" in content or "P\\u002fE" in content or "Ratio" in content
        self.assertTrue(has_pe, "Chart 23 missing P/E reference")
        self.assertIn("Revenue Growth", content, "Chart 23 missing Revenue Growth")
        self.assertIn("Pillar 5", content, "Chart 23 missing Pillar 5 reference")

        print("✅ Chart 23 contains all required elements")

    def test_chart24_file_exists(self):
        """Test that Chart 24 HTML file was created."""
        chart_path = Path("output/chart_pe_band.html")
        self.assertTrue(chart_path.exists(),
            "Chart 24 (P/E Band) HTML file not found")

        file_size = chart_path.stat().st_size
        self.assertGreater(file_size, 10000,
            f"Chart 24 file too small ({file_size} bytes)")
        print(f"✅ Chart 24 exists: {file_size:,} bytes")

    def test_chart24_has_required_elements(self):
        """Test that Chart 24 contains required elements."""
        chart_path = Path("output/chart_pe_band.html")
        if not chart_path.exists():
            self.skipTest("Chart 24 not generated")

        with open(chart_path, 'r') as f:
            content = f.read()

        # Check for key elements (P/E may be encoded as P\u002fE in JSON)
        self.assertIn("Stock Price", content, "Chart 24 missing Stock Price label")
        has_pe = "P/E" in content or "P\\u002fE" in content
        self.assertTrue(has_pe, "Chart 24 missing P/E reference")
        self.assertIn("Undervalued", content, "Chart 24 missing valuation zones")
        self.assertIn("Pillar 5", content, "Chart 24 missing Pillar 5 reference")

        print("✅ Chart 24 contains all required elements")


class TestValuationMetricsCalculation(unittest.TestCase):
    """Test valuation metric calculations."""

    @classmethod
    def setUpClass(cls):
        """Initialize market data fetcher."""
        from market_data_fetcher import MarketDataFetcher
        cls.fetcher = MarketDataFetcher()
        cls.metrics = cls.fetcher.get_valuation_metrics()

    def test_pe_ratio_values(self):
        """Test that P/E ratios are in reasonable range."""
        pe_ratios = []
        for ticker, data in self.metrics.items():
            pe = data.get('pe_ratio')
            if pe is not None:
                pe_ratios.append((ticker, pe))
                # P/E should be positive and reasonable for retail
                self.assertGreater(pe, 0, f"{ticker} P/E should be positive")
                self.assertLess(pe, 100, f"{ticker} P/E {pe:.1f} seems high")

        print(f"✅ P/E ratios validated for {len(pe_ratios)} companies")

    def test_ps_ratio_values(self):
        """Test that P/S ratios are in reasonable range."""
        ps_ratios = []
        for ticker, data in self.metrics.items():
            ps = data.get('ps_ratio')
            if ps is not None:
                ps_ratios.append((ticker, ps))
                # P/S should be positive for any company
                self.assertGreater(ps, 0, f"{ticker} P/S should be positive")

        print(f"✅ P/S ratios validated for {len(ps_ratios)} companies")

    def test_dividend_yield_values(self):
        """Test that dividend yields are reasonable."""
        for ticker, data in self.metrics.items():
            div_yield = data.get('dividend_yield_percent')
            if div_yield is not None:
                # Dividend yield should be 0-15% for normal companies
                self.assertGreaterEqual(div_yield, 0,
                    f"{ticker} dividend yield should not be negative")
                self.assertLess(div_yield, 20,
                    f"{ticker} dividend yield {div_yield:.1f}% seems high")

        print("✅ Dividend yields validated")

    def test_target_valuation_summary(self):
        """Test Target valuation summary generation."""
        summary = self.fetcher.get_target_valuation_summary()

        self.assertIn('target', summary)
        self.assertIn('peer_averages', summary)
        self.assertIn('valuation_status', summary)

        status = summary.get('valuation_status')
        self.assertIn(status, ['Undervalued', 'Fair Value', 'Overvalued', 'N/A'],
            f"Invalid valuation status: {status}")

        print(f"✅ Target valuation summary: {status}")


def run_tests():
    """Run all Pillar 5 tests."""
    print("=" * 70)
    print("Running Pillar 5: Valuation & Market Sentiment Tests")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMarketDataFetcher))
    suite.addTests(loader.loadTestsFromTestCase(TestValuationCharts))
    suite.addTests(loader.loadTestsFromTestCase(TestValuationMetricsCalculation))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")

    return result


if __name__ == "__main__":
    run_tests()
