"""
Email notification service for vulnerability alerts.

Handles SMTP configuration, email template rendering, and alert sending.
Supports both immediate alerts and digest mode (batching alerts).
"""

import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Dict, Any
from aiosmtplib import SMTP
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
import os

from app.database.models import (
    SMTPConfig, EmailNotificationConfig, EmailAlert, Vulnerability
)

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for managing email notifications for vulnerability alerts."""

    def __init__(self):
        """Initialize email service with encryption key."""
        # In production, load from secure storage
        self._encryption_key = os.getenv("EMAIL_ENCRYPTION_KEY")
        if self._encryption_key:
            try:
                self._cipher = Fernet(self._encryption_key.encode())
            except Exception as e:
                logger.warning(f"Failed to initialize encryption: {e}")
                self._cipher = None
        else:
            self._cipher = None

    def _encrypt_password(self, password: str) -> str:
        """Encrypt SMTP password."""
        if not self._cipher or not password:
            return password
        try:
            return self._cipher.encrypt(password.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt password: {e}")
            return password

    def _decrypt_password(self, encrypted: str) -> str:
        """Decrypt SMTP password."""
        if not self._cipher or not encrypted:
            return encrypted
        try:
            return self._cipher.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt password: {e}")
            return encrypted

    async def test_smtp_connection(
        self,
        db: AsyncSession,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        use_tls: bool
    ) -> Dict[str, Any]:
        """
        Test SMTP connection.

        Args:
            db: Database session
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            use_tls: Whether to use TLS

        Returns:
            Test result dictionary with success status and message
        """
        try:
            async with SMTP(
                hostname=smtp_host,
                port=smtp_port,
                use_tls=use_tls,
                timeout=10
            ) as smtp:
                if smtp_username and smtp_password:
                    await smtp.login(smtp_username, smtp_password)

                logger.info(f"SMTP connection test successful to {smtp_host}:{smtp_port}")
                return {
                    "success": True,
                    "message": f"Connected to {smtp_host}:{smtp_port}"
                }

        except Exception as e:
            error_msg = f"SMTP connection test failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "message": error_msg
            }

    async def save_smtp_config(
        self,
        db: AsyncSession,
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        sender_name: str,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True
    ) -> SMTPConfig:
        """
        Save SMTP configuration.

        Args:
            db: Database session
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            sender_email: Sender email address
            sender_name: Sender display name
            smtp_username: SMTP username
            smtp_password: SMTP password
            use_tls: Whether to use TLS

        Returns:
            Saved SMTPConfig object
        """
        encrypted_password = self._encrypt_password(smtp_password) if smtp_password else None

        # Try to update existing config, or create new
        result = await db.execute(select(SMTPConfig).limit(1))
        config = result.scalar_one_or_none()

        if config:
            config.smtp_host = smtp_host
            config.smtp_port = smtp_port
            config.smtp_username = smtp_username
            config.smtp_password_encrypted = encrypted_password
            config.use_tls = use_tls
            config.sender_email = sender_email
            config.sender_name = sender_name
            config.updated_at = datetime.utcnow()
        else:
            config = SMTPConfig(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password_encrypted=encrypted_password,
                use_tls=use_tls,
                sender_email=sender_email,
                sender_name=sender_name,
                is_enabled=False,
                is_verified=False
            )
            db.add(config)

        await db.commit()
        await db.refresh(config)
        logger.info(f"SMTP config saved: {sender_email}")
        return config

    async def get_smtp_config(self, db: AsyncSession) -> Optional[SMTPConfig]:
        """Get current SMTP configuration."""
        result = await db.execute(select(SMTPConfig).limit(1))
        return result.scalar_one_or_none()

    async def mark_smtp_verified(self, db: AsyncSession, success: bool = True) -> None:
        """Mark SMTP as verified after successful test."""
        config = await self.get_smtp_config(db)
        if config:
            config.is_verified = success
            config.last_test_at = datetime.utcnow()
            config.last_test_success = success
            await db.commit()

    async def save_notification_config(
        self,
        db: AsyncSession,
        alert_on_kev: bool = True,
        alert_on_high_epss: bool = True,
        epss_threshold: float = 0.8,
        recipient_emails: List[str] = None,
        digest_enabled: bool = True,
        digest_hours: int = 24,
        is_enabled: bool = False
    ) -> EmailNotificationConfig:
        """
        Save email notification configuration.

        Args:
            db: Database session
            alert_on_kev: Alert on new KEV vulnerabilities
            alert_on_high_epss: Alert on high EPSS scores
            epss_threshold: EPSS percentile threshold (0-1)
            recipient_emails: List of recipient email addresses
            digest_enabled: Enable digest mode
            digest_hours: Hours between digest emails
            is_enabled: Enable notifications

        Returns:
            Saved EmailNotificationConfig
        """
        if recipient_emails is None:
            recipient_emails = []

        # Validate threshold
        if not (0 <= epss_threshold <= 1):
            raise ValueError(f"EPSS threshold must be between 0 and 1, got {epss_threshold}")

        # Try to update existing, or create new
        result = await db.execute(select(EmailNotificationConfig).limit(1))
        config = result.scalar_one_or_none()

        if config:
            config.alert_on_kev = alert_on_kev
            config.alert_on_high_epss = alert_on_high_epss
            config.epss_threshold = epss_threshold
            config.recipient_emails = recipient_emails
            config.digest_enabled = digest_enabled
            config.digest_hours = digest_hours
            config.is_enabled = is_enabled
            config.updated_at = datetime.utcnow()
        else:
            config = EmailNotificationConfig(
                alert_on_kev=alert_on_kev,
                alert_on_high_epss=alert_on_high_epss,
                epss_threshold=epss_threshold,
                recipient_emails=recipient_emails,
                digest_enabled=digest_enabled,
                digest_hours=digest_hours,
                is_enabled=is_enabled
            )
            db.add(config)

        await db.commit()
        await db.refresh(config)
        logger.info(f"Notification config saved: {len(recipient_emails)} recipients")
        return config

    async def get_notification_config(self, db: AsyncSession) -> Optional[EmailNotificationConfig]:
        """Get current notification configuration."""
        result = await db.execute(select(EmailNotificationConfig).limit(1))
        return result.scalar_one_or_none()

    def _render_vulnerability_alert_html(
        self,
        vulnerability: Vulnerability,
        alert_type: str
    ) -> str:
        """Render HTML email template for vulnerability alert."""
        severity_color = {
            "CRITICAL": "#d32f2f",
            "HIGH": "#f57c00",
            "MEDIUM": "#fbc02d",
            "LOW": "#388e3c"
        }.get(vulnerability.severity or "UNKNOWN", "#757575")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1565c0; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .severity {{
                    display: inline-block;
                    background-color: {severity_color};
                    color: white;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
                .kev-badge {{ background-color: #c62828; color: white; padding: 5px 10px; border-radius: 3px; }}
                .epss-badge {{ background-color: #6200ea; color: white; padding: 5px 10px; border-radius: 3px; }}
                .field {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #1565c0; }}
                .footer {{ color: #999; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>VulnDash Security Alert</h1>
                    <p>New vulnerability requiring attention</p>
                </div>

                <div class="content">
                    <div class="field">
                        <span class="label">Vulnerability ID:</span> {vulnerability.cve_id}
                    </div>

                    <div class="field">
                        <span class="label">Title:</span> {vulnerability.title or "N/A"}
                    </div>

                    <div class="field">
                        <span class="label">Severity:</span>
                        <span class="severity">{vulnerability.severity or "UNKNOWN"}</span>
                    </div>

                    <div class="field">
                        <span class="label">Alert Type:</span>
                        {self._render_alert_type_badge(alert_type)}
                    </div>

                    {self._render_score_details(vulnerability)}

                    <div class="field">
                        <span class="label">Published:</span>
                        {vulnerability.published_date.isoformat() if vulnerability.published_date else "N/A"}
                    </div>

                    {self._render_description(vulnerability.description)}
                </div>

                <div class="footer">
                    <p>This is an automated security alert from VulnDash.</p>
                    <p>Please review the vulnerability immediately and take appropriate action.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _render_alert_type_badge(self, alert_type: str) -> str:
        """Render badge for alert type."""
        if alert_type == "kev":
            return '<span class="kev-badge">KEV - CISA Known Exploited Vulnerability</span>'
        elif alert_type == "high_epss":
            return '<span class="epss-badge">HIGH EPSS - High Exploitation Probability</span>'
        return f'<span>{alert_type}</span>'

    def _render_score_details(self, vulnerability: Vulnerability) -> str:
        """Render scoring details."""
        html = ""

        if vulnerability.cvss_score is not None:
            html += f"""
            <div class="field">
                <span class="label">CVSS v3 Score:</span> {vulnerability.cvss_score}
                {f'({vulnerability.cvss_vector})' if vulnerability.cvss_vector else ''}
            </div>
            """

        if vulnerability.epss_score is not None:
            html += f"""
            <div class="field">
                <span class="label">EPSS Score:</span> {vulnerability.epss_score:.2%}
                {f'(Percentile: {vulnerability.epss_percentile:.1%})' if vulnerability.epss_percentile else ''}
            </div>
            """

        return html

    def _render_description(self, description: Optional[str]) -> str:
        """Render description section if available."""
        if not description:
            return ""
        return f"""
        <div class="field">
            <span class="label">Description:</span>
            <p>{description[:500]}{'...' if len(description) > 500 else ''}</p>
        </div>
        """

    def _render_digest_html(
        self,
        vulnerabilities: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """Render HTML for digest email."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1565c0; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .vuln-item {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #1565c0; border-radius: 3px; }}
                .vuln-id {{ font-weight: bold; color: #1565c0; }}
                .severity {{ display: inline-block; padding: 2px 5px; border-radius: 3px; color: white; font-size: 12px; }}
                .critical {{ background-color: #d32f2f; }}
                .high {{ background-color: #f57c00; }}
                .medium {{ background-color: #fbc02d; color: #333; }}
                .low {{ background-color: #388e3c; }}
                .footer {{ color: #999; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>VulnDash Security Digest</h1>
                    <p>Summary of vulnerability alerts</p>
                </div>

                <div class="summary">
                    <h3>Alert Summary</h3>
                    <p><strong>{len(vulnerabilities)}</strong> vulnerabilities detected</p>
                    <p>Period: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}</p>
                </div>

                <div class="vulnerabilities">
        """

        for vuln in vulnerabilities:
            severity_class = (vuln.get("severity") or "UNKNOWN").lower()
            html += f"""
            <div class="vuln-item">
                <div class="vuln-id">{vuln.get('cve_id', 'N/A')}</div>
                <div>{vuln.get('title', 'N/A')}</div>
                <div>
                    <span class="severity {severity_class}">{vuln.get('severity', 'UNKNOWN')}</span>
                    {self._render_alert_type_badge(vuln.get('alert_type', 'unknown'))}
                </div>
            </div>
            """

        html += """
                </div>

                <div class="footer">
                    <p>This is an automated security digest from VulnDash.</p>
                    <p>Please review each vulnerability and take appropriate action.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    async def send_alert_email(
        self,
        db: AsyncSession,
        vulnerability: Vulnerability,
        alert_type: str,
        recipient_email: str
    ) -> Dict[str, Any]:
        """
        Send immediate alert email.

        Args:
            db: Database session
            vulnerability: Vulnerability object
            alert_type: Type of alert ('kev' or 'high_epss')
            recipient_email: Email address to send to

        Returns:
            Result dictionary with status and message
        """
        smtp_config = await self.get_smtp_config(db)
        if not smtp_config or not smtp_config.is_enabled:
            return {
                "success": False,
                "message": "SMTP not configured or disabled"
            }

        try:
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[VulnDash Alert] {vulnerability.cve_id} - {alert_type.upper()}"
            msg["From"] = f"{smtp_config.sender_name} <{smtp_config.sender_email}>"
            msg["To"] = recipient_email

            # HTML content
            html_content = self._render_vulnerability_alert_html(vulnerability, alert_type)
            part = MIMEText(html_content, "html")
            msg.attach(part)

            # Send email
            password = self._decrypt_password(smtp_config.smtp_password_encrypted) if smtp_config.smtp_password_encrypted else None

            async with SMTP(
                hostname=smtp_config.smtp_host,
                port=smtp_config.smtp_port,
                use_tls=smtp_config.use_tls,
                timeout=30
            ) as smtp:
                if smtp_config.smtp_username and password:
                    await smtp.login(smtp_config.smtp_username, password)
                await smtp.send_message(msg)

            # Log successful send
            alert = EmailAlert(
                vulnerability_id=vulnerability.cve_id,
                alert_type=alert_type,
                recipient_email=recipient_email,
                sent_at=datetime.utcnow(),
                send_status="sent",
                subject=msg["Subject"],
                sent_via_digest=False
            )
            db.add(alert)
            await db.commit()

            logger.info(f"Alert email sent to {recipient_email} for {vulnerability.cve_id}")
            return {
                "success": True,
                "message": f"Alert sent to {recipient_email}"
            }

        except Exception as e:
            error_msg = f"Failed to send alert email: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Log failed send
            alert = EmailAlert(
                vulnerability_id=vulnerability.cve_id,
                alert_type=alert_type,
                recipient_email=recipient_email,
                send_status="failed",
                error_message=str(e),
                sent_via_digest=False
            )
            db.add(alert)
            await db.commit()

            return {
                "success": False,
                "message": error_msg
            }

    async def should_send_alert(
        self,
        db: AsyncSession,
        vulnerability: Vulnerability,
        alert_type: str
    ) -> bool:
        """
        Determine if alert should be sent based on configuration.

        Args:
            db: Database session
            vulnerability: Vulnerability object
            alert_type: Type of alert ('kev' or 'high_epss')

        Returns:
            True if alert should be sent
        """
        config = await self.get_notification_config(db)
        if not config or not config.is_enabled:
            return False

        if alert_type == "kev":
            return config.alert_on_kev and vulnerability.kev_status

        elif alert_type == "high_epss":
            if not config.alert_on_high_epss:
                return False
            if vulnerability.epss_percentile is None:
                return False
            return vulnerability.epss_percentile >= config.epss_threshold

        return False

    async def queue_alerts_for_vulnerability(
        self,
        db: AsyncSession,
        vulnerability: Vulnerability,
        alert_types: List[str]
    ) -> int:
        """
        Queue alert emails for a vulnerability.

        Args:
            db: Database session
            vulnerability: Vulnerability object
            alert_types: List of alert types to send

        Returns:
            Number of alerts queued
        """
        config = await self.get_notification_config(db)
        if not config or not config.is_enabled or not config.recipient_emails:
            return 0

        alerts_created = 0
        for alert_type in alert_types:
            if not await self.should_send_alert(db, vulnerability, alert_type):
                continue

            for recipient_email in config.recipient_emails:
                alert = EmailAlert(
                    vulnerability_id=vulnerability.cve_id,
                    alert_type=alert_type,
                    recipient_email=recipient_email,
                    send_status="pending"
                )
                db.add(alert)
                alerts_created += 1

        if alerts_created > 0:
            await db.commit()
            config.alert_count_since_digest += alerts_created
            config.last_alert_at = datetime.utcnow()
            await db.commit()

        return alerts_created

    async def send_pending_alerts(
        self,
        db: AsyncSession,
        max_batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Send all pending alert emails.

        Args:
            db: Database session
            max_batch_size: Maximum alerts to send in one call

        Returns:
            Statistics about sends
        """
        # Get pending alerts
        result = await db.execute(
            select(EmailAlert)
            .where(EmailAlert.send_status == "pending")
            .limit(max_batch_size)
        )
        pending_alerts = result.scalars().all()

        stats = {
            "total": len(pending_alerts),
            "sent": 0,
            "failed": 0
        }

        for alert in pending_alerts:
            # Get vulnerability details
            vuln_result = await db.execute(
                select(Vulnerability).where(Vulnerability.cve_id == alert.vulnerability_id)
            )
            vulnerability = vuln_result.scalar_one_or_none()

            if not vulnerability:
                alert.send_status = "failed"
                alert.error_message = "Vulnerability not found"
                stats["failed"] += 1
                continue

            # Send email
            result = await self.send_alert_email(
                db, vulnerability, alert.alert_type, alert.recipient_email
            )

            if result["success"]:
                stats["sent"] += 1
            else:
                stats["failed"] += 1

        await db.commit()
        return stats

    async def send_digest_email(
        self,
        db: AsyncSession,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Send digest email with all alerts from the last N hours.

        Args:
            db: Database session
            hours: Number of hours to include in digest

        Returns:
            Result dictionary with status
        """
        config = await self.get_notification_config(db)
        if not config or not config.is_enabled or not config.digest_enabled:
            return {
                "success": False,
                "message": "Digest not enabled"
            }

        smtp_config = await self.get_smtp_config(db)
        if not smtp_config or not smtp_config.is_enabled:
            return {
                "success": False,
                "message": "SMTP not configured"
            }

        # Get alerts since last digest
        time_cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await db.execute(
            select(EmailAlert)
            .where(
                and_(
                    EmailAlert.created_at >= time_cutoff,
                    EmailAlert.send_status == "sent"
                )
            )
            .order_by(desc(EmailAlert.created_at))
        )
        alerts = result.scalars().all()

        if not alerts:
            return {
                "success": True,
                "message": "No alerts to digest",
                "digest_count": 0
            }

        # Build vulnerability list for digest
        vulns_by_id = {}
        for alert in alerts:
            if alert.vulnerability_id not in vulns_by_id:
                vuln_result = await db.execute(
                    select(Vulnerability).where(Vulnerability.cve_id == alert.vulnerability_id)
                )
                vuln = vuln_result.scalar_one()
                vulns_by_id[alert.vulnerability_id] = {
                    "cve_id": vuln.cve_id,
                    "title": vuln.title,
                    "severity": vuln.severity,
                    "alert_type": alert.alert_type
                }

        try:
            # Create digest email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[VulnDash Digest] {len(vulns_by_id)} vulnerabilities - {datetime.utcnow().strftime('%Y-%m-%d')}"
            msg["From"] = f"{smtp_config.sender_name} <{smtp_config.sender_email}>"

            html_content = self._render_digest_html(
                list(vulns_by_id.values()),
                time_cutoff,
                datetime.utcnow()
            )
            part = MIMEText(html_content, "html")
            msg.attach(part)

            # Send to all recipients
            password = self._decrypt_password(smtp_config.smtp_password_encrypted) if smtp_config.smtp_password_encrypted else None
            sent_count = 0

            for recipient_email in config.recipient_emails:
                msg["To"] = recipient_email
                try:
                    async with SMTP(
                        hostname=smtp_config.smtp_host,
                        port=smtp_config.smtp_port,
                        use_tls=smtp_config.use_tls,
                        timeout=30
                    ) as smtp:
                        if smtp_config.smtp_username and password:
                            await smtp.login(smtp_config.smtp_username, password)
                        await smtp.send_message(msg)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send digest to {recipient_email}: {e}")

            if sent_count > 0:
                config.last_digest_at = datetime.utcnow()
                config.alert_count_since_digest = 0
                await db.commit()

            return {
                "success": sent_count > 0,
                "message": f"Digest sent to {sent_count}/{len(config.recipient_emails)} recipients",
                "digest_count": len(vulns_by_id),
                "sent_to": sent_count
            }

        except Exception as e:
            error_msg = f"Failed to send digest email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "message": error_msg,
                "digest_count": len(vulns_by_id)
            }
