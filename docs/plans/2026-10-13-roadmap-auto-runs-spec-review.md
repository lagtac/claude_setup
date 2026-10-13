# Review: docs/plans/2026-10-13-roadmap-auto-runs-spec.md

**Status:** review of docs/plans/2026-10-13-roadmap-auto-runs-spec.md, 2026-10-13. Problematic: Candidate A is the right design, but the rules for the queue's walk and pruning (D2, D4, D5) can stall the queue forever, and two Critical findings need decisions before a plan. Answered by the second version of the spec, committed with this review: four editorial fixes, and eight design findings decided by the user.

## Spec Summary

The spec adds `/my:handoff auto rows <n> ...`. The command judges each roadmap row once, commits the specs' `approved` edits, writes a queue file under the git common dir, and starts rows with a new locked `handoff-state.py pull`. Each finishing auto run, and each run the user ends, runs `pull` again to fill its slot. `my:status` shows the queue. A Files section becomes a spec rule, and `kit:setup` offers the "Parallel runs" section. The work ships as three batches.

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
| --- | --- | --- | --- |
| `auto rows` form in `my:handoff` | The judgment made at call time (skip reasons, `stage`, `after`, `exclusive`, the overlap warning). The D3 commits of `approved` edits. The first launches. | `status-scan.py`, `ROADMAP.md`, the specs, `git-fold-fixups.py`, `locked-commit.py`, `handoff-state.py live`, `queue add` and `pull`, Launch | New, inside existing `plugins/my/skills/handoff/SKILL.md:26` (Forms) |
| Queue file `my-handoff/queue/rows.json` | The entries: `row`, `slug`, `spec`, `stage`, `after`, `exclusive`, `spec_hash`, `state`, `reason`. It is the **only** home of `exclusive` and of `skipped`. | `handoff-state.py` as its only writer | New. The subfolder claim holds: `handoff-state.py:176-187` and `status-scan.py:197` read only `my-handoff/*.json` |
| `handoff-state.py queue add` | Appending entries. Pruning every entry that is not `waiting`. Refusing an invalid entry. Detecting a duplicate. | Lock `main`, taken by the caller | New, beside `handoff-state.py:201` |
| `handoff-state.py pull --max <n>` | The walk rules 1 to 6: spec hash, failed blocker, ready, exclusive, cap, start. Marking entries `started` or `skipped`. | `start()` in the same process, the state files, `git hash-object`, lock `main` taken by the caller | New. Reuses `start()` at `handoff-state.py:201-223` |
| Run state files `my-handoff/<slug>.json` | `next`, `stopped`, `slot` and the other run fields. `exclusive` is **not** among them. | `handoff-state.py set` and `start` | Existing, `handoff-state.py:77-78,116-141` |
| `handoff-lock.py main` | Mutual exclusion for `queue add`, `pull` and the parallel commits | `flock` on `my-handoff/locks/main.lock` | Existing, `handoff-lock.py:1-27` |
| Refill hook | Running `pull` and Launch after a finish, and signalling a refill failure | `pull`, Launch, the review session's own flags and mode | New text at existing `SKILL.md:871-875` (review sub-step 4) and `SKILL.md:349-357` (To end an abandoned run) |
| Launch | Opening a tmux window with `MY_AUTORUN=<slug>`, or falling back | `$TMUX`, the permission mode, `$CLAUDE_PID` | Existing, `SKILL.md:255-316` |
| `status-scan.py` `queue` block | Printing the `waiting` and `skipped` entries | The queue file | New block in existing `status-scan.py:307-315` |
| `my:status` report lines | The "rows wait and slots are free" item, and one line per waiting or skipped row | The `queue` and `runs` blocks, **Max runs** from step 3 | New lines in existing `plugins/my/skills/status/SKILL.md:86-107` |
| Files rule (D8) | The rule that every spec lists the paths it changes. Tasks counts as a file list. | `my.md` item 1, the spec-review prompt, `my:status` step 6 | Existing texts: `global/methods/my.md:79`, `plugins/my/skills/spec-review/spec-reviewer-prompt.md:64-68`, `plugins/my/skills/status/SKILL.md:76-82` |
| `kit:setup` "Parallel runs" step (D9) | The proposed four lines, and the locked commit when the section existed before | `/proc/meminfo` or `sysctl`, compose and `.env` files, `locked-commit.py` | Existing skill, `plugins/kit/skills/setup/SKILL.md:51-159` |
| `git-fold-fixups.py`, `locked-commit.py` | The fold with its refusals. The locked commit. | git | Existing, `plugins/my/bin/git-fold-fixups.py:1-40`, `plugins/my/bin/locked-commit.py:1-35` |

