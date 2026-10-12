# Architecture brief: parallel auto runs

**Status:** approved, 2026-10-12. Candidate A chosen by the user; brainstorming writes the spec next.

## How to read this brief

| Document | Path | Why you would read it |
| --- | --- | --- |
| **This brief** | `docs/plans/2026-10-12-parallel-auto-runs-architecture.md` | Forces, candidates, evaluation and the chosen design. |
| Auto-run brief | `docs/plans/2026-10-11-autonomous-run-architecture.md` | The single-run design this extends. Its force 1 was one run; this brief re-judges its rejected Candidate B. |
| Auto-run spec | `docs/plans/2026-10-12-autonomous-run-spec.md` | "Out of scope" deferred parallel runs and "a queue for the steps on `main`". |
| Handoff skill | `plugins/my/skills/handoff/SKILL.md` | "Stop points in auto mode" (rows 3, 15 to 17), Review stage step 8, and "Rules for every stage" ("never poll"), which the chosen design changes. |
| Fold script | `plugins/my/bin/git-fold-fixups.py` | It refuses when another worktree holds a fixup's target. With overlapping runs that is the usual case. |
| State script | `plugins/my/bin/handoff-state.py` | The per-run state file that gains `checked_base`. |
| Docs layout rule | `global/rules/docs-layout.md` | "One feature, four commits on `main`" and "Cite only commits on `main`" (force 5). |
| Efficiency critique | `docs/reports/2026-10-09-workflow-efficiency-critique.md` | M1: branch life 1.1 h and spec-to-`done` 4.6 h at the median, the inputs of estimate 1. |
| zitamu local rules | `~/projects/zitamu/real-estate-webapp/CLAUDE.local.md`, `web/scripts/e2e-worktree.sh`, `web/scripts/preview.sh` | One fixed e2e Docker project `realestate_e2e`; preview port 54310 unless `PORT` is set. |
| diagoradisa-annotator | `~/projects/diagoradisa/diagoradisa-annotator/CLAUDE.md`, `scripts/worktree-provision.sh` | One shared Docker stack with MySQL; provisioning a worktree stops main's stack. |

The description came from the conversation, not a file: "Parallel auto runs in one project: several approved specs run `my:handoff auto` at the same time, each to its done marks, in projects that use the existing workflow (docs on main, code in worktrees, squash-merge, fold, done marks). Builds on my:handoff auto (docs/plans/2026-10-11-autonomous-run-architecture.md, docs/plans/2026-10-12-autonomous-run-spec.md, whose Out of scope deferred "a queue for the steps on main"). Decisions already made by the user: (1) scope is several auto runs at once, not the user designing alongside a run and not parallel tasks inside one feature; (2) when run B's squash-merge conflicts or its tests break because run A merged first, B rebases onto the new main, reruns the end-of-branch checks and merges if they pass; it stops only when the rebase itself conflicts; (3) test stacks: projects declare per-worktree isolation where they can (goal: fully parallel), and a resource the project marks as shared is used under a lock (fallback). Known findings from exploration: notegraph and laravel-docker-examples test on in-memory SQLite (already parallel); zitamu API tests are SQLite but its e2e uses one fixed Docker project `realestate_e2e` and preview port 54310; diagoradisa-annotator has one shared Docker stack with MySQL and `worktree-provision.sh` downs main's stack. Open problem for the brief: the fold (git-fold-fixups.py) rewrites main, which (a) leaves other runs' worktrees on rewritten bases (repairable by recording a fork point and `git rebase --onto`), and (b) changes hashes that other runs' done marks already cite (not repairable). Options to weigh include: fall back to a normal commit when the fold range holds another run's commits; or no fixups at all in auto mode. Also: SKILL.md today says a busy resource means signal the user and never poll another session; a waiting lock contradicts that. A lock cannot span tool calls, so scope each lock to one command (fcntl.flock, stdlib), and use the same lock for writes in the main checkout (index.lock collisions). Re-judge the rejected Candidate B (supervisor + queue) now that load is N runs."

## Forces

| # | Force | Value | Label | Source or reason |
| --- | --- | --- | --- | --- |
| 1 | Load | 2–4 auto runs at once in one project, routinely. Each run has 3 stages (plan, code, review), each a top-level session, run one after another. | stated | User answer. |
| 2 | Data volume and growth | One state file per run in `.git/my-handoff/<slug>.json`; about 4 commits on `main` per feature; grows linearly with features. | inferred | `plugins/my/bin/handoff-state.py`; `global/rules/docs-layout.md` "One feature, four commits on main". |
| 3 | Latency target | No target. A run finishes when it finishes; the user checks later. | stated | User answer. |
| 4 | Availability | When one run stops for the user, the other runs go on. The stopped run waits as long as needed (hours or days) in a resumable state. | stated | User answer. |
| 5 | Consistency | Never a half-done rebase on `main`. `done` marks cite only commits on `main` (they must stay valid after later folds). One writer in the main checkout at a time (`.git/index.lock`). When run B's squash-merge conflicts or its tests break because run A merged first, B rebases onto the new `main`, reruns the end-of-branch checks, and merges if they pass; it stops only when the rebase itself conflicts. | stated (rebase and retry) / inferred (rest) | User answer; `docs-layout.md` "Cite only commits on main"; `git-fold-fixups.py` refusals (it already refuses when another worktree holds a fixup's target). |
| 6 | Security and compliance | Sessions run in `auto` or `bypassPermissions` mode and act without asking. They may squash-merge to `main` and fold fixups without a yes. They never push. Anything outside the spec's Delegation section stops the run. | inferred | `docs/plans/2026-10-11-autonomous-run-architecture.md` force 6; `plugins/my/skills/handoff/SKILL.md`. |
| 7 | Team and operations | One developer, the only approver, on one machine, in tmux. No on-call. | stated | User answer. |
| 8 | Rate of change | Workflow rules change often: handoff amended several times in a month; the feature steps moved to `docs-layout.md` on 2026-10-10. | inferred | Git log; autonomous-run brief force 8. |
| 9 | Cost | unknown, assumed N × 3 stage sessions at 1.5M–8M tokens each, no budget cap. | assumed | No budget stated; numbers from `plugins/my/skills/handoff/README.md`. |
| 10 | Fixed constraints | Claude Code + tmux. Each stage runs in its own top-level session (handoff spec D2). Skills are Markdown prompts plus Python standard-library scripts. No new dependencies without approval. Never push. Projects keep the existing workflow: specs and plans on `main` in the main checkout, code in a worktree, squash-merge, fold fixups with `git-fold-fixups.py`, `done` marks. Test stacks: projects declare per-worktree isolation where they can (goal: fully parallel); a resource the project marks as shared is used under a lock (fallback). SKILL.md today says a busy resource means "signal the user" and "never poll for another session". Bash state does not persist between tool calls, so a lock held across several tool calls needs a lease file. | stated (test stacks) / inferred (rest) | User answer; `docs/plans/2026-09-21-handoff-spec.md` D2; global CLAUDE.md; `plugins/my/skills/handoff/SKILL.md` "Rules for every stage". |

