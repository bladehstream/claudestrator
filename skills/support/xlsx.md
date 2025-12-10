---
name: Excel Spreadsheet Handler
id: xlsx
version: 1.0
category: support
domain: [documents, office, data, finance]
task_types: [implementation, analysis, creation, editing]
keywords: [xlsx, excel, spreadsheet, formula, data, analysis, financial, model, openpyxl, pandas]
complexity: [normal, complex]
pairs_with: [docx, pdf, pptx]
source: https://github.com/anthropics/skills/tree/main/skills/xlsx
---

# Excel Spreadsheet Handler

## Role

Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. Use when Claude needs to work with spreadsheets (.xlsx, .xlsm, .csv, .tsv) for creating new spreadsheets, reading/analyzing data, modifying existing files, data analysis, or recalculating formulas.

## Core Requirements

### Zero Tolerance for Errors

**Every Excel model MUST be delivered with ZERO formula errors**:
- No `#REF!`
- No `#DIV/0!`
- No `#VALUE!`
- No `#N/A`
- No `#NAME?`

### Template Respect

When modifying existing files, maintain established format rather than imposing standardized formatting.

### Use Formulas, Not Hardcoded Values

**Critical**: Use Excel formulas instead of hardcoding calculated values. This preserves dynamic recalculation when source data changes.

```python
# ❌ Bad - hardcoded value
ws['C1'] = 150  # Sum of A1:A10

# ✅ Good - formula
ws['C1'] = '=SUM(A1:A10)'
```

## Color Coding Convention (Financial Models)

| Color | Meaning |
|-------|---------|
| Blue text | User-changeable inputs |
| Black text | Formulas and calculations |
| Green text | Internal cross-sheet links |
| Red text | External file references |
| Yellow background | Key assumptions |

## Number Formatting Standards

| Type | Format | Example |
|------|--------|---------|
| Years | Text | "2024" |
| Currency | Units in header | $1,234 |
| Zeros | Dash | - |
| Percentages | 0.0% | 12.5% |
| Negatives | Parentheses | (1,234) |

## Python Libraries

### openpyxl - Full Excel Support

**Reading**:
```python
from openpyxl import load_workbook

wb = load_workbook('file.xlsx')
ws = wb.active

# Read cell
value = ws['A1'].value

# Read range
for row in ws['A1:C10']:
    for cell in row:
        print(cell.value)

# Get all sheet names
print(wb.sheetnames)
```

**Creating**:
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border

wb = Workbook()
ws = wb.active
ws.title = "Data"

# Write values
ws['A1'] = 'Header'
ws['A1'].font = Font(bold=True)

# Write formula
ws['B10'] = '=SUM(B1:B9)'

# Format numbers
ws['C1'].number_format = '#,##0.00'

wb.save('output.xlsx')
```

**Formatting**:
```python
from openpyxl.styles import Font, PatternFill, Alignment

# Blue input cells
input_font = Font(color='0000FF')
ws['A1'].font = input_font

# Yellow highlight
highlight = PatternFill(start_color='FFFF00', fill_type='solid')
ws['B1'].fill = highlight

# Percentage format
ws['C1'].number_format = '0.0%'

# Currency format
ws['D1'].number_format = '$#,##0.00'

# Center alignment
ws['E1'].alignment = Alignment(horizontal='center')
```

### pandas - Data Analysis

**Reading**:
```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx', sheet_name='Sheet1')

# Read CSV
df = pd.read_csv('file.csv')

# Read specific columns
df = pd.read_excel('file.xlsx', usecols=['A', 'B', 'C'])
```

**Analysis**:
```python
# Summary statistics
print(df.describe())

# Group and aggregate
summary = df.groupby('Category').agg({
    'Amount': ['sum', 'mean', 'count'],
    'Date': 'max'
})

# Pivot table
pivot = pd.pivot_table(
    df,
    values='Amount',
    index='Category',
    columns='Month',
    aggfunc='sum'
)
```

**Writing**:
```python
# Write to Excel
df.to_excel('output.xlsx', sheet_name='Results', index=False)

# Multiple sheets
with pd.ExcelWriter('output.xlsx') as writer:
    df1.to_excel(writer, sheet_name='Data')
    df2.to_excel(writer, sheet_name='Summary')
```

## Formula Recalculation

Excel formulas don't auto-calculate when reading. Use the recalc script:

```bash
# Requires LibreOffice
python recalc.py input.xlsx output.xlsx
```

**recalc.py**:
```python
import subprocess
import shutil
import os

def recalc_xlsx(input_path, output_path):
    """Recalculate Excel formulas using LibreOffice."""
    # Create temp directory
    temp_dir = '/tmp/xlsx_recalc'
    os.makedirs(temp_dir, exist_ok=True)

    # Copy input file
    temp_input = os.path.join(temp_dir, 'input.xlsx')
    shutil.copy(input_path, temp_input)

    # Run LibreOffice to recalculate
    subprocess.run([
        'libreoffice',
        '--headless',
        '--calc',
        '--convert-to', 'xlsx',
        '--outdir', temp_dir,
        temp_input
    ], check=True)

    # Move result
    shutil.move(temp_input, output_path)
```

## Documentation Requirements

**Hardcoded values require source citations**:
```
Source: Annual Report 2024, Page 15
Source: API response 2024-01-15
Source: User input
```

## Common Tasks

### Create Financial Model
```python
from openpyxl import Workbook
from openpyxl.styles import Font

wb = Workbook()
ws = wb.active

# Headers
headers = ['Item', '2024', '2025', '2026']
for col, header in enumerate(headers, 1):
    ws.cell(row=1, column=col, value=header)
    ws.cell(row=1, column=col).font = Font(bold=True)

# Input cells (blue)
input_font = Font(color='0000FF')
ws['B2'] = 1000  # Revenue
ws['B2'].font = input_font

# Formula cells (black)
ws['C2'] = '=B2*1.1'  # 10% growth
ws['D2'] = '=C2*1.1'
```

### Validate Formulas
```python
def check_for_errors(ws):
    """Find all error cells in worksheet."""
    errors = []
    for row in ws.iter_rows():
        for cell in row:
            if cell.value in ['#REF!', '#DIV/0!', '#VALUE!', '#N/A', '#NAME?']:
                errors.append(f"{cell.coordinate}: {cell.value}")
    return errors
```

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Read Excel | openpyxl/pandas | `pd.read_excel('f.xlsx')` |
| Write Excel | openpyxl/pandas | `df.to_excel('f.xlsx')` |
| Add formula | openpyxl | `ws['A1'] = '=SUM(B:B)'` |
| Format cell | openpyxl.styles | `cell.font = Font(bold=True)` |
| Recalculate | LibreOffice | `python recalc.py in.xlsx out.xlsx` |
| Pivot table | pandas | `pd.pivot_table(df, ...)` |

## Dependencies

```bash
pip install openpyxl pandas xlrd xlsxwriter
# For recalculation
apt install libreoffice-calc
```

---

*Skill Version: 1.0*
*Source: Anthropic xlsx skill*
