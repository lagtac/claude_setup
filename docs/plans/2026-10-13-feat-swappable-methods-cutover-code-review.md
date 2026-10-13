# Code review: feat/swappable-methods-cutover

**Status:** review of the batch 2 branch, 2026-10-13. A `/code-review high` bug scan of the branch head against local `main`; the fix round answered findings 2 and 4, and finding 10 for `CLAUDE.md`, in `kit:setup`; the plan's Risk section records the rest as known limits.

- **Range reviewed:** `main..feat/swappable-methods-cutover` (local `main`, not `origin/main`). The `/code-review high` run read `git diff main...HEAD` with `HEAD` at the branch head; `main` is an ancestor of the branch, so this is the same diff as `main..feat/swappable-methods-cutover` (24 files, 10 commits).
- **Level:** `high` (8 finder angles, deduplicated, no verify pass).
- **Documents:** spec `docs/plans/2026-10-12-swappable-methods-spec.md`, plan `docs/plans/2026-10-12-swappable-methods.md`. Known limits in either **Risk** section are not reported.
- **Tests:** the kit tests pass (28 run, OK). `test_local_settings_override_project` asserts the advice described in finding 1.
- **Severity scale:** High (blocks the stated goal), Medium (wrong result in a plausible case), Low (edge case or misleading output).

## Findings

### 1. The plugin warnings name the wrong file when `settings.local.json` holds the value

- **Where:** `plugins/kit/hooks/method-guard.py:127` (also `:153`)
- **Severity:** Medium
- **Defect:** `enabled_plugins` merges `.claude/settings.local.json` last, so it wins per key. The `plugins_missing` and `plugins_stray` warnings always tell the user to edit `.claude/settings.json`.
- **Failure scenario:** a `my` project has both keys on in `.claude/settings.json` and `{"superpowers@synced": false}` in `.claude/settings.local.json`. The guard says "Add to .claude/settings.json under enabledPlugins: "superpowers@synced": true. Or run /kit:setup my." The key is already true there. `/kit:setup my` reports "already set up" and stops. The warning comes back at every session start.
- **Suggested fix:** record which file last set each key in `enabled_plugins`, and name that file in the warning. The plan's Risk section says the warning text is a contract, so change `test_local_settings_override_project` and cutover steps 7 and 9 with it.

### 2. `kit:setup` never removes the other method's import, and the tutor steps are not idempotent

- **Where:** `plugins/kit/skills/setup/SKILL.md:175`
- **Severity:** Medium
- **Defect:** neither method's steps remove the other method's import line or facts block. The tutor steps have no "already set up" check.
- **Failure scenario:** `/kit:setup tutor` on a project already set to `my` keeps `@~/.claude/methods/my.md` and the facts block, and appends the tutor import. Both rule files load, and the guard warns "imports more than one method file: my, tutor". The `tutor` to `my` direction fails the same way. Running `/kit:setup tutor` twice appends a second identical import line.
- **Suggested fix:** in both step lists, remove any other `@~/.claude/methods/*.md` line (and, for tutor, the `my` facts block) in `CLAUDE.md` and `CLAUDE.local.md`, and add an "already set up" check to the tutor steps.

### 3. `kit:setup` ignores `.claude/settings.local.json`

- **Where:** `plugins/kit/skills/setup/SKILL.md:177` (also step 3 for `my`, `:109`)
- **Severity:** Medium
- **Defect:** the skill reads and writes `.claude/settings.json` only. The guard, and Claude Code, let `.claude/settings.local.json` override it per key.
- **Failure scenario:** a repo has a leftover `"my@claude-setup": true` in `settings.local.json`. `/kit:setup tutor` removes the keys from `settings.json` only, so `my` stays on. Or a repo has `"superpowers@synced": false` there, and `/kit:setup my` commits `true` in `settings.json` while superpowers stays off. In both cases the guard warns right after a "successful" setup commit.
- **Suggested fix:** read `settings.local.json` too. When it sets either key against the chosen method, show it and propose removing that key (the file is not committed, so this is a local edit only).

### 4. The `.gitignore` edit can commit the user's unrelated edits

- **Where:** `plugins/kit/skills/setup/SKILL.md:135`
- **Severity:** Low
- **Defect:** step 3 checks only `CLAUDE.md` and `.claude/settings.json` for uncommitted edits of the user's own. Step 4 then adds `.gitignore` to a pathspec commit, which commits that whole file from the working tree.
- **Failure scenario:** the user has unrelated, uncommitted edits in `.gitignore`, and the repo ignores `.claude/`. On the yes to the ignore-line fix, `git commit -- CLAUDE.md .claude/settings.json .gitignore` puts those edits into "chore: switch to the my method".
- **Suggested fix:** before editing `.gitignore`, run `git -C <path> status --porcelain -- .gitignore` and handle a listed file as step 3 does.

