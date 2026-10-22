# Code re-review: supervised runs take slots

**Status:** review of docs/plans/2026-10-22-supervised-run-slots.md, 2026-10-22. Re-review after the fix round: /code-review high on main..fix/supervised-run-slots.

## Scope

The review read the range `main..fix/supervised-run-slots`, compared with the
local `main`, not `origin/main`. The range has eight commits. It focused on
the fix round: the commit about supervised runs that resume into the review
and batch plans that wait for the merge, and the commit that adds decisions
D17 to D19 and the review reports. It also read the rest of the range. It had
the spec, the plan, the map of changed symbols and their callers, and the
earlier review `docs/plans/2026-10-22-supervised-run-slots-code-review.md`.

`test_handoff_state` and `test_status_scan` pass (136 tests); the background
review reports all 292 tests in `plugins/my/tests` pass. Line numbers refer
to the branch head.

The plan's **Risk** section holds known limits, and a known limit is not a
finding. The fix round moved earlier findings 4, 5 and 7 into **Risk**, so
they are not repeated here. Earlier findings 1, 2, 3 and 8 are fixed by
D17 to D19.

## Findings

### 1. Ending an earlier plan of a batch removes the batch's shared worktree

- **Severity:** Warning. **New in the fix round.**
- **File:** `plugins/my/skills/handoff/SKILL.md`, line 409
- **Defect:** D18 now leaves an earlier batch plan's supervised run live, and
  "To end an abandoned run" removes the worktree that the run's state names,
  which in a batch is the worktree all plans of the batch share.
- **Failure scenario:** Batch plans A and B share
  `.claude/worktrees/batch`. A's code stage ends at step 4 and stays live at
  `next=code` with that worktree in its state. An exclusive row waits on
  `live runs`. `my:status` says "Needs you: the queue waits for supervised
  run A; finish it or end it" (status `SKILL.md` line 105), and `auto resume`
  for A also says "or end the run" (line 372). The user ends A. The worktree
  is clean, so `git worktree remove` needs no `--force` and removes B's
  worktree while B's code stage is still to run or running. A also gets
  `stopped="ended by the user"`, so every row queued `after=[A]` is skipped
  although A's code will merge with the batch. In the other direction, if
  the user ends the batch's last run instead, nothing ever finishes A, which
  stays live and holds its slot and the exclusive rows.

### 2. Code stage step 4 promises a batch finish that auto mode never runs

- **Severity:** Warning. **Partly new:** the gap is older than the branch;
  the fix round's text now claims the finish.
- **File:** `plugins/my/skills/handoff/SKILL.md`, line 906 (and auto
  sub-step 4 at line 1142)
- **Defect:** Step 4 says "The run stays live: the batch's review stage
  finishes it after the merge (Review stage, step 8, sub-step 4)", but in
  auto mode step 8 is replaced by sub-steps whose sub-step 4 sets
  `next=finished` only on its own slug.
- **Failure scenario:** An auto batch of plans A and B. A's code stage ends
  at step 4 with `next=code`. B's review merges, and auto sub-step 4 runs
  `set B next=finished stopped=`. Nothing finishes A. A is an auto run, so
  `is_auto` counts it toward **Max runs** forever, and an exclusive row
  waits on `live runs` with no end. The user must end A, which writes
  `stopped`, and rows gated `after` A are skipped as failed. On `main` an
  auto batch's earlier run was also never finished, but no text said it
  would be. The sentence sits after "Without `auto`, first stop every
  server", so a reader cannot tell whether it covers auto mode.

### 3. `resume` tells an earlier batch plan to "finish its tasks"

- **Severity:** Suggestion. **New in the fix round.**
- **File:** `plugins/my/skills/handoff/SKILL.md`, line 372
- **Defect:** For a supervised run at `next=code` with a branch, the line
  says "finish its tasks in `<worktree>`, then run /my:handoff review
  `<doc>`", but an earlier batch plan left live by D18 has finished its
  tasks; only the batch's later plans and the merge remain.
- **Failure scenario:** Batch of plans A and B. The user runs `auto resume`
  on A's spec while B is not yet coded. The line tells them to finish A's
  tasks and run the review with the batch's last plan. Running that review
  now reviews and squash-merges a batch whose plan B has no commits.

### 4. A supervised review that stops after the merge has no way to finish cleanly

- **Severity:** Warning. Not new in the fix round.
- **File:** `plugins/my/skills/handoff/SKILL.md`, line 1060 (and line 412)
- **Defect:** The supervised review stage writes no state between the
  squash-merge and `next=finished`, so a stop after the merge leaves the run
  at `next=review`, and the only way out, ending the run, writes `stopped`.
