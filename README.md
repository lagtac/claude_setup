# Claude Code Configuration

This directory contains reusable Claude Code configuration shared across projects via symlink.

## When to Use Each Planning Tool

There are three overlapping approaches to planning and analysis. Here's when to use each:

---

### `/task` — Direct implementation with structured requirements gathering

Use when you have a concrete, bounded coding task and want Claude to gather requirements before diving in. Enforces: ask clarifying questions → outline approach → implement → review. No persistent output, no subagent.

> "Fix the image upload validation" / "Add pagination to this table"

---

### `/plan` — Architecture RFC via Opus subagent

Use when the scope is uncertain or the design decisions matter before any code is written. Launches an Opus subagent that explores the codebase, challenges assumptions, and writes a persistent plan document to `$planDirectory/`. Best for multi-file features or anything where the *how* isn't obvious.

> "Plan how to integrate the ML results caching layer" / "Plan the notification system"

---

### Superpowers skills — Proactively triggered by Claude, not you

You don't call these — Claude invokes them automatically based on what you're asking:

| Skill | When Claude triggers it |
|---|---|
| `brainstorming` | Before building any feature or component |
| `writing-plans` | When you have requirements and need a granular TDD execution spec |
| `executing-plans` | When running a written plan in a fresh session |
| `systematic-debugging` | On any bug or test failure |

---

### Decision rule

| Situation | Tool |
|---|---|
| Small task, clear requirements | Nothing (or `/task` for structured requirements gathering) |
| Non-trivial feature, uncertain scope | `/plan` first, then implement |
| Complex spec already written | `superpowers:writing-plans` → `superpowers:executing-plans` |
| Bug or test failure | `superpowers:systematic-debugging` (Claude auto-invokes) |

The superpowers skills operate *within* a session. `/plan` produces a persistent artifact *between* sessions.
