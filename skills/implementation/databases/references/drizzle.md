# Drizzle ORM Reference

Drizzle is a lightweight, SQL-like TypeScript ORM with zero dependencies (~7.4KB), perfect for serverless and edge environments.

## Installation & Setup

```bash
# Core ORM
npm install drizzle-orm

# Database driver (choose one)
npm install postgres          # PostgreSQL (recommended)
npm install pg                # node-postgres
npm install better-sqlite3    # SQLite
npm install mysql2            # MySQL

# Drizzle Kit (migrations CLI)
npm install -D drizzle-kit
```

## Configuration

### drizzle.config.ts

```typescript
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  dialect: 'postgresql',     // postgresql | mysql | sqlite
  schema: './src/db/schema.ts',
  out: './drizzle',          // Migration output folder
  
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
  
  // Optional settings
  verbose: true,              // Log SQL during generate
  strict: true,               // Fail on warnings
  
  migrations: {
    prefix: 'timestamp',      // timestamp | supabase | unix | none
    table: '__drizzle_migrations__',
    schema: 'public',
  },
});
```

### Database Connection

```typescript
// PostgreSQL with postgres.js (recommended)
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const client = postgres(process.env.DATABASE_URL!);
export const db = drizzle(client, { schema });

// PostgreSQL with node-postgres
import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
export const db = drizzle(pool, { schema });

// SQLite with better-sqlite3
import { drizzle } from 'drizzle-orm/better-sqlite3';
import Database from 'better-sqlite3';

const sqlite = new Database('sqlite.db');
export const db = drizzle(sqlite, { schema });

// Cloudflare D1
import { drizzle } from 'drizzle-orm/d1';

export default {
  fetch(request: Request, env: Env) {
    const db = drizzle(env.DB, { schema });
    // ...
  }
};
```

## Schema Definition

### Table Definition (PostgreSQL)

```typescript
import {
  pgTable,
  text,
  integer,
  boolean,
  timestamp,
  varchar,
  serial,
  uuid,
  json,
  jsonb,
  index,
  uniqueIndex,
  primaryKey,
} from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  // Primary keys
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  // or: id: serial('id').primaryKey(),
  // or: id: uuid('id').primaryKey().defaultRandom(),
  
  // Basic fields
  email: text('email').notNull().unique(),
  name: varchar('name', { length: 255 }),
  age: integer('age'),
  isActive: boolean('is_active').default(true).notNull(),
  
  // JSON
  metadata: jsonb('metadata').$type<{ preferences: Record<string, unknown> }>(),
  
  // Timestamps
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull().$onUpdate(() => new Date()),
  deletedAt: timestamp('deleted_at'),
}, (table) => [
  // Indexes
  index('users_email_idx').on(table.email),
  index('users_created_at_idx').on(table.createdAt.desc()),
]);

// Infer types from schema
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
```

### Enums

```typescript
import { pgEnum } from 'drizzle-orm/pg-core';

export const roleEnum = pgEnum('role', ['user', 'admin', 'moderator']);

export const users = pgTable('users', {
  id: text('id').primaryKey(),
  role: roleEnum('role').default('user').notNull(),
});
```

### Relations

```typescript
import { relations } from 'drizzle-orm';

// Tables
export const users = pgTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull(),
});

export const posts = pgTable('posts', {
  id: text('id').primaryKey(),
  title: text('title').notNull(),
  authorId: text('author_id').notNull().references(() => users.id),
});

export const comments = pgTable('comments', {
  id: text('id').primaryKey(),
  content: text('content').notNull(),
  postId: text('post_id').notNull().references(() => posts.id),
  authorId: text('author_id').notNull().references(() => users.id),
});

// Many-to-Many (explicit join table)
export const postsTags = pgTable('posts_tags', {
  postId: text('post_id').notNull().references(() => posts.id),
  tagId: text('tag_id').notNull().references(() => tags.id),
}, (t) => [
  primaryKey({ columns: [t.postId, t.tagId] }),
]);

export const tags = pgTable('tags', {
  id: text('id').primaryKey(),
  name: text('name').notNull().unique(),
});

// Define relations (for Queries API)
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
  comments: many(comments),
}));

export const postsRelations = relations(posts, ({ one, many }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
  comments: many(comments),
  postsTags: many(postsTags),
}));

export const commentsRelations = relations(comments, ({ one }) => ({
  post: one(posts, {
    fields: [comments.postId],
    references: [posts.id],
  }),
  author: one(users, {
    fields: [comments.authorId],
    references: [users.id],
  }),
}));
```

### Reusable Column Helpers

```typescript
// timestamps.ts
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

## Query Builder (SQL-like)

```typescript
import { eq, ne, gt, gte, lt, lte, and, or, not, like, ilike, between, inArray, isNull, isNotNull, sql, desc, asc } from 'drizzle-orm';

// SELECT
const allUsers = await db.select().from(users);

const user = await db.select()
  .from(users)
  .where(eq(users.id, userId))
  .limit(1);

// Select specific columns
const emails = await db.select({ email: users.email }).from(users);

// Complex filtering
const filteredUsers = await db.select()
  .from(users)
  .where(
    and(
      eq(users.isActive, true),
      or(
        like(users.email, '%@gmail.com'),
        like(users.email, '%@outlook.com'),
      ),
      gt(users.age, 18),
      isNotNull(users.name),
    )
  )
  .orderBy(desc(users.createdAt))
  .limit(10)
  .offset(0);

// JOIN
const postsWithAuthors = await db.select({
  post: posts,
  author: users,
})
  .from(posts)
  .innerJoin(users, eq(posts.authorId, users.id))
  .where(eq(posts.published, true));

// Left join
const usersWithPosts = await db.select()
  .from(users)
  .leftJoin(posts, eq(users.id, posts.authorId));

