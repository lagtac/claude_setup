# Architecture brief: autonomous single-feature run

**Status:** approved, 2026-10-11. Candidate A chosen by the user; brainstorming writes the spec next.

## How to read this brief

| Document | Path | Why you would read it |
| --- | --- | --- |
| **This brief** | `docs/plans/2026-10-11-autonomous-run-architecture.md` | Forces, candidates, evaluation and the chosen design. |
| Handoff skill | `plugins/my/skills/handoff/SKILL.md` | The stage chain this design extends. Its stop points are listed in the Decision section. |
| Handoff spec | `docs/plans/2026-09-21-handoff-spec.md` | D1, D2 and D4: why each stage is its own top-level session, and how a stage signals. Force 10 comes from here. |
| Handoff README | `plugins/my/skills/handoff/README.md` | Stage costs, the source of force 9. |
| Docs layout rule | `global/rules/docs-layout.md` | "One feature, four commits on `main`", steps 9 to 13: merge, fold and `done` marks. Force 5 comes from here. |
| Fold script | `plugins/my/bin/git-fold-fixups.py` | Exit codes 1 and 3, which the run must handle unattended. |
| User settings | `~/.claude/settings.json` (symlink into `global/`) | Allows `Bash(git push:*)` today. See the Decision section. |

The description came from the conversation, not a file: "Autonomous single-feature run in claude-setup: after the user approves a spec, one feature runs plan → code → review → squash-merge → fold → done marks with no user input, never pushing. Builds on my:handoff. Decisions already made by the user: (1) the spec gets a user-approved Delegation section saying what the agent may decide (deps, design-changing findings, failed end-of-branch tests); anything outside it stops and notifies; (2) autonomy starts after spec approval; (3) the agent may squash-merge and fold fixups without a yes, never pushes; (4) new skill vs handoff mode is left open for brainstorming. Parallel features are out of scope for now."

## Forces

| # | Force | Value | Label | Source or reason |
| --- | --- | --- | --- | --- |
| 1 | Load | One feature run at a time. A run has 3 stages (plan, code, review); each stage is one top-level session. | stated | User: orchestrate a single line of work first; parallel features out of scope. |
| 2 | Data volume and growth | Per feature about 4-6 Markdown docs and 4 commits on `main`, plus any run log. Grows linearly with features. | inferred | `global/rules/docs-layout.md`, "One feature, four commits on main". |
| 3 | Latency target | No target. A run finishes when it finishes; the user checks later. | stated | User answer. |
| 4 | Availability | When the run stops for the user, it waits as long as needed (hours or days) in a resumable state. | stated | User answer. |
| 5 | Consistency | `main` may hold a half-finished state between steps (merged but not folded or not marked done) while the run is stopped, as long as the run's recorded state says exactly which step is next. The done marks must cite the squash hash as it is after the fold. Never leave a half-done rebase. | stated | User answer; docs-layout.md steps 12-13; handoff Review stage step 8. |
| 6 | Security and compliance | Sessions run in `auto` or `bypassPermissions` mode and act without asking. The agent may squash-merge to `main` and rewrite its history (fold fixups) unattended. It never pushes. Decisions outside the spec's user-approved Delegation section stop the run and notify. | stated | User answers. |
| 7 | Team and operations | One developer, who is the only approver, on one machine, in tmux. No on-call. | stated | User answer. |
| 8 | Rate of change | The workflow rules change often: handoff amended 2026-09-29 and 2026-09-30; the feature steps moved to docs-layout.md on 2026-10-10. | inferred | Handoff spec amendments; git log commit dc998fb. |
| 9 | Cost | unknown, assumed about 3 stage sessions per feature at 1.5M-8M tokens each, no hard budget. | assumed | No budget stated; numbers from plugins/my/skills/handoff/README.md. |
| 10 | Fixed constraints | Claude Code + tmux. Each stage runs in its own top-level session (handoff spec D2: one session running every stage dropped end-of-branch rules in practice; subagents read no CLAUDE.md and get no Grep/Glob/LSP). Skills are Markdown prompts plus Python standard-library scripts. No new dependencies without approval. Never push. | inferred | docs/plans/2026-09-21-handoff-spec.md Context and D1-D2; memory note on subagent tools; global CLAUDE.md. |

## Collapse gate

Three candidates. Forces 1 (one run at a time), 3 (no latency target), 4 (waits as long as needed) and 7 (one developer) would collapse the gate. Force 10 does not: each stage must run in its own top-level session (handoff spec D2), so the design needs more than one process.

- Event-driven: not used. It would need several consumers of one event; force 1 allows one run.
- Separate deployables, each owning its own data: not used. Force 1 gives one run and no data to split.
- Client-heavy or offline-first: not used. Force 10 has no client; everything runs in local sessions.
- Managed or serverless services: not used. Force 10 is local tmux; the handoff spec notes that cloud sessions cannot message back.

## Candidates

### Candidate A: simplest design

**Reason:** Always included: the simplest design that could meet the forces.
**Contrast:** vs B: process count, sync or async. vs C: process count, where computation runs.
**Labels:** none

#### Summary

