# Review: docs/plans/2026-10-12-locked-commit-spec.md

**Status:** review of docs/plans/2026-10-12-locked-commit-spec.md, 2026-10-12. Mixed: the design is sound, but the "prints nothing" `git grep` checks in Task 4 and Risk 2 can never pass, because the old command text stays in docs files and in this spec. The spec answers all five findings: four are fixed in its text, and the author decided finding 2 (stop row 23 names `locked-commit.py`).

## Spec Summary

The spec adds `plugins/my/bin/locked-commit.py`, which takes `-F <message file>` and paths, checks its input, then hands off with `exec` to `handoff-lock.py main` to run `git add`, `git commit -F`, `git show --stat` and delete the message file. The five copies of the long heredoc command become one line each. The column-0 heredoc rule in `my:handoff` moves to the squash-merge command, which keeps its heredoc. The two merge commands are out of scope.

## System Model

The caller sweep below was text-only (`grep -rn` and `git grep`). No symbol-reference tool was available.

| Component | Owns | Depends on | New / existing (verified at) |
| --- | --- | --- | --- |
| `locked-commit.py` | Argument parsing, input refusals (exit 64, `locked-commit:` stderr), the `sh -c` step list, deleting the message file on success | `handoff-lock.py` (next to it), `git`, `sh` | New |
| `handoff-lock.py` | Lock file path, `flock` wait and timeout, `autoDetach` settings, exit codes 64/74/75/126/127 | git common dir | Existing `plugins/my/bin/handoff-lock.py:1`–`27`, `exec` at `:126` |
| Message file | The commit message text | Written by the agent with the Write tool in the session scratchpad | New (convention) |
| Instruction copies (5) | The text that tells an agent how to make a locked commit | `locked-commit.py` | Existing `global/CLAUDE.md:173`, `global/rules/docs-layout.md:168`–`178`, `plugins/my/commands/commit.md:11`, `plugins/my/skills/architect/SKILL.md:248`–`256`, `plugins/my/skills/handoff/SKILL.md:565`–`586` |
| `my:handoff` column-0 rule | When heredoc lines must start at column 0 | The squash-merge (`SKILL.md:822`) and `handoff-state.py merge` (`SKILL.md:895`) heredocs | Existing `plugins/my/skills/handoff/SKILL.md:580`–`583`, `:828`, `:901` |
| `my:handoff` stop rows 18 and 23 | How an auto run reacts to a lock timeout or a lock-script failure | `handoff-lock.py` exit codes and its `handoff-lock:` stderr line | Existing `plugins/my/skills/handoff/SKILL.md:236`, `:241`, `:171`–`172` (not changed by the spec) |
| `ROADMAP.md` rows | The "One script for the locked commit" row and the new "Merges read a message file" row | None | Existing `ROADMAP.md:149`–`151`; the new row is not there yet |
| `test_locked_commit.py` | End-to-end tests of the script | `test_handoff_lock.py` style | New; the style source exists at `plugins/my/tests/test_handoff_lock.py` |

| From → To | What passes | Owner of what passes |
| --- | --- | --- |
| Agent → message file | Message text, through the Write tool | Agent |
| Instruction copies → agent | The one-line command | Instruction copies |
| Agent → `locked-commit.py` | `-F <file>`, paths, an optional `--timeout` | Agent |
| `locked-commit.py` → `handoff-lock.py` | `exec` with `main [--timeout] -- sh -c '<steps>' sh <file> <paths>` | `locked-commit.py` builds it; `handoff-lock.py` owns the lock |
| `handoff-lock.py` → `sh` → git | The step list run under the lock; the exit code goes back to the agent unchanged | `locked-commit.py` (steps), git (codes) |
| Exit code and stderr → `my:handoff` stop rows | 0, 64 (`locked-commit:` or `handoff-lock:`), 75, git's own codes | `locked-commit.py` and `handoff-lock.py`. The spec gives no row for the codes that are new. |

## Grounding

