# Swappable methods Implementation Plan

**Status:** current, 2026-10-13. Batch 1 merged in `1fe2d57`; batch 2 not started.

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan task-by-task. The tasks
> build on each other, and several stop for the user at an interactive
> prompt, so one session runs them in order. The global review rules replace
> that skill's own reviews: run no per-task reviewer and no final
> `requesting-code-review` pass. The `my:handoff` review stage runs the
> end-of-branch reviews. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A project picks its method with its own `.claude/settings.json` and one import line in its `CLAUDE.md`, and `~/.claude/CLAUDE.md` holds only rules that hold under any method.

**Architecture:** Batch 1 creates `plugins/kit/` and moves 15 neutral skills, agents and commands, the md-table filters and the tutor hook into it, renaming `my:<name>` to `kit:<name>`. Batch 2 moves the method sections of `global/CLAUDE.md` into `global/methods/my.md` and `global/methods/tutor.md`, adds the `kit:setup` skill and the `method-guard.py` SessionStart hook, and ends with a cutover runbook that turns `my` and superpowers off at user scope and on in 21 repos.

**Tech Stack:** Markdown prompt files, Python 3 standard library (`unittest`, `json`, `subprocess`), Claude Code plugin manifests and hooks.

**Spec:** `docs/plans/2026-10-12-swappable-methods-spec.md`. Architecture brief: `docs/plans/2026-10-12-swappable-methods-architecture.md`. Spec review: `docs/plans/2026-10-12-swappable-methods-spec-review.md`.

## How the batches run through `my:handoff`

The spec's D1 splits the work into two batches, each with its own branch, reviews and squash-merge. The `my:handoff` stages read these names instead of `<type>/<slug>`:

| Batch | Tasks | Branch | Worktree |
| --- | --- | --- | --- |
| 1 | 1 to 2 | `refactor/swappable-methods-kit` | `.claude/worktrees/swappable-methods-kit` |
| 2 | 3 to 9 | `feat/swappable-methods-cutover` | `.claude/worktrees/swappable-methods-cutover` |

- **Code stage:** implement the first batch whose branch does not exist yet. A batch's code stage runs only its own tasks, then launches the review stage as usual.
- **Review stage:** the batch is the one whose worktree exists.
- **After batch 1's squash-merge:** no `done` marks. Run "Batch 1 runbook" below. Then, in one `docs(plans)` commit on `main`, set this plan's status to `current` (sentence: "Batch 1 merged in `<hash>`; batch 2 not started.") and set the `ROADMAP.md` row to 🚧. Then signal `review-swappable-methods: batch 1 merged; start batch 2 with /my:handoff code docs/plans/2026-10-12-swappable-methods.md`.
- **Batch 2's review stage, step 8:** runs "Cutover runbook" steps 1 to 5 in place of a plain squash-merge, then signals and stops (step 5 ends the session). A new session runs steps 6 to 9 and then the `done` marks.

Commit scopes: `kit-plugin` (new, for `plugins/kit/`), `my-plugin`, `global` and `plans`, as in `git log`. Squash subjects:

- Batch 1: `refactor(kit-plugin): move the neutral tools out of my into a new kit plugin`
- Batch 2: `feat(global): split the global rules into a neutral core and method files`

## Global Constraints

- No new packages. The guard uses the Python standard library only (spec, Dependencies).
- `plugins/kit/.claude-plugin/plugin.json` has no `version` field (spec, Plugins).
- The method plugin keeps the folder `plugins/my/` and the name `my` (D3). The neutral plugin is `kit` in `plugins/kit/` (D4).
- Moved text keeps today's wording. Only the paragraphs in "Reworded text" below change (spec, Non-goals).
- `global/CLAUDE.md` after batch 2 contains none of `my:`, `superpowers:`, `docs/plans`, `docs/reports` (spec, Testing).
- The guard reads `$HOME`, never a fixed path; always exits 0; output under 2,000 characters (spec, Guard).
- Tests: `cd plugins/kit && python3 -m unittest discover tests` and `cd plugins/my && python3 -m unittest discover tests`. On `main` today the `my` suite runs 145 tests, all passing.
- Markdown lint: `markdownlint-cli2 <files>`. There is no config file, and `global/CLAUDE.md` already fails MD013 and MD012 on `main`. The check is "no new errors compared with `main`", not "lint clean".
- Committed docs under `docs/` keep their old `my:` names (spec, Testing: rename sweep).

## Review Focus

1. **The project path in `~/.claude.json` differs in form from `CLAUDE_PROJECT_DIR`**, for example a trailing `/`. Expected: the guard still finds the approval. Test: `test_trailing_slash_in_project_dir_still_finds_approval` (Task 4).
2. **An import line with Windows line endings or trailing spaces.** Expected: it still counts as an import. Test: `test_import_line_with_crlf_counts` (Task 4).
3. **An `enabledPlugins` value that is not a JSON boolean**, such as the string `"true"`. Expected: it counts as not `true`, so the guard warns. Test: `test_string_true_is_not_on` (Task 4).
4. **A settings file that is valid JSON but not an object**, or whose `enabledPlugins` is not an object. Expected: `method guard could not read <path>`, not a crash. Test: `test_settings_not_an_object_is_unreadable` (Task 4).
5. **A session started in a subfolder with no `CLAUDE_PROJECT_DIR`.** Expected: the root is the git top level, so the import is found. Test: `test_root_falls_back_to_git_toplevel` (Task 4).

---

## Batch 1: split out `kit`

Behaviour does not change. `my` and superpowers stay on at user scope, and `global/CLAUDE.md` stays whole.

### Task 1: Create the `kit` plugin and move its files

**Files:**

- Create: `plugins/kit/.claude-plugin/plugin.json`, `plugins/kit/hooks/hooks.json`
- Modify: `.claude-plugin/marketplace.json`, `plugins/my/hooks/hooks.json` (remove the tutor SessionStart entry)
- Move with `git mv`, keeping each path below `plugins/my/` the same below `plugins/kit/`:
  - `skills/de-slop`, `skills/md-tables`, `skills/briefing`, `skills/dev-reports`, `skills/git-squasher`, `skills/tune-claude-instructions`, `skills/tutor`
  - `agents/laravel-fullstack-expert.md`, `agents/oral-medicine-expert.md`
  - `commands/commit.md`, `commands/push.md`, `commands/clean-gone-branches.md`, `commands/laravel-debug.md`, `commands/laravel-migration-check.md`, `commands/optimize-prompt.md`
  - `bin/md-expand-table.py`, `bin/md-collapse-sections.py` (symlinks to `~/src/scripts/`; `git mv` keeps the absolute targets)

**Interfaces:**

- Produces: the plugin `kit@claude-setup`, with folder `plugins/kit/` and the files above. Task 2 renames references to them.

- [ ] **Step 1: Red: show the layout check fails**

Run: `test -f plugins/kit/.claude-plugin/plugin.json && test -d plugins/kit/skills/tutor && test -L plugins/kit/bin/md-expand-table.py && echo OK`
Expected: no `OK`, exit 1.

- [ ] **Step 2: Write `plugins/kit/.claude-plugin/plugin.json`**

