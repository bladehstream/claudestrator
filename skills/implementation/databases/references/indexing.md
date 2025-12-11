# Database Indexing Reference

Index types, strategies, and optimization patterns for PostgreSQL.

## Index Types Quick Reference

| Type | Best For | Operators |
|------|----------|-----------|
| B-Tree | Equality, range, sorting | `=`, `<`, `>`, `<=`, `>=`, `BETWEEN`, `IN`, `IS NULL` |
| Hash | Exact equality only | `=` |
| GIN | Arrays, JSONB, full-text | `@>`, `<@`, `?`, `?&`, `?|`, `@@` |
| GiST | Spatial, ranges, nearest-neighbor | `<<`, `>>`, `&<`, `&>`, `&&`, `@>` |
| BRIN | Large ordered datasets | Range operators on naturally ordered data |

## Creating Indexes

### Basic Syntax

```sql
-- Standard B-Tree index
CREATE INDEX idx_users_email ON users(email);

-- Unique index
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);

-- Composite index
CREATE INDEX idx_posts_author_date ON posts(author_id, created_at DESC);

-- Partial index (filtered)
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;

-- Expression index
CREATE INDEX idx_users_lower_email ON users(lower(email));

-- Concurrent (no lock)
CREATE INDEX CONCURRENTLY idx_users_name ON users(name);
```

### Prisma Indexes

```prisma
model User {
  id    String @id @default(cuid())
  email String @unique
  name  String
  role  Role
  
  // Single column index
  @@index([email])
  
  // Composite index
  @@index([role, createdAt(sort: Desc)])
  
  // Multiple indexes
  @@index([name])
}

model Post {
  id        String @id
  title     String
  authorId  String
  createdAt DateTime
  
  // Always index foreign keys
  @@index([authorId])
  
  // Composite for common query pattern
  @@index([authorId, createdAt(sort: Desc)])
}
```

### Drizzle Indexes

```typescript
import { pgTable, text, timestamp, index, uniqueIndex } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull(),
  name: text('name'),
  role: text('role'),
  createdAt: timestamp('created_at').defaultNow(),
}, (table) => [
  // Single column
  index('users_email_idx').on(table.email),
  
  // Unique index
  uniqueIndex('users_email_unique').on(table.email),
  
  // Composite
  index('users_role_created_idx').on(table.role, table.createdAt.desc()),
  
  // Expression index
  index('users_lower_email_idx').on(sql`lower(${table.email})`),
]);
```

## B-Tree Indexes (Default)

### When to Use
- Equality comparisons (`=`)
- Range queries (`<`, `>`, `BETWEEN`)
- Sorting (`ORDER BY`)
- `IS NULL` / `IS NOT NULL`
- Pattern matching with prefix (`LIKE 'abc%'`)

### Composite Index Column Order

```sql
-- Index on (a, b, c) supports:
-- ✓ WHERE a = 1
-- ✓ WHERE a = 1 AND b = 2
-- ✓ WHERE a = 1 AND b = 2 AND c = 3
-- ✓ WHERE a = 1 ORDER BY b
-- ✗ WHERE b = 2 (leading column not used)
-- ✗ WHERE c = 3

CREATE INDEX idx_orders ON orders(customer_id, status, created_at DESC);

-- This index supports:
-- WHERE customer_id = 123
-- WHERE customer_id = 123 AND status = 'pending'
-- WHERE customer_id = 123 ORDER BY status
-- WHERE customer_id = 123 AND status = 'pending' ORDER BY created_at DESC
```

### Index-Only Scans

```sql
-- If index covers all selected columns, no table access needed
CREATE INDEX idx_users_covering ON users(email) INCLUDE (name);

-- Query can use index-only scan:
SELECT email, name FROM users WHERE email = 'alice@example.com';
```

## GIN Indexes

### Arrays

```sql
CREATE INDEX idx_posts_tags ON posts USING gin(tags);

-- Queries that use the index:
SELECT * FROM posts WHERE tags @> ARRAY['postgresql'];  -- Contains
SELECT * FROM posts WHERE tags && ARRAY['sql', 'db'];   -- Overlaps
```

### JSONB

```sql
CREATE INDEX idx_users_metadata ON users USING gin(metadata);

-- Queries that use the index:
SELECT * FROM users WHERE metadata @> '{"role": "admin"}';
SELECT * FROM users WHERE metadata ? 'preferences';
SELECT * FROM users WHERE metadata ?& array['email', 'phone'];

-- Index specific path for equality queries
CREATE INDEX idx_users_role ON users((metadata->>'role'));
SELECT * FROM users WHERE metadata->>'role' = 'admin';
```

