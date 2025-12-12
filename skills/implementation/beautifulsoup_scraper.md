---
name: BeautifulSoup Web Scraper
id: beautifulsoup_scraper
version: 1.0
category: implementation
domain: [web_scraping, data_extraction, python]
task_types: [implementation, data_extraction]
keywords: [beautifulsoup, scraping, html, parsing, requests, web, extraction, lxml, css, selectors, xpath]
complexity: normal
pairs_with: [api_development, databases]
external_dependencies:
  - type: python_package
    name: beautifulsoup4
    description: HTML/XML parsing library
    setup_url: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
    required: true
  - type: python_package
    name: requests
    description: HTTP library for making web requests
    setup_url: https://docs.python-requests.org/
    required: true
  - type: python_package
    name: lxml
    description: Fast XML/HTML parser (optional but recommended)
    setup_url: https://lxml.de/
    required: false
---

# BeautifulSoup Web Scraper

## Role

Expert in static HTML parsing and data extraction using Python's BeautifulSoup library. Specializes in scraping structured data from web pages, parsing feeds, and extracting content from HTML/XML documents. Use this skill when you need to extract data from static web pages, parse HTML content, or build web scraping solutions.

## Pre-Flight Check (MANDATORY)

**You MUST run this check before using this skill. Do NOT skip.**

```bash
# Check for required Python packages
python3 -c "import bs4; import requests; print('✓ beautifulsoup4 and requests are installed')" 2>/dev/null || {
    echo "✗ Required packages are NOT installed - CANNOT PROCEED"
    echo ""
    echo "This skill requires BeautifulSoup4 and requests."
    echo "Setup instructions:"
    echo "  1. Install using pip:"
    echo "     pip install beautifulsoup4 requests"
    echo "  2. Optional (recommended for better performance):"
    echo "     pip install lxml"
    echo ""
    echo "STOP: Report this task as BLOCKED with the above instructions."
    exit 1
}

# Check for optional lxml parser
python3 -c "import lxml" 2>/dev/null && echo "✓ lxml parser available (optimal)" || echo "⚠ lxml not installed (using html.parser)"
```

**If the check fails:**
1. Do NOT attempt to proceed with the task
2. Do NOT try workarounds or alternative approaches
3. Report the task as **BLOCKED** in your handoff
4. Include the setup instructions in your blocker notes
5. The orchestrator will surface this to the user

## Core Competencies

- Static HTML parsing and content extraction using BeautifulSoup
- CSS selectors and tag-based navigation for precise data targeting
- HTTP requests with session management and header configuration
- Error handling for network failures and malformed HTML
- Rate limiting and respectful scraping practices
- Parsing multiple content types (HTML, XML, RSS/Atom feeds)
- Data cleaning and normalization after extraction
- Handling pagination and multi-page scraping workflows

## Patterns and Standards

### Basic Scraping Pattern

```python
import requests
from bs4 import BeautifulSoup
from typing import Optional

def scrape_page(url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
    """
    Fetch and parse a web page.

    Args:
        url: Target URL to scrape
        timeout: Request timeout in seconds

    Returns:
        BeautifulSoup object or None if request fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; VulnDash/1.0; +http://example.com/bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Use lxml parser if available, fallback to html.parser
        return BeautifulSoup(response.content, 'lxml')

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
```

**When to use**: Basic page scraping with proper error handling and headers.

### CSS Selector Extraction

```python
def extract_with_selectors(soup: BeautifulSoup) -> dict:
    """
    Extract data using CSS selectors - most readable approach.
    """
    data = {}

    # Single element
    title = soup.select_one('h1.title')
    data['title'] = title.get_text(strip=True) if title else None

    # Multiple elements
    links = soup.select('a.article-link')
    data['links'] = [
        {
            'text': link.get_text(strip=True),
            'href': link.get('href'),
            'title': link.get('title', '')
        }
        for link in links
    ]

    # Attribute extraction
    images = soup.select('img.thumbnail')
    data['images'] = [img.get('src') for img in images if img.get('src')]

    return data
```

**When to use**: When HTML has classes/IDs (most modern websites). CSS selectors are more readable than tag-based navigation.

### Tag Navigation Pattern

```python
def extract_with_navigation(soup: BeautifulSoup) -> dict:
    """
    Extract data using tag navigation - useful for simple or older HTML.
    """
    data = {}

    # Find first occurrence
    title = soup.find('h1')
    data['title'] = title.string if title else None

    # Find all with filters
    paragraphs = soup.find_all('p', class_='content')
    data['content'] = [p.get_text(strip=True) for p in paragraphs]

    # Recursive search
    table = soup.find('table', id='data-table')
    if table:
        rows = table.find_all('tr')
        data['table_rows'] = len(rows)

        # Extract table data
        data['table_data'] = []
        for row in rows[1:]:  # Skip header
            cells = row.find_all('td')
            data['table_data'].append([cell.get_text(strip=True) for cell in cells])

    return data
```

