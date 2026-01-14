# Changelog

All notable changes to Claudestrator are documented here.

## [4.2] - 2026-01-14

### Added
- **`--test-only` mode**: Create and verify tests without running BUILD tasks
  - Use when implementation exists and tests need rework/validation
  - Executes: TASK-T## (test creation) → TASK-V## (verification)
  - Skips: TASK-### (build) and TASK-99999 (QA)

- **`--help` flag**: Comprehensive help output with all options and examples
  - `/orchestrate --help` or `/orchestrate -h`
  - Shows usage, options, examples, task types, and modes

- **Skip rate verification** in Test Verification Agent:
  - Enforces ≤10% skip rate for PASS verdict
  - Environmental issues (ECONNREFUSED, EADDRINUSE, etc.) → BLOCKED
  - Code issues (import/export errors) → FAIL
  - Two-tier pattern detection: universal system errors + project-specific patterns

- **TASK-V## (verification tasks)** now created by Decomposition Agent:
  - Verification handled through task queue, not inline in orchestrator
  - Each TASK-T## gets a corresponding TASK-V##
  - Proper dependency chain: TEST → BUILD → VERIFY → QA

### Changed
- Updated orchestrate.md to v4.2
- install.sh now properly handles symlinked destinations
- Improved documentation consistency for test-only mode

### Fixed
- Verification tasks were never being created via task queue (were inline in orchestrator)
- Environmental skip "cheating" where tests passed with "100% (of runnable)" while 34% skipped
- install.sh "same file" errors when destination is symlinked to source

---

## [4.1] - 2026-01-13

### Changed
- **MCP-First Browser Testing** - Both test agents now enforce MCP browser tools over curl/fetch for UI testing

- **Test Creation Agent v1.1**:
  - Added "MCP-First Testing Principle (CRITICAL)" section
  - UI tests MUST specify MCP verification steps
  - curl/fetch-only UI tests are FORBIDDEN
  - If MCP unavailable, UI tests must be BLOCKED (not faked)
  - New test header field: `@mcp-required: true|false`
  - Added `verification_method` field to testid-map.json

- **Test Verification Agent v1.1**:
  - Added "MCP-First Verification Principle (CRITICAL)" section
  - Phase 4.4: MCP Browser Verification (MANDATORY for UI Tests)
  - Verifier captures its own screenshots via MCP
  - UI tests without MCP verification are automatically BLOCKED
  - Updated findings.json with `mcp_verification` section
  - Updated report template with MCP verification table

### Why This Change
curl/fetch can test API responses but cannot verify actual UI rendering. A broken frontend can return `200 OK` via API while showing errors to users. MCP browser tools interact with the real rendered DOM, proving the UI actually works.

---

## [4.0] - 2026-01-13

### Added
- **Test Creation Agent** (`test_creation_agent.md`):
  - Adversarial test writing - assumes implementation will try to cheat
  - Requires real HTTP (fetch to localhost), real DB (file, not :memory:), real browser (MCP/Playwright)
  - Evidence-carrying with `evidence.json` and hash validation
  - Anti-cheat grep checks built into workflow
  - BLOCKED protocol for missing infrastructure

- **Test Verification Agent** (`test_verification_agent.md`):
  - Zero-trust model - treats all other agents as adversarial
  - Re-executes all tests independently (doesn't trust producer evidence)
  - Hash validation to detect evidence tampering
  - E2E boundary verification (detects `app.request()` cheating)
  - Verdicts: PASS, FAIL, or BLOCKED with evidence

- **New task pattern**: `TASK-V##` for verification tasks
- **Updated workflow**: TEST → BUILD → VERIFY → QA

### Changed
- Flattened `prompts/` directory structure (removed `implementation/` subdirectory)
- Updated `install.sh` to skip symlinks instead of failing

### Deprecated
- `testing_agent.md` - replaced by `test_creation_agent.md` and `test_verification_agent.md`
  - Old file kept for reference with deprecation notice
  - Migration: `category: testing` → `category: test_creation` or `category: test_verification`

### Why This Change
The single testing agent pattern allowed "cheating" where tests could be marked complete without genuine verification. The new two-agent architecture creates adversarial validation that catches fake tests.

---

## [3.8] - 2026-01-13

### Added
- **Concurrency Control**: MAX_CONCURRENT_AGENTS = 10 to prevent resource exhaustion
  - Orchestrator blocks when all slots are in use
  - Tracks running tasks in `.orchestrator/running_tasks.txt`
  - Single bash blocking wait for efficient slot management

- **E2E Test Integrity Requirements** (testing_agent.md v1.4):
  - Anti-pattern detection table for fake E2E tests
  - Mandatory evidence requirements (server logs, HTTP captures, screenshots)
  - BLOCKED as valid completion state for missing dependencies
  - Browser automation tool detection (Chrome extension > Playwright > Puppeteer)
  - Self-check checklist before completion

### Changed
- Testing Agent now rejects E2E tests that use `:memory:` databases or mocks
- Updated orchestrate.md to v3.8 with concurrency gate (section 2a-1)

### Fixed
- Agents no longer spawn unbounded when tasks have no dependencies
- E2E tests must now demonstrate real server interactions

## [3.7] - 2026-01-12

### Added
- Research Agent requires explicit `--research` flag
- External spec source support (`--source external_spec`)

## [3.6] - 2026-01-10

### Added
- TDD workflow enforcement
- TEST tasks (TASK-T##) execute before BUILD tasks (TASK-###)

---

See [DECISIONS.md](DECISIONS.md) for architectural decision records.
