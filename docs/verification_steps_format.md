# Verification Steps Format

> How implementation agents record verification steps for QA execution.

---

## Overview

Each implementation agent appends verification steps to `.orchestrator/verification_steps.md`. The Testing Agent executes all accumulated steps and raises issues for failures.

---

## File Location

`.orchestrator/verification_steps.md`

---

## Format

```markdown
## [TASK-ID]

| Field | Value |
|-------|-------|
| Category | [category] |
| Agent | [agent type] |
| Timestamp | [ISO timestamp] |

### Build Verification
[Commands to verify the code compiles/builds without errors]

### Runtime Verification
[Commands to verify the implementation works at runtime]

### Expected Outcomes
- [Outcome 1]: [How to verify success]
- [Outcome 2]: [How to verify success]

---
```

---

## Verification Types by Category

### Backend Agent

| Verification Type | What to Verify | Example Checks |
|-------------------|----------------|----------------|
| **Build** | Code compiles, no type errors | Build command succeeds |
| **Server Startup** | Server starts without crash | Process stays alive for 5+ seconds |
| **API Response** | Endpoints respond correctly | Health/status endpoint returns success |
| **Database** | DB operations work | Can connect, migrations applied |
| **Dependencies** | External services reachable | Required services respond |

**Append verification for:**
- Each new API endpoint created
- Database schema changes
- Service integrations added

### Frontend Agent

| Verification Type | What to Verify | Example Checks |
|-------------------|----------------|----------------|
| **Build** | Bundle compiles without errors | Build command succeeds |
| **Dev Server** | Dev server starts | Serves content on expected port |
| **Page Load** | Main pages render | Root element present in HTML |
| **Routes** | Navigation works | Key routes return 200 |
| **Assets** | Static assets load | CSS/JS files accessible |

**Append verification for:**
- Each new page/route created
- Component library additions
- Build configuration changes

### Fullstack Agent

| Verification Type | What to Verify | Example Checks |
|-------------------|----------------|----------------|
| **Build** | Both frontend and backend build | All build commands succeed |
| **Integration** | Frontend can reach backend | API calls from UI succeed |
| **Auth Flow** | Authentication works end-to-end | Login/logout cycle works |
| **Data Flow** | CRUD operations work | Create, read, update, delete succeed |

**Append verification for:**
- Features spanning frontend and backend
- Authentication/authorization changes
- Data model changes affecting both layers

### DevOps Agent

| Verification Type | What to Verify | Example Checks |
|-------------------|----------------|----------------|
| **Container Build** | Images build successfully | Docker build exits 0 |
| **Container Run** | Containers start and stay healthy | Container health check passes |
| **Config Validity** | Configuration files are valid | Config validation passes |
| **CI Pipeline** | Pipeline syntax is valid | Linter/validator passes |
| **Ports/Network** | Expected ports are exposed | Services bind to expected ports |

**Append verification for:**
- Dockerfile changes
- CI/CD pipeline changes
- Infrastructure configuration changes

### Docs Agent

| Verification Type | What to Verify | Example Checks |
|-------------------|----------------|----------------|
| **Links** | Internal links are valid | No broken links |
| **Code Examples** | Code samples are syntactically valid | Examples parse without errors |
| **Completeness** | Required sections present | README has expected structure |

**Append verification for:**
- Documentation additions
- API documentation changes
- README updates

---

## Writing Verification Steps

### DO

- **Be specific about what you implemented**: "Verify the `/api/users` endpoint returns a list of users"
- **Include success criteria**: "Response should be JSON array with `id` and `email` fields"
- **Test the happy path first**: Ensure basic functionality works
- **Test critical error cases**: Authentication required, invalid input handling
- **Use the project's actual commands**: Read package.json/Makefile/etc. to find correct commands

### DON'T

- **Don't hardcode ports**: Use environment variables or detect from config
- **Don't assume specific tools**: Check what's available in the project
- **Don't write platform-specific commands without checking**: Verify the OS/environment first
- **Don't skip verification**: Every implementation change needs at least one verification step

---

## Example: Backend API Implementation

```markdown
## TASK-003

| Field | Value |
|-------|-------|
| Category | backend |
| Agent | backend |
| Timestamp | 2024-12-13T10:30:00Z |

### Build Verification
```bash
# Verify TypeScript compiles without errors
npm run build
# Expected: Exit code 0, no type errors
```

### Runtime Verification
```bash
# Start server in background, wait for startup
npm run dev &
SERVER_PID=$!
sleep 5

# Verify server is still running (didn't crash)
kill -0 $SERVER_PID 2>/dev/null || { echo "Server crashed on startup"; exit 1; }

# Test the new endpoint
curl -sf http://localhost:${PORT:-3000}/api/users | head -c 500

# Cleanup
kill $SERVER_PID 2>/dev/null
```

### Expected Outcomes
- Build completes with exit code 0
- Server starts and remains running for 5+ seconds
- GET /api/users returns JSON array (may be empty)
- Response includes appropriate headers (Content-Type: application/json)

---
```

---

## Example: Frontend Component Implementation

```markdown
## TASK-004

| Field | Value |
|-------|-------|
| Category | frontend |
| Agent | frontend |
| Timestamp | 2024-12-13T11:00:00Z |

### Build Verification
```bash
# Verify build succeeds
npm run build
# Expected: Exit code 0, bundle created
```

### Runtime Verification
```bash
# Start dev server
npm run dev &
SERVER_PID=$!
sleep 8

# Verify server responds
curl -sf http://localhost:${PORT:-3000}/ | grep -q '<div id="root">' || \
curl -sf http://localhost:${PORT:-5173}/ | grep -q '<div id="root">'

# Verify new route exists (if applicable)
curl -sf http://localhost:${PORT:-3000}/dashboard -o /dev/null

# Cleanup
kill $SERVER_PID 2>/dev/null
```

### Expected Outcomes
- Build completes with exit code 0
- Dev server starts successfully
- Root page loads with React mount point
- New /dashboard route returns 200

---
```

---

## Testing Agent Execution

The Testing Agent:

1. **Reads** `.orchestrator/verification_steps.md`
2. **Parses** each task's verification section
3. **Executes** build verification first (fail fast)
4. **Executes** runtime verifications
5. **Records** pass/fail for each task
6. **Raises issues** for any failures:
   ```
   /issue [generated] Title: TASK-XXX verification failed
   Description: [failure details]
   Category: bug
   Priority: high
   ```

---

## Failure Handling

| Failure Type | Action |
|--------------|--------|
| Build fails | Raise HIGH priority issue, block completion |
| Server won't start | Raise HIGH priority issue, block completion |
| Endpoint returns error | Raise MEDIUM priority issue, continue other checks |
| Missing expected content | Raise MEDIUM priority issue, continue other checks |

---

*Verification Steps Format v1.0*
