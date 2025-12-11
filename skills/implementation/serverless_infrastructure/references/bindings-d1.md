# Cloudflare D1 Database Bindings

Serverless SQLite database with automatic read replication. Ideal for relational data, complex queries, and ACID transactions.

## Overview

| Characteristic | Value |
|----------------|-------|
| **Database engine** | SQLite |
| **Max database size** | 10 GB |
| **Max rows per query** | 10,000 (configurable) |
| **Max statement size** | 100 KB |
| **Replication** | Automatic read replicas globally |
| **Consistency** | Strong for writes, eventual for reads |

## Configuration

### wrangler.toml
```toml
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### Create Database
```bash
# Create new database
npx wrangler d1 create my-database

# List databases
npx wrangler d1 list
```

## Basic Operations

### TypeScript Types
```typescript
interface Env {
  DB: D1Database;
}
```

### Query Methods
```typescript
// Execute single statement (returns metadata only)
const result = await c.env.DB.exec('CREATE TABLE users (id INTEGER PRIMARY KEY)');

// Prepared statement - single row
const user = await c.env.DB.prepare(
  'SELECT * FROM users WHERE id = ?'
).bind(userId).first<User>();

// Prepared statement - all rows
const users = await c.env.DB.prepare(
  'SELECT * FROM users WHERE status = ?'
).bind('active').all<User>();

// Prepared statement - raw results
const { results, success, meta } = await c.env.DB.prepare(
  'SELECT * FROM users'
).all();

// Run (for INSERT/UPDATE/DELETE)
const { meta } = await c.env.DB.prepare(
  'INSERT INTO users (email, name) VALUES (?, ?)'
).bind(email, name).run();

console.log(meta.changes); // Rows affected
console.log(meta.last_row_id); // Last inserted ID
```

### Batch Operations
```typescript
// Execute multiple statements in a transaction
const results = await c.env.DB.batch([
  c.env.DB.prepare('INSERT INTO users (email) VALUES (?)').bind('a@example.com'),
  c.env.DB.prepare('INSERT INTO users (email) VALUES (?)').bind('b@example.com'),
  c.env.DB.prepare('SELECT COUNT(*) as count FROM users'),
]);

// All succeed or all fail (automatic transaction)
```

## Migrations

### Create Migration
```bash
# Create new migration file
npx wrangler d1 migrations create my-database init
# Creates: migrations/0001_init.sql
```

### Migration File Structure
```
migrations/
├── 0001_init.sql
├── 0002_add_users.sql
└── 0003_add_posts.sql
```

### Example Migration
```sql
-- migrations/0001_init.sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_email ON users(email);

CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  content TEXT,
  published BOOLEAN DEFAULT FALSE,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_posts_user ON posts(user_id);
CREATE INDEX idx_posts_published ON posts(published) WHERE published = TRUE;
```

### Run Migrations
```bash
# Local development
npx wrangler d1 migrations apply my-database --local

# Production
npx wrangler d1 migrations apply my-database --remote

# Check status
npx wrangler d1 migrations list my-database
```

## Query Patterns

### Type-Safe Queries
```typescript
interface User {
  id: number;
  email: string;
  name: string | null;
  created_at: string;
}

// Type the result
const user = await env.DB.prepare(
  'SELECT * FROM users WHERE id = ?'
).bind(userId).first<User>();

if (!user) {
  throw new Error('User not found');
}
// user is typed as User
```

### Parameterized Queries (REQUIRED)
```typescript
// CORRECT: Use parameterized queries
const user = await env.DB.prepare(
  'SELECT * FROM users WHERE email = ?'
).bind(email).first();

// WRONG: SQL injection vulnerability!
const user = await env.DB.prepare(
  `SELECT * FROM users WHERE email = '${email}'`
).first();
```

### Named Parameters
```typescript
// SQLite supports :name, @name, and $name
const user = await env.DB.prepare(
  'SELECT * FROM users WHERE email = :email AND status = :status'
).bind({ email: 'test@example.com', status: 'active' }).first();
```

### Pagination
```typescript
interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

