#!/usr/bin/env python3
"""
Course/Studio Detailed Budget Breakdown
Shows detailed calculations and visualizations for each expense category
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def extract_course_data():
    """Extract course information from Sheet1"""
    file_path = '/Users/KLAW/project/budget/FY/fy26.xlsx'
    df = pd.read_excel(file_path, sheet_name='Sheet1', header=None)

    categories = {}
    current_category = None

    for i in range(len(df)):
        col0 = df.iloc[i, 0]
        col1 = df.iloc[i, 1]
        col3 = df.iloc[i, 3]

        if pd.notna(col0):
            current_category = str(col0).strip()
            categories[current_category] = []

        if pd.notna(col1) and current_category:
            course_code = str(col1).strip()
            course_name = str(col3).strip() if pd.notna(col3) else ''
            if course_code:
                categories[current_category].append({
                    'code': course_code,
                    'name': course_name
                })

    return categories

def create_course_studio_detail():
    """Generate detailed Course/Studio budget breakdown page"""

    # Extract course data from Sheet1
    course_data = extract_course_data()

    # Course/Studio budget data with detailed breakdowns
    budget_data = {
        'total': 104500.00,
        'categories': [
            {
                'name': 'Printmaking (0506)',
                'total': 10000.00,
                'description': 'Materials and supplies for printmaking courses',
                'breakdown': [],
                'courses': course_data.get('Printmaking (0506)', [])
            },
            {
                'name': 'Visiting Lectures (0050)',
                'total': 12600.00,
                'description': 'Guest artist and critic visits',
                'breakdown': [
                    {'item': 'Visiting lecture payments', 'calculation': '$200/visitor × 63 courses'}
                ],
                'courses': course_data.get('Visiting Lectures (0050)', [])
            },
            {
                'name': 'Senior Seminar (0592)',
                'total': 15400.00,
                'description': 'Senior thesis support and programming',
                'breakdown': [
                    {'item': 'Alumni panels', 'calculation': '2 panels'},
                    {'item': 'Thesis exhibition support', 'calculation': 'Installation and materials'},
                    {'item': 'Senior thesis development', 'calculation': '$100/semester per senior'},
                    {'item': 'Senior seminar field trips', 'calculation': 'Transportation and visits'},
                    {'item': 'Catalog production and printing', 'calculation': 'Design and printing'}
                ],
                'courses': course_data.get('Senior Seminar (0592)', [])
            },
            {
                'name': 'Photography Instructional (0515)',
                'total': 2500.00,
                'description': 'Photography course materials',
                'breakdown': [],
                'courses': course_data.get('Photography Instructional (0515)', [])
            },
            {
                'name': 'Animation Intructional (0511)',
                'total': 8400.00,
                'description': 'Animation software and materials',
                'breakdown': [],
                'courses': course_data.get('Animation Intructional (0511)', [])
            },
            {
                'name': 'Digital Design Intructional (0513)',
                'total': 11950.00,
                'description': 'Digital design software and equipment',
                'breakdown': [],
                'courses': course_data.get('Digital Design Intructional (0513)', [])
            },
            {
                'name': 'Drawing/Painting Instructional  (0505)',
                'total': 10750.00,
                'description': 'Drawing and painting supplies',
                'breakdown': [],
                'courses': course_data.get('Drawing/Painting Instructional  (0505)', [])
            },
            {
                'name': 'Sculpture Instructional (0507)',
                'total': 8400.00,
                'description': 'Sculpture materials and tools',
                'breakdown': [],
                'courses': course_data.get('Sculpture Instructional (0507)', [])
            },
            {
                'name': 'Video Instructional (0509)',
                'total': 2000.00,
                'description': 'Video equipment and software',
                'breakdown': [],
                'courses': course_data.get('Video Instructional (0509)', [])
            },
            {
                'name': 'Photography Consumables (0569)',
                'total': 22500.00,
                'description': 'Photography chemicals, paper, and consumables',
                'breakdown': [],
                'courses': course_data.get('Photography Consumables (0569)', [])
            }
        ]
    }

    # Create visualizations (bar charts only)
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            'Top 5 Expense Categories',
            'Instructional Supplies Overview'
        ),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]],
        horizontal_spacing=0.15
    )

    # 1. Top 5 bar chart
    sorted_cats = sorted(budget_data['categories'], key=lambda x: x['total'], reverse=True)[:5]

    fig.add_trace(
        go.Bar(
            x=[cat['name'].split('(')[0].strip() for cat in sorted_cats],
            y=[cat['total'] for cat in sorted_cats],
            marker=dict(color='#4a90e2'),
            text=[f"${cat['total']:,.0f}" for cat in sorted_cats],
            textposition='outside',
            hovertemplate='%{x}<br>$%{y:,.2f}<extra></extra>',
            textfont=dict(color='white')
        ),
        row=1, col=1
    )

    # 2. Instructional supplies bar
    instructional = [cat for cat in budget_data['categories'] if 'Instructional' in cat['name'] or 'Consumables' in cat['name']]

    fig.add_trace(
        go.Bar(
            x=[cat['name'].split('(')[0].strip() for cat in instructional],
            y=[cat['total'] for cat in instructional],
            marker=dict(color='#50c878'),
            text=[f"${cat['total']:,.0f}" for cat in instructional],
            textposition='outside',
            hovertemplate='%{x}<br>$%{y:,.2f}<extra></extra>',
            textfont=dict(color='white')
        ),
        row=1, col=2
    )

    # Update layout
    fig.update_layout(
        title=dict(
            text='Course/Studio Budget Overview',
            font=dict(size=22, color='white'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=False,
        height=500,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a'
    )

    # Update axes
    fig.update_xaxes(showgrid=False, color='white', tickangle=-45)
    fig.update_yaxes(showgrid=True, gridcolor='#333', color='white', title_text="Budget ($)")

    # Generate detailed breakdown HTML for each category
    categories_html = ""
    for cat in budget_data['categories']:
        # Breakdown section (without dollar amounts)
        breakdown_html = ""
        if cat['breakdown']:
            breakdown_html = "<div class='breakdown-list'>"
            for item in cat['breakdown']:
                breakdown_html += f"""
                <div class='breakdown-item'>
                    <div class='breakdown-name'>{item['item']}</div>
                    <div class='breakdown-calc'>{item['calculation']}</div>
                </div>
                """
            breakdown_html += "</div>"

        # Courses section
        courses_html = ""
        if cat['courses']:
            courses_html = "<div class='courses-section'><h4>Courses Supported:</h4><div class='courses-list'>"
            for course in cat['courses']:
                course_display = f"{course['code']}"
                if course['name']:
                    course_display += f" - {course['name']}"
                courses_html += f"<div class='course-item'>{course_display}</div>"
            courses_html += "</div></div>"

        categories_html += f"""
        <div class='category-card'>
            <div class='category-header'>
                <h3>{cat['name']}</h3>
            </div>
            <p class='category-description'>{cat['description']}</p>
            {breakdown_html}
            {courses_html}
        </div>
        """

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course/Studio Budget Detail - FY26</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d0d0d; color: #e0e0e0; }}

        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 40px 30px; color: white; border-bottom: 3px solid #4a90e2; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .header .back-link {{ display: inline-block; margin-top: 15px; padding: 10px 20px; background: #4a90e2; color: white; text-decoration: none; border-radius: 5px; transition: background 0.3s; }}
        .header .back-link:hover {{ background: #357abd; }}

        .container {{ max-width: 1400px; margin: 30px auto; padding: 0 20px; }}

        .summary-box {{ background: #1a1a1a; padding: 30px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #333; text-align: center; }}
        .summary-box h2 {{ color: #4a90e2; font-size: 2em; margin-bottom: 10px; }}
        .summary-box .total {{ color: #50c878; font-size: 3em; font-weight: bold; }}

        .chart-container {{ background: #1a1a1a; padding: 30px; border-radius: 10px; border: 1px solid #333; margin-bottom: 30px; }}

        .categories-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 30px; }}

        .category-card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 25px; border-left: 4px solid #4a90e2; }}
        .category-header {{ margin-bottom: 15px; }}
        .category-header h3 {{ color: #4a90e2; font-size: 1.2em; }}
        .category-description {{ color: #999; font-size: 0.95em; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #333; }}

        .breakdown-list {{ margin-top: 15px; margin-bottom: 15px; }}
        .breakdown-item {{ padding: 10px; background: #252525; margin-bottom: 8px; border-radius: 6px; }}
        .breakdown-name {{ color: #e0e0e0; font-weight: 600; margin-bottom: 4px; }}
        .breakdown-calc {{ color: #4a90e2; font-size: 0.9em; }}

        .courses-section {{ margin-top: 15px; }}
        .courses-section h4 {{ color: #50c878; font-size: 1em; margin-bottom: 10px; }}
        .courses-list {{ display: grid; gap: 6px; }}
        .course-item {{ padding: 8px 12px; background: #252525; border-radius: 4px; color: #e0e0e0; font-size: 0.9em; border-left: 3px solid #50c878; }}

        .footer {{ text-align: center; padding: 30px; color: #666; margin-top: 40px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Course/Studio Budget Detail</h1>
        <p>Fiscal Year 2026 | Detailed Breakdown & Course Information</p>
        <a href="fy26_budget.html" class="back-link">← Back to Main Budget</a>
    </div>

    <div class="container">
        <div class="summary-box">
            <h2>Total Course/Studio Budget</h2>
            <div class="total">$104,500.00</div>
            <p style="color: #999; margin-top: 10px;">Supporting {len(budget_data['categories'])} instructional categories</p>
        </div>

        <div class="chart-container">
            <div id="visualizations"></div>
        </div>

        <h2 style="color: #4a90e2; margin: 30px 0 20px 0; font-size: 1.8em;">Detailed Category Breakdown</h2>

        <div class="categories-grid">
            {categories_html}
        </div>
    </div>

    <div class="footer">
        <p><strong>Course/Studio Budget Analysis</strong></p>
        <p>Fine Arts Department | Fiscal Year 2026</p>
    </div>

    <script>
        var data = {fig.to_json()};
        Plotly.newPlot('visualizations', data.data, data.layout, {{responsive: true}});
    </script>
</body>
</html>"""

    # Save file
    with open('course_studio_detail.html', 'w') as f:
        f.write(html_content)

    print("✓ Saved: course_studio_detail.html")
    print("\nTo view: open course_studio_detail.html")

if __name__ == '__main__':
    create_course_studio_detail()
