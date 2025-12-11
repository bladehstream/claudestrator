# OpenAPI Specification

## Overview

OpenAPI (formerly Swagger) is the standard for describing REST APIs. Current version is 3.1.0 (JSON Schema 2020-12 aligned) with 3.2.0 released September 2025.

## Basic Structure

```yaml
openapi: 3.1.0
info:
  title: My API
  version: 1.0.0
  description: API description with **markdown** support
  contact:
    name: API Support
    email: support@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging

paths:
  /users:
    # ... endpoint definitions
    
components:
  schemas:
    # ... reusable schemas
  securitySchemes:
    # ... auth definitions
```

## Path Definitions

```yaml
paths:
  /users:
    get:
      operationId: listUsers
      summary: List all users
      description: Returns paginated list of users
      tags:
        - Users
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
        - name: role
          in: query
          schema:
            $ref: '#/components/schemas/UserRole'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
    
    post:
      operationId: createUser
      summary: Create a user
      tags:
        - Users
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserInput'
            examples:
              basic:
                summary: Basic user
                value:
                  email: user@example.com
                  name: John Doe
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
          headers:
            Location:
              schema:
                type: string
              description: URL of created resource
        '400':
          $ref: '#/components/responses/ValidationError'
        '409':
          $ref: '#/components/responses/Conflict'

  /users/{userId}:
    parameters:
      - name: userId
        in: path
        required: true
        schema:
          type: string
          format: uuid
    
    get:
      operationId: getUser
      summary: Get user by ID
      tags:
        - Users
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          $ref: '#/components/responses/NotFound'
    
    patch:
      operationId: updateUser
      summary: Update user
      tags:
        - Users
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateUserInput'
      responses:
        '200':
          description: User updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
    
    delete:
      operationId: deleteUser
      summary: Delete user
      tags:
        - Users
      responses:
        '204':
          description: User deleted
```

## Components (Reusable Definitions)

### Schemas

```yaml
components:
  schemas:
    # Basic types
    User:
      type: object
      required:
        - id
        - email
        - role
        - createdAt
      properties:
        id:
          type: string
          format: uuid
          readOnly: true
        email:
          type: string
          format: email
        name:
          type: string
          minLength: 2
          maxLength: 100
        role:
          $ref: '#/components/schemas/UserRole'
        createdAt:
          type: string
          format: date-time
          readOnly: true
        updatedAt:
          type: string
          format: date-time
          readOnly: true
    
    UserRole:
      type: string
      enum:
        - user
        - admin
        - moderator
      default: user
    
    # Input schemas
    CreateUserInput:
      type: object
      required:
        - email
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          minLength: 2
          maxLength: 100
        role:
          $ref: '#/components/schemas/UserRole'
    
    UpdateUserInput:
      type: object
      properties:
        name:
          type: string
          minLength: 2
          maxLength: 100
        role:
          $ref: '#/components/schemas/UserRole'
    
    # Paginated response
    UserListResponse:
      type: object
      required:
        - data
        - meta
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/User'
        meta:
          $ref: '#/components/schemas/PaginationMeta'
        links:
          $ref: '#/components/schemas/PaginationLinks'
    
    PaginationMeta:
      type: object
      properties:
        total:
          type: integer
        page:
          type: integer
        limit:
          type: integer
        totalPages:
          type: integer
    
    PaginationLinks:
      type: object
      properties:
        self:
          type: string
        next:
          type: string
          nullable: true
        prev:
          type: string
          nullable: true
    
    # Error schemas (RFC 9457)
    ProblemDetails:
      type: object
      required:
        - type
        - title
        - status
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string
    
    ValidationError:
      allOf:
        - $ref: '#/components/schemas/ProblemDetails'
        - type: object
          properties:
            errors:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  message:
                    type: string
```

### Parameters

```yaml
components:
  parameters:
    PageParam:
      name: page
      in: query
      schema:
        type: integer
        minimum: 1
        default: 1
    
    LimitParam:
      name: limit
      in: query
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
    
    CursorParam:
      name: cursor
      in: query
      schema:
        type: string
      description: Pagination cursor from previous response
    
    SortParam:
      name: sort
      in: query
      schema:
        type: string
      description: Field to sort by (prefix with - for descending)
      example: -createdAt
```

### Responses

