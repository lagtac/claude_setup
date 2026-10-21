# Review: docs/plans/2026-10-20-method-bundles.md

**Status:** review of docs/plans/2026-10-20-method-bundles.md, 2026-10-21. Mixed: the approach is sound and almost every anchor holds against the repo. But Task 9's sweep test can never pass, because the plan's own new pointer text (`plugins/my/output-styles/my.md`) matches its `output-styles` token.

## Change Summary

The plan carries out row 68 in two batches. Batch 1 has nine tasks: `claude-method`, the core split into a neutral core plus a path-scoped `engineering.md`, the `my`, `tutor` and `sp` plugins with forced styles, the rewritten start check, the rewritten `/kit:setup`, and the moves of this repo and zitamu. Between the batches comes a manual rollout. Batch 2 has three tasks: the `~/bin` symlink, `/kit:method`, and the `my:handoff` launch lines through `claude-method my`.

## Grounding

Every caller sweep in this review was a text search (`git grep`, `grep -rn`). No symbol-reference tool was available.

What holds:

- All twelve "Old text" anchors in Task 4 Step 3 occur exactly once in `global/methods/my.md` or `global/rules/docs-layout.md`. Checked with `grep -cF`: `global/methods/my.md:3`, `:8`, `:122`, `:215`, `:217`, `:219`, `:253`, `:279`; `global/rules/docs-layout.md:139`.
- Task 9's regex, run today over the same pathspec, finds exactly the files that Tasks 3 to 9 list. No caller is missing from Files to Modify.
- `CLAUDE.md:23,29` and `projects/real-estate-webapp/claude-local.md:22,28,238` hold the lines the plan removes.
- The plan says ten repos import `my`. A text search of the `CLAUDE.md` files found nine plus zitamu, `~/src/scripts` included. `mv3-tab-notes/CLAUDE.md` imports `tutor`, and its `.claude/settings.local.json` sets `outputStyle`.
- The four launch lines are at `plugins/my/skills/handoff/SKILL.md:319,330,345,354`. Today `grep -c "claude -n <name>"` prints 4.
- `plugins/kit/hooks/hooks.json:4-13` has the tutor hook as the first `SessionStart` entry. `method-guard.py` has `project_root`, `read_json`, `DEFAULTS`, the `IMPORT` regex and the `.claude.json` approval read, as Task 7 assumes.
- `test_neutral_core.py` defines `REPO`, `CORE`, `KIT` and `headings()`. `test_method_guard.py:19` defines `SCRIPT`. `test_design_router.py:295` loops over the plugin tuple. `plugins/kit/tests` has no `__init__.py`.
- In `~/.claude/settings.json`, `my@claude-setup` and `superpowers@synced` are `false` and `outputStyle` is `plain`. `known_marketplaces.json` has `claude-setup` with `installLocation` `/home/dchris/projects/claude-setup`. `claude --version` prints 2.1.306.
- The `my:handoff` code stage accepts a worktree and branch named by the plan (`plugins/my/skills/handoff/SKILL.md:623-628`, `:825-827`).

Stale references and false assumptions:

