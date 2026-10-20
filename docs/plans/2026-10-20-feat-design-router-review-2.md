# Review: main..feat/design-router

**Status:** review of main..feat/design-router, 2026-10-20. Sound: the fix round answers the first review's Warning and its fixes are correct; the top remaining item is that plan R19 gives a reason that the rehearsal itself contradicts.

## Change Summary

The branch adds a `PreToolUse` gate on `Skill` to `kit` (`plugins/kit/hooks/design-router-gate.py`), a one-time ticket script (`plugins/kit/bin/design-router-ticket.py`) and the `kit:design-router` skill with its plugin list. It also adds a "Design work" line to the global core and removes the `my:design-system` calls from the `my` method files. The fix round, at the branch head, does six things:

- adds a router line for a refusal that comes after a ticket, in both the skill and the spec;
- makes the ticket script drop one leading `/`, as the gate does;
- adds a test that runs the script and the gate with their default tickets folder;
- drops "at step 13" from the README;
- records R18–R24 and new manual steps in the plan;
- adds the code-review and first soundness-review reports.

I swept callers with text search only (`grep -rn`), because I had no symbol tool. The branch renames or removes no code symbol.

## Plan Alignment

The implementation matches the plan. Tasks 1–7 are present as written, and the first review confirmed them. The fix round's changes match what the first review and the code review asked for:

- **Router fallback.** `plugins/kit/skills/design-router/SKILL.md:40-43` and spec lines 163-165 hold the line the first review asked for. `plugins/kit/tests/test_design_router.py:319` pins it.
- **Ticket script.** It strips one leading `/` at `plugins/kit/bin/design-router-ticket.py:39`, and its docstring says so. `test_ticket_script_strips_leading_slash` (`test_design_router.py:232`) covers it. This answers code-review F4.
- **Default tickets folder.** `test_default_tickets_folder_is_shared` (`test_design_router.py:237`) answers code-review F6 with a real end-to-end check, not a vacuous one. It removes `DESIGN_ROUTER_TICKETS` and points `HOME` at a temporary folder. The fixture marks `design-skills` as `routed`, so empty stdout proves that the gate found the ticket the script wrote.
- **README.** `README.md:130-135` no longer says "at step 13". This answers code-review F8 and the first review's README finding.
- **Plan Risk.** R18–R22 record code-review F1, F2, F3, F5 and F7. R23 records the `auto`-mode ticket write. R24 records `my:design-system`'s stale text.
- **Manual steps.** `docs/plans/2026-10-20-design-router.md:800-805` now add the allow rule, the `auto`-mode rehearsal and the session-ID check after `/clear`.
- **Tests.** Both suites pass on the branch head: kit 73 tests, which is 70 plus the fix round's three, and my 234 tests.

Deviations and gaps:

- **Rehearsal results (still open, merge-time).** Task 8, Step 2 puts the rehearsal results in the squash commit's body. They still sit only in the rehearsal commit on the branch. Nothing in the fix round or the plan carries them over. The branch cannot hold this action, so it is listed in the Recommendation, not in the Issues table.
- **The spec's manual steps were not updated.** Spec "The user's settings" (`docs/plans/2026-10-20-design-router-spec.md:334-337`) and its "Manual steps" line (`:439`) still list only the `design-superpowers` toggle. The plan's manual steps now also add the allow rule. The first review named both places, and the fix round changed only the plan.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | R19 explains the limit with a claim that the rehearsal itself contradicts. R19 says "The Skill tool calls plugin skills only as `plugin:skill`, so no plugin skill reaches the gate without its prefix." Rehearsal step 5, in the rehearsal commit body, found three loaded plugins (`cc-plugin-agents-md`, `cc-plugin-plugin-authoring`, `cc-plugin-telemetry`) whose skills "carry no prefix". The spec review (`docs/plans/2026-10-20-design-router-spec-review.md:105`) and code-review F2 (`docs/plans/2026-10-20-design-router-code-review.md:42`) both say that this was never checked. The limit itself is recorded and is fine. A later reader would take the wrong reason as settled: a design plugin loaded that way would bypass the gate without notice. | `docs/plans/2026-10-20-design-router.md:785-786`; the rehearsal commit body, step 5 | Reword R19: some loaded plugins expose skills with no prefix (rehearsal step 5), and the gate lets such names through. The three `routed` plugins appear with their prefix today. No code change. |
| Suggestion / High | The router's attended check needs a permission that no step grants and no Risk entry records. `SKILL.md:34-36` tells the router to run `printenv CLAUDE_CODE_SESSION_ATTENDED`. Rehearsal step 4 says this call "needed approval in default mode and was denied", so the router "judged from the session". The fix round added an allow rule for the ticket script only (R23, manual steps). The result is a prompt for each undecided job in an interactive default-mode session. Where no user can answer, the router guesses from context. | `plugins/kit/skills/design-router/SKILL.md:34-36`; `docs/plans/2026-10-20-design-router.md:795-805`; the rehearsal commit body, step 4 | Record it in Risk, or add `Bash(printenv CLAUDE_CODE_SESSION_ATTENDED)` to the manual allow step. No code change. |
| Suggestion / High | The spec's manual steps no longer match the plan's. The fix round added the allow rule `Bash(design-router-ticket.py *)` to the plan's `done`-mark steps. The spec's "The user's settings" section still lists only the `design-superpowers` toggle, and the spec's R11 still says only that the write "may prompt". The first review named both places. | `docs/plans/2026-10-20-design-router-spec.md:334-337`, `:439`; `docs/plans/2026-10-20-design-router.md:800-802` | Add the allow rule to the spec's "The user's settings", or point that section at the plan's manual steps. |

