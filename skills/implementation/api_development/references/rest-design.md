# REST API Design

## Core Principles

REST (Representational State Transfer) is an architectural style for designing networked applications.

### 1. Resource-Oriented Design

Resources are nouns, not verbs:
```
✅ GET /users/123
✅ POST /orders
✅ DELETE /articles/456

❌ GET /getUser?id=123
❌ POST /createOrder
❌ GET /deleteArticle/456
```

### 2. URL Structure

```
https://api.example.com/v1/users/123/orders?status=pending&limit=20
└──────────────────────┘ └┘ └───┘ └─┘ └────┘ └──────────────────┘
        Base URL        Ver Collection ID  Sub    Query params
                                          resource
```

**Naming conventions:**
- Use plural nouns: `/users`, `/orders`, `/products`
- Use kebab-case for multi-word: `/order-items`, `/user-profiles`
- Nest for relationships: `/users/123/orders` (orders belonging to user 123)
- Max 2-3 levels deep; beyond that, use query params or separate endpoints

### 3. HTTP Methods (Verbs)

| Method | Purpose | Idempotent | Safe | Request Body |
|--------|---------|------------|------|--------------|
| GET | Read resource(s) | Yes | Yes | No |
| POST | Create resource | No | No | Yes |
| PUT | Replace entire resource | Yes | No | Yes |
| PATCH | Partial update | Yes* | No | Yes |
| DELETE | Remove resource | Yes | No | No |

*PATCH is idempotent if operations are idempotent (set value, not increment)

### 4. HTTP Method Semantics

**GET** - Retrieve resources
```
GET /users           → List all users
GET /users/123       → Get user 123
GET /users?role=admin → Filter users by role
```

**POST** - Create new resource
```
POST /users
Content-Type: application/json

{ "name": "Alice", "email": "alice@example.com" }

Response: 201 Created
Location: /users/456
{ "id": "456", "name": "Alice", ... }
```

**PUT** - Replace entire resource
```
PUT /users/123
Content-Type: application/json

{ "name": "Alice Updated", "email": "alice@new.com", "role": "admin" }
// All fields required - replaces entire resource
```

**PATCH** - Partial update
```
PATCH /users/123
Content-Type: application/json

{ "name": "Alice Updated" }
// Only specified fields change
```

**DELETE** - Remove resource
```
DELETE /users/123

Response: 204 No Content
```

## Response Design

### Standard Response Structure

**Single resource:**
```json
{
  "id": "123",
  "name": "Alice",
  "email": "alice@example.com",
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2025-01-20T14:22:00Z"
}
```

**Collection (paginated):**
```json
{
  "data": [
    { "id": "123", "name": "Alice" },
    { "id": "124", "name": "Bob" }
  ],
  "meta": {
    "total": 150,
    "page": 1,
    "limit": 20,
    "totalPages": 8
  },
  "links": {
    "self": "/users?page=1",
    "next": "/users?page=2",
    "last": "/users?page=8"
  }
}
```

### Field Naming

Use consistent naming convention (camelCase recommended for JavaScript/TypeScript):
```json
{
  "userId": "123",
  "firstName": "Alice",
  "createdAt": "2025-01-15T10:30:00Z",
  "isActive": true
}
```

### Timestamps

Use ISO 8601 format with timezone:
```
"2025-01-15T10:30:00Z"           // UTC
"2025-01-15T10:30:00+05:30"      // With offset
```

## Query Parameters

### Filtering
```
GET /users?role=admin&status=active
GET /orders?createdAfter=2025-01-01&createdBefore=2025-02-01
GET /products?price[gte]=100&price[lte]=500
```

### Sorting
```
GET /users?sort=createdAt        // Ascending
GET /users?sort=-createdAt       // Descending (prefix with -)
GET /users?sort=role,-createdAt  // Multiple fields
```

### Field Selection (Sparse Fieldsets)
```
GET /users?fields=id,name,email
GET /users/123?fields=id,name,orders.id,orders.total
```

