"""
Product inventory management API routes.

Provides endpoints for:
- Searching products (FTS5 full-text search)
- Adding custom products
- Importing from NVD CPE dictionary
- Toggling monitoring status
- Managing product inventory
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.database import get_db
from app.backend.models.product import Product, ProductSearchIndex, CPESyncLog

router = APIRouter(prefix="/api/products", tags=["products"])


# Request/Response Models
class ProductCreate(BaseModel):
    """Request model for creating custom products."""
    cpe_uri: Optional[str] = Field(None, max_length=500)
    vendor: str = Field(..., min_length=1, max_length=200)
    product_name: str = Field(..., min_length=1, max_length=200)
    version: Optional[str] = Field(None, max_length=100)
    part: Optional[str] = Field(None, regex="^[aoh]$")
    description: Optional[str] = None
    is_monitored: bool = True

    @validator('vendor', 'product_name')
    def normalize_name(cls, v):
        """Normalize vendor and product names (lowercase, strip whitespace)."""
        return v.strip().lower() if v else v


class ProductUpdate(BaseModel):
    """Request model for updating product monitoring status."""
    is_monitored: bool


class ProductResponse(BaseModel):
    """Response model for product data."""
    id: int
    cpe_uri: Optional[str]
    vendor: str
    product_name: str
    version: Optional[str]
    part: Optional[str]
    is_monitored: bool
    source: str
    description: Optional[str]
    deprecated: bool
    created_at: str
    updated_at: str
    last_synced_at: Optional[str]

    class Config:
        from_attributes = True


class ProductSearchResponse(BaseModel):
    """Response model for product search results."""
    total: int
    products: List[ProductResponse]
    page: int
    page_size: int


class CPESyncResponse(BaseModel):
    """Response model for CPE sync status."""
    id: int
    started_at: str
    completed_at: Optional[str]
    status: str
    products_added: int
    products_updated: int
    products_deprecated: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


# API Endpoints

@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: Optional[str] = Query(None, description="Search query for vendor/product name"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    monitored_only: bool = Query(False, description="Show only monitored products"),
    source: Optional[str] = Query(None, description="Filter by source (nvd_cpe or custom)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search products using FTS5 full-text search or filters.

    Supports:
    - Full-text search across vendor and product names
    - Filtering by vendor, monitoring status, source
    - Pagination
    """
    # Build base query
    query = select(Product)

    # Apply FTS5 search if query provided
    if q and q.strip():
        # For SQLite with FTS5
        search_query = q.strip().replace("'", "''")  # Escape single quotes
        fts_subquery = text(f"""
            SELECT product_id FROM product_search_fts5
            WHERE product_search_fts5 MATCH :search_term
        """)

        # Join with FTS results
        result = await db.execute(
            fts_subquery,
            {"search_term": search_query}
        )
        product_ids = [row[0] for row in result.fetchall()]

        if product_ids:
            query = query.where(Product.id.in_(product_ids))
        else:
            # No matches, return empty result
            return ProductSearchResponse(
                total=0,
                products=[],
                page=page,
                page_size=page_size
            )

    # Apply filters
    if vendor:
        query = query.where(Product.vendor.ilike(f"%{vendor.strip().lower()}%"))

    if monitored_only:
        query = query.where(Product.is_monitored == True)

    if source:
        query = query.where(Product.source == source)

    # Exclude deprecated products by default
    query = query.where(Product.deprecated == False)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Order by vendor, then product_name
    query = query.order_by(Product.vendor, Product.product_name)

    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()

    return ProductSearchResponse(
        total=total,
        products=[ProductResponse.from_orm(p) for p in products],
        page=page,
        page_size=page_size
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single product by ID."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse.from_orm(product)


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_custom_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a custom product entry.

    Custom products can be added when the CPE dictionary doesn't contain
    a specific vendor/product combination.
    """
    # Check for duplicates
    existing = await db.execute(
        select(Product).where(
            Product.vendor == product_data.vendor,
            Product.product_name == product_data.product_name,
            Product.version == product_data.version
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Product with this vendor/product/version combination already exists"
        )

    # Create product
    product = Product(
        cpe_uri=product_data.cpe_uri,
        vendor=product_data.vendor,
        product_name=product_data.product_name,
        version=product_data.version,
        part=product_data.part,
        description=product_data.description,
        is_monitored=product_data.is_monitored,
        source="custom"
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Update search index
    await _update_search_index(db, product)

    return ProductResponse.from_orm(product)


@router.patch("/{product_id}/monitoring", response_model=ProductResponse)
async def toggle_monitoring(
    product_id: int,
    update_data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle monitoring status for a product.

    When monitoring is disabled, vulnerabilities for this product
    will be hidden from the main dashboard view.
    """
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_monitored = update_data.is_monitored
    product.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(product)

    return ProductResponse.from_orm(product)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a custom product.

    Only custom products (source='custom') can be deleted.
    NVD CPE products are marked as deprecated instead.
    """
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.source != "custom":
        raise HTTPException(
            status_code=400,
            detail="Only custom products can be deleted. NVD products are deprecated automatically."
        )

    # Delete from search index first
    await db.execute(
        text("DELETE FROM product_search_index WHERE product_id = :product_id"),
        {"product_id": product_id}
    )

    await db.delete(product)
    await db.commit()


@router.get("/sync/status", response_model=List[CPESyncResponse])
async def get_sync_status(
    limit: int = Query(10, ge=1, le=100, description="Number of recent syncs to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent CPE dictionary sync history.

    Shows status of weekly synchronization jobs that update
    the product inventory from NVD.
    """
    result = await db.execute(
        select(CPESyncLog)
        .order_by(CPESyncLog.started_at.desc())
        .limit(limit)
    )
    syncs = result.scalars().all()

    return [CPESyncResponse.from_orm(sync) for sync in syncs]


@router.get("/vendors", response_model=List[str])
async def get_vendors(
    monitored_only: bool = Query(False, description="Show only vendors with monitored products"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all unique vendors.

    Useful for populating filter dropdowns in the UI.
    """
    query = select(Product.vendor).distinct()

    if monitored_only:
        query = query.where(Product.is_monitored == True)

    query = query.where(Product.deprecated == False)
    query = query.order_by(Product.vendor)

    result = await db.execute(query)
    vendors = [row[0] for row in result.fetchall()]

    return vendors


# Helper Functions

async def _update_search_index(db: AsyncSession, product: Product):
    """
    Update FTS5 search index for a product.

    Creates or updates the search index entry with combined searchable text.
    """
    # Combine searchable fields
    search_text = f"{product.vendor} {product.product_name}"
    if product.description:
        search_text += f" {product.description}"
    if product.cpe_uri:
        search_text += f" {product.cpe_uri}"

    # Check if index entry exists
    existing = await db.execute(
        select(ProductSearchIndex).where(ProductSearchIndex.product_id == product.id)
    )
    index_entry = existing.scalar_one_or_none()

    if index_entry:
        # Update existing entry
        index_entry.vendor = product.vendor
        index_entry.product_name = product.product_name
        index_entry.description = product.description
        index_entry.search_text = search_text
    else:
        # Create new entry
        index_entry = ProductSearchIndex(
            product_id=product.id,
            vendor=product.vendor,
            product_name=product.product_name,
            description=product.description,
            search_text=search_text
        )
        db.add(index_entry)

    await db.commit()
