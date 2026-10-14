# Harness Roadmap

Living index of work on the Claude harness (global instructions, `my` plugin,
rules, hooks). Keep it short: details live in the linked `docs/plans/` docs,
and what shipped when is in [`CHANGELOG.md`](CHANGELOG.md). In each section,
open rows come first.

Each row has one number, in one sequence for the whole file. A number is
never changed or reused, also when a row ships or is deleted; a split row's
children take suffixes (`12b`, `12c`). A new row takes the next number below,
and the same edit raises it by one.

**Next number:** 56

**Status legend:** ✅ shipped · 🚧 in progress · 📋 planned · 💭 discussed, not scheduled

---

## Order of work

Set on 2026-10-14. The steps run top to bottom. Rows in one step can run
side by side, because they edit different files.

1. **9 "Start auto runs from roadmap rows".** Shipped on 2026-10-14, so the
   rows that waited for it in steps 6 and 7 may start.
2. **41 "`git-squasher` loses `$1`" and 1 "Deny list has no effect", side by
   side.** Two fixes with no spec. 41 is a live bug.
3. **45 "Review preparation as a script" and 46 "`git-squasher` plan and
   apply scripts", side by side.** The most-used script rows that edit no
   file of row 9. 45 is in `my`, 46 in `kit`; they share only `README.md`.
   46 builds on 41's fix.
4. **55 "Decisions that go back to the user", then 53 "`my:draft-spec`",
   then 54 "Small rows in forks while the user is away".** 53 and 54 both
   use the rule of 55. 55 and 53 both edit `global/methods/my.md`. 54 comes
   after 53, because both run forks while the user is away, and 53 is being
   designed now.
5. **8 "`my:spec-review` checks Delegation content" after 45.** Both edit
   `my:spec-review` `SKILL.md`. Side by side with 8: **48 "`setup` facts by
   script", then 39 "`kit:setup` offers a Parallel runs section"**, which
   edit the same skill; 47 "`clean-plans` moves by script"; 49
   "`dev-reports` dates and TODOs by script"; 50 "`clean-gone-branches` as a
   script"; 51 "Roadmap number and link check".
6. **After row 9 merges, one at a time, all in `my:handoff`: 33 "Skill text
   loses `$1` and `$2`", 37 "Launch from a session outside tmux", 34 "Merges
   read a message file", 44 "`git-fold-fixups.py list <path>`", 42 "Parallel
   runs parser", 43 "`handoff` start checks as a script", then 35 "Trim copied
   facts in `my:handoff`" with 36 "Name repeated cross-references", as one
   branch.** The fixes come first; 33 is a live bug, and row 9's branch
   already edits the same file. 34 reworks the command 33 fixed. 43 uses the
   parser from 42. The trims come last, so they trim the text the scripts
   leave.
7. **After row 9 merges: 40 "Every spec has a Files section", then 52
   "`status` gates and overlap by script".** Both edit `my:status`
   `SKILL.md`, and 40 also edits `my:spec-review`, so it goes after step 5.
8. **22 "Spec writers decide off-path events", 21 "E2E tests check the
   result" and 20 "Plan names the layouts to check".** Rule text only. 22
   edits the spec rules in `global/methods/my.md`, as 40 and 53 do, so it
   goes after them.
9. **Waiting rows: 29 "Measure the auto runs", then 30 "Split `my:handoff` by
   mode", then 31 "Write review step 8 whole per mode"; and 17 "Generalize
   the gates".** 29 waits for weeks of auto runs, 30 and 31 wait for 29, and
   17 waits for a second project to adopt the gates.

## `my` plugin hygiene

Follow-ups spawned by the planner retirement. Spec:
[`docs/plans/2026-09-11-retire-planner-path-spec.md`](docs/plans/2026-09-11-retire-planner-path-spec.md)
(see its "Out of scope").

