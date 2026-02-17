#!/usr/bin/env python3
"""
FY26 Fine Arts Budget - Full PDF Report Generator
Sections: Master Budget → Compensation → Current Expenses → Course/Studio Detail
"""

import pandas as pd
from collections import Counter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

# ── Brand colors ──────────────────────────────────────────────────────────────
BLUE       = colors.HexColor('#4a90e2')
GREEN      = colors.HexColor('#50c878')
DARK_BG    = colors.HexColor('#1a1a2e')
MID_GRAY   = colors.HexColor('#555555')
LIGHT_GRAY = colors.HexColor('#f4f6f9')
ROW_ALT    = colors.HexColor('#eef3fb')
WHITE      = colors.white
BLACK      = colors.HexColor('#1a1a1a')
AMBER      = colors.HexColor('#f0a500')
RED        = colors.HexColor('#e74c3c')

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    styles = {
        'title': ParagraphStyle('title', fontName='Helvetica-Bold',
                                fontSize=26, textColor=WHITE, spaceAfter=4,
                                alignment=TA_CENTER),
        'subtitle': ParagraphStyle('subtitle', fontName='Helvetica',
                                   fontSize=12, textColor=colors.HexColor('#ccddff'),
                                   spaceAfter=2, alignment=TA_CENTER),
        'section': ParagraphStyle('section', fontName='Helvetica-Bold',
                                  fontSize=16, textColor=BLUE, spaceBefore=18,
                                  spaceAfter=8, borderPadding=(0, 0, 4, 0)),
        'subsection': ParagraphStyle('subsection', fontName='Helvetica-Bold',
                                     fontSize=12, textColor=BLACK, spaceBefore=10,
                                     spaceAfter=6),
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10,
                               textColor=BLACK, spaceAfter=4, leading=14),
        'small': ParagraphStyle('small', fontName='Helvetica', fontSize=8,
                                textColor=MID_GRAY, spaceAfter=2),
        'amount': ParagraphStyle('amount', fontName='Helvetica-Bold', fontSize=10,
                                 textColor=GREEN, alignment=TA_RIGHT),
        'label': ParagraphStyle('label', fontName='Helvetica', fontSize=9,
                                textColor=MID_GRAY, spaceAfter=1),
        'big_number': ParagraphStyle('big_number', fontName='Helvetica-Bold',
                                     fontSize=22, textColor=GREEN, spaceAfter=2,
                                     alignment=TA_CENTER),
        'note': ParagraphStyle('note', fontName='Helvetica-Oblique', fontSize=9,
                               textColor=AMBER, spaceAfter=4),
        'course': ParagraphStyle('course', fontName='Helvetica', fontSize=9,
                                 textColor=BLACK, leading=13),
    }
    return styles


# ── Header / footer ───────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    w, h = letter

    # Top stripe
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, h - 36, w, 36, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, h - 38, w, 2, fill=1, stroke=0)

    # Page title in stripe
    canvas.setFont('Helvetica-Bold', 9)
    canvas.setFillColor(colors.HexColor('#ccddff'))
    canvas.drawString(0.5 * inch, h - 24, 'Fine Arts · FY26 Master Budget Report')
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(WHITE)
    canvas.drawRightString(w - 0.5 * inch, h - 24, f'Page {doc.page}')

    # Bottom stripe
    canvas.setFillColor(LIGHT_GRAY)
    canvas.rect(0, 0, w, 28, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, 28, w, 1, fill=1, stroke=0)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(0.5 * inch, 10, 'School of Design · Fine Arts Department · Confidential')
    canvas.drawRightString(w - 0.5 * inch, 10, 'Generated February 17, 2026')

    canvas.restoreState()


