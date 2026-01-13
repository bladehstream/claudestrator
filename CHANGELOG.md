# Changelog

All notable changes to Claudestrator are documented here.

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
