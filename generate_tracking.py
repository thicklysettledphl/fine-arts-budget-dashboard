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

    Structure rules (confirmed from actual file):
      - Col A(0) B(1) C(2) D(3) E(4) F(5) G(6) H(7) I(8)
      - Charge rows:  B='F A UNDERGRAD', C=section code, D=category name, E=charge type
      - Total rows:   A=blank, B=blank, C=section code, D=blank, E=blank,
                      F=Budget, G=Spent (FYTD), H=Committed, I=Available
      - UG fund total: A='4118', B='UGRAD FNAR ...'
      - Grad section starts at A='4119'
    """
    df = pd.read_excel(path, sheet_name='Monthly Department Summary', header=None)

    def c(i, col):
        """Safe cell read."""
        return safe_str(df.iloc[i, col]) if df.shape[1] > col else ''

    def nums(i):
        return {
            'budget':    safe_float(df.iloc[i, 5]),
            'actuals':   safe_float(df.iloc[i, 6]),
            'committed': safe_float(df.iloc[i, 7]),
            'available': safe_float(df.iloc[i, 8]),
        }

    # ── Report period ─────────────────────────────────────────────────────────
    period = c(1, 0) or c(0, 0)

    # ── Helper: find first row matching a pattern ─────────────────────────────
    def find_row(col, pattern, start=0):
        for i in range(start, len(df)):
            if pattern.lower() in c(i, col).lower():
                return i
        return None

    # ── Compensation subtotals ────────────────────────────────────────────────
    ac_row = find_row(4, 'Academic Salaries')
    na_row = find_row(4, 'Non-Academic Salaries')
    te_row = find_row(0, 'TOTAL EXPENDITURES')

    academic    = {**nums(ac_row), 'name': 'Academic Salaries'}    if ac_row is not None else {}
    nonacademic = {**nums(na_row), 'name': 'Non-Academic Salaries'} if na_row is not None else {}
    total_exp   = {**nums(te_row), 'name': 'Total Expenditures'}   if te_row is not None else {}

    # ── Locate UG current expense section ────────────────────────────────────
    # Find CURRENT EXPENSE header, then the 4118 fund row within it.
    # Row structure (confirmed):
    #   Row 62: A='4118', B='F A UNDERGRAD', C='0.0' → first row of UG block
    #   Row 137: A='4118', B='UGRAD FNAR', C='' → fund-level total (ug_end)
    ce_start = find_row(0, 'CURRENT EXPENSE')
    ug_start = None
    ug_end   = None
    if ce_start is not None:
        for i in range(ce_start, len(df)):
            a = c(i, 0)
            b = c(i, 1)
            # First row with A='4118' in the CE section opens the UG block
            if a == '4118' and ug_start is None:
                ug_start = i
            # Fund-level total: A='4118', C='', has budget in F
            if (a == '4118' and c(i, 2) == '' and c(i, 5)
                    and ('UGRAD' in b.upper() or 'UNDERGRAD' in b.upper())):
                ug_end = i
                break
            # Grad section starts — UG is done
            if a == '4119':
                if ug_end is None:
                    ug_end = i
                break

    # ── Parse UG categories ───────────────────────────────────────────────────
    # Total rows: A=blank, B=blank, C=code (not '0.0'), D=blank, E=blank
    # Exclude the '0.0' general section; exclude fund total rows (A has value)
    ug_cats = []
    cat_name = ''

    if ug_start is not None and ug_end is not None:
        for i in range(ug_start, ug_end):
            a = c(i, 0)
            b = c(i, 1)
            code = c(i, 2)
            name_col = c(i, 3)
            charge = c(i, 4)

            # First charge row of a new category introduces its name in col D
            if b == 'F A UNDERGRAD' and code and name_col:
                cat_name = name_col

            # Total row: A blank, B blank, C=code, D blank, E blank
            is_total = (a == '' and b == '' and code not in ('', '0.0')
                        and name_col == '' and charge == '')
            if is_total:
                ug_cats.append({
                    'name':    cat_name,
                    'code':    code.replace('.0', ''),
                    **nums(i),
                })
                cat_name = ''   # reset for next category

    # ── UG fund total ─────────────────────────────────────────────────────────
    ug_total = {}
    if ug_end is not None and c(ug_end, 0) == '4118':
        ug_total = {**nums(ug_end), 'name': 'Undergraduate Total'}

    # ── CE subtotal ───────────────────────────────────────────────────────────
    ce_row = find_row(0, 'Subtotal - Current Expense')
    ce_total = {**nums(ce_row), 'name': 'Current Expense Total'} if ce_row is not None else {}

    return {
        'period':      period,
        'file_name':   Path(path).name,
        'academic':    academic,
        'nonacademic': nonacademic,
        'ce_total':    ce_total,
        'total_exp':   total_exp,
        'ug_cats':     ug_cats,
        'ug_total':    ug_total,
    }


# ── HTML helpers ──────────────────────────────────────────────────────────────

def pct(actuals, budget):
    if budget == 0:
        return None
    return actuals / budget * 100


def fmt(v):
    return f'${v:,.2f}'


def progress_bar(spent, budget):
    """Returns HTML for a progress bar showing actuals vs budget."""
    if budget <= 0:
        return f"<div class='progress-wrap'><span class='no-budget'>No budget allocated — {fmt(spent)} spent</span></div>"

    spent_pct = min(spent / budget * 100, 100)
    over      = spent > budget
    bar_class = 'bar-over' if over else ('bar-warn' if spent_pct > 85 else 'bar-ok')
    label_pct = f'{spent / budget * 100:.1f}%'

    return f"""
    <div class='progress-wrap'>
        <div class='progress-track'>
            <div class='progress-fill {bar_class}' style='width:{spent_pct:.1f}%'></div>
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


