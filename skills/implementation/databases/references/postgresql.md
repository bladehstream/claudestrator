# PostgreSQL Reference

PostgreSQL optimization, indexing, and advanced features for TypeScript applications.

## Query Optimization

### EXPLAIN ANALYZE

```sql
-- Basic explain
EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';

-- With actual execution stats
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'alice@example.com';

-- Verbose output with buffers
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) 
SELECT * FROM users WHERE email = 'alice@example.com';
```

### Reading EXPLAIN Output

```
Seq Scan on users  (cost=0.00..35.50 rows=10 width=244) (actual time=0.012..0.015 rows=1 loops=1)
  Filter: (email = 'alice@example.com'::text)
  Rows Removed by Filter: 999
Planning Time: 0.080 ms
Execution Time: 0.030 ms
```

Key indicators:
- **Seq Scan** - Full table scan (often bad for large tables)
- **Index Scan** - Using index efficiently
- **Index Only Scan** - Best case, data from index only
- **Bitmap Index Scan** - Multiple index conditions combined
- **cost** - Estimated startup..total cost
- **rows** - Estimated row count
- **actual time** - Real execution time
- **Rows Removed by Filter** - Rows scanned but filtered out

### Scan Types

| Scan Type | When Used | Performance |
|-----------|-----------|-------------|
| Seq Scan | No suitable index, small tables | Slow on large tables |
| Index Scan | Index exists, selective filter | Good |
| Index Only Scan | All columns in index | Best |
| Bitmap Index Scan | Multiple conditions, OR queries | Good for medium selectivity |

## Index Types

### B-Tree (Default)

```sql
-- Standard index
CREATE INDEX idx_users_email ON users(email);

-- Composite index (order matters!)
CREATE INDEX idx_posts_author_created ON posts(author_id, created_at DESC);

-- Unique index
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);

-- Partial index
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;

-- Concurrent creation (no locks)
CREATE INDEX CONCURRENTLY idx_users_name ON users(name);
```

Best for: Equality (`=`), range (`<`, `>`, `BETWEEN`), sorting, `IS NULL`

### Hash Index

```sql
CREATE INDEX idx_users_id_hash ON users USING hash(id);
```

Best for: Exact equality (`=`) only, slightly faster than B-tree for equality

### GIN (Generalized Inverted Index)

```sql
-- Array containment
CREATE INDEX idx_posts_tags ON posts USING gin(tags);

-- JSONB
CREATE INDEX idx_users_metadata ON users USING gin(metadata);

-- Full-text search
CREATE INDEX idx_posts_search ON posts USING gin(to_tsvector('english', title || ' ' || content));
```

Best for: Arrays, JSONB, full-text search, `@>`, `<@`, `?`, `?&`, `?|`

### GiST (Generalized Search Tree)

```sql
-- PostGIS geometry
CREATE INDEX idx_locations_geom ON locations USING gist(geom);

-- Range types
CREATE INDEX idx_events_during ON events USING gist(during);
```

Best for: Spatial data, range types, geometric operations

### BRIN (Block Range Index)

```sql
-- Time-series data (naturally ordered)
CREATE INDEX idx_logs_created ON logs USING brin(created_at);
```

Best for: Very large tables with naturally ordered data, time-series

## Index Strategy

### When to Create Indexes

1. **Primary keys** - Auto-created
2. **Foreign keys** - Always index manually
3. **Unique constraints** - Auto-created
4. **WHERE clause columns** - Frequently filtered
5. **JOIN columns** - Used in joins
6. **ORDER BY columns** - Frequently sorted

### When NOT to Create Indexes

1. **Small tables** - Seq scan is faster
2. **Low cardinality** - Boolean, status columns
3. **Frequently updated columns** - Index maintenance overhead
4. **Already covered** - Composite index covers leftmost columns

### Composite Index Order

```sql
-- This index covers queries filtering on:
-- (author_id), (author_id, created_at), (author_id, created_at, status)
-- But NOT: (created_at), (status), (created_at, status)
CREATE INDEX idx_posts_compound ON posts(author_id, created_at DESC, status);
```

## Analyzing & Maintenance

```sql
-- Update statistics
ANALYZE users;

-- Full vacuum (reclaim space, update stats)
VACUUM ANALYZE users;

-- Reindex (rebuild fragmented indexes)
REINDEX INDEX idx_users_email;
REINDEX TABLE users;

-- Check index usage
SELECT 
  schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT 
  schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND schemaname = 'public';
```

## JSONB Operations

