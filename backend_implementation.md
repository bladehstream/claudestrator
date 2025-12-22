# VulnDash Backend - Route Architecture Implementation (BUILD-012)

## Deliverable: FastAPI Backend with Admin Route Segregation

This document provides the complete implementation blueprint for BUILD-012: "Authentication (Deferred) - Design admin pages with segregation to allow authentication to be added later."

---

## Task Acceptance Criteria - Met By

1. **Admin routes are separable from public routes** ✓
   - Path-based segregation: `/api/*` vs `/admin/*`
   - Separate route modules: `routes/public.py` and `routes/admin.py`
   - Reverse proxy can isolate `/admin/*` independently

2. **Route structure allows auth middleware to be added later** ✓
   - FastAPI middleware hooks prepared
   - Decorator pattern ready: `@Depends(require_admin)`
   - No breaking changes when auth is implemented

3. **No actual auth implementation for MVP** ✓
   - Routes work without authentication
   - Authentication middleware is placeholder only
   - Can be enforced at reverse proxy level (Nginx/Caddy)

4. **Clear separation between admin and public endpoints** ✓
   - Public: `/api/*` - Data queries, dashboard endpoints
   - Admin: `/admin/*` - System configuration, maintenance
   - Different HTTP modules for maintainability

---

## File Structure

```
backend/
├── main.py                          # FastAPI app initialization
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── README.md                        # Setup instructions
│
├── app/
│   ├── __init__.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── public.py               # PUBLIC: /api/* routes
│   │   │   ├── GET /api/vulnerabilities
│   │   │   ├── GET /api/vulnerabilities/<cve_id>
│   │   │   ├── GET /api/trends
│   │   │   ├── GET /api/kpis
│   │   │   └── GET /api/export
│   │   │
│   │   └── admin.py                # ADMIN: /admin/* routes
│   │       ├── GET /admin/sources
│   │       ├── POST /admin/sources
│   │       ├── GET /admin/inventory
│   │       ├── GET /admin/llm/config
│   │       ├── GET /admin/review-queue
│   │       └── [See full list below]
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── cors_config.py           # CORS setup
│   │   ├── error_handler.py         # Global error handling
│   │   └── auth.py                  # [PLACEHOLDER] Future auth
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py                    # SQLAlchemy base & session
│   │   ├── vulnerability.py         # Vulnerability ORM model
│   │   ├── data_source.py           # DataSource ORM model
│   │   └── product.py               # Product ORM model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── vulnerability.py         # Pydantic schemas for responses
│   │   ├── data_source.py           # Request/response for sources
│   │   └── product.py               # Request/response for products
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py            # DB connection management
│   │   ├── migrations/              # Alembic migrations (if used)
│   │   └── seed.py                  # Test data seeding
│   │
│   └── services/
│       ├── __init__.py
│       ├── vulnerability_service.py # Business logic for vulnerabilities
│       ├── source_service.py        # Business logic for data sources
│       ├── product_service.py       # Business logic for products
│       └── llm_service.py           # LLM integration service
│
└── tests/
    ├── __init__.py
    ├── test_routes.py               # Route tests (verify segregation)
    ├── test_public_api.py           # Public endpoint tests
    ├── test_admin_routes.py         # Admin endpoint tests
    └── conftest.py                  # Pytest configuration
```

---

## Public Routes (`/api/*`)

These routes handle dashboard queries and are accessible without authentication in MVP.

