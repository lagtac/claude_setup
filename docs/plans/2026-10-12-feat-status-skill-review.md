# Review: main..feat/status-skill

**Status:** review of main..feat/status-skill, 2026-10-12. Mixed: the script-plus-skill split is sound and matches the spec, but one branch with no shared history (which the plugin's own `git-squasher` produces) turns the whole `branches` block into an empty error line and hides every unfinished branch. The fix round answered both Warnings: a branch with no shared history is compared with all of `main`'s history, and `SKILL.md` defines `main` as the base branch.

## Change Summary

The branch adds `plugins/my/bin/status-scan.py`, a read-only script that prints seven tab-separated blocks of facts: roadmap rows, order of work, open documents, the main checkout, worktrees, auto runs and branches that may hold unmerged work. It adds `plugins/my/skills/status/SKILL.md`, which runs the script once and judges "where we are", "what is next" and "what can run in parallel". It also adds 18 subprocess tests, one README entry, and one edited "Out of scope" line in the parallel auto runs spec.

Caller sweep: done by text search only (`grep -rn`); this reviewer has no symbol-reference tool. The payload removes or renames no symbol. The only callers of the new script are the skill and the tests.

## Plan Alignment

The implementation matches the spec (`docs/plans/2026-10-12-status-skill-spec.md`) closely. The block order, fields, row formats, 200-commit fixup depth, the 8-character line rule, the cap of 30 with a `skipped` line, the `live`-then-fallback runs source and the exit codes are all as D3 and D4 describe. The 18 tests match the Task 1 list one for one, and the suite passes (82 tests, all OK).

- `plugins/my/bin/status-scan.py:72-178` — Task 2's signatures differ. `checkout_facts`, `worktree_facts`, `branch_facts` and `base_branch` take `root`/`base` explicitly, and the helpers `main_root`, `worktree_list`, `changed_lines`, `read_roadmap` and `usage` were added. This is a justified, harmless deviation. Not an issue.
- `plugins/my/bin/status-scan.py:31-35` — exit 2 also covers a usage error (extra arguments). The spec names only two causes. This follows the `handoff-state.py` style. Not an issue.
- `plugins/my/bin/status-scan.py:228-256` — D4 is implemented as written. However, D4 and D3 together did not decide what happens to a candidate branch with no merge base. The code's answer, an error for the whole block, defeats Goal 4 in real repos (Issue 1).
- (missing) Task 4, the headless rehearsal, cannot be seen in a diff. The spec says to record it in the squash commit message. See Needs Investigation.
- `README.md` and `docs/plans/2026-10-12-parallel-auto-runs-spec.md:51-53` — Task 5 is done as worded.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | One candidate branch with no shared history makes `git merge-base` exit 1 with empty stderr. The `GitError` escapes `branch_facts`, so the whole `branches` block becomes `error<TAB>git merge-base main refs/heads/<b>: `, with no reason given. Every other branch check is lost with it. The trigger is ordinary: `git-squasher` creates `backup/squash-*` branches after rewriting history. | `plugins/my/bin/status-scan.py:241`, `:68`, `:311`; `plugins/my/skills/git-squasher/SKILL.md:34`. Reproduced in `~/projects/grispy2-web-ext`: all three local branches (the backup, `feat/field-classifier` 34 ahead, `feat/plane-a-events` 40 ahead) share no history with `main`, so the block errors on every run. A scratch repo with an orphan `backup/old` and a real unfinished `feat/z` printed only the error line, and `feat/z` was hidden. | Handle failures per branch. When `merge-base` fails, print a per-branch line (for example `no-merge-base<TAB><branch><TAB><subject>`) and go on, and have SKILL.md step 2 send those lines to the `git grep` check. Make `GitError` fall back to the exit code when stderr is empty. `worktree_facts` (`:178-179`) has the same weakness: one worktree whose git call fails takes down its whole block. Catch per worktree there too. |
| Warning / Medium | SKILL.md hard-codes `main` in the commands the model runs (`git diff main...<branch>`, `--name-only main...<branch>`) and in the block table. The script uses whatever branch is checked out in the main checkout. Unlike the spec (D3), SKILL.md never says "main" means that branch. | `plugins/my/skills/status/SKILL.md:38`, `:49`, `:72`; script `plugins/my/bin/status-scan.py:77-78`. On this machine `~/projects/mv3-tab-notes` has `ex/01-note-keys` checked out in its main checkout. There, the script measures against `ex/01-note-keys`, but step 2's `git grep` check and step 6's file lists diff against `main`, a different base. | Add one sentence to SKILL.md step 1: "`main` below means the branch checked out in the main checkout, as the script uses". Or name it `<base>` in the commands. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Facts and judgment are split as D2 decided. The script only reads, and the prose judgments (gates, spec relevance, overlap) stay in the skill. | `plugins/my/bin/status-scan.py:1-35`; `plugins/my/skills/status/SKILL.md:18-20`, `:57-80` | Strong |
| The branch line test does what it claims on the target repo. On this repo, 1 of 20 local branches is flagged (`feat/spec-review-off-path`, 1 line), against the 18 that `--no-merged` lists. That matches D4's measured result. | Run of `status-scan.py` in this worktree, `branches` block; `plugins/my/bin/status-scan.py:213-256` | Strong |
| Each block's errors are isolated, so a bad state file or a failing git call does not stop the other blocks, as D3 asks. | `plugins/my/bin/status-scan.py:308-313`; test `test_bad_state_file_is_error_line` | Moderate (undercut per branch by Issue 1) |
| The runs fallback matches the sibling branch's `live` contract: five fields, with an `unreadable` marker in the `next` field. Exit 2 from `live` on today's `handoff-state.py` was checked and triggers the fallback. | `plugins/my/bin/status-scan.py:184-210`; `feat/parallel-auto-runs:plugins/my/bin/handoff-state.py:175`; `handoff-state.py live` exits 2 on this branch | Moderate |
| Both roadmap formats parse correctly on real data: bullet rows here, and numbered table rows with `## Order of work` in grispy2-web-ext. | Scan output on both repos; `plugins/my/bin/status-scan.py:81-116` | Strong |
| Follows sibling conventions: docstring Usage block, `usage()`, base branch from the main checkout, and the test harness from `test_handoff_state.py`. | `plugins/my/bin/handoff-state.py:1-33`, `:252-255`; `plugins/my/tests/test_status_scan.py:1-115` | Moderate |
| Fast: 1.5 s on this repo with 20 branches. | Timed run | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| One branch with no shared history hides every branch result, and the error line gives no reason. | `plugins/my/bin/status-scan.py:241`, `:68` | Medium |
| The skill's follow-up commands assume the base is named `main`. | `plugins/my/skills/status/SKILL.md:49`, `:72` | Low |

## Not Applicable

None.

## Needs Investigation

- **Task 4 rehearsal.** The spec makes a headless `claude -p "/my:status"` run on this repo the only test of the skill's judgment (three sections, no squash-merged branch shown as unfinished, no writing command). Nothing in the range records it, because the spec puts the record in the squash commit message. Whether it ran, and passed, can only be checked at squash time. Resolve it by running the rehearsal and quoting its result in the squash message, as Task 4 says.

## Reasoning

The approach is right. The script collects mechanical facts, the skill makes the prose judgments, and the line test for squash-merged branches works on the repo it was measured on. Both roadmap formats parse correctly on real data. The one real defect is in the error handling's scope. D3's "one error line per block" rule is applied to a per-branch failure. Repos rewritten by the plugin's own `git-squasher` create that failure, so there the branch check, the main point of Goal 4, never gives an answer. That is a fix, not a redesign, so the verdict is Mixed rather than Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the top finding was reproduced in a scratch repo and in a real repo of the user's, and the code matches the spec elsewhere.
**Recommendation:** In `branch_facts`, catch the merge-base failure per branch and print a per-branch line; do the same per worktree in `worktree_facts`. Give `GitError` a reason when stderr is empty. Add a test with an orphan branch next to an unfinished one. Define "main" in SKILL.md step 1. Then run the Task 4 rehearsal.
