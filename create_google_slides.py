"""
Create Google Slides compatible presentation
Uses Google Slides API format (JSON)
"""

import json


def create_google_slides_json():
    """Create presentation data in Google Slides format."""

    # Load analysis data
    with open('output/target_analysis.json', 'r') as f:
        data = json.load(f)

    # Create presentation structure
    presentation = {
        "title": "Target Corporation Financial Analysis",
        "slides": []
    }

    # Slide 1: Title
    presentation["slides"].append({
        "layout": "TITLE",
        "elements": [
            {
                "type": "title",
                "text": "Target Corporation",
                "style": {"fontSize": 44, "bold": True, "color": "#CC0000"}
            },
            {
                "type": "subtitle",
                "text": "Financial Analysis Report\nFY2024 - Q3 2025",
                "style": {"fontSize": 24}
            }
        ]
    })

    # Slide 2: Executive Summary
    baseline = data[0]['vital_signs']
    q3 = data[3]['vital_signs']

    presentation["slides"].append({
        "layout": "TITLE_AND_BODY",
        "elements": [
            {
                "type": "title",
                "text": "Executive Summary"
            },
            {
                "type": "body",
                "text": f"""FY2024 Baseline Performance:
• Net Sales: ${baseline['net_sales_billion']:.2f}B
• Operating Margin: {baseline['operating_margin_percent']:.2f}%
• Gross Margin: {baseline['gross_margin_percent']:.2f}%

Q3 2025 - Critical Weakness Detected:
• Operating Margin: {q3['operating_margin_percent']:.2f}% ({q3['vs_baseline']['operating_margin_change']:+.2f}% vs baseline) ⚠️
• Inventory: ${q3['inventory_billion']:.2f}B (+{((q3['inventory_billion']/baseline['inventory_billion']-1)*100):.1f}%)
• Debt increased 7.5% while operating income declined

Key Risk Flags:
• Interest coverage deteriorated from 9.7x to 1.5x
• Shrink/theft mentioned in all quarters
• Inventory buildup suggests potential clearance ahead"""
            }
        ]
    })

    # Slides 3-6: Each quarter
    for i, quarter in enumerate(data):
        vital = quarter['vital_signs']

        if i == 0:
            title = "Baseline: FY2024 Annual Performance"
        else:
            title = f"{quarter['period']} Performance"

        # Build metrics text
        metrics_text = f"""Net Sales: ${vital.get('net_sales_billion', 0):.2f}B
Operating Income: ${vital.get('operating_income_billion', 0):.2f}B
Operating Margin: {vital.get('operating_margin_percent', 0):.2f}%
Gross Margin: {vital.get('gross_margin_percent', 0):.2f}%
Inventory: ${vital.get('inventory_billion', 0):.2f}B"""

        # Add vs baseline if available
        if 'vs_baseline' in vital and vital['vs_baseline']:
            vs = vital['vs_baseline']
            metrics_text += f"\n\nvs Baseline:"
            if 'operating_margin_change' in vs:
                metrics_text += f"\n• Operating Margin: {vs['operating_margin_change']:+.2f}% ({vs['operating_margin_trend']})"
            if 'gross_margin_change' in vs:
                metrics_text += f"\n• Gross Margin: {vs['gross_margin_change']:+.2f}%"
            if 'markdown_flag' in vs:
                metrics_text += f"\n• {vs['markdown_flag']}"

        # Add risk flags
        if quarter.get('risk_flags'):
            metrics_text += "\n\nRisk Flags:"
            for flag in quarter['risk_flags'][:3]:
                metrics_text += f"\n• {flag}"

        presentation["slides"].append({
            "layout": "TITLE_AND_BODY",
            "elements": [
                {
                    "type": "title",
                    "text": title
                },
                {
                    "type": "body",
                    "text": metrics_text
                }
            ]
        })

    # Slide: Debt Analysis
    presentation["slides"].append({
        "layout": "TITLE_AND_BODY",
        "elements": [
            {
                "type": "title",
                "text": "Debt & Leverage Analysis"
            },
            {
                "type": "body",
                "text": """Debt Metrics Over Time:

                FY2024    Q1 2025   Q2 2025   Q3 2025
Total Debt      $14.30B   $14.33B   $15.32B   $15.37B
Debt/Equity     0.97x     0.96x     0.99x     0.99x
Int. Coverage   9.7x      2.6x      2.2x      1.5x
Change          —         +0.2%     +7.1%     +7.5%

Critical Findings:
• Debt increased 7.5% while operating income declined
• Interest coverage compressed from 9.7x to 1.5x (approaching distressed)
• Debt likely funding inventory buildup and working capital shortfalls
• $2.00B debt matures in FY2026 - refinancing risk"""
            }
        ]
    })

    # Slide: Recommendations
    presentation["slides"].append({
        "layout": "TITLE_AND_BODY",
        "elements": [
            {
                "type": "title",
                "text": "Key Risks & Monitoring Points"
            },
            {
                "type": "body",
                "text": """Immediate Risks (Q4 2025):
• Q4 operating margin recovery critical
• High inventory + weak margins → Expected clearance sales
• Interest coverage below 1.5x triggers debt covenant concerns

Watch Points for Next Quarter:
• Operating margin trend (needs 5%+ recovery)
• Inventory levels (should decline post-holiday)
• Comparable sales breakdown
• Cash flow from operations

Strategic Questions:
• Can Target reduce inventory without severe margin impact?
• Is operating margin decline temporary or structural?
• Will shrink/theft issues persist into FY2026?
• Is current debt level sustainable with lower profitability?"""
            }
        ]
    })

    # Save as JSON
    output_path = 'output/target_presentation_data.json'
    with open(output_path, 'w') as f:
        json.dump(presentation, f, indent=2)

    print(f"✅ Presentation data created: {output_path}")

    # Also create a simple HTML version for viewing
    create_html_presentation(presentation)

    # Create markdown version for Google Docs import
    create_markdown_presentation(presentation, data)

    return output_path