- 💭 1 **Deny list has no effect** — fix: the repo-root `settings.json` deny list
  is read by nothing (Claude Code reads `.claude/settings.json`, and a plugin
  `settings.json` drops permission rules), yet `CLAUDE.md` and `README.md`
  describe it as active. Found while writing the
  [spec](docs/plans/2026-10-12-autonomous-run-spec.md) for `my:handoff auto`
  (its D4).
- ✅ 2 **Retire the planner path** — `/my:plan`, `my:planner` and `/my:task`
  removed; Superpowers owns planning.
- ✅ 3 **`clean-plans` scans abolished paths** — scans only `docs/plans/`.
- ✅ 4 **`tune-claude-instructions` is a model behind** — no Opus 4.7 pin; checks
  for tools subagents never get.
- ✅ 5 **Plugin docs drift** — `README.md` documents all skills, agents and hooks.
- ✅ 6 **`summarizer` plan-path convention** — dated files in `docs/plans/`; same
  fix for `optimize-prompt`.
- ✅ 7 **md-tables tests fail on `main`** — fix: the tests moved to
  `~/src/scripts/`, which owns the scripts. Small.

## Design workflow

- 💭 8 **`my:spec-review` checks Delegation content** — when a spec has a
  Delegation section, check that its values fit the design: the listed
  dependencies match what the design adds, the check commands and test names
  exist, and `decide` is flagged on a spec that changes stored data or a
  contract. Not the format: the auto start check owns that. Small.
- ✅ 9 **Start auto runs from roadmap rows** — one command takes a list of
  rows, starts the ones with an approved spec as parallel auto runs up to
  **Max runs**, and starts a waiting row each time a run finishes. Shipped in
  `9fe3314`; known limits are in the plan's Risk section.
  [brief](docs/plans/2026-10-13-roadmap-auto-runs-architecture.md),
  [spec](docs/plans/2026-10-13-roadmap-auto-runs-spec.md),
  [plan](docs/plans/2026-10-13-roadmap-auto-runs.md)
- 💭 40 **Every spec has a Files section** — a spec rule in
  `global/methods/my.md`; a Medium spec's Tasks section counts when it names
  the files. `my:spec-review` flags a missing one, and `my:status` reads Tasks
  as a file list. Lets row 9's queue tell which rows may run side by side.
  Split out of row 9's first spec draft.
- 💭 53 **`my:draft-spec`** — a second route to an approved spec: an agent
  drafts fast, then hardens the draft through the draft-time checks of the
  [spec hardening audit](docs/reports/2026-10-14-spec-hardening-audit.md)
  until a round finds nothing new, and brings the user only the decisions
  that row 55 names. First framed as "Draft specs in forks"; reframed on
  2026-10-14 after the fork drafts of rows 45 and 46 and the audit.
