# Review: docs/plans/2026-10-12-parallel-auto-runs-spec.md

**Status:** review of docs/plans/2026-10-12-parallel-auto-runs-spec.md, 2026-10-12. Problematic: the approach (a lock per command, a compare-and-swap merge, folding at once or not at all) holds, but `checked_base` as defined can let a merge land code that was never tested together, and the new `Max runs` start check would refuse a run's own later stages. Answered with the user on 2026-10-12, in the spec's D3 to D11, Risk and Testing: every finding was accepted, none rejected.

## Spec Summary

The spec lets 2 to 4 `my:handoff auto` runs work at once in one project. It does this with a per-command `flock` wrapper (`handoff-lock.py`), lock `main` around every commit in the main checkout, a three-way-merge helper for shared docs (`handoff-merge-file.py`), a new fold refusal and a `commit` mode in `git-fold-fixups.py`, and a compare-and-swap `merge` subcommand in `handoff-state.py` driven by a new `checked_base` field. A project opts in with a "Parallel runs" section, and `my:roadmap-management` answers "what can we do in parallel?" and launches the picks.

## System Model

All caller sweeps in this review were text-only (`grep -rn`, `git grep`); no symbol-reference tool was available.

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `my:roadmap-management` "What next" section (D1) | The four-group answer; the multi-select pick; the launches | `ROADMAP.md` `## Order of work` and `Blocked by` lines; `handoff-state.py live`; `git worktree list`; the spec's status and Delegation section; the "Parallel runs" section | Existing skill `plugins/my/skills/roadmap-management/SKILL.md:1-10`, rule 12 at `:185-198`; section new |
| "Parallel runs" section (D2) | `Max runs`, `Docs paths`, `Isolation`, `Shared resources` per project | Read by sessions only | New (project `CLAUDE.md` / `CLAUDE.local.md`) |
| `my:handoff` start checks (D3) | Refusing a launch past `Max runs`, without the section, or on a blocked row | `handoff-state.py live`; the "Parallel runs" section; `ROADMAP.md` | Existing `plugins/my/skills/handoff/SKILL.md:352-400`; three checks new |
| `handoff-lock.py` (D4) | Nothing persistent; the kernel owns each `<common dir>/my-handoff/locks/<name>.lock` | `fcntl.flock`; the git common dir | New |
| Lock `main` (D5) | Who may commit in the main checkout right now | `handoff-lock.py` | New |
| `handoff-merge-file.py` (D6) | Commits of shared docs (`ROADMAP.md`, `CHANGELOG.md`, plans index) built from `HEAD` with a temporary index | `git merge-file`, `commit-tree`, `update-ref`; caller's base and edited copies | New |
| `git-fold-fixups.py` (D7) | The fold, `check`, the new "code after the target" refusal, the new `commit` mode | `--docs-paths`; git | Existing `plugins/my/bin/git-fold-fixups.py:1-305` |
| `handoff-state.py` (D3, D8) | Run state file; new `live`, `merge`, `checked_base`, `merge_retries` | git; the base branch in the main checkout | Existing `plugins/my/bin/handoff-state.py:1-286` |
| Review stage (D8, D10) | Setting `checked_base`; the rebase-recheck-retry loop; calling `merge` | `handoff-state.py`, `handoff-lock.py`, the worktree | Existing `plugins/my/skills/handoff/SKILL.md:546-675` |
| Code stage (D9) | Applying `Isolation`; wrapping shared-resource commands | "Parallel runs" section; `handoff-lock.py` | Existing `plugins/my/skills/handoff/SKILL.md:483-544` |
| Rule text (D11) | The lock rule for the user's own Claude sessions | `global/rules/docs-layout.md` (path-scoped load), `global/CLAUDE.md` | Existing `global/rules/docs-layout.md:1-5,132-173`, `global/CLAUDE.md:58-68` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| roadmap-management → `handoff-state.py live` | Lines: slug, `next`, `stopped`, branch | `handoff-state.py` |
| roadmap-management → `/my:handoff auto plan|code <spec>` | A skill invocation per pick | roadmap-management |
| handoff start checks → `live` | Count of live runs (own run included in `run auto` sessions) | `handoff-state.py` |
| handoff start checks → `ROADMAP.md` | The spec's row and its `Blocked by` line | roadmap-management (by D1's own claim) |
| Any session → `handoff-lock.py main` | One command (commit, `commit` mode, merge-file, merge) | the calling session |
| Session → `handoff-merge-file.py` | Base and edited copies, `--with` paths | the session (copies), the script (the commit) |
| Session → `git-fold-fixups.py commit` | Target hash, paths, message, docs paths | the session |
| Review stage → `handoff-state.py set checked_base` | A base commit hash | review stage (definition unclear, see Issues) |
| Review stage → `handoff-state.py merge` | slug, message, docs paths; exit 0 / 1 / 3 | `handoff-state.py` |
| Code and review stages → `handoff-lock.py <resource>` | One shared-resource command, `run_in_background` | the calling stage |
| `resume` → restarted review stage | `next=review` after rows 22 and 23 | `handoff-state.py` and SKILL.md "Restarted stages" |

