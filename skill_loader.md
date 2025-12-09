# Dynamic Skill Loader Specification

## Overview

The skill loader dynamically discovers and indexes skills at runtime by scanning a configured directory. This eliminates the need for a static manifest file - simply drop skill files into the directory and they become available.

## Configuration

### Skill Directory Location

The orchestrator looks for skills in this order:

1. **User-specified path** (if provided at session start)
2. **Project-local**: `./skills/` or `./.claude/skills/`
3. **User global**: `~/.claude/skills/`
4. **System default**: `~/claudestrator/skills/`

### Specifying Custom Path

At session start, user can specify:
```
"Use skills from /path/to/my/skills"
```

Or in project's `.claude/config.md`:
```yaml
skill_directory: /path/to/skills
```

---

## Discovery Process

### Step 1: Scan Directory

```
FUNCTION discoverSkills(directory):
    skills = []

    FOR each file IN recursiveGlob(directory, "**/*.md"):
        content = readFile(file)
        frontmatter = parseYAMLFrontmatter(content)

        IF frontmatter AND isValidSkillMetadata(frontmatter):
            skill = {
                id: frontmatter.id,
                name: frontmatter.name,
                path: file,
                domain: frontmatter.domain,
                task_types: frontmatter.task_types,
                keywords: frontmatter.keywords,
                complexity: frontmatter.complexity,
                pairs_with: frontmatter.pairs_with,
                content: content  # Full skill definition
            }
            skills.append(skill)
        ELSE:
            log("Skipping invalid skill file: " + file)

    RETURN skills
```

### Step 2: Validate Metadata

Required frontmatter fields:
```yaml
---
name: [required] Human-readable name
id: [required] Unique identifier (lowercase, underscore)
domain: [required] Array of applicable domains
task_types: [required] Array of task types handled
keywords: [required] Array of matching keywords
complexity: [required] Array of complexity levels
pairs_with: [optional] Array of complementary skill IDs
version: [optional] Skill version
---
```

Validation rules:
- `id` must be unique across all skills
- `domain`, `task_types`, `keywords`, `complexity` must be non-empty arrays
- File must have valid YAML frontmatter block

### Step 3: Build Index

```
FUNCTION buildSkillIndex(skills):
    index = {
        by_id: {},           # id -> skill
        by_domain: {},       # domain -> [skills]
        by_task_type: {},    # task_type -> [skills]
        by_keyword: {},      # keyword -> [skills]
        all: skills
    }

    FOR each skill IN skills:
        # Index by ID
        index.by_id[skill.id] = skill

        # Index by domain
        FOR domain IN skill.domain:
            index.by_domain[domain].append(skill)

        # Index by task type
        FOR task_type IN skill.task_types:
            index.by_task_type[task_type].append(skill)

        # Index by keyword
        FOR keyword IN skill.keywords:
            index.by_keyword[keyword.lower()].append(skill)

    RETURN index
```

---

## Runtime Matching

### Query the Index

```
FUNCTION matchSkills(task, index):
    candidates = []
    scores = {}

    # Step 1: Get candidates by task type
    IF task.type IN index.by_task_type:
        candidates = index.by_task_type[task.type]
    ELSE:
        candidates = index.all  # Fallback to all

    # Step 2: Filter by complexity
    candidates = candidates.filter(s =>
        task.complexity IN s.complexity
    )

    # Step 3: Score remaining candidates
    task_keywords = extractKeywords(task.objective)
    project_domains = getProjectDomains()

    FOR skill IN candidates:
        score = 0

        # Domain match (weight: 3)
        IF skill.domain INTERSECTS project_domains:
            score += 3

        # Keyword match (weight: 1 per match)
        FOR keyword IN task_keywords:
            IF keyword.lower() IN skill.keywords:
                score += 1

        scores[skill.id] = score

    # Step 4: Sort and return top matches
    candidates.sortBy(scores, DESC)

    max_skills = CASE task.complexity
        WHEN 'easy' THEN 3
        WHEN 'normal' THEN 7
        WHEN 'complex' THEN 15

    RETURN candidates.take(max_skills)
```

---

## Session Initialization

### Orchestrator Startup Sequence

```
1. DETERMINE skill directory
   - Check user specification
   - Check project config
   - Fall back to defaults

2. DISCOVER skills
   - Scan directory recursively
   - Parse and validate each file
   - Report any invalid files

3. BUILD index
   - Create searchable data structures
   - Log skill count and categories

4. REPORT to user
   "Loaded X skills from /path/to/skills:
    - Implementation: A, B, C
    - Design: D, E
    - Quality: F, G
    - Support: H, I"

5. PROCEED with normal orchestrator flow
```

### Example Output

```
Skill Discovery Complete
========================
Directory: ~/.claude/skills/
Files scanned: 15
Valid skills: 12
Invalid/skipped: 3

Loaded Skills by Category:
- implementation: html5_canvas, game_feel, react_components
- design: game_designer, api_designer
- quality: qa_agent, security_reviewer, user_persona
- support: svg_asset_gen, documentation, refactoring

Ready for task matching.
```

---

## Adding New Skills

### For Users

1. Create a `.md` file with valid frontmatter
2. Drop it in the skill directory (any subdirectory)
3. Start new session - skill is automatically available

### Directory Organization (Optional)

Subdirectories are scanned recursively, so organization is flexible:

```
skills/
├── my-company/
│   ├── internal_api.md
│   └── our_framework.md
├── web/
│   ├── react.md
│   └── vue.md
└── general/
    └── debugging.md
```

Or flat:
```
skills/
├── react.md
├── vue.md
├── internal_api.md
└── debugging.md
```

Both work identically.

---

## Handling Conflicts

### Duplicate IDs

If two skills have the same `id`:
```
WARNING: Duplicate skill ID 'my_skill'
  - /path/to/skills/a/my_skill.md
  - /path/to/skills/b/my_skill.md
Using first found. Rename one to resolve.
```

### Missing Required Fields

```
WARNING: Invalid skill file: /path/to/skills/broken.md
  Missing required field: 'keywords'
  Skipping this skill.
```

---

## Caching (Optional)

For large skill directories, optional caching:

```
skills/
└── .skill_cache.json  # Auto-generated index

Cache invalidation:
- Any .md file modified more recently than cache
- Cache file missing
- User requests refresh
```

Most use cases won't need caching - scanning 50-100 small markdown files is fast.

---

## Integration with Protocol

### Updated Protocol Section

Replace static manifest reference with:

```
Phase 1.3: Load Skills
======================
1. Determine skill directory (user config or default)
2. Scan directory for *.md files with valid frontmatter
3. Build runtime skill index
4. Report loaded skills to user
5. Use index for all subsequent skill matching
```

### Matching Algorithm (unchanged)

The matching algorithm remains the same - it just queries the runtime index instead of a static manifest file.

---

## Benefits

| Aspect | Static Manifest | Dynamic Loading |
|--------|-----------------|-----------------|
| Adding skills | Edit manifest + add file | Just add file |
| Removing skills | Edit manifest + delete file | Just delete file |
| Organization | Must match manifest | Any structure |
| Maintenance | Two places to update | Single source of truth |
| Portability | Copy files + manifest | Just copy files |
| Custom directories | Hardcoded | User configurable |

---

*Specification Version: 1.0*