Keys: `name` `kit`; `description` `Neutral tools that work under any method: writing, git, Laravel and prompt helpers, and the tutor for learning workspaces with its SessionStart hook.` (batch 1's review added the tutor clause); `author` as in `plugins/my/.claude-plugin/plugin.json`. No `version`.

- [ ] **Step 3: Add the `kit` entry to `.claude-plugin/marketplace.json`**

After the `my` entry: `name` `kit`, the same description, `source` `./plugins/kit`, `category` `development`.

- [ ] **Step 4: `git mv` every file in the list above**

- [ ] **Step 5: Move the tutor hook**

Cut the second SessionStart entry (matcher `startup|clear`) from `plugins/my/hooks/hooks.json` into a new `plugins/kit/hooks/hooks.json` with the same shape, and change `my:tutor` to `kit:tutor` in its text. The squash-merge hook and its learning-workspace check stay in `my` until Task 7.

- [ ] **Step 6: Green: run the layout check, the validators and the `my` tests**

Run: the Step 1 command, then `claude plugin validate plugins/kit`, `claude plugin validate plugins/my`, `claude plugin validate .`, then `cd plugins/my && python3 -m unittest discover tests`.
Expected: `OK`; three validations pass; `Ran 145 tests` and `OK`.

- [ ] **Step 7: Commit**

`git add -A plugins .claude-plugin && git commit -m "refactor(kit-plugin): create the kit plugin and move the neutral tools into it"`. Read `git diff --cached` first.

### Task 2: Rename the neutral names

**Files:** every hit below. Line numbers are from `main` on 2026-10-13; paths under `plugins/my/` are the old paths of files Task 1 moved.

`my:<name>` and `/my:<name>` hits (15 names: `de-slop`, `md-tables`, `briefing`, `dev-reports`, `git-squasher`, `tune-claude-instructions`, `tutor`, `laravel-fullstack-expert`, `oral-medicine-expert`, `commit`, `push`, `clean-gone-branches`, `laravel-debug`, `laravel-migration-check`, `optimize-prompt`):

- `global/CLAUDE.md:16`, `:18`, `:89` (`my:tutor`)
- `global/output-styles/tutor.md:19`, `:23`, `:29`, `:33` (`my:tutor`)
- `global/rules/docs-layout.md:24` (`my:briefing`)
- `plugins/kit/agents/laravel-fullstack-expert.md:7` (`/my:laravel-debug`, `/my:laravel-migration-check`)
- `plugins/kit/commands/laravel-debug.md:11` and `plugins/kit/commands/laravel-migration-check.md:21` (`my:laravel-fullstack-expert`, twice each, including `subagent_type`)
- `plugins/kit/commands/optimize-prompt.md:13`
- `plugins/kit/skills/briefing/SKILL.md:96` (`my:de-slop`)
- `plugins/my/skills/changelog-management/SKILL.md:65` (`my:dev-reports`)
- `plugins/kit/skills/dev-reports/SKILL.md:5`, `:16` to `:21`
- `plugins/kit/skills/git-squasher/SKILL.md:3`, `:13` to `:16`
- `plugins/my/skills/handoff/README.md:285` (`my:push`), `:364` (`/my:commit`)
- `plugins/kit/skills/tune-claude-instructions/SKILL.md:10`
- `plugins/kit/skills/tutor/method.md:4`
- `README.md:17`, `:80`, `:85`, `:93`, `:94`, `:98`, `:101`, `:102`, `:128`, `:129`, `:132`, `:134`, `:136`, `:138`, `:160`

Path hits for `plugins/my/` that change: `README.md:8` (add a `plugins/kit/` bullet), `README.md:103` (becomes `plugins/kit/bin/`), `README.md:153` (the hooks list names both `hooks.json` files), `CLAUDE.md:7` (see Step 3). Path hits that stay, because the file stays in `my`: `README.md:75`, `:109`, `plugins/my/skills/architect/candidate-prompt.md:12`, `plugins/my/skills/handoff/README.md:283`, `:296`, `:301`, `plugins/my/skills/soundness-review/SKILL.md:259`, `plugins/my/skills/soundness-review/code-reviewer-prompt.md:15`, `plugins/my/skills/spec-review/spec-reviewer-prompt.md:11`.

The project memory folder had no hit on 2026-10-13.

**Interfaces:**

- Consumes: the moved files from Task 1.
- Produces: no `my:<kit name>` left outside `docs/`.

- [ ] **Step 1: Red: run the sweep**

```bash
names='de-slop|md-tables|briefing|dev-reports|git-squasher|tune-claude-instructions|tutor|laravel-fullstack-expert|oral-medicine-expert|commit|push|clean-gone-branches|laravel-debug|laravel-migration-check|optimize-prompt'
git grep -n -E "(^|[^a-z-])/?my:($names)([^a-z-]|$)" -- global plugins README.md CLAUDE.md
grep -rn -E "/?my:($names)([^a-z-]|$)" ~/.claude/projects/-home-dchris-projects-claude-setup/memory/
```

Expected: the hits listed above (about 50 lines).

- [ ] **Step 2: Replace each hit** with `kit:<name>` or `/kit:<name>`.

- [ ] **Step 3: Update the path hits**

`README.md`: a `plugins/kit/` bullet under `plugins/` (`the kit plugin: neutral skills, commands, agents and the tutor hook, which work under any method`); move the 15 `kit` items into their own entries under Skills, Commands and Agents, named `kit:`; Installation and Updating gain `kit@claude-setup` lines next to `my@claude-setup`; Hooks says which hook lives in which `hooks.json`. `CLAUDE.md:7`: "Each plugin lives in `plugins/<name>/`: `my` holds the method, `kit` the neutral tools. The paths below are relative to a plugin folder."

- [ ] **Step 4: Green: rerun the sweep, the `my` tests and the lint**

Run: the Step 1 commands; `cd plugins/my && python3 -m unittest discover tests`; `markdownlint-cli2 README.md CLAUDE.md global/output-styles/tutor.md global/rules/docs-layout.md`.
Expected: the sweep prints nothing; `Ran 145 tests`, `OK`; no lint error that `main` does not have.

- [ ] **Step 5: Commit**

`refactor(kit-plugin): rename the neutral tools from my: to kit:`. Read `git diff --cached` first.

### Batch 1 runbook

The review stage runs this after the squash-merge, before its `docs(plans)` commit.

1. Back up `~/.claude/settings.json` to `~/.claude/settings.json.bak-swappable-1`, before any other step: `claude plugin install` may write to that file.
2. `claude plugin marketplace update claude-setup`, then `claude plugin install kit@claude-setup`. If `install` reports that `kit` is not found, the marketplace update did not run: rerun it. Then check that `~/.claude/settings.json` has `"kit@claude-setup": true` under `enabledPlugins`, and add it if not.
3. `claude plugin update my@claude-setup`.
4. `ln -sfn ~/projects/claude-setup/plugins/kit/bin/md-expand-table.py ~/bin/md-expand-table.py`, the same for `md-collapse-sections.py`. The `git-fold-fixups.py` link stays.
5. Check: `claude plugin list` shows `kit@claude-setup` and `my@claude-setup` enabled; `md-expand-table.py --help` runs from a plain shell; `readlink ~/bin/md-*.py` points into `plugins/kit/bin/`.
6. Tell the user to restart every open Claude session. Until then, an old session runs the cached `my` with the tutor hook, so the hook may fire twice in a learning workspace.

---

## Batch 2: the cutover

### Task 3: Checks 1, 3, 4, 5 and 6 (task 0 of the spec)

These run before any batch 2 code, because checks 1, 3 and 5 can reopen D7 or change the guard. Check 2 needs `kit:setup` and runs as Task 8. Record each result in a new section "Task 0 results" at the end of this plan, in the worktree, one line per check: what ran, what was seen, and the decision it confirms. Commit that section at the end of the task: `docs(plans): record the task 0 checks for swappable methods`.

If check 1 fails, or check 3 or 5 shows that the guard must change, stop and ask the user (spec, Open questions). Do not change the guard on your own.

Checks 3, 4 and 5 need the user at an interactive prompt: signal once with the list of what they must do, then wait.

Each check uses a scratch folder under the session's scratchpad. Any check that edits `~/.claude/settings.json` or `~/.claude/methods` backs up first and restores at once after.

- [ ] **Check 1: `"superpowers@synced": false` at user scope.** Back up `~/.claude/settings.json`. Add the key under `enabledPlugins`. In a scratch folder with no `.claude/`, run `claude -p --verbose --output-format stream-json 'reply ok' | head -1 | jq '[.plugins[]?.name], [.skills[]? | select(startswith("superpowers"))]'`. Restore the backup at once, and `diff` it against the live file. Expected: no superpowers plugin and no `superpowers` skill. If the first line has no `plugins` or `skills` field, ask `claude -p 'List every skill you can invoke whose name starts with superpowers:, or say NONE.'` instead. Keep the edit window under one minute: any session that starts in it runs without superpowers.
- [ ] **Check 3: declined once.** User step: in a scratch project whose `CLAUDE.md` imports a file outside it, start `claude`, decline the import prompt, exit, start `claude` again. Record whether it asks again, and the value of `projects[<scratch>]` in `~/.claude.json` (`hasClaudeMdExternalIncludesApproved`, `hasClaudeMdExternalIncludesWarningShown`).
- [ ] **Check 4: parent folder.** User step: a scratch folder holding a nested git repo; the parent's `CLAUDE.md` imports a scratch file; start `claude` in the nested repo, approve if asked. Record whether the import loads and which path's flag in `~/.claude.json` changed.
- [ ] **Check 5: import into the same repo.** Make `~/.claude/methods` a temporary link to `<scratch>/repo/methods`, holding a `my.md` with one marker sentence. User step: in `<scratch>/repo`, whose `CLAUDE.md` holds `@~/.claude/methods/my.md`, start `claude`. Record whether it asks for approval and whether the flag is set. Then `rm ~/.claude/methods`. The cutover's step 3 creates the real link and fails if this one is left.
- [ ] **Check 6: missing target.** In a scratch project whose `CLAUDE.md` imports `@~/.claude/methods/none.md`, run `claude -p 'reply ok'` and read stderr and stdout. Record whether Claude Code says anything. The spec's Rollback relies on silence.

### Task 4: The method guard

**Files:**

- Create: `plugins/kit/hooks/method-guard.py`
- Test: `plugins/kit/tests/test_method_guard.py`
- Modify: `plugins/kit/hooks/hooks.json` (add the SessionStart entry)

**Interfaces:**

- Produces: `method-guard.py`, run as `python3 "$CLAUDE_PLUGIN_ROOT/hooks/method-guard.py"`. It reads no stdin. Its output is empty, or one JSON object: `{"systemMessage": <text>, "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": <text>}}`. `<text>` is the warnings joined by `\n`, cut to 2,000 characters. Exit code 0 always.
- Produces, for Task 8 and the cutover steps 7 and 9: the exact warnings below.

Warnings, in this order:

| Key | When | Exact text |
| --- | --- | --- |
| `unreadable` | An input file exists but is not valid JSON, or its top level (or `enabledPlugins`) is not an object. One per file. | `method guard could not read <path>` |
| `multi` | Two or more method imports | `method guard: this project imports more than one method file: <names, comma-space, in file order>. Keep one.` |
| `plugins_missing` | `my` imported; `my@claude-setup` or `superpowers@synced` is not `true` | `method guard: this project imports the my method, but its plugins are off. Add to .claude/settings.json under enabledPlugins: <lines>. Or run /kit:setup my.` where `<lines>` is the missing ones of `"my@claude-setup": true` and `"superpowers@synced": true`, joined by a comma and a space |
| `not_approved` | `my` or `tutor` imported; the approval flag is `false` or missing, and the import was not declined (see `declined`). One per imported name. Not given when `~/.claude.json` is unreadable. | `method guard: the <name> method import is not approved, so its rules are not loaded. Read ~/.claude/methods/<name>.md before your first reply, and ask the user to approve the import (start a new interactive session in this directory).` |
| `declined` | In place of `not_approved` when the approval flag is not `true` and `projects[<root>].hasClaudeMdExternalIncludesWarningShown` is `true`: the user saw the prompt and declined, and Claude Code does not ask again (Task 3, check 3). One per imported name. | `method guard: the <name> method import was declined earlier, so its rules are not loaded and Claude Code will not ask again. Read ~/.claude/methods/<name>.md before your first reply. To be asked again, set projects["<root>"].hasClaudeMdExternalIncludesWarningShown to false in ~/.claude.json while no session runs in this directory, then start a new interactive session here.` where `<root>` is the project root as the guard found it |
| `plugins_stray` | `my` not imported; `my@claude-setup` or `superpowers@synced` is `true` | `method guard: this project does not import the my method, but these plugins are on: <keys>. To turn them off, add to .claude/settings.json under enabledPlugins: <lines>.` with `<keys>` like `my@claude-setup, superpowers@synced` and `<lines>` like `"my@claude-setup": false, "superpowers@synced": false` |

Inputs as in the spec's "Guard" section: the root (`CLAUDE_PROJECT_DIR` with any trailing `/` removed, else `git rev-parse --show-toplevel` in the current directory, else the current directory); imports matching `^@~/\.claude/methods/([a-z0-9-]+)\.md\s*$` in `<root>/CLAUDE.md` then `<root>/CLAUDE.local.md`; `enabledPlugins` merged from `$HOME/.claude/settings.json`, `<root>/.claude/settings.json`, `<root>/.claude/settings.local.json`, later file winning per key, with a missing `superpowers@synced` counting as `true` and a missing `my@claude-setup` or `kit@claude-setup` as `false` (D18); approval from `projects[<root>].hasClaudeMdExternalIncludesApproved` in `$HOME/.claude.json`, where `true` is the only approved value; and, for the `declined` row, `projects[<root>].hasClaudeMdExternalIncludesWarningShown` from the same file, where only `true` counts as shown (added after Task 3, check 3, with the user's yes on 2026-10-13).

