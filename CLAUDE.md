# Claude Setup Plugin

Two Claude Code plugins (`my` and `kit`) providing reusable slash commands, subagent definitions, and skills for development workflows.

## Architecture

The repo is a plugin marketplace (`.claude-plugin/marketplace.json`, which must stay at the repo root). Each plugin lives in `plugins/<name>/`: `my` holds the method, `kit` the neutral tools. The paths below are relative to a plugin folder.

- **`.claude-plugin/plugin.json`** — Plugin manifest (name, description, author). No `version` field: the marketplace uses the commit hash, so each commit is a new version. Commands and agents are auto-discovered.
- **`commands/`** — Slash commands. Each `.md` file is a prompt template; `$ARGUMENTS` is replaced with user input.
- **`agents/`** — Subagent definitions with frontmatter (`name`, `description`, `tools`, `model`). Commands reference agents by name.
- **`skills/`** — Multi-file skill directories. Each contains a `SKILL.md` with frontmatter and prompt.

## Editing Plugin Files

- Command files are prompt templates — `$ARGUMENTS` is a placeholder, not a variable to define.
- Agent frontmatter fields (`name`, `description`, `tools`, `model`) are parsed by Claude Code; keep them accurate.
- The plugin manifest (`.claude-plugin/plugin.json`) must accurately list the `commands` and `agents` directory paths.
- Agents are self-contained — they do not inherit CLAUDE.md. Any standards they must follow need to be embedded directly in the agent file.

## Project facts

- **Method:** my
- **Commit scopes:** `my-plugin`, `kit-plugin`, `global`, `plans`
- **Test command:** `cd plugins/kit && python3 -m unittest discover tests` and `cd plugins/my && python3 -m unittest discover tests`
- **Plans index:** none
- **Remote:** origin (github.com)

@~/.claude/methods/my.md
