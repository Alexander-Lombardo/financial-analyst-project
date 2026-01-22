"""
Create PowerPoint presentation from Target financial analysis
"""

import json
import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from thesis_generator import ThesisGenerator


def create_target_presentation():
    """Create comprehensive PowerPoint presentation."""

    # Generate investment thesis (Phase 4)
    print("   Generating investment thesis...")
    thesis_gen = ThesisGenerator()
    thesis_gen.export_thesis()

    # Load analysis data
    with open('output/target_analysis.json', 'r') as f:
        full_data = json.load(f)
        data = full_data['filings']  # Extract filings array

    # Load timeseries data for Phase 4 charts
    with open('output/target_timeseries.json', 'r') as f:
        timeseries_data = json.load(f)

    # Load investment thesis
    with open('output/investment_thesis.json', 'r') as f:
        thesis = json.load(f)

    # Create presentation
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title
    add_title_slide(prs)

    # Slide 2: Executive Summary
    add_executive_summary(prs, data)

    # Slide 3: Investment Thesis (Phase 4)
    add_investment_thesis_slide(prs, thesis)

    # Slide 4: Baseline (FY2024)
    add_baseline_slide(prs, data[10])

    # Slide 5: Revenue vs Inventory Growth (Phase 3 Chart)
    add_revenue_vs_inventory_slide(prs, timeseries_data)

    # Slide 6: Operating Margin Waterfall (Phase 3 Chart)
    add_operating_margin_waterfall_slide(prs, timeseries_data)

    # Slide 7: Inventory Efficiency (Phase 3 Chart)
    add_inventory_efficiency_slide(prs, timeseries_data)

    # Slide 8: Debt Health (Phase 3 Chart)
    add_debt_health_slide(prs, timeseries_data)

    # Slide 9: Cash Flows (Phase 3 Chart)
    add_cash_flows_slide(prs, timeseries_data)

    # Slide 10: Q1 2025 Analysis
    add_quarter_slide(prs, data[14], data[10])

    # Slide 11: Q2 2025 Analysis
    add_quarter_slide(prs, data[15], data[10])

    # Slide 12: Q3 2025 Analysis - RED FLAGS
    add_q3_warning_slide(prs, data[16], data[10])

    # Slide 13: Margin Bridge Analysis (Phase 4)
    add_margin_bridge_slide(prs, timeseries_data, full_data)

    # Slide 14: Risk Heatmap (Phase 4)
    add_risk_heatmap_slide(prs, full_data)

    # Slide 15: Debt & Leverage Analysis
    add_debt_analysis_slide(prs)

    # Slide 16: Key Risks & Recommendations
    add_recommendations_slide(prs, data)

    # Save presentation
    output_path = 'output/Target_Financial_Analysis.pptx'
    prs.save(output_path)
    print(f"✅ Presentation created: {output_path}")
    print("   16 slides total including:")
    print("     • Investment Thesis slide (Phase 4)")
    print("     • Revenue vs Inventory Growth (Phase 3)")
    print("     • Operating Margin Waterfall (Phase 3)")
    print("     • Inventory Efficiency (Phase 3)")
    print("     • Debt Health (Phase 3)")
    print("     • Cash Flows (Phase 3)")
    print("     • Margin Bridge Analysis (Phase 4)")
    print("     • Risk Heatmap (Phase 4)")
    print("     • Links to all 8 interactive Plotly charts ✅")
    return output_path


def add_title_slide(prs):
    """Add title slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Title
    left = Inches(1)
    top = Inches(2.5)
    width = Inches(8)
    height = Inches(1)

    title_box = slide.shapes.add_textbox(left, top, width, height)
    tf = title_box.text_frame
    tf.text = "Target Corporation"

    p = tf.paragraphs[0]
    p.font.size = Pt(54)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)  # Target red
    p.alignment = PP_ALIGN.CENTER

    # Subtitle
    subtitle_box = slide.shapes.add_textbox(left, Inches(3.5), width, Inches(0.5))
    tf = subtitle_box.text_frame
    tf.text = "Financial Analysis Report"
    p = tf.paragraphs[0]
    p.font.size = Pt(32)
    p.alignment = PP_ALIGN.CENTER

    # Period
    period_box = slide.shapes.add_textbox(left, Inches(4.2), width, Inches(0.4))
    tf = period_box.text_frame
    tf.text = "FY2024 - Q3 2025"
    p = tf.paragraphs[0]
    p.font.size = Pt(24)
    p.font.color.rgb = RGBColor(128, 128, 128)
    p.alignment = PP_ALIGN.CENTER


def add_executive_summary(prs, data):
    """Add executive summary slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title only
    title = slide.shapes.title
    title.text = "Executive Summary"

    # Key findings box
    left = Inches(0.5)
    top = Inches(1.5)
    width = Inches(9)
    height = Inches(5.5)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame
    tf.word_wrap = True

    # Baseline metrics
    baseline = data[0]['vital_signs']
    q3 = data[3]['vital_signs']

    findings = [
        ("FY2024 Baseline Performance", [
            f"• Net Sales: ${baseline['net_sales_billion']:.2f}B",
            f"• Operating Margin: {baseline['operating_margin_percent']:.2f}%",
            f"• Gross Margin: {baseline['gross_margin_percent']:.2f}%",
        ]),
        ("Q3 2025 - Critical Weakness Detected", [
            f"• Operating Margin: {q3['operating_margin_percent']:.2f}% ({q3['vs_baseline']['operating_margin_change']:+.2f}% vs baseline) ⚠️",
            f"• Inventory: ${q3['inventory_billion']:.2f}B (+{((q3['inventory_billion']/baseline['inventory_billion']-1)*100):.1f}%) 🚨",
            f"• Debt increased 7.5% while operating income declined",
        ]),
        ("Key Risk Flags", [
            "• Interest coverage deteriorated from 9.7x to 1.5x",
            "• Shrink/theft mentioned in all quarters",
            "• Inventory buildup suggests potential clearance ahead",
        ]),
    ]

    for section_title, bullets in findings:
        p = tf.add_paragraph()
        p.text = section_title
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)
        p.space_after = Pt(6)

        for bullet in bullets:
            p = tf.add_paragraph()
            p.text = bullet
            p.level = 0
            p.font.size = Pt(14)
            p.space_after = Pt(3)

        p = tf.add_paragraph()
        p.space_after = Pt(12)


