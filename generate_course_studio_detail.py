#!/usr/bin/env python3
"""
Course/Studio Detailed Budget Breakdown
Shows detailed calculations and visualizations for each expense category
"""

import pandas as pd
from collections import Counter

def extract_course_data():
    """Extract course information from Sheet1"""
    file_path = '/Users/KLAW/project/budget/FY/fy26.xlsx'
    df = pd.read_excel(file_path, sheet_name='Sheet1', header=None)

    # Non-course annotation patterns to treat as notes instead of course codes
    NOTE_PATTERNS = ['$', 'Photo/Video Equipment Room']

    categories = {}
    category_notes = {}
    current_category = None

    for i in range(len(df)):
        col0 = df.iloc[i, 0]
        col1 = df.iloc[i, 1]
        col2 = df.iloc[i, 2] if df.shape[1] > 2 else None

        if pd.notna(col0):
            current_category = str(col0).strip()
            categories[current_category] = []
            category_notes[current_category] = []

        if pd.notna(col1) and current_category:
            entry = str(col1).strip()
            if not entry:
                continue
            # Check if it's a note/annotation rather than a course code
            if any(entry.startswith(pat) or entry == pat for pat in NOTE_PATTERNS):
                category_notes[current_category].append(entry)
            else:
                course_name = str(col2).strip() if col2 is not None and pd.notna(col2) else ''
                categories[current_category].append({
                    'code': entry,
                    'name': course_name
                })

    return categories, category_notes

