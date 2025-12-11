# SQL Injection Prevention

Protect database queries from injection attacks using parameterized queries and ORM best practices.

## The Vulnerability

SQL injection occurs when user input is directly concatenated into SQL queries, allowing attackers to manipulate query logic.

### Vulnerable Code
```typescript
// NEVER DO THIS - SQL Injection vulnerability
const email = req.query.email;
const query = `SELECT * FROM users WHERE email = '${email}'`;

// Attacker input: ' OR '1'='1
// Resulting query: SELECT * FROM users WHERE email = '' OR '1'='1'
// Returns ALL users!

// Worse: '; DROP TABLE users; --
// Could delete your entire table
```

## Parameterized Queries

The primary defense against SQL injection is parameterized queries (also called prepared statements).

### D1 (Cloudflare)
```typescript
// CORRECT: Parameterized query with D1
const user = await env.DB.prepare(
  'SELECT * FROM users WHERE email = ?'
).bind(email).first<User>();

// Multiple parameters
const user = await env.DB.prepare(
  'SELECT * FROM users WHERE email = ? AND status = ?'
).bind(email, 'active').first<User>();

// Named parameters (SQLite style)
const user = await env.DB.prepare(
  'SELECT * FROM users WHERE email = :email AND status = :status'
).bind({ email, status: 'active' }).first<User>();
```

### PostgreSQL (node-postgres)
```typescript
import { Pool } from 'pg';

const pool = new Pool();

// Parameterized query
const result = await pool.query(
  'SELECT * FROM users WHERE email = $1 AND status = $2',
  [email, 'active']
);

// Named parameters with pg-named
const result = await pool.query(
  'SELECT * FROM users WHERE email = :email',
  { email }
);
```

### MySQL (mysql2)
```typescript
import mysql from 'mysql2/promise';

const connection = await mysql.createConnection(process.env.DATABASE_URL);

// Parameterized query
const [rows] = await connection.execute(
  'SELECT * FROM users WHERE email = ? AND status = ?',
  [email, 'active']
);

// Named placeholders
const [rows] = await connection.execute(
  'SELECT * FROM users WHERE email = :email',
  { email }
);
```

## ORM Security

ORMs provide an additional layer of protection by abstracting SQL queries.

### Drizzle ORM
```typescript
import { eq, and } from 'drizzle-orm';
import { users } from './schema';

// Safe: Drizzle handles parameterization
const user = await db
  .select()
  .from(users)
  .where(eq(users.email, email))
  .get();

// Multiple conditions
const user = await db
  .select()
  .from(users)
  .where(and(
    eq(users.email, email),
    eq(users.status, 'active')
  ))
  .get();

// DANGEROUS: Raw SQL without parameters
// Only use when absolutely necessary
const result = await db.run(sql`
  SELECT * FROM users WHERE email = ${email}
`);
// The sql`` template tag handles escaping
```

### Prisma
```typescript
// Safe: Prisma handles parameterization
const user = await prisma.user.findUnique({
  where: { email },
});

// Safe: Complex queries
const users = await prisma.user.findMany({
  where: {
    email: { contains: searchTerm },
    status: 'active',
  },
});

// DANGEROUS: Raw queries - use parameterization
const result = await prisma.$queryRaw`
  SELECT * FROM users WHERE email = ${email}
`;
// Prisma's template tag handles escaping
```

## Dynamic Queries

When you need to build queries dynamically, be extra careful.

### Safe Dynamic Column Selection
```typescript
// Allowlist approach - SAFE
const ALLOWED_COLUMNS = ['id', 'email', 'name', 'created_at'] as const;
type AllowedColumn = typeof ALLOWED_COLUMNS[number];

function isAllowedColumn(col: string): col is AllowedColumn {
  return ALLOWED_COLUMNS.includes(col as AllowedColumn);
}

app.get('/users', async (c) => {
  const sortBy = c.req.query('sortBy') || 'created_at';
  
  // Validate column name against allowlist
  if (!isAllowedColumn(sortBy)) {
    return c.json({ error: 'Invalid sort column' }, 400);
  }
  
  // Safe to use in query since it's validated
  const users = await c.env.DB.prepare(
    `SELECT * FROM users ORDER BY ${sortBy} DESC`
  ).all();
  
  return c.json(users.results);
});
```

### Safe Dynamic WHERE Clauses
```typescript
interface FilterOptions {
  email?: string;
  status?: string;
  role?: string;
}

async function findUsers(db: D1Database, filters: FilterOptions) {
  const conditions: string[] = [];
  const params: unknown[] = [];
  
  if (filters.email) {
    conditions.push('email = ?');
    params.push(filters.email);
  }
  
  if (filters.status) {
    conditions.push('status = ?');
    params.push(filters.status);
  }
  
  if (filters.role) {
    conditions.push('role = ?');
    params.push(filters.role);
  }
  
  const whereClause = conditions.length > 0
    ? `WHERE ${conditions.join(' AND ')}`
    : '';
  
  const query = `SELECT * FROM users ${whereClause}`;
  
  // Bind all parameters safely
  let stmt = db.prepare(query);
  for (const param of params) {
    stmt = stmt.bind(param);
  }
  
  return stmt.all();
}
```

