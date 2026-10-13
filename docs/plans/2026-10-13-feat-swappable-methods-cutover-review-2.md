# Review: main..feat/swappable-methods-cutover

**Status:** review of main..feat/swappable-methods-cutover, 2026-10-13. Sound: the fix round does what it says, and no Critical or Warning finding remains; the top finding is a Suggestion: `kit:setup` removes another method's import from `CLAUDE.md` only, so a stray import in `CLAUDE.local.md` (code-review finding 10) is still not handled, though two documents call it answered.

## Change Summary

Batch 2 (Tasks 3 to 9) moves the method sections of `global/CLAUDE.md` into `global/methods/my.md` and `global/methods/tutor.md`, adds the `kit:setup` skill and the `method-guard.py` SessionStart hook with their tests, drops the learning check from the `my` squash hook, tracks `.claude/settings.json` in `.gitignore`, rewords the D15 skills and the plugin descriptions, and documents methods in the README. The fix round has three changes: the `fix(kit-plugin)` change makes `kit:setup` remove the other method's import, adds an "already set up" check to the tutor steps, and checks `.gitignore` for the user's own edits; the `docs(my-plugin)` change disables `my` in the README install block and replaces "global" wording in two `my` skills; the `docs(plans)` change adds the two reviews and records known limits in the plan's Risk section.

Caller sweeps in this review were text searches only (`grep -rn` through Bash). No symbol-reference tool was available. The kit suite was rerun: 28 tests, OK.

## Plan Alignment

The implementation matches Tasks 3 to 9, as the first review found. The fix round's three changes match their stated intent, with one partial answer (first row below). Deviations, all justified:

