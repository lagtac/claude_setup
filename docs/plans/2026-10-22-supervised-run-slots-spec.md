# Spec: every run gets its own slot

**Status:** approved, 2026-10-22. Row 56; supervised `my:handoff` runs get a state file and a slot from the same pool as auto runs.

**Route:** architectural with plan. Row 56 is a bug. `superpowers:systematic-debugging` found the
root cause, and the fix changes the shape of the run state that `handoff-state.py` stores, which
hits the risk line. It touches more than two files, and it had several reasonable fixes. The user
chose on 2026-10-22 to settle the state change inside brainstorming, without `my:architect`.

## How to read this spec

1. `ROADMAP.md`, row 56 "Two supervised runs get the same port", and `## Order of work`, step 1.
2. `docs/reports/2026-10-15-parallel-runs-section-critique.md`, finding P1. It names row 56 as one
   case of per-command isolation, and says a supervised launch needs a slot of its own.
3. `plugins/my/skills/handoff/SKILL.md`: "Forms" (the slug, line 82), "Parallel runs" (lines 147
   to 200), "Resume" and "To end an abandoned run" (lines 358 to 400), "From roadmap rows" and
   "Refill" (lines 445 to 596), "Start checks in auto mode" (lines 639 to 712), the code stage
   (lines 827 to 910) and the review stage, step 8 (lines 1002 to 1050).
4. `plugins/my/bin/handoff-state.py`: the docstring, `live_states`, `start_run`, `walk` and
   `pull`.
5. `plugins/my/bin/status-scan.py`, `run_facts`, and `plugins/my/skills/status/SKILL.md`.
6. `plugins/my/tests/test_handoff_state.py` and `plugins/my/tests/test_status_scan.py`: the
   classes `StartTest`, `LiveTest`, `PullTest` and `RunsTest`.
7. `docs/plans/2026-10-22-supervised-run-slots-spec-review.md`. The spec review. Decisions D12 to
   D16 answer its design findings.

## Context

A run is one piece of work that `my:handoff` carries from stage to stage: plan, code, review. An
**auto run** goes without the user. A **supervised run** stops for the user at each gate.

A project's "Parallel runs" section can hold an **Isolation** line, for example
`PORT=$((54310 + <slot>))`. The code and review stages apply it to every test and server command,
so two runs do not share a port or a test stack. `<slot>` is a whole number per run.

**Root cause.** Only auto runs get a slot. `handoff-state.py start` writes an auto run's state
file and picks the lowest slot that no live state file uses (`start_run`). A supervised run writes
no state file, and `SKILL.md` line 185 says it "uses slot `1`". So:

- two supervised runs at once both use slot `1`;
- a supervised run and the first auto run both use slot `1`, because `start_run` cannot see the
  supervised run.

**"Slot" has two meanings in the skill.** It is the number above. It is also used for a place
under the cap, the most auto runs allowed at once: "a run that finishes frees its slot", "rows
wait for a free slot". The cap check counts live state files and never reads slot numbers. The
slot was designed as part of an auto run's state, so a run without state got none.

**Limit.** Without a "Parallel runs" section there is no Isolation line, so the slot is never
used. A search of every `CLAUDE.md` and `CLAUDE.local.md` under `~/projects` on 2026-10-22 found
no project with the section. This spec fixes the general problem. It takes effect in a project
once that project has the section (see Open questions).

## Goal

No two live runs in one project, of either mode, ever have the same slot.

## Out of scope

- Per-run values for a project without a "Parallel runs" section.
- Applying Isolation once at launch, as process environment (critique P1, "Better").
- Changing how auto runs stop, resume or count toward the cap.

## Decisions

