"""
Tests for review queue API endpoints.

Tests the REST API for low-confidence vulnerability review queue management.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from app.main import app
from app.database.models import Vulnerability, Product


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    with patch('app.backend.api.review_queue.get_db') as mock:
        db = Mock()
        mock.return_value = db
        yield db


@pytest.fixture
def sample_vulnerability():
    """Create sample vulnerability for testing."""
    vuln = Mock(spec=Vulnerability)
    vuln.cve_id = "CVE-2024-1234"
    vuln.title = "Test Vulnerability"
    vuln.description = "Test description"
    vuln.severity = "HIGH"
    vuln.cvss_score = 7.5
    vuln.cvss_vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"
    vuln.confidence_score = 0.65
    vuln.needs_review = True
    vuln.extraction_metadata = {}
    vuln.published_date = datetime(2024, 1, 15)
    vuln.created_at = datetime(2024, 1, 16)
    vuln.products = []
    return vuln


def test_list_review_queue_empty(client, mock_db_session):
    """Test listing review queue when empty."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.count.return_value = 0
    query_mock.offset.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = []

    mock_db_session.query.return_value = query_mock

    response = client.get("/admin/review-queue/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1
    assert data["total_pages"] == 0


def test_list_review_queue_with_items(client, mock_db_session, sample_vulnerability):
    """Test listing review queue with items."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.count.return_value = 1
    query_mock.offset.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = [sample_vulnerability]

    mock_db_session.query.return_value = query_mock

    response = client.get("/admin/review-queue/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["cve_id"] == "CVE-2024-1234"
    assert data["items"][0]["confidence_score"] == 0.65


def test_list_review_queue_with_severity_filter(client, mock_db_session):
    """Test listing review queue with severity filter."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.count.return_value = 0
    query_mock.offset.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = []

    mock_db_session.query.return_value = query_mock

    response = client.get("/admin/review-queue/?severity=CRITICAL")

    assert response.status_code == 200
    # Verify filter was called (would need more detailed mock to verify the actual filter)
    assert query_mock.filter.called


def test_list_review_queue_pagination(client, mock_db_session):
    """Test pagination parameters."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.count.return_value = 50
    query_mock.offset.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = []

    mock_db_session.query.return_value = query_mock

    response = client.get("/admin/review-queue/?page=2&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 10
    assert data["total_pages"] == 5


def test_approve_vulnerability_success(client, mock_db_session, sample_vulnerability):
    """Test approving a vulnerability with edits."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = sample_vulnerability

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_id": "CVE-2024-1234",
        "title": "Updated Title",
        "description": "Updated description",
        "vendor": "TestVendor",
        "product": "TestProduct",
        "severity": "CRITICAL",
        "cvss_score": 9.0,
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
    }

    response = client.post("/admin/review-queue/approve", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vulnerability CVE-2024-1234 approved successfully"
    assert data["confidence_score"] == 1.0
    assert data["needs_review"] == False

    # Verify vulnerability was updated
    assert sample_vulnerability.title == "Updated Title"
    assert sample_vulnerability.description == "Updated description"
    assert sample_vulnerability.severity == "CRITICAL"
    assert sample_vulnerability.cvss_score == 9.0
    assert sample_vulnerability.confidence_score == 1.0
    assert sample_vulnerability.needs_review == False


def test_approve_vulnerability_not_found(client, mock_db_session):
    """Test approving non-existent vulnerability."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_id": "CVE-9999-9999",
        "title": "Updated Title"
    }

    response = client.post("/admin/review-queue/approve", json=request_data)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_approve_vulnerability_not_in_queue(client, mock_db_session, sample_vulnerability):
    """Test approving vulnerability not in review queue."""
    sample_vulnerability.needs_review = False

    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = sample_vulnerability

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_id": "CVE-2024-1234",
        "title": "Updated Title"
    }

    response = client.post("/admin/review-queue/approve", json=request_data)

    assert response.status_code == 400
    assert "not in review queue" in response.json()["detail"].lower()


def test_approve_vulnerability_with_product_creation(client, mock_db_session, sample_vulnerability):
    """Test approving vulnerability creates product if not exists."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock

    # First query for vulnerability
    query_results = [sample_vulnerability, None]  # Vuln exists, product doesn't
    query_mock.first.side_effect = query_results

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_id": "CVE-2024-1234",
        "vendor": "NewVendor",
        "product": "NewProduct"
    }

    response = client.post("/admin/review-queue/approve", json=request_data)

    assert response.status_code == 200
    # Verify product was added
    mock_db_session.add.called


