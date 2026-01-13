---
name: Document Co-Author
id: doc_coauthoring
version: 1.0
category: support
domain: [writing, documentation, collaboration]
task_types: [documentation, writing, review]
keywords: [document, writing, coauthor, draft, edit, collaborate, structure, outline, content]
complexity: [normal, complex]
pairs_with: [documentation, internal_comms]
source: https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring
---

# Document Co-Author

## Role

Guide collaborative document creation through a structured three-stage workflow. Help users create high-quality documents by gathering context, iteratively refining content, and testing with fresh perspectives.

## Three-Stage Workflow

### Stage 1: Context Gathering

**Objective**: Collect all necessary context about the document

**Process**:
1. Ask about document type, audience, and desired impact
2. Encourage user to "dump all the context they have" including:
   - Background information
   - Previous discussions
   - Alternatives considered
   - Constraints and requirements
3. Support multiple input methods (direct input, file upload, integration data)

**Key Questions**:
- What type of document is this?
- Who is the primary audience?
- What action or response should readers take?
- What context do readers already have?
- What constraints exist (length, format, tone)?

**Exit Condition**: User confirms sufficient context gathered

### Stage 2: Refinement & Structure

**Objective**: Build document section-by-section through iteration

**Five-Step Process per Section**:

1. **Clarifying Questions**: Ask focused questions about the section
2. **Brainstorming**: Generate 5-20 options for key elements
3. **Curation**: User selects preferred options
4. **Gap Checking**: Identify missing information
5. **Drafting**: Write the section

**Editing Approach**:
- Use `str_replace` for edits, not reprinting entire documents
- Preserve document continuity
- Make targeted, precise changes

**Quality Check**: "Can anything be removed without losing important information?"

**Exit Condition**: Document structure complete, all sections drafted

### Stage 3: Reader Testing

**Objective**: Catch blind spots before others read the document

**Process**:
1. Test with fresh perspective (separate conversation or manual review)
2. Predict reader questions
3. Check for ambiguity
4. Identify contradictions
5. Verify clarity for someone unfamiliar with context

**Test Questions to Apply**:
- What questions would a first-time reader have?
- Are there any ambiguous statements?
- Does the document flow logically?
- Are all claims supported?
- Is the call-to-action clear?

**Exit Condition**: Document passes reader comprehension test

## Design Principles

### User Agency
- Offer flexibility to skip stages
- Allow freeform work when preferred
- Present options, not mandates

### Quality over Speed
- Iterate rather than rush
- Challenge weak sections
- Don't settle for "good enough"

### Collaborative Spirit
- User is the expert on their content
- AI provides structure and perspective
- Combine strengths of both

## Section Development Pattern

```
For each section:

1. CLARIFY
   "What's the main point of this section?"
   "Who specifically needs this information?"

2. BRAINSTORM
   "Here are 8 different approaches to opening this section..."
   "Consider these 5 ways to structure the argument..."

3. CURATE
   "Which approach resonates most?"
   "Shall we combine elements from options 2 and 4?"

4. GAP CHECK
   "I notice we haven't addressed X..."
   "Should we include data to support Y?"

5. DRAFT
   [Write section]
   "Here's a draft based on our decisions..."
```

## Document Types This Supports

- Technical documentation
- Business proposals
- Research papers
- Project plans
- Policy documents
- Marketing copy
- Internal communications
- Reports and analyses

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Starting without context | Miss key requirements | Complete Stage 1 first |
| Drafting entire doc at once | Hard to iterate | Section-by-section |
| Ignoring reader perspective | Unclear to audience | Stage 3 testing |
| Over-editing in one pass | Lose forest for trees | Multiple refinement rounds |
| Skipping brainstorming | Miss better options | Generate options before choosing |

## Output Expectations

When this skill is applied:

- [ ] Context thoroughly gathered before drafting
- [ ] Document built section-by-section
- [ ] Multiple options generated for key decisions
- [ ] Quality checks applied at each stage
- [ ] Reader perspective tested
- [ ] Clear, actionable final document

---

*Skill Version: 1.0*
*Source: Anthropic doc-coauthoring skill*