### Safe LIKE Queries
```typescript
// Escape special LIKE characters
function escapeLike(str: string): string {
  return str.replace(/[%_\\]/g, '\\$&');
}

app.get('/search', async (c) => {
  const query = c.req.query('q') || '';
  
  // Escape and add wildcards
  const searchTerm = `%${escapeLike(query)}%`;
  
  const results = await c.env.DB.prepare(
    `SELECT * FROM users WHERE name LIKE ? ESCAPE '\\'`
  ).bind(searchTerm).all();
  
  return c.json(results.results);
});
```

## Batch Operations

### Safe Batch Inserts
```typescript
async function batchInsertUsers(db: D1Database, users: CreateUser[]) {
  const statements = users.map(user =>
    db.prepare(
      'INSERT INTO users (email, name, role) VALUES (?, ?, ?)'
    ).bind(user.email, user.name, user.role)
  );
  
  // D1 batch executes in a transaction
  return db.batch(statements);
}
```

### Safe Bulk Updates
```typescript
async function updateUserStatuses(
  db: D1Database,
  userIds: string[],
  status: string
) {
  // Create parameterized placeholders
  const placeholders = userIds.map(() => '?').join(', ');
  
  const query = `
    UPDATE users 
    SET status = ?, updated_at = datetime('now')
    WHERE id IN (${placeholders})
  `;
  
  // First param is status, rest are IDs
  let stmt = db.prepare(query).bind(status);
  for (const id of userIds) {
    stmt = stmt.bind(id);
  }
  
  return stmt.run();
}
```

## Common Mistakes

### Mistake 1: String Interpolation
```typescript
// WRONG
const query = `SELECT * FROM users WHERE id = ${userId}`;

// CORRECT
const query = 'SELECT * FROM users WHERE id = ?';
db.prepare(query).bind(userId);
```

### Mistake 2: Manual Escaping
```typescript
// WRONG - Don't try to escape manually
const safeEmail = email.replace(/'/g, "''");
const query = `SELECT * FROM users WHERE email = '${safeEmail}'`;

// CORRECT - Use parameterized queries
const query = 'SELECT * FROM users WHERE email = ?';
db.prepare(query).bind(email);
```

### Mistake 3: Dynamic Table Names
```typescript
// DANGEROUS - Table name from user input
const table = req.query.table;
const query = `SELECT * FROM ${table}`;

// SAFER - Allowlist tables
const ALLOWED_TABLES = ['users', 'posts', 'comments'];
if (!ALLOWED_TABLES.includes(table)) {
  throw new Error('Invalid table');
}
const query = `SELECT * FROM ${table}`;
```

### Mistake 4: Trusting ORM Completely
```typescript
// DANGEROUS - Raw query without proper escaping
const result = await prisma.$executeRawUnsafe(
  `SELECT * FROM users WHERE email = '${email}'`
);

// CORRECT - Use template literal for escaping
const result = await prisma.$executeRaw`
  SELECT * FROM users WHERE email = ${email}
`;
```

## Testing for SQL Injection

### Common Payloads to Test
```
' OR '1'='1
' OR '1'='1' --
'; DROP TABLE users; --
' UNION SELECT username, password FROM users --
1; SELECT * FROM users
' AND 1=CONVERT(int, @@version) --
```

### Automated Testing
```bash
# Using sqlmap for testing
sqlmap -u "http://localhost:8787/api/users?email=test" --batch

# Using OWASP ZAP
# Point ZAP at your API and run active scan
```

## Defense in Depth

Even with parameterized queries, add additional layers:

### 1. Input Validation
```typescript
import { z } from 'zod';

const UserIdSchema = z.string().uuid();
const EmailSchema = z.string().email().max(255);

// Validate before query
const validatedId = UserIdSchema.parse(userId);
```

### 2. Least Privilege Database User
```sql
-- Create read-only user for queries
CREATE USER api_reader WITH PASSWORD 'xxx';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO api_reader;

-- Create writer for mutations
CREATE USER api_writer WITH PASSWORD 'xxx';
GRANT SELECT, INSERT, UPDATE ON users, posts TO api_writer;
-- No DELETE or DROP permissions
```

### 3. Database Query Logging
```typescript
// Log queries for monitoring (without sensitive data)
async function queryWithLogging(db: D1Database, sql: string, params: unknown[]) {
  const start = Date.now();
  try {
    const result = await db.prepare(sql).bind(...params).all();
    console.log({
      type: 'db_query',
      sql: sql.substring(0, 100), // Truncate for safety
      duration: Date.now() - start,
      rowCount: result.results.length,
    });
    return result;
  } catch (error) {
    console.error({
      type: 'db_error',
      sql: sql.substring(0, 100),
      error: error instanceof Error ? error.message : 'Unknown',
    });
    throw error;
  }
}
```

## Best Practices Summary

1. **Always use parameterized queries** - No exceptions
2. **Never concatenate user input** - Into SQL strings
3. **Use ORMs when possible** - They handle escaping
4. **Allowlist dynamic identifiers** - Table names, column names
5. **Validate input first** - Before it reaches the query
6. **Use least privilege** - Database permissions
7. **Escape LIKE wildcards** - When using pattern matching
8. **Test with injection payloads** - As part of security testing
9. **Log suspicious queries** - For monitoring and alerting
10. **Keep dependencies updated** - Database drivers get security fixes