- `spec §D3` says a message file inside the work tree "blocks `my:handoff`'s fold check". The script runs only in a project with a "Parallel runs" section, and nothing folds there: rows 5, 16 and 17 "cannot arise there, because nothing folds" (`plugins/my/skills/handoff/SKILL.md:243`–`245`). The other reason, that `my:status` shows a dirty checkout (`plugins/my/skills/status/SKILL.md:37`), holds. Every other file, line range, row number and behaviour I checked holds. Small exceptions: `SKILL.md:565`–`588` runs two lines into step 8, which ends the old text at `:586`. The "Merges read a message file" row does not exist yet, as the spec says ("the new 💭 row").

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Warning / High | editorial | Task 4 requires `git grep -n "sh -c 'm=\$1"` and `git grep -n "locked form of Plan stage"` to print nothing, and Risk 2 uses the first as its check. Both strings stay in historical docs, and in this spec, so the checks can never pass. In auto mode a failed check could stop the run, or the agent could start editing old docs. | `docs/plans/2026-10-12-parallel-auto-runs.md:146`, `:966`; `docs/plans/2026-10-12-parallel-auto-runs-plan-review.md:35`; `docs/reports/2026-10-12-handoff-instructions-audit.md:168`, `:198`; spec §Context (line with the command) and §Out of scope ("the locked form of Plan stage, step 7") | Limit both greps to the live files: `git grep -n "…" -- global plugins README.md`. Use the same limit in Risk 2. |
| Warning / Medium | design | The stop table does not cover the new script's failures. Row 18 names `handoff-lock.py` exit 75. Row 23 covers "any other failure of `handoff-lock.py` or `handoff-state.py merge`". The rule at `:171`–`172` reads a code as the script's only when a `handoff-lock:` line is there. `locked-commit.py` adds exit 64 with a `locked-commit:` line, and git failures such as "nothing to commit" under it. D7 keeps only "A lock timeout is row 18", so an auto run has no row that names a refused or failed locked commit. | `plugins/my/skills/handoff/SKILL.md:171`–`172`, `:236`, `:241`; spec §D4, §D7 | Decision for the author: name `locked-commit.py` in row 23, or state which row its 64 and git failures map to. Today's "path with no change is not listed, and that is correct" case (`SKILL.md:560`–`562`) also changes, because a commit where every path is unchanged now exits 1. |
| Warning / Medium | editorial | D6 and Out of scope say the roadmap row is corrected (it still says "reads the message from stdin") and a new 💭 row "Merges read a message file" is added. `ROADMAP.md` is in neither §Files nor any Task, and the spec does not say which commit carries these edits. | `ROADMAP.md:149`–`151`; spec §D6 ↔ §Files, §Tasks | Add `ROADMAP.md` to §Files and to a Task, or say that the edits go into the spec commit on `main`. |
| Suggestion / High | editorial | The D3 reason for refusing a message file in the work tree cites the fold check. No fold runs in a parallel project, the only place the script is used. | `plugins/my/skills/handoff/SKILL.md:243`–`245`; spec §D3 | Drop the fold-check clause and keep the `my:status` reason. A file in the work tree would also be swept up by any later `git add` of a folder. |
| Suggestion / High | editorial | `commit.md` step 4 still says "Use a HEREDOC to preserve formatting". The Parallel runs paragraph lists which steps change (3, 5, 7) but not step 4. D7 changes only the command in that paragraph, so the two instructions about how to write the message stay in conflict. | `plugins/my/commands/commit.md:11`, `:19`; spec §D7 | In the new paragraph, say that step 4 writes the message to the scratchpad file instead. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Boundaries | The lock stays in one place. The new script only checks input and builds the step list, then `exec`s `handoff-lock.py`, which itself `exec`s (`handoff-lock.py:126`). The lock path and `autoDetach` are not copied. | Strong |
| Contracts | Exit codes 74, 75, 126 and 127 pass through unchanged, and the `handoff-lock:` stderr line survives `exec`, so row 18 detection still works (`SKILL.md:236`). | Strong |
| Failures | D4 and D5 keep the message file on any failure and delete it only after `git show` succeeds, inside the lock. The message is never lost, and the next Write is never blocked after a success. | Moderate |
| Fit | The script sits beside `handoff-lock.py` in `plugins/my/bin/`, like the other helpers. The scratchpad-for-temp-files pattern matches `architect/SKILL.md:33` and `spec-review/SKILL.md:39`. | Strong |
| Scope | The merges are left out for a stated reason (a `handoff-state.py` interface change), and that work is kept in a new row. | Moderate |
| Spec rules | "How to read this spec" comes first with paths. Risk, Dependencies and Trade-offs are present. There is no UI. | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| Contracts (stop rows) | The new exit-64 refusal and git failures map to no stop row (`SKILL.md:236`, `:241`). | Medium |
| Self-containment | The acceptance greps cannot pass. The ROADMAP edit is not in the task list. | Medium |
| Exit-code overlap | Codes 126 and 127 are said to mean "Nothing ran". `sh` also returns 127 when `git` is not found inside the step list. The case is unlikely, but the D4 table is not exact. | Low |

## Not Applicable

- Criterion 3, off-path UI events: the spec adds no UI.
- Criterion 6, Visual Language: the spec adds no UI.

## Reasoning

The System Model has one lock owner (`handoff-lock.py`) and a thin new front end. Ownership is clean, and the exit-code contract passes through intact, so the chosen approach holds. The gaps are at the edges: the agent-facing stop rows do not name the new script's own failures, the acceptance greps match text that stays in docs, and the ROADMAP edit has no task. None of these needs rework, but the stop-row gap is a decision for the author. That makes the spec Mixed rather than Sound.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every file, line range and exit code the spec cites was opened, and the grep failure was reproduced against the current tree.
**Recommendation:** Narrow the Task 4 and Risk 2 greps to `global plugins README.md`. Add `ROADMAP.md` to Files and Tasks. Fix the D3 and `commit.md` step 4 wording. Ask the user how `my:handoff` stop rows treat `locked-commit.py` exit 64 and git failures.
