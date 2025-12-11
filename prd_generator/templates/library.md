# Product Requirements Document: Library/SDK

```yaml
# PRD Metadata (machine-readable for orchestrator)
metadata:
  schema_version: "2.0"
  project:
    name: "[Library Name]"
    type: library
    complexity: simple | moderate | complex
  mvp:
    target_date: "[YYYY-MM-DD or TBD]"
    feature_count: 0
  tech_stack:
    languages: []  # TypeScript, Python, Go, Rust
    frameworks: []
    databases: []
  library:
    package_name: "[e.g., @org/library-name]"
    module_system: "[ESM, CJS, Both]"
    min_runtime: "[e.g., Node 18+, Python 3.9+]"
  constraints:
    team_size: 1
    timeline: "[e.g., 4 weeks]"
  tags: []
```

## Document Information

| Field | Value |
|-------|-------|
| **Project Name** | [Library Name] |
| **Document Version** | 2.0 |
| **Created** | [Date] |
| **Last Updated** | [Date] |
| **Author** | [Author] |
| **Status** | Draft / In Review / Approved |

---

## 1. Executive Summary

### 1.1 Vision Statement
[One sentence describing what this library will enable]

### 1.2 Problem Statement
[What problem does this library solve? What repetitive task or complex functionality does it abstract?]

### 1.2 Proposed Solution
[High-level description of the library and its core functionality]

### 1.3 Target Users

| User Type | Description | Use Case |
|-----------|-------------|----------|
| [e.g., Frontend Developers] | [Description] | [Primary use case] |
| [e.g., Data Scientists] | [Description] | [Primary use case] |

### 1.4 Success Metrics

| Metric | Target |
|--------|--------|
| npm/PyPI downloads | [Number] / month |
| GitHub stars | [Number] |
| Open issues response time | < [X] days |
| Documentation coverage | [X]% |

---

## 2. Library Overview

### 2.1 Package Information

| Field | Value |
|-------|-------|
| **Package Name** | [e.g., @org/library-name] |
| **Language** | [JavaScript/TypeScript/Python/etc.] |
| **Module System** | [ESM/CJS/Both] |
| **License** | [MIT/Apache-2.0/etc.] |
| **Repository** | [GitHub URL] |

### 2.2 Installation

```bash
# npm
npm install [package-name]

# yarn
yarn add [package-name]

# pnpm
pnpm add [package-name]
```

### 2.3 Quick Start

```javascript
// Minimal working example
import { mainFunction } from '[package-name]';

const result = mainFunction(input);
console.log(result);
```

---

## 3. Design Principles

### 3.1 Core Principles

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Simplicity** | [Easy to use for common cases] | [How achieved] |
| **Flexibility** | [Extensible for advanced cases] | [How achieved] |
| **Performance** | [Fast and efficient] | [How achieved] |
| **Type Safety** | [Strong typing if applicable] | [How achieved] |
| **Zero/Minimal Dependencies** | [Dependency philosophy] | [How achieved] |

### 3.2 API Design Guidelines

| Guideline | Description |
|-----------|-------------|
| Consistency | [Naming conventions, patterns] |
| Discoverability | [How users find functionality] |
| Error handling | [Error philosophy] |
| Defaults | [Sensible defaults philosophy] |

---

## 4. API Specification

### 4.1 Core API

#### Function/Class: `[mainFunction]`

```typescript
/**
 * [Description of what this function does]
 *
 * @param input - [Description of input parameter]
 * @param options - [Description of options parameter]
 * @returns [Description of return value]
 * @throws [When and what errors are thrown]
 *
 * @example
 * const result = mainFunction('input', { option: true });
 */
function mainFunction(input: InputType, options?: Options): ReturnType;
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `input` | `InputType` | Yes | - | [Description] |
| `options` | `Options` | No | `{}` | [Description] |

**Options Object:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `option1` | `string` | `'default'` | [Description] |
| `option2` | `boolean` | `false` | [Description] |

**Returns:** `ReturnType`

| Property | Type | Description |
|----------|------|-------------|
| `result` | `string` | [Description] |
| `metadata` | `object` | [Description] |

**Throws:**

| Error | Condition |
|-------|-----------|
| `InvalidInputError` | [When thrown] |
| `ConfigurationError` | [When thrown] |

**Examples:**

```typescript
// Basic usage
const result = mainFunction('hello');

// With options
const result = mainFunction('hello', {
  option1: 'custom',
  option2: true
});

// Error handling
try {
  const result = mainFunction(invalidInput);
} catch (error) {
  if (error instanceof InvalidInputError) {
    // Handle invalid input
  }
}
```

[Repeat for each public API function/class]

### 4.2 Types & Interfaces

```typescript
// All public types exported by the library

interface Options {
  option1?: string;
  option2?: boolean;
}

interface ReturnType {
  result: string;
  metadata: Metadata;
}

type InputType = string | Buffer;

// Enums
enum Mode {
  Fast = 'fast',
  Accurate = 'accurate'
}
```

### 4.3 Error Types

```typescript
// Custom error classes