| From → To | What passes | Owner of what passes |
| --- | --- | --- |
| User → `auto rows` | Row numbers | User |
| `auto rows` → `status-scan.py` | The roadmap, order and runs facts, read once | `status-scan.py` |
| `auto rows` → git, `git-fold-fixups.py`, `locked-commit.py` | Fixup or normal commits of the `approved` edits, then a fold of `<base>` | `auto rows` (the call) |
| `auto rows` → `queue add` (under lock `main`) | The entries of one call | `handoff-state.py` |
| `auto rows` or refill → `pull` (under lock `main`) | `--max <n>` in. One tab-split line per start out (slug, stage, spec, slot), and `skipped:` lines on stderr. | `pull` |
| `pull` → `start()` | In-process call that writes a fresh state file | `handoff-state.py` |
| `pull` → state files of the `after` slugs | Read of `next` and `stopped` | The stages, through `handoff-state.py set` |
| `pull` → queue file | Each entry's `state` and `reason` | `pull` |
| `pull` → live runs, to apply rule 4 | Whether a live run is `exclusive`, read from a `started` queue entry | Queue file. Nothing else stores it (`handoff-state.py:77-78`). |
| Review sub-step 4 / end-a-run session → refill | Runs after `next=finished` is set | Refill hook |
| Refill or `auto rows` → Launch | `run auto <stage> <spec>` with `MY_AUTORUN=<new slug>` | Launch |
| `status-scan.py` → queue file | Read only | `handoff-state.py` |
| `my:status` → user | The "slots are free" item, and the waiting and skipped lines | `my:status` |
| `kit:setup` → `CLAUDE.md` | The "Parallel runs" section | `kit:setup` |

The search for callers and references was text-only (`git grep` and `grep -rn` through Bash). No symbol tool was available.

## Grounding

- The **Blast radius** item in Risk lists the callers of `handoff-state.py` as `my:handoff`, its README, `README.md` and the tests. The list leaves out `plugins/my/bin/status-scan.py:188`, which runs `handoff-state.py live`, and `plugins/my/skills/status/SKILL.md`, which names the script. `git grep -l handoff-state -- ':!docs'` lists both. The spec does tell the plan to sweep with `git grep`, so this is minor.
- Every other checked reference holds:
  - `a0144ee` is batch 2 (its commit body says so).
  - The machine has 15.3 GiB of memory (`/proc/meminfo`), and `README.md:390-394` gives the `Max runs: 1` advice.
  - This repo has no "Parallel runs" section, and there is no `CLAUDE.local.md`.
  - Stop row 16 is at `SKILL.md:234`.
  - Review sub-step 4 writes `stopped=` (`SKILL.md:875`).
  - The end-run text writes `stopped="ended by the user"` (`SKILL.md:356`).
  - Start check 4 is at `SKILL.md:466` and check 7 at `SKILL.md:474-478`.
  - Plan stage step 6 is at `SKILL.md:538-548`.
  - The supervised Medium fixup rule is at `my.md:36-40`, and Spec → Plan item 1 at `my.md:79`.
  - `docs-layout.md` steps 4 and 9 are at `docs-layout.md:151-162`.
  - `kit:commit` uses `locked-commit.py` (`plugins/kit/commands/commit.md:11`).
  - `kit:setup` steps 1 and 3 are at `setup/SKILL.md:51-91`.
  - A nested `flock` blocks: `handoff-lock.py` execs the command and keeps the lock open (`handoff-lock.py:4-8`).
  - Roadmap rows 9, 16, 29, 30, 31 and 37 all exist in `ROADMAP.md`.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Critical / High | design | **Call order can deadlock the queue.** Entries are walked in call order, and a row that is not ready stops the walk (rule 3). Nothing puts a blocker ahead of the rows gated behind it. Take `/my:handoff auto rows 12 9`, with 12 gated behind 9. Entry 12 comes first and is not ready, because 9 has no state file. The walk stops, so 9 never starts. Every later `pull` and every rerun of the command stops at the same place. D7 then tells the user to run a command that does nothing. | `spec §D4` ("in call order") ↔ `§D5` rule 3 ("An entry that is not ready stops the walk") ↔ `§D2` (no ordering rule) | Decision for the author. For example, the call orders the entries so that each comes after its `after` slugs, keeping call order otherwise, and refuses a cycle. Or the walk skips past an entry whose blockers are themselves still `waiting`. |