def add_revenue_vs_inventory_slide(prs, timeseries_data):
    """Add Revenue vs Inventory Growth slide (Phase 3 Chart 1)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.5)
    )
    title_frame = title_box.text_frame
    title = title_frame.paragraphs[0]
    title.text = "Revenue vs Inventory Growth Trend"
    title.font.size = Pt(28)
    title.font.bold = True

    # Instruction text with hyperlink
    instruction_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.0), Inches(9), Inches(1.0)
    )
    instruction_frame = instruction_box.text_frame
    p = instruction_frame.paragraphs[0]
    p.text = "Dual-axis chart comparing revenue and inventory growth over time:"
    p.font.size = Pt(14)
    p.space_after = Pt(6)

    # Add clickable hyperlink
    p = instruction_frame.add_paragraph()
    p.text = "📊 Click to view: "
    p.font.size = Pt(14)

    # Get absolute path to the chart file
    chart_path = Path("output/chart_revenue_vs_inventory.html").resolve()

    run = p.add_run()
    run.text = "Revenue vs Inventory Interactive Chart"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 255)
    run.font.underline = True
    run.hyperlink.address = str(chart_path)

    p.space_after = Pt(12)

    # Summary bullets with key insights
    summary_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(4)
    )
    summary_frame = summary_box.text_frame

    # Get latest data points
    revenue = timeseries_data['metrics']['revenue']['net_sales_billion']
    inventory = timeseries_data['metrics']['inventory']['inventory_billion']
    periods = timeseries_data['periods']

    # Find Q3 2024 and Q3 2025 for apples-to-apples quarterly comparison
    q3_2024_idx = next((i for i, p in enumerate(periods) if p['period'] == 'Q3 2024'), None)
    q3_2025_idx = next((i for i, p in enumerate(periods) if p['period'] == 'Q3 2025'), None)

    if q3_2024_idx is not None and q3_2025_idx is not None:
        q3_2024_rev = revenue[q3_2024_idx]
        q3_2025_rev = revenue[q3_2025_idx]
        q3_2024_inv = inventory[q3_2024_idx]
        q3_2025_inv = inventory[q3_2025_idx]

        p = summary_frame.paragraphs[0]
        p.text = "Key Insights (Q3 2024 vs Q3 2025):"
        p.font.size = Pt(16)
        p.font.bold = True
        p.space_after = Pt(8)

        # Revenue comparison
        p = summary_frame.add_paragraph()
        p.text = "Revenue (Quarterly):"
        p.font.size = Pt(14)
        p.font.bold = True
        p.space_after = Pt(4)

        p = summary_frame.add_paragraph()
        p.text = f"• Q3 2024: ${q3_2024_rev:.2f}B"
        p.font.size = Pt(14)
        p.level = 1

        p = summary_frame.add_paragraph()
        p.text = f"• Q3 2025: ${q3_2025_rev:.2f}B"
        p.font.size = Pt(14)
        p.level = 1
        p.space_after = Pt(8)

        # Inventory comparison
        p = summary_frame.add_paragraph()
        p.text = "Inventory:"
        p.font.size = Pt(14)
        p.font.bold = True
        p.space_after = Pt(4)

        p = summary_frame.add_paragraph()
        p.text = f"• Q3 2024: ${q3_2024_inv:.2f}B"
        p.font.size = Pt(14)
        p.level = 1

        p = summary_frame.add_paragraph()
        p.text = f"• Q3 2025: ${q3_2025_inv:.2f}B"
        p.font.size = Pt(14)
        p.level = 1
        p.space_after = Pt(12)

        # Calculate year-over-year growth rates
        rev_growth = ((q3_2025_rev / q3_2024_rev) - 1) * 100
        inv_growth = ((q3_2025_inv / q3_2024_inv) - 1) * 100

        p = summary_frame.add_paragraph()
        p.text = "Year-over-Year Growth:"
        p.font.size = Pt(14)
        p.font.bold = True
        p.space_after = Pt(6)

        p = summary_frame.add_paragraph()
        emoji = "✅" if rev_growth > 0 else "⚠️"
        p.text = f"{emoji} Revenue: {rev_growth:+.1f}% YoY"
        p.font.size = Pt(14)
        p.level = 1

        p = summary_frame.add_paragraph()
        emoji = "⚠️" if inv_growth > rev_growth + 5 else "✅"
        p.text = f"{emoji} Inventory: {inv_growth:+.1f}% YoY"
        p.font.size = Pt(14)
        p.level = 1

        if inv_growth > rev_growth + 5:
            p = summary_frame.add_paragraph()
            p.text = f"🚨 Warning: Inventory growing {inv_growth - rev_growth:.1f}pp faster than revenue"
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(255, 0, 0)
            p.font.bold = True
            p.level = 1


def add_operating_margin_waterfall_slide(prs, timeseries_data):
    """Add Operating Margin Waterfall slide (Phase 3 Chart 2)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.5)
    )
    title_frame = title_box.text_frame
    title = title_frame.paragraphs[0]
    title.text = "Operating Margin Waterfall - Quarterly Trend"
    title.font.size = Pt(28)
    title.font.bold = True

    # Instruction text with hyperlink
    instruction_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.0), Inches(9), Inches(1.0)
    )
    instruction_frame = instruction_box.text_frame
    p = instruction_frame.paragraphs[0]
    p.text = "Waterfall chart showing quarterly operating margin changes:"
    p.font.size = Pt(14)
    p.space_after = Pt(6)

    # Add clickable hyperlink
    p = instruction_frame.add_paragraph()
    p.text = "📊 Click to view: "
    p.font.size = Pt(14)

    # Get absolute path to the chart file
    chart_path = Path("output/chart_operating_margin_waterfall.html").resolve()

    run = p.add_run()
    run.text = "Operating Margin Waterfall Chart"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 255)
    run.font.underline = True
    run.hyperlink.address = str(chart_path)

    p.space_after = Pt(12)

    # Summary bullets with key insights
    summary_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(4)
    )
    summary_frame = summary_box.text_frame

    # Get margin data
    margins = timeseries_data['metrics']['margins']['operating_margin_percent']
    periods = timeseries_data['periods']

    # Find FY2024 baseline and Q3 2025
    fy2024_idx = next((i for i, p in enumerate(periods) if p['period'] == 'FY2024'), None)
    q3_2025_idx = next((i for i, p in enumerate(periods) if p['period'] == 'Q3 2025'), None)

    if fy2024_idx is not None and q3_2025_idx is not None:
        fy2024_margin = margins[fy2024_idx]
        q3_2025_margin = margins[q3_2025_idx]
        total_change = q3_2025_margin - fy2024_margin

        p = summary_frame.paragraphs[0]
        p.text = "Key Insights:"
        p.font.size = Pt(16)
        p.font.bold = True
        p.space_after = Pt(8)

        # Baseline
        p = summary_frame.add_paragraph()
        p.text = f"• FY2024 Baseline: {fy2024_margin:.2f}%"
        p.font.size = Pt(14)
        p.space_after = Pt(4)

        # Current
        p = summary_frame.add_paragraph()
        p.text = f"• Q3 2025 Current: {q3_2025_margin:.2f}%"
        p.font.size = Pt(14)
        p.space_after = Pt(4)

        # Net change
        p = summary_frame.add_paragraph()
        emoji = "✅" if total_change > 0 else "⚠️"
        p.text = f"{emoji} Net Change: {total_change:+.2f} percentage points"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(0, 128, 0) if total_change > 0 else RGBColor(255, 0, 0)
        p.font.bold = True
        p.space_after = Pt(12)

        # Calculate best and worst quarters
        quarterly_margins = []
        for i, period in enumerate(periods):
            if period['filing_type'] == '10-Q' and margins[i] is not None:
                quarterly_margins.append((period['period'], margins[i]))

        if len(quarterly_margins) >= 2:
            quarterly_margins.sort(key=lambda x: x[1])
            worst_q = quarterly_margins[0]
            best_q = quarterly_margins[-1]

            p = summary_frame.add_paragraph()
            p.text = "Quarterly Performance Range:"
            p.font.size = Pt(14)
            p.font.bold = True
            p.space_after = Pt(6)

            p = summary_frame.add_paragraph()
            p.text = f"• Worst Quarter: {worst_q[0]} at {worst_q[1]:.2f}%"
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(255, 0, 0)
            p.level = 1

            p = summary_frame.add_paragraph()
            p.text = f"• Best Quarter: {best_q[0]} at {best_q[1]:.2f}%"
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(0, 128, 0)
            p.level = 1
            p.space_after = Pt(12)

        # Key observation
        p = summary_frame.add_paragraph()
        p.text = "📈 The waterfall chart shows quarter-over-quarter margin changes, helping identify inflection points and trends over time."
        p.font.size = Pt(13)
        p.font.color.rgb = RGBColor(70, 70, 70)