## Grounding

- spec §D2 "Without the section, a project behaves exactly as today: a second auto run refuses to start (D3)" ↔ `plugins/my/skills/handoff/SKILL.md:375-376`: today only a run for the same slug refuses. A second auto run for another spec starts. The refusal is new behaviour, not today's.
- spec §Context item 2 "The script refuses only when a worktree holds the target or the target is pushed" ↔ `plugins/my/bin/git-fold-fixups.py:167-168,191-197`: it also refuses on uncommitted tracked changes, merge commits and `squash!`/`amend!` in the range. The point the sentence makes (nothing protects a squash in the range) still holds.
- spec §Risk "Blast radius" lists the callers of `git-fold-fixups.py` but misses `plugins/my/skills/handoff/README.md:51,116,147`, `README.md:107-114` and `~/projects/zitamu/real-estate-webapp/CLAUDE.local.md:251`. The Files table gives the handoff README only "a Parallel runs section", but its plan-stage step 7 and review-stage step 7 describe the fold-later steps that D7 removes.
- Every other reference checked holds: the SKILL.md steps and rows named (plan step 6 and 8, auto code step 2, review step 8 sub-step 3, rows 3, 5, 15, 16, 17, "Never poll for another session" at `:698`), `docs-layout.md` steps 4, 8, 9 (`:149-160`), the global Medium paragraph (`global/CLAUDE.md:67-68`), zitamu's `realestate_e2e` (`web/scripts/e2e-worktree.sh:12,82`) and port 54310 (`web/scripts/preview.sh:17`), the test files and their temp-repo pattern (`plugins/my/tests/test_git_fold_fixups.py:78`), the critique's M1 (`docs/reports/2026-10-09-workflow-efficiency-critique.md:158`), the brief's estimates (28 %, 0.03 %, 30 min) and the Delegation command (`python3 -m unittest discover plugins/my/tests`: 64 tests, OK).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Critical / High | design | `checked_base` is "the `<base>` commit the end-of-branch checks last ran against", but the checks run on the branch, which holds only its fork point. If run A merges while B is in its code stage, and B's review records the current `<base>` tip, B's `merge` sees no code diff and lands a combination nobody tested. That breaks Goal 3 and D8's own title. The integration test only covers A merging after B's checks. | `spec §D8 ↔ §Goal`, `spec §Testing` (test_parallel_runs) | Define `checked_base` as `git merge-base <base> <branch>` at check time, or rebase onto `<base>` before the first check; add a test where A merges before B's checks. |
| Critical / Medium | design | D3's `Max runs` check counts every line of `live`, and the auto start checks run in every `run auto` session, not only at launch. A run's own state is live there, so with `Max runs: 2` and two runs live, each run's code or review stage (and `resume`) refuses itself. Check 1 says "another run"; check 2 does not exclude the own slug. | `plugins/my/skills/handoff/SKILL.md:354-356`; `spec §D3` | Decision for the author: run the three checks only in the auto launch, or exclude the run's own slug in every check. |
| Warning / High | design | Rows 22 and 23 stop with `next=review`, and D10 says `resume` then reruns the whole review stage. The existing restart rule refuses a restarted review whose branch already has a review report ("the fix round already ran"), which is always true at a rebase or merge-retry stop. The spec does not change that rule, so those stops cannot be resumed. | `plugins/my/skills/handoff/SKILL.md:301-305`; `spec §D10` | Decision for the author: exempt rows 22 and 23 from the one-fix-round restart check, or resume them at a new sub-step that skips the reviews. |
| Warning / High | design | D3's third check makes `my:handoff` read `ROADMAP.md` to find the spec's row and its `Blocked by` line. D1 rejected a `my:handoff` form for exactly that reason ("it would read roadmap formats it does not own"). The spec also never says how handoff finds a spec's row, or what `<N>` is. | `spec §D1 ↔ §D3`; `plugins/my/skills/roadmap-management/SKILL.md:185-198` | Decision for the author: keep the blocked check only in D1's answer, or name the lookup (the row that links the spec) and accept the ownership leak. |
| Warning / High | design | `handoff-merge-file.py` commits with `git commit-tree` and `update-ref`, so it runs no hooks. In zitamu the `pre-commit` hook formats staged Markdown and refuses a commit on `main` whose doc lines cite a commit outside `main`. The `done` marks (D9) would skip exactly the check behind Goal 3. | `~/projects/zitamu/real-estate-webapp/.git/hooks/pre-commit:62-80`; `spec §D6`, `§D9` | Decision for the author: run the hooks (for example `git commit` with `GIT_INDEX_FILE` set), or state the bypass in Risk with what replaces the check. |
| Warning / High | design | Lock `main` covers only the commit command. Untracked files (a new plan, a review) need `git add` first, and `git add` writes `.git/index` outside the lock, so it can collide on `index.lock` or leave staged paths. `merge` then commits the whole index after `git merge --squash`, sweeping in anything staged. The brief put `git add` under the lock. | `spec §D5`; `plugins/my/skills/handoff/SKILL.md:439-441`; brief `docs/plans/2026-10-12-parallel-auto-runs-architecture.md:64,74` | Put `add` and commit in one locked command; have `merge` refuse when the index has staged changes before the squash, as `check` does at `plugins/my/bin/handoff-state.py:193-194`. |
| Warning / High | design | The review stage runs the end-of-branch checks (e2e included) in the worktree, and reruns them on every merge retry. D9 applies `Isolation` only in the code stage, so two review stages share one test stack. Row 19 already counts the review stage for shared resources. | `spec §D9 ↔ §D10` row 19; `plugins/my/skills/handoff/SKILL.md:561-566` | Apply `Isolation` in every stage that runs a command in the worktree. |
| Warning / Medium | design | D7 calls `reset --soft HEAD~1` safe because nothing can land under lock `main`. But D5 says commits from a plain terminal take no lock. A user commit landing between the fixup and the undo would be removed from history, and its changes would be left staged. | `spec §D7 ↔ §D5` | Undo only when `HEAD` still equals the fixup's hash (`git update-ref HEAD <parent> <fixup>`), the way D6 checks the old value. |
| Warning / Medium | design | `handoff-state.py` already uses exit 1 for "no state" and for every git error. The new `merge` uses exit 1 for "squash conflict", which maps to row 15. So any git error becomes a conflict stop with `next=merge`. | `plugins/my/bin/handoff-state.py:225-227,279-281`; `spec §D8` | Give the conflict its own exit code, or have the stage read the printed paths, not the code. |
| Warning / Medium | design | `merge_retries` "starts at 0" but is never reset. After row 23 the user resumes, and the next exit 3 is already past the cap, so the run stops again at once. | `spec §D8`, `§D10` row 23 | State when the counter resets: on `resume`, or when the review stage starts. |
| Warning / Medium | design | `check` for `next=done` still reports `fixup waits` for the spec and task doc. The Risk section's crash case leaves a `fixup!` stuck behind a squash, so `resume` would refuse that run forever. | `plugins/my/bin/handoff-state.py:213-215`; `spec §Risk` "A crash between the fixup and the fold" | Drop the `fixup waits` check for `done`, or name it as a stop the user clears. |
| Warning / Medium | design | `commit` mode folds without the project's pre-rebase check, which every fold runs first today. Row 5, which held that check's failure, is removed. | `plugins/my/skills/handoff/SKILL.md:454-457`; `spec §D7`, `§D10` row 5 | Say whether the pre-rebase check is dropped, or run it inside `commit` mode before the fold. |
| Warning / Medium | design | D1 rejects a rule file because rules load only when a matching file is read. D11 then puts the lock-`main` rule for the user's sessions in `docs-layout.md`, which loads only for `docs/plans/` and `docs/reports/` paths. A session that only edits `ROADMAP.md` or `CHANGELOG.md` (for example `my:roadmap-management` or `changelog-management`) never sees it. | `global/rules/docs-layout.md:1-5`; `spec §D1 ↔ §D11` | Put the rule where those sessions read it (`global/CLAUDE.md` Git Workflow, and the roadmap and changelog skills). |
| Warning / Medium | design | Lock `main` waits up to 300 s, but a Bash tool call times out at 120 s unless the call sets a longer timeout. A wait past 120 s ends in a tool timeout, not exit 75, so row 18 never fires. The spec handles the 10-minute limit only for shared resources. | `spec §D4` | Require a Bash timeout above the lock timeout for every lock-`main` call, or lower the lock-`main` timeout below 120 s. |
| Warning / Medium | design | A stopped run counts toward `Max runs` "until the user resumes or ends it", but no way to end a run is defined: there is no subcommand or step that sets `next=finished` for an abandoned run, or says what happens to its worktree and branch. | `spec §D1` step 3, `§Risk` | Define the end-a-run step (for example `handoff-state.py set <slug> next=finished`) and what it leaves behind. |
| Warning / Medium | design | The `Isolation` example uses `<54310 + run number>`. Nothing in the spec or the state file defines a run number, and two runs could pick the same port. | `spec §D2`; `plugins/my/bin/handoff-state.py:43-44` | Name the placeholders a session may fill (for example `<slug>` only), or add a run number to the state. |
| Warning / Medium | design | D6 does not say where the base copy comes from: the working file, which may hold the user's uncommitted lines, or `HEAD`. The merge into `HEAD` gives different results, or conflicts, depending on the choice. | `spec §D6` | State the source of the base copy. |
| Suggestion / High | editorial | §D2 says a project without the section "behaves exactly as today: a second auto run refuses to start". Today a second run for another slug starts. | `plugins/my/skills/handoff/SKILL.md:375-376`; `spec §D2` | Say the refusal is new. |
| Suggestion / High | editorial | The Risk section's blast radius and the Files table miss three places that describe the fold: the handoff README's fold steps, the root README, and zitamu's `CLAUDE.local.md`. | `plugins/my/skills/handoff/README.md:116,147`; `README.md:107-114`; `~/projects/zitamu/real-estate-webapp/CLAUDE.local.md:251` | Add them to Files and Risk (zitamu's as a later change in its own repo). |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Fit with what exists | Reuses the state file, the common-dir layout (`plugins/my/bin/handoff-state.py:76-81`) and the fold script; no daemon; the queue (B) and the integrator (C) were real candidates with stated reasons in the brief (`architecture.md:221-231`) | Strong |
| Failures: lock lifetime | `flock` released by the kernel on process death; nothing spans two tool calls (spec §D4); this matches the brief's analysis of crash cases | Strong |
| Fold safety | The existing "held by a worktree" refusal (`git-fold-fixups.py:106-113`) plus the new "code after the target" refusal together keep a squash commit and a live branch's base out of any fold range | Strong |
| Shared-file edits | D6 merges into `HEAD` and the working file separately, and commits from a temporary index with a checked `update-ref`. That answers the brief's open item about half-made edits (`architecture.md:314`) | Moderate |
| Spec rules | "How to read" is first with the brief listed first; Risk, Dependencies and Trade-offs are present; the Delegation section is valid and its command passes | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Contracts: `checked_base` | spec §D8 defines it ambiguously, and the likely reading lets untested code merge | High |
| Interactions: start checks in later stages | `SKILL.md:354-356` with spec §D3 | High |
| Interactions: resume after rows 22 and 23 | `SKILL.md:301-305` | Medium |
| Boundaries: roadmap ownership | spec §D1 ↔ §D3 | Medium |
| Lock coverage | `git add`, terminal commits, hooks bypassed by plumbing, the Bash timeout (spec §D4 to §D7) | Medium |

