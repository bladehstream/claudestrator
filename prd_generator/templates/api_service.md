# Product Requirements Document: API Service

```yaml
# PRD Metadata (machine-readable for orchestrator)
metadata:
  schema_version: "2.0"
  project:
    name: "[Project Name]"
    type: api_service
    complexity: simple | moderate | complex
  mvp:
    target_date: "[YYYY-MM-DD or TBD]"
    feature_count: 0
  tech_stack:
    languages: []
    frameworks: []
    databases: []
    infrastructure: []
  api:
    style: REST | GraphQL | gRPC
    versioning: url_path | header | query_param
  constraints:
    team_size: 1
    timeline: "[e.g., 4 weeks]"
  tags: []
```

## Document Information

| Field | Value |
|-------|-------|
| **Project Name** | [Project Name] |
| **Document Version** | 2.0 |
| **Created** | [Date] |
| **Last Updated** | [Date] |
| **Author** | [Author] |
| **Status** | Draft / In Review / Approved |

---

## 1. Executive Summary

### 1.1 Vision Statement
[One sentence describing what this API will enable]

### 1.2 Problem Statement
[What problem does this API solve? What systems or applications will consume it?]

### 1.2 Proposed Solution
[High-level description of the API service and its primary purpose]

### 1.3 API Consumers

| Consumer | Description | Use Case |
|----------|-------------|----------|
| [e.g., Mobile App] | [Description] | [Primary use case] |
| [e.g., Web Frontend] | [Description] | [Primary use case] |
| [e.g., Third-party] | [Description] | [Primary use case] |

### 1.4 Success Metrics

| Metric | Target |
|--------|--------|
| API Response Time (p95) | < [X] ms |
| Availability | [99.9]% uptime |
| Error Rate | < [X]% |

---

## 2. API Overview

### 2.1 API Style

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| **Architecture** | REST / GraphQL / gRPC | [Why this choice] |
| **Data Format** | JSON / Protocol Buffers | [Why this choice] |
| **Versioning** | URL path / Header / Query param | [Why this choice] |

### 2.2 Base URL Structure
```
Production:  https://api.[domain].com/v1
Staging:     https://api.staging.[domain].com/v1
Development: http://localhost:[port]/v1
```

### 2.3 API Versioning Strategy
[Describe versioning approach, deprecation policy, breaking change handling]

---

## 3. Authentication & Authorization

### 3.1 Authentication Methods

| Method | Use Case | Priority |
|--------|----------|----------|
| API Key | Server-to-server | Must Have |
| JWT Bearer Token | User sessions | Must Have |
| OAuth 2.0 | Third-party integrations | Should Have |

### 3.2 Authorization Model

| Model Component | Description |
|-----------------|-------------|
| **Type** | [RBAC / ABAC / ACL] |
| **Roles** | [List of roles] |
| **Permissions** | [Permission structure] |

### 3.3 Token Specifications

| Aspect | Specification |
|--------|---------------|
| Token Type | JWT / Opaque |
| Expiration | Access: [X] minutes, Refresh: [X] days |
| Refresh Strategy | [Sliding / Fixed] |
| Revocation | [Mechanism] |

---

## 4. API Endpoints

### 4.1 Resource: [Resource Name]

**Base Path**: `/v1/[resources]`

#### Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/[resources]` | List all [resources] | Yes |
| POST | `/[resources]` | Create a [resource] | Yes |
| GET | `/[resources]/{id}` | Get a specific [resource] | Yes |
| PUT | `/[resources]/{id}` | Update a [resource] | Yes |
| PATCH | `/[resources]/{id}` | Partial update | Yes |
| DELETE | `/[resources]/{id}` | Delete a [resource] | Yes |

#### GET `/[resources]` - List Resources