## Collapse gate

Three candidates. Forces 1 (2–4 runs, far under 50 requests/s), 3 (no latency target), 4 (a stop may last days) and 7 (one developer) would collapse the gate. Force 10 does not: each stage runs in its own top-level session (handoff spec D2), and 2–4 runs share one `main`, so the design needs more than one process.

- Event-driven: not used. It would need consumers that keep their own views; force 2 gives one small store, git, and force 7 one machine.
- Separate deployables, each owning its own data: not used. Force 2 gives about 4 commits and one state file per feature, nothing to split.
- Client-heavy or offline-first: not used. Force 10 has no client; everything runs in local sessions.
- Managed or serverless services: not used. Force 10 is local tmux, and the user never pushes from a run.

## Candidates

### Candidate A: simplest design

**Reason:** Always included: the simplest design that could meet the forces.
**Contrast:** vs B: process count (no new process vs a daemon), sync or async (blocking lock vs submit and wait), data ownership (kernel locks vs a queue journal). vs C: process count, sync or async, data ownership.
**Labels:** none

#### Summary

Shape: simplest design. Each run stays its own chain of `my:handoff` stage sessions, as it is today. There is no supervisor and no new long-lived process, and git plus `.git/my-handoff/` remains the only data store. Runs coordinate through one stdlib helper, `handoff-lock.py <name> -- <command>`. It holds an `fcntl.flock` on `.git/my-handoff/locks/<name>.lock` for exactly one shell command, and the kernel frees the lock when the process exits, so no lease file is needed. The fold is removed from auto mode: the `approved` edit, spec and plan corrections, and review edits all become normal commits. Done marks then cite hashes that never change. A merge is an optimistic compare-and-swap on `main`: B merges only code that was tested on the `main` it merges into. Otherwise it rebases its worktree, reruns the checks and tries again.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Stage session (plan, code, review) | Runs one stage of one run, as today. Wraps every write in the main checkout and every shared-resource command in `handoff-lock.py` | Its worktree and branch | Top-level `claude` session in tmux, one per stage |
| `handoff-lock.py` (new, stdlib) | Blocking `flock` with a timeout around one command; exit 75 on timeout | none (the kernel owns the lock) | Script in `plugins/my/bin/` |
| Lock `main` | Serialises every write in the main checkout: `git add`/`commit -- <paths>`, the merge group, `worktree remove`, done marks | Who may write `.git/index` right now | Lock file |
| Locks `<resource>` | Serialise a resource the project marks as shared (zitamu: `e2e`, which covers project `realestate_e2e` and port 54310) | Who uses the resource | Lock file |
| Run-state file `<slug>.json` | As today, plus `checked_base` (the `main` SHA the end-of-branch checks ran against) and `retries` | Where the run is | Plain file |
| Project "Parallel runs" section (CLAUDE.md) | Declares per-worktree isolation (env vars such as `COMPOSE_PROJECT_NAME=<slug>`, port offsets) and names the shared resources with their commands | The project's isolation contract | Markdown |
| `git-fold-fixups.py` | Unchanged. Not called in auto mode | none | Existing script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Stage → lock `main` | One command: stage paths, commit with an explicit pathspec, `handoff-state.py set` | sync, waits ≤ 5 min | Timeout: stop (signal) with `next` unchanged |
| Review → lock `main` (merge group) | One command: if `main` ≠ `checked_base` and `git diff checked_base..main` touches non-`.md` files or `git merge-tree` reports a conflict, exit 3 with no change. Else `merge --squash`, commit, set `next`. On a conflict, `reset --merge` inside the same command | sync | Exit 3: release the lock, `git rebase main` in the worktree, rerun the checks, set `checked_base`, retry. A rebase conflict means `rebase --abort` and a stop. After 3 retries, stop |
| Stage → lock `<resource>` | One test command, such as `make e2e` (up, test and down in one recipe, confirmed in zitamu's Makefile) | async (`run_in_background`) | Timeout or test failure: the existing stop rows |
| Stage → user | Signal (⚠ mark plus notification), unchanged | async | The ⚠ mark persists |
| Lock → git `index.lock` held by the user's own commit | git exits with an error | sync | Retry once after 5 s, then stop |

### Candidate B: queue and background workers

**Reason:** Force 1 (2–4 runs at once) and force 5 (one writer in the main checkout): the steps on `main` from N runs need a queue with one owner, which re-judges the supervisor-and-queue design rejected when load was one run.
**Contrast:** vs A: process count, sync or async, data ownership. vs C: where computation runs (a Python process vs a Claude session) only.
**Labels:** none

#### Summary

Shape: queue and background workers. One Python stdlib daemon, `main-queue.py serve`, runs in its own tmux window. It is the only writer in the main checkout. Its rule: `git merge --squash` runs only when `merge-base(branch, main) == main HEAD` and the job carries check evidence for that exact branch tip. If `main` has moved, the job goes back to the run's review session. That session rebases in its worktree, reruns only the end-of-branch checks, and enqueues the merge again. So the squash on `main` can never conflict. Every conflict moves to the rebase in the worktree, which is decision 2's one stop point. Fixups fold only when the fold range holds nothing but this run's commits. Otherwise they become plain commits.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Queue daemon `main-queue.py serve` | Runs main jobs one at a time, in order: merge, worktree remove, fold-or-plain-commit. Grants the exclusive main lease. | Queue journal: job files, results, the lease, which commit belongs to which run | Python process in a tmux window. Single instance by `flock` on a pidfile. Started by the first auto launch. |
| Queue dir `<git-common-dir>/my-handoff/queue/` | Holds jobs and their results | Job outcomes | Files |
| Stage sessions (plan, code, review) | Same as today, but every write to `main` goes through a job or a lease | The run file `<slug>.json`. The daemon never writes it. | Top-level `claude`, one per stage |
| `main-queue.py submit/wait` | Enqueue a job, block until its result | none | CLI in `run_in_background` |
| `run-shared.py <resource> -- <cmd>` | Runs one test command under `fcntl.flock` | none | CLI, one command per lock |
| `handoff-state.py check` | Crash recovery: `merge done` detection, in-progress refusal | none | Existing script, reused by the daemon on restart |
| `git-fold-fixups.py` | Folds, or refuses | none | Existing script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Review session → daemon | Merge job: branch, tip hash, check evidence, squash subject | async (submit + `wait`) | Daemon dead: `wait` sees the pidfile lock is free and restarts the daemon. The job file survives. |
| Daemon → review session | Result: `merged <hash>` / `rebase-needed` / `refused <reason>` | async | Session window dead: the result stays on disk. `auto resume` reads the queue result before the run file. |
| Plan / done-mark session → daemon | Lease request, then edit, `git commit -- <paths>`, release | async grant, then sync | Holder's tmux window or pid gone: the daemon frees the lease, sets `stopped` in the result, and goes on with the other runs. |
| Session → daemon | "Approve spec X" intent instead of `commit --fixup` | async | Daemon decides: a fixup plus a fold if the range is this run's own, else a plain `docs(plans)` commit. |
| Daemon → git on `main` | `merge --squash`, `worktree remove`, `git-fold-fixups.py` | sync | Dirty main checkout or fold exit 1/3: the job is `refused` and the queue pauses on main jobs only. Signal the user. |
| Session → shared resource | One test command under `flock` | sync (blocks) | Holder dies: the kernel frees the lock. |

### Candidate C: pipeline or batch processing

**Reason:** Force 5 (`done` marks must cite commits that stay on `main` after later folds): a staged integration step can fold once before any `done` mark is written.
**Contrast:** vs A: process count, sync or async, data ownership. vs B: where computation runs only.
**Labels:** near-copy of candidate B

#### Summary

Shape: pipeline or batch processing. Each auto run moves through the stations plan → code → review and ends as a **finished branch in an integration queue**. It no longer squash-merges itself. One integrator stage (`/my:handoff run integrate`, a top-level session with a lease so only one runs) works through the queue in batches. For each branch it rebases onto `main` and reruns the end-of-branch checks if needed, then squash-merges. It then runs **one fold for the whole batch**, writes every `done` mark in the batch only after that fold, and moves a recorded **fold floor** up to the new `main`. From then on, a fixup is allowed only when its target sits above the floor. A fixup aimed at an older commit becomes a normal commit. So no later fold can rewrite a commit that a `done` mark cites.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Stage sessions (plan, code, review) | As today. The review stage ends by adding its branch to the queue, not by merging | none | Top-level `claude` session per stage (D2) |
| Run-state file `.git/my-handoff/<slug>.json` | Next step per run, plus new fields `fork_point` and `checks` (the check commands to rerun) | Where each run is | File, written by `handoff-state.py` |
| Integration queue `.git/my-handoff/queue/<slug>` | Finished branches waiting to merge, in arrival order | Which branches are ready | One file per branch, added under flock |
| Integrator (`run integrate`) | Drains the queue: rebase → recheck → squash-merge → worktree remove, for each item. Then one fold, the `done` marks for the batch, and moving the floor | The batch in progress | Top-level session. Launched by the review stage that finds no live lease |
| Integrate lease `.git/my-handoff/integrate.lease` | Allows one integrator at a time, across tool calls | Who is integrating (tmux window id) | Created with O_EXCL. It counts as stale when its window is gone |
| Fold floor `refs/my-handoff/fold-floor` | Lowest commit a fold may rewrite | The boundary for folds | Git ref |
| `git-fold-fixups.py` (extended) | `check` exits 1 when the target is not above the floor. The fold refuses the same targets | none | Existing script |
| `main-lock` (fcntl.flock wrapper) | Wraps one command that writes the main checkout (commit, merge) or one command that uses a shared test resource | none | Stdlib Python script, one lock per resource name |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Plan stage → `main` | Plan commit, or a fixup above the floor, each wrapped in `main-lock` | sync | Lock busy: blocks inside the one command. Commit fails: stop (row 3) |
| Review stage → queue | Queue file `<slug>`, then `next=queued` | sync | Write fails: stop and signal |
| Review stage → integrator | `tmux new-window '/my:handoff run integrate'` if no live lease | async | Window fails to open: print the command and signal. The item stays queued |
| Integrator → worktree branch | `git rebase --onto main <fork_point>`, then the `checks` commands | sync | Rebase conflicts: `rebase --abort`, mark the item stopped and signal, go on with the next item. Checks fail: stop that item, go on |
| Integrator → `main` | Squash-merge, worktree remove, fold, `done` commit | sync | Fold exits 1: write no `done` marks, leave the items as `merged`, signal. Exit 3: record the HEAD before the fold and stop the integrator |
| Integrator → lease | Removes the lease, then reads the queue once more | sync | Queue not empty: takes the lease again, so no item is left behind |
| Test command → shared resource | `main-lock <resource> -- <cmd>` | sync (blocks inside one command) | Times out: stop and signal |

## Evaluation

### Data ownership

| State | A | B | C |
| --- | --- | --- | --- |
| A run's next step (`<slug>.json`) | the run's stage session | the run's stage session (the daemon never writes it) | **two owners**: the stage sessions and the integrator (`queued`, `integrating`, `merged`) |
| Who may write the main checkout now | the kernel, through lock `main` | the daemon, plus sessions holding its lease | lock `main` for commits; the integrator lease for merges |
| Use of a shared test resource | the kernel, through lock `<resource>` | the kernel, through `run-shared.py` | the kernel, through `main-lock <resource>` |
| Which commit belongs to which run | nobody; not needed, because there is no fold | the daemon's journal | nobody; the fold floor replaces it |
| Merge order | nobody: whichever run wins the lock | the daemon's queue | the integration queue: review stages add, the integrator removes (two writers under one flock) |
| Isolation per worktree | the project's "Parallel runs" section | not named; assumed the same | not named; assumed the same |
| The fold boundary | none (no fold in auto mode) | the daemon's rule "own commits only" | the ref `refs/my-handoff/fold-floor`, written by the integrator |

Flags: C's run state has two owners. In all three, the user's own commits in the main checkout take no lock, so the main checkout has a writer outside every design.

### Scenarios

1. **Normal path at peak: 4 runs, two reach the merge within minutes.**
   - A: holds. The second run's merge command sees `main` ≠ `checked_base` with code changes and exits 3. It rebases in its worktree, reruns the checks and merges. Estimate 1 puts this at about 28% of runs.
   - B: holds. The daemon returns `rebase-needed`; the review session rebases and submits again.
   - C: partial. Both branches merge, but the batch fold refuses while the other two runs' worktrees hold its targets. The `done` marks wait (Integrator → `main`, fold exit 1).
2. **A dependency fails: the shared e2e stack hangs, or a session holding a lock crashes.**
   - A: holds. The kernel frees a lock when its command dies. The lock timeout stops the waiting run with a signal, and the other runs go on.
   - B: holds, with more steps. A dead daemon is restarted by the next `wait`; a dead lease holder is detected by its tmux window or pid.
   - C: holds. A stale integrator lease is detected by its tmux window. The item stops, and the queue goes on.
3. **Most frequent change: a workflow rule changes, for example the `done`-mark format or a step on `main`.**
   - A: holds. One edit in `SKILL.md`.
   - B: breaks at "Daemon → git on `main`": the steps live in Python and in `SKILL.md`, and both must change together.
   - C: holds. One edit in the integrate stage of `SKILL.md`.
4. **Data volume after 3 years: about 13 branches per week (critique M1), about 2,000 features.**
   - A and B: hold. About 5–7 commits per feature instead of 4, so about 12,000 commits; git handles that easily. One small state file per run.
   - C: holds. Fewer commits, because some folds succeed.
5. **Abuse or safety: a session writes the main checkout without taking the lock, or tries to push.**
   - All three: partial. The locks are advisory, so a session that skips the wrapper can commit another run's staged files or hit `index.lock`. Commits with an explicit pathspec, as the plan stage already does, limit the damage. The push guard from the auto-run design still blocks `git push`.

### Pre-mortem

**A**, one year on:

1. A stage forgot to wrap a write in `handoff-lock.py`. The rule is prose, the lock is advisory, and two commits collided.
2. Waits for zitamu's shared e2e stack were longer than the lock timeout. Runs stopped often until the project isolated its e2e stack.
3. History noise: 5–7 commits per auto feature, while manual features still fold to 4. The two kinds of history confused later readers.

**B**, one year on:

1. The daemon's Python copy of the merge and fold steps drifted from `SKILL.md` after a rule change.
2. The daemon was hard to debug: a stale pidfile, or a job file in an old format after an update.
3. Review sessions waiting in the background on `wait` lost their place, and recheck rounds cost tokens.

**C**, one year on:

1. The batch fold was refused nearly every time, so `done` marks piled up until the user stepped in.
2. The integrator stopped for problems in other runs' branches, and the user could not tell which run a stop belonged to.
3. Moving the merge out of the review stage, an approved decision, broke the auto run that had just shipped.

### Comparison

| Force | A: lock per command | B: queue daemon | C: integrator session |
| --- | --- | --- | --- |
| 1 Load | meets: two short locked sections per run | meets: one queue | meets |
| 2 Data volume | meets: 5–7 commits per feature | meets: same | meets: fewer commits |
| 3 Latency | meets: no target | meets | meets |
| 4 Availability | meets: a lock dies with its command | meets | partial: a refused batch fold holds back every run's `done` marks |
| 5 Consistency | meets: no fold, so cited hashes never change; merges only code checked on the current `main` | meets: the same merge rule, in code | partial: the floor protects cited hashes, but the fold is usually refused |
| 6 Security | partial: the lock is advisory | partial: the lease is advisory | partial: the lock is advisory |
| 7 Team | meets: no new process | partial: a daemon to keep alive and debug | partial: one more kind of window, with stops about other runs |
| 8 Rate of change | meets: prose in one place | fails: the steps on `main` live twice | meets |
| 9 Cost (assumed) | meets: waits cost no tokens | meets | partial: one extra session per batch |
| 10 Fixed constraints | meets: stdlib, nothing spans tool calls; needs the "never poll" rule narrowed | partial: needs a "waiting on the queue is allowed" exception | fails: reverses the approved rule that the review stage merges |

## Decision

**Candidate A: a lock per command, no fold in auto mode.** Chosen by the user on 2026-10-12.

- Each run stays its own chain of `my:handoff` stage sessions. A new stdlib script, `handoff-lock.py <name> -- <command>`, holds an `fcntl.flock` for one shell command. The kernel frees it when the command ends or dies.
- Lock `main` covers every write in the main checkout. Lock `<resource>` covers each resource a project marks as shared.
- Auto mode makes no fixups. Every later edit is a normal commit, so no auto run rewrites a hash that a `done` mark cites. This settles open problem (b) between auto runs. Problem (a) cannot arise from an auto run, because no auto run rewrites `main`. The user's own spec work on `main` still folds, which reopens (b); see "Open for brainstorming".
- The merge is a compare-and-swap. The run records `checked_base`, the `main` commit its end-of-branch checks ran against. It merges only when `main` has no code change since then. Otherwise it rebases, reruns the checks and tries again, up to 3 times. A rebase conflict is a stop. This is the user's decision 2, with a trigger that can be detected before the merge.
- A project gets a "Parallel runs" section. It names how each worktree gets its own test stack, and which resources are shared and so locked.

Why the others lost:

- **B lost** on force 8: the steps on `main` would live twice, in Python and in `SKILL.md`, and the workflow rules change often. Its real gains, first-in-first-out merges and one view of all runs, matter little when 2–4 runs merge hours apart (estimate 1). B's own weakest-point section reached the same verdict.
- **C lost** on forces 4 and 10: the fold is refused whenever another worktree holds its target, which is the usual case with overlapping runs, so the `done` marks would pile up. It also reverses the approved rule that the review stage merges.

## Reversibility and checks

| Decision | Label | Check |
| --- | --- | --- |
| No fixups in auto mode: later edits are normal commits | hard | no quantity to check: about 1–3 more commits per feature is history noise, not load. The cost is readability, which the user judges. |
| The project "Parallel runs" section and the lock names (`main`, `<resource>`) | hard | Estimate 2: how long a run waits for a shared resource. |
| `checked_base` in the state file, and the compare-and-swap merge with 3 retries | hard | Estimate 1: how often a run retries, and how often it hits the cap. |
| `handoff-lock.py` behind a one-command interface | medium | none needed |
| The "never poll" rule narrowed to "block on a lock inside one command; never poll across tool calls" | cheap | none needed |
| Lock timeouts | cheap | none needed |

Estimate 1, merge retries:

```python
"""Estimate how often a run's merge finds `main` moved (compare-and-swap retry)."""
import math

N = 4                 # runs at once, force 1 (upper end)
T_hours = 4.6         # spec first commit to done, median, zitamu (critique M1)
W_first_hours = 0.5   # assumed: end-of-branch checks + reviews + fix round, before the merge
W_retry_hours = 1/6   # assumed: rebase + rerun of end-of-branch checks only (10 min)
CAP = 3               # retries before a stop

rate = (N - 1) / T_hours          # other runs' merges per hour, if spread evenly
p1 = 1 - math.exp(-rate * W_first_hours)
pr = 1 - math.exp(-rate * W_retry_hours)
p_stop = p1 * pr ** (CAP - 1) * pr  # first miss, then CAP retries all miss
print(f"inputs: N={N}, T={T_hours} h, first window={W_first_hours} h, retry window={W_retry_hours:.2f} h, cap={CAP}")
print("formula: P(miss) = 1 - exp(-(N-1)/T * window); P(stop) = P1 * Pr^CAP")
print(f"other merges per hour: {rate:.2f}")
print(f"P(at least one retry): {p1:.0%}")
print(f"P(a retry misses again): {pr:.0%}")
print(f"P(run stops after {CAP} retries): {p_stop:.2%}  (compare: budget 'rare', under 1%)")
```

```text
inputs: N=4, T=4.6 h, first window=0.5 h, retry window=0.17 h, cap=3
formula: P(miss) = 1 - exp(-(N-1)/T * window); P(stop) = P1 * Pr^CAP
other merges per hour: 0.65
P(at least one retry): 28%
P(a retry misses again): 10%
P(run stops after 3 retries): 0.03%  (compare: budget 'rare', under 1%)
```

Not near a limit. The 4.6 h comes from zitamu runs with human waits (critique M2), so auto runs may be shorter and retries more frequent. Even at half the time, the stop chance stays far under 1%.

Estimate 2, shared-resource wait:

```python
"""Estimate the worst wait for a project-shared test resource under one lock."""
N = 4                  # runs at once, force 1
hold_min = 10          # assumed: one zitamu e2e run, up + test + down
uses_per_run = 3       # assumed: code-stage e2e checks + end-of-branch + one CAS recheck
bash_cap_min = 10      # Bash tool foreground limit, 600 s
worst_wait = (N - 1) * hold_min
busy_share = N * uses_per_run * hold_min / (4.6 * 60)
print(f"inputs: N={N}, hold={hold_min} min, uses per run={uses_per_run}, Bash foreground cap={bash_cap_min} min")
print("formula: worst wait = (N-1) * hold; resource busy share = N * uses * hold / run length (4.6 h)")
print(f"worst wait for one use: {worst_wait} min vs foreground cap {bash_cap_min} min -> {'over' if worst_wait > bash_cap_min else 'under'} ({worst_wait/bash_cap_min:.1f}x)")
print(f"resource busy share over a run: {busy_share:.0%}  (compare: 100% = runs serialised on the resource)")
```

```text
inputs: N=4, hold=10 min, uses per run=3, Bash foreground cap=10 min
formula: worst wait = (N-1) * hold; resource busy share = N * uses * hold / run length (4.6 h)
worst wait for one use: 30 min vs foreground cap 10 min -> over (3.0x)
resource busy share over a run: 43%  (compare: 100% = runs serialised on the resource)
```

The worst wait is 3 times the Bash foreground limit, so a locked resource command must run with `run_in_background`, and the lock timeout must be longer than 30 minutes. The busy share depends on the assumed 10-minute hold. **Spike proposed, not run:** time one run of zitamu's `web/scripts/e2e-worktree.sh --no-journeys` and one full e2e run, to replace the assumed 10 minutes. The user chose to skip it.

## Open for brainstorming

- Force 9 (cost): unknown, assumed N × 3 stage sessions at 1.5M–8M tokens each, no budget cap.
- Spike not run: how long one zitamu e2e run holds the shared lock (assumed 10 minutes). It sets the lock timeout, and whether zitamu should isolate its e2e stack before parallel runs.
- diagoradisa-annotator: `worktree-provision.sh` stops main's stack, which no lock prevents. Does the spec cover a project fix, or is that project out of scope until it isolates its stack?
- The user's own commits in the main checkout take no lock. Is a retry on `index.lock` enough, or should the spec give the user a wrapper too?
- Manual (non-auto) features still fold to four commits. Should "One feature, four commits on `main`" in `docs-layout.md` name the auto-mode exception, and how?
- What counts as a "code change" for the compare-and-swap: any file outside `docs/`, or any file that is not `.md`? Candidate A proposed non-`.md`.
- The user's own folds while runs are live. The user writes the next spec on `main` while other runs go on, and that flow still folds: docs-layout steps 4 and 9, and the Medium `approved` fixup. Two problems follow. First, `target_refusal` in `git-fold-fixups.py` refuses only a target that a worktree holds or that is pushed. A finished run's squash commit has neither, so the user's fold can rewrite it and break the `done` mark that cites it. Second, other runs' drafts in the main checkout make the fold refuse with "uncommitted changes to tracked files". One answer to weigh: the fold also refuses when its range holds a commit that changes a file other than `.md`, which means another feature's squash, and the existing fallback to a normal commit takes over. The global `CLAUDE.md` Medium paragraph, which says the auto code stage "commits and folds that edit itself", is a contract the spec must change.
- Lock `main` covers the commit command, not the edit before it. An Edit to `ROADMAP.md`, `CHANGELOG.md` or a plans index happens in an earlier tool call, outside any lock. The `done` commit `6e5f47a` edits `ROADMAP.md`, for example. Two runs that write `done` marks close together can then commit each other's half-made edits. Options to weigh: make shared-file edits in the worktree, so they arrive with the squash (step 11 forbids this for the plans index, so the index needs its own answer); or make the edit inside the locked command, through a script.

## Appendix: candidate drafts

### Candidate A

#### Summary

Shape: simplest design. Each run stays its own chain of `my:handoff` stage sessions, as it is today. There is no supervisor and no new long-lived process, and git plus `.git/my-handoff/` remains the only data store. Runs coordinate through one stdlib helper, `handoff-lock.py <name> -- <command>`. It holds an `fcntl.flock` on `.git/my-handoff/locks/<name>.lock` for exactly one shell command, and the kernel frees the lock when the process exits, so no lease file is needed. The fold is removed from auto mode: the `approved` edit, spec and plan corrections, and review edits all become normal commits. Done marks then cite hashes that never change. A merge is an optimistic compare-and-swap on `main`: B merges only code that was tested on the `main` it merges into. Otherwise it rebases its worktree, reruns the checks and tries again.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Stage session (plan, code, review) | Runs one stage of one run, as today. Wraps every write in the main checkout and every shared-resource command in `handoff-lock.py` | Its worktree and branch | Top-level `claude` session in tmux, one per stage |
| `handoff-lock.py` (new, stdlib) | Blocking `flock` with a timeout around one command; exit 75 on timeout | none (the kernel owns the lock) | Script in `plugins/my/bin/` |
| Lock `main` | Serialises every write in the main checkout: `git add`/`commit -- <paths>`, the merge group, `worktree remove`, done marks | Who may write `.git/index` right now | Lock file |
| Locks `<resource>` | Serialise a resource the project marks as shared (zitamu: `e2e`, which covers project `realestate_e2e` and port 54310) | Who uses the resource | Lock file |
| Run-state file `<slug>.json` | As today, plus `checked_base` (the `main` SHA the end-of-branch checks ran against) and `retries` | Where the run is | Plain file |
| Project "Parallel runs" section (CLAUDE.md) | Declares per-worktree isolation (env vars such as `COMPOSE_PROJECT_NAME=<slug>`, port offsets) and names the shared resources with their commands | The project's isolation contract | Markdown |
| `git-fold-fixups.py` | Unchanged. Not called in auto mode | none | Existing script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Stage → lock `main` | One command: stage paths, commit with an explicit pathspec, `handoff-state.py set` | sync, waits ≤ 5 min | Timeout: stop (signal) with `next` unchanged |
| Review → lock `main` (merge group) | One command: if `main` ≠ `checked_base` and `git diff checked_base..main` touches non-`.md` files or `git merge-tree` reports a conflict, exit 3 with no change. Else `merge --squash`, commit, set `next`. On a conflict, `reset --merge` inside the same command | sync | Exit 3: release the lock, `git rebase main` in the worktree, rerun the checks, set `checked_base`, retry. A rebase conflict means `rebase --abort` and a stop. After 3 retries, stop |
| Stage → lock `<resource>` | One test command, such as `make e2e` (up, test and down in one recipe, confirmed in zitamu's Makefile) | async (`run_in_background`) | Timeout or test failure: the existing stop rows |
| Stage → user | Signal (⚠ mark plus notification), unchanged | async | The ⚠ mark persists |
| Lock → git `index.lock` held by the user's own commit | git exits with an error | sync | Retry once after 5 s, then stop |

#### Forces

Served:

- 1 (load): runs share nothing except two short critical sections. The per-slug state files already allow N runs.
- 4 (availability): a stopped run holds no lock, because the lock dies with its command, so the other runs go on.
- 5 (consistency): one writer in the main checkout; the merge and its cleanup sit inside one locked command, so no half-done state is left; no fold means cited hashes never change; the compare-and-swap means merged code was tested on the tip it lands on.
- 10 (fixed constraints): stdlib only, no new process type, and no lock spans tool calls.

Sacrificed:

- 10 (fold with `git-fold-fixups.py`): auto mode drops it. The alternative, "fold unless another run's commits sit in the range", works out to normal commits anyway whenever runs overlap. A run that forked after the spec commit holds it, and the fold refuses on "another worktree holds a target". That refusal must become "commit normally", not a stop. The fold option only adds a branch that is rarely taken.
- 2 (data volume): `main` gets about 5–7 commits per feature instead of 4.
- 9 (cost): each compare-and-swap retry costs a fresh run of the end-of-branch checks.
- SKILL.md "never poll": replaced by "block on a lock inside one command; never poll across tool calls".

#### Hard-to-reverse decisions

- No fixups in auto mode. The extra commits on `main` stay in history for good.
- The lock names and the project "Parallel runs" section become a contract that every project must follow.
- `checked_base` defines "tests break because A merged first" as "`main`'s code changed since my checks ran". This replaces decision 2's trigger with an equivalent you can detect without testing after the merge.

#### Numbers it depends on

- Lock `main` is held for under 10 s, against a 5-minute wait timeout.
- The wait for a shared resource is (N−1) × hold time. With N = 4 and an e2e run of about 10 min (assumed), the wait is about 30 min. That is over Bash's 600 s foreground cap, so these commands must run with `run_in_background`.
- Compare-and-swap retries: few, because code merges happen about once per run, hours apart. The cap is 3.
- 2–4 runs (force 1). Above about 6, the e2e queue dominates the time a run takes.

#### Weakest point

Order on `main` is set by whichever run wins the lock race, not by a queue. Under a burst of merges one run can lose three times and stop. That is the honest case for Candidate B: with N runs, a supervisor's queue gives first-in-first-out merges and one place to see every run. The lock is advisory. The user's own commits in the main checkout do not take it, so a collision on git's `index.lock` costs a retry or a stop. Because other runs' drafts sit there across tool calls, a dirty main checkout becomes the normal state. That is harmless only because the fold is gone. diagoradisa-annotator does not fit: its `worktree-provision.sh` takes down main's stack, which no lock prevents. It needs a project fix first, or every run there stops.
The e2e hold time (and so the wait) and the token cost of reruns rest on the assumed force 9.

### Candidate B

#### Summary

Shape: queue and background workers. One Python stdlib daemon, `main-queue.py serve`, runs in its own tmux window. It is the only writer in the main checkout. Its rule: `git merge --squash` runs only when `merge-base(branch, main) == main HEAD` and the job carries check evidence for that exact branch tip. If `main` has moved, the job goes back to the run's review session. That session rebases in its worktree, reruns only the end-of-branch checks, and enqueues the merge again. So the squash on `main` can never conflict. Every conflict moves to the rebase in the worktree, which is decision 2's one stop point. Fixups fold only when the fold range holds nothing but this run's commits. Otherwise they become plain commits.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Queue daemon `main-queue.py serve` | Runs main jobs one at a time, in order: merge, worktree remove, fold-or-plain-commit. Grants the exclusive main lease. | Queue journal: job files, results, the lease, which commit belongs to which run | Python process in a tmux window. Single instance by `flock` on a pidfile. Started by the first auto launch. |
| Queue dir `<git-common-dir>/my-handoff/queue/` | Holds jobs and their results | Job outcomes | Files |
| Stage sessions (plan, code, review) | Same as today, but every write to `main` goes through a job or a lease | The run file `<slug>.json`. The daemon never writes it. | Top-level `claude`, one per stage |
| `main-queue.py submit/wait` | Enqueue a job, block until its result | none | CLI in `run_in_background` |
| `run-shared.py <resource> -- <cmd>` | Runs one test command under `fcntl.flock` | none | CLI, one command per lock |
| `handoff-state.py check` | Crash recovery: `merge done` detection, in-progress refusal | none | Existing script, reused by the daemon on restart |
| `git-fold-fixups.py` | Folds, or refuses | none | Existing script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Review session → daemon | Merge job: branch, tip hash, check evidence, squash subject | async (submit + `wait`) | Daemon dead: `wait` sees the pidfile lock is free and restarts the daemon. The job file survives. |
| Daemon → review session | Result: `merged <hash>` / `rebase-needed` / `refused <reason>` | async | Session window dead: the result stays on disk. `auto resume` reads the queue result before the run file. |
| Plan / done-mark session → daemon | Lease request, then edit, `git commit -- <paths>`, release | async grant, then sync | Holder's tmux window or pid gone: the daemon frees the lease, sets `stopped` in the result, and goes on with the other runs. |
| Session → daemon | "Approve spec X" intent instead of `commit --fixup` | async | Daemon decides: a fixup plus a fold if the range is this run's own, else a plain `docs(plans)` commit. |
| Daemon → git on `main` | `merge --squash`, `worktree remove`, `git-fold-fixups.py` | sync | Dirty main checkout or fold exit 1/3: the job is `refused` and the queue pauses on main jobs only. Signal the user. |
| Session → shared resource | One test command under `flock` | sync (blocks) | Holder dies: the kernel frees the lock. |

#### Forces

Served:

- 1 (Load): each step on `main` from N runs takes its turn in one queue. No `index.lock` collisions.
- 4 (Availability): a stopped run releases its lease and its jobs. The others drain on. The stopped run's state stays on disk for days.
- 5 (Consistency): the merge precondition rules out a conflicting squash and a half-done rebase on `main`. The rebase-and-retry happens in the worktree. A fold never rewrites commits that another run cites, because the daemon's journal knows who owns each commit.
- 9 (Cost): the daemon spends zero tokens. The old Candidate B needed a Claude supervisor session.

Sacrificed:

- 8 (Rate of change): merge, worktree remove and the fold move out of SKILL.md prose into Python. The old B lost for this reason, a second copy of the steps on `main`. That loss is now worse, and only the standing-session loss is fixed.
- 10 (Fixed constraints): SKILL.md's "never poll" rule must become "waiting on the queue is allowed; waiting on another session is not".
- 7 (Team): one more process that must stay alive and be debugged.
- In practice there are almost no folds. With 2–4 runs alive, a newer worktree nearly always holds an older run's spec commit, so `held_branches` refuses. "Four commits on `main`" in `docs-layout.md` becomes five or six, and the user must see that rule change.

#### Hard-to-reverse decisions

- Merge and fold logic become tested code. Going back to prose means rewriting handoff's Review step 8.
- The fold rule "own commits only, else a plain commit" changes how `main` history looks for every auto feature.
- Job and lease file formats under `.git/my-handoff/queue/`. Runs in flight when the format changes cannot resume.
- The amended no-poll rule.

#### Numbers it depends on

- 2–4 runs at once. Rechecks per run are at most N−1 = 3, each a full end-of-branch check run.
- About 4–6 main jobs per feature, each taking seconds, against hours per stage. Queue wait is negligible except for done-mark leases (minutes).
- Bash's foreground cap of 600 s. The zitamu e2e and the diagoradisa stack under `run-shared.py` must run through `run_in_background`.
- Done-mark lease hold time against N: all runs hold one lease, so at worst 3 runs wait a few minutes each.
- Stage sessions at 1.5M–8M tokens (assumed), plus up to 3 recheck rounds that cost tokens even though they are mechanical.

#### Weakest point

A lock-per-command design gets the same results with less machinery. Each write to `main` would wrap itself in `flock`. The review session would check `merge-base == main` itself before squashing. That gives one writer at a time, the same merge precondition and the same fold rule, with no daemon to keep alive, no job format, no lease liveness rules and no second copy of the steps. The queue adds three things the lock lacks: FIFO order, one place that knows which run owns each commit, and zero-token waiting. With 2–4 runs and seconds-long jobs, ordering hardly matters, and commit ownership could be a trailer instead. The recheck cost also rests on force 9, which is assumed. If e2e runs take tens of minutes, N−1 rechecks under a shared lock could serialize runs badly. That happens in any shape, but this one does not reduce it.

The lock does not fix diagoradisa: `worktree-provision.sh` downs main's stack, so that project needs its own change in any candidate.

### Candidate C

#### Summary

Shape: pipeline or batch processing. Each auto run moves through the stations plan → code → review and ends as a **finished branch in an integration queue**. It no longer squash-merges itself. One integrator stage (`/my:handoff run integrate`, a top-level session with a lease so only one runs) works through the queue in batches. For each branch it rebases onto `main` and reruns the end-of-branch checks if needed, then squash-merges. It then runs **one fold for the whole batch**, writes every `done` mark in the batch only after that fold, and moves a recorded **fold floor** up to the new `main`. From then on, a fixup is allowed only when its target sits above the floor. A fixup aimed at an older commit becomes a normal commit. So no later fold can rewrite a commit that a `done` mark cites.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Stage sessions (plan, code, review) | As today. The review stage ends by adding its branch to the queue, not by merging | none | Top-level `claude` session per stage (D2) |
| Run-state file `.git/my-handoff/<slug>.json` | Next step per run, plus new fields `fork_point` and `checks` (the check commands to rerun) | Where each run is | File, written by `handoff-state.py` |
| Integration queue `.git/my-handoff/queue/<slug>` | Finished branches waiting to merge, in arrival order | Which branches are ready | One file per branch, added under flock |
| Integrator (`run integrate`) | Drains the queue: rebase → recheck → squash-merge → worktree remove, for each item. Then one fold, the `done` marks for the batch, and moving the floor | The batch in progress | Top-level session. Launched by the review stage that finds no live lease |
| Integrate lease `.git/my-handoff/integrate.lease` | Allows one integrator at a time, across tool calls | Who is integrating (tmux window id) | Created with O_EXCL. It counts as stale when its window is gone |
| Fold floor `refs/my-handoff/fold-floor` | Lowest commit a fold may rewrite | The boundary for folds | Git ref |
| `git-fold-fixups.py` (extended) | `check` exits 1 when the target is not above the floor. The fold refuses the same targets | none | Existing script |
| `main-lock` (fcntl.flock wrapper) | Wraps one command that writes the main checkout (commit, merge) or one command that uses a shared test resource | none | Stdlib Python script, one lock per resource name |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Plan stage → `main` | Plan commit, or a fixup above the floor, each wrapped in `main-lock` | sync | Lock busy: blocks inside the one command. Commit fails: stop (row 3) |
| Review stage → queue | Queue file `<slug>`, then `next=queued` | sync | Write fails: stop and signal |
| Review stage → integrator | `tmux new-window '/my:handoff run integrate'` if no live lease | async | Window fails to open: print the command and signal. The item stays queued |
| Integrator → worktree branch | `git rebase --onto main <fork_point>`, then the `checks` commands | sync | Rebase conflicts: `rebase --abort`, mark the item stopped and signal, go on with the next item. Checks fail: stop that item, go on |
| Integrator → `main` | Squash-merge, worktree remove, fold, `done` commit | sync | Fold exits 1: write no `done` marks, leave the items as `merged`, signal. Exit 3: record the HEAD before the fold and stop the integrator |
| Integrator → lease | Removes the lease, then reads the queue once more | sync | Queue not empty: takes the lease again, so no item is left behind |
| Test command → shared resource | `main-lock <resource> -- <cmd>` | sync (blocks inside one command) | Times out: stop and signal |

#### Forces

Served:

- 5 (Consistency): `done` marks are written only after the batch fold. The floor keeps every cited commit out of reach of later folds, so the unfixable case (b) cannot happen. Rebasing with `--onto <fork_point>` repairs case (a). There is one writer to `main` for merges and folds.
- 4 (Availability): a stopped item does not block the queue. The integrator skips it, and the other branches merge.
- 1 (Load): stages run fully in parallel. Only the steps on `main` run one after another, which suits 2–4 runs.
- 8 (Rate of change): the integrator is a handoff stage in `SKILL.md`, not a second copy in a supervisor. It moves Review step 8 rather than duplicating it.

Sacrificed:

- "Four commits on `main`": a fixup below the floor becomes a normal commit, so features that run alongside each other leave more than four commits.
- 7 (Operations): there is one more kind of window (the integrator), and its stops are about other runs' branches.
- D2 and the auto spec: the review stage no longer merges. That reverses part of an approved decision, so the user must re-approve it.
- `SKILL.md` "never poll / signal on busy": replaced by a lock that blocks inside one command. This needs a rule change.

#### Hard-to-reverse decisions

- Merge, fold and `done` marks move out of the review stage into a separate integrate stage, and the state file gains new steps (`queued`, `integrating`).
- The fold floor becomes part of `git-fold-fixups.py`, so it changes what counts as a safe fixup in every project, not only during auto runs.
- `done` marks are written per batch. One `done` commit may cover several features.

#### Numbers it depends on

- At most about 4 queue items per batch (force 1). Integrator time ≈ the number of rebased items × the time of their check commands. With zitamu's e2e (one shared stack, minutes per run) under one lock, a batch of 4 could hold `main` for tens of minutes. This is acceptable only because force 3 sets no latency target.
- An integrator session per batch costs well under one stage session (assumed under 1M tokens, against 1.5M–8M per stage, force 9 assumed).
- Fixups below the floor: assumed rare, under about 1 per feature. Spec edits during a plan stage target that run's own spec, and that spec usually sits above the floor unless another batch has finished in the meantime.

#### Weakest point

The batch fold has no way to wait for a quiet window. `git-fold-fixups.py` already refuses when another worktree holds a target. With 2–4 runs routinely in flight, nearly every worktree branched from `main` holds the other runs' spec commits. So the batch fold will often exit 1, and under this design no `done` marks are written then. Marks can pile up as `merged, awaiting fold` until all runs go quiet. With steady load (force 1), that may be days, and the whole point of the shape, a fold before the marks, rarely happens.

The only way out is to let the integrator fold over held targets and then rebase the idle worktrees with `--onto`. But rebasing a worktree while a live code session works in it is unsafe, so the integrator would need to know which worktrees are idle. That is the supervisor knowledge Candidate B had. If folds mostly fail, the design reduces to "no fixups in auto mode" plus a merge queue, and the batch fold adds machinery that does nothing.

It also depends on the assumed cost (force 9) and on end-of-branch checks being plain commands that a session can rerun. Review findings are not rerun after a rebase.
