# Architecture brief: start auto runs from roadmap rows

**Status:** approved, 2026-10-13. Candidate A chosen by the user; brainstorming writes the spec next.

## How to read this brief

| Document | Path | Why you would read it |
| --- | --- | --- |
| **This brief** | `docs/plans/2026-10-13-roadmap-auto-runs-architecture.md` | Forces, candidates, evaluation and the chosen design. |
| Roadmap row | `ROADMAP.md`, "Design workflow", "Start auto runs from roadmap rows"; and "Order of work" | The row this brief serves. It comes after "Swappable methods" batch 2. |
| Parallel-runs brief | `docs/plans/2026-10-12-parallel-auto-runs-architecture.md` | The lock-per-command design this builds on. It rejected a supervisor (its Candidate B). |
| Parallel-runs spec | `docs/plans/2026-10-12-parallel-auto-runs-spec.md` | "Out of scope": "the auto runs still start only when the user starts them". This brief lifts that limit. |
| Status spec and skill | `docs/plans/2026-10-12-status-skill-spec.md`, `plugins/my/skills/status/SKILL.md` | Steps 4 to 6 (spec, gates, file lists) and "What can run in parallel", the rules the new command reuses. |
| Handoff skill | `plugins/my/skills/handoff/SKILL.md` | "Parallel runs", "Launch", "Start checks in auto mode", the review stage and "To end an abandoned run", where the refill goes; "Rules for every stage" ("never poll"). |
| State script | `plugins/my/bin/handoff-state.py` | `start --max`, `live`, the slot rule. The new `pull` sits beside `start`. |
| Status scan | `plugins/my/bin/status-scan.py` | Counts every `my-handoff/*.json` as a run, so the queue file must sit in a subfolder. |
| Swappable methods plan | `docs/plans/2026-10-12-swappable-methods.md` | Batch 2 moves the method rules out of `global/CLAUDE.md` and edits `my:status`. |

The description came from the conversation, not a file: "Start auto runs from roadmap rows (ROADMAP.md row in "Design workflow", added in 0e7ae2a). One command takes a list of roadmap rows, starts the rows that have an approved spec as parallel `my:handoff auto` runs up to Max runs, and starts a waiting row each time a run finishes. Builds on docs/plans/2026-10-12-parallel-auto-runs-architecture.md and -spec.md (whose Out of scope said "the auto runs still start only when the user starts them") and on my:status (docs/plans/2026-10-12-status-skill-spec.md), whose step 3 rules decide what can run together. Decisions and findings from the conversation: (1) The user wants to call one command once in a session with the roadmap rows; it handles the session orchestration itself. Typing /my:handoff auto once per spec is not practical. (2) Only rows with an approved spec that has a Delegation section can start; writing a spec needs the user (brainstorming). Open: confirm the command lists and skips the others. (3) Who refills a free slot: Option A "each finished run starts the next waiting row" (no supervisor, matches the parallel-runs brief, which rejected a supervisor as Candidate B) vs Option B a supervisor session that watches .git/my-handoff/ state files. Both keep up to Max runs live; a stopped run keeps its slot because the cap counts every run whose next is not finished. Recommended A; re-judge. (4) Mechanical detection of parallel work, measured in this repo: predicted file lists were accurate when present (status-skill spec named all 4 code files of c4d3832; the parallel-auto-runs plan named all 15 of 38f6c34; misses were only test and helper files). But 6 of the last 13 specs have no Files section, and README.md, plugins/my/skills/handoff/SKILL.md, plugins/my/skills/handoff/README.md, global/CLAUDE.md and global/rules/docs-layout.md each changed in 3-4 of the last 8 code merges, so a whole-file overlap check marks most pairs here as not safe. Proposal to weigh: gates in "## Order of work" and unknown overlap are hard blocks; file overlap is a soft signal, because the parallel merge step already rebases, reruns checks and stops only on a rebase conflict. Option: make a Files section required in every spec. Semantic conflicts without shared files are caught only by the end-of-branch tests after the rebase. (5) Order of work: this row comes after "Swappable methods" batch 2, which moves the method rules out of global/CLAUDE.md into global/methods/my.md and edits my:status. (6) my:handoff launches stages in tmux windows; there is also a roadmap row about launching my:handoff outside tmux."

## Forces

| # | Force | Value | Label | Source or reason |
| --- | --- | --- | --- | --- |
| 1 | Load | 2–3 rows per call. Up to **Max runs** (1–4, default 2) auto runs live at once; each run is 3 stage sessions (plan, code, review) one after another. | stated | User answer; cap from `handoff-state.py start --max`. |
| 2 | Data volume and growth | One list of waiting rows per call, plus one state file per run in `.git/my-handoff/<slug>.json`. Grows with the number of calls. | inferred | `plugins/my/bin/handoff-state.py`. |
| 3 | Latency target | No target. Runs finish when they finish; the user checks later. | stated | User answer. |
| 4 | Availability | A stopped run must not block the others; a stopped run keeps its slot until resumed. The waiting rows must survive the launching session closing, and can be resumed. | stated (survival) / inferred (slot rule) | User answer; `my:status` step 3. |
| 5 | Consistency | Never more than **Max runs** live (the locked `handoff-state.py start` already enforces this). Each listed row starts at most once. A row gated in `## Order of work` never starts before its blocker is finished. | inferred | `handoff-state.py start`; `plugins/my/skills/status/SKILL.md` step 3. |
| 6 | Security and compliance | One user call approves every listed row. Runs act in `auto` or `bypassPermissions` mode within each spec's Delegation section and never push. | stated (one call) / inferred (rest) | User request; `plugins/my/skills/handoff/SKILL.md` "Delegation". |
| 7 | Team and operations | One developer, the only approver, one machine, in tmux. | stated | User answer. |
| 8 | Rate of change | `my:handoff` changes often; "Swappable methods" batch 2 and "Split `my:handoff` by mode" will move its text. | inferred | Git log; `ROADMAP.md`. |
| 9 | Cost | unknown, assumed N rows × 3 stages × 1.5M–8M tokens per stage, no cap. A session that stays open to watch would add idle cost. | assumed | No budget stated; numbers from `plugins/my/skills/handoff/README.md`. |
| 10 | Fixed constraints | Claude Code + tmux. Each stage is its own top-level session (handoff spec D2). Markdown skills plus Python standard-library scripts. No new dependencies without approval. Never push. `my:handoff` rule: "Wait only inside one `handoff-lock.py` command. Never poll another session across tool calls, and never message one." A project without a "Parallel runs" section allows 1 auto run. | inferred | `plugins/my/skills/handoff/SKILL.md` "Rules for every stage" and "Parallel runs". |

