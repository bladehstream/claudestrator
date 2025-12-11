# Database Migrations Reference

Strategies and workflows for managing database schema changes in TypeScript applications.

## Migration Fundamentals

### What Migrations Track
- Table creation/modification/deletion
- Column additions/changes/removals
- Index creation/deletion
- Constraint changes (foreign keys, unique, check)
- Enum changes
- Data transformations

### Migration File Structure

```
migrations/
├── 20240101120000_initial_schema.sql
├── 20240102150000_add_users_table.sql
├── 20240103090000_add_email_index.sql
└── 20240104140000_add_posts_table.sql
```

## Prisma Migrations

### Commands

```bash
# Development: Create and apply migration
npx prisma migrate dev --name add_user_table

# Create migration without applying
npx prisma migrate dev --create-only --name add_user_table

# Apply pending migrations (production)
npx prisma migrate deploy

# Reset database and reapply all migrations
npx prisma migrate reset

# Check migration status
npx prisma migrate status

# Resolve migration issues
npx prisma migrate resolve --applied "20240101120000_init"
npx prisma migrate resolve --rolled-back "20240101120000_init"
```

### Migration Workflow

```bash
# 1. Modify schema.prisma
# 2. Generate and apply migration
npx prisma migrate dev --name descriptive_name

# 3. Review generated SQL in prisma/migrations/
# 4. Test locally
# 5. Commit to version control
git add prisma/

# 6. Deploy to production
npx prisma migrate deploy
```

### Generated Migration Example

```sql
-- prisma/migrations/20240101120000_add_users/migration.sql
-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");
```

### Custom Migration (Data Migration)

```sql
-- After generation, edit the SQL file
-- prisma/migrations/20240102150000_migrate_data/migration.sql

-- Add new column
ALTER TABLE "posts" ADD COLUMN "slug" TEXT;

-- Populate from existing data
UPDATE "posts" SET "slug" = lower(replace(title, ' ', '-'));

-- Add constraint after data populated
ALTER TABLE "posts" ALTER COLUMN "slug" SET NOT NULL;
CREATE UNIQUE INDEX "posts_slug_key" ON "posts"("slug");
```

## Drizzle Migrations

### Commands

```bash
# Generate SQL migration from schema
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate

# Push schema directly (no file, dev only)
npx drizzle-kit push

# Pull schema from database
npx drizzle-kit pull

# Check for drift
npx drizzle-kit check

# Update snapshots
npx drizzle-kit up
```

### drizzle.config.ts

```typescript
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  dialect: 'postgresql',
  schema: './src/db/schema.ts',
  out: './drizzle',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
  migrations: {
    prefix: 'timestamp',  // timestamp | supabase | unix | none
    table: '__drizzle_migrations__',
    schema: 'public',
  },
  verbose: true,
  strict: true,
});
```

### Generated Migration Structure

```
drizzle/
├── meta/
│   ├── _journal.json
│   ├── 0000_snapshot.json
│   └── 0001_snapshot.json
├── 0000_initial.sql
└── 0001_add_posts.sql
```

### Custom Migration

```bash
# Generate empty migration file
npx drizzle-kit generate --custom --name seed_users
```

```sql
-- drizzle/0002_seed_users.sql
INSERT INTO "users" ("id", "email", "name") 
VALUES 
  ('1', 'admin@example.com', 'Admin'),
  ('2', 'user@example.com', 'User');
```

### Runtime Migrations

```typescript
import { migrate } from 'drizzle-orm/postgres-js/migrator';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

const runMigrations = async () => {
  const migrationClient = postgres(process.env.DATABASE_URL!, { max: 1 });
  const db = drizzle(migrationClient);
  
  console.log('Running migrations...');
  await migrate(db, { migrationsFolder: './drizzle' });
  console.log('Migrations complete!');
  
  await migrationClient.end();
};

runMigrations();
```

## Migration Strategies

### Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Method | `push` / `migrate dev` | `migrate deploy` |
| Destructive | Allowed | Never |
| Data loss | Acceptable | Never |
| Speed | Fast iteration | Careful, reviewed |
| Rollback | Reset database | Down migrations |

### Breaking vs Non-Breaking Changes

#### Non-Breaking (Safe)
- Add nullable column
- Add new table
- Add index
- Add new enum value
- Widen column (VARCHAR(50) → VARCHAR(100))

#### Breaking (Requires Care)
- Remove column
- Rename column/table
- Change column type
- Add NOT NULL constraint
- Remove/change foreign key

### Safe Column Addition Pattern

```sql
-- Step 1: Add nullable column
ALTER TABLE posts ADD COLUMN slug TEXT;

-- Step 2: Backfill data
UPDATE posts SET slug = lower(replace(title, ' ', '-'));

-- Step 3: Add constraint
ALTER TABLE posts ALTER COLUMN slug SET NOT NULL;

-- Step 4: Add index
CREATE UNIQUE INDEX posts_slug_idx ON posts(slug);
```

### Safe Column Removal Pattern

```sql
-- Step 1: Stop using column in application
-- (Deploy application change first)

-- Step 2: Drop default/constraints
ALTER TABLE users ALTER COLUMN old_field DROP DEFAULT;

-- Step 3: Remove column
ALTER TABLE users DROP COLUMN old_field;
```

### Safe Rename Pattern

```sql
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN full_name TEXT;

-- Step 2: Copy data
UPDATE users SET full_name = name;

-- Step 3: Update application to use new column
-- (Deploy application)

-- Step 4: Remove old column (later migration)
ALTER TABLE users DROP COLUMN name;
```

## Team Workflows

### Git Branch Strategy

```bash
# Feature branch
git checkout -b feature/add-comments

# Make schema changes
# Generate migration
npx prisma migrate dev --name add_comments_table

# Commit migration with feature
git add prisma/
git commit -m "feat: add comments table"

# Merge to main
git checkout main
git merge feature/add-comments

# Deploy
npx prisma migrate deploy
```

### Conflict Resolution

```bash
# When migrations conflict after merge
# Option 1: Reset and regenerate
npx prisma migrate reset
npx prisma migrate dev --name merged_changes

# Option 2: Mark as applied (if already in DB)
npx prisma migrate resolve --applied "migration_name"
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
      
      - name: Deploy application
        run: # your deploy command
```

## Rollback Strategies

### Prisma (No Built-in Down)

```bash
# Option 1: Create reverse migration
npx prisma migrate dev --name rollback_feature

# Option 2: Restore from backup
pg_restore -d mydb backup.dump

# Option 3: Manual SQL
psql $DATABASE_URL -f rollback.sql
```

### Drizzle Down Migrations

Drizzle doesn't generate down migrations automatically. Options:

1. **Manual down files**: Create corresponding `*.down.sql` files
2. **Restore from backup**: Keep database backups
3. **Forward-only**: Create new migration to undo changes

## Best Practices

1. **One change per migration** - Atomic, reversible changes
2. **Descriptive names** - `add_user_email_index` not `migration_1`
3. **Never edit deployed migrations** - Create new migration instead
4. **Test rollbacks** - Verify down migrations work
5. **Review SQL** - Check generated SQL before deploying
6. **Version control migrations** - Commit with related code
7. **Backup before deploy** - Always have rollback option
8. **Use transactions** - Wrap DDL in transactions when possible
9. **Avoid data in schema migrations** - Separate data migrations
10. **Document breaking changes** - Note required app changes
