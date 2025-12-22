"""
HTMX fragment routes for data sources.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.database.models import DataSource

router = APIRouter(prefix="/admin/sources", tags=["sources-fragments"])

templates_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "templates")
templates = Jinja2Templates(directory=templates_path)


@router.get("/", response_class=HTMLResponse)
def sources_fragment(request: Request, db: Session = Depends(get_db)):
    """Return HTMX fragment with all sources."""
    sources = db.query(DataSource).all()

    if not sources:
        return """
        <div class="empty-state">
            <div class="empty-state-icon">📡</div>
            <p class="empty-state-text">No data sources configured yet</p>
            <button class="btn btn-primary" onclick="showAddSourceModal()">
                + Add Your First Source
            </button>
        </div>
        """

    html_parts = ['<div class="sources-grid">']

    for source in sources:
        # Determine status class and health text
        status_class = f"status-{source.health_status.value}"
        health_text = source.health_status.value.upper()
        warning_icon = ""

        if source.is_running:
            status_class = "status-running"
            health_text = "POLLING"
        elif not source.is_enabled:
            status_class = "status-disabled"
            health_text = "DISABLED"
        elif source.health_status.value == "warning":
            warning_icon = "⚠️ "
            health_text = f"WARNING ({source.consecutive_failures} failures)"
        elif source.health_status.value == "failed":
            warning_icon = "❌ "
            health_text = f"FAILED ({source.consecutive_failures}/20 failures)"

        # Format dates
        last_poll = source.last_poll_at.strftime("%Y-%m-%d %H:%M") if source.last_poll_at else "Never"
        last_success = source.last_success_at.strftime("%Y-%m-%d %H:%M") if source.last_success_at else "Never"

        # Build error section
        error_section = ""
        if source.last_error:
            error_section = f'''
            <div class="error-message">
                <strong>Last Error:</strong> {source.last_error[:200]}
            </div>
            '''

        # Disable toggle button label
        toggle_label = "Disable" if source.is_enabled else "Enable"

        # Determine card CSS class
        card_classes = []
        if not source.is_enabled:
            card_classes.append('disabled')
        elif source.health_status.value == 'failed':
            card_classes.append('failed')
        elif source.health_status.value == 'warning':
            card_classes.append('warning')

        card_class_str = ' '.join(card_classes)

        html_parts.append(f'''
        <div class="source-card {card_class_str}">
            <div class="source-header">
                <div class="source-title">
                    <div class="source-name">{source.name}</div>
                    <span class="source-type">{source.source_type.value}</span>
                </div>
                <div class="source-status">
                    <span class="{status_class} status-indicator" title="{health_text}"></span>
                    <span class="status-text">{warning_icon}{health_text}</span>
                </div>
            </div>

            {f'<p class="source-description">{source.description}</p>' if source.description else ''}

            <div class="source-details">
                <div class="detail-row">
                    <span class="detail-label">Polling Interval:</span>
                    <span class="detail-value">{source.polling_interval_hours} hours</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Last Poll:</span>
                    <span class="detail-value">{last_poll}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Last Success:</span>
                    <span class="detail-value">{last_success}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Consecutive Failures:</span>
                    <span class="detail-value">{source.consecutive_failures}</span>
                </div>
                {f'<div class="detail-row"><span class="detail-label">URL:</span><span class="detail-value" style="font-size: 11px; word-break: break-all;">{source.url}</span></div>' if source.url else ''}
            </div>

            {error_section}

            <div class="source-actions">
                <button class="btn btn-primary btn-sm"
                        onclick="manualPoll({source.id}, '{source.name}')"
                        {'disabled' if source.is_running or not source.is_enabled else ''}>
                    {'⏳ Polling...' if source.is_running else '▶️ Poll Now'}
                </button>
                <button class="btn btn-secondary btn-sm" onclick="toggleSource({source.id})">
                    {toggle_label}
                </button>
                <button class="btn btn-danger btn-sm"
                        onclick="deleteSource({source.id}, '{source.name}')"
                        {'disabled' if source.is_running else ''}>
                    🗑️ Delete
                </button>
            </div>
        </div>
        ''')

    html_parts.append('</div>')

    return ''.join(html_parts)
