# Review: main..feat/design-system-skill

**Status:** review of main..feat/design-system-skill, 2026-10-16. Mixed: the design is sound and matches the plan, but `sync` (the only mode that publishes outside the repo) has never run, and the rehearsal never showed the new criterion 6 bullet working on its own.

## Change Summary

The branch adds `plugins/my/bin/ds-count.py`, which counts the search patterns stored in the `ds-patterns` block of `docs/DESIGN-SYSTEM.md`, and 27 subprocess tests for it. It also adds the `my:design-system` skill, with three modes: `audit`, `refresh` and `sync`. The rest is prompt text: a task-class row, a Visual Language sentence and a UI Design paragraph in `global/methods/my.md`, a refresh clause in step 13 of `global/rules/docs-layout.md`, `docs/DESIGN-SYSTEM.md` added to the `my:handoff` shared-doc list in three places, a new criterion 6 bullet in the spec reviewer, README entries, the kit name guard, and the rehearsal record in the plan.

## Plan Alignment

The implementation matches the plan task by task. Every Decision (1 to 13) is in the script or the skill. The edits in Tasks 3 to 5 use the plan's text word for word. The lint counts match the Global Constraints: 1 for `global/methods/my.md` and 0 for every other edited file, measured at the branch head. Deviations:

- `plugins/my/tests/test_ds_count.py:227`: one extra test, `test_bool_count_refused` (27 tests, not the plan's 26; 203 + 27 = 230 matches the run). Justified: it covers Decision 10's `bool` case.
- `plugins/my/skills/design-system/SKILL.md:144` and `:191-193`: the "exclude the wrapping component" sentences in `audit` step 3 and `refresh` step 2. They came from the rehearsal fix round, which Task 6 Step 7 allows. Justified.
- `docs/plans/2026-10-16-design-system-skill.md:802-809`: Risk items 9 and 10 were added from the rehearsal. They are known limits, not findings.
- `docs/plans/2026-10-16-design-system-skill.md:868-872`: Task 6 Step 6 (the zitamu regression) and Task 7 (`sync`) were skipped by the user. The plan allows a skip for Task 7 (`:724-725`, "On a no, record 'skipped by the user'"), so this is not a deviation in itself. It leaves the work unverified, though: see the first Issues row.
- `docs/plans/2026-10-16-design-system-skill.md:858-863`: Task 6 Step 5, "spec 1 without the inventory", is recorded as "partial". Task 6 Step 7 (`:692`) says a failed check is a bug to debug, fix and rerun on a fresh fixture. The record blames the test's premise instead and moves on. This is a deviation from the plan's own rule: see the second Issues row.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | `sync` has never run: it is the only mode that publishes outside the repo (to claude.ai), and the zitamu regression (spec Testing item 4) has not run either. Its prompt text is unverified: create or revise, the README "Not synced" list, the Sources write, and whether the staleness command is clean afterwards. The Risk section does not list this as a known limit. | `docs/plans/2026-10-16-design-system-skill.md:868-872`; `plugins/my/skills/design-system/SKILL.md:214-235`; plan Risk `:770-809` (no such item) | Either rehearse `sync` with the user's yes (a throwaway fixture artifact still publishes, so it still needs that yes), or add "sync and the zitamu regression are unrehearsed" to Risk as a known limit. |
| Warning / Medium | Spec Testing item 3 ("the new criterion 6 bullet, in isolation") was never shown. Without the inventory, the reviewer still raised the same `design` finding through criterion 4, from the code. So the first new sub-bullet ("built in the page where a listed component does the job") may duplicate criterion 4 whenever the component can be found in the code. The name sub-bullet and the «new» sub-bullet did show value (specs 2 and 3). The plan's rule for a failed check was not followed. | `docs/plans/2026-10-16-design-system-skill.md:858-863`, `:692`; `plugins/my/skills/spec-review/spec-reviewer-prompt.md:70-71` | Rerun on a fixture where code search cannot find the component (for example, a component whose name does not match the element), or record the gap in Risk with the user's acknowledgement. |
| Suggestion / High | The staleness command leaves its path placeholders unquoted. With a Sources name pattern such as `web/components/Z*.vue` (the skill's own example), the shell expands the glob to the files that exist now. A component deleted since the last sync is then not matched, the command prints nothing, `sync` never runs, and the artifact keeps the deleted component. Reproduced in a scratch repo: unquoted prints nothing, quoted prints the deleting commit. | `plugins/my/skills/design-system/SKILL.md:202`, `:44-45`; `global/methods/my.md:131-132` | Quote the placeholders in both copies (`'<tokens file>' '<components folder>'`), so git expands the pattern, not the shell. |
| Suggestion / High | The new UI Design paragraph does not say what to do in a project with no `docs/DESIGN-SYSTEM.md`. That case happens: a Small change that adds a state needs a canvas but never triggers `audit`, and the trigger row covers only Medium and Large. The paragraph's only skip is for a new app with no tokens file. | `global/methods/my.md:127-135`, `:58` | Add one clause: "In a project with no `docs/DESIGN-SYSTEM.md`, skip this." |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Counts are produced by a script, which treats the root cause | The spec's D4: a model recounting each time phrases the search differently. `plugins/my/bin/ds-count.py:338-360` counts from stored regexes over git-tracked files only | Strong |
| The script refuses before it writes | It validates every line (`ds-count.py:304-326`), counts every line (`:414-422`), then writes atomically with the file's mode kept (`:374-386`). Tests: `test_duplicate_name_refused`, `test_empty_match_regex_refused`, `test_unclosed_block_refused` | Strong |
| The no-match check runs before the excludes (Decision 2), so a finished extraction reads 0/0 and a glob typo still refuses | `ds-count.py:416-418`; `test_excludes_leaving_no_file_report_zero`, `test_glob_matching_no_file_refused` | Strong |
| Matches sibling conventions | Docstring form and test helpers copy `status-scan.py` and `test_status_scan.py` (`test_ds_count.py:803-854`); the skill's commit rules mirror `plugins/my/skills/architect/SKILL.md:246-254` | Moderate |
| The shared-doc list is complete | A text search for "shared doc" across `plugins/` and `global/` finds only the three edited places plus the two back-references at `handoff/SKILL.md:1012` and `:1091`. `DOCS_PATHS` already covers `docs/` (`handoff-state.py:152`) | Strong |
| Step 13 reaches auto runs with no handoff edit | `handoff/SKILL.md:981` and `:1052` set the `done` marks "as the project's rules say", which is `docs-layout.md:173-177` | Moderate |
| Rehearsed end to end for `audit`, `refresh` and step 13 | `docs/plans/2026-10-16-design-system-skill.md:829-857` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The outward-facing mode is unverified | `docs/plans/2026-10-16-design-system-skill.md:871-872` | Medium |
| The new reviewer sub-bullet's added value is not isolated | `docs/plans/2026-10-16-design-system-skill.md:858-863` | Medium |
| The staleness check misses deletions when the components source is a name pattern | `plugins/my/skills/design-system/SKILL.md:202` | Low |
| A global rule is silent on canvases in a project with no inventory | `global/methods/my.md:127-135` | Low |

## Not Applicable

None.

## Needs Investigation

- **Whether `sync` works against the Artifact tool's real Design System type.** It has never run (see the first Issues row). Its behaviour depends on the type's `from-code.md` and its re-sync rules, which this review cannot exercise. One `sync` run with the user's yes would resolve it.

## Reasoning

The approach is right. It puts the counts in a tested script and the judgment in the skill. It hooks the refresh into step 13, the one place the `done` marks already pass through, and it extends the shared-doc list everywhere it appears. I found no orphaned reference: the change removes and renames nothing, and the sweep was text-only (grep), with no symbol tool. The Warnings are verification gaps, not design flaws: `sync` and the zitamu regression never ran, and the isolation test for the criterion 6 bullet did not prove what it set out to. The two Suggestions are small text fixes in prompt rules that reach every project on the method.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. The script and the prompt edits were read in full, and the tests and lint were checked. The two Warnings rest on rehearsal records, not on runs I could repeat.
**Recommendation:** Before the squash-merge, either rehearse `sync` with the user's yes or record it and the zitamu regression as unrehearsed in Risk. Do the same for the criterion 6 isolation gap. Quote the staleness command's placeholders in `SKILL.md:202` and `my.md:131-132`, and add the no-inventory skip to the UI Design paragraph.
