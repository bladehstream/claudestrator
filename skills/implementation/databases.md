---
name: Databases
id: databases
version: 1.0
category: implementation
domain: [database, orm, sql, backend]
task_types: [design, implementation, optimization]
keywords: [database, postgresql, prisma, drizzle, orm, sql, migration, query, index, transaction, d1, connection pooling]
complexity: [normal, complex]
pairs_with: [api_development, backend_security]
source: backend-skills/databases/SKILL-databases.md
---

# Databases Skill

Comprehensive database management for TypeScript applications with PostgreSQL, ORMs (Prisma/Drizzle), migrations, query optimization, and serverless patterns.

## When to Use What

| Need | Solution |
|------|----------|
| Type-safe ORM, schema-first | Prisma |
| SQL-like queries, lightweight | Drizzle |
| Edge/serverless database | Cloudflare D1, Neon, Turso |
| Connection pooling | PgBouncer, Prisma Accelerate |
| Rapid prototyping | `drizzle-kit push` / `prisma db push` |
| Production migrations | `drizzle-kit generate` / `prisma migrate` |

## Quick Reference

### Prisma Setup
```bash
npm install prisma @prisma/client
npx prisma init
npx prisma generate       # Generate client
npx prisma migrate dev    # Create/apply migration
npx prisma db push        # Push schema (no migration file)
npx prisma studio         # GUI browser
```

### Drizzle Setup
```bash
npm install drizzle-orm drizzle-kit
npx drizzle-kit generate  # Generate SQL migrations
npx drizzle-kit migrate   # Apply migrations
npx drizzle-kit push      # Push schema directly
npx drizzle-kit studio    # GUI browser
```

## Core Patterns

### Prisma Schema (schema.prisma)
```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Post {
  id        String   @id @default(cuid())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  String

  @@index([authorId])
}
```

### Drizzle Schema (schema.ts)
```typescript
import { pgTable, text, boolean, timestamp, index } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

export const users = pgTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

export const posts = pgTable('posts', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  title: text('title').notNull(),
  content: text('content'),
  published: boolean('published').default(false).notNull(),
  authorId: text('author_id').notNull().references(() => users.id),
}, (table) => [
  index('posts_author_idx').on(table.authorId),
]);

export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, { fields: [posts.authorId], references: [users.id] }),
}));
```

## Common Queries

### Prisma Queries
```typescript
// Find with relations
const user = await prisma.user.findUnique({
  where: { id },
  include: { posts: true },
});

// Create with relation
const post = await prisma.post.create({
  data: {
    title: 'Hello',
    author: { connect: { id: userId } },
  },
});

// Transaction
const [user, post] = await prisma.$transaction([
  prisma.user.create({ data: userData }),
  prisma.post.create({ data: postData }),
]);

// Interactive transaction
await prisma.$transaction(async (tx) => {
  const user = await tx.user.findUnique({ where: { id } });
  if (!user) throw new Error('User not found');
  return tx.post.create({ data: { ...postData, authorId: user.id } });
});
```

### Drizzle Queries
```typescript
// Find with relations (Queries API)
const user = await db.query.users.findFirst({
  where: eq(users.id, id),
  with: { posts: true },
});

// SQL-like query builder
const results = await db
  .select()
  .from(posts)
  .where(eq(posts.authorId, userId))
  .orderBy(desc(posts.createdAt))
  .limit(10);

// Insert
const [newPost] = await db.insert(posts).values(postData).returning();

// Transaction
await db.transaction(async (tx) => {
  const [user] = await tx.select().from(users).where(eq(users.id, id));
  if (!user) throw new Error('User not found');
  return tx.insert(posts).values({ ...postData, authorId: user.id });
});
```

## Index Types (PostgreSQL)

| Type | Use Case | Example |
|------|----------|---------|
| B-Tree | Equality, range, sorting (default) | `WHERE status = 'active'` |
| Hash | Exact match only | `WHERE id = 123` |
| GIN | Arrays, JSONB, full-text | `WHERE tags @> ARRAY['sql']` |
| GiST | Spatial, geometric | PostGIS queries |
| BRIN | Large time-series tables | `WHERE created_at > '2024-01-01'` |

## Transaction Isolation Levels

| Level | Dirty Read | Non-repeatable Read | Phantom Read | Use Case |
|-------|------------|---------------------|--------------|----------|
| Read Committed (default) | ✗ | ✓ | ✓ | Most applications |
| Repeatable Read | ✗ | ✗ | ✗* | Reports, consistent reads |
| Serializable | ✗ | ✗ | ✗ | Financial, strict consistency |

