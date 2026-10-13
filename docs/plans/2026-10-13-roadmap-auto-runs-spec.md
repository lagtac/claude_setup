# Spec: start auto runs from roadmap rows

**Status:** draft, 2026-10-13. Waiting for the user's review.

## How to read this spec

| Document | Path | Why you would read it |
| --- | --- | --- |
| Architecture brief | `docs/plans/2026-10-13-roadmap-auto-runs-architecture.md` | The forces, the three candidates and why candidate A won. This spec settles its "Open for brainstorming" list. Read first. |
| **This spec** | `docs/plans/2026-10-13-roadmap-auto-runs-spec.md` | What to build and why. |
| Spec review | `docs/plans/2026-10-13-roadmap-auto-runs-spec-review.md` | The review of the first draft: Problematic, 2 Critical. Every finding is answered in this version. Its decision numbers D8 to D10 no longer exist. |
| Second spec review | `docs/plans/2026-10-13-roadmap-auto-runs-spec-review-2.md` | The review of the second version: Problematic, 1 Critical (fixups that can never be folded). Every finding is answered in this version. |
| Implementation plan | `docs/plans/2026-10-13-roadmap-auto-runs.md` | Written after this spec is approved. It holds argument forms, exit codes and test cases. |
| Roadmap | `ROADMAP.md`, rows 9, 39 and 40, and `## Order of work` | Row 9 is this spec. Rows 39 and 40 took the two parts split out of the first draft. Row 9's gate, row 16 "Swappable methods" batch 2, merged in `a0144ee`. |
| Parallel-runs spec | `docs/plans/2026-10-12-parallel-auto-runs-spec.md` | The "Parallel runs" section, the locks, `start --max` and the slot rule. Its "Out of scope" said runs start only when the user starts them; this spec lifts that. |
| Status spec and skill | `docs/plans/2026-10-12-status-skill-spec.md`, `plugins/my/skills/status/SKILL.md` | Steps 4 to 6 (spec, gates, file lists), which the new call reuses. |
| Handoff skill and README | `plugins/my/skills/handoff/SKILL.md`, `plugins/my/skills/handoff/README.md` | "Signal", "Launch", "Start checks", "Start checks in auto mode", Plan stage step 8, Code stage sub-steps a and b, Review stage step 8 sub-steps 3 and 4, "To end an abandoned run", "Finish". |
| State script and tests | `plugins/my/bin/handoff-state.py`, `plugins/my/tests/test_handoff_state.py`, `plugins/my/tests/test_parallel_runs.py` | `start`, `live`, `write_state`. The new `queue add`, `queue drop`, `queue show` and `pull` sit beside `start`. |
| Status scan and tests | `plugins/my/bin/status-scan.py`, `plugins/my/tests/test_status_scan.py` | Gets a `queue` block. |
| Docs layout rule | `global/rules/docs-layout.md` | "One feature, four commits on `main`", steps 4 and 9: the fixup and fold that D3 uses. |
| Fold script | `plugins/my/bin/git-fold-fixups.py` | Run by the call when it is safe (D3). |

## Context

`/my:handoff auto plan <spec>` and `auto code <spec>` take one approved spec
to its `done` marks without the user. A project with a "Parallel runs" section
allows up to **Max runs** of them at once. But the user still starts each run
by hand, one command per spec, and must come back when a run finishes to
start the next one. With three approved specs, that is three commands typed
at three different times.

Two more facts shape this spec:

- **This machine has 15 GB of memory.** The handoff README advises
  `Max runs: 1` on such a machine, and this repo has no "Parallel runs"
  section, so Max runs is 1 here anyway. On this machine the feature is a
  queue: rows run one after another, without the user. On a larger machine,
  in a project with the section, the same queue runs rows side by side.
- **Specs leave their `approved` edit uncommitted** until their own plan or
  code stage commits it. A queued spec waits for hours. While it waits, the
  main checkout is not clean, and the running row's fold stops at stop-point
  row 16 ("`<base>` is not clean, so the fold must wait"). D3 fixes this.

## Goal