# ── Cover page ────────────────────────────────────────────────────────────────
def cover_block():
    w, h = letter
    drawing = Drawing(w - inch, 3.4 * inch)

    # Background rect
    drawing.add(Rect(0, 0, w - inch, 3.4 * inch,
                     fillColor=DARK_BG, strokeColor=None))
    # Accent bar
    drawing.add(Rect(0, 0, 6, 3.4 * inch, fillColor=BLUE, strokeColor=None))

    drawing.add(String((w - inch) / 2, 2.7 * inch,
                        'Fine Arts Department',
                        fontName='Helvetica', fontSize=13,
                        fillColor=colors.HexColor('#ccddff'),
                        textAnchor='middle'))
    drawing.add(String((w - inch) / 2, 2.25 * inch,
                        'FY26 Master Budget Report',
                        fontName='Helvetica-Bold', fontSize=28,
                        fillColor=WHITE, textAnchor='middle'))
    drawing.add(String((w - inch) / 2, 1.8 * inch,
                        'Fiscal Year 2026  ·  July 1, 2025 – June 30, 2026',
                        fontName='Helvetica', fontSize=12,
                        fillColor=colors.HexColor('#8ab4e8'),
                        textAnchor='middle'))

    # Accent line
    drawing.add(Line(0.3 * inch, 1.55 * inch, (w - inch) - 0.3 * inch, 1.55 * inch,
                     strokeColor=BLUE, strokeWidth=1.5))

    drawing.add(String((w - inch) / 2, 1.1 * inch,
                        'School of Design',
                        fontName='Helvetica-Bold', fontSize=11,
                        fillColor=WHITE, textAnchor='middle'))
    drawing.add(String((w - inch) / 2, 0.75 * inch,
                        'CONFIDENTIAL — Internal Use Only',
                        fontName='Helvetica-Oblique', fontSize=9,
                        fillColor=colors.HexColor('#8ab4e8'),
                        textAnchor='middle'))
    return drawing


# ── Stat card row ─────────────────────────────────────────────────────────────
def stat_row(items, col_widths=None):
    """
    items = list of (label, value, sub) tuples.
    Returns a Table that renders as side-by-side stat cards.
    """
    n = len(items)
    cw = col_widths or ([6.5 * inch / n] * n)
    data = [[Paragraph(label, ParagraphStyle('sl', fontName='Helvetica',
                                             fontSize=8, textColor=MID_GRAY,
                                             alignment=TA_CENTER)),
             ] for label, val, sub in items]
    data2 = [[Paragraph(val, ParagraphStyle('sv', fontName='Helvetica-Bold',
                                            fontSize=18, textColor=GREEN,
                                            alignment=TA_CENTER)),
              ] for label, val, sub in items]
    data3 = [[Paragraph(sub, ParagraphStyle('ss', fontName='Helvetica',
                                            fontSize=8, textColor=MID_GRAY,
                                            alignment=TA_CENTER)),
              ] for label, val, sub in items]

    # Combine into single cells with line breaks
    combined = []
    for label, val, sub in items:
        cell = [
            Paragraph(label, ParagraphStyle('L', fontName='Helvetica', fontSize=8,
                                            textColor=MID_GRAY, alignment=TA_CENTER,
                                            spaceAfter=2)),
            Paragraph(val, ParagraphStyle('V', fontName='Helvetica-Bold', fontSize=17,
                                          textColor=GREEN, alignment=TA_CENTER,
                                          spaceAfter=2)),
            Paragraph(sub, ParagraphStyle('S', fontName='Helvetica', fontSize=8,
                                          textColor=MID_GRAY, alignment=TA_CENTER)),
        ]
        combined.append(cell)

    t = Table([combined], colWidths=cw)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d8e8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d8e8')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 3, BLUE),
    ]))
    return t


# ── Pie chart drawing ─────────────────────────────────────────────────────────
def pie_chart(labels, values, chart_colors, title, size=200):
    d = Drawing(size, size + 20)

    pc = Pie()
    pc.x = 20
    pc.y = 20
    pc.width = size - 40
    pc.height = size - 40
    pc.data = values
    pc.labels = [f'{l}\n${v:,.0f}' for l, v in zip(labels, values)]
    pc.sideLabels = 1
    pc.slices.strokeWidth = 0.5
    pc.slices.strokeColor = colors.HexColor('#333333')
    for i, c in enumerate(chart_colors):
        pc.slices[i].fillColor = c

    d.add(pc)
    d.add(String(size / 2, size + 6, title,
                 fontName='Helvetica-Bold', fontSize=9,
                 fillColor=BLACK, textAnchor='middle'))
    return d


# ── Section divider ───────────────────────────────────────────────────────────
def section_divider(title, styles):
    elems = []
    elems.append(Spacer(1, 0.15 * inch))
    elems.append(HRFlowable(width='100%', thickness=2, color=BLUE,
                             spaceAfter=6))
    elems.append(Paragraph(title, styles['section']))
    return elems


