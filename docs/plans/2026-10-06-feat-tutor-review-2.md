# Review: main..feat/tutor

**Status:** review of main..feat/tutor, 2026-10-06. Final re-review after the fix round. Sound: the four earlier findings are answered and the code matches the approved spec. The top finding is new: the `progress.md` template still calls **Review** "oldest first" (`templates.md:91`), which the approved D7 queue rule no longer holds. Answered by the fix round and the Risk section; shipped in 1e69584.

## Change Summary

The branch adds the `my:tutor` skill (`SKILL.md`, `method.md`, `templates.md`) and the `tutor` output style. It also adds a "Learning workspaces" section and a Precedence exception to `global/CLAUDE.md`, two marker checks to `plugins/my/hooks/hooks.json`, and `README.md` entries. The fix round did several things. It changed the red-flag reason, the README Hooks bullets, the qualified `method.md` references in the style and Task 5's guarded-write assertion. It added code-review fixes: a `startup|clear` matcher, `CLAUDE_PROJECT_DIR`, a tracked-file check, a stop when the folder already exists, and a way to tell whether the style is active. It also added the four spec changes the user approved (D3, D4 step 7, D7 queue, D10 Risk bullet).

Caller sweep: this review had no symbol tool, so every sweep was a text search (`grep -rn`). Nothing was renamed or removed, so no caller can be orphaned. I ran both hook commands by hand with `bash -c` in a workspace root, a workspace subfolder, a normal repo and a folder outside any repo, and once with `CLAUDE_PROJECT_DIR` unset. Every case gave the expected output, and `hooks.json` parses with `jq`.

## Plan Alignment

The implementation matches the spec's Tasks 2, 3, 4, 6, 7 and 8 (the `README.md` part), including the approved changes:

- D3's suggested answers: `plugins/my/skills/tutor/SKILL.md:44-49` (case 1 for a new app, case 3 for this repo's code, case 2 only on request), and the existing-folder stop at `SKILL.md:63-65`, as in spec D3 case 1.
- D4 steps 1-10: `SKILL.md:99-137`. The tracked-file check in step 6 (`:110-112`) and the test runner in step 7 (`:118-123`) match spec D4. `templates.md:45` adds **Test command**, and `method.md:16` allows the runner config after approval.
- D7's queue: `method.md:67-72` matches the approved rule. The template does not (see Issues).
- D2/Task 6 hooks: `hooks.json:10` and `:26-35` match Task 6's `startup|clear` group and the `CLAUDE_PROJECT_DIR` form.
- D10: `global/output-styles/tutor.md:15-23` has all the D10 items. It invokes `my:tutor` before `anthropic-skills:learn`, the reverse of D10's list order. D10 does not set an order, so this is not a finding.
- Task 5 assertion: `docs/plans/2026-10-06-tutor-spec.md:517-522` now checks the attempted guarded writes, which matches the Risk bullet at `:393-397`.
- (missing) The Task 8 `ROADMAP.md` row belongs to the `done` commit on `main`, so its absence here is correct.

Earlier findings, checked:

- README Hooks section: fixed (`README.md:132-137`).
- `method.md` named by bare file name in the style: fixed (`tutor.md:19-20`, `:23`, `:29`).
- Task 5's outdated `check-ignore` assertion: fixed (spec `:517-522`).
- False reason in the red-flag row: partly fixed. See Issues.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | **New.** The `progress.md` template still describes **Review** as "Practised concepts for recall questions, oldest first." The approved D7 rule moves a concept to the end after a correct answer, so the queue is no longer ordered by age. `progress.md` is written from this template and read at the start of every session, so it repeats the old rule beside the new one in `method.md`. | `plugins/my/skills/tutor/templates.md:91`; `plugins/my/skills/tutor/method.md:70-72`; spec `:271-274` | Change the line to "Practised concepts for recall questions. Ask from the front; see `method.md`, 'Concept status'." |
| Suggestion / High | **Carried over, partly fixed.** The red-flag row now says "The 'Git' commands below and later sessions expect" the names `<name>-learning` and `learning`. The "Git" section below uses the placeholder `<learning branch>`, not the name `learning`. The only command that uses the name is the update command above it, in Setup. The stated reason still points at the wrong place. | `plugins/my/skills/tutor/SKILL.md:148`; `:198` (`git switch <learning branch>`); `:82-83` | Point at the case 3 update command in Setup and at the user, who needs to find the clone, or drop the "Git commands below" clause. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Hook checks work in every location tested, including a subfolder and an unset `CLAUDE_PROJECT_DIR`. The `startup\|clear` matcher stops the instruction from being injected again after a summary. | `plugins/my/hooks/hooks.json:10`, `:26-35`; manual `bash -c` runs in this review | Strong |
| Setup now stops safely before it could harm an existing folder or tracked file: an existing workspace folder, a tracked `settings.local.json`, and an unrelated `docs/learning/` | `SKILL.md:50-51`, `:63-65`, `:110-112` | Strong |
| The test runner respects the still-binding "no new dependencies without approval" rule, and `method.md`'s write table names the one exception | `SKILL.md:118-123`; `method.md:16`; `global/CLAUDE.md` "Learning workspaces" | Strong |
| The check for an active style uses evidence the model actually has (its own system prompt text), not the settings file, which the setup session also has | `SKILL.md:158-163`; `tutor.md:7` | Moderate |
| The core rule (the student writes the target code; level 5 only after a repeated request) stays stated in the style, the method and the skill | `tutor.md:27-31`; `method.md:11-26`; `SKILL.md:175-178` | Strong |
| The global exception is listed explicitly, and Precedence names it | `global/CLAUDE.md:12-32`, `:83` | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The template's "oldest first" contradicts the approved queue rule | `templates.md:91` | Low |
| The red-flag reason still points at commands that use a placeholder | `SKILL.md:148`, `:198` | Low |
| The global section loads in every session in every project. A wrong marker match would relax workflow rules for a real project. The specific marker path and the setup stops limit this, and Risk records it. | `global/CLAUDE.md:12-32` | Low |

## Not Applicable

None.

## Reasoning

All five dimensions applied. The fix round answered the four earlier findings: three fully, and one partly (the red-flag reason). The code-review fixes and the four approved spec changes match the spec text line for line. I checked the hook behaviour by running the commands by hand, not only by reading them. The two remaining findings are both Suggestions. They concern wording that could slightly mislead the model, not the design or the wiring. Nothing was removed or renamed, so there is no blast radius beyond the always-loaded global section, which is guarded and listed in Risk.

## Verdict

**Assessment:** Sound
**Confidence:** High. The design, the spec alignment and the hook behaviour were checked against the repo and by execution. The remaining findings are wording only.
**Recommendation:** This is the final re-review, so under "One fix round per review" these Suggestions are not a new fix round. Fix them as trivial edits before the squash-merge, or record them in the spec's Risk section. Then squash-merge.