Shape: simplest design. This is an `auto` mode inside the existing `my:handoff` chain. The approved spec's **Delegation** section switches it on. The plan, code and review sessions still launch one after another in tmux, with only one alive at a time. The only new rule is that each existing stop point now has a fixed outcome: it consults Delegation, it always runs on its own, or it always stops. Run state is one small file under `.git/`, so git stays the only data store and the run adds no commits on `main`. This leans toward "handoff mode" on open decision (4), but does not settle it: the same rules could live in a thin new skill that calls handoff's stages.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Spec `## Delegation` section | Lists what the agent may decide: deps, design-changing findings, failed end-of-branch tests | The user's grant of authority (committed with the spec) | Markdown file |
| `my:handoff` auto mode (SKILL.md) | Runs each stage. At every stop point it applies the outcome table below instead of always signalling | none | Prompt in a top-level `claude` session, one per stage |
| Run-state file `.git/my-handoff/<slug>.json` | Records the next step: `plan`, `code`, `review`, `merged`, `worktree-removed`, `folded`, `done`, plus the pre-fold HEAD and the stop reason | Where the run is and what comes next | Plain file in the git common dir. It is untracked, so `git status --porcelain` never shows it and no fold is blocked |
| Small stdlib helper (for example `handoff-state.py get/set`) | Writes the state file atomically and reads it | none | Python script in `plugins/my/bin/` |
| `git-fold-fixups.py` | Folds fixups, and refuses when that is unsafe | none (git owns history) | Existing script |
| Signal (tmux ⚠ mark + PushNotification) | Tells the user that the run stopped | none | Existing |

Outcome for each stop point:

| Stop point | Outcome |
| --- | --- |
| Plan-stage design finding / false premise | Consult Delegation ("design-changing findings") |
| New dependency | Consult Delegation ("deps") |
| Failed end-of-branch test | Consult Delegation |
| No end-of-branch checks named | Always stop |
| Test failure that survives systematic debugging | Always stop |
| Weakened or removed assertion | Always stop |
| New Critical finding in the re-review | Always stop |
| "Ready to squash-merge" | Always auto (decision 3) |
| Dirty `<base>` before the fold | Always stop. The state records `merged`, and the fold is next |
| Fold exit 1 / exit 3 | Always stop. Exit 3 records the pre-fold HEAD |
| Busy shared resource / another session's edit | Always stop |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Stage session → next stage session | `tmux new-window … '/my:handoff run <stage> <doc>'` (existing Launch) | sync launch, then the sender finishes | No window opens: the sender prints the fallback command, writes `next=<stage>` and signals |
| Stage session → state file | Writes `next=<step>` before and after each step that changes `main` | sync | Write fails: stop and signal before acting |
| Stage session → Delegation section | Reads it at the start checks and at each consult point | sync | Section missing or unparseable: start check fails, stop |
| Review session → git (`merge --squash`, `worktree remove`, fold, done marks) | Commands, in the order of Review step 8 | sync | A step fails: the state keeps the last completed step. Signal |
| Stopped session → user | ⚠ mark + notification. The session waits in its window | async | Notification dropped (the known case): the ⚠ mark persists |
| User → stopped session | Reply typed in the ⚠ window, or a new `/my:handoff run <stage> <doc>` that reads the state file | sync | The window is gone after a reboot: a new run reads `next` and resumes there |

### Candidate B: queue and background workers

**Reason:** Force 5 (consistency) needs one owner that records exactly which step comes next while a run is stopped; a supervisor session is that owner.
**Contrast:** vs A: process count, sync or async. vs C: sync or async, where computation runs.
**Labels:** none

#### Summary

Shape: queue and background workers. A supervisor session reads one queue: an untracked JSON state file per run. The file lists the steps in order, each with its status and evidence. The supervisor sends each stage (plan, code, review) to a worker. A worker is a fresh top-level `claude` session in its own tmux window, running the existing `/my:handoff run <stage>` steps in a "worker" mode. In worker mode the session neither launches the next stage nor asks for the merge yes. It writes a result file and finishes. The supervisor then runs the steps on `main` itself (squash-merge, worktree remove, fold, done marks) and moves the step pointer forward after each one. It is the only writer of the run state.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Supervisor (`/my:autorun <spec>`, or a `handoff auto` mode) | Takes the next queued step, sends a stage to a worker, or runs a step on `main` itself; checks results against the Delegation section; stops and notifies | The step pointer and run log, written only through the state script | Long-lived top-level Claude session in a tmux window, with a small context |
| Run state script (`autorun-state.py`, Python stdlib) | Atomic write (temp file + rename) of the run file; refuses transitions that are not allowed, for example `fold` before `merge`; prints the next step | `<git-common-dir>/my-runs/<slug>.json`: steps, status, the squash commit's subject, the HEAD before the fold, the decisions it made, the stop reason | Script on PATH (`plugins/my/bin/`) |
| Stage worker | Runs one handoff stage; applies the spec's Delegation section to its own gates; writes one result file | Its worktree and branch while it runs (code and review stages) | Fresh top-level `claude` session in a tmux window, mode `auto` or `bypassPermissions` |
| Result file (outbox) | Carries a worker's outcome: `done`, `blocked <question>` or `failed <reason>`, plus evidence (commits, test counts, review paths) | The outcome of one job | File next to the run file |
| Waiter | Wakes the supervisor when a result file appears or the worker's tmux window closes | none | A `run_in_background` Bash loop (or Monitor) started by the supervisor |
| `git-fold-fixups.py` | Folds fixups safely, or refuses | none | Existing script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Supervisor → Worker | `tmux new-window "claude -n <name> … '/my:handoff run <stage> <doc> --worker <run file>'"` | async | Window fails to open: record `failed` and signal the user |
| Worker → Result file | One JSON or Markdown result, written last | async | Worker dies without writing one: the Waiter sees the window close; the supervisor records `failed: no result` and signals |
| Waiter → Supervisor | Process exit, which wakes the supervisor | async | Supervisor dead: the result file stays; `/my:autorun resume <slug>` reads it |
| Supervisor → State script | Transition request plus evidence | sync | Script refuses: the supervisor stops and signals; it never edits the file by hand |
| Supervisor → git on `main` | `merge --squash`, commit, `worktree remove`, fold, done-mark commit | sync | Merge conflict, fold exit `1` or `3`, dirty tree: record the step as `blocked` with the old HEAD; signal |
| Supervisor → User | tmux `⚠` mark, PushNotification, last output line | async | User away: the run waits in its recorded state, for days if needed |
| User → Supervisor | Answer typed in the supervisor window | sync | none |