class LibraryError extends Error {
  code: string;
  cause?: Error;
}

class InvalidInputError extends LibraryError {
  code = 'INVALID_INPUT';
}

class ConfigurationError extends LibraryError {
  code = 'CONFIGURATION_ERROR';
}
```

---

## 5. Feature Requirements

### 5.1 Core Features

| Feature | Description | Priority |
|---------|-------------|----------|
| [Feature 1] | [What it does] | Must Have |
| [Feature 2] | [What it does] | Must Have |
| [Feature 3] | [What it does] | Should Have |

### 5.2 Feature: [Feature Name]

| Aspect | Description |
|--------|-------------|
| **Description** | [Detailed description] |
| **API** | [Function/method name] |
| **Input** | [Expected input] |
| **Output** | [Expected output] |
| **Priority** | Must Have / Should Have / Nice to Have |

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Edge Cases:**
- [Edge case 1]: [Expected behavior]
- [Edge case 2]: [Expected behavior]

[Repeat for each feature]

---

## 6. Configuration

### 6.1 Global Configuration

```typescript
import { configure } from '[package-name]';

configure({
  setting1: 'value',
  setting2: true
});
```

### 6.2 Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `setting1` | `string` | `'default'` | [Description] |
| `setting2` | `boolean` | `false` | [Description] |

### 6.3 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LIB_DEBUG` | Enable debug logging | `false` |
| `LIB_[SETTING]` | Override [setting] | - |

---

## 7. Integration Patterns

### 7.1 Framework Integration

#### React

```jsx
import { useLibrary } from '[package-name]/react';

function Component() {
  const { result, loading, error } = useLibrary(input);
  // ...
}
```

#### Node.js

```javascript
const { mainFunction } = require('[package-name]');

async function handler(req, res) {
  const result = await mainFunction(req.body);
  res.json(result);
}
```

[Add integrations as applicable]

### 7.2 Plugin/Extension System

```typescript
// If the library supports plugins
import { registerPlugin, Plugin } from '[package-name]';

const myPlugin: Plugin = {
  name: 'my-plugin',
  hooks: {
    beforeProcess: (input) => { /* ... */ },
    afterProcess: (result) => { /* ... */ }
  }
};

registerPlugin(myPlugin);
```

---

## 8. Performance Requirements

### 8.1 Benchmarks

| Operation | Target | Measurement |
|-----------|--------|-------------|
| [Operation 1] | < [X] ms | [How measured] |
| [Operation 2] | < [X] ms | [How measured] |
| Memory usage | < [X] MB | [For typical use case] |

### 8.2 Bundle Size

| Build | Target Size |
|-------|-------------|
| Minified | < [X] KB |
| Minified + Gzipped | < [X] KB |
| ESM tree-shakeable | [Expected savings] |

### 8.3 Optimization Strategies

| Strategy | Implementation |
|----------|----------------|
| Lazy loading | [Approach] |
| Caching | [Approach] |
| Tree shaking | [ESM exports structure] |

---

## 9. Compatibility

### 9.1 Runtime Support

| Runtime | Minimum Version | Notes |
|---------|-----------------|-------|
| Node.js | [X].x | [Notes] |
| Browser | [ES version] | [Notes] |
| Deno | [Version] | [If supported] |
| Bun | [Version] | [If supported] |

### 9.2 Browser Support

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | [Version] |
| Firefox | [Version] |
| Safari | [Version] |
| Edge | [Version] |

### 9.3 TypeScript Support

| Aspect | Support |
|--------|---------|
| TypeScript version | [X].x+ |
| Type definitions | Included / @types package |
| Strict mode | [Supported/Required] |

---

## 10. Dependencies

### 10.1 Runtime Dependencies

| Dependency | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| [dep-name] | ^[X.Y.Z] | [Why needed] | [Why this dep] |

### 10.2 Peer Dependencies

| Dependency | Version | Required |
|------------|---------|----------|
| [peer-dep] | ^[X.Y.Z] | [Yes/No] |

### 10.3 Development Dependencies

| Category | Key Tools |
|----------|-----------|
| Testing | [Jest/Vitest/etc.] |
| Linting | [ESLint config] |
| Building | [Rollup/esbuild/etc.] |
| Documentation | [TypeDoc/etc.] |

---

## 11. Error Handling

### 11.1 Error Philosophy

| Aspect | Approach |
|--------|----------|
| Validation | [Fail fast / Lenient] |
| Async errors | [Promises / Callbacks / Both] |
| Error messages | [Detailed / Minimal] |
| Stack traces | [Preserved / Cleaned] |

### 11.2 Error Recovery

| Scenario | Behavior |
|----------|----------|
| Invalid input | [Throw / Return null / Coerce] |
| Network failure | [Retry strategy] |
| Resource exhaustion | [Handling] |

---

## 12. Security Considerations

### 12.1 Security Requirements

| Requirement | Implementation |
|-------------|----------------|
| Input sanitization | [Approach] |
| Dependency auditing | [Process] |
| Sensitive data handling | [Approach] |

### 12.2 Known Limitations