No finding is Critical. No finding is a Warning.

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The first review's Warning is fixed where it occurs. The router now stops after a refusal that follows a ticket, instead of invoking itself again. The spec carries the same line, and a test pins it. | `plugins/kit/skills/design-router/SKILL.md:40-43`; spec `:163-165`; `plugins/kit/tests/test_design_router.py:319` | Strong |
| The script and the gate now judge `/`-prefixed names the same way. The rule is in both docstrings and has its own test. | `plugins/kit/bin/design-router-ticket.py:39`; `plugins/kit/hooks/design-router-gate.py:114`; `test_design_router.py:232` | Strong |
| The duplicated default folder is now guarded by a test that runs both real scripts with no override. The default-path drift that code-review F6 feared would now fail this test. | `test_design_router.py:237-251` | Strong |
| Every code-review finding not fixed on the branch is recorded as a known limit, with its reason and a check. R20's claim holds on this machine: no `design`, `data` or other listed-plugin skill folder exists under `~/projects/*/.claude/skills/` or `~/.claude/skills/`. | `docs/plans/2026-10-20-design-router.md:778-798`; `find ~/projects … -path '*/.claude/skills/design'` returned nothing | Moderate |
| The fix round touched no gate logic and renamed no symbol, so it cannot orphan a caller. A grep for `DESIGN-SYSTEM`, `my:design-system` and `frontend-design` finds hits only in the skill itself, `ds-count` and its test, the router's table, `plugins.json` and its tests, and the README entry. | grep sweep over `global`, `plugins`, `README.md` | Strong |
| The rehearsal already exercised the new fallback for a failed ticket script. In step 3, with the ticket write denied, "the router then said so and printed the command to type". | the rehearsal commit body, step 3 | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| R19's reason is contradicted by rehearsal step 5. | `docs/plans/2026-10-20-design-router.md:785-786` | Low |
| The `printenv` permission gap is not recorded. | `plugins/kit/skills/design-router/SKILL.md:34-36` | Low |
| The spec and the plan now disagree on the manual steps. | `docs/plans/2026-10-20-design-router-spec.md:334-337` | Low |
| `tickets_dir` and `safe` are still copied between the two scripts. The new test guards the folder, but a change to the name rule in one script alone is still untested. | `plugins/kit/bin/design-router-ticket.py:26-32`; `plugins/kit/hooks/design-router-gate.py:59-65` | Low |

## Not Applicable

None.

## Needs Investigation

- **How the Skill tool resolves a bare name.** This shapes how R19 should be reworded (see the first Issues row). From the repo I could not check whether a call such as `Skill("ux-writing")` resolves to `design-skills:ux-writing` and reaches the gate under its bare name. The spec review cites a changelog line suggesting that an unknown bare name errors and does not resolve. To resolve it: in a scratch session, call the Skill tool with a bare name of a skill from a `routed` plugin, and log the `tool_input.skill` that the gate receives.

## Reasoning

The fix round does what the first review and the code review asked. It changes no gate logic and introduces no new behaviour risk. The router fallback, the slash strip and the default-folder test are each correct, and each is pinned by a test that can fail. The three surfaced items are all wording in the plan and the spec. One Risk entry gives a wrong reason. One permission seen in the rehearsal is not recorded. The spec's manual steps lag the plan's. None of them changes what the code does. With no Critical and no Warning, the verdict is Sound.

## Verdict

**Assessment:** Sound
**Confidence:** High. Both suites pass on the branch head. Each fix was read against the code and its test, and the remaining items are text-only.
**Recommendation:**

- At the merge, copy the rehearsal commit's body into the squash message, as Task 8, Step 2 says.
- Under the one-fix-round rule, record the three Suggestions as text edits, either in the done-mark commit or as Risk entries:
  - reword R19;
  - record the `printenv` permission, or add its allow rule;
  - align the spec's "The user's settings" with the plan's manual steps.
