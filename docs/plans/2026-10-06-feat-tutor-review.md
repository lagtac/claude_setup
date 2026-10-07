# Review: main..feat/tutor

**Status:** review of main..feat/tutor, 2026-10-06. Sound: the branch builds what the spec's Tasks ask for, and the top finding is a false reason in a setup red-flag row (`SKILL.md:134` says the hook relies on the clone and branch names, but it checks only the marker file). Answered by the fix round and the Risk section; shipped in 1e69584.

## Change Summary

The branch adds the `my:tutor` skill (`SKILL.md`, `method.md`, `templates.md`) and the `tutor` output style. It adds a "Learning workspaces" section and a Precedence exception to `global/CLAUDE.md`, and two marker checks to `plugins/my/hooks/hooks.json`: a new SessionStart command and an early exit in the squash-merge reminder. It also updates `README.md`, and adds one Risk bullet to the spec about headless runs that cannot write guarded files.

Caller sweep: this review had no symbol tool, so every sweep was a text search (`grep -rn`), checked against the supplied map. Nothing was renamed or removed, so no caller can be orphaned. The only other text that describes the changed hooks is `README.md:128-137`.

## Plan Alignment

The implementation matches the spec's Tasks 2, 3, 4, 6, 7 and 8 (the `README.md` part). Decisions D1 to D10 each map onto text in the new files. Deviations and gaps:

- `plugins/my/skills/tutor/method.md:43-50`: describes "stuck versus impatient" in its own words instead of pointing to the `learn` skill's section, as D6 does. This is an improvement, because the method then works without `learn`. Not a finding.
- `plugins/my/skills/tutor/method.md:85-91`: adds an "Every turn" section that Task 2 did not list. It is harmless and repeats D10.
- `docs/plans/2026-10-06-tutor-spec.md:381-385` (new Risk bullet) versus Task 5 (`spec:500-501`): Task 5 still asserts that `git check-ignore` passes for both files in scenario 1. The new Risk bullet says a headless run cannot make those writes. The limit itself is a known limit, so it is not a finding. The stale Task 5 assertion is surfaced below as a Suggestion.
- (missing) Task 1 asks for a record of whether a style written mid-session applies before a restart. The diff records no result anywhere (see Needs Investigation).
- (missing) Task 8's `ROADMAP.md` row is for the `done` commit on `main`, so its absence here is correct.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | A setup red-flag row gives a false reason. It says "The hook and later sessions rely on" the names `<name>-learning` and `learning`. Both hook commands check only `docs/learning/curriculum.md`, and the session steps say "the learning branch" without a name. A rule whose stated reason is false is easier for the model to argue past. | `plugins/my/skills/tutor/SKILL.md:134`; `plugins/my/hooks/hooks.json:10`, `:26` | Give the real reason (for example, the spec and later sessions expect fixed names, and the user knows where to find the clone), or remove the hook claim. |
| Suggestion / High | The README "Hooks" section is now out of date. It does not mention the new SessionStart command, and it says the squash-merge reminder always fires, but the reminder is now silent in a learning workspace. | `README.md:128-137`; `plugins/my/hooks/hooks.json:10`, `:24-28` | Add one bullet for the workspace SessionStart check, and add "except in a learning workspace" to the PostToolUse bullet. |
| Suggestion / High | The output style names `method.md` by its bare file name. The style lives in `~/.claude/output-styles/`, and `method.md` lives in the plugin's `skills/tutor/` folder. Step 3's fallback ("follow `method.md` alone") is read before step 4 loads `my:tutor`, which is the step that makes the folder known. Step 4 then resolves the reference, so the harm is small. | `global/output-styles/tutor.md:20`, `:22`, `:28` | Write "`my:tutor`'s `method.md`", or put the fallback after step 4. |
| Suggestion / High | Task 5's scenario 1 assertions still require `git check-ignore` to pass for `.claude/settings.local.json` and `progress.md`. The new Risk bullet says a headless run cannot write those files, so the spec's Green criteria contradict its own Risk section. | `docs/plans/2026-10-06-tutor-spec.md:381-385` versus `:500-501` | Change Task 5's assertion to check that the run attempted both writes with the right content, as the Risk bullet already says. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Layer split follows D1: procedures in the skill, rules for every turn in the style, state in repo files | `plugins/my/skills/tutor/SKILL.md:27-30`, `global/output-styles/tutor.md:24-32`, `templates.md:69-71` | Strong |
| The core rule (the student writes the target code; level 5 only after a repeated request) is stated the same way in three places, so a summarized conversation still holds it | `tutor.md:26-29`, `method.md:11-26`, `SKILL.md:158-160` | Strong |
| Hook checks are a narrow, additive guard on one marker file, and the map reports 7 of 7 manual checks passed, in a workspace root, a subfolder, a normal repo and a folder outside any repo | `hooks.json:10`, `:26`; review map "End-of-branch checks run" | Strong |
| The global exception is scoped and listed explicitly, including what stays in force, and the Precedence paragraph names it | `global/CLAUDE.md:12-32`, `:83` | Strong |
| The case 3 push guard is enforced by git, not by the agent, and setup forbids any write to the original repo | `SKILL.md:69-80` | Strong |
| The new style matches the sibling `plain.md` frontmatter shape (`name`, `description`, `keep-coding-instructions: true`) | `global/output-styles/plain.md:1-5`, `tutor.md:1-5` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The global `CLAUDE.md` edit is loaded in every session in every project. A wrong marker match would relax workflow rules for a real project. This is mitigated by the specific marker path and the setup collision stop. | `global/CLAUDE.md:12-32`; `SKILL.md:47-48` | Medium |
| The effect of the skill can only be shown by scenario runs, and this review cannot see them | spec Tasks 1 and 5 | Medium |
| A false reason in a red-flag row | `SKILL.md:134` | Low |
| The README Hooks section is out of date | `README.md:128-137` | Low |

## Not Applicable

None.

## Needs Investigation

- **Scenario results for Tasks 1 and 5 are not visible to this review.** The scratchpad holds only hook fixtures (`ws/`, `normal/`, `plain/` with no `.jsonl` runs), and the map lists only the hook checks. For a skill made only of prompt files, the scenario runs are the only proof that dimension 1 holds: that the tutor refuses "just write it", reads `progress.md` first, and leaves the original repo unchanged in case 3. To resolve: the Red and Green `.jsonl` runs, or a short note of which assertions passed.
- **Task 1's two checks are not recorded.** Whether `claude -p` applies `outputStyle` decides whether the spec's Testing section needed the `--append-system-prompt` note, and that section is unchanged. Whether a style written mid-session applies before a restart tests D3's hand-over assumption. To resolve: say where the results were recorded, or add them to the spec's Testing section.

## Reasoning

All five dimensions applied, and no finding is above Suggestion. The approach treats the actual problem: the global rules assume an agent that ships code, and a marker file makes a narrow, explicit exception. The rule that the student writes the code is repeated in the layers that last the whole session. Nothing was renamed or removed, and the only blast radius is the always-loaded global section, which is guarded by a specific marker path. The remaining doubt is about evidence, not design: the scenario runs that would show the behaviour were not visible to this review.

## Verdict

**Assessment:** Sound
**Confidence:** Medium. The design and wiring were checked against the repo, but the behaviour of the prompt files depends on scenario runs this review could not see.
**Recommendation:** Fix the four Suggestions (the `SKILL.md:134` reason, the README Hooks bullets, the qualified `method.md` reference, and Task 5's stale assertion). Confirm that the Task 5 Green runs passed, then squash-merge.
