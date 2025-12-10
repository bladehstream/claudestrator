---
name: MCP Server Builder
id: mcp_builder
version: 1.0
category: implementation
domain: [backend, api, integration]
task_types: [implementation, design, planning]
keywords: [mcp, model context protocol, server, api, integration, tools, llm, agent, typescript, python, fastmcp]
complexity: [complex]
pairs_with: [api_designer, documentation]
source: https://github.com/anthropics/skills/tree/main/skills/mcp-builder
---

# MCP Server Builder

## Role

Create high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).

## Overview

The quality of an MCP server is measured by how well it enables LLMs to accomplish real-world tasks.

## Four-Phase Workflow

### Phase 1: Deep Research and Planning

#### 1.1 Understand Modern MCP Design

**API Coverage vs. Workflow Tools**:
- Balance comprehensive API endpoint coverage with specialized workflow tools
- Workflow tools can be more convenient for specific tasks
- Comprehensive coverage gives agents flexibility to compose operations
- When uncertain, prioritize comprehensive API coverage

**Tool Naming and Discoverability**:
- Clear, descriptive names help agents find tools quickly
- Use consistent prefixes (e.g., `github_create_issue`, `github_list_repos`)
- Action-oriented naming

**Context Management**:
- Concise tool descriptions
- Support filtering and pagination
- Return focused, relevant data

**Actionable Error Messages**:
- Guide agents toward solutions
- Include specific suggestions and next steps

#### 1.2 Study MCP Protocol Documentation

Start with: `https://modelcontextprotocol.io/sitemap.xml`

Key areas:
- Specification overview and architecture
- Transport mechanisms (streamable HTTP, stdio)
- Tool, resource, and prompt definitions

#### 1.3 Study Framework Documentation

**Recommended stack**:
- **Language**: TypeScript (high-quality SDK support)
- **Transport**: Streamable HTTP for remote servers, stdio for local servers

**SDK Resources**:
- TypeScript: `https://github.com/modelcontextprotocol/typescript-sdk`
- Python: `https://github.com/modelcontextprotocol/python-sdk`

#### 1.4 Plan Implementation

- Review service API documentation
- Identify key endpoints and auth requirements
- Prioritize comprehensive API coverage
- List endpoints to implement

### Phase 2: Implementation

#### 2.1 Project Structure

**TypeScript**:
```
mcp-server/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts        # Entry point
│   ├── server.ts       # Server setup
│   ├── tools/          # Tool implementations
│   ├── api/            # API client
│   └── utils/          # Helpers
```

**Python**:
```
mcp_server/
├── pyproject.toml
├── src/
│   └── mcp_server/
│       ├── __init__.py
│       ├── server.py
│       ├── tools/
│       └── api/
```

#### 2.2 Core Infrastructure

Create shared utilities:
- API client with authentication
- Error handling helpers
- Response formatting (JSON/Markdown)
- Pagination support

#### 2.3 Implement Tools

**For each tool**:

**Input Schema** (TypeScript with Zod):
```typescript
const createIssueSchema = z.object({
  repo: z.string().describe("Repository in format owner/repo"),
  title: z.string().describe("Issue title"),
  body: z.string().optional().describe("Issue body markdown"),
  labels: z.array(z.string()).optional().describe("Labels to apply"),
});
```

**Output Schema**:
- Define `outputSchema` where possible
- Use `structuredContent` in responses
- Helps clients process outputs

**Tool Description**:
- Concise functionality summary
- Parameter descriptions
- Return type schema

**Implementation**:
- Async/await for I/O
- Proper error handling
- Support pagination
- Return both text and structured data

**Annotations**:
```typescript
{
  readOnlyHint: true,      // Doesn't modify state
  destructiveHint: false,  // Doesn't delete data
  idempotentHint: true,    // Safe to retry
  openWorldHint: false,    // Closed set of results
}
```

### Phase 3: Review and Test

#### 3.1 Code Quality
- No duplicated code (DRY)
- Consistent error handling
- Full type coverage
- Clear tool descriptions

#### 3.2 Build and Test

**TypeScript**:
```bash
npm run build
npx @modelcontextprotocol/inspector
```

**Python**:
```bash
python -m py_compile server.py
# Test with MCP Inspector
```

### Phase 4: Create Evaluations

#### 4.1 Evaluation Purpose
Test whether LLMs can effectively use your MCP server to answer realistic, complex questions.

#### 4.2 Create 10 Evaluation Questions

Process:
1. List available tools
2. Explore available data (READ-ONLY)
3. Generate 10 complex, realistic questions
4. Verify answers yourself

#### 4.3 Evaluation Requirements

Each question must be:
- **Independent**: Not dependent on other questions
- **Read-only**: Only non-destructive operations
- **Complex**: Multiple tool calls required
- **Realistic**: Based on real use cases
- **Verifiable**: Single, clear answer
- **Stable**: Answer won't change over time

#### 4.4 Output Format
```xml
<evaluation>
  <qa_pair>
    <question>Find discussions about AI model launches...</question>
    <answer>3</answer>
  </qa_pair>
</evaluation>
```

## Tool Design Patterns

### CRUD Operations
```typescript
// List resources
server.registerTool("github_list_repos", {
  description: "List repositories for user or org",
  inputSchema: listReposSchema,
  annotations: { readOnlyHint: true },
  handler: async (input) => { /* ... */ }
});

// Get single resource
server.registerTool("github_get_repo", { /* ... */ });

// Create resource
server.registerTool("github_create_issue", {
  annotations: { readOnlyHint: false },
  /* ... */
});

// Update resource
server.registerTool("github_update_issue", { /* ... */ });

// Delete resource
server.registerTool("github_delete_branch", {
  annotations: { destructiveHint: true },
  /* ... */
});
```

### Pagination
```typescript
const listSchema = z.object({
  page: z.number().default(1).describe("Page number"),
  per_page: z.number().default(30).describe("Items per page (max 100)"),
});

// Return pagination info in response
return {
  items: results,
  pagination: {
    page,
    per_page,
    total,
    has_more: page * per_page < total,
  },
};
```

## Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Vague tool names | Hard to discover | Descriptive, prefixed names |
| Missing pagination | Overwhelming results | Support page/per_page |
| Silent failures | Agent confusion | Actionable error messages |
| No type hints | Unsafe usage | Full TypeScript/Pydantic |
| Monolithic tools | Inflexible | Composable CRUD operations |

---

*Skill Version: 1.0*
*Source: Anthropic mcp-builder skill*
