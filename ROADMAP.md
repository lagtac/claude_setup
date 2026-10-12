# Harness Roadmap

Living index of work on the Claude harness (global instructions, `my` plugin,
rules, hooks). Keep it short: details live in the linked `docs/plans/` docs,
and what shipped when is in [`CHANGELOG.md`](CHANGELOG.md). In each section,
open rows come first.

**Status legend:** ✅ shipped · 🚧 in progress · 📋 planned · 💭 discussed, not scheduled

---

## `my` plugin hygiene

Follow-ups spawned by the planner retirement. Spec:
[`docs/plans/2026-09-11-retire-planner-path-spec.md`](docs/plans/2026-09-11-retire-planner-path-spec.md)
(see its "Out of scope").

- 📋 **Deny list has no effect** — fix: the repo-root `settings.json` deny list
  is read by nothing (Claude Code reads `.claude/settings.json`, and a plugin
  `settings.json` drops permission rules), yet `CLAUDE.md` and `README.md`
  describe it as active. Found while writing the
  [spec](docs/plans/2026-10-12-autonomous-run-spec.md) for `my:handoff auto`
  (its D4).
- ✅ **Retire the planner path** — `/my:plan`, `my:planner` and `/my:task`
  removed; Superpowers owns planning.
- ✅ **`clean-plans` scans abolished paths** — scans only `docs/plans/`.
- ✅ **`tune-claude-instructions` is a model behind** — no Opus 4.7 pin; checks
  for tools subagents never get.
- ✅ **Plugin docs drift** — `README.md` documents all skills, agents and hooks.
- ✅ **`summarizer` plan-path convention** — dated files in `docs/plans/`; same
  fix for `optimize-prompt`.
- ✅ **md-tables tests fail on `main`** — fix: the tests moved to
  `~/src/scripts/`, which owns the scripts. Small.

## Design workflow

- 💭 **`my:spec-review` checks Delegation content** — when a spec has a
  Delegation section, check that its values fit the design: the listed
  dependencies match what the design adds, the check commands and test names
  exist, and `decide` is flagged on a spec that changes stored data or a
  contract. Not the format: the auto start check owns that. Small.
- ✅ **`my:architect`** — forces-first architecture brief before brainstorming.
  [spec](docs/plans/2026-09-17-architect-skill-spec.md),
  [plan](docs/plans/2026-09-17-architect-skill.md)
- ✅ **`my:handoff`** — plan, code and review stages run in their own sessions
  in tmux windows. [spec](docs/plans/2026-09-21-handoff-spec.md),
  [plan](docs/plans/2026-09-21-handoff.md); `--plan-only` for
  `my:soundness-review`:
  [spec](docs/plans/2026-09-30-soundness-plan-only-spec.md),
  [plan](docs/plans/2026-09-30-soundness-plan-only.md)
- ✅ **`my:tutor`** — a learning mode where the student writes the code; known
  limits in the spec's Risk section. [spec](docs/plans/2026-10-06-tutor-spec.md)
- ✅ **`my:handoff auto`** — an approved spec runs to its `done` marks without
  the user, within its Delegation section, and never pushes; known limits in
  the plan's Risk section.
  [brief](docs/plans/2026-10-11-autonomous-run-architecture.md),
  [spec](docs/plans/2026-10-12-autonomous-run-spec.md),
  [plan](docs/plans/2026-10-12-autonomous-run.md)
- ✅ **Parallel auto runs** — 2 to 4 `my:handoff auto` runs at once in a
  project with a "Parallel runs" section; commits in the main checkout take
  turns under a lock, and a merge reruns the checks when `main` moved.
  Shipped in `38f6c34`; known limits are in the plan's Risk section.
  [brief](docs/plans/2026-10-12-parallel-auto-runs-architecture.md),
  [spec](docs/plans/2026-10-12-parallel-auto-runs-spec.md),
  [plan](docs/plans/2026-10-12-parallel-auto-runs.md)
- ✅ **`my:status`** — one read-only report of where we are, what is next,
  and what can run in parallel. Shipped in `c4d3832`; known limits are in the
  spec's Risk section. Since 2026-10-12, items that take turns on a
  **Shared resources** lock can pair; see `CHANGELOG.md`.
  [spec](docs/plans/2026-10-12-status-skill-spec.md)

## Harness generalization

Make the harness reusable in new projects without forking copies. Spec:
[`docs/plans/2026-06-16-harness-generalization-audit.md`](docs/plans/2026-06-16-harness-generalization-audit.md).

