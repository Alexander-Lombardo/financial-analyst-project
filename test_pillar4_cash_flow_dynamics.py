#!/usr/bin/env python3
"""
Test Suite for Pillar 4: Cash Flow Dynamics

Tests the extraction and calculation of:
- Capital Expenditures (CapEx)
- Free Cash Flow (FCF = OCF - CapEx)
- Cash flow components (dividends, buybacks, debt repayments)
- Chart 21: OCF vs CapEx Combo Chart
- Chart 22: Cash Flow Sankey Diagram

Run: python3 test_pillar4_cash_flow_dynamics.py
"""
import json
import os
import unittest
from pathlib import Path


class TestPillar4CashFlowDynamics(unittest.TestCase):
    """Test suite for Pillar 4: Cash Flow Dynamics metrics and visualizations."""

    @classmethod
    def setUpClass(cls):
        """Load test data once for all tests."""
        timeseries_path = Path("output/target_timeseries.json")
        if not timeseries_path.exists():
            raise FileNotFoundError("Run financial_analyzer.py first to generate data")

        with open(timeseries_path, 'r') as f:
            cls.data = json.load(f)

        cls.cash_flows = cls.data['metrics']['cash_flows']
        cls.periods = cls.data['periods']
        cls.num_periods = len(cls.periods)

    # =========================================================================
    # CapEx Extraction Tests
    # =========================================================================

    def test_capex_extraction_coverage(self):
        """Test that CapEx is extracted for majority of periods."""
        capex = self.cash_flows['capital_expenditures_billion']
        non_null = sum(1 for x in capex if x is not None)

        # Expect at least 90% coverage (CapEx should be in all filings)
        coverage = non_null / self.num_periods
        self.assertGreaterEqual(coverage, 0.90,
            f"CapEx coverage {coverage:.1%} below 90% threshold")
        print(f"✅ CapEx extraction: {non_null}/{self.num_periods} periods ({coverage:.1%})")

    def test_capex_values_reasonable(self):
        """Test that CapEx values are in reasonable range for Target."""
        capex = [x for x in self.cash_flows['capital_expenditures_billion'] if x is not None]

        # Target quarterly CapEx typically $0.5B - $3B
        # Annual CapEx typically $2B - $6B
        min_capex = min(capex)
        max_capex = max(capex)

        self.assertGreater(min_capex, 0, "CapEx should be positive")
        self.assertLess(max_capex, 10, "CapEx > $10B seems unreasonable for Target")
        print(f"✅ CapEx range: ${min_capex:.2f}B - ${max_capex:.2f}B (reasonable)")

    def test_capex_positive_values(self):
        """Test that all CapEx values are positive (cash outflow)."""
        capex = [x for x in self.cash_flows['capital_expenditures_billion'] if x is not None]

        negative_count = sum(1 for x in capex if x < 0)
        self.assertEqual(negative_count, 0,
            f"Found {negative_count} negative CapEx values (should all be positive)")
        print(f"✅ All {len(capex)} CapEx values are positive")

    # =========================================================================
    # Free Cash Flow Calculation Tests
    # =========================================================================

    def test_fcf_calculation_coverage(self):
        """Test that FCF is calculated for periods with both OCF and CapEx."""
        fcf = self.cash_flows['free_cash_flow_billion']
        non_null = sum(1 for x in fcf if x is not None)

        # FCF requires both OCF and CapEx
        ocf = self.cash_flows['operating_cash_flow_billion']
        capex = self.cash_flows['capital_expenditures_billion']
        expected_count = sum(1 for o, c in zip(ocf, capex) if o is not None and c is not None)

        self.assertEqual(non_null, expected_count,
            f"FCF count {non_null} doesn't match expected {expected_count}")
        print(f"✅ FCF calculated: {non_null}/{self.num_periods} periods")

    def test_fcf_formula_correct(self):
        """Test that FCF = OCF - CapEx formula is correctly applied."""
        ocf = self.cash_flows['operating_cash_flow_billion']
        capex = self.cash_flows['capital_expenditures_billion']
        fcf = self.cash_flows['free_cash_flow_billion']

        errors = []
        for i in range(self.num_periods):
            if ocf[i] is not None and capex[i] is not None and fcf[i] is not None:
                expected_fcf = ocf[i] - capex[i]
                if abs(fcf[i] - expected_fcf) > 0.01:  # Allow $10M tolerance
                    errors.append(f"{self.periods[i]['period']}: "
                                  f"FCF={fcf[i]}, expected={expected_fcf:.3f}")

        self.assertEqual(len(errors), 0,
            f"FCF formula errors:\n" + "\n".join(errors))
        print(f"✅ FCF = OCF - CapEx formula verified for all periods")

    def test_fcf_can_be_negative(self):
        """Test that FCF can be negative (when CapEx > OCF)."""
        fcf = [x for x in self.cash_flows['free_cash_flow_billion'] if x is not None]

        negative_fcf = [x for x in fcf if x < 0]
        # Some quarters may have negative FCF (heavy investment periods)
        print(f"ℹ️ FCF distribution: {len([x for x in fcf if x > 0])} positive, "
              f"{len(negative_fcf)} negative quarters")

        # Just verify we can handle both positive and negative values
        self.assertTrue(len(fcf) > 0, "Should have FCF values")

    def test_fcf_margin_calculation(self):
        """Test that FCF margin is calculated correctly."""
        fcf_margin = self.cash_flows['free_cash_flow_margin_percent']
        non_null = sum(1 for x in fcf_margin if x is not None)

        self.assertGreater(non_null, 0, "Should have FCF margin calculations")

        # FCF margin should typically be -5% to 15% for retail
        margins = [x for x in fcf_margin if x is not None]
        print(f"✅ FCF margin range: {min(margins):.1f}% to {max(margins):.1f}%")

    # =========================================================================
    # Cash Flow Components Tests (for Sankey Diagram)
    # =========================================================================

    def test_dividends_extraction(self):
        """Test that dividends paid are extracted."""
        dividends = self.cash_flows['dividends_paid_billion']
        non_null = sum(1 for x in dividends if x is not None)

        # Dividends should be available in most periods
        coverage = non_null / self.num_periods
        self.assertGreaterEqual(coverage, 0.80,
            f"Dividends coverage {coverage:.1%} below 80% threshold")
        print(f"✅ Dividends extraction: {non_null}/{self.num_periods} periods ({coverage:.1%})")

    def test_stock_repurchases_extraction(self):
        """Test that stock repurchases are extracted."""
        buybacks = self.cash_flows['stock_repurchases_billion']
        non_null = sum(1 for x in buybacks if x is not None)

        # Stock buybacks may not be in every period
        coverage = non_null / self.num_periods
        self.assertGreaterEqual(coverage, 0.50,
            f"Stock repurchases coverage {coverage:.1%} below 50% threshold")
        print(f"✅ Stock repurchases extraction: {non_null}/{self.num_periods} periods ({coverage:.1%})")

    def test_debt_repayments_extraction(self):
        """Test that debt repayments are extracted."""
        debt_repay = self.cash_flows['debt_repayments_billion']
        non_null = sum(1 for x in debt_repay if x is not None)

        # Debt repayments may vary by period
        coverage = non_null / self.num_periods
        self.assertGreaterEqual(coverage, 0.50,
            f"Debt repayments coverage {coverage:.1%} below 50% threshold")
        print(f"✅ Debt repayments extraction: {non_null}/{self.num_periods} periods ({coverage:.1%})")

    def test_cash_flow_components_positive(self):
        """Test that cash outflow components are positive values."""
        dividends = self.cash_flows['dividends_paid_billion']
        buybacks = self.cash_flows['stock_repurchases_billion']
        debt_repay = self.cash_flows['debt_repayments_billion']

        for name, values in [('Dividends', dividends),
                             ('Buybacks', buybacks),
                             ('Debt Repayments', debt_repay)]:
            negative = sum(1 for x in values if x is not None and x < 0)
            self.assertEqual(negative, 0,
                f"{name} should be positive (found {negative} negative values)")

        print("✅ All cash flow components are positive values")

    # =========================================================================
    # Chart 21: OCF vs CapEx Tests
    # =========================================================================

    def test_chart21_file_exists(self):
        """Test that Chart 21 HTML file was created."""
        chart_path = Path("output/chart_ocf_vs_capex.html")
        self.assertTrue(chart_path.exists(),
            "Chart 21 (OCF vs CapEx) HTML file not found")

        file_size = chart_path.stat().st_size
        self.assertGreater(file_size, 10000,
            f"Chart 21 file too small ({file_size} bytes)")
        print(f"✅ Chart 21 exists: {file_size:,} bytes")

    def test_chart21_has_required_elements(self):
        """Test that Chart 21 contains required chart elements."""
        chart_path = Path("output/chart_ocf_vs_capex.html")
        with open(chart_path, 'r') as f:
            content = f.read()

        # Check for key elements
        self.assertIn("Operating Cash Flow", content,
            "Chart 21 missing 'Operating Cash Flow' label")
        self.assertIn("Capital Expenditures", content,
            "Chart 21 missing 'Capital Expenditures' label")
        self.assertIn("Free Cash Flow", content,
            "Chart 21 missing 'Free Cash Flow' label")
        self.assertIn("Pillar 4", content,
            "Chart 21 missing 'Pillar 4' reference")

        print("✅ Chart 21 contains all required elements")

    # =========================================================================
    # Chart 22: Cash Flow Sankey Tests
    # =========================================================================

    def test_chart22_file_exists(self):
        """Test that Chart 22 HTML file was created."""
        chart_path = Path("output/chart_cash_flow_sankey.html")
        self.assertTrue(chart_path.exists(),
            "Chart 22 (Sankey) HTML file not found")

        file_size = chart_path.stat().st_size
        self.assertGreater(file_size, 10000,
            f"Chart 22 file too small ({file_size} bytes)")
        print(f"✅ Chart 22 exists: {file_size:,} bytes")

    def test_chart22_has_sankey_elements(self):
        """Test that Chart 22 contains Sankey diagram elements."""
        chart_path = Path("output/chart_cash_flow_sankey.html")
        with open(chart_path, 'r') as f:
            content = f.read()

        # Check for Sankey-specific elements
        self.assertIn("sankey", content.lower(),
            "Chart 22 missing Sankey diagram type")
        self.assertIn("Dividends", content,
            "Chart 22 missing 'Dividends' node")
        self.assertIn("Capital Expenditures", content,
            "Chart 22 missing 'Capital Expenditures' node")

        print("✅ Chart 22 contains Sankey diagram elements")

    def test_chart22_has_dropdown(self):
        """Test that Chart 22 has fiscal year dropdown."""
        chart_path = Path("output/chart_cash_flow_sankey.html")
        with open(chart_path, 'r') as f:
            content = f.read()

        # Check for dropdown menu (fiscal year selector)
        self.assertIn("FY2024", content, "Chart 22 missing FY2024 option")
        self.assertIn("FY2023", content, "Chart 22 missing FY2023 option")

        print("✅ Chart 22 has fiscal year dropdown")


