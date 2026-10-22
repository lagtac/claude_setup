# Code review: supervised runs take slots

**Status:** review of docs/plans/2026-10-22-supervised-run-slots.md, 2026-10-22. /code-review high on the branch range main..fix/supervised-run-slots.

## Scope

The review read the range `main..fix/supervised-run-slots`, compared with the
local `main`, not `origin/main`. The range has six commits and touches eight
files: `README.md`, `plugins/my/bin/handoff-state.py`,
`plugins/my/bin/status-scan.py`, `plugins/my/skills/handoff/README.md`,
`plugins/my/skills/handoff/SKILL.md`, `plugins/my/skills/status/SKILL.md`,
`plugins/my/tests/test_handoff_state.py` and
`plugins/my/tests/test_status_scan.py`. The review also had the spec, the
plan and the map of changed symbols and their callers.

`test_handoff_state` and `test_status_scan` pass (136 tests). The review did
not check each finding a second time, so a few may be wrong. Line numbers
refer to the branch head.

The plan's **Risk** section holds known limits, and a known limit is not a
finding. The "Note" lines below say where a finding meets the Risk section
or a spec decision.

## Findings

### 1. Resuming a supervised run at `next=code` cannot work

- **File:** `plugins/my/skills/handoff/SKILL.md`, line 367
- **Defect:** For a live supervised run, resume step 1 tells the user to run
  `/my:handoff <next> <task_doc>`. When `next` is `code`, that command always
  fails its start checks.
- **Failure scenario:** A supervised code stage makes
  `.claude/worktrees/<slug>` and a branch `*/<slug>` in step 1, then crashes.
  `/my:handoff auto resume <spec>` prints "the run for <slug> is supervised;
  run /my:handoff code <plan>". The user runs that command. The code stage's
  start checks "no branch */<slug>" and "no directory
  .claude/worktrees/<slug>" fail. "Restarted stages" covers only `run auto`
  sessions, so nothing can restart a supervised code stage. The only way left
  is "end the run". That writes `stopped`, so every queue entry that waits on
  this run fails.

### 2. A batch plan that stops early is marked finished before its merge

- **File:** `plugins/my/skills/handoff/SKILL.md`, line 897
- **Defect:** A supervised batch plan that ends at code stage step 4 writes
  `next=finished` with an empty `stopped`, while its branch is still not
  merged. Queue rule 3 and `my:status` both read that as "done".
- **Failure scenario:** Batch plan A ends at step 4 with `next=finished`. Its
  branch is shared and is merged only after the last plan. Queued row B has
  `after=[A]`. In `handoff-state.py`, `walk()` and `open_blocker` (line 774)
  see A finished with an empty `stopped`, so `pull` starts B on a base that
  does not have A's code. `my:status` also counts A's row as done.