def add_inventory_efficiency_slide(prs, timeseries_data):
    """Add Inventory Efficiency slide (Phase 3 Chart 3)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.5)
    )
    title_frame = title_box.text_frame
    title = title_frame.paragraphs[0]
    title.text = "Inventory Efficiency Metrics"
    title.font.size = Pt(28)
    title.font.bold = True

    # Instruction text with hyperlink
    instruction_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.0), Inches(9), Inches(1.0)
    )
    instruction_frame = instruction_box.text_frame
    p = instruction_frame.paragraphs[0]
    p.text = "Dual-axis chart tracking Inventory Turnover Ratio and Days Sales of Inventory:"
    p.font.size = Pt(14)
    p.space_after = Pt(6)

    # Add clickable hyperlink
    p = instruction_frame.add_paragraph()
    p.text = "📊 Click to view: "
    p.font.size = Pt(14)

    # Get absolute path to the chart file
    chart_path = Path("output/chart_inventory_efficiency.html").resolve()

    run = p.add_run()
    run.text = "Inventory Efficiency Interactive Chart"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 255)
    run.font.underline = True
    run.hyperlink.address = str(chart_path)

    p.space_after = Pt(12)

    # Summary bullets with key insights
    summary_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(4)
    )
    summary_frame = summary_box.text_frame

    # Get inventory metrics
    turnover = timeseries_data['metrics']['inventory']['inventory_turnover_ratio']
    dsi = timeseries_data['metrics']['inventory']['days_sales_of_inventory']
    periods = timeseries_data['periods']

    # Find latest quarterly data
    latest_q_idx = None
    for i in range(len(periods) - 1, -1, -1):
        if periods[i]['filing_type'] == '10-Q' and turnover[i] is not None:
            latest_q_idx = i
            break

    # Find FY2024 baseline
    fy2024_idx = next((i for i, p in enumerate(periods) if p['period'] == 'FY2024'), None)

    if latest_q_idx is not None and fy2024_idx is not None:
        latest_turnover = turnover[latest_q_idx]
        latest_dsi = dsi[latest_q_idx]
        latest_period = periods[latest_q_idx]['period']

        baseline_turnover = turnover[fy2024_idx]
        baseline_dsi = dsi[fy2024_idx]

        p = summary_frame.paragraphs[0]
        p.text = "Key Insights:"
        p.font.size = Pt(16)
        p.font.bold = True
        p.space_after = Pt(8)

        # Inventory Turnover section
        p = summary_frame.add_paragraph()
        p.text = "Inventory Turnover Ratio (higher is better):"
        p.font.size = Pt(14)
        p.font.bold = True
        p.space_after = Pt(4)

        p = summary_frame.add_paragraph()
        p.text = f"• FY2024 Baseline: {baseline_turnover:.2f}x"
        p.font.size = Pt(14)
        p.level = 1

        p = summary_frame.add_paragraph()
        p.text = f"• {latest_period}: {latest_turnover:.2f}x"
        p.font.size = Pt(14)
        p.level = 1

        turnover_change = latest_turnover - baseline_turnover
        emoji = "✅" if turnover_change > 0 else "⚠️"
        p = summary_frame.add_paragraph()
        p.text = f"{emoji} Change: {turnover_change:+.2f}x"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(0, 128, 0) if turnover_change > 0 else RGBColor(255, 0, 0)
        p.level = 1
        p.space_after = Pt(10)

        # Days Sales of Inventory section
        p = summary_frame.add_paragraph()
        p.text = "Days Sales of Inventory (lower is better):"
        p.font.size = Pt(14)
        p.font.bold = True
        p.space_after = Pt(4)

        p = summary_frame.add_paragraph()
        p.text = f"• FY2024 Baseline: {baseline_dsi:.1f} days"
        p.font.size = Pt(14)
        p.level = 1

        p = summary_frame.add_paragraph()
        p.text = f"• {latest_period}: {latest_dsi:.1f} days"
        p.font.size = Pt(14)
        p.level = 1

        dsi_change = latest_dsi - baseline_dsi
        emoji = "✅" if dsi_change < 0 else "⚠️"
        p = summary_frame.add_paragraph()
        p.text = f"{emoji} Change: {dsi_change:+.1f} days"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(0, 128, 0) if dsi_change < 0 else RGBColor(255, 0, 0)
        p.level = 1
        p.space_after = Pt(12)

        # Interpretation
        p = summary_frame.add_paragraph()
        if turnover_change < 0 or dsi_change > 0:
            p.text = "⚠️ Inventory efficiency has deteriorated - items are taking longer to sell"
            p.font.color.rgb = RGBColor(255, 0, 0)
        else:
            p.text = "✅ Inventory efficiency has improved - faster inventory turnover"
            p.font.color.rgb = RGBColor(0, 128, 0)
        p.font.size = Pt(13)
        p.font.bold = True


def add_debt_health_slide(prs, timeseries_data):
    """Add Debt Health slide (Phase 3 Chart 4)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.5)
    )
    title_frame = title_box.text_frame
    title = title_frame.paragraphs[0]
    title.text = "Debt Health & Interest Coverage"
    title.font.size = Pt(28)
    title.font.bold = True

    # Instruction text with hyperlink
    instruction_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.0), Inches(9), Inches(1.0)
    )
    instruction_frame = instruction_box.text_frame
    p = instruction_frame.paragraphs[0]
    p.text = "Dual-axis chart tracking Interest Coverage Ratio and Total Debt:"
    p.font.size = Pt(14)
    p.space_after = Pt(6)

    # Add clickable hyperlink
    p = instruction_frame.add_paragraph()
    p.text = "📊 Click to view: "
    p.font.size = Pt(14)

    # Get absolute path to the chart file
    chart_path = Path("output/chart_debt_health.html").resolve()

    run = p.add_run()
    run.text = "Debt Health Interactive Chart"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 255)
    run.font.underline = True
    run.hyperlink.address = str(chart_path)

    p.space_after = Pt(12)

    # Summary bullets with key insights
    summary_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(4)
    )
    summary_frame = summary_box.text_frame

    # Get debt metrics
    coverage = timeseries_data['metrics']['debt']['interest_coverage_ratio']
    total_debt = timeseries_data['metrics']['debt']['total_debt_billion']
    periods = timeseries_data['periods']

    # Find latest quarterly data
    latest_q_idx = None
    for i in range(len(periods) - 1, -1, -1):
        if periods[i]['filing_type'] == '10-Q' and coverage[i] is not None:
            latest_q_idx = i
            break

    # Find FY2024 baseline
    fy2024_idx = next((i for i, p in enumerate(periods) if p['period'] == 'FY2024'), None)

    if latest_q_idx is not None and fy2024_idx is not None:
        latest_coverage = coverage[latest_q_idx]
        latest_debt = total_debt[latest_q_idx]
        latest_period = periods[latest_q_idx]['period']

        baseline_coverage = coverage[fy2024_idx]
        baseline_debt = total_debt[fy2024_idx]

        # Skip if missing critical data
        if baseline_coverage is None or baseline_debt is None or latest_coverage is None or latest_debt is None:
            p = summary_frame.paragraphs[0]
            p.text = "⚠️ Insufficient debt data available for comparison. Please check annual 10-K reports for complete debt metrics."
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(255, 140, 0)
            return

        p = summary_frame.paragraphs[0]
        p.text = "Key Insights:"
        p.font.size = Pt(16)
        p.font.bold = True
        p.space_after = Pt(8)

        # Interest Coverage section
        p = summary_frame.add_paragraph()
        p.text = "Interest Coverage Ratio (higher is better):"
        p.font.size = Pt(14)
        p.font.bold = True
        p.space_after = Pt(4)

        p = summary_frame.add_paragraph()
        p.text = f"• FY2024 Baseline: {baseline_coverage:.2f}x"
        p.font.size = Pt(14)
        p.level = 1

        p = summary_frame.add_paragraph()
        p.text = f"• {latest_period}: {latest_coverage:.2f}x"
        p.font.size = Pt(14)
        p.level = 1

        coverage_change = latest_coverage - baseline_coverage
        emoji = "✅" if coverage_change > 0 else "⚠️"
        p = summary_frame.add_paragraph()
        p.text = f"{emoji} Change: {coverage_change:+.2f}x"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(0, 128, 0) if coverage_change > 0 else RGBColor(255, 0, 0)
        p.level = 1

        # Warning if below 2.0x
        if latest_coverage < 2.0:
            p = summary_frame.add_paragraph()
            p.text = "🚨 CRITICAL: Coverage below 2.0x threshold!"
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(255, 0, 0)
            p.font.bold = True
            p.level = 1

        p.space_after = Pt(10)

        # Total Debt section
        p = summary_frame.add_paragraph()
        p.text = "Total Debt:"
        p.font.size = Pt(14)
        p.font.bold = True
        p.space_after = Pt(4)

        p = summary_frame.add_paragraph()
        p.text = f"• FY2024 Baseline: ${baseline_debt:.2f}B"
        p.font.size = Pt(14)
        p.level = 1

        p = summary_frame.add_paragraph()
        p.text = f"• {latest_period}: ${latest_debt:.2f}B"
        p.font.size = Pt(14)
        p.level = 1

        debt_change = latest_debt - baseline_debt
        debt_pct_change = (debt_change / baseline_debt) * 100
        emoji = "⚠️" if debt_change > 0 else "✅"
        p = summary_frame.add_paragraph()
        p.text = f"{emoji} Change: ${debt_change:+.2f}B ({debt_pct_change:+.1f}%)"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(255, 0, 0) if debt_change > 0 else RGBColor(0, 128, 0)
        p.level = 1
        p.space_after = Pt(12)

        # Overall assessment
        p = summary_frame.add_paragraph()
        if coverage_change < -2.0 and debt_change > 0:
            p.text = "🚨 CRITICAL: Deteriorating coverage + rising debt = elevated financial risk"
            p.font.color.rgb = RGBColor(255, 0, 0)
        elif coverage_change < 0 and debt_change > 0:
            p.text = "⚠️ WARNING: Both coverage declining and debt increasing"
            p.font.color.rgb = RGBColor(255, 140, 0)
        else:
            p.text = "Debt health metrics require monitoring"
            p.font.color.rgb = RGBColor(100, 100, 100)
        p.font.size = Pt(13)
        p.font.bold = True


