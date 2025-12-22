"""
API routes for low-confidence review queue management.
Allows admins to review, approve, reject, and edit vulnerabilities flagged for manual review.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel, Field, validator

from app.database import get_db
from app.database.models import Vulnerability, Product, vulnerability_product


router = APIRouter(prefix="/admin/review-queue", tags=["review-queue"])


# Request/Response Models

class ReviewQueueItemResponse(BaseModel):
    """Response model for a single review queue item."""
    cve_id: str
    title: Optional[str]
    description: Optional[str]
    vendor: Optional[str] = None
    product: Optional[str] = None
    severity: Optional[str]
    cvss_score: Optional[float]
    cvss_vector: Optional[str]
    confidence_score: float
    extraction_metadata: Optional[dict]
    published_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewQueueListResponse(BaseModel):
    """Response model for paginated review queue list."""
    items: List[ReviewQueueItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApprovalRequest(BaseModel):
    """Request model for approving a vulnerability with optional edits."""
    cve_id: str = Field(..., description="CVE ID to approve")
    title: Optional[str] = Field(None, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    vendor: Optional[str] = Field(None, description="Updated vendor")
    product: Optional[str] = Field(None, description="Updated product")
    severity: Optional[str] = Field(None, description="Updated severity")
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Updated CVSS score")
    cvss_vector: Optional[str] = Field(None, description="Updated CVSS vector")

    @validator('severity')
    def validate_severity(cls, v):
        if v is not None:
            valid_severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NONE', 'UNKNOWN']
            if v.upper() not in valid_severities:
                raise ValueError(f"Severity must be one of {valid_severities}")
            return v.upper()
        return v


class RejectRequest(BaseModel):
    """Request model for rejecting/deleting a vulnerability."""
    cve_id: str = Field(..., description="CVE ID to reject and delete")
    reason: Optional[str] = Field(None, description="Reason for rejection (for logging)")


class BulkApprovalRequest(BaseModel):
    """Request model for bulk approval of vulnerabilities."""
    cve_ids: List[str] = Field(..., description="List of CVE IDs to approve")


class BulkRejectRequest(BaseModel):
    """Request model for bulk rejection of vulnerabilities."""
    cve_ids: List[str] = Field(..., description="List of CVE IDs to reject")
    reason: Optional[str] = Field(None, description="Reason for bulk rejection")


# API Endpoints

@router.get("/", response_model=ReviewQueueListResponse)
def list_review_queue(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    sort_by: str = Query("confidence_score", description="Sort field (confidence_score, created_at, severity)"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    List all vulnerabilities in the review queue (needs_review = true).

    Returns paginated list with filtering and sorting options.
    """
    # Build query
    query = db.query(Vulnerability).filter(Vulnerability.needs_review == True)

    # Apply filters
    if severity:
        query = query.filter(Vulnerability.severity == severity.upper())

    # Apply sorting
    sort_field = getattr(Vulnerability, sort_by, Vulnerability.confidence_score)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size

    # Execute query with pagination
    vulnerabilities = query.offset(offset).limit(page_size).all()

    # Format response
    items = []
    for vuln in vulnerabilities:
        # Get first vendor/product if available
        vendor = None
        product = None
        if vuln.products:
            vendor = vuln.products[0].vendor
            product = vuln.products[0].product_name

        items.append(ReviewQueueItemResponse(
            cve_id=vuln.cve_id,
            title=vuln.title,
            description=vuln.description,
            vendor=vendor,
            product=product,
            severity=vuln.severity,
            cvss_score=vuln.cvss_score,
            cvss_vector=vuln.cvss_vector,
            confidence_score=vuln.confidence_score,
            extraction_metadata=vuln.extraction_metadata,
            published_date=vuln.published_date,
            created_at=vuln.created_at
        ))

    return ReviewQueueListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/approve")
