## BUILD-013: Mark as Remediated - Allow marking vulnerabilities as remediated to track status

| Field | Value |
|-------|-------|
| Category | dashboard-ui |
| Agent | frontend |
| Timestamp | 2025-12-22T23:05:00Z |
| Complexity | easy |

### Build Verification

Verify all modified files compile and have correct syntax:

```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator

# Check Python syntax
python3 -m py_compile app/backend/routes/vulnerabilities.py
python3 -m py_compile app/backend/routes/vulnerabilities_fragments.py
python3 -m py_compile app/main.py

# Verify files exist
ls -lh app/backend/routes/vulnerabilities.py
ls -lh app/backend/routes/vulnerabilities_fragments.py
ls -lh app/frontend/templates/vulnerabilities.html
```

### Runtime Verification

Start the FastAPI application and test the remediation feature:

```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator

# Create necessary directories
mkdir -p .orchestrator/pids .orchestrator/process-logs

# Start FastAPI server in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 > .orchestrator/process-logs/fastapi-server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > .orchestrator/pids/fastapi-server.pid
echo "$(date -Iseconds) | fastapi-server | $SERVER_PID | uvicorn app.main:app" >> .orchestrator/pids/manifest.log

# Wait for server startup
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8000/health | grep "healthy" && echo "✓ Server is healthy"

# Test vulnerabilities page loads
echo "Testing vulnerabilities page..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/vulnerabilities-ui)
echo "Vulnerabilities page HTTP status: $HTTP_CODE"

# Test remediate endpoint exists (should work if vulnerabilities exist)
echo "Testing remediate endpoint..."
# Note: This requires CVE data in database
curl -s -X POST http://localhost:8000/vulnerabilities/CVE-2024-0001/remediate \
  -H "Content-Type: application/json" | grep -q "is_remediated" && echo "✓ Remediate endpoint works"

# Test stats include remediated count
echo "Testing stats endpoint..."
curl -s http://localhost:8000/vulnerabilities/stats | grep -q "remediated" && echo "✓ Stats include remediated count"

# Test table fragment returns remediate checkbox
echo "Testing table fragment..."
curl -s "http://localhost:8000/vulnerabilities/fragments/table" | grep -q "remediate-checkbox" && echo "✓ Table includes remediation checkbox"

# Cleanup
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null || true
sleep 2
rm -f .orchestrator/pids/fastapi-server.pid 2>/dev/null || true

echo "✓ Runtime verification complete"
```

### Functional Test Cases

**Test 1: Remediation Checkbox Displays**
- Navigate to http://localhost:8000/vulnerabilities-ui
- Verify table loads with vulnerabilities
- Confirm first column is "Remediated" with checkboxes
- Verify checkboxes are initially unchecked for new vulnerabilities

**Test 2: Mark Single Vulnerability as Remediated**
- Click checkbox for any vulnerability row
- Verify:
  - Row gets "remediated" class (opacity/strikethrough style applied)
  - CVE link becomes crossed out and dimmed
  - Checkbox remains checked
  - Stats update showing remediated count increased

**Test 3: Unmark Remediated Vulnerability**
- Click checkbox again on a marked vulnerability
- Verify:
  - Row "remediated" class is removed
  - CVE link returns to normal styling
  - Checkbox becomes unchecked
  - Stats update showing remediated count decreased

**Test 4: Visual Indicator for Remediated Status**
- Mark one vulnerability as remediated
- Verify visual changes:
  - Row opacity reduced (opacity: 0.6)
  - Background has subtle green tint
  - CVE link has strikethrough and gray color
  - Severity badge is dimmed

**Test 5: Hide Remediated Filter Works**
- Mark 3-5 vulnerabilities as remediated
- Check "Hide Remediated" checkbox
- Verify:
  - Table only shows unmediated vulnerabilities
  - Remediated items are hidden
  - Row count decreases
  - Total vulnerability count in stats remains same

**Test 6: Uncheck Hide Remediated Filter**
- With filter active, uncheck "Hide Remediated"
- Verify:
  - All vulnerabilities display including remediated ones
  - Remediated items show with visual indicator

**Test 7: Stats Display Remediated Count**
- Observe stats cards at top of page
- Verify "Remediated" card displays count
- Mark/unmark vulnerabilities and confirm count updates in real-time

**Test 8: Filter Persistence with Remediation**
- Apply other filters (severity, vendor, EPSS)
- Mark some vulnerabilities as remediated
- Verify remediation status persists with other filters
- Change filters and verify remediation state maintained

**Test 9: Error Handling on Failed Remediation**
- (Requires network error simulation)
- Attempt remediation when server unavailable
- Verify checkbox reverts to previous state
- No error message but action doesn't persist

**Test 10: Remediated Count in Stats Fragment**
- Stats load via HTMX fragment
- Verify remediated count displays
- Mark/unmark and trigger stats refresh
- Confirm count updates correctly

### Expected Outcomes

**Build Verification:**
- All Python files compile without syntax errors
- No import errors in FastAPI routes
- HTML template is valid and well-formed

**Runtime Verification:**
- FastAPI server starts without errors
- Health endpoint returns 200
- Vulnerabilities page loads at /vulnerabilities-ui
- POST /vulnerabilities/{cve_id}/remediate endpoint exists and works
- Stats include "remediated" field

**UI Features:**
- Remediation checkbox column displays in table
- Visual indicator applied to remediated rows
- Hide Remediated filter checkbox visible in filter panel
- Stats card shows remediated count

**Database:**
- Vulnerability.is_remediated field updates correctly
- Vulnerability.remediated_at timestamp set on mark, NULL on unmark
- Data persists across page reloads

### Acceptance Criteria Checklist

From BUILD-013 task definition:

- [x] Toggle button/checkbox per vulnerability row
- [x] Updates remediated_at timestamp on mark
- [x] Sets remediated_at to NULL on unmark
- [x] Visual indicator for remediated status
- [x] Filter option to hide/show remediated items

### Known Limitations

- No bulk operations (mark multiple as remediated at once)
- No remediation history/audit trail
- No user tracking (who marked it remediated)
- No remediation notes/comments
- Stats do not exclude remediated from "total" count

---
