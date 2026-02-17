#!/usr/bin/env python3
"""
FY26 Budget Dashboard Generator
Dark mode with tabbed view for Compensation and Current Expenses
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if pd.isna(value):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        import re
        cleaned = re.sub(r'[^\d\.\-]', '', str(value))
        try:
            return float(cleaned) if cleaned else default
        except:
            return default
    return default

def extract_budget_data():
    """Extract FY26 budget data from Excel file"""

    file_path = '/Users/KLAW/project/budget/FY/fy26.xlsx'

    # Column U is index 20
    budget_col = 20

    print("Reading FA_Summary sheet (column U)...")
    df_summary = pd.read_excel(file_path, sheet_name='FA_Summary', header=None)

    # Extract budget info from column U
    budget_data = {
        'total_budget': 4241604.00,
        'total_compensation': 3879484.00,
        'standing_faculty': safe_float(df_summary.iloc[10, budget_col]),
        'other_fulltime_faculty': safe_float(df_summary.iloc[11, budget_col]),
        'parttime_faculty': safe_float(df_summary.iloc[12, budget_col]),
        'total_academic': safe_float(df_summary.iloc[15, budget_col]),
    }

    # Non-academic compensation without benefits
    # Total Non-Academic Comp (Row 42) - Non-Academic Benefits (Row 40)
    total_nonacademic = safe_float(df_summary.iloc[41, budget_col])
    nonacademic_benefits = safe_float(df_summary.iloc[39, budget_col])
    budget_data['nonacademic_compensation'] = total_nonacademic - nonacademic_benefits

    # Faculty counts
    budget_data['standing_faculty_count'] = 7
    budget_data['other_fulltime_count'] = 10
    budget_data['parttime_count'] = 45

    # Current expenses from FA_Summary sheet
    total_current_expense = safe_float(df_summary.iloc[110, budget_col])
    budget_data['current_expenses'] = total_current_expense

    # Graduate and Undergraduate totals
    budget_data['graduate_total'] = safe_float(df_summary.iloc[111, budget_col])
    budget_data['undergraduate_total'] = safe_float(df_summary.iloc[112, budget_col])

    print(f"Total Current Expense: ${budget_data['current_expenses']:,.2f}")
    print(f"Graduate total: ${budget_data['graduate_total']:,.2f}")
    print(f"Undergraduate total: ${budget_data['undergraduate_total']:,.2f}")

    # Read CE_Breakdown for subcategories
    df_ce = pd.read_excel(file_path, sheet_name='CE_Breakdown', header=None)

    # Extract Chair Expenses subcategories (rows 24-26, column Q)
    # Column Q is index 16
    chair_subcats = []
    for i in range(23, 27):  # Rows 24-27
        subcat_name = df_ce.iloc[i, 1]  # Column B
        subcat_value = safe_float(df_ce.iloc[i, 16])  # Column Q
        if pd.notna(subcat_name) and subcat_value > 0:
            chair_subcats.append({'name': str(subcat_name), 'amount': subcat_value})

    # Extract Course/Studio subcategories (rows 30-39, column Q)
    course_studio_subcats = []
    for i in range(29, 40):  # Rows 30-40
        subcat_name = df_ce.iloc[i, 1]  # Column B
        subcat_value = safe_float(df_ce.iloc[i, 16])  # Column Q
        if pd.notna(subcat_name) and subcat_value > 0:
            course_studio_subcats.append({'name': str(subcat_name), 'amount': subcat_value})

    # Extract Departmental Events subcategories (rows 64-68, column Q)
    dept_events_subcats = []
    for i in range(63, 69):  # Rows 64-69
        subcat_name = df_ce.iloc[i, 1]  # Column B
        subcat_value = safe_float(df_ce.iloc[i, 16])  # Column Q
        if pd.notna(subcat_name) and subcat_value > 0:
            dept_events_subcats.append({'name': str(subcat_name), 'amount': subcat_value})

    # Undergraduate expense categories
    ce_categories = [
        {'category': 'Chair Expenses', 'amount': 10000.00, 'subcategories': chair_subcats},
        {'category': 'Course/Studio Expenses', 'amount': safe_float(df_summary.iloc[66, budget_col]), 'subcategories': course_studio_subcats},
        {'category': 'Department Administrative', 'amount': safe_float(df_summary.iloc[74, budget_col]), 'subcategories': []},
        {'category': 'Departmental Events', 'amount': safe_float(df_summary.iloc[78, budget_col]), 'subcategories': dept_events_subcats},
        {'category': 'Promotion of Department', 'amount': safe_float(df_summary.iloc[98, budget_col]), 'subcategories': []}
    ]

    budget_data['ce_categories'] = [cat for cat in ce_categories if cat['amount'] > 0]

    return budget_data

def create_compensation_chart(budget_data):
    """Create compensation pie chart"""

    fig = go.Figure()

    # Compensation Overview Pie
    labels = ['Standing Faculty', 'Other Fulltime Faculty', 'Part-Time Faculty']
    values = [
        budget_data['standing_faculty'],
        budget_data['other_fulltime_faculty'],
        budget_data['parttime_faculty']
    ]

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=['#4a90e2', '#50c878', '#9b59b6']),
            hole=0.4,
            textinfo='label+percent',
            texttemplate='%{label}<br>%{percent}<br>$%{value:,.2f}',
            hovertemplate='%{label}<br>$%{value:,.2f}<extra></extra>',
            textfont=dict(color='white', size=12)
        )
    )

    fig.update_layout(
        title=dict(
            text='Academic Compensation by Faculty Type',
            font=dict(size=20, color='white'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        legend=dict(
            font=dict(color='white', size=12),
            bgcolor='rgba(0,0,0,0)'
        ),
        height=500,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a'
    )

    return fig

def create_expense_chart(budget_data):
    """Create current expense pie chart"""

    fig = go.Figure()

    # Graduate vs Undergraduate Pie
    fig.add_trace(
        go.Pie(
            labels=['Graduate', 'Undergraduate'],
            values=[budget_data['graduate_total'], budget_data['undergraduate_total']],
            marker=dict(colors=['#e74c3c', '#3498db']),
            hole=0.4,
            textinfo='label+percent',
            texttemplate='%{label}<br>%{percent}<br>$%{value:,.2f}',
            hovertemplate='%{label}<br>$%{value:,.2f}<extra></extra>',
            textfont=dict(color='white', size=12)
        )
    )

    fig.update_layout(
        title=dict(
            text='Graduate vs Undergraduate Expenses',
            font=dict(size=20, color='white'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        legend=dict(
            font=dict(color='white', size=12),
            bgcolor='rgba(0,0,0,0)'
        ),
        height=500,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a'
    )

    return fig

def generate_fy26_budget():
    """Generate FY26 budget view HTML with tabs"""

    print("="*80)
    print("GENERATING FY26 BUDGET VIEW")
    print("="*80)

    # Extract budget data
    budget_data = extract_budget_data()

    print(f"\nBudget Summary:")
    print(f"  Total Budget: ${budget_data['total_budget']:,.2f}")
    print(f"  Total Compensation: ${budget_data['total_compensation']:,.2f}")
    print(f"  Current Expenses: ${budget_data['current_expenses']:,.2f}")

    # Create visualizations
    print("\nCreating visualizations...")
    comp_fig = create_compensation_chart(budget_data)
    expense_fig = create_expense_chart(budget_data)

    # Generate expense categories HTML
    expense_list_html = ""
    for cat in budget_data['ce_categories']:
        # Add link to Course/Studio detail page
        if cat['category'] == 'Course/Studio Expenses':
            expense_list_html += f"""
        <div class="expense-item expense-item-clickable" onclick="window.location='course_studio_detail.html'">
            <span class="expense-label">{cat['category']} <span style="font-size: 0.8em; color: #4a90e2;">→ View Details</span></span>
            <span class="expense-amount">${cat['amount']:,.2f}</span>
        </div>
        """
        else:
            expense_list_html += f"""
        <div class="expense-item">
            <span class="expense-label">{cat['category']}</span>
            <span class="expense-amount">${cat['amount']:,.2f}</span>
        </div>
        """

        # Add subcategories if they exist
        if cat.get('subcategories'):
            for subcat in cat['subcategories']:
                if isinstance(subcat, dict):
                    # Subcategory with amount
                    expense_list_html += f"""
        <div class="expense-subitem">
            <span class="expense-sublabel">• {subcat['name']}</span>
            <span class="expense-subamount">${subcat['amount']:,.2f}</span>
        </div>
        """
                else:
                    # Subcategory without amount (legacy)
                    expense_list_html += f"""
        <div class="expense-subitem">
            <span class="expense-sublabel">• {subcat}</span>
        </div>
        """

    # Generate HTML with tabs
    print("Generating HTML...")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26 Budget - Fine Arts</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d0d0d; color: #e0e0e0; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 40px 30px; color: white; text-align: center; border-bottom: 3px solid #4a90e2; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .container {{ max-width: 1400px; margin: 30px auto; padding: 0 20px; }}

        /* Tabs */
        .tabs {{ display: flex; gap: 10px; margin-bottom: 30px; }}
        .tab {{ padding: 15px 30px; background: #1a1a1a; border: 2px solid #333; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: bold; color: #999; transition: all 0.3s; }}
        .tab:hover {{ background: #2a2a2a; color: #fff; }}
        .tab.active {{ background: #4a90e2; color: white; border-color: #4a90e2; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        .info-box {{ background: #1a1a1a; padding: 30px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #333; }}
        .info-box h2 {{ color: #4a90e2; margin-bottom: 20px; font-size: 1.8em; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }}
        .info-item {{ background: #252525; padding: 20px; border-radius: 8px; border-left: 4px solid #4a90e2; }}
        .info-item h3 {{ color: #4a90e2; font-size: 0.9em; margin-bottom: 8px; text-transform: uppercase; }}
        .info-item p {{ color: #fff; font-size: 1.6em; font-weight: bold; }}
        .info-item .count {{ color: #50c878; font-size: 0.9em; margin-top: 5px; }}

        .chart-container {{ background: #1a1a1a; padding: 30px; border-radius: 10px; border: 1px solid #333; margin-bottom: 30px; }}

        .expense-list {{ background: #1a1a1a; padding: 30px; border-radius: 10px; border: 1px solid #333; }}
        .expense-item {{ display: flex; justify-content: space-between; padding: 15px 20px; background: #252525; margin-bottom: 12px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .expense-item-clickable {{ cursor: pointer; transition: all 0.3s; }}
        .expense-item-clickable:hover {{ background: #2a2a2a; transform: translateX(5px); border-left-color: #4a90e2; }}
        .expense-label {{ color: #e0e0e0; font-size: 1.1em; }}
        .expense-amount {{ color: #50c878; font-size: 1.2em; font-weight: bold; }}
        .expense-subitem {{ display: flex; justify-content: space-between; padding: 8px 20px 8px 40px; background: #1f1f1f; margin-bottom: 6px; border-radius: 4px; border-left: 2px solid #666; }}
        .expense-sublabel {{ color: #999; font-size: 0.95em; }}
        .expense-subamount {{ color: #3498db; font-size: 1em; font-weight: 600; }}

        .footer {{ text-align: center; padding: 30px; color: #666; margin-top: 40px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Fiscal Year 2026 Master Budget</h1>
        <p>July 1, 2025 - June 30, 2026 | Fine Arts Department</p>
    </div>

    <div class="container">
        <div class="info-box">
            <h2>Budget Overview</h2>
            <div class="info-grid">
                <div class="info-item">
                    <h3>Total Budget</h3>
                    <p>${budget_data['total_budget']:,.2f}</p>
                </div>
                <div class="info-item">
                    <h3>Total Compensation</h3>
                    <p>${budget_data['total_compensation']:,.2f}</p>
                </div>
                <div class="info-item">
                    <h3>Current Expenses</h3>
                    <p>${budget_data['current_expenses']:,.2f}</p>
                </div>
            </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('compensation')">💼 Compensation</div>
            <div class="tab" onclick="switchTab('expenses')">💰 Current Expenses</div>
        </div>

        <!-- Compensation Tab -->
        <div id="compensation-tab" class="tab-content active">
            <div class="info-box">
                <h2>Academic Compensation by Faculty Type</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <h3>Standing Faculty</h3>
                        <p>${budget_data['standing_faculty']:,.2f}</p>
                        <p class="count">{budget_data['standing_faculty_count']} faculty members</p>
                    </div>
                    <div class="info-item">
                        <h3>Other Fulltime Faculty</h3>
                        <p>${budget_data['other_fulltime_faculty']:,.2f}</p>
                        <p class="count">{budget_data['other_fulltime_count']} faculty members</p>
                    </div>
                    <div class="info-item">
                        <h3>Part-Time Faculty</h3>
                        <p>${budget_data['parttime_faculty']:,.2f}</p>
                        <p class="count">{budget_data['parttime_count']} faculty members</p>
                    </div>
                    <div class="info-item">
                        <h3>Total Academic</h3>
                        <p>${budget_data['total_academic']:,.2f}</p>
                        <p class="count">{budget_data['standing_faculty_count'] + budget_data['other_fulltime_count'] + budget_data['parttime_count']} total faculty</p>
                    </div>
                </div>
            </div>

            <div class="info-box">
                <h2>Non-Academic Compensation</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <h3>Total Non-Academic Compensation</h3>
                        <p>${budget_data['nonacademic_compensation']:,.2f}</p>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div id="compensation-chart"></div>
            </div>
        </div>

        <!-- Current Expenses Tab -->
        <div id="expenses-tab" class="tab-content">
            <div class="info-box">
                <h2>Graduate vs Undergraduate</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <h3>Graduate Total</h3>
                        <p>${budget_data['graduate_total']:,.2f}</p>
                    </div>
                    <div class="info-item">
                        <h3>Undergraduate Total</h3>
                        <p>${budget_data['undergraduate_total']:,.2f}</p>
                    </div>
                    <div class="info-item">
                        <h3>Total Current Expense</h3>
                        <p>${budget_data['current_expenses']:,.2f}</p>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div id="expense-chart"></div>
            </div>

            <div class="info-box">
                <h2>Undergraduate Expense Categories</h2>
            </div>

            <div class="expense-list">
                {expense_list_html}
            </div>
        </div>
    </div>

    <div class="footer">
        <p><strong>Fine Arts Department Budget System</strong></p>
        <p>Fiscal Year 2026 | Generated on February 16, 2026</p>
    </div>

    <script>
        var compData = {comp_fig.to_json()};
        var expenseData = {expense_fig.to_json()};

        Plotly.newPlot('compensation-chart', compData.data, compData.layout, {{responsive: true}});
        Plotly.newPlot('expense-chart', expenseData.data, expenseData.layout, {{responsive: true}});

        function switchTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});

            // Show selected tab
            if (tabName === 'compensation') {{
                document.getElementById('compensation-tab').classList.add('active');
                document.querySelectorAll('.tab')[0].classList.add('active');
            }} else if (tabName === 'expenses') {{
                document.getElementById('expenses-tab').classList.add('active');
                document.querySelectorAll('.tab')[1].classList.add('active');
            }}
        }}
    </script>
</body>
</html>"""

    # Save file
    with open('fy26_budget.html', 'w') as f:
        f.write(html_content)

    print("\n✓ Saved: fy26_budget.html")
    print("\nTo view: open fy26_budget.html")

if __name__ == '__main__':
    generate_fy26_budget()
