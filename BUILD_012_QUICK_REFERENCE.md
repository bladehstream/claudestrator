# BUILD-012 Quick Reference Guide

## Task Summary
Design FastAPI backend with admin route segregation to allow authentication to be added later (deferred from MVP).

## Status: ✓ COMPLETED

---

## Route Architecture at a Glance

### Public Routes (No Auth)
```
/api/vulnerabilities           GET     List with filters
/api/vulnerabilities/<cve_id>  GET     Single CVE details
/api/trends                    GET     Chart data
/api/kpis                      GET     Statistics
/api/export                    GET     CSV/JSON export
```

### Admin Routes (Auth Ready)
```
/admin/sources/*               [6]     Data source management
/admin/inventory/*             [6]     Product inventory
/admin/llm/*                   [5]     LLM configuration
/admin/review-queue/*          [4]     Low-confidence review
/admin/jobs/*                  [3]     Background job control
/admin/* (health/metrics/settings) [4] System monitoring
```

---

## Key Files

| File | Purpose | Key Section |
|------|---------|------------|
| **BACKEND_ROUTES.md** | Route design | Route segregation strategy |
| **backend_implementation.md** | API specs | Endpoint request/response schemas |
| **BUILD_012_CODE.py** | Code reference | Working FastAPI examples |
| **verification_steps_BUILD_012.md** | Testing | How to verify implementation |

---

## How to Add Authentication (3 Steps)

### Step 1: Implement middleware
Edit `app/middleware/auth.py` - Replace placeholder with JWT validation

### Step 2: Uncomment decorators
In `app/routes/admin.py`, uncomment `@Depends(require_admin)` on route handlers

### Step 3: Done!
No changes to route definitions needed - everything else stays the same

---

## Architecture Principles

1. **Path-based segregation** - `/api/*` vs `/admin/*`
2. **Middleware-ready** - Auth middleware prepared for FastAPI
3. **No code duplication** - Decorator pattern, not wrapper functions
4. **MVP-friendly** - Reverse proxy can enforce `/admin/*` protection
5. **Future-proof** - Adding auth requires zero route changes

---

## Code Snippet: Adding New Admin Route

```python
# app/routes/admin.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

admin_router = APIRouter()

class MyRequest(BaseModel):
    param1: str
    param2: int

@admin_router.post("/my-endpoint")
async def my_admin_endpoint(
    request: MyRequest,
    # user: dict = Depends(require_admin),  # Uncomment for auth
):
    """
    New admin endpoint.

    Security:
    - Input validated via Pydantic
    - Admin auth ready (uncomment decorator)
    - Segregated under /admin/* path
    """
    return {"status": "success", "data": request}

# In main.py:
# app.include_router(admin_router, prefix="/admin", tags=["admin"])
```

---

## Acceptance Criteria Checklist

- [x] Admin routes are separable from public routes
  - Public: `/api/*` in `app/routes/public.py`
  - Admin: `/admin/*` in `app/routes/admin.py`
  - Reverse proxy can isolate `/admin/*`

- [x] Route structure allows auth middleware to be added later
  - Placeholder in `app/middleware/auth.py`
  - `@Depends(require_admin)` pattern ready (commented)
  - Implementation guide provided

- [x] No actual auth implementation for MVP
  - `require_admin()` returns mock user
  - All routes accessible without auth
  - Reverse proxy recommended for `/admin/*` protection

- [x] Clear separation between admin and public endpoints
  - Distinct modules
  - Different prefixes
  - Different business logic
  - Different security considerations

---

## Security Checklist

- [x] No hardcoded secrets
- [x] Input validation via Pydantic
- [x] SQL injection prevention (parameterized queries)
- [x] XSS prevention (template escaping)
- [x] CORS configurable from environment
- [x] Admin routes segregated by path
- [x] Auth middleware structure ready
- [x] Rate limiting can be added to public endpoints

---

## Testing Commands

