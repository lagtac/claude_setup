## Instructions

### Commit Style

Conventional Commits specification: `feat:`, `fix:`, `refactor:`, etc.

### Plans Directory

The `/my:plan`, `/my:code-review`, and `/my:summarize` commands write output to `$planDirectory/`. This variable is resolved from `plansDirectory` in the consuming project's `.claude/settings.json` — it is not set by the plugin.

### Editing Guidelines

- Command files are prompt templates — `$ARGUMENTS` is a placeholder, not a variable to define.
- Agent frontmatter fields (`name`, `description`, `tools`, `model`) are parsed by Claude Code; keep them accurate.
- The plugin manifest (`.claude-plugin/plugin.json`) must accurately list the `commands` and `agents` directory paths.