def create_html_presentation(presentation):
    """Create HTML version that can be opened in browser."""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{presentation['title']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f0f0f0;
        }}
        .slide {{
            width: 960px;
            height: 720px;
            margin: 20px auto;
            background: white;
            padding: 40px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            page-break-after: always;
            position: relative;
        }}
        .title-slide {{
            text-align: center;
            padding-top: 250px;
        }}
        .title-slide h1 {{
            color: #CC0000;
            font-size: 48px;
            margin-bottom: 20px;
        }}
        .title-slide h2 {{
            color: #666;
            font-size: 32px;
        }}
        h1 {{
            color: #CC0000;
            font-size: 36px;
            margin-bottom: 30px;
            border-bottom: 3px solid #CC0000;
            padding-bottom: 10px;
        }}
        .body-text {{
            font-size: 18px;
            line-height: 1.6;
            white-space: pre-line;
        }}
        .slide-number {{
            position: absolute;
            bottom: 20px;
            right: 40px;
            color: #999;
            font-size: 14px;
        }}
        @media print {{
            .slide {{
                margin: 0;
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
"""

    for i, slide in enumerate(presentation['slides'], 1):
        if i == 1:
            # Title slide
            title_elem = next((e for e in slide['elements'] if e['type'] == 'title'), None)
            subtitle_elem = next((e for e in slide['elements'] if e['type'] == 'subtitle'), None)

            html += f"""
    <div class="slide title-slide">
        <h1>{title_elem['text'] if title_elem else ''}</h1>
        <h2>{subtitle_elem['text'].replace(chr(10), '<br>') if subtitle_elem else ''}</h2>
        <div class="slide-number">{i}</div>
    </div>
"""
        else:
            # Content slide
            title_elem = next((e for e in slide['elements'] if e['type'] == 'title'), None)
            body_elem = next((e for e in slide['elements'] if e['type'] == 'body'), None)

            html += f"""
    <div class="slide">
        <h1>{title_elem['text'] if title_elem else ''}</h1>
        <div class="body-text">{body_elem['text'] if body_elem else ''}</div>
        <div class="slide-number">{i}</div>
    </div>
"""

    html += """
</body>
</html>
"""

    output_path = 'output/Target_Financial_Analysis.html'
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✅ HTML presentation created: {output_path}")
    print(f"   → Open in browser and use File > Print > Save as PDF")
    print(f"   → Then upload PDF to Google Drive and open with Google Slides")


def create_markdown_presentation(presentation, data):
    """Create Markdown version for Google Docs import."""

    md = f"""# {presentation['title']}

---

"""

    for slide in presentation['slides']:
        title_elem = next((e for e in slide['elements'] if e['type'] == 'title'), None)

        if title_elem:
            md += f"## {title_elem['text']}\n\n"

        for elem in slide['elements']:
            if elem['type'] == 'subtitle':
                md += f"### {elem['text']}\n\n"
            elif elem['type'] == 'body':
                md += f"{elem['text']}\n\n"

        md += "---\n\n"

    output_path = 'output/Target_Financial_Analysis.md'
    with open(output_path, 'w') as f:
        f.write(md)

    print(f"✅ Markdown document created: {output_path}")
    print(f"   → Upload to Google Drive")
    print(f"   → Open with Google Docs")
    print(f"   → File > Open with > Google Slides")


if __name__ == "__main__":
    print("=" * 60)
    print("Creating Google Slides Compatible Presentation")
    print("=" * 60)
    print()

    create_google_slides_json()

    print()
    print("=" * 60)
    print("✅ All formats created!")
    print("=" * 60)
    print()
    print("EASIEST METHOD:")
    print("1. Open: output/Target_Financial_Analysis.html in your browser")
    print("2. Print to PDF (Cmd+P or Ctrl+P)")
    print("3. Upload PDF to Google Drive")
    print("4. Right-click PDF → Open with → Google Slides")
    print()
    print("The PDF will be converted to editable Google Slides!")
