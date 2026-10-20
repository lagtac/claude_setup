# Review: docs/plans/2026-10-20-design-router.md

**Status:** review of docs/plans/2026-10-20-design-router.md, 2026-10-20. Mixed: the approach and the repo grounding hold, but several planned tests stay green without the code they guard, and Task 4 cannot pass as written, because the spec text it copies trips the new whole-name check.

## Change Summary

The plan builds the design router in eight tasks: a whole-name match in `test_neutral_core.py`, a `PreToolUse` gate with its `plugins.json`, one-time tickets, the `kit:design-router` skill, a "Design work" section in the core, and the removal of `my:design-system` from the method files. Task 7 updates the README, and Task 8 is a headless rehearsal whose form waits for Open question 1. Every code task starts with a failing test, run through `subprocess` against the real scripts.

## Grounding

The sweep was text-only (`grep -rn`; no symbol-reference tool was available). Most claims hold:

- The Task 6 line numbers all match `main` today: `global/methods/my.md:117,144,182–183,186–196,212–213`, `global/rules/docs-layout.md:171–174`, `plugins/my/skills/handoff/SKILL.md:277,747`, `plugins/my/skills/handoff/README.md:389`, `plugins/my/skills/spec-review/spec-reviewer-prompt.md:70–73`. The Step 1 grep gives exactly the hits the plan lists.
- The reference sweep `grep -rn 'DESIGN-SYSTEM\|design-system\|frontend-design' global/ plugins/ README.md` finds no file missing from "Files to Modify". The leftover hits are `plugins/my/bin/ds-count.py`, `plugins/my/tests/test_ds_count.py`, `README.md:130,195` and `test_neutral_core.py:31`. The plan covers these or rules them out of scope. No `my` test pins the text Task 6 removes.
- `plugins.json` (Task 2 Step 3) covers every name in `~/.claude/plugins/installed_plugins.json` (version 2, keys `name@market`) and every `synced/*/*/.claude-plugin/plugin.json`, plus `anthropic-skills`.
- `hooks.json` has no `PreToolUse` key, so the `KeyError` red step is right (`plugins/kit/hooks/hooks.json:2`). `method-guard.py` has the shape the plan cites (`plugins/kit/hooks/method-guard.py:177-182`). `tmux-name-pane.py` uses `argparse` and is called bare from a skill (`plugins/kit/skills/name-pane/SKILL.md:41`). The `Task: <N>` trailer is the handoff convention (`plugins/my/skills/handoff/SKILL.md:892-894`). Commit `f03b0e3` is on `main`. The README headings exist (`README.md:108,143,228`).
- `test_skill_placeholders.py` globs only existing `skills/*/SKILL.md` files (`plugins/kit/tests/test_skill_placeholders.py:24`). So a `design-router/` folder that holds only `plugins.json` between Tasks 2 and 4 breaks nothing.
- `kit@claude-setup` is on at user scope in `~/.claude/settings.json`, so the core line and the gate reach every project once `kit` is updated (R14).
- **False assumption:** Task 4 Step 3 item 5 copies the spec's trial points, and Step 4 expects `test_kit_cites_no_method` to pass. The spec's `critique` trial point reads "whether A's design-system check works without Figma" (`docs/plans/2026-10-20-design-router-spec.md:205`). There, `design-system` is a bare whole name, so Task 1's `names_in` still flags it (checked by running the planned regex over spec lines 142–232: this is the only hit).
- **False assumption:** Task 2 Step 2 says the gate tests fail on the missing script. `python3 /nonexistent.py` prints nothing to stdout and exits 2, which was checked. So every test that asserts only `stdout == ""` passes before the gate exists.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | Task 4 cannot pass as written. Copying the spec's `critique` trial point puts a bare `design-system` into `SKILL.md`, and `test_kit_cites_no_method` fails. The executor then has to invent a rewording. | Plan Task 4 Step 3 item 5 and Step 4 ↔ `docs/plans/2026-10-20-design-router-spec.md:205`; `plugins/kit/tests/test_neutral_core.py:32` (`design-system` is in `MY_BARE`) | Give the reworded line in the plan, for example "whether A's design system check works without Figma" or "whether A's `design:design-system` check …". |
| Warning / High | `test_ticket_path_cannot_escape` does not test the gate's path guard (Review Focus 5). Cases 1 and 3 have no `:`, so `decide` returns at rule 1 before `take_ticket` runs. Case 2 and the last assertion resolve to `root/design:ux-copy`, which was never written. A `take_ticket` with no check on `..` or `/` passes every gate assertion. Only the ticket-script half is pinned. | Plan Task 3 test (lines 407–415) ↔ plan Task 2 Step 4 rule 1 (line 297) | Pin `self.tickets = self.root / "tickets"`. Plant a fresh ticket file at `self.root / "design:ux-copy"`. Run the gate with `session=".."` and that skill. Assert that the file still exists and that the decision is `deny`. Do the same for a skill such as `x:../../design:ux-copy` under `s1`. |
| Warning / High | Three Task 2 tests pass before the gate exists, against Step 2's stated red. `test_unknown_prefix_passes`, `test_no_prefix_passes` and `test_kit_passes` assert only `stdout == ""`. A missing script gives empty stdout (exit 2). These are the fail-open cases, so their red step proves nothing. | Plan Task 2 tests (lines 211–222) and Step 2 (lines 273–275); checked: `python3 /nonexistent.py` → stdout empty, rc 2 | Assert `(r.stdout, r.returncode) == ("", 0)` in each, as `test_not_design_passes` already does. |
| Warning / Medium | `test_kit_passes` does not pin rule 2, even after the gate is built. The fixture home does not install `kit`, so rule 9 (absent and not installed) lets the call through. Deleting rule 2 leaves the test green, yet rule 2 is what keeps the router callable (D8). | Plan Task 2 fixture (lines 180–184) and rules 2, 8, 9 (lines 298, 306–309) | Add `"kit@claude-setup": []` to the fixture's `installed_plugins.json`, so a missing rule 2 makes rule 8 refuse `kit`. |
| Warning / Medium | Two Task 3 tests never go red, and the plan names no deliberate break. `test_ticket_is_per_session` and `test_ticket_is_per_skill` already pass on Task 2's gate, which refuses every routed skill. The project's Test Standards ask for a deliberate break for any assertion that never went red. | Plan Task 3 tests (lines 383–389) and Step 2 (lines 425–426) | In Step 4, name the break: for example, take the ticket path without the session (or with a fixed skill), watch the two tests fail, then restore it. |
| Warning / Medium | Task 1 weakens an existing assertion on purpose: `test_kit_cites_no_method` moves from a substring check to a whole-name check. Under the method's controller check, which stops when an assertion is removed or weakened, a supervised or auto run stops at Task 1. | Plan Task 1 Step 3 (lines 141–143) ↔ `plugins/kit/tests/test_neutral_core.py:68-81`; the controller rule in `global/methods/my.md` "Code Review Routing" | Add one line to Task 1: the weakening is mandated by the spec ("Other edits", the `test_neutral_core.py` row), so the controller check should not stop on it. |
| Warning / Medium | Task 8's headless command conflicts with this repo's recorded headless-testing practice. It uses `--output-format json` and reads `permission_denials`, which can be empty while denials happen. Sub-step 5 needs the `stream-json` `init` message, which that command does not produce. No `--add-dir` (for the scratch folder and the plugin folder), no permission mode and no allow rule for the ticket script's Bash call are given. So sub-step 3 may be refused for reasons unrelated to the code. | Plan Task 8 Step 1 (lines 676–687) ↔ `~/.claude/projects/-home-dchris-projects-claude-setup/memory/headless-skill-testing.md` | Use `--output-format stream-json --verbose`, count `permission_denied` events, and add `--add-dir <scratch> --add-dir <worktree>/plugins/kit` and `--permission-mode acceptEdits`. State whether the ticket script gets an `--allowedTools` entry, and what counts as a pass if it is refused (R11). |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Edit sites grounded on today's `main` | The Task 6 Step 1 grep gives exactly the listed hits (`global/methods/my.md:117,144,182,187,193,195`, `global/rules/docs-layout.md:171,173`, …). R16 covers drift. | Strong |
| Reference sweep complete | The text sweep over `global/`, `plugins/`, `README.md` finds nothing outside "Files to Modify" except `ds-count.py`, its test and `README.md:195`, which the plan rules out of scope (row 69). | Strong |
| Plugin list matches the machine | Every key of `installed_plugins.json` and every `synced/*/*` name appears in Task 2 Step 3. | Strong |
| Tests drive the real surface | Gate and ticket tests run the real scripts through `subprocess` with environment overrides, as in `plugins/kit/tests/test_method_guard.py:1-8`. The table tests read the real `SKILL.md` and `plugins.json`. | Strong |
| Sequencing | Task 1 (whole-name match) lands before Task 4 needs `design:design-system`. The gate (2) lands before tickets (3), and both land before the router (4) that uses them. Each task is one commit with its own failing test first. | Strong |
| Fail-open and never-allow are pinned | `test_missing_list_fails_open`, `test_broken_list_fails_open` and `test_never_allows` follow spec D8 and the gate table (`docs/plans/2026-10-20-design-router-spec.md:269-277`). | Moderate |
| The spec conflict is surfaced, not resolved silently | Open question 1 names the clash between "by hand before the `done` mark" and the Delegation section (`docs/plans/2026-10-20-design-router-spec.md:337-342,477`). | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Copied spec text breaks Task 4's own test | `docs/plans/2026-10-20-design-router-spec.md:205`; `plugins/kit/tests/test_neutral_core.py:32` | Medium |
| Path-escape test does not test the gate | Plan lines 407–415 vs rule 1, line 297 | Medium |
| Several tests never go red, against the project standard | Plan lines 211–222, 383–389; missing script → stdout empty | Medium |
| Rule 2 (`kit` passes) unpinned | Plan fixture lines 180–184 | Medium |
| Rehearsal command not runnable as given | Plan lines 676–687; memory `headless-skill-testing.md` | Medium |
| Test helpers left to invention | `reason()`, `write_ticket()`, `routed_plugins()` are used but never described; `self.tickets` and `self.root` are said to come from Task 2, but Task 2's `run_gate` signature takes no tickets path (plan lines 177–179, 419–420) | Low |

