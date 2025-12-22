"""
Tests for email notification admin API endpoints.

Tests:
- SMTP configuration endpoints
- Email notification settings endpoints
- Health check endpoint
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.models import Base


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
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# SMTP Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_save_smtp_config(client):
    """Test saving SMTP configuration via API."""
    response = await client.post(
        "/admin/email/smtp/config",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "alerts@example.com",
            "sender_name": "Alerts",
            "smtp_username": "user@gmail.com",
            "smtp_password": "password123",
            "use_tls": True
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["smtp_host"] == "smtp.gmail.com"
    assert data["sender_email"] == "alerts@example.com"
    assert data["is_enabled"] is False


@pytest.mark.asyncio
async def test_get_smtp_config(client):
    """Test retrieving SMTP configuration via API."""
    # Create first
    await client.post(
        "/admin/email/smtp/config",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "alerts@example.com",
            "sender_name": "Alerts"
        }
    )

    # Retrieve
    response = await client.get("/admin/email/smtp/config")
    assert response.status_code == 200
    data = response.json()
    assert data["smtp_host"] == "smtp.gmail.com"


@pytest.mark.asyncio
async def test_get_smtp_config_not_found(client):
    """Test retrieving SMTP config when not configured."""
    response = await client.get("/admin/email/smtp/config")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_test_smtp_connection(client):
    """Test SMTP connection test endpoint."""
    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_instance

        response = await client.post(
            "/admin/email/smtp/test",
            json={
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_username": "user@gmail.com",
                "smtp_password": "password123",
                "use_tls": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_enable_smtp(client):
    """Test enabling SMTP."""
    # Create and verify first
    await client.post(
        "/admin/email/smtp/config",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "alerts@example.com",
            "sender_name": "Alerts"
        }
    )

    # Mark as verified
    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_instance

        await client.post(
            "/admin/email/smtp/test",
            json={
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587
            }
        )

    # Enable
    response = await client.post("/admin/email/smtp/enable")
    assert response.status_code == 204

    # Verify
    config_response = await client.get("/admin/email/smtp/config")
    assert config_response.json()["is_enabled"] is True


@pytest.mark.asyncio
async def test_disable_smtp(client):
    """Test disabling SMTP."""
    # Create first
    await client.post(
        "/admin/email/smtp/config",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "alerts@example.com",
            "sender_name": "Alerts"
        }
    )

    # Disable
    response = await client.post("/admin/email/smtp/disable")
    assert response.status_code == 204


# ============================================================================
# Email Notification Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_save_notification_config(client):
    """Test saving notification configuration via API."""
    response = await client.post(
        "/admin/email/notification/config",
        json={
            "alert_on_kev": True,
            "alert_on_high_epss": True,
            "epss_threshold": 0.75,
            "recipient_emails": ["admin@example.com", "security@example.com"],
            "digest_enabled": True,
            "digest_hours": 24,
            "is_enabled": False
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["alert_on_kev"] is True
    assert data["epss_threshold"] == 0.75
    assert len(data["recipient_emails"]) == 2


@pytest.mark.asyncio
async def test_get_notification_config(client):
    """Test retrieving notification configuration via API."""
    # Create first
    await client.post(
        "/admin/email/notification/config",
        json={
            "recipient_emails": ["admin@example.com"]
        }
    )

    # Retrieve
    response = await client.get("/admin/email/notification/config")
    assert response.status_code == 200
    data = response.json()
    assert "admin@example.com" in data["recipient_emails"]


@pytest.mark.asyncio
async def test_save_notification_config_invalid_threshold(client):
    """Test that invalid EPSS threshold is rejected."""
    response = await client.post(
        "/admin/email/notification/config",
        json={
            "epss_threshold": 1.5  # Invalid
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_enable_notifications(client):
    """Test enabling notifications."""
    # Setup SMTP first
    await client.post(
        "/admin/email/smtp/config",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "alerts@example.com",
            "sender_name": "Alerts"
        }
    )

    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_instance

        await client.post(
            "/admin/email/smtp/test",
            json={
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587
            }
        )

    await client.post("/admin/email/smtp/enable")

    # Setup notifications
    await client.post(
        "/admin/email/notification/config",
        json={
            "recipient_emails": ["admin@example.com"]
        }
    )

    # Enable
    response = await client.post("/admin/email/notification/enable")
    assert response.status_code == 204

    # Verify
    config_response = await client.get("/admin/email/notification/config")
    assert config_response.json()["is_enabled"] is True


@pytest.mark.asyncio
async def test_enable_notifications_smtp_not_enabled(client):
    """Test that enabling notifications fails without SMTP."""
    # Setup notifications but no SMTP
    await client.post(
        "/admin/email/notification/config",
        json={
            "recipient_emails": ["admin@example.com"]
        }
    )

    # Try to enable
    response = await client.post("/admin/email/notification/enable")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_disable_notifications(client):
    """Test disabling notifications."""
    # Create first
    await client.post(
        "/admin/email/notification/config",
        json={
            "recipient_emails": ["admin@example.com"]
        }
    )

    # Disable
    response = await client.post("/admin/email/notification/disable")
    assert response.status_code == 204


# ============================================================================
# Health Check Tests
# ============================================================================


@pytest.mark.asyncio
async def test_email_health_check_not_configured(client):
    """Test health check when nothing configured."""
    response = await client.get("/admin/email/health")
    assert response.status_code == 200
    data = response.json()
    assert data["smtp_configured"] is False
    assert data["notifications_enabled"] is False
    assert "SMTP not configured" in data["message"]


@pytest.mark.asyncio
async def test_email_health_check_configured(client):
    """Test health check when SMTP and notifications configured."""
    # Setup SMTP
    await client.post(
        "/admin/email/smtp/config",
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "alerts@example.com",
            "sender_name": "Alerts"
        }
    )

    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_instance

        await client.post(
            "/admin/email/smtp/test",
            json={
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587
            }
        )

    await client.post("/admin/email/smtp/enable")

    # Setup notifications
    await client.post(
        "/admin/email/notification/config",
        json={
            "recipient_emails": ["admin@example.com", "security@example.com"]
        }
    )

    await client.post("/admin/email/notification/enable")

    # Check health
    response = await client.get("/admin/email/health")
    assert response.status_code == 200
    data = response.json()
    assert data["smtp_configured"] is True
    assert data["smtp_verified"] is True
    assert data["notifications_enabled"] is True
    assert data["recipients_count"] == 2
    assert "ready" in data["message"]
