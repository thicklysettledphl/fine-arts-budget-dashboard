#!/usr/bin/env python3
"""
FY26 Budget Tracking Page Generator
Reads the most recent file from ~/project/budget/FY/tracking/
and generates fy26_tracking.html
"""

import pandas as pd
import json
import re
import glob
import os
from pathlib import Path

TRACKING_DIR = Path('/Users/KLAW/project/budget/FY/tracking')


def find_latest_file():
    """Return the most recently modified xlsx in the tracking directory."""
    files = sorted(
        [f for f in TRACKING_DIR.glob('*.xlsx') if not f.name.startswith('~')],
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    if not files:
        raise FileNotFoundError(f"No .xlsx files found in {TRACKING_DIR}")
    return files[0]


def safe_float(v, default=0.0):
    if pd.isna(v):
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def safe_str(v):
    s = str(v).strip()
    return '' if s == 'nan' else s


def parse_tracking_file(path):
    """
    Parse the Monthly Department Summary sheet.
    Returns a structured dict with all key sections.
    """
    df = pd.read_excel(path, sheet_name='Monthly Department Summary', header=None)

    # Column indices: 5=Budget, 6=FYTD Actuals, 7=Committed, 8=Available, 9=% used
    B, A, C, AV, PCT = 5, 6, 7, 8, 9

    def row(i):
        """Return dict for row i (0-indexed)."""
        return {
            'label':     safe_str(df.iloc[i, 4]) if df.shape[1] > 4 else '',
            'cat':       safe_str(df.iloc[i, 3]) if df.shape[1] > 3 else '',
            'section':   safe_float(df.iloc[i, 2]) if df.shape[1] > 2 else 0,
            'fund':      safe_str(df.iloc[i, 1]) if df.shape[1] > 1 else '',
            'budget':    safe_float(df.iloc[i, B]) if df.shape[1] > B else 0,
            'actuals':   safe_float(df.iloc[i, A]) if df.shape[1] > A else 0,
            'committed': safe_float(df.iloc[i, C]) if df.shape[1] > C else 0,
            'available': safe_float(df.iloc[i, AV]) if df.shape[1] > AV else 0,
        }

    # ── Detect report period from row 2 ──────────────────────────────────────
    period = safe_str(df.iloc[1, 0])

    # ── Subtotals rows (search by label) ─────────────────────────────────────
    def find_row(label_col, pattern, start=0):
        """Find first row where column label_col matches pattern (case-insensitive)."""
        for i in range(start, len(df)):
            v = safe_str(df.iloc[i, label_col])
            if pattern.lower() in v.lower():
                return i
        return None

    academic_row    = find_row(4, 'Academic Salaries')
    nonacademic_row = find_row(4, 'Non-Academic Salaries')
    ce_total_row    = find_row(0, 'Subtotal - Current Expense')
    total_exp_row   = find_row(0, 'TOTAL EXPENDITURES')

    academic    = row(academic_row)    if academic_row    is not None else {}
    nonacademic = row(nonacademic_row) if nonacademic_row is not None else {}
    ce_total    = row(ce_total_row)    if ce_total_row    is not None else {}
    total_exp   = row(total_exp_row)   if total_exp_row   is not None else {}

    # ── UG current expense categories (section subtotals) ────────────────────
    # Identified by rows where col2 has a section number and col1 = 'F A UNDERGRAD'
    # and col0 is blank (subtotal rows)
    ug_cats = []
    grad_cats = []

    cat_map = {
        '50.0':  'Studios/Courses',
        '54.0':  'Chair Expenses',
        '55.0':  'Department Administrative',
        '56.0':  'Admissions & Recruitment',
        '58.0':  'Promotion of Department',
        '61.0':  'Departmental Events',
        '62.0':  'Lecture Series',
        '503.0': 'Exhibitions',
        '505.0': 'Painting/Drawing',
        '506.0': 'Printmaking',
        '507.0': 'Sculpture',
        '509.0': 'Video',
        '511.0': 'Animation',
        '513.0': 'Digital Design',
        '515.0': 'Photography Instructional',
        '548.0': 'MFA Thesis Exhibition',
        '561.0': 'MFA Senior Critics',
        '562.0': 'MFA Reviews',
        '565.0': 'MFA Workshops',
        '569.0': 'Photography Consumables',
        '592.0': 'Senior Seminar',
    }

    for i in range(len(df)):
        c0 = safe_str(df.iloc[i, 0])
        c1 = safe_str(df.iloc[i, 1])
        c2 = safe_str(df.iloc[i, 2])
        # Subtotal rows have blank c0, section number in c2, no line item label in c4
        if c0 == '' and c2 and c2 != '' and safe_str(df.iloc[i, 4]) == '':
            section_key = c2 if c2.endswith('.0') else c2 + '.0'
            name = cat_map.get(section_key, f'Section {c2}')
            r = row(i)
            r['name'] = name
            r['section_code'] = c2

            # Determine if UG or Grad based on nearby fund column
            if 'UNDERGRAD' in c1.upper() or 'UGRAD' in c1.upper():
                ug_cats.append(r)
            elif 'GRADUATE' in c1.upper() or 'GRAD' in c1.upper():
                grad_cats.append(r)
            elif c1 == '':
                # Look above for fund context
                for look in range(i - 1, max(i - 10, -1), -1):
                    fc = safe_str(df.iloc[look, 1])
                    if 'UNDERGRAD' in fc.upper() or 'UGRAD' in fc.upper():
                        ug_cats.append(r)
                        break
                    elif 'GRADUATE' in fc.upper() or 'GRAD' in fc.upper():
                        grad_cats.append(r)
                        break

    # ── UG and Grad totals (the fund-level rollup rows) ───────────────────────
    ug_total = {}
    grad_total = {}
    for i in range(len(df)):
        c0 = safe_str(df.iloc[i, 0])
        c1 = safe_str(df.iloc[i, 1])
        # Fund total rows have the fund code in c0 (like '4118') and a label in c1
        if c0 in ('4118',) and ('UGRAD' in c1.upper() or 'UNDERGRAD' in c1.upper()):
            ug_total = row(i)
            ug_total['name'] = 'Undergraduate Total'
        elif c0 in ('4119',) and ('GRAD' in c1.upper()):
            grad_total = row(i)
            grad_total['name'] = 'Graduate Total'

    # ── Final compilation ─────────────────────────────────────────────────────
    return {
        'period':      period,
        'file_name':   Path(path).name,
        'academic':    academic,
        'nonacademic': nonacademic,
        'ce_total':    ce_total,
        'total_exp':   total_exp,
        'ug_cats':     ug_cats,
        'grad_cats':   grad_cats,
        'ug_total':    ug_total,
        'grad_total':  grad_total,
    }


# ── HTML helpers ──────────────────────────────────────────────────────────────

def pct(actuals, budget):
    if budget == 0:
        return None
    return actuals / budget * 100


def fmt(v):
    return f'${v:,.2f}'


def progress_bar(spent, budget, committed=0):
    """
    Returns HTML for a progress bar.
    spent = FYTD actuals, committed = committed funds
    """
    if budget <= 0:
        # No budget — show how much was spent as an alert
        return f"<div class='progress-wrap'><span class='no-budget'>No budget allocated — {fmt(spent)} spent</span></div>"

    spent_pct     = min(spent / budget * 100, 100)
    committed_pct = min(committed / budget * 100, max(0, 100 - spent_pct))
    total_pct     = (spent + committed) / budget * 100
    over = total_pct > 100

    bar_class = 'bar-over' if over else ('bar-warn' if total_pct > 85 else 'bar-ok')
    label_pct = f'{spent / budget * 100:.1f}%'

    return f"""
    <div class='progress-wrap'>
        <div class='progress-track'>
            <div class='progress-fill {bar_class}' style='width:{spent_pct:.1f}%'></div>
            <div class='progress-committed' style='width:{committed_pct:.1f}%'></div>
        </div>
        <span class='progress-label {'over-label' if over else ''}'>{label_pct} spent</span>
    </div>"""


def stat_card(label, value, sub='', accent='#50c878'):
    return f"""
    <div class='stat-card'>
        <div class='stat-label'>{label}</div>
        <div class='stat-value' style='color:{accent}'>{value}</div>
        {'<div class="stat-sub">' + sub + '</div>' if sub else ''}
    </div>"""


def section_table(title, rows, show_committed=True):
    """Build an HTML table for a list of category dicts."""
    over_count = sum(1 for r in rows if r.get('budget', 0) > 0
                     and (r.get('actuals', 0) + r.get('committed', 0)) > r.get('budget', 0))
    alert = f"<span class='alert-badge'>{over_count} over budget</span>" if over_count else ''

    html = f"<div class='section-block'><h3>{title} {alert}</h3>"
    html += "<table class='track-table'><thead><tr>"
    html += "<th>Category</th><th>Budget</th><th>FYTD Actual</th>"
    if show_committed:
        html += "<th>Committed</th>"
    html += "<th>Available</th><th>Progress</th></tr></thead><tbody>"

    for r in rows:
        b  = r.get('budget', 0)
        a  = r.get('actuals', 0)
        co = r.get('committed', 0)
        av = r.get('available', 0)
        name = r.get('name', r.get('cat', ''))

        total_used = a + co
        is_over = b > 0 and total_used > b
        is_warn = b > 0 and total_used / b > 0.85 and not is_over
        row_class = 'row-over' if is_over else ('row-warn' if is_warn else '')

        av_class = 'neg' if av < 0 else ''

        html += f"<tr class='{row_class}'>"
        html += f"<td class='cat-name'>{name}</td>"
        html += f"<td>{fmt(b) if b else '—'}</td>"
        html += f"<td>{fmt(a)}</td>"
        if show_committed:
            html += f"<td>{fmt(co) if co else '—'}</td>"
        html += f"<td class='{av_class}'>{fmt(av)}</td>"
        html += f"<td>{progress_bar(a, b, co)}</td>"
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


# ── Page generator ────────────────────────────────────────────────────────────

def generate_tracking_page(data):
    t = data['total_exp']
    ac = data['academic']
    na = data['nonacademic']
    ce = data['ce_total']
    ug = data['ug_total']
    gr = data['grad_total']

    total_spent_pct = pct(t.get('actuals', 0), t.get('budget', 0))
    pct_label = f'{total_spent_pct:.1f}%' if total_spent_pct is not None else 'N/A'

    ug_cats_html   = section_table('Undergraduate Expense Categories', data['ug_cats'])
    grad_cats_html = section_table('Graduate Expense Categories', data['grad_cats'])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26 Budget Tracking</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d0d0d; color: #e0e0e0; }}

        /* ── Nav ── */
        .nav {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 16px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #4a90e2; }}
        .nav h1 {{ font-size: 1.4em; color: white; }}
        .nav-links {{ display: flex; gap: 10px; }}
        .nav-links a {{ color: #ccc; text-decoration: none; padding: 8px 14px; border-radius: 5px; transition: all 0.2s; font-size: 0.95em; }}
        .nav-links a:hover {{ background: rgba(74,144,226,0.3); color: white; }}
        .nav-links a.active {{ background: #4a90e2; color: white; }}

        /* ── Layout ── */
        .container {{ max-width: 1300px; margin: 30px auto; padding: 0 20px; }}

        /* ── Report badge ── */
        .report-meta {{ display: flex; align-items: center; gap: 16px; margin-bottom: 28px; }}
        .report-badge {{ background: #1a2a3a; border: 1px solid #4a90e2; color: #4a90e2; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }}
        .report-file {{ color: #666; font-size: 0.85em; }}

        /* ── Stat cards ── */
        .stats-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 30px; }}
        .stat-card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 20px; border-top: 3px solid #4a90e2; text-align: center; }}
        .stat-label {{ color: #888; font-size: 0.78em; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
        .stat-value {{ font-size: 1.5em; font-weight: bold; }}
        .stat-sub {{ color: #666; font-size: 0.8em; margin-top: 5px; }}

        /* ── Section headers ── */
        .section-title {{ color: #4a90e2; font-size: 1.5em; margin: 36px 0 16px; padding-bottom: 8px; border-bottom: 2px solid #4a90e2; }}

        /* ── Comp cards ── */
        .comp-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
        .comp-card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 22px; }}
        .comp-card h4 {{ color: #4a90e2; font-size: 1em; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.04em; }}
        .comp-nums {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }}
        .comp-num {{ text-align: center; }}
        .comp-num .label {{ color: #888; font-size: 0.75em; text-transform: uppercase; }}
        .comp-num .val {{ color: #e0e0e0; font-size: 1.1em; font-weight: bold; }}
        .comp-num .val.green {{ color: #50c878; }}
        .comp-num .val.red {{ color: #e74c3c; }}

        /* ── Progress bars ── */
        .progress-wrap {{ display: flex; align-items: center; gap: 10px; min-width: 160px; }}
        .progress-track {{ flex: 1; height: 8px; background: #2a2a2a; border-radius: 4px; overflow: hidden; display: flex; }}
        .progress-fill {{ height: 100%; border-radius: 4px 0 0 4px; transition: width 0.4s; }}
        .progress-committed {{ height: 100%; opacity: 0.4; }}
        .bar-ok {{ background: #50c878; }}
        .bar-warn {{ background: #f0a500; }}
        .bar-over {{ background: #e74c3c; }}
        .progress-committed {{ background: #f0a500; }}
        .progress-label {{ font-size: 0.8em; color: #888; white-space: nowrap; }}
        .over-label {{ color: #e74c3c; font-weight: bold; }}
        .no-budget {{ color: #e74c3c; font-size: 0.8em; font-style: italic; }}

        /* ── Tables ── */
        .section-block {{ background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 24px; margin-bottom: 24px; }}
        .section-block h3 {{ color: #4a90e2; font-size: 1.1em; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }}
        .alert-badge {{ background: #3a1010; color: #e74c3c; border: 1px solid #e74c3c; font-size: 0.75em; padding: 2px 10px; border-radius: 10px; }}
        .track-table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        .track-table thead tr {{ background: #252525; }}
        .track-table th {{ padding: 10px 12px; text-align: left; color: #999; font-weight: 600; font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid #333; }}
        .track-table td {{ padding: 10px 12px; border-bottom: 1px solid #222; }}
        .track-table tr:last-child td {{ border-bottom: none; }}
        .track-table tbody tr:hover {{ background: #202020; }}
        .row-over {{ background: #1f0d0d !important; border-left: 3px solid #e74c3c; }}
        .row-warn {{ background: #1e1800 !important; border-left: 3px solid #f0a500; }}
        .cat-name {{ font-weight: 600; color: #e0e0e0; }}
        .neg {{ color: #e74c3c; }}

        /* ── Legend ── */
        .legend {{ display: flex; gap: 20px; font-size: 0.8em; color: #888; margin-top: 12px; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

        .footer {{ text-align: center; padding: 30px; color: #555; margin-top: 40px; }}
    </style>
</head>
<body>

<div class="nav">
    <h1>📊 Fiscal Year 2026</h1>
    <div class="nav-links">
        <a href="index.html">🏠 Home</a>
        <a href="fy26_budget.html">💰 Budget View</a>
        <a href="fy26_tracking.html" class="active">📈 Tracking</a>
    </div>
</div>

<div class="container">

    <div class="report-meta">
        <span class="report-badge">📅 {data['period']}</span>
        <span class="report-file">Source: {data['file_name']}</span>
    </div>

    <!-- ── Overall KPIs ── -->
    <div class="stats-row">
        {stat_card('TOTAL BUDGET',     fmt(t.get('budget', 0)),   'FY26 Approved')}
        {stat_card('FYTD ACTUALS',     fmt(t.get('actuals', 0)),  f'{pct_label} of budget', '#4a90e2')}
        {stat_card('COMMITTED',        fmt(t.get('committed', 0)),'Encumbered funds', '#f0a500')}
        {stat_card('AVAILABLE BALANCE',fmt(t.get('available', 0)),'Unspent + uncommitted',
                   '#e74c3c' if t.get('available', 0) < 0 else '#50c878')}
    </div>

    {progress_bar(t.get('actuals', 0), t.get('budget', 0), t.get('committed', 0))}

    <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:#50c878"></div> Spent (FYTD Actuals)</div>
        <div class="legend-item"><div class="legend-dot" style="background:#f0a500"></div> Committed</div>
        <div class="legend-item"><div class="legend-dot" style="background:#e74c3c"></div> Over budget</div>
    </div>

    <!-- ── Compensation ── -->
    <h2 class="section-title">Compensation</h2>

    <div class="comp-row">
        <div class="comp-card">
            <h4>Academic Salaries</h4>
            <div class="comp-nums">
                <div class="comp-num"><div class="label">Budget</div><div class="val">{fmt(ac.get('budget',0))}</div></div>
                <div class="comp-num"><div class="label">FYTD Actual</div><div class="val green">{fmt(ac.get('actuals',0))}</div></div>
                <div class="comp-num"><div class="label">Committed</div><div class="val">{fmt(ac.get('committed',0))}</div></div>
                <div class="comp-num"><div class="label">Available</div>
                    <div class="val {'red' if ac.get('available',0) < 0 else 'green'}">{fmt(ac.get('available',0))}</div></div>
            </div>
            {progress_bar(ac.get('actuals',0), ac.get('budget',0), ac.get('committed',0))}
        </div>
        <div class="comp-card">
            <h4>Non-Academic Salaries</h4>
            <div class="comp-nums">
                <div class="comp-num"><div class="label">Budget</div><div class="val">{fmt(na.get('budget',0))}</div></div>
                <div class="comp-num"><div class="label">FYTD Actual</div><div class="val green">{fmt(na.get('actuals',0))}</div></div>
                <div class="comp-num"><div class="label">Committed</div><div class="val">{fmt(na.get('committed',0))}</div></div>
                <div class="comp-num"><div class="label">Available</div>
                    <div class="val {'red' if na.get('available',0) < 0 else 'green'}">{fmt(na.get('available',0))}</div></div>
            </div>
            {progress_bar(na.get('actuals',0), na.get('budget',0), na.get('committed',0))}
        </div>
    </div>

    <!-- ── Current Expenses ── -->
    <h2 class="section-title">Current Expenses</h2>

    <div class="stats-row">
        {stat_card('UG ACTUALS',   fmt(ug.get('actuals',0)), f"{pct(ug.get('actuals',0), ug.get('budget',0)) or 0:.1f}% of UG budget", '#3498db')}
        {stat_card('GRAD ACTUALS', fmt(gr.get('actuals',0)), f"{pct(gr.get('actuals',0), gr.get('budget',0)) or 0:.1f}% of Grad budget", '#9b59b6')}
        {stat_card('CE TOTAL ACTUAL', fmt(ce.get('actuals',0)), f"{pct(ce.get('actuals',0), ce.get('budget',0)) or 0:.1f}% of CE budget")}
        {stat_card('CE AVAILABLE',    fmt(ce.get('available',0)), 'Remaining current expense',
                   '#e74c3c' if ce.get('available',0) < 0 else '#50c878')}
    </div>

    {ug_cats_html}
    {grad_cats_html}

</div>

<div class="footer">
    <p><strong>Fine Arts Department Budget Tracking</strong></p>
    <p>FY26 · Generated from {data['file_name']}</p>
</div>

</body>
</html>"""
    return html


def main():
    latest = find_latest_file()
    print(f'Reading: {latest.name}')

    data = parse_tracking_file(latest)
    print(f"Period: {data['period']}")
    print(f"Total expenditures: budget={fmt(data['total_exp'].get('budget',0))} "
          f"actuals={fmt(data['total_exp'].get('actuals',0))}")
    print(f"UG categories: {len(data['ug_cats'])}   Grad categories: {len(data['grad_cats'])}")

    html = generate_tracking_page(data)

    out = Path('/Users/KLAW/project/budget/fy26_tracking.html')
    out.write_text(html)
    print(f'✓ Saved: {out}')


if __name__ == '__main__':
    main()
