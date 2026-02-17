# Fine Arts Budget Dashboard - FY26

A comprehensive budget management system for the Fine Arts Department, featuring interactive visualizations and detailed expense tracking.

## Features

- **Dark Mode Interface** - Modern, easy-on-the-eyes design
- **Interactive Visualizations** - Powered by Plotly for dynamic charts
- **Multi-Tab Navigation** - Separate views for Compensation and Current Expenses
- **Detailed Breakdowns** - Course/Studio expenses with course listings
- **Faculty Information** - Compensation by faculty type with headcount

## System Components

### Main Budget Dashboard (`fy26_budget.html`)
- Total budget overview: $4,241,604.00
- Compensation tab with academic and non-academic breakdown
- Current expenses tab with graduate vs undergraduate split
- Clickable subcategories with detailed line items

### Course/Studio Detail Page (`course_studio_detail.html`)
- Detailed breakdown of $104,500 Course/Studio budget
- Bar chart visualizations
- Course listings for each category
- Calculation details (e.g., visiting lectures: $200/visitor × 63 courses)

## Data Sources

- **FA_Summary Sheet (Column U)**: Main budget totals and fiscal year data
- **CE_Breakdown Sheet (Column Q)**: Subcategory expense values
- **Sheet1**: Course information and listings

## Python Scripts

### `generate_fy26.py`
Generates the main FY26 budget dashboard with:
- Compensation breakdown (standing, other fulltime, part-time faculty)
- Current expenses breakdown (chair, course/studio, admin, events, promotion)
- Graduate vs undergraduate expense distribution

### `generate_course_studio_detail.py`
Creates detailed Course/Studio budget page with:
- Category-wise expense breakdowns
- Course listings from Sheet1
- Detailed calculation explanations

### `generate_fiscal_year.py`
Multi-year budget generator for FY23-FY26:
- Extracts data from master budget files
- Creates budget and tracking views for each fiscal year
- Generates home page with fiscal year navigation

### `add_fiscal_year.py`
Utility for managing fiscal years:
- Add new fiscal years to configuration
- Update file paths
- List all configured fiscal years

## Budget Breakdown

### Total Budget: $4,241,604.00

**Compensation: $3,879,484.00**
- Standing Faculty: 7 members
- Other Fulltime Faculty: 10 members
- Part-Time Faculty: 45 members
- Non-Academic Compensation: $715,482.08 (excluding benefits)

**Current Expenses: $358,000.00**
- Graduate: $162,300.00
- Undergraduate: $195,700.00

### Undergraduate Expense Categories

1. **Chair Expenses**: $10,000.00
   - Fall PT Faculty Fund: $3,000
   - Spring PT Faculty Fund: $3,000
   - Student Summer Programs: $4,000

2. **Course/Studio Expenses**: $104,500.00
   - Printmaking, Photography, Animation, Digital Design, Drawing/Painting, Sculpture, Video
   - See detail page for full breakdown

3. **Department Administrative**: $16,000.00

4. **Departmental Events**: $25,200.00
   - Commencement, Engagement Events, Student Prizes, Senior Reviews, Exhibitions

5. **Promotion of Department**: $7,000.00

## Usage

### Generate Main Budget
```bash
python3 generate_fy26.py
open fy26_budget.html
```

### Generate Course/Studio Detail
```bash
python3 generate_course_studio_detail.py
open course_studio_detail.html
```

### Generate All Fiscal Years
```bash
python3 generate_fiscal_year.py all
open index.html
```

## Requirements

- Python 3.9+
- pandas
- openpyxl
- plotly

Install dependencies:
```bash
pip install pandas openpyxl plotly
```

## File Structure

```
/Users/KLAW/Project/budget/
├── fy26_budget.html              # Main budget dashboard
├── course_studio_detail.html     # Course/Studio detail page
├── generate_fy26.py              # FY26 generator script
├── generate_course_studio_detail.py
├── generate_fiscal_year.py       # Multi-year generator
├── add_fiscal_year.py            # Fiscal year management
├── fiscal_years.json             # Fiscal year configuration
├── index.html                    # Multi-year home page
└── FY/                           # Excel budget files (not in repo)
    └── fy26.xlsx
```

## Data Privacy

Excel files containing actual budget data are excluded from the repository via `.gitignore` to protect sensitive financial information.

## Color Scheme

- Primary Blue: #4a90e2
- Success Green: #50c878
- Purple: #9b59b6
- Background: #0d0d0d
- Cards: #1a1a1a

---

**Fine Arts Department | Fiscal Year 2026**