### Full-Text Search

```sql
-- Add tsvector column
ALTER TABLE posts ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B')
  ) STORED;

-- Create GIN index
CREATE INDEX idx_posts_search ON posts USING gin(search_vector);

-- Query
SELECT * FROM posts 
WHERE search_vector @@ to_tsquery('english', 'postgresql & tutorial');
```

## BRIN Indexes

Best for very large tables with naturally ordered data (time-series).

```sql
-- For append-only time-series data
CREATE INDEX idx_logs_time ON logs USING brin(created_at);

-- Much smaller than B-Tree for large tables
-- But only effective when data is physically ordered
```

### When to Use BRIN
- Tables with millions+ rows
- Data naturally ordered (timestamps, auto-increment IDs)
- Mostly append-only workloads
- Storage is a concern

## Partial Indexes

Index only a subset of rows.

```sql
-- Only active users
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;

-- Only recent orders
CREATE INDEX idx_recent_orders ON orders(customer_id) 
WHERE created_at > '2024-01-01';

-- Only non-null values
CREATE INDEX idx_users_phone ON users(phone) WHERE phone IS NOT NULL;
```

### Use Cases
- Filter on common WHERE condition
- Exclude frequently occurring values
- Index only relevant subset

## Expression Indexes

Index computed values.

```sql
-- Case-insensitive search
CREATE INDEX idx_users_lower_email ON users(lower(email));
SELECT * FROM users WHERE lower(email) = 'alice@example.com';

-- Date extraction
CREATE INDEX idx_orders_year ON orders(extract(year from created_at));
SELECT * FROM orders WHERE extract(year from created_at) = 2024;

-- JSON path
CREATE INDEX idx_users_country ON users((metadata->>'country'));
SELECT * FROM users WHERE metadata->>'country' = 'US';
```

## Index Maintenance

### Check Index Usage

```sql
-- Index usage statistics
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,        -- Times index used
  idx_tup_read,    -- Rows read from index
  idx_tup_fetch    -- Rows fetched from table
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT 
  schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public';
```

### Index Size

```sql
SELECT
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Reindex

```sql
-- Rebuild fragmented index
REINDEX INDEX idx_users_email;

-- Rebuild all indexes on table
REINDEX TABLE users;

-- Concurrent reindex (no lock)
REINDEX INDEX CONCURRENTLY idx_users_email;
```

### Analyze

```sql
-- Update statistics for query planner
ANALYZE users;

-- Full vacuum with analyze
VACUUM ANALYZE users;
```

## Anti-Patterns

### Don't Index
- Small tables (< 1000 rows)
- Low cardinality columns (boolean, status with few values)
- Columns rarely used in WHERE/JOIN/ORDER BY
- Frequently updated columns (high write overhead)

### Common Mistakes

```sql
-- ❌ Redundant: composite index covers single column
CREATE INDEX idx_a ON t(a);
CREATE INDEX idx_a_b ON t(a, b);  -- This covers WHERE a = x

-- ❌ Wrong order for query pattern
CREATE INDEX idx_b_a ON t(b, a);
-- Query: WHERE a = x ORDER BY b  -- Can't use index efficiently

-- ❌ Index won't be used (function on column)
CREATE INDEX idx_email ON users(email);
SELECT * FROM users WHERE lower(email) = 'alice@example.com';
-- Need: CREATE INDEX idx_lower_email ON users(lower(email));
```

## Index Strategy by Query Type

| Query Pattern | Index Strategy |
|---------------|----------------|
| `WHERE a = x` | B-Tree on (a) |
| `WHERE a = x AND b = y` | Composite B-Tree on (a, b) |
| `WHERE a = x ORDER BY b` | Composite B-Tree on (a, b) |
| `WHERE a IN (1,2,3)` | B-Tree on (a) |
| `WHERE a LIKE 'abc%'` | B-Tree on (a) |
| `WHERE tags @> ARRAY['x']` | GIN on tags |
| `WHERE data @> '{"k":"v"}'` | GIN on data (JSONB) |
| `WHERE search @@ query` | GIN on tsvector |
| Time-series range queries | BRIN on timestamp |

## Best Practices

1. **Always index foreign keys** - PostgreSQL doesn't auto-create them
2. **Index columns in WHERE clauses** - Most common optimization
3. **Consider column order** - Leftmost column should be most selective
4. **Use partial indexes** - When queries filter to subset
5. **Use CONCURRENTLY** - For production index creation
6. **Monitor usage** - Remove unused indexes
7. **Don't over-index** - Each index adds write overhead
8. **Analyze after bulk operations** - Keep statistics fresh
