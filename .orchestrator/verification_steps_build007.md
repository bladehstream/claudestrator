## BUILD-007: LLM Integration (Ollama)

| Field | Value |
|-------|-------|
| Category | llm-processing |
| Agent | backend |
| Timestamp | 2025-12-22T22:20:00Z |
| Complexity | normal |

### Build Verification

Verify all LLM integration code compiles without errors:

```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator

# Check Python syntax for all LLM-related files
python3 -m py_compile app/backend/models/database.py
python3 -m py_compile app/backend/services/ollama_client.py
python3 -m py_compile app/backend/services/llm_service.py
python3 -m py_compile app/backend/api/llm.py
python3 -m py_compile app/main.py

# Verify imports work
python3 -c "from app.backend.services.ollama_client import OllamaClient; print('OllamaClient OK')"
python3 -c "from app.backend.services.llm_service import LLMService; print('LLMService OK')"
python3 -c "from app.backend.models.database import LLMConfig; print('Models OK')"
```

### Unit Tests

Run unit tests with mocked Ollama server:

```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator

# Install dependencies if needed
pip install -q pytest pytest-asyncio httpx

# Run LLM integration tests
pytest tests/test_ollama_client.py -v --tb=short
pytest tests/test_llm_service.py -v --tb=short
```

### Runtime Verification

Test that API endpoints work:

```bash
cd /home/devbuntu/claudecode/vdash2/claudestrator

# Install dependencies
pip install -r requirements.txt

# Start application
export DATABASE_URL="sqlite+aiosqlite:///./test_vulndash.db"
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/vulndash.log 2>&1 &
SERVER_PID=$!
sleep 3

# Test health
curl -s http://localhost:8000/health

# Test LLM config endpoint
curl -s -X GET http://localhost:8000/admin/llm/config | jq .

# Update config
curl -s -X POST http://localhost:8000/admin/llm/config \
  -H "Content-Type: application/json" \
  -d '{"ollama_base_url": "http://localhost:11434", "selected_model": "llama3", "temperature": 0.1}' | jq .

# Test connection (may fail if Ollama not running)
curl -s -X GET http://localhost:8000/admin/llm/test | jq .

# Cleanup
kill $SERVER_PID 2>/dev/null
rm -f test_vulndash.db*
```

### Expected Outcomes

**Build Verification:**
- All Python files compile without syntax errors
- All imports resolve successfully
- No missing dependencies

**Unit Tests:**
- All OllamaClient tests pass
- All LLMService tests pass
- Test coverage > 80%

**Runtime:**
- Application starts successfully
- Health endpoint returns {"status": "healthy"}
- LLM config endpoints work
- Default configuration created
- Connection test handles errors gracefully

### Acceptance Criteria Checklist

From BUILD-007 task definition:

- [x] Configure Ollama server endpoint
- [x] Test connection functionality
- [x] Discover available models
- [x] Select model for processing
- [x] Extract structured data:
  - [x] CVE ID (with format validation)
  - [x] Vendor
  - [x] Product
  - [x] Severity
  - [x] Description
- [x] Confidence scoring for extractions
  - [x] Multi-factor calculation
  - [x] Configurable threshold
  - [x] Review queue flagging

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /admin/llm/config | GET | Get configuration |
| /admin/llm/config | POST | Update configuration |
| /admin/llm/test | GET | Test connection |
| /admin/llm/models | GET | List models |
| /admin/llm/test-extract | POST | Test extraction |

### Files Created

- app/backend/models/database.py (updated with LLM models)
- app/backend/services/ollama_client.py
- app/backend/services/llm_service.py
- app/backend/api/llm.py
- tests/test_ollama_client.py
- tests/test_llm_service.py
- docs/llm-integration.md
- requirements.txt (updated)
- .env.example

---
