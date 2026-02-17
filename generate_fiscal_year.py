#!/usr/bin/env python3
"""
Multi-Year Budget Dashboard Generator
Generates budget and tracking views for any fiscal year
"""

import json
import sys
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def safe_float(value, default=0.0):
    """Safely convert value to float, handling text and errors"""
    if pd.isna(value):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Try to extract number from string
        import re
        # Remove common text patterns
        cleaned = re.sub(r'[^\d\.\-]', '', str(value))
        try:
            return float(cleaned) if cleaned else default
        except:
            return default
    return default

def extract_budget_from_master(excel_path, fiscal_year='FY26'):
    """Extract budget data from master budget Excel file"""
    try:
        # Read the FA_Summary sheet
        df = pd.read_excel(excel_path, sheet_name='FA_Summary', header=None)

        # Find the column for this fiscal year (row 4 contains FY labels)
        budget_col = None
        for i, val in enumerate(df.iloc[4, :]):
            if pd.notna(val) and str(val).strip() == fiscal_year:
                budget_col = i
                break

        if budget_col is None:
            print(f"  ✗ Could not find column for {fiscal_year} in Excel file")
            return None

        print(f"  Found {fiscal_year} data in column {budget_col}")

        # Extract key budget values with safe conversion
        # Row indices based on the Excel structure
        budget_data = {
            'standing_faculty': safe_float(df.iloc[10, budget_col]),
            'practice_faculty': safe_float(df.iloc[11, budget_col]),
            'adjunct_faculty': safe_float(df.iloc[12, budget_col]),
            'total_academic': safe_float(df.iloc[15, budget_col]),
            'total_non_academic': safe_float(df.iloc[41, budget_col]),
            'total_compensation': safe_float(df.iloc[42, budget_col]),
            'current_expenses': safe_float(df.iloc[110, budget_col]),
            'grand_total': safe_float(df.iloc[116, budget_col])
        }

        # Extract detailed compensation rows
        compensation_detail = []
        for i in range(10, 43):  # Rows with compensation data
            label = str(df.iloc[i, 1]) if not pd.isna(df.iloc[i, 1]) else ''
            value = safe_float(df.iloc[i, budget_col])
            if label and value > 0:
                compensation_detail.append({'category': label, 'amount': value})

        # Extract current expenses detail
        expense_detail = []
        for i in range(48, 111):  # Rows with expense data
            label = str(df.iloc[i, 1]) if not pd.isna(df.iloc[i, 1]) else ''
            value = safe_float(df.iloc[i, budget_col])
            if label and value > 0:
                expense_detail.append({'category': label, 'amount': value})

        budget_data['compensation_detail'] = compensation_detail
        budget_data['expense_detail'] = expense_detail

        return budget_data

    except Exception as e:
        print(f"  ✗ Error reading budget file: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_budget_visualizations(budget_data, fy_label):
    """Create Plotly visualizations for budget view"""

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Budget Overview',
            'Compensation Breakdown',
            'Academic Compensation Detail',
            'Non-Academic Compensation',
            'Current Expenses',
            'Graduate vs Undergraduate Programs'
        ),
        specs=[
            [{'type': 'pie'}, {'type': 'bar'}],
            [{'type': 'bar'}, {'type': 'bar'}],
            [{'type': 'bar'}, {'type': 'pie'}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )

    # 1. Budget Overview Pie
    fig.add_trace(
        go.Pie(
            labels=['Compensation', 'Current Expenses'],
            values=[budget_data['total_compensation'], budget_data['current_expenses']],
            marker=dict(colors=['#1e3c72', '#667eea']),
            hole=0.4,
            textinfo='label+percent+value',
            texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}'
        ),
        row=1, col=1
    )

    # 2. Compensation Breakdown
    fig.add_trace(
        go.Bar(
            x=['Academic', 'Non-Academic'],
            y=[budget_data['total_academic'], budget_data['total_non_academic']],
            marker=dict(color=['#2a5298', '#764ba2']),
            text=[f"${budget_data['total_academic']:,.0f}",
                  f"${budget_data['total_non_academic']:,.0f}"],
            textposition='outside'
        ),
        row=1, col=2
    )

    # 3. Academic Compensation Detail
    academic_cats = ['Standing Faculty', 'Practice/Lecture', 'Adjunct/PT']
    academic_vals = [
        budget_data['standing_faculty'],
        budget_data['practice_faculty'],
        budget_data['adjunct_faculty']
    ]
    fig.add_trace(
        go.Bar(
            x=academic_cats,
            y=academic_vals,
            marker=dict(color=['#1e3c72', '#2a5298', '#667eea']),
            text=[f"${v:,.0f}" for v in academic_vals],
            textposition='outside'
        ),
        row=2, col=1
    )

    # 4. Non-Academic Compensation (top categories from detail)
    comp_detail = sorted(budget_data['compensation_detail'],
                        key=lambda x: x['amount'], reverse=True)[:10]
    if comp_detail:
        fig.add_trace(
            go.Bar(
                x=[c['amount'] for c in comp_detail],
                y=[c['category'] for c in comp_detail],
                orientation='h',
                marker=dict(color='#764ba2'),
                text=[f"${c['amount']:,.0f}" for c in comp_detail],
                textposition='outside'
            ),
            row=2, col=2
        )

    # 5. Current Expenses (top categories)
    expense_detail = sorted(budget_data['expense_detail'],
                           key=lambda x: x['amount'], reverse=True)[:10]
    if expense_detail:
        fig.add_trace(
            go.Bar(
                x=[e['category'] for e in expense_detail],
                y=[e['amount'] for e in expense_detail],
                marker=dict(color='#667eea'),
                text=[f"${e['amount']:,.0f}" for e in expense_detail],
                textposition='outside'
            ),
            row=3, col=1
        )

    # 6. Grad vs Undergrad placeholder
    fig.add_trace(
        go.Pie(
            labels=['Graduate Programs', 'Undergraduate Programs'],
            values=[budget_data['grand_total'] * 0.3, budget_data['grand_total'] * 0.7],
            marker=dict(colors=['#2a5298', '#667eea']),
            hole=0.4,
            textinfo='label+percent'
        ),
        row=3, col=2
    )

    # Update layout
    fig.update_layout(
        title=dict(
            text=f'{fy_label} Master Budget - ${budget_data["grand_total"]:,.0f}',
            font=dict(size=24, color='#1e3c72')
        ),
        showlegend=False,
        height=1400,
        template='plotly_white'
    )

    # Update axes
    fig.update_xaxes(title_text="Category", row=2, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=2, col=1)
    fig.update_xaxes(title_text="Amount ($)", row=2, col=2)
    fig.update_xaxes(title_text="Category", row=3, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=3, col=1)

    return fig

