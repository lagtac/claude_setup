# claude-setup

My Claude Code setup. It has two parts:

- **`my-plugin/`** — the `my` plugin: skills, commands, agents and hooks for
  development workflows.
- **`GLOBAL-*`** — global instructions, rules and output styles. Files in
  `~/.claude/` are symlinks into these, so edit them here.

## Installation

Load the plugin from its folder with the `--plugin-dir` flag:

```bash
claude --plugin-dir ~/projects/claude-setup/my-plugin
```

To load it in every session, add an alias to `~/.bash_aliases`:

```bash
alias claude='claude --plugin-dir ~/projects/claude-setup/my-plugin'
```

## Skills

Skills load when a task matches their description, or when you call them
as `/my:<name>`.

- `my:architect` — Writes an architecture brief from the forces on a system,
  before the spec. Output: `docs/plans/YYYY-MM-DD-<slug>-architecture.md`.
- `my:spec-review` — Reviews one `*-spec.md` as a system: components, contracts,
  state ownership, failure spread. Output: a review in `docs/plans/`.
- `my:soundness-review` — Gives a for/against verdict on a diff, or checks a
  diff or plan against its plan. Output: a review in `docs/plans/`. Bug-finding
  goes to the built-in `/code-review`.
- `my:briefing` — Writes a plain-English, decision-focused briefing for
  non-technical readers, in `docs/briefings/`.
- `my:roadmap-management` — Edits `ROADMAP.md`: adds rows and moves them between
  status tiers.
- `my:changelog-management` — Edits `CHANGELOG.md` for shipped features, fixes
  and deploy changes.
- `my:dev-reports` — Builds a daily or weekly developer report from git history.
- `my:git-squasher` — Squashes runs of small consecutive commits.
- `my:clean-plans` — Renames randomly named plan files in `docs/plans/` to dated
  names, and offers to delete trivial ones.
- `my:tune-claude-instructions` — Audits instruction files (CLAUDE.md, agents,
  commands, skills) for vague directives and for tools a subagent will not have.
- `my:de-slop` — Rewrites text so it does not read as machine-written.

## Commands

- `/my:commit` — Structured commit workflow with Conventional Commits.
- `/my:push` — Push with pre-push checks.
- `/my:summarize` — Compare a plan or review against the actual git diff (runs
  the `summarizer` agent).
- `/my:optimize-prompt` — Score and rewrite a prompt; saves it to
  `docs/plans/optimized-prompts/`.
- `/my:clean-gone-branches` — Remove local branches whose remote is gone, with
  their worktrees.
- `/my:laravel-debug` — Laravel-specific debugging.
- `/my:laravel-migration-check` — Check Laravel migrations for safety and
  rollback.

## Agents

| Agent | Model | Used by |
| --- | --- | --- |
| `code-reviewer` | opus | `my:soundness-review` |
| `spec-reviewer` | opus | `my:spec-review` |
| `summarizer` | sonnet | `/my:summarize` |
| `laravel-fullstack-expert` | — | `/my:laravel-*` |
| `oral-medicine-expert` | — | Called directly (oral medicine questions) |

## Hooks

Defined in `my-plugin/hooks/hooks.json`:

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