# ── Data extraction ───────────────────────────────────────────────────────────
def load_data():
    file_path = '/Users/KLAW/project/budget/FY/fy26.xlsx'

    def sf(v):
        if pd.isna(v): return 0.0
        try: return float(v)
        except: return 0.0

    df = pd.read_excel(file_path, sheet_name='FA_Summary', header=None)
    bc = 20  # FY26 column

    data = {
        'total_budget':       4241604.00,
        'total_comp':         sf(df.iloc[46, bc]),
        'standing_faculty':   sf(df.iloc[10, bc]),
        'other_ft_faculty':   sf(df.iloc[11, bc]),
        'parttime_faculty':   sf(df.iloc[12, bc]),
        'total_academic':     sf(df.iloc[15, bc]),
        'nonacademic_comp':   sf(df.iloc[41, bc]),   # includes benefits
        'current_expenses':   sf(df.iloc[110, bc]),
        'grad_total':         sf(df.iloc[111, bc]),
        'undergrad_total':    sf(df.iloc[112, bc]),
    }

    # CE breakdown
    df_ce = pd.read_excel(file_path, sheet_name='CE_Breakdown', header=None)
    def ce(row): return sf(df_ce.iloc[row, 16])
    def cel(row): return str(df_ce.iloc[row, 1]) if pd.notna(df_ce.iloc[row, 1]) else ''

    data['ce_categories'] = [
        {'name': 'Chair Expenses',          'amount': 10000.00,
         'subs': [('Fall PT Faculty Fund', ce(23)), ('Spring PT Faculty Fund', ce(24)),
                  ('Student Summer Programs', ce(25))]},
        {'name': 'Course/Studio Expenses',  'amount': ce(27),  'subs': [], 'link': True},
        {'name': 'Department Administrative','amount': ce(40), 'subs': []},
        {'name': 'Departmental Events',     'amount': ce(53),
         'subs': [('Commencement', ce(63)), ('Engagement Events', ce(64)),
                  ('Student Prizes', ce(65)), ('Senior Reviews', ce(66)),
                  ('Student Exhibitions', ce(67))]},
        {'name': 'Promotion of Department', 'amount': ce(83), 'subs': []},
    ]

    # Course/Studio categories from Sheet1
    NOTE_PATTERNS = ['$', 'Photo/Video Equipment Room']
    df_s1 = pd.read_excel(file_path, sheet_name='Sheet1', header=None, na_filter=False)
    cat_courses = {}
    cat_notes = {}
    cur = None
    for i in range(len(df_s1)):
        c0 = str(df_s1.iloc[i, 0]).strip()
        c1 = str(df_s1.iloc[i, 1]).strip()
        c2 = str(df_s1.iloc[i, 2]).strip() if df_s1.shape[1] > 2 else ''
        if c0:
            cur = c0
            cat_courses[cur] = []
            cat_notes[cur] = []
        if c1 and cur:
            if any(c1.startswith(p) or c1 == p for p in NOTE_PATTERNS):
                cat_notes[cur].append(c1)
            else:
                cat_courses[cur].append({'code': c1, 'name': c2 if c2 else ''})

    def get_courses(key):
        return cat_courses.get(key, [])
    def get_notes(key):
        return cat_notes.get(key, [])

    data['course_studio'] = [
        {'name': 'Printmaking (0506)',                'total': 10000.00,
         'courses': get_courses('Printmaking (0506)'),
         'notes': get_notes('Printmaking (0506)')},
        {'name': 'Visiting Lectures (0050)',           'total': 12600.00,
         'courses': get_courses('Visiting Lectures (0050)'),
         'notes': get_notes('Visiting Lectures (0050)')},
        {'name': 'Senior Seminar (0592)',              'total': 15400.00,
         'courses': get_courses('Senior Seminar (0592)'),
         'notes': get_notes('Senior Seminar (0592)')},
        {'name': 'Photography Instructional (0515)',   'total': 2500.00,
         'courses': get_courses('Photography Instructional (0515)'),
         'notes': get_notes('Photography Instructional (0515)')},
        {'name': 'Animation Instructional (0511)',     'total': 8400.00,
         'courses': get_courses('Animation Instructional (0511)'),
         'notes': get_notes('Animation Instructional (0511)')},
        {'name': 'Digital Design (0513)',              'total': 11950.00,
         'courses': get_courses('Digital Design (0513)'),
         'notes': get_notes('Digital Design (0513)')},
        {'name': 'Drawing/Painting Instructional (0505)', 'total': 10750.00,
         'courses': get_courses('Drawing/Painting Instructional (0505)'),
         'notes': get_notes('Drawing/Painting Instructional (0505)')},
        {'name': 'Sculpture Instructional (0507)',     'total': 8400.00,
         'courses': get_courses('Sculpture Instructional (0507)'),
         'notes': get_notes('Sculpture Instructional (0507)')},
        {'name': 'Video Instructional (0509)',         'total': 2000.00,
         'courses': get_courses('Video Instructional (0509)'),
         'notes': get_notes('Video Instructional (0509)')},
        {'name': 'Photography Consumables (0569)',     'total': 22500.00,
         'courses': get_courses('Photography Consumables (0569)'),
         'notes': get_notes('Photography Consumables (0569)')},
    ]

    return data