- 💭 **Generalize the gates** — move the gate logic (`e2e-gate`, `review-gate`,
  `require-*`) into the plugin behind a per-repo `.claude/harness.json`, with a
  `/harness-init` bootstrap. Waits for a second project to adopt the gates;
  today only `diagoradisa-annotator` uses them. Design and reasons in the spec.
- ✅ **Global orphan-plan hook** — `check-orphan-plans.sh` runs in the `my`
  plugin at session start, in all repos.
- ✅ **Runtime-command contract — DRAFT** — written down, not adopted:
  [`docs/harness-runtime-contract-DRAFT.md`](docs/harness-runtime-contract-DRAFT.md).

## Workflow efficiency

Findings of
[`docs/reports/2026-10-09-workflow-efficiency-critique.md`](docs/reports/2026-10-09-workflow-efficiency-critique.md).
Rows are unordered unless a row says what it waits for. S2, S3, M1 and M3 got
no row; the report says why.

- 💭 **Plan names the layouts to check** — `plan-format.md` asks a plan that
  changes UI to list the widths at its breakpoint edges, every language the
  project ships, and its longest real text, and to measure them in e2e tests.
  Report M4.
- 💭 **E2E tests check the result** — extend "End-to-end coverage" in
  `global/CLAUDE.md`: the test checks what the user gets (the video plays),
  not only the markup. Report M4.
- 💭 **Spec writers decide off-path events** — the spec rules in
  `global/CLAUDE.md` ask a spec that adds UI to decide the events
  `my:spec-review` now checks, next to Visual Language, so the review finds
  fewer gaps. Report M4.
- ✅ **Spec review checks off-path events** — `my:spec-review` asks a spec
  that adds UI to decide Back and Forward, a deleted or restored record, an
  element that hides, a language change, and empty and error text. Small.
  Report M4.
- ✅ **Trigger table contradictions** — fix: the "Invoke first" rows name the
  Git Workflow steps and the end-of-branch reviews. Report C1, C2.
- ✅ **UI rule has a Small case** — no design canvas for a Small change without
  a new screen or state. Report S1.
- ✅ **Fold script for docs fixups** — one script that folds or refuses with a
  reason. Report G1. [spec](docs/plans/2026-10-10-git-fold-fixups-spec.md)
- ✅ **Git steps leave the always-loaded file** — the feature steps moved to
  `docs-layout.md`. Report G2.
  [spec](docs/plans/2026-10-10-git-fold-fixups-spec.md)
- ✅ **`check` asks the fold** — fix: `git-fold-fixups.py check` runs the
  fold's own rules. Small. [spec](docs/plans/2026-10-10-git-fold-fixups-spec.md)
- 💭 **Measure the auto runs** — after a few weeks of `my:handoff auto` on
  zitamu, rerun the spec-to-`done` timing and the docs-only commits per branch
  from zitamu's commit size audit, and compare them with the 2026-10-12 numbers.
  Waits for those weeks. Report M2.

## `my:handoff` instructions

Findings of
[`docs/reports/2026-10-12-handoff-instructions-audit.md`](docs/reports/2026-10-12-handoff-instructions-audit.md).
Rows are unordered unless a row says what it waits for.

- 💭 **Split `my:handoff` by mode** — move auto-only and parallel-only text
  out of `SKILL.md` into files read through a pointer step, so a stage loads
  only its own branch. Rehearse a supervised and an auto run headless before
  and after. Report P1.
- 💭 **Write review step 8 whole per mode** — the four versions of the merge
  step become one list per mode; smaller patches sit under the step they
  change. Waits for "Split `my:handoff` by mode". Report P2.
- 💭 **One script for the locked commit** — a `locked-commit.py` that reads
  the message from stdin replaces the five copies of the locked command and
  the heredoc rule. Report P3.
- 💭 **Trim copied facts in `my:handoff`** — the lock exit-code table points
  to `handoff-lock.py --help`, and design explanations stay in the specs.
  Small. Report P4.
- 💭 **Name repeated cross-references** — *locked commit*, *shared-doc
  check* and *waiting fixups* replace "as in Plan stage, step N". Small.
  Report P5.
- ✅ **Rubric fixes in `my:handoff`** — `PushNotification` is loaded before
  use, findings are classified in writing before a fix, and the code stage's
  auto sub-steps have their own letters. Small. Report R1 to R4.

## Other

Older self-contained efforts (code-review consolidation, planning-standards
single-source, briefing skill, Opus prompt tuning, …) are dated specs in
`docs/plans/`. They are not indexed here unless they spawn open follow-ups.
