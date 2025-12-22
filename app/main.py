"""
VulnDash - Main FastAPI application.
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.database import init_db
from app.backend.routes import sources, sources_fragments, products, vulnerabilities, vulnerabilities_fragments, dashboard_fragments
from app.backend.api import llm_router, vulnerabilities_router, processing_router, review_queue_router, epss_router, admin_email_router
from app.backend.api import llm_multi
from app.backend.services.scheduler import start_scheduler, stop_scheduler
from app.backend.services.epss_scheduler import start_epss_scheduler, stop_epss_scheduler
from app.backend.services.email_scheduler import start_email_scheduler, stop_email_scheduler

# Initialize FastAPI app
app = FastAPI(
    title="VulnDash",
    description="Cybersecurity Vulnerability Dashboard with LLM-powered data aggregation",
    version="1.0.0"
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and start background schedulers on startup."""
    await init_db()
    await start_scheduler()
    await start_epss_scheduler()
    await start_email_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background schedulers on shutdown."""
    await stop_scheduler()
    await stop_epss_scheduler()
    await stop_email_scheduler()

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "frontend", "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Setup templates
templates_path = os.path.join(os.path.dirname(__file__), "frontend", "templates")
os.makedirs(templates_path, exist_ok=True)
templates = Jinja2Templates(directory=templates_path)

# Include routers - fragments first to override API routes
app.include_router(sources_fragments.router)
app.include_router(vulnerabilities_fragments.router)
app.include_router(dashboard_fragments.router)
app.include_router(sources.router)
app.include_router(products.router)
app.include_router(vulnerabilities.router)
app.include_router(llm_router)
app.include_router(llm_multi.router)
app.include_router(vulnerabilities_router)
app.include_router(processing_router)
app.include_router(review_queue_router)
app.include_router(epss_router)
app.include_router(admin_email_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - Dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/admin/sources-ui", response_class=HTMLResponse)
async def sources_ui(request: Request):
    """Admin page for data source management."""
    return templates.TemplateResponse("admin_sources.html", {"request": request})


@app.get("/admin/products", response_class=HTMLResponse)
async def products_ui(request: Request):
    """Admin page for product inventory management."""
    return templates.TemplateResponse("admin/products.html", {"request": request})


@app.get("/admin/review-queue", response_class=HTMLResponse)
async def review_queue_ui(request: Request):
    """Admin page for low-confidence review queue management."""
    return templates.TemplateResponse("admin/review_queue.html", {"request": request})


@app.get("/intelligence", response_class=HTMLResponse)
async def intelligence(request: Request):
    """Threat intelligence view with critical advisories and threat feeds."""
    return templates.TemplateResponse("intelligence.html", {"request": request})


@app.get("/vulnerabilities-ui", response_class=HTMLResponse)
async def vulnerabilities_ui(request: Request):
    """Vulnerability table with filters and sorting."""
    return templates.TemplateResponse("vulnerabilities.html", {"request": request})


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vulndash"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