**When to use**: Simple HTML structures, when CSS classes are unreliable, or for structured data like tables.

### Rate-Limited Scraping with Sessions

```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class RespectfulScraper:
    """
    Web scraper with rate limiting and retry logic.
    """

    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        self.delay = delay
        self.last_request_time = 0

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; VulnDashBot/1.0)',
        })

    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL with rate limiting."""
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            self.last_request_time = time.time()

            return BeautifulSoup(response.content, 'lxml')

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

# Usage
with RespectfulScraper(delay=2.0) as scraper:
    for url in urls:
        soup = scraper.fetch(url)
        if soup:
            # Extract data
            pass
```

**When to use**: Production scraping, scraping multiple pages, being respectful to target servers.

### RSS/Atom Feed Parsing

```python
def parse_feed(url: str) -> list[dict]:
    """
    Parse RSS or Atom feed.
    BeautifulSoup handles XML feeds well.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'xml')  # Use xml parser

        items = []
        for entry in soup.find_all(['item', 'entry']):  # RSS uses 'item', Atom uses 'entry'
            item = {
                'title': None,
                'link': None,
                'description': None,
                'published': None,
            }

            # Handle RSS
            if entry.find('title'):
                item['title'] = entry.find('title').get_text(strip=True)
            if entry.find('link'):
                item['link'] = entry.find('link').get_text(strip=True)
            if entry.find('description'):
                item['description'] = entry.find('description').get_text(strip=True)
            if entry.find('pubDate'):
                item['published'] = entry.find('pubDate').get_text(strip=True)

            # Handle Atom (alternative tags)
            if entry.find('summary') and not item['description']:
                item['description'] = entry.find('summary').get_text(strip=True)
            if entry.find('updated') and not item['published']:
                item['published'] = entry.find('updated').get_text(strip=True)

            items.append(item)

        return items

    except Exception as e:
        print(f"Error parsing feed {url}: {e}")
        return []
```

**When to use**: Parsing vulnerability feeds, blog RSS feeds, news feeds.

### Robust Data Extraction with Validation

```python
from typing import List, Dict, Any
import re

def extract_vulnerability_data(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Extract vulnerability data with validation and cleaning.
    Example for a hypothetical CVE listing page.
    """
    vulns = []

    for vuln_div in soup.select('div.vulnerability-item'):
        try:
            # Extract CVE ID with validation
            cve_id = vuln_div.select_one('.cve-id')
            cve_text = cve_id.get_text(strip=True) if cve_id else ''

            # Validate CVE format
            cve_match = re.match(r'CVE-\d{4}-\d{4,}', cve_text)
            if not cve_match:
                print(f"Invalid CVE format: {cve_text}")
                continue

            # Extract severity with fallback
            severity_elem = vuln_div.select_one('.severity')
            severity = severity_elem.get_text(strip=True).upper() if severity_elem else 'UNKNOWN'

            # Validate severity
            valid_severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']
            if severity not in valid_severities:
                severity = 'UNKNOWN'

            # Extract CVSS score
            cvss_elem = vuln_div.select_one('.cvss-score')
            cvss_score = None
            if cvss_elem:
                try:
                    cvss_score = float(cvss_elem.get_text(strip=True))
                    if not (0.0 <= cvss_score <= 10.0):
                        cvss_score = None
                except ValueError:
                    pass

            # Extract description with HTML cleaning
            desc_elem = vuln_div.select_one('.description')
            description = ''
            if desc_elem:
                # Remove extra whitespace and newlines
                description = ' '.join(desc_elem.get_text().split())

            # Extract links
            links = []
            for link in vuln_div.select('a.reference-link'):
                href = link.get('href')
                if href and href.startswith('http'):
                    links.append(href)

            vulns.append({
                'cve_id': cve_match.group(0),
                'severity': severity,
                'cvss_score': cvss_score,
                'description': description,
                'references': links,
            })

        except Exception as e:
            print(f"Error parsing vulnerability item: {e}")
            continue

    return vulns
```

**When to use**: Production data extraction where data quality is critical (vulnerability dashboards, security feeds).

### Pagination Handling

```python
def scrape_paginated_site(base_url: str, max_pages: int = 10) -> list:
    """
    Handle pagination patterns.
    """
    all_data = []

    with RespectfulScraper(delay=2.0) as scraper:
        page = 1

        while page <= max_pages:
            url = f"{base_url}?page={page}"
            soup = scraper.fetch(url)

            if not soup:
                break

            # Extract data from current page
            items = soup.select('.item')
            if not items:
                # No more items, stop pagination
                break

            for item in items:
                # Extract item data
                data = {
                    'title': item.select_one('.title').get_text(strip=True),
                    'link': item.select_one('a').get('href'),
                }
                all_data.append(data)

            # Check for "next page" link
            next_link = soup.select_one('a.next-page')
            if not next_link or 'disabled' in next_link.get('class', []):
                break

            page += 1

    return all_data
```

