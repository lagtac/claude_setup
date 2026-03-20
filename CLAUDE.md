# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A Claude Code plugin (`my`) that provides reusable slash commands and subagent definitions for development workflows. Installed via `claude plugin add` — no symlinks needed.

## Architecture

- **`.claude-plugin/plugin.json`** — Plugin manifest. Declares the plugin name (`my`), version, and paths to commands and agents.
- **`settings.json`** — Plugin-scoped deny-list safety defaults (blocks dangerous Bash commands and `.env` reads).
- **`commands/`** — Slash commands (e.g., `/my:plan`, `/my:commit`). Each `.md` file is a prompt template; `$ARGUMENTS` is replaced with user input.
- **`agents/`** — Subagent definitions with frontmatter (`name`, `description`, `tools`, `model`). Commands reference agents by name (e.g., `/my:plan` dispatches the `planner` agent).

## Key Conventions

### Commit Style
Conventional Commits specification: `feat:`, `fix:`, `refactor:`, etc.

### Plans Directory
The `/my:plan`, `/my:code-review`, and `/my:summarize` commands write output to `$planDirectory/`. This variable is resolved from `plansDirectory` in the consuming project's `.claude/settings.json` — it is not set by the plugin.

### Laravel-Specific Commands
Three commands (`/my:laravel-debug`, `/my:laravel-migration-check`, `/my:laravel-code-review`) and one agent (`laravel-fullstack-expert`) target Laravel full-stack projects.

## Command to Agent Mapping

| Command | Agent | Model | Purpose |
|---------|-------|-------|---------|
| `/my:plan` | `planner` | opus | Explore codebase, write implementation plan |
| `/my:code-review` | `code-reviewer` | opus | Dual-perspective review of uncommitted changes |
| `/my:summarize` | `summarizer` | sonnet | Compare plan/review against git diff |
| `/my:laravel-*` | `laravel-fullstack-expert` | — | Laravel-specific analysis |

## Editing Guidelines

- Command files are prompt templates — `$ARGUMENTS` is a placeholder, not a variable to define.
- Agent frontmatter fields (`name`, `description`, `tools`, `model`) are parsed by Claude Code; keep them accurate.
- The plugin manifest (`.claude-plugin/plugin.json`) must accurately list the `commands` and `agents` directory paths.
