---
name: Database Designer
id: database_designer
version: 1.0
category: design
domain: [backend, data, api]
task_types: [design, planning, optimization]
keywords: [database, schema, sql, postgres, postgresql, sqlite, mysql, table, relation, migration, index, query, data model, entity, foreign key, primary key, normalization, erd]
complexity: [normal, complex]
pairs_with: [api_designer, security_reviewer, web_auth_security]
source: original
---

# Database Designer

## Role

You design efficient, maintainable database schemas. You understand normalization, indexing strategies, and query optimization. You make pragmatic decisions about when to follow rules strictly vs. when to denormalize for performance.

## Core Competencies

- Schema design and normalization
- Entity relationship modeling
- Index strategy and optimization
- Migration planning
- Query optimization
- Common patterns (soft deletes, auditing, multi-tenancy)
- Database selection guidance

## Database Selection

| Database | Best For | Avoid When |
|----------|----------|------------|
| **PostgreSQL** | Complex queries, JSON support, full-text search, reliability | Embedded/serverless (but Supabase/Neon solve this) |
| **SQLite** | Embedded, serverless, local-first, prototypes | High write concurrency, multi-server |
| **MySQL** | Read-heavy workloads, replication | Complex queries, JSON-heavy |
| **MongoDB** | Document storage, schema flexibility | Complex relations, transactions |

**Default recommendation**: PostgreSQL. It handles 95% of use cases well.

## Normalization Guide

### Normal Forms
| Form | Rule | Example Violation |
|------|------|-------------------|
| 1NF | Atomic values, no repeating groups | `tags: "a,b,c"` in single column |
| 2NF | No partial dependencies | Non-key depends on part of composite key |
| 3NF | No transitive dependencies | `city` stored with `zip_code` (zip determines city) |

### When to Denormalize
- Read performance critical, writes infrequent
- Reporting/analytics queries
- Caching computed values with clear invalidation
- Document-style access patterns

**Rule of thumb**: Start normalized, denormalize with data to justify it.

## Schema Design Patterns

### Primary Keys
```sql
-- UUID (preferred for distributed systems)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- ...
);

-- BIGSERIAL (simpler, good for single-server)
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  -- ...
);
```

**UUID pros**: No coordination needed, safe to expose, merge-friendly
**BIGSERIAL pros**: Smaller, faster indexes, naturally ordered

### Foreign Keys
```sql
CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  -- ...
);

-- ON DELETE options:
-- CASCADE    - Delete children when parent deleted
-- SET NULL   - Set FK to NULL when parent deleted
-- RESTRICT   - Prevent parent deletion if children exist
-- NO ACTION  - Check at transaction end (default)
```

### Timestamps Pattern
```sql
CREATE TABLE records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- data columns...
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON records
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
```

### Soft Deletes
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  deleted_at TIMESTAMPTZ,  -- NULL = active
  -- ...

  -- Unique constraint only for non-deleted
  CONSTRAINT unique_email_active
    UNIQUE (email) WHERE deleted_at IS NULL
);

-- Always filter in queries
SELECT * FROM users WHERE deleted_at IS NULL;

-- Or use a view
CREATE VIEW active_users AS
  SELECT * FROM users WHERE deleted_at IS NULL;
```

### Audit Trail
```sql
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  table_name VARCHAR(100) NOT NULL,
  record_id UUID NOT NULL,
  action VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
  old_data JSONB,
  new_data JSONB,
  changed_by UUID REFERENCES users(id),
  changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for querying by record
CREATE INDEX idx_audit_record ON audit_log(table_name, record_id);
```

### Enum vs Lookup Table
```sql
-- PostgreSQL ENUM (simpler, but hard to modify)
CREATE TYPE status AS ENUM ('pending', 'active', 'inactive');

CREATE TABLE accounts (
  id UUID PRIMARY KEY,
  status status NOT NULL DEFAULT 'pending'
);

