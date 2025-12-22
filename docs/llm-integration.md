# LLM Integration (Ollama)

This document describes the LLM integration for extracting structured vulnerability data from raw text feeds.

## Overview

VulnDash uses Ollama for local LLM inference to extract structured vulnerability information from unstructured text sources (RSS feeds, security blogs, vendor advisories).

## Architecture

### Components

1. **OllamaClient** (`app/backend/services/ollama_client.py`)
   - Low-level client for Ollama API
   - Handles connection testing, model discovery, and text generation
   - Supports both text and JSON output modes

2. **LLMService** (`app/backend/services/llm_service.py`)
   - High-level extraction service
   - Implements vulnerability data extraction logic
   - Provides confidence scoring and validation
   - Handles fallback for LLM failures

3. **Admin API** (`app/backend/api/llm.py`)
   - RESTful endpoints for LLM configuration
   - Model selection and testing
   - Live extraction testing

## Features

### 1. Ollama Connection Management

Configure and test connection to Ollama server:

```bash
# Test connection
GET /admin/llm/test

# Response:
{
  "status": "success",
  "message": "Successfully connected to Ollama at http://localhost:11434",
  "details": {
    "status": "connected",
    "models_count": 3,
    "server": "http://localhost:11434"
  }
}
```

### 2. Model Discovery

Automatically discover available models:

```bash
# List models
GET /admin/llm/models

# Response:
{
  "models": [
    {
      "name": "llama3",
      "model": "llama3:latest",
      "size": 3800000000,
      "modified_at": "2024-01-15T10:30:00Z",
      "digest": "abc123def456"
    },
    {
      "name": "mistral",
      "model": "mistral:latest",
      "size": 4100000000,
      "modified_at": "2024-01-14T08:15:00Z",
      "digest": "xyz789uvw012"
    }
  ],
  "count": 2
}
```

### 3. Structured Data Extraction

Extract structured vulnerability data from raw text:

**Input:** Raw vulnerability text from RSS/API
**Output:** Structured JSON with:
- `cve_id`: CVE identifier (validated format)
- `title`: Short vulnerability title
- `description`: Detailed description
- `vendor`: Affected vendor/organization
- `product`: Affected product name
- `severity`: CRITICAL, HIGH, MEDIUM, LOW, NONE, or UNKNOWN
- `cvss_score`: CVSS score (0.0-10.0)
- `cvss_vector`: CVSS vector string
- `confidence_score`: Extraction confidence (0.0-1.0)
- `needs_review`: Boolean flag for low-confidence extractions

### 4. Confidence Scoring

Confidence score is calculated based on:

| Factor | Weight | Details |
|--------|--------|---------|
| CVE ID presence | 30% | Required field, highest weight |
| Vendor/Product | 20% | 10% each for identification |
| Severity | 15% | Must be valid severity level |
| CVSS Score | 10% | Optional but valuable |
| Description quality | 15% | Length and content quality |
| Title presence | 10% | Optional metadata |
| Validation issues | -5% each | Penalties for errors |

**Confidence Threshold:** 0.8 (configurable)
- Above threshold: Auto-approved for curated table
- Below threshold: Sent to review queue

### 5. Format Validation

Heuristic validation before trusting LLM output:

1. **CVE ID Format**
   - Regex: `CVE-\d{4}-\d{4,}`
   - Fallback: Extract from raw text if LLM fails

2. **Severity Normalization**
   - Valid: CRITICAL, HIGH, MEDIUM, LOW, NONE, UNKNOWN
   - Invalid values → UNKNOWN

3. **CVSS Score Range**
   - Valid: 0.0 - 10.0
   - Out of range → None

4. **Description Fallback**
   - If LLM description < 10 chars → Use raw text

### 6. Test Extraction Endpoint

Test extraction with sample text before processing real entries:

```bash
POST /admin/llm/test-extract
{
  "raw_text": "CVE-2024-1234: Critical authentication bypass in Acme CMS allows remote attackers to gain administrative access.",
  "model": "llama3"  # Optional: override default model
}

# Response:
{
  "success": true,
  "extraction": {
    "cve_id": "CVE-2024-1234",
    "title": "Critical Authentication Bypass",
    "description": "Critical authentication bypass in Acme CMS allows remote attackers to gain administrative access.",
    "vendor": "Acme",
    "product": "Acme CMS",
    "severity": "CRITICAL",
    "cvss_score": null,
    "cvss_vector": null,
    "confidence_score": 0.75,
    "needs_review": true,
    "extraction_metadata": {
      "model": "llama3",
      "temperature": 0.1,
      "extraction_time": "2024-01-15T12:30:00Z",
      "llm_duration_ms": 1500,
      "validation_issues": ["No CVSS score"]
    }
  },
  "error": null
}
```

## Configuration

### Environment Variables