*PostgreSQL's Repeatable Read prevents phantoms via snapshot isolation

## Connection Pooling

### PgBouncer Modes
- **Session**: Connection held for entire session (admin tasks)
- **Transaction**: Connection released after each transaction (serverless)
- **Statement**: Connection released after each statement (rare)

### Serverless Connection Strings
```
# Supabase (pooled)
postgresql://user:pass@db.project.supabase.co:6543/postgres?pgbouncer=true

# Neon (pooled)
postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require

# Prisma with PgBouncer
postgresql://user:pass@host:6543/db?pgbouncer=true&connection_limit=1
```

## Migration Best Practices

1. **Never edit deployed migrations** - Create new migration for fixes
2. **Test rollbacks** - Ensure `down` migrations work
3. **Use transactions** - Wrap DDL in transactions (PostgreSQL supports this)
4. **Avoid breaking changes** - Add columns nullable, backfill, then add constraint
5. **Review generated SQL** - Check migrations before applying to production

## Cloudflare D1 (Edge SQLite)

```typescript
// wrangler.toml binding
// [[d1_databases]]
// binding = "DB"
// database_name = "my-db"

export default {
  async fetch(request: Request, env: Env) {
    // Prepared statement (prevents SQL injection)
    const { results } = await env.DB.prepare(
      'SELECT * FROM users WHERE id = ?'
    ).bind(userId).all();

    // Batch operations
    const batch = await env.DB.batch([
      env.DB.prepare('INSERT INTO users (name) VALUES (?)').bind('Alice'),
      env.DB.prepare('INSERT INTO users (name) VALUES (?)').bind('Bob'),
    ]);

    return Response.json(results);
  }
};
```

## N+1 Problem Solutions

### Prisma - Use `include` or `select`
```typescript
// ❌ N+1: Separate queries per user
const users = await prisma.user.findMany();
for (const user of users) {
  const posts = await prisma.post.findMany({ where: { authorId: user.id } });
}

// ✅ Single query with include
const users = await prisma.user.findMany({ include: { posts: true } });
```

### Drizzle - Use Queries API with `with`
```typescript
// ✅ Uses lateral joins, single roundtrip
const users = await db.query.users.findMany({
  with: { posts: true },
});
```

### GraphQL - Use DataLoader or Prisma's built-in batching
```typescript
// Prisma auto-batches findUnique in same tick
const User = {
  posts: (parent, _, ctx) =>
    ctx.prisma.user.findUnique({ where: { id: parent.id } }).posts(),
};
```

## Soft Deletes Pattern

```typescript
// Prisma schema
model User {
  id        String    @id @default(cuid())
  email     String    @unique
  deletedAt DateTime?

  @@index([deletedAt])
}

// Prisma middleware for soft delete
prisma.$use(async (params, next) => {
  if (params.model === 'User') {
    if (params.action === 'delete') {
      params.action = 'update';
      params.args.data = { deletedAt: new Date() };
    }
    if (params.action === 'findMany' || params.action === 'findFirst') {
      params.args.where = { ...params.args.where, deletedAt: null };
    }
  }
  return next(params);
});
```

## Timestamps Pattern

```typescript
// Drizzle helper
import { timestamp } from 'drizzle-orm/pg-core';

export const timestamps = {
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull().$onUpdate(() => new Date()),
};

// Usage
export const users = pgTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull(),
  ...timestamps,
});
```

## Reference Files

- `references/prisma.md` - Full Prisma patterns and configuration
- `references/drizzle.md` - Full Drizzle patterns and configuration
- `references/postgresql.md` - PostgreSQL optimization and features
- `references/migrations.md` - Migration strategies and workflows
- `references/connection-pooling.md` - Connection management patterns
- `references/transactions.md` - Transaction patterns and isolation
- `references/indexing.md` - Index types and optimization
- `references/patterns.md` - Common database patterns (soft delete, audit, etc.)
- `references/d1.md` - Cloudflare D1 edge database

## Best Practices Summary

1. **Use an ORM** - Type safety prevents SQL injection and runtime errors
2. **Index foreign keys** - Always index columns used in JOINs/WHERE
3. **Use connection pooling** - Essential for serverless, recommended everywhere
4. **Avoid N+1** - Use eager loading (`include`/`with`) for relations
5. **Transaction appropriately** - Use for multi-step operations, understand isolation
6. **Version migrations** - Track all schema changes in version control
7. **Soft delete carefully** - Consider audit tables for complex requirements
8. **Monitor queries** - Use `EXPLAIN ANALYZE`, enable query logging in dev

---

*Skill Version: 1.0*