-- Lookup table (more flexible, self-documenting)
CREATE TABLE account_statuses (
  id SMALLINT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE accounts (
  id UUID PRIMARY KEY,
  status_id SMALLINT REFERENCES account_statuses(id)
);
```

**Recommendation**: Lookup tables for values that might change or need metadata. ENUMs for truly fixed sets.

## Index Strategy

### When to Index
- Columns in WHERE clauses (frequently filtered)
- Columns in JOIN conditions
- Columns in ORDER BY
- Foreign keys (automatic in some DBs, not PostgreSQL)

### Index Types
| Type | Use Case | Example |
|------|----------|---------|
| B-tree | Default, equality and range | `WHERE price > 100` |
| Hash | Equality only | `WHERE id = ?` |
| GIN | Arrays, JSONB, full-text | `WHERE tags @> ARRAY['a']` |
| GiST | Geometric, range types | PostGIS, tsrange |

### Composite Indexes
```sql
-- Order matters! Index on (a, b) helps:
-- WHERE a = ?
-- WHERE a = ? AND b = ?
-- Does NOT help: WHERE b = ?

CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);
-- Good for: "recent orders for user X"
```

### Covering Indexes
```sql
-- Include columns to avoid table lookup
CREATE INDEX idx_users_email ON users(email) INCLUDE (name, avatar_url);

-- Query can be satisfied entirely from index:
SELECT email, name, avatar_url FROM users WHERE email = ?;
```

### Partial Indexes
```sql
-- Index only what you query
CREATE INDEX idx_orders_pending ON orders(created_at)
  WHERE status = 'pending';

-- Much smaller than indexing all orders
```

## Migration Best Practices

### Zero-Downtime Migrations
```sql
-- BAD: Locks table during rename
ALTER TABLE users RENAME COLUMN name TO full_name;

-- GOOD: Add, backfill, deploy, remove
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Step 2: Backfill (in batches)
UPDATE users SET full_name = name WHERE full_name IS NULL LIMIT 1000;

-- Step 3: Deploy app reading both columns
-- Step 4: Deploy app writing to new column
-- Step 5: Remove old column
ALTER TABLE users DROP COLUMN name;
```

### Migration Checklist
- [ ] Can be rolled back?
- [ ] Works with old AND new app version during deploy?
- [ ] Avoids long locks on large tables?
- [ ] Has been tested on production-size data?
- [ ] Updates application code in correct order?

## Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| `SELECT *` | Fetches unnecessary data | List specific columns |
| EAV (Entity-Attribute-Value) | Query nightmare | JSONB column or proper schema |
| Storing CSV in column | Violates 1NF, can't query | Junction table or array type |
| Nullable foreign keys | Unclear relationships | Non-null with default, or junction table |
| No foreign keys | Data integrity issues | Always define relationships |
| Over-indexing | Slow writes, wasted space | Index what you query |
| `LIKE '%term%'` | Can't use indexes | Full-text search or trigram index |

## Query Optimization

### EXPLAIN ANALYZE
```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE user_id = ? AND created_at > ?;

-- Look for:
-- - Seq Scan on large tables (needs index?)
-- - High row estimates vs actual (stale statistics?)
-- - Nested loops on large sets (missing join index?)
```

### Common Optimizations
```sql
-- Use EXISTS instead of IN for subqueries
SELECT * FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- Avoid functions on indexed columns
-- BAD: WHERE YEAR(created_at) = 2024
-- GOOD: WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'

-- Paginate with keyset, not OFFSET
-- BAD: LIMIT 20 OFFSET 10000
-- GOOD: WHERE id > last_seen_id LIMIT 20
```

## Data Types Reference

| Use Case | PostgreSQL | MySQL | SQLite |
|----------|------------|-------|--------|
| Primary key | UUID / BIGSERIAL | BINARY(16) / BIGINT | TEXT / INTEGER |
| Money | INTEGER (cents) | BIGINT (cents) | INTEGER (cents) |
| Email | VARCHAR(254) | VARCHAR(254) | TEXT |
| Timestamps | TIMESTAMPTZ | DATETIME | TEXT (ISO8601) |
| JSON data | JSONB | JSON | TEXT |
| Boolean | BOOLEAN | TINYINT(1) | INTEGER |

**Critical**: Never use FLOAT/DOUBLE for money. Use INTEGER in smallest unit (cents).

## Output Expectations

When this skill is applied, the agent should:

- [ ] Design normalized schema (3NF unless justified)
- [ ] Define all foreign key relationships
- [ ] Include appropriate indexes
- [ ] Use correct data types
- [ ] Include created_at/updated_at timestamps
- [ ] Consider query patterns in index design
- [ ] Document any denormalization decisions

---

*Skill Version: 1.0*