- Task 3 Step 4 item 8 says the HTML comment comes "as it is, last". Today it sits before `## HTTP Requests` (`global/CLAUDE.md:73-78`, then `:80`). The spec repeats the same claim.
- Task 3 Step 2 says the five new tests fail. `test_core_keeps_neutral_sections` passes against today's core, because `headings()` strips every `#` level and `### Critical Thinking` is at `global/CLAUDE.md:31`.
- Task 4 Step 2 says all five tests fail. Two of them pass vacuously, because today no marketplace entry has `"category": "method"` (`.claude-plugin/marketplace.json`).
- Rollout step 5 runs `claude-method` from the shell. `~/bin` has no `claude-method` until Task 10 Step 3, in batch 2.
- The snippets in Tasks 4 and 9 call `json` and `subprocess`. `test_neutral_core.py` imports neither today (it imports only `re`, `unittest` and `Path`). This is trivial and is not listed below.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | **Task 9's sweep test can never pass as written.** `OLD_PATHS` contains the bare token `output-styles`. Task 4 Step 6 puts "the `my` style (`plugins/my/output-styles/my.md`)" into the status, handoff README, clean-plans, `pre-commit`, `pre-push` and `plugins/my/README.md` files. Task 8 Step 2 item 4 puts the same path into the `setup` skill. Task 9 Step 3 adds `output-styles/` to `CLAUDE.md`. None of these files is excluded, so Step 2's "expected hits" list is wrong and Step 6 stays red. Narrowing the regex in the middle of the run counts as weakening an assertion, which is a stop gate for the code stage. | Piping the Task 4 pointer string and the planned `CLAUDE.md` line through the regex matched both. Today's sweep hit `README.md:18`. Gate: `plugins/my/skills/handoff/SKILL.md:851-854` | Change the token to `global/output-styles\|\.claude/output-styles`, and correct the Step 2 expected hits. |
| Warning / High | **The rollout result is never committed before batch 2 starts.** Line 955 says to commit step 1's result "with the next plan edit". Batch 2 starts with `/my:handoff code <plan>`, whose start check needs `git status --porcelain -- <doc>` to print nothing. The batch 2 worktree is also cut from a commit, so Task 10 Step 2 cannot see an uncommitted "Result of step 1" line. | `plugins/my/skills/handoff/SKILL.md:614-616`; plan "Rollout after batch 1" and Task 10 Step 2 | Commit the result as its own `docs:` commit (or a fixup of the plan commit) before `/my:handoff code`. Say so in the rollout section. |
| Warning / High | **Rollout step 5 runs `claude-method tutor` before the command is on the shell's `PATH`.** The `~/bin/claude-method` symlink is created in Task 10 Step 3, which comes after the rollout. | `ls ~/bin` shows `git-fold-fixups.py` and no `claude-method` | Use the full path, `~/projects/claude-setup/plugins/kit/bin/claude-method tutor`, or move the symlink step into the rollout. |
| Warning / High | **The red steps of Tasks 3 and 4 claim failures that will not happen, and two Task 4 tests are vacuous.** `test_method_styles_have_forced_frontmatter` and `test_no_applies_line_left` loop over `methods()`. Before Step 5 that is `{}`, so they assert nothing and pass. They also pass whenever the method list is empty. `test_core_keeps_neutral_sections` passes before Task 3, which is fine for a regression guard but contradicts "the five new tests fail". A cold executor sees results that do not match the plan. | `.claude-plugin/marketplace.json` (no `"category": "method"`); `global/CLAUDE.md:31`; `plugins/kit/tests/test_neutral_core.py` `headings()` | Start both loop tests with `self.assertIn("my", methods())`. State which tests are guards that pass now: "four fail" in Task 3, "five fail" in Task 4 after the fix. |
| Warning / Medium | **Task 8's headless check grants no Bash permission.** It runs `--permission-mode acceptEdits` plus `--add-dir`. The skill must run `claude-method --json`, `git add` and `git commit`. The user settings allow only `Bash(git push:*)`. Step 3 needs zero `permission_denied` events and a commit in `HEAD`. Task 11 passes `--allowedTools` for its commands. Task 8 does not. | `~/.claude/settings.json` `permissions.allow`; plan Task 8 Step 1 vs Task 11 Step 1 | Add `--allowedTools 'Bash(claude-method:*)' 'Bash(git:*)' Read Edit Write` to Task 8, with the flag order fixed as in the next row. |
| Warning / Medium | **In Task 8, `/kit:setup my` reads the `my` style from the main checkout, not the branch.** Step 2 item 4 resolves `<installLocation>/plugins/my/output-styles/my.md` through `known_marketplaces.json`, and that path does not exist on `main` until the merge. `CLAUDE_METHOD_MARKETPLACE` does not reach this read. In Case B a missing file is not a `permission_denied` event, so the check can pass while the model works around the failed read. | `~/.claude/plugins/known_marketplaces.json` → `/home/dchris/projects/claude-setup`; `plugins/my/` has no `output-styles/` today | Have the skill read the style from `$CLAUDE_METHOD_MARKETPLACE` when it is set, or check in Step 3 that the stream read the worktree's style. |
| Warning / Medium | **Task 11's `--allowedTools A B C D` can swallow the `-p` prompt.** The flag takes a list of values. This repo has already shown it eating the prompt when it comes before the prompt. The plan does not fix the order. | `docs/plans/2026-09-21-handoff-plan-review-2.md:44-50` | Write the full command with the prompt before `--allowedTools`, or put a flag between them. |
| Warning / Medium | **The plan settled a spec stop condition without asking the user.** The spec says: if the path-scoped rule "does not load on create, stop and ask the user: D2 was picked on the assumption that it does". The probe found that it does not load when a Bash redirect creates the file. The plan records this as a known limit in Risk. The `my` rules' "No silent reinterpretation" section requires the ask. | `docs/plans/2026-10-20-method-bundles-spec.md:227-231`; plan Context, probe paragraph, and Risk | Put the probe result to the user, say whether they confirmed D2 on the new grounds, and record the answer in the plan. |
| Suggestion / High | Task 3 places the HTML comment "last". On `main` it sits before `## HTTP Requests`, so "as it is, last" changes the order. | `global/CLAUDE.md:73-80` | Say "before `## HTTP Requests`, as it is", or note the move as intended. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Moves are anchored by exact quoted text, and every anchor exists once | `global/methods/my.md:3,8,122,215,217,219,253,279`; `global/rules/docs-layout.md:139` | Strong |
| Reference sweep is complete: today's regex hits only files the plan lists | `git grep` over the Task 9 pathspec | Strong |
| One owner for the method list (`claude-method`), tested end to end through a fake `claude` on `PATH` and called for real by the guard tests | Plan Task 2 Step 1, Task 7 Interfaces | Strong |
| Plan-named batch branches fit the handoff code stage | `plugins/my/skills/handoff/SKILL.md:623-628` | Moderate |
| Move checks diff each new file against `main` | Plan Task 3 Step 6, Task 4 Step 4 | Moderate |
| Risk and rollback are named, including dirty shared files before the merge | Plan Risk | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The final sweep test contradicts the plan's own replacement text | Regex simulation; `README.md:18` | High |
| The handover between the batches breaks: the result is uncommitted, and the command is not on `PATH` yet | `plugins/my/skills/handoff/SKILL.md:614-616`; `~/bin` | Medium |
| Red-step expectations are wrong, and two tests are vacuous at red | `.claude-plugin/marketplace.json`; `global/CLAUDE.md:31` | Medium |
| The headless checks are under-specified: permissions, flag order, and a read from the main checkout | `~/.claude/settings.json`; `2026-09-21-handoff-plan-review-2.md:44-50` | Medium |
| A spec stop condition was decided inside the plan | spec lines 227-231 | Medium |