### Candidate C: pipeline or batch processing

**Reason:** Force 8 (rate of change) and force 5 (consistency): a Python script sequences headless stage sessions and does the steps on `main` as tested code.
**Contrast:** vs A: process count, where computation runs. vs B: sync or async, where computation runs.
**Labels:** none

#### Summary

Shape: pipeline or batch processing. A Python standard-library driver, `plugins/my/bin/feature-run.py`, runs in one tmux window. It steps through a fixed list: plan session → code session → review session → squash-merge → worktree remove → fold → done-mark session → done-mark commit check. The three judgment stages (plan, code, review) and the short done-mark stage run as headless `claude -p` sessions. They still read the global and project `CLAUDE.md` and call `/my:handoff run <stage> <doc>` in a new "autonomous" variant. Each session ends by writing a result file. The git steps on `main` (merge, `git worktree remove`, `git-fold-fixups.py`, checking the commits) are tested Python, not prompt text. A step's outcome is decided by checking git, never by trusting a session's prose.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| `feature-run.py` driver | Runs the step list in order. Writes the next step to the run file before each step, then checks the step in git after it. Stops and notifies on a gate. | none (reads and writes the run file) | One foreground Python process in a tmux window. It exits when the run stops and starts again with `feature-run.py resume <slug>`. |
| Run file `.git/feature-runs/<slug>.json` | Records the next step, each stage's session id, the HEAD before each step, the squash hash before and after the fold, the stop reason, and the end-of-branch test counts. | Run progress (force 5's "recorded state") | A file inside `.git`. It is untracked, so a rebase never rewrites it and it is never pushed. |
| Stage sessions (plan, code, review) | The work that needs judgment: write and review the plan, implement the plan, run the reviews and the one fix round. Each applies the spec's **Delegation** section. | The branch, the worktree and the docs they write | `claude -p --permission-mode auto --plugin-dir … --disallowedTools "Bash(git push:*)"` |
| Stage result file `.git/feature-runs/<slug>-<stage>.json` | Says `done` or `gate`, plus a reason, the files written and, for the review stage, the squash commit message. | One stage's outcome | Written by the session, read by the driver |
| Done-mark session | Writes the project's `done` marks (Status lines, roadmap row, changelog) from the post-fold squash hash that the driver passes in. | none | A short `claude -p` session |
| Notifier | `tmux rename-window -t <pane> "<slug> ⚠"`, one line printed, and the terminal bell | none | A function inside the driver |
| Driver tests | A fixture repo plus a fake `claude` stub on `PATH`. They exercise every step, every stop and every resume. | none | `plugins/my/tests/test_feature_run.py` |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Driver → stage session | A subprocess call with the prompt `/my:handoff run <stage> <doc> --autonomous` | sync (the driver waits for the exit) | A non-zero exit, a missing result file or a failed git check stops the run. The run file keeps `next = <same stage>`, and the driver notifies. |
| Stage session → driver | The result file | sync, read after exit | An invalid file is treated as a gate. |
| Driver → git (merge, worktree remove) | `git merge --squash` and `git commit -F <message from the review result>` | sync | Before the merge, the driver checks that `main` is clean. If the merge fails, it runs `git merge --abort` and `git reset --merge`, then stops. |
| Driver → `git-fold-fixups.py` | A subprocess call | sync | Exit 1 (refused, nothing changed): stop. Exit 3: record the old HEAD in the run file, then stop. The script already aborts a failed rebase, so no rebase is ever left half done. |
| Driver → done-mark session | The squash hash after the fold | sync | The driver checks that the new commit touches only `.md` files and cites that hash. Otherwise it stops. |
| User → driver | `feature-run.py resume <slug> [--accept\|--retry]` after settling a gate, often in an interactive `claude --resume <session id>` | async (hours to days) | Not applicable |

