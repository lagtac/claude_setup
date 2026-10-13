# Review: main..feat/swappable-methods-cutover

**Status:** review of main..feat/swappable-methods-cutover, 2026-10-13. Mixed: batch 2 does what Tasks 3 to 9 ask and the split is clean, but the method guard is silent in a session started in a subfolder of a set-up `my` repo, because it takes `CLAUDE_PROJECT_DIR` as the root without going up to the repo root. Answered: the user recorded that Warning in the plan's Risk section; the fix round fixed both Suggestions.

## Change Summary

The branch moves the method sections of `global/CLAUDE.md` into a new `global/methods/my.md`, adds `global/methods/tutor.md`, and leaves a neutral core with a new Precedence paragraph and an `## Engineering standards` heading. It adds the `kit:setup` skill (writes the import line, the `## Project facts` block and the `enabledPlugins` switch, then commits them in the target repo) and the `method-guard.py` SessionStart hook in `kit`, with guard tests and neutral-core tests (28 kit tests in all). It also drops the learning-workspace check from the `my` squash-merge hook, changes `.gitignore` to track `.claude/settings.json`, rewords the D15 skills and `kit:dev-reports`, adds a `locked-commit.py` note to `/kit:commit`, rewords the plugin descriptions, and records the Task 0 checks, the setup rehearsal and the live guard check in the plan.

Caller sweeps in this review were text searches only (`grep -rn` through Bash). No symbol-reference tool was available.

## Plan Alignment

The implementation matches Tasks 3 to 9. Each listed file was changed as the task says. Task 5's text-move check output is in the plan, and the kit suite runs 28 tests, all passing (rerun in this review). Deviations:

- `plugins/kit/hooks/method-guard.py:104-114`: `approval()` returns `(approved, shown)` or `None`, not `bool | None` as Task 4 Step 3 says. Justified: the `declined` row was added after Task 3 check 3, with the user's yes, as recorded in "Task 0 results" and the Task 4 table.
- `plugins/kit/tests/test_method_guard.py:260` (`test_hooks_json_runs_the_guard_at_session_start`): this test is not in the plan's list. It is an addition that pins the Task 4 Step 5 entry. Justified.
- `plugins/kit/tests/test_neutral_core.py` (`test_kit_cites_no_method`) also skips symlinks and `__pycache__`, not only `tests/` and `skills/setup/`. Justified: the `bin/` md-table links point outside the repo.
- `plugins/kit/commands/commit.md:11`, the plugin descriptions and the README push-guard bullet come from the batch 1 review items that the plan's Risk section assigned to batch 2. They are recorded there as done.
- The plan's Review Focus 5 covers only a subfolder session with no `CLAUDE_PROJECT_DIR`. The subfolder case with the variable set is not covered (see Issues).

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | **The guard is silent in a subfolder session of a `my` repo.** `project_root()` uses `CLAUDE_PROJECT_DIR` as it is, and goes to `git rev-parse --show-toplevel` only when the variable is missing. Claude Code sets that variable for every hook, so the fallback does not run in practice. In a session started in `<repo>/src`, the guard reads only `<repo>/src/CLAUDE.md` and `<repo>/src/.claude/settings.json`. It finds no import and treats the session as a neutral project. Claude Code itself still loads `<repo>/CLAUDE.md` and its import from a parent folder (Task 0 check 4), and the approval key is the start folder, not the repo root (check 4, and `~/.claude.json` holds a key `~/.config/nvim` that sits below a git top level). So a subfolder session can have an import that is not approved, in a headless run or after a decline, and possibly `my` off, with no warning. Scratch run: a repo with the import and both plugins on, and nothing approved. With `CLAUDE_PROJECT_DIR=<repo>` the guard gives `not_approved`. With `CLAUDE_PROJECT_DIR=<repo>/src` it prints nothing and exits 0. `test_root_falls_back_to_git_toplevel` passes only because it unsets the variable, which a real hook run never does. The sibling tutor hook in the same `hooks.json` does go up to `git rev-parse --show-toplevel` from `CLAUDE_PROJECT_DIR`. Neither the spec's nor the plan's Risk section names subfolder sessions; they name worktree paths only. Impact is likely low: `my:handoff` opens every stage at the repo root, and the `~/.claude.json` scan found no subfolder session in a `my` repo. | `plugins/kit/hooks/method-guard.py:43-54` (`project_root`), `:57-68` (`method_imports`), `:88-101` (`enabled_plugins`); `plugins/kit/tests/test_method_guard.py` :230 `test_root_falls_back_to_git_toplevel` (`project_dir=False`); `plugins/kit/hooks/hooks.json:9` (tutor hook uses the git top level) | Read imports and project settings from the git top level of `CLAUDE_PROJECT_DIR` (or walk up to it), but keep the approval lookup on `CLAUDE_PROJECT_DIR` itself, since that is Claude Code's key. Add a test with the variable set to a subfolder. If this is not fixed now, record it in the plan's Risk section as a known limit. |
| Suggestion / High | **The README still installs `my` at user scope.** The Installation block runs `/plugin install my@claude-setup`, which enables the plugin in `~/.claude/settings.json` (the batch 1 runbook relies on this). That goes against D7, which the new Methods section describes: `my` and superpowers are off at user scope. On a fresh machine, following the README turns `my` on everywhere, and the guard then reports `plugins_stray` in every neutral project. | `README.md:26-36` (Installation); `README.md:71-73` (Methods: "turns `my@claude-setup` and `superpowers@synced` off") | After the install lines, say to set `"my@claude-setup": false` and `"superpowers@synced": false` under `enabledPlugins` in `~/.claude/settings.json`, or use `/plugin disable` for both at user scope. |
| Suggestion / High | **Prose references to "the global instructions" were left behind by the move.** The Task 5 sweep looked for path tokens (`global/CLAUDE.md`, `~/.claude/CLAUDE.md`), so it could not find prose. Two `my` skills still describe method rules as global: `clean-plans` says "The global instructions send all plans and specs to `docs/plans/`", and `handoff` says "Under the global rules that is `my:soundness-review --plan-only`". Both rules now live only in `my.md`. Impact is low, because both skills load only where `my.md` is imported. | `plugins/my/skills/clean-plans/SKILL.md:31`; `plugins/my/skills/handoff/SKILL.md:523` | Change "the global instructions" and "the global rules" to "the `my` method (`~/.claude/methods/my.md`)" in both lines. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The core boundary matches the spec's section table, and a test enforces it | `global/CLAUDE.md:1-79`; `plugins/kit/tests/test_neutral_core.py` (`test_core_names_no_method`, `test_core_has_no_method_heading`) | Strong |
| The text moved without loss: the line check allowed only the four reworded paragraphs | plan, "Text move check" (exit 0, four `allowed` lines); `global/methods/my.md` keeps today's order and headings | Strong |
| The guard follows the spec's input rules, D18 defaults and exact warning texts, fails safe (exit 0, cap 2,000), and has one test per table row plus the five Review Focus cases | `plugins/kit/hooks/method-guard.py:36-179`; `plugins/kit/tests/test_method_guard.py` (the kit suite, 28/28 pass, rerun) | Strong |
| The `declined` warning answers a real finding (Task 0 check 3) instead of leaving the runbook's step 8 to guesswork | plan "Task 0 results", check 3; `method-guard.py:129-146`; runbook steps 7 and 8 | Strong |
| The guard was checked end to end through Claude Code: the `hooks.json` entry runs, `$CLAUDE_PLUGIN_ROOT` resolves, and the model sees the text | plan "Task 0 results", "The guard through Claude Code (Task 9)" | Moderate |
| `kit:setup` is self-contained, stages only its own paths, never skips hooks, and handles an ignored `.claude/settings.json` | `plugins/kit/skills/setup/SKILL.md:125-153`; rehearsal in "Task 0 results", check 2 | Strong |
| Moved references were updated where the spec's item 6 sweep found them | `global/rules/docs-layout.md:136-137`, `plugins/my/skills/status/SKILL.md:59`, `plugins/my/skills/handoff/README.md:253`, `plugins/kit/skills/tutor/SKILL.md:21` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The guard's root ignores the repo root when `CLAUDE_PROJECT_DIR` is a subfolder, unlike the sibling tutor hook | `plugins/kit/hooks/method-guard.py:43-54`; `plugins/kit/hooks/hooks.json:9` | Medium |
| The Installation steps contradict D7 for a fresh setup | `README.md:26-36` | Low |
| Two `my` skills still call method rules "global" | `plugins/my/skills/clean-plans/SKILL.md:31`; `plugins/my/skills/handoff/SKILL.md:523` | Low |