def add_cash_flows_slide(prs, timeseries_data):
    """Add Cash Flows slide (Phase 3 Chart 5)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.5)
    )
    title_frame = title_box.text_frame
    title = title_frame.paragraphs[0]
    title.text = "Cash Flow Analysis"
    title.font.size = Pt(28)
    title.font.bold = True

    # Instruction text with hyperlink
    instruction_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.0), Inches(9), Inches(1.0)
    )
    instruction_frame = instruction_box.text_frame
    p = instruction_frame.paragraphs[0]
    p.text = "Stacked bar chart showing Operating, Investing, and Financing cash flows:"
    p.font.size = Pt(14)
    p.space_after = Pt(6)

    # Add clickable hyperlink
    p = instruction_frame.add_paragraph()
    p.text = "📊 Click to view: "
    p.font.size = Pt(14)

    # Get absolute path to the chart file
    chart_path = Path("output/chart_cash_flows.html").resolve()

    run = p.add_run()
    run.text = "Cash Flows Interactive Chart"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 255)
    run.font.underline = True
    run.hyperlink.address = str(chart_path)

    p.space_after = Pt(12)

    # Summary bullets with key insights
    summary_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(4)
    )
    summary_frame = summary_box.text_frame

    # Get cash flow metrics
    operating_cf = timeseries_data['metrics']['cash_flows']['operating_cash_flow_billion']
    investing_cf = timeseries_data['metrics']['cash_flows']['investing_cash_flow_billion']
    financing_cf = timeseries_data['metrics']['cash_flows']['financing_cash_flow_billion']
    periods = timeseries_data['periods']

    # Find latest quarterly data
    latest_q_idx = None
    for i in range(len(periods) - 1, -1, -1):
        if periods[i]['filing_type'] == '10-Q' and operating_cf[i] is not None:
            latest_q_idx = i
            break

    # Find FY2024 baseline
    fy2024_idx = next((i for i, p in enumerate(periods) if p['period'] == 'FY2024'), None)

    if latest_q_idx is not None and fy2024_idx is not None:
        latest_operating = operating_cf[latest_q_idx]
        latest_investing = investing_cf[latest_q_idx]
        latest_financing = financing_cf[latest_q_idx]
        latest_period = periods[latest_q_idx]['period']

        baseline_operating = operating_cf[fy2024_idx]

        p = summary_frame.paragraphs[0]
        p.text = f"Latest Cash Flows ({latest_period}):"
        p.font.size = Pt(16)
        p.font.bold = True
        p.space_after = Pt(8)

        # Operating cash flow
        p = summary_frame.add_paragraph()
        emoji = "✅" if latest_operating > 0 else "⚠️"
        p.text = f"{emoji} Operating Activities: ${latest_operating:.2f}B"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(0, 128, 0) if latest_operating > 0 else RGBColor(255, 0, 0)
        p.level = 0

        # Investing cash flow
        p = summary_frame.add_paragraph()
        p.text = f"• Investing Activities: ${latest_investing:.2f}B"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(100, 100, 100)
        p.level = 0

        # Financing cash flow
        p = summary_frame.add_paragraph()
        p.text = f"• Financing Activities: ${latest_financing:.2f}B"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(100, 100, 100)
        p.level = 0
        p.space_after = Pt(12)

        # Net cash flow
        net_cf = latest_operating + latest_investing + latest_financing
        p = summary_frame.add_paragraph()
        p.text = f"Net Cash Flow: ${net_cf:.2f}B"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 128, 0) if net_cf > 0 else RGBColor(255, 0, 0)
        p.space_after = Pt(12)

        # YoY comparison for operating CF
        if baseline_operating is not None:
            p = summary_frame.add_paragraph()
            p.text = "Operating Cash Flow vs FY2024:"
            p.font.size = Pt(14)
            p.font.bold = True
            p.space_after = Pt(4)

            p = summary_frame.add_paragraph()
            p.text = f"• FY2024: ${baseline_operating:.2f}B"
            p.font.size = Pt(14)
            p.level = 1

            p = summary_frame.add_paragraph()
            p.text = f"• {latest_period}: ${latest_operating:.2f}B (quarterly)"
            p.font.size = Pt(14)
            p.level = 1
            p.space_after = Pt(12)

        # Key insight
        p = summary_frame.add_paragraph()
        if latest_operating > 0 and net_cf > 0:
            p.text = "✅ Positive operating cash flow indicates healthy core business operations"
            p.font.color.rgb = RGBColor(0, 128, 0)
        elif latest_operating > 0 and net_cf < 0:
            p.text = "⚠️ Operating CF positive but net CF negative due to investing/financing outflows"
            p.font.color.rgb = RGBColor(255, 140, 0)
        else:
            p.text = "🚨 Negative operating cash flow requires immediate attention"
            p.font.color.rgb = RGBColor(255, 0, 0)
        p.font.size = Pt(13)
        p.font.bold = True


def add_baseline_slide(prs, baseline_data):
    """Add baseline slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Baseline: FY2024 Annual Performance"

    vital = baseline_data['vital_signs']

    # Create table
    left = Inches(2)
    top = Inches(2)
    width = Inches(6)
    height = Inches(3)

    table = slide.shapes.add_table(6, 2, left, top, width, height).table

    # Header
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = "Value"

    # Data rows
    metrics = [
        ("Net Sales", f"${vital['net_sales_billion']:.2f}B"),
        ("Operating Income", f"${vital['operating_income_billion']:.2f}B"),
        ("Operating Margin", f"{vital['operating_margin_percent']:.2f}%"),
        ("Gross Margin", f"{vital['gross_margin_percent']:.2f}%"),
        ("Inventory", f"${vital['inventory_billion']:.2f}B"),
    ]

    for i, (metric, value) in enumerate(metrics, 1):
        table.cell(i, 0).text = metric
        table.cell(i, 1).text = value

    # Style table
    for row in table.rows:
        row.height = Inches(0.5)
        for cell in row.cells:
            cell.text_frame.paragraphs[0].font.size = Pt(14)

    # Risk flags
    if baseline_data['risk_flags']:
        left = Inches(1)
        top = Inches(5.5)
        width = Inches(8)
        height = Inches(1.5)

        text_box = slide.shapes.add_textbox(left, top, width, height)
        tf = text_box.text_frame

        p = tf.add_paragraph()
        p.text = "Risk Flags:"
        p.font.size = Pt(14)
        p.font.bold = True

        for flag in baseline_data['risk_flags']:
            p = tf.add_paragraph()
            p.text = f"• {flag}"
            p.font.size = Pt(12)
            p.level = 0


