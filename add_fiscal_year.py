#!/usr/bin/env python3
"""
Add Fiscal Year to Configuration
Manually adds a fiscal year to the multi-year budget system
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def parse_year_code(year_code):
    """Convert FY26 to full fiscal year info"""
    year_num = int(year_code.replace('FY', '').replace('fy', ''))
    full_year = 2000 + year_num

    return {
        'year': f'FY{year_num}',
        'label': f'Fiscal Year {full_year}',
        'period': f'July 1, {full_year-1} - June 30, {full_year}'
    }

def add_fiscal_year(year_code, budget_file_path):
    """Add a fiscal year to the configuration"""

    print("="*80)
    print(f"ADDING FISCAL YEAR: {year_code.upper()}")
    print("="*80)

    # Validate file exists
    if not Path(budget_file_path).exists():
        print(f"✗ Error: Budget file not found: {budget_file_path}")
        return False

    # Parse year code
    fy_info = parse_year_code(year_code)

    # Load existing configuration
    config_file = 'fiscal_years.json'
    if Path(config_file).exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {'fiscal_years': [], 'current_fiscal_year': ''}

    # Check if fiscal year already exists
    existing_idx = None
    for idx, fy in enumerate(config['fiscal_years']):
        if fy['year'] == fy_info['year']:
            existing_idx = idx
            break

    # Create fiscal year entry
    fy_entry = {
        'year': fy_info['year'],
        'label': fy_info['label'],
        'period': fy_info['period'],
        'master_budget_file': budget_file_path,
        'latest_report_file': None,
        'latest_report_month': None,
        'months_elapsed': 0,
        'status': 'active'
    }

    if existing_idx is not None:
        print(f"⚠️  {fy_info['year']} already exists. Updating...")
        fy_entry['added'] = config['fiscal_years'][existing_idx].get('added', datetime.now().strftime('%Y-%m-%d'))
        fy_entry['updated'] = datetime.now().strftime('%Y-%m-%d')
        config['fiscal_years'][existing_idx] = fy_entry
        print(f"✓ Updated {fy_info['year']}")
    else:
        fy_entry['added'] = datetime.now().strftime('%Y-%m-%d')
        config['fiscal_years'].append(fy_entry)
        print(f"✓ Added {fy_info['year']}")

    # Sort by year (descending)
    config['fiscal_years'].sort(key=lambda x: x['year'], reverse=True)

    # Set current fiscal year if not set
    if not config.get('current_fiscal_year'):
        config['current_fiscal_year'] = fy_info['year']

    # Save configuration
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n✓ Fiscal year added successfully!")
    print(f"\nNext steps:")
    print(f"  1. Generate views: python3 generate_fiscal_year.py {fy_info['year']}")
    print(f"  2. Or generate all: python3 generate_fiscal_year.py all")
    print(f"  3. View home page:  open index.html")

    return True

def list_fiscal_years():
    """List all fiscal years in the system"""
    config_file = 'fiscal_years.json'
    if not Path(config_file).exists():
        print("No fiscal years configured yet.")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    print("="*80)
    print("FISCAL YEARS IN SYSTEM")
    print("="*80)

    for fy in config['fiscal_years']:
        is_current = fy['year'] == config['current_fiscal_year']
        marker = '⭐ CURRENT' if is_current else ''
        print(f"\n{fy['year']}: {fy['label']} {marker}")
        print(f"  Period: {fy['period']}")
        print(f"  Budget File: {fy['master_budget_file']}")
        print(f"  Status: {fy['status']}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Add fiscal year:  python3 add_fiscal_year.py FY26 /path/to/budget.xlsx")
        print("  List all years:   python3 add_fiscal_year.py list")
        print("  Set current year: python3 add_fiscal_year.py current FY26")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'list':
        list_fiscal_years()
    elif command == 'current':
        if len(sys.argv) < 3:
            print("Usage: python3 add_fiscal_year.py current FY26")
            sys.exit(1)
        year_code = sys.argv[2].upper()
        with open('fiscal_years.json', 'r') as f:
            config = json.load(f)
        config['current_fiscal_year'] = year_code
        with open('fiscal_years.json', 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Set current fiscal year to {year_code}")
    else:
        if len(sys.argv) < 3:
            print("Usage: python3 add_fiscal_year.py FY26 /path/to/budget.xlsx")
            sys.exit(1)
        year_code = sys.argv[1]
        budget_file = sys.argv[2]
        add_fiscal_year(year_code, budget_file)

if __name__ == '__main__':
    main()