def approve_vulnerability(
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve a vulnerability from the review queue.

    - Updates fields with any edits provided
    - Sets needs_review = false
    - Sets confidence_score = 1.0 (manual review = highest confidence)
    - Creates/links product if vendor/product provided
    """
    # Find vulnerability
    vuln = db.query(Vulnerability).filter(Vulnerability.cve_id == request.cve_id).first()

    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vulnerability {request.cve_id} not found"
        )

    if not vuln.needs_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vulnerability {request.cve_id} is not in review queue"
        )

    # Apply edits
    if request.title is not None:
        vuln.title = request.title
    if request.description is not None:
        vuln.description = request.description
    if request.severity is not None:
        vuln.severity = request.severity
    if request.cvss_score is not None:
        vuln.cvss_score = request.cvss_score
    if request.cvss_vector is not None:
        vuln.cvss_vector = request.cvss_vector

    # Handle product association
    if request.vendor and request.product:
        # Find or create product
        product = db.query(Product).filter(
            and_(
                Product.vendor == request.vendor,
                Product.product_name == request.product
            )
        ).first()

        if not product:
            product = Product(
                vendor=request.vendor,
                product_name=request.product,
                source="manual"
            )
            db.add(product)
            db.flush()  # Get product ID

        # Link product to vulnerability if not already linked
        if product not in vuln.products:
            vuln.products.append(product)

    # Approve: set confidence to 1.0, remove from review queue
    vuln.confidence_score = 1.0
    vuln.needs_review = False
    vuln.updated_at = datetime.utcnow()

    # Update extraction metadata to track manual review
    if not vuln.extraction_metadata:
        vuln.extraction_metadata = {}
    vuln.extraction_metadata['manually_reviewed'] = True
    vuln.extraction_metadata['reviewed_at'] = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(vuln)

    return {
        "message": f"Vulnerability {request.cve_id} approved successfully",
        "cve_id": vuln.cve_id,
        "confidence_score": vuln.confidence_score,
        "needs_review": vuln.needs_review
    }


@router.post("/reject")
def reject_vulnerability(
    request: RejectRequest,
    db: Session = Depends(get_db)
):
    """
    Reject and delete a vulnerability from the review queue.

    - Removes the vulnerability from the database entirely
    - Cannot be undone
    """
    # Find vulnerability
    vuln = db.query(Vulnerability).filter(Vulnerability.cve_id == request.cve_id).first()

    if not vuln:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vulnerability {request.cve_id} not found"
        )

    if not vuln.needs_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vulnerability {request.cve_id} is not in review queue"
        )

    # Delete vulnerability (cascade will remove product associations)
    cve_id = vuln.cve_id
    db.delete(vuln)
    db.commit()

    return {
        "message": f"Vulnerability {cve_id} rejected and deleted successfully",
        "cve_id": cve_id,
        "reason": request.reason
    }


@router.post("/bulk-approve")
def bulk_approve_vulnerabilities(
    request: BulkApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk approve multiple vulnerabilities without edits.

    - Sets needs_review = false for all
    - Sets confidence_score = 1.0 for all
    """
    if not request.cve_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No CVE IDs provided"
        )

    # Find all vulnerabilities
    vulns = db.query(Vulnerability).filter(
        and_(
            Vulnerability.cve_id.in_(request.cve_ids),
            Vulnerability.needs_review == True
        )
    ).all()

    if not vulns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vulnerabilities found in review queue with provided CVE IDs"
        )

    # Approve all
    approved_count = 0
    for vuln in vulns:
        vuln.confidence_score = 1.0
        vuln.needs_review = False
        vuln.updated_at = datetime.utcnow()

        if not vuln.extraction_metadata:
            vuln.extraction_metadata = {}
        vuln.extraction_metadata['manually_reviewed'] = True
        vuln.extraction_metadata['reviewed_at'] = datetime.utcnow().isoformat()
        vuln.extraction_metadata['bulk_approved'] = True

        approved_count += 1

    db.commit()

    return {
        "message": f"Bulk approved {approved_count} vulnerabilities",
        "approved_count": approved_count,
        "cve_ids": [v.cve_id for v in vulns]
    }


@router.post("/bulk-reject")
def bulk_reject_vulnerabilities(
    request: BulkRejectRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk reject and delete multiple vulnerabilities.

    - Permanently deletes all specified vulnerabilities
    - Cannot be undone
    """
    if not request.cve_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No CVE IDs provided"
        )

    # Find all vulnerabilities
    vulns = db.query(Vulnerability).filter(
        and_(
            Vulnerability.cve_id.in_(request.cve_ids),
            Vulnerability.needs_review == True
        )
    ).all()

    if not vulns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vulnerabilities found in review queue with provided CVE IDs"
        )

    # Delete all
    deleted_cve_ids = [v.cve_id for v in vulns]
    for vuln in vulns:
        db.delete(vuln)

    db.commit()

    return {
        "message": f"Bulk rejected and deleted {len(deleted_cve_ids)} vulnerabilities",
        "deleted_count": len(deleted_cve_ids),
        "cve_ids": deleted_cve_ids,
        "reason": request.reason
    }


@router.get("/stats")
def get_review_queue_stats(db: Session = Depends(get_db)):
    """
    Get statistics about the review queue.

    Returns counts by severity and overall metrics.
    """
    # Total in review queue
    total_needs_review = db.query(Vulnerability).filter(Vulnerability.needs_review == True).count()

    # Count by severity
    by_severity = {}
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN', 'NONE']:
        count = db.query(Vulnerability).filter(
            and_(
                Vulnerability.needs_review == True,
                Vulnerability.severity == severity
            )
        ).count()
        by_severity[severity] = count

    # Average confidence score of items in queue
    result = db.query(Vulnerability).filter(Vulnerability.needs_review == True).all()
    avg_confidence = sum([v.confidence_score for v in result]) / len(result) if result else 0.0

    return {
        "total_needs_review": total_needs_review,
        "by_severity": by_severity,
        "average_confidence": round(avg_confidence, 3),
        "threshold": 0.8  # Hardcoded threshold (could be fetched from LLMConfig)
    }