```yaml
components:
  responses:
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          example:
            type: https://api.example.com/errors/not-found
            title: Not Found
            status: 404
            detail: User with id 123 not found
    
    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    
    Forbidden:
      description: Insufficient permissions
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    
    ValidationError:
      description: Validation failed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationError'
    
    Conflict:
      description: Resource conflict (e.g., duplicate)
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
    
    TooManyRequests:
      description: Rate limit exceeded
      headers:
        Retry-After:
          schema:
            type: integer
          description: Seconds until rate limit resets
        X-RateLimit-Limit:
          schema:
            type: integer
        X-RateLimit-Remaining:
          schema:
            type: integer
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
```

### Security Schemes

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    
    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          scopes:
            read:users: Read user data
            write:users: Modify user data
            admin: Full admin access

# Apply globally
security:
  - BearerAuth: []

# Or per-operation
paths:
  /public:
    get:
      security: []  # No auth required
  /admin:
    get:
      security:
        - BearerAuth: []
        - OAuth2: [admin]
```

## Webhooks (3.1+)

```yaml
webhooks:
  userCreated:
    post:
      summary: User created webhook
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                event:
                  type: string
                  enum: [user.created]
                data:
                  $ref: '#/components/schemas/User'
                timestamp:
                  type: string
                  format: date-time
      responses:
        '200':
          description: Webhook processed
```

## Advanced Schema Features

### Discriminator (Polymorphism)

```yaml
components:
  schemas:
    Notification:
      oneOf:
        - $ref: '#/components/schemas/EmailNotification'
        - $ref: '#/components/schemas/SmsNotification'
        - $ref: '#/components/schemas/PushNotification'
      discriminator:
        propertyName: type
        mapping:
          email: '#/components/schemas/EmailNotification'
          sms: '#/components/schemas/SmsNotification'
          push: '#/components/schemas/PushNotification'
    
    EmailNotification:
      type: object
      required: [type, email, subject]
      properties:
        type:
          type: string
          enum: [email]
        email:
          type: string
          format: email
        subject:
          type: string
    
    SmsNotification:
      type: object
      required: [type, phone, message]
      properties:
        type:
          type: string
          enum: [sms]
        phone:
          type: string
        message:
          type: string
```

### File Upload

```yaml
paths:
  /upload:
    post:
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                description:
                  type: string
            encoding:
              file:
                contentType: image/png, image/jpeg
```

### Server-Sent Events (SSE)

```yaml
paths:
  /events:
    get:
      responses:
        '200':
          description: Event stream
          content:
            text/event-stream:
              schema:
                type: string
```

## Design-First Workflow

1. **Write spec first** - Define endpoints, schemas, responses
2. **Generate types** - Use tools to create TypeScript interfaces
3. **Implement handlers** - Code against generated types
4. **Validate at runtime** - Ensure responses match spec
5. **Generate docs** - Auto-generate API documentation

### Tooling

```bash
# Generate TypeScript types from OpenAPI
npx openapi-typescript ./openapi.yaml -o ./types/api.ts

# Generate Zod schemas
npx openapi-zod-client ./openapi.yaml -o ./schemas

# Validate spec
npx @redocly/cli lint openapi.yaml

# Generate documentation
npx @redocly/cli build-docs openapi.yaml -o docs.html
```

### Hono + OpenAPI Integration

```typescript
import { OpenAPIHono, createRoute, z } from '@hono/zod-openapi';

const route = createRoute({
  method: 'get',
  path: '/users/{id}',
  request: {
    params: z.object({
      id: z.string().uuid(),
    }),
  },
  responses: {
    200: {
      content: {
        'application/json': {
          schema: UserSchema,
        },
      },
      description: 'User found',
    },
    404: {
      content: {
        'application/json': {
          schema: ProblemDetailsSchema,
        },
      },
      description: 'User not found',
    },
  },
});

app.openapi(route, async (c) => {
  const { id } = c.req.valid('param');
  const user = await userService.findById(id);
  if (!user) {
    return c.json({ type: 'not_found', title: 'Not Found', status: 404 }, 404);
  }
  return c.json(user, 200);
});

// Generate OpenAPI doc
app.doc('/openapi.json', {
  openapi: '3.1.0',
  info: { title: 'My API', version: '1.0.0' },
});
```

## Best Practices

1. **Use `operationId`** - Unique identifier for code generation
2. **Add examples** - Real data examples improve understanding
3. **Use `$ref`** - Avoid duplication with components
4. **Document all responses** - Including errors
5. **Use tags** - Group related operations
6. **Semantic versioning** - In `info.version`
7. **Describe deprecations** - `deprecated: true` with description
8. **Security first** - Define schemes, apply globally