- `plugins/kit/hooks/method-guard.py:125-135`: `approval()` returns `(approved, shown)` or `None`, not `bool | None` as Task 4 Step 3 says. Justified by the `declined` row, added after Task 3 check 3 with the user's yes (plan, Task 4 table and "Task 0 results").
- `plugins/kit/tests/test_method_guard.py` (`test_hooks_json_runs_the_guard_at_session_start`): not in the plan's list; it pins the Task 4 Step 5 entry. Justified.
- `plugins/kit/tests/test_neutral_core.py` (`test_kit_cites_no_method`) also skips symlinks and `__pycache__`. Justified: the `bin/` md-table links point outside the repo.
- `plugins/kit/commands/commit.md:11`, both plugin descriptions and the README push-guard bullet answer batch 1 review items that the plan's Risk section gave to batch 2; the Risk section now records each as done.
- `plugins/kit/skills/setup/SKILL.md:86-98`, `:179-187`: the fix round extends Task 6 beyond the plan text (import removal, tutor idempotence, `.gitignore` check). Justified: it answers code-review findings 2, 4 and 10. It answers finding 10 only in part (see Issues).
- The first review's Warning (subfolder sessions) and its Needs Investigation item are now known limits in the plan's Risk section, under "Known limits from batch 2's review". They are not findings here.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | **New.** The fix round's import removal reaches `CLAUDE.md` only. The guard reads imports from both `CLAUDE.md` and `CLAUDE.local.md`, but the skill's only instruction to remove another method's import sits under the `CLAUDE.md` bullet, and the tutor "already set up" check names `CLAUDE.md` alone. The `my` check says "no other method's import line" without naming a file. So code-review finding 10's own scenario, a stray `@~/.claude/methods/tutor.md` in `CLAUDE.local.md`, still leaves the guard's "more than one method file" warning after `/kit:setup my`. The code-review report's status line says the fix round "answered findings 2, 4 and 10", and the new Risk entry on duplicate imports rests on "`kit:setup` removes other import lines". Impact is low: no `CLAUDE.local.md` under `~/projects` or `~/src` holds a method import today (searched). | `plugins/kit/skills/setup/SKILL.md:86-88`, `:93-98`, `:179-187`; the only `CLAUDE.local.md` mention is `:66`; `plugins/kit/hooks/method-guard.py:59`; `docs/plans/2026-10-13-feat-swappable-methods-cutover-code-review.md:3`; plan Risk, "The same import twice" | By the one-fix-round rule, add one known-limit line to the plan's Risk section ("`kit:setup` removes another method's import from `CLAUDE.md` only, not from `CLAUDE.local.md`"), and change "answered findings 2, 4 and 10" to "answered findings 2 and 4, and finding 10 for `CLAUDE.md`". Or extend the three places to name `CLAUDE.local.md` as a local, uncommitted edit. |
| Suggestion / High | **Carried over, partly fixed.** The README install block now disables `my`, but not superpowers, while the next sentence says superpowers "stays off" at user scope too. Under D18, superpowers comes from the account sync and is on when no settings file names it. On a fresh machine that follows the block, superpowers stays on at user scope, and the guard gives `plugins_stray` for `superpowers@synced` in every neutral project. The Methods section does say that `~/.claude/settings.json` turns it off, so a careful reader can find the step. | `README.md:30-41` (install block and the sentence after it); `README.md:74-75` (Methods); spec D18 at `docs/plans/2026-10-12-swappable-methods-spec.md:62` | Add one sentence after the block: set `"superpowers@synced": false` under `enabledPlugins` in `~/.claude/settings.json`. Or reword "as does superpowers" to say how to turn it off. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The fix round makes `kit:setup` idempotent and lets it switch between methods: the tutor steps gain an "already set up" check and add the import only when it is missing; both step lists remove the other method's import; the `my` check also requires no other import | `plugins/kit/skills/setup/SKILL.md:86-98`, `:179-187` | Strong |
| The `.gitignore` edit no longer sweeps the user's own edits into the setup commit: it runs `status --porcelain -- .gitignore` first and asks | `plugins/kit/skills/setup/SKILL.md:138-140` | Strong |
| The cutover's one tutor repo does not stall at the ignore check: `.claude/settings.json` is not ignored in `~/projects/mv3-tab-notes` (`check-ignore` exit 1) | `plugins/kit/skills/setup/SKILL.md:128-131`, `:191-193` | Moderate |
| Both "global" phrases the first review named now say "the `my` method rules"; a search for "global instructions" and "global rules" in `plugins/` and `global/methods/` finds no other hit | `plugins/my/skills/clean-plans/SKILL.md:31`; `plugins/my/skills/handoff/SKILL.md:523-524` | Strong |
| Every finding of both reviews has a disposition: fixed in the fix round, or a known limit with its reason in the plan's Risk section | plan Risk, "Known limits from batch 2's review"; `docs/plans/2026-10-13-feat-swappable-methods-cutover-code-review.md:3` | Strong |
| The core boundary, the text move and the guard contract stand as the first review found them; the guard matches the Task 4 table and its tests pass (28/28, rerun) | `global/CLAUDE.md`; `plugins/kit/hooks/method-guard.py:138-176`; `plugins/kit/tests/test_method_guard.py` | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The import removal covers `CLAUDE.md` only, while two documents describe the fix as complete | `plugins/kit/skills/setup/SKILL.md:93-98`; code-review report status line | Low |
| The install block disables `my` but leaves superpowers on, against the sentence that follows it | `README.md:30-41` | Low |

## Not Applicable

None.

## Reasoning

The fix round answers what it set out to answer: the two Suggestions of the first review are fixed (the superpowers half of the README one only partly), and `kit:setup` now handles a switch between methods and a repeat run. The first review's Warning is a known limit in Risk by the user's decision, so it is not counted. What remains are two small gaps that only a fresh machine or a hand-edited `CLAUDE.local.md` reaches, so no finding rises above Suggestion.

## Verdict

**Assessment:** Sound
**Confidence:** High. The fix round is three small, readable changes, each checked against the skill text, the guard and the live repos it will touch.
**Recommendation:** Go on to the cutover runbook. If the user wants the record exact, add the `CLAUDE.local.md` limit to the plan's Risk section, adjust the code-review report's status line, and add the superpowers sentence to the README, all in the same `docs(plans)` commit.