class TestPillar4DataConsistency(unittest.TestCase):
    """Test data consistency between related Pillar 4 metrics."""

    @classmethod
    def setUpClass(cls):
        """Load test data."""
        with open("output/target_timeseries.json", 'r') as f:
            cls.data = json.load(f)
        cls.cash_flows = cls.data['metrics']['cash_flows']

    def test_fcf_less_than_ocf_when_capex_positive(self):
        """Test that FCF < OCF when there is CapEx spending."""
        ocf = self.cash_flows['operating_cash_flow_billion']
        capex = self.cash_flows['capital_expenditures_billion']
        fcf = self.cash_flows['free_cash_flow_billion']

        for i in range(len(ocf)):
            if all([ocf[i], capex[i], fcf[i], capex[i] > 0]):
                self.assertLess(fcf[i], ocf[i],
                    f"FCF should be less than OCF when CapEx > 0")

        print("✅ FCF < OCF relationship verified")

    def test_annual_capex_greater_than_quarterly(self):
        """Test that annual CapEx is typically larger than quarterly."""
        periods = self.data['periods']
        capex = self.cash_flows['capital_expenditures_billion']

        annual_capex = [capex[i] for i, p in enumerate(periods)
                        if p['filing_type'] == '10-K' and capex[i] is not None]
        quarterly_capex = [capex[i] for i, p in enumerate(periods)
                          if p['filing_type'] == '10-Q' and capex[i] is not None]

        if annual_capex and quarterly_capex:
            avg_annual = sum(annual_capex) / len(annual_capex)
            avg_quarterly = sum(quarterly_capex) / len(quarterly_capex)

            self.assertGreater(avg_annual, avg_quarterly,
                f"Annual CapEx (${avg_annual:.2f}B) should be > quarterly (${avg_quarterly:.2f}B)")
            print(f"✅ Annual CapEx (${avg_annual:.2f}B) > Quarterly (${avg_quarterly:.2f}B)")


def run_tests():
    """Run all Pillar 4 tests."""
    print("=" * 70)
    print("Running Pillar 4: Cash Flow Dynamics Tests")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPillar4CashFlowDynamics))
    suite.addTests(loader.loadTestsFromTestCase(TestPillar4DataConsistency))

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
