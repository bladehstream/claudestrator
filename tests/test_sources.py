"""
Tests for data source management.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.database.models import Base, DataSource, SourceType, HealthStatus

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "vulndash"}


def test_create_source(setup_database):
    """Test creating a new data source."""
    source_data = {
        "name": "Test NVD Source",
        "source_type": "nvd",
        "url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
        "description": "Test NVD source",
        "polling_interval_hours": 24,
        "is_enabled": True
    }

    response = client.post("/admin/sources/", json=source_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test NVD Source"
    assert data["source_type"] == "nvd"
    assert data["polling_interval_hours"] == 24
    assert data["health_status"] == "healthy"


def test_create_duplicate_source(setup_database):
    """Test creating a duplicate source fails."""
    source_data = {
        "name": "Duplicate Source",
        "source_type": "rss",
        "url": "https://example.com/feed.xml",
        "polling_interval_hours": 12,
        "is_enabled": True
    }

    # Create first source
    response1 = client.post("/admin/sources/", json=source_data)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = client.post("/admin/sources/", json=source_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_list_sources(setup_database):
    """Test listing all sources."""
    # Create two sources
    source1 = {
        "name": "Source 1",
        "source_type": "nvd",
        "polling_interval_hours": 24,
        "is_enabled": True
    }
    source2 = {
        "name": "Source 2",
        "source_type": "cisa_kev",
        "polling_interval_hours": 12,
        "is_enabled": False
    }

    client.post("/admin/sources/", json=source1)
    client.post("/admin/sources/", json=source2)

    # List all sources
    response = client.get("/admin/sources/")
    assert response.status_code == 200
    # Note: This endpoint returns HTML fragment, not JSON
    # In production, you'd have separate JSON and HTML endpoints


def test_get_source(setup_database):
    """Test getting a specific source."""
    source_data = {
        "name": "Get Test Source",
        "source_type": "api",
        "url": "https://api.example.com/vulns",
        "polling_interval_hours": 6,
        "is_enabled": True
    }

    # Create source
    create_response = client.post("/admin/sources/", json=source_data)
    source_id = create_response.json()["id"]

    # Get source
    response = client.get(f"/admin/sources/{source_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Test Source"
    assert data["source_type"] == "api"


def test_get_nonexistent_source(setup_database):
    """Test getting a source that doesn't exist."""
    response = client.get("/admin/sources/9999")
    assert response.status_code == 404


def test_update_source(setup_database):
    """Test updating a source."""
    # Create source
    source_data = {
        "name": "Update Test Source",
        "source_type": "rss",
        "polling_interval_hours": 24,
        "is_enabled": True
    }
    create_response = client.post("/admin/sources/", json=source_data)
    source_id = create_response.json()["id"]

    # Update source
    update_data = {
        "polling_interval_hours": 12,
        "is_enabled": False
    }
    response = client.patch(f"/admin/sources/{source_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["polling_interval_hours"] == 12
    assert data["is_enabled"] is False


def test_delete_source(setup_database):
    """Test deleting a source."""
    # Create source
    source_data = {
        "name": "Delete Test Source",
        "source_type": "url_scraper",
        "polling_interval_hours": 24,
        "is_enabled": True
    }
    create_response = client.post("/admin/sources/", json=source_data)
    source_id = create_response.json()["id"]

    # Delete source
    response = client.delete(f"/admin/sources/{source_id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = client.get(f"/admin/sources/{source_id}")
    assert get_response.status_code == 404


def test_manual_poll(setup_database):
    """Test manually triggering a poll."""
    # Create source
    source_data = {
        "name": "Poll Test Source",
        "source_type": "nvd",
        "polling_interval_hours": 24,
        "is_enabled": True
    }
    create_response = client.post("/admin/sources/", json=source_data)
    source_id = create_response.json()["id"]

    # Trigger poll
    response = client.post(f"/admin/sources/{source_id}/poll")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_manual_poll_disabled_source(setup_database):
    """Test that polling a disabled source fails."""
    # Create disabled source
    source_data = {
        "name": "Disabled Poll Test",
        "source_type": "rss",
        "polling_interval_hours": 24,
        "is_enabled": False
    }
    create_response = client.post("/admin/sources/", json=source_data)
    source_id = create_response.json()["id"]

    # Try to poll
    response = client.post(f"/admin/sources/{source_id}/poll")
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()


def test_health_status(setup_database):
    """Test getting health status for all sources."""
    # Create sources
    source1 = {
        "name": "Health Source 1",
        "source_type": "nvd",
        "polling_interval_hours": 24,
        "is_enabled": True
    }
    source2 = {
        "name": "Health Source 2",
        "source_type": "cisa_kev",
        "polling_interval_hours": 12,
        "is_enabled": True
    }

    client.post("/admin/sources/", json=source1)
    client.post("/admin/sources/", json=source2)

    # Get health status
    response = client.get("/admin/sources/health/status")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("health_status" in item for item in data)


def test_polling_interval_validation(setup_database):
    """Test that polling interval is validated."""
    # Test too low
    source_data = {
        "name": "Invalid Interval Low",
        "source_type": "rss",
        "polling_interval_hours": 0,
        "is_enabled": True
    }
    response = client.post("/admin/sources/", json=source_data)
    assert response.status_code == 422

    # Test too high
    source_data["polling_interval_hours"] = 73
    response = client.post("/admin/sources/", json=source_data)
    assert response.status_code == 422


def test_invalid_source_type(setup_database):
    """Test that invalid source type is rejected."""
    source_data = {
        "name": "Invalid Type Source",
        "source_type": "invalid_type",
        "polling_interval_hours": 24,
        "is_enabled": True
    }
    response = client.post("/admin/sources/", json=source_data)
    assert response.status_code == 422
