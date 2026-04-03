# Claude Setup Plugin

A Claude Code plugin (`my`) providing reusable slash commands, subagent definitions, and skills for development workflows.

## Architecture

- **`.claude-plugin/plugin.json`** — Plugin manifest (name, version, description). Commands and agents are auto-discovered.
- **`settings.json`** — Plugin-scoped deny-list safety defaults.
- **`commands/`** — Slash commands. Each `.md` file is a prompt template; `$ARGUMENTS` is replaced with user input.
- **`agents/`** — Subagent definitions with frontmatter (`name`, `description`, `tools`, `model`). Commands reference agents by name.
- **`skills/`** — Multi-file skill directories. Each contains a `SKILL.md` with frontmatter and prompt.

## Editing Plugin Files

- Command files are prompt templates — `$ARGUMENTS` is a placeholder, not a variable to define.
- Agent frontmatter fields (`name`, `description`, `tools`, `model`) are parsed by Claude Code; keep them accurate.
- The plugin manifest (`.claude-plugin/plugin.json`) must accurately list the `commands` and `agents` directory paths.
- Agents are self-contained — they do not inherit CLAUDE.md. Any standards they must follow need to be embedded directly in the agent file.