def add_quarter_slide(prs, quarter_data, baseline_data):
    """Add quarterly analysis slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = f"{quarter_data['period']} Performance"

    vital = quarter_data['vital_signs']
    baseline_vital = baseline_data['vital_signs']

    # Left column: Metrics
    left = Inches(0.5)
    top = Inches(1.8)
    width = Inches(4.5)
    height = Inches(4)

    table = slide.shapes.add_table(6, 3, left, top, width, height).table

    # Headers
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = quarter_data['period']
    table.cell(0, 2).text = "vs Baseline"

    # Data
    metrics = [
        ("Net Sales", vital.get('net_sales_billion', 0), baseline_vital.get('net_sales_billion', 0), "B"),
        ("Operating Margin", vital.get('operating_margin_percent', 0), baseline_vital.get('operating_margin_percent', 0), "%"),
        ("Gross Margin", vital.get('gross_margin_percent', 0), baseline_vital.get('gross_margin_percent', 0), "%"),
        ("Operating Income", vital.get('operating_income_billion', 0), baseline_vital.get('operating_income_billion', 0), "B"),
        ("Inventory", vital.get('inventory_billion', 0), baseline_vital.get('inventory_billion', 0), "B"),
    ]

    for i, (metric, current, baseline, unit) in enumerate(metrics, 1):
        table.cell(i, 0).text = metric
        if unit == "B":
            table.cell(i, 1).text = f"${current:.2f}B"
            change = current - baseline
            table.cell(i, 2).text = f"{change:+.2f}B"
        else:
            table.cell(i, 1).text = f"{current:.2f}%"
            change = current - baseline
            table.cell(i, 2).text = f"{change:+.2f}%"

            # Color code changes
            cell = table.cell(i, 2)
            if change < -0.5:
                cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 0, 0)
            elif change > 0.5:
                cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 128, 0)

    # Style table
    for row in table.rows:
        row.height = Inches(0.5)
        for cell in row.cells:
            cell.text_frame.paragraphs[0].font.size = Pt(12)

    # Right column: Analysis
    left = Inches(5.5)
    top = Inches(1.8)
    width = Inches(4)
    height = Inches(4)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame
    tf.word_wrap = True

    p = tf.add_paragraph()
    p.text = "Key Observations:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.space_after = Pt(8)

    # Add trend analysis from baseline comparison
    if 'vs_baseline' in vital and vital['vs_baseline']:
        vs = vital['vs_baseline']

        if 'operating_margin_trend' in vs:
            p = tf.add_paragraph()
            trend = vs['operating_margin_trend']
            change = vs.get('operating_margin_change', 0)
            emoji = "✅" if trend == "improving" else "⚠️"
            p.text = f"{emoji} Operating margin {trend} ({change:+.2f}% vs baseline)"
            p.font.size = Pt(12)
            p.level = 0

        if 'gross_margin_change' in vs:
            change = vs['gross_margin_change']
            if abs(change) > 0.5:
                p = tf.add_paragraph()
                emoji = "✅" if change > 0 else "⚠️"
                p.text = f"{emoji} Gross margin {change:+.2f}% vs baseline"
                p.font.size = Pt(12)
                p.level = 0

    # Add YoY analysis
    if 'vs_year_ago' in vital and vital['vs_year_ago']:
        yoy = vital['vs_year_ago']

        if 'operating_margin_yoy_change' in yoy:
            p = tf.add_paragraph()
            change = yoy['operating_margin_yoy_change']
            comparison = yoy.get('comparison_period', 'prior year')
            emoji = "✅" if change > 0 else "⚠️"
            p.text = f"{emoji} Operating margin {change:+.2f}% vs {comparison}"
            p.font.size = Pt(12)
            p.level = 0

        if 'net_sales_yoy_growth_percent' in yoy:
            growth = yoy['net_sales_yoy_growth_percent']
            p = tf.add_paragraph()
            emoji = "✅" if growth > 0 else "⚠️"
            p.text = f"{emoji} Sales {growth:+.1f}% YoY"
            p.font.size = Pt(12)
            p.level = 0

        if 'inventory_buildup_warning' in yoy:
            p = tf.add_paragraph()
            p.text = f"🚨 {yoy['inventory_buildup_warning']}"
            p.font.size = Pt(12)
            p.font.color.rgb = RGBColor(255, 0, 0)
            p.level = 0

    # Risk flags
    if quarter_data.get('risk_flags'):
        p = tf.add_paragraph()
        p.text = "\nRisk Flags:"
        p.font.size = Pt(12)
        p.font.bold = True
        p.space_before = Pt(8)

        for flag in quarter_data['risk_flags'][:3]:
            p = tf.add_paragraph()
            p.text = f"• {flag}"
            p.font.size = Pt(11)
            p.level = 1


def add_q3_warning_slide(prs, q3_data, baseline_data):
    """Special slide for Q3 with warnings."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Warning banner
    left = Inches(0)
    top = Inches(0.5)
    width = Inches(10)
    height = Inches(1)

    banner = slide.shapes.add_shape(1, left, top, width, height)  # Rectangle
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(255, 0, 0)
    banner.line.color.rgb = RGBColor(255, 0, 0)

    tf = banner.text_frame
    tf.text = "⚠️ Q3 2025: CRITICAL WEAKNESS DETECTED"
    p = tf.paragraphs[0]
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Metrics comparison
    vital = q3_data['vital_signs']
    baseline_vital = baseline_data['vital_signs']

    left = Inches(1)
    top = Inches(2)
    width = Inches(8)
    height = Inches(4.5)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame
    tf.word_wrap = True

    issues = [
        f"Operating Margin: {vital['operating_margin_percent']:.2f}% ({vital['vs_baseline']['operating_margin_change']:+.2f}% vs baseline)",
        f"  → Declined 147 basis points - worst quarter of the year",
        "",
        f"Inventory: ${vital['inventory_billion']:.2f}B",
        f"  → Up {((vital['inventory_billion']/baseline_vital['inventory_billion']-1)*100):.1f}% from baseline",
        f"  → Excess inventory building = potential clearance sales ahead",
        "",
        f"Operating Income: ${vital['operating_income_billion']:.2f}B",
        f"  → Lowest quarterly operating income despite similar sales",
        "",
        "Combined Effect:",
        "  → Interest coverage dropped to 1.5x (from 9.7x at baseline)",
        "  → Approaching distressed territory (<1.5x is red flag)",
        "  → Rising debt + falling profitability = liquidity risk",
    ]

    for line in issues:
        p = tf.add_paragraph()
        p.text = line
        if line.startswith("  →"):
            p.font.size = Pt(13)
            p.level = 1
            p.font.color.rgb = RGBColor(128, 0, 0)
        elif ":" in line and not line.startswith(" "):
            p.font.size = Pt(16)
            p.font.bold = True
            p.space_after = Pt(4)
        else:
            p.font.size = Pt(14)

        if "worst" in line.lower() or "distressed" in line.lower() or "risk" in line.lower():
            p.font.color.rgb = RGBColor(255, 0, 0)


