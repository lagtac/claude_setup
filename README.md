# claude-setup

My Claude Code setup. The repo is also a plugin marketplace, named
`claude-setup`. It has two parts:

- **`plugins/`** — my local plugins. Every local plugin goes here and gets a
  row in `.claude-plugin/marketplace.json` at the repo root.
  - **`plugins/my/`** — the `my` plugin: skills, commands, agents and hooks
    for development workflows.
  - **`plugins/kit/`** — the `kit` plugin: neutral skills, commands, agents and
    the tutor hook, which work under any method.
  - **`plugins/vue-lsp/`** — the `vue-lsp` plugin: the TypeScript language
    server with `@vue/typescript-plugin`, so LSP also covers `.vue` files. Its
    README lists the npm packages it needs.
- **`global/`** — global instructions (`CLAUDE.md`, the rules that hold under
  any method), method files (`methods/`), path-scoped rules (`rules/`),
  output styles (`output-styles/`) and the git hooks of the `my` method
  (`git-hooks/`, linked into a project's `.git/hooks/`). `~/.claude/CLAUDE.md`, `~/.claude/methods`,
  `~/.claude/rules` and `~/.claude/output-styles` are symlinks into this
  folder, so edit the files here. There are two output styles: `plain`, the
  default, and `tutor`, which a learning workspace sets (see `kit:tutor`).

`marketplace.json` stays at the repo root. There, the plugin version is the
commit hash. In a subfolder, Claude Code cannot read the hash, so every version
is `unknown` and an update copies uncommitted edits too.

## Installation

Add the repo as a marketplace once, then install the plugins:

```text
/plugin marketplace add ~/projects/claude-setup
/plugin install my@claude-setup
/plugin install kit@claude-setup
/plugin install vue-lsp@claude-setup
/plugin disable my@claude-setup
/plugin disable typescript-lsp@claude-plugins-official
```

`my` is a method, so it stays off at user scope, as does superpowers. A
project turns both on with `/kit:setup my` (see Methods). `vue-lsp` replaces
`typescript-lsp`, so disable that one. Otherwise two servers both claim `.ts`
files.

## Updating

Claude Code runs a copy of each plugin from `~/.claude/plugins/cache/`, not the
files in this repo. The plugins have no `version` field, so the version is the
commit hash. After you commit a change, copy it into the cache and restart:

```bash
claude plugin update my@claude-setup
claude plugin update kit@claude-setup
```

Uncommitted edits never reach the cache. So a skill you are halfway through
editing cannot break other sessions. To try an uncommitted edit, start one
session with the plugin folder instead. Use `plugins/kit` for an edit to a
`kit` tool:

```bash
claude --plugin-dir ~/projects/claude-setup/plugins/my
claude --plugin-dir ~/projects/claude-setup/plugins/kit
```

Do not also keep this flag in a shell alias, or every session loads that
plugin twice.

## Methods

A method is a set of skills plus the always-on rules that go with them. Each
project picks its own, so trying another method does not touch the global
files.

- `~/.claude/settings.json` turns `my@claude-setup` and `superpowers@synced`
  off, and `kit@claude-setup` on. A project with no switch of its own gets
  only the neutral rules in `global/CLAUDE.md` and the `kit` tools.
- A `my` project has a `## Project facts` block and the line
  `@~/.claude/methods/my.md` in its `CLAUDE.md`, and turns
  `my@claude-setup` and `superpowers@synced` on in its
  `.claude/settings.json`.
- A tutor project has the line `@~/.claude/methods/tutor.md` in its
  `CLAUDE.md`, and no plugin switch: `my` and superpowers stay off.
- A trial project uses whatever the outside method's own setup writes.

`/kit:setup my [<path>]` or `/kit:setup tutor [<path>]` writes these switches
and commits them in that project. Then start a new interactive session there:
Claude Code asks once to approve the import, and the rules load only after
that. The `method-guard.py` hook (see Hooks) warns when the switches disagree.

## Skills

Skills load when a task matches their description, or when you call them
as `/my:<name>` or `/kit:<name>`.

### `my` skills

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
  `/my:handoff auto plan|code <spec>` runs the whole cycle to the `done`
  marks without the user, as far as the spec's Delegation section allows,
  and never pushes; `/my:handoff auto resume <spec>` continues a stopped run.
- `my:status` — Answers "where are we", "what is next" and "what can be done
  in parallel" in one read-only report.
- `my:roadmap-management` — Edits `ROADMAP.md`: adds rows and moves them between
  status tiers.
- `my:changelog-management` — Edits `CHANGELOG.md` for shipped features, fixes
  and deploy changes.
- `my:clean-plans` — Gives undated plan files in `docs/plans/` dated names, updates
  the links to them, and offers to delete files from another project, empty files
  and duplicates.

### `kit` skills

- `kit:tutor` — A learning mode. Sets up a learning workspace (a new repo, a
  repo made for learning, or a clone of a real project that cannot push), and
  runs the sessions: the student writes the code, the tutor sets exercises,
  gives hints and keeps notes in `docs/learning/`. Say "let's make a learning
  project for …" to start.
- `kit:setup` — Switches a project to the `my` or `tutor` method: writes the
  import line, the facts block and the plugin switch, and commits them in that
  project. See Methods.
- `kit:briefing` — Writes a plain-English, decision-focused briefing for
  non-technical readers, in `docs/briefings/`.
- `kit:dev-reports` — Builds a daily or weekly developer report from git history.
- `kit:git-squasher` — Squashes runs of small consecutive commits.
- `kit:tune-claude-instructions` — Audits instruction files (CLAUDE.md, agents,
  commands, skills and their dispatch prompts) for vague directives, tools a
  subagent will not have, stale harness assumptions and contradictions.
- `kit:de-slop` — Rewrites text so it does not read as machine-written.
- `kit:name-pane` — Say "name it" to label the tmux pane with the session's
  focus (a roadmap row or goal) and rename its window after its panes' labels.
  The tmux part is `plugins/kit/bin/tmux-name-pane.py`, tested with
  `cd plugins/kit && python3 -m unittest discover tests`.
- `kit:md-tables` — Turns a Markdown table into one section per row, or
  sections back into a table, with the two filters in `plugins/kit/bin/`
  (`md-expand-table.py`, `md-collapse-sections.py`). Claude Code puts that
  folder on PATH in its sessions only; your shell finds them through symlinks
  in `~/bin`. Both files are symlinks to `~/src/scripts/`, which holds the
  scripts and their tests: `cd ~/src/scripts && python3 -m unittest -v`.

`plugins/my/bin/` also holds `git-fold-fixups.py`, which is not a skill. The
feature steps in `global/rules/docs-layout.md` and `my:handoff` call it.
`git-fold-fixups.py check <sha>` says whether a fixup of a commit is safe. With
no argument it folds every waiting `fixup!` commit on the branch, or refuses
with one line and changes nothing. Your shell finds it through a symlink in
`~/bin`, as for the md-tables filters. Its tests:
`cd plugins/my && python3 -m unittest discover tests`.
`handoff-state.py`, in the same folder, keeps the state of a `my:handoff auto`
run and the queue of `/my:handoff auto rows`, and its tests run with the same
command. `handoff-lock.py`, in the same folder, runs one command under a
named lock, so that parallel auto runs take turns in the main checkout.
`locked-commit.py`, in the same folder, makes the commit in such a main
checkout under that lock, with the message read from a file.
`status-scan.py`, in the same folder, prints the facts `my:status` judges:
roadmap rows, open documents, worktrees, auto runs, the queue of roadmap rows
and branches that may hold unmerged work. It reads and never writes; its
tests run with the same command.

## Commands

### `my` commands

- `/my:summarize` — Compare a plan or review against the actual git diff (runs
  the `summarizer` agent).

### `kit` commands

- `/kit:commit` — Structured commit workflow with Conventional Commits.
- `/kit:push` — Push with pre-push checks.
- `/kit:optimize-prompt` — Score and rewrite a prompt; saves it to
  `docs/optimized-prompts/`.
- `/kit:clean-gone-branches` — Remove local branches whose remote is gone, with
  their clean worktrees, after asking.
- `/kit:laravel-debug` — Laravel-specific debugging: diagnose read-only, then
  propose a fix.
- `/kit:laravel-migration-check` — Check Laravel migrations for safety and
  rollback, without running them.

## Agents

| Agent | Model | Used by |
| --- | --- | --- |
| `my:code-reviewer` | opus | `my:soundness-review` |
| `my:spec-reviewer` | opus | `my:spec-review` |
| `my:summarizer` | sonnet | `/my:summarize` |
| `kit:laravel-fullstack-expert` | — | `/kit:laravel-*` |
| `kit:oral-medicine-expert` | — | Called directly (oral medicine questions) |

## Hooks

Defined in `plugins/my/hooks/hooks.json`:

- **PreToolUse** (Bash and Monitor) — `block-autorun-push.py` blocks `git push`
  in a `my:handoff` auto run, a session started with `MY_AUTORUN` set. A
  project with `my` off has no push guard.
- **SessionStart** — `check-orphan-plans.sh` warns about files in `docs/plans/`
  or `docs/reports/` that are untracked or not named `YYYY-MM-DD-<slug>`.
  If `docs/plans/README.md` contains `<!-- plans-index: strict -->`, it also
  warns about plans missing from that index or missing a `**Status:**` line.
- **PostToolUse** — after `git merge --squash`, reminds Claude to update the
  roadmap with `my:roadmap-management`.

Defined in `plugins/kit/hooks/hooks.json`:

- **SessionStart** (on startup and `/clear`) — in a learning workspace, a repo
  with `docs/learning/curriculum.md`, tells Claude to invoke `kit:tutor`
  before its first reply.
- **SessionStart** (on startup, resume and `/clear`) — `method-guard.py` checks
  the project's method switch and warns when its parts disagree: a `my` import
  with its plugins off, an import that is not approved or was declined, `my`
  or superpowers on without the `my` import, or more than one method import.
  It reads and never writes, and prints nothing when all is well.

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