- [ ] **Step 1: Write the failing tests**

Follow `plugins/my/tests/test_block_autorun_push.py`: `unittest`, the script run with `subprocess.run([sys.executable, SCRIPT], env=..., cwd=..., capture_output=True, text=True, timeout=10)`. A helper `make_world(user_plugins=None, project_md="", local_md=None, project_plugins=None, local_plugins=None, approved=None, warning_shown=None)` builds a temporary `HOME` (with `.claude/settings.json` and `.claude.json`) and a temporary project, and returns their paths; `run_guard(home, project, project_dir=True)` sets `HOME` and, when asked, `CLAUDE_PROJECT_DIR`. A helper `text(result)` parses stdout and asserts `systemMessage == additionalContext`, then returns it.

Tests (one per table row, then the extra cases):

```python
MY = "@~/.claude/methods/my.md\n"
ON = {"my@claude-setup": True, "superpowers@synced": True}
OFF = {"my@claude-setup": False, "superpowers@synced": False}

test_my_with_plugins_off_names_each_missing_line:
    # user OFF, project imports MY, approved True, no project plugins
    assertEqual(text(r), 'method guard: this project imports the my method, but its plugins are off. '
        'Add to .claude/settings.json under enabledPlugins: "my@claude-setup": true, "superpowers@synced": true. '
        'Or run /kit:setup my.')
test_my_with_only_superpowers_missing:   # project {"my@claude-setup": True}; text names only "superpowers@synced": true
test_my_not_approved:                    # project MY + ON, approved False -> exact not_approved text with <name> = my
test_tutor_missing_approval_flag:        # project imports tutor.md, user OFF, no projects entry -> not_approved with tutor
test_declined_import_gives_reset_advice: # project MY + ON, approved False, warning_shown True -> exact declined text with <name> = my and <root> = the project path; no not_approved line
test_neutral_with_stray_plugins:         # no import, project ON -> exact plugins_stray text naming both keys
test_neutral_with_superpowers_by_default:# no import, user {"my@claude-setup": False}, no superpowers key -> plugins_stray naming superpowers@synced only
test_tutor_with_my_on_is_stray:          # imports tutor, approved, user OFF, project {"my@claude-setup": True} -> plugins_stray naming my@claude-setup only
test_two_imports:                        # MY in CLAUDE.md, tutor in CLAUDE.local.md, ON, approved -> text == multi text "my, tutor"
test_neutral_and_off_prints_nothing:     # no import, OFF -> stdout == "" and returncode 0
test_my_set_up_prints_nothing:           # MY, ON, approved True -> stdout == ""
test_unreadable_user_settings:           # user settings file "{" -> first line "method guard could not read <home>/.claude/settings.json"; project ON + MY + approved still gives nothing else
test_unreadable_claude_json_skips_approval: # .claude.json "{" -> could-not-read line, no not_approved line
test_local_settings_override_project:    # project ON, local {"superpowers@synced": False}, MY, approved -> plugins_missing naming superpowers only
test_trailing_slash_in_project_dir_still_finds_approval  # Review Focus 1
test_import_line_with_crlf_counts                        # Review Focus 2: "@~/.claude/methods/my.md  \r\n"
test_string_true_is_not_on                              # Review Focus 3: project {"my@claude-setup": "true", ...}
test_settings_not_an_object_is_unreadable               # Review Focus 4: project settings "[]"
test_root_falls_back_to_git_toplevel                    # Review Focus 5: git init the project, cwd = a subfolder, no CLAUDE_PROJECT_DIR
test_output_is_capped:                   # 40 imports with 60-character names (a-z, 0-9, -), so the uncut text is over 2,000 -> len(text) <= 2000
test_exit_code_is_zero_in_every_case:    # loop over the worlds above; returncode == 0
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd plugins/kit && python3 -m unittest tests.test_method_guard -v`
Expected: every test errors, because `hooks/method-guard.py` does not exist.

