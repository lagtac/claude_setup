# Review: docs/plans/2026-09-30-soundness-plan-only.md

**Status:** review of docs/plans/2026-09-30-soundness-plan-only.md, 2026-09-30. Mixed: the approach and the test design are sound, but the lint check in Task 2 step 5 fails as written, because the new table's `|---|---|` separator adds MD060 errors. The plan's fixes on 2026-09-30 (Global Constraints lint rule, Task 1 fixture path, Task 2 steps 1, 2 and 5, and the step "After the merge") answered all four findings.

## Change Summary

The plan adds a `--plan-only` token to `my:soundness-review`. The token has three effects: stops for mixed arguments (D3), a short path through steps 1 and 1a (D2), a new description sentence and a worked example. The plan also rewrites the `my:handoff` plan stage so it reviews the uncommitted plan and then makes one path-limited commit (D4), and it updates five documents (D5, D6). Tests are headless `claude -p --plugin-dir` runs against a fixture repo, recorded Red in Task 1 and Green in Task 2. A scratch-repo probe tests `git commit -- <paths>`.

## Grounding

Most claims hold against the repo. The caller sweep was text-only (`grep -rn`), because this reviewer has no symbol-reference tool.

- Line references hold:
  - Task 2 cites `soundness-review/SKILL.md` step 0 at `:27-44`, step 1 at `:46-56` and step 1a at `:100-102`.
  - Task 3 cites `handoff/SKILL.md` "Plan stage" at `:150-177` and review stage step 6 at `:265`, and `handoff/README.md` "Plan stage" at `:90-98`.
  - Task 4 cites `docs/plans/2026-09-21-handoff-spec.md` D9 at `:258-288` and the Risk bullet at `:385-389`, `global/CLAUDE.md:58`, `README.md:65-67` and `ROADMAP.md:66-67`.
