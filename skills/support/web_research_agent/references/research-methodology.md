# Research Methodology

## Content Priority Framework

When researching a topic, prioritize capturing these content types in order:

### Tier 1: Primary Sources (Highest Value)
- Official documentation, specifications, whitepapers
- Government/regulatory publications (.gov domains)
- Academic papers and peer-reviewed content
- Company announcements, SEC filings, press releases
- Original data sets, statistics from authoritative sources

### Tier 2: Expert Analysis
- Industry analyst reports (Gartner, Forrester, etc.)
- Technical blogs from recognized practitioners
- Conference presentations and recorded talks
- Vendor-neutral comparison sites

### Tier 3: Community Knowledge
- Stack Overflow answers (check vote counts and dates)
- GitHub issues and discussions
- Reddit threads (verify claims independently)
- Forum discussions from domain experts

### Tier 4: General Coverage
- News articles (note publication date and potential bias)
- Wikipedia (use as starting point, follow citations)
- Aggregator sites (verify original source)

## Visual Capture Priorities

When deciding what to screenshot vs. text-extract:

**Always Screenshot:**
- Charts, graphs, visualizations (data relationships)
- Dashboards and UI layouts (spatial organization matters)
- Architecture diagrams, flowcharts
- Comparison tables with complex formatting
- Infographics
- Error messages and UI states (for troubleshooting research)

**Text Extract is Sufficient:**
- Article body text
- Documentation prose
- Code snippets (better as text for searchability)
- Simple lists and tables
- Metadata (titles, dates, authors)

**Capture Both When:**
- Page layout affects interpretation
- Visual hierarchy conveys priority/importance
- Content includes inline images with text
- Researching UX/design patterns

## Source Evaluation Checklist

Before including a source in synthesis, verify:

1. **Currency**: When was it published/updated? Is this time-sensitive info?
2. **Authority**: Who wrote it? What's their expertise? Is this their domain?
3. **Accuracy**: Can claims be verified? Are sources cited?
4. **Purpose**: Is this informational, promotional, or persuasive?
5. **Bias**: What perspective does the source represent? What might they omit?

## Research Patterns by Task Type

### Competitive Analysis
- Capture: Pricing pages, feature matrices, product screenshots
- Extract: Marketing copy (for positioning analysis), changelog/release notes
- Look for: G2/Capterra reviews, analyst quadrants, comparison articles

### Technical Evaluation
- Capture: Architecture diagrams, benchmark results, config examples
- Extract: Documentation, API references, GitHub READMEs
- Look for: Production case studies, migration guides, known limitations

### Market Research
- Capture: Market size charts, trend graphs, demographic breakdowns
- Extract: Report summaries, methodology descriptions
- Look for: Multiple sources for cross-validation, date consistency

### Troubleshooting/Debug Research
- Capture: Error screenshots, log outputs, UI states
- Extract: Stack traces, error codes, config files
- Look for: GitHub issues, vendor knowledge bases, dated solutions (check version relevance)

### Security Research
- Capture: Vulnerability timelines, attack diagrams, affected version matrices
- Extract: CVE details, patch notes, mitigation steps
- Look for: NVD entries, vendor advisories, proof-of-concept availability (note responsibly)

## Synthesis Guidelines

### Structuring Findings

1. **Lead with conclusions**: State the answer/recommendation first
2. **Evidence hierarchy**: Primary sources before secondary analysis
3. **Conflicting information**: Note disagreements explicitly, explain which source to trust and why
4. **Gaps**: Acknowledge what couldn't be determined
5. **Recency**: Flag if findings may be outdated for fast-moving topics

### Citation Practices

- Always note source URL and capture date
- For statistics: include methodology caveats if known
- For opinions: attribute to specific author/org, not "sources say"
- Distinguish between: fact, expert consensus, majority opinion, minority view, speculation

### Red Flags to Note

When capturing research, flag these issues for human review:

- Single-source claims for important facts
- Circular citations (A cites B cites A)
- Outdated information on fast-changing topics
- Promotional content disguised as analysis
- Missing methodology for statistics
- Extraordinary claims without extraordinary evidence

## Workflow Integration

### Before Starting Research
1. Clarify the research question—what decision does this inform?
2. Identify what "good enough" looks like (depth vs. breadth tradeoff)
3. List known authoritative sources for this domain

### During Capture
1. Start with authoritative sources (Tier 1)
2. Screenshot visual content, extract text for prose
3. Note source metadata (URL, date, author) with each capture
4. Flag contradictions or surprising claims for deeper investigation

### After Capture
1. Review for gaps in the original question
2. Cross-validate key claims across sources
3. Synthesize with explicit confidence levels
4. Provide source links for verification

## Domain-Specific Guidance

### Cybersecurity Research
- Prioritize: NIST, CISA, vendor security advisories, CVE databases
- Verify: Exploit dates, affected versions, patch availability
- Caution: PoC code sharing, avoid reproducing attack details unnecessarily

### Financial/FinTech Research
- Prioritize: SEC filings, regulatory guidance, central bank publications
- Verify: Numbers against primary filings, check for restatements
- Caution: Forward-looking statements, promotional content from vendors

### Technical/Development Research
- Prioritize: Official docs, GitHub repos, RFCs/specifications
- Verify: Version compatibility, deprecation status, last update date
- Caution: Outdated tutorials, copy-paste security vulnerabilities

### Healthcare/Medical Research
- Prioritize: PubMed, NIH, WHO, peer-reviewed journals
- Verify: Study methodology, sample sizes, conflict of interest disclosures
- Caution: Never provide medical advice, always note "consult professional"
