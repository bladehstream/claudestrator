# External Spec Category Mapping

This file defines the mapping between test categories (from test-plan-output.json) and features (from spec-final.json) for the external_spec decomposition mode.

## Test Category → Feature Mapping

| Test Category | Related Features | Description |
|---------------|------------------|-------------|
| `vulnerability-validation` | Vulnerability Dashboard, Vulnerability Table with Filters | CVE format validation, CVSS normalization, KEV status |
| `dashboard-ui` | Vulnerability Dashboard, Filter-Responsive Statistics, Trend Chart | KPI cards, table rendering, chart visualization |
| `llm-processing` | LLM Integration (Ollama), Two-Table Async Processing, Low-Confidence Review Queue | Extraction pipeline, confidence scoring, review queue |
| `data-ingestion` | Data Source Management, EPSS Enrichment, Two-Table Async Processing | NVD/KEV polling, RSS parsing, EPSS API |
| `filtering` | Vulnerability Table with Filters, Filter-Responsive Statistics | SQL generation, EPSS thresholds, multi-parameter filters |
| `admin-maintenance` | Product Inventory Management, Source Health Monitoring, Low-Confidence Review Queue, Data Source Management | Admin pages, source config, review workflow |
| `security` | *Cross-cutting* | SSRF, XSS, SQLi, encryption - depends on ALL build tasks |
| `performance` | *Cross-cutting* | Load times, throughput, concurrency - depends on ALL build tasks |

## Feature → Category Mapping (Reverse Lookup)

| Feature | Primary Category | Secondary Categories |
|---------|------------------|---------------------|
| Vulnerability Dashboard | `frontend` | dashboard-ui, vulnerability-validation |
| Vulnerability Table with Filters | `fullstack` | filtering, dashboard-ui |
| Filter-Responsive Statistics | `frontend` | dashboard-ui, filtering |
| Trend Chart | `frontend` | dashboard-ui |
| Data Source Management | `backend` | admin-maintenance, data-ingestion |
| Product Inventory Management | `backend` | admin-maintenance |
| LLM Integration (Ollama) | `backend` | llm-processing |
| Two-Table Async Processing | `backend` | llm-processing, data-ingestion |
| EPSS Enrichment | `backend` | data-ingestion |
| Low-Confidence Review Queue | `fullstack` | admin-maintenance, llm-processing |
| Source Health Monitoring | `backend` | admin-maintenance |

## Test Type Execution Order

| Test Type | When to Run | Dependencies |
|-----------|-------------|--------------|
| `unit` | After related build task(s) | Specific feature tasks |
| `integration` | After all related features complete | Multiple feature tasks |
| `e2e` | After ALL build tasks | All build tasks |
| `security` | After ALL build tasks | All build tasks |
| `performance` | After ALL build tasks | All build tasks |
| `edge_cases` | After related build task(s) | Specific feature tasks |

## Priority Mapping

| Spec Priority | Task Complexity | Model |
|---------------|-----------------|-------|
| `must_have` | `complex` | opus |
| `nice_to_have` | `normal` | sonnet |

| Test Priority | Task Complexity | Model |
|---------------|-----------------|-------|
| `critical` | `complex` | opus |
| `high` | `normal` | sonnet |
| `medium` | `normal` | sonnet |
| `low` | `easy` | haiku |