### Vulnerability Queries
```
GET /api/vulnerabilities
  Query Parameters:
    - vendor: str (optional, filter by vendor)
    - product: str (optional, filter by product)
    - min_cvss: float (optional, minimum CVSS score)
    - min_epss: float (optional, minimum EPSS score)
    - kev_only: bool (optional, KEV vulnerabilities only)
    - limit: int (default: 100, max: 1000)
    - offset: int (default: 0)

  Response:
    {
      "total": 1234,
      "limit": 100,
      "offset": 0,
      "vulnerabilities": [
        {
          "cve_id": "CVE-2024-12345",
          "cvss_score": 8.5,
          "epss_score": 0.95,
          "kev_status": true,
          "vendor": "Microsoft",
          "products": ["Windows 11", "Windows Server 2022"],
          "published_date": "2024-01-15T00:00:00Z",
          "description": "..."
        }
      ]
    }


GET /api/vulnerabilities/<cve_id>
  Path Parameters:
    - cve_id: str (e.g., "CVE-2024-12345")

  Response:
    {
      "cve_id": "CVE-2024-12345",
      "cvss_score": 8.5,
      "epss_score": 0.95,
      "kev_status": true,
      "vendor": "Microsoft",
      "products": ["Windows 11", "Windows Server 2022"],
      "published_date": "2024-01-15T00:00:00Z",
      "description": "...",
      "references": ["https://example.com"],
      "remediated_at": null
    }


GET /api/trends
  Query Parameters:
    - days: int (default: 30, max: 365)
    - vendor: str (optional, filter by vendor)
    - product: str (optional, filter by product)
    - kev_only: bool (optional)

  Response:
    {
      "labels": ["2024-12-01", "2024-12-02", ...],
      "datasets": [
        {
          "label": "Total Vulnerabilities",
          "data": [100, 105, 110, ...]
        }
      ]
    }


GET /api/kpis
  Query Parameters:
    - vendor: str (optional)
    - product: str (optional)
    - kev_only: bool (optional)

  Response:
    {
      "total_vulnerabilities": 1234,
      "high_epss_count": 456,
      "kev_count": 89,
      "new_today": 12,
      "new_this_week": 67
    }


GET /api/export
  Query Parameters:
    - format: str ("csv" or "json", default: "csv")
    - vendor: str (optional)
    - product: str (optional)
    - min_epss: float (optional)
    - kev_only: bool (optional)

  Response:
    - CSV file or JSON file matching current filter selection
```

---

## Admin Routes (`/admin/*`)

These routes handle system configuration and are segregated for authentication. MVP approach: use reverse proxy authentication.

### Data Source Management
```
GET /admin/sources
  Authorization: Admin only
  Response:
    {
      "sources": [
        {
          "id": "source-nvd-001",
          "source_type": "nvd",
          "url": "https://services.nvd.nist.gov/rest/json/cves/1.0",
          "polling_interval_hours": 24,
          "is_enabled": true,
          "is_running": false,
          "last_poll_at": "2024-12-22T10:00:00Z",
          "consecutive_failures": 0,
          "health_status": "healthy"
        }
      ]
    }


POST /admin/sources
  Authorization: Admin only
  Request Body:
    {
      "source_type": "rss",
      "url": "https://example.com/feed.xml",
      "polling_interval_hours": 12,
      "auth_config": {
        "api_key": "secret_key_here",
        "auth_type": "header"
      }
    }
  Response: 201 Created
    { "id": "source-rss-002", ... }


PUT /admin/sources/<id>
  Authorization: Admin only
  Request Body: Partial update (same as POST)
  Response: 200 OK


DELETE /admin/sources/<id>
  Authorization: Admin only
  Response: 204 No Content


POST /admin/sources/<id>/poll
  Authorization: Admin only
  Purpose: Manually trigger source polling
  Response:
    {
      "job_id": "job-12345",
      "status": "queued",
      "source_id": "source-rss-002"
    }


GET /admin/sources/<id>/health
  Authorization: Admin only
  Response:
    {
      "source_id": "source-rss-002",
      "health_status": "healthy|warning|error",
      "last_poll_at": "2024-12-22T10:00:00Z",
      "consecutive_failures": 0,
      "last_error": null
    }
```

