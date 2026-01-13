---
name: HTML5 Game Development Workflow
id: html5_game_dev_workflow
version: 1.0
category: implementation
domain: [game, web]
task_types: [planning, implementation, workflow]
keywords: [html5, game, workflow, canvas, javascript, single-file, browser, arcade, casual]
complexity: [normal, complex]
pairs_with: [html5_canvas, game_feel, svg_asset_generator, game_designer]
source: local
---

# HTML5 Game Development Workflow

## Overview
Multi-agent workflow for building self-contained HTML5 games using Claude Code. Distilled from the "Turtle Rescue" development session.

## Constraints
- **Single file output**: All JS, CSS, assets inline in one `.html` file
- **No external dependencies**: SVG/CSS only for graphics
- **Scope control**: 3-7 mechanics, 500-2500 lines of code
- **Autonomous execution**: Minimal user intervention after initial spec

---

## Agent Workflow Architecture

### Agent Hierarchy
```
ORCHESTRATOR (Main Claude session)
└── Task Agents (spawned as needed)
    ├── Design Agent (specs, GDD, feature definitions)
    ├── Implementation Agent (code changes)
    ├── Asset Agent (SVG sprites, animations)
    ├── Polish Agent (game feel, juice, effects)
    └── QA Agent (verification, bug hunting)
```

### Model Selection by Task Complexity
| Complexity | Model | Use Case |
|------------|-------|----------|
| Easy | Haiku | Constants, text changes, simple searches |
| Normal | Sonnet | Features, bug fixes, QA, single-system changes |
| Complex | Opus | Architecture, multi-system, algorithms |

See: `agent_model_selection` skill for detailed criteria.

---

## Development Phases

### Phase 1: Specification
- Gather game concept from user
- Define core mechanics (3-7)
- Establish visual style
- Set success criteria
- Document in plan file

### Phase 2: Design
**Design Agent tasks:**
- Core loop definition
- Mechanic specifications with parameters
- Scoring/progression systems
- Game states (title, play, pause, gameover)
- Edge cases documentation

### Phase 3: Asset Generation
**Asset Agent tasks:**
- Player sprite SVG
- Entity sprites (enemies, obstacles, collectibles)
- UI elements (HUD, buttons)
- Animation frames
- Particle effect shapes
- Color palette (5-7 colors)

### Phase 4: Implementation
**Implementation Agent tasks:**
- HTML5 Canvas boilerplate
- Game loop (requestAnimationFrame, 60 FPS)
- Input handling (keyboard, mouse, touch)
- Core mechanics one at a time
- Collision detection
- State machine
- Scoring/lives system
- localStorage persistence

### Phase 5: Polish
**Polish Agent tasks:**
- Screen shake on impacts
- Particle effects
- Easing animations
- Visual feedback (flashes, glows)
- Sound (optional, Web Audio API)

### Phase 6: QA & Iteration
**QA Agent tasks:**
- Verify all mechanics work
- Check state transitions
- Performance validation (60 FPS)
- Edge case testing
- Code quality review

**Iteration loop:** Fix → QA → Repeat (max 3 iterations per issue)

---

## Task Agent Prompt Patterns

### Implementation Agent
```
You are an HTML5 game implementation agent. Implement [FEATURE] in [FILE].

## Requirements
- [Specific requirements]

## Technical Constraints
- [Constraints]

## Implementation Steps
1. Read relevant sections of the file
2. [Specific steps]

## Deliverables
Return summary of changes with line numbers.
```

### QA Agent
```
You are a QA agent for HTML5 games. Verify [FEATURES] in [FILE].

## Features to Verify
1. [Feature]: Check [specific criteria]
2. [Feature]: Check [specific criteria]

## Deliverables
Return QA report with:
- PASS/FAIL status for each item
- Any issues found
- Overall readiness assessment
```

---

## Code Patterns

### Game Loop
```javascript
let lastTime = 0;
function gameLoop(currentTime) {
    const deltaTime = (currentTime - lastTime) / 1000;
    lastTime = currentTime;

    update(deltaTime);
    render();

    requestAnimationFrame(gameLoop);
}
```

### State Machine
```javascript
const GameState = {
    TITLE: 'title',
    PLAYING: 'playing',
    PAUSED: 'paused',
    GAMEOVER: 'gameover'
};
let currentState = GameState.TITLE;
```

### SVG as Data URI
```javascript
const SPRITES = {
    player: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 32">...</svg>`
};

function loadSprite(svgString) {
    return new Promise(resolve => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.src = 'data:image/svg+xml;base64,' + btoa(svgString);
    });
}
```

### Collision Detection (AABB)
```javascript
function checkCollision(a, b) {
    return a.x < b.x + b.width &&
           a.x + a.width > b.x &&
           a.y < b.y + b.height &&
           a.y + a.height > b.y;
}
```

---

## Quality Gates

| Gate | Criteria | Owner |
|------|----------|-------|
| Design Complete | Specs approved, mechanics defined | Design Agent |
| Assets Complete | All SVGs generated | Asset Agent |
| MVP Playable | Core loop works | Implementation Agent |
| Polish Complete | "Feels good" | Polish Agent |
| QA Pass | No critical bugs, 60 FPS | QA Agent |

---

## Lessons Learned

1. **Always use agents for implementation** - Keeps orchestrator context clean
2. **QA after every feature batch** - Catch bugs early
3. **Specify model explicitly** - Match complexity to capability
4. **Give agents specific file sections** - Avoid context overflow
5. **Track progress with TodoWrite** - Visibility and focus
6. **Fix bugs immediately** - Don't batch, iterate quickly
7. **User stays high-level** - Orchestrator handles details
