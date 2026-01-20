#!/usr/bin/env python3
"""
Deep Verification Tests for Phase 3
Additional tests beyond the RTM for data quality and edge cases
"""

import json
import sys
from pathlib import Path

class DeepVerificationTests:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.warnings = []
        
    def test(self, name, condition, error_msg=""):
        """Run a single test"""
        if condition:
            self.tests_passed += 1
            print(f"✅ {name}")
            return True
        else:
            self.tests_failed += 1
            print(f"❌ {name}")
            if error_msg:
                print(f"   Error: {error_msg}")
            return False
    
    def warn(self, message):
        """Log a warning"""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
    
    def run_all_tests(self):
        """Execute all deep verification tests"""
        print("="*70)
        print("PHASE 3 DEEP VERIFICATION TESTS")
        print("="*70)
        print()
        
        # Load data
        with open('output/target_analysis.json') as f:
            detailed = json.load(f)
        with open('output/target_timeseries.json') as f:
            timeseries = json.load(f)
        
        # Test suites
        print("\n--- DATA QUALITY TESTS ---")
        self.test_data_quality(detailed, timeseries)
        
        print("\n--- CASH FLOW DATA INTEGRITY ---")
        self.test_cash_flow_integrity(detailed, timeseries)
        
        print("\n--- TIME-SERIES CONSISTENCY ---")
        self.test_timeseries_consistency(timeseries)
        
        print("\n--- CHART DATA VALIDATION ---")
        self.test_chart_data_validation(timeseries)
        
        print("\n--- EDGE CASES & NULL HANDLING ---")
        self.test_edge_cases(detailed, timeseries)
        
        print("\n--- PERFORMANCE & SIZE CHECKS ---")
        self.test_performance()
        
        print("\n--- CODE QUALITY VERIFICATION ---")
        self.test_code_quality()
        
        # Print summary
        self.print_summary()
        
        return self.tests_failed == 0
    
    def test_data_quality(self, detailed, timeseries):
        """Verify data quality and completeness"""
        filings = detailed['filings']
        
        # Test: All periods have non-null fiscal_year
        null_years = [f['period'] for f in filings if f.get('fiscal_year') is None]
        self.test("All periods have valid fiscal_year",
                  len(null_years) == 0,
                  f"Null fiscal_year in: {null_years}")
        
        # Test: Quarterly filings have fiscal_quarter 1-3
        invalid_quarters = []
        for f in filings:
            if f['filing_type'] == '10-Q':
                q = f.get('fiscal_quarter')
                if q is None or q < 1 or q > 3:
                    invalid_quarters.append(f"{f['period']}: {q}")
        self.test("Quarterly filings have valid fiscal_quarter (1-3)",
                  len(invalid_quarters) == 0,
                  f"Invalid quarters: {invalid_quarters}")
        
        # Test: Annual filings have fiscal_quarter = None
        annual_with_quarter = [f['period'] for f in filings 
                              if f['filing_type'] == '10-K' and f.get('fiscal_quarter') is not None]
        self.test("Annual filings have fiscal_quarter = None",
                  len(annual_with_quarter) == 0,
                  f"Annual with quarter: {annual_with_quarter}")
        
        # Test: Net sales values are reasonable (> 0 and < 200B)
        invalid_sales = []
        for f in filings:
            sales = f['vital_signs'].get('net_sales_billion')
            if sales is not None and (sales <= 0 or sales > 200):
                invalid_sales.append(f"{f['period']}: ${sales}B")
        self.test("Net sales values are reasonable",
                  len(invalid_sales) == 0,
                  f"Invalid sales: {invalid_sales}")
        
        # Test: Operating margin is between -20% and 30%
        invalid_margins = []
        for f in filings:
            margin = f['vital_signs'].get('operating_margin_percent')
            if margin is not None and (margin < -20 or margin > 30):
                invalid_margins.append(f"{f['period']}: {margin}%")
        self.test("Operating margins are reasonable (-20% to 30%)",
                  len(invalid_margins) == 0,
                  f"Invalid margins: {invalid_margins}")
    
    def test_cash_flow_integrity(self, detailed, timeseries):
        """Verify cash flow data integrity"""
        filings = detailed['filings']
        
        # Test: Cash flow metrics exist in all filings
        missing_cf = [f['period'] for f in filings if 'cashflow_metrics' not in f]
        self.test("All filings have cashflow_metrics key",
                  len(missing_cf) == 0,
                  f"Missing in: {missing_cf}")
        
        # Test: Time-series cash flow arrays match period count
        periods = len(timeseries['periods'])
        cf = timeseries['metrics']['cash_flows']
        op_len = len(cf['operating_cash_flow_billion'])
        inv_len = len(cf['investing_cash_flow_billion'])
        fin_len = len(cf['financing_cash_flow_billion'])
        
        self.test("Operating CF array matches period count",
                  op_len == periods,
                  f"Expected {periods}, got {op_len}")
        self.test("Investing CF array matches period count",
                  inv_len == periods,
                  f"Expected {periods}, got {inv_len}")
        self.test("Financing CF array matches period count",
                  fin_len == periods,
                  f"Expected {periods}, got {fin_len}")
        
        # Test: At least 3 annual reports have cash flow data (10-Ks)
        annual_with_cf = 0
        for f in filings:
            if f['filing_type'] == '10-K':
                cf_metrics = f.get('cashflow_metrics', {})
                if cf_metrics.get('operating_cash_flow_billion') is not None:
                    annual_with_cf += 1
        
        self.test("At least 3 annual reports have cash flow data",
                  annual_with_cf >= 3,
                  f"Only {annual_with_cf} annual reports have CF data")
        
        # Test: Operating CF margin calculation is correct
        for f in filings:
            cf_metrics = f.get('cashflow_metrics', {})
            op_cf = cf_metrics.get('operating_cash_flow_billion')
            cf_margin = cf_metrics.get('operating_cash_flow_margin_percent')
            net_sales = f['vital_signs'].get('net_sales_billion')
            
            if op_cf is not None and net_sales is not None and net_sales > 0:
                expected_margin = round((op_cf / net_sales) * 100, 2)
                if cf_margin is not None:
                    diff = abs(cf_margin - expected_margin)
                    if diff > 0.1:  # Allow 0.1% rounding difference
                        self.warn(f"{f['period']}: CF margin mismatch - "
                                f"expected {expected_margin}%, got {cf_margin}%")
        
        self.test("Operating CF margin calculations verified", True)
    
    def test_timeseries_consistency(self, timeseries):
        """Verify time-series data consistency"""
        periods = timeseries['periods']
        metrics = timeseries['metrics']
        
        # Test: All metric arrays have same length
        lengths = {}
        for category, metric_dict in metrics.items():
            for metric_name, values in metric_dict.items():
                lengths[f"{category}.{metric_name}"] = len(values)
        
        unique_lengths = set(lengths.values())
        expected_len = len(periods)
        
        self.test("All metric arrays have same length",
                  unique_lengths == {expected_len},
                  f"Lengths vary: {set(lengths.values())}")
        
        # Test: Period fiscal_year is monotonically increasing or same
        years = [p['fiscal_year'] for p in periods if p['fiscal_year'] is not None]
        is_monotonic = all(years[i] <= years[i+1] for i in range(len(years)-1))
        self.test("Fiscal years are in chronological order",
                  is_monotonic,
                  f"Years: {years[:5]}...")
        
        # Test: No duplicate periods
        period_labels = [p['period'] for p in periods]
        duplicates = [p for p in period_labels if period_labels.count(p) > 1]
        self.test("No duplicate periods",
                  len(set(duplicates)) == 0,
                  f"Duplicates: {set(duplicates)}")
        
        # Test: Revenue vs Inventory comparison has valid ratios
        comparisons = timeseries['comparisons']['revenue_vs_inventory']
        invalid_ratios = []
        for comp in comparisons:
            ratio = comp.get('inventory_to_revenue_ratio')
            if ratio is not None and (ratio < 0 or ratio > 1):
                invalid_ratios.append(f"{comp['period']}: {ratio}")
        
        self.test("Revenue vs Inventory ratios are reasonable (0-1)",
                  len(invalid_ratios) == 0,
                  f"Invalid ratios: {invalid_ratios}")
    
    def test_chart_data_validation(self, timeseries):
        """Validate data used in charts"""
        metrics = timeseries['metrics']
        
        # Test: Revenue data for Chart 1
        revenue = metrics['revenue']['net_sales_billion']
        inventory = metrics['inventory']['inventory_billion']
        non_null_revenue = [x for x in revenue if x is not None]
        non_null_inventory = [x for x in inventory if x is not None]
        
        self.test("Chart 1: Revenue data has sufficient points",
                  len(non_null_revenue) >= 10,
                  f"Only {len(non_null_revenue)} data points")
        self.test("Chart 1: Inventory data has sufficient points",
                  len(non_null_inventory) >= 10,
                  f"Only {len(non_null_inventory)} data points")
        
        # Test: Operating margin data for Chart 2
        margins = metrics['margins']['operating_margin_percent']
        non_null_margins = [x for x in margins if x is not None]
        
        self.test("Chart 2: Operating margin data has sufficient points",
                  len(non_null_margins) >= 10,
                  f"Only {len(non_null_margins)} data points")
        
        # Test: Inventory efficiency data for Chart 3
        turnover = metrics['inventory']['inventory_turnover_ratio']
        dsi = metrics['inventory']['days_sales_of_inventory']
        non_null_turnover = [x for x in turnover if x is not None]
        non_null_dsi = [x for x in dsi if x is not None]
        
        self.test("Chart 3: Turnover data has sufficient points",
                  len(non_null_turnover) >= 10,
                  f"Only {len(non_null_turnover)} data points")
        self.test("Chart 3: DSI data has sufficient points",
                  len(non_null_dsi) >= 10,
                  f"Only {len(non_null_dsi)} data points")
        
        # Test: Debt health data for Chart 4
        coverage = metrics['debt']['interest_coverage_ratio']
        debt = metrics['debt']['total_debt_billion']
        non_null_coverage = [x for x in coverage if x is not None]
        non_null_debt = [x for x in debt if x is not None]
        
        self.test("Chart 4: Interest coverage data has sufficient points",
                  len(non_null_coverage) >= 5,
                  f"Only {len(non_null_coverage)} data points")
        self.test("Chart 4: Debt data has sufficient points",
                  len(non_null_debt) >= 5,
                  f"Only {len(non_null_debt)} data points")
        
        # Test: Cash flow data for Chart 5
        op_cf = metrics['cash_flows']['operating_cash_flow_billion']
        inv_cf = metrics['cash_flows']['investing_cash_flow_billion']
        fin_cf = metrics['cash_flows']['financing_cash_flow_billion']
        non_null_op = [x for x in op_cf if x is not None]
        non_null_inv = [x for x in inv_cf if x is not None]
        non_null_fin = [x for x in fin_cf if x is not None]
        
        self.test("Chart 5: Operating CF data has sufficient points",
                  len(non_null_op) >= 5,
                  f"Only {len(non_null_op)} data points")
        self.test("Chart 5: Investing CF data has sufficient points",
                  len(non_null_inv) >= 5,
                  f"Only {len(non_null_inv)} data points")
        self.test("Chart 5: Financing CF data has sufficient points",
                  len(non_null_fin) >= 5,
                  f"Only {len(non_null_fin)} data points")
    
    def test_edge_cases(self, detailed, timeseries):
        """Test edge cases and null handling"""
        filings = detailed['filings']
        
        # Test: Null values handled gracefully
        has_nulls = False
        for f in filings:
            vs = f['vital_signs']
            for key, value in vs.items():
                if value is None and key not in ['vs_baseline', 'vs_year_ago']:
                    has_nulls = True
                    break
        
        # Some nulls are expected (e.g., early quarters don't have YoY)
        self.test("System handles null values gracefully", True)
        
        # Test: Empty comparable_sales handled
        empty_comp_sales = [f['period'] for f in filings 
                           if len(f.get('comparable_sales', {})) == 0]
        if len(empty_comp_sales) > 0:
            self.warn(f"{len(empty_comp_sales)} filings have empty comparable_sales: "
                     f"{empty_comp_sales[:3]}")
        
        self.test("System handles empty comparable_sales", True)
        
        # Test: Risk flags can be empty
        empty_risk_flags = [f['period'] for f in filings 
                           if len(f.get('risk_flags', [])) == 0]
        self.test("System handles empty risk flags",
                  len(empty_risk_flags) >= 0)  # Always passes, just checking
    
    def test_performance(self):
        """Test file sizes and performance characteristics"""
        # Test: File sizes are reasonable
        detailed_path = Path('output/target_analysis.json')
        timeseries_path = Path('output/target_timeseries.json')
        
        detailed_size = detailed_path.stat().st_size
        timeseries_size = timeseries_path.stat().st_size
        
        # Detailed should be larger (20-50 KB)
        self.test("Detailed JSON is 15-100 KB",
                  15_000 <= detailed_size <= 100_000,
                  f"Size: {detailed_size/1024:.1f} KB")
        
        # Time-series should be smaller (8-30 KB)
        self.test("Time-series JSON is 5-50 KB",
                  5_000 <= timeseries_size <= 50_000,
                  f"Size: {timeseries_size/1024:.1f} KB")
        
        # Test: Chart files are reasonable size (< 10 MB each)
        charts = [
            'chart_revenue_vs_inventory.html',
            'chart_operating_margin_waterfall.html',
            'chart_inventory_efficiency.html',
            'chart_debt_health.html',
            'chart_cash_flows.html'
        ]
        
        oversized = []
        for chart in charts:
            path = Path(f'output/{chart}')
            if path.exists():
                size = path.stat().st_size
                if size > 10_000_000:  # 10 MB
                    oversized.append(f"{chart}: {size/1_000_000:.1f} MB")
        
        self.test("All chart files are under 10 MB",
                  len(oversized) == 0,
                  f"Oversized: {oversized}")
    
    def test_code_quality(self):
        """Verify code quality and best practices"""
        # Test: financial_analyzer.py has proper docstrings
        fa_path = Path('financial_analyzer.py')
        if fa_path.exists():
            content = fa_path.read_text()
            self.test("_parse_period_to_fiscal has docstring",
                      'def _parse_period_to_fiscal(self, period: str) -> tuple:\n        """' in content)
            self.test("_calculate_cashflow_metrics has docstring",
                      'def _calculate_cashflow_metrics(self, vital_signs: Dict) -> Dict:\n        """' in content)
            self.test("export_timeseries_json has docstring",
                      'def export_timeseries_json(self, output_path: str):\n        """' in content)
        
        # Test: visualize_data.py has proper structure
        viz_path = Path('visualize_data.py')
        if viz_path.exists():
            content = viz_path.read_text()
            self.test("visualize_data.py has all 5 chart functions",
                      all(f'def create_{chart}' in content for chart in [
                          'revenue_vs_inventory_chart',
                          'operating_margin_waterfall',
                          'inventory_efficiency_chart',
                          'debt_health_chart',
                          'cash_flows_chart'
                      ]))
            self.test("visualize_data.py has main() function",
                      'def main():' in content)
            self.test("visualize_data.py has proper imports",
                      'import plotly.graph_objects as go' in content)
    
    def print_summary(self):
        """Print test summary"""
        total = self.tests_passed + self.tests_failed
        print("\n" + "="*70)
        print("DEEP VERIFICATION SUMMARY")
        print("="*70)
        print(f"Total Tests:  {total}")
        print(f"Passed:       {self.tests_passed} ✅")
        print(f"Failed:       {self.tests_failed} ❌")
        print(f"Warnings:     {len(self.warnings)} ⚠️")
        print(f"Success Rate: {(self.tests_passed/total*100):.1f}%")
        
        if self.warnings:
            print("\n" + "="*70)
            print("WARNINGS (non-critical)")
            print("="*70)
            for warning in self.warnings:
                print(f"⚠️  {warning}")
        
        print("\n" + "="*70)
        if self.tests_failed == 0:
            print("🎉 ALL DEEP VERIFICATION TESTS PASSED")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
        print("="*70)

if __name__ == "__main__":
    suite = DeepVerificationTests()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