## Evaluation

### Data ownership

- **A:** one owner per piece of state. The run-state file has one writer at a time, because only one stage session is alive. The spec owns the Delegation grant. Nothing owns "never push" except the prompt.
- **B:** flag. The Delegation decision has two owners: the worker applies it to its own gates, and the supervisor checks results against it again.
- **C:** one owner per piece of state. The driver writes the run file; each session writes only its own result file; the review session writes the squash message and the driver commits it.

### Scenarios

| Scenario | A | B | C |
| --- | --- | --- | --- |
| Normal path: one feature, plan to `done` marks | holds | holds | uncertain: breaks at "Driver → stage session" if `auto` mode under `claude -p` denies `git worktree add`, the rebase or parallel `Agent` calls. The memory note `headless-skill-testing` records that `bypassPermissions` is blocked under `-p` and that denials can be silent. |
| A session dies after the squash-merge, before the fold | breaks at "User → stopped session": a new `/my:handoff run review` fails the start checks, because the worktree is already removed. Needs a resume path that reads the state file. | breaks at "Supervisor → Worker" for a stopped stage: a fresh worker must restart on an existing branch, which the start checks refuse. The steps on `main` resume from the state file. | holds for the steps on `main`: the driver resumes from its file. A crashed stage needs the same restart path as B. |
| A gate that the Delegation section does not cover | holds: the session stops in its window; the user answers there and it goes on. | partial: the user answers in the supervisor, and a fresh worker restarts with the answer but no memory. | partial: the user runs `claude --resume <id>` interactively, then `feature-run.py resume`. |
| The most frequent change: a workflow rule changes (force 8) | holds: edit `SKILL.md` and `docs-layout.md` only. | partial: the steps on `main` are copied into the supervisor and drift from handoff's Review step 8. | partial: the steps are tested code, but a second copy of handoff's prose. |
| Data after 3 years (force 2) | holds: one untracked state file per feature under `.git/`. | holds | holds |
| Abuse: the model pushes, or goes past Delegation | breaks at "Review session → git": `~/.claude/settings.json` allows `Bash(git push:*)` and no deny rule exists; the gated session judges its own Delegation. | breaks in the same place, in the supervisor. | holds for push: `--disallowedTools` plus a driver with no push code. Delegation stays self-judged. |

### Pre-mortem

- **A:** (1) a session talked itself past a gate that Delegation did not cover; (2) an unattended push or a bad fold happened, with no guard outside the model; (3) resuming after a crash failed at the start checks.
- **B:** (1) the supervisor's copy of the steps on `main` drifted from handoff; (2) a worker stuck at a permission prompt was never noticed, because handoff forbids polling; (3) the restart path for stopped stages broke under a rule change.
- **C:** (1) silent permission denials under `-p` skipped a review while every git check passed; (2) the driver and handoff's prose drifted; (3) settling a gate with two tools was so awkward that runs were abandoned.

### Comparison

| Force | A | B | C |
| --- | --- | --- | --- |
| 1 Load | meets: one chain, one state file | meets | meets |
| 2 Data volume | meets | meets | meets |
| 3 Latency | meets: no target | meets | meets |
| 4 Availability | partial: waits in a live window; resume after a reboot needs a new path | partial: needs a worker restart path | meets: a stop is a process exit plus a file |
| 5 Consistency | meets: the state file names the next step; the fold runs before the `done` marks | meets: one writer, transitions checked by a script | meets: the next step is written before each step |
| 6 Security | partial: push and Delegation enforced by the prompt; fixable with a deny rule | partial: same | meets for push; partial for Delegation |
| 7 Team and operations | meets: one window per gate, as today | partial: two windows to read per stop | partial: two tools per gate; headless sessions show nothing |
| 8 Rate of change | meets: one place to edit | fails: a second copy of the steps on `main` | partial: tested, but a second copy |
| 9 Cost (assumed) | meets: 3 sessions | partial: 3 sessions plus a supervisor | partial: 4 sessions |
| 10 Fixed constraints | meets | meets | partial: relies on `claude -p`, unproven for these stages |

## Decision

**Candidate A: an auto mode for the `my:handoff` chain**, chosen by the user on 2026-10-11. The plan, code and review sessions still launch one after another in tmux, one alive at a time. The approved spec's **Delegation** section switches the mode on. Each stop point of handoff gets a fixed outcome: consult Delegation, always go on, or always stop (the outcome table is in A's draft in the appendix). The review session runs the squash-merge, the worktree removal, the fold and the `done` marks unattended, and never pushes. A small state file under the git common directory records the next step, so a stopped run resumes at the right place.

Why: it is the smallest change; it keeps the one-window way of answering a gate; it keeps one copy of the steps; it scored best on forces 7 and 8. Its two failures are both fixable inside A, and the spec must fix them:

1. **Push guard.** Add a real deny rule for `git push`. Today `~/.claude/settings.json` allows it and `plugins/my/settings.json` does not exist.
2. **Resume path.** A new run of a stage must read the state file and continue, instead of failing the start checks.