- [ ] **Step 3: Implement `plugins/kit/hooks/method-guard.py`**

Functions, all private to the script: `project_root() -> Path`; `method_imports(root: Path) -> list[str]`; `read_json(path: Path, errors: list[str]) -> dict | None` (returns `None` and appends the `unreadable` line when the file exists but is not a JSON object; returns `{}` when it does not exist); `enabled_plugins(home: Path, root: Path, errors: list[str]) -> dict[str, bool]` (applies the D18 defaults, and treats a non-object `enabledPlugins` as unreadable); `approval(home: Path, root: Path, errors: list[str]) -> bool | None` (`None` when `.claude.json` is unreadable); `warnings(...) -> list[str]` in the table's order; `main() -> int`. Wrap `main` so any exception still exits 0 with no output.

- [ ] **Step 4: Run them to see them pass**

Run: `cd plugins/kit && python3 -m unittest discover tests -v`
Expected: all pass.

- [ ] **Step 5: Add the hook**

In `plugins/kit/hooks/hooks.json`, a SessionStart entry with matcher `startup|resume|clear`, command `python3 "$CLAUDE_PLUGIN_ROOT/hooks/method-guard.py"`, timeout 10. Run `claude plugin validate plugins/kit`; expected: passes.

- [ ] **Step 6: Commit**: `feat(kit-plugin): add method-guard.py, a SessionStart check of the method switch`

### Task 5: Method files and the trimmed core

**Files:**

- Create: `global/methods/my.md`, `global/methods/tutor.md`, `plugins/kit/tests/test_neutral_core.py`
- Modify: `global/CLAUDE.md`, `global/rules/docs-layout.md` (first line, and line 135), `global/rules/plan-format.md` (first line), `plugins/my/skills/status/SKILL.md:59`, `plugins/my/skills/handoff/README.md:253`, `plugins/kit/skills/tutor/SKILL.md:21`

**Interfaces:**

- Produces: `global/methods/my.md` and `global/methods/tutor.md`, which Task 6's setup skill and the guard's `not_approved` text name as `~/.claude/methods/<name>.md`.
- Produces: the first-line sentence `Applies only in projects whose \`CLAUDE.md\` imports \`~/.claude/methods/my.md\`. Ignore it otherwise.`

- [ ] **Step 1: Write the failing test `plugins/kit/tests/test_neutral_core.py`**

`REPO = Path(__file__).resolve().parents[3]`. Tests:

```python
METHOD_HEADINGS = ["Learning workspaces", "Superpowers Integration", "Size the process to the change",
    "Spec → Plan two-artifact flow", "No silent reinterpretation of approved decisions", "Code Review Routing",
    "UI Design", "Git Workflow", "One feature, four commits on `main`", "Splitting scope before branching",
    "When to use worktrees", "When NOT to use worktrees", "Finishing a worktree branch",
    "Assessing branch redundancy", "When to open an MR (optional)", "Planning Standards",
    "Trade-Off Analysis", "Risk Awareness", "Test Standards", "Plan Output Format"]
APPLIES = "Applies only in projects whose `CLAUDE.md` imports `~/.claude/methods/my.md`. Ignore it otherwise."

test_core_names_no_method:      # for token in ["my:", "superpowers:", "docs/plans", "docs/reports"]: assertNotIn(token, core)
test_core_has_no_method_heading:# headings = {line.lstrip("#").strip() for line in core lines starting with "#"}; for h in METHOD_HEADINGS: assertNotIn(h, headings)
test_core_has_engineering_standards: # assertIn("Engineering standards", headings)
test_method_files_exist:        # (REPO/"global/methods/my.md").is_file() and tutor.md
test_lazy_rules_start_with_applies_line: # for docs-layout.md, plan-format.md: first non-empty line after the "# " title == APPLIES
test_kit_cites_no_method:       # every file under plugins/kit except skills/setup/ and tests/: no "docs/plans", "superpowers:",
                                # "global/CLAUDE.md", and no "my:<n>" for n in the my skills, agents and command of the spec's Plugins table
```

- [ ] **Step 2: Run it to see it fail**

Run: `cd plugins/kit && python3 -m unittest tests.test_neutral_core -v`
Expected: `test_core_names_no_method`, `test_core_has_no_method_heading`, `test_core_has_engineering_standards`, `test_method_files_exist` and `test_lazy_rules_start_with_applies_line` fail. `test_kit_cites_no_method` fails on `optimize-prompt.md` and `tune-claude-instructions/SKILL.md` until Task 7.

- [ ] **Step 3: Write `global/methods/my.md`**

Title `# Method: my`, then: `The rules of the \`my\` method. A project uses them by importing this file from its \`CLAUDE.md\`. They add to the core in \`~/.claude/CLAUDE.md\`.` Then, in today's order and with today's headings and wording, every section the spec's section table marks **method**: the `docs/plans/` and `docs/reports/` bullets (under the `**Important:**` label), Superpowers Integration with all its subsections, UI Design, Git Workflow with all its subsections except the Conventional Commits bullets, and `## Planning Standards` with Trade-Off Analysis, Risk Awareness, Test Standards and Plan Output Format. Apply "Reworded text" items 2, 3 (method part), 4 (method part) and 5.

- [ ] **Step 4: Write `global/methods/tutor.md`** with the final text in "Reworded text" item 7.

- [ ] **Step 5: Trim `global/CLAUDE.md`**

Keep `# Instructions`, then "Reworded text" item 1, then the Conventional Commits bullets and the dependency bullet; `## Communication`; `## Code`; `## Engineering standards` with item 3's core part, Verify against ground truth, `### Critical Thinking`, `### Mandatory Exploration`, `### Reference Sweep` (item 4's core part), `### Simplicity Rules`; `## HTTP Requests`. Remove "Learning workspaces" and every section moved in Step 3.

- [ ] **Step 6: Lazy rules and references**

Add the APPLIES sentence as the first line after the title in `docs-layout.md` and `plan-format.md`. Change `~/.claude/CLAUDE.md` to `~/.claude/methods/my.md` at `docs-layout.md:135`, and `global/CLAUDE.md` to `~/.claude/methods/my.md` at `status/SKILL.md:59` and `handoff/README.md:253`. In `plugins/kit/skills/tutor/SKILL.md:21`, `The global section "Learning workspaces"` becomes `` `~/.claude/methods/tutor.md` ``.

- [ ] **Step 7: Check the text moved without loss**

Save this one-time script to the scratchpad (not the repo) and run `python3 <scratch>/check-moved.py <(git show main:global/CLAUDE.md) global/CLAUDE.md global/methods/my.md global/methods/tutor.md`:

