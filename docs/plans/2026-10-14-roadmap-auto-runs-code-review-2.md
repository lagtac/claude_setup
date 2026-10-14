# Code review (high), re-review: roadmap-auto-runs

**Status:** review of `feat/roadmap-auto-runs`, 2026-10-14.
Final re-review after the fix round. Answered by the plan's Risk section:
no finding is Critical, so each is a known limit.

**Scope:** the committed range `main..feat/roadmap-auto-runs` (local `main`,
not `origin/main`), read up to the branch head. The review read the whole
range and paid special attention to the fix round: the `fix(my-plugin)` code
commit and the `docs(plans)` commit that closes the branch. Inputs: spec
`docs/plans/2026-10-13-roadmap-auto-runs-spec.md`, plan
`docs/plans/2026-10-13-roadmap-auto-runs.md` and its **Risk** section, the
first round's report `docs/plans/2026-10-14-roadmap-auto-runs-code-review.md`,
and the map of changed symbols and callers. All 203 tests in
`plugins/my/tests` and all 28 in `plugins/kit/tests` pass on the branch head.

Severity labels: **Critical** = data loss or a broken main path; **Normal** =
wrong behaviour a user can hit; **Low** = rare input, a narrow window, or
misleading output; **Cleanup** = no wrong behaviour today, but duplicated logic
or extra cost.

**Verdict on the fix round:** it is correct and broke nothing. `in_loop`
labels a row that only waits behind a loop as `behind a gate cycle`, and the
new test proves it. `not_fresh` matches spec D5 rule 6 as amended: it anchors
the plan name with `re.escape`, and the test shows that a longer slug
(`x-a`) does not block `a`. Caching `common_dir` is safe, because the
script never changes its directory and a failed `git` call raises, so it is
not cached. Keeping the blocker states from rule 2 for rule 3 gives the same
result as before. Finding 1 below is the only gap in the fix itself.

No finding is Critical, so none needs the user before the merge. By the
"one fix round" rule, the Low and Cleanup findings go into the plan's
**Risk** section.

## Left out: known limits

These are in the plan's **Risk** section, so they are not findings here:
`queue show` does not apply rule 6; `my:status` is silent about stale waiting
rows; a failed queue write in `pull`; a tab in `row`; the `queue` block reads
the queue twice; a row the user starts by hand after the call; a run started
by hand is not seen as exclusive; head-of-line blocking by rules 3 and 4.

## Findings in the fix round

### 1. `pull`'s new drop misses a hand rerun made before any `pull` (Low)

**File:** `plugins/my/bin/handoff-state.py:769`

**Summary:** `pull` drops a `started` entry only while its run's state says
`next=finished`. When the user reruns the slug by hand before any `pull`
runs, the state is live again and the old exclusive entry stays. So first
round finding 2 is fixed only when a `pull` runs between the finish and the
hand rerun.

**Failure scenario:** reproduced in a test repo. Exclusive row `a` is pulled
and finishes, and no `pull` runs after that. The user reruns `a` by hand, then
queues `b`. `queue show` prints `waits b exclusive a`, and `pull --max 2`
starts nothing. In the normal flow the refill `pull` runs right after
`next=finished` (handoff `SKILL.md`, "Refill"), so this happens only when that
refill fails, for example on a lock timeout, or when a run is marked finished
without the refill. Then the queue holds every row until the hand run ends.

### 2. `pull` copies `prune`'s rule for finished `started` entries (Cleanup)

**File:** `plugins/my/bin/handoff-state.py:769`

**Summary:** the new list comprehension in `pull` repeats the first half of
`prune` (line 611) instead of calling shared code, although the docstring says
`pull` does it "as `queue add` does".

**Failure scenario:** a later change to the "finished" test, for example for
an unreadable state file, must be made in both places. If only one changes,
`queue add` and `pull` disagree about which `started` entries still count, and
rule 4 sees a different exclusive run in each.

## Findings in the rest of the branch

### 3. `queue add` re-adds a slug whose entry is `started` (Low)

**File:** `plugins/my/bin/handoff-state.py:646`

**Summary:** the duplicate check counts only `waiting` entries. A slug whose
entry is `started` and whose run is live is added again as a new `waiting`
entry.

**Failure scenario:** reproduced by the reviewer. Queue `x`, then `y` after
`x`; `pull --max 2` starts `x`. Re-adding `x` prints `added x`. The next
`pull` skips the new `x` as `a run for x exists` and, in the same walk, skips
`y` as `blocker x did not finish`. When `x` then finishes cleanly, `y` stays
skipped and never runs. The judge step of `auto rows` refuses a row whose run
exists, so the path needs a race: a refill in another session starts `x`
between the judge step and `queue add`.

### 4. Rule 2 lets a stale `skipped` entry win over the blocker's real run (Low)

**File:** `plugins/my/bin/handoff-state.py:716`

**Summary:** rule 2 fails a blocker when any entry for its slug is `skipped`,
even when the same slug also has a live `started` entry or a state that
finished cleanly.

