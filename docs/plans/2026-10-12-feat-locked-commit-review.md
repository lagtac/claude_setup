# Review: main..feat/locked-commit

**Status:** review of main..feat/locked-commit, 2026-10-12. Sound: the branch does what the spec asks, and its only finding is a Suggestion. The multi-run integration test still commits with the old `sh -c` form, not with `locked-commit.py`. Answered by the fix round: the test now commits with `locked-commit.py`.

## Change Summary

The branch adds `plugins/my/bin/locked-commit.py`. The script checks its input, then runs `handoff-lock.py main` in its own place (`os.execv`). Under the lock, a `sh -c` stages the paths, commits them with `git commit -F <message file> -- <paths>`, prints `git show --stat`, and deletes the message file. Five instruction files had a copy of the long heredoc command. Each copy is now one `locked-commit.py -F <message file> <paths>` line, with the message written to a scratchpad file. The column-0 heredoc rule moves to the squash-merge command in `my:handoff`. Stop row 23 now names the script. Both READMEs describe it, and 17 end-to-end tests in `plugins/my/tests/test_locked_commit.py` cover it.

## Plan Alignment

The implementation matches the spec (`docs/plans/2026-10-12-locked-commit-spec.md`), D1 to D7 and Tasks 1 to 5. I checked each site against the repo, not only against the diff:

- D1/D2: the interface and the four steps match (`plugins/my/bin/locked-commit.py:20-21`, `:38-40`, `:100-102`). `handoff-lock.py` is found next to the script through `Path(__file__).resolve().parent` (`:38`), so a symlink on `PATH` still finds it.
- D3: the script refuses a missing `-F`, missing paths, an unknown option, an unreadable or blank file, a file inside the work tree, and a folder that is not a repository (`locked-commit.py:48-83`). Each refusal exits 64 with a `locked-commit:` line.
- D4: exit 75 and its `handoff-lock:` line pass through unchanged. The test at `plugins/my/tests/test_locked_commit.py:505-525` proves it.
- D6: the column-0 rule left Plan stage, step 7. It now stands once, at the squash-merge (`plugins/my/skills/handoff/SKILL.md:824-826`), and `SKILL.md:898-899` points to "Review stage, step 8, sub-step 1". I checked that pointer: the squash-merge block at `SKILL.md:817` is in Review stage (heading at `:697`), step 8 (`:788`), sub-step 1. The old text said "This holds for every heredoc in this skill". After the edit, `<<'EOF'` appears only at `SKILL.md:817` and `:892`, the two merge commands, and both are covered. D6's "three uses" premise holds.
- D7: every listed site changed: `global/CLAUDE.md:173`, `global/rules/docs-layout.md:168-175`, `plugins/my/commands/commit.md:11`, `plugins/my/skills/architect/SKILL.md:252-255`, `SKILL.md:241` (row 23), `:678`, `:834`, `:911`, `plugins/my/skills/handoff/README.md:360-365`, `README.md:119-121`. Each "Plan stage, step 7" pointer still expects only what step 7 holds: the stage-and-commit and the stat check.
- Task 1: the tests add two cases the spec did not list: an unknown option, and a relative path to a file inside the work tree. `test_message_file_kept_when_commit_fails` uses the unchanged `root.md` instead of `a.md`, because `a.md` is a new file in the fixture and would commit. Both changes fix the spec's sketch. They are not departures from it.
- Task 4: the two greps the spec asks for find nothing in `global`, `plugins` or `README.md`. The lint target was relaxed to "no new errors", and the spec records this as Risk 6.
- Task 5: the rehearsal result is in the body of an empty branch commit ("the rehearsal commit"), so the squash message can carry it. That is what the spec asks.

No deviation needs a row in the Issues table.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | The multi-run integration test still makes its `done`-mark commit with its own copy of the old `sh -c` command. So the test that runs several sessions against one `main` never goes through `locked-commit.py`, the path the instructions now prescribe. The unit tests prove the lock timeout, but no test has two locked commits taking turns through the new script. | `plugins/my/tests/test_parallel_runs.py:129-131` | Change `done()` to call `locked-commit.py -F <file> <path>`, with the message file in the test's temporary folder outside the repo. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| One lock implementation: the script runs `handoff-lock.py` in its own place and does not copy the lock path or the `autoDetach` settings | `plugins/my/bin/locked-commit.py:38`, `:100-102`; `plugins/my/bin/handoff-lock.py:71-77`, `:94-104` | Strong |
| No shell reads the message: it reaches git through `-F`, and only the resolved path reaches `sh` | `locked-commit.py:39-40`, `:101`; test `test_locked_commit.py:423-428` | Strong |
| Fails closed before the lock: no input that the script refuses changes HEAD or the index | `locked-commit.py:89-98`; `assert_refused` at `test_locked_commit.py:415-421` | Strong |
| Root cause treated: five copies become one script, and the column-0 rule stays only where heredocs remain | `SKILL.md:817`, `:824-826`, `:892`, `:898` | Strong |
| Matches sibling style: docstring with Usage and exit codes, `fail`/`parse`/`main`, a `-h` path | `handoff-lock.py:1-27`, `:42-67`, `:107-113` vs `locked-commit.py:1-31`, `:43-64`, `:86-90` | Moderate |
| The whole suite passes (144 tests), and the old form still works for sessions that loaded old text (Risk 4) | `python3 -m unittest discover plugins/my/tests` run in this review | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The parallel-runs integration test does not exercise the new script | `plugins/my/tests/test_parallel_runs.py:129-131` | Low |

## Not Applicable

None.

## Reasoning

The change does what the spec asks. Each instruction site names the script, and the remaining heredocs are exactly the two merge commands the spec leaves out of scope. Every cross-reference I followed lands on the step it names. The design reuses the existing lock instead of copying it. Input that the script refuses never reaches the lock, and git's own exit codes pass through as D4 says. Callers were found by text search only (`grep`, `git grep`), because this review had no symbol tool. The script has no code callers, only the Markdown sites listed above. The one finding is a gap in test coverage, not a flaw in the approach.

## Verdict

**Assessment:** Sound
**Confidence:** High. I read every touched site and its pointers in the live files, and the full test suite passes.
**Recommendation:** Squash-merge. Optionally, first move `test_parallel_runs.py`'s `done()` to `locked-commit.py`, so the integration test exercises the prescribed path.