## Not Applicable

None.

## Needs Investigation

- **What a Bash tool timeout or a kill does to the locked child.** If Claude Code kills only `handoff-lock.py` and not its child (a `git rebase`, an e2e run), the kernel frees the lock while the command still runs, and a second run enters. Python's default `close_fds` means the child does not hold the lock fd. Resolve by checking whether the Bash tool kills the whole process group, and decide whether the child should inherit the lock fd.
- **Which projects define a "pre-rebase check".** SKILL.md runs "the project's pre-rebase check" before each fold, but zitamu's `CLAUDE.local.md` defines none that the grep found. If no project has one, the D7 finding about it shrinks to a wording fix.

## Reasoning

The System Model is coherent: each new script has one job, and lock `main`, the merge helper and the compare-and-swap merge divide the main checkout cleanly. But the one field that carries D8's guarantee, `checked_base`, is defined in a way whose natural reading lets untested combinations merge. The new `Max runs` check, placed where `SKILL.md` already runs auto start checks, would also block every run's later stages at the cap. Both are gaps inside the spec that a plan writer would carry into code. The other findings are at the edges of the locks and the resume paths.

## Verdict

**Assessment:** Problematic
**Confidence:** High — both Critical findings rest on spec text checked against `SKILL.md:354-356` and the stated Goal, and the rest were checked against the scripts and zitamu's hooks.
**Recommendation:** Settle the two Critical findings with the user (the definition of `checked_base`, and where the D3 checks run), and the design Warnings on the restart rule, the roadmap ownership and the hook bypass. Then fix the two editorial rows and rerun `my:spec-review`.