- 💭 54 **Small rows in forks while the user is away** — rows with no spec,
  which `my:handoff auto` cannot start, each run in a fork and its own
  worktree up to the merge, under one e2e lock that every session takes. The
  main session reads each fork's e2e log and test diff itself, then merges
  one branch at a time. Tried on zitamu on 2026-10-14 (rows 112 and 102,
  beside row 103's spec draft, 31% of a 1M context); there the lock bound
  only that session's forks. Open: the forks made decisions the user never
  saw (Greek copy, new tokens, scope dropped from a finding, review findings
  declined). Some of these must go back to the developer, the user, but
  which ones is not settled yet. Pairs with 53.
- 💭 55 **Decisions that go back to the user** — one rule in
  `global/methods/my.md` for forks, auto runs and review fixes: a choice
  goes back when it changes what users see, a shared definition or contract,
  the scope of the row or finding, or the verdict on a review finding. It
  may narrow which `design` findings go to the user. Rows 53 and 54 use it.
  Sources: the
  [spec hardening audit](docs/reports/2026-10-14-spec-hardening-audit.md)
  and row 54's zitamu run.
- ✅ 10 **`my:architect`** — forces-first architecture brief before brainstorming.
  [spec](docs/plans/2026-09-17-architect-skill-spec.md),
  [plan](docs/plans/2026-09-17-architect-skill.md)
- ✅ 11 **`my:handoff`** — plan, code and review stages run in their own sessions
  in tmux windows. [spec](docs/plans/2026-09-21-handoff-spec.md),
  [plan](docs/plans/2026-09-21-handoff.md); `--plan-only` for
  `my:soundness-review`:
  [spec](docs/plans/2026-09-30-soundness-plan-only-spec.md),
  [plan](docs/plans/2026-09-30-soundness-plan-only.md)
- ✅ 12 **`my:tutor`** — a learning mode where the student writes the code; known
  limits in the spec's Risk section. [spec](docs/plans/2026-10-06-tutor-spec.md)
- ✅ 13 **`my:handoff auto`** — an approved spec runs to its `done` marks without
  the user, within its Delegation section, and never pushes; known limits in
  the plan's Risk section.
  [brief](docs/plans/2026-10-11-autonomous-run-architecture.md),
  [spec](docs/plans/2026-10-12-autonomous-run-spec.md),
  [plan](docs/plans/2026-10-12-autonomous-run.md)
- ✅ 14 **Parallel auto runs** — 2 to 4 `my:handoff auto` runs at once in a
  project with a "Parallel runs" section; commits in the main checkout take
  turns under a lock, and a merge reruns the checks when `main` moved.
  Shipped in `38f6c34`; known limits are in the plan's Risk section.
  [brief](docs/plans/2026-10-12-parallel-auto-runs-architecture.md),
  [spec](docs/plans/2026-10-12-parallel-auto-runs-spec.md),
  [plan](docs/plans/2026-10-12-parallel-auto-runs.md)
- ✅ 15 **`my:status`** — one read-only report of where we are, what is next,
  and what can run in parallel. Shipped in `c4d3832`; known limits are in the
  spec's Risk section. Since 2026-10-12, items that take turns on a
  **Shared resources** lock can pair; see `CHANGELOG.md`.
  [spec](docs/plans/2026-10-12-status-skill-spec.md)

## Harness generalization

Make the harness reusable in new projects without forking copies. Spec:
[`docs/plans/2026-06-16-harness-generalization-audit.md`](docs/plans/2026-06-16-harness-generalization-audit.md).

- 🚧 16 **Swappable methods** — split `global/CLAUDE.md` into a neutral core
  and per-method files, and split `my` into `my` (the method) and `kit`
  (neutral tools), so one project can try another method. Two batches; the
  second is a one-sitting cutover. Batch 1 (`kit`) merged in `1fe2d57`.
  [brief](docs/plans/2026-10-12-swappable-methods-architecture.md),
  [spec](docs/plans/2026-10-12-swappable-methods-spec.md),
  [plan](docs/plans/2026-10-12-swappable-methods.md)
- 💭 17 **Generalize the gates** — move the gate logic (`e2e-gate`, `review-gate`,
  `require-*`) into the plugin behind a per-repo `.claude/harness.json`, with a
  `/harness-init` bootstrap. Waits for a second project to adopt the gates;
  today only `diagoradisa-annotator` uses them. Design and reasons in the spec.
- 💭 39 **`kit:setup` offers a Parallel runs section** — `/kit:setup my` asks
  whether to allow parallel auto runs, and proposes the section's four lines
  from the machine's memory and the repo's compose, `.env` and e2e files.
  Split out of row 9's first spec draft.
- ✅ 18 **Global orphan-plan hook** — `check-orphan-plans.sh` runs in the `my`
  plugin at session start, in all repos.
- ✅ 19 **Runtime-command contract — DRAFT** — written down, not adopted:
  [`docs/harness-runtime-contract-DRAFT.md`](docs/harness-runtime-contract-DRAFT.md).

## Workflow efficiency

Findings of
[`docs/reports/2026-10-09-workflow-efficiency-critique.md`](docs/reports/2026-10-09-workflow-efficiency-critique.md).
Rows are unordered unless a row says what it waits for. S2, S3, M1 and M3 got
no row; the report says why.

- 💭 20 **Plan names the layouts to check** — `plan-format.md` asks a plan that
  changes UI to list the widths at its breakpoint edges, every language the
  project ships, and its longest real text, and to measure them in e2e tests.
  Report M4.
- 💭 21 **E2E tests check the result** — extend "End-to-end coverage" in
  `global/CLAUDE.md`: the test checks what the user gets (the video plays),
  not only the markup. Report M4.
- 💭 22 **Spec writers decide off-path events** — the spec rules in
  `global/CLAUDE.md` ask a spec that adds UI to decide the events
  `my:spec-review` now checks, next to Visual Language, so the review finds
  fewer gaps. Report M4.
- ✅ 23 **Spec review checks off-path events** — `my:spec-review` asks a spec
  that adds UI to decide Back and Forward, a deleted or restored record, an
  element that hides, a language change, and empty and error text. Small.
  Report M4.
- ✅ 24 **Trigger table contradictions** — fix: the "Invoke first" rows name the
  Git Workflow steps and the end-of-branch reviews. Report C1, C2.
- ✅ 25 **UI rule has a Small case** — no design canvas for a Small change without
  a new screen or state. Report S1.
- ✅ 26 **Fold script for docs fixups** — one script that folds or refuses with a
  reason. Report G1. [spec](docs/plans/2026-10-10-git-fold-fixups-spec.md)
- ✅ 27 **Git steps leave the always-loaded file** — the feature steps moved to
  `docs-layout.md`. Report G2.
  [spec](docs/plans/2026-10-10-git-fold-fixups-spec.md)
- ✅ 28 **`check` asks the fold** — fix: `git-fold-fixups.py check` runs the
  fold's own rules. Small. [spec](docs/plans/2026-10-10-git-fold-fixups-spec.md)
- 💭 29 **Measure the auto runs** — after a few weeks of `my:handoff auto` on
  zitamu, rerun the spec-to-`done` timing and the docs-only commits per branch
  from zitamu's commit size audit, and compare them with the 2026-10-12 numbers.
  Waits for those weeks. Report M2.

## `my:handoff` instructions

Findings of
[`docs/reports/2026-10-12-handoff-instructions-audit.md`](docs/reports/2026-10-12-handoff-instructions-audit.md).
Their order is in "Order of work" above.

- 💭 30 **Split `my:handoff` by mode** — move auto-only and parallel-only text
  out of `SKILL.md` into files read through a pointer step, so a stage loads
  only its own branch. Rehearse a supervised and an auto run headless before
  and after. Waits for row 29 "Measure the auto runs". Report P1.
- 💭 31 **Write review step 8 whole per mode** — the four versions of the merge
  step become one list per mode; smaller patches sit under the step they
  change. Waits for row 30 "Split `my:handoff` by mode". Report P2.
- ✅ 32 **One script for the locked commit** — a `locked-commit.py` that reads
  the message from a file replaces the five copies of the locked command and
  the commit's heredoc rule. Report P3. Shipped in `39000ec`; known limits are
  in the spec's Risk section.
  [spec](docs/plans/2026-10-12-locked-commit-spec.md)
- 💭 33 **Skill text loses `$1` and `$2`** — fix: Claude Code replaces `$1` and
  `$2` in a loaded skill with its arguments, so the parallel squash-merge in
  `my:handoff` (`"$1"`, `"$2"`) merges a branch named after the stage. Live in
  every project with a "Parallel runs" section.
- 💭 34 **Merges read a message file** — `handoff-state.py merge` and the
  parallel squash-merge take `-F <file>`, so the heredoc rule leaves
  `my:handoff`. Changes the `handoff-state.py` interface. Out of scope of the
  [locked commit spec](docs/plans/2026-10-12-locked-commit-spec.md).
- 💭 35 **Trim copied facts in `my:handoff`** — the lock exit-code table points
  to `handoff-lock.py --help`, and design explanations stay in the specs.
  Small. Report P4.
- 💭 36 **Name repeated cross-references** — *locked commit*, *shared-doc
  check* and *waiting fixups* replace "as in Plan stage, step N". Small.
  Report P5.
- 💭 37 **Launch from a session outside tmux** — fix: Launch reads only `TMUX`,
  so a background session falls back to printing the command even when a
  tmux server runs. When `TMUX` is empty, pick the target session from
  `tmux ls` (for example the one named after the repo) and open the window
  with `-t <session>:`. Found on 2026-10-13; not from the audit report.
- ✅ 38 **Rubric fixes in `my:handoff`** — `PushNotification` is loaded before
  use, findings are classified in writing before a fix, and the code stage's
  auto sub-steps have their own letters. Small. Report R1 to R4.

## Scripted skill steps

Findings of
[`docs/reports/2026-10-14-scriptable-skill-steps.md`](docs/reports/2026-10-14-scriptable-skill-steps.md):
steps of the `my` and `kit` skills that fixed rules decide, and that a script
in `bin/` can run instead of the model. Their order is in "Order of work"
above.

- 💭 41 **`git-squasher` loses `$1`** — fix: the `squash-todo.sh` example in
  `kit:git-squasher` step 5 uses `"$1"`, which Claude Code replaces with the
  skill's arguments, as in row 33. Small. Report B1.
- 💭 42 **Parallel runs parser** — a `handoff-state.py` subcommand prints
  **Max runs**, `<n>`, the docs paths and the `--docs-paths` arguments, for
  `my:handoff`, `my:status`, `kit:commit` and `my:architect`. Report S4.
- 💭 43 **`handoff` start checks as a script** — a subcommand prints `<slug>`,
  `<name>` and `<base>`, the first failed start check, the Delegation
  validation and the restart point. Report S2, S3.
- 💭 44 **`git-fold-fixups.py list <path>`** — lists a document's waiting
  fixups, which `my:handoff` finds by hand in three places. Small. Report S6.
- 💭 45 **Review preparation as a script** — the argument sorting, the diff
  file, the mode table, the review file name and the template filling of
  `my:soundness-review` and `my:spec-review`. Report S5.
- 💭 46 **`git-squasher` plan and apply scripts** — the grouping rules run as a
  script, and the apply step reads the messages from a file. Report S7.
- 💭 47 **`clean-plans` moves by script** — the candidate list, the date,
  `git mv` or `mv`, and repointing the links; "Moving a document" in
  `docs-layout.md` uses the same script. Report S8.
- 💭 48 **`setup` facts by script** — the fact discovery and the
  `settings.json` merge of `kit:setup`; the "already set up" check reuses
  `method-guard.py`. Report S9.
- 💭 49 **`dev-reports` dates and TODOs by script** — the ISO week, the Monday
  rule, the days with commits and the TODO extraction. Report S10.
- 💭 50 **`clean-gone-branches` as a script** — list, check and delete; the
  command keeps the approval question. Report S11.
- 💭 51 **Roadmap number and link check** — a script prints the next row
  number and flags `.html`, `../` and dead links in `ROADMAP.md` and
  `CHANGELOG.md`. Small. Report S12.
- 💭 52 **`status` gates and overlap by script** — `my:status` steps 5 and 6
  and the overlap test. Blocked by row 9, whose spec uses these steps as
  model judgment. Report S13.

## Other

Older self-contained efforts (code-review consolidation, planning-standards
single-source, briefing skill, Opus prompt tuning, …) are dated specs in
`docs/plans/`. They are not indexed here unless they spawn open follow-ups.