**Query Parameters**:
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `page` | integer | No | Page number | 1 |
| `limit` | integer | No | Items per page | 20 |
| `sort` | string | No | Sort field | `created_at` |
| `order` | string | No | Sort order (asc/desc) | `desc` |
| `filter[field]` | string | No | Filter by field | - |

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "uuid",
      "type": "[resource]",
      "attributes": {
        "field1": "value1",
        "field2": "value2",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "total_pages": 5
  },
  "links": {
    "self": "/v1/[resources]?page=1",
    "next": "/v1/[resources]?page=2",
    "last": "/v1/[resources]?page=5"
  }
}
```

#### POST `/[resources]` - Create Resource

**Request Body**:
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

**Response** (201 Created):
```json
{
  "data": {
    "id": "uuid",
    "type": "[resource]",
    "attributes": {
      "field1": "value1",
      "field2": "value2",
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

[Repeat for each resource]

---

## 5. Data Models

### 5.1 Resource: [Resource Name]

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `id` | UUID | Auto | Unique identifier | Primary key |
| `field1` | string | Yes | [Description] | max 255 chars |
| `field2` | integer | No | [Description] | min 0, max 1000 |
| `status` | enum | Yes | [Description] | [active, inactive, pending] |
| `created_at` | datetime | Auto | Creation timestamp | ISO 8601 |
| `updated_at` | datetime | Auto | Last update timestamp | ISO 8601 |

### 5.2 Relationships

```
[Resource1] 1---* [Resource2]  (one-to-many)
[Resource2] *---* [Resource3]  (many-to-many via join table)
```

### 5.3 Data Validation Rules

| Field | Validation |
|-------|------------|
| `email` | Valid email format, unique |
| `[field]` | [Validation rules] |

---

## 6. Error Handling

### 6.1 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error message",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "req_abc123"
  }
}
```

### 6.2 Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `BAD_REQUEST` | Malformed request syntax |
| 400 | `VALIDATION_ERROR` | Request validation failed |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource conflict (e.g., duplicate) |
| 422 | `UNPROCESSABLE_ENTITY` | Semantic validation error |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

---

## 7. Rate Limiting

### 7.1 Rate Limit Tiers

| Tier | Requests/Minute | Requests/Day | Use Case |
|------|-----------------|--------------|----------|
| Free | 60 | 1,000 | Development, testing |
| Standard | 300 | 50,000 | Production apps |
| Enterprise | 1,000 | Unlimited | High-volume clients |

### 7.2 Rate Limit Headers

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Requests remaining in window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |
| `Retry-After` | Seconds to wait (when rate limited) |

---

## 8. Pagination & Filtering

### 8.1 Pagination Strategy

| Strategy | Implementation |
|----------|----------------|
| **Type** | Offset-based / Cursor-based |
| **Default Limit** | 20 |
| **Maximum Limit** | 100 |

### 8.2 Filtering Syntax
```
GET /resources?filter[status]=active&filter[created_at][gte]=2024-01-01
```

### 8.3 Sorting Syntax
```
GET /resources?sort=-created_at,name
```
(Prefix `-` for descending order)

---

## 9. Security Requirements

### 9.1 Transport Security

| Requirement | Specification |
|-------------|---------------|
| Protocol | HTTPS only (TLS 1.2+) |
| HSTS | Enabled, max-age 31536000 |
| Certificate | Valid, not self-signed |

### 9.2 Input Validation

| Attack Vector | Mitigation |
|---------------|------------|
| SQL Injection | Parameterized queries |
| XSS | Output encoding, Content-Type headers |
| CSRF | Token validation for state-changing requests |
| Mass Assignment | Explicit field allowlists |

### 9.3 Security Headers

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Content-Security-Policy` | [Policy] |

### 9.4 Audit Logging

| Event | Logged Data |
|-------|-------------|
| Authentication | User ID, IP, timestamp, success/failure |
| Authorization Failure | User ID, resource, action, timestamp |
| Data Modification | User ID, resource ID, changes, timestamp |

---

## 10. Performance Requirements

### 10.1 Response Time SLAs

| Endpoint Category | p50 | p95 | p99 |
|-------------------|-----|-----|-----|
| Read (single) | < 50ms | < 100ms | < 200ms |
| Read (list) | < 100ms | < 200ms | < 500ms |
| Write | < 100ms | < 300ms | < 500ms |
| Complex queries | < 200ms | < 500ms | < 1000ms |

### 10.2 Throughput Requirements

| Metric | Requirement |
|--------|-------------|
| Peak RPS | [X] requests/second |
| Sustained RPS | [X] requests/second |

### 10.3 Caching Strategy

| Resource | Cache Duration | Invalidation |
|----------|----------------|--------------|
| [Resource] | [Duration] | [Strategy] |
| Static config | 24 hours | Manual |

---

## 11. Technical Architecture

### 11.1 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | [e.g., Go, Node.js, Python] | [Why] |
| Framework | [e.g., Express, FastAPI, Gin] | [Why] |
| Database | [e.g., PostgreSQL, MongoDB] | [Why] |
| Cache | [e.g., Redis] | [Why] |
| Queue | [e.g., RabbitMQ, SQS] | [Why] |

### 11.2 Infrastructure

| Component | Service/Tool |
|-----------|--------------|
| Hosting | [e.g., AWS, GCP, Azure] |
| Container Orchestration | [e.g., Kubernetes, ECS] |
| Load Balancer | [e.g., ALB, nginx] |
| CDN | [e.g., CloudFront, Cloudflare] |

### 11.3 Database Schema
[Reference to schema documentation or ERD]

---

## 12. Monitoring & Observability

### 12.1 Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| Request Rate | Requests per second | > [X] |
| Error Rate | 5xx errors percentage | > [X]% |
| Latency (p95) | 95th percentile response time | > [X]ms |
| Availability | Uptime percentage | < [99.9]% |

### 12.2 Logging

| Log Level | Use Case |
|-----------|----------|
| ERROR | Exceptions, failures |
| WARN | Degraded performance, retries |
| INFO | Request/response summaries |
| DEBUG | Detailed debugging (dev only) |

### 12.3 Tracing
- Distributed tracing with correlation IDs
- Request ID in all responses (`X-Request-ID`)

---

## 13. API Documentation

### 13.1 Documentation Requirements

| Document | Format | Priority |
|----------|--------|----------|
| OpenAPI Spec | YAML/JSON (3.0+) | Must Have |
| Interactive Docs | Swagger UI / Redoc | Must Have |
| Getting Started Guide | Markdown | Must Have |
| SDK Documentation | Per-language | Should Have |

### 13.2 Example Requests
[Provide curl examples for key endpoints]

```bash
# Authenticate
curl -X POST https://api.example.com/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "..."}'

# List resources
curl https://api.example.com/v1/resources \
  -H "Authorization: Bearer <token>"
```

---

## 14. Testing Requirements

### 14.1 Test Coverage

| Test Type | Coverage Target |
|-----------|-----------------|
| Unit Tests | [X]% |
| Integration Tests | All endpoints |
| Contract Tests | All public APIs |
| Load Tests | Peak traffic scenarios |

### 14.2 Test Environments

| Environment | Purpose | Data |
|-------------|---------|------|
| Development | Local development | Seeded/mock |
| Staging | Pre-production testing | Anonymized production |
| Production | Live traffic | Real data |

---

## 15. Release Planning

### 15.1 MVP (v1.0)
- [Core endpoints]
- [Authentication]
- [Basic rate limiting]

### 15.2 v1.1
- [Additional endpoints]
- [Webhooks]
- [Enhanced filtering]

### 15.3 Future Considerations
- [GraphQL support]
- [Real-time subscriptions]
- [Public API marketplace]

---

## 16. Open Questions

| Question | Owner | Resolution |
|----------|-------|------------|
| [Question] | [Person] | [Pending/Resolved] |

---

## 17. Appendices

### A. Glossary

| Term | Definition |
|------|------------|
| [Term] | [Definition] |

### B. References
- [API design guidelines followed]
- [Industry standards referenced]

---

## 18. MVP Feature List

### Feature Summary

| ID | Feature/Resource | Priority | Complexity | Dependencies |
|----|------------------|----------|------------|--------------|
| F-001 | [Resource/Endpoint Group] | Must Have | Normal | None |
| F-002 | [Resource/Endpoint Group] | Must Have | Normal | F-001 |
| F-003 | [Resource/Endpoint Group] | Should Have | Normal | F-001 |

---

## 19. Implementation Guidance

### Suggested Task Order
1. Project setup (framework, linting, CI/CD)
2. Database schema and migrations
3. Authentication middleware
4. Core resource endpoints (F-001)
5. Additional resources (F-002, F-003)
6. Rate limiting and caching
7. API documentation (OpenAPI)
8. Testing and QA

### Parallelization Opportunities
- Resource endpoints can be developed in parallel after auth is complete
- Documentation can be written alongside implementation
- Integration tests can be written as endpoints are completed

### Definition of Done
- [ ] All acceptance criteria passing
- [ ] Unit test coverage > 80%
- [ ] Integration tests for all endpoints
- [ ] OpenAPI spec complete and valid
- [ ] Security scan passing
- [ ] Load test meeting SLAs
- [ ] Documentation complete

---

*Generated with Claudestrator PRD Generator v2.0*
