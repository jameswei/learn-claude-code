# learn-claude-code

This is a learning repository for harness engineering — building the environment
that surrounds an agent model. It uses Claude Code as a concrete example to
reverse-engineer the mechanisms of a production agent harness.

## What This Repo Is

12 progressive Python sessions (s01–s12), each adding one harness mechanism:

```
s01  agent loop          s07  task system
s02  tool use            s08  background tasks
s03  todo/planning       s09  agent teams
s04  subagents           s10  team protocols
s05  skill loading       s11  autonomous agents
s06  context compaction  s12  worktree isolation
```

The `agents/` directory contains the implementations.
The `docs/en/` directory contains the matching explanations.

## Coding Conventions

- All agent implementations are plain Python, no frameworks
- Each session file is self-contained: one file, one mechanism
- Keep the agent loop itself unchanged across sessions — only add harness layers
- Use `print()` for educational output (this is a learning repo, not production)
- Session files are named `s##_topic.py` — do not rename them

## Domain Knowledge

Key concept: **the model is the agent; the code is the harness.**

- `TOOL_HANDLERS` dict — maps tool names to Python functions (s02 pattern)
- `messages[]` — the agent's working memory; subagents get their own copy (s04)
- Skills are injected via `tool_result`, not the system prompt (s05)
- Context compaction summarizes old messages, not the task state (s06)
- Tasks persist to disk as JSON; the agent survives restarts (s07)

## What to Avoid

- Do not add external dependencies beyond `anthropic` and standard library
- Do not refactor working session files — they exist as learning artifacts
- Do not merge session mechanisms; one session = one concept