def add_debt_analysis_slide(prs):
    """Add debt analysis slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Debt & Leverage Analysis"

    # Debt metrics table
    left = Inches(0.5)
    top = Inches(1.8)
    width = Inches(9)
    height = Inches(2.5)

    table = slide.shapes.add_table(5, 5, left, top, width, height).table

    # Headers
    headers = ["Metric", "FY2024", "Q1 2025", "Q2 2025", "Q3 2025"]
    for i, header in enumerate(headers):
        table.cell(0, i).text = header

    # Data
    debt_data = [
        ["Total Debt", "$14.30B", "$14.33B", "$15.32B", "$15.37B"],
        ["Debt-to-Equity", "0.97x", "0.96x", "0.99x", "0.99x"],
        ["Interest Coverage", "9.7x", "2.6x", "2.2x", "1.5x"],
        ["Change from Baseline", "—", "+0.2%", "+7.1%", "+7.5%"],
    ]

    for i, row_data in enumerate(debt_data, 1):
        for j, value in enumerate(row_data):
            cell = table.cell(i, j)
            cell.text = value

            # Highlight deteriorating coverage
            if i == 2 and j > 1:  # Interest coverage row
                coverage = float(value.replace('x', ''))
                if coverage < 2.0:
                    cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 0, 0)

    # Style table
    for row in table.rows:
        row.height = Inches(0.4)
        for cell in row.cells:
            cell.text_frame.paragraphs[0].font.size = Pt(12)

    # Key findings
    left = Inches(0.5)
    top = Inches(4.5)
    width = Inches(9)
    height = Inches(2.5)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame

    p = tf.add_paragraph()
    p.text = "Critical Findings:"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = RGBColor(204, 0, 0)

    findings = [
        "Debt increased 7.5% while operating income declined significantly",
        "Interest coverage compressed from 9.7x to 1.5x in one year (approaching distressed level)",
        "Debt likely used to fund inventory buildup and cover working capital shortfalls",
        "$2.00B debt matures in FY2026 - needs refinancing or paydown with limited cash flow",
    ]

    for finding in findings:
        p = tf.add_paragraph()
        p.text = f"• {finding}"
        p.font.size = Pt(13)
        p.level = 0


def add_recommendations_slide(prs, data):
    """Add recommendations slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Key Risks & Monitoring Points"

    left = Inches(0.5)
    top = Inches(1.5)
    width = Inches(9)
    height = Inches(5.5)

    text_box = slide.shapes.add_textbox(left, top, width, height)
    tf = text_box.text_frame
    tf.word_wrap = True

    sections = [
        ("Immediate Risks (Q4 2025)", [
            "Q4 operating margin recovery critical to avoid further deterioration",
            "High inventory + weak margins → Expected Q4 clearance sales",
            "If interest coverage falls below 1.5x, triggers debt covenant concerns",
        ]),
        ("Watch Points for Next Quarter", [
            "Operating margin trend (needs to recover to 5%+ range)",
            "Inventory levels (should decline post-holiday)",
            "Comparable sales breakdown (store vs. digital performance)",
            "Cash flow from operations (ability to service $2B FY2026 debt maturity)",
        ]),
        ("Strategic Questions", [
            "Can Target reduce inventory without severe margin impact?",
            "Is the operating margin decline temporary or structural?",
            "Will shrink/theft issues persist into FY2026?",
            "Is current debt level sustainable with lower profitability?",
        ]),
    ]

    for section_title, bullets in sections:
        p = tf.add_paragraph()
        p.text = section_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = RGBColor(204, 0, 0)
        p.space_after = Pt(6)

        for bullet in bullets:
            p = tf.add_paragraph()
            p.text = f"• {bullet}"
            p.font.size = Pt(13)
            p.level = 0
            p.space_after = Pt(3)

        p = tf.add_paragraph()
        p.space_after = Pt(10)