**Failure scenario:** the state from finding 3: `x` has a live `started` entry
and a `skipped` duplicate. Every waiting row after `x` is skipped as
`blocker x did not finish` at once, before `x` ends. Fixing finding 3 removes
the only known way into this state.

### 5. `auto rows drop` calls `queue drop` with no slug (Low)

**File:** `plugins/my/skills/handoff/SKILL.md:444`

**Summary:** the drop step runs `queue drop` "with the other slugs" but does
not say to skip the call when no slug is left.

**Failure scenario:** `/my:handoff auto rows drop 99`, where row 99 is not
waiting. The session prints `row 99 is not waiting`, then runs
`handoff-state.py queue drop` with no slug. `queue_command` needs at least one
slug, so it prints the usage block and exits 2. The user sees a usage error
after a call that should have done nothing.

### 6. Without "Parallel runs", the `approved` commit takes no lock (Low)

**File:** `plugins/my/skills/handoff/SKILL.md:507`

**Summary:** without a "Parallel runs" section, step 4 commits on `main` with
plain `git add` and `git commit`, even when `handoff-state.py live` shows a
queued run that may be in its review stage.

**Failure scenario:** Max runs 1, row 9 is live and is between
`git merge --squash` and its commit, or inside `git-fold-fixups.py`, in the
main checkout. The user types `/my:handoff auto rows 12`. Step 4's
`git add` and `git commit` run at the same moment and can hit `index.lock` or
commit into a rebase that is still running. Any supervised session of the
user carries the same risk today, so this is not new in kind, but the queue
makes overlap with a live run more likely.

### 7. A hand-started auto run ignores a live exclusive queued run (Low)

**File:** `plugins/my/bin/handoff-state.py:274`

**Summary:** only `walk` rule 4 enforces `exclusive`. `start_run`, which the
hand `start` also uses, does not check for a live exclusive queued run.

**Failure scenario:** in a project with "Parallel runs" and Max runs 2, the
queue starts a row with no file list (`exclusive=true`). The user then types
`/my:handoff auto plan <other spec>`. `start --max 2` passes the cap check and
starts a second run beside the row that was meant to run alone. The spec's
known limit covers the opposite direction only (a hand run that `pull` cannot
see as exclusive). The same mitigation applies: the parallel merge rebases and
reruns the checks. At Max runs 1 it cannot happen.

### 8. The handoff README promises more starts than the walk makes (Low)

**File:** `plugins/my/skills/handoff/README.md:402`

**Summary:** the README says the call "starts as many as **Max runs** allows"
and that a gated row waits "whatever order you typed". Rule 3 stops the walk
at the first row that is not ready, so free slots can stay empty, depending on
the typed order.

**Failure scenario:** reproduced by the reviewer. Rows `x`, `y` (after `x`)
and `z` (no gate), typed in that order, with `pull --max 2`: only `x` starts,
and `z` waits behind `y` while a slot is free. Typed as `z`, `x`, `y`, both
`z` and `x` start. The spec chose this on purpose (Trade-offs), so the code is
right and the README is not. It should say that a waiting row holds the rows
behind it.

### 9. `pull` scans the state folder several times per entry under lock `main` (Cleanup)

**File:** `plugins/my/bin/handoff-state.py:729`

**Summary:** each walked entry lists and parses the state folder up to three
times (rule 4 at line 729, `ready` at line 776, and `start_run`). Rule 1
starts one `git hash-object` process per waiting entry, in every `pull` and
every `queue show`.

**Failure scenario:** with k waiting entries, one `pull` makes about 3k
passes over `my-handoff/` and k `git` processes, all while it holds lock
`main`. Every commit on `main` in a parallel project waits on that lock.
Better: read the live list once per `pull` and update it after each start,
and hash all specs in one `git hash-object` call.

### 10. `queue_facts` starts `queue show` even when there is no queue (Cleanup)

**File:** `plugins/my/bin/status-scan.py:219`

**Summary:** `queue_facts` always starts a Python process for
`handoff-state.py queue show`, with its `git` calls, even when no queue file
exists. It also builds the queue path itself (line 227).

**Failure scenario:** every `my:status` scan in a project that never used the
queue pays for an extra interpreter start and the `git` calls of `Repo()`,
only to print `none`. Better: check that the file exists before starting the
process. The duplicated path is part of a known limit; the extra process is
not.

### 11. A failed write in `queue add` or `queue drop` ends in a traceback (Low)

**File:** `plugins/my/bin/handoff-state.py:836`

**Summary:** `queue_command` catches only `QueueError` and `GitError`. An
`OSError` from `write_json` escapes as a Python traceback.

**Failure scenario:** the disk is full or the queue folder is read-only.
`handoff-lock.py main -- handoff-state.py queue add --file <path>` prints a
traceback and exits 1. Step 5 of `auto rows` then shows the user the
traceback instead of a one-line message. Nothing is queued, because
`write_json` writes atomically. The plan's **Risk** section covers a failed
write in `pull`, not in `queue add` or `queue drop`.
