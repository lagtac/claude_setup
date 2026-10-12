<!-- markdownlint-configure-file {"MD024": {"siblings_only": true}} -->

# Changelog

Changes to the Claude harness that a session can notice: the global
instructions in `global/`, and the `my` and `vue-lsp` plugins. Refactors,
tests and internal docs are not listed.

The plugins have no version numbers. The marketplace uses the commit hash, so
every commit on `main` is a release. Entries are grouped by month, newest
first. History before 2026-09 is in `git log` and in `docs/plans/`.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
**BREAKING** marks a change that removes a command or changes how you invoke
or install something.

## 2026-10

### 2026-10-12 — Parallel auto runs (Design workflow)

In a project whose `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs"
section, 2 to 4 `my:handoff auto` runs can go at once. Commits in the main
checkout take turns under a lock, and a run merges only code whose checks
ran on the current `main`. See the
[spec](docs/plans/2026-10-12-parallel-auto-runs-spec.md) and the
[plan](docs/plans/2026-10-12-parallel-auto-runs.md), whose **Risk** section
lists the known limits.

- New script `handoff-lock.py` runs one command under a named lock.
- `handoff-state.py` gains `start`, which keeps a cap on live runs, `live`,
  which lists them, and `merge`, which squash-merges under the lock.
- `git-fold-fixups.py` refuses a fold that would give a commit cited in
  `docs/`, `ROADMAP.md` or `CHANGELOG.md` a new hash, in every project.
- In a project with the section, the global rules, `/my:commit` and
  `my:architect` commit in the main checkout with one locked command, and
  nobody makes fixups there. Projects without the section are unchanged.

### 2026-10-12 — `my:handoff auto` (Design workflow)

`my:handoff` can take an approved spec to its `done` marks on `main` without
the user. A **Delegation** section in the spec says what the run may decide
alone. Anything else stops the run. It never pushes. See the
[spec](docs/plans/2026-10-12-autonomous-run-spec.md) and the
[plan](docs/plans/2026-10-12-autonomous-run.md), whose **Risk** section lists
the known limits.

- New forms: `/my:handoff auto plan <spec>`, `/my:handoff auto code <spec>`
  and `/my:handoff auto resume <spec>`.
- A `PreToolUse` hook blocks `git push` in any session where `MY_AUTORUN` is
  set. Sessions without the variable are not affected.
- `handoff-state.py` keeps a run's state in `.git/my-handoff/<slug>.json`.
- `global/CLAUDE.md` asks, while a spec is written, whether it may run in
  auto mode, and offers "supervised or auto?" at the hand-off.

### Added

- `git-fold-fixups.py` folds waiting `docs:` fixup commits into their target
  in one step, or refuses with a reason. See the
  [spec](docs/plans/2026-10-10-git-fold-fixups-spec.md).
- The global instructions size each change as Small, Medium or Large, and
  scale the documents and reviews to the size.
- `my:handoff` code and review stages accept a spec with a **Tasks**
  section, for a Medium change that has no separate plan.
- `my:tutor`, a learning mode: the student writes the code, the tutor sets
  exercises and keeps notes in `docs/learning/`. It comes with a `tutor`
  output style. See the [spec](docs/plans/2026-10-06-tutor-spec.md).

### Changed

- `my:spec-review` checks that a spec which adds UI decides off-path events:
  browser Back and Forward, a reload or deep link, a record deleted or
  restored while shown, an element that hides with focus or a panel open, a
  language change, and empty and error text. A missing decision is a
  `design` finding, so the author decides it.
- The fourteen feature steps moved from `global/CLAUDE.md` to
  `global/rules/docs-layout.md`, which loads only when a file in
  `docs/plans/` is touched.
- The roadmap keeps the only order of work. An action plan only routes a
  report's findings into roadmap rows.
- A Small UI change that adds no screen and no state needs no design canvas.
- The "Invoke first" table names the end-of-branch reviews and merge steps
  it means.

### Fixed

- `git-fold-fixups.py check` runs the fold's own rules, so it no longer
  passes a target that the fold then refuses.
- The md-tables docs describe the scripts' current command line in
  `~/src/scripts/`.

### Docs

- A critique of the workflow's efficiency, with its findings as roadmap
  rows: [report](docs/reports/2026-10-09-workflow-efficiency-critique.md).

## 2026-09

### 2026-09-22 — `my:handoff` (Design workflow)

The plan, code and review stages each run in their own top-level session,
opened in a tmux window, so each stage reads the real `CLAUDE.md` rules. See
the [spec](docs/plans/2026-09-21-handoff-spec.md) and the
[plan](docs/plans/2026-09-21-handoff.md).

- `/my:handoff <stage> <doc>` opens the stage in a new window. Each stage
  launches the next.
- The review stage (added 2026-09-29) runs the end-of-branch checks and
  reviews, one fix round, then the squash-merge after the user's yes.
- A finished stage marks its window with `✓`. A stage that waits marks it
  with `⚠`. Stages no longer message other sessions.

### Added

- `my:soundness-review --plan-only` reviews a plan on any working tree, so a
  busy `main` no longer stops the handoff plan stage. See the
  [spec](docs/plans/2026-09-30-soundness-plan-only-spec.md).
- `my:md-tables`, with filters that turn a Markdown table into one section
  per row and back.
- `my:architect` writes an architecture brief from labelled forces before
  brainstorming. The global instructions run it for new systems and contract
  changes. See the [spec](docs/plans/2026-09-17-architect-skill-spec.md).
- `my:spec-review`, a system-thinking review of one spec, required in the
  spec flow. See the [spec](docs/plans/2026-09-16-spec-review-skill-spec.md).
- The `plain` output style, enabled globally: short sentences, terms defined
  at first use, no idioms.
- The `vue-lsp` plugin, so the `LSP` tool also covers `.vue` files.
- `tune-claude-instructions` flags prompts that need a tool a subagent never
  receives.

### Changed

- **BREAKING** The repo is a plugin marketplace, and the plugins live in
  `plugins/`. Install from the marketplace instead of a `--plugin-dir`
  alias. Sessions now run a cached copy of the last commit, and
  `claude plugin update` refreshes it.
- The orphan-plan hook also checks the `docs/plans/` index and
  `docs/reports/`, but only in a project whose README opts in.
- Reports go to `docs/reports/`, and their findings become roadmap rows.
- Reviews run once, at the end of the branch, with one fix round. A failing
  red step counts as the proof that a test can fail.
- Commit messages carry a scope: `type(scope): sentence`.
- UI work must be drawn on a design canvas, not described in prose.
- A session must call the `LSP` tool before it concludes that no language
  server is configured.
- `clean-plans`, `summarizer` and `optimize-prompt` read and write dated
  files in `docs/plans/`.

### Removed

- **BREAKING** `/my:plan`, the `my:planner` agent and `/my:task`.
  Superpowers owns planning. See the
  [spec](docs/plans/2026-09-11-retire-planner-path-spec.md).

### Fixed

- `my:soundness-review`: four defects that lowered review quality, the
  contradictions its critique found, and the argument rules. It now asks
  what to review when a plan meets a dirty working tree, and stops on a
  mistyped range. See the [audit](docs/plans/2026-09-07-soundness-review-audit.md)
  and the [critique](docs/reports/2026-09-19-soundness-review-critique.md).
- Agents search the repo through `Bash`, because subagents never receive
  `Grep`, `Glob` or `LSP`.
- Subagents can start subagents when their agent file lists `Agent`.
