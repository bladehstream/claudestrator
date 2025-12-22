# VulnDash - Vulnerability Dashboard

A dark cyberpunk-themed vulnerability management dashboard for tracking CVEs, CISA KEV entries, EPSS scores, and vulnerability trends.

## Features

### KPI Cards
- **Total Vulnerabilities**: Displays count of all vulnerabilities in the current filtered view
- **KEV Active Exploits**: Shows vulnerabilities with active exploits (CISA KEV)
- **High EPSS (>70%)**: Tracks vulnerabilities with high exploitation probability
- **New This Week**: Displays newly published vulnerabilities with today's count

### Filterable Vulnerability Table
- Sort by CVE ID, Vendor, CVSS Score, KEV Status, or Published Date
- Filter by:
  - Vendor (Microsoft, Google, Apache, etc.)
  - Severity (Critical, High, Medium, Low)
  - KEV Status (Active Exploit / No Exploit)
  - EPSS Threshold (>70%, >50%, >30%)
  - Search by CVE ID or keywords
- Pagination with configurable rows per page (10, 20, 50, 100)
- Responsive design for mobile, tablet, and desktop

### Trend Chart
- 30-day vulnerability discovery trend
- Responsive to all filter selections
- Interactive Chart.js visualization

### Dark Cyberpunk Aesthetic
- Space Grotesk font for modern tech feel
- Custom color palette: primary blue (#2b4bee), accent pink (#ff2a6d), accent cyan (#05d9e8)
- Glass-morphism panels with backdrop blur
- Neon glow effects on interactive elements
- Grid background pattern
- Smooth transitions and animations

## Usage

### Opening the Dashboard

Simply open `index.html` in a modern web browser:

```bash
# From the dashboard directory
open index.html
# or
firefox index.html
# or
google-chrome index.html
```

### Using Filters

All filters update the entire dashboard in real-time:
1. **Vendor Filter**: Select a specific vendor to view only their vulnerabilities
2. **Severity Filter**: Filter by CVSS severity rating
3. **KEV Filter**: Show only vulnerabilities with active exploits
4. **EPSS Filter**: Filter by exploitation probability threshold
5. **Search Bar**: Search for CVE IDs or keywords in descriptions

### Sorting the Table

Click any column header to sort:
- First click: Sort descending
- Second click: Sort ascending
- Supports: CVE ID, Vendor, CVSS, KEV Status, Published Date

### Pagination

Navigate through results using:
- First Page / Last Page buttons
- Previous / Next buttons
- Adjust rows per page (10, 20, 50, 100)

## Technical Stack

- **HTML5**: Semantic markup
- **Tailwind CSS**: Utility-first styling via CDN
- **Chart.js**: Trend visualization
- **Vanilla JavaScript**: No framework dependencies
- **Material Symbols**: Icon set

## Sample Data

The dashboard includes 26 realistic CVE entries with:
- Real CVE IDs from 2023
- Accurate CVSS scores and severity ratings
- Realistic EPSS scores (0-1 range)
- KEV status flags
- Vendor/product information
- Published dates

## Responsive Design

Breakpoints:
- **Mobile**: 320px+ (single column layout)
- **Tablet**: 768px+ (2-column KPI cards)
- **Desktop**: 1024px+ (4-column KPI cards, full navigation)

## Filter Responsiveness Verification

All components update based on active filters:
- ✅ KPI cards recalculate based on filtered dataset
- ✅ Trend chart updates to show only filtered vulnerabilities
- ✅ Table displays filtered and sorted results
- ✅ Pagination adjusts to filtered result count
- ✅ "No results" message when filters exclude all data

## Accessibility

- Semantic HTML structure
- ARIA labels on icon-only buttons
- Keyboard navigation support
- High contrast text (WCAG AA compliant)
- Focus indicators on interactive elements

## Future Enhancements

When integrated with backend:
- Real-time data from NVD, CISA KEV, EPSS APIs
- HTMX for server-driven partial updates
- LLM-processed vulnerability data
- Product inventory filtering
- Export to CSV/JSON
- Admin review queue for low-confidence extractions

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

See project root for license information.
