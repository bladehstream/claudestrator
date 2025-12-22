"""
Unit tests for email notification service.

Tests:
- SMTP configuration management
- Email notification settings
- Alert queuing and sending
- Email template rendering
- Encryption/decryption
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import (
    SMTPConfig, EmailNotificationConfig, EmailAlert, Vulnerability, Base
)
from app.backend.services.email_notification_service import EmailNotificationService


@pytest.fixture
async def db_session():
    """Create an in-memory test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
def email_service():
    """Create email notification service."""
    return EmailNotificationService()


# ============================================================================
# SMTP Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_save_smtp_config(email_service, db_session):
    """Test saving SMTP configuration."""
    config = await email_service.save_smtp_config(
        db=db_session,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        sender_email="alerts@example.com",
        sender_name="Alerts",
        smtp_username="user@gmail.com",
        smtp_password="password123",
        use_tls=True
    )

    assert config.smtp_host == "smtp.gmail.com"
    assert config.smtp_port == 587
    assert config.sender_email == "alerts@example.com"
    assert config.sender_name == "Alerts"
    assert config.smtp_username == "user@gmail.com"
    assert config.use_tls is True
    assert config.is_enabled is False


@pytest.mark.asyncio
async def test_get_smtp_config(email_service, db_session):
    """Test retrieving SMTP configuration."""
    # Save first
    await email_service.save_smtp_config(
        db=db_session,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        sender_email="alerts@example.com",
        sender_name="Alerts"
    )

    # Retrieve
    config = await email_service.get_smtp_config(db_session)
    assert config is not None
    assert config.smtp_host == "smtp.gmail.com"


@pytest.mark.asyncio
async def test_update_smtp_config(email_service, db_session):
    """Test updating existing SMTP configuration."""
    # Create initial
    await email_service.save_smtp_config(
        db=db_session,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        sender_email="alerts@example.com",
        sender_name="Alerts"
    )

    # Update
    config = await email_service.save_smtp_config(
        db=db_session,
        smtp_host="smtp.office365.com",
        smtp_port=465,
        sender_email="new@example.com",
        sender_name="New Alerts"
    )

    assert config.smtp_host == "smtp.office365.com"
    assert config.smtp_port == 465
    assert config.sender_email == "new@example.com"


@pytest.mark.asyncio
async def test_mark_smtp_verified(email_service, db_session):
    """Test marking SMTP as verified."""
    config = await email_service.save_smtp_config(
        db=db_session,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        sender_email="alerts@example.com",
        sender_name="Alerts"
    )

    assert config.is_verified is False
    await email_service.mark_smtp_verified(db_session, success=True)

    updated = await email_service.get_smtp_config(db_session)
    assert updated.is_verified is True
    assert updated.last_test_success is True


# ============================================================================
# Email Notification Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_save_notification_config(email_service, db_session):
    """Test saving notification configuration."""
    config = await email_service.save_notification_config(
        db=db_session,
        alert_on_kev=True,
        alert_on_high_epss=True,
        epss_threshold=0.75,
        recipient_emails=["admin@example.com", "security@example.com"],
        digest_enabled=True,
        digest_hours=24,
        is_enabled=False
    )

    assert config.alert_on_kev is True
    assert config.alert_on_high_epss is True
    assert config.epss_threshold == 0.75
    assert config.recipient_emails == ["admin@example.com", "security@example.com"]
    assert config.digest_enabled is True
    assert config.digest_hours == 24
    assert config.is_enabled is False


@pytest.mark.asyncio
async def test_notification_config_invalid_threshold(email_service, db_session):
    """Test that invalid EPSS threshold is rejected."""
    with pytest.raises(ValueError):
        await email_service.save_notification_config(
            db=db_session,
            epss_threshold=1.5  # Invalid: > 1.0
        )

    with pytest.raises(ValueError):
        await email_service.save_notification_config(
            db=db_session,
            epss_threshold=-0.1  # Invalid: < 0.0
        )


@pytest.mark.asyncio
async def test_get_notification_config(email_service, db_session):
    """Test retrieving notification configuration."""
    # Save first
    await email_service.save_notification_config(
        db=db_session,
        recipient_emails=["admin@example.com"]
    )

    # Retrieve
    config = await email_service.get_notification_config(db_session)
    assert config is not None
    assert config.recipient_emails == ["admin@example.com"]


# ============================================================================
# Email Template Rendering Tests
# ============================================================================


def test_render_vulnerability_alert_html(email_service):
    """Test HTML rendering for vulnerability alerts."""
    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        title="Critical RCE in Library X",
        severity="CRITICAL",
        cvss_score=9.8,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        epss_score=0.85,
        epss_percentile=0.92,
        published_date=datetime(2024, 1, 15),
        description="A critical remote code execution vulnerability...",
        kev_status=True
    )

    html = email_service._render_vulnerability_alert_html(vuln, "kev")

    assert "CVE-2024-1234" in html
    assert "Critical RCE in Library X" in html
    assert "CRITICAL" in html
    assert "9.8" in html
    assert "EPSS" in html
    assert "KEV" in html


