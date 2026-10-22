# claude-setup

My Claude Code setup. The repo is also a plugin marketplace, named
`claude-setup`. It has two parts:

- **`plugins/`** — my local plugins. Every local plugin goes here and gets a
  row in `.claude-plugin/marketplace.json` at the repo root. Three of them,
  `my`, `tutor` and `sp`, are methods (see Methods).
  - **`plugins/my/`** — the `my` plugin: skills, commands, agents and hooks
    for development workflows. Its README explains the method and how it
    builds on superpowers.
  - **`plugins/kit/`** — the `kit` plugin: neutral skills, commands, agents and
    the method start check, which work under any method.
  - **`plugins/tutor/`** — the `tutor` method plugin: its rules as a forced
    output style, and the `tutor:tutor` skill for learning workspaces.
  - **`plugins/sp/`** — the `sp` method plugin: the superpowers workflow as
    superpowers defines it, with no rules of its own.
  - **`plugins/vue-lsp/`** — the `vue-lsp` plugin: the TypeScript language
    server with `@vue/typescript-plugin`, so LSP also covers `.vue` files. Its
    README lists the npm packages it needs.
- **`global/`** — global instructions (`CLAUDE.md`, the core: the rules that
  hold under any method), path-scoped rules (`rules/`, among them
  `engineering.md`, which loads when Claude reads or writes code) and the git
  hooks of the `my` method (`git-hooks/`, which a project turns on through
  `core.hooksPath`). `~/.claude/CLAUDE.md` and `~/.claude/rules` are symlinks
  into this folder, so edit the files here.
- **`projects/<repo>/`** — one project's private Claude files, which its own
  repo ignores: `claude-local.md` and `rules/`. A fresh clone of that project
  links them back from its root:

  ```bash
  ln -s ~/projects/claude-setup/projects/<repo>/claude-local.md CLAUDE.local.md
  ln -s ~/projects/claude-setup/projects/<repo>/rules .claude/rules
  ```

  The file is not named `CLAUDE.local.md` here, so that sessions in this repo
  do not load it.

`marketplace.json` stays at the repo root. There, the plugin version is the
commit hash. In a subfolder, Claude Code cannot read the hash, so every version
is `unknown` and an update copies uncommitted edits too.

## Installation

Add the repo as a marketplace once, then install the plugins that are on in
every session:

```text
/plugin marketplace add ~/projects/claude-setup
/plugin install kit@claude-setup
/plugin install vue-lsp@claude-setup
/plugin disable typescript-lsp@claude-plugins-official
```

The methods, `my`, `tutor` and `sp`, need no `/plugin install`.
`~/.claude/settings.json` turns no method on, and keeps superpowers off. A
project turns its method on with `/kit:setup <method>` (see Methods), and
Claude Code then loads the method from the marketplace. `vue-lsp` replaces
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

A method is a way of working that Claude follows in a project: a set of
rules, plus the tools those rules need. This repo has three:

- **`my`** — how I build software: one roadmap orders the work, each change
  gets the process its risk needs, a second reader reviews it, and each
  branch lands on `main` as one squash commit.
- **`tutor`** — for learning: I write the code, and Claude sets exercises,
  gives hints and keeps notes in `docs/learning/`.
- **`sp`** — the superpowers workflow as its authors ship it, with none of
  my rules added.

Each project picks one method, or none. With none, Claude follows only the
core rules in `global/` and has the `kit` tools. Changing one project's
method changes nothing in other projects.

You pick a method in one of three ways:

| To change the method for | Run | Lasts until |
| --- | --- | --- |
| A project, for good | `/kit:setup <method>` | You run it again |
| One session | `claude-method <method>` | The session ends |
| A folder, for now | `/kit:method <method>`, then `/reload-plugins` | You run `/kit:method default` |

`claude-method` with no arguments lists the methods.

### How methods work

Each method is a plugin with `"category": "method"` in
`.claude-plugin/marketplace.json`. Its forced output style holds its rules,
and the `dependencies` field of its `plugin.json` holds the plugins it needs.
So turning a method on loads its rules and its tools together, and turning
it off removes both.

- `~/.claude/settings.json` keeps every method off, and `kit@claude-setup`
  on. A project with no method of its own gets only the core in
  `global/CLAUDE.md`, the rules in `global/rules/` and the `kit` tools.
- A project's `.claude/settings.json` names its method: the method's key and
  its dependencies' keys are `true`. A `my` project also has a
  `## Project facts` block in its `CLAUDE.md`.
- A trial project uses whatever the outside method's own setup writes.

`/kit:setup <method> [<path>]` writes these keys, from
`plugins/kit/bin/claude-method`, and commits them in that project. The method
loads in the next session there. The `method-guard.py` hook (see Hooks) warns
when two methods are on, when a dependency is off, or when an old import line
is left.

The other two ways switch the method without a commit:

- `claude-method <m> [claude args]` starts one session with method `<m>`, in
  any folder. It passes the method's keys to `claude` with `--settings`, and
  passes the other args on. `my:handoff` starts each stage this way, with `claude-method my`.
- `/kit:method <m>`, typed in a session, switches the folder: it writes the
  keys into `.claude/settings.local.json`, the folder's local settings, which
  outrank its committed `.claude/settings.json`. The method loads after you
  submit `/reload-plugins`, in that session and in every new one there. A
  session started by `claude-method`, such as a `my:handoff` stage, keeps
  its method, because `--settings` outranks the local file.
  `/kit:method default` removes those keys again, so the folder's committed
  method applies.

