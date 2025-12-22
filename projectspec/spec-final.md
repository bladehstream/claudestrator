# VulnDash - Technical Specification

**Version:** 1.0.0  
**Generated:** December 21, 2025 at 01:45 AM GMT+10:30  

## Table of Contents

- [Overview](#overview)
- [Users and Actors](#users-and-actors)
- [Core Functionality](#core-functionality)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [API Contracts](#api-contracts)
- [User Flows](#user-flows)
- [Security](#security)
- [Deployment](#deployment)
- [Decisions](#decisions)
- [Acceptance Criteria](#acceptance-criteria)


---


## Overview

Cybersecurity analysts need a centralized dashboard to aggregate, filter, and prioritize vulnerability data from multiple sources.


### Context

Analysts face thousands of new CVEs monthly across fragmented sources (NVD, vendor advisories, RSS feeds, security blogs). Manual correlation against their product inventory is time-consuming and error-prone. CVSS scores alone don't indicate real-world exploitation likelihood.


### Motivation

Reduce time-to-insight for vulnerability management by automating source aggregation, LLM-powered data extraction, product matching, and threat prioritization (KEV + EPSS) in a single modern dashboard.


### Constraints


### Out of Scope

- User authentication and authorization (deferred - design for segregation only)
- Multi-user support and role-based access control
- Mobile applications (responsive web only)
- SIEM integration (Splunk, Sentinel webhooks)
- Ticket system integration (Jira, ServiceNow)
- Vulnerability scanning of assets
- Asset discovery and automatic inventory
- Compliance mapping (PCI, HIPAA, SOC2)
- Paid threat intelligence feed integration
- Public API for external consumers
- Detailed audit logging
- Multi-tenancy
- SSO/SAML/enterprise identity providers
- Real-time WebSocket updates (HTMX polling is sufficient)
- PDF/scheduled report generation



---


## Users and Actors

### Security Analyst

Primary user. SOC analyst or vulnerability management specialist monitoring vulnerability feeds, assessing relevance to their environment, and prioritizing remediation.


**Goals:**

- See all relevant vulnerabilities affecting configured products in one place
- Filter and sort by severity, EPSS score, KEV status, vendor, product
- Quickly identify high-priority vulnerabilities requiring immediate attention
- Understand trends in vulnerability activity over time


### Administrator

Configures the system. Manages data sources, product inventory, LLM settings, and reviews low-confidence LLM extractions.


**Goals:**

- Add and configure vulnerability data sources (NVD, KEV, RSS, custom APIs)
- Manage product inventory for vulnerability matching
- Configure Ollama LLM connection and model selection
- Review and remediate low-confidence LLM extractions
- Monitor data source health and troubleshoot failures



---


## Core Functionality

| Feature | Description | Priority |
|---|---|---|
| Vulnerability Dashboard | Main view displaying KPI cards (total vulns, KEV count, high EPSS, new today/week), a filterable vulnerability table, and trend charts. All components are responsive to filter selections. | 🔴 Must Have |
| Vulnerability Table with Filters | Sortable table of curated vulnerabilities with columns for CVE ID, Vendor, Product, CVSS severity, EPSS score, KEV status, and date. Filters for CVE search, vendor, product, severity, EPSS threshold, and KEV-only toggle. | 🔴 Must Have |
| Filter-Responsive Statistics | All KPI cards, trend charts, and summary statistics dynamically update based on the currently applied filters. User sees statistics only for the filtered dataset. | 🔴 Must Have |
| Trend Chart | Animated line/area chart showing vulnerability count over time (per day). Responsive to filters. Dark cyberpunk aesthetic matching overall theme. | 🔴 Must Have |
| Data Source Management | Admin page to configure fixed sources (NVD, CISA KEV) and add custom sources (RSS feeds, APIs, URL scraping). Per-source polling interval (1-72 hours), enable/disable toggle, manual poll trigger, health status display. | 🔴 Must Have |
| Product Inventory Management | Admin page to manage products being monitored. Search and import from NVD CPE dictionary (synced weekly). Add custom vendor/product entries. Vulnerabilities are filtered at display time against this inventory. | 🔴 Must Have |
| LLM Integration (Ollama) | Configure Ollama server endpoint, test connection, discover and select models. LLM processes raw ingested entries to extract structured vulnerability data (CVE ID, vendor, product, severity, description). | 🔴 Must Have |
| Two-Table Async Processing | Raw entries from feeds stored in raw_entries table. Background LLM job processes entries on configurable schedule (1-60 min) or manual trigger, extracts structured data, deduplicates, and moves to curated vulnerabilities table. Raw entries purged after successful processing. | 🔴 Must Have |
| EPSS Enrichment | Separate background job queries FIRST.org EPSS API to enrich curated CVEs with exploitation probability scores. Scriptable, not LLM-based. | 🔴 Must Have |
| Low-Confidence Review Queue | Admin page showing LLM extractions with low confidence scores marked as needs_review. Admin can delete or manually classify entries. | 🔴 Must Have |
| Source Health Monitoring | Admin console displays health status for each source with visual indicators (highlight + warning icon for failures). Sources retry on schedule up to 20 consecutive failures before considered persistently failing. | 🔴 Must Have |
| Authentication (Deferred) | Design admin pages with segregation to allow authentication to be added later. Do not implement auth for MVP, but ensure admin routes are separable. | 🟢 Nice to Have |
| Mark as Remediated | Allow marking vulnerabilities as remediated to track status. | 🟢 Nice to Have |
| Export Filtered View | Export current filtered vulnerability list to CSV or JSON. | 🟢 Nice to Have |
| Email Notifications | Alert on new KEV or high-EPSS vulnerabilities. | 🟢 Nice to Have |
| Multi-LLM Support | Support for Claude, Gemini APIs alongside Ollama. | 🟢 Nice to Have |
| Intelligence Page | Threat intelligence view with critical advisories, recent exploits feed, mitigation coverage stats, and vendor advisory feed. Placeholder in MVP with full implementation deferred. | 🟢 Nice to Have |


---


## Architecture

{
  "overview": "A three-tier 'Collector-Processor-Viewer' architecture designed for fault isolation and low-latency presentation. Ingestion and LLM processing are decoupled from the web layer via a shared persistent store and background job orchestration.",
  "components": [
    {
      "name": "Web/API Server",
      "purpose": "Serves the dashboard UI via Jinja2, handles HTMX partial updates, and manages Admin operations.",
      "technology": "FastAPI, HTMX, Jinja2",
      "interfaces": [
        "REST API",
        "HTMX Fragments",
        "Web UI"
      ]
    },
    {
      "name": "Background Worker",
      "purpose": "Orchestrates multi-source polling, LLM extraction (Ollama), and EPSS API enrichment. Runs as a separate container in production to ensure UI responsiveness.",
      "technology": "APScheduler, Taskiq",
      "interfaces": [
        "Internal Database access",
        "Ollama REST API",
        "External Security APIs"
      ]
    },
    {
      "name": "LLM Engine",
      "purpose": "Processes raw text from RSS/custom APIs to extract structured vulnerability data (CVE, Vendor, Product).",
      "technology": "Ollama (local/network-based)",
      "interfaces": [
        "Ollama API (v1/generate)"
      ]
    },
    {
      "name": "Persistence Layer",
      "purpose": "Stores configuration, raw entries, curated vulnerabilities, and the massive CPE dictionary.",
      "technology": "PostgreSQL (Prod) / SQLite (Dev) with FTS5",
      "interfaces": [
        "SQLAlchemy 2.0 (Async)"
      ]
    },
    {
      "name": "Reverse Proxy",
      "purpose": "TLS termination, static asset caching, and basic auth for the admin sub-paths.",
      "technology": "Nginx / Caddy",
      "interfaces": [
        "HTTPS (Port 443)"
      ]
    }
  ],
  "communication_patterns": "Asynchronous background jobs for ingestion; synchronous internal API calls for LLM processing; RESTful API with HTMX Fragments for front-to-back UI state changes.",
  "diagrams": "[Data Sources] --(Poll)--> [RawEntry Table] --(LLM/Worker)--> [Review Queue] --(Admin)--> [Curated Table] <--(HTMX)--> [Web Dashboard]"
}


---


## Data Model

{
  "entities": [
    {
      "name": "DataSource",
      "description": "Configuration for external feeds (NVD, RSS, Custom API).",
      "key_attributes": [
        "id",
        "source_type",
        "url",
        "polling_interval",
        "auth_config_encrypted",
        "is_enabled"
      ],
      "relationships": [
        "One-to-many with RawEntry"
      ]
    },
    {
      "name": "RawEntry",
      "description": "Staging table for ingested data before processing. 7-day retention policy after processing.",
      "key_attributes": [
        "id",
        "source_id",
        "raw_payload",
        "ingested_at",
        "processing_status"
      ],
      "relationships": [
        "Linked to Vulnerability post-extraction"
      ]
    },
    {
      "name": "Vulnerability",
      "description": "Core structured vulnerability record.",
      "key_attributes": [
        "cve_id (PK)",
        "cvss_score",
        "epss_score",
        "kev_status",
        "confidence_score",
        "needs_review",
        "remediated_at"
      ],
      "relationships": [
        "Many-to-Many with Product via VulnerabilityProduct"
      ]
    },
    {
      "name": "Product",
      "description": "Inventory from NVD CPE Dictionary (1M+ items).",
      "key_attributes": [
        "id",
        "cpe_uri",
        "vendor",
        "product_name",
        "is_monitored"
      ],
      "relationships": [
        "Many-to-Many with Vulnerability"
      ]
    },
    {
      "name": "VulnerabilityProduct",
      "description": "Association table for M:N mapping.",
      "key_attributes": [
        "vulnerability_id",
        "product_id"
      ],
      "relationships": [
        "Composite primary key, indexed on both IDs"
      ]
    }
  ],
  "storage_recommendations": "SQLite for dev (using FTS5 for product search); PostgreSQL for production. Partition 'Vulnerability' and 'VulnerabilityProduct' tables by 'published_date' (Yearly) once records exceed 100k to maintain query performance.",
  "data_flow": "Ingestion -> RawEntry -> LLM Processor -> Confidence Heuristic -> Review Queue (if < 0.8) -> Curated Vulnerabilities Table."
}


---


## API Contracts

{
  "style": "RESTful with HTML Fragment support (HTMX) and JSON for telemetry.",
  "endpoints": [
    {
      "method": "GET",
      "path": "/api/vulnerabilities",
      "purpose": "Returns filtered vulnerability list.",
      "request_shape": "Query: ?vendor=&product=&min_epss=&kev_only=true",
      "response_shape": "HTML Table Fragments for HTMX hx-swap."
    },
    {
      "method": "GET",
      "path": "/api/trends",
      "purpose": "Aggregated time-series data for charts.",
      "request_shape": "None",
      "response_shape": "JSON: { labels: string[], datasets: { data: number[] } }"
    },
    {
      "method": "GET",
      "path": "/admin/llm/models",
      "purpose": "Discovers available models on the Ollama instance.",
      "request_shape": "None",
      "response_shape": "JSON: [ 'llama3', 'mistral', 'phi3' ]"
    },
    {
      "method": "POST",
      "path": "/admin/review-queue/{id}/approve",
      "purpose": "Manual override and promotion of extracted data.",
      "request_shape": "JSON: { edited_fields: { ... } }",
      "response_shape": "JSON: { status: 'success' }"
    },
    {
      "method": "GET",
      "path": "/export",
      "purpose": "Dumps current filtered view for reporting.",
      "request_shape": "Query params (same as /api/vulnerabilities)",
      "response_shape": "CSV or JSON File"
    }
  ],
  "authentication": "Logical route segregation (/admin/*). Reverse-proxy basic auth recommended for MVP; FastAPI middleware ready for future JWT/Session auth."
}


---


## User Flows

[
  {
    "name": "Vulnerability Triage",
    "actor": "Security Analyst",
    "steps": [
      "Dashboard loads with KPI cards (Total, KEV, High EPSS)",
      "Analyst applies 'KEV-only' filter via HTMX toggle",
      "Analyst selects high-priority CVE to view full extraction details",
      "Analyst marks 'Remediated' to remove from active view"
    ],
    "happy_path": "Relevant vulnerabilities identified and status updated within 60 seconds.",
    "error_cases": [
      "Chart data fails to load (show placeholder)",
      "Empty filtered results"
    ]
  },
  {
    "name": "Admin Data Maintenance",
    "actor": "Administrator",
    "steps": [
      "Admin enters Review Queue to see low-confidence extractions",
      "Admin compares raw source text vs LLM structured fields",
      "Admin fixes a minor hallucination (e.g., wrong vendor name)",
      "Admin clicks 'Approve', moving record to curated table"
    ],
    "happy_path": "Human correction ensures high-quality data for non-standard RSS feeds.",
    "error_cases": [
      "Ollama connection timeout",
      "Duplicate record detected"
    ]
  }
]


---


## Security

{
  "authentication": "Admin-only routes segregated by path for firewall/proxy rules.",
  "authorization": "Path-based (Analyst: /dashboard, /api; Admin: /admin, /sources).",
  "data_protection": "Sensitive credentials (API keys) stored using Fernet symmetric encryption. TLS 1.3 enforced for all external traffic.",
  "compliance_notes": "No PII stored; ephemeral storage for raw third-party content (7-day purge).",
  "threat_model": "Mitigations: URL validation for SSRF, JSON schema validation for LLM outputs to prevent prompt injection payload execution, and server-side aggregation to prevent DB DoS."
}


---


## Deployment

{
  "infrastructure": "Docker Compose (Web, Worker, Postgres, Ollama, Nginx).",
  "scaling_strategy": "Horizontal scaling for Web pods; vertical scaling for Ollama/Worker based on ingestion volume; Shared PG job store for task coordination.",
  "monitoring": "Prometheus metrics for job latency/failure; HTMX error handling via 'hx-on::after-request' toasts.",
  "ci_cd": "GitHub Actions for Pytest, Playwright (UI testing), and multi-arch Docker builds."
}


---


## Decisions

### AMB-1

**Decision:** Prioritize format validation (regex for CVEs) over LLM self-rating


**Rationale:** Heuristic format checks are deterministic and reliable; LLM self-assessment can be overconfident or inconsistent. Format validation catches obvious errors before trusting LLM output.


### AMB-2

**Decision:** Use database lock via DataSource.is_running flag to prevent concurrent jobs


**Rationale:** DB-level flag provides persistence across worker restarts and visibility for debugging. Simple to implement and query.



---


## Acceptance Criteria

1. Dashboard loads in under 2 seconds with 1000+ vulnerabilities
2. All KPIs, charts, and table update within 500ms when filters change
3. LLM extraction achieves >90% accuracy on structured fields (CVE ID, vendor, product)
4. NVD/KEV polling runs reliably on schedule with proper error handling
5. Admin can configure a new RSS source and see extracted vulnerabilities within one LLM processing cycle
6. Low-confidence extractions surface in review queue for manual remediation
7. Browser-based testing via Claude-in-Chrome validates all UI flows work correctly
8. Clean dark cyberpunk aesthetic that looks distinct from generic dashboards



---


_Generated by Council Spec_