def add_investment_thesis_slide(prs, thesis):
    """Add Investment Thesis slide (Phase 4)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.5)
    )
    title_frame = title_box.text_frame
    title = title_frame.paragraphs[0]
    title.text = "Investment Thesis"
    title.font.size = Pt(32)
    title.font.bold = True
    title.font.color.rgb = RGBColor(204, 0, 0)  # Target red

    # Recommendation box (highlighted)
    rec_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.0), Inches(9), Inches(1.2)
    )
    rec_frame = rec_box.text_frame
    rec = thesis['recommendation']

    p = rec_frame.paragraphs[0]
    p.text = f"Recommendation: {rec['rating']}"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0, 128, 0) if rec['rating'] == 'Buy' else \
                       RGBColor(255, 140, 0) if rec['rating'] == 'Hold' else \
                       RGBColor(255, 0, 0)

    p = rec_frame.add_paragraph()
    p.text = rec['rationale']
    p.font.size = Pt(16)
    p.space_after = Pt(6)

    # Risk factors (left column)
    risk_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(4.25), Inches(4)
    )
    risk_frame = risk_box.text_frame

    p = risk_frame.paragraphs[0]
    p.text = "⚠️  Risk Factors"
    p.font.size = Pt(20)
    p.font.bold = True
    p.space_after = Pt(12)

    for risk in thesis['risk_factors']:
        p = risk_frame.add_paragraph()
        p.text = f"• {risk['factor']} ({risk['severity']})"
        p.font.size = Pt(14)
        p.level = 0

        p = risk_frame.add_paragraph()
        p.text = risk['evidence']
        p.font.size = Pt(12)
        p.level = 1
        p.space_after = Pt(6)

    # Opportunities (right column)
    opp_box = slide.shapes.add_textbox(
        Inches(5.25), Inches(2.5), Inches(4.25), Inches(4)
    )
    opp_frame = opp_box.text_frame

    p = opp_frame.paragraphs[0]
    p.text = "✨ Opportunities"
    p.font.size = Pt(20)
    p.font.bold = True
    p.space_after = Pt(12)

    for opp in thesis['opportunities']:
        p = opp_frame.add_paragraph()
        p.text = f"• {opp['factor']} ({opp['potential']} potential)"
        p.font.size = Pt(14)
        p.level = 0

        p = opp_frame.add_paragraph()
        p.text = opp['evidence']
        p.font.size = Pt(12)
        p.level = 1
        p.space_after = Pt(6)


def add_margin_bridge_slide(prs, timeseries_data, full_data):
    """Add Margin Bridge Analysis slide (Phase 4)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.5)
    )
    title_frame = title_box.text_frame
    title = title_frame.paragraphs[0]
    title.text = "Operating Margin Bridge (FY2022 → Q3 2025)"
    title.font.size = Pt(28)
    title.font.bold = True

    # Instruction text with hyperlink
    instruction_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.0), Inches(9), Inches(1.0)
    )
    instruction_frame = instruction_box.text_frame
    p = instruction_frame.paragraphs[0]
    p.text = "Interactive waterfall chart showing operating margin evolution:"
    p.font.size = Pt(14)
    p.space_after = Pt(6)

    # Add clickable hyperlink
    p = instruction_frame.add_paragraph()
    p.text = "📂 Click to view: "
    p.font.size = Pt(14)

    # Get absolute path to the chart file
    chart_path = Path("output/chart_margin_bridge.html").resolve()

    run = p.add_run()
    run.text = "Margin Bridge Waterfall Chart"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 255)
    run.font.underline = True
    run.hyperlink.address = str(chart_path)

    p.space_after = Pt(12)

    # Summary bullets
    summary_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(4)
    )
    summary_frame = summary_box.text_frame

    margins = timeseries_data['metrics']['margins']['operating_margin_percent']
    periods = timeseries_data['periods']

    # Get FY2022 and Q3 2025
    fy2022_idx = next((i for i, p in enumerate(periods) if p['period'] == 'FY2022'), None)
    q3_2025_idx = next((i for i, p in enumerate(periods) if p['period'] == 'Q3 2025'), None)

    if fy2022_idx is not None and q3_2025_idx is not None:
        fy2022_margin = margins[fy2022_idx]
        q3_2025_margin = margins[q3_2025_idx]
        total_change = q3_2025_margin - fy2022_margin

        p = summary_frame.paragraphs[0]
        p.text = f"• FY2022 Baseline: {fy2022_margin:.2f}%"
        p.font.size = Pt(16)
        p.space_after = Pt(6)

        p = summary_frame.add_paragraph()
        p.text = f"• Q3 2025 Current: {q3_2025_margin:.2f}%"
        p.font.size = Pt(16)
        p.space_after = Pt(6)

        p = summary_frame.add_paragraph()
        p.text = f"• Net Change: {total_change:+.2f} percentage points"
        p.font.size = Pt(16)
        p.font.color.rgb = RGBColor(0, 128, 0) if total_change > 0 else RGBColor(255, 0, 0)
        p.space_after = Pt(12)

    p = summary_frame.add_paragraph()
    p.text = "Key Drivers:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.space_after = Pt(6)

    # Load risk heatmap for context
    shrink_trend = full_data['risk_heatmap']['shrink']['trend']
    markdown_trend = full_data['risk_heatmap']['markdown']['trend']

    p = summary_frame.add_paragraph()
    p.text = f"• Shrink impact: {shrink_trend} trend"
    p.font.size = Pt(14)
    p.level = 1

    p = summary_frame.add_paragraph()
    p.text = f"• Markdown activity: {markdown_trend} trend"
    p.font.size = Pt(14)
    p.level = 1