Your shell finds `claude-method` through the symlink
`~/bin/claude-method`:

```bash
ln -s ~/projects/claude-setup/plugins/kit/bin/claude-method ~/bin/claude-method
```

## Skills

Skills load when a task matches their description, or when you call them
as `/my:<name>`, `/kit:<name>` or `/tutor:<name>`.

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
- `my:design-system` — Keeps `docs/DESIGN-SYSTEM.md`, the inventory of shared
  components and hand-built patterns that UI specs read and spec reviews
  check. `audit` builds it, `refresh` updates it, and `sync` makes
  the Design System artifact that canvases draw from. It writes no component
  code: each component to build becomes a roadmap row. The method no longer
  calls it; row 69 decides whether it moves to `kit` or is deleted.
- `my:roadmap-management` — Edits `ROADMAP.md`: adds rows and moves them between
  status tiers.
- `my:changelog-management` — Edits `CHANGELOG.md` for shipped features, fixes
  and deploy changes.
- `my:clean-plans` — Gives undated plan files in `docs/plans/` dated names, updates
  the links to them, and offers to delete files from another project, empty files
  and duplicates.

### `kit` skills

- `kit:setup` — Sets a project's method: writes the method's plugin keys
  (and, for `my`, the facts block), removes other methods' keys and an old
  import line, and commits them in that project. See Methods.
- `kit:method` — Switches the method of the current folder during a session,
  in `.claude/settings.local.json`, until `/kit:method default`. Only you
  start it. See Methods.
- `kit:briefing` — Writes a plain-English, decision-focused briefing for
  non-technical readers, in `docs/briefings/`. Five events: a result landed,
  a decision needs sign-off, a long job started, changes since a fixed point
  (the last briefing, deploy or request list), and where the product stands
  (a first briefing). The deck or shared copy is built from the briefing, not
  by it. Its "Scope" section lists what goes elsewhere.
- `kit:dev-reports` — Builds a daily or weekly developer report from git
  history. For developers only; `kit:briefing` can use one as its source when
  a project keeps no changelog.
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
- `kit:design-router` — Decides which design skill does each design job, and
  starts it with a one-time ticket (`plugins/kit/bin/design-router-ticket.py`).
  For a job with two candidate skills, it can run both side by side and keep
  the winner in the project's `.claude/design-router.json`. Its plugin list is
  `plugins/kit/skills/design-router/plugins.json`. Tests:
  `cd plugins/kit && python3 -m unittest discover tests`.

### `tutor` skills

- `tutor:tutor` — A learning mode. Sets up a learning workspace (a new repo, a
  repo made for learning, or a clone of a real project that cannot push), and
  runs the sessions: the student writes the code, the tutor sets exercises,
  gives hints and keeps notes in `docs/learning/`. The `tutor` plugin is off
  outside a learning workspace, so start a session with `claude-method tutor`
  in the folder that will hold the new workspace, then say "let's make a
  learning project for …".

`plugins/my/bin/` also holds `git-fold-fixups.py`, which is not a skill. The
feature steps in the `my` style (`plugins/my/output-styles/my.md`) and
`my:handoff` call it.
`git-fold-fixups.py check <sha>` says whether a fixup of a commit is safe. With
no argument it folds every waiting `fixup!` commit on the branch, or refuses
with one line and changes nothing. Your shell finds it through a symlink in
`~/bin`, as for the md-tables filters. Its tests:
`cd plugins/my && python3 -m unittest discover tests`.
`handoff-state.py`, in the same folder, keeps the state of a `my:handoff` run,
auto or supervised, and the queue of `/my:handoff auto rows`, and its tests
run with the same command. `handoff-lock.py`, in the same folder, runs one
command under a named lock, so that parallel auto runs take turns in the main
checkout. `locked-commit.py`, in the same folder, makes the commit in such a
main checkout under that lock, with the message read from a file.
`status-scan.py`, in the same folder, prints the facts `my:status` judges:
roadmap rows, open documents, worktrees, runs, the queue of roadmap rows
and branches that may hold unmerged work. It reads and never writes; its
tests run with the same command. `ds-count.py`, in the same folder, counts the
search patterns in the `ds-patterns` block of `docs/DESIGN-SYSTEM.md`, and with
`--write` stores the counts there; its tests run with the same command.
`link-check.py`, in the same folder, lists bad links in `ROADMAP.md` and
`CHANGELOG.md` and marks the ones on lines the current edit changed; both
skills run it after each edit, before the commit; its tests run with the same
command.

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

- **SessionStart** (on startup, resume and `/clear`) — `method-guard.py`
  reads the method list from `claude-method --methods` and warns in three
  cases: more than one method on, a method on with a dependency off, or an old
  import line `@~/.claude/methods/<m>.md` left in `CLAUDE.md` or
  `CLAUDE.local.md`. It reads and never writes, and prints nothing when all is
  well.
- **PreToolUse** (Skill) — `design-router-gate.py` refuses Claude's calls to
  skills of plugins that `kit:design-router`'s plugin list marks `routed` or
  `excluded`, and of installed plugins the list lacks, unless the router wrote
  a ticket for the call. A command the user types always runs. It fails open:
  a missing or broken list refuses nothing.

## Settings

The plugins set no permission rules. A plugin's `settings.json` keeps only
`agent` and `subagentStatusLine`, so a deny list there would have no effect.
The one command the plugins block is `git push` in an auto run, through a
hook (see Hooks above).
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