## Collapse gate

Three candidates. Forces 1 (2–3 rows, far under 50 requests/s), 3 (no latency target), 4 (no uptime target; a stop may wait for days) and 7 (one developer) would collapse the gate. Force 10 does not: each stage already runs as its own top-level session, and up to 4 runs share one `main`, so the system has more than one process.

- Event-driven: not used. Consumers that keep their own views need data to split; force 2 gives one small queue and one state file per run.
- Separate deployables, each owning its own data: not used. Force 2 gives nothing to split between owners.
- Client-heavy or offline-first: not used. Force 10 has no client; everything runs in local sessions.
- Managed or serverless services: not used. Forces 7 and 10: one machine, local tmux, no remote services.

## Candidates

### Candidate A: simplest design

**Reason:** Always included: the simplest design that could meet the forces.
**Contrast:** vs B: process count, communication (sync vs a 60 s reread), computation (sessions vs a worker); vs C: `contrast rule not met` after return (see C).
**Labels:** none

#### Summary

Shape: simplest design. There is one new command form, `/my:handoff auto rows "<row title>" ...`, plus one queue file at `.git/my-handoff/queue/rows.json` and one new locked subcommand, `handoff-state.py pull`. There is no supervisor and no session that waits. The call judges each row once, in the user's session, using `my:status` steps 4–6, and stores the result as data. It then pulls up to **Max runs** rows and exits. After that, each run that finishes pulls the next waiting row (Option A), and so does each run the user ends by hand. Running the command again with no titles fills any free slots, which is how the user restarts a stalled queue.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| `auto rows` form (new section in `my:handoff`) | Match each title to its spec (`my:status` step 4). Skip and list rows with no `approved` spec or no Delegation section, and rows that already have a state file. Store each row's stage (`code` if the spec has Tasks, `plan` if not), its gates as `after: [slug]`, and `exclusive` when its overlap is unknown. Print file-overlap warnings, which do not block. | none | the user's Claude session; it ends once the first launches are done |
| Queue file `my-handoff/queue/rows.json` | Hold the rows that are waiting | entries: slug, spec, stage, after, exclusive, state (`waiting`/`started`/`skipped` + reason) | file in the git common dir. It sits in a subfolder because `live` and `status-scan.py` count every `my-handoff/*.json` as a run. |
| `handoff-state.py queue add` / `pull --max <n>` | `add`: add entries and drop duplicates. `pull`: pick the first `waiting` entry whose `after` runs are all `finished`. An `exclusive` row starts only when no run is live, and while it runs nothing else is pulled. `pull` then runs the same code as `start`, marks the entry `started`, and prints the slug, spec, stage and slot. | the only writer of the queue | stdlib Python, run under `handoff-lock.py main` |
| Refill hook (one line in two places) | After review sub-step 4 sets `next=finished`, and after "To end an abandoned run": run `pull`, then Launch | none | the run's own review session, or the user's session |
| Existing auto launch and stages | Launch the tmux window. The `run auto` start checks re-check the spec. | `<slug>.json` | as today |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| User → `auto rows` | row titles | sync | — |
| `auto rows` → `status-scan.py`, ROADMAP, specs | read facts | sync | Scan error: stop and write nothing |
| `auto rows` → `queue add` | entries, one locked command | sync | Lock timeout (exit 75): stop and report; the queue is unchanged |
| caller → `pull` | `--max <n>`, with `<n>` read from "Parallel runs" at pull time (1 when there is no section) | sync | Nothing eligible: Finish as normal. Cap refused: the entry stays `waiting`. Lock timeout: print the restart command for the user. |
| caller → Launch | `run auto <stage> <spec>` in a new tmux window | sync | Outside tmux: print the command (the existing fallback). If the window fails, a live state with `next=<stage>` is left and is resumed like a stopped run. |
| `run auto` session → its start checks | spec status, Delegation, Tasks | sync | A spec that changed since the call fails here. The run signals and keeps its slot, like a stop. |

### Candidate B: queue and background workers

**Reason:** Force 4 (availability): the waiting rows must survive the launching session closing, which calls for a durable queue with one owner that starts runs in the background.
**Contrast:** vs A: process count, communication, computation; vs C: process count, communication, computation.
**Labels:** none

#### Summary

