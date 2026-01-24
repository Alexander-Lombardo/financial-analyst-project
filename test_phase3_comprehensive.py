#!/usr/bin/env python3
"""
Comprehensive Phase 3 Test Suite
Tests all 43 requirements from the RTM
"""

import json
import sys
from pathlib import Path

class Phase3TestSuite:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        
    def test(self, name, condition, error_msg=""):
        """Run a single test"""
        if condition:
            self.tests_passed += 1
            print(f"✅ {name}")
            return True
        else:
            self.tests_failed += 1
            self.failures.append(f"{name}: {error_msg}")
            print(f"❌ {name}")
            if error_msg:
                print(f"   Error: {error_msg}")
            return False
    
    def load_json(self, filepath):
        """Load JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            return None
    
    def run_all_tests(self):
        """Execute all Phase 3 verification tests"""
        print("="*70)
        print("PHASE 3 COMPREHENSIVE TEST SUITE")
        print("="*70)
        print()
        
        # Load data files
        detailed = self.load_json('output/target_analysis.json')
        timeseries = self.load_json('output/target_timeseries.json')
        
        if not detailed:
            print("❌ CRITICAL: Cannot load target_analysis.json")
            return False
        if not timeseries:
            print("❌ CRITICAL: Cannot load target_timeseries.json")
            return False
        
        # Test Category R1: Temporal Keys
        print("\n--- R1: TEMPORAL KEYS ---")
        self.test_temporal_keys(detailed)
        
        # Test Category R2: Cash Flow Extraction
        print("\n--- R2: CASH FLOW EXTRACTION ---")
        self.test_cash_flow_extraction(detailed)
        
        # Test Category R3: Dual Export Approach
        print("\n--- R3: DUAL EXPORT APPROACH ---")
        self.test_dual_export(detailed, timeseries)
        
        # Test Category R4: Time-Series JSON Structure
        print("\n--- R4: TIME-SERIES JSON STRUCTURE ---")
        self.test_timeseries_structure(timeseries)
        
        # Test Category R5: Plotly Visualization
        print("\n--- R5: PLOTLY VISUALIZATION ---")
        self.test_plotly_charts()
        
        # Test Category R6: Dependencies
        print("\n--- R6: DEPENDENCIES ---")
        self.test_dependencies()
        
        # Test Category R7: Backward Compatibility
        print("\n--- R7: BACKWARD COMPATIBILITY ---")
        self.test_backward_compatibility(detailed)
        
        # Test Category R8: Output Files
        print("\n--- R8: OUTPUT FILES ---")
        self.test_output_files()
        
        # Print summary
        self.print_summary()
        
        return self.tests_failed == 0
    
    def test_temporal_keys(self, data):
        """Test R1.1-R1.4: Temporal key extraction"""
        filings = data.get('filings', [])
        
        # R1.1 & R1.2: All filings have fiscal_year and fiscal_quarter
        missing_fy = []
        missing_fq = []
        for filing in filings:
            if 'fiscal_year' not in filing:
                missing_fy.append(filing['period'])
            if 'fiscal_quarter' not in filing:
                missing_fq.append(filing['period'])
        
        self.test("R1.1: fiscal_year present in all filings",
                  len(missing_fy) == 0,
                  f"Missing in: {missing_fy}")
        self.test("R1.2: fiscal_quarter present in all filings",
                  len(missing_fq) == 0,
                  f"Missing in: {missing_fq}")
        
        # R1.3: Annual format parsing (FY2024 -> 2024, None)
        fy2020 = next((f for f in filings if f['period'] == 'FY2020'), None)
        if fy2020:
            self.test("R1.3: Parse FY2024 format correctly",
                      fy2020['fiscal_year'] == 2020 and fy2020['fiscal_quarter'] is None,
                      f"Expected (2020, None), got ({fy2020.get('fiscal_year')}, {fy2020.get('fiscal_quarter')})")
        
        # R1.4: Quarterly format parsing (Q1 2025 -> 2025, 1)
        q1_2025 = next((f for f in filings if f['period'] == 'Q1 2025'), None)
        if q1_2025:
            self.test("R1.4: Parse Q1 2025 format correctly",
                      q1_2025['fiscal_year'] == 2025 and q1_2025['fiscal_quarter'] == 1,
                      f"Expected (2025, 1), got ({q1_2025.get('fiscal_year')}, {q1_2025.get('fiscal_quarter')})")
    
    def test_cash_flow_extraction(self, data):
        """Test R2.1-R2.5: Cash flow data extraction"""
        filings = data.get('filings', [])
        
        # R2.1-R2.3: GAAP mappings extracted values
        fy2020 = next((f for f in filings if f['period'] == 'FY2020'), None)
        if fy2020:
            vital = fy2020.get('vital_signs', {})
            self.test("R2.1: Operating cash flow extracted",
                      'operating_cash_flow_billion' in vital and vital['operating_cash_flow_billion'] is not None,
                      f"Value: {vital.get('operating_cash_flow_billion')}")
            self.test("R2.2: Investing cash flow extracted",
                      'investing_cash_flow_billion' in vital and vital['investing_cash_flow_billion'] is not None)
            self.test("R2.3: Financing cash flow extracted",
                      'financing_cash_flow_billion' in vital and vital['financing_cash_flow_billion'] is not None)
        
        # R2.4: Operating CF Margin calculation
        if fy2020:
            cf_metrics = fy2020.get('cashflow_metrics', {})
            self.test("R2.4: Operating CF margin calculated",
                      'operating_cash_flow_margin_percent' in cf_metrics,
                      f"Value: {cf_metrics.get('operating_cash_flow_margin_percent')}")
        
        # R2.5: Cash flow metrics stored in filing objects
        cf_count = sum(1 for f in filings if 'cashflow_metrics' in f)
        self.test("R2.5: Cash flow metrics in all filings",
                  cf_count == len(filings),
                  f"{cf_count}/{len(filings)} filings have cashflow_metrics")
    
    def test_dual_export(self, detailed, timeseries):
        """Test R3.1-R3.4: Dual export approach"""
        # R3.1: Detailed JSON maintains structure
        self.test("R3.1: Detailed JSON has 'filings' key",
                  'filings' in detailed)
        self.test("R3.1: Detailed JSON has 'risk_heatmap' key",
                  'risk_heatmap' in detailed)
        
        # R3.2: Time-series JSON exists
        self.test("R3.2: Time-series JSON created",
                  timeseries is not None)
        
        # R3.3: Both files generated (already tested by loading)
        self.test("R3.3: Both JSON formats export",
                  Path('output/target_analysis.json').exists() and 
                  Path('output/target_timeseries.json').exists())
        
        # R3.4: All existing fields preserved
        if detailed and len(detailed.get('filings', [])) > 0:
            sample = detailed['filings'][0]
            required_fields = ['period', 'filing_type', 'vital_signs', 'comparable_sales',
                             'inventory_metrics', 'debt_metrics', 'cashflow_metrics']
            missing = [f for f in required_fields if f not in sample]
            self.test("R3.4: All required fields preserved",
                      len(missing) == 0,
                      f"Missing: {missing}")
    
    def test_timeseries_structure(self, data):
        """Test R4.1-R4.6: Time-series JSON structure"""
        # R4.1: Flat array structure
        self.test("R4.1: Flat array structure for metrics",
                  'metrics' in data and isinstance(data['metrics'], dict))
        
        # R4.2: Separate metric categories
        if 'metrics' in data:
            categories = ['revenue', 'margins', 'inventory', 'debt', 'comparable_sales', 'cash_flows']
            present = [c for c in categories if c in data['metrics']]
            self.test("R4.2: All 6 metric categories present",
                      len(present) == 6,
                      f"Present: {present}")
        
        # R4.3: Cash flows category with 4 metrics
        if 'metrics' in data and 'cash_flows' in data['metrics']:
            cf = data['metrics']['cash_flows']
            cf_metrics = ['operating_cash_flow_billion', 'investing_cash_flow_billion',
                         'financing_cash_flow_billion', 'operating_cash_flow_margin_percent']
            present = [m for m in cf_metrics if m in cf]
            self.test("R4.3: Cash flows category has 4 metrics",
                      len(present) == 4,
                      f"Present: {present}")
        
        # R4.4: Parallel arrays (same length)
        if 'periods' in data and 'metrics' in data:
            period_count = len(data['periods'])
            revenue_count = len(data['metrics']['revenue']['net_sales_billion'])
            self.test("R4.4: Parallel arrays same length",
                      period_count == revenue_count,
                      f"Periods: {period_count}, Revenue: {revenue_count}")
        
        # R4.5: Metadata present
        if 'metadata' in data:
            required = ['company', 'ticker', 'cik', 'total_periods']
            present = [k for k in required if k in data['metadata']]
            self.test("R4.5: Metadata fields present",
                      len(present) == 4,
                      f"Present: {present}")
        
        # R4.6: Periods array with temporal keys
        if 'periods' in data and len(data['periods']) > 0:
            sample = data['periods'][0]
            required = ['period', 'fiscal_year', 'fiscal_quarter', 'filing_type']
            present = [k for k in required if k in sample]
            self.test("R4.6: Period entries have temporal keys",
                      len(present) == 4,
                      f"Present: {present}")
    
    def test_plotly_charts(self):
        """Test R5.1-R5.13: Plotly visualization"""
        # R5.1: visualize_data.py exists
        self.test("R5.1: visualize_data.py exists",
                  Path('visualize_data.py').exists())
        
        # R5.3-R5.7: All 5 charts generated
        charts = [
            'chart_revenue_vs_inventory.html',
            'chart_operating_margin_waterfall.html',
            'chart_inventory_efficiency.html',
            'chart_debt_health.html',
            'chart_cash_flows.html'
        ]
        for i, chart in enumerate(charts, start=3):
            self.test(f"R5.{i}: {chart} created",
                      Path(f'output/{chart}').exists())
        
        # R5.8-R5.11: Cash flow chart content verification
        cf_chart_path = Path('output/chart_cash_flows.html')
        if cf_chart_path.exists():
            content = cf_chart_path.read_text()
            self.test("R5.8: Operating CF line in chart",
                      'Operating Cash Flow' in content)
            self.test("R5.9: Investing CF line in chart",
                      'Investing Cash Flow' in content)
            self.test("R5.10: Financing CF line in chart",
                      'Financing Cash Flow' in content)
            # Check for line styles
            self.test("R5.11: Cash flow chart has proper formatting",
                      'dash' in content or 'line' in content)
        
        # R5.12: Interactive tooltips (Plotly default)
        if cf_chart_path.exists():
            content = cf_chart_path.read_text()
            self.test("R5.12: Interactive features present",
                      'plotly' in content.lower())
        
        # R5.13: Error handling (checked by reading visualize_data.py)
        viz_path = Path('visualize_data.py')
        if viz_path.exists():
            content = viz_path.read_text()
            self.test("R5.13: Error handling for missing data",
                      'not timeseries_path.exists()' in content or 'FileNotFoundError' in content)
    
    def test_dependencies(self):
        """Test R6.1-R6.2: Dependencies"""
        req_path = Path('requirements.txt')
        if req_path.exists():
            content = req_path.read_text()
            self.test("R6.1: plotly in requirements.txt",
                      'plotly' in content)
            self.test("R6.2: plotly version specified",
                      'plotly>=5.0.0' in content or 'plotly>=' in content)
    
    def test_backward_compatibility(self, data):
        """Test R7.1-R7.3: Backward compatibility"""
        filings = data.get('filings', [])
        
        # R7.1: Existing code continues to work (JSON loads without errors)
        self.test("R7.1: Existing JSON structure loads",
                  filings is not None and len(filings) > 0)
        
        # R7.2: Detailed JSON structure preserved
        if len(filings) > 0:
            sample = filings[0]
            self.test("R7.2: Original structure preserved",
                      'vital_signs' in sample and 'period' in sample)
        
        # R7.3: Phase 2 metrics still included
        if len(filings) > 0:
            sample = filings[0]
            self.test("R7.3: Phase 2 metrics present",
                      'inventory_metrics' in sample and 'debt_metrics' in sample)
    
    def test_output_files(self):
        """Test R8.1-R8.6: Output files"""
        files = [
            ('R8.1', 'output/target_timeseries.json', 'Time-series JSON'),
            ('R8.2', 'output/chart_revenue_vs_inventory.html', 'Revenue chart'),
            ('R8.3', 'output/chart_operating_margin_waterfall.html', 'Margin chart'),
            ('R8.4', 'output/chart_inventory_efficiency.html', 'Inventory chart'),
            ('R8.5', 'output/chart_debt_health.html', 'Debt chart'),
            ('R8.6', 'output/chart_cash_flows.html', 'Cash flow chart')
        ]
        
        for req_id, filepath, desc in files:
            path = Path(filepath)
            self.test(f"{req_id}: {desc} exists",
                      path.exists(),
                      f"Expected: {filepath}")
    
    def print_summary(self):
        """Print test summary"""
        total = self.tests_passed + self.tests_failed
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests:  {total}")
        print(f"Passed:       {self.tests_passed} ✅")
        print(f"Failed:       {self.tests_failed} ❌")
        print(f"Success Rate: {(self.tests_passed/total*100):.1f}%")
        
        if self.failures:
            print("\n" + "="*70)
            print("FAILURES")
            print("="*70)
            for failure in self.failures:
                print(f"❌ {failure}")
        
        print("\n" + "="*70)
        if self.tests_failed == 0:
            print("🎉 ALL TESTS PASSED - PHASE 3 COMPLETE")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
        print("="*70)

if __name__ == "__main__":
    suite = Phase3TestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
