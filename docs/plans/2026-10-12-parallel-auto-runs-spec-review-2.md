# Review: docs/plans/2026-10-12-parallel-auto-runs-spec.md

**Status:** review of docs/plans/2026-10-12-parallel-auto-runs-spec.md, 2026-10-12. Mixed: the first review's findings are settled, but a stop or crash during the new merge phase leaves `next=review`, which the restart rule refuses, and a squash commit refused by a hook blocks every other run. Answered with the user on 2026-10-12, in the spec's D1, D3, D4, D7 to D11 and Testing: every finding was accepted, none rejected.

## Spec Summary

The spec lets 2 to 4 `my:handoff auto` runs work at once in one project that opts in with a "Parallel runs" section, and lets `my:roadmap-management` answer "what can we do in parallel?" and launch the picks. Every commit in the main checkout runs under a per-command `flock` (`handoff-lock.py main`), and shared docs go through a three-way-merge script (`handoff-merge-file.py`). Fixups fold at once or become normal commits (`git-fold-fixups.py commit`), and the merge is a compare-and-swap on `checked_base` with a rebase-recheck-retry loop (`handoff-state.py merge`).

## System Model

All caller sweeps in this review were text-only (`grep -rn`, `git grep`). No symbol-reference tool was available.

| Component | Owns | Depends on | New / existing (verified at) |
| --- | --- | --- | --- |
| `my:roadmap-management`, section "What next, and what can run in parallel" (D1) | The four-group answer, the overlap warning, the multi-select pick, the launches | `ROADMAP.md` `## Order of work` and `Blocked by`/`Waits for` lines; `handoff-state.py live`; `git worktree list`; spec status and Delegation; the "Parallel runs" section | Skill exists `plugins/my/skills/roadmap-management/SKILL.md:1-10`, rule 12 at `:185-193`; section new |
| "Parallel runs" section (D2) | `Max runs`, `Docs paths`, `Isolation`, `Shared resources` for one project | Read by sessions only; scripts get docs paths as an argument | New (project `CLAUDE.md` / `CLAUDE.local.md`) |
| `my:handoff` auto launch start checks (D3) | Refusing a new run with no section, or past `Max runs` | `handoff-state.py live` / `start`; lock `main` | Existing `plugins/my/skills/handoff/SKILL.md:352-400`; two checks new |
| `handoff-state.py` (D3, D8, D11) | The run state file; new `live`, `start`, `merge`; fields `slot`, `checked_base`, `merge_retries`; `next=merge-retry` | git; the main checkout's branch | Existing `plugins/my/bin/handoff-state.py:1-286` |
| `handoff-lock.py` (D4) | Nothing persistent; the kernel owns each `<common dir>/my-handoff/locks/<name>.lock` | `fcntl.flock`, `os.execvp`, the git common dir | New |
| Lock `main` (D5) | Who may write the main checkout's index and `HEAD` right now | `handoff-lock.py`; rule text in `global/CLAUDE.md` and `SKILL.md` | New |
| `handoff-merge-file.py` (D6) | Commits of shared docs (`ROADMAP.md`, `CHANGELOG.md`, plans index) built from `HEAD` in a temporary index; merge into the working file | `git merge-file`, `git commit` with `GIT_INDEX_FILE`, project hooks; the session's base and edited copies | New |
| `git-fold-fixups.py` (D7) | The fold, `check`, the new "code after the target" refusal, `--docs-paths`, the `commit` mode with its undo | git; docs paths from the session | Existing `plugins/my/bin/git-fold-fixups.py:1-305` |
| Review stage (D8, D9, D10) | Recording `checked_base`; the rebase-recheck-retry loop; calling `merge`; the `done` marks via D6 | `handoff-state.py`, `handoff-lock.py`, `handoff-merge-file.py`, the worktree | Existing `plugins/my/skills/handoff/SKILL.md:546-674` |
| Code stage (D9) | Applying `Isolation`; wrapping shared-resource commands | The "Parallel runs" section; `handoff-lock.py`; the execution skill and its subagents | Existing `plugins/my/skills/handoff/SKILL.md:483-544` |
| `auto resume` and "Restarted stages" | Picking the stage from `next`; the one-fix-round restart refusal | `handoff-state.py check`/`get` | Existing `plugins/my/skills/handoff/SKILL.md:238-308` |
| Rule text (D11) | The lock rule for the user's own sessions; docs-layout steps 4, 8, 9 | `global/CLAUDE.md`, `global/rules/docs-layout.md` | Existing `global/CLAUDE.md:55-70`, `global/rules/docs-layout.md:146-160` |

