# Harness Roadmap

Living index of work on the Claude harness (global instructions, `my` plugin,
rules, hooks). Keep it short: details live in the linked `docs/plans/` docs,
and what shipped when is in [`CHANGELOG.md`](CHANGELOG.md). In each section,
open rows come first.

Each row has one number, in one sequence for the whole file. A number is
never changed or reused, also when a row ships or is deleted; a split row's
children take suffixes (`12b`, `12c`). A new row takes the next number below,
and the same edit raises it by one.

**Next number:** 74

**Status legend:** ✅ shipped · 🚧 in progress · 📋 planned · 💭 discussed, not scheduled

---

## Order of work

Set on 2026-10-14; the shipped steps were removed on 2026-10-16, and the
`my:handoff` fixes moved to step 1 the same day. Row 64 shipped on
2026-10-16 ahead of its place; rows 33, 37, 56, 45 and 61 rebase onto its
text. Row 67 was put first on 2026-10-18. Rows 68 and 69 became step 3
the same day, and row 48 was folded into 68. Row 51 was moved ahead of
its place by the user on 2026-10-20, to the head of step 2's script chain,
and shipped on 2026-10-21.
The steps run top to bottom. Rows in one step can run side by side,
because they edit different files.

1. **67 "Brainstorming's paths replace the size table".** It changes how
   every row is sized and which documents it gets, so the rows after it are
   specced under the new rule instead of being reviewed again later.
2. **33 "Parallel squash-merge uses the wrong branch" and 37 "Handoff opens
   no window from outside tmux" on one branch, then 56 "Two supervised runs
   get the same port". Beside them, 45 "Review preparation as a script",
   then 46 "`git-squasher` plan and apply scripts"; and 62 "Question prompts
   follow `plain`".** 33, 37 and 56 are bugs in `my:handoff`, so they come
   first. 33 is live in every project with a "Parallel runs" section. 33 and
   37 are bug fixes and may share one branch. 56 no longer waits for row 29:
   zitamu hits it now, and row 29 takes weeks. 45 is the most-used script
   row. 45 is in `my` and 46 in `kit`, but both edit `README.md`, so 46 goes
   after 45. 46 builds on 41's fix. 62 edits only `global/output-styles/plain.md`.
3. **68 "Methods as plugins", then 69 "Shared skills move to `kit`".**
   68 comes after 67, so its spec uses the new routes, and after 33, 37 and
   56, because it changes the launch lines in `my:handoff` that they fix. It
   replaces `kit:setup`'s two switches and `method-guard.py`, so 60 in step
   5 edits the new `kit:setup`. 69 renames skills in files 68 also edits, so
   it comes right after, and each name changes once.
4. **61 "Auto start on approval, and re-review findings as rows", then 55
   "Decisions that go back to the user", then 53 "`my:draft-spec`", then 54
   "Bugs and approved bounded rows in forks while the user is away".** 61 is
   two small rules in `global/methods/my.md`, the file 55 and 53 edit, so it
   goes first. 53 and
   54 both use the rule of 55. 55 and 53 both edit
   `global/methods/my.md`. 54 comes after 53, because both run forks while
   the user is away, and 53 is being designed now.
5. **8 "`my:spec-review` checks Delegation content" after 45.** Both edit
   `my:spec-review` `SKILL.md`. Side by side with 8: **60 "Project facts in
   `CLAUDE.local.md`"**, which edits `kit:setup` after 68 reshapes it; 47
   "`clean-plans` moves by script"; 49 "`dev-reports` dates and TODOs by
   script"; 50 "`clean-gone-branches` as a script".
6. **One at a time, all in `my:handoff`: 34 "Merges read a message file",
   44 "`git-fold-fixups.py list <path>`", 43 "`handoff` start checks as a
   script", 66 "Window row lookup by script", 57 "An auto run that stops
   before the merge", then 35 "Trim `my:handoff` text".** 34 reworks the
   command that 33 fixed in step 2. 43 does not wait for 42's parser:
   without a "Parallel runs" section, `<n>` is `1`. 57 is a feature, so it
   follows the scripts. The trims come last, so they trim the text the
   scripts leave.