async function paginateUsers(
  env: Env,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResult<User>> {
  const offset = (page - 1) * pageSize;
  
  const [users, countResult] = await env.DB.batch([
    env.DB.prepare(
      'SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?'
    ).bind(pageSize, offset),
    env.DB.prepare('SELECT COUNT(*) as total FROM users'),
  ]);
  
  const total = (countResult.results[0] as { total: number }).total;
  
  return {
    data: users.results as User[],
    total,
    page,
    pageSize,
    hasMore: offset + pageSize < total,
  };
}
```

### Search with LIKE
```typescript
async function searchUsers(env: Env, query: string): Promise<User[]> {
  // Escape special characters and add wildcards
  const searchTerm = `%${query.replace(/[%_]/g, '\\$&')}%`;
  
  const { results } = await env.DB.prepare(
    `SELECT * FROM users 
     WHERE name LIKE ? ESCAPE '\\' 
        OR email LIKE ? ESCAPE '\\'
     ORDER BY name
     LIMIT 50`
  ).bind(searchTerm, searchTerm).all<User>();
  
  return results;
}
```

### Upsert Pattern
```typescript
async function upsertUser(env: Env, email: string, name: string): Promise<User> {
  const { results } = await env.DB.prepare(`
    INSERT INTO users (email, name, updated_at)
    VALUES (?, ?, datetime('now'))
    ON CONFLICT(email) DO UPDATE SET
      name = excluded.name,
      updated_at = datetime('now')
    RETURNING *
  `).bind(email, name).all<User>();
  
  return results[0];
}
```

### Soft Delete
```typescript
async function softDeleteUser(env: Env, userId: number): Promise<void> {
  await env.DB.prepare(`
    UPDATE users 
    SET deleted_at = datetime('now')
    WHERE id = ?
  `).bind(userId).run();
}

// Query active users only
async function getActiveUsers(env: Env): Promise<User[]> {
  const { results } = await env.DB.prepare(
    'SELECT * FROM users WHERE deleted_at IS NULL'
  ).all<User>();
  return results;
}
```

### Transactions with batch()
```typescript
async function transferCredits(
  env: Env,
  fromId: number,
  toId: number,
  amount: number
): Promise<void> {
  await env.DB.batch([
    env.DB.prepare(
      'UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?'
    ).bind(amount, fromId, amount),
    env.DB.prepare(
      'UPDATE accounts SET balance = balance + ? WHERE id = ?'
    ).bind(amount, toId),
    env.DB.prepare(
      'INSERT INTO transfers (from_id, to_id, amount) VALUES (?, ?, ?)'
    ).bind(fromId, toId, amount),
  ]);
  // All statements succeed or all fail
}
```

## Repository Pattern

```typescript
// repositories/user-repository.ts
export class UserRepository {
  constructor(private db: D1Database) {}

  async findById(id: number): Promise<User | null> {
    return this.db.prepare(
      'SELECT * FROM users WHERE id = ? AND deleted_at IS NULL'
    ).bind(id).first<User>();
  }

  async findByEmail(email: string): Promise<User | null> {
    return this.db.prepare(
      'SELECT * FROM users WHERE email = ? AND deleted_at IS NULL'
    ).bind(email).first<User>();
  }

  async create(data: CreateUserInput): Promise<User> {
    const { results } = await this.db.prepare(`
      INSERT INTO users (email, name)
      VALUES (?, ?)
      RETURNING *
    `).bind(data.email, data.name).all<User>();
    return results[0];
  }

  async update(id: number, data: UpdateUserInput): Promise<User | null> {
    const sets: string[] = [];
    const values: unknown[] = [];

    if (data.name !== undefined) {
      sets.push('name = ?');
      values.push(data.name);
    }
    if (data.email !== undefined) {
      sets.push('email = ?');
      values.push(data.email);
    }

    if (sets.length === 0) return this.findById(id);

    sets.push("updated_at = datetime('now')");
    values.push(id);

    const { results } = await this.db.prepare(`
      UPDATE users SET ${sets.join(', ')}
      WHERE id = ? AND deleted_at IS NULL
      RETURNING *
    `).bind(...values).all<User>();

    return results[0] || null;
  }

  async delete(id: number): Promise<boolean> {
    const { meta } = await this.db.prepare(`
      UPDATE users SET deleted_at = datetime('now')
      WHERE id = ? AND deleted_at IS NULL
    `).bind(id).run();
    return meta.changes > 0;
  }
}

// Usage in Hono
app.get('/users/:id', async (c) => {
  const repo = new UserRepository(c.env.DB);
  const user = await repo.findById(Number(c.req.param('id')));
  if (!user) return c.json({ error: 'Not found' }, 404);
  return c.json(user);
});
```

## Performance Optimization

### Indexes
```sql
-- Single column index
CREATE INDEX idx_users_email ON users(email);

-- Composite index (order matters!)
CREATE INDEX idx_posts_user_date ON posts(user_id, created_at DESC);

-- Partial index (only index some rows)
CREATE INDEX idx_posts_published ON posts(published) WHERE published = TRUE;

-- Covering index (includes all needed columns)
CREATE INDEX idx_users_lookup ON users(email, name, status);
```

### Query Analysis
```bash
# Explain query plan
npx wrangler d1 execute my-database --command "EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = 'test@example.com'"
```

### Batch Inserts
```typescript
// EFFICIENT: Batch multiple inserts
async function bulkCreateUsers(env: Env, users: CreateUserInput[]): Promise<void> {
  const statements = users.map(user =>
    env.DB.prepare('INSERT INTO users (email, name) VALUES (?, ?)')
      .bind(user.email, user.name)
  );
  
  // Process in chunks of 100 (D1 limit)
  for (let i = 0; i < statements.length; i += 100) {
    await env.DB.batch(statements.slice(i, i + 100));
  }
}
```

### Read Replicas
```typescript
// D1 automatically uses read replicas for SELECT queries
// No configuration needed - just query normally

// Force read from primary (for consistency after write)
const user = await env.DB.prepare(
  'SELECT * FROM users WHERE id = ?'
).bind(userId).first<User>();
// After insert, you might want a small delay for replica sync
```

## Error Handling

```typescript
import { HTTPException } from 'hono/http-exception';

async function createUser(env: Env, data: CreateUserInput): Promise<User> {
  try {
    const { results } = await env.DB.prepare(`
      INSERT INTO users (email, name) VALUES (?, ?)
      RETURNING *
    `).bind(data.email, data.name).all<User>();
    return results[0];
  } catch (error) {
    if (error instanceof Error) {
      // SQLite UNIQUE constraint violation
      if (error.message.includes('UNIQUE constraint failed')) {
        throw new HTTPException(409, { message: 'Email already exists' });
      }
      // Foreign key constraint
      if (error.message.includes('FOREIGN KEY constraint failed')) {
        throw new HTTPException(400, { message: 'Invalid reference' });
      }
    }
    throw error;
  }
}
```

## Testing

### Local Development
```bash
# Run with local D1
npx wrangler dev --local --persist-to=.wrangler/state

# Execute SQL locally
npx wrangler d1 execute my-database --local --file=./seed.sql

# Interactive SQL shell
npx wrangler d1 execute my-database --local --command "SELECT * FROM users"
```

### Seed Data
```sql
-- seed.sql
INSERT INTO users (email, name) VALUES 
  ('alice@example.com', 'Alice'),
  ('bob@example.com', 'Bob'),
  ('charlie@example.com', 'Charlie');

INSERT INTO posts (user_id, title, content, published) VALUES
  (1, 'First Post', 'Hello World', TRUE),
  (1, 'Draft Post', 'Work in progress', FALSE);
```

```bash
# Run seed
npx wrangler d1 execute my-database --local --file=./seed.sql
```

## SQLite-Specific Features

### JSON Support
```typescript
// Store JSON in TEXT column
await env.DB.prepare(`
  INSERT INTO settings (user_id, preferences)
  VALUES (?, json(?))
`).bind(userId, JSON.stringify(preferences)).run();

// Query JSON fields
const { results } = await env.DB.prepare(`
  SELECT id, json_extract(preferences, '$.theme') as theme
  FROM settings
  WHERE json_extract(preferences, '$.notifications') = true
`).all();
```

### Date/Time
```sql
-- Current timestamp
SELECT datetime('now');
SELECT datetime('now', 'localtime');

-- Date arithmetic
SELECT datetime('now', '+7 days');
SELECT datetime('now', '-1 month');

-- Extract parts
SELECT strftime('%Y', created_at) as year FROM posts;
```

### Window Functions
```typescript
// Rank users by post count
const { results } = await env.DB.prepare(`
  SELECT 
    u.id,
    u.name,
    COUNT(p.id) as post_count,
    RANK() OVER (ORDER BY COUNT(p.id) DESC) as rank
  FROM users u
  LEFT JOIN posts p ON p.user_id = u.id
  GROUP BY u.id
  ORDER BY rank
`).all();
```

## Best Practices

1. **Always use parameterized queries** - Never concatenate user input
2. **Create indexes for query patterns** - Check EXPLAIN QUERY PLAN
3. **Use batch() for multiple operations** - Automatic transaction
4. **Design for eventual consistency** - Read replicas may lag slightly
5. **Use RETURNING for insert/update** - Avoid extra query
6. **Implement soft deletes** - Use deleted_at column
7. **Keep migrations small** - One logical change per file
8. **Use typed results** - Always specify `<Type>` on queries