# ── Section builders ──────────────────────────────────────────────────────────
def build_master_budget(data, styles):
    elems = []
    elems += section_divider('Master Budget Overview', styles)

    elems.append(stat_row([
        ('TOTAL BUDGET',       f"${data['total_budget']:,.2f}",       'FY26 General Purpose'),
        ('TOTAL COMPENSATION', f"${data['total_comp']:,.2f}",         'Academic + Non-Academic'),
        ('CURRENT EXPENSES',   f"${data['current_expenses']:,.2f}",   'Operating Expenses'),
    ]))

    elems.append(Spacer(1, 0.2 * inch))

    # Budget split table
    comp_pct   = data['total_comp'] / data['total_budget'] * 100
    exp_pct    = data['current_expenses'] / data['total_budget'] * 100

    t_data = [
        [Paragraph('Category', ParagraphStyle('th', fontName='Helvetica-Bold',
                                               fontSize=9, textColor=WHITE)),
         Paragraph('Amount', ParagraphStyle('th', fontName='Helvetica-Bold',
                                             fontSize=9, textColor=WHITE,
                                             alignment=TA_RIGHT)),
         Paragraph('% of Total', ParagraphStyle('th', fontName='Helvetica-Bold',
                                                  fontSize=9, textColor=WHITE,
                                                  alignment=TA_RIGHT))],
        ['Total Compensation',
         f"${data['total_comp']:,.2f}",
         f'{comp_pct:.1f}%'],
        ['Current Expenses',
         f"${data['current_expenses']:,.2f}",
         f'{exp_pct:.1f}%'],
        [Paragraph('TOTAL BUDGET', ParagraphStyle('tot', fontName='Helvetica-Bold',
                                                   fontSize=10, textColor=BLACK)),
         Paragraph(f"${data['total_budget']:,.2f}", ParagraphStyle('tot',
                   fontName='Helvetica-Bold', fontSize=10, textColor=BLACK,
                   alignment=TA_RIGHT)),
         Paragraph('100.0%', ParagraphStyle('tot', fontName='Helvetica-Bold',
                                             fontSize=10, textColor=BLACK,
                                             alignment=TA_RIGHT))],
    ]

    t = Table(t_data, colWidths=[3.8 * inch, 1.7 * inch, 1 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), DARK_BG),
        ('BACKGROUND',   (0, 1), (-1, 2), LIGHT_GRAY),
        ('BACKGROUND',   (0, 3), (-1, 3), colors.HexColor('#dce8f8')),
        ('ROWBACKGROUNDS', (0, 1), (-1, 2), [WHITE, LIGHT_GRAY]),
        ('ALIGN',        (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME',     (0, 1), (-1, 2), 'Helvetica'),
        ('FONTSIZE',     (0, 1), (-1, 2), 10),
        ('TOPPADDING',   (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 7),
        ('LEFTPADDING',  (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BOX',          (0, 0), (-1, -1), 0.5, colors.HexColor('#c0cfe8')),
        ('INNERGRID',    (0, 0), (-1, -1), 0.5, colors.HexColor('#d8e4f4')),
        ('LINEABOVE',    (0, 3), (-1, 3), 1.5, BLUE),
    ]))
    elems.append(t)
    return elems


def build_compensation(data, styles):
    elems = []
    elems += section_divider('Compensation', styles)

    # --- Academic ---
    elems.append(Paragraph('Academic Compensation by Faculty Type', styles['subsection']))

    total_fac = 7 + 10 + 45
    ac_data = [
        [Paragraph(h, ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9,
                                      textColor=WHITE))
         for h in ['Faculty Type', 'Count', 'Amount', '% of Academic']],
        ['Standing Faculty',      '7',
         f"${data['standing_faculty']:,.2f}",
         f"{data['standing_faculty']/data['total_academic']*100:.1f}%"],
        ['Other Full-Time Faculty','10',
         f"${data['other_ft_faculty']:,.2f}",
         f"{data['other_ft_faculty']/data['total_academic']*100:.1f}%"],
        ['Part-Time Faculty',     '45',
         f"${data['parttime_faculty']:,.2f}",
         f"{data['parttime_faculty']/data['total_academic']*100:.1f}%"],
        [Paragraph('Total Academic', ParagraphStyle('tot', fontName='Helvetica-Bold',
                                                     fontSize=10, textColor=BLACK)),
         Paragraph(str(total_fac), ParagraphStyle('tot', fontName='Helvetica-Bold',
                                                    fontSize=10, textColor=BLACK,
                                                    alignment=TA_CENTER)),
         Paragraph(f"${data['total_academic']:,.2f}", ParagraphStyle('tot',
                   fontName='Helvetica-Bold', fontSize=10, textColor=BLACK,
                   alignment=TA_RIGHT)),
         Paragraph('100.0%', ParagraphStyle('tot', fontName='Helvetica-Bold',
                                             fontSize=10, textColor=BLACK,
                                             alignment=TA_RIGHT))],
    ]

    cws = [2.8 * inch, 0.8 * inch, 1.8 * inch, 1.1 * inch]
    t = Table(ac_data, colWidths=cws)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), DARK_BG),
        ('ROWBACKGROUNDS',(0, 1), (-1, -2), [WHITE, LIGHT_GRAY]),
        ('BACKGROUND',    (0, -1), (-1, -1), colors.HexColor('#dce8f8')),
        ('ALIGN',         (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN',         (1, 1), (1, -2), 'CENTER'),
        ('FONTNAME',      (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -2), 10),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.HexColor('#c0cfe8')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, colors.HexColor('#d8e4f4')),
        ('LINEABOVE',     (0, -1), (-1, -1), 1.5, BLUE),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 0.2 * inch))

    # --- Non-Academic ---
    elems.append(Paragraph('Non-Academic Compensation', styles['subsection']))

    na_data = [
        [Paragraph(h, ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9,
                                      textColor=WHITE))
         for h in ['Category', 'Amount']],
        ['Total Non-Academic Compensation (includes employee benefits)',
         f"${data['nonacademic_comp']:,.2f}"],
    ]
    t2 = Table(na_data, colWidths=[4.5 * inch, 2.0 * inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), DARK_BG),
        ('BACKGROUND',    (0, 1), (-1, 1), LIGHT_GRAY),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME',      (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, 1), 10),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.HexColor('#c0cfe8')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, colors.HexColor('#d8e4f4')),
    ]))
    elems.append(t2)
    elems.append(Spacer(1, 0.2 * inch))

    # --- Grand total comp ---
    elems.append(stat_row([
        ('ACADEMIC COMPENSATION',     f"${data['total_academic']:,.2f}",    '62 faculty members'),
        ('NON-ACADEMIC COMPENSATION', f"${data['nonacademic_comp']:,.2f}",  'Includes benefits'),
        ('TOTAL COMPENSATION',        f"${data['total_comp']:,.2f}",        'All compensation'),
    ]))

    # Pie chart
    elems.append(Spacer(1, 0.25 * inch))
    pie = pie_chart(
        ['Standing Faculty', 'Other Full-Time', 'Part-Time'],
        [data['standing_faculty'], data['other_ft_faculty'], data['parttime_faculty']],
        [BLUE, GREEN, colors.HexColor('#9b59b6')],
        'Academic Compensation by Faculty Type',
        size=260
    )
    pie_table = Table([[pie]], colWidths=[6.5 * inch])
    pie_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'CENTER')]))
    elems.append(pie_table)

    return elems


