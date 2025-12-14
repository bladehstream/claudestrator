---
name: LLM Integration
id: llm_integration
version: 1.0
category: implementation
domain: [llm, ai, ollama, api_integration, python]
task_types: [implementation, integration]
keywords: [ollama, llm, ai, claude, gemini, openai, prompts, extraction, inference, structured_output, json_mode]
complexity: [normal]
pairs_with: [api_development, beautifulsoup_scraper]
external_dependencies:
  - type: service
    name: Ollama
    description: Local LLM server (network-accessible)
    setup_url: https://ollama.ai/
    required: true
  - type: python_package
    name: requests
    description: HTTP client library
    setup_url: https://docs.python-requests.org/
    required: true
  - type: env_var
    name: OLLAMA_BASE_URL
    description: Base URL for Ollama API (e.g., http://192.168.1.100:11434)
    required: true
  - type: env_var
    name: ANTHROPIC_API_KEY
    description: Claude API key (optional, for cloud LLM)
    required: false
  - type: env_var
    name: GOOGLE_API_KEY
    description: Google Gemini API key (optional, for cloud LLM)
    required: false
  - type: env_var
    name: OPENAI_API_KEY
    description: OpenAI API key (optional, for cloud LLM)
    required: false
---

# LLM Integration

## Role

Expert in integrating local and cloud-based LLM services for data extraction, structured output generation, and AI-powered analysis. Specializes in Ollama (network-accessible local models) with support for cloud APIs (Claude, Gemini, OpenAI). Use this skill when you need to extract structured data from unstructured text, perform NLP tasks, or leverage LLMs for vulnerability analysis and enrichment.

## Pre-Flight Check (MANDATORY)

**You MUST run this check before using this skill. Do NOT skip.**

```bash
# Check for required Python packages
python3 -c "import requests; print('✓ requests is installed')" 2>/dev/null || {
    echo "✗ requests is NOT installed - CANNOT PROCEED"
    echo ""
    echo "Install using pip:"
    echo "  pip install requests"
    echo ""
    echo "STOP: Report this task as BLOCKED with the above instructions."
    exit 1
}

# Check Ollama connectivity (primary requirement)
if [ -z "$OLLAMA_BASE_URL" ]; then
    echo "✗ OLLAMA_BASE_URL environment variable not set"
    echo ""
    echo "Set the Ollama server URL:"
    echo "  export OLLAMA_BASE_URL=http://192.168.1.100:11434"
    echo ""
    echo "STOP: Report this task as BLOCKED."
    exit 1
fi

# Test Ollama connection
curl -sf "$OLLAMA_BASE_URL/api/tags" > /dev/null 2>&1 && {
    echo "✓ Ollama server reachable at $OLLAMA_BASE_URL"
    echo ""
    echo "Available models:"
    curl -s "$OLLAMA_BASE_URL/api/tags" | python3 -c "import sys, json; [print(f\"  - {m['name']}\") for m in json.load(sys.stdin).get('models', [])]"
} || {
    echo "✗ Cannot connect to Ollama at $OLLAMA_BASE_URL"
    echo ""
    echo "Ensure Ollama is running and accessible:"
    echo "  1. Check the server is running"
    echo "  2. Verify network connectivity"
    echo "  3. Confirm the URL is correct"
    echo ""
    echo "STOP: Report this task as BLOCKED."
    exit 1
}

# Optional: Check for cloud API keys
[ -n "$ANTHROPIC_API_KEY" ] && echo "✓ Claude API key configured (optional)"
[ -n "$GOOGLE_API_KEY" ] && echo "✓ Gemini API key configured (optional)"
[ -n "$OPENAI_API_KEY" ] && echo "✓ OpenAI API key configured (optional)"
```

**If the check fails:**
1. Do NOT attempt to proceed with the task
2. Do NOT try workarounds or alternative approaches
3. Report the task as **BLOCKED** in your handoff
4. Include the setup instructions in your blocker notes
5. The orchestrator will surface this to the user

## Core Competencies

- Ollama API integration (list models, generate, chat endpoints)
- Cloud LLM API integration (Claude, Gemini, OpenAI)
- Prompt engineering for structured data extraction
- JSON mode and structured output parsing
- Response validation and error handling
- Retry logic with exponential backoff
- Connection pooling and session management
- Rate limiting and token counting
- Multi-provider abstraction layer
- Vulnerability data extraction from unstructured text
- CVE, CVSS, and EPSS score extraction
- Remediation and impact assessment generation

## Patterns and Standards

### Basic Ollama Connection

```python
import os
import requests
from typing import Optional, Dict, Any

class OllamaClient:
    """
    Client for Ollama API with error handling and validation.
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL (defaults to OLLAMA_BASE_URL env var)
        """
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

    def test_connection(self) -> bool:
        """Test if Ollama server is reachable."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_models(self) -> list[str]:
        """
        Get list of available models.

        Returns:
            List of model names
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()

            data = response.json()
            return [model['name'] for model in data.get('models', [])]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching models: {e}")
            return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

# Usage
with OllamaClient() as client:
    if client.test_connection():
        models = client.list_models()
        print(f"Available models: {models}")
    else:
        print("Cannot connect to Ollama")
```

**When to use**: Basic connectivity check and model discovery.

### Text Generation with Ollama

```python
import json
from typing import Optional, Iterator

class OllamaClient:
    # ... (previous methods)

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        format: Optional[str] = None,
    ) -> str | Iterator[str]:
        """
        Generate text using Ollama.

        Args:
            model: Model name (e.g., 'llama2', 'mistral')
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Enable streaming response
            format: Response format ('json' for JSON mode)

        Returns:
            Generated text or iterator of text chunks if streaming
        """
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': stream,
        }

        if system:
            payload['system'] = system

        # Options
        options = {'temperature': temperature}
        if max_tokens:
            options['num_predict'] = max_tokens
        payload['options'] = options

        # JSON mode
        if format == 'json':
            payload['format'] = 'json'

        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300,  # 5 min timeout for generation
                stream=stream
            )
            response.raise_for_status()

            if stream:
                return self._stream_response(response)
            else:
                data = response.json()
                return data.get('response', '')

        except requests.exceptions.RequestException as e:
            print(f"Error generating text: {e}")
            raise

    def _stream_response(self, response) -> Iterator[str]:
        """Stream response chunks."""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if not chunk.get('done', False):
                    yield chunk.get('response', '')

# Usage
with OllamaClient() as client:
    # Simple generation
    response = client.generate(
        model='llama2',
        prompt='Explain SQL injection in one sentence.'
    )
    print(response)

    # Streaming
    for chunk in client.generate(
        model='llama2',
        prompt='Explain XSS attacks.',
        stream=True
    ):
        print(chunk, end='', flush=True)
```

**When to use**: General text generation tasks, simple prompts without conversation history.

### Chat Completions with Ollama

```python
from typing import List, Dict

class OllamaClient:
    # ... (previous methods)

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        format: Optional[str] = None,
    ) -> str:
        """
        Chat completion with message history.

        Args:
            model: Model name
            messages: List of message dicts with 'role' and 'content'
                     roles: 'system', 'user', 'assistant'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            format: Response format ('json' for JSON mode)

        Returns:
            Assistant's response text
        """
        payload = {
            'model': model,
            'messages': messages,
            'stream': False,
        }

        options = {'temperature': temperature}
        if max_tokens:
            options['num_predict'] = max_tokens
        payload['options'] = options

        if format == 'json':
            payload['format'] = 'json'

        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300
            )
            response.raise_for_status()

            data = response.json()
            return data['message']['content']

        except requests.exceptions.RequestException as e:
            print(f"Error in chat: {e}")
            raise

# Usage
with OllamaClient() as client:
    messages = [
        {
            'role': 'system',
            'content': 'You are a cybersecurity expert specializing in vulnerability analysis.'
        },
        {
            'role': 'user',
            'content': 'What is CVE-2021-44228 (Log4Shell)?'
        }
    ]

    response = client.chat(model='llama2', messages=messages)
    print(response)

    # Continue conversation
    messages.append({'role': 'assistant', 'content': response})
    messages.append({'role': 'user', 'content': 'How do I mitigate it?'})

    response = client.chat(model='llama2', messages=messages)
    print(response)
```

**When to use**: Multi-turn conversations, when you need context from previous messages.

### Structured Data Extraction with JSON Mode

```python
import json
from pydantic import BaseModel, Field
from typing import Optional, List

class VulnerabilityExtraction(BaseModel):
    """Structured vulnerability data."""
    cve_ids: List[str] = Field(description="CVE identifiers found")
    cvss_score: Optional[float] = Field(description="CVSS score (0-10)")
    epss_score: Optional[float] = Field(description="EPSS score (0-1)")
    severity: Optional[str] = Field(description="Severity level")
    vendor: Optional[str] = Field(description="Affected vendor")
    product: Optional[str] = Field(description="Affected product")
    description: str = Field(description="Vulnerability description")
    impact: str = Field(description="Impact assessment")
    remediation: str = Field(description="Remediation guidance")

class VulnerabilityExtractor:
    """Extract structured vulnerability data from unstructured text."""

    def __init__(self, client: OllamaClient, model: str = 'llama2'):
        self.client = client
        self.model = model

    def extract(self, text: str) -> Optional[VulnerabilityExtraction]:
        """
        Extract vulnerability data from text.

        Args:
            text: Unstructured text containing vulnerability information

        Returns:
            Structured vulnerability data or None if extraction fails
        """
        # Create schema description for the model
        schema_desc = {
            "cve_ids": "array of CVE identifiers (e.g., ['CVE-2021-44228'])",
            "cvss_score": "CVSS score as a number between 0 and 10, or null",
            "epss_score": "EPSS score as a number between 0 and 1, or null",
            "severity": "severity level: CRITICAL, HIGH, MEDIUM, LOW, or null",
            "vendor": "affected vendor/organization name or null",
            "product": "affected product/software name or null",
            "description": "brief description of the vulnerability",
            "impact": "assessment of the security impact",
            "remediation": "recommended remediation steps"
        }

        system_prompt = f"""You are a vulnerability data extraction expert.
Extract structured information from the provided text.

Return a JSON object with this exact structure:
{json.dumps(schema_desc, indent=2)}

Rules:
- Extract all CVE IDs in format CVE-YYYY-NNNNN
- CVSS scores must be between 0 and 10
- EPSS scores must be between 0 and 1
- Severity must be one of: CRITICAL, HIGH, MEDIUM, LOW
- Use null for missing fields
- Be concise but accurate
- Only extract information actually present in the text
"""

        user_prompt = f"""Extract vulnerability data from this text:

{text}

Return ONLY valid JSON, no additional text."""

        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=0.0,  # Low temperature for factual extraction
                format='json'  # Enable JSON mode
            )

            # Parse JSON response
            data = json.loads(response)

            # Validate with Pydantic
            return VulnerabilityExtraction(**data)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing response: {e}")
            return None
        except Exception as e:
            print(f"Extraction error: {e}")
            return None

# Usage
with OllamaClient() as client:
    extractor = VulnerabilityExtractor(client, model='llama2')

    sample_text = """
    CVE-2021-44228 is a critical remote code execution vulnerability in Apache Log4j 2.
    CVSS Score: 10.0 (Critical)
    Affected: Apache Log4j 2.0-beta9 through 2.15.0 (excluding 2.12.2, 2.12.3, and 2.3.1)

    Impact: Allows remote attackers to execute arbitrary code on affected systems by
    controlling log messages or log message parameters.

    Mitigation: Upgrade to Log4j 2.17.0 or later. As a temporary workaround, set
    log4j2.formatMsgNoLookups to true or remove JndiLookup class from classpath.
    """

    result = extractor.extract(sample_text)
    if result:
        print(f"CVEs: {result.cve_ids}")
        print(f"CVSS: {result.cvss_score}")
        print(f"Severity: {result.severity}")
        print(f"Product: {result.product}")
        print(f"Remediation: {result.remediation}")
```

**When to use**: Extracting structured data from scraped content, parsing vulnerability advisories, enriching CVE data.

### Robust Error Handling and Retry Logic

```python
import time
from functools import wraps
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (requests.exceptions.RequestException,)
):
    """
    Decorator for exponential backoff retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = base_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_retries:
                        raise

                    # Exponential backoff
                    wait_time = min(delay * (2 ** attempt), max_delay)
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)

            raise RuntimeError("Should not reach here")

        return wrapper
    return decorator

class RobustOllamaClient(OllamaClient):
    """Ollama client with retry logic."""

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def generate(self, *args, **kwargs):
        """Generate with automatic retry on failure."""
        return super().generate(*args, **kwargs)

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def chat(self, *args, **kwargs):
        """Chat with automatic retry on failure."""
        return super().chat(*args, **kwargs)

# Usage
with RobustOllamaClient() as client:
    # Automatically retries on network errors
    response = client.generate(
        model='llama2',
        prompt='Explain CSRF attacks.'
    )
```

**When to use**: Production environments where reliability is critical, handling intermittent network issues.

### Multi-Provider Abstraction Layer

```python
from abc import ABC, abstractmethod
from enum import Enum

class LLMProvider(Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion with message history."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if service is accessible."""
        pass

class ClaudeClient(BaseLLMClient):
    """Claude API client."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        })

    def generate(self, prompt: str, model: str = 'claude-3-haiku-20240307', **kwargs) -> str:
        """Generate using Claude API."""
        messages = [{'role': 'user', 'content': prompt}]
        return self.chat(messages, model=model, **kwargs)

    def chat(self, messages: List[Dict[str, str]], model: str = 'claude-3-haiku-20240307', **kwargs) -> str:
        """Chat using Claude Messages API."""
        payload = {
            'model': model,
            'messages': messages,
            'max_tokens': kwargs.get('max_tokens', 1024),
        }

        if 'temperature' in kwargs:
            payload['temperature'] = kwargs['temperature']

        # Extract system message
        system_msg = next((m['content'] for m in messages if m['role'] == 'system'), None)
        if system_msg:
            payload['system'] = system_msg
            messages = [m for m in messages if m['role'] != 'system']
            payload['messages'] = messages

        response = self.session.post(
            'https://api.anthropic.com/v1/messages',
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        return data['content'][0]['text']

    def test_connection(self) -> bool:
        """Test Claude API connectivity."""
        try:
            self.generate("test", max_tokens=1)
            return True
        except:
            return False

class LLMClientFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create(provider: LLMProvider) -> BaseLLMClient:
        """
        Create LLM client for specified provider.

        Args:
            provider: LLM provider enum

        Returns:
            LLM client instance

        Raises:
            ValueError: If provider not supported or credentials missing
        """
        if provider == LLMProvider.OLLAMA:
            return RobustOllamaClient()
        elif provider == LLMProvider.CLAUDE:
            return ClaudeClient()
        elif provider == LLMProvider.GEMINI:
            # Placeholder for Gemini client
            raise NotImplementedError("Gemini client not implemented")
        elif provider == LLMProvider.OPENAI:
            # Placeholder for OpenAI client
            raise NotImplementedError("OpenAI client not implemented")
        else:
            raise ValueError(f"Unknown provider: {provider}")

# Usage - provider-agnostic code
def analyze_vulnerability(text: str, provider: LLMProvider = LLMProvider.OLLAMA):
    """Analyze vulnerability using any LLM provider."""
    client = LLMClientFactory.create(provider)

    if not client.test_connection():
        raise ConnectionError(f"Cannot connect to {provider.value}")

    messages = [
        {
            'role': 'system',
            'content': 'You are a cybersecurity expert. Analyze the vulnerability and provide assessment.'
        },
        {
            'role': 'user',
            'content': f'Analyze this vulnerability:\n\n{text}'
        }
    ]

    return client.chat(messages, temperature=0.0)

# Switch providers easily
result_ollama = analyze_vulnerability(vuln_text, LLMProvider.OLLAMA)
result_claude = analyze_vulnerability(vuln_text, LLMProvider.CLAUDE)
```

**When to use**: Applications supporting multiple LLM providers, enabling provider switching via configuration.

### Prompt Engineering for Vulnerability Analysis

```python
class VulnerabilityAnalyzer:
    """Comprehensive vulnerability analysis using LLMs."""

    SYSTEM_PROMPT = """You are an expert vulnerability analyst with deep knowledge of:
- CVE database and vulnerability classification
- CVSS scoring methodology
- Common vulnerabilities (OWASP Top 10, CWE)
- Attack vectors and exploitation techniques
- Security remediation best practices

Your task is to analyze vulnerability information and provide accurate, actionable insights."""

    def __init__(self, client: BaseLLMClient):
        self.client = client

    def identify_cves(self, text: str) -> List[str]:
        """Extract CVE IDs from text."""
        prompt = f"""Extract all CVE identifiers from the following text.
Return ONLY a JSON array of CVE IDs in format ["CVE-YYYY-NNNNN", ...].
If no CVEs found, return empty array [].

Text:
{text}

JSON array:"""

        response = self.client.generate(prompt, temperature=0.0)
        try:
            return json.loads(response)
        except:
            return []

    def assess_severity(self, vulnerability_description: str) -> Dict[str, Any]:
        """Assess vulnerability severity and impact."""
        prompt = f"""Analyze this vulnerability and assess its severity.

Vulnerability:
{vulnerability_description}

Provide assessment in JSON format:
{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "cvss_estimate": <number 0-10>,
  "attack_vector": "NETWORK|ADJACENT|LOCAL|PHYSICAL",
  "attack_complexity": "LOW|HIGH",
  "privileges_required": "NONE|LOW|HIGH",
  "user_interaction": "NONE|REQUIRED",
  "impact_summary": "<brief impact description>",
  "exploitability": "EASY|MODERATE|DIFFICULT"
}}

Return ONLY valid JSON:"""

        response = self.client.generate(prompt, temperature=0.0)
        try:
            return json.loads(response)
        except:
            return {}

    def generate_remediation(self, cve_id: str, context: str = "") -> str:
        """Generate remediation guidance for a CVE."""
        prompt = f"""Provide remediation guidance for {cve_id}.

Context:
{context if context else "No additional context provided."}

Include:
1. Immediate mitigation steps
2. Long-term remediation
3. Verification steps
4. References to patches/updates

Guidance:"""

        return self.client.generate(prompt, temperature=0.3)

    def enrich_cve_data(self, cve_id: str, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich CVE data with LLM-generated insights."""
        description = base_data.get('description', '')

        # Generate additional analysis
        enrichment_prompt = f"""Analyze {cve_id}:

Description: {description}

Provide additional insights in JSON:
{{
  "affected_systems": ["<system types>"],
  "attack_scenarios": ["<realistic attack scenario>"],
  "business_impact": "<impact on business operations>",
  "detection_methods": ["<how to detect exploitation>"],
  "related_cves": ["<similar CVEs>"]
}}

JSON:"""

        try:
            response = self.client.generate(enrichment_prompt, temperature=0.2)
            enrichment = json.loads(response)

            # Merge with base data
            return {**base_data, **enrichment}
        except:
            return base_data

# Usage
with OllamaClient() as client:
    analyzer = VulnerabilityAnalyzer(client)

    # Extract CVEs from scraped text
    cves = analyzer.identify_cves(scraped_advisory)

    # Assess severity
    severity = analyzer.assess_severity(vulnerability_text)
    print(f"Severity: {severity['severity']}")
    print(f"CVSS Estimate: {severity['cvss_estimate']}")

    # Generate remediation
    remediation = analyzer.generate_remediation('CVE-2021-44228')
    print(remediation)

    # Enrich CVE data
    enriched = analyzer.enrich_cve_data('CVE-2021-44228', base_cve_data)
```

**When to use**: Building vulnerability dashboards, enriching CVE data, automating security assessments.

## Quality Standards

- **Always validate LLM outputs** - LLMs can hallucinate; verify critical data
- **Use low temperature (0.0-0.2)** for factual extraction tasks
- **Implement retry logic** for production systems
- **Test connection before operations** - fail fast with clear error messages
- **Use JSON mode** when available for structured output
- **Validate against schemas** - use Pydantic or similar for type safety
- **Handle timeouts gracefully** - LLM generation can take time
- **Log prompts and responses** - essential for debugging and improvement
- **Sanitize user inputs** - prevent prompt injection attacks
- **Monitor token usage** - implement rate limiting for cloud APIs

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| No connection testing | Fails silently or with unclear errors | Test connection in pre-flight check |
| Trusting LLM output blindly | LLMs hallucinate and make errors | Validate all extracted data |
| High temperature for facts | Increases hallucination risk | Use temp=0.0 for factual tasks |
| No retry logic | Single network failure breaks system | Implement exponential backoff |
| Parsing free-form text | Fragile and error-prone | Use JSON mode for structured output |
| Hardcoded provider | Cannot switch or test alternatives | Use abstraction layer |
| Missing error handling | Crashes on malformed JSON | Try/except with fallback behavior |
| No timeout configuration | Can hang indefinitely | Always set reasonable timeouts |

## Decision Framework

When integrating LLMs:

1. **Provider selection:**
   - Local/sensitive data → Ollama (network-accessible)
   - High quality needed → Claude or GPT-4
   - Cost-sensitive → Ollama or cheaper cloud models
   - High throughput → Consider rate limits and costs

2. **Task type:**
   - Factual extraction → Low temperature (0.0-0.2)
   - Creative generation → Higher temperature (0.5-0.9)
   - Structured output → Enable JSON mode
   - Conversational → Use chat API with history

3. **Reliability requirements:**
   - Production system → Implement retries, fallbacks, monitoring
   - Development/testing → Basic error handling acceptable
   - Critical path → Consider multiple providers as fallback

## Output Expectations

When this skill is applied, the agent should:

- [ ] Test Ollama connectivity and list available models
- [ ] Implement appropriate error handling and retries
- [ ] Use JSON mode for structured data extraction
- [ ] Validate LLM outputs against expected schema
- [ ] Configure appropriate temperature for task type
- [ ] Handle timeouts and network failures gracefully
- [ ] Log prompts and responses for debugging
- [ ] Document prompt templates and expected outputs
- [ ] Include example usage and test cases
- [ ] Consider security (prompt injection, data sanitization)

## Example Task

**Objective**: Extract structured vulnerability data from scraped NVD advisory pages.

**Approach**:
1. Set up OllamaClient with connection testing
2. Design prompt template for CVE data extraction
3. Define Pydantic model for structured output validation
4. Implement VulnerabilityExtractor with JSON mode
5. Add retry logic for network resilience
6. Test with sample advisory text
7. Validate extracted CVE IDs, CVSS scores, severity levels
8. Handle edge cases (missing data, malformed text, multiple CVEs)
9. Log extraction success/failure for monitoring

**Output**: Python module that reliably extracts structured CVE data from unstructured vulnerability advisories, with validation, error handling, and support for multiple LLM providers.

---

## Ollama API Quick Reference

### Endpoints

```
GET  /api/tags              - List available models
POST /api/generate          - Generate text (streaming or non-streaming)
POST /api/chat              - Chat completion with message history
POST /api/pull              - Pull/download a model
POST /api/show              - Show model info
POST /api/embeddings        - Generate embeddings
```

### Generate API

```json
POST /api/generate
{
  "model": "llama2",
  "prompt": "Why is the sky blue?",
  "system": "You are a helpful assistant.",
  "stream": false,
  "format": "json",
  "options": {
    "temperature": 0.7,
    "num_predict": 128,
    "top_p": 0.9,
    "top_k": 40
  }
}
```

### Chat API

```json
POST /api/chat
{
  "model": "llama2",
  "messages": [
    {"role": "system", "content": "You are a security expert."},
    {"role": "user", "content": "Explain XSS."}
  ],
  "stream": false,
  "format": "json",
  "options": {
    "temperature": 0.0
  }
}
```

### Recommended Models for Vulnerability Analysis

- **mistral:latest** - Good balance of speed and accuracy
- **llama2:13b** - Better reasoning, slower
- **codellama:latest** - Excellent for code-related vulnerabilities
- **phi** - Fast, good for simple extraction tasks

### Temperature Guidelines

| Task Type | Temperature | Rationale |
|-----------|-------------|-----------|
| CVE extraction | 0.0 | Factual, no creativity needed |
| CVSS scoring | 0.0-0.1 | Objective assessment |
| Remediation steps | 0.2-0.3 | Some flexibility in wording |
| Impact analysis | 0.3-0.5 | Balanced reasoning |
| Threat scenarios | 0.5-0.7 | Creative but plausible |

---

## Cloud LLM Integration Notes

### Claude (Anthropic)

```python
# Messages API
POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: $ANTHROPIC_API_KEY
  anthropic-version: 2023-06-01

Body:
{
  "model": "claude-3-haiku-20240307",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 1024
}

# Models: claude-3-opus, claude-3-sonnet, claude-3-haiku
```

### Google Gemini

```python
# Generative AI API
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GOOGLE_API_KEY

Body:
{
  "contents": [{"parts": [{"text": "Hello"}]}]
}

# JSON mode: Add "generationConfig": {"response_mime_type": "application/json"}
```

### OpenAI

```python
# Chat Completions API
POST https://api.openai.com/v1/chat/completions
Headers:
  Authorization: Bearer $OPENAI_API_KEY

Body:
{
  "model": "gpt-3.5-turbo",
  "messages": [{"role": "user", "content": "Hello"}],
  "response_format": {"type": "json_object"}
}
```

---

*Skill Version: 1.0*
*Last Updated: December 2024*