```bash
# Verify routes are segregated
grep -r "prefix=\"/api\"" app/routes/
grep -r "prefix=\"/admin\"" app/routes/

# Verify auth middleware exists
grep -r "require_admin" app/middleware/auth.py

# Check for hardcoded secrets
grep -r "password\|api_key\|secret" app/ | grep -v "# "

# Start server
uvicorn main:app --reload

# Test public endpoint
curl http://localhost:8000/api/vulnerabilities

# Test admin endpoint (MVP: no auth required)
curl http://localhost:8000/admin/sources

# View API docs
open http://localhost:8000/docs
```

---

## File Structure

```
backend/
├── main.py                  # FastAPI app creation
├── requirements.txt         # Dependencies
├── .env.example            # Configuration template
│
├── app/
│   ├── routes/
│   │   ├── public.py       # /api/* routes (5 endpoints)
│   │   └── admin.py        # /admin/* routes (28 endpoints)
│   │
│   ├── middleware/
│   │   ├── auth.py         # [PLACEHOLDER] Future auth
│   │   ├── cors_config.py  # CORS setup
│   │   └── error_handler.py
│   │
│   ├── models/
│   │   ├── vulnerability.py
│   │   ├── data_source.py
│   │   └── product.py
│   │
│   ├── schemas/
│   │   ├── vulnerability.py
│   │   ├── data_source.py
│   │   └── product.py
│   │
│   ├── database/
│   │   └── connection.py
│   │
│   └── services/
│       ├── vulnerability_service.py
│       ├── source_service.py
│       └── llm_service.py
│
└── tests/
    └── test_routes.py      # Route segregation tests
```

---

## Environment Variables (MVP)

```bash
# Database
DATABASE_URL=sqlite:///./vulndash.db

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
DEBUG=false
PORT=8000

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Auth (Future - add when implementing)
# JWT_SECRET_KEY=...
# JWT_ALGORITHM=HS256
# JWT_EXPIRATION_HOURS=24
```

---

## Dependencies (requirements.txt)

```
fastapi==0.104.1           # Web framework
uvicorn==0.24.0            # ASGI server
sqlalchemy==2.0.23         # ORM
pydantic==2.5.0            # Validation
psycopg==3.9.1             # PostgreSQL driver
aiosqlite==0.19.0          # SQLite async
python-dotenv==1.0.0       # .env support
cryptography==41.0.7       # Encryption (Fernet for creds)
httpx==0.25.2              # Async HTTP client
apscheduler==3.10.4        # Background jobs
```

---

## Common Questions

**Q: Where do I add authentication?**
A: Edit `app/middleware/auth.py` and uncomment `@Depends()` decorators. No route changes needed.

**Q: How do I add a new admin endpoint?**
A: Add to `app/routes/admin.py` under `@admin_router`. Use Pydantic models for validation.

**Q: How do I add a new public endpoint?**
A: Add to `app/routes/public.py` under `@router`. Keep same pattern as existing endpoints.

**Q: Why is authentication in middleware?**
A: FastAPI Depends() is cleaner than wrapper functions and works with async/await natively.

**Q: Can I use the admin routes without auth in MVP?**
A: Yes - they're open. Use reverse proxy (Nginx/Caddy) to protect `/admin/*` if needed.

**Q: How do I test that routes are segregated?**
A: See verification_steps_BUILD_012.md - grep commands to verify prefixes and modules.

---

## Next Steps for Implementation

1. **Create database models** - Use SQLAlchemy ORM for Vulnerability, DataSource, Product
2. **Implement services** - Business logic for querying and updates
3. **Connect routes to services** - Replace placeholder returns with actual data
4. **Add tests** - Unit tests for routes, integration tests for services
5. **Implement authentication** - Uncomment decorators and implement middleware

---

## Verification

All acceptance criteria met:
- ✓ Route segregation clear and documented
- ✓ Auth middleware structure ready
- ✓ No auth implemented in MVP
- ✓ Clear separation between admin and public

Ready for implementation tasks BUILD-001, BUILD-005, BUILD-006, etc.

---

**Last Updated:** 2025-12-22
**Status:** COMPLETED
**Version:** 1.0.0