- The texts the plan replaces exist verbatim. Examples: `soundness-review/SKILL.md:44` ("If args is empty, all three variables are empty …"), `handoff/SKILL.md:265` ("apply the test in Plan stage, step 6."), `handoff-spec.md:262` ("plan stage step 2 commits it"), `ROADMAP.md:66-67`.
- The lint baselines in Global Constraints match a run today: 101, 1, 0, 15, 0, 0 and 71.
- The step-number sweep (plan lines 120-125) matches. Outside dated history, the only hits are `handoff/SKILL.md:166`, `:265` and `handoff-spec.md:262`, `:275`.
- `Review written to docs/plans/<filename>.`, which the handoff plan stage relies on, is printed at `soundness-review/SKILL.md:233`. The plan-review slug and the collision rule are at `:163-165`.
- `.gitignore` excludes `.claude/`, so the fixture at `$WT/.claude/spo-fixture` stays out of the branch.
- Re-running the Task 3 step 1 probe gave the stated result: the commit held only the three named paths, and `A  other.md` stayed staged.
- The `--plugin-dir` claim holds. This session's `probe.jsonl` `init` event lists `my` once, with the probe plugin's path.
- `"name":"Agent"` counting works. A prior `seeded.jsonl` run shows exactly 1 hit, and no `"name":"Task"`.
- False assumption: plan lines 711-713 say the review stage adds the squash hash to the ROADMAP note. The review stage's step 8 (`handoff/SKILL.md:276-279`) sets the done marks "as the project's rules say". The project `CLAUDE.md` has no ROADMAP rule.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
| --- | --- | --- | --- |
| Warning / High | Task 2 step 5's lint check ("the two counts are equal") fails as written. The new mixed-arguments table uses the compact `\|---\|---\|` separator, and in this file that separator raises MD060. I applied Task 2's edits to a scratch copy. The non-MD013 count went from 18 on `main` to 22, with four new MD060 errors on the new separator line. The executor then meets a failing check with no instruction for it. | Plan lines 326-327 and 450-457; existing MD060 errors at `plugins/my/skills/soundness-review/SKILL.md:32` and `:105` | Write that separator as `\| --- \| --- \|`. A scratch test gives 0 errors for that form. Or exclude MD060 from the comparison as well as MD013. |
| Warning / High | Global Constraints contradict Task 2. Lines 42-49 say each touched file's error count "must not rise above" its count on `main` (101 for `soundness-review/SKILL.md`). Task 2 step 5 says each new paragraph adds an MD013 error, "That is expected". My scratch copy reached 113. A cold executor has to guess which rule wins, and rewrapping to satisfy the global rule would break the "match each file's line style" constraint. | Plan lines 42-52 vs 447-449 | In Global Constraints, exempt `soundness-review/SKILL.md` from the total count and point to Task 2 step 5's per-rule check. |
| Warning / Medium | The frontmatter `description` would pass 1024 characters. Today it is about 960 characters, and Task 2 step 2 adds a 76-character sentence, for about 1036. The Agent Skills format caps descriptions at 1024. I did not verify whether Claude Code rejects, truncates or accepts a longer one. If it truncates, the tail is lost, and the tail holds the "use `my:spec-review`" routing clause. | `plugins/my/skills/soundness-review/SKILL.md:4-14`; plan lines 336-344 | Shorten the new sentence (for example ``--plan-only <plan>` never asks.``) or trim an existing clause, so the total stays under 1024. |
| Suggestion / High | No step owns adding the squash hash to the ROADMAP note. The plan says the review stage will add it. The review stage only sets done marks "as the project's rules say", and this project's rules do not mention ROADMAP. The earlier shipped note does cite a hash (`ROADMAP.md:62`). | Plan lines 711-713; `plugins/my/skills/handoff/SKILL.md:276-279` | Say in the plan's Risk that the hash must be added by hand at the done mark, or put the step in a place the review stage reads (for example the plan's Risk section, which the review stage notes). |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Grounding: every line reference, replaced string and lint baseline matched the repo | `soundness-review/SKILL.md:44`, `handoff/SKILL.md:150-177`, `:265`, `handoff-spec.md:262`, `:385-389`, `ROADMAP.md:66-67` | Strong |
| The reference sweep is complete. All four step-number hits are covered by Tasks 3 and 4, and the plan names its own command | `handoff/SKILL.md:166`, `:265`; `handoff-spec.md:262`, `:275` | Strong |
| The central git behaviour is proven. `git commit -- <paths>` leaves another session's staged file alone (re-run by this reviewer) | Plan lines 491-501 | Strong |
| The Red expectations trace correctly through today's step 1a table. `r-noplan` and `r-range` reach diff-review with alignment. `r-spec` on a dirty tree reaches the ask row and the headless fallback, which the plan notes explicitly | `soundness-review/SKILL.md:104-113`, `:129` | Strong |
| The test harness checks for invalid runs: loaded plugin path, permission-denial events, `Agent` call count, and new files. Stop tests check 0 agent calls and no new file, not only the message | Plan lines 185-193; memory note on denial detection | Strong |
| Red → Green order: Task 1 records Red for every new behaviour before Task 2 edits the skill. A regression guard covers the no-token path | Plan lines 232-290, 376-435 | Moderate |
| Review-before-commit removes the stage's own fixup, so a busy `main` no longer needs a rebase to finish. This matches the global steps 5 to 7 | `global/CLAUDE.md:124-126`; plan lines 520-547 | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| The lint check in Task 2 step 5 fails on the plan's own table | `soundness-review/SKILL.md:32` (existing MD060); plan lines 326-327, 450-457 | Medium |
| The lint constraints contradict each other | Plan lines 42-49 vs 447-449 | Medium |
| The description may pass the 1024-character cap | `soundness-review/SKILL.md:4-14` | Medium |
| The ROADMAP hash has no owner | `handoff/SKILL.md:276-279` | Low |

## Not Applicable

None.

## Needs Investigation

- **Writes under a `.claude/` path in `acceptEdits` mode.**
  - What is unclear: the fixture sits at `$WT/.claude/spo-fixture`, and the reviewer subagent writes its report there with `Write`. I could not check whether Claude Code adds write protection to paths that contain a `.claude/` part.
  - Why it matters: if it does, every run that writes a review would be denied.
  - What would resolve it: the first Red run (Task 1 step 2). `chk` prints `denials:`, and the plan says a nonzero count makes the run invalid, so the problem cannot pass silently. If it shows up, move the fixture into `$SCRATCH`, as the architect-skill plan did.

## Reasoning

Grounding is unusually clean: every file, line, string, baseline and sweep hit checked out, and the one new git behaviour was re-proven. The test harness guards against false passes, and the Red expectations match today's mode table. The problems are all in the plan's own verification text: a lint check that fails on the plan's own table, a lint constraint that contradicts that check, and a description that may pass a length cap. None of them changes the design, and each has a one-line fix, so this is Mixed, not Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the MD060 failure and the constraint contradiction were reproduced on a scratch copy of the edited file. Only the 1024-character cap's enforcement is unverified.
**Recommendation:** Before execution, change the new table's separator to `| --- | --- |`, exempt `soundness-review/SKILL.md` from the total-count rule in Global Constraints, and shorten the description sentence to stay under 1024 characters. Then execute as written.