1. The user types one command with a list of roadmap row numbers, such as
   `/my:handoff auto rows 9 12 30`, in any order, and walks away.
2. Every listed row that can start ends in one of the two end states of an
   auto run: merged with its `done` marks, or stopped with a clear line and a
   state file. Every row that cannot start is listed with its reason when the
   command runs.
3. Never more than **Max runs** runs are live. Each row starts at most once.
   A row gated behind another row never starts before that row finished with
   its `done` marks.
4. When the first waiting row could start now but nothing starts it,
   `my:status` says so and names the command that starts it.

## Out of scope

- **A supervisor or background worker** that watches the runs (brief,
  Candidate B).
- **Automatic repair of a crash** between a run's finish and its refill. The
  `my:status` line and a rerun of the command cover it (D7).
- **Rows without an approved spec with a Delegation section.** Writing a spec
  needs the user.
- **A cost limit per call.** The call is the user's approval. Row 29 "Measure
  the auto runs" can add one later, based on measured numbers.
- **Row 37 "Launch from a session outside tmux".** A refill from a review
  session always runs in a tmux window. A refill from the user's own session
  ("To end an abandoned run") may fall back, and D6 covers that. So only the
  first call needs tmux, as `/my:handoff auto` does today.
- **Row 39 "`kit:setup` offers a Parallel runs section"** and **row 40
  "Every spec has a Files section".** The first draft held both. They were
  split out because an auto run carries one branch and one squash-merge.
  This spec works without them: a row with no file list runs alone (D2).
- **Adding a "Parallel runs" section to this repo.** After row 39 ships, the
  user may run `/kit:setup my` here and decide.
- **Pinning the plan's text.** The pin covers the spec only (D4).

## Decisions

**D1: One new form, `/my:handoff auto rows [<row number> ...]`.** It runs in
the user's session. `<name>` for its signals is `rows`.

- With numbers, it judges each row (D2), commits the `approved` edits (D3),
  writes the queue (D4), runs `pull` (D5) and launches one window per row
  that `pull` prints. Then it ends. No session stays open to watch.
- With no numbers, it only runs `pull` and launches. This is how the user
  starts the first waiting row after a stall.
- `/my:handoff auto rows drop <row number> ...` cancels waiting rows with
  `queue drop` (D4).
- The usage line of `my:handoff` gains these forms.

**D2: The call judges each row once, at call time.** It runs
`status-scan.py` once and uses the rules of `my:status` steps 4 to 6. A row
is skipped, listed with its reason, and not written to the queue, when any of
these holds:

| Case | Reason printed |
| --- | --- |
| The roadmap has no row with that number. | `no row <n>` |
| The row has no spec of its own (`my:status` step 4). | `row <n> has no spec` |
| The spec's status is not `approved`. | `spec is <status>, not approved` |
| The spec has no valid Delegation section (`my:handoff` "Delegation"). | `Delegation: <key> <missing, unknown or invalid>` |
| A state file for its slug exists and its `next` is not `finished`. | `a run for <slug> exists` |
| The slug is already `waiting` in the queue. | `already waiting` |
| The stage could not start fresh: a plan `docs/plans/<date>-<slug>.md` exists (the anchored `ls` of the plan start check), `git branch --list '*/<slug>'` prints a branch, or `.claude/worktrees/<slug>` exists. These are the "Start checks" for a fresh start; a run the user ended leaves its branch behind. | `<plan, branch or worktree> for <slug> exists` |
| It is gated behind a row that is not done and is none of: a row in this call, a live auto run (a state file whose `next` is not `finished`), a `waiting` queue entry. Nothing would ever start such a blocker. A row is done when it is ✅, or when its slug's state file has `next=finished` and an empty `stopped`: a `done` mark does not always set ✅. | `blocked by row <m>, which nothing will start` |
| It is gated behind a row in this call that this call skips. | `blocker row <m> was skipped` |
| Its own text says it waits for something that is not a row ("Waits for …", `my:status` step 5). Nothing in the queue would start it. | `waits for <what the row says>` |

For each row that can start, the call records:

- **`stage`:** `code` when the spec has a section titled Tasks, `plan` when
  not. This is the existing rule of start check 4.
- **`after`:** the slugs of the rows it is gated behind (`my:status` step 5):
  rows in this call, live auto runs and `waiting` entries. A done blocker is
  no gate.
- **`exclusive`:** `true` when the row has no file list (`my:status` step 6).
  Its overlap is unknown.

When two rows in the call both have file lists and share a path outside the
docs paths, the call prints a warning naming the path. It does not block: the
parallel merge already rebases and reruns the checks.

**D3: The call commits each queued spec's `approved` edit before it writes
the queue.** This applies the Code stage's sub-steps a and b, and the rule
for a supervised Medium hand-off in `global/methods/my.md`, to every queued
spec. So a queued spec never holds an uncommitted edit.

- **A fixup only when the call folds it at once.** A fixup that waits is
  never safe here. The run ahead finishes first, and its `done` mark cites
  its squash commit, which is newer than every queued spec. From then on
  `git-fold-fixups.py` refuses to fold the waiting fixup, and the queued row
  stops at Plan stage step 8 or Review stage sub-step 3, where `resume`
  cannot clear it.
- **Without a "Parallel runs" section, the call folds when all of these
  hold:** `handoff-state.py live` lists no run; `git status --porcelain`
  prints nothing; and `git-fold-fixups.py check <spec commit>` exits 0 for
  every edited spec, where `<spec commit>` is the commit that added it.
  First list every `fixup!` commit already on `<base>`. When one targets a
  document outside this call, name it and ask the user, because the fold
  gives that document's commit a new hash. Then make one
  `git commit --fixup <spec commit> -- <spec>` per spec and run
  `git-fold-fixups.py`.
- **Otherwise one normal commit.** When any of those does not hold, or the
  user says no, make one normal docs commit with every edited spec, with the
  scope the project's rules give docs. When the fold itself refuses after
  the fixups, print its message and `fixups left unfolded: <hashes>`, write
  no queue and launch nothing: those fixups must be folded or reverted by
  hand before a row behind them can run.
- **With a "Parallel runs" section:** one normal commit with every edited
  spec, through `locked-commit.py`. Nothing folds there.

The plan stage already handles a committed `approved` edit: its step 6 lists
no hunk for the spec. The code stage handles it in start check 7.

**D4: The queue is one file, `<git common dir>/my-handoff/queue/rows.json`.**
It is a JSON list. `handoff-state.py` is its only writer, and every write
runs under lock `main`. It sits in a subfolder because `live` and
`status-scan.py` count every `my-handoff/*.json` as a run.

| Field | Value |
| --- | --- |
| `row` | The roadmap row number, as written (`9`, `1b`). |
| `slug` | As `my:handoff` derives it from the spec path. |
| `spec` | The spec path. |
| `stage` | `plan` or `code`. |
| `after` | A list of slugs, maybe empty. |
| `exclusive` | `true` or `false`. |
| `spec_hash` | `git hash-object <spec>` after D3's commits. |
| `state` | `waiting`, `started` or `skipped`. |
| `reason` | Empty, or why the entry was skipped. |

`handoff-state.py queue add` takes every entry of one call in one command:

- **Validate.** It refuses the whole command, and writes nothing, when any
  entry is invalid: an unknown field, a bad slug, a `stage` other than `plan`
  or `code`. An entry whose slug is already `waiting` is not added; `add`
  prints it, and the call lists it as skipped.
- **Order blockers first.** It appends the new entries after the existing
  ones, sorted so that each comes after every new entry named in its
  `after`, and otherwise in the order the user typed them. Entries that wait
  for each other in a loop are not added; `add` prints each one as
  `skipped: <slug>: gate cycle`.
- **Prune safely.** It drops a `started` entry whose state file has
  `next=finished`, and a `skipped` entry that no `waiting` entry names in its
  `after`. Every other entry stays, because `pull` still reads it. A
  `started` entry is the only record that a live run is `exclusive`.