### Pagination
```
GET /users?page=2&limit=20       // Offset-based
GET /users?cursor=abc123&limit=20 // Cursor-based
```

### Search
```
GET /users?q=alice               // Full-text search
GET /products?search=laptop      // Product search
```

## Relationships and Nesting

### Nested Resources
```
GET /users/123/orders            // Orders belonging to user 123
POST /users/123/orders           // Create order for user 123
GET /orders/456/items            // Items in order 456
```

### Resource Expansion (Include Related)
```
GET /orders/456?include=user,items
GET /users/123?include=orders,profile

Response:
{
  "id": "456",
  "total": 99.99,
  "user": { "id": "123", "name": "Alice" },
  "items": [...]
}
```

### Linking Instead of Nesting
When nesting becomes deep, use links:
```json
{
  "id": "456",
  "total": 99.99,
  "links": {
    "user": "/users/123",
    "items": "/orders/456/items"
  }
}
```

## Content Negotiation

### Request Headers
```
Accept: application/json
Accept: application/xml
Accept: application/vnd.api+json  // JSON:API
```

### Response Headers
```
Content-Type: application/json; charset=utf-8
```

### Compression
```
Accept-Encoding: gzip, deflate
Content-Encoding: gzip
```

## Batch Operations

When single-resource operations are inefficient:

```
POST /users/batch
Content-Type: application/json

{
  "operations": [
    { "method": "POST", "body": { "name": "Alice" } },
    { "method": "POST", "body": { "name": "Bob" } },
    { "method": "DELETE", "id": "123" }
  ]
}

Response: 207 Multi-Status
{
  "results": [
    { "status": 201, "id": "456" },
    { "status": 201, "id": "457" },
    { "status": 204 }
  ]
}
```

## Idempotency

For non-idempotent operations (POST), use idempotency keys:
```
POST /payments
Idempotency-Key: unique-request-id-12345
Content-Type: application/json

{ "amount": 100, "currency": "USD" }
```

Server stores result keyed by idempotency key and returns same response for duplicate requests.

## HATEOAS (Hypermedia)

Include navigable links in responses:
```json
{
  "id": "123",
  "name": "Alice",
  "links": {
    "self": "/users/123",
    "orders": "/users/123/orders",
    "profile": "/users/123/profile",
    "deactivate": "/users/123/deactivate"
  },
  "actions": [
    {
      "name": "update",
      "method": "PATCH",
      "href": "/users/123"
    }
  ]
}
```

## Caching

### Cache Headers
```
# Response can be cached for 1 hour
Cache-Control: public, max-age=3600

# Response is user-specific
Cache-Control: private, max-age=3600

# Never cache
Cache-Control: no-store

# Revalidate before using
Cache-Control: no-cache
```

### ETags for Conditional Requests
```
# Response includes ETag
ETag: "abc123"

# Subsequent request checks if changed
GET /users/123
If-None-Match: "abc123"

# If unchanged: 304 Not Modified
# If changed: 200 OK with new ETag
```

### Last-Modified
```
Last-Modified: Wed, 15 Jan 2025 10:30:00 GMT

# Conditional request
If-Modified-Since: Wed, 15 Jan 2025 10:30:00 GMT
```

## Best Practices Summary

1. **Use nouns for resources**, verbs come from HTTP methods
2. **Use plural nouns** consistently: `/users`, not `/user`
3. **Use HTTP methods correctly** - GET is safe, PUT/DELETE are idempotent
4. **Return appropriate status codes** - be specific, not just 200/500
5. **Version your API** from day one - URL path (`/v1/`) is clearest
6. **Use consistent naming** - pick camelCase or snake_case, stick with it
7. **Support filtering, sorting, pagination** on collection endpoints
8. **Use ISO 8601 for dates** with timezone info
9. **Include links** to related resources and available actions
10. **Document with OpenAPI** - generate docs, client SDKs automatically
