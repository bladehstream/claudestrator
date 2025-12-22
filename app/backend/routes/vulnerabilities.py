"""
API routes for vulnerability management.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel

from app.database import get_db
from app.database.models import Vulnerability, Product

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


class VulnerabilityResponse(BaseModel):
    cve_id: str
    title: Optional[str]
    description: Optional[str]
    published_date: Optional[datetime]
    cvss_score: Optional[float]
    cvss_vector: Optional[str]
    severity: Optional[str]
    epss_score: Optional[float]
    epss_percentile: Optional[float]
    kev_status: bool
    kev_date_added: Optional[datetime]
    is_remediated: bool
    vendors: List[str]
    products: List[str]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


@router.get("/", response_model=List[VulnerabilityResponse])
def list_vulnerabilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    cve_search: Optional[str] = Query(None, description="Search by CVE ID"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    product: Optional[str] = Query(None, description="Filter by product"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    epss_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum EPSS score"),
    kev_only: bool = Query(False, description="Show only KEV entries"),
    sort_by: str = Query("published_date", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """List vulnerabilities with filtering and sorting."""
    query = db.query(Vulnerability)

    # Apply filters
    if cve_search:
        query = query.filter(Vulnerability.cve_id.ilike(f"%{cve_search}%"))

    if vendor:
        query = query.join(Vulnerability.products).filter(Product.vendor.ilike(f"%{vendor}%"))

    if product:
        query = query.join(Vulnerability.products).filter(Product.product_name.ilike(f"%{product}%"))

    if severity:
        query = query.filter(Vulnerability.severity == severity.upper())

    if epss_min is not None:
        query = query.filter(Vulnerability.epss_score >= epss_min)

    if kev_only:
        query = query.filter(Vulnerability.kev_status == True)

    # Apply sorting
    sort_field = getattr(Vulnerability, sort_by, Vulnerability.published_date)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    # Execute query
    vulnerabilities = query.offset(skip).limit(limit).all()

    # Format response
    results = []
    for vuln in vulnerabilities:
        vendors = list(set([p.vendor for p in vuln.products])) if vuln.products else []
        products = list(set([p.product_name for p in vuln.products])) if vuln.products else []

        results.append(VulnerabilityResponse(
            cve_id=vuln.cve_id,
            title=vuln.title,
            description=vuln.description,
            published_date=vuln.published_date,
            cvss_score=vuln.cvss_score,
            cvss_vector=vuln.cvss_vector,
            severity=vuln.severity,
            epss_score=vuln.epss_score,
            epss_percentile=vuln.epss_percentile,
            kev_status=vuln.kev_status,
            kev_date_added=vuln.kev_date_added,
            is_remediated=vuln.is_remediated,
            vendors=vendors,
            products=products
        ))

    return results


@router.get("/filters/vendors", response_model=List[str])
def get_vendors(db: Session = Depends(get_db)):
    """Get distinct list of vendors for filter dropdown."""
    vendors = db.query(Product.vendor).distinct().order_by(Product.vendor).all()
    return [v[0] for v in vendors if v[0]]


@router.get("/filters/products", response_model=List[str])
def get_products(
    vendor: Optional[str] = Query(None, description="Filter products by vendor"),
    db: Session = Depends(get_db)
):
    """Get distinct list of products for filter dropdown."""
    query = db.query(Product.product_name).distinct()

    if vendor:
        query = query.filter(Product.vendor == vendor)

    products = query.order_by(Product.product_name).all()
    return [p[0] for p in products if p[0]]


@router.get("/stats", response_model=dict)
def get_vulnerability_stats(db: Session = Depends(get_db)):
    """Get vulnerability statistics for dashboard."""
    total = db.query(Vulnerability).count()
    kev_count = db.query(Vulnerability).filter(Vulnerability.kev_status == True).count()
    high_epss = db.query(Vulnerability).filter(Vulnerability.epss_score >= 0.7).count()
    critical = db.query(Vulnerability).filter(Vulnerability.severity == "CRITICAL").count()
    high = db.query(Vulnerability).filter(Vulnerability.severity == "HIGH").count()
    remediated = db.query(Vulnerability).filter(Vulnerability.is_remediated == True).count()

    return {
        "total": total,
        "kev_active": kev_count,
        "high_epss": high_epss,
        "critical": critical,
        "high": high,
        "remediated": remediated,
        "by_severity": {
            "CRITICAL": critical,
            "HIGH": high,
            "MEDIUM": db.query(Vulnerability).filter(Vulnerability.severity == "MEDIUM").count(),
            "LOW": db.query(Vulnerability).filter(Vulnerability.severity == "LOW").count()
        }
    }


@router.post("/{cve_id}/remediate")
def toggle_remediate_vulnerability(
    cve_id: str,
    db: Session = Depends(get_db)
):
    """Toggle remediation status for a vulnerability."""
    vuln = db.query(Vulnerability).filter(Vulnerability.cve_id == cve_id).first()

    if not vuln:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vulnerability not found")

    # Toggle remediation status
    if vuln.is_remediated:
        vuln.is_remediated = False
        vuln.remediated_at = None
    else:
        vuln.is_remediated = True
        vuln.remediated_at = datetime.utcnow()

    db.commit()

    return {
        "cve_id": cve_id,
        "is_remediated": vuln.is_remediated,
        "remediated_at": vuln.remediated_at.isoformat() if vuln.remediated_at else None
    }