```python
# Each non-empty line of the old global file must appear, stripped of
# leading '#' marks and spaces, as a line of the new core or of a method
# file. The named lines are the allowed misses.
import sys
def lines(path): return {l.strip().lstrip("#").strip() for l in open(path) if l.strip()}
old = [l.strip().lstrip("#").strip() for l in open(sys.argv[1]) if l.strip()]
new = lines(sys.argv[2]) | lines(sys.argv[3]) | lines(sys.argv[4])
# Every line of the old "Learning workspaces" section, from its heading to the
# line before "### Superpowers Integration", is an allowed miss (D6).
raw = [l for l in open(sys.argv[1])]
start = next(i for i, l in enumerate(raw) if l.startswith("### Learning workspaces"))
end = next(i for i, l in enumerate(raw) if l.startswith("### Superpowers Integration"))
learning = {l.strip().lstrip("#").strip() for l in raw[start:end] if l.strip()}
ALLOWED = {
    "item 2: Precedence": ["**Precedence:**"],
    "item 3: Planning Standards intro": ["These standards apply to **all** planning"],
    "item 4: Reference Sweep": ["When a plan removes/renames"],
    "item 5: Before step 1": ["**Before step 1 in a project"],
}
missing = [l for l in old if l not in new and l not in learning]
for l in missing:
    name = next((n for n, keys in ALLOWED.items() if any(l.startswith(k) for k in keys)), None)
    print(f"allowed ({name}): {l[:70]}" if name else f"MISSING: {l[:100]}")
sys.exit(any(not any(l.startswith(k) for ks in ALLOWED.values() for k in ks) for l in missing))
```

Expected: exit 0; only `allowed (…)` lines. If a reworded paragraph spans several lines, add the start of each of its lines to its own group; never add a prefix for a line outside the four named groups. Paste the output into "Task 0 results" under a heading "Text move check".

- [ ] **Step 8: Run the test, the `my` tests and the lint**

Run: `cd plugins/kit && python3 -m unittest tests.test_neutral_core -v`; `cd plugins/my && python3 -m unittest discover tests`; `markdownlint-cli2 global/CLAUDE.md global/methods/*.md global/rules/*.md`.
Expected: all `test_neutral_core` tests pass except `test_kit_cites_no_method`; 145 `my` tests pass; no lint error kind that `main`'s `global/CLAUDE.md` does not have.

- [ ] **Step 9: Commit**: `feat(global): move the method rules into global/methods/my.md and tutor.md`

### Task 6: The setup skill `kit:setup`

**Files:** Create `plugins/kit/skills/setup/SKILL.md`.

**Interfaces:**

- Consumes: `~/.claude/methods/my.md` and `tutor.md` (Task 5); the guard's warnings (Task 4), which name `/kit:setup my`.
- Produces: the `## Project facts` block and the `.claude/settings.json` switch that the guard checks.

- [ ] **Step 1: Write `SKILL.md`**

Frontmatter `name: setup`; a `description` that says it switches a project to the `my` or `tutor` method, takes `<method> [<project path>]`, and is not for outside methods. The body is the spec's "Setup skill" section turned into steps, with these fixed:

- Usage line on bad args: `Usage: /kit:setup <my|tutor> [<project path>]`.
- The facts block, word for word as in the spec, including the `- **Method:** my` line and the blank line before `@~/.claude/methods/my.md`.
- The settings merge keeps every other key and sets only `"my@claude-setup": true` and `"superpowers@synced": true` under `enabledPlugins`.
- The commit: `git -C <path> add -- CLAUDE.md .claude/settings.json` (plus `.gitignore` on the user's yes), then `git -C <path> commit -m "chore: switch to the my method" -- <those paths>`; follow the project's own scope style when its `git log` shows one for config.
- Step 4's `git check-ignore -q .claude/settings.json` test, and the proposed exception lines `.claude/*` and `!.claude/settings.json`.
- For `tutor`: the import line `@~/.claude/methods/tutor.md` only, and removal of `enabledPlugins` keys that turn `my` or superpowers on.
- The skill embeds these facts, because a skill does not inherit `CLAUDE.md`.

- [ ] **Step 2: Validate**: `claude plugin validate plugins/kit`; expected: passes, and `setup` is listed.

- [ ] **Step 3: Commit**: `feat(kit-plugin): add kit:setup, which switches a project to the my or tutor method`

### Task 7: Hook, ignore rule, D15 rewording and README

**Files:**

- Modify: `plugins/my/hooks/hooks.json` (squash-merge hook), `.gitignore`, `plugins/kit/commands/optimize-prompt.md:133`, `plugins/kit/skills/tune-claude-instructions/SKILL.md:197`, `:203`, `:220`, `README.md`

- [ ] **Step 1: Red**: run `cd plugins/kit && python3 -m unittest tests.test_neutral_core.NeutralCoreTest.test_kit_cites_no_method -v` (use the class name Task 5 chose); expected: fails on the two files above.

- [ ] **Step 2: Reword per D15**

`optimize-prompt.md:133`: the folder becomes `docs/optimized-prompts/`. `tune-claude-instructions/SKILL.md:197`: write the report to a path the user names, with no default path. `:203`: the example `/my:summarize` becomes `a one-line command that only invokes an agent`. `:220`: drop the pointer to the `docs/plans/` worked example, and say the pattern grades each file on the S/R/F rubric in `references/grading-rubric.md`.

- [ ] **Step 3: Green**: rerun Step 1's command; expected: pass. Then the whole `kit` suite: all pass.

- [ ] **Step 4: Squash-merge hook**

Remove the leading `top=…; [ -n "$top" ] && [ -f "$top/docs/learning/curriculum.md" ] && exit 0;` from the PostToolUse command. Check by hand: `cd <scratch learning repo with docs/learning/curriculum.md> && echo '{"tool_input":{"command":"git merge --squash x"}}' | sh -c '<the new command>'` prints the `squash-merge detected` JSON.

- [ ] **Step 5: `.gitignore`** (D16): replace `.claude/` with `.claude/*` and `!.claude/settings.json`. Check: `git check-ignore -q .claude/settings.local.json` exits 0; `git check-ignore -q .claude/settings.json` exits 1; `git check-ignore -q .claude/worktrees/x` exits 0.

- [ ] **Step 6: `README.md`**: the `global/` bullet names `methods/` and the `~/.claude/methods` link; Skills lists `kit:setup`; Hooks lists `method-guard.py` and drops the "stays silent in a learning workspace" sentence; a short "Methods" section says how a project picks one (the spec's Switches table, as prose). Lint: no new error kinds.

- [ ] **Step 7: Commit**: `feat(kit-plugin): drop the learning check from the squash hook, reword the D15 skills, document methods`

### Task 8: Check 2, the rehearsal

User gate: this needs an interactive approval. Record the result in "Task 0 results".

- [ ] **Step 1:** Copy a small `my` repo (`~/projects/notes-cli`, with its `.git`) to `<scratch>/rehearsal`. Make `~/.claude/methods` a temporary link to `<worktree>/global/methods`.
- [ ] **Step 2:** From a session started in `~/projects/claude-setup` with `--plugin-dir <worktree>/plugins/kit`, first check that `/kit:setup` is offered: `setup` exists only in the worktree copy, so this shows the `--plugin-dir` copy is the one loaded. If it is not offered, stop and signal. Then run `/kit:setup my <scratch>/rehearsal`. Record whether the writes into that other repo were refused. If they were, the cutover's step 5 session needs `--add-dir ~/projects --add-dir ~/src`; note it in the runbook.
- [ ] **Step 3:** Check the diff it showed and the commit it made: `git -C <scratch>/rehearsal show --stat HEAD` lists only `CLAUDE.md` and `.claude/settings.json`.
- [ ] **Step 4:** Run the guard with `CLAUDE_PROJECT_DIR=<scratch>/rehearsal`; expected: only the `not_approved` warning for `my`.
- [ ] **Step 5:** User step: start `claude` in `<scratch>/rehearsal` and approve the import.
- [ ] **Step 6:** The size table is still in `~/.claude/CLAUDE.md` during batch 2, so ask for text that only `my.md` has: `cd <scratch>/rehearsal && claude -p 'Quote the sentence in your instructions that starts with "The rules of the" and names the my method, or say NONE.'`. Run this once before Step 5 (expected: `NONE`) and once after it (expected: the sentence). Run the guard again; expected: no output.
- [ ] **Step 7:** `rm ~/.claude/methods`, delete `<scratch>/rehearsal`, and remove its key from `~/.claude.json` only if the user agrees. Commit "Task 0 results": `docs(plans): record the setup rehearsal`.

### Task 9: Final checks before the review stage

- [ ] Run: `cd plugins/kit && python3 -m unittest discover tests`; `cd plugins/my && python3 -m unittest discover tests`; `claude plugin validate .`.
  Expected: all `kit` tests pass, including `test_kit_cites_no_method`; 145 `my` tests pass; validation passes.

### Cutover runbook

Batch 2's review stage runs steps 1 to 5 as its step 8, in place of a plain squash-merge, after the user's yes. A new session runs steps 6 to 9.

In auto mode, Claude Code refuses steps 3 and 4 as "Self-Modification": the `~/.claude/methods` link and the edit of `~/.claude/settings.json`. It refuses an edit of `~/.claude.json` (step 8's reset) the same way. In Task 3 a plain sentence from the user in that session was enough: "You may create and remove the ~/.claude/methods link, and run check1.sh, which edits ~/.claude/settings.json." So ask the user for such a sentence before step 3, naming each edit, or let the user run the commands with `!`.

1. **Wait for other sessions.** Both commands must show nothing, checked in the same turn:
   - `handoff-state.py live`
   - `pgrep -a -x claude | grep -v -e "^$CLAUDE_PID " -e ' daemon run '`. The `claude daemon run` process is a helper that a session spawns, not a session, so it is left out. On 2026-10-13 this machine had about ten sessions open.

   While either shows something, signal `review-swappable-methods: cutover waits for other sessions: <what was found>` and stop. Check again after the user's reply.
2. Squash-merge batch 2 on `main` with batch 2's subject, then `git worktree remove .claude/worktrees/swappable-methods-cutover`.
3. `ln -s /home/dchris/projects/claude-setup/global/methods ~/.claude/methods`. If it exists (a link left by Task 3 or 8), check where it points, and replace it only if it is not this path.
4. Back up `~/.claude/settings.json` to `~/.claude/settings.json.bak-swappable-2`. Set `"my@claude-setup": false` and `"superpowers@synced": false` under `enabledPlugins`; keep `"kit@claude-setup": true`.
5. `claude plugin update kit@claude-setup` and `claude plugin update my@claude-setup`. Signal `review-swappable-methods: cutover steps 1-5 done; end this session, start a new one in claude-setup (add --add-dir ~/projects --add-dir ~/src if Task 8 needed it), and say: run the cutover runbook in docs/plans/2026-10-12-swappable-methods.md from step 6`. Stop.
6. In the new session: `/kit:setup my <path>` for each of the 21 repos: `~/projects/claude-setup`, `grispy2-web-ext`, `irini`, `lequal`, `maritime`, `mv3-starter`, `niche-research`, `notegraph`, `notes-cli`, `webext` (all under `~/projects/`), `~/projects/diagoradisa/diagoradisa-annotator`, `…/diagoradisa-meta`, `…/diagoradisa-ml`, `…/diagoradisa-palmist`, `…/diagoradisa-platform`, `~/projects/grispy-web-ext/grispy-ext`, `…/grispy-site`, `~/projects/zitamu/real-estate-webapp`, `~/src/containers`, `~/src/cv`, `~/src/scripts`. Then `/kit:setup tutor ~/projects/mv3-tab-notes`. `lequal`, `niche-research`, `notes-cli` and `~/src/containers` had unrelated uncommitted work; the setup stages only its own files. Then, for each repo, `git -C <repo> worktree list`. For each extra worktree (on 2026-10-13: `diagoradisa-annotator/.claude/worktrees/parallel-worktree-runs` and `zitamu/real-estate-webapp/.claude/worktrees/client-review`), ask the user: merge `main` into its branch now, or start its sessions only at the repo root until it is merged (D20).
7. For each of the 22 repos: `CLAUDE_PROJECT_DIR=<repo> python3 ~/projects/claude-setup/plugins/kit/hooks/method-guard.py`. The only warnings allowed are `not_approved` and `declined`.
8. User step: open each of the 22 repos once in an interactive session and approve the import. Task 3's check 3 showed that a declined import is not asked again: for each repo that step 7 gave `declined`, first set `projects["<repo>"].hasClaudeMdExternalIncludesWarningShown` to `false` in `~/.claude.json`, with no session running in that repo, as the warning says.
9. Step 7 again: no output in any of the 22 repos.

Then end the session and start a new one in `claude-setup`: step 6 gave this repo its settings file, and only a new session loads `my` and `my:roadmap-management` from it. Check that `my:roadmap-management` is offered. Then the `done` marks, in one `docs(plans)` commit on `main`: the spec and this plan get status `done`, citing batch 1's and batch 2's squash commits and the end-of-branch check counts; the `ROADMAP.md` row becomes ✅ and `CHANGELOG.md` gains an entry, through `my:roadmap-management`.

### Rollback

As the spec says: `git revert` batch 2's squash commit, and restore `~/.claude/settings.json.bak-swappable-2`. Batch 1 alone: `git revert` its squash commit, restore `~/.claude/settings.json.bak-swappable-1`, and repoint the two `~/bin` md-table links to `plugins/my/bin/`.

---

## Reworded text

The final text of each paragraph the spec's "Reworded text" lists. Bold labels and backticks as written here.

1. **Core Precedence**, after the `# Instructions` title in `global/CLAUDE.md`:

   > **Precedence:** this file and the method file a project imports are the highest authority: when plan mode, a skill or a system default conflicts, follow them. The rules in this file hold under every method. A method file may add rules. It may name an exception to a rule in this file only by naming the rule.

2. **Method Precedence**, in `my.md` where today's Precedence paragraph stands:

   > **Precedence:** these rules and the core in `~/.claude/CLAUDE.md` are the highest authority — when plan mode, a skill, or any system default conflicts, follow them. Superpowers may override **only** plan output format and the core's Simplicity Rules (announce when it does). Everything else here is non-overridable: `docs/plans/` output path, Git Workflow (GitLab/worktrees/squash-merge), Risk + Trade-Off Analysis, and that plans include **Dependencies** + **Risk** sections and follow **Red → Green → Refactor** (tests before implementation).

3. **Planning Standards intro.** Core, under `## Engineering standards`, followed by today's "Verify against ground truth" paragraph unchanged:

   > These standards apply to every planning workflow: built-in plan mode, a method's own planning steps, and any agent that writes an implementation plan.

   Method, under `## Planning Standards` in `my.md`:

   > These standards add to the Engineering standards in `~/.claude/CLAUDE.md`. Critical Thinking (in the core), Risk Awareness and Trade-Off Analysis are always enforced. Mandatory Exploration (in the core) applies only when no superpowers discovery skill is active (see Superpowers Integration above). Plan Output Format may be overridden by Superpowers.

4. **Reference Sweep.** Core:

   > When a change removes, renames or changes the signature of a cross-file symbol (function, type, route/event name, config/DI key, field, file-naming scheme), find every reference with **both** a symbol-reference tool **and** a plain text search for the name token (string-literal refs — routes, DI keys, ORM eager-loads, templates — are invisible to symbol tools). Handle every hit, including cross-repo consumers.

   Method, one more sentence at the end of item 3's method paragraph:

   > In a plan, the "Files to Modify" list is the output of the core's Reference Sweep: every hit is a row.

5. **"Before step 1 in a project for the first time"**, in `my.md`'s Git Workflow:

   > **Before step 1 in a project for the first time,** check that the project's `CLAUDE.md` has a `## Project facts` block that names the method, the commit scopes, the test command, the plans index and the remote. If it is missing or incomplete, run `/kit:setup my`.

6. **References to the global file:** Task 5, Step 6.

7. **`global/methods/tutor.md`** (the spec's "The tutor method file", D14):

   ```markdown
   # Method: tutor

   This repo is a learning workspace: the student writes the code, and the agent teaches through the `kit:tutor` skill.

   - If the `tutor` output style is not active, say so once, and point to `.claude/settings.local.json`, which sets it with `{"outputStyle": "tutor"}`. The style takes effect in the next session.
   - The project's `CLAUDE.md` gives facts: commands, stack. Workflow rules from any other file do not apply here.
   - Exceptions to the core in `~/.claude/CLAUDE.md`: Verify against ground truth, Mandatory Exploration, Reference Sweep and Simplicity Rules do not apply in a learning workspace. The rest of the core applies.
   - No vacuous tests: each test the tutor writes must fail for the right reason before the student's code exists.
   ```

## Trade-offs

- **Task 0 split in two.** Checks 1, 3, 4, 5 and 6 run first in batch 2 (Task 3), because they can change the guard. Check 2 runs as Task 8, because it needs `kit:setup`. Running all six first would leave the rehearsal with nothing to rehearse.
- **One plan file, two batches**, instead of one plan per batch. The spec names one plan path, and the batches share the reworded text and the warning texts. The cost: the `my:handoff` stages must read the batch table above.
- **Exact warning texts in the plan.** The tests assert exact text, and the cutover steps 7 and 9 read it, so the plan fixes it. Rewording a warning later means changing the tests too.
- **Line check, not paragraph check, for the text move.** The `# Instructions` bullet list is one paragraph that splits between core and method, so a paragraph check would miss all of it. A line check catches each bullet.

## Dependencies

- No new packages.
- Outside the repo: `~/.claude/settings.json` (both runbooks), the `~/.claude/methods` link, the two `~/bin` md-table links, the plugin cache (`claude plugin install` / `update`), and commits in 21 other repos plus `mv3-tab-notes`.
- The undocumented key `hasClaudeMdExternalIncludesApproved` in `~/.claude.json`.

## Risk

- **Live settings edits during Task 3, check 1.** For up to a minute, any session that starts runs without superpowers. Detection: none automatic; keep the window short and restore from the backup, then `diff` it. It is not known whether a running session rereads `~/.claude/settings.json`; if it does, the sessions already open also lose superpowers for that minute. Run check 1 when few sessions are open.
- **Temporary `~/.claude/methods` links in Tasks 3 and 8.** A link left behind makes cutover step 3 fail or point at a removed worktree. Step 3 checks where an existing link points.
- **Cutover step 1 never clears** while other sessions stay open. It signals and waits for the user; it never kills a session.
- **A missed repo** gets the neutral core only, with no message (spec, Risk). Detection: cutover step 7 for the 22 known repos.
- **Conflicts with open `my:handoff` work.** Batch 1 moves no handoff file. Batch 1 edits `plugins/my/skills/handoff/README.md:285` and `:364`; batch 2 edits `:253`. `ROADMAP.md` has two open `my:handoff` rows that may touch that file; a conflict there is small and shows at merge time. No other `claude-setup` worktree existed on 2026-10-13.
- **The guard's warnings are a contract** for the tests and the cutover steps 7 and 9. A change to one must change all three.
- **Plugin cache lag** after each batch: a session started before `claude plugin update` runs the old code. Both runbooks restart; other sessions must restart too.
- **`/kit:commit` needs `locked-commit.py` from `my`** (batch 1 review). In a project with a "Parallel runs" section, the command commits with `locked-commit.py`, which stays in `plugins/my/bin/` and is on PATH only while `my` is on. Today only `my` projects have that section, so the case does not arise. A project that keeps the section with `my` off gets `locked-commit.py: command not found`. Batch 2 decides whether to note this in `commit.md` or move the script. Decided on 2026-10-13 by the user: a note in `commit.md`; the script stays in `my`.
- **`kit:dev-reports` names `changelog-management`, a `my` skill, without a prefix** (batch 1 review). The Task 2 sweep and the Task 5 check look for `my:<name>` only, so they cannot see it. With `my` off, the description points at a skill that is not loaded. Task 7 should reword it when it rewords the other method references in `kit`.
- **Between batch 1's merge and its runbook** (batch 1 review), `~/.claude/CLAUDE.md` and the tutor style already name `kit:tutor`, but `kit` is not installed, the tutor hook does not fire, and the `~/bin` md-table links point at the removed `plugins/my/bin/` files. Nothing warns if the runbook is skipped. The review stage runs the runbook right after the merge, in the same session, so the gap lasts minutes. The double hook in open sessions is runbook step 6.
- **Low findings of batch 1's final re-review**, left as they are by the one-fix-round rule:
  - The `~/bin` md-table links could point straight at `~/src/scripts/`, which would remove the gap before runbook step 4 and survive a plugin folder move.
  - The README's Hooks section does not list the `block-autorun-push.py` PreToolUse hook in `my`, so it does not show that turning `my` off drops the push guard. Batch 2 added it.
  - `CLAUDE.md` says the `settings.json` bullet is relative to a plugin folder, but the deny-list `settings.json` is at the repo root. The claim was already false for `my`.
  - `CLAUDE.md` says the manifest "must accurately list" the `commands` and `agents` paths, and also that they are auto-discovered. Neither manifest lists them.
  - The `my` description in `plugin.json` and `marketplace.json` does not tell the method apart from `kit`. Batch 2, which turns `my` off at user scope, is the place to reword it. Batch 2 reworded both descriptions, and `kit`'s.
  - The README's `--plugin-dir` example does not show both flags in one command, for an edit that spans the two plugins.
  - The learning-workspace check exists twice, in `kit`'s tutor hook and in `my`'s squash hook, until Task 7 removes the second copy. Task 7 removed it.
- **Known limits from batch 2's review**, recorded instead of fixed. The first three change the spec's guard contract, and the user chose Risk for each:
  - **A session started in a subfolder gets no guard warning.** Claude Code always sets `CLAUDE_PROJECT_DIR`, so the guard reads the subfolder's `CLAUDE.md` and `.claude/settings.json`, finds no import, and prints nothing, while Claude Code still loads the parent's import. The spec's root rule stays. Sessions, `my:handoff` stages included, start at the repo root. Which settings file Claude Code reads in a subfolder session was not checked.
  - **The warnings always name `.claude/settings.json`.** When `.claude/settings.local.json` sets the key, it wins, and an edit to `settings.json` changes nothing. No repo had local `enabledPlugins` keys on 2026-10-13.
  - **The guard does not run after compaction** (matcher `startup|resume|clear`, as the spec says). The user saw the warning at session start; only the model's copy drops.
  - **`kit:setup` ignores `.claude/settings.local.json`**, so a local value can still override a committed switch. No repo had one on 2026-10-13.
  - **The same import twice reads as "more than one method file: my, my".** Only a hand edit produces it: `kit:setup` removes other import lines from `CLAUDE.md` and does not add one twice.
  - **The import regex also matches an example line inside a fenced code block**, which Claude Code does not import. No project `CLAUDE.md` has such a line.
  - **A `CLAUDE.md` that exists but cannot be read** gives no `could not read` line; the guard treats it as having no import. Only broken file permissions produce it.
- **Known limits from batch 2's final re-reviews**, recorded as the one-fix-round rule says. None is Critical:
  - **A new learning workspace does not get the tutor switch** (Medium). `kit:tutor` sets up a workspace but never writes the tutor import or runs `/kit:setup tutor`. A workspace made in a repo, or a clone of a project, that already has the `my` switch keeps running `my` and superpowers, against D6. The cutover's one tutor repo, `mv3-tab-notes`, gets `/kit:setup tutor` in step 6. Two Low findings follow from the same cause: `my`'s squash-merge hook no longer skips learning workspaces, so such a workspace is told to run `my:roadmap-management`; and the guard does not tie `docs/learning/curriculum.md` to the tutor method, so a workspace that runs `my` passes as consistent.
  - **`kit:setup` removes the other method's import from `CLAUDE.md` only**, not from `CLAUDE.local.md`, which the guard also reads. Its "already set up" checks miss an import there too. No `CLAUDE.local.md` under `~/projects` or `~/src` had a method import on 2026-10-13.
  - **`kit:setup` commits with plain `git commit`**, also in a project with a "Parallel runs" section, where commits in the main checkout go through `locked-commit.py`. Run setup when no auto run is live; the cutover's step 1 makes sure of that.
  - **The tutor commit always runs the `.claude/settings.json` ignore check**, even when it commits only `CLAUDE.md`. It can stop, or propose a `.gitignore` rewrite, that the commit does not need.
  - **An ignore rule from the global excludes file or `.git/info/exclude`** is not undone by the proposed `.gitignore` edit, so the switch still cannot be committed. The setup shows the rule's source with `check-ignore -v`.
  - **A read of `~/.claude.json` while another session writes it** may fail; the guard then says `could not read` and skips the approval warnings for that start. Whether Claude Code writes that file atomically was not checked.
  - **The README install block turns `my` off at user scope but not superpowers.** Under D18, superpowers counts as on when no settings file names it, so on a fresh machine the guard warns in every project without a method until `"superpowers@synced": false` is set in `~/.claude/settings.json`. Cutover step 4 sets it on this machine.
- The spec's Risk section holds the rest, unchanged: hard-to-reverse import lines in 22 repos, worktree paths with their own approval flag, the core boundary, memory size, and the guard not checking the method file's content.

## Testing Strategy

- Unit: `test_method_guard.py` (Task 4) and `test_neutral_core.py` (Tasks 5 and 7), run as subprocesses in the style of `test_block_autorun_push.py`.
- Regression: the 145 `my` tests after every task.
- Rename: the sweep in Task 2.
- Text move: the one-time line check in Task 5, its output kept in "Task 0 results".
- Rehearsals: Task 3's checks, Task 8's setup rehearsal, and the batch 1 runbook's step 5 checks.
- After the cutover: runbook steps 7 and 9 in all 22 repos.

## Open Questions

None. Task 3 may reopen D7 or change the guard; then the stage stops and asks.

## Task 0 results

Run on 2026-10-13 with Claude Code 2.1.296, in scratch folders under the session's scratchpad.

- **Check 1, `"superpowers@synced": false` at user scope.** Baseline with today's settings: the `claude -p --verbose --output-format stream-json` init line lists the plugin `superpowers` (source `superpowers@synced`) and 15 `superpowers:` skills. With the key set to `false` in `~/.claude/settings.json`: no superpowers plugin and no `superpowers` skill. The edit lasted about 5 seconds; the file was restored, and `diff` against the backup showed no difference. Confirms D7. Note: the init line is not the first stream line (a hook event comes first); select it with `select(.type=="system" and .subtype=="init")`.
- **Check 3, declined once.** In a fresh scratch repo, the user declined the import prompt, exited and started `claude` again: it did not ask a second time. `~/.claude.json` then holds `hasClaudeMdExternalIncludesApproved: false` and `hasClaudeMdExternalIncludesWarningShown: true` for that path. So "start a new interactive session" does not bring the prompt back after a decline. Then the reset was tested: with `hasClaudeMdExternalIncludesWarningShown` set to `false` for that path (nothing else in `~/.claude.json` changed), the next start asked again; the user approved, and both flags became `true`. The guard changed, with the user's yes: a new `declined` warning, given in place of `not_approved` when the flag is not `true` and the prompt was shown, names this reset (Task 4 table and test, cutover steps 7 and 8).
- **Check 4, parent folder.** A parent folder's `CLAUDE.md` import loads in a nested repo (the session quoted the parent's marker). The approval flags were set on the nested repo's path only; the parent path has no entry. Under D13 the parents hold no import, so nothing reaches the nested repos twice.
- **Check 5, import into the same repo.** With `~/.claude/methods` a temporary link into the scratch repo, `@~/.claude/methods/my.md` loaded (the session quoted the marker) and `hasClaudeMdExternalIncludesApproved` became `true` for the repo. The guard's approval input needs no change. The link was removed after the check.
- **Check 6, missing target.** `claude -p 'reply ok'` with an import of a file that does not exist printed `ok`, exited 0 and wrote nothing to stderr, both in a repo that never approved the import and in a repo that had approved it (after the link was removed). Confirms the silence the Rollback relies on.
- **Check 2, the setup rehearsal (Task 8).** A copy of `~/projects/notes-cli`, with its `.git` and its uncommitted deletions, in the scratchpad; `~/.claude/methods` a temporary link to the worktree's `global/methods/`. The user started a session in `~/projects/claude-setup` with `--plugin-dir <worktree>/plugins/kit`, in auto mode; `/kit:setup` was offered, so the worktree copy was loaded. `/kit:setup my <copy>` wrote and committed into the other repo with no refusal and no permission prompt, so the cutover's step 5 session needs no `--add-dir`. The commit `chore: switch to the my method` listed only `CLAUDE.md` and `.claude/settings.json`; the facts block matched the skill's format; the 36 uncommitted changes of the copy were left alone. The repo's pre-commit hook first rejected the commit: `notes-cli`'s `.git/hooks/pre-commit` names `INSTALL_PYTHON=/home/dchris/Documents/notes/.venv/bin/python`, a path that no longer exists, so the hook needs `pre-commit` on `PATH`, as that repo's `CLAUDE.md` says. The session found that and ran the hook; it did not skip it. This holds for the real repo too: running `.venv/bin/pre-commit install` in `~/projects/notes-cli` before the cutover rewrites the hook. `kit:setup` gained one sentence for this case (read the project's `CLAUDE.md` for how its hooks run; never `--no-verify`). The guard then gave only `not_approved` for `my`. Before approval, `claude -p` in the copy did not see `my.md` (the import arrived as a literal line). The user approved the import in an interactive session; `hasClaudeMdExternalIncludesApproved` became `true`, `claude -p` quoted "The rules of the `my` method.", and the guard printed nothing. The link and the copy were removed.
- **The guard through Claude Code (Task 9).** In a scratch folder, `claude -p --plugin-dir <worktree>/plugins/kit --verbose --output-format stream-json` with the user's settings of today (`my` on at user scope, no import): the stream shows the `SessionStart:startup` hook response with exit code 0 and outcome `success`, its output the `plugins_stray` JSON, and the model quoted the `plugins_stray` line. So Claude Code runs the `hooks.json` entry, fills in `$CLAUDE_PLUGIN_ROOT` and accepts the output.

### Text move check

Task 5, step 7, run on 2026-10-13 against `main`'s `global/CLAUDE.md`. Exit 0. The old file was saved to the scratchpad first, because the script reads it twice and a `<(…)` pipe can be read only once. Output:

```text
allowed (item 2: Precedence): **Precedence:** these project instructions are the highest authority —
allowed (item 5: Before step 1): **Before step 1 in a project for the first time,** check that the proj
allowed (item 3: Planning Standards intro): These standards apply to **all** planning workflows — built-in plan mo
allowed (item 4: Reference Sweep): When a plan removes/renames/changes the signature of a cross-file symb
```

## Batch 2 end-of-branch checks

Run by the `my:handoff` review stage on 2026-10-13, after the user had the branch rebased onto `main`. The user chose these checks, because the project's rules name none.

- `kit` suite: `Ran 28 tests`, `OK`, before and after the fix round.
- `my` suite: `Ran 146 tests`, `OK` (`main` gained one test since the plan was written).
- markdownlint against `main`: no new error kind; MD013 (line length) rose by 31, which the user accepted as not blocking. The fix round added no new error kind.
- Reviews: `docs/plans/2026-10-13-feat-swappable-methods-cutover-review.md` and `…-code-review.md`, then one fix round, then the final re-reviews `…-review-2.md` and `…-code-review-2.md`. No Critical finding; the rest is in Risk.

Summary for the `done` marks: 3 checks run, 3 passed (the lint check with 31 accepted MD013 errors). Batch 1's counts are in its squash commit message.
