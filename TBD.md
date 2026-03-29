The repo is well-structured and covers the core harness engineering concepts thoroughly. Based on the README's own "Scope" section and my knowledge of Claude Code, here are the important areas not covered:

### Explicitly omitted (per your own README):
  1. Hooks system (PreToolUse, PostToolUse, PreCompact, Stop, SubagentStop, etc.) — arguably the most powerful customization mechanism in Claude
  Code. Lets you run shell commands at lifecycle events, enforce guardrails, auto-format, audit tool calls, etc.
  1. Permission governance — trust levels (default, trusted), allowedTools/deniedTools, approval workflows in settings.json
  2. MCP runtime details — you have a playground server but no doc on transport layers, OAuth, resource subscriptions

### Not mentioned at all:
  4. CLAUDE.md files — project-level, user-level, and directory-level memory that persists across sessions. This is how real teams ship institutional
   knowledge into the harness. Probably the most practically important missing topic.
  5. settings.json configuration — the full schema: env, mcpServers, permissions, hooks, model overrides, etc.
  6. Session resume / --continue / --resume — how the CLI manages conversation state across invocations
  7. /compact manual trigger and compact customization — you cover auto-compaction but not the user-driven workflow
  8. IDE integrations — VS Code / JetBrains differ from CLI in meaningful ways (inline diff views, terminal embedding)

**The single highest-value gap** is CLAUDE.md + Hooks together — that's the mechanism real teams use to encode standards, run linters on every tool call, and make harness behavior persistent without touching agent code. If you add one more session, it should be that.

The gaps I mentioned — especially CLAUDE.md and Hooks — are worth learning next because they represent the configuration layer of the harness: how you encode domain knowledge and enforce behavior without changing code. That's often where the gap is between a demo agent and one that's actually useful in a real project.