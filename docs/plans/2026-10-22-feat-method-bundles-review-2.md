# Review: main..feat/method-bundles

**Status:** review of main..feat/method-bundles, 2026-10-22. Sound: the fix round fixes what it set out to fix and breaks nothing; two Suggestions remain, a README command that does not run from the folder it names, and plan text that still puts the `/kit:setup tutor` call in setup step 6.

## Change Summary

The branch is batch 1 (Tasks 1–9) of the method-bundles plan. It makes `my`, `tutor` and `sp` method plugins whose rules are a forced output style. It adds `plugins/kit/bin/claude-method` as the one reader of the method list, and it rewrites the start check (`method-guard.py`) and `/kit:setup` to call that script. It also folds the `plain` style into the core and moves the engineering rules to a path-scoped `global/rules/engineering.md`. The fix round changed three things:

- It moved the tutor skill's `/kit:setup tutor` call from setup step 6 to the end of step 8, after the curriculum commit, and reworded step 6's guard on a tracked `settings.local.json`.
- It changed the README's `tutor:tutor` entry to start with `claude-method tutor`.
- It added five known limits to the plan's Risk section and committed the first review.

## Plan Alignment

Tasks 1–9 match the plan. The first review checked each task, and the fix round touched none of the code it checked (`claude-method`, `method-guard.py`, the tests, `/kit:setup`). One deviation is new in the fix round:

- `plugins/tutor/skills/tutor/SKILL.md:123-129`: the `/kit:setup tutor` call sits at the end of setup step 8. The plan puts it as "a new last bullet" of setup step 6 (`docs/plans/2026-10-20-method-bundles.md:693-696`). The plan's Trade-Offs section says the same thing (`docs/plans/2026-10-20-method-bundles.md:1089-1091`).
  - **The move is justified.** At step 6, step 4's `learning` scope line in `CLAUDE.md` is not committed yet. `/kit:setup`'s uncommitted-edits check (`plugins/kit/skills/setup/SKILL.md:114-117`) would then stop and ask whether to put the user's own edit into the setup commit. At the end of step 8, that line and the curriculum are committed.
  - **The plan's reason still holds.** The plan avoided a new numbered step so that steps 7 to 10 keep their numbers. The move adds no step, so `templates.md:73` "(setup step 6)" is still right: step 6 still writes the ignore entries.
  - It also matches the spec, which says only "A new step calls `/kit:setup tutor <workspace path>`" (`docs/plans/2026-10-20-method-bundles-spec.md:187-188`).
  - **What is left is the record.** The fix round edited the plan's Risk section but left the step 6 text at lines 694 and 1089. It is listed below as a Suggestion.
- The five Risk entries the fix round added (`docs/plans/2026-10-20-method-bundles.md:1125-1142`) are known limits, so they are not findings.
- Tasks 10–12 and the batch 1 marks are out of scope for this branch, as the caller said.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | The README fix tells the user to run `plugins/kit/bin/claude-method tutor` "in the folder that will hold the new workspace". The default for that folder is `~/projects/`. The path is relative to this repo, so it does not exist there: `cd ~/projects && test -x plugins/kit/bin/claude-method` reports it missing. Every other command the README tells the user to run uses `~/projects/claude-setup/…`. The plan's rollout step 5 writes the same call as `~/projects/claude-setup/plugins/kit/bin/claude-method tutor`. | `README.md:189-190`; compare `README.md:31-32`, `README.md:77-78` and `docs/plans/2026-10-20-method-bundles.md:985` | Write `~/projects/claude-setup/plugins/kit/bin/claude-method tutor`. Batch 2 Task 12 can shorten it to `claude-method tutor` once the `~/bin` symlink exists. |
| Suggestion / High | The fix round moved the `/kit:setup tutor` call to the end of setup step 8. The plan still says it is a bullet of setup step 6, in Task 5 Step 5 and in Trade-Offs. The move is justified (see Plan Alignment), but the plan now gives a placement and a reason that the code does not follow. | `plugins/tutor/skills/tutor/SKILL.md:123-129`; `docs/plans/2026-10-20-method-bundles.md:694`, `docs/plans/2026-10-20-method-bundles.md:1089-1091` | Change the Trade-Offs bullet: the call ends setup step 8, after the curriculum commit, so `/kit:setup` finds no uncommitted `CLAUDE.md` scope line, and no step is renumbered. Or name the deviation in the squash commit body. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The fix round fixes the cause. `/kit:setup` refuses to commit silently over uncommitted edits in `CLAUDE.md`. Running it after the commit that holds the scope line removes that conflict, and does not weaken the check. | `plugins/tutor/skills/tutor/SKILL.md:123-129`; `plugins/kit/skills/setup/SKILL.md:114-117` | Strong |
| No step is renumbered, so the step numbers other files cite stay true. The only outside citation, `templates.md:73` "(setup step 6)", is about the ignore entries, which step 6 still writes. | `plugins/tutor/skills/tutor/templates.md:73`; `plugins/tutor/skills/tutor/SKILL.md:109-116` | Strong |
| The reworded step 6 guard says what can really happen. `/kit:setup` edits `.claude/settings.local.json` only when the file exists, and only to remove method keys or an `outputStyle` of `plain` or `tutor`. The guard now calls that "the edit `/kit:setup` may make there (step 8)". | `plugins/tutor/skills/tutor/SKILL.md:110-113`; `plugins/kit/skills/setup/SKILL.md:134-136` | Moderate |
| The skill can call `/kit:setup`. Its frontmatter has no `disable-model-invocation`, so the tutor skill can invoke it. Its path argument lets the session run from the parent folder. Its commit lands on the learning branch before step 9 branches off it, so each exercise branch has the method keys. | `plugins/kit/skills/setup/SKILL.md:1-12`, `:45-47`; `plugins/tutor/skills/tutor/SKILL.md:123-131` | Moderate |
| The README now names the real entry point: the `tutor` plugin must be on first. That settles the first review's Suggestion in substance. Its "folder that will hold the new workspace" fits the skill's rule that a case 1 or case 3 workspace folder must not exist yet. | `README.md:186-190`; `plugins/tutor/skills/tutor/SKILL.md:63-65` | Moderate |
| Nothing regressed. Both suites pass at the branch head (kit 103, my 292, rerun in this pass). The skill still holds the string `test_tutor_style_and_skill_use_new_names` asserts. The plan and the first review cite no commit from this branch. | `plugins/kit/tests/test_neutral_core.py`; `plugins/tutor/skills/tutor/SKILL.md:126` | Strong |
| The whole range keeps the strengths the first review found: one owner of the method list, text moved word for word, and no orphaned references to removed paths. The fix round changed none of those files. | `plugins/kit/bin/claude-method:71-108`; `plugins/kit/hooks/method-guard.py:56-75`; `docs/plans/2026-10-22-feat-method-bundles-review.md` | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The README's start command does not run from the folder it names. | `README.md:189-190` | Low |
| The plan text and the skill disagree about where the `/kit:setup tutor` call sits. | `docs/plans/2026-10-20-method-bundles.md:694`, `:1089-1091` | Low |

