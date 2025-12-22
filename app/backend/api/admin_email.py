"""
Admin API endpoints for email notification configuration.

Endpoints for:
- SMTP configuration management
- Email notification settings
- Alert recipient management
- Test email sending
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.database import get_db
from app.backend.services.email_notification_service import EmailNotificationService

router = APIRouter(prefix="/admin/email", tags=["admin-email"])
email_service = EmailNotificationService()


# ============================================================================
# Request/Response Models
# ============================================================================


class SMTPConfigRequest(BaseModel):
    """SMTP configuration request."""
    smtp_host: str = Field(..., min_length=1, max_length=256, example="smtp.gmail.com")
    smtp_port: int = Field(default=587, ge=1, le=65535, example=587)
    smtp_username: Optional[str] = Field(None, max_length=256, example="your-email@gmail.com")
    smtp_password: Optional[str] = Field(None, max_length=512, example="app-password")
    sender_email: EmailStr = Field(..., example="alerts@vulndash.local")
    sender_name: str = Field(default="VulnDash Alerts", max_length=256)
    use_tls: bool = Field(default=True, example=True)


class SMTPConfigResponse(BaseModel):
    """SMTP configuration response."""
    id: int
    smtp_host: str
    smtp_port: int
    sender_email: str
    sender_name: str
    use_tls: bool
    is_enabled: bool
    is_verified: bool
    last_test_success: Optional[bool]
    last_test_at: Optional[str]

    class Config:
        from_attributes = True


class SMTPTestRequest(BaseModel):
    """SMTP test request."""
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True


class SMTPTestResponse(BaseModel):
    """SMTP test response."""
    success: bool
    message: str


class EmailNotificationConfigRequest(BaseModel):
    """Email notification configuration request."""
    alert_on_kev: bool = Field(default=True, description="Alert on new KEV vulnerabilities")
    alert_on_high_epss: bool = Field(default=True, description="Alert on high EPSS scores")
    epss_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="EPSS percentile threshold (0-1)"
    )
    recipient_emails: List[EmailStr] = Field(
        default=[],
        description="List of recipient email addresses"
    )
    digest_enabled: bool = Field(default=True, description="Enable digest mode")
    digest_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours between digest emails"
    )
    is_enabled: bool = Field(default=False, description="Enable notifications")


class EmailNotificationConfigResponse(BaseModel):
    """Email notification configuration response."""
    id: int
    alert_on_kev: bool
    alert_on_high_epss: bool
    epss_threshold: float
    recipient_emails: List[str]
    digest_enabled: bool
    digest_hours: int
    is_enabled: bool
    alert_count_since_digest: int
    last_alert_at: Optional[str]
    last_digest_at: Optional[str]

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Health check response."""
    smtp_configured: bool
    smtp_verified: bool
    notifications_enabled: bool
    recipients_count: int
    message: str


# ============================================================================
# SMTP Configuration Endpoints
# ============================================================================


@router.get(
    "/smtp/config",
    response_model=Optional[SMTPConfigResponse],
    summary="Get SMTP Configuration",
    description="Get current SMTP configuration for email notifications"
)
async def get_smtp_config(db: AsyncSession = Depends(get_db)):
    """Get SMTP configuration."""
    config = await email_service.get_smtp_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMTP configuration not found"
        )
    return config


