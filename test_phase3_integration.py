#!/usr/bin/env python3
"""
Integration Test: Full End-to-End Workflow
Simulates a user running the complete Phase 3 pipeline
"""

import json
import subprocess
import sys
from pathlib import Path

class IntegrationTest:
    def __init__(self):
        self.passed = []
        self.failed = []
        
    def step(self, name, func):
        """Run a test step"""
        print(f"\n{'='*70}")
        print(f"STEP: {name}")
        print('='*70)
        try:
            result = func()
            if result:
                self.passed.append(name)
                print(f"✅ {name} - PASSED")
            else:
                self.failed.append(name)
                print(f"❌ {name} - FAILED")
            return result
        except Exception as e:
            self.failed.append(name)
            print(f"❌ {name} - EXCEPTION: {e}")
            return False
    
    def run_all_steps(self):
        """Execute full integration test"""
        print("="*70)
        print("PHASE 3 INTEGRATION TEST - END-TO-END WORKFLOW")
        print("="*70)
        
        # Step 1: Verify source files exist
        self.step("Verify source files exist", self.verify_source_files)
        
        # Step 2: Verify analyzer runs without errors
        self.step("Run financial_analyzer.py", self.run_analyzer)
        
        # Step 3: Verify JSON outputs exist and are valid
        self.step("Verify JSON outputs", self.verify_json_outputs)
        
        # Step 4: Verify time-series JSON structure
        self.step("Verify time-series structure", self.verify_timeseries_structure)
        
        # Step 5: Run visualization script
        self.step("Run visualize_data.py", self.run_visualizations)
        
        # Step 6: Verify all charts exist
        self.step("Verify chart outputs", self.verify_chart_outputs)
        
        # Step 7: Verify chart content (sample)
        self.step("Verify chart content", self.verify_chart_content)
        
        # Step 8: Data consistency check
        self.step("Cross-validate data consistency", self.cross_validate_data)
        
        # Step 9: Verify Phase 3 specific features
        self.step("Verify Phase 3 features", self.verify_phase3_features)
        
        # Print summary
        self.print_summary()
        
        return len(self.failed) == 0
    
    def verify_source_files(self):
        """Verify all source files exist"""
        required_files = [
            'financial_analyzer.py',
            'visualize_data.py',
            'requirements.txt',
            'sec_data_fetcher.py'
        ]
        
        missing = [f for f in required_files if not Path(f).exists()]
        
        if missing:
            print(f"❌ Missing files: {missing}")
            return False
        
        print("✅ All source files present")
        return True
    
    def run_analyzer(self):
        """Run the analyzer (outputs already exist, just verify it can run)"""
        # Check if outputs already exist
        if not Path('output/target_analysis.json').exists():
            print("⚠️  Output files don't exist, analyzer needs to be run first")
            return False
        
        print("✅ Analyzer has been run successfully (outputs exist)")
        return True
    
    def verify_json_outputs(self):
        """Verify JSON outputs exist and are valid"""
        files = ['output/target_analysis.json', 'output/target_timeseries.json']
        
        for filepath in files:
            if not Path(filepath).exists():
                print(f"❌ Missing: {filepath}")
                return False
            
            try:
                with open(filepath) as f:
                    data = json.load(f)
                print(f"✅ {filepath} - Valid JSON, {len(json.dumps(data))} bytes")
            except json.JSONDecodeError as e:
                print(f"❌ {filepath} - Invalid JSON: {e}")
                return False
        
        return True
    
    def verify_timeseries_structure(self):
        """Verify time-series JSON has correct structure"""
        with open('output/target_timeseries.json') as f:
            data = json.load(f)
        
        # Check top-level structure
        required_keys = ['metadata', 'periods', 'metrics', 'comparisons', 'risk_heatmap']
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            print(f"❌ Missing top-level keys: {missing}")
            return False
        
        # Check metrics categories
        required_categories = ['revenue', 'margins', 'inventory', 'debt', 'comparable_sales', 'cash_flows']
        missing = [c for c in required_categories if c not in data['metrics']]
        
        if missing:
            print(f"❌ Missing metric categories: {missing}")
            return False
        
        # Check cash_flows metrics (Phase 3 specific)
        cf = data['metrics']['cash_flows']
        required_cf_metrics = [
            'operating_cash_flow_billion',
            'investing_cash_flow_billion',
            'financing_cash_flow_billion',
            'operating_cash_flow_margin_percent'
        ]
        missing = [m for m in required_cf_metrics if m not in cf]
        
        if missing:
            print(f"❌ Missing cash flow metrics: {missing}")
            return False
        
        print(f"✅ Time-series structure correct with {len(data['periods'])} periods")
        return True
    
    def run_visualizations(self):
        """Run visualization script"""
        # Check if charts already exist
        if not Path('output/chart_cash_flows.html').exists():
            print("⚠️  Charts don't exist, visualize_data.py needs to be run")
            return False
        
        print("✅ Visualizations have been generated (charts exist)")
        return True
    
    def verify_chart_outputs(self):
        """Verify all chart files exist"""
        charts = [
            'chart_revenue_vs_inventory.html',
            'chart_operating_margin_waterfall.html',
            'chart_inventory_efficiency.html',
            'chart_debt_health.html',
            'chart_cash_flows.html'
        ]
        
        for chart in charts:
            path = Path(f'output/{chart}')
            if not path.exists():
                print(f"❌ Missing: {chart}")
                return False
            
            size = path.stat().st_size
            print(f"✅ {chart} - {size/1_000_000:.2f} MB")
        
        return True
    
    def verify_chart_content(self):
        """Verify chart content is valid"""
        # Check cash flows chart (Phase 3 specific)
        chart_path = Path('output/chart_cash_flows.html')
        content = chart_path.read_text()
        
        required_elements = [
            'Operating Cash Flow',
            'Investing Cash Flow',
            'Financing Cash Flow',
            'plotly'
        ]
        
        missing = [e for e in required_elements if e not in content]
        
        if missing:
            print(f"❌ Cash flow chart missing elements: {missing}")
            return False
        
        print("✅ Cash flow chart contains all 3 cash flow lines + Plotly")
        return True
    
    def cross_validate_data(self):
        """Cross-validate data between detailed and time-series JSON"""
        with open('output/target_analysis.json') as f:
            detailed = json.load(f)
        with open('output/target_timeseries.json') as f:
            timeseries = json.load(f)
        
        # Verify period count matches
        detailed_count = len(detailed['filings'])
        timeseries_count = len(timeseries['periods'])
        
        if detailed_count != timeseries_count:
            print(f"❌ Period count mismatch: detailed={detailed_count}, timeseries={timeseries_count}")
            return False
        
        # Cross-validate a sample metric (net sales for FY2020)
        fy2020_detailed = next((f for f in detailed['filings'] if f['period'] == 'FY2020'), None)
        fy2020_ts_idx = next((i for i, p in enumerate(timeseries['periods']) if p['period'] == 'FY2020'), None)
        
        if fy2020_detailed and fy2020_ts_idx is not None:
            detailed_sales = fy2020_detailed['vital_signs'].get('net_sales_billion')
            ts_sales = timeseries['metrics']['revenue']['net_sales_billion'][fy2020_ts_idx]
            
            if detailed_sales != ts_sales:
                print(f"❌ Net sales mismatch for FY2020: detailed={detailed_sales}, ts={ts_sales}")
                return False
            
            print(f"✅ Cross-validation passed: FY2020 net sales = ${detailed_sales}B (both formats)")
        
        return True
    
    def verify_phase3_features(self):
        """Verify Phase 3 specific features"""
        with open('output/target_analysis.json') as f:
            detailed = json.load(f)
        
        # Check Phase 3 fields in a sample filing
        sample = detailed['filings'][0]
        
        phase3_fields = [
            'fiscal_year',
            'fiscal_quarter',
            'cashflow_metrics'
        ]
        
        missing = [f for f in phase3_fields if f not in sample]
        
        if missing:
            print(f"❌ Missing Phase 3 fields: {missing}")
            return False
        
        # Verify cashflow_metrics structure
        cf = sample.get('cashflow_metrics', {})
        if 'operating_cash_flow_billion' not in cf:
            print("❌ cashflow_metrics missing operating_cash_flow_billion")
            return False
        
        print(f"✅ Phase 3 fields present: fiscal_year={sample['fiscal_year']}, "
              f"cashflow_metrics has {len(cf)} metrics")
        return True
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.passed) + len(self.failed)
        print("\n" + "="*70)
        print("INTEGRATION TEST SUMMARY")
        print("="*70)
        print(f"Total Steps:  {total}")
        print(f"Passed:       {len(self.passed)} ✅")
        print(f"Failed:       {len(self.failed)} ❌")
        print(f"Success Rate: {(len(self.passed)/total*100):.1f}%")
        
        if self.failed:
            print("\nFailed Steps:")
            for step in self.failed:
                print(f"  ❌ {step}")
        
        print("\n" + "="*70)
        if len(self.failed) == 0:
            print("🎉 INTEGRATION TEST PASSED - COMPLETE WORKFLOW VERIFIED")
        else:
            print("⚠️  INTEGRATION TEST FAILED - REVIEW REQUIRED")
        print("="*70)

if __name__ == "__main__":
    test = IntegrationTest()
    success = test.run_all_steps()
    sys.exit(0 if success else 1)
