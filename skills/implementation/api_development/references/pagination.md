# Pagination

## Pagination Strategies

### 1. Offset-Based Pagination

Simple page/limit approach using SQL OFFSET.

**Request:**
```
GET /users?page=2&limit=20
GET /users?offset=20&limit=20
```

**Response:**
```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 2,
    "limit": 20,
    "totalPages": 8
  },
  "links": {
    "self": "/users?page=2&limit=20",
    "first": "/users?page=1&limit=20",
    "prev": "/users?page=1&limit=20",
    "next": "/users?page=3&limit=20",
    "last": "/users?page=8&limit=20"
  }
}
```

**Implementation:**
```typescript
interface OffsetPaginationParams {
  page?: number;
  limit?: number;
}

async function getUsers({ page = 1, limit = 20 }: OffsetPaginationParams) {
  const offset = (page - 1) * limit;
  
  const [users, total] = await Promise.all([
    db.user.findMany({
      skip: offset,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    db.user.count(),
  ]);
  
  const totalPages = Math.ceil(total / limit);
  
  return {
    data: users,
    meta: {
      total,
      page,
      limit,
      totalPages,
    },
    links: {
      self: `/users?page=${page}&limit=${limit}`,
      first: `/users?page=1&limit=${limit}`,
      prev: page > 1 ? `/users?page=${page - 1}&limit=${limit}` : null,
      next: page < totalPages ? `/users?page=${page + 1}&limit=${limit}` : null,
      last: `/users?page=${totalPages}&limit=${limit}`,
    },
  };
}
```

**Pros:**
- Simple to implement
- Supports random page access
- Familiar UI pattern
- Total count available

**Cons:**
- Performance degrades on deep pages (OFFSET is slow)
- Data inconsistency (duplicates/skips if data changes)
- Not suitable for real-time data

**When to use:**
- Small datasets (<10,000 records)
- Admin panels with page navigation
- Static/rarely changing data

### 2. Cursor-Based Pagination

Use opaque cursor pointing to last item.

**Request:**
```
GET /users?cursor=eyJpZCI6MTIzfQ&limit=20
GET /users?after=abc123&limit=20
```

**Response:**
```json
{
  "data": [...],
  "meta": {
    "hasNextPage": true,
    "hasPrevPage": true,
    "nextCursor": "eyJpZCI6MTQzfQ",
    "prevCursor": "eyJpZCI6MTIzfQ"
  },
  "links": {
    "self": "/users?limit=20",
    "next": "/users?cursor=eyJpZCI6MTQzfQ&limit=20",
    "prev": "/users?cursor=eyJpZCI6MTIzfQ&direction=prev&limit=20"
  }
}
```

**Implementation:**
```typescript
interface CursorPaginationParams {
  cursor?: string;
  limit?: number;
  direction?: 'next' | 'prev';
}

// Cursor encoding
function encodeCursor(data: Record<string, unknown>): string {
  return Buffer.from(JSON.stringify(data)).toString('base64url');
}

function decodeCursor(cursor: string): Record<string, unknown> {
  return JSON.parse(Buffer.from(cursor, 'base64url').toString());
}

async function getUsers({ cursor, limit = 20, direction = 'next' }: CursorPaginationParams) {
  let whereClause = {};
  let orderBy = { createdAt: 'desc' as const, id: 'desc' as const };
  
  if (cursor) {
    const { createdAt, id } = decodeCursor(cursor);
    if (direction === 'next') {
      whereClause = {
        OR: [
          { createdAt: { lt: new Date(createdAt as string) } },
          {
            createdAt: new Date(createdAt as string),
            id: { lt: id as string },
          },
        ],
      };
    } else {
      // Previous page - reverse direction
      whereClause = {
        OR: [
          { createdAt: { gt: new Date(createdAt as string) } },
          {
            createdAt: new Date(createdAt as string),
            id: { gt: id as string },
          },
        ],
      };
      orderBy = { createdAt: 'asc', id: 'asc' };
    }
  }
  
  // Fetch one extra to check if there's a next page
  const users = await db.user.findMany({
    where: whereClause,
    orderBy,
    take: limit + 1,
  });
  
  // Reverse if fetching previous
  if (direction === 'prev') {
    users.reverse();
  }
  
  const hasMore = users.length > limit;
  const data = hasMore ? users.slice(0, limit) : users;
  
  const firstItem = data[0];
  const lastItem = data[data.length - 1];
  
  return {
    data,
    meta: {
      hasNextPage: hasMore,
      hasPrevPage: !!cursor,
      nextCursor: lastItem ? encodeCursor({ 
        createdAt: lastItem.createdAt, 
        id: lastItem.id 
      }) : null,
      prevCursor: firstItem ? encodeCursor({ 
        createdAt: firstItem.createdAt, 
        id: firstItem.id 
      }) : null,
    },
  };
}
```

**Pros:**
- Consistent performance regardless of offset
- No duplicates or skips when data changes
- Works well with infinite scroll
- Efficient for large datasets

**Cons:**
- No random page access
- More complex implementation
- No total count (requires separate query)

**When to use:**
- Large datasets
- Real-time feeds
- Infinite scroll UIs
- Mobile applications

### 3. Keyset Pagination

Similar to cursor but uses visible field values directly.