def build_current_expenses(data, styles):
    elems = []
    elems += section_divider('Current Expenses', styles)

    # Grad / UG split
    elems.append(stat_row([
        ('GRADUATE TOTAL',      f"${data['grad_total']:,.2f}",
         f"{data['grad_total']/data['current_expenses']*100:.1f}% of current expenses"),
        ('UNDERGRADUATE TOTAL', f"${data['undergrad_total']:,.2f}",
         f"{data['undergrad_total']/data['current_expenses']*100:.1f}% of current expenses"),
        ('TOTAL CURRENT EXPENSES', f"${data['current_expenses']:,.2f}", 'FY26'),
    ]))

    elems.append(Spacer(1, 0.2 * inch))

    # Costs covered note
    elems.append(Paragraph('Costs Covered by Current Expenses', styles['subsection']))
    covered = [
        'Department Administrative Expenses',
        'Internal Facility Expenses',
        'Internal Technology Expenses',
        'Department Extra-Curricular Expenses',
        'Support for All Courses in Fine Arts and Design',
    ]
    for item in covered:
        elems.append(Paragraph(f'• {item}', styles['body']))
    elems.append(Spacer(1, 0.2 * inch))

    # Pie chart
    pie = pie_chart(
        ['Graduate', 'Undergraduate'],
        [data['grad_total'], data['undergrad_total']],
        [RED, BLUE],
        'Graduate vs Undergraduate Expenses',
        size=240
    )
    pie_table = Table([[pie]], colWidths=[6.5 * inch])
    pie_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'CENTER')]))
    elems.append(pie_table)

    elems.append(Spacer(1, 0.2 * inch))
    elems.append(Paragraph('Undergraduate Expense Categories', styles['subsection']))

    # Expense categories table
    hdr = [Paragraph(h, ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=9,
                                        textColor=WHITE))
           for h in ['Category / Line Item', 'Amount']]
    rows = [hdr]
    for cat in data['ce_categories']:
        # Main row
        rows.append([
            Paragraph(cat['name'], ParagraphStyle('cat', fontName='Helvetica-Bold',
                                                   fontSize=10, textColor=BLACK)),
            Paragraph(f"${cat['amount']:,.2f}", ParagraphStyle('ca',
                      fontName='Helvetica-Bold', fontSize=10, textColor=GREEN,
                      alignment=TA_RIGHT)),
        ])
        # Subcategory rows
        for sub_name, sub_amt in cat.get('subs', []):
            rows.append([
                Paragraph(f'    • {sub_name}', ParagraphStyle('sub',
                          fontName='Helvetica', fontSize=9, textColor=MID_GRAY)),
                Paragraph(f"${sub_amt:,.2f}", ParagraphStyle('sa',
                          fontName='Helvetica', fontSize=9, textColor=BLUE,
                          alignment=TA_RIGHT)),
            ])

    t = Table(rows, colWidths=[4.8 * inch, 1.7 * inch])
    style_cmds = [
        ('BACKGROUND',    (0, 0), (-1, 0), DARK_BG),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.HexColor('#c0cfe8')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, colors.HexColor('#e4ecf8')),
    ]
    # Alternate row colors for non-sub rows
    row_idx = 1
    for cat in data['ce_categories']:
        bg = LIGHT_GRAY if row_idx % 2 == 0 else WHITE
        style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))
        row_idx += 1
        for _ in cat.get('subs', []):
            style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx),
                                colors.HexColor('#f8fbff')))
            row_idx += 1

    t.setStyle(TableStyle(style_cmds))
    elems.append(t)

    return elems


