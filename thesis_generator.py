"""
Investment Thesis Generator for Target Corporation
Auto-generates professional investment narrative from financial data.
"""
import json
from typing import Dict, List, Tuple
from pathlib import Path


class ThesisGenerator:
    """Generate investment thesis from Target financial data."""

    def __init__(self, timeseries_path: str = "output/target_timeseries.json",
                 detailed_path: str = "output/target_analysis.json"):
        """Initialize with data file paths."""
        with open(timeseries_path, 'r') as f:
            self.timeseries = json.load(f)

        with open(detailed_path, 'r') as f:
            self.detailed = json.load(f)

    def calculate_cagr(self, start_value: float, end_value: float,
                      periods: int) -> float:
        """Calculate Compound Annual Growth Rate."""
        if start_value <= 0 or end_value <= 0 or periods <= 0:
            return 0.0
        return ((end_value / start_value) ** (1 / periods) - 1) * 100

    def analyze_current_state(self) -> Dict:
        """Analyze current financial state."""
        margins = self.timeseries['metrics']['margins']['operating_margin_percent']
        revenues = self.timeseries['metrics']['revenue']['net_sales_billion']
        periods = self.timeseries['periods']

        # Find FY2020 index
        fy2020_idx = next((i for i, p in enumerate(periods) if p['period'] == 'FY2020'), None)

        # Get FY2020 and latest
        fy2020_margin = margins[fy2020_idx] if fy2020_idx is not None else None
        latest_margin = [m for m in margins if m is not None][-1]

        # Margin trend (only if we have FY2020 data)
        if fy2020_margin is not None:
            margin_trend = "declining" if latest_margin < fy2020_margin else "improving"
        else:
            # Fallback: use earliest available margin
            earliest_margin = next((m for m in margins if m is not None), None)
            margin_trend = "declining" if earliest_margin and latest_margin < earliest_margin else "improving"

        # Latest revenue
        latest_revenue = [r for r in revenues if r is not None][-1]
        latest_period = [p for p in periods][-1]['period']

        # Calculate margin change (use FY2020 if available, else earliest available)
        if fy2020_margin is not None:
            margin_change_3yr = round(latest_margin - fy2020_margin, 2)
        else:
            earliest_margin = next((m for m in margins if m is not None), 0)
            margin_change_3yr = round(latest_margin - earliest_margin, 2)

        return {
            'latest_operating_margin': latest_margin,
            'margin_change_3yr': margin_change_3yr,
            'margin_trend': margin_trend,
            'latest_revenue_billion': latest_revenue,
            'latest_period': latest_period,
            'fy2020_baseline_margin': fy2020_margin
        }

    def identify_risk_factors(self) -> List[Dict]:
        """Identify top risk factors from heatmap and debt metrics."""
        risks = []
        risk_heatmap = self.detailed.get('risk_heatmap', {})

        # Risk 1: Shrink trend
        shrink_data = risk_heatmap.get('shrink', {})
        if shrink_data.get('trend') == 'increasing':
            risks.append({
                'factor': 'Shrink/Theft',
                'severity': 'High',
                'trend': 'Increasing',
                'evidence': f"{shrink_data['total_mentions']} mentions across "
                           f"{shrink_data['periods_affected']} periods, "
                           f"avg {shrink_data['avg_mentions_per_period']}/period"
            })

        # Risk 2: Debt coverage
        # Get latest annual filing with debt data
        latest_annual = None
        for filing in reversed(self.detailed['filings']):
            if filing['filing_type'] == '10-K' and filing.get('debt_metrics', {}).get('interest_coverage_ratio'):
                latest_annual = filing
                break

        if latest_annual:
            coverage = latest_annual['debt_metrics']['interest_coverage_ratio']
            if coverage < 2.5:
                risks.append({
                    'factor': 'Interest Coverage',
                    'severity': 'Critical' if coverage < 2.0 else 'High',
                    'trend': 'Deteriorating',
                    'evidence': f"Coverage at {coverage:.2f}x "
                               f"({'below' if coverage < 2.0 else 'near'} 2.0x warning threshold)"
                })

        # Also check for rapid decline in coverage
        interest_coverage = [f.get('debt_metrics', {}).get('interest_coverage_ratio')
                            for f in self.detailed['filings']]
        if len(interest_coverage) >= 2:
            prev_coverage = interest_coverage[-2] if interest_coverage[-2] else None
            curr_coverage = interest_coverage[-1]
            if prev_coverage and curr_coverage and (prev_coverage - curr_coverage) / prev_coverage > 0.2:
                risks.append({
                    'factor': 'Interest Coverage Decline',
                    'severity': 'Medium',
                    'trend': 'Deteriorating',
                    'evidence': f"Coverage dropped {((prev_coverage - curr_coverage) / prev_coverage * 100):.0f}% QoQ ({prev_coverage:.1f}x → {curr_coverage:.1f}x)"
                })

        # Risk 3: Inventory buildup
        inv_yoy = self.timeseries['metrics']['inventory']['inventory_yoy_growth_percent']
        rev_yoy = self.timeseries['metrics']['revenue']['yoy_growth_percent']

        # Find latest quarter with both metrics
        for i in range(len(inv_yoy) - 1, -1, -1):
            if inv_yoy[i] is not None and rev_yoy[i] is not None:
                if inv_yoy[i] > rev_yoy[i] + 5:
                    risks.append({
                        'factor': 'Inventory Buildup',
                        'severity': 'Medium',
                        'trend': 'Concerning',
                        'evidence': f"Inventory growing {inv_yoy[i]:.1f}% vs "
                                   f"sales {rev_yoy[i]:.1f}%"
                    })
                break

        # Risk: Margin compression
        margins = self.timeseries['metrics']['margins']['operating_margin_percent']
        periods = self.timeseries['periods']
        fy2020_idx = next((i for i, p in enumerate(periods) if p['period'] == 'FY2020'), None)
        fy2020_margin = margins[fy2020_idx] if fy2020_idx is not None else None
        current_margin = [m for m in margins if m is not None][-1]
        if fy2020_margin and current_margin < fy2020_margin - 2:
            risks.append({
                'factor': 'Margin Compression',
                'severity': 'High',
                'trend': 'Declining',
                'evidence': f"Operating margin {current_margin:.1f}% vs {fy2020_margin:.1f}% baseline (-{fy2020_margin - current_margin:.1f}pp)"
            })

        return risks[:4]  # Top 4 risks

    def identify_opportunities(self) -> List[Dict]:
        """Identify growth opportunities from data."""
        opportunities = []

        # Opportunity 1: Digital sales growth
        digital_sales = self.timeseries['metrics']['comparable_sales']['digital_change_percent']
        latest_digital = [d for d in digital_sales if d is not None][-1]

        if latest_digital > 2.0:
            # Check if digital growth is decelerating
            if len(digital_sales) >= 2:
                prev_digital = digital_sales[-2] if digital_sales[-2] else None
                if prev_digital and latest_digital < prev_digital:
                    evidence = f"Digital comp sales {latest_digital}% (slowing from {prev_digital}%)"
                    potential = 'Medium'  # Downgrade from High
                else:
                    evidence = f"Digital comp sales up {latest_digital}% in latest quarter"
                    potential = 'High'
            else:
                evidence = f"Digital comp sales up {latest_digital}% in latest quarter"
                potential = 'High'

            opportunities.append({
                'factor': 'Digital Sales Growth',
                'potential': potential,
                'evidence': evidence
            })

        # Opportunity 2: Margin recovery potential
        current_state = self.analyze_current_state()
        if current_state['latest_operating_margin'] > current_state['fy2020_baseline_margin']:
            opportunities.append({
                'factor': 'Margin Recovery',
                'potential': 'Medium',
                'evidence': f"Operating margin improved from "
                           f"{current_state['fy2020_baseline_margin']:.2f}% (FY2020) to "
                           f"{current_state['latest_operating_margin']:.2f}% (current)"
            })

        # Opportunity 3: Inventory efficiency improvement
        inv_turnover = self.timeseries['metrics']['inventory']['inventory_turnover_ratio']
        periods = self.timeseries['periods']
        fy2020_idx = next((i for i, p in enumerate(periods) if p['period'] == 'FY2020'), None)

        recent_turnover = [t for t in inv_turnover if t is not None][-1]
        baseline_turnover = inv_turnover[fy2020_idx] if fy2020_idx is not None else next((t for t in inv_turnover if t is not None), None)

        if baseline_turnover and recent_turnover > baseline_turnover:
            opportunities.append({
                'factor': 'Inventory Efficiency',
                'potential': 'Medium',
                'evidence': f"Turnover improved to {recent_turnover:.2f}x from "
                           f"{baseline_turnover:.2f}x baseline"
            })

        return opportunities[:3]

    def generate_recommendation(self, current_state: Dict, risks: List[Dict],
                               opportunities: List[Dict]) -> Dict:
        """Generate investment recommendation with nuanced logic."""

        # Get key metrics for distress detection
        interest_coverage = None
        for filing in reversed(self.detailed['filings']):
            if filing.get('debt_metrics', {}).get('interest_coverage_ratio'):
                interest_coverage = filing['debt_metrics']['interest_coverage_ratio']
                break

        operating_margin = current_state['latest_operating_margin']
        has_critical_risk = any(r['severity'] == 'Critical' for r in risks)

        # SELL: Only on actual distress signals
        distress_signals = []
        if interest_coverage and interest_coverage < 3.0:
            distress_signals.append(f"Interest coverage at {interest_coverage:.1f}x (below 3x threshold)")
        if operating_margin < 0:
            distress_signals.append(f"Negative operating margin ({operating_margin:.1f}%)")
        if has_critical_risk:
            distress_signals.append("Critical risk factors present")

        if len(distress_signals) >= 2 or (interest_coverage and interest_coverage < 2.0):
            return {
                'rating': 'Sell',
                'rationale': f"Distress signals: {'; '.join(distress_signals)}",
                'confidence': 'High' if len(distress_signals) >= 2 else 'Medium',
                'catalysts': [o['factor'] for o in opportunities],
                'headwinds': [r['factor'] for r in risks]
            }

        # BUY: Improving margins + more opportunities than risks + no high-severity risks
        high_risks = sum(1 for r in risks if r['severity'] in ('Critical', 'High'))
        high_opps = sum(1 for o in opportunities if o['potential'] == 'High')

        if (current_state['margin_trend'] == 'improving' and
            high_opps > high_risks and
            high_risks == 0):
            return {
                'rating': 'Buy',
                'rationale': "Improving margins with opportunities outweighing risks",
                'confidence': 'Medium',
                'catalysts': [o['factor'] for o in opportunities],
                'headwinds': [r['factor'] for r in risks]
            }

        # HOLD: Everything else (the most common case)
        # Generate nuanced rationale based on specific conditions
        if current_state['margin_trend'] == 'declining' and high_risks > 0:
            rationale = "Margin pressure and elevated risks warrant caution; watch for stabilization"
        elif len(opportunities) == 0:
            rationale = "Limited near-term catalysts; maintaining position pending clarity"
        else:
            rationale = "Balanced risk/reward with execution uncertainty"

        return {
            'rating': 'Hold',
            'rationale': rationale,
            'confidence': 'Medium',
            'catalysts': [o['factor'] for o in opportunities],
            'headwinds': [r['factor'] for r in risks]
        }

    def generate_thesis(self) -> Dict:
        """Generate complete investment thesis."""
        current_state = self.analyze_current_state()
        risks = self.identify_risk_factors()
        opportunities = self.identify_opportunities()
        recommendation = self.generate_recommendation(current_state, risks, opportunities)

        thesis = {
            'company': 'Target Corporation',
            'ticker': 'TGT',
            'analysis_date': self.timeseries['periods'][-1]['period'],
            'current_state': current_state,
            'risk_factors': risks,
            'opportunities': opportunities,
            'recommendation': recommendation
        }

        return thesis

    def export_thesis(self, output_path: str = "output/investment_thesis.json"):
        """Export thesis to JSON file."""
        thesis = self.generate_thesis()

        with open(output_path, 'w') as f:
            json.dump(thesis, f, indent=2)

        print(f"✅ Investment thesis exported to: {output_path}")
        return thesis

    def print_thesis(self):
        """Print human-readable thesis."""
        thesis = self.generate_thesis()

        print("\n" + "=" * 80)
        print("INVESTMENT THESIS: TARGET CORPORATION (TGT)")
        print("=" * 80)

        print(f"\nAnalysis Period: {thesis['analysis_date']}")

        print("\n📊 CURRENT STATE")
        print("-" * 80)
        cs = thesis['current_state']
        print(f"   Operating Margin: {cs['latest_operating_margin']:.2f}% "
              f"({cs['margin_trend']})")
        print(f"   3-Year Change: {cs['margin_change_3yr']:+.2f} percentage points")
        print(f"   Latest Revenue: ${cs['latest_revenue_billion']:.2f}B")

        print("\n⚠️  RISK FACTORS")
        print("-" * 80)
        for i, risk in enumerate(thesis['risk_factors'], 1):
            print(f"   {i}. {risk['factor']} ({risk['severity']} - {risk['trend']})")
            print(f"      {risk['evidence']}")

        print("\n✨ OPPORTUNITIES")
        print("-" * 80)
        for i, opp in enumerate(thesis['opportunities'], 1):
            print(f"   {i}. {opp['factor']} ({opp['potential']} potential)")
            print(f"      {opp['evidence']}")

        print("\n💡 RECOMMENDATION")
        print("-" * 80)
        rec = thesis['recommendation']
        print(f"   Rating: {rec['rating']}")
        print(f"   Rationale: {rec['rationale']}")
        print(f"   Confidence: {rec['confidence']}")
        print(f"   Catalysts: {', '.join(rec['catalysts'])}")
        print(f"   Headwinds: {', '.join(rec['headwinds'])}")

        print("\n" + "=" * 80)


def main():
    """Generate and display investment thesis."""
    generator = ThesisGenerator()
    generator.print_thesis()
    generator.export_thesis()


if __name__ == "__main__":
    main()
