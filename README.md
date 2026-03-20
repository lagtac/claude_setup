# claude-setup

A Claude Code plugin providing personal commands and agents for development workflows.

## Commands

| Command | Description |
|---------|-------------|
| `/my:plan` | Launch an Opus subagent to explore the codebase and write an implementation plan |
| `/my:code-review` | Dual-perspective code review of uncommitted changes |
| `/my:summarize` | Compare a plan/review against the actual git diff |
| `/my:commit` | Structured commit workflow |
| `/my:push` | Push with pre-push checks |
| `/my:task` | Direct implementation with structured requirements gathering |
| `/my:optimize-prompt` | Optimize a prompt template |
| `/my:clean-gone-branches` | Clean up local branches whose remote is gone |
| `/my:laravel-debug` | Laravel-specific debugging |
| `/my:laravel-migration-check` | Check Laravel migrations |
| `/my:laravel-code-review` | Laravel-focused code review |

## Agents

| Agent | Model | Used by |
|-------|-------|---------|
| `planner` | opus | `/my:plan` |
| `code-reviewer` | opus | `/my:code-review` |
| `summarizer` | sonnet | `/my:summarize` |
| `laravel-fullstack-expert` | — | `/my:laravel-*` |

## Installation

From a local path:

```bash
claude plugin add /path/to/claude-setup
```

Or from a git remote:

```bash
claude plugin add https://github.com/your-user/claude-setup.git
```

## Recommended Project Settings

The plugin only ships deny-list safety defaults. Add these to your project's `.claude/settings.json` as needed:

```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "WebFetch(*)",
      "WebSearch"
    ]
  },
  "plansDirectory": "./docs/plans",
  "autoMemoryEnabled": true,
  "includeCoAuthoredBy": true,
  "enableAllProjectMcpServers": true
}
```

**Important:** `$planDirectory` must be set in your project settings (via `plansDirectory`) for the `/my:plan`, `/my:code-review`, and `/my:summarize` commands to write their output files.

## When to Use Each Planning Tool

### `/my:task` — Direct implementation with structured requirements gathering

Use when you have a concrete, bounded coding task and want Claude to gather requirements before diving in.

> "Fix the image upload validation" / "Add pagination to this table"

### `/my:plan` — Architecture RFC via Opus subagent

Use when the scope is uncertain or design decisions matter before writing code. The subagent explores the codebase, challenges assumptions, and writes a persistent plan to `$planDirectory/`.

> "Plan how to integrate the ML results caching layer" / "Plan the notification system"

### Decision rule

| Situation | Tool |
|---|---|
| Small task, clear requirements | Nothing (or `/my:task`) |
| Non-trivial feature, uncertain scope | `/my:plan` first, then implement |
| Complex spec already written | `superpowers:writing-plans` then `superpowers:executing-plans` |
| Bug or test failure | `superpowers:systematic-debugging` (auto-invoked) |
