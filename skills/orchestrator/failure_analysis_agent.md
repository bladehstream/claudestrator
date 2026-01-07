---
name: Failure Analysis Agent
id: failure_analysis_agent
version: 2.0
category: orchestrator
domain: [orchestration, debugging, analysis]
task_types: [analysis, debugging, issue-creation]
keywords: [failure, analysis, diagnosis, root-cause, debugging, remediation, critical, retry, signature]
complexity: [complex]
pairs_with: [decomposition_agent, agent_construction, testing_agent]
source: original
prompt_source: prompts/failure_analysis_agent.md
---

# Failure Analysis Agent Skill

> **Role**: Senior Debugging Specialist / Root Cause Analyst
> **Purpose**: Examine failed implementations, diagnose root causes, create critical remediation issues
> **Model**: Opus (requires deep reasoning and code analysis)
> **Source of Truth**: `prompts/failure_analysis_agent.md`

---

## Quick Reference

This skill provides metadata for the Failure Analysis Agent. The full prompt with detailed instructions is maintained in:

```
prompts/failure_analysis_agent.md
```

When spawning this agent, read and follow the prompt source file.

---

## When Triggered

This agent is spawned by the orchestrator when:
- An implementation task has `Status | failed` in task_queue.md
- A `.failed` marker exists in `.orchestrator/complete/`
- The implementation agent exhausted all 3 attempts

---

## Capabilities Summary

The Failure Analysis Agent:
- Analyzes failed test output and stack traces
- Reads code to identify bugs and logic errors
- Determines if tests or implementation is wrong
- Generates failure signatures for retry loop detection
- Creates remediation issues with `Priority | critical`

---

## Root Cause Classification

| Type | Description |
|------|-------------|
| `implementation_bug` | Code has bugs (null reference, logic error) |
| `test_defect` | Tests are wrong (wrong assertion, bad fixture) |
| `missing_dependency` | Package not installed (ImportError) |
| `configuration_error` | Config/env wrong (missing env var) |
| `architecture_conflict` | Approach conflicts with patterns |
| `scope_too_large` | Task needs splitting |
| `missing_prerequisite` | Depends on unfinished work |

---

## Failure Signature (v2.0)

**All issues MUST include a failure signature** to detect repeated identical failures:

```
SIGNATURE_INPUT = CONCAT(
    root_cause_type,
    primary_error_message,
    failing_test_name,
    affected_file
)
FAILURE_SIGNATURE = SHA256(SIGNATURE_INPUT)[0:16]
```

---

## Issue Fields (v2.0)

| Field | Value |
|-------|-------|
| Priority | critical |
| Auto-Retry | true |
| Max-Retries | 10 |
| Failure-Signature | {generated} |
| Previous-Signatures | [] |
| Signature-Repeat-Count | 0 |
| Halted | false |

---

## Usage

```
Task(
    model: "opus",
    prompt: "Read('prompts/failure_analysis_agent.md') and follow those instructions.

    FAILED_TASK: TASK-001
    FAILURE_REPORT: .orchestrator/reports/TASK-001-loop-1.json

    When done: Write('.orchestrator/complete/analysis-TASK-001.done', 'done')"
)
```

---

## Related Skills

- `decomposition_agent` - Converts remediation issues back to tasks
- `testing_agent` - Verifies fixes
- `implementation_agent` - Implements the fix

---

*Skill Version: 2.0 - Updated for failure signature tracking*
*Source of Truth: prompts/failure_analysis_agent.md*
