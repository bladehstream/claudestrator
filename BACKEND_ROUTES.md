# VulnDash Backend Route Architecture (BUILD-012)

## Overview

This document describes the route architecture for VulnDash, implementing segregation between public and admin routes to enable authentication middleware to be added later.

**Status:** Design specification for MVP (no auth implementation)
**Task:** BUILD-012 - Authentication (Deferred)

---

## Route Segregation Strategy

### 1. Public Routes (`/api/*`)

Public routes serve the main dashboard and vulnerability queries. These routes are accessible without authentication in the MVP.

```
GET  /api/vulnerabilities              - List filtered vulnerabilities
GET  /api/vulnerabilities/<cve_id>     - Get vulnerability details
GET  /api/trends                        - Get trend chart data
GET  /api/kpis                          - Get KPI statistics
GET  /api/products                      - List monitored products
GET  /export?format=csv|json            - Export filtered vulnerabilities
```

**Security Notes for MVP:**
- No authentication required
- Input validation on all query parameters
- Rate limiting should be applied
- SQL injection prevention via parameterized queries
- XSS prevention via template escaping

---

### 2. Admin Routes (`/admin/*`)

Admin routes handle system configuration and maintenance. These routes are segregated by URL path prefix to allow reverse proxy rules (Nginx/Caddy) and future middleware authentication.

```
# DATA SOURCE MANAGEMENT
GET    /admin/sources                   - List data sources
POST   /admin/sources                   - Create new data source
GET    /admin/sources/<id>              - Get source details
PUT    /admin/sources/<id>              - Update source configuration
DELETE /admin/sources/<id>              - Delete source
POST   /admin/sources/<id>/poll         - Manually trigger source poll
GET    /admin/sources/<id>/health       - Get source health status

# PRODUCT INVENTORY
GET    /admin/inventory                 - List products with monitoring status
POST   /admin/inventory                 - Add custom product
PUT    /admin/inventory/<id>            - Update product monitoring status
DELETE /admin/inventory/<id>            - Remove custom product
GET    /admin/inventory/search          - Search CPE dictionary
POST   /admin/inventory/sync            - Sync NVD CPE dictionary

# LLM CONFIGURATION
GET    /admin/llm/config                - Get current Ollama configuration
PUT    /admin/llm/config                - Update Ollama endpoint
GET    /admin/llm/models                - List available models
POST   /admin/llm/test-connection       - Test Ollama connection
POST   /admin/llm/select-model          - Select active model

# REVIEW QUEUE (Low-confidence extractions)
GET    /admin/review-queue              - List entries needing review
GET    /admin/review-queue/<id>         - Get extraction details
PUT    /admin/review-queue/<id>/approve - Approve and move to curated
DELETE /admin/review-queue/<id>         - Reject extraction

# BACKGROUND JOBS
GET    /admin/jobs                      - List scheduled jobs
POST   /admin/jobs/<id>/trigger         - Manually trigger job
GET    /admin/jobs/<id>/logs            - Get job execution logs

# SYSTEM MONITORING
GET    /admin/health                    - System health dashboard
GET    /admin/metrics                   - Prometheus metrics (placeholder)
GET    /admin/settings                  - System settings
PUT    /admin/settings                  - Update system settings
```

---

## Authentication Middleware Preparation

### Current State (MVP)
- No authentication implemented
- Routes are segregated by path prefix
- All route handlers can be decorated with auth requirements later

### Future Implementation

To add authentication, follow this pattern:

#### 1. Create Auth Middleware (not in MVP)

```python
# app/middleware/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def require_admin(credentials = Depends(security)):
    """
    PLACEHOLDER: Future authentication check.
    Replace with actual JWT/session validation.
    """
    # Validate token/session
    # Check user has 'admin' role
    # Return user info
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not implemented in MVP - use reverse proxy auth",
    )
```

#### 2. Decorate Admin Routes

```python
from app.middleware.auth import require_admin

@admin_router.get("/sources")
async def list_sources(user = Depends(require_admin)):
    """Requires admin authentication."""
    ...
```

#### 3. Configure Reverse Proxy (MVP approach)

For the MVP, use reverse proxy (Nginx/Caddy) basic auth on `/admin/*`:

```nginx
# Nginx example
location /admin/ {
    auth_basic "Admin Area";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}
```

---

## Route Module Structure

