"""
Database models for VulnDash application.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Table, Text, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class SourceType(enum.Enum):
    """Types of data sources."""
    NVD = "nvd"
    CISA_KEV = "cisa_kev"
    RSS = "rss"
    API = "api"
    URL_SCRAPER = "url_scraper"


class ProcessingStatus(enum.Enum):
    """Processing status for raw entries."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HealthStatus(enum.Enum):
    """Health status for data sources."""
    HEALTHY = "healthy"
    WARNING = "warning"
    FAILED = "failed"
    DISABLED = "disabled"


class DataSource(Base):
    """Configuration for external vulnerability feeds."""
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    source_type = Column(Enum(SourceType), nullable=False)
    url = Column(String(2048), nullable=True)
    description = Column(Text, nullable=True)

    # Polling configuration
    polling_interval_hours = Column(Integer, nullable=False, default=24)
    is_enabled = Column(Boolean, nullable=False, default=True)
    is_running = Column(Boolean, nullable=False, default=False)  # Lock flag

    # Authentication (encrypted JSON)
    auth_config_encrypted = Column(Text, nullable=True)

    # Health monitoring
    health_status = Column(Enum(HealthStatus), nullable=False, default=HealthStatus.HEALTHY)
    last_poll_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, nullable=False, default=0)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    raw_entries = relationship("RawEntry", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DataSource(id={self.id}, name='{self.name}', type={self.source_type.value})>"


class RawEntry(Base):
    """Staging table for ingested data before LLM processing."""
    __tablename__ = "raw_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False)

    # Raw data
    raw_payload = Column(JSON, nullable=False)
    raw_text = Column(Text, nullable=True)
    external_id = Column(String(512), nullable=True)  # Source's unique ID

    # Processing
    processing_status = Column(Enum(ProcessingStatus), nullable=False, default=ProcessingStatus.PENDING)
    processing_attempts = Column(Integer, nullable=False, default=0)
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    # Metadata
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    source = relationship("DataSource", back_populates="raw_entries")
    vulnerability = relationship("Vulnerability", back_populates="raw_entry", uselist=False)

    # Unique constraint on source + external_id for deduplication
    __table_args__ = (
        UniqueConstraint('source_id', 'external_id', name='uq_source_external_id'),
    )

    def __repr__(self):
        return f"<RawEntry(id={self.id}, source_id={self.source_id}, status={self.processing_status.value})>"


# Association table for many-to-many relationship
vulnerability_product = Table(
    'vulnerability_product',
    Base.metadata,
    Column('vulnerability_id', String(64), ForeignKey('vulnerabilities.cve_id', ondelete="CASCADE"), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id', ondelete="CASCADE"), primary_key=True)
)


class Vulnerability(Base):
    """Core structured vulnerability record."""
    __tablename__ = "vulnerabilities"

    cve_id = Column(String(64), primary_key=True)
    raw_entry_id = Column(Integer, ForeignKey("raw_entries.id", ondelete="SET NULL"), nullable=True)

    # Vulnerability details
    title = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    published_date = Column(DateTime, nullable=True)

    # Scoring
    cvss_score = Column(Float, nullable=True)
    cvss_vector = Column(String(256), nullable=True)
    severity = Column(String(32), nullable=True)  # CRITICAL, HIGH, MEDIUM, LOW

    # Enrichment
    epss_score = Column(Float, nullable=True)
    epss_percentile = Column(Float, nullable=True)
    enriched_at = Column(DateTime, nullable=True)  # EPSS enrichment timestamp
    kev_status = Column(Boolean, nullable=False, default=False)
    kev_date_added = Column(DateTime, nullable=True)

    # LLM extraction metadata
    confidence_score = Column(Float, nullable=True)
    needs_review = Column(Boolean, nullable=False, default=False)

    # Status tracking
    is_remediated = Column(Boolean, nullable=False, default=False)
    remediated_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    raw_entry = relationship("RawEntry", back_populates="vulnerability")
    products = relationship("Product", secondary=vulnerability_product, back_populates="vulnerabilities")

    def __repr__(self):
        return f"<Vulnerability(cve_id='{self.cve_id}', severity={self.severity})>"


class Product(Base):
    """Product inventory from NVD CPE Dictionary."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # CPE information
    cpe_uri = Column(String(512), nullable=False, unique=True)
    vendor = Column(String(256), nullable=False)
    product_name = Column(String(256), nullable=False)
    version = Column(String(128), nullable=True)

    # Configuration
    is_monitored = Column(Boolean, nullable=False, default=False)
    is_custom = Column(Boolean, nullable=False, default=False)  # User-added vs NVD

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vulnerabilities = relationship("Vulnerability", secondary=vulnerability_product, back_populates="products")

    def __repr__(self):
        return f"<Product(id={self.id}, vendor='{self.vendor}', product='{self.product_name}')>"


class LLMConfig(Base):
    """Configuration for LLM integration (Ollama)."""
    __tablename__ = "llm_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Connection
    endpoint_url = Column(String(512), nullable=False)
    model_name = Column(String(128), nullable=False)

    # Processing
    processing_interval_minutes = Column(Integer, nullable=False, default=15)
    batch_size = Column(Integer, nullable=False, default=10)

    # Thresholds
    confidence_threshold = Column(Float, nullable=False, default=0.8)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    last_connection_test = Column(DateTime, nullable=True)
    connection_healthy = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LLMConfig(id={self.id}, model='{self.model_name}')>"


class SMTPConfig(Base):
    """SMTP configuration for email notifications."""
    __tablename__ = "smtp_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # SMTP Connection (encrypted in practice)
    smtp_host = Column(String(256), nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_username = Column(String(256), nullable=True)
    smtp_password_encrypted = Column(Text, nullable=True)  # Encrypted value
    use_tls = Column(Boolean, nullable=False, default=True)

    # Sender information
    sender_email = Column(String(256), nullable=False)
    sender_name = Column(String(256), nullable=False, default="VulnDash Alerts")

    # Configuration flags
    is_enabled = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, nullable=False, default=False)

    # Status tracking
    last_test_at = Column(DateTime, nullable=True)
    last_test_success = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SMTPConfig(id={self.id}, host='{self.smtp_host}', sender='{self.sender_email}')>"


class EmailNotificationConfig(Base):
    """Email notification settings for vulnerability alerts."""
    __tablename__ = "email_notification_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Notification triggers
    alert_on_kev = Column(Boolean, nullable=False, default=True)  # Alert on new KEV vulnerabilities
    alert_on_high_epss = Column(Boolean, nullable=False, default=True)  # Alert on high EPSS scores
    epss_threshold = Column(Float, nullable=False, default=0.8)  # EPSS percentile threshold (0-1)

    # Recipients
    recipient_emails = Column(JSON, nullable=False, default=list)  # List of email addresses

    # Digest settings
    digest_enabled = Column(Boolean, nullable=False, default=True)
    digest_hours = Column(Integer, nullable=False, default=24)  # Collect alerts every N hours

    # Configuration flags
    is_enabled = Column(Boolean, nullable=False, default=False)

    # Status tracking
    last_alert_at = Column(DateTime, nullable=True)
    last_digest_at = Column(DateTime, nullable=True)
    alert_count_since_digest = Column(Integer, nullable=False, default=0)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EmailNotificationConfig(id={self.id}, enabled={self.is_enabled})>"


class EmailAlert(Base):
    """Log of sent email alerts."""
    __tablename__ = "email_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Alert details
    vulnerability_id = Column(String(64), ForeignKey("vulnerabilities.cve_id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(32), nullable=False)  # 'kev' or 'high_epss'
    recipient_email = Column(String(256), nullable=False)

    # Send status
    sent_at = Column(DateTime, nullable=True)
    send_status = Column(String(32), nullable=False, default="pending")  # pending, sent, failed
    error_message = Column(Text, nullable=True)

    # Email content preview
    subject = Column(String(512), nullable=True)
    sent_via_digest = Column(Boolean, nullable=False, default=False)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    vulnerability = relationship("Vulnerability")

    def __repr__(self):
        return f"<EmailAlert(id={self.id}, type='{self.alert_type}', status='{self.send_status}')>"