## Not Applicable

None.

## Needs Investigation

- **Two `kit` plugins in the rehearsal.** Task 8 loads the branch's `kit` with `--plugin-dir` while `kit@claude-setup` is also on at user scope. It is unclear which copy's skills and hooks Claude Code loads when both share the name `kit`. This matters because the rehearsal could pass or fail on the installed copy, which has no gate and no router. A short `claude -p` run that lists the skills and hooks loaded (the `stream-json` `init` message) would settle it. I could not run Claude Code from this review.
- **The leading slash and the ticket lookup.** Line 311 says `<skill>` is the name without the leading `/`. The plan does not say that `take_ticket` gets the stripped name. If it gets the raw name, a ticketed call to `/design-skills:ux-writing` is refused, because the name holds `/`. No test covers a ticketed call with a leading slash. Stating the stripped name as `take_ticket`'s input, plus one test, would settle it.

## Reasoning

The grounding holds: the edit sites, the reference sweep, the plugin inventory, the hook and test patterns, and the commit and trailer conventions all match the repo. The Task order puts each dependency first. The weaknesses are in test strategy: one security-relevant test (path escape) and two rule tests (fail-open passes, `kit` passes) stay green without the code they guard, and two ticket tests never go red with no break named. Task 4 also has a concrete trap, where copying the spec verbatim fails the plan's own neutrality test. Each fix is a local edit to the plan, not a redesign, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every Warning was traced against the repo or against the plan's own rules. The trial-point clash was checked by running the planned regex, and the missing-script behaviour was checked by running it.
**Recommendation:** Before the plan is approved: give the reworded `critique` trial point in Task 4, rewrite `test_ticket_path_cannot_escape` so it reaches `take_ticket`, add `returncode == 0` to the "passes" tests and `kit` to the fixture's installed list, name the deliberate break for the two ticket negatives, and note the mandated weakening in Task 1. Open question 1 blocks only Task 8. Fix Task 8's command (stream-json, `--add-dir`, permission mode) when that answer comes in.
