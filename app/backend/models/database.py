"""
Database models for VulnDash.
Implements the core schema for vulnerability management.
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, Table, JSON, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SourceType(str, Enum):
    """Types of vulnerability data sources."""
    NVD = "nvd"
    CISA_KEV = "cisa_kev"
    RSS = "rss"
    CUSTOM_API = "custom_api"
    URL_SCRAPE = "url_scrape"


class ProcessingStatus(str, Enum):
    """Status of raw entry processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


# Association table for many-to-many relationship
vulnerability_product = Table(
    'vulnerability_product',
    Base.metadata,
    Column('vulnerability_id', String(20), ForeignKey('vulnerabilities.cve_id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Index('idx_vuln_product_vuln', 'vulnerability_id'),
    Index('idx_vuln_product_prod', 'product_id'),
)


class DataSource(Base):
    """Configuration for external vulnerability feeds."""
    __tablename__ = 'data_sources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    polling_interval_hours = Column(Integer, default=24, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    is_running = Column(Boolean, default=False, nullable=False)  # Lock flag

    # Auth config stored as encrypted JSON
    auth_config_encrypted = Column(Text, nullable=True)

    # Health monitoring
    last_poll_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    raw_entries = relationship("RawEntry", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DataSource(id={self.id}, name='{self.name}', type='{self.source_type}')>"


class RawEntry(Base):
    """Staging table for ingested data before LLM processing."""
    __tablename__ = 'raw_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey('data_sources.id'), nullable=False)

    # Raw payload from the source
    raw_payload = Column(Text, nullable=False)
    raw_metadata = Column(JSON, nullable=True)  # Additional context (headers, etc.)

    # Processing tracking
    processing_status = Column(String(20), default=ProcessingStatus.PENDING.value, nullable=False)
    processing_attempts = Column(Integer, default=0, nullable=False)
    last_processing_error = Column(Text, nullable=True)

    # Timestamps
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    source = relationship("DataSource", back_populates="raw_entries")

    __table_args__ = (
        Index('idx_raw_status', 'processing_status'),
        Index('idx_raw_ingested', 'ingested_at'),
    )

    def __repr__(self):
        return f"<RawEntry(id={self.id}, source_id={self.source_id}, status='{self.processing_status}')>"


class Vulnerability(Base):
    """Core structured vulnerability record extracted from raw entries."""
    __tablename__ = 'vulnerabilities'

    cve_id = Column(String(20), primary_key=True)  # e.g., CVE-2024-1234

    # Core vulnerability data
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=False)

    # Severity scoring
    cvss_score = Column(Float, nullable=True)
    cvss_vector = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=True)  # CRITICAL, HIGH, MEDIUM, LOW

    # Threat intelligence
    epss_score = Column(Float, nullable=True)  # Exploitation probability
    kev_status = Column(Boolean, default=False, nullable=False)  # CISA Known Exploited
    kev_date_added = Column(DateTime, nullable=True)

    # LLM extraction metadata
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    needs_review = Column(Boolean, default=False, nullable=False)
    extraction_metadata = Column(JSON, nullable=True)  # LLM model, prompts, etc.

    # Lifecycle management
    remediated_at = Column(DateTime, nullable=True)
    published_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    products = relationship("Product", secondary=vulnerability_product, back_populates="vulnerabilities")

    __table_args__ = (
        Index('idx_vuln_severity', 'severity'),
        Index('idx_vuln_kev', 'kev_status'),
        Index('idx_vuln_epss', 'epss_score'),
        Index('idx_vuln_needs_review', 'needs_review'),
        Index('idx_vuln_published', 'published_date'),
    )

    def __repr__(self):
        return f"<Vulnerability(cve_id='{self.cve_id}', severity='{self.severity}', confidence={self.confidence_score})>"


class Product(Base):
    """Product inventory from NVD CPE Dictionary and custom entries."""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # CPE data
    cpe_uri = Column(String(500), unique=True, nullable=True)  # e.g., cpe:2.3:a:vendor:product:*
    vendor = Column(String(200), nullable=False)
    product_name = Column(String(200), nullable=False)

    # Monitoring configuration
    is_monitored = Column(Boolean, default=False, nullable=False)

    # Metadata
    source = Column(String(50), default="manual", nullable=False)  # 'nvd', 'manual'

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    vulnerabilities = relationship("Vulnerability", secondary=vulnerability_product, back_populates="products")

    __table_args__ = (
        UniqueConstraint('vendor', 'product_name', name='uq_vendor_product'),
        Index('idx_product_monitored', 'is_monitored'),
        Index('idx_product_vendor', 'vendor'),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, vendor='{self.vendor}', product='{self.product_name}', monitored={self.is_monitored})>"


class LLMConfig(Base):
    """LLM configuration supporting multiple providers (Ollama, Claude, Gemini)."""
    __tablename__ = 'llm_config'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Primary provider
    primary_provider = Column(String(50), default="ollama", nullable=False)  # 'ollama', 'claude', 'gemini'

    # Fallback providers (comma-separated for simplicity)
    fallback_providers = Column(String(200), nullable=True)  # e.g., 'claude,gemini'

    # Provider-specific configurations stored as JSON
    provider_config = Column(JSON, default={}, nullable=False)  # {
    #   "ollama": {"base_url": "..."},
    #   "claude": {"api_key": "..."},
    #   "gemini": {"api_key": "..."}
    # }

    # Legacy Ollama-specific fields (deprecated but kept for migration)
    ollama_base_url = Column(String(500), default="http://localhost:11434", nullable=True)
    selected_model = Column(String(100), nullable=True)

    # Processing configuration
    temperature = Column(Float, default=0.1, nullable=False)
    max_tokens = Column(Integer, default=1000, nullable=False)
    confidence_threshold = Column(Float, default=0.8, nullable=False)  # Below this = needs_review

    # Processing schedule
    processing_interval_minutes = Column(Integer, default=30, nullable=False)
    batch_size = Column(Integer, default=10, nullable=False)

    # Health
    last_connection_test = Column(DateTime, nullable=True)
    connection_status = Column(String(50), default="unknown", nullable=False)
    available_models = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<LLMConfig(id={self.id}, primary='{self.primary_provider}', model='{self.selected_model}', status='{self.connection_status}')>"
