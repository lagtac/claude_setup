# Code review (high): roadmap-auto-runs

**Status:** review of `feat/roadmap-auto-runs`, 2026-10-14. Answered by the
fix round: findings 1, 2 and 7 fixed in code, finding 8 in part (the blocker
states are read once; the cap check stays, with a comment on why), 3 to 6
recorded in the plan's Risk as known limits (4 by the user's choice).

**Scope:** the committed range `main..feat/roadmap-auto-runs` (local `main`, not
`origin/main`), read up to the branch head. Eleven files:
`plugins/my/bin/handoff-state.py`, `plugins/my/bin/status-scan.py`, the
`my:handoff` and `my:status` skill files, the handoff README, `README.md`,
`ROADMAP.md`, the plan, and three test files. Inputs: spec
`docs/plans/2026-10-13-roadmap-auto-runs-spec.md`, plan
`docs/plans/2026-10-13-roadmap-auto-runs.md` and its **Risk** section, and the
map of changed symbols and callers. All 199 tests in `plugins/my/tests` pass on
the branch, and no test assertion was removed or weakened. The reviewer
reproduced findings 1 and 2 in throwaway repos.

Severity labels: **normal** = wrong behaviour a user can hit; **low** = rare
input or misleading output; **cleanup** = no wrong behaviour today, but
duplicated logic or extra cost.

## Left out: known limits

- **A queued row that the user starts by hand.** `pull` marks it `skipped: a run
  for <slug> exists`, and rule 2 then skips the rows behind it
  (`handoff-state.py:741`). The plan's **Risk** section names this exact case as
  a known limit, so it is not a finding here. Finding 4 is a separate symptom of
  the same case, in `queue show`.
- **Head-of-line blocking by rules 3 and 4** (one waiting row stops the walk).
  The spec chose this as a trade-off.

## 1. Gate-cycle check drops entries that are not in a loop (normal)

**File:** `plugins/my/bin/handoff-state.py:633`

**Summary:** `queue add` treats every new entry that `blockers_first` cannot
place as part of a loop. A new entry that only waits for a loop member is also
dropped and reported as `gate cycle`.

**Failure scenario:** `w` is waiting with `after=[x]`. A new file adds `x`
(after `w`) and `c` (after `x`). Only `w` and `x` form a loop, but `queue add`
prints `skipped: x: gate cycle` and `skipped: c: gate cycle` (reproduced). The
user is told that row `c` is in a loop when it is not, and `c` is never queued.

## 2. An old exclusive entry blocks the queue during a hand rerun (normal)

**File:** `plugins/my/bin/handoff-state.py:704`

**Summary:** rule 4 treats any `started` exclusive entry whose slug is live as a
live exclusive run. `pull` never prunes, and `queue add` prunes only finished
runs. So an old exclusive entry blocks the queue when the same slug is later run
again by hand as a normal run.

**Failure scenario:** exclusive row `e` is pulled and finishes. The user then
reruns `e` by hand (`start e`), which is not exclusive. Later `f` is queued.
`queue add` keeps `e`'s old `started` entry, because `e` is live again. `pull`
starts nothing, and `queue show` prints `waits f exclusive e` (reproduced). The
queue holds every row until the manual rerun ends. This is the opposite
direction of the spec's known limit "a run started by hand is not seen as
exclusive", so that limit does not cover it.

## 3. A failed queue write leaves live runs with no window (low)

**File:** `plugins/my/bin/handoff-state.py:752`

**Summary:** `pull` writes each new state file through `start_run` during the
walk, but writes the queue file and prints the `started` lines only at the end.

**Failure scenario:** `write_json(queue_path())` raises an `OSError`, for
example on a full disk. Each started run has a state file and a cap slot, but
its line is never printed, so the refill or step 7 launches no window. The
entries stay `waiting`. The next `pull` skips them as `a run for <slug> exists`,
rule 2 then skips the rows behind them, and the orphan runs keep their cap
slots. The spec's "a run with no window" limit covers a crash between `pull` and
Launch, where the entries are already `started`. Here they stay `waiting`, so
the later skip cascade is new.

## 4. `queue show` says `ready` for a row that `pull` would skip (low)

**File:** `plugins/my/bin/handoff-state.py:759`

**Summary:** `queue show` does not apply rule 6 (a run for the slug exists). It
prints `ready <slug>` for an entry that `pull` would skip.

**Failure scenario:** the first waiting entry's slug has a live run that the
user started by hand. `queue show` prints `ready x`, and `my:status` says the
first row can start now: run `/my:handoff auto rows`. The user runs it, and
`pull` only skips `x`, then skips the rows behind it (the known limit above).
The status report sends the user into the known limit instead of warning about
it.

## 5. The `row` field accepts tabs and newlines (low)

**File:** `plugins/my/bin/handoff-state.py:553`

**Summary:** `entry_problem` checks `row` only as a non-empty string. The skill
defines row numbers as `\d+[a-z]?`, but the script does not enforce it.

**Failure scenario:** a queue file holds the row `"9\t"`, with a stray tab
picked up while copying row numbers. `status-scan.py` prints the tab-separated
`queue` block with an extra field. Then `auto rows drop 9` cannot map the row to
its slug, and `my:status` shows the wrong columns.

## 6. `status-scan.py` reads the queue file a second time, on its own (cleanup)

**File:** `plugins/my/bin/status-scan.py:231`

**Summary:** `queue_facts` builds the queue path itself and reads `rows.json`
directly, apart from the `queue show` call. This copies `queue_path` and
`read_queue`, skips their checks of each entry, and reads the file twice.

**Failure scenario:** a `pull` or refill rewrites `rows.json` between the `queue
show` call and the direct `json.load`. The `ready` or `waits` line then
describes a different queue than the rows printed under it. Also, any change to
the queue's place or format must now be made in two scripts. Better:
`handoff-state.py` prints the entry rows, for example from `queue show`, and
`status-scan.py` only parses them.

## 7. Many `git` calls while lock `main` is held (cleanup)

**File:** `plugins/my/bin/handoff-state.py:167`

**Summary:** every `run_state`, `live_states` and `spec_hash` call starts its
own `git` process through `common_dir()`. `walk` calls `live_states` once per
entry and `run_state` twice per blocker, and `ready()` and `start_run` call
`live_states` again, all under lock `main`.

**Failure scenario:** for a queue of N entries with blockers, one `pull` starts
dozens of `git rev-parse --git-common-dir` processes under lock `main`. The lock
is held longer, so a refill or merge that runs at the same time is more likely
to time out with exit 75. Better: compute `common_dir` once per process, and
call `live_states` once per walk step.

## 8. The cap check and the blocker reads are done twice (cleanup)

**File:** `plugins/my/bin/handoff-state.py:732`

**Summary:** the cap check in `pull`'s `ready()` repeats the cap check that
`start_run` already makes. Rule 3 (line 697) reads again the blocker states that
rule 2 has just read.

**Failure scenario:** the same decision lives in two places. If one cap check
changes, for example to count only runs the queue started, the other check can
silently override it. The second reads also add file and `git` work under the
lock. Better: rely on `start_run`'s `Refused` with `exists=False` for the cap,
and keep each blocker's state from the rule-2 loop for rule 3.