- **B lost** because it adds a standing session and a second copy of the steps on `main`, and it needs the same restart path as A, for little gain over A's state file.
- **C lost** because its main gain, tested git steps, depends on headless `claude -p` sessions whose permission behaviour is unproven for worktrees, rebases and parallel reviews. A silent denial there would skip a review unseen. Its push guard (`--disallowedTools`) is the one idea worth carrying into A, as a deny rule.

## Reversibility and checks

| Decision | Label | Check |
| --- | --- | --- |
| The Delegation section's format, carried by every future spec | hard | no quantity to check: it is a format, and its risk is wording, not size. |
| Unattended squash-merge and fold, which rewrite local `main` | hard | no quantity to check: the fold touches the few commits after the spec commit; recovery is through the reflog and the recorded pre-fold HEAD. |
| The state file's location (`.git/`) and format | medium | none |
| A mode of handoff versus a thin new skill | medium | none |

No estimate scripts: no `hard` decision depends on a load, storage, cost or latency number. No spike proposed: the only decision tied to an assumed force (cost) has no experiment that can answer it.

## Open for brainstorming

- Force 9 (cost): unknown, assumed about 3 stage sessions per feature at 1.5M-8M tokens each, with no budget stop. Should a run have a token or time cap?
- Whether a `deny` rule for `Bash(git push:*)` holds in `auto` and `bypassPermissions` modes, and where it lives (user settings, project settings or the plugin). This is testable; the plan must test it before the mode ships.
- The Delegation section's format: closed lists (named allowed dependencies, which tests may fail) versus prose.
- Open decision (4) from the description: an auto mode of `my:handoff`, or a thin new skill that calls handoff's stages.
- The resume path: how a stage started again reads the state file, and which start checks it skips.
- The outcome for each stop point. The table in candidate A's draft (appendix) is a subagent's proposal; the user has not reviewed its rows, for example "failed end-of-branch test → consult Delegation" or "no end-of-branch checks named → always stop".
- The Medium entry point. A Medium change enters at the code stage with a spec that has a Tasks section. Its `approved` status is committed as a fixup and folded by hand today. Does the auto mode cover that path, and who folds?

## Appendix: candidate drafts

### Candidate A

#### Summary

Shape: simplest design. This is an `auto` mode inside the existing `my:handoff` chain. The approved spec's **Delegation** section switches it on. The plan, code and review sessions still launch one after another in tmux, with only one alive at a time. The only new rule is that each existing stop point now has a fixed outcome: it consults Delegation, it always runs on its own, or it always stops. Run state is one small file under `.git/`, so git stays the only data store and the run adds no commits on `main`. This leans toward "handoff mode" on open decision (4), but does not settle it: the same rules could live in a thin new skill that calls handoff's stages.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Spec `## Delegation` section | Lists what the agent may decide: deps, design-changing findings, failed end-of-branch tests | The user's grant of authority (committed with the spec) | Markdown file |
| `my:handoff` auto mode (SKILL.md) | Runs each stage. At every stop point it applies the outcome table below instead of always signalling | none | Prompt in a top-level `claude` session, one per stage |
| Run-state file `.git/my-handoff/<slug>.json` | Records the next step: `plan`, `code`, `review`, `merged`, `worktree-removed`, `folded`, `done`, plus the pre-fold HEAD and the stop reason | Where the run is and what comes next | Plain file in the git common dir. It is untracked, so `git status --porcelain` never shows it and no fold is blocked |
| Small stdlib helper (for example `handoff-state.py get/set`) | Writes the state file atomically and reads it | none | Python script in `plugins/my/bin/` |
| `git-fold-fixups.py` | Folds fixups, and refuses when that is unsafe | none (git owns history) | Existing script |
| Signal (tmux ⚠ mark + PushNotification) | Tells the user that the run stopped | none | Existing |

Outcome for each stop point:

| Stop point | Outcome |
| --- | --- |
| Plan-stage design finding / false premise | Consult Delegation ("design-changing findings") |
| New dependency | Consult Delegation ("deps") |
| Failed end-of-branch test | Consult Delegation |
| No end-of-branch checks named | Always stop |
| Test failure that survives systematic debugging | Always stop |
| Weakened or removed assertion | Always stop |
| New Critical finding in the re-review | Always stop |
| "Ready to squash-merge" | Always auto (decision 3) |
| Dirty `<base>` before the fold | Always stop. The state records `merged`, and the fold is next |
| Fold exit 1 / exit 3 | Always stop. Exit 3 records the pre-fold HEAD |
| Busy shared resource / another session's edit | Always stop |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Stage session → next stage session | `tmux new-window … '/my:handoff run <stage> <doc>'` (existing Launch) | sync launch, then the sender finishes | No window opens: the sender prints the fallback command, writes `next=<stage>` and signals |
| Stage session → state file | Writes `next=<step>` before and after each step that changes `main` | sync | Write fails: stop and signal before acting |
| Stage session → Delegation section | Reads it at the start checks and at each consult point | sync | Section missing or unparseable: start check fails, stop |
| Review session → git (`merge --squash`, `worktree remove`, fold, done marks) | Commands, in the order of Review step 8 | sync | A step fails: the state keeps the last completed step. Signal |
| Stopped session → user | ⚠ mark + notification. The session waits in its window | async | Notification dropped (the known case): the ⚠ mark persists |
| User → stopped session | Reply typed in the ⚠ window, or a new `/my:handoff run <stage> <doc>` that reads the state file | sync | The window is gone after a reboot: a new run reads `next` and resumes there |