Shape: queue and background workers. One command, run in a Claude session, makes every judgment once. It resolves each row's spec, runs start checks 2–4, turns every gate in `## Order of work` into a blocker slug, and lists and skips the rows that fail. It then writes one durable queue file per row, opens a worker window, and ends. The worker is a stdlib Python loop, `handoff-queue.py serve`, not a Claude session. It runs as a single instance under `handoff-lock.py queue --timeout 0`, rereads `.git/my-handoff/*.json` every 60 s, and for each free slot opens a short launcher window that types the existing `/my:handoff auto <stage> <spec>`. The cap and "start at most once" stay with the locked `handoff-state.py start`. The worker writes no git state and holds no copy of the start checks or of Launch.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Enqueue command (`/my:handoff auto queue <rows…>`, and the same command with no rows to resume) | Resolve rows to specs. Run start checks 2–4 and list the skips. Turn each gate into `after: [slug]`; a blocker that is neither queued, nor a run, nor ✅ means skip. Mark unknown overlap `alone`. Pin the spec's blob hash. Open the worker window. | none after it exits | Claude session (the user's) |
| Queue `.git/my-handoff/queue/<slug>.json` | One "wanted" entry per row: spec, stage, `after`, `alone`, file list (a soft signal only), spec hash, launcher mode, `launched_at` | Which rows are wanted, and with which gates | Files, written atomically (temp file, then rename) |
| Worker `handoff-queue.py serve` | Each tick: read `live` and the queue. When a slot is free and an entry is ready, open one launcher. Remove an entry once its state file shows `finished`. Exit when no entry is left. | `launched_at` only, as a hint | Python stdlib process in its own tmux window. Single instance by `flock`. |
| Launcher window | Run the unchanged auto launch: the checks, the locked `start`, then the window for `run auto` | none | Short Claude session in `auto` mode |
| `handoff-state.py start` / `live` | Cap, slot, refusal of a repeat | The run files `<slug>.json` (the existing owner) | Existing script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Enqueue → queue dir | Entry files, under lock `main` | sync | The write fails: report it. No worker is opened. |
| Enqueue → worker | `tmux new-window` running `handoff-lock.py queue --timeout 0 -- handoff-queue.py serve` | async | Exit 75 means a worker already runs, which is fine. No tmux: print the command. |
| Worker → run files | `handoff-state.py live` and `get` each tick | sync (a file read) | An `unreadable` file counts as live, so its slot stays held. The queue may stall until the user fixes it. |
| Worker → launcher | `tmux new-window … claude --permission-mode auto '/my:handoff auto <stage> <spec>'` | async | The window fails to open: keep the entry and retry on the next tick. |
| Launcher → `start` | The locked cap check and write | sync | A cap refusal or a repeat refusal: the entry stays wanted, and the worker retries. `start` makes a double start impossible. |
| Launcher → run window | Launch step 5, unchanged | async | `start` passed but the window failed: the stage's existing stop (row 2) sets `stopped`. The slot stays held, and `auto resume` relaunches the run. |
| Worker → itself | A slot with a launch in flight (`launched_at` under 10 min, no state file yet) counts as used | — | After 10 min with no state file: the entry is marked `launch-failed` and shown to the user. It is not retried. |
| Reboot or tmux server death | The worker dies; the queue files remain | — | The enqueue command with no rows, or `my:status`, sees "entries waiting, `queue` lock free" and starts the worker again. |

### Candidate C: pipeline or batch processing

**Reason:** Force 1 (load): each listed row passes through 3 stages (plan, code, review) in a row, so the work can be modelled as staged batches where each stage owns its output and hands it on.
**Contrast:** vs A: `contrast rule not met` after return. Before dispatch the shapes differed on all four axes; the draft came back with the same process count (no new process), the same data ownership (one queue file written by one script), sync calls, and the same computation (the sessions) as A. vs B: process count, communication, computation.
**Labels:** near-copy of candidate A

#### Summary

Shape: pipeline or batch processing. The user's one call is an **admit** station. It runs every judgment once: it finds each row's spec, checks for `approved` and Delegation, turns `## Order of work` into explicit edges, sorts the rows into normal and solo, and writes a batch manifest. From then on a **mechanical dispatcher** (`handoff-batch.py fill`, stdlib) moves rows into runs. It runs in one locked command at each slot-freeing event, mainly when a review stage writes `next=finished` (Option A, with no supervisor). The difference from the parallel-runs brief's Candidate A is that row choice and gates are compiled into data at admit time, so no stage session needs to judge the roadmap again.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Admit (`/my:handoff auto rows <rows…>`) | Resolve rows (`my:status` steps 4–6), check the spec status and Delegation (start checks 2–4), compile the gates into `after:` edges, mark unknown-overlap rows `solo`, list the skipped rows with a reason, write the manifest, call `fill` once, launch windows, end | none after it writes the manifest | Claude session, the user's call; it never stays open |
| Batch manifest | Waiting rows in order: slug, spec, task doc, mode (plan or code), `after:` edges, `solo`, file list, `max`; each row `waiting`, `started` or `skipped:<reason>` | Which rows wait, their compiled edges, started or skipped | `.git/my-handoff/batch/<id>.json`. It must sit in a subfolder: `live_states()` counts every top-level `*.json` as a live run |
| Dispatcher `handoff-batch.py fill` | While `live < max`: pick the first waiting row whose `after:` blockers are `finished` and whose solo rule passes (a solo row needs 0 live runs; while a solo run is live, nothing else starts). Prefer rows whose files do not touch the live runs' files. Call `start`. Print `slug stage` lines | none (it reads `live`; the manifest owns the rows) | Stdlib script under `handoff-lock.py main` |
| Run state `<slug>.json` | As today | Live or finished, slot, next step | `handoff-state.py` |
| Stage sessions | As today. The review stage's sub-step 4 adds one call to `fill` after `next=finished`, then a Launch for each printed slug | Worktree, branch | Top-level `claude` in tmux |
| Refill hooks | The same `fill` call in "To end an abandoned run", and a `fill` line in the `my:status` report when rows wait | none | Text in `SKILL.md` and `my:status` |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Admit → manifest | Written once, atomically (temp file and rename, as `write_state`) | sync | The write fails: print the error; no row starts |
| Finishing review stage → dispatcher | `handoff-lock.py main -- handoff-batch.py fill` | sync, inside one lock | Lock timeout (75): the run is already finished, the rows stay waiting. Signal "rows wait; run `auto rows resume`" |
| Dispatcher → `handoff-state.py start` | The call goes to the function **directly**, never through `handoff-lock.py main` again: a nested flock on the same file blocks until exit 75. The manifest is marked `started` **after** `start` succeeds | sync, same process | A crash between the two writes repairs itself: the next `fill` gets `refused: a run for <slug> exists`, which it reads as "mark started" |
| Session → tmux (Launch) | One window per printed slug, with `MY_AUTORUN=<new slug>`, not the finishing run's own slug, or the push guard is off | async | Window fails: the row 2 stop on the new run; `auto resume <spec>` launches it |
| User → `auto rows resume <id>` | Calls `fill` again | sync | Used after a crashed finish or a blocker outside the batch that finished |

## Evaluation

### Data ownership

| State | A | B | C |
| --- | --- | --- | --- |
| A run's next step and slot (`<slug>.json`) | `handoff-state.py` (the stages, through it) | `handoff-state.py` | `handoff-state.py` |
| Which rows wait, with their gates | `handoff-state.py queue`/`pull`, the only writer | **two writers**: the enqueue command writes entries; the worker writes `launched_at`, `launch-failed` and removes entries | **two writers**: admit writes the manifest; `fill` marks rows `started` |
| The cap on live runs | `start`'s locked check (inside `pull`) | `start`'s locked check | `start`'s locked check (called by `fill`) |
| The judgment (spec found, gates, overlap) | frozen at call time in the queue | frozen at enqueue time; spec pinned by hash | frozen at admit time |
| Plugin-dir flags and permission mode for later launches | the finishing run's own session (Launch step 3 reads them from `$CLAUDE_PID`) | **nobody**: a Python worker has no Claude process to read them from, so the enqueue must record them | the finishing run's own session |

B's and C's two writers are safe only if every write runs under lock `main`. A has one writer by construction.

### Scenarios

| Scenario | A | B | C |
| --- | --- | --- | --- |
| 1. Normal path: 3 rows, **Max runs** 2 (force 1) | holds: call → `queue add` → `pull` twice → 2 windows; run 1 finishes → `pull` → window 3 | holds; also opens one short Claude launcher session per row | holds, as A |
| 2a. The launching session closes (force 4) | holds: the queue is in `.git/`; refills come from finishing runs | holds | holds |
| 2b. Every live run stops | holds: no slot frees, which is correct because each stop already signals the user; the resumed run refills when it finishes | holds, same | holds, same |
| 2c. A crash between `next=finished` and `pull` | breaks at "caller → `pull`": the slot is free and nothing fills it until another run finishes or the user reruns the command | holds: the next 60 s tick sees the free slot | breaks at "finishing review → dispatcher", as A; `my:status` shows the waiting rows |
| 2d. Reboot or tmux server death | holds: the queue stays; `auto resume` restarts runs, and they refill when they finish | breaks at "Reboot": the worker is gone until the user restarts it | holds, as A |
| 3. `my:handoff` text moves: batch 2, "Split by mode", "Write step 8 whole" (force 8) | partial: the refill line in review sub-step 4 and "To end an abandoned run" must move with that text | holds: no stage text changes | partial: lines in three places, one of them in `my:status`, which batch 2 also edits |
| 4. Data after 3 years (force 2) | holds: estimate 1, 2,340 entries if never pruned, 8 ms per rewrite | holds: entries are removed when finished | holds: one manifest per batch, many small files |
| 5. A spec edited after the call (force 6) | partial: start checks re-check `approved` and Delegation, but new text under the same status runs without a new yes | holds: the pinned hash blocks the row | partial, as A |

### Pre-mortem

**A**, one year after launch:

1. The queue stalled after a crashed finish or an unusual end of a run, and the user found out days later.
2. A rewrite of review step 8 ("Split by mode", "Write step 8 whole") dropped or misplaced the refill line.
3. The `exclusive` rule and missing Files sections made every batch serial, so the feature gave no parallel work and fell out of use. In repos without a "Parallel runs" section, including this one, **Max runs** is 1 anyway.

**B**, one year after launch:

1. The worker died on a reboot or a tmux restart, nobody restarted it, and rows waited for days.
2. Launcher sessions failed again and again: missing `--plugin-dir` flags (no `$CLAUDE_PID` in a Python worker), or a permission prompt in a session nobody watches.
3. Two kinds of process to debug and one leftover launcher window per row; the user turned the worker off.

**C**, one year after launch:

1. The same silent stall as A.
2. Several manifests from several calls competed: `fill` had to read all of them, and their order was unclear.
3. The compiled gates went stale mid-batch, and a row started before a blocker added to the roadmap after the call.

### Comparison

| Force | A | B | C |
| --- | --- | --- | --- |
| 1 Load | meets: one locked `pull` per refill | meets | meets |
| 2 Data volume | meets: estimate 1 | meets | meets |
| 3 Latency | meets: no target | meets | meets |
| 4 Availability | partial: survives a session closing and a reboot; a crashed finish leaves a slot empty | partial: refills after a crash; a reboot stops the worker | partial, as A |
| 5 Consistency | meets: one writer; pick and start in one lock | partial: two writers to the queue | partial: two writers to the manifest |
| 6 Security | partial: no pin on the spec's text | meets: hash pin | partial, as A |
| 7 Team and operations | meets: nothing new to keep alive | fails: a long-lived worker plus launcher sessions for one developer | meets |
| 8 Rate of change | partial: one refill line in text that will move | meets: no stage text changes | partial: three places |
| 9 Cost (assumed) | meets: nothing waits | partial: one extra Claude launcher session per row | meets |
| 10 Fixed constraints | meets: refills are pushed by finishing runs, no polling | partial: a timed reread, outside the rule's letter but needing a rule change | meets |

## Decision

**Candidate A: the finished run refills.** Chosen by the user on 2026-10-13.

- One new form, `/my:handoff auto rows <rows…>`. It judges each row once with the `my:status` rules, lists and skips the rows that cannot start, writes `.git/my-handoff/queue/rows.json`, pulls up to **Max runs** rows and launches them, then ends.
- One new locked subcommand, `handoff-state.py pull --max <n>`. It picks the first ready row and starts it in the same locked command, so the cap holds and each row starts once. The queue has one writer, `handoff-state.py`.
- A refill line where a run finishes (review sub-step 4) and where the user ends a run by hand. Running the command again with no rows fills any free slot.
- Two parts taken from the other candidates:
  - From B: pin each spec's blob hash at call time. A changed spec blocks its row (scenario 5).
  - From C: `my:status` reports waiting rows next to a free slot, so a stall is visible (scenario 2c).

Why the others lost:

- **B lost** on forces 7 and 9: a long-lived worker plus one launcher session per row, for 2–3 rows per call and one developer. Its real gains, refill after a crash and no stage text to change, do not pay for that. Its own weakest point reached the same verdict. It also leaves the plugin-dir flags with no owner.
- **C lost** as a near-copy of A with two writers to its manifest and refill text in three places instead of two. Its `my:status` line is kept in A.

## Reversibility and checks

| Decision | Label | Check |
| --- | --- | --- |
| The queue file's format and location, `.git/my-handoff/queue/rows.json`, outside the folder that `live` and `status-scan.py` read | hard | Estimate 1: size and rewrite time under lock `main`. |
| `handoff-state.py pull`: pick and start in one locked command, as part of the script's interface | hard | Estimate 1 covers the time it holds lock `main`. |
| The judgment is made once, at call time, and stored as data (`after`, `exclusive`, spec hash) | medium | none needed |
| Unknown overlap is a hard block (`exclusive`); file overlap is only a warning | medium | none needed |
| The refill line in review sub-step 4 and "To end an abandoned run" | medium | none needed |
| Spec hash pin; the `my:status` line for waiting rows | cheap | none needed |

Estimate 1, queue file:

```python
"""Estimate 1: size of the queue file and time to rewrite it under lock main."""
import json, time

calls_per_week = 5          # assumed: a busy week of `auto rows` calls
rows_per_call = 3           # force 1, stated: 2-3 rows per call
years = 3                   # force 2 horizon
lock_timeout_s = 90         # handoff-lock.py default timeout

entries = calls_per_week * rows_per_call * 52 * years
entry = {"slug": "start-auto-runs-from-roadmap-rows",
         "spec": "docs/plans/2026-10-13-start-auto-runs-from-roadmap-rows-spec.md",
         "stage": "plan", "after": ["swappable-methods"], "exclusive": False,
         "spec_hash": "0" * 40, "state": "started"}
queue = [dict(entry, slug=f"{entry['slug']}-{i}") for i in range(entries)]

t0 = time.perf_counter()
for _ in range(10):
    text = json.dumps(queue, indent=2)
    json.loads(text)
per_rewrite = (time.perf_counter() - t0) / 10

print(f"inputs: {calls_per_week} calls/week x {rows_per_call} rows x 52 weeks x {years} years")
print(f"formula: entries = calls x rows x weeks; size = len(json); time = dump + load")
print(f"estimate: {entries} entries if never pruned, {len(text)/1024:.0f} KiB, {per_rewrite*1000:.1f} ms per read+rewrite")
print(f"compared to: lock timeout {lock_timeout_s} s -> {lock_timeout_s/per_rewrite:,.0f}x headroom")
```

```text
inputs: 5 calls/week x 3 rows x 52 weeks x 3 years
formula: entries = calls x rows x weeks; size = len(json); time = dump + load
estimate: 2340 entries if never pruned, 728 KiB, 8.2 ms per read+rewrite
compared to: lock timeout 90 s -> 10,940x headroom
```

Not near a limit, so no spike. Pruning finished entries is still worth a line in the spec, to keep the file readable.

## Open for brainstorming

- Force 9 (cost): unknown, assumed N rows × 3 stages × 1.5M–8M tokens per stage, no cap.
- Rows that cannot start: confirm that the command lists them with a reason and skips them, and does not wait for them (description item 2).
- This repo has no "Parallel runs" section, so **Max runs** is 1 here and every call runs its rows one at a time. Does the spec add the section to this repo, or leave that to the user?
- Unknown overlap makes a row `exclusive`, and 6 of the last 13 specs have no Files section. Should a Files section become required in every spec? That is a change to the spec rules (`global/CLAUDE.md`, `my:spec-review`), which batch 2 moves.
- How the user names rows in the call: by title text, by a slug, or by spec path. `ROADMAP.md` rows here have no numbers.
- A gate whose blocker is outside the call and not finished: skip the row with its reason (C's rule, since no finish in this call would wake it), or keep it waiting for a later rerun?
- A crash between `next=finished` and `pull` leaves a slot empty (scenario 2c). Is the `my:status` line plus a rerun of the command enough, or should a run's start also pull, so that any later start repairs it?
- The "Launch from a session outside tmux" row: a refill launched from a session outside tmux prints a command instead of opening a window. Does this row wait for that fix?

## Appendix: candidate drafts

### Candidate A

#### Summary

Shape: simplest design. There is one new command form, `/my:handoff auto rows "<row title>" ...`, plus one queue file at `.git/my-handoff/queue/rows.json` and one new locked subcommand, `handoff-state.py pull`. There is no supervisor and no session that waits. The call judges each row once, in the user's session, using `my:status` steps 4–6, and stores the result as data. It then pulls up to **Max runs** rows and exits. After that, each run that finishes pulls the next waiting row (Option A), and so does each run the user ends by hand. Running the command again with no titles fills any free slots, which is how the user restarts a stalled queue.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| `auto rows` form (new section in `my:handoff`) | Match each title to its spec (`my:status` step 4). Skip and list rows with no `approved` spec or no Delegation section, and rows that already have a state file. Store each row's stage (`code` if the spec has Tasks, `plan` if not), its gates as `after: [slug]`, and `exclusive` when its overlap is unknown. Print file-overlap warnings, which do not block. | none | the user's Claude session; it ends once the first launches are done |
| Queue file `my-handoff/queue/rows.json` | Hold the rows that are waiting | entries: slug, spec, stage, after, exclusive, state (`waiting`/`started`/`skipped` + reason) | file in the git common dir. It sits in a subfolder because `live` and `status-scan.py` count every `my-handoff/*.json` as a run. |
| `handoff-state.py queue add` / `pull --max <n>` | `add`: add entries and drop duplicates. `pull`: pick the first `waiting` entry whose `after` runs are all `finished`. An `exclusive` row starts only when no run is live, and while it runs nothing else is pulled. `pull` then runs the same code as `start`, marks the entry `started`, and prints the slug, spec, stage and slot. | the only writer of the queue | stdlib Python, run under `handoff-lock.py main` |
| Refill hook (one line in two places) | After review sub-step 4 sets `next=finished`, and after "To end an abandoned run": run `pull`, then Launch | none | the run's own review session, or the user's session |
| Existing auto launch and stages | Launch the tmux window. The `run auto` start checks re-check the spec. | `<slug>.json` | as today |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| User → `auto rows` | row titles | sync | — |
| `auto rows` → `status-scan.py`, ROADMAP, specs | read facts | sync | Scan error: stop and write nothing |
| `auto rows` → `queue add` | entries, one locked command | sync | Lock timeout (exit 75): stop and report; the queue is unchanged |
| caller → `pull` | `--max <n>`, with `<n>` read from "Parallel runs" at pull time (1 when there is no section) | sync | Nothing eligible: Finish as normal. Cap refused: the entry stays `waiting`. Lock timeout: print the restart command for the user. |
| caller → Launch | `run auto <stage> <spec>` in a new tmux window | sync | Outside tmux: print the command (the existing fallback). If the window fails, a live state with `next=<stage>` is left and is resumed like a stopped run. |
| `run auto` session → its start checks | spec status, Delegation, Tasks | sync | A spec that changed since the call fails here. The run signals and keeps its slot, like a stop. |

#### Forces

Served:

- 1 (Load): 2–4 runs; a `pull` is one locked command that takes milliseconds.
- 4 (Availability): the queue lives in `.git/`, so it outlives the launching session. A stopped run keeps its slot because `start`'s cap already counts it. Running the command again restarts the queue.
- 5 (Consistency): picking and starting happen in one process under lock `main`. So the cap holds, and an entry moves to `started` exactly once. `start` would replace a `finished` state, so `add` refuses any slug that already has a state file. `after` makes gates hard.
- 6 (Security): the one call approves the listed rows. Each run still checks its own Delegation section.
- 9 (Cost): nothing waits and nothing watches, so there are no idle tokens.
- 10 (Fixed constraints): there is no polling and no messages. Refills are pushed by runs that finish, which fits "wait only inside one lock command".

Sacrificed:

- 5 (Consistency, partly): gates and overlap are fixed at call time. A roadmap edited later is not seen until the next call.
- 8 (Rate of change): the hook sits in review step 8, which "Split by mode" and "Write step 8 whole" will rewrite. That is why it is one line pointing at the script, and why the rules point to `my:status` instead of copying them, since batch 2 edits that skill.
- Throughput: an `exclusive` row runs alone. 6 of the last 13 specs have no Files section, so in this repo many calls will run in series.

#### Hard-to-reverse decisions

- The queue file's format and its location in a subfolder. Both `live` and `status-scan.py` enumerate `*.json` in `my-handoff/`.
- `pull` combines picking and `start` in one locked command, and becomes part of `handoff-state.py`'s interface.
- Judgment happens once at call time and is stored as data (`after`, `exclusive`). The finishing session never reads the roadmap.
- Unknown overlap is a hard block, and file overlap is only a warning. The merge step's rebase, recheck and up to 3 retries absorb collisions on the hot shared files.

#### Numbers it depends on

- At most 4 live runs and about 10 entries per queue. A JSON rewrite under a 90 s lock timeout takes milliseconds.
- Hot files (README, handoff SKILL and README, `global/CLAUDE.md`, docs-layout) each changed in 3–4 of the last 8 merges. The design assumes rebase conflicts on them stay rare enough that `merge_retries ≤ 3` rarely stops a run.
- 7 of 13 specs have a Files section. A pair of rows runs in parallel only when both have one.
- Stage cost of 1.5M–8M tokens (assumed). A refill adds about 3 tool calls to a finished review session's context, which is already cached.

#### Weakest point

Refills ride on other runs' finishes, and nothing watches the queue. If every live run stops, no slot frees and the queue stalls without any signal. Only `my:status` or the user running the command again reveals it. A crash between `next=finished` and `pull` has the same effect: the slot is free but nothing fills it. Gates fixed at call time can go stale. The `exclusive` rule makes this repo mostly serial until specs are required to have a Files section, and adding that rule is a separate edit to the spec rules. The first batch also depends on tmux: if the user calls from a session outside tmux, only printed commands come out until "Launch from a session outside tmux" ships. The cost judgment (no idle watcher) rests on force 9, which is assumed.

### Candidate B

#### Summary

Shape: queue and background workers. One command, run in a Claude session, makes every judgment once. It resolves each row's spec, runs start checks 2–4, turns every gate in `## Order of work` into a blocker slug, and lists and skips the rows that fail. It then writes one durable queue file per row, opens a worker window, and ends. The worker is a stdlib Python loop, `handoff-queue.py serve`, not a Claude session. It runs as a single instance under `handoff-lock.py queue --timeout 0`, rereads `.git/my-handoff/*.json` every 60 s, and for each free slot opens a short launcher window that types the existing `/my:handoff auto <stage> <spec>`. The cap and "start at most once" stay with the locked `handoff-state.py start`. The worker writes no git state and holds no copy of the start checks or of Launch.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Enqueue command (`/my:handoff auto queue <rows…>`, and the same command with no rows to resume) | Resolve rows to specs. Run start checks 2–4 and list the skips. Turn each gate into `after: [slug]`; a blocker that is neither queued, nor a run, nor ✅ means skip. Mark unknown overlap `alone`. Pin the spec's blob hash. Open the worker window. | none after it exits | Claude session (the user's) |
| Queue `.git/my-handoff/queue/<slug>.json` | One "wanted" entry per row: spec, stage, `after`, `alone`, file list (a soft signal only), spec hash, launcher mode, `launched_at` | Which rows are wanted, and with which gates | Files, written atomically (temp file, then rename) |
| Worker `handoff-queue.py serve` | Each tick: read `live` and the queue. When a slot is free and an entry is ready, open one launcher. Remove an entry once its state file shows `finished`. Exit when no entry is left. | `launched_at` only, as a hint | Python stdlib process in its own tmux window. Single instance by `flock`. |
| Launcher window | Run the unchanged auto launch: the checks, the locked `start`, then the window for `run auto` | none | Short Claude session in `auto` mode |
| `handoff-state.py start` / `live` | Cap, slot, refusal of a repeat | The run files `<slug>.json` (the existing owner) | Existing script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Enqueue → queue dir | Entry files, under lock `main` | sync | The write fails: report it. No worker is opened. |
| Enqueue → worker | `tmux new-window` running `handoff-lock.py queue --timeout 0 -- handoff-queue.py serve` | async | Exit 75 means a worker already runs, which is fine. No tmux: print the command. |
| Worker → run files | `handoff-state.py live` and `get` each tick | sync (a file read) | An `unreadable` file counts as live, so its slot stays held. The queue may stall until the user fixes it. |
| Worker → launcher | `tmux new-window … claude --permission-mode auto '/my:handoff auto <stage> <spec>'` | async | The window fails to open: keep the entry and retry on the next tick. |
| Launcher → `start` | The locked cap check and write | sync | A cap refusal or a repeat refusal: the entry stays wanted, and the worker retries. `start` makes a double start impossible. |
| Launcher → run window | Launch step 5, unchanged | async | `start` passed but the window failed: the stage's existing stop (row 2) sets `stopped`. The slot stays held, and `auto resume` relaunches the run. |
| Worker → itself | A slot with a launch in flight (`launched_at` under 10 min, no state file yet) counts as used | — | After 10 min with no state file: the entry is marked `launch-failed` and shown to the user. It is not retried. |
| Reboot or tmux server death | The worker dies; the queue files remain | — | The enqueue command with no rows, or `my:status`, sees "entries waiting, `queue` lock free" and starts the worker again. |

#### Forces

Served:

- 4 (Availability): The waiting rows live in files and the worker lives in its own window, so both survive the launching session closing. A stopped run stays in `live`, so it keeps its slot, and the worker never resumes it.
- 5 (Consistency): `start` remains the only gate for the cap and for "once". A blocker must reach `finished` before its waiter starts. A changed spec hash blocks its row.
- 8 (Rate of change): No stage text changes. Refill happens without editing the review stage's Finish, which batch 2 and "Split `my:handoff` by mode" will move. The only contract is the command line `/my:handoff auto <stage> <spec>`.
- 9 (Cost): Waiting costs no tokens. Each row adds one small launcher session.
- 6 (Security): One call approves the rows that are listed and pinned by hash. Runs keep each spec's Delegation section.

Sacrificed:

- 7 (Team and operations): A new kind of process to keep alive and debug, and one leftover launcher window per row.
- 10 (Fixed constraints): A timed reread of files. The "never poll" rule names stage sessions across tool calls, and its reason is token cost and coupling between sessions. A Python loop is outside the rule's letter, but the rule should say so, in one added sentence. Also needs tmux (see the "outside tmux" row).
- 5, partly: Gates and file lists are frozen at enqueue time. A plan written later can change the overlap, and the worker will not notice.

#### Hard-to-reverse decisions

- Refill is owned by a separate worker, not by the finishing run (the user's Option A).
- The queue file format and the `queue` lock name, which `my:status`/`status-scan.py` will read.
- A policy: unknown overlap means `alone` (a hard block), and a shared file is only a soft signal. In this repo, rows without a Files section then run one at a time.

#### Numbers it depends on

- A 60 s poll against runs of hours (3 stages each): the refill delay is under 2% of a run, with about 600 cheap ticks over 10 hours.
- The `start` critical section takes milliseconds, against the 90 s default lock timeout that other runs' commits wait on.
- Max runs is 1–4 and there are 2–3 rows per call, so at most about 8 tmux windows.
- A launcher reaches `start` in well under 10 min (the threshold for a launch in flight). The `auto` mode flag must not prompt.
- Checked: `handoff-lock.py` makes the lock file descriptor inheritable into the worker, so the worker must spawn with `subprocess`, whose default `close_fds=True` keeps the lock out of children (not `os.system`). Windows are children of the tmux server.

#### Weakest point

The worker buys little over Option A. Durability comes from the queue files, and A needs those too. The worker dies on reboot exactly as a run's window does, so both designs need a manual resume. What the worker adds is refill when a run finishes or is abandoned by an unusual path. In exchange, it is a long-lived process: the thing the parallel-runs brief rejected, and a reading of the "never poll" rule that the rule should state outright. Its "no idle token cost" advantage over a supervisor session rests on force 9, which is `assumed`. The frozen snapshot of gates and overlap can go stale. And the `alone` rule makes most pairs in this repo run one after the other.

### Candidate C

#### Summary

Shape: pipeline or batch processing. The user's one call is an **admit** station. It runs every judgment once: it finds each row's spec, checks for `approved` and Delegation, turns `## Order of work` into explicit edges, sorts the rows into normal and solo, and writes a batch manifest. From then on a **mechanical dispatcher** (`handoff-batch.py fill`, stdlib) moves rows into runs. It runs in one locked command at each slot-freeing event, mainly when a review stage writes `next=finished` (Option A, with no supervisor). The difference from the parallel-runs brief's Candidate A is that row choice and gates are compiled into data at admit time, so no stage session needs to judge the roadmap again.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Admit (`/my:handoff auto rows <rows…>`) | Resolve rows (`my:status` steps 4–6), check the spec status and Delegation (start checks 2–4), compile the gates into `after:` edges, mark unknown-overlap rows `solo`, list the skipped rows with a reason, write the manifest, call `fill` once, launch windows, end | none after it writes the manifest | Claude session, the user's call; it never stays open |
| Batch manifest | Waiting rows in order: slug, spec, task doc, mode (plan or code), `after:` edges, `solo`, file list, `max`; each row `waiting`, `started` or `skipped:<reason>` | Which rows wait, their compiled edges, started or skipped | `.git/my-handoff/batch/<id>.json`. It must sit in a subfolder: `live_states()` counts every top-level `*.json` as a live run |
| Dispatcher `handoff-batch.py fill` | While `live < max`: pick the first waiting row whose `after:` blockers are `finished` and whose solo rule passes (a solo row needs 0 live runs; while a solo run is live, nothing else starts). Prefer rows whose files do not touch the live runs' files. Call `start`. Print `slug stage` lines | none (it reads `live`; the manifest owns the rows) | Stdlib script under `handoff-lock.py main` |
| Run state `<slug>.json` | As today | Live or finished, slot, next step | `handoff-state.py` |
| Stage sessions | As today. The review stage's sub-step 4 adds one call to `fill` after `next=finished`, then a Launch for each printed slug | Worktree, branch | Top-level `claude` in tmux |
| Refill hooks | The same `fill` call in "To end an abandoned run", and a `fill` line in the `my:status` report when rows wait | none | Text in `SKILL.md` and `my:status` |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Admit → manifest | Written once, atomically (temp file and rename, as `write_state`) | sync | The write fails: print the error; no row starts |
| Finishing review stage → dispatcher | `handoff-lock.py main -- handoff-batch.py fill` | sync, inside one lock | Lock timeout (75): the run is already finished, the rows stay waiting. Signal "rows wait; run `auto rows resume`" |
| Dispatcher → `handoff-state.py start` | The call goes to the function **directly**, never through `handoff-lock.py main` again: a nested flock on the same file blocks until exit 75. The manifest is marked `started` **after** `start` succeeds | sync, same process | A crash between the two writes repairs itself: the next `fill` gets `refused: a run for <slug> exists`, which it reads as "mark started" |
| Session → tmux (Launch) | One window per printed slug, with `MY_AUTORUN=<new slug>`, not the finishing run's own slug, or the push guard is off | async | Window fails: the row 2 stop on the new run; `auto resume <spec>` launches it |
| User → `auto rows resume <id>` | Calls `fill` again | sync | Used after a crashed finish or a blocker outside the batch that finished |

#### Forces

Served:

- 1 (Load): 2–3 rows drain through the `max` slots with no idle watcher.
- 4 (Availability): the manifest is on disk and survives the admit session. A stopped run keeps its slot because `fill` reads the same `live` as `start`. The other slots keep refilling.
- 5 (Consistency): the cap and the start happen in one lock. "Each row starts once" comes from the manifest plus `start`'s refusal. Gate edges are checked against `finished`.
- 6 (Security): the one approval is recorded as the manifest's row list. Each `run auto` session still repeats start checks 2–4.
- 9 (Cost): the dispatcher is a script, so zero tokens are spent waiting.
- 10 (Constraints): the dispatcher waits only inside one lock command and never polls.

Sacrificed:

- Throughput under unknown overlap: a solo row runs alone, by design.
- Freshness: the judgment is frozen at admit time. A spec edited or a gate added later is not seen until a resume re-admits.
- 8 (Rate of change): it adds hooks in three places (review sub-step 4, ending an abandoned run, `my:status`), all of them text that batch 2 and "Split `my:handoff` by mode" will move.

#### Hard-to-reverse decisions

- The manifest format and its folder. The live count must keep skipping it.
- Gates are compiled at admit time. A blocker outside the batch that is not `finished` makes admission **skip** the row with its reason, because no finish event would ever wake it. This row itself is gated behind "Swappable methods" batch 2.
- Unknown overlap means `solo`, a hard rule. Known file overlap is only an ordering preference: the merge station's rebase and recheck is the conflict handler.
- One approval covers rows that start hours later.

#### Numbers it depends on

- 2–3 rows per call against **Max runs** 1–4. **This repo has no "Parallel runs" section** in `CLAUDE.md`, and there is no `CLAUDE.local.md`, so `max` is 1 here and the pipeline runs strictly one row at a time until the section is added.
- `fill` takes milliseconds, against the 90 s lock timeout and the 120 s Bash limit. Launches happen outside the lock.
- 6 of the last 13 specs have no Files section, so about half the rows would be solo unless Files becomes required.
- Hot files changed in 3–4 of the last 8 merges, so the ordering preference rarely finds a disjoint row. The rebase at the merge station carries the risk.

#### Weakest point

The design spends its strength on a compile step whose inputs are often missing or go stale. With about half the specs lacking a Files section, `solo` makes the batch mostly serial. Treating known overlap as soft pushes conflicts on the hot files (`SKILL.md`, `global/CLAUDE.md`, `docs-layout.md`) to the merge station, where a rebase conflict is a stop that **keeps its slot**. So one conflict can stall the rest of the batch until the user acts. Refill also depends on every path that ends a run calling `fill`. A crashed finish, an abandoned run, or a blocker outside the batch that finishes leaves rows waiting silently, unless `my:status` shows them, and that adds another edit to a skill that batch 2 is also changing. Admission compiles the gates once, so a spec edited or a gate added mid-batch goes unseen until a resume. Cost (force 9, assumed) is the only assumed force it relies on: it adds no idle session, so the token cost is only the runs themselves.