| Limitation | Mitigation |
|------------|------------|
| [Security limitation] | [How users should handle] |

---

## 13. Documentation Requirements

### 13.1 Documentation Structure

| Document | Priority | Format |
|----------|----------|--------|
| README | Must Have | Markdown |
| API Reference | Must Have | Generated from TSDoc |
| Getting Started | Must Have | Markdown |
| Examples | Should Have | Code + Markdown |
| Migration Guide | Should Have | Markdown |
| Contributing Guide | Should Have | Markdown |

### 13.2 Code Examples

| Example | Complexity | Covers |
|---------|------------|--------|
| Basic usage | Simple | Core API |
| [Example 2] | Medium | [Features] |
| [Example 3] | Advanced | [Features] |

### 13.3 API Documentation Standard

```typescript
/**
 * Brief description of the function.
 *
 * Longer description with details about behavior,
 * edge cases, and usage notes.
 *
 * @param param1 - Description of param1
 * @param param2 - Description of param2
 * @returns Description of return value
 * @throws {ErrorType} When this error occurs
 *
 * @example
 * // Example with explanation
 * const result = function('input');
 *
 * @see {@link RelatedFunction} for related functionality
 * @since 1.0.0
 */
```

---

## 14. Testing Requirements

### 14.1 Test Coverage

| Test Type | Coverage Target |
|-----------|-----------------|
| Unit tests | [X]% |
| Integration tests | Critical paths |
| Property-based tests | [If applicable] |
| Browser tests | Cross-browser matrix |

### 14.2 Test Categories

| Category | Focus Areas |
|----------|-------------|
| Functionality | All public API functions |
| Edge cases | Null, undefined, empty, large inputs |
| Error handling | All error paths |
| Types | TypeScript compilation |
| Performance | Regression tests |

### 14.3 CI/CD Pipeline

| Stage | Actions |
|-------|---------|
| Lint | ESLint, Prettier |
| Type check | TypeScript |
| Test | Jest/Vitest across Node versions |
| Build | All output formats |
| Size check | Bundle size limits |

---

## 15. Versioning & Releases

### 15.1 Versioning Strategy

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Breaking changes | Major | 1.0.0 → 2.0.0 |
| New features | Minor | 1.0.0 → 1.1.0 |
| Bug fixes | Patch | 1.0.0 → 1.0.1 |

### 15.2 Release Process

| Step | Action |
|------|--------|
| 1 | Update CHANGELOG |
| 2 | Bump version |
| 3 | Run full test suite |
| 4 | Build all outputs |
| 5 | Publish to registry |
| 6 | Create GitHub release |
| 7 | Update documentation |

### 15.3 Deprecation Policy

| Stage | Timeline | Action |
|-------|----------|--------|
| Deprecation notice | Version N | Add @deprecated, console warning |
| Documentation update | Version N | Update docs with alternatives |
| Removal | Version N+2 (major) | Remove deprecated API |

---

## 16. Build Outputs

### 16.1 Distribution Formats

| Format | File | Use Case |
|--------|------|----------|
| ESM | `dist/index.mjs` | Modern bundlers, Node.js ESM |
| CJS | `dist/index.cjs` | Node.js require(), older bundlers |
| UMD | `dist/index.umd.js` | Script tags, AMD |
| Types | `dist/index.d.ts` | TypeScript consumers |

### 16.2 Package.json Exports

```json
{
  "name": "[package-name]",
  "version": "1.0.0",
  "main": "./dist/index.cjs",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs",
      "types": "./dist/index.d.ts"
    },
    "./subpath": {
      "import": "./dist/subpath.mjs",
      "require": "./dist/subpath.cjs"
    }
  },
  "files": ["dist"],
  "sideEffects": false
}
```

---

## 17. Release Planning

### 17.1 MVP (v1.0.0)

- [ ] Core functionality
- [ ] TypeScript support
- [ ] Basic documentation
- [ ] Unit tests ([X]% coverage)

### 17.2 v1.1.0

- [ ] [Additional feature]
- [ ] [Framework integration]
- [ ] [Enhanced documentation]

### 17.3 Future Roadmap

| Version | Features |
|---------|----------|
| v1.2.0 | [Planned features] |
| v2.0.0 | [Breaking changes planned] |

---

## 18. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes in dependencies | Medium | High | Lock versions, audit regularly |
| Browser compatibility issues | Medium | Medium | Comprehensive browser testing |
| [Risk] | [Likelihood] | [Impact] | [Mitigation] |

---

## 19. Open Questions

| Question | Owner | Resolution |
|----------|-------|------------|
| [Question] | [Person] | [Pending/Resolved] |

---

## 20. Appendices

### A. Similar Libraries & Differentiation

| Library | How We Differ |
|---------|---------------|
| [Competitor 1] | [Differentiation] |
| [Competitor 2] | [Differentiation] |

### B. Glossary

| Term | Definition |
|------|------------|
| [Term] | [Definition] |

### C. References

- [Relevant standards or specifications]
- [Design inspirations]

---

*Generated with Claudestrator PRD Generator*