| Critical / High | design | **Pruning deletes facts that `pull` still reads.** `queue add` drops every entry that is not `waiting`. (a) Say a blocker was marked `skipped`, but the walk stopped (cap or exclusive) before reaching the row behind it. A later call prunes the skipped entry. The dependent now has an `after` slug with no entry and no state file. Rule 2 cannot fire, rule 3 never passes, and the queue stalls forever, with every row behind it. (b) The `started` entry is the only record that a live run is `exclusive`, because the state file has no such field. Once a later call prunes that entry, `pull` starts rows beside the exclusive run, which breaks rule 4. Also, nothing removes a `waiting` entry. The only way out of a stall is to edit the spec so that rule 1's hash check trips, and the spec does not document that. | `spec §D4` ("drops every entry whose `state` is not `waiting`") ↔ `§D5` rules 2-4; `plugins/my/bin/handoff-state.py:77-78` (FIELDS has no `exclusive`) | Decision for the author. Options: prune only entries that no `waiting` entry names in `after`; record `exclusive` in the run's state file; have rule 2 also treat "no entry and no state file" as a failed blocker; add a way to remove an entry (`queue drop <slug>`). |
| Warning / High | design | **D3's fold runs even when a run is live,** and a refusal blocks the whole call. When `live` lists a run, D3 makes normal commits, but it still runs `git-fold-fixups.py` afterwards. That fold rewrites `<base>` under the live run. A project without the section takes no lock, so the rebase can also collide with the live review's squash-merge in the same checkout. If the live run's own spec fixup waits, with its worktree on top of it, the fold refuses (code sub-step b skips the fold when the tree is dirty). Then the call writes no queue in the very case the queue exists for: Max 1 with a run live. The same happens when any tracked file is dirty. The step "ask the user before folding" has no branch for a "no" answer. | `spec §D3` ↔ `plugins/my/bin/git-fold-fixups.py:22-30` (refuses on a dirty tracked file or a target held by a worktree); `SKILL.md:670-673` (sub-step b skips the fold when dirty); `SKILL.md:597-599` (existing pattern: skip the fold when not clean, and the review folds later) | Decision for the author. For example: fold only when this call made fixups and no run is live; otherwise skip the fold and let each spec's own stage fold it, as plan stage step 8 does. Also state what a "no" to the ask does. |
| Warning / High | design | **D2 has no check that the stage can start fresh.** D2 checks the status, the Delegation section and the state file, but not the start checks the stage runs hours later: no plan yet, no branch `*/<slug>`, no worktree folder. A row whose earlier run the user ended keeps its branch, so its re-queued stage fails start check "no branch". A failed start check writes nothing. The slot stays held with no stop line. `my:status` shows the run as "in progress", and the D7 line cannot fire because no slot is free. This breaks Goal 2: the run neither merges nor stops with a line. | `spec §Goal` 2 ↔ `§D2`; `SKILL.md:356-357` ("The branch stays"); `SKILL.md:414-426` (fresh-start checks); `SKILL.md:450-452` (a failed check writes nothing); `status/SKILL.md:95,101` | Add the fresh-start checks of the target stage (plan `ls`, `git branch --list '*/<slug>'`, worktree folder) to D2's skip table. |
| Warning / High | design | **D10's three branches cannot run under the spec's own Delegation section.** An auto run keeps one `branch`, one worktree and one squash per slug, then writes `next=finished`. D10 asks for three branches, three review rounds and three squash-merges. The precedent for a batched spec, swappable-methods D12, was "Supervised only. No Delegation section." | `spec §Delegation` ↔ `§D10`; `SKILL.md:424-426`, `SKILL.md:628-629` (one worktree `<type>/<slug>`); `SKILL.md:856-875` (one merge, then finished); `docs/plans/2026-10-12-swappable-methods-spec.md:56` | Decision for the author: drop the Delegation section and run supervised, or drop the batches (or split the spec). |
| Warning / High | design | **D7's "needs you" item fires when a rerun cannot help.** Goal 4 asks for a message when a slot is free "with nothing filling it". D7's test is only "rows wait and live < Max runs". It fires while the first waiting row is gated behind a live run, while an exclusive row waits for a live run, and in the call-order deadlock above. In each case `/my:handoff auto rows` starts nothing, so the advice is wrong. | `spec §Goal` 4 ↔ `§D7` | Fire the item only when the first waiting entry would pass rules 1 to 4 now, or say "waiting for `<slug>`" otherwise. The facts are already in the `queue` and `runs` blocks. |
| Warning / Medium | design | **A blocker that is a live or queued run outside the call is treated as unwakeable.** D2 skips a row gated behind a row "not in this call". The stated reason is that nothing would wake it. But every auto run's finish runs the refill (D6), and so does every hand-started auto run. A blocker that is `waiting` from an earlier call would also start and finish through the queue. D2 already reads the queue for its "already waiting" case. Separately, the spec does not say whether rows skipped at D2 are written as `skipped` entries. Take a blocker listed in the call but skipped with "a run exists". Its dependent either queues with `after` set to it (and is woken correctly) or is skipped by rule 2. Which one happens is not decided. | `spec §D2` ↔ `§Trade-offs` ("Nothing in the call would wake it") ↔ `§D6`; `§D4` (`state` `skipped`) | Decision for the author. For example, allow `after` to name a slug that has a live state file or a `waiting` entry, and say whether D2 skips are written to the queue. |
| Warning / Medium | design | **A refill failure is a "signal" yet "never a stop", and the spec does not say whether Finish runs after it.** A signal renames the window with ⚠, prints its line last, and stops and waits. Finish renames the window with ✓ and prints the squash hash line last. Both cannot happen. | `spec §D6` ↔ `SKILL.md:179-190` (Signal: "then stop and wait"); `SKILL.md:876-877`, `SKILL.md:913-921` (Finish) | Decision for the author: which mark and which last line the finished window shows after a refill failure. |
| Suggestion / High | design | **D5 does not say what `pull` does when `start()` refuses an entry.** For example, the user started the same slug by hand after the call. The choices are: skip the entry, stop the walk, or fail the whole `pull`. A failed `pull` makes every refill signal until that run ends. | `spec §D5` rule 6 ↔ `handoff-state.py:211-213` | State the behaviour, for example "mark it `skipped` with `a run for <slug> exists`". |
| Suggestion / High | editorial | **D3 hardcodes the commit scope `docs(plans)`.** The feature runs in every `my` project, and `plans` is this repo's scope. The code stage already says "with the scope the project's rules give docs". | `spec §D3` ↔ `SKILL.md:665-666` | Use the same wording as the code stage. |
| Suggestion / High | editorial | **Out of scope says "Refills always run in a tmux window".** D6's second place, "To end an abandoned run", runs in whatever session the user is in, which may be outside tmux. D6's own failure branch covers that case. | `spec §Out of scope` ↔ `§D6`; `SKILL.md:349-357` | Say "refills from a review session run in tmux; a refill from the user's session may fall back (D6)". |
| Suggestion / High | editorial | **D9's locked commit has no working directory.** `kit:setup` runs every command as `git -C <path>` and supports a path other than the current repo. `locked-commit.py` commits in the current directory and has no `-C`. `kit:commit` also checks that it is in the main checkout first. | `spec §D9` ↔ `plugins/kit/skills/setup/SKILL.md:43-47`; `plugins/my/bin/locked-commit.py:1-25`; `plugins/kit/commands/commit.md:11` | Say "run `cd <path> && locked-commit.py …` from the main checkout". |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Fit with what exists | `pull` reuses `start()` (`handoff-state.py:201-223`) inside the existing lock. The queue sits in a subfolder that `live` and `status-scan.py` skip (`handoff-state.py:176-187`, `status-scan.py:197`). The refill reuses Launch, and the review session's flags (`SKILL.md:263-270`). | Strong |
| Boundaries | The queue has one writer, `handoff-state.py`. The caller takes the lock, and the spec explicitly forbids a nested lock, which is correct because `handoff-lock.py` execs the command and holds the `flock` (`handoff-lock.py:4-8`). | Strong |
| Contracts | Each skip reason has exact text (D2 table). The `pull` output is a defined tab-split line. Rule 3 relies on `stopped=` from a successful finish (`SKILL.md:875`) and the non-empty stop line from an ended run (`SKILL.md:356`), both verified. | Moderate |
| Rejected options | Candidate B was rejected on stated forces (brief, Comparison table rows 7 and 9). Each Trade-offs item names what it gives up (head-of-line blocking, crash stall). The brief's "Open for brainstorming" items are each settled. | Strong |
| Spec rules | "How to read this spec" comes first and lists every related document with its path. Risk, Dependencies and Trade-offs are present. A Files section is present. There is no UI, so no Visual Language section is needed. | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| Contracts and flow | Call-order deadlock (`§D4` ↔ `§D5` rule 3). | High |
| State ownership | `exclusive` and `skipped` live only in queue entries that `queue add` prunes (`§D4`; `handoff-state.py:77-78`). | High |
| Failures and interactions | D3 folds `<base>` under a live run, with no lock in a project without the section. A refused fold blocks the whole call (`git-fold-fixups.py:22-30`). | Medium |
| Failures and interactions | A refused fresh-start check leaves a held slot with no stop line (`SKILL.md:450-452`, `356-357`). | Medium |
| Spec rules | D10's batches conflict with the spec's own Delegation section (`SKILL.md:628-629`, `856-875`). | Medium |
| Contracts | D7's free-slot item gives wrong advice in gated and exclusive waits (`§Goal` 4 ↔ `§D7`). | Medium |

## Not Applicable

None.

## Reasoning

Candidate A's components are well placed: one writer for the queue, a pick-and-start step inside one lock, and a refill run by the finishing session. These all fit the existing code. The defects sit in the walk's rules and the queue's state ownership. The walk stops at the first entry that is not ready, but it does not order entries by gate. It also reads facts (`skipped` entries, `exclusive` flags) that `queue add` deletes, and the state file never holds them. Both paths end with a `waiting` entry that can never pass rule 3, so the queue stalls with no way out. That breaks Goals 1 and 4. The D3 fold and the missing fresh-start checks add ways to block or silently hold a slot. Each is a decision about a rule, so the author must decide; none needs a new architecture.

## Verdict

**Assessment:** Problematic
**Confidence:** High. Both Critical findings follow directly from the spec's own rules (D4 and D5), and the second is confirmed by the state fields at `handoff-state.py:77-78`.
**Recommendation:** Keep Candidate A. Before the plan, the author should decide: an ordering rule for the walk (D2/D5); what pruning keeps, and where `exclusive` lives (D4); when D3 folds; D2's fresh-start checks; and Delegation versus D10's batches. Then fix the editorial rows and run `my:spec-review` again.