**When to use**: Scraping sites with multiple pages of results.

## Quality Standards

- **Always set User-Agent headers** to identify your bot and provide contact information
- **Implement rate limiting** - default to 1-2 seconds between requests minimum
- **Handle errors gracefully** - network failures, timeouts, malformed HTML should not crash
- **Validate extracted data** - check formats, ranges, required fields before storing
- **Respect robots.txt** - check and follow site crawling rules
- **Use appropriate parsers** - lxml for speed, html.parser for built-in, html5lib for strict HTML5
- **Clean extracted text** - strip whitespace, remove HTML entities, normalize unicode
- **Log scraping activity** - track URLs, timestamps, errors for debugging

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| No rate limiting | Overloads servers, risks IP ban | Use time.sleep() or RespectfulScraper pattern |
| Generic User-Agent | Looks like bot, may be blocked | Set descriptive User-Agent with contact info |
| No error handling | Crashes on network failures | Wrap in try/except, validate responses |
| Storing raw HTML | Wastes space, hard to query | Extract and validate data before storing |
| Using BeautifulSoup for JavaScript-rendered content | Won't work - BS only parses static HTML | Use Selenium/Playwright or find API endpoint |
| No request timeout | Hangs indefinitely on slow servers | Always set timeout parameter |
| Hardcoded selectors without validation | Breaks when site changes | Check if elements exist before extracting |

## Decision Framework

When choosing a scraping approach:

1. **Consider**: Is the content static HTML or JavaScript-rendered?
   - Static HTML → BeautifulSoup (this skill)
   - JavaScript-rendered → Selenium/Playwright (different skill)

2. **Evaluate**: What's the site structure?
   - Modern with CSS classes → Use CSS selectors (`.select()`)
   - Simple/legacy → Use tag navigation (`.find()`, `.find_all()`)
   - Well-structured data → Look for tables, lists
   - Complex nested → Build navigation from parent to child elements

3. **Choose based on**:
   - Volume: Single page vs. large-scale scraping
   - Frequency: One-time vs. recurring scraping
   - Legal: Check terms of service and robots.txt
   - Alternative: Is there an API available? Use API instead of scraping

## Output Expectations

When this skill is applied, the agent should:

- [ ] Install and verify required packages (beautifulsoup4, requests, lxml)
- [ ] Set appropriate User-Agent and headers for respectful scraping
- [ ] Implement error handling for network and parsing failures
- [ ] Add rate limiting for multi-page scraping
- [ ] Validate and clean extracted data before storing
- [ ] Document CSS selectors or navigation logic used
- [ ] Include example usage and test cases
- [ ] Handle edge cases (missing elements, malformed HTML, empty pages)

## Example Task

**Objective**: Scrape CVE vulnerability data from the NVD recent vulnerabilities page.

**Approach**:
1. Analyze the target page HTML structure to identify selectors
2. Create a RespectfulScraper with 2-second delays
3. Parse the page and extract CVE IDs, descriptions, CVSS scores
4. Validate data format (CVE-YYYY-NNNNN pattern, CVSS 0-10 range)
5. Handle pagination if multiple pages of results exist
6. Store cleaned data in structured format (JSON/database)
7. Log scraping activity and any errors encountered

**Output**: Python script that extracts validated vulnerability data, handles errors gracefully, respects rate limits, and returns structured data ready for database insertion or API serving.

---

## When NOT to Use BeautifulSoup

- **JavaScript-heavy sites**: If content loads via JavaScript after page load
  - Use Selenium, Playwright, or Puppeteer instead
  - Or find the underlying API the JavaScript calls

- **Sites with APIs**: If an official API exists
  - Always prefer APIs over scraping
  - APIs are more stable and legally safer

- **Dynamic content**: Real-time data, live updates, websockets
  - Use appropriate real-time client libraries

- **Sites that explicitly prohibit scraping**: Check terms of service and robots.txt
  - Respect legal boundaries
  - Contact site owners for permission or API access

## Vulnerability Scanning Use Cases

BeautifulSoup is excellent for:

- **Parsing CVE feeds** from NVD, MITRE, vendor security pages
- **Extracting vulnerability data** from security advisories
- **Scraping RSS/Atom feeds** of security blogs and bulletins
- **Processing HTML reports** from security tools
- **Parsing structured security data** from HTML tables/lists

---

*Skill Version: 1.0*
*Last Updated: December 2024*