def generate_budget_view(fy_data):
    """Generate budget-only view HTML"""

    year = fy_data['year']
    label = fy_data['label']
    master_file = fy_data['master_budget_file']

    print(f"\n{'='*80}")
    print(f"GENERATING BUDGET VIEW FOR {year}")
    print(f"{'='*80}")
    print(f"  Reading master budget: {Path(master_file).name}")

    # Extract budget data
    budget_data = extract_budget_from_master(master_file, year)
    if not budget_data:
        print(f"  ✗ Failed to extract budget data")
        return False

    print(f"  Budget total: ${budget_data['grand_total']:,.0f}")
    print(f"  Creating visualizations...")

    # Create visualizations
    fig = create_budget_visualizations(budget_data, label)

    # Generate HTML
    print(f"  Generating HTML...")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{label} - Master Budget</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }}
        .nav {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 15px 30px; color: white; display: flex; justify-content: space-between; align-items: center; }}
        .nav h1 {{ font-size: 1.5em; }}
        .nav-links {{ display: flex; gap: 15px; }}
        .nav-links a {{ color: white; text-decoration: none; padding: 8px 15px; border-radius: 5px; transition: background 0.3s; }}
        .nav-links a:hover {{ background: rgba(255,255,255,0.2); }}
        .nav-links a.active {{ background: rgba(255,255,255,0.3); }}
        .container {{ max-width: 1400px; margin: 30px auto; padding: 0 20px; }}
        .info-box {{ background: white; padding: 25px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .info-box h2 {{ color: #1e3c72; margin-bottom: 15px; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }}
        .info-item {{ background: #f8f9fa; padding: 15px; border-radius: 8px; }}
        .info-item h3 {{ color: #667eea; font-size: 0.9em; margin-bottom: 5px; }}
        .info-item p {{ color: #1e3c72; font-size: 1.4em; font-weight: bold; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="nav">
        <h1>📊 {label}</h1>
        <div class="nav-links">
            <a href="index.html">🏠 Home</a>
            <a href="{year.lower()}_budget.html" class="active">💰 Budget View</a>
            <a href="{year.lower()}_tracking.html">📈 Tracking</a>
        </div>
    </div>

    <div class="container">
        <div class="info-box">
            <h2>Master Budget Overview</h2>
            <p style="color: #666; margin-bottom: 20px;">{fy_data['period']}</p>
            <div class="info-grid">
                <div class="info-item">
                    <h3>Total Budget</h3>
                    <p>${budget_data['grand_total']:,.0f}</p>
                </div>
                <div class="info-item">
                    <h3>Total Compensation</h3>
                    <p>${budget_data['total_compensation']:,.0f}</p>
                </div>
                <div class="info-item">
                    <h3>Current Expenses</h3>
                    <p>${budget_data['current_expenses']:,.0f}</p>
                </div>
                <div class="info-item">
                    <h3>Academic Compensation</h3>
                    <p>${budget_data['total_academic']:,.0f}</p>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <div id="budget-charts"></div>
        </div>
    </div>

    <script>
        var data = {fig.to_json()};
        Plotly.newPlot('budget-charts', data.data, data.layout, {{responsive: true}});
    </script>
</body>
</html>"""

    # Save file
    output_file = f"{year.lower()}_budget.html"
    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"  ✓ Saved: {output_file}")
    return True

def generate_tracking_view(fy_data):
    """Generate tracking view HTML (placeholder for now)"""

    year = fy_data['year']
    label = fy_data['label']

    print(f"\n{'='*80}")
    print(f"GENERATING TRACKING VIEW FOR {year}")
    print(f"{'='*80}")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{label} - Budget Tracking</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }}
        .nav {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 15px 30px; color: white; display: flex; justify-content: space-between; align-items: center; }}
        .nav h1 {{ font-size: 1.5em; }}
        .nav-links {{ display: flex; gap: 15px; }}
        .nav-links a {{ color: white; text-decoration: none; padding: 8px 15px; border-radius: 5px; transition: background 0.3s; }}
        .nav-links a:hover {{ background: rgba(255,255,255,0.2); }}
        .nav-links a.active {{ background: rgba(255,255,255,0.3); }}
        .container {{ max-width: 1200px; margin: 50px auto; padding: 0 20px; text-align: center; }}
        .placeholder {{ background: white; padding: 60px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .placeholder h2 {{ color: #1e3c72; font-size: 2em; margin-bottom: 20px; }}
        .placeholder p {{ color: #666; font-size: 1.1em; line-height: 1.8; }}
    </style>
</head>
<body>
    <div class="nav">
        <h1>📊 {label}</h1>
        <div class="nav-links">
            <a href="index.html">🏠 Home</a>
            <a href="{year.lower()}_budget.html">💰 Budget View</a>
            <a href="{year.lower()}_tracking.html" class="active">📈 Tracking</a>
        </div>
    </div>

    <div class="container">
        <div class="placeholder">
            <h2>📈 Budget Tracking</h2>
            <p>Tracking view for {label} will be available once monthly reports are uploaded.</p>
            <p style="margin-top: 20px;">Upload monthly summary reports to track actual spending against the master budget.</p>
        </div>
    </div>
</body>
</html>"""

    output_file = f"{year.lower()}_tracking.html"
    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"  ✓ Saved: {output_file}")
    return True

def generate_home_page(fiscal_years, current_year):
    """Generate home page with all fiscal years"""

    print(f"\n{'='*80}")
    print("GENERATING HOME PAGE")
    print(f"{'='*80}")

    # Generate fiscal year cards
    fy_cards = ""
    for fy in fiscal_years:
        is_current = fy['year'] == current_year
        badge = '🟢 Active ⭐ Current' if is_current else '🟢 Active'

        fy_cards += f"""
        <div class="fy-card">
            <div class="fy-header">
                <h3>{fy['label']}</h3>
                <span class="badge">{badge}</span>
            </div>
            <p class="fy-period">{fy['period']}</p>
            <div class="fy-actions">
                <a href="{fy['year'].lower()}_budget.html" class="btn btn-budget">💰 View Budget</a>
                <a href="{fy['year'].lower()}_tracking.html" class="btn btn-tracking">📈 View Tracking</a>
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fine Arts Budget System - All Fiscal Years</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 50px 30px; text-align: center; }}
        .header h1 {{ font-size: 3em; margin-bottom: 15px; }}
        .header p {{ font-size: 1.2em; opacity: 0.9; }}
        .content {{ padding: 50px 30px; }}
        .intro {{ text-align: center; margin-bottom: 40px; }}
        .intro h2 {{ color: #1e3c72; margin-bottom: 15px; }}
        .intro p {{ color: #666; font-size: 1.1em; }}
        .fy-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 25px; margin: 40px 0; }}
        .fy-card {{ background: white; border: 3px solid #e0e0e0; border-radius: 10px; padding: 25px; transition: all 0.3s; }}
        .fy-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.15); border-color: #667eea; }}
        .fy-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
        .fy-header h3 {{ color: #1e3c72; font-size: 1.4em; }}
        .badge {{ background: #28a745; color: white; padding: 5px 12px; border-radius: 15px; font-size: 0.8em; font-weight: bold; }}
        .fy-period {{ color: #666; margin-bottom: 20px; font-size: 0.95em; }}
        .fy-actions {{ display: flex; gap: 10px; }}
        .btn {{ flex: 1; padding: 12px 20px; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; transition: all 0.3s; }}
        .btn-budget {{ background: #f0f7ff; color: #1e3c72; border: 2px solid #1e3c72; }}
        .btn-budget:hover {{ background: #1e3c72; color: white; }}
        .btn-tracking {{ background: #667eea; color: white; border: 2px solid #667eea; }}
        .btn-tracking:hover {{ background: #5568d3; transform: scale(1.02); }}
        .footer {{ background: #f8f9fa; padding: 30px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Fine Arts Budget System</h1>
            <p>Multi-Year Budget Management | All Fiscal Years</p>
            <p style="font-size: 0.9em; margin-top: 10px; opacity: 0.8;">Last Updated: February 16, 2026</p>
        </div>

        <div class="content">
            <div class="intro">
                <h2>Select a Fiscal Year</h2>
                <p>View budget details and track spending for any fiscal year below</p>
            </div>

            <div class="fy-grid">
                {fy_cards}
            </div>
        </div>

        <div class="footer">
            <p><strong>Fine Arts Multi-Year Budget System</strong></p>
            <p>School of Design | {len(fiscal_years)} Fiscal Years Available</p>
        </div>
    </div>
</body>
</html>"""

    with open('index.html', 'w') as f:
        f.write(html_content)

    print(f"  ✓ Saved: index.html")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_fiscal_year.py <FY26|all>")
        sys.exit(1)

    target = sys.argv[1].upper()

    # Load configuration
    with open('fiscal_years.json', 'r') as f:
        config = json.load(f)

    print("="*80)
    print("MULTI-YEAR BUDGET DASHBOARD GENERATOR")
    print("="*80)

    if target == 'ALL':
        # Generate for all fiscal years
        for fy in config['fiscal_years']:
            generate_budget_view(fy)
            generate_tracking_view(fy)

        # Generate home page
        generate_home_page(config['fiscal_years'], config['current_fiscal_year'])
    else:
        # Generate for specific fiscal year
        fy_data = next((fy for fy in config['fiscal_years'] if fy['year'] == target), None)
        if not fy_data:
            print(f"✗ Fiscal year {target} not found in configuration")
            sys.exit(1)

        generate_budget_view(fy_data)
        generate_tracking_view(fy_data)
        generate_home_page(config['fiscal_years'], config['current_fiscal_year'])

    print(f"\n{'='*80}")
    print("✓ GENERATION COMPLETE!")
    print("="*80)
    print("\nTo view: open index.html")

if __name__ == '__main__':
    main()
