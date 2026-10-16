# Review: main..feat/design-system-skill

**Status:** review of main..feat/design-system-skill, 2026-10-16. Mixed: the fix round answers every first-round finding correctly, but it adds one new rule to `refresh` step 1 that reads a "globs match no tracked file" refusal as "the files were deleted". So a folder rename or a hand-edited glob silently removes a pattern whose copies still exist.

## Change Summary

The branch adds `plugins/my/bin/ds-count.py`, which counts the search patterns in the `ds-patterns` block of `docs/DESIGN-SYSTEM.md`, and 30 subprocess tests for it. It also adds the `my:design-system` skill (`audit`, `refresh`, `sync`), plus prompt text in `global/methods/my.md`, `global/rules/docs-layout.md` step 13, the `my:handoff` shared-doc list, criterion 6 of the spec reviewer, the README and the kit name guard. This is the final re-review. It covers the fix round: Risk items 11 to 15, the quoted staleness command and the `is-ancestor` check in both copies, the no-inventory skip, `--deduplicate` and the empty-glob refusal in the script, and three new `refresh` rules.

## Plan Alignment

The branch matches the plan task by task, as the first review found. Every first-round finding was answered:

- Warning 1 (`sync` and the zitamu regression never ran) is now Risk item 11 (`docs/plans/2026-10-16-design-system-skill.md:810-815`). Warning 2 (the criterion 6 bullet was not isolated) is Risk item 12 (`:816-821`). Both are known limits, so this review does not raise them again.
- Suggestion 1: the staleness command is quoted in `plugins/my/skills/design-system/SKILL.md:209` and in `global/methods/my.md:131-132`.
- Suggestion 2: `global/methods/my.md:137-138` now skips the paragraph in a project with no inventory.

The tests pass: 233 in `plugins/my` and 40 in `plugins/kit`. The lint counts still match the Global Constraints: 1 for `global/methods/my.md` and 0 for every other edited file. I ran a mutation check on the three new tests. With `--deduplicate` removed, `test_conflicted_file_counted_once` fails (4/4 instead of 2/2). With the `and v` guard removed, `test_empty_glob_refused` and `test_empty_exclude_refused` both fail.

Deviations:

- `plugins/my/skills/design-system/SKILL.md:209`, `:213-215` and `global/methods/my.md:131-135`: the staleness command is quoted and gains an `is-ancestor` test. This changes text that the spec (D11) and plan Task 3 Step 3 (`plan:469-473`) fix word for word. Justified: it answers the first review's reproduced bug. The spec and plan still show the unquoted command.
- `global/methods/my.md:85`: step 1 gains the «new: `<name>`» clause, beyond plan Task 3 Step 2's text. Justified: it makes step 1 agree with the reviewer's «new» sub-bullet and the UI Design paragraph, which already allowed the label.
- `plugins/my/skills/design-system/SKILL.md:190-191` and `:203-204`: `refresh` fills a `none yet (row <N>)` Sources line, and skips staleness for a new app. Justified: this is consistent with spec D11 and `audit` step 7.
- `plugins/my/skills/design-system/SKILL.md:186-189`: the new step 1 rule. It contradicts the spec's script contract (`docs/plans/2026-10-16-design-system-skill-spec.md:205`, "globs match no tracked file at all, which is a typo, not an unused component"). Not justified as written: see the Issues row.
- `docs/plans/2026-10-16-design-system-skill.md:838`: Testing Strategy still says 26 unit tests. There are 30 (203 + 30 = 233 matches the run).

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | The fix round's new `refresh` step 1 rule treats every "globs match no tracked file" refusal on a line that already has counts as a deletion, and removes the line and its part 2 or 3 row. Two other causes give the same refusal. The first is a folder rename: I reproduced it in a scratch repo, where `git mv web/admin web/staff` gives the identical message while the `<input>` copy still exists. The second is a hand-edited glob, which the template invites ("Edit the search keys by hand"). For a `hand-built` line the loss is silent and permanent until the next `audit`, because `refresh` may not add `hand-built` lines (step 3, D6). In an auto run at step 13 nobody sees it, so later spec reviews stop flagging those copies. This undermines dimension 3 (a fallback that masks a failure), and it is a plan deviation against spec line 205. | `plugins/my/skills/design-system/SKILL.md:186-189`, `:107`; `plugins/my/bin/ds-count.py:219`; `docs/plans/2026-10-16-design-system-skill-spec.md:205` | The rule exists for a real reason: without it, one deleted pattern blocks every later `refresh`, including step 13 in an auto run (D5). So the fix must tell the three cases apart, not just stop. A rename (`git log -M --diff-filter=R --name-status -- '<glob>'`) means: point the glob at the new path. A glob edited since the last inventory commit means: a typo, so stop and name the line. Only a deletion with no rename means: retire the line. Under the one-fix-round rule, this can go into Risk as a known limit instead (see Recommendation). |
| Suggestion / High | The plan's Testing Strategy still says 26 unit tests. The branch has 30. | `docs/plans/2026-10-16-design-system-skill.md:838`; `plugins/my/tests/test_ds_count.py:231-252` | Change "26" to "30" when the plan is marked `done`. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The quoting fix is correct, and both copies now agree | `plugins/my/skills/design-system/SKILL.md:209`; `global/methods/my.md:131-132`; the first review reproduced the unquoted bug | Strong |
| The script fixes treat their root causes, and each has a test that goes red without its fix | `ds-count.py:77`, `:132-133`; `test_ds_count.py:231-252`; the mutation runs in Plan Alignment | Strong |
| The no-inventory skip closes the Small-change gap the first review found | `global/methods/my.md:137-138` beside the trigger row at `:58` | Moderate |
| The new-app path now works end to end: `refresh` fills the `none yet (row <N>)` line once the starting row ships, and staleness then reports the artifact as `none yet` | `SKILL.md:190-191`, `:203-204`, `:213-215`; `audit` step 7 | Moderate |
| The `is-ancestor` test catches a synced commit that a fold replaced, or one that no longer exists, where `git log` alone could print nothing to stdout | `SKILL.md:213-215`; `global/methods/my.md:134-135` | Moderate |
| The verification gaps are now recorded honestly, each with a "Detect:" clause | `docs/plans/2026-10-16-design-system-skill.md:810-821` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| A refusal that the spec defines as "a typo" is now read as "deleted" inside `refresh`, the mode that runs most often, and in auto runs | `SKILL.md:186-189`; spec `:205` | Medium |
| The spec and plan still show the old, unquoted staleness command, so anyone who reads them after the merge sees the version with the bug | spec D11; `plan:469-473` | Low |

## Not Applicable

None.

## Reasoning

The fix round is right on every point the first review raised. Each script fix has a test that fails without it, and the prompt fixes agree across `SKILL.md` and `my.md`. The one new problem came from the same round. A rule meant to unblock `refresh` after a real deletion also fires on a rename or a glob typo, and then it removes data without telling anyone. That is a Warning, not a Critical: the loss is in a docs file that git keeps, and the next `audit` finds the copies again. I found no orphaned reference. The change removes and renames nothing, and the caller sweep was text-only (grep), with no symbol tool. I read the payload, the plan copy, the worktree's `SKILL.md` `refresh` section, the UI Design section of `my.md` and both git hooks. For everything else I relied on the payload and the first review.

## Verdict

**Assessment:** Mixed
**Confidence:** High. The new finding is reproduced in a scratch repo, and every fix-round test was checked to fail without its fix.
**Recommendation:** This is the final re-review, so under the one-fix-round rule, add the `refresh` step 1 finding to the plan's **Risk** section as a known limit. Suggested Detect clause: a step-13 commit that removes an inventory row while its pattern still appears in the code. If the user prefers to fix it now, change step 1 to tell a deletion apart from a rename or a hand edit, as the Issues row says. Correct the test count at the `done` mark. Then squash-merge.