7. **40 "Every spec has a Files section", then 52 "`status` gates and
   overlap by script".** Both edit `my:status` `SKILL.md`, and 40 also edits
   `my:spec-review`, so it goes after step 5.
8. **20 "Specs and plans name what UI tests check".** Rule text only. It
   edits the spec rules in `global/methods/my.md`, as 40 and 53 do, so it
   goes after them.
9. **Waiting rows: 72 "Workflow metrics as one `my` script", then 29
   "Measure the auto runs", then 30 "Split `my:handoff` by mode"; and 17
   "Generalize the gates"; after 29, 39 "`kit:setup` offers a Parallel runs
   section" and 42 "Parallel runs parser".** 72 gives 29 its script, so it
   comes first. 29 waits for weeks of auto runs, and 30 waits for 29. 39
   and 42 matter only if 29's count keeps parallel runs. 17 waits for a
   second project to adopt the gates.

## `my` plugin hygiene

Follow-ups spawned by the planner retirement. Spec:
[`docs/plans/2026-09-11-retire-planner-path-spec.md`](docs/plans/2026-09-11-retire-planner-path-spec.md)
(see its "Out of scope").

- ✅ 1 **Deny list has no effect** — fix: the repo-root `settings.json` deny list,
  which nothing read, is deleted, and `CLAUDE.md` and `README.md` no longer
  call it active. Small. Found while writing the
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

- 💭 8 **`my:spec-review` checks Delegation content** — feature in
  `my:spec-review`, route not set. A spec's Delegation section can hold values
  that do not fit its design, and the review does not notice. Goal: when a
  spec has a Delegation section, check that its values fit the design: the
  listed dependencies match what the design adds, the check commands and test
  names exist, and `decide` is flagged on a spec that changes stored data or a
  contract. Not the format: the auto start check owns that. Also flag a manual
  step before the merge, which an auto run can never take (zitamu,
  2026-10-15). The flag informs and does not push toward `stop`: row 74a's
  user chose `decide` on a contract change on purpose ([run
  audit](docs/reports/2026-10-15-row-74-handoff-run-audit.md) H2).
- ✅ 9 **Start auto runs from roadmap rows** — one command takes a list of
  rows, starts the ones with an approved spec as parallel auto runs up to
  **Max runs**, and starts a waiting row each time a run finishes. Shipped in
  `9fe3314`; known limits are in the plan's Risk section.
  [brief](docs/plans/2026-10-13-roadmap-auto-runs-architecture.md),
  [spec](docs/plans/2026-10-13-roadmap-auto-runs-spec.md),
  [plan](docs/plans/2026-10-13-roadmap-auto-runs.md)
- 💭 40 **Every spec has a Files section** — rule in `global/methods/my.md`,
  with checks in `my:spec-review` and `my:status`; route not set. A spec need
  not list the files it changes, so row 9's queue cannot tell which rows may
  run side by side. Goal: a spec rule asks for a Files section, and a spec's
  Tasks section counts when it names the files. `my:spec-review` flags a
  missing one, and `my:status` reads Tasks as a file list. Split out of row
  9's first spec draft.
- 💭 53 **`my:draft-spec`** — feature, a new skill in `my`; route not set. A
  second way to an approved spec, only for a row that cites a source with
  concrete findings (a report, a bug, a review); other rows go through
  brainstorming. The user answers only the decisions that row 55 names. Goal:
  one intake call first (goal, scope, route, limits). Then an agent drafts,
  with options for each key decision, and hardens the draft through the
  draft-time checks of the [spec hardening
  audit](docs/reports/2026-10-14-spec-hardening-audit.md) until a round finds
  nothing new. First framed as "Draft specs in forks"; reframed on 2026-10-14
  after the fork drafts of rows 45 and 46 and the audit, and gated on a source
  the same day. Open: how the hardening loop stops, since
  `global/methods/my.md` allows one fix round per review; and drafting several
  specs from one request, which the reframe dropped and no row covers. Tried
  without this design on zitamu on 2026-10-15 (rows 76, 77 and 74): forks ran
  `my:architect` and wrote three specs with no intake call, decisions came as
  defaults, and 35 questions came in one batch. The user named it a skipped
  brainstorming. 76 and 77 are test-driven through plan and code in worktrees,
  unmerged, as evidence for this row. Tried again on zitamu row 146 on
  2026-10-16, by hand, with brainstorming run and a "Decisions made without
  you" section: 2 questions and 4 marked decisions in place of 35 questions,
  and the review's design findings became decisions. Three lessons. The agent
  measured a local build and decided not to check production first, so it
  missed that the live edge sent scripts uncompressed; a row that depends on
  live state needs a read of it (the live site in Playwright, the server
  config) before deciding. A 10-line server change got a 340-line spec, so the
  intake must first ask whether the row is bounded and needs no spec. The
  agent acted on an unclear two-word reply in the Q&A round; an unclear reply
  gets a question back.
