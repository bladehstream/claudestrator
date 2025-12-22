# Verification Steps for BUILD-011

## BUILD-011: Source Health Monitoring

| Field | Value |
|-------|-------|
| Category | admin-maintenance |
| Agent | fullstack |
| Timestamp | 2025-12-22T22:04:37Z |

### Build Verification

```bash
# 1. Verify Python syntax
python3 -m py_compile app/backend/routes/sources_fragments.py
python3 -m py_compile app/frontend/templates/admin_sources.html

# 2. Run health monitoring test
python3 test_health_monitoring.py
```

### Runtime Verification

```bash
# 1. Start the application (background)
cd /home/devbuntu/claudecode/vdash2/claudestrator
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/vulndash.log 2>&1 &
VULNDASH_PID=$!
echo $VULNDASH_PID > /tmp/vulndash.pid

# 2. Wait for startup
sleep 5

# 3. Verify application is running
curl -f http://localhost:8000/health || exit 1

# 4. Test health monitoring features
# Create a test source
curl -X POST http://localhost:8000/admin/sources/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Health Source",
    "source_type": "api",
    "url": "https://api.example.com/test",
    "description": "Test source for health monitoring",
    "polling_interval_hours": 24,
    "is_enabled": true
  }' | jq -r '.id' > /tmp/test_source_id.txt

TEST_SOURCE_ID=$(cat /tmp/test_source_id.txt)

# 5. Verify source health status endpoint
curl -f http://localhost:8000/admin/sources/health/status | jq '.'

# 6. Get specific source and verify health fields
curl -f http://localhost:8000/admin/sources/$TEST_SOURCE_ID | jq '{
  name: .name,
  health_status: .health_status,
  consecutive_failures: .consecutive_failures,
  last_poll_at: .last_poll_at,
  last_success_at: .last_success_at
}'

# 7. Verify admin UI renders correctly
curl -f http://localhost:8000/admin/sources-ui | grep -q "Data Source Management"

# 8. Verify HTMX fragment includes health indicators
curl -f http://localhost:8000/admin/sources/ | grep -E "(status-indicator|status-text)"

# 9. Cleanup test source
curl -X DELETE http://localhost:8000/admin/sources/$TEST_SOURCE_ID

# 10. Stop application
kill $VULNDASH_PID 2>/dev/null || true
rm /tmp/vulndash.pid /tmp/test_source_id.txt
```

### Expected Outcomes

#### Build Phase
- Python syntax validation passes with exit code 0
- Health monitoring test script executes successfully
- All test assertions pass

#### Runtime Phase
- Application starts and responds to health checks
- Health status endpoint returns data for all sources
- Each source includes health monitoring fields:
  - `health_status`: "healthy", "warning", "failed", or "disabled"
  - `consecutive_failures`: Integer from 0 to 20+
  - `last_poll_at`: ISO timestamp or null
  - `last_success_at`: ISO timestamp or null
  - `last_error`: String or null
- Admin UI displays source cards with:
  - Color-coded status indicator (green/yellow/red)
  - Status text with health state
  - Warning icons (⚠️ or ❌) for failures
  - Consecutive failure count displayed
  - Border highlight for failed/warning sources
- HTMX fragment includes:
  - CSS classes: `status-healthy`, `status-warning`, `status-failed`
  - Visual elements: `status-indicator`, `status-text`
  - Card classes: `failed`, `warning` for highlighting

### Feature-Specific Verification

#### Health Status Display
- ✓ Each source card shows health status indicator
- ✓ Status indicator has appropriate color (green/yellow/red)
- ✓ Status text displays current health state

#### Visual Indicators
- ✓ Green indicator for healthy sources (consecutive_failures < 5)
- ✓ Yellow indicator for warning sources (consecutive_failures 5-19)
- ✓ Red indicator for failed sources (consecutive_failures >= 20)
- ✓ Border highlighting for warning/failed source cards

#### Warning Icons
- ✓ ⚠️ icon displayed for WARNING status
- ✓ ❌ icon displayed for FAILED status
- ✓ No icon for HEALTHY status

#### Failure Counter
- ✓ Consecutive failures counter displayed in detail row
- ✓ Counter shown in status text for WARNING/FAILED states
- ✓ Counter tracks up to 20+ failures

#### Persistent Failure State
- ✓ Sources marked as FAILED after 20 consecutive failures
- ✓ Failed sources remain in FAILED state until successful poll

#### Reset on Success
- ✓ Consecutive failures reset to 0 on successful poll
- ✓ Health status changes to HEALTHY after reset
- ✓ last_success_at timestamp updated

---