| From → To | What passes | Owner of what passes |
| --- | --- | --- |
| roadmap-management → `handoff-state.py live` | One line per live run: slug, slot, `next`, `stopped`, branch | `handoff-state.py` |
| roadmap-management → `/my:handoff auto plan\|code <spec>` | One skill invocation per pick | roadmap-management |
| auto launch → `handoff-lock.py main -- handoff-state.py start` | slug, `--max <n>`, fields; back: slot, or exit 6 | `handoff-state.py` |
| Any session → `handoff-lock.py main` | One command: plain add+commit, `commit` mode, merge-file, `merge` | the calling session |
| Session → `handoff-merge-file.py` | Base and edited copies, `--with` paths, message; back: exit 0 / 1 | session (copies), script (the commit) |
| Session → `git-fold-fixups.py commit` | Target, message, docs paths, paths; back: exit 0 / 3 / 4 | the session |
| Review stage → `handoff-state.py set checked_base` | `git merge-base <base> <branch>` after the last check run | review stage |
| Review stage → `handoff-state.py merge` | slug, message, docs paths; back: exit 0 / 1 / 3 / 4 / 5 | `handoff-state.py` |
| Code and review stages → `handoff-lock.py <resource> --timeout 3600` | One shared-resource command, in the background | the calling stage |
| Code stage → execution-skill subagents | Task prompts (no `CLAUDE.md`, no "Parallel runs" section) | the code stage |
| Stop rows 18 to 26 → `auto resume` | `next` (`merge`, `merge-retry`, or unchanged) and `stopped` | `handoff-state.py` |

## Grounding

All checked references hold. Checked:

- the `SKILL.md` steps and rows named: plan steps 6 to 9 at `:430-470`, auto code steps 1 and 2 at `:513-526`, review step 8 and its auto sub-steps at `:617-674`, rows 3, 5, 15, 16 and 17 at `:149-165`, and "Never poll for another session" at `:698`;
- `docs-layout.md` steps 4, 8 and 9 at `:149-160`, and the Medium paragraph at `global/CLAUDE.md:61-67`;
- rule 12 and `Waits for` at `roadmap-management/SKILL.md:185-193`;
- the auto-run spec's D2, D5, D6, D7 and its "Out of scope" at `docs/plans/2026-10-12-autonomous-run-spec.md:53-56,97-242`;
- the brief's estimates (28 %, 0.03 %, 30 min) at `docs/plans/2026-10-12-parallel-auto-runs-architecture.md:273-303`;
- zitamu's `realestate_e2e` at `~/projects/zitamu/real-estate-webapp/web/scripts/e2e-worktree.sh:12,82` and port 54310 at `~/projects/zitamu/real-estate-webapp/web/scripts/preview.sh:17`;
- diagoradisa-annotator's shared compose project at `~/projects/diagoradisa/diagoradisa-annotator/CLAUDE.md:128-134`;
- zitamu's `pre-commit` hook, which formats and re-stages Markdown and refuses citations of commits not on main, at `~/projects/zitamu/real-estate-webapp/.git/hooks/pre-commit:42-81`;
- the blast-radius list against `git grep git-fold-fixups`, which also finds `CHANGELOG.md` and `ROADMAP.md` history lines that need no change;
- the Delegation command `python3 -m unittest discover plugins/my/tests`: 64 tests, OK.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Warning / High | design | Some stops in the merge phase cannot be resumed. `merge` exit 3 changes nothing, so `next` stays `review` through the whole rebase-and-recheck loop. Only rows 22 and 23 write `merge-retry`. Row 18 (lock `main` busy on the `merge` call) and row 19 (a shared-resource lock busy during the check rerun) say "`next` unchanged". A crash or a closed window during that loop leaves `review` too, and the loop can take up to an hour of lock wait. `resume` then restarts the review stage with `next=review`. By that point the branch holds a committed review report, so the restart rule stops with "the fix round already ran", every time. | `plugins/my/skills/handoff/SKILL.md:298-305`; `spec §D8 ↔ §D10` rows 18, 19 | Decision for the author. For example, set `next=merge` (or `merge-retry`) before the first `merge` call, so every later stop and crash resumes at the merge step. |
| Warning / High | design | D8 step 4 does not say what happens when the squash commit fails after `git merge --squash` has staged it. zitamu's `pre-commit` refuses a commit on `main` whose docs cite a commit not on `main`, and the squash brings the branch's review reports in. A refused commit leaves the staged squash and `SQUASH_MSG` in the main checkout. Then every other run's `merge` exits 5. Every run's `check`, and so its `resume`, also refuses, because `IN_PROGRESS` looks at the shared checkout, not at the slug. One stop then stops every run, against Goal 3. | `~/projects/zitamu/real-estate-webapp/.git/hooks/pre-commit:63-81`; `plugins/my/bin/handoff-state.py:57-58,232-233`; `spec §D8 ↔ §Goal` | On a failed commit, run `git reset --merge`, check the tree is clean, and exit with a code of its own. Give that code a D10 row. |
| Warning / High | design | The new fold refusal protects only commits that change a path outside the docs paths, because it reads such a commit as "another feature's squash". A cited commit can change only docs. An existing rule makes one: an action plan's status "becomes `done`, naming the commit that added the rows", which is a roadmap-only commit. A feature whose diff lies under docs paths is another case. A later fold can rewrite such a commit, and folds now run at once, so far more often than before. The citing line then names a hash that is not on `main`, against Goal 3's "never". | `plugins/my/bin/git-fold-fixups.py:178-192`; `global/rules/docs-layout.md:76-77`; `spec §D7 ↔ §Goal` item 3 | Decision for the author. Also refuse on a commit that some doc on `main` cites, or on any state file's `squash_subject`. Or narrow Goal 3 and record the docs-only case in Risk. |
| Warning / Medium | design | `commit` mode defines exits 0, 3 and 4, but not the case where its own `git commit` fails: a hook refuses the `--fixup` commit, or the normal commit after the undo. The locked plain commit of D5 has no outcome for this either. D10 has no row for these cases, though zitamu's hook makes them reachable. | `spec §D7`, `§D5`, `§D10`; `~/projects/zitamu/real-estate-webapp/.git/hooks/pre-commit:42-48,76-81` | Name the exit code and the state left behind, and add a stop row. |
| Warning / Medium | design | D9 applies `Isolation` and the shared-resource lock to "every test and server command" the code stage runs. But the code stage often hands tasks to subagents (`superpowers:subagent-driven-development`), and the review stage hands the reviews to subagents too. Subagents read no `CLAUDE.md`, so they never see the "Parallel runs" section. Their test runs hit the shared stack unlocked, which is the collision that Context item 3 describes. | `plugins/my/skills/handoff/SKILL.md:415-421,489-494,546-548`; `spec §D9` | Say that the stage puts the filled-in `Isolation` line and the lock-wrapped commands into every subagent prompt, as review step 4 already does for the range. |
| Warning / Medium | design | Git's own detached children keep lock `main` held. The lock descriptor stays inheritable through `execvp` (D4). A locked `git commit` that triggers `git gc --auto` detaches a `gc`, `repack` and `pack-objects` that inherit it, so the lock stays held after the command exits. Risk names only servers or daemons that the caller starts. Another run then waits up to 90 s and stops at row 18. | Scratch test in this review: a `flock` wrapper that `execvp`s `git -c gc.auto=256 commit` over 3000 loose objects. Right after the exit, `ps -C git` showed `git gc --auto`, and `flock -n` reported the lock held. `spec §D4`, `§Risk` "A locked command that starts a background process" | Decision for the author. Run locked git commands with `-c gc.autoDetach=false -c maintenance.autoDetach=false`, or record the case in Risk with that mitigation. |
| Suggestion / High | design | D1 step 3 and the Risk section promise to name how long a stopped run has waited. The `live` output (slug, slot, `next`, `stopped`, branch) and the state fields carry no time. | `spec §D1 ↔ §D3`; `plugins/my/bin/handoff-state.py:43-44` | Add a `stopped_at` field, or print the state file's modification time in `live`. |
| Suggestion / High | editorial | "Rules for every stage" still says a busy shared resource "is a gate: signal the user". D4 and D9 now wait under a lock instead, but D4 rewrites only the "never poll" sentence. | `plugins/my/skills/handoff/SKILL.md:693-697`; `spec §D4` | Rewrite that rule too, in D4's rule change. |
| Suggestion / High | editorial | D11 removes `docs-layout.md` step 9 but does not say whether the later steps are renumbered. `global/CLAUDE.md` refers to "the fourteen steps", "Steps 12 and 13" and "(step 13)". | `global/CLAUDE.md:82,174,178`; `spec §D11` | Say "step 9 goes, the later steps keep their numbers", or list those three lines under D11 and Files. |
| Suggestion / High | editorial | The new `next` value `merge-retry` is not added to the places that list `next` values: `check`'s fields and facts per value, Resume step 3's stage map, and auto start check 6's list for `run auto review`. D8 implies all three. | `plugins/my/bin/handoff-state.py:47-56`; `plugins/my/skills/handoff/SKILL.md:252-254,377-379`; `spec §D8` | Name the three places under D8 or in the Files row for `handoff-state.py`. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Contracts: `checked_base` (first review's Critical) | Now defined as `git merge-base <base> <branch>`, with an integration test for "A merges before B's checks" (spec §D8, §Testing) | Strong |
| Boundaries: start checks (first review's Critical) | They run only at a new launch and leave out the own slug. The cap, the slot and the first write are one locked `start` (spec §D3) | Strong |
| Boundaries: roadmap ownership | The `Blocked by` check lives only in D1, so `my:handoff` never reads the roadmap (spec §D3) | Strong |
| Failures: lock lifetime | A `flock` held through `execvp` and freed by the kernel; a 90 s default under Bash's 120 s; shared resources run in the background with 3600 s (spec §D4). | Strong |
| Lock coverage | `git add` sits inside the locked command (§D5). `merge` refuses staged changes (§D8 step 1). The undo is a checked `update-ref` (§D7). Hooks run through `git commit` with `GIT_INDEX_FILE` (§D6) | Strong |
| Fit with what exists | Reuses the state file, the common-dir layout and the fold script. The queue and the integrator were real candidates, with reasons in the brief (`docs/plans/2026-10-12-parallel-auto-runs-architecture.md:221-231`) | Strong |
| Spec rules | "How to read" comes first and lists the brief first. Risk, Dependencies and Trade-offs are present. The Delegation command passes. No UI, so no Visual Language section | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| Failures: resume in the merge phase | `SKILL.md:298-305` with spec §D8, §D10 rows 18, 19 | Medium |
| Failures spread: a failed squash commit | `plugins/my/bin/handoff-state.py:57-58,232-233`; `~/projects/zitamu/real-estate-webapp/.git/hooks/pre-commit:63-81` | Medium |
| Contracts: a commit that fails inside `commit` mode | spec §D7, §D10 | Medium |
| Isolation does not reach subagents | `SKILL.md:415-421,489-494`; spec §D9 | Medium |
| Goal 3's "never" for cited docs-only commits | `plugins/my/bin/git-fold-fixups.py:178-192`; `global/rules/docs-layout.md:76-77`; spec §D7 | Medium |
| Lock held by git's detached gc | scratch test; spec §D4 | Low |

## Not Applicable

None.

## Needs Investigation

- **The size of D1's multi-select.** `AskUserQuestion` takes a small, fixed number of options per question. Its schema was not visible in this review, so the limit is unchecked. With more startable rows than that limit, the answer cannot list them all in one question. To resolve, check the tool's option limit and say how D1 picks the rows it offers.
- **Several launches from one session.** D1 step 5 launches each pick with `/my:handoff auto …`. Launch step 6 ends with "print … and stop" (`SKILL.md:234-236`). Nobody has tried whether one session goes on to the next pick after the first launch stops. To resolve, try it with two fixture specs in the rehearsal, or say in D1 that the session invokes the skill once per pick and goes on.

## Reasoning

The System Model holds together. Each new script has one job. Lock `main`, the shared-file merge and the compare-and-swap merge divide the main checkout's writers cleanly, and the first review's two Critical findings and its design Warnings are settled in the text. What is left sits where the new merge phase meets the existing resume and restart rules, and where a hook can refuse a commit that is half-made in the shared checkout. Both can stop or block runs in ways the stop table does not handle, but each needs a sentence or a field, not a new approach.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the two top findings rest on `SKILL.md:298-305`, `handoff-state.py:57-58,232-233` and zitamu's hook, all opened in this review.
**Recommendation:** Settle the two High Warnings with the user: where `next` points during the merge phase, and the cleanup after a failed squash commit, and which cited commits the fold must protect. Then decide the `commit`-mode failure row, how subagents get Isolation, and the lock held by git's gc. Fix the three editorial rows, and approve without another full review unless a decision changes a component's job.