| # | Decision | Why |
|---|---|---|
| D1 | A slot belongs to the run, not to a worktree. | A process can outlive its worktree, and later modes may work without one. Chosen over "the slot lives as long as the worktree" on 2026-10-22. |
| D2 | Every run has a state file, supervised runs included, in every project. | It removes "has no state file", the root cause. One rule everywhere; `my:status` sees supervised runs. The user chose every project over "only with the section". |
| D3 | A new field `mode`: `auto` or `supervised`. A file without it is `auto`. | Only auto runs wrote state before this change. |
| D4 | One slot pool: the lowest whole number from 1 that no live run uses, of either mode. A run is live while its `next` is not `finished`. | The Goal. |
| D5 | The cap counts only auto runs: `start --max` and rule 5 of `pull`. | The cap limits auto runs today. A supervised run must not block an auto start. |
| D6 | An exclusive row waits for every live run, of either mode: rule 4 of `pull`. | A row is exclusive because its overlap with other work is unknown. A supervised run edits files too. |
| D7 | A queued row's `after` may name live runs of either mode. | Today a row gated behind supervised work is skipped with `blocked by row <m>, which nothing will start` (`SKILL.md:487`), because its blocker is not a live auto run. With D7 it waits for that run. |
| D8 | The code stage writes a supervised run's first state, under the task doc's slug. The plan stage writes nothing. | In a batch, the spec's slug differs from its plans' slugs, so a plan-stage state would never finish. Only the code and review stages apply Isolation. |
| D9 | A supervised finish runs no refill. It prints a line when `queue show` says a row is ready. | The refill opens auto windows, which a supervised session may not be able to open. |
| D10 | `resume` refuses a supervised run. | `resume` launches auto stages only. |
| D11 | "Slot" keeps only the meaning of the number. The text says "place under the cap" for the other meaning. | The double meaning is how the bug arose. |
| D12 | Slots are not bounded by **Max runs**. They start at 1 and grow with the live runs of both modes. The README tells a project to leave room above **Max runs** for supervised runs. | D4 and D5 together allow an auto run a slot above **Max runs**. Bounding the pool would need a second rule. Review finding 1, user, 2026-10-22. |
| D13 | Auto start check 5 gets a supervised case: `a supervised run for <slug> exists; finish or end it first`. | The check runs before `start`, so its "use resume" text would hide the refusal of `start` and point to `resume`, which D10 refuses. Review finding 2. |
| D14 | The fold of `auto rows` step 4, in a project without the section, keeps waiting until no run is live, of either mode. | The fold rewrites `main` under every open branch, supervised branches included. Review finding 4. |
| D15 | `my:status` lists a live supervised run as needing the user when the queue waits on it. | A dropped supervised run blocks exclusive rows (D6) and `after` gates (D7), and has no stop line. Review finding 5. |
| D16 | Code stage step 4 stops the servers that the stage started under **Isolation** before it finishes a supervised run. | Otherwise a server in the shared worktree of a batch keeps the slot's port while another run takes the slot. Review finding 6. |
| D17 | The code stage sets `next=review` before it launches the review, in both modes. `resume` tells a supervised run at `code` with a branch to finish its tasks and run the review, or end the run. | A new code stage refuses once the branch exists, so "run /my:handoff code" led nowhere. End-of-branch review, user, 2026-10-22. |
| D18 | A supervised batch plan stays live after code stage step 4. The batch's review stage finishes every live run of the batch after the merge. | A finished run opens the `after` gate, so a gated row started before the batch's code was on `main`. Chosen over a new "merged" field. End-of-branch review, user, 2026-10-22. |
| D19 | `my:status` names the supervised run for a `live runs` wait only when no live auto run is live. | A live auto run also holds back that entry, so ending the supervised run would not start it. End-of-branch review, user, 2026-10-22. |

## Design

### 1. `handoff-state.py`

**Field.** `FIELDS` gains `mode`. A state without `mode` reads as `auto`.

**`start` gains a supervised form:**

```text
handoff-state.py start <slug> --max <n> <field>=<value> ...    auto, as today
handoff-state.py start <slug> --supervised <field>=<value> ...  supervised
```

Both forms write `mode`. Both run under `handoff-lock.py main`, so two starts at once cannot take
the same slot.

| State of `<slug>` before the call | Auto `start` | Supervised `start` |
| --- | --- | --- |
| none, or `finished` | writes a fresh state, prints the slot (as today) | writes a fresh state, prints the slot |
| live, `auto` | exit 1: `refused: a run for <slug> exists; use resume` (as today) | exit 1: `refused: an auto run for <slug> exists` |
| live, `supervised` | exit 1: `refused: a supervised run for <slug> exists` | writes the given fields, keeps `slot` and the other fields, prints the slot |

A fresh state also gets `merge_retries=0`, as today. The last cell lets each later supervised
stage call `start` again and get the same slot.

**Slot pool.** `start_run` picks the lowest whole number from 1 that no live state uses, of either
mode. A state that is not valid JSON has no known slot, as today.

**Counting.**