`handoff-state.py queue drop <slug> ...` marks each named `waiting` entry
`skipped` with `dropped by the user`. Rule 2 of D5 then skips the rows
behind it. The plan fixes the argument forms.

**D5: `handoff-state.py pull --max <n>` picks and starts rows in one locked
command.** The caller runs it as `handoff-lock.py main -- handoff-state.py
pull --max <n>`, with `<n>` as "Parallel runs" says (1 without the section).
Inside, `pull` calls the existing `start()` code in the same process. It must
never run `handoff-lock.py main` itself: a second `flock` on the same lock
file waits for the first and times out with exit 75.

`pull` walks the `waiting` entries in queue order. For each entry:

1. **Spec changed:** when `git hash-object <spec>` differs from `spec_hash`,
   mark it `skipped` with `spec changed since the call`.
2. **Blocker failed:** mark it `skipped` with `blocker <slug> did not finish`
   when a slug in `after`:
   - belongs to a `skipped` entry; or
   - has a state file with `next=finished` and a non-empty `stopped`, which is
     a run the user ended; or
   - has neither an entry nor a state file.
3. **Ready:** every slug in `after` has a state file with `next=finished` and
   an empty `stopped`. A successful finish writes `stopped=` (Review stage,
   sub-step 4). An entry that is not ready stops the walk.
4. **Exclusive:** an `exclusive` run is live when a `started` entry is
   `exclusive` and its state file's `next` is not `finished`. While one is
   live, nothing starts. An `exclusive` entry starts only when no run is
   live. An exclusive entry that cannot start yet stops the walk, and so does
   one that has just started.
5. **Cap:** when the live runs reach `<n>`, the walk stops.
6. **Start:** write the state as the auto launch does: `spec`, `task_doc`,
   `next=<stage>`, the empty fields, `slot` and `merge_retries=0`. `task_doc`
   is the spec for `code`, and `docs/plans/<spec date>-<slug>.md` for `plan`.
   Then mark the entry `started` and print one line: slug, stage, spec, slot,
   split by tabs. When `start()` refuses because a run for the slug exists
   (the user started it by hand), mark the entry `skipped` with
   `a run for <slug> exists`, and go on.

Rules 3 and 4 stop the walk, so a row never passes the first row that is
still waiting. Without this, an exclusive row could wait forever while the
rows behind it keep taking the free slot. Because `queue add` puts blockers
first, the first waiting row is never gated behind a row that waits behind
it. Each skip prints one line on stderr that starts with `skipped:`, so the
caller can report it.

A queue file that is not valid JSON makes `pull`, `queue add` and
`queue drop` refuse and change nothing. No queue file means nothing waits:
`pull` prints nothing and exits 0.

**D6: A finishing run refills its slot.** Two places get the same steps:

- Review stage, step 8, sub-step 4, after
  `handoff-state.py set <slug> next=finished stopped=`.
- "To end an abandoned run", after the run is marked finished.

The steps: run `pull` as in D5. For each printed line, run "Launch" in auto
mode with the name `<stage>-<new slug>` and `MY_AUTORUN=<new slug>`. The
new slug matters: the review session's own `MY_AUTORUN` names the finished
run, and the new session's start check 1 would refuse it. Launch reads the
plugin-dir flags from the review session's own process and the mode from its
own context, as it does for a next stage today. Then go on to "Finish".

The finishing run is done, so a refill failure is never a stop of that run.
But the user must act, so the signal replaces "Finish": the window gets the
⚠ mark, not ✓. In the review stage, the signal line starts with
`<name>: done; squash commit <hash>.`, so the finish is not lost.

- **Launch cannot open a window:** run
  `handoff-state.py set <new slug> stopped="cannot open a window: <reason>"`,
  then signal `… cannot open a window for <stage>-<new slug>; run /my:handoff auto resume <spec>`.
  The new run keeps its slot, as any stopped run does.
- **`pull` fails,** a lock timeout included: signal
  `… rows wait in the queue; run /my:handoff auto rows`.

**D7: `my:status` shows the queue.** The `runs` block lists only live runs,
and the queue's `started` entries are not printed, so `my:status` cannot
judge D5's rules itself. The rules stay in one place instead:

