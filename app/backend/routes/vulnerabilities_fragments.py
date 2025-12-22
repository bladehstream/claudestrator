"""
HTMX fragment routes for vulnerability table.
"""
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import csv
import json
import io

from app.database import get_db
from app.database.models import Vulnerability, Product

router = APIRouter(prefix="/vulnerabilities/fragments", tags=["vulnerabilities-fragments"])


@router.get("/table", response_class=HTMLResponse)
def vulnerability_table_fragment(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    cve_search: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    epss_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    kev_only: bool = Query(False),
    hide_remediated: bool = Query(False),
    sort_by: str = Query("published_date"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):
    """Return HTMX fragment with vulnerability table rows."""
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

    if hide_remediated:
        query = query.filter(Vulnerability.is_remediated == False)

    # Apply sorting
    sort_field = getattr(Vulnerability, sort_by, Vulnerability.published_date)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    # Get total count before pagination
    total_count = query.count()

    # Apply pagination
    vulnerabilities = query.offset(skip).limit(limit).all()

    if not vulnerabilities:
        return """
        <tr>
            <td colspan="8" style="text-align: center; padding: 40px; color: #8a8a8a;">
                No vulnerabilities found matching your filters
            </td>
        </tr>
        """

    html_parts = []

    for vuln in vulnerabilities:
        # Get vendors and products
        vendors = list(set([p.vendor for p in vuln.products])) if vuln.products else []
        products = list(set([p.product_name for p in vuln.products])) if vuln.products else []

        vendor_str = vendors[0] if vendors else "N/A"
        product_str = products[0] if products else "N/A"
        if len(products) > 1:
            product_str += f" (+{len(products)-1})"

        # Severity badge
        severity_class = ""
        if vuln.severity == "CRITICAL":
            severity_class = "severity-critical"
        elif vuln.severity == "HIGH":
            severity_class = "severity-high"
        elif vuln.severity == "MEDIUM":
            severity_class = "severity-medium"
        elif vuln.severity == "LOW":
            severity_class = "severity-low"

        # KEV badge
        kev_badge = '<span class="kev-badge">KEV</span>' if vuln.kev_status else ''

        # EPSS score formatting
        epss_display = f"{vuln.epss_score:.1%}" if vuln.epss_score is not None else "N/A"
        epss_class = "epss-high" if vuln.epss_score and vuln.epss_score >= 0.7 else ""

        # CVSS score display
        cvss_display = f"{vuln.cvss_score:.1f}" if vuln.cvss_score is not None else "N/A"

        # Date formatting
        date_display = vuln.published_date.strftime("%Y-%m-%d") if vuln.published_date else "N/A"

        # Remediation status
        remediated_class = "remediated" if vuln.is_remediated else ""
        checkbox_checked = "checked" if vuln.is_remediated else ""

        html_parts.append(f'''
        <tr class="vuln-row {remediated_class}">
            <td>
                <input type="checkbox"
                       class="remediate-checkbox"
                       data-cve-id="{vuln.cve_id}"
                       {checkbox_checked}
                       onchange="toggleRemediate(this, '{vuln.cve_id}')"
                       title="Mark as remediated" />
            </td>
            <td>
                <a href="https://nvd.nist.gov/vuln/detail/{vuln.cve_id}"
                   target="_blank"
                   class="cve-link">{vuln.cve_id}</a>
            </td>
            <td class="vendor-cell">{vendor_str}</td>
            <td class="product-cell">{product_str}</td>
            <td>
                <span class="severity-badge {severity_class}">
                    {vuln.severity or 'N/A'}
                </span>
                <span class="cvss-score">{cvss_display}</span>
            </td>
            <td>
                <span class="epss-score {epss_class}">{epss_display}</span>
            </td>
            <td>{kev_badge if kev_badge else '<span style="color: #666;">—</span>'}</td>
            <td class="date-cell">{date_display}</td>
        </tr>
        ''')

    return ''.join(html_parts)


@router.get("/filter-options", response_class=HTMLResponse)
def filter_options_fragment(
    request: Request,
    db: Session = Depends(get_db)
):
    """Return HTMX fragment with filter dropdown options."""
    vendors = db.query(Product.vendor).distinct().order_by(Product.vendor).all()
    products = db.query(Product.product_name).distinct().order_by(Product.product_name).all()

    vendor_options = ['<option value="">All Vendors</option>']
    for v in vendors:
        if v[0]:
            vendor_options.append(f'<option value="{v[0]}">{v[0]}</option>')

    product_options = ['<option value="">All Products</option>']
    for p in products:
        if p[0]:
            product_options.append(f'<option value="{p[0]}">{p[0]}</option>')

    return {
        "vendors": ''.join(vendor_options),
        "products": ''.join(product_options)
    }


@router.get("/stats", response_class=HTMLResponse)
def stats_fragment(
    request: Request,
    db: Session = Depends(get_db)
):
    """Return HTMX fragment with vulnerability statistics."""
    total = db.query(Vulnerability).count()
    kev_count = db.query(Vulnerability).filter(Vulnerability.kev_status == True).count()
    high_epss = db.query(Vulnerability).filter(Vulnerability.epss_score >= 0.7).count()
    critical = db.query(Vulnerability).filter(Vulnerability.severity == "CRITICAL").count()
    remediated = db.query(Vulnerability).filter(Vulnerability.is_remediated == True).count()

    return f"""
    <div class="stat-card">
        <div class="stat-value">{total}</div>
        <div class="stat-label">Total Vulnerabilities</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{kev_count}</div>
        <div class="stat-label">KEV Active Exploits</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{high_epss}</div>
        <div class="stat-label">High EPSS (&gt;70%)</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{critical}</div>
        <div class="stat-label">Critical Severity</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{remediated}</div>
        <div class="stat-label">Remediated</div>
    </div>
    """


def _build_vulnerability_query(
    db: Session,
    cve_search: Optional[str] = None,
    vendor: Optional[str] = None,
    product: Optional[str] = None,
    severity: Optional[str] = None,
    epss_min: Optional[float] = None,
    kev_only: bool = False,
    hide_remediated: bool = False,
    sort_by: str = "published_date",
    sort_order: str = "desc"
):
    """
    Build and apply filters to vulnerability query.
    Reusable helper for both UI and export endpoints.
    """
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

    if hide_remediated:
        query = query.filter(Vulnerability.is_remediated == False)

    # Apply sorting
    sort_field = getattr(Vulnerability, sort_by, Vulnerability.published_date)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    return query


@router.get("/export/csv")
async def export_csv(
    cve_search: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    epss_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    kev_only: bool = Query(False),
    hide_remediated: bool = Query(False),
    sort_by: str = Query("published_date"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):
    """
    Export filtered vulnerabilities as CSV.

    Applies the same filters as the table view and returns a downloadable CSV file.
    Filename includes timestamp for uniqueness.
    """
    # Build query with filters
    query = _build_vulnerability_query(
        db,
        cve_search=cve_search,
        vendor=vendor,
        product=product,
        severity=severity,
        epss_min=epss_min,
        kev_only=kev_only,
        hide_remediated=hide_remediated,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Execute query - no pagination limit for exports
    vulnerabilities = query.all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "CVE ID",
        "Vendor",
        "Product",
        "Severity",
        "CVSS Score",
        "EPSS Score",
        "EPSS Percentile",
        "KEV Status",
        "Published Date",
        "Title",
        "Description",
        "Is Remediated"
    ])

    # Write data rows
    for vuln in vulnerabilities:
        vendors = list(set([p.vendor for p in vuln.products])) if vuln.products else []
        products = list(set([p.product_name for p in vuln.products])) if vuln.products else []

        vendor_str = ";".join(vendors) if vendors else "N/A"
        product_str = ";".join(products) if products else "N/A"

        writer.writerow([
            vuln.cve_id,
            vendor_str,
            product_str,
            vuln.severity or "N/A",
            vuln.cvss_score or "N/A",
            f"{vuln.epss_score:.4f}" if vuln.epss_score is not None else "N/A",
            f"{vuln.epss_percentile:.2f}" if vuln.epss_percentile is not None else "N/A",
            "Yes" if vuln.kev_status else "No",
            vuln.published_date.isoformat() if vuln.published_date else "N/A",
            vuln.title or "",
            vuln.description or "",
            "Yes" if vuln.is_remediated else "No"
        ])

    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"vulnerabilities_{timestamp}.csv"

    # Return as streaming response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/json")
async def export_json(
    cve_search: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    epss_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    kev_only: bool = Query(False),
    hide_remediated: bool = Query(False),
    sort_by: str = Query("published_date"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):
    """
    Export filtered vulnerabilities as JSON.

    Applies the same filters as the table view and returns a downloadable JSON file.
    Filename includes timestamp for uniqueness.
    """
    # Build query with filters
    query = _build_vulnerability_query(
        db,
        cve_search=cve_search,
        vendor=vendor,
        product=product,
        severity=severity,
        epss_min=epss_min,
        kev_only=kev_only,
        hide_remediated=hide_remediated,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Execute query - no pagination limit for exports
    vulnerabilities = query.all()

    # Build JSON structure
    data = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "filters_applied": {
            "cve_search": cve_search,
            "vendor": vendor,
            "product": product,
            "severity": severity,
            "epss_min": epss_min,
            "kev_only": kev_only,
            "hide_remediated": hide_remediated,
            "sort_by": sort_by,
            "sort_order": sort_order
        },
        "total_count": len(vulnerabilities),
        "vulnerabilities": []
    }

    # Convert vulnerabilities to dictionaries
    for vuln in vulnerabilities:
        vendors = list(set([p.vendor for p in vuln.products])) if vuln.products else []
        products_list = list(set([p.product_name for p in vuln.products])) if vuln.products else []

        vuln_dict = {
            "cve_id": vuln.cve_id,
            "title": vuln.title,
            "description": vuln.description,
            "severity": vuln.severity,
            "cvss_score": vuln.cvss_score,
            "cvss_vector": vuln.cvss_vector,
            "epss_score": vuln.epss_score,
            "epss_percentile": vuln.epss_percentile,
            "kev_status": vuln.kev_status,
            "kev_date_added": vuln.kev_date_added.isoformat() if vuln.kev_date_added else None,
            "published_date": vuln.published_date.isoformat() if vuln.published_date else None,
            "is_remediated": vuln.is_remediated,
            "remediated_at": vuln.remediated_at.isoformat() if vuln.remediated_at else None,
            "confidence_score": vuln.confidence_score,
            "vendors": vendors,
            "products": products_list
        }
        data["vulnerabilities"].append(vuln_dict)

    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"vulnerabilities_{timestamp}.json"

    # Return as streaming response
    output = io.StringIO()
    json.dump(data, output, indent=2)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