| Rule | Counts |
| --- | --- |
| The cap in `start --max` | live auto runs; an unreadable state counts as auto |
| Rule 5 of `pull` (the cap) | live auto runs; an unreadable state counts as auto |
| Rule 4 of `pull` (exclusive rows) | every live run |
| Rule 6 of `pull` (the slug's own run is live) | every live run |
| Rules 2 and 3 of `pull` (`after`) | the blocker's state, of either mode |

The refusal line of the cap keeps its words, `refused: <k> auto runs are live (<slugs>); the most
is <n>`, and lists only auto runs.

**`live`** prints a sixth column, `mode`, after `branch`. An unreadable state prints it empty.

**Docstring.** It documents `mode`, the supervised form of `start`, its refusals, and the
counting table above.

### 2. The supervised path in the handoff `SKILL.md`

**The code stage writes the state.** After its start checks pass, a supervised code stage runs:

```bash
handoff-lock.py main -- handoff-state.py start <slug> --supervised \
  spec=<design doc> task_doc=<task doc> next=code
```

The supervised review stage runs the same command with `next=review`, and gets the same slot. The
session that does the work writes the state, so this also holds when Launch falls back to printing
a command for the user. A refusal or a lock timeout is a failed start check:
`<name>: start check failed: <the script's message>`, and nothing is written. After the code stage
creates the worktree, it runs `handoff-state.py set <slug> branch=<branch> worktree=<worktree path>`,
as auto runs do. The plan stage writes nothing, as today.

**How a supervised run ends.**

- Review stage, step 8: after the `done` marks, `handoff-state.py set <slug> next=finished`.
- Code stage, step 4: when the plan ends this work before the branch is done, as in a batch,
  first stop every server the stage started under **Isolation** (D16). The run stays live
  (D18). After the merge, the batch's review stage sets `next=finished` on its own state and on
  every live state of the batch's other plans. The next plan of the batch is a new run with its
  own slug. Auto runs keep today's step 4.
- Code stage, step 5: `handoff-state.py set <slug> next=review` before "Launch", in both modes
  (D17), so the state names the review stage also when Launch falls back to printing a command.
- A dropped run: "To end an abandoned run" applies to both modes.

After `next=finished`, the session runs `handoff-state.py queue show`. When its first line is
`ready`, it prints `rows wait in the queue; run /my:handoff auto rows`.

**`resume`.** After step 2 of "Resume", when `mode` is `supervised`, print one line and stop
(D17). When `next` is `code` and `branch` is set, a new code stage would fail its start checks,
so the line is
`<name>: the run for <slug> is supervised; finish its tasks in <worktree>, then run /my:handoff review <doc>, or end the run`.
Otherwise it is `<name>: the run for <slug> is supervised; run /my:handoff <stage> <doc>`.

**Stops** in a supervised run stay as today: the session waits in its window, and writes no
`stopped`.

**Text edits.**

- Lines 184 and 185: `<slot>` keeps "the `slot` field that `handoff-state.py get <slug>`
  prints". The sentence "A supervised run has no state file and uses slot `1`." goes.
- Line 170: without the section, three parts apply. The third is the supervised `start` under
  `handoff-lock.py main`.
- Lines 673 and 674, start check 5 of the auto launch (D13): when the live state's `mode` is
  `supervised`, the reason is `a supervised run for <slug> exists; finish or end it first`.
  Otherwise it stays `a run for <slug> exists; use resume`.
- Line 512, the fold condition of `auto rows` step 4: unchanged. "`handoff-state.py live` prints
  nothing" now also waits for supervised runs (D14).
- Line 487, the skip table of `auto rows` step 3: "a live auto run" becomes "a live run".
- Line 496, `after`: "live auto runs" becomes "live runs".
- Line 393: "`handoff-state.py live` lists the runs that count" becomes "lists the live runs of
  both modes; only auto runs count toward the cap".
- Line 399: "the ended run freed its slot" becomes "the ended run may let waiting rows start".
- Line 559, "the runs refill their own slots", and line 563, "a run that finishes frees its
  slot": "place under the cap".
- Line 582, "The new run keeps its slot": unchanged, both meanings hold there.

### 3. What reads the runs

**`status-scan.py`.** The `runs` block gains a sixth field, `mode`: slug, slot, `next`, stop line,
branch, mode. The fallback path, which reads the files itself when `live` exits 2, reads `mode`,
with `auto` when it is missing. The module docstring and `run_facts` say "runs", not "auto
runs".

**`my:status` `SKILL.md`.**

- The `runs` row of the facts table names `mode`.
- Every count against the cap counts only `auto` runs: the "first can start now" line, the
  "rows wait for a free slot" line, the parallel rule "stay within **Max runs**", and "allow one
  auto run".
- "Rows wait for a free slot" becomes "rows wait for a free place under the cap".
- A supervised run shows as one in-progress line, such as "supervised run `<slug>`, at code,
  branch `fix/x`".
- A live supervised run needs the user when the queue waits on it (D15): the `queue` block's first
  line is `waits`, and its reason is that run's slug, or `live runs` while that run is live and
  no live auto run is (D19). The
  line is "Needs you: the queue waits for supervised run `<slug>`; finish it or end it with the
  steps in "To end an abandoned run"".
- "What is next" offers `auto resume` only for auto runs.

**Handoff `README.md`,** line 311: supervised runs keep a state file too, with `mode`. Line 364:
"**Max runs** is the most runs live at once" becomes "the most auto runs live at once". Lines 367
and 368 (D12): "`<slot>` is the run's place, 1 to **Max runs**" becomes "`<slot>` is the run's
number, from 1 up. Supervised runs take numbers too, so leave room above **Max runs** for them".

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `cd plugins/kit && python3 -m unittest discover tests`, `cd plugins/my && python3 -m unittest discover tests`

## Files

| File | Change |
|---|---|
| `plugins/my/bin/handoff-state.py` | `mode`, `start --supervised`, the slot pool, the counting table, the `live` column, the docstring |
| `plugins/my/tests/test_handoff_state.py` | New tests below; the exact `live` lines at 346 and 357 gain the sixth column |
| `plugins/my/bin/status-scan.py` | `runs` block's `mode` field; fallback; docstrings |
| `plugins/my/tests/test_status_scan.py` | Two new `RunsTest` tests |
| `plugins/my/skills/handoff/SKILL.md` | Design section 2 |
| `plugins/my/skills/handoff/README.md` | Lines 311, 364, 367 and 368 |
| `plugins/my/skills/status/SKILL.md` | Design section 3 |

The Reference Sweep on 2026-10-22: `LSP` `findReferences` on `start_run` (called by `start` and
`pull`) and `live_states` (called by `print_live`, `start_run`, `walk` and `pull`), and
`git grep` for `my-handoff/`, `handoff-state.py` and `"live"` under `plugins/`. Outside the
script, `live` is run by `status-scan.py` and read in the handoff `SKILL.md` at line 393 (what
counts) and line 512 (the fold condition of `auto rows` step 4). The push guard, `block-autorun-push.py`, reads only
`MY_AUTORUN` and does not change. The plan runs the sweep again and owns the final list.

## Trade-offs

- **Slot belongs to the run (chosen).** Pros: one rule; no dependence on worktrees; removes the
  root cause. Cons: a dropped supervised run holds its slot until the user ends it; supervised
  sessions now write state.
- **Slot lives as long as the worktree.** Pros: removing the worktree frees the slot, with no end
  step. Cons: a preview can outlive its worktree; work without a worktree gets no slot; the slot
  depends on a git detail. Rejected on 2026-10-22.
- **Auto runs unchanged; supervised records beside them.** Pros: the auto path does not move.
  Cons: two rules in one pool, and "slot" keeps its two meanings.
- **Slot from the worktree's place in `git worktree list`.** Rejected: removing an earlier
  worktree shifts every later slot, so a running preview would change port.

## Dependencies

- No new package. `handoff-lock.py` and `handoff-state.py` are already on `PATH` in every
  project that has the `my` plugin.
- Row 68 "Methods as plugins" edits the same `SKILL.md`, but only its four launch lines, which this
  spec does not touch. The order of work puts row 56 first.

## Risk

- **Stored state changes shape:** a `mode` field and new supervised files in
  `<git common dir>/my-handoff/`. To undo, delete the supervised files and revert. If the plugin
  is rolled back while supervised files exist, the old script counts them toward the cap. `live`
  shows them, and ending those runs fixes it.
- **Two outputs change:** `live` and the `runs` block gain a sixth column. Their readers,
  `status-scan.py`, `my:status` and `my:handoff` (lines 393 and 512), are handled here.
- **Runs started before the change.** A supervised run whose code stage ran before the change has
  no state. Its review stage writes one, and may get a slot other than `1`, so its ports can differ
  from the code stage. This repo had no worktrees on 2026-10-22; other projects may.
- **A dropped supervised run stays live** in `my:status` until the user ends it. The user chose
  this. While it is live it holds its slot, blocks exclusive queued rows and `after` gates, and
  blocks the fold of `auto rows` step 4 in a project without the section (D14). `my:status`
  names it as needing the user when the queue waits on it (D15).
- **Slots above Max runs** (D12). A project whose Isolation reserves exactly **Max runs** ports
  can get a slot outside them. The README tells projects to leave room.
- **Batch servers** (D16). Code stage step 4 must stop the servers it started. A server the
  stage did not start, such as one the user started by hand, is not stopped, and can still hold
  a freed slot's port.
- **A supervised stage can wait** up to 90 seconds for the `main` lock while an auto run merges. A
  timeout is a failed start check; the user reruns the stage.
- **Judgement steps are not tested by a command:** `resume` refusing a supervised run, start
  check 5's supervised case, code stage step 4 stopping servers and finishing a batch run, and
  `my:status` naming a supervised run that the queue waits on. The end-of-branch review reads the `SKILL.md` diff for them.
- **No effect without the section.** Until a project has a "Parallel runs" section, its runs use
  no slot. Row 56's `done` mark says so.

## Testing strategy

The tests run the real `handoff-state.py` and `status-scan.py` as commands in a fixture repo, so
they cover the public surface from end to end. Each test fails first for the reason it names,
except the three guard tests, which get a deliberate break.

`plugins/my/tests/test_handoff_state.py`:

| Class | Test | Asserts |
| --- | --- | --- |
| `StartTest` | `test_supervised_start_takes_the_lowest_slot_no_live_run_uses` | auto `a` in slot 1 is live, so supervised `b` gets `2` |
| `StartTest` | `test_auto_start_skips_a_supervised_slot` | supervised `a` in slot 1, so auto `b` gets `2` |
| `StartTest` | `test_supervised_run_does_not_count_toward_the_cap` | with `--max 1` and one live supervised run, an auto start exits 0 |
| `StartTest` | `test_supervised_start_again_keeps_the_slot_and_writes_the_fields` | a second call with `next=review` prints the same slot, sets `next`, keeps `branch` |
| `StartTest` | `test_supervised_start_refuses_beside_a_live_auto_run_of_its_slug` | exit 1, `refused: an auto run for a exists`, file unchanged |
| `StartTest` | `test_auto_start_refuses_beside_a_live_supervised_run_of_its_slug` | exit 1, `refused: a supervised run for a exists`, file unchanged |
| `StartTest` | `test_finished_supervised_run_frees_its_slot` | after `next=finished`, the next start gets `1` |
| `StartTest` | `test_state_without_mode_counts_as_auto` | guard: an old file counts toward the cap |
| `StartTest` | `test_concurrent_locked_supervised_starts_never_share_a_slot` | as `test_concurrent_locked_starts_never_pass_the_cap` |
| `LiveTest` | `test_live_prints_mode_last` | the sixth column is `auto` or `supervised` |
| `PullTest` | `test_rule4_exclusive_entry_waits_for_a_live_supervised_run` | guard: the walk stops with `live runs` |
| `PullTest` | `test_rule5_cap_ignores_supervised_runs` | a waiting row starts beside a supervised run at `--max 1` |
| `PullTest` | `test_rule3_after_waits_for_a_live_supervised_run` | guard: the row waits until that run is `finished` |

`plugins/my/tests/test_status_scan.py`, `RunsTest`: `test_runs_block_shows_mode`, and
`test_runs_fallback_reads_mode_with_auto_by_default`.

**The three guard tests** pass before the change, because today every state counts. Each gets a
deliberate break that must turn it red: treat a missing `mode` as `supervised`; make rule 4 count
only auto runs; make rule 3 ignore supervised states.

**Rehearsal.** The skill text has no unit tests. The plan rehearses its commands in a fixture
repo: two supervised code-stage starts get slots 1 and 2; an auto start gets 3; the review-stage
`start` of the first supervised run prints 1 again; `set next=finished` frees it; `queue show`
runs; `status-scan.py` lists all live runs with their mode.

## Open questions

- **Projects without a "Parallel runs" section** still get no per-run values. Row 39
  "`kit:setup` offers a Parallel runs section" is the closest row; it waits for row 29. This spec
  does not decide whether that gap gets its own row.
