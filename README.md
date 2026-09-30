# claude-setup

My Claude Code setup. The repo is also a plugin marketplace, named
`claude-setup`. It has two parts:

- **`plugins/`** — my local plugins. Every local plugin goes here and gets a
  row in `.claude-plugin/marketplace.json` at the repo root.
  - **`plugins/my/`** — the `my` plugin: skills, commands, agents and hooks
    for development workflows.
  - **`plugins/vue-lsp/`** — the `vue-lsp` plugin: the TypeScript language
    server with `@vue/typescript-plugin`, so LSP also covers `.vue` files. Its
    README lists the npm packages it needs.
- **`global/`** — global instructions (`CLAUDE.md`), path-scoped rules
  (`rules/`) and output styles (`output-styles/`). `~/.claude/CLAUDE.md`,
  `~/.claude/rules` and `~/.claude/output-styles` are symlinks into this
  folder, so edit the files here.

`marketplace.json` stays at the repo root. There, the plugin version is the
commit hash. In a subfolder, Claude Code cannot read the hash, so every version
is `unknown` and an update copies uncommitted edits too.

## Installation

Add the repo as a marketplace once, then install the plugins:

```text
/plugin marketplace add ~/projects/claude-setup
/plugin install my@claude-setup
/plugin install vue-lsp@claude-setup
/plugin disable typescript-lsp@claude-plugins-official
```

`vue-lsp` replaces `typescript-lsp`, so disable that one. Otherwise two servers
both claim `.ts` files.

## Updating

Claude Code runs a copy of each plugin from `~/.claude/plugins/cache/`, not the
files in this repo. The plugins have no `version` field, so the version is the
commit hash. After you commit a change, copy it into the cache and restart:

```bash
claude plugin update my@claude-setup
```

Uncommitted edits never reach the cache. So a skill you are halfway through
editing cannot break other sessions. To try an uncommitted edit, start one
session with the plugin folder instead:

```bash
claude --plugin-dir ~/projects/claude-setup/plugins/my
```

Do not also keep this flag in a shell alias, or every session loads `my` twice.

## Skills

Skills load when a task matches their description, or when you call them
as `/my:<name>`.

- `my:architect` — Writes an architecture brief from the forces on a system,
  before the spec. Output: `docs/plans/YYYY-MM-DD-<slug>-architecture.md`.
- `my:spec-review` — Reviews one `*-spec.md` as a system: components, contracts,
  state ownership, failure spread. Output: a review in `docs/plans/`.
- `my:soundness-review` — Gives a for/against verdict on a diff, or checks a
  diff or plan against its plan. `--plan-only <plan>` reviews the plan and
  never asks, even when the tree is dirty. Output: a review in `docs/plans/`.
  Bug-finding goes to the built-in `/code-review`.
- `my:handoff` — Hands the plan, code or review stage to a new top-level
  session in a tmux window, which stops at fixed gates and marks its window
  `⚠`, and marks it `✓` when it is done. The review stage runs the
  end-of-branch checks and reviews with a fixed prompt, one fix round, and the
  squash-merge after the user's yes. How it works:
  `plugins/my/skills/handoff/README.md`.
  `/my:handoff <stage> <doc>` launches; `/my:handoff run <stage> <doc>` runs.
- `my:briefing` — Writes a plain-English, decision-focused briefing for
  non-technical readers, in `docs/briefings/`.
- `my:roadmap-management` — Edits `ROADMAP.md`: adds rows and moves them between
  status tiers.
- `my:changelog-management` — Edits `CHANGELOG.md` for shipped features, fixes
  and deploy changes.
- `my:dev-reports` — Builds a daily or weekly developer report from git history.
- `my:git-squasher` — Squashes runs of small consecutive commits.
- `my:clean-plans` — Gives undated plan files in `docs/plans/` dated names, updates
  the links to them, and offers to delete files from another project, empty files
  and duplicates.
- `my:tune-claude-instructions` — Audits instruction files (CLAUDE.md, agents,
  commands, skills and their dispatch prompts) for vague directives, tools a
  subagent will not have, stale harness assumptions and contradictions.
- `my:de-slop` — Rewrites text so it does not read as machine-written.
- `my:md-tables` — Turns a Markdown table into one section per row, or
  sections back into a table, with the two filters in `plugins/my/bin/`
  (`md-expand-table.py`, `md-collapse-sections.py`). Claude Code puts that
  folder on PATH in its sessions only; your shell finds them through symlinks
  in `~/bin`. Tests: `cd plugins/my && python3 -m unittest discover tests`.

## Commands

- `/my:commit` — Structured commit workflow with Conventional Commits.
- `/my:push` — Push with pre-push checks.
- `/my:summarize` — Compare a plan or review against the actual git diff (runs
  the `summarizer` agent).
- `/my:optimize-prompt` — Score and rewrite a prompt; saves it to
  `docs/plans/optimized-prompts/`.
- `/my:clean-gone-branches` — Remove local branches whose remote is gone, with
  their clean worktrees, after asking.
- `/my:laravel-debug` — Laravel-specific debugging: diagnose read-only, then
  propose a fix.
- `/my:laravel-migration-check` — Check Laravel migrations for safety and
  rollback, without running them.

## Agents

| Agent | Model | Used by |
| --- | --- | --- |
| `code-reviewer` | opus | `my:soundness-review` |
| `spec-reviewer` | opus | `my:spec-review` |
| `summarizer` | sonnet | `/my:summarize` |
| `laravel-fullstack-expert` | — | `/my:laravel-*` |
| `oral-medicine-expert` | — | Called directly (oral medicine questions) |

## Hooks

Defined in `plugins/my/hooks/hooks.json`:

- **SessionStart** — `check-orphan-plans.sh` warns about files in `docs/plans/`
  or `docs/reports/` that are untracked or not named `YYYY-MM-DD-<slug>`.
  If `docs/plans/README.md` contains `<!-- plans-index: strict -->`, it also
  warns about plans missing from that index or missing a `**Status:**` line.
- **PostToolUse** — after `git merge --squash`, reminds Claude to update the
  roadmap with `my:roadmap-management`.

## Settings

`settings.json` at the repo root holds a deny-list of unsafe commands.
Add allow rules to your project's `.claude/settings.json` as needed:

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

Skills, commands and agents write to fixed paths under `docs/` in the project
root. They do not read `plansDirectory`.