```bash
# Ollama server URL
OLLAMA_BASE_URL=http://localhost:11434

# Default model
OLLAMA_MODEL=llama3

# Processing parameters
LLM_TEMPERATURE=0.1
LLM_CONFIDENCE_THRESHOLD=0.8
LLM_PROCESSING_INTERVAL_MINUTES=30
LLM_BATCH_SIZE=10
```

### Database Configuration

Configuration stored in `llm_config` table:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| ollama_base_url | string | http://localhost:11434 | Ollama server URL |
| selected_model | string | null | Model for extraction |
| temperature | float | 0.1 | Sampling temperature |
| max_tokens | int | 1000 | Max tokens per request |
| confidence_threshold | float | 0.8 | Review threshold |
| processing_interval_minutes | int | 30 | Batch processing interval |
| batch_size | int | 10 | Entries per batch |

## API Endpoints

### Configuration

- `GET /admin/llm/config` - Get current configuration
- `POST /admin/llm/config` - Update configuration

### Connection & Models

- `GET /admin/llm/test` - Test Ollama connection
- `GET /admin/llm/models` - List available models

### Testing

- `POST /admin/llm/test-extract` - Test extraction on sample text

## Error Handling

### Connection Errors

- `OllamaConnectionError`: Raised when Ollama server is unreachable
- Automatic fallback to low-confidence extraction
- Status tracked in `connection_status` field

### Model Errors

- `OllamaModelError`: Raised when generation fails
- Creates fallback result with CVE extraction from raw text
- Logs error for debugging

### Validation Failures

- Invalid data normalized (e.g., severity → UNKNOWN)
- Confidence score reduced based on issues
- Flagged for manual review

## Recommended Models

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| llama3 | 3.8 GB | Fast | Good | General purpose, recommended |
| mistral | 4.1 GB | Medium | Very Good | Higher accuracy needed |
| phi3 | 2.3 GB | Very Fast | Fair | High volume, speed priority |

## Best Practices

1. **Model Selection**
   - Start with llama3 for balanced performance
   - Use mistral for higher accuracy on complex text
   - Use phi3 for high-volume, simple extractions

2. **Temperature**
   - Keep low (0.1-0.2) for deterministic extraction
   - Higher values (0.5+) increase creativity but reduce consistency

3. **Confidence Threshold**
   - 0.8 (default) balances automation and quality
   - Lower (0.6) for more automation, more false positives
   - Higher (0.9) for higher quality, more manual review

4. **Batch Size**
   - 10 (default) balances throughput and resource usage
   - Increase for powerful hardware
   - Decrease if Ollama timeouts occur

## Troubleshooting

### Connection Failed

```
Error: Cannot connect to Ollama server at http://localhost:11434
```

**Solutions:**
1. Verify Ollama is running: `ollama list`
2. Check URL in configuration
3. Test with: `curl http://localhost:11434/api/tags`

### Model Not Available

```
Error: Model 'llama3' not available
```

**Solutions:**
1. List models: `GET /admin/llm/models`
2. Pull model: `ollama pull llama3`
3. Select different model in configuration

### Low Confidence Scores

**Causes:**
- Incomplete raw text
- Non-standard vulnerability format
- Missing CVE ID

**Solutions:**
1. Review extraction in test endpoint
2. Adjust temperature (lower = more deterministic)
3. Try different model
4. Add to review queue for manual processing

## Implementation Details

### System Prompt

```
You are a cybersecurity data extraction assistant. Your task is to extract structured vulnerability information from raw text.

Extract the following fields:
- cve_id: CVE identifier (format: CVE-YYYY-NNNNN)
- title: Short vulnerability title
- description: Detailed description
- vendor: Affected vendor/organization
- product: Affected product name
- severity: One of CRITICAL, HIGH, MEDIUM, LOW, NONE, or UNKNOWN
- cvss_score: CVSS score if available (0.0-10.0)
- cvss_vector: CVSS vector string if available

Return ONLY a JSON object with these fields. Use null for missing values.
Be conservative - only extract information you are confident about.
```

### Processing Flow

```
Raw Entry (RSS/API)
     ↓
OllamaClient.generate_json()
     ↓
LLMService.extract_vulnerability()
     ↓
Validation & Normalization
     ↓
Confidence Calculation
     ↓
[High Confidence] → Curated Table
[Low Confidence] → Review Queue
```

## Testing

Run LLM integration tests:

```bash
# Unit tests (mocked Ollama)
pytest tests/test_ollama_client.py tests/test_llm_service.py -v

# Integration tests (requires Ollama running)
pytest tests/test_llm_integration.py -v --integration
```

## Future Enhancements

- Multi-LLM support (Claude, Gemini, OpenAI)
- Streaming responses for large batches
- Fine-tuned models for vulnerability extraction
- Active learning from review queue corrections
- Automatic prompt optimization