#### Forces

Served:

- 1 (Load): one feature, one line of sessions, one state file.
- 4 (Availability): a stop is a live window plus a state file that survives a reboot. Resuming needs no extra service.
- 5 (Consistency): the state names the exact next step between merge, worktree removal, fold and done marks. The done marks run only after `folded` and read the squash hash after the fold. Fold exit 3 always stops, so a half-done rebase never continues unattended.
- 7 (Team): no daemon or supervisor. tmux plus Markdown, which the user already runs.
- 8 (Rate of change): the change is one table plus one Delegation check. Most of the rules stay in SKILL.md and docs-layout.md, where they already change often.
- 10 (Fixed constraints): one top-level session per stage. Only stdlib Python. No new dependency.

Sacrificed:

- 6 (Security): the agent itself enforces both Delegation and "never push". Nothing outside it checks them.
- 3 (Latency): every stop waits for the user. Nothing retries around it.
- 2 (Data volume): the state file is not committed, so the run leaves no lasting record beyond the commits and the review reports.

#### Hard-to-reverse decisions

- The squash-merge and the fold rewrite local `main` unattended. They are recoverable through the reflog and the recorded pre-fold HEAD, but that is manual work.
- The Delegation section's wording becomes a contract that every future spec carries. Changing its keys later means editing approved specs.
- The state lives under `.git/`. It is invisible to review and lost if the repo is cloned again. Moving it into a tracked file later changes the four-commit count.

#### Numbers it depends on

- 3 stage sessions per feature at 1.5M-8M tokens each (assumed, force 9). That is about 5-25M tokens per unattended run, with no budget stop.
- 1 live session at a time, compared with 0 locks: the design has no locking because force 1 allows only one run.
- 4 commits on `main` per Large feature. The state file adds 0.
- About 11 stop points. 3 consult Delegation, 1 is auto, and the rest always stop.

#### Weakest point

The session that a gate holds back is the same session that reads a prose Delegation section and decides whether it may go on. No outside check enforces that decision. "Never push" is also enforced by the prompt alone. `~/.claude/settings.json` *allows* `Bash(git push:*)`. `plugins/my/settings.json`, which the project's CLAUDE.md describes as the deny list, does not exist. Under `bypassPermissions`, nothing stops a push the model decides to make, so a real deny rule would be needed. Whether `bypassPermissions` honours that rule is unverified. The design also leans on the assumed cost (force 9): with no budget stop, a run that loops in systematic debugging can burn tokens until it stops itself. Last, the state file sits outside the tree, so the user cannot see why a run stopped without opening it or the ⚠ window. If the user edits `main` by hand while a run is stopped, the recorded `next` step can go stale without anyone noticing.

### Candidate B

#### Summary

Shape: queue and background workers. A supervisor session reads one queue: an untracked JSON state file per run. The file lists the steps in order, each with its status and evidence. The supervisor sends each stage (plan, code, review) to a worker. A worker is a fresh top-level `claude` session in its own tmux window, running the existing `/my:handoff run <stage>` steps in a "worker" mode. In worker mode the session neither launches the next stage nor asks for the merge yes. It writes a result file and finishes. The supervisor then runs the steps on `main` itself (squash-merge, worktree remove, fold, done marks) and moves the step pointer forward after each one. It is the only writer of the run state.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Supervisor (`/my:autorun <spec>`, or a `handoff auto` mode) | Takes the next queued step, sends a stage to a worker, or runs a step on `main` itself; checks results against the Delegation section; stops and notifies | The step pointer and run log, written only through the state script | Long-lived top-level Claude session in a tmux window, with a small context |
| Run state script (`autorun-state.py`, Python stdlib) | Atomic write (temp file + rename) of the run file; refuses transitions that are not allowed, for example `fold` before `merge`; prints the next step | `<git-common-dir>/my-runs/<slug>.json`: steps, status, the squash commit's subject, the HEAD before the fold, the decisions it made, the stop reason | Script on PATH (`plugins/my/bin/`) |
| Stage worker | Runs one handoff stage; applies the spec's Delegation section to its own gates; writes one result file | Its worktree and branch while it runs (code and review stages) | Fresh top-level `claude` session in a tmux window, mode `auto` or `bypassPermissions` |
| Result file (outbox) | Carries a worker's outcome: `done`, `blocked <question>` or `failed <reason>`, plus evidence (commits, test counts, review paths) | The outcome of one job | File next to the run file |
| Waiter | Wakes the supervisor when a result file appears or the worker's tmux window closes | none | A `run_in_background` Bash loop (or Monitor) started by the supervisor |
| `git-fold-fixups.py` | Folds fixups safely, or refuses | none | Existing script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Supervisor → Worker | `tmux new-window "claude -n <name> … '/my:handoff run <stage> <doc> --worker <run file>'"` | async | Window fails to open: record `failed` and signal the user |
| Worker → Result file | One JSON or Markdown result, written last | async | Worker dies without writing one: the Waiter sees the window close; the supervisor records `failed: no result` and signals |
| Waiter → Supervisor | Process exit, which wakes the supervisor | async | Supervisor dead: the result file stays; `/my:autorun resume <slug>` reads it |
| Supervisor → State script | Transition request plus evidence | sync | Script refuses: the supervisor stops and signals; it never edits the file by hand |
| Supervisor → git on `main` | `merge --squash`, commit, `worktree remove`, fold, done-mark commit | sync | Merge conflict, fold exit `1` or `3`, dirty tree: record the step as `blocked` with the old HEAD; signal |
| Supervisor → User | tmux `⚠` mark, PushNotification, last output line | async | User away: the run waits in its recorded state, for days if needed |
| User → Supervisor | Answer typed in the supervisor window | sync | none |