def build_course_studio(data, styles):
    elems = []
    elems += section_divider('Course/Studio Budget Detail', styles)

    total = sum(c['total'] for c in data['course_studio'])
    elems.append(stat_row([
        ('TOTAL COURSE/STUDIO BUDGET', f"${total:,.2f}",
         f"{len(data['course_studio'])} instructional categories"),
    ], col_widths=[6.5 * inch]))

    elems.append(Spacer(1, 0.2 * inch))

    for cat in data['course_studio']:
        # Count sections
        section_counts = Counter((c['code'], c['name']) for c in cat['courses'])
        seen = set()
        unique_courses = []
        for c in cat['courses']:
            key = (c['code'], c['name'])
            if key not in seen:
                seen.add(key)
                unique_courses.append(c)
        total_sections = sum(section_counts.values())

        card_elems = []

        # Category header row
        hdr_data = [[
            Paragraph(cat['name'], ParagraphStyle('ch', fontName='Helvetica-Bold',
                                                   fontSize=11, textColor=WHITE)),
            Paragraph(f"${cat['total']:,.2f}", ParagraphStyle('ct',
                      fontName='Helvetica-Bold', fontSize=12, textColor=GREEN,
                      alignment=TA_RIGHT)),
        ]]
        hdr_t = Table(hdr_data, colWidths=[4.5 * inch, 2.0 * inch])
        hdr_t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), DARK_BG),
            ('LEFTPADDING',   (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW',     (0, 0), (-1, -1), 2, BLUE),
        ]))
        card_elems.append(hdr_t)

        # Notes (e.g. $200/visit)
        for note in cat.get('notes', []):
            card_elems.append(
                Paragraph(f'ℹ  {note}', ParagraphStyle('n', fontName='Helvetica-Oblique',
                                                        fontSize=9, textColor=AMBER,
                                                        leftIndent=10, spaceAfter=2,
                                                        spaceBefore=4))
            )

        # Courses table
        if unique_courses:
            section_label = f"{total_sections} section{'s' if total_sections != 1 else ''}"
            card_elems.append(
                Paragraph(f'Courses Supported  ({section_label})',
                          ParagraphStyle('cs', fontName='Helvetica-Bold', fontSize=9,
                                         textColor=BLUE, spaceBefore=6, spaceAfter=4,
                                         leftIndent=10))
            )

            course_rows = [
                [Paragraph(h, ParagraphStyle('ch2', fontName='Helvetica-Bold', fontSize=8,
                                              textColor=MID_GRAY))
                 for h in ['Course', 'Title', 'Sections']],
            ]
            for i, course in enumerate(unique_courses):
                key = (course['code'], course['name'])
                cnt = section_counts[key]
                bg = LIGHT_GRAY if i % 2 == 0 else WHITE
                course_rows.append([
                    Paragraph(course['code'], ParagraphStyle('cc', fontName='Helvetica-Bold',
                                                              fontSize=9, textColor=BLUE)),
                    Paragraph(course['name'], ParagraphStyle('cn', fontName='Helvetica',
                                                              fontSize=9, textColor=BLACK)),
                    Paragraph(str(cnt), ParagraphStyle('cs2', fontName='Helvetica-Bold',
                                                        fontSize=9, textColor=GREEN,
                                                        alignment=TA_CENTER)),
                ])

            ct = Table(course_rows, colWidths=[1.3 * inch, 3.8 * inch, 0.9 * inch])
            ct_style = [
                ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#dce8f8')),
                ('ALIGN',         (2, 0), (2, -1), 'CENTER'),
                ('FONTSIZE',      (0, 0), (-1, 0), 8),
                ('TOPPADDING',    (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
                ('BOX',           (0, 0), (-1, -1), 0.5, colors.HexColor('#c0cfe8')),
                ('INNERGRID',     (0, 0), (-1, -1), 0.5, colors.HexColor('#e4ecf8')),
            ]
            for ri in range(1, len(course_rows)):
                bg = LIGHT_GRAY if (ri % 2 == 1) else WHITE
                ct_style.append(('BACKGROUND', (0, ri), (-1, ri), bg))

            ct.setStyle(TableStyle(ct_style))
            card_elems.append(ct)
        else:
            card_elems.append(
                Paragraph('No individual course data in Sheet1 for this category.',
                          ParagraphStyle('empty', fontName='Helvetica-Oblique',
                                         fontSize=9, textColor=MID_GRAY,
                                         leftIndent=10, spaceBefore=4))
            )

        card_elems.append(Spacer(1, 0.18 * inch))
        elems.append(KeepTogether(card_elems))

    return elems


# ── Main ──────────────────────────────────────────────────────────────────────
def generate_pdf(output_path='fy26_budget_report.pdf'):
    print('Loading data...')
    data = load_data()
    styles = make_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.65 * inch,
        bottomMargin=0.55 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title='FY26 Fine Arts Budget Report',
        author='School of Design – Fine Arts',
    )

    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.2 * inch))
    story.append(cover_block())
    story.append(PageBreak())

    # ── Master Budget ─────────────────────────────────────────────────────────
    story += build_master_budget(data, styles)
    story.append(PageBreak())

    # ── Compensation ──────────────────────────────────────────────────────────
    story += build_compensation(data, styles)
    story.append(PageBreak())

    # ── Current Expenses ──────────────────────────────────────────────────────
    story += build_current_expenses(data, styles)
    story.append(PageBreak())

    # ── Course/Studio Detail ──────────────────────────────────────────────────
    story += build_course_studio(data, styles)

    print('Building PDF...')
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'✓ Saved: {output_path}')


if __name__ == '__main__':
    generate_pdf('/Users/KLAW/project/budget/fy26_budget_report.pdf')
