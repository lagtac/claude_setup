# Review: docs/plans/2026-10-12-swappable-methods.md

**Status:** review of docs/plans/2026-10-12-swappable-methods.md, 2026-10-13. Mixed: the batching, the sweep and the guard design are grounded and ready to build. The top finding: Task 8's rehearsal check for the method's text passes whether or not the import loads, because the whole `global/CLAUDE.md` is still live during batch 2. The plan stage fixed all six findings and both Needs Investigation items in the plan before its commit.

## Change Summary

The plan carries out the swappable-methods spec in two batches. Batch 1 (Tasks 1 and 2) moves 15 neutral tools from `plugins/my/` into a new `kit` plugin and renames `my:<name>` to `kit:<name>`. Batch 2 (Tasks 3 to 9) runs the task 0 checks, adds `method-guard.py` with its tests, moves the method rules of `global/CLAUDE.md` into `global/methods/my.md` and `tutor.md`, adds `kit:setup`, rehearses the setup, and ends with a cutover runbook over 22 repos.

## Grounding

All searches were text-only (`git grep`, `grep -rn`, `find`). This reviewer has no symbol-reference tool, and the subject is Markdown and JSON anyway.

- Task 2's rename list matches the repo: `git grep` with the plan's own regex returns 46 lines, the same files and lines the plan lists (`README.md:17` to `:160`, `global/CLAUDE.md:16`, `:18`, `:89`, `global/output-styles/tutor.md:19` to `:33`, `global/rules/docs-layout.md:24`, `plugins/my/hooks/hooks.json:43`, and the rest). The memory folder has no hit. No other repo's `CLAUDE.md` or settings file names a `kit` tool under `my:`.
- The path hits that stay in `my` (`README.md:75`, `:109`, `plugins/my/skills/handoff/README.md:283`, `:296`, `:301`, and the three prompt files) are correct. `README.md:52` (`--plugin-dir …/plugins/my`) and `README.md:115` (the `my` test command) are in neither list. Both still hold after the move, so this is minor.
- The `my` suite runs `Ran 145 tests … OK` on `main` today, as the Global Constraints say. `plugins/my/tests/test_block_autorun_push.py:77-82` reads `plugins/my/hooks/hooks.json`, but only the `PreToolUse` entry, which no task changes.
- The line numbers in Tasks 5 and 7 hold: `global/rules/docs-layout.md:134`-`135` (`~/.claude/CLAUDE.md` with the size table), `plugins/my/skills/status/SKILL.md:59`, `plugins/my/skills/handoff/README.md:253`, `plugins/my/skills/tutor/SKILL.md:21`, `plugins/my/commands/optimize-prompt.md:133`, `plugins/my/skills/tune-claude-instructions/SKILL.md:197`, `:203`, `:220`.
- Task 5's claim that `test_kit_cites_no_method` fails only on `optimize-prompt.md` and `tune-claude-instructions/SKILL.md` holds. A grep of the 15 moved paths for `docs/plans`, `superpowers:`, `global/CLAUDE.md` and the `my` skill names hits only those two files.
- The `bin/md-*.py` files are symlinks to `~/src/scripts/`, and `~/bin/md-*.py` link to `plugins/my/bin/` (`ls -la ~/bin`). Batch 1 runbook step 4 repoints them, as the plan says.
- `.gitignore` holds `.claude/` today. `claude-setup/.claude/` holds only `settings.local.json` and `worktrees/`, so D16's change exposes no stray file.
- `claude plugin validate`, `install`, `update`, `list` and `marketplace update` exist (`claude plugin --help`). `handoff-state.py live` exists (`plugins/my/bin/handoff-state.py:13`). `$CLAUDE_PID` is set in session shells and equals the session's `claude` process, and `pgrep -a -x claude` lists sessions and the `daemon run` helper, so cutover step 1's filter works as written.
- `my:handoff` supports plan-named worktrees and branches (`plugins/my/skills/handoff/SKILL.md:427-432`, `:629-633`), and its supervised code stage does not require the plan to be `approved` (`SKILL.md:416-420`). Batch 2 can start after the plan becomes `current`.
- `~/.claude.json` stores project keys as plain paths with no trailing `/`, and the flags `hasClaudeMdExternalIncludesApproved` and `hasClaudeMdExternalIncludesWarningShown` exist (for example on `/home/dchris/projects/claude-setup`). This matches the guard's input.
- The plan says no other `claude-setup` worktree exists. This holds: `git worktree list` shows only the main checkout.
- False assumption: Task 5 Step 7's `ALLOWED` prefixes do not match today's lines. See the Issues table.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
| --- | --- | --- | --- |
| Warning / High | Task 8 Step 6 cannot fail. It asks `claude -p` for the first row of the size table and expects `Small`. During batch 2, `~/.claude/CLAUDE.md` still links to `main`'s whole `global/CLAUDE.md`, which contains that table. So `Small` comes back even if the import never loads. This is the only check that the method file's text reaches the model: cutover steps 7 and 9 run only the guard, and the guard does not read content (plan Risk, last bullet). | `global/CLAUDE.md:38-46`; `~/.claude/CLAUDE.md -> /home/dchris/projects/claude-setup/global/CLAUDE.md` (`ls -la ~/.claude`) | Ask for a sentence that exists only in the worktree's `my.md`, such as its intro line "The rules of the `my` method. …", or add a marker that is not in the global file. Run the same question once before the approval in Step 5, and expect NONE there, so the check has a red step. |
| Warning / High | `test_output_is_capped` cannot fail. Twelve short import names produce one `multi` line of about 150 characters, far under 2,000, so the test passes with no cap code at all. Its only red step is the missing script. | plan Task 4 Step 1 (`12 imports of different names -> len(text) <= 2000`); warning table row `multi` | Use names long enough to go past 2,000 characters uncapped (the regex allows `[a-z0-9-]+` of any length, for example 12 names of 200 characters), and assert both `len(text) <= 2000` and that the uncapped text would be longer. |
| Warning / Medium | The `done` marks run in a session where `my` is probably not loaded. Cutover step 5 starts the new session after `my` is off at user scope, and before claude-setup has its own `.claude/settings.json` (written in step 6). The plan then writes the `done` marks "through `my:roadmap-management`" in that same session. Plugins enabled by a settings file mid-session are likely not loaded until a restart, and the method rules (`my.md`) are not imported either. | plan "Cutover runbook" step 5 and the paragraph after step 9; `plugins/my/skills/roadmap-management` stays in `my` (spec, Plugins table) | After step 8's approval in claude-setup, start a new session in claude-setup for the `done` marks, and check that `my:roadmap-management` is listed before invoking it. |
| Warning / Medium | Batch 1 runbook takes its backup too late. Step 1 runs `claude plugin install kit@claude-setup`, whose default scope is `user`, so it may already write `"kit@claude-setup": true` into `~/.claude/settings.json`. Step 2 then backs up the file. The rollback copy `bak-swappable-1` would then already enable `kit`, and restoring it after a batch 1 revert leaves a plugin enabled that the marketplace no longer has. | `claude plugin install --help` (`-s, --scope … (default: "user")`); plan "Batch 1 runbook" steps 1-2 and "Rollback" | Move the backup to a step 0, before `install`. In step 2, add the key only if `install` did not. |
| Suggestion / High | Task 5 Step 7's script exits 1 as written. Bullets keep their leading dash and space after `strip().lstrip("#").strip()`, and wrapped lines start mid-sentence. Seven lines of the "Learning workspaces" section match no `ALLOWED` prefix, for example `- In a learning workspace, …`, `change"), "Code Review Routing", …` and `Requests", Conventional Commits, …`. The plan's "refine the prefixes" clause covers this, but it leaves the executor to widen a list of allowed misses by hand. | `global/CLAUDE.md:18`, `:20`, `:22`, `:23`, `:24`, `:26`, `:29` (checked by running the plan's prefixes against those lines) | Allow the "Learning workspaces" group by line range (old lines 12 to 32, from its heading to the line before `### Superpowers Integration`) instead of by prefixes. Keep prefixes only for the four reworded paragraphs. |
| Suggestion / High | `test_tutor_with_my_on_is_stray` expects the wrong text. Its world sets only the project's `"my@claude-setup": true` and no user settings. D18 counts a missing `superpowers@synced` as on, so `plugins_stray` names both keys, not only `my@claude-setup`. | plan Task 4 Step 1; `make_world(user_plugins=None, …)`; the inputs paragraph of Task 4 (D18 defaults) | Set `user_plugins=OFF` in that world, as `test_tutor_missing_approval_flag` does. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| The rename sweep is complete and reproducible | The plan's regex gives the same 46 lines as its list; the memory folder and other repos have no hit (`git grep`, `grep -rl` over `~/projects/*/CLAUDE.md`) | Strong |
| Batching fits `my:handoff` | Named worktree and branch are supported (`plugins/my/skills/handoff/SKILL.md:427-432`, `:629-633`); batch 1's branch is kept after merge, so "first batch whose branch does not exist" picks batch 2 | Strong |
| Guard contract is exact and testable | Exact warning texts, order, D18 defaults and the five Review Focus cases each have a named test (plan Task 4) | Strong |
| Red steps exist for each code task | Task 1 layout check, Task 4 missing script, Task 5 `test_neutral_core`, Task 7 `test_kit_cites_no_method` failing on the two files confirmed by grep | Moderate |
| The cutover waits on real signals | `handoff-state.py live` (`plugins/my/bin/handoff-state.py:13`) and `$CLAUDE_PID` with `pgrep -a -x claude` behave as the plan says | Strong |
| Outside-repo state is backed up and listed | Both runbooks back up `~/.claude/settings.json`; Dependencies and Rollback name every outside path | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| The one content check of the import is vacuous | `global/CLAUDE.md:38-46` is live during Task 8 | Medium |
| A guard test cannot go red for its own reason | `test_output_is_capped` with 12 short names | Medium |
| The final session may lack the `my` plugin it uses | Cutover step 5 versus the `done` marks through `my:roadmap-management` | Medium |
| The rollback copy of batch 1 may not be the "before" state | `claude plugin install` defaults to user scope | Medium |
| A one-time script and one test need fixing by the executor | `global/CLAUDE.md:18-29`; D18 default in `test_tutor_with_my_on_is_stray` | Low |

## Not Applicable

None.

## Needs Investigation

- **`--plugin-dir` over an installed plugin with the same name (Task 8 Step 2).** After batch 1, `kit@claude-setup` is installed at user scope, and Task 8 loads `--plugin-dir <worktree>/plugins/kit` on top. If the installed copy wins, `/kit:setup` does not exist and the rehearsal fails for the wrong reason. `my:handoff` already runs `--plugin-dir …/plugins/my` with `my` installed (seen in `pgrep -a claude`), which suggests it works, but this was not checked for a skill that the installed copy lacks. To resolve: before Step 2, check that the session lists `kit:setup`.
- **Whether running sessions reload `~/.claude/settings.json`.** If Claude Code applies an edit to `enabledPlugins` to sessions that are already open, then Task 3 check 1 affects the roughly ten open sessions, not only sessions that start in the one-minute window, as the plan's Risk assumes. Not checked. To resolve: look up the settings reload behaviour, or run check 1 only after cutover step 1's "no other sessions" test.

## Reasoning

Grounding is strong: every file, line, command and count that the plan names checked out, and the rename sweep matches the repo exactly. The problems are in verification, not in design. One rehearsal check and one guard test pass whatever the code does, and two runbook steps (the late backup, the final session's plugin set) can leave the user with a wrong rollback copy or a missing skill. Each has a small, local fix, and none changes the approach. No finding reaches Critical, because none breaks the build or loses data, and each would be noticed in a later step.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every claim was checked against the repo or a command run, except the two items under Needs Investigation.
**Recommendation:** Before the code stage, change Task 8 Step 6 to ask for text that exists only in `my.md`, give `test_output_is_capped` long names, move the batch 1 backup before `install`, and add a restart before the `done` marks. Then fix the two Suggestion rows in the same edit.