def add_risk_heatmap_slide(prs, full_data):
    """Add Risk Heatmap slide (Phase 4)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.5)
    )
    title_frame = title_box.text_frame
    title = title_frame.paragraphs[0]
    title.text = "Risk Heatmap: Shrink & Markdown Trends"
    title.font.size = Pt(28)
    title.font.bold = True

    # Instructions with clickable hyperlinks
    instruction_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.0), Inches(9), Inches(2.0)
    )
    instruction_frame = instruction_box.text_frame

    p = instruction_frame.paragraphs[0]
    p.text = "Interactive visualizations showing risk mention trends:"
    p.font.size = Pt(14)
    p.space_after = Pt(6)

    p = instruction_frame.add_paragraph()
    p.text = "📂 Click to view charts:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.space_after = Pt(6)

    # First hyperlink - Risk Trends
    p = instruction_frame.add_paragraph()
    p.text = "   • "
    p.level = 1

    chart1_path = Path("output/chart_risk_trends.html").resolve()
    run = p.add_run()
    run.text = "Risk Mention Trends (stacked area chart)"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 255)
    run.font.underline = True
    run.hyperlink.address = str(chart1_path)

    # Second hyperlink - Risk Heatmap Grid
    p = instruction_frame.add_paragraph()
    p.text = "   • "
    p.level = 1

    chart2_path = Path("output/chart_risk_heatmap_grid.html").resolve()
    run = p.add_run()
    run.text = "Risk Heatmap Grid (intensity matrix)"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 255)
    run.font.underline = True
    run.hyperlink.address = str(chart2_path)

    p.space_after = Pt(12)

    # Summary stats (table)
    risk_heatmap = full_data['risk_heatmap']

    rows = 3
    cols = 4
    left = Inches(1.5)
    top = Inches(3.0)
    width = Inches(7)
    height = Inches(2.5)

    table = slide.shapes.add_table(rows, cols, left, top, width, height).table

    # Headers
    table.cell(0, 0).text = "Risk Type"
    table.cell(0, 1).text = "Total Mentions"
    table.cell(0, 2).text = "Avg per Period"
    table.cell(0, 3).text = "Trend"

    # Shrink row
    table.cell(1, 0).text = "Shrink/Theft"
    table.cell(1, 1).text = str(risk_heatmap['shrink']['total_mentions'])
    table.cell(1, 2).text = str(risk_heatmap['shrink']['avg_mentions_per_period'])
    table.cell(1, 3).text = risk_heatmap['shrink']['trend']

    # Color code shrink trend cell
    cell = table.cell(1, 3)
    if risk_heatmap['shrink']['trend'] == 'increasing':
        for paragraph in cell.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(255, 0, 0)
                run.font.bold = True

    # Markdown row
    table.cell(2, 0).text = "Markdown/Promo"
    table.cell(2, 1).text = str(risk_heatmap['markdown']['total_mentions'])
    table.cell(2, 2).text = str(risk_heatmap['markdown']['avg_mentions_per_period'])
    table.cell(2, 3).text = risk_heatmap['markdown']['trend']

    # Format table
    for row in table.rows:
        for cell in row.cells:
            cell.text_frame.paragraphs[0].font.size = Pt(14)
            cell.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Bold headers
    for col in range(cols):
        table.cell(0, col).text_frame.paragraphs[0].font.bold = True


if __name__ == "__main__":
    create_target_presentation()