## Not Applicable

None.

## Needs Investigation

- **Dependencies of an inline `--plugin-dir` plugin.** Task 4 Step 9 and Task 6 Step 5 load the branch's `my` or `sp` as `<p>@inline`, with `dependencies: ["superpowers@synced"]`. The spec tested this dependency only for a plugin from a local-folder marketplace. If Claude Code resolves an inline plugin's dependencies differently, both checks fail with `dependency-unsatisfied`, for a reason that has nothing to do with the code. A two-minute headless probe with a throwaway inline plugin would settle it.
- **Who sets the "Batch 1 marks".** The plan says batch 1's review stage sets custom marks and no `done` mark. The handoff review stage says "Set the `done` marks as the project's rules say" (`plugins/my/skills/handoff/SKILL.md:1008`). I found no text there that tells it to follow marks a plan names. In a supervised run the user can steer it, but this should be confirmed before batch 1's review, or written into the review-stage prompt.
- **`acceptEdits` and read-only git commands.** Whether `-p` with `acceptEdits` auto-approves `git status` and `git rev-parse` was not run here. It changes how many `--allowedTools` entries Task 8 needs, not whether it needs any.

## Reasoning

The design follows the spec closely. The anchors and the reference sweep were checked against the repo and hold, and the main contract (`claude-method` as the only reader) is tested end to end. Every surfaced issue is local: one regex token, a missing commit and `PATH` step between the batches, red-step claims and two vacuous loops, three headless-command details, and one decision that belongs to the user. None calls for a different approach. But the Task 9 contradiction would stop batch 1 at its last task. So the plan is not ready to hand off until those rows are fixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the top four findings were reproduced or read directly in the repo. The three Medium rows depend on headless behaviour I did not run.
**Recommendation:** Narrow `OLD_PATHS` to `global/output-styles|\.claude/output-styles`. Add a commit step and the full `claude-method` path to the rollout. Guard the two `methods()` loop tests and correct the red-step counts. Specify the `--allowedTools` set and flag order for Tasks 8 and 11. Ask the user to confirm D2 given the redirect probe. Then hand off batch 1.