```
app/
├── main.py                    # FastAPI application setup
├── routes/
│   ├── __init__.py
│   ├── public.py             # Public API routes (/api/*)
│   └── admin.py              # Admin routes (/admin/*)
├── middleware/
│   ├── __init__.py
│   ├── auth.py              # [RESERVED] Future auth middleware
│   ├── error_handler.py      # Global error handling
│   └── cors.py               # CORS configuration
├── models/
│   ├── vulnerability.py      # Vulnerability model
│   ├── data_source.py        # DataSource model
│   └── product.py            # Product model
├── schemas/
│   ├── request.py            # Request validation schemas
│   └── response.py           # Response schemas
├── database/
│   ├── connection.py         # DB connection pool
│   ├── models.py             # SQLAlchemy ORM models
│   └── migrations/
└── services/
    ├── vulnerability_service.py
    ├── source_service.py
    └── llm_service.py
```

---

## Security Design Principles

### 1. Path-Based Segregation
- Public: `/api/*` - Dashboard and query endpoints
- Admin: `/admin/*` - System management endpoints
- This allows reverse proxy rules without code changes

### 2. Middleware-Ready Authentication
- No auth implemented in MVP code
- Structure supports FastAPI `Depends()` for future auth
- Reverse proxy can enforce `/admin/*` access control

### 3. Input Validation
All routes validate input using Pydantic schemas:
- Query parameters are typed and validated
- Request bodies use Pydantic models
- SQL injection prevented via SQLAlchemy parameterized queries

### 4. CORS Configuration
- Public routes allow cross-origin requests (configurable origins)
- Admin routes will restrict CORS (requires auth first)

### 5. No Secrets in Routes
- API keys/credentials stored in database (encrypted)
- Environment variables for service configuration
- Never pass secrets in URL parameters

---

## Implementation Timeline

### Phase 1: MVP (Current - BUILD-012)
- [x] Design route structure
- [x] Segregate public vs admin
- [x] Create placeholder auth middleware
- [ ] Implement public routes (BUILD-001+)
- [ ] Implement admin routes (BUILD-005+)

### Phase 2: Future
- [ ] Implement JWT authentication middleware
- [ ] Add role-based access control (RBAC)
- [ ] Implement audit logging for admin actions
- [ ] Add webhook support for external integrations

---

## Testing Strategy

### Public Routes (No Auth)
```bash
# All public endpoints should be testable without auth
curl http://localhost:8000/api/vulnerabilities
```

### Admin Routes (Auth Placeholder)
```bash
# MVP: Will work without auth
# Future: Will require valid JWT/credentials
curl http://localhost:8000/admin/sources
```

### Integration Tests
- Test route segregation in `tests/test_routes.py`
- Verify 401/403 responses when auth is implemented
- Test query parameter validation

---

## Database Tables Supporting This Architecture

Admin routes rely on these tables:

```sql
-- Data Sources
CREATE TABLE data_sources (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,  -- 'nvd', 'cisa_kev', 'rss', 'api', 'url'
    url TEXT NOT NULL,
    polling_interval_hours INT,
    auth_config_encrypted TEXT,  -- Fernet encrypted
    is_enabled BOOLEAN DEFAULT true,
    is_running BOOLEAN DEFAULT false,
    consecutive_failures INT DEFAULT 0,
    last_poll_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products (Monitored)
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    cpe_uri TEXT UNIQUE NOT NULL,
    vendor TEXT NOT NULL,
    product_name TEXT NOT NULL,
    is_monitored BOOLEAN DEFAULT true,
    custom BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review Queue (Low-confidence LLM extractions)
CREATE TABLE review_queue (
    id TEXT PRIMARY KEY,
    raw_entry_id TEXT NOT NULL REFERENCES raw_entries(id),
    extracted_data JSONB NOT NULL,
    confidence_score FLOAT,
    needs_review BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Configuration (Environment Variables)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/vulndash
DATABASE_ECHO=false

# Ollama LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# API Configuration
API_TITLE=VulnDash
API_VERSION=1.0.0
DEBUG=false

# CORS (public endpoints)
CORS_ORIGINS=["http://localhost:3000", "https://vulndash.example.com"]

# Authentication (future)
# JWT_SECRET_KEY=your-secret-key-here
# JWT_ALGORITHM=HS256
# JWT_EXPIRATION_HOURS=24
```

---

## Summary

This route architecture achieves the BUILD-012 acceptance criteria:

1. **Admin routes are separable** ✓
   - Clear path prefix `/admin/*`
   - Can be isolated with reverse proxy rules

2. **Route structure allows auth middleware to be added later** ✓
   - Placeholder for `Depends(require_admin)` decorator
   - No breaking changes needed when auth is added

3. **No actual auth implementation for MVP** ✓
   - Routes work without authentication
   - Reverse proxy authentication recommended
   - FastAPI middleware structure prepared

4. **Clear separation between admin and public endpoints** ✓
   - Public routes: `/api/*`
   - Admin routes: `/admin/*`
   - Separate route modules for maintainability

---

**Generated by Backend Agent - BUILD-012**
**Task**: Design admin pages with segregation to allow authentication to be added later