### 5. Duplicate imports read as a conflict between methods

- **Where:** `plugins/kit/hooks/method-guard.py:119`
- **Severity:** Low
- **Defect:** `imports` is not de-duplicated before the "more than one method" check.
- **Failure scenario:** `CLAUDE.md` and `CLAUDE.local.md` both hold `@~/.claude/methods/my.md`, or the tutor setup ran twice (finding 2). The guard prints "imports more than one method file: my, my. Keep one." That reads as a conflict that does not exist, and cutover step 9 does not pass.
- **Suggested fix:** check `len(set(imports)) > 1` for the conflict, and give a separate "imports the same method twice" line if a duplicate should still be reported.

### 6. The guard does not resolve `CLAUDE_PROJECT_DIR` to the git top level

- **Where:** `plugins/kit/hooks/method-guard.py:44`
- **Severity:** Medium
- **Defect:** when `CLAUDE_PROJECT_DIR` is set, the guard uses it as the root as is. Claude Code sets it to the folder the session started in. The tutor hook in the same `hooks.json` (line 9) runs `git rev-parse --show-toplevel` inside `CLAUDE_PROJECT_DIR`. The plan's Review Focus 5 covers a subfolder start only with no `CLAUDE_PROJECT_DIR`. This follows the spec's "Guard" step 1 text, so a fix may also need the spec's root rule changed.
- **Failure scenario:** the user runs `claude` in `~/projects/foo/src` of a `my` repo. Claude Code still loads `../CLAUDE.md` with its import. The guard reads `src/CLAUDE.md` and `src/.claude/settings*.json`, which do not exist, and finds no import. It then stays silent while the plugins are off, or gives a wrong `plugins_stray` warning.
- **Suggested fix:** run `git rev-parse --show-toplevel` with `cwd=CLAUDE_PROJECT_DIR` first and fall back to the variable itself, as the tutor hook does. Check that the approval key in `~/.claude.json` uses the same path for a subfolder start before changing it, since the Risk section notes that worktree paths get their own approval entry.

### 7. The import regex counts lines inside code fences

- **Where:** `plugins/kit/hooks/method-guard.py:65` (regex at `:36`)
- **Severity:** Low
- **Defect:** every line is matched, including lines inside fenced code blocks, which Claude Code does not import.
- **Failure scenario:** a project `CLAUDE.md` shows the setup example in a ```` ```markdown ```` fence that holds `@~/.claude/methods/my.md`. The guard counts it as a real import and warns `plugins_missing` or "not approved", although nothing was imported.
- **Suggested fix:** skip lines between fence markers (lines starting with ```` ``` ```` or `~~~`) in `method_imports`, and add a test.

### 8. An unreadable `CLAUDE.md` counts as "no import", with no warning

- **Where:** `plugins/kit/hooks/method-guard.py:62`
- **Severity:** Low
- **Defect:** an `OSError` on an existing `CLAUDE.md` or `CLAUDE.local.md` is skipped silently. The docstring promises a warning for an input file that cannot be read, and the JSON files get one through `unreadable`.
- **Failure scenario:** a `CLAUDE.md` with mode 000, or a link with a broken target, holds the `my` import. The guard prints the `plugins_stray` warning ("does not import the my method … turn them off") and no "could not read" line, so the user is told to turn off the plugins the project needs.
- **Suggested fix:** call `unreadable(path, errors)` when the file exists (or is a link) but cannot be read, and skip the `plugins_stray` warning when such an error was recorded.

### 9. The guard does not run after a compaction

- **Where:** `plugins/kit/hooks/hooks.json:15`
- **Severity:** Low
- **Defect:** the guard's `SessionStart` matcher is `startup|resume|clear`, without `compact`.
- **Failure scenario:** in a project whose import is not approved, the agent reads `my.md` because of the guard's warning. The session then auto-compacts. The method rules and the warning both drop out of context, are not added again, and the agent goes on without the method rules.
- **Suggested fix:** use `startup|resume|clear|compact`.

### 10. The `my` "already set up" check misses a stray tutor import and local overrides

- **Where:** `plugins/kit/skills/setup/SKILL.md:86`
- **Severity:** Low
- **Defect:** the check looks only at the facts block, the `my` import line and the two keys in `settings.json`.
- **Failure scenario:** a repo has the `my` facts block, the `my` import and both keys on in `settings.json`, plus a stray `@~/.claude/methods/tutor.md` in `CLAUDE.local.md`. The guard warns "more than one method file". `/kit:setup my` says the project is set up and stops, so the guard's "Or run /kit:setup my" advice cannot fix it.
- **Suggested fix:** extend the check to "no other method import in `CLAUDE.md` or `CLAUDE.local.md`, and no `settings.local.json` key against the method", and fall through to the normal steps otherwise. This fix shares its work with findings 2 and 3.