def create_course_studio_detail():
    """Generate detailed Course/Studio budget breakdown page"""

    # Extract course data from Sheet1
    course_data, course_notes = extract_course_data()

    # Course/Studio budget data with detailed breakdowns
    budget_data = {
        'total': 104500.00,
        'categories': [
            {
                'name': 'Printmaking (0506)',
                'total': 10000.00,
                'description': 'Materials and supplies for printmaking courses',
                'breakdown': [],
                'notes': course_notes.get('Printmaking (0506)', []),
                'courses': course_data.get('Printmaking (0506)', [])
            },
            {
                'name': 'Visiting Lectures (0050)',
                'total': 12600.00,
                'description': 'Guest artist and critic visits',
                'breakdown': [
                    {'item': 'Visiting lecture payments', 'calculation': '$200/visitor × 63 courses'}
                ],
                'notes': course_notes.get('Visiting Lectures (0050)', []),
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
                'notes': course_notes.get('Senior Seminar (0592)', []),
                'courses': course_data.get('Senior Seminar (0592)', [])
            },
            {
                'name': 'Photography Instructional (0515)',
                'total': 2500.00,
                'description': 'Photography course materials',
                'breakdown': [],
                'notes': course_notes.get('Photography Instructional (0515)', []),
                'courses': course_data.get('Photography Instructional (0515)', [])
            },
            {
                'name': 'Animation Instructional (0511)',
                'total': 8400.00,
                'description': 'Animation software and materials',
                'breakdown': [],
                'notes': course_notes.get('Animation Instructional (0511)', []),
                'courses': course_data.get('Animation Instructional (0511)', [])
            },
            {
                'name': 'Digital Design (0513)',
                'total': 11950.00,
                'description': 'Digital design software and equipment',
                'breakdown': [],
                'notes': course_notes.get('Digital Design (0513)', []),
                'courses': course_data.get('Digital Design (0513)', [])
            },
            {
                'name': 'Drawing/Painting Instructional (0505)',
                'total': 10750.00,
                'description': 'Drawing and painting supplies',
                'breakdown': [],
                'notes': course_notes.get('Drawing/Painting Instructional (0505)', []),
                'courses': course_data.get('Drawing/Painting Instructional (0505)', [])
            },
            {
                'name': 'Sculpture Instructional (0507)',
                'total': 8400.00,
                'description': 'Sculpture materials and tools',
                'breakdown': [],
                'notes': course_notes.get('Sculpture Instructional (0507)', []),
                'courses': course_data.get('Sculpture Instructional (0507)', [])
            },
            {
                'name': 'Video Instructional (0509)',
                'total': 2000.00,
                'description': 'Video equipment and software',
                'breakdown': [],
                'notes': course_notes.get('Video Instructional (0509)', []),
                'courses': course_data.get('Video Instructional (0509)', [])
            },
            {
                'name': 'Photography Consumables (0569)',
                'total': 22500.00,
                'description': 'Photography chemicals, paper, and consumables',
                'breakdown': [],
                'notes': course_notes.get('Photography Consumables (0569)', []),
                'courses': course_data.get('Photography Consumables (0569)', [])
            }
        ]
    }

    # No bar chart visualization — removed per user request

    # Generate detailed breakdown HTML for each category
    categories_html = ""
    for cat in budget_data['categories']:
        # Breakdown section
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

        # Notes section (non-course annotations from Sheet1, e.g. "$200 / visit")
        notes_html = ""
        if cat.get('notes'):
            for note in cat['notes']:
                notes_html += f"<div class='category-note'>{note}</div>"

        # Courses section — count sections per unique course, preserve first-seen order
        section_counts = Counter((c['code'], c['name']) for c in cat['courses'])
        seen = set()
        unique_courses = []
        for c in cat['courses']:
            key = (c['code'], c['name'])
            if key not in seen:
                seen.add(key)
                unique_courses.append(c)

        total_sections = sum(section_counts.values())
        courses_html = ""
        if unique_courses:
            section_label = f"{total_sections} section{'s' if total_sections != 1 else ''}"
            courses_html = f"<div class='courses-section'><h4>Courses Supported <span class='section-count'>({section_label})</span></h4><div class='courses-list'>"
            for course in unique_courses:
                key = (course['code'], course['name'])
                count = section_counts[key]
                course_display = course['code']
                if course['name']:
                    course_display += f" — {course['name']}"
                section_badge = f"<span class='section-badge'>{count} section{'s' if count != 1 else ''}</span>"
                courses_html += f"<div class='course-item'><span class='course-name'>{course_display}</span>{section_badge}</div>"
            courses_html += "</div></div>"

        categories_html += f"""
        <div class='category-card'>
            <div class='category-header'>
                <h3>{cat['name']}</h3>
                <div class='category-total'>${cat['total']:,.2f}</div>
            </div>
            <p class='category-description'>{cat['description']}</p>
            {notes_html}
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

        .categories-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 30px; }}

        .category-card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 25px; border-left: 4px solid #4a90e2; }}
        .category-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; gap: 10px; }}
        .category-header h3 {{ color: #4a90e2; font-size: 1.2em; }}
        .category-total {{ color: #50c878; font-size: 1.3em; font-weight: bold; white-space: nowrap; }}
        .category-description {{ color: #999; font-size: 0.95em; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #333; }}
        .category-note {{ color: #f0a500; font-size: 0.9em; margin-bottom: 8px; padding: 6px 10px; background: #2a2000; border-radius: 4px; border-left: 3px solid #f0a500; }}

        .breakdown-list {{ margin-top: 15px; margin-bottom: 15px; }}
        .breakdown-item {{ padding: 10px; background: #252525; margin-bottom: 8px; border-radius: 6px; }}
        .breakdown-name {{ color: #e0e0e0; font-weight: 600; margin-bottom: 4px; }}
        .breakdown-calc {{ color: #4a90e2; font-size: 0.9em; }}

        .courses-section {{ margin-top: 15px; }}
        .courses-section h4 {{ color: #50c878; font-size: 1em; margin-bottom: 10px; }}
        .section-count {{ color: #888; font-weight: normal; font-size: 0.9em; }}
        .courses-list {{ display: grid; gap: 6px; }}
        .course-item {{ display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 8px 12px; background: #252525; border-radius: 4px; color: #e0e0e0; font-size: 0.9em; border-left: 3px solid #50c878; }}
        .course-name {{ flex: 1; }}
        .section-badge {{ background: #1a3a1a; color: #50c878; font-size: 0.8em; padding: 2px 8px; border-radius: 10px; white-space: nowrap; border: 1px solid #2a5a2a; }}

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

        <h2 style="color: #4a90e2; margin: 0 0 20px 0; font-size: 1.8em;">Detailed Category Breakdown</h2>

        <div class="categories-grid">
            {categories_html}
        </div>
    </div>

    <div class="footer">
        <p><strong>Course/Studio Budget Analysis</strong></p>
        <p>Fine Arts Department | Fiscal Year 2026</p>
    </div>

</body>
</html>"""

    # Save file
    with open('course_studio_detail.html', 'w') as f:
        f.write(html_content)

    print("✓ Saved: course_studio_detail.html")
    print("\nTo view: open course_studio_detail.html")

if __name__ == '__main__':
    create_course_studio_detail()