### Product Inventory Management
```
GET /admin/inventory
  Authorization: Admin only
  Query Parameters:
    - search: str (optional, search by vendor/product name)
    - is_monitored: bool (optional)
    - limit: int (default: 100)
    - offset: int (default: 0)

  Response:
    {
      "total": 1000000,  # Full NVD CPE dictionary size
      "products": [
        {
          "id": "cpe-001",
          "cpe_uri": "cpe:2.3:a:microsoft:windows:11:*:*:*:*:*:*:*",
          "vendor": "Microsoft",
          "product_name": "Windows",
          "version": "11",
          "is_monitored": true,
          "custom": false
        }
      ]
    }


POST /admin/inventory
  Authorization: Admin only
  Purpose: Add custom product not in NVD
  Request Body:
    {
      "vendor": "CustomVendor",
      "product_name": "CustomProduct",
      "version": "1.0",
      "is_monitored": true
    }
  Response: 201 Created
    { "id": "cpe-custom-001", ... }


PUT /admin/inventory/<id>
  Authorization: Admin only
  Purpose: Update monitoring status
  Request Body:
    {
      "is_monitored": true|false
    }
  Response: 200 OK


DELETE /admin/inventory/<id>
  Authorization: Admin only
  Purpose: Remove custom product
  Response: 204 No Content


GET /admin/inventory/search?q=<query>
  Authorization: Admin only
  Purpose: Full-text search using SQLite FTS5
  Response:
    {
      "results": [
        {
          "id": "cpe-001",
          "vendor": "Microsoft",
          "product_name": "Windows",
          "match_score": 0.95
        }
      ]
    }


POST /admin/inventory/sync
  Authorization: Admin only
  Purpose: Sync NVD CPE dictionary (weekly)
  Response:
    {
      "job_id": "job-sync-123",
      "status": "queued",
      "estimated_size": 1000000
    }
```

### LLM Configuration
```
GET /admin/llm/config
  Authorization: Admin only
  Response:
    {
      "ollama_base_url": "http://localhost:11434",
      "selected_model": "llama3",
      "connection_status": "connected|disconnected",
      "last_tested_at": "2024-12-22T10:00:00Z"
    }


PUT /admin/llm/config
  Authorization: Admin only
  Request Body:
    {
      "ollama_base_url": "http://localhost:11434",
      "selected_model": "mistral"
    }
  Response: 200 OK


GET /admin/llm/models
  Authorization: Admin only
  Purpose: List available models on connected Ollama instance
  Response:
    {
      "models": [
        {
          "name": "llama3",
          "size_gb": 8.0,
          "modified_at": "2024-12-01T00:00:00Z"
        },
        {
          "name": "mistral",
          "size_gb": 7.5,
          "modified_at": "2024-12-01T00:00:00Z"
        }
      ]
    }


POST /admin/llm/test-connection
  Authorization: Admin only
  Purpose: Test Ollama connection with provided config
  Request Body:
    {
      "ollama_base_url": "http://localhost:11434"
    }
  Response:
    {
      "status": "success|failure",
      "message": "Connection test result",
      "models_available": 5
    }


POST /admin/llm/select-model
  Authorization: Admin only
  Request Body:
    {
      "model_name": "llama3"
    }
  Response: 200 OK
```

### Review Queue (Low-Confidence LLM Extractions)
```
GET /admin/review-queue
  Authorization: Admin only
  Query Parameters:
    - limit: int (default: 50)
    - offset: int (default: 0)

  Response:
    {
      "total": 42,
      "items": [
        {
          "id": "review-001",
          "raw_entry_id": "raw-123",
          "extracted_data": {
            "cve_id": "CVE-2024-??",
            "vendor": "Unknown",
            "product": "UnknownProduct",
            "cvss_score": null
          },
          "confidence_score": 0.65,
          "raw_source_text": "...",
          "created_at": "2024-12-22T10:00:00Z"
        }
      ]
    }


GET /admin/review-queue/<id>
  Authorization: Admin only
  Response:
    {
      "id": "review-001",
      "extracted_data": { ... },
      "raw_source_text": "..."
    }


PUT /admin/review-queue/<id>/approve
  Authorization: Admin only
  Purpose: Approve extraction and move to curated vulnerabilities
  Request Body:
    {
      "edited_fields": {
        "cve_id": "CVE-2024-12345",  # Optional corrections
        "vendor": "Microsoft",
        "cvss_score": 7.5
      }
    }
  Response: 200 OK
    {
      "status": "approved",
      "moved_to_curated": true
    }


DELETE /admin/review-queue/<id>
  Authorization: Admin only
  Purpose: Reject extraction (don't move to curated)
  Response: 204 No Content
```