- **`handoff-state.py queue show`** runs D5's walk, rules 1 to 4, and writes
  nothing. It ignores the cap, which `my:status` checks. It prints one line
  for the first entry the walk would reach: `ready`, slug; or `waits`, slug,
  and what it waits for: a blocker's slug, `exclusive <slug>` for a live
  exclusive run, or `live runs` for an exclusive entry that waits until no
  run is live. When nothing waits, it prints `none`. An entry that `pull`
  would skip is passed over, as `pull` would.
- **`status-scan.py`** prints a new block, `queue`: first that line, then one
  line per `waiting` or `skipped` entry, in queue order: state, row, slug,
  `after` (comma-separated or `-`), reason (or `-`). An unreadable queue file
  prints an `error` line, as the other blocks do.

The report gains:

- **Among the items that need the user:**
  `<k> rows wait and the first can start now: run /my:handoff auto rows`.
  Only when the `queue show` line is `ready` and the live runs are fewer than
  **Max runs**. Otherwise a rerun would start nothing.
- **Among the items in progress:** `<k> rows wait for <what>`, from the
  `queue show` line. When the line is `ready` but the live runs fill
  **Max runs**, it says `<k> rows wait for a free slot`. Then one line per
  `skipped` entry with its reason, until `queue add` prunes it.

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `cd plugins/my && python3 -m unittest discover tests`

## Files

| File | Change |
| --- | --- |
| `plugins/my/bin/handoff-state.py` | `queue add`, `queue drop`, `queue show` and `pull` (D4, D5, D7). |
| `plugins/my/bin/status-scan.py` | The `queue` block, with the `queue show` line (D7). |
| `plugins/my/skills/handoff/SKILL.md` | The `auto rows` forms (D1 to D3), the refill (D6), the usage line. |
| `plugins/my/skills/handoff/README.md` | A "From roadmap rows" section for a reader. |
| `plugins/my/skills/status/SKILL.md` | The `queue` block and its report lines (D7). |
| `README.md` | The `handoff-state.py` and `status-scan.py` paragraphs mention the queue. |
| `plugins/my/tests/test_handoff_state.py` | `queue add`, `queue drop`, `queue show` and `pull` cases. |
| `plugins/my/tests/test_roadmap_queue.py` | New: the end-to-end test (Testing). |
| `plugins/my/tests/test_status_scan.py` | The `queue` block. |
| `ROADMAP.md` | Spec commit: row 9 links this spec; new rows 39 and 40. |

## Trade-offs

- **A refill by the finishing run versus a supervisor.** No process waits and
  nothing new stays alive. The cost: a crash between a finish and its `pull`
  leaves a slot empty until the user reruns the command (D7). The brief
  rejected the supervisor (Candidate B) on forces 7 and 9.
- **Commit the `approved` edits in the call versus leave them.** Left
  uncommitted, they stop the first run's fold (Context). Fixups keep four
  commits per feature, but only when the call folds them at once: a fixup
  left waiting can never be folded once the run ahead cites a newer commit
  (D3). So the call falls back to one normal commit, which adds a commit to
  `<base>`. Rejected: always one normal commit, which adds a commit even
  when a fold was safe; and making the user commit the edits first, which
  adds a manual step per row.
- **First in line, with blockers sorted first, versus skip ahead.** A blocked
  or exclusive first row can leave a slot idle. Skipping ahead would fill it,
  but an exclusive row could then wait forever. Sorting blockers first keeps
  the walk from stopping on a row whose blocker waits behind it.
- **Queue a row gated outside the call only when its blocker can wake it.** A
  live auto run or a waiting entry finishes through the refill, which starts
  the row. Any other open blocker would leave the row waiting silently, so
  the row is skipped and the user calls it again later.
- **One spec per branch.** The first draft held three batches: this queue,
  the setup step and the Files rule. An auto run carries one branch, so the
  other two became rows 39 and 40, each with its own small spec.

## Dependencies

None. Python 3 standard library, git, tmux and Claude Code, as `my:handoff`
uses today.

