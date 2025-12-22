"""
Product inventory models for VulnDash.

Manages the CPE dictionary and custom product entries for vulnerability matching.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Product(Base):
    """
    Product inventory from NVD CPE Dictionary and custom entries.

    Supports FTS5 full-text search for finding products by vendor/name.
    Products can be toggled for monitoring to filter vulnerability display.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpe_uri = Column(String(500), unique=True, nullable=True, index=True)
    vendor = Column(String(200), nullable=False, index=True)
    product_name = Column(String(200), nullable=False, index=True)
    version = Column(String(100), nullable=True)
    part = Column(String(1), nullable=True)  # 'a' (application), 'o' (OS), 'h' (hardware)

    # Monitoring flag - only monitored products show in vulnerability filters
    is_monitored = Column(Boolean, default=False, nullable=False, index=True)

    # Source tracking
    source = Column(String(50), default="nvd_cpe", nullable=False)  # 'nvd_cpe' or 'custom'

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_synced_at = Column(DateTime, nullable=True)  # Last sync from NVD

    # Additional metadata
    description = Column(Text, nullable=True)
    deprecated = Column(Boolean, default=False, nullable=False)

    # Relationships
    vulnerabilities = relationship(
        "Vulnerability",
        secondary="vulnerability_product",
        back_populates="products"
    )

    # Indexes for performance
    __table_args__ = (
        Index('idx_vendor_product', 'vendor', 'product_name'),
        Index('idx_monitored', 'is_monitored'),
        Index('idx_source', 'source'),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, vendor='{self.vendor}', product='{self.product_name}', monitored={self.is_monitored})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "cpe_uri": self.cpe_uri,
            "vendor": self.vendor,
            "product_name": self.product_name,
            "version": self.version,
            "part": self.part,
            "is_monitored": self.is_monitored,
            "source": self.source,
            "description": self.description,
            "deprecated": self.deprecated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
        }


class ProductSearchIndex(Base):
    """
    FTS5 virtual table for full-text search of products.

    SQLite FTS5 extension provides fast searching across vendor and product names.
    This is a separate table that mirrors the products table for search.
    """
    __tablename__ = "product_search_index"

    rowid = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False, index=True)
    vendor = Column(Text, nullable=False)
    product_name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    search_text = Column(Text, nullable=False)  # Combined searchable text

    def __repr__(self):
        return f"<ProductSearchIndex(product_id={self.product_id}, text='{self.search_text[:50]}...')>"


class CPESyncLog(Base):
    """
    Tracks CPE dictionary synchronization from NVD.

    Weekly sync jobs fetch the latest CPE dictionary to keep product inventory current.
    """
    __tablename__ = "cpe_sync_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # 'running', 'success', 'failed'
    products_added = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    products_deprecated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # NVD API metadata
    nvd_timestamp = Column(DateTime, nullable=True)  # Last modified timestamp from NVD
    total_results = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<CPESyncLog(id={self.id}, status='{self.status}', added={self.products_added})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "products_added": self.products_added,
            "products_updated": self.products_updated,
            "products_deprecated": self.products_deprecated,
            "error_message": self.error_message,
            "nvd_timestamp": self.nvd_timestamp.isoformat() if self.nvd_timestamp else None,
            "total_results": self.total_results,
        }