- 💭 54 **Bugs and approved bounded rows in forks while the user is away** —
  bug rows, and bounded rows whose chat design the user approved before
  leaving. They have no spec, so `my:handoff auto` cannot start them. Each
  runs in a fork and its own
  worktree up to the merge, under one e2e lock that every session takes. The
  main session reads each fork's e2e log and test diff itself, then merges
  one branch at a time. Tried on zitamu on 2026-10-14 (rows 112 and 102,
  beside row 103's spec draft, 31% of a 1M context); there the lock bound
  only that session's forks. Open: the forks made decisions the user never
  saw (Greek copy, new tokens, scope dropped from a finding, review findings
  declined). Some of these must go back to the developer, the user, but
  which ones is not settled yet. Pairs with 53.
- 💭 55 **Decisions that go back to the user** — rule in
  `global/methods/my.md`, route not set. Forks, auto runs and review fixes
  make some choices without the user that the user should make. Goal: one rule
  for all three: a choice goes back when it changes what users see, a shared
  definition or contract, the scope of the row or finding, or the verdict on a
  review finding. It may narrow which `design` findings go to the user. Rows
  53 and 54 use it. Sources: the [spec hardening
  audit](docs/reports/2026-10-14-spec-hardening-audit.md) and row 54's zitamu
  run, and the [run
  audit](docs/reports/2026-10-15-row-74-handoff-run-audit.md) H1 and H2.
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
- ✅ 59 **Shared parts named in the spec** — Visual Language names the other
  pages that use each drawn element, and one with two or more becomes a
  shared component; `my:spec-review` checks it. zitamu's row 74b built every
  drawn part inside its page (2026-10-15). Small.
- ✅ 64 **`my:design-system`: an inventory every UI spec reads** — one
  `docs/DESIGN-SYSTEM.md` per project, counted by
  `plugins/my/bin/ds-count.py`, which a `my:design-system` skill audits,
  refreshes at step 13 and syncs to a Design System artifact. Shipped
  2026-10-16; `sync` is not rehearsed yet (plan Risk). Large.
  [spec](docs/plans/2026-10-16-design-system-skill-spec.md),
  [plan](docs/plans/2026-10-16-design-system-skill.md)
- ✅ 70 **Choose the design skill** — feature in `kit` and the core,
  architectural with plan. Design work runs the installed design skill that
  fits the job, and Claude can no longer call a third-party design skill
  directly. A `kit:design-router` skill names and starts the skill, a
  `PreToolUse` gate refuses other calls, and the design-system rules leave
  `global/methods/my.md`. Shipped in `5dfd634`; manual steps and known
  limits are in the plan's Risk section.
  [spec](docs/plans/2026-10-20-design-router-spec.md),
  [plan](docs/plans/2026-10-20-design-router.md)

## Harness generalization

Make the harness reusable in new projects without forking copies. Spec:
[`docs/plans/2026-06-16-harness-generalization-audit.md`](docs/plans/2026-06-16-harness-generalization-audit.md).

- 💭 17 **Generalize the gates** — feature in the gate hooks (`e2e-gate`,
  `review-gate`, `require-*`), route not set. A new project that wants the
  gates has to copy them. Goal: move the gate logic into the plugin behind a
  per-repo `.claude/harness.json`, with a `/harness-init` bootstrap. Waits for
  a second project to adopt the gates; today only `diagoradisa-annotator` uses
  them. Design and reasons in the spec.
- 💭 39 **`kit:setup` offers a Parallel runs section** — feature in
  `kit:setup`, route not set. The user writes a project's Parallel runs
  section by hand, and a `CLAUDE.local.md` line can wrongly say the project
  has none (zitamu, 2026-10-15). Goal: `/kit:setup my` asks whether to allow
  parallel auto runs, proposes the section's four lines from the machine's
  memory and the repo's compose, `.env` and e2e files, asks for the ports
  already in use, and fixes that line. Split out of row 9's first spec draft.
  Blocked by row 29.
- 💭 68 **Methods as plugins** — feature across the methods, `kit` and the
  marketplace; architectural with plan. Today a directory picks its method
  through an import line, plugin keys and `method-guard.py`. Goal: each method
  becomes a plugin whose forced output style holds its rules and whose
  `dependencies` hold its plugins. A directory's settings name its method, and
  `claude-method <m>` switches one session at launch. It replaces the import
  line, the plugin keys and `method-guard.py`. Brief approved, brainstorming
  next. Reframed on 2026-10-20 from a launcher named `claude`; row 48 was
  folded in on 2026-10-18.
  [brief](docs/plans/2026-10-20-method-bundles-architecture.md)
- 💭 69 **Shared skills move to `kit`** — feature, moving skills from `my` to
  `kit`; architectural with plan. `roadmap-management` and
  `changelog-management` live in `my`, so other methods cannot use them. Goal:
  both move to `kit`, and every `my:` reference is renamed. `link-check.py`,
  its test and its `README.md` sentence move with them. Row 70 takes the `design-system` rules out
  of the method, so this row decides whether that skill moves to `kit` or is
  deleted.
- 📋 71 **Project rules outrank the core** — rule in the core's Precedence
  paragraph (`global/CLAUDE.md`), route not set. Today the core and the method
  call themselves the highest authority, so a project's own rules can lose to
  them. Goal: the paragraph lists the order: protected rules, the user, the
  project files, the method, the core, then skills. Two protected rules: ask
  before adding dependencies, and before actions that are hard to undo or
  leave the machine. Spec drafted, not placed in the order yet.
  [spec](docs/plans/2026-10-18-project-precedence-spec.md)
- ✅ 16 **Swappable methods** — split `global/CLAUDE.md` into a neutral core
  and per-method files, and split `my` into `my` (the method) and `kit`
  (neutral tools), so one project can try another method. Shipped; 11 of 22
  repos set up, and the plan's status line says what is left.
  [brief](docs/plans/2026-10-12-swappable-methods-architecture.md),
  [spec](docs/plans/2026-10-12-swappable-methods-spec.md),
  [plan](docs/plans/2026-10-12-swappable-methods.md)
- ✅ 18 **Global orphan-plan hook** — `check-orphan-plans.sh` runs in the `my`
  plugin at session start, in all repos.
- ✅ 19 **Runtime-command contract — DRAFT** — written down, not adopted:
  [`docs/harness-runtime-contract-DRAFT.md`](docs/harness-runtime-contract-DRAFT.md).

## Workflow efficiency

Findings of
[`docs/reports/2026-10-09-workflow-efficiency-critique.md`](docs/reports/2026-10-09-workflow-efficiency-critique.md).
Rows are unordered unless a row says what it waits for. S2, S3, M1 and M3 got
no row; the report says why.

- 💭 20 **Specs and plans name what UI tests check** — rule in `plan-format.md`
  and `global/methods/my.md`, route not set. A plan that changes UI need not
  say which widths, languages and texts its tests check, so a test can check
  the markup and miss what the user gets. Goal: `plan-format.md` asks such a
  plan to list the widths at its breakpoint edges, every language the project
  ships, and its longest real text, and to measure them in e2e tests. In
  `global/methods/my.md`, "End-to-end coverage" asks the test to check what
  the user gets (the video plays), not only the markup, and the spec rules ask
  a spec that adds UI to decide the off-path events of row 23, next to Visual
  Language. Report M4. Rows 21 and 22 were folded in on 2026-10-16.
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
- 💭 29 **Measure the auto runs** — measurement of `my:handoff auto`, route not
  set. Nobody knows yet whether auto runs made work faster, or whether the row
  queue and parallel runs are worth keeping. Goal: after a few weeks of
  `my:handoff auto` on zitamu, rerun the spec-to-`done` timing and the
  docs-only commits per branch (zitamu's commit size audit) against the
  2026-10-12 numbers. Also count how often two or more approved specs waited
  at once: that count decides whether the row queue and parallel runs stay.
  Runs row 72's script; the [speed
  audit](docs/reports/2026-10-18-workflow-speed-audit.md) holds the numbers to
  compare with. Waits for those weeks. Report M2;
  [critique](docs/reports/2026-10-15-parallel-runs-section-critique.md).

## `my:handoff` instructions

Findings of
[`docs/reports/2026-10-12-handoff-instructions-audit.md`](docs/reports/2026-10-12-handoff-instructions-audit.md).
Their order is in "Order of work" above.

- 💭 30 **Split `my:handoff` by mode** — refactor of `my:handoff` `SKILL.md`,
  route not set. Every stage loads the auto-only and parallel-only text too,
  and review step 8, the merge step, has four versions. Goal: move that text
  into files read through a pointer step, so a stage loads only its own
  branch. The four versions of step 8 become one list per mode; smaller
  patches sit under the step they change. Rehearse a supervised and an auto
  run headless before and after. Waits for row 29 "Measure the auto runs".
  Report P1, P2. Row 31 was folded in on 2026-10-16.
- ✅ 32 **One script for the locked commit** — a `locked-commit.py` that reads
  the message from a file replaces the five copies of the locked command and
  the commit's heredoc rule. Report P3. Shipped in `39000ec`; known limits are
  in the spec's Risk section.
  [spec](docs/plans/2026-10-12-locked-commit-spec.md)
- 💭 33 **Parallel squash-merge uses the wrong branch** — bug in
  `my:handoff`. With a "Parallel runs" section, the review stage's
  squash-merge fails or merges the wrong branch. Fix: the merge command stops
  using `$1` and `$2`, which Claude Code fills with the skill's arguments,
  and kit's placeholder test also checks `my`.
  [Report](docs/reports/2026-10-14-scriptable-skill-steps.md) B1 (the bug),
  S1 (the fix).
- 💭 34 **Merges read a message file** — feature in `handoff-state.py` and
  `my:handoff`, route not set. The merges take their commit message from a
  heredoc, so `my:handoff` must keep the heredoc rule. Goal: `handoff-state.py
  merge` and the parallel squash-merge take `-F <file>`, so the heredoc rule
  leaves `my:handoff`. Changes the `handoff-state.py` interface. Out of scope
  of the [locked commit spec](docs/plans/2026-10-12-locked-commit-spec.md).
- 💭 35 **Trim `my:handoff` text** — rule text in `my:handoff`, route not set.
  The skill repeats a table and design explanations, and points with "as in
  Plan stage, step N". Goal: the lock exit-code table points to
  `handoff-lock.py --help`, and design explanations stay in the specs. *Locked
  commit*, *shared-doc check* and *waiting fixups* replace "as in Plan stage,
  step N". Report P4, P5. Row 36 was folded in on 2026-10-16.
- 💭 37 **Handoff opens no window from outside tmux** — bug in `my:handoff`.
  When Claude runs outside tmux, a handoff prints a command to paste
  by hand, even when tmux is running. Fix: the Launch step reads only
  `TMUX`; when it is empty, pick a session from `tmux ls` (for example the
  one named after the repo) and open the window with `-t <session>:`.
- 💭 56 **Two supervised runs get the same port** — bug in `my:handoff`.
  Two supervised (not auto) runs at the same time get the same
  preview port and other per-run values, so the second fails to start. Fix:
  a supervised run has no state file and always takes slot `1`, so give it
  a slot of its own.
  [Critique](docs/reports/2026-10-15-parallel-runs-section-critique.md) P1,
  which names this bug as one case; shipping this row does not close P1.
- 💭 57 **An auto run that stops before the merge** — feature in `my:handoff`,
  route not set. A test drive of the auto path, `decide` included, always ends
  in a merge. Goal: a Delegation key, or an `auto` flag, that stops at
  stop-table row 14 "Ready to squash-merge". Found on zitamu on 2026-10-15;
  not from the audit report.
- 💭 66 **Window row lookup by script** — feature in `my:handoff`, route not
  set. A handoff window can get no row prefix, or a wrong one, because the row
  is found by the prose lookup of row 65. Its known limits: a batch plan whose
  slug differs from its spec's gets no prefix, a missing `ROADMAP.md` is not
  named as "no row", Launch step 1 builds `<window>` before step 3 finds the
  repo root, and `resume` windows get a prefix. Goal: a tested helper finds
  the roadmap row for a doc, or the `auto rows` queue passes its stored row
  through.
- ✅ 38 **Rubric fixes in `my:handoff`** — `PushNotification` is loaded before
  use, findings are classified in writing before a fix, and the code stage's
  auto sub-steps have their own letters. Small. Report R1 to R4.
- ✅ 65 **Windows name their roadmap row** — `my:handoff` names each tmux
  window `r<row>: <stage>-<slug>`, the `kit:name-pane` prefix, with the row
  that links the doc. Small; known limits are in the squash commit and in
  row 66. Not from the audit report.

## Scripted skill steps

Findings of
[`docs/reports/2026-10-14-scriptable-skill-steps.md`](docs/reports/2026-10-14-scriptable-skill-steps.md):
steps of the `my` and `kit` skills that fixed rules decide, and that a script
in `bin/` can run instead of the model. Their order is in "Order of work"
above.

- 💭 42 **Parallel runs parser** — feature in `handoff-state.py`, route not
  set. `my:handoff`, `my:status`, `kit:commit` and `my:architect` each read
  the Parallel runs section by hand. Goal: a `handoff-state.py` subcommand
  prints **Max runs**, `<n>`, the docs paths and the `--docs-paths` arguments
  for them. Report S4. Blocked by row 29.
- 💭 43 **`handoff` start checks as a script** — feature in `my:handoff`, route
  not set. The start checks run by hand, and a Delegation command list with
  prose in a value, or a value wrapped onto two lines, gets through (zitamu,
  2026-10-15). Goal: a subcommand prints `<slug>`, `<name>` and `<base>`, the
  first failed start check, the Delegation validation and the restart point.
  The validation refuses a command list with prose in a value, or a value
  wrapped onto two lines. An auto launch also asks once about changes on
  `main` that would block the fold ([run
  audit](docs/reports/2026-10-15-row-74-handoff-run-audit.md) H4). Report S2,
  S3.
- 💭 44 **`git-fold-fixups.py list <path>`** — feature in `git-fold-fixups.py`,
  route not set. `my:handoff` finds a document's waiting fixups by hand in
  three places. Goal: `git-fold-fixups.py list <path>` lists them. Report S6.
- 💭 45 **Review preparation as a script** — feature in `my:soundness-review`
  and `my:spec-review`, route not set. Every review starts with the same fixed
  steps, done by hand today, and two reviews that started in the same second
  once shared one work folder. Goal: a script does these steps. Report S5;
  [draft spec](docs/plans/2026-10-14-review-prep-script-spec.md).
- 💭 46 **`git-squasher` plan and apply scripts** — feature in
  `kit:git-squasher`, route not set. The model applies the skill's fixed grouping
  rules by hand, and a commit message may not contain a single quote. Goal:
  scripts plan the groups and apply them, reading messages from a file.
  Report S7; [draft spec](docs/plans/2026-10-14-git-squasher-scripts-spec.md).
- 💭 47 **`clean-plans` moves by script** — feature in `my:clean-plans`, route
  not set. The model picks the files, dates them, moves them and repoints the
  links by hand. Goal: a script does the candidate list, the date, `git mv` or
  `mv`, and repointing the links; "Moving a document" in `docs-layout.md` uses
  the same script. Report S8.
- 💭 49 **`dev-reports` dates and TODOs by script** — feature in
  `kit:dev-reports`, route not set. The model works out the dates and the TODO
  list by hand. Goal: a script computes the ISO week, the Monday rule, the
  days with commits and the TODO extraction. Report S10.
- 💭 50 **`clean-gone-branches` as a script** — feature in
  `kit:clean-gone-branches`, route not set. The model lists, checks and
  deletes the branches by hand. Goal: a script does the list, the check and
  the delete; the command keeps the approval question. Report S11.
- ✅ 51 **Link check for the roadmap and changelog** — feature in
  `my:roadmap-management` and `my:changelog-management`; architectural. The
  model checked links by eye, and only in the row or entry it edited. Now
  `link-check.py` lists the bad links in `ROADMAP.md` and `CHANGELOG.md` and
  marks those on lines the edit changed; the skills fix those and list the
  rest. The next-number part was dropped on 2026-10-20. Shipped in
  `6042aa3`; known limits are in the spec's Risk section. Report S12;
  [spec](docs/plans/2026-10-20-link-check-spec.md)
- 💭 52 **`status` gates and overlap by script** — feature in `my:status`,
  route not set. The model runs `my:status` steps 5 and 6 and the overlap test
  by hand. Goal: a script does them. Report S13.
- ✅ 41 **`git-squasher` loses `$1`** — fix: the `squash-todo.sh` example in
  `kit:git-squasher` step 5 uses `"${1}"`, which Claude Code leaves alone, and
  a test refuses a bare `$` and digit in kit skill text. Small. Report B1.

## Handoff run audit

Findings of [`docs/reports/2026-10-15-row-74-handoff-run-audit.md`](docs/reports/2026-10-15-row-74-handoff-run-audit.md), from zitamu rows 74a and 74b.

- 💭 60 **Project facts in `CLAUDE.local.md`** — fix: the facts check in
  `global/methods/my.md` and `kit:setup` also accept `CLAUDE.local.md`, as
  the Parallel runs rule does, and `kit:setup` asks which file to use.
  Report H4.
- 💭 61 **Auto start on approval, and re-review findings as rows** — rule in
  `global/methods/my.md`, route not set. After approving a spec with a
  Delegation section, the user still answers "supervised or auto?", and a
  re-review finding that today's code can reach may end up only in **Risk**.
  Goal: two rules. When the approved spec has a Delegation section, approval
  starts `/my:handoff auto` with one line saying so, in place of the question
  (report H3). "One fix round per review" sends a re-review finding that
  today's code can reach to a new roadmap row; **Risk** keeps only input that
  today's code never produces (report H8). Row 63 was folded in on 2026-10-16.
- 💭 62 **Question prompts follow `plain`** — rule in
  `global/output-styles/plain.md`, route not set. Multiple-choice questions
  use the agent's own terms, such as "force" or "tab", so the user cannot answer
  them. Fix: the `plain` style also covers these questions. Report H5.

## Superpowers fit

Findings of [`docs/reports/2026-10-14-superpowers-fit-critique.md`](docs/reports/2026-10-14-superpowers-fit-critique.md).
Only F1 is routed so far.

- ✅ 67 **Brainstorming's paths replace the size table** — rule in
  `global/methods/my.md` and the files that name the sizes, architectural
  with plan. A session picks its process as superpowers' brainstorming does
  (spike, bounded or architectural), not by a second `my` size. `my` adapts
  the paths with a risk line, a two-file limit on bounded, a bug route and a
  spike file. Shipped; known limits are in the plan's Risk section. Report F1.
  [spec](docs/plans/2026-10-18-brainstorming-routes-spec.md),
  [plan](docs/plans/2026-10-18-brainstorming-routes.md)

- 💭 73 **`my:status` lists every spike branch as unfinished work** — bug in
  `plugins/my/bin/status-scan.py` and `my:status`. A spike's `spike/<slug>`
  branch is never merged, so every report asks the user about it, for ever.
  Fix: treat `spike/` branches as records, not unfinished work. Found by
  row 67's end-of-branch code review; detail in its plan's Risk section.

## Workflow speed audit

Findings of [`docs/reports/2026-10-18-workflow-speed-audit.md`](docs/reports/2026-10-18-workflow-speed-audit.md).
W1 to W5 are evidence for rows 29, 30, 55, 61 and 67; W6 and W7 are zitamu
proposals with no row; the report says why.

- 💭 72 **Workflow metrics as one `my` script** — feature in `plugins/my/bin/`,
  route not set. Four reports each built one-off scripts for the same
  measures. Goal: one tested script that measures a project's shipped rows
  from git and its sessions from transcripts, starting from the three in
  [the report's assets](docs/reports/assets/2026-10-18-workflow-speed/).
  Row 29 runs it. Report W8.

## Other

Older self-contained efforts (code-review consolidation, planning-standards
single-source, briefing skill, Opus prompt tuning, …) are dated specs in
`docs/plans/`. They are not indexed here unless they spawn open follow-ups.