- **Note:** The spec chose to finish a batch plan this way (Design, "Code
  stage, step 4"). The effect on `after` entries and on `my:status` is not in
  the Risk section.

### 3. A supervised run stays at `next=code` until the review session starts

- **File:** `plugins/my/skills/handoff/SKILL.md`, line 943
- **Defect:** Only auto mode sets `next=review` before the code stage starts
  the review. A supervised run's state stays at `next=code` until the review
  session runs its own start.
- **Failure scenario:** The supervised code stage finishes. Launch falls back
  to printing a command, because there is no tmux or the mode is manual. The
  user has not run the command yet. `my:status` shows "supervised run <slug>,
  at code". Resume step 1 says to run the code stage again, which fails as in
  finding 1, instead of the review stage.

### 4. A stopped auto run can no longer be finished by a supervised review

- **File:** `plugins/my/bin/handoff-state.py`, line 313
- **Defect:** A supervised start now refuses when an auto run of the same
  slug is live, even a stopped one. So the user can no longer finish a
  stopped auto run by hand with `/my:handoff review <doc>`.
- **Failure scenario:** An auto run stops at review, for example on a gate
  finding. Before this branch, the user could run `/my:handoff review <plan>`
  supervised to finish it. Now the review stage's supervised start fails its
  start check with "refused: an auto run for <slug> exists". The user must
  either run `auto resume` or end the run. Ending writes a non-empty
  `stopped`, and queue rule 2 then skips every row that waits on this slug
  ("blocker did not finish").
- **Note:** The refusal itself is a spec decision: the spec's `start` table
  gives this exit 1, and a test asserts it. The lost manual path is not in
  the Risk section.

### 5. `start <slug> --supervised` with no fields writes a run with no `next`

- **File:** `plugins/my/bin/handoff-state.py`, line 335
- **Defect:** `start_args` accepts `start <slug> --supervised` with no field
  pairs, so it writes a live state with no `next`.
- **Failure scenario:** `handoff-state.py start a --supervised` exits 0 and
  writes `{mode, slot, merge_retries}`. `live_states()` counts the run as
  live forever, because its `next` is not `finished`. `live` prints an empty
  `next`. Exclusive queue entries wait on it ("live runs"). Resume step 1
  prints "run /my:handoff  <empty doc>".

### 6. The SKILL's Isolation row does not warn that slots can go above Max runs

- **File:** `plugins/my/skills/handoff/SKILL.md`, line 167
- **Defect:** Supervised runs take slots with no upper bound, so slots can go
  above **Max runs**. Only the handoff README warns about this. The SKILL's
  Isolation row and its PORT example do not.
- **Failure scenario:** A project sets `Max runs: 2` and reserves ports
  54311-54312 for `PORT=$((54310 + <slot>))`. One supervised run and two
  auto runs are live, so one run gets slot 3. Its server binds 54313, which
  is outside the reserved range and may clash with another service. A reader
  of the SKILL table still assumes slots 1 to **Max runs**.
- **Note:** Slots above **Max runs** are a known limit (Risk, "Slots above Max
  runs", D12). The spec puts the warning in the handoff README
  (`plugins/my/skills/handoff/README.md` line 369), where it is. What is left
  is only that the SKILL text does not repeat it.

### 7. A supervised finish runs no refill, but ending an abandoned run does

- **File:** `plugins/my/skills/handoff/SKILL.md`, line 1057
- **Defect:** A supervised finish runs no refill, although supervised runs
  now block exclusive entries (rule 4) and `after` entries. "To end an
  abandoned run" does run the refill for the same supervised run.
- **Failure scenario:** An exclusive queue entry waits on "live runs" because
  one supervised run is live. That run finishes normally. The queue only
  prints a hint, and nothing starts until the user types `/my:handoff auto
  rows`. If the user had ended the same run as abandoned, the refill would
  have started the entry at once. Both paths free the same slot but behave
  differently.
- **Note:** "No refill on a supervised finish" is spec decision D9. Its reason
  is that a supervised session may not be able to open auto windows. The
  difference from the abandoned-run path is not discussed there.

### 8. `my:status` can blame a supervised run when an auto run also blocks

- **File:** `plugins/my/skills/status/SKILL.md`, line 101
- **Defect:** The "Needs you" line names a supervised run whenever the
  queue's reason is `live runs` and that run is live, even when live auto
  runs also block the exclusive entry.
- **Failure scenario:** One auto run and one supervised run are live, and an
  exclusive entry waits with "live runs". Status says "the queue waits for
  supervised run <slug>; finish it or end it". The user ends the supervised
  run, but the entry still waits for the auto run.

### 9. Cleanup: repeated checks and defaults

- **File:** `plugins/my/bin/handoff-state.py`, line 307
- **Defect:** `start_run` tests `mode == "auto"` twice in a row. The rule "a
  missing mode means auto" is written in three places: `is_auto`,
  `print_live` and the fallback in `status-scan.py` `run_facts`.
- **Failure scenario:** No runtime failure. The two auto branches could be
  one branch with a conditional message. If the default ever changes, three
  places must change together. Also, `pull`'s `ready()` reads
  `live_states()`, and then `start_run` reads it again for every entry.

### 10. One commit subject has no scope

- **File:** the subject of the commit "fix: my:status lists supervised runs
  and what waits on them"
- **Defect:** This commit has no scope. The project defines commit scopes,
  and the other commits on the branch use `fix(my-plugin):`.
- **Failure scenario:** `~/.claude/CLAUDE.md` asks for `type(scope):
  sentence`, and this project lists the scopes `my-plugin`, `kit-plugin`,
  `global` and `plans`, so the subject should start `fix(my-plugin):`. This
  matters only if the subject is reused in the squash commit.