## Not Applicable

None.

## Needs Investigation

- **The first review's open item is settled.** The caller reports that the code stage's saved headless runs for Task 4, Task 6 and Task 8 cases A and B show zero `permission_denied` events. Both Task 8 fixtures ended with the expected keys and a `chore: switch to the … method` commit. I did not read those stream files myself.
- **Nothing tests the call from the tutor skill to `/kit:setup`.** No headless run takes `tutor:tutor` setup through step 8, so no run shows the model calling `/kit:setup tutor <path>` in the middle of the skill and answering its diff question. The plan never asked for such a run, so its absence is not a deviation. Rollout step 5 calls `/kit:setup tutor` as a user command, so it will not show this either. It would be settled by running a case 1 setup once, by hand, after the rollout.
- **Coverage.** This pass covered the payload unevenly:
  - Read directly from the payload: lines 1–539 (manifests, `CLAUDE.md`, `README.md`, the plan's Risk edit, the first review, `global/CLAUDE.md`, the git-hook comments, the deleted `tutor.md` and `plain.md`) and lines 2810–3040 (the `sp` and `tutor` plugins, the tutor skill move, `claude-local.md`).
  - Read in full from the repo: `plugins/kit/bin/claude-method`, `plugins/kit/skills/setup/SKILL.md` and `plugins/tutor/skills/tutor/SKILL.md`.
  - Read in part: the first 80 lines of `plugins/kit/hooks/method-guard.py`.
  - Not read in this pass: the deleted `docs-layout.md` and `plan-format.md`, the `my` style body, `engineering.md`, the test diffs, and the rest of the guard. My judgement of those rests on the first review's move checks and on the test runs. The fix round did not touch them.
  - Every caller sweep was a plain text search (`grep`). I had no symbol-reference tool.

## Reasoning

The fix round fixes a real conflict at its cause: `/kit:setup` now runs after the commit that holds the `CLAUDE.md` scope line, and no step is renumbered. It breaks nothing: the suites pass, the cited step numbers stay true, and no branch commit is cited. The rest of the range is unchanged since the first review. Its checks of the moved text, the single owner of the method list and the reference sweep still hold. The two remaining findings are Suggestions about documentation, a README path and stale plan text. No Warning or Critical row exists, so by the table the assessment is Sound.

## Verdict

**Assessment:** Sound
**Confidence:** High — the fix round is small, I read every file it touched in full, and both test suites pass at the branch head.
**Recommendation:** Merge batch 1. Before or in the squash, write the absolute path in `README.md:190`, and fix the plan's Trade-Offs bullet (or name the move in the squash body). This is the final re-review: neither Suggestion needs another review round.