**Request:**
```
GET /users?after_id=123&after_created_at=2025-01-15T10:00:00Z&limit=20
```

**Response:**
```json
{
  "data": [...],
  "meta": {
    "hasNextPage": true,
    "lastId": "143",
    "lastCreatedAt": "2025-01-15T09:30:00Z"
  }
}
```

**Implementation:**
```typescript
interface KeysetPaginationParams {
  afterId?: string;
  afterCreatedAt?: string;
  limit?: number;
}

async function getUsers({ afterId, afterCreatedAt, limit = 20 }: KeysetPaginationParams) {
  let whereClause = {};
  
  if (afterCreatedAt && afterId) {
    whereClause = {
      OR: [
        { createdAt: { lt: new Date(afterCreatedAt) } },
        {
          createdAt: new Date(afterCreatedAt),
          id: { lt: afterId },
        },
      ],
    };
  }
  
  const users = await db.user.findMany({
    where: whereClause,
    orderBy: [
      { createdAt: 'desc' },
      { id: 'desc' },
    ],
    take: limit + 1,
  });
  
  const hasNextPage = users.length > limit;
  const data = hasNextPage ? users.slice(0, limit) : users;
  const lastItem = data[data.length - 1];
  
  return {
    data,
    meta: {
      hasNextPage,
      lastId: lastItem?.id,
      lastCreatedAt: lastItem?.createdAt,
    },
  };
}
```

**Pros:**
- Same performance benefits as cursor
- Transparent/debuggable (not encoded)
- Can resume from any point

**Cons:**
- Exposes database structure
- Requires stable sort columns
- Complex for composite keys

### Comparison Table

| Feature | Offset | Cursor | Keyset |
|---------|--------|--------|--------|
| Random access | ✅ Yes | ❌ No | ❌ No |
| Deep page performance | ❌ Poor | ✅ Good | ✅ Good |
| Data consistency | ❌ May drift | ✅ Stable | ✅ Stable |
| Total count | ✅ Easy | ⚠️ Extra query | ⚠️ Extra query |
| Implementation | ✅ Simple | ⚠️ Medium | ⚠️ Medium |
| Debuggability | ✅ Clear | ⚠️ Encoded | ✅ Clear |

## Relay-Style Connections (GraphQL)

Standard pagination pattern for GraphQL.

```graphql
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  users(
    first: Int
    after: String
    last: Int
    before: String
  ): UserConnection!
}
```

## Best Practices

### 1. Set Sensible Defaults and Limits

```typescript
const paginationSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});
```

### 2. Require Stable Ordering

Always include a unique field in sort to ensure consistent pagination:

```typescript
// ❌ Bad - ties cause inconsistent ordering
orderBy: { createdAt: 'desc' }

// ✅ Good - id breaks ties
orderBy: [
  { createdAt: 'desc' },
  { id: 'desc' },
]
```

### 3. Use Composite Index

```sql
-- For cursor pagination on (createdAt, id)
CREATE INDEX idx_users_pagination ON users (created_at DESC, id DESC);
```

### 4. Include Helpful Metadata

```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 2,
    "limit": 20,
    "totalPages": 8,
    "hasNextPage": true,
    "hasPrevPage": true
  },
  "links": {
    "self": "/users?page=2",
    "first": "/users?page=1",
    "prev": "/users?page=1",
    "next": "/users?page=3",
    "last": "/users?page=8"
  }
}
```

### 5. Handle Edge Cases

```typescript
// Empty results
if (data.length === 0) {
  return {
    data: [],
    meta: {
      total: 0,
      page: 1,
      limit: 20,
      totalPages: 0,
      hasNextPage: false,
      hasPrevPage: false,
    },
  };
}

// Invalid page number
if (page > totalPages && totalPages > 0) {
  throw new BadRequestError(`Page ${page} exceeds total pages (${totalPages})`);
}
```

### 6. Document Pagination in OpenAPI

```yaml
parameters:
  - name: page
    in: query
    schema:
      type: integer
      minimum: 1
      default: 1
    description: Page number (1-indexed)
  - name: limit
    in: query
    schema:
      type: integer
      minimum: 1
      maximum: 100
      default: 20
    description: Items per page (max 100)

responses:
  200:
    description: Paginated list of users
    headers:
      X-Total-Count:
        schema:
          type: integer
        description: Total number of items
      X-Page:
        schema:
          type: integer
        description: Current page number
      Link:
        schema:
          type: string
        description: RFC 5988 pagination links
```

## Zod Schemas for Pagination

```typescript
// Offset pagination params
export const offsetPaginationSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

// Cursor pagination params
export const cursorPaginationSchema = z.object({
  cursor: z.string().optional(),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  direction: z.enum(['next', 'prev']).default('next'),
});

// Generic paginated response
export const paginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    data: z.array(itemSchema),
    meta: z.object({
      total: z.number().optional(),
      page: z.number().optional(),
      limit: z.number(),
      totalPages: z.number().optional(),
      hasNextPage: z.boolean(),
      hasPrevPage: z.boolean(),
      nextCursor: z.string().nullable().optional(),
      prevCursor: z.string().nullable().optional(),
    }),
    links: z.object({
      self: z.string(),
      first: z.string().nullable().optional(),
      prev: z.string().nullable(),
      next: z.string().nullable(),
      last: z.string().nullable().optional(),
    }).optional(),
  });
```