#### Forces

Served:

- 5 (Consistency): there is one writer and one recorded pointer. Before a step on `main` starts, the run file records `started` plus evidence (HEAD before the fold, the squash commit's subject). A resume therefore knows exactly which step is next. The done marks find the squash commit by its recorded subject after the fold, not by its old hash. A rebase still in progress on resume is a stop, never a guess.
- 4 (Availability): the state lives on disk, outside the worktree and outside tracked history. It survives a session dying, the tmux server ending or a reboot, and a resume takes one command.
- 10 (Fixed constraints): each stage is still its own top-level session (D2), and no new dependencies are needed.
- 6 (Security): every decision outside the Delegation section stops the run at one place. The run log records which delegated decisions were taken and why.
- 1 (Load): one run, one queue, no locking between runs.

Sacrificed:

- 8 (Rate of change): the steps on `main` move out of handoff's Review stage step 8 into the supervisor. Unless both point at one shared section, the two copies will drift. That is another file to edit at each amendment of the rules.
- 9 (Cost): the supervisor adds one session per run. It is idle while waiting, but every wake after the one-hour cache expiry rereads its context.
- 7 (Operations): the user has two windows to read per stop (the supervisor and the worker that asked), not one.

#### Hard-to-reverse decisions

- Run state lives untracked in the git common dir, not in `docs/plans/`. This keeps the four-commit rule and the fold clean, but leaves no record in history. The run log must be copied into the done mark if a record is wanted.
- The worker contract: the result file's schema and the meaning of `--worker`. Every handoff stage depends on it.
- The supervisor, not the review worker, owns merge, fold and done marks. This partly reverses D2's "review session squash-merges".
- A blocked job is re-run as a fresh worker that gets the user's answer in its prompt. Nothing resumes the old session, so each stage must be able to restart on an existing branch and worktree. Today's start checks refuse that.

#### Numbers it depends on

- 3 worker sessions per run at 1.5M-8M tokens each (assumed), against a supervisor of under 150k context.
- At most about 10 supervisor wakes per run (3 results plus stops). Each wake after an hour costs one full reread of under 150k, under 2% of the stage costs.
- One writer to one state file. Atomic rename makes torn writes impossible at this rate (a few writes per hour).
- Up to 5 steps on `main` after the review, each recorded before and after it runs.

#### Weakest point

The supervisor is a standing session. D1 rejected a standing worker because it carries context from one feature into the next. Here the supervisor lives for only one run, but a stop that lasts days still leaves it with an expired cache. Rereading the state file in a fresh `resume` session would do equally well, which suggests the supervisor need not be a session at all. A stdlib Python loop could own the queue, but it could not judge "is this inside the Delegation section". That judgment is then pushed into the workers, and the supervisor becomes mostly bookkeeping.

The second weakness is that the design depends on workers that can restart. A blocked code or review stage has to resume on an existing branch, with a new prompt and no memory of why it stopped. The current start checks forbid exactly this, so they need a new "resume" path. That path is most likely to break as the rules keep changing (force 8).

The cost figures rest on the assumed force 9. Detecting a hung worker is also weak. A worker waiting at a permission prompt never writes a result and never closes its window. Only a check of `ListAgents` on a timer catches it, and the handoff rules forbid that kind of polling.

### Candidate C

#### Summary

Shape: pipeline or batch processing. A Python standard-library driver, `plugins/my/bin/feature-run.py`, runs in one tmux window. It steps through a fixed list: plan session → code session → review session → squash-merge → worktree remove → fold → done-mark session → done-mark commit check. The three judgment stages (plan, code, review) and the short done-mark stage run as headless `claude -p` sessions. They still read the global and project `CLAUDE.md` and call `/my:handoff run <stage> <doc>` in a new "autonomous" variant. Each session ends by writing a result file. The git steps on `main` (merge, `git worktree remove`, `git-fold-fixups.py`, checking the commits) are tested Python, not prompt text. A step's outcome is decided by checking git, never by trusting a session's prose.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| `feature-run.py` driver | Runs the step list in order. Writes the next step to the run file before each step, then checks the step in git after it. Stops and notifies on a gate. | none (reads and writes the run file) | One foreground Python process in a tmux window. It exits when the run stops and starts again with `feature-run.py resume <slug>`. |
| Run file `.git/feature-runs/<slug>.json` | Records the next step, each stage's session id, the HEAD before each step, the squash hash before and after the fold, the stop reason, and the end-of-branch test counts. | Run progress (force 5's "recorded state") | A file inside `.git`. It is untracked, so a rebase never rewrites it and it is never pushed. |
| Stage sessions (plan, code, review) | The work that needs judgment: write and review the plan, implement the plan, run the reviews and the one fix round. Each applies the spec's **Delegation** section. | The branch, the worktree and the docs they write | `claude -p --permission-mode auto --plugin-dir … --disallowedTools "Bash(git push:*)"` |
| Stage result file `.git/feature-runs/<slug>-<stage>.json` | Says `done` or `gate`, plus a reason, the files written and, for the review stage, the squash commit message. | One stage's outcome | Written by the session, read by the driver |
| Done-mark session | Writes the project's `done` marks (Status lines, roadmap row, changelog) from the post-fold squash hash that the driver passes in. | none | A short `claude -p` session |
| Notifier | `tmux rename-window -t <pane> "<slug> ⚠"`, one line printed, and the terminal bell | none | A function inside the driver |
| Driver tests | A fixture repo plus a fake `claude` stub on `PATH`. They exercise every step, every stop and every resume. | none | `plugins/my/tests/test_feature_run.py` |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Driver → stage session | A subprocess call with the prompt `/my:handoff run <stage> <doc> --autonomous` | sync (the driver waits for the exit) | A non-zero exit, a missing result file or a failed git check stops the run. The run file keeps `next = <same stage>`, and the driver notifies. |
| Stage session → driver | The result file | sync, read after exit | An invalid file is treated as a gate. |
| Driver → git (merge, worktree remove) | `git merge --squash` and `git commit -F <message from the review result>` | sync | Before the merge, the driver checks that `main` is clean. If the merge fails, it runs `git merge --abort` and `git reset --merge`, then stops. |
| Driver → `git-fold-fixups.py` | A subprocess call | sync | Exit 1 (refused, nothing changed): stop. Exit 3: record the old HEAD in the run file, then stop. The script already aborts a failed rebase, so no rebase is ever left half done. |
| Driver → done-mark session | The squash hash after the fold | sync | The driver checks that the new commit touches only `.md` files and cites that hash. Otherwise it stops. |
| User → driver | `feature-run.py resume <slug> [--accept\|--retry]` after settling a gate, often in an interactive `claude --resume <session id>` | async (hours to days) | Not applicable |

