# V2 Future Features (Deferred)

These documents describe features that are **deferred to v2** after the MVP is stable.

## Why Deferred?

The MVP focuses on minimal orchestrator context. These features add significant token overhead:

| Feature | Token Cost | Status |
|---------|------------|--------|
| Knowledge Graph | ~500-2000/query | Deferred |
| Computed Context | ~500-1000/agent | Deferred |
| Structured Handoffs | ~500/agent | Deferred |
| Hot/Cold State | ~500/read | Deferred |
| Strategy Evolution | ~200/update | Deferred |
| Prompt Caching | Optimization | Deferred |

## MVP vs V2

| MVP | V2 (Future) |
|-----|-------------|
| Completion markers only | + Structured handoffs |
| task_queue.md | + Knowledge graph |
| session_state.md | + Hot/cold state separation |
| No learning | + Strategy evolution |
| Simple prompts | + Prompt caching |

## Implementation Plan

When MVP is stable, these features will be implemented via a **Memory Agent** that runs between loops in its own isolated context:

```
End of Loop ──▶ MEMORY AGENT ──▶ loop_summary.md ──▶ Next Loop
                     │
                     ├── Read git diff
                     ├── Extract patterns/gotchas (handoff_schema.md)
                     ├── Update knowledge_graph.json
                     ├── Evolve strategies (strategy_evolution.md)
                     └── Write 500-token summary
```

The orchestrator never loads these features directly - only reads the Memory Agent's summary.

## Documents

| Document | Description |
|----------|-------------|
| [computed_context.md](computed_context.md) | Dynamic context computation per-agent |
| [handoff_schema.md](handoff_schema.md) | YAML schema for structured agent handoffs |
| [knowledge_graph.md](knowledge_graph.md) | Tag-based retrieval of project knowledge |
| [orchestrator_memory.md](orchestrator_memory.md) | Long-term memory persistence |
| [prompt_caching.md](prompt_caching.md) | Cache-optimized prompt structure |
| [state_management.md](state_management.md) | Hot/cold state separation |
| [strategy_evolution.md](strategy_evolution.md) | Adaptive learning from feedback |

---

*These features are documented but not active in MVP.*