### Background Job Management
```
GET /admin/jobs
  Authorization: Admin only
  Response:
    {
      "jobs": [
        {
          "id": "job-nvd-poll",
          "name": "NVD Source Polling",
          "schedule": "0 */12 * * *",  # Every 12 hours
          "next_run": "2024-12-23T00:00:00Z",
          "last_run": "2024-12-22T12:00:00Z",
          "status": "scheduled|running|failed"
        },
        {
          "id": "job-llm-process",
          "name": "LLM Processing",
          "schedule": "*/30 * * * *",  # Every 30 minutes
          "next_run": "2024-12-22T10:30:00Z",
          "last_run": "2024-12-22T10:00:00Z",
          "status": "scheduled"
        },
        {
          "id": "job-epss-enrich",
          "name": "EPSS Enrichment",
          "schedule": "0 2 * * *",  # Daily at 2 AM
          "next_run": "2024-12-23T02:00:00Z",
          "last_run": "2024-12-22T02:00:00Z",
          "status": "scheduled"
        }
      ]
    }


POST /admin/jobs/<id>/trigger
  Authorization: Admin only
  Purpose: Manually trigger job (bypass schedule)
  Response:
    {
      "job_id": "job-nvd-poll",
      "execution_id": "exec-12345",
      "status": "queued"
    }


GET /admin/jobs/<id>/logs
  Authorization: Admin only
  Purpose: Get execution logs
  Query Parameters:
    - limit: int (default: 100)
  Response:
    {
      "job_id": "job-llm-process",
      "logs": [
        {
          "timestamp": "2024-12-22T10:00:00Z",
          "level": "INFO",
          "message": "Starting LLM processing..."
        }
      ]
    }
```

### System Monitoring
```
GET /admin/health
  Authorization: Admin only
  Response:
    {
      "status": "healthy|degraded|critical",
      "services": {
        "database": { "status": "ok", "latency_ms": 5 },
        "ollama": { "status": "ok", "latency_ms": 120 },
        "cache": { "status": "ok", "hit_rate": 0.85 }
      },
      "job_queue": {
        "pending": 0,
        "running": 1,
        "failed": 0
      }
    }


GET /admin/metrics
  Authorization: Admin only
  Purpose: Prometheus-compatible metrics
  Response:
    # HELP vulndash_vulnerabilities_total Total vulnerabilities in database
    # TYPE vulndash_vulnerabilities_total gauge
    vulndash_vulnerabilities_total 1234

    # HELP vulndash_http_requests_total Total HTTP requests
    # TYPE vulndash_http_requests_total counter
    vulndash_http_requests_total{method="GET",endpoint="/api/vulnerabilities"} 5432


GET /admin/settings
  Authorization: Admin only
  Response:
    {
      "settings": {
        "llm_processing_interval_minutes": 30,
        "raw_entry_retention_days": 7,
        "review_queue_threshold": 0.8,
        "epss_enrichment_enabled": true
      }
    }


PUT /admin/settings
  Authorization: Admin only
  Request Body:
    {
      "llm_processing_interval_minutes": 15,
      "review_queue_threshold": 0.85
    }
  Response: 200 OK
```

---

## Authentication Placeholder Implementation

File: `app/middleware/auth.py`

```python
"""
Authentication Middleware - PLACEHOLDER FOR MVP

This file contains the structure for future authentication.
In MVP, all routes are accessible without auth.
Use reverse proxy (Nginx/Caddy) for /admin/* path protection.

To implement:
1. Replace the placeholder functions with real JWT/session validation
2. Decorate admin routes with @Depends(require_admin)
3. Update route inclusion in main.py to apply auth
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer(auto_error=False)


async def require_admin(credentials = Depends(security)):
    """
    [PLACEHOLDER] Future authentication check for admin routes.

    In MVP, this is NOT enforced in code. Instead:
    - Use reverse proxy (Nginx/Caddy) with basic auth on /admin/*
    - Or manually check credentials at proxy level

    When implementing for production:
    1. Extract JWT token from credentials
    2. Validate token signature and expiration
    3. Check user has 'admin' role
    4. Return user info or raise 401

    Example implementation:

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await get_user(user_id)
        if not user or user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    """

    # MVP: No auth enforcement - routes are open
    # Future: Uncomment and implement real validation
    return {"user_id": "mvp-user", "role": "admin"}


class AuthUser:
    """[PLACEHOLDER] User model for authenticated requests."""
    def __init__(self, user_id: str, role: str = "user"):
        self.user_id = user_id
        self.role = role
        self.is_admin = role == "admin"
```

