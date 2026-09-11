# claude-setup

A Claude Code plugin providing personal commands and agents for development workflows.

## Commands

| Command | Description |
|---------|-------------|
| `/my:soundness-review` | Dual-perspective soundness verdict + plan-alignment, written to `docs/plans/`; or, on a clean tree with a `.md` plan, reviews the plan itself (bug-finding/fix delegated to built-in `/code-review`) |
| `/my:summarize` | Compare a plan/review against the actual git diff |
| `/my:commit` | Structured commit workflow |
| `/my:push` | Push with pre-push checks |
| `/my:optimize-prompt` | Optimize a prompt template |
| `/my:clean-gone-branches` | Clean up local branches whose remote is gone |
| `/my:laravel-debug` | Laravel-specific debugging |
| `/my:laravel-migration-check` | Check Laravel migrations |

## Agents

| Agent | Model | Used by |
|-------|-------|---------|
| `code-reviewer` | opus | `/my:soundness-review` |
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

**Important:** `$planDirectory` must be set in your project settings (via `plansDirectory`) for the `/my:soundness-review` and `/my:summarize` commands to write their output files.