@router.post(
    "/smtp/config",
    response_model=SMTPConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save SMTP Configuration",
    description="Save or update SMTP configuration"
)
async def save_smtp_config(
    request: SMTPConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """Save SMTP configuration."""
    config = await email_service.save_smtp_config(
        db=db,
        smtp_host=request.smtp_host,
        smtp_port=request.smtp_port,
        sender_email=request.sender_email,
        sender_name=request.sender_name,
        smtp_username=request.smtp_username,
        smtp_password=request.smtp_password,
        use_tls=request.use_tls
    )
    return config


@router.post(
    "/smtp/test",
    response_model=SMTPTestResponse,
    summary="Test SMTP Connection",
    description="Test SMTP server connectivity and authentication"
)
async def test_smtp_connection(
    request: SMTPTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Test SMTP connection."""
    result = await email_service.test_smtp_connection(
        db=db,
        smtp_host=request.smtp_host,
        smtp_port=request.smtp_port,
        smtp_username=request.smtp_username,
        smtp_password=request.smtp_password,
        use_tls=request.use_tls
    )

    if result["success"]:
        # Mark SMTP as verified if test succeeds
        await email_service.mark_smtp_verified(db, success=True)

    return result


@router.post(
    "/smtp/enable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Enable SMTP",
    description="Enable SMTP for sending emails"
)
async def enable_smtp(db: AsyncSession = Depends(get_db)):
    """Enable SMTP."""
    config = await email_service.get_smtp_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMTP configuration not found"
        )
    if not config.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMTP must be verified before enabling"
        )
    config.is_enabled = True
    await db.commit()


@router.post(
    "/smtp/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disable SMTP",
    description="Disable SMTP temporarily"
)
async def disable_smtp(db: AsyncSession = Depends(get_db)):
    """Disable SMTP."""
    config = await email_service.get_smtp_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMTP configuration not found"
        )
    config.is_enabled = False
    await db.commit()


# ============================================================================
# Email Notification Configuration Endpoints
# ============================================================================


@router.get(
    "/notification/config",
    response_model=Optional[EmailNotificationConfigResponse],
    summary="Get Email Notification Configuration",
    description="Get current email notification settings"
)
async def get_notification_config(db: AsyncSession = Depends(get_db)):
    """Get notification configuration."""
    config = await email_service.get_notification_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification configuration not found"
        )
    return config


@router.post(
    "/notification/config",
    response_model=EmailNotificationConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save Email Notification Configuration",
    description="Save or update email notification settings"
)
async def save_notification_config(
    request: EmailNotificationConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """Save notification configuration."""
    config = await email_service.save_notification_config(
        db=db,
        alert_on_kev=request.alert_on_kev,
        alert_on_high_epss=request.alert_on_high_epss,
        epss_threshold=request.epss_threshold,
        recipient_emails=request.recipient_emails,
        digest_enabled=request.digest_enabled,
        digest_hours=request.digest_hours,
        is_enabled=request.is_enabled
    )
    return config


@router.post(
    "/notification/enable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Enable Email Notifications",
    description="Enable vulnerability alert emails"
)
async def enable_notifications(db: AsyncSession = Depends(get_db)):
    """Enable notifications."""
    config = await email_service.get_notification_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification configuration not found"
        )

    smtp_config = await email_service.get_smtp_config(db)
    if not smtp_config or not smtp_config.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMTP must be configured and enabled first"
        )

    if not config.recipient_emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one recipient email is required"
        )

    config.is_enabled = True
    await db.commit()


@router.post(
    "/notification/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disable Email Notifications",
    description="Disable vulnerability alert emails"
)
async def disable_notifications(db: AsyncSession = Depends(get_db)):
    """Disable notifications."""
    config = await email_service.get_notification_config(db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification configuration not found"
        )
    config.is_enabled = False
    await db.commit()


# ============================================================================
# Health Check Endpoint
# ============================================================================


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Email System Health Check",
    description="Check SMTP and notification system health"
)
async def email_health_check(db: AsyncSession = Depends(get_db)):
    """Check email system health."""
    smtp_config = await email_service.get_smtp_config(db)
    notification_config = await email_service.get_notification_config(db)

    smtp_configured = smtp_config is not None
    smtp_verified = smtp_config.is_verified if smtp_config else False
    notifications_enabled = notification_config.is_enabled if notification_config else False
    recipients_count = len(notification_config.recipient_emails) if notification_config else 0

    # Determine overall status
    if not smtp_configured:
        message = "SMTP not configured"
    elif not smtp_verified:
        message = "SMTP not verified"
    elif not notifications_enabled:
        message = "Notifications disabled"
    elif recipients_count == 0:
        message = "No recipient emails configured"
    else:
        message = "Email system ready"

    return {
        "smtp_configured": smtp_configured,
        "smtp_verified": smtp_verified,
        "notifications_enabled": notifications_enabled,
        "recipients_count": recipients_count,
        "message": message
    }