---

## How to Add Authentication Later

### Step 1: Implement JWT Middleware
```python
# app/middleware/auth.py

from fastapi import Depends, HTTPException
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

async def require_admin(credentials = Depends(security)):
    """Validate JWT and check admin role."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id or role != "admin":
            raise HTTPException(status_code=403)
        return {"user_id": user_id, "role": role}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401)
```

### Step 2: Decorate Admin Routes
```python
# app/routes/admin.py

from fastapi import Depends
from app.middleware.auth import require_admin

@admin_router.get("/sources")
async def list_sources(user = Depends(require_admin)):
    """Admin authentication required."""
    ...
```

### Step 3: Update Main App
```python
# main.py

# Include admin routes with auth dependency applied
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)]  # Applies to ALL routes
)
```

---

## Testing Route Segregation

File: `tests/test_routes.py`

```python
"""
Verify that public and admin routes are properly segregated.
"""

def test_public_routes_accessible():
    """Public routes should not require authentication."""
    response = client.get("/api/vulnerabilities")
    assert response.status_code in [200, 400]  # OK or validation error, not 401


def test_admin_routes_exist():
    """Admin routes should be defined and accessible."""
    # In MVP, no auth required
    response = client.get("/admin/sources")
    assert response.status_code in [200, 400, 500]  # Not 404


def test_admin_routes_segregated():
    """Admin routes should be under /admin/* prefix."""
    # Verify no admin functionality leaks into /api/*
    response = client.post("/api/sources")
    assert response.status_code == 404  # Should not exist


def test_admin_auth_placeholder():
    """Verify auth middleware is structured for future implementation."""
    # This tests that the auth dependency exists and can be applied
    from app.middleware.auth import require_admin
    assert callable(require_admin)
    assert hasattr(require_admin, "__call__")
```

---

## Configuration for MVP

File: `.env.example`

```env
# Database
DATABASE_URL=sqlite:///./vulndash.db
# DATABASE_URL=postgresql://user:password@localhost:5432/vulndash  # Production

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://vulndash.example.com
DEBUG=false
PORT=8000

# Ollama (LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Authentication (Future)
# JWT_SECRET_KEY=your-secret-key-here
# JWT_ALGORITHM=HS256
# JWT_EXPIRATION_HOURS=24
```

---

## Docker Setup (MVP)

File: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://vulndash:password@postgres:5432/vulndash
      OLLAMA_BASE_URL: http://ollama:11434
    depends_on:
      - postgres
      - ollama
    volumes:
      - ./backend:/app

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: vulndash
      POSTGRES_PASSWORD: password
      POSTGRES_DB: vulndash
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  ollama_data:
```

---

## Summary of Deliverables for BUILD-012

✓ **Route Segregation Design**
  - Public routes under `/api/*`
  - Admin routes under `/admin/*`
  - Separate route modules for maintainability

✓ **Authentication Middleware Structure**
  - Placeholder in `app/middleware/auth.py`
  - Ready for FastAPI `Depends()` decorator pattern
  - Clear documentation on implementation steps

✓ **No Auth Implementation for MVP**
  - Routes work without authentication
  - Reverse proxy (Nginx/Caddy) recommended for `/admin/*` protection
  - Environment variables prepared for future JWT configuration

✓ **Clear Separation Between Admin and Public Endpoints**
  - Complete endpoint specifications above
  - Different security considerations documented
  - Testing strategy for route segregation

---

**Status:** Design Complete
**Ready for:** Implementation by Backend Implementation Agent
**Next Tasks:** BUILD-001 (Dashboard UI), BUILD-005 (Data Source Management)

---

Generated: 2025-12-22
Task: BUILD-012 - Authentication (Deferred)
Agent: Backend Implementation Agent