#### Forces

Served:

- 8 (rate of change): The order of steps and the git operations are code with tests. A rule change in `docs-layout.md` or handoff becomes a code diff that a test breaks on, not prose drift inside a long session.
- 5 (consistency): The next step is written before it runs. Each step can be checked in git (is the squash commit there, is HEAD past the fold). The fold runs before the done marks by construction.
- 4 (availability): The driver holds no memory between steps. A stop is a process exit with a file left behind, so it can wait any length of time.
- 6 (security): Push is blocked twice: the driver contains no push code, and every session gets `--disallowedTools`. Delegation judgment stays with the sessions. The driver cannot widen it.
- 10 (fixed constraints): Each stage is its own top-level session. The script uses the standard library only.

Sacrificed:

- 7 (operations): `claude -p` has no `AskUserQuestion`. To settle a gate, the user must resume the session id interactively, then rerun the driver. That is two tools where handoff had one window.
- 8, in part: Two copies of the step sequence now exist, handoff's prose and the driver. Without discipline they drift.
- Visibility: headless sessions show nothing in tmux while they run. Progress is visible only through a `--output-format stream-json` log file.

#### Hard-to-reverse decisions

- The run file format and its location inside `.git`. A changed format makes old stopped runs unresumable.
- The contract between the stage result file and handoff (`--autonomous` writes a file instead of signalling). Handoff's manual mode and autonomous mode must both keep it.
- The driver, not a session, owns squash, fold and commit. Moving that back into prompts later means rewriting both.
- The squash commit message is written by the review session and committed by the driver.

#### Numbers it depends on

- 3 stage sessions plus 1 short done-mark session per run, each 1.5M-8M tokens (assumed). This is about 5-25M tokens per feature, with no budget to stop it.
- One run at a time. A single run file, with no locking beyond a check that the file exists.
- A test suite under 1 minute with a stubbed `claude`, against about 15 stop and resume paths.
- The fold touches about 3-6 commits between the spec commit and HEAD.

#### Weakest point

Headless `claude -p` is a different runtime from the interactive sessions that handoff was proven on. The memory note `headless-skill-testing` records that `bypassPermissions` is blocked by the safety classifier under `-p`. It also records that permission denials can be silent, and that a denied read made the model improvise while every structural check still passed. If `auto` mode in `-p` also refuses `git rebase`, `git worktree add` or the parallel review `Agent` calls, the pipeline stalls or, worse, quietly does less. Then the driver's git checks are the only guard, and they cannot see a skipped review. Second, the done marks and the Delegation judgment differ per project, so they stay in prompts. The tested-code gain covers only merge, remove and fold, about a quarter of the risky steps. The cost force is assumed: about 4 sessions per feature with no budget cap could surprise the user.
