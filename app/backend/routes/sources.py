"""
API routes for data source management.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, HttpUrl, validator

from app.database import get_db
from app.database.models import DataSource, SourceType, HealthStatus
from app.backend.services.poller import trigger_manual_poll

router = APIRouter(prefix="/admin/sources", tags=["sources"])


# Pydantic models for request/response
class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(...)
    url: Optional[str] = Field(None, max_length=2048)
    description: Optional[str] = None
    polling_interval_hours: int = Field(24, ge=1, le=72)
    is_enabled: bool = True
    auth_config: Optional[dict] = None

    @validator('source_type')
    def validate_source_type(cls, v):
        valid_types = [t.value for t in SourceType]
        if v not in valid_types:
            raise ValueError(f'source_type must be one of: {", ".join(valid_types)}')
        return v

    @validator('polling_interval_hours')
    def validate_polling_interval(cls, v):
        if not 1 <= v <= 72:
            raise ValueError('polling_interval_hours must be between 1 and 72')
        return v


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, max_length=2048)
    description: Optional[str] = None
    polling_interval_hours: Optional[int] = Field(None, ge=1, le=72)
    is_enabled: Optional[bool] = None
    auth_config: Optional[dict] = None


class SourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    url: Optional[str]
    description: Optional[str]
    polling_interval_hours: int
    is_enabled: bool
    is_running: bool
    health_status: str
    last_poll_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_error: Optional[str]
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class HealthResponse(BaseModel):
    source_id: int
    source_name: str
    health_status: str
    is_running: bool
    last_poll_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_error: Optional[str]
    consecutive_failures: int

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


@router.get("/", response_model=List[SourceResponse])
def list_sources(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all data sources."""
    query = db.query(DataSource)

    if enabled_only:
        query = query.filter(DataSource.is_enabled == True)

    sources = query.offset(skip).limit(limit).all()

    return [
        SourceResponse(
            id=s.id,
            name=s.name,
            source_type=s.source_type.value,
            url=s.url,
            description=s.description,
            polling_interval_hours=s.polling_interval_hours,
            is_enabled=s.is_enabled,
            is_running=s.is_running,
            health_status=s.health_status.value,
            last_poll_at=s.last_poll_at,
            last_success_at=s.last_success_at,
            last_error=s.last_error,
            consecutive_failures=s.consecutive_failures,
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        for s in sources
    ]


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    """Get a specific data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source with id {source_id} not found"
        )

    return SourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type.value,
        url=source.url,
        description=source.description,
        polling_interval_hours=source.polling_interval_hours,
        is_enabled=source.is_enabled,
        is_running=source.is_running,
        health_status=source.health_status.value,
        last_poll_at=source.last_poll_at,
        last_success_at=source.last_success_at,
        last_error=source.last_error,
        consecutive_failures=source.consecutive_failures,
        created_at=source.created_at,
        updated_at=source.updated_at
    )


@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(source_data: SourceCreate, db: Session = Depends(get_db)):
    """Create a new data source."""
    # Check for duplicate name
    existing = db.query(DataSource).filter(DataSource.name == source_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source with name '{source_data.name}' already exists"
        )

    # TODO: Encrypt auth_config if provided
    auth_encrypted = None
    if source_data.auth_config:
        # In production, use Fernet encryption
        import json
        auth_encrypted = json.dumps(source_data.auth_config)

    # Create source
    new_source = DataSource(
        name=source_data.name,
        source_type=SourceType(source_data.source_type),
        url=source_data.url,
        description=source_data.description,
        polling_interval_hours=source_data.polling_interval_hours,
        is_enabled=source_data.is_enabled,
        auth_config_encrypted=auth_encrypted,
        health_status=HealthStatus.HEALTHY
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return SourceResponse(
        id=new_source.id,
        name=new_source.name,
        source_type=new_source.source_type.value,
        url=new_source.url,
        description=new_source.description,
        polling_interval_hours=new_source.polling_interval_hours,
        is_enabled=new_source.is_enabled,
        is_running=new_source.is_running,
        health_status=new_source.health_status.value,
        last_poll_at=new_source.last_poll_at,
        last_success_at=new_source.last_success_at,
        last_error=new_source.last_error,
        consecutive_failures=new_source.consecutive_failures,
        created_at=new_source.created_at,
        updated_at=new_source.updated_at
    )


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: int,
    source_data: SourceUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source with id {source_id} not found"
        )

    # Update fields
    update_data = source_data.dict(exclude_unset=True)

    # Handle auth_config encryption
    if 'auth_config' in update_data:
        import json
        update_data['auth_config_encrypted'] = json.dumps(update_data.pop('auth_config'))

    for field, value in update_data.items():
        if hasattr(source, field):
            setattr(source, field, value)

    source.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(source)

    return SourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type.value,
        url=source.url,
        description=source.description,
        polling_interval_hours=source.polling_interval_hours,
        is_enabled=source.is_enabled,
        is_running=source.is_running,
        health_status=source.health_status.value,
        last_poll_at=source.last_poll_at,
        last_success_at=source.last_success_at,
        last_error=source.last_error,
        consecutive_failures=source.consecutive_failures,
        created_at=source.created_at,
        updated_at=source.updated_at
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Delete a data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source with id {source_id} not found"
        )

    if source.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a source while it is running. Please wait for the current poll to complete."
        )

    db.delete(source)
    db.commit()


@router.post("/{source_id}/poll", response_model=dict)
def manual_poll(source_id: int, db: Session = Depends(get_db)):
    """Manually trigger a poll for a specific data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source with id {source_id} not found"
        )

    if not source.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot poll a disabled source. Enable it first."
        )

    if source.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source is already being polled. Please wait for the current poll to complete."
        )

    # Trigger the poll
    try:
        success = trigger_manual_poll(source_id, db)
        if success:
            return {"status": "success", "message": f"Poll triggered for source '{source.name}'"}
        else:
            return {"status": "failed", "message": "Poll job could not be queued"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger poll: {str(e)}"
        )


@router.get("/health/status", response_model=List[HealthResponse])
def get_health_status(db: Session = Depends(get_db)):
    """Get health status for all data sources."""
    sources = db.query(DataSource).all()

    return [
        HealthResponse(
            source_id=s.id,
            source_name=s.name,
            health_status=s.health_status.value,
            is_running=s.is_running,
            last_poll_at=s.last_poll_at,
            last_success_at=s.last_success_at,
            last_error=s.last_error,
            consecutive_failures=s.consecutive_failures
        )
        for s in sources
    ]