// INSERT
const [newUser] = await db.insert(users)
  .values({ email: 'alice@example.com', name: 'Alice' })
  .returning();

// Insert multiple
await db.insert(users).values([
  { email: 'bob@example.com' },
  { email: 'charlie@example.com' },
]);

// INSERT ... ON CONFLICT (upsert)
await db.insert(users)
  .values({ id: 'existing-id', email: 'updated@example.com' })
  .onConflictDoUpdate({
    target: users.id,
    set: { email: 'updated@example.com', updatedAt: new Date() },
  });

await db.insert(users)
  .values({ email: 'unique@example.com' })
  .onConflictDoNothing({ target: users.email });

// UPDATE
await db.update(users)
  .set({ name: 'Alice Updated', updatedAt: new Date() })
  .where(eq(users.id, userId));

// DELETE
await db.delete(users).where(eq(users.id, userId));

// Subqueries
const avgAge = db.select({ avg: sql<number>`avg(${users.age})` }).from(users);
const aboveAverage = await db.select()
  .from(users)
  .where(gt(users.age, avgAge));
```

## Queries API (Relational)

The Queries API provides a higher-level abstraction for relational data with automatic joins.

```typescript
// Setup: Pass schema to drizzle
const db = drizzle(client, { schema });

// Find one
const user = await db.query.users.findFirst({
  where: eq(users.id, userId),
});

// Find many with relations
const usersWithPosts = await db.query.users.findMany({
  with: {
    posts: true,
  },
  where: eq(users.isActive, true),
  orderBy: [desc(users.createdAt)],
  limit: 10,
});

// Nested relations
const postsWithDetails = await db.query.posts.findMany({
  with: {
    author: true,
    comments: {
      with: {
        author: true,
      },
      orderBy: [desc(comments.createdAt)],
      limit: 5,
    },
  },
  where: eq(posts.published, true),
});

// Select specific columns in relations
const usersPartial = await db.query.users.findMany({
  columns: {
    id: true,
    email: true,
  },
  with: {
    posts: {
      columns: {
        id: true,
        title: true,
      },
    },
  },
});

// Filter relations
const usersWithPublishedPosts = await db.query.users.findMany({
  with: {
    posts: {
      where: eq(posts.published, true),
      limit: 5,
    },
  },
});
```

## Transactions

```typescript
// Basic transaction
await db.transaction(async (tx) => {
  const [user] = await tx.insert(users)
    .values({ email: 'alice@example.com' })
    .returning();
  
  await tx.insert(posts)
    .values({ title: 'First Post', authorId: user.id });
});

// With rollback
await db.transaction(async (tx) => {
  await tx.insert(users).values({ email: 'bob@example.com' });
  
  // Explicitly rollback
  tx.rollback();
});

// Nested transactions (savepoints)
await db.transaction(async (tx) => {
  await tx.insert(users).values({ email: 'outer@example.com' });
  
  await tx.transaction(async (tx2) => {
    await tx2.insert(posts).values({ title: 'Nested' });
    // Rollback only inner transaction
  });
});
```

## Migrations

```bash
# Generate migration from schema changes
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate

# Push schema directly (no migration file - dev only)
npx drizzle-kit push

# Pull schema from existing database
npx drizzle-kit pull

# Open Drizzle Studio (GUI)
npx drizzle-kit studio
```

### Migration Commands Summary

| Command | Use Case |
|---------|----------|
| `generate` | Create SQL migration file from schema diff |
| `migrate` | Apply pending migrations to database |
| `push` | Push schema directly (prototyping) |
| `pull` | Generate schema from existing database |
| `check` | Check for schema drift |
| `up` | Update migration snapshots |

### Runtime Migrations

```typescript
import { migrate } from 'drizzle-orm/postgres-js/migrator';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

const client = postgres(process.env.DATABASE_URL!, { max: 1 });
const db = drizzle(client);

await migrate(db, { migrationsFolder: './drizzle' });
```

## Raw SQL

```typescript
import { sql } from 'drizzle-orm';

// In queries
const result = await db.select({
  count: sql<number>`count(*)`,
  avgAge: sql<number>`avg(${users.age})`,
}).from(users);

// Raw execute
await db.execute(sql`
  CREATE INDEX CONCURRENTLY IF NOT EXISTS users_email_idx
  ON users (email)
`);

// Typed raw query
const users = await db.execute<User>(sql`
  SELECT * FROM users WHERE age > ${minAge}
`);
```

## Prepared Statements

```typescript
// Prepare once, execute many times
const prepared = db.select()
  .from(users)
  .where(eq(users.id, sql.placeholder('id')))
  .prepare('get_user_by_id');

const user1 = await prepared.execute({ id: 'user-1' });
const user2 = await prepared.execute({ id: 'user-2' });
```

## Zod Integration

```bash
npm install drizzle-zod zod
```

```typescript
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import { z } from 'zod';

// Auto-generate Zod schemas
const insertUserSchema = createInsertSchema(users, {
  email: z.string().email(),
  age: z.number().min(0).max(150),
});

const selectUserSchema = createSelectSchema(users);

// Use for validation
const validatedData = insertUserSchema.parse(requestBody);
await db.insert(users).values(validatedData);
```

## Best Practices

1. **Use Queries API for relations** - Avoids N+1, single roundtrip
2. **Schema in separate files** - Organize by domain/feature
3. **Type inference** - Use `$inferSelect` and `$inferInsert`
4. **Prepared statements** - For frequently executed queries
5. **Index foreign keys** - Always add indexes on reference columns
6. **Use `push` for dev only** - Use `generate` + `migrate` for production
7. **Review generated SQL** - Check migrations before applying
8. **Connection pooling** - Use appropriate pool settings for your environment