def section_table(title, rows):
    """Build an HTML table for a list of category dicts (budget, actuals, available)."""
    over_count = sum(1 for r in rows if r.get('budget', 0) > 0
                     and r.get('actuals', 0) > r.get('budget', 0))
    alert = f"<span class='alert-badge'>{over_count} over budget</span>" if over_count else ''

    html = f"<div class='section-block'><h3>{title} {alert}</h3>"
    html += "<table class='track-table'><thead><tr>"
    html += "<th>Category</th><th>Budget</th><th>FYTD Actual</th>"
    html += "<th>Available</th><th>Progress</th></tr></thead><tbody>"

    for r in rows:
        b  = r.get('budget', 0)
        a  = r.get('actuals', 0)
        av = r.get('available', 0)
        name = r.get('name', r.get('cat', ''))

        is_over = b > 0 and a > b
        is_warn = b > 0 and a / b > 0.85 and not is_over
        row_class = 'row-over' if is_over else ('row-warn' if is_warn else '')

        av_class = 'neg' if av < 0 else ''

        html += f"<tr class='{row_class}'>"
        html += f"<td class='cat-name'>{name}</td>"
        html += f"<td>{fmt(b) if b else '—'}</td>"
        html += f"<td>{fmt(a)}</td>"
        html += f"<td class='{av_class}'>{fmt(av)}</td>"
        html += f"<td>{progress_bar(a, b)}</td>"
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

    total_spent_pct = pct(t.get('actuals', 0), t.get('budget', 0))
    pct_label = f'{total_spent_pct:.1f}%' if total_spent_pct is not None else 'N/A'

    EXCLUDE_CODES = {'50', '503'}
    ug_filtered  = [r for r in data['ug_cats'] if r['code'] not in EXCLUDE_CODES]
    ug_cats_html = section_table('Undergraduate Current Expense Categories', ug_filtered)

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
        {stat_card('AVAILABLE BALANCE',fmt(t.get('available', 0)),'Unspent balance',
                   '#e74c3c' if t.get('available', 0) < 0 else '#50c878')}
    </div>

    {progress_bar(t.get('actuals', 0), t.get('budget', 0))}

    <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:#50c878"></div> Spent (FYTD Actuals)</div>
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
                <div class="comp-num"><div class="label">Available</div>
                    <div class="val {'red' if ac.get('available',0) < 0 else 'green'}">{fmt(ac.get('available',0))}</div></div>
            </div>
            {progress_bar(ac.get('actuals',0), ac.get('budget',0))}
        </div>
        <div class="comp-card">
            <h4>Non-Academic Salaries</h4>
            <div class="comp-nums">
                <div class="comp-num"><div class="label">Budget</div><div class="val">{fmt(na.get('budget',0))}</div></div>
                <div class="comp-num"><div class="label">FYTD Actual</div><div class="val green">{fmt(na.get('actuals',0))}</div></div>
                <div class="comp-num"><div class="label">Available</div>
                    <div class="val {'red' if na.get('available',0) < 0 else 'green'}">{fmt(na.get('available',0))}</div></div>
            </div>
            {progress_bar(na.get('actuals',0), na.get('budget',0))}
        </div>
    </div>

    <!-- ── Current Expenses ── -->
    <h2 class="section-title">Current Expenses</h2>

    <div class="stats-row">
        {stat_card('UG ACTUALS',      fmt(ug.get('actuals',0)),  f"{pct(ug.get('actuals',0), ug.get('budget',0)) or 0:.1f}% of UG budget", '#3498db')}
        {stat_card('UG BUDGET',       fmt(ug.get('budget',0)),   'Undergraduate allocation', '#4a90e2')}
        {stat_card('CE TOTAL ACTUAL', fmt(ce.get('actuals',0)),  f"{pct(ce.get('actuals',0), ce.get('budget',0)) or 0:.1f}% of CE budget")}
        {stat_card('CE AVAILABLE',    fmt(ce.get('available',0)),'Remaining current expense',
                   '#e74c3c' if ce.get('available',0) < 0 else '#50c878')}
    </div>

    {ug_cats_html}

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
    print(f"UG categories: {len(data['ug_cats'])}")

    html = generate_tracking_page(data)

    out = Path('/Users/KLAW/project/budget/fy26_tracking.html')
    out.write_text(html)
    print(f'✓ Saved: {out}')


if __name__ == '__main__':
    main()