## Risk

- **Hard to reverse: the queue file's format and location, and `pull` as an
  interface.** A change later means a migration of waiting entries, or
  keeping the old form readable. Waiting entries are few, so dropping them
  with a notice is an acceptable migration.
- **The fold in the call rewrites `<base>`.** It runs only when no run is
  live, the tree is clean and `check` passes for every spec. A `fixup!` of a
  document outside the call gets a new hash; the call asks first (D3). If the
  fold still refuses after the fixups are made, the call stops, and the user
  folds or reverts them by hand.
- **Frozen judgment.** Gates and `exclusive` are fixed at call time. A gate
  added to `## Order of work` after the call is not seen. Text added to a spec
  is caught by the hash pin; a new gate is not.
- **Silent stall.** A crash between `next=finished` and `pull` leaves a slot
  empty. Only `my:status` shows it (D7).
- **A run with no window.** A crash between `pull` and Launch leaves a live
  run with no window and no stop line. `my:status` shows it only as in
  progress. `/my:handoff auto resume <spec>` launches it.
- **A run started by hand is not seen as exclusive.** In a project with a
  "Parallel runs" section, `pull` cannot tell that a run the user started by
  hand has no file list, so it may start a queued row beside it. The parallel
  merge still rebases and reruns the checks. At **Max runs** 1 this cannot
  happen.
- **The refill text moves.** Rows 30 "Split `my:handoff` by mode" and 31
  "Write review step 8 whole" will move Review stage sub-step 4. The refill
  lines must move with it. Detection: the end-to-end test drives `pull`, but
  not the skill text; the plan for rows 30 and 31 must grep for `pull`.
- **Old specs have no Files section** and run alone. Rows here stay mostly
  serial until row 40 ships and new specs replace them.
- **Cost.** Assumed, never confirmed: each row about 3 stage sessions at 1.5M
  to 8M tokens each, with no limit per call.
- **Blast radius.** `handoff-state.py` is called from `my:handoff`, its
  README, `README.md`, `status-scan.py` (which runs `handoff-state.py live`),
  `my:status` and the tests. `status-scan.py` is called from `my:status`. The
  plan must sweep both names with `git grep` before it changes them.
- **Manual steps.** The rehearsal below is started by the user.

## Testing

All tests are `unittest` files, written red first, in temporary fixture
repos. The plan lists the cases.

- **`test_handoff_state.py`:**
  - `queue add` refuses an invalid entry and writes nothing, reports a
    duplicate, sorts blockers first, keeps the typed order otherwise, reports
    a gate cycle, and prunes only what D4 allows;
  - `queue drop` skips a waiting entry;
  - `queue show` prints `ready`, `waits` or `none` as `pull` would decide,
    and writes nothing;
  - `pull`: each rule of D5, one case each, including a blocker with no entry
    and no state file, and a start refused because a run exists.
- **`test_roadmap_queue.py`:** driven only through the real scripts, under the
  real `handoff-lock.py main`, in one fixture repo. Cases:
  - three rows at `--max 1`, typed with the dependent first: blockers start
    first, one start per finished run;
  - an `after` gate holds a row until its blocker finishes;
  - a blocker ended by the user, or dropped, skips the rows behind it;
  - a changed spec is skipped;
  - an `exclusive` row waits while another run is live, and blocks the rows
    behind it while it runs, also after a later `queue add`;
  - two `pull` commands at once never pass the cap;
  - `pull` inside `handoff-lock.py main` does not wait on its own lock.
- **`test_status_scan.py`:** the `queue` block, with waiting, skipped and
  unreadable queues.
- **Rehearsal, once, before the spec is marked `done`:** in a separate tmux
  server, against a fixture repo whose `origin` is a local bare repo, with no
  "Parallel runs" section and two tiny Medium specs, the second gated behind
  the first. The user runs `/my:handoff auto rows <second> <first>`. Check:
  one window opens, for the first; when it finishes, the second starts
  without the user; both end with their `done` marks on `main`; the bare repo
  is unchanged.

## Open questions

None.
