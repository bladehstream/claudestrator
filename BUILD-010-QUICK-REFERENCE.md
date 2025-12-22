# BUILD-010: Review Queue - Quick Reference

## URLs

- **Frontend:** http://localhost:8000/admin/review-queue
- **API Docs:** http://localhost:8000/docs#/review-queue

## API Endpoints

### List Review Queue
```bash
GET /admin/review-queue/?page=1&page_size=20&severity=CRITICAL&sort_by=confidence_score&sort_order=asc
```

### Get Statistics
```bash
GET /admin/review-queue/stats
```

### Approve with Edits
```bash
POST /admin/review-queue/approve
Content-Type: application/json

{
  "cve_id": "CVE-2024-1234",
  "title": "Updated Title",
  "description": "Updated description",
  "vendor": "microsoft",
  "product": "windows_10",
  "severity": "CRITICAL",
  "cvss_score": 9.8,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
}
```

### Reject/Delete
```bash
POST /admin/review-queue/reject
Content-Type: application/json

{
  "cve_id": "CVE-2024-1234",
  "reason": "False positive"
}
```

### Bulk Approve
```bash
POST /admin/review-queue/bulk-approve
Content-Type: application/json

{
  "cve_ids": ["CVE-2024-1001", "CVE-2024-1002"]
}
```

### Bulk Reject
```bash
POST /admin/review-queue/bulk-reject
Content-Type: application/json

{
  "cve_ids": ["CVE-2024-1001", "CVE-2024-1002"],
  "reason": "Bulk cleanup"
}
```

## Files Modified

### Backend
- `app/backend/api/review_queue.py` (NEW)
- `app/backend/api/__init__.py`
- `app/main.py`

### Frontend
- `app/frontend/templates/admin/review_queue.html` (NEW)

### Tests
- `tests/test_review_queue_api.py` (NEW)

## Database Fields

### Vulnerability Table
- `needs_review` (boolean) - True if in review queue
- `confidence_score` (float) - 0.0 to 1.0
- `extraction_metadata` (JSON) - Tracks manual review

### On Approval
- `needs_review` = false
- `confidence_score` = 1.0
- `extraction_metadata.manually_reviewed` = true
- `extraction_metadata.reviewed_at` = ISO timestamp

## Query Parameters

### Pagination
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20, max: 100) - Items per page

### Filtering
- `severity` (string) - CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN, NONE

### Sorting
- `sort_by` (string, default: confidence_score) - confidence_score, created_at, severity
- `sort_order` (string, default: asc) - asc, desc

## Testing

```bash
# Run unit tests
pytest tests/test_review_queue_api.py -v

# Run with coverage
pytest tests/test_review_queue_api.py --cov=app/backend/api/review_queue --cov-report=term-missing

# Start server for manual testing
uvicorn app.main:app --port 8000
```

## Common Workflows

### Review Single Item
1. Navigate to /admin/review-queue
2. Click "Review" button on item
3. Edit fields as needed in modal
4. Click "Approve & Save" or "Reject"

### Bulk Approve Items
1. Select items with checkboxes
2. Click "Bulk Approve" button
3. Confirm action
4. All selected items approved without edits

### Filter Critical Items
1. Select "Critical" from severity dropdown
2. Table auto-updates to show only critical items

### Sort by Lowest Confidence
1. Select "Sort by Confidence" from dropdown
2. Select "Ascending" from order dropdown
3. Lowest confidence items shown first

## Troubleshooting

### No items in queue
- Check that processing pipeline is running
- Verify LLM confidence threshold is set to 0.8
- Check that vulnerabilities have confidence < 0.8

### Approval fails
- Verify CVE ID exists and is in review queue
- Check that all required fields are provided
- Ensure CVSS score is between 0.0 and 10.0
- Verify severity is valid (CRITICAL, HIGH, MEDIUM, LOW, NONE, UNKNOWN)

### Stats not updating
- Refresh page
- Check database connection
- Verify vulnerabilities table has data

## Acceptance Criteria

- [x] Admin page at /admin/review-queue
- [x] Display entries with needs_review=true
- [x] Show confidence score and extracted fields
- [x] Approve action (promotes to curated table with edits)
- [x] Reject/Delete action (removes without promotion)
- [x] Edit fields before approval
- [x] Threshold: confidence < 0.8 triggers needs_review

## Dependencies

- BUILD-007: LLM Integration (provides needs_review, confidence_score)
- BUILD-008: Two-Table Processing (creates review queue entries)
