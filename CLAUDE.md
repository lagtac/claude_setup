# Claude Setup Plugin

A marketplace of Claude Code plugins: method plugins (`my`, `tutor`, `sp`) and neutral tools (`kit`, `vue-lsp`), providing reusable slash commands, subagent definitions, and skills.

## Architecture

The repo is a plugin marketplace (`.claude-plugin/marketplace.json`, which must stay at the repo root). Each plugin lives in `plugins/<name>/`: `my`, `tutor` and `sp` are methods, `kit` holds the neutral tools. The paths below are relative to a plugin folder.

- **`.claude-plugin/plugin.json`** — Plugin manifest (name, description, author, and for a method `dependencies`, its plugin set). No `version` field: the marketplace uses the commit hash, so each commit is a new version. Commands and agents are auto-discovered.
- **`commands/`** — Slash commands. Each `.md` file is a prompt template; `$ARGUMENTS` is replaced with user input.
- **`agents/`** — Subagent definitions with frontmatter (`name`, `description`, `tools`, `model`). Commands reference agents by name.
- **`skills/`** — Multi-file skill directories. Each contains a `SKILL.md` with frontmatter and prompt.
- **`output-styles/`** — A method's forced output style, which holds its rules.

## Editing Plugin Files

- Command files are prompt templates — `$ARGUMENTS` is a placeholder, not a variable to define.
- Agent frontmatter fields (`name`, `description`, `tools`, `model`) are parsed by Claude Code; keep them accurate.
- The plugin manifest (`.claude-plugin/plugin.json`) must accurately list the `commands` and `agents` directory paths.
- Agents are self-contained — they do not inherit CLAUDE.md. Any standards they must follow need to be embedded directly in the agent file.

## Git host

This repo is on GitHub only. It is no longer on GitLab. This replaces the GitLab rules in the `my` method's Git Workflow: when a change needs one (for CI or a link to it), open a pull request with `gh pr create`, not a merge request with `glab`. The worktree and squash-merge rules still apply.

## Project facts

- **Commit scopes:** `my-plugin`, `kit-plugin`, `tutor-plugin`, `sp-plugin`, `global`, `plans`
- **Test command:** `cd plugins/kit && python3 -m unittest discover tests` and `cd plugins/my && python3 -m unittest discover tests`
- **Plans index:** none
- **Remote:** origin (github.com)