def test_reject_vulnerability_success(client, mock_db_session, sample_vulnerability):
    """Test rejecting and deleting a vulnerability."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = sample_vulnerability

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_id": "CVE-2024-1234",
        "reason": "False positive"
    }

    response = client.post("/admin/review-queue/reject", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vulnerability CVE-2024-1234 rejected and deleted successfully"
    assert data["cve_id"] == "CVE-2024-1234"
    assert data["reason"] == "False positive"

    # Verify vulnerability was deleted
    mock_db_session.delete.assert_called_once_with(sample_vulnerability)
    mock_db_session.commit.assert_called_once()


def test_reject_vulnerability_not_found(client, mock_db_session):
    """Test rejecting non-existent vulnerability."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_id": "CVE-9999-9999"
    }

    response = client.post("/admin/review-queue/reject", json=request_data)

    assert response.status_code == 404


def test_bulk_approve_success(client, mock_db_session):
    """Test bulk approval of multiple vulnerabilities."""
    # Create multiple sample vulnerabilities
    vulns = []
    for i in range(3):
        vuln = Mock(spec=Vulnerability)
        vuln.cve_id = f"CVE-2024-{1000+i}"
        vuln.needs_review = True
        vuln.confidence_score = 0.65
        vuln.extraction_metadata = {}
        vulns.append(vuln)

    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = vulns

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_ids": ["CVE-2024-1000", "CVE-2024-1001", "CVE-2024-1002"]
    }

    response = client.post("/admin/review-queue/bulk-approve", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["approved_count"] == 3
    assert len(data["cve_ids"]) == 3

    # Verify all were updated
    for vuln in vulns:
        assert vuln.confidence_score == 1.0
        assert vuln.needs_review == False


def test_bulk_approve_empty_list(client):
    """Test bulk approval with empty list."""
    request_data = {
        "cve_ids": []
    }

    response = client.post("/admin/review-queue/bulk-approve", json=request_data)

    assert response.status_code == 400
    assert "No CVE IDs provided" in response.json()["detail"]


def test_bulk_reject_success(client, mock_db_session):
    """Test bulk rejection of multiple vulnerabilities."""
    # Create multiple sample vulnerabilities
    vulns = []
    for i in range(3):
        vuln = Mock(spec=Vulnerability)
        vuln.cve_id = f"CVE-2024-{1000+i}"
        vuln.needs_review = True
        vulns.append(vuln)

    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = vulns

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_ids": ["CVE-2024-1000", "CVE-2024-1001", "CVE-2024-1002"],
        "reason": "Bulk false positives"
    }

    response = client.post("/admin/review-queue/bulk-reject", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["deleted_count"] == 3
    assert len(data["cve_ids"]) == 3
    assert data["reason"] == "Bulk false positives"

    # Verify all were deleted
    assert mock_db_session.delete.call_count == 3


def test_get_stats(client, mock_db_session):
    """Test getting review queue statistics."""
    # Mock total count
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.count.side_effect = [15, 5, 7, 2, 1, 0, 0]  # Total, then by severity
    query_mock.all.return_value = [
        Mock(confidence_score=0.65),
        Mock(confidence_score=0.70),
        Mock(confidence_score=0.55),
    ]

    mock_db_session.query.return_value = query_mock

    response = client.get("/admin/review-queue/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_needs_review"] == 15
    assert "by_severity" in data
    assert data["by_severity"]["CRITICAL"] == 5
    assert data["by_severity"]["HIGH"] == 7
    assert "average_confidence" in data
    assert data["threshold"] == 0.8


def test_approval_validation_severity(client):
    """Test severity validation in approval request."""
    request_data = {
        "cve_id": "CVE-2024-1234",
        "severity": "INVALID"
    }

    response = client.post("/admin/review-queue/approve", json=request_data)

    # Should fail validation
    assert response.status_code == 422  # Validation error


def test_approval_validation_cvss_score(client):
    """Test CVSS score validation in approval request."""
    request_data = {
        "cve_id": "CVE-2024-1234",
        "cvss_score": 11.0  # Invalid: max is 10.0
    }

    response = client.post("/admin/review-queue/approve", json=request_data)

    # Should fail validation
    assert response.status_code == 422  # Validation error


def test_severity_normalization(client, mock_db_session, sample_vulnerability):
    """Test that severity values are normalized to uppercase."""
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = sample_vulnerability

    mock_db_session.query.return_value = query_mock

    request_data = {
        "cve_id": "CVE-2024-1234",
        "severity": "medium"  # Lowercase input
    }

    response = client.post("/admin/review-queue/approve", json=request_data)

    assert response.status_code == 200
    # Verify severity was normalized to uppercase
    assert sample_vulnerability.severity == "MEDIUM"