- **Failure scenario:** A supervised review squash-merges and removes the
  worktree, then stops at sub-step 3 ("merged; fixups wait for a clean
  base") and the window is closed, or the session crashes. `auto resume`
  prints "run /my:handoff review `<doc>`". That review fails its start
  check, because the worktree is gone. The user ends the run, which writes
  `stopped="ended by the user"`, and `walk` skips every row queued
  `after=[slug]` with "blocker `<slug>` did not finish", although its code
  is on `main`. Auto runs avoid this with `next=merge` to `next=done`. This
  case is not in **Risk**.

### 5. Three places still say step 4 finishes a batch run

- **Severity:** Suggestion. **New in the fix round.**
- **File:** `docs/plans/2026-10-22-supervised-run-slots-spec.md`, lines 83
  and 291; `docs/plans/2026-10-22-supervised-run-slots.md`, line 834
- **Defect:** D16 ("stops the servers ... before it finishes a supervised
  run"), the spec's Risk bullet and the plan's Risk bullet ("code stage step
  4 stopping servers and finishing a batch run") contradict D18, which keeps
  the run live.
- **Failure scenario:** A reader of the spec or plan, or a later review,
  takes D16 as current and expects the slot to be freed at step 4. D16's
  reason, "another run takes the slot", no longer holds, since the slot
  stays held until the merge.

### 6. The queue line after a supervised finish ignores the cap

- **Severity:** Suggestion. Not new in the fix round.
- **File:** `plugins/my/skills/handoff/SKILL.md`, line 1064
- **Defect:** The line prints "rows wait in the queue; run /my:handoff auto
  rows" whenever `queue show` says `ready`, while `my:status` prints the
  same hint only when live auto runs are fewer than the cap (status
  `SKILL.md` line 110).
- **Failure scenario:** **Max runs** is 1 and one auto run is live. A
  supervised run finishes and `queue show` prints `ready`. The session tells
  the user to run `/my:handoff auto rows`, and `pull --max 1` starts
  nothing.

### 7. A supervised start does not wait for a started exclusive row

- **Severity:** Suggestion. Not new in the fix round, and not a regression.
- **File:** `plugins/my/bin/handoff-state.py`, line 300
- **Defect:** `start_run(slug, "supervised", ...)` checks only the slug's
  own run, so a supervised run starts beside a started exclusive auto row;
  D6 holds only in the other direction.
- **Failure scenario:** `auto rows` starts exclusive row X, whose file list
  is unknown. The user runs `/my:handoff code <plan>` for another slug, and
  `start --supervised` succeeds. The two runs may edit the same files.
  Before the branch a supervised run could start there too, so this is a gap
  the spec does not cover, not a new break.

### 8. The spec and the skill disagree on when `resume` checks the mode

- **Severity:** Suggestion. Not new in the fix round (the fix round rewrote
  the paragraph and kept the wording).
- **File:** `docs/plans/2026-10-22-supervised-run-slots-spec.md`, line 165;
  `plugins/my/skills/handoff/SKILL.md`, line 367
- **Defect:** The spec says "After step 2 of Resume", while the skill runs
  the supervised check as step 1, on purpose before `check`.
- **Failure scenario:** A supervised state mid-merge gets the "run
  /my:handoff `<stage>`" line from the skill, while a reader of the spec
  expects the `check` mismatch. The skill's order is the better one; the
  spec should say so.

### 9. Cleanup: repeated reads and defaults (earlier finding 9, partly fixed)

- **Severity:** Suggestion. Carried over.
- **File:** `plugins/my/bin/handoff-state.py`, line 825
- **Defect:** The fix round merged `start_run`'s two `mode == "auto"`
  branches, but `pull` still reads the state folder three times per queue
  entry (`walk`, `ready`, `start_run`), and "a missing mode means auto" is
  still written in `is_auto`, `print_live` and `status-scan.py` `run_facts`.
- **Failure scenario:** No runtime failure. Extra directory reads under lock
  `main`, and three copies of a default that must change together.

### 10. One commit subject has no scope (earlier finding 10)

- **Severity:** Suggestion. Carried over.
- **File:** the subject of the commit "fix: my:status lists supervised runs
  and what waits on them"
- **Defect:** The subject has no scope, while the project lists scopes and
  the other commits use `fix(my-plugin):`.
- **Failure scenario:** If the subject is reused in the squash commit, it
  breaks the `type(scope): sentence` rule.

## Considered and not reported

- A row gated behind a row in its supervised plan stage is still skipped
  with "which nothing will start", because the plan stage writes no state.
  That is spec decision D8, and the outcome is the same as before the
  branch.
- A supervised re-take of a live state with no `slot` prints an empty slot,
  and a rerun code stage can move `next` from `review` back to `code`. No
  caller writes a supervised state without `start`, and the rerun is the
  user's own choice: input today's code never produces.
