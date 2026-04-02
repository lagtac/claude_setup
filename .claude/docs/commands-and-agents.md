## Command to Agent Mapping

| Command | Agent | Model | Purpose |
|---------|-------|-------|---------|
| `/my:plan` | `planner` | opus | Explore codebase, write implementation plan |
| `/my:code-review` | `code-reviewer` | opus | Dual-perspective review of uncommitted changes |
| `/my:summarize` | `summarizer` | sonnet | Compare plan/review against git diff |
| `/my:laravel-*` | `laravel-fullstack-expert` | — | Laravel-specific analysis |

## Command Selection Guide

When the user describes work, suggest the appropriate command:

| Situation | Command |
|---|---|
| Concrete, bounded task with clear requirements | `/my:task` (or no command — just do it) |
| Non-trivial feature, uncertain scope or design | `/my:plan` to explore and write a plan first |
| Reviewing uncommitted changes | `/my:code-review` |
| Comparing implementation against a plan | `/my:summarize` |
| Ready to commit | `/my:commit` |
| Laravel project debugging or review | `/my:laravel-debug`, `/my:laravel-code-review` |

### Laravel-Specific Commands

Three commands (`/my:laravel-debug`, `/my:laravel-migration-check`, `/my:laravel-code-review`) and one agent (`laravel-fullstack-expert`) target Laravel full-stack projects.
