# Verification Steps - BUILD-008

| Field | Value |
|-------|-------|
| Task ID | BUILD-008 |
| Category | data-ingestion |
| Agent | backend |
| Timestamp | 2025-12-22T22:40:00Z |

## Build Verification

Verify code compiles without errors:

```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run Python syntax check
python -m py_compile app/backend/services/processing_service.py
python -m py_compile app/backend/services/scheduler.py
python -m py_compile app/backend/api/processing.py

# Check for import errors
python -c "from app.backend.services.processing_service import ProcessingService; print('✓ ProcessingService imports OK')"
python -c "from app.backend.services.scheduler import ProcessingScheduler; print('✓ Scheduler imports OK')"
python -c "from app.backend.api.processing import router; print('✓ Processing API imports OK')"
```

## Unit Tests

Run comprehensive test suite:

```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator

# Run all processing tests with verbose output
pytest tests/test_processing_service.py -v
pytest tests/test_scheduler.py -v
pytest tests/test_processing_api.py -v

# Run with coverage
pytest tests/test_processing_service.py tests/test_scheduler.py tests/test_processing_api.py --cov=app.backend.services.processing_service --cov=app.backend.services.scheduler --cov=app.backend.api.processing --cov-report=term-missing
```

## Runtime Verification

### 1. Start the Server

```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator

# Start in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/vulndash_build008.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > /tmp/vulndash_build008.pid

# Wait for startup
sleep 3

# Check if running
if ps -p $SERVER_PID > /dev/null; then
    echo "✓ Server started (PID: $SERVER_PID)"
else
    echo "✗ Server failed to start"
    cat /tmp/vulndash_build008.log
    exit 1
fi
```

### 2. Test Processing Status Endpoint

```bash
# Get current processing status
curl -s http://localhost:8000/admin/processing/status | jq '.'

# Expected: JSON with raw_entries and vulnerabilities counts
```

### 3. Test Scheduler Status Endpoint

```bash
# Get scheduler status
curl -s http://localhost:8000/admin/processing/scheduler | jq '.'

# Expected: JSON with is_running: true (auto-started)
```

### 4. Test Manual Processing Trigger

Note: This requires LLM config to be set up. If Ollama is not running, trigger will complete but with no entries processed.

```bash
# Trigger manual processing
curl -s -X POST http://localhost:8000/admin/processing/trigger | jq '.'

# Expected: JSON with stats (processed, created, etc.)
```

### 5. Test Scheduler Control

```bash
# Stop scheduler
curl -s -X POST http://localhost:8000/admin/processing/scheduler/stop | jq '.'

# Check status
curl -s http://localhost:8000/admin/processing/scheduler | jq '.is_running'
# Expected: false

# Start scheduler
curl -s -X POST http://localhost:8000/admin/processing/scheduler/start | jq '.'

# Check status
curl -s http://localhost:8000/admin/processing/scheduler | jq '.is_running'
# Expected: true
```

### 6. Test Purge Endpoint

```bash
# Purge old entries (default 7 days)
curl -s -X POST http://localhost:8000/admin/processing/purge | jq '.'

# Expected: JSON with purged_count

# Purge with custom days
curl -s -X POST http://localhost:8000/admin/processing/purge \
  -H "Content-Type: application/json" \
  -d '{"days": 14}' | jq '.'

# Expected: JSON with purged_count
```

### 7. Test API Documentation

```bash
# Check OpenAPI docs include processing endpoints
curl -s http://localhost:8000/openapi.json | jq '.paths | keys | map(select(contains("/processing")))'

# Expected: Array with processing endpoints
```

### 8. Cleanup

```bash
# Stop server
if [ -f /tmp/vulndash_build008.pid ]; then
    SERVER_PID=$(cat /tmp/vulndash_build008.pid)
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        kill $SERVER_PID
        sleep 2
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            kill -9 $SERVER_PID
        fi
        echo "✓ Server stopped"
    fi
    rm /tmp/vulndash_build008.pid
fi

# Cleanup logs
rm -f /tmp/vulndash_build008.log
```

## Expected Outcomes

### Build Verification
- ✅ All Python files compile without syntax errors
- ✅ All imports succeed without errors
- ✅ No missing dependencies

### Unit Tests
- ✅ All test_processing_service.py tests pass
- ✅ All test_scheduler.py tests pass
- ✅ All test_processing_api.py tests pass
- ✅ Test coverage > 80%

### Runtime Verification
- ✅ Server starts successfully and remains running
- ✅ Processing status endpoint returns correct structure
- ✅ Scheduler starts automatically on app startup
- ✅ Manual trigger endpoint works (returns stats)
- ✅ Scheduler can be stopped and restarted via API
- ✅ Purge endpoint works with default and custom days
- ✅ All endpoints documented in OpenAPI schema

## Integration Test (Optional - Requires Full Setup)

If you have Ollama running and LLM configured:

```bash
# 1. Insert test raw entry
sqlite3 vulndash.db <<EOF
INSERT INTO raw_entries (source_id, raw_payload, processing_status, ingested_at)
VALUES (1, 'CVE-2024-9999: Critical auth bypass in Test Product', 'pending', datetime('now'));
EOF

# 2. Trigger processing
curl -s -X POST http://localhost:8000/admin/processing/trigger | jq '.'

# 3. Check vulnerability was created
curl -s http://localhost:8000/api/vulnerabilities?search=CVE-2024-9999 | jq '.'

# 4. Check raw entry was marked completed
sqlite3 vulndash.db "SELECT processing_status FROM raw_entries WHERE raw_payload LIKE '%CVE-2024-9999%';"
# Expected: completed
```

## Success Criteria

✅ All acceptance criteria met:

1. ✅ raw_entries table exists and used for ingested feed data
2. ✅ curated vulnerabilities table populated by processing
3. ✅ Background job processes entries on schedule (configurable 1-60 min)
4. ✅ Manual trigger option available via API
5. ✅ Deduplication logic implemented (by CVE ID with confidence scoring)
6. ✅ Raw entries purged after 7 days when processed
7. ✅ Status tracking implemented (pending, processing, processed, failed)

---

**Notes:**
- Scheduler auto-starts on application startup
- Processing interval configurable via LLM config table
- Deduplication prioritizes higher confidence scores
- Failed entries retry up to 3 times before permanent failure
- Manual trigger runs independently of scheduler
