## Overview

A Claude Code plugin (`my`) that provides reusable slash commands and subagent definitions for development workflows. Installed via `claude plugin add` — no symlinks needed.

### Architecture

- **`.claude-plugin/plugin.json`** — Plugin manifest. Declares the plugin name (`my`), version, and paths to commands and agents.
- **`settings.json`** — Plugin-scoped deny-list safety defaults (blocks dangerous Bash commands and `.env` reads).
- **`commands/`** — Slash commands (e.g., `/my:plan`, `/my:commit`). Each `.md` file is a prompt template; `$ARGUMENTS` is replaced with user input.
- **`agents/`** — Subagent definitions with frontmatter (`name`, `description`, `tools`, `model`). Commands reference agents by name (e.g., `/my:plan` dispatches the `planner` agent).
- **`skills/`** — Multi-file skill directories (e.g., `dev-reports/`, `git-squasher/`). Each contains its own prompt and configuration.