```sql
-- Create table with JSONB
CREATE TABLE events (
  id SERIAL PRIMARY KEY,
  data JSONB NOT NULL
);

-- Insert
INSERT INTO events (data) VALUES ('{"type": "click", "x": 100, "y": 200}');

-- Query operators
SELECT * FROM events WHERE data->>'type' = 'click';           -- Text extraction
SELECT * FROM events WHERE data->'position'->>'x' = '100';    -- Nested
SELECT * FROM events WHERE data @> '{"type": "click"}';       -- Containment
SELECT * FROM events WHERE data ? 'type';                     -- Key exists
SELECT * FROM events WHERE data ?& array['type', 'x'];        -- All keys exist
SELECT * FROM events WHERE data ?| array['type', 'click'];    -- Any key exists

-- GIN index for JSONB
CREATE INDEX idx_events_data ON events USING gin(data);

-- Index specific path
CREATE INDEX idx_events_type ON events ((data->>'type'));
```

## Full-Text Search

```sql
-- Add tsvector column
ALTER TABLE posts ADD COLUMN search_vector tsvector;

-- Populate search vector
UPDATE posts SET search_vector = 
  setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
  setweight(to_tsvector('english', coalesce(content, '')), 'B');

-- Create GIN index
CREATE INDEX idx_posts_search ON posts USING gin(search_vector);

-- Search
SELECT * FROM posts 
WHERE search_vector @@ to_tsquery('english', 'postgresql & tutorial');

-- With ranking
SELECT *, ts_rank(search_vector, query) AS rank
FROM posts, to_tsquery('english', 'postgresql | database') query
WHERE search_vector @@ query
ORDER BY rank DESC;
```

## Common Table Expressions (CTEs)

```sql
-- Basic CTE
WITH active_users AS (
  SELECT * FROM users WHERE is_active = true
)
SELECT u.*, COUNT(p.id) as post_count
FROM active_users u
LEFT JOIN posts p ON u.id = p.author_id
GROUP BY u.id;

-- Recursive CTE (hierarchical data)
WITH RECURSIVE category_tree AS (
  -- Base case
  SELECT id, name, parent_id, 1 as depth
  FROM categories
  WHERE parent_id IS NULL
  
  UNION ALL
  
  -- Recursive case
  SELECT c.id, c.name, c.parent_id, ct.depth + 1
  FROM categories c
  JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY depth, name;
```

## Window Functions

```sql
-- Row number
SELECT 
  *,
  ROW_NUMBER() OVER (ORDER BY created_at DESC) as row_num
FROM posts;

-- Rank with partitioning
SELECT 
  *,
  RANK() OVER (PARTITION BY author_id ORDER BY views DESC) as author_rank
FROM posts;

-- Running total
SELECT 
  date,
  amount,
  SUM(amount) OVER (ORDER BY date) as running_total
FROM transactions;

-- Moving average
SELECT 
  date,
  amount,
  AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg_7d
FROM daily_stats;
```

## Performance Configuration

### Key Settings

```sql
-- View current settings
SHOW shared_buffers;
SHOW work_mem;
SHOW effective_cache_size;

-- Recommended starting points (adjust based on RAM)
-- shared_buffers: 25% of RAM (e.g., 4GB for 16GB RAM)
-- effective_cache_size: 75% of RAM
-- work_mem: RAM / max_connections / 4 (e.g., 64MB)
-- maintenance_work_mem: 512MB-2GB for VACUUM/CREATE INDEX
```

### Slow Query Logging

```sql
-- postgresql.conf
log_min_duration_statement = 1000  -- Log queries > 1 second
log_statement = 'all'              -- Log all statements (dev only)
```

## Useful Queries

### Table Sizes

```sql
SELECT 
  relname as table_name,
  pg_size_pretty(pg_table_size(relid)) as table_size,
  pg_size_pretty(pg_indexes_size(relid)) as index_size,
  pg_size_pretty(pg_total_relation_size(relid)) as total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Active Connections

```sql
SELECT 
  pid, usename, application_name, client_addr, 
  state, query_start, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;
```

### Kill Long-Running Queries

```sql
-- Cancel query (graceful)
SELECT pg_cancel_backend(pid);

-- Terminate connection (force)
SELECT pg_terminate_backend(pid);
```

### Lock Monitoring

```sql
SELECT 
  blocked_locks.pid AS blocked_pid,
  blocked_activity.usename AS blocked_user,
  blocking_locks.pid AS blocking_pid,
  blocking_activity.usename AS blocking_user,
  blocked_activity.query AS blocked_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted AND blocking_locks.granted;
```

## Best Practices

1. **Always EXPLAIN ANALYZE** - Before optimizing, measure
2. **Index foreign keys** - PostgreSQL doesn't auto-index them
3. **Use CONCURRENTLY** - For index creation on live tables
4. **Partial indexes** - When filtering on subset of data
5. **VACUUM regularly** - Configure autovacuum appropriately
6. **Monitor pg_stat_user_indexes** - Remove unused indexes
7. **Connection pooling** - Use PgBouncer for high concurrency
8. **JSONB over JSON** - Binary format is faster