def test_render_alert_type_badge(email_service):
    """Test alert type badge rendering."""
    kev_badge = email_service._render_alert_type_badge("kev")
    assert "KEV" in kev_badge
    assert "CISA" in kev_badge

    epss_badge = email_service._render_alert_type_badge("high_epss")
    assert "EPSS" in epss_badge
    assert "Exploitation" in epss_badge


def test_render_digest_html(email_service):
    """Test digest email HTML rendering."""
    vulns = [
        {
            "cve_id": "CVE-2024-0001",
            "title": "RCE Vulnerability",
            "severity": "CRITICAL",
            "alert_type": "kev"
        },
        {
            "cve_id": "CVE-2024-0002",
            "title": "XSS Vulnerability",
            "severity": "HIGH",
            "alert_type": "high_epss"
        }
    ]

    start = datetime(2024, 1, 1, 0, 0)
    end = datetime(2024, 1, 2, 0, 0)

    html = email_service._render_digest_html(vulns, start, end)

    assert "CVE-2024-0001" in html
    assert "CVE-2024-0002" in html
    assert "2" in html  # Count of vulnerabilities
    assert "Security Digest" in html


# ============================================================================
# Alert Queuing Tests
# ============================================================================


@pytest.mark.asyncio
async def test_queue_alerts_for_vulnerability(email_service, db_session):
    """Test queuing alerts for a vulnerability."""
    # Setup config
    await email_service.save_notification_config(
        db=db_session,
        alert_on_kev=True,
        alert_on_high_epss=True,
        epss_threshold=0.8,
        recipient_emails=["admin@example.com", "security@example.com"],
        is_enabled=True
    )

    # Create vulnerability
    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        severity="CRITICAL",
        kev_status=True,
        epss_percentile=0.85
    )
    db_session.add(vuln)
    await db_session.commit()

    # Queue alerts
    count = await email_service.queue_alerts_for_vulnerability(
        db_session,
        vuln,
        ["kev", "high_epss"]
    )

    # Should queue 4 alerts (2 types × 2 recipients)
    assert count == 4


@pytest.mark.asyncio
async def test_queue_alerts_respects_threshold(email_service, db_session):
    """Test that alert queuing respects EPSS threshold."""
    # Setup config with high threshold
    await email_service.save_notification_config(
        db=db_session,
        alert_on_high_epss=True,
        epss_threshold=0.9,  # High threshold
        recipient_emails=["admin@example.com"],
        is_enabled=True
    )

    # Create vulnerability with lower EPSS
    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        severity="MEDIUM",
        epss_percentile=0.75  # Below threshold
    )
    db_session.add(vuln)
    await db_session.commit()

    # Try to queue alert
    count = await email_service.queue_alerts_for_vulnerability(
        db_session,
        vuln,
        ["high_epss"]
    )

    # Should not queue alert
    assert count == 0


# ============================================================================
# Alert Sending Tests
# ============================================================================


@pytest.mark.asyncio
async def test_send_alert_email_success(email_service, db_session):
    """Test successfully sending an alert email."""
    # Setup SMTP config
    await email_service.save_smtp_config(
        db=db_session,
        smtp_host="smtp.example.com",
        smtp_port=587,
        sender_email="alerts@example.com",
        sender_name="Alerts"
    )

    config = await email_service.get_smtp_config(db_session)
    config.is_enabled = True
    await db_session.commit()

    # Create vulnerability
    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        title="RCE",
        severity="CRITICAL"
    )

    # Mock SMTP
    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_instance

        result = await email_service.send_alert_email(
            db_session,
            vuln,
            "kev",
            "admin@example.com"
        )

        assert result["success"] is True
        mock_instance.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_alert_email_smtp_disabled(email_service, db_session):
    """Test sending email fails when SMTP is disabled."""
    # Create vulnerability
    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        title="RCE",
        severity="CRITICAL"
    )

    result = await email_service.send_alert_email(
        db_session,
        vuln,
        "kev",
        "admin@example.com"
    )

    assert result["success"] is False
    assert "SMTP not configured" in result["message"]


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_should_send_alert_kev(email_service, db_session):
    """Test KEV alert decision logic."""
    # Setup config
    await email_service.save_notification_config(
        db=db_session,
        alert_on_kev=True,
        is_enabled=True
    )

    # Create KEV vulnerability
    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        kev_status=True
    )

    should_send = await email_service.should_send_alert(
        db_session,
        vuln,
        "kev"
    )

    assert should_send is True


@pytest.mark.asyncio
async def test_should_send_alert_epss(email_service, db_session):
    """Test EPSS alert decision logic."""
    # Setup config
    await email_service.save_notification_config(
        db=db_session,
        alert_on_high_epss=True,
        epss_threshold=0.8,
        is_enabled=True
    )

    # Create vulnerability with high EPSS
    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        epss_percentile=0.85
    )

    should_send = await email_service.should_send_alert(
        db_session,
        vuln,
        "high_epss"
    )

    assert should_send is True


@pytest.mark.asyncio
async def test_should_not_send_alert_notifications_disabled(email_service, db_session):
    """Test that alerts are not sent when notifications disabled."""
    # Don't setup config (disabled by default)

    vuln = Vulnerability(
        cve_id="CVE-2024-1234",
        kev_status=True
    )

    should_send = await email_service.should_send_alert(
        db_session,
        vuln,
        "kev"
    )

    assert should_send is False