## Not Applicable

None.

## Needs Investigation

- **How Claude Code resolves project settings in a subfolder session.** It is not known whether a session started in `<repo>/src` reads `<repo>/.claude/settings.json` or only `<repo>/src/.claude/settings.json`, or what `CLAUDE_PROJECT_DIR` holds there. If it reads only the subfolder, `my` and superpowers are off in such a session while `my.md` loads. The guard then misses a `plugins_missing` case, not only a `not_approved` one, which makes the Warning above more serious. To settle it: start a session once in a subfolder of a scratch `my` repo, and read `CLAUDE_PROJECT_DIR` and the loaded plugins from the `--output-format stream-json` init line. I did not run `claude -p` in this review.

## Reasoning

The approach is right. The method rules move to one imported file, one test enforces the core boundary, and one fail-safe guard checks both directions of the switch. Every task in batch 2 lands as the plan says, and each deviation is recorded and approved. The one material gap is that the guard reads the start folder instead of the repo root. That gives a silent miss in an uncommon case, and neither the plan's nor the spec's Risk section lists it. No finding is Critical, and the two Suggestions are documentation drift.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. The guard's silence in a subfolder was reproduced. How much it matters depends on Claude Code's settings and key resolution, which was only partly observed (Task 0 check 4 and the `~/.claude.json` keys).
**Recommendation:** Before the cutover, either change `project_root()`/`method_imports()`/`enabled_plugins()` to use the git top level of `CLAUDE_PROJECT_DIR` while keeping the approval key on `CLAUDE_PROJECT_DIR`, with a test where the variable is set to a subfolder, or add "a session started in a subfolder of a `my` repo gets no guard warning" to the plan's Risk section as a known limit. Fix the README Installation note and the two "global" phrases in the same round.
