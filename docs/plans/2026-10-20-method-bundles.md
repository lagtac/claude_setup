# Methods as Plugins Implementation Plan

**Status:** current, 2026-10-22. Batch 1 merged in `1a6d653`; rollout, then batch 2. Written by
the `my:handoff` plan stage from the approved spec; row 68.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this
> plan task-by-task. The tasks build on each other: the start check and `/kit:setup` call
> `claude-method`, the styles point at `engineering.md`, and each move is checked by a diff
> against the files it replaces, which needs one context. The project's review rules (the `my`
> rules, "Code Review Routing") replace the skill's own reviews: no per-task reviewer, no final
> `requesting-code-review` pass. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Each method (`my`, `tutor`, `sp`) becomes a plugin whose forced output style holds its
rules and whose `dependencies` hold its plugin set; a folder's settings name its method,
`claude-method <m>` starts one session with another method, and `/kit:method <m>` switches a
folder during a session.

**Architecture:** One script, `plugins/kit/bin/claude-method`, is the only reader of the method
list (`marketplace.json`, `"category": "method"`) and of each method's `dependencies`. The start
check, `/kit:setup` and `/kit:method` call it. The rule files move into plugin styles, the core
loses its development rules to a path-scoped `global/rules/engineering.md`, and the import line
goes.

**Tech Stack:** Python 3 standard library, `unittest`, Claude Code plugins (output styles with
`force-for-plugin`, `dependencies`, `--settings`, `claude plugin enable|disable --scope local`),
Markdown skills.

**Spec:** `docs/plans/2026-10-20-method-bundles-spec.md` (review:
`docs/plans/2026-10-20-method-bundles-spec-review.md`; brief:
`docs/plans/2026-10-20-method-bundles-architecture.md`).

**Commit type:** `feat`. Two batches, two branches (spec D13):

| Batch | Tasks | Branch | Worktree | Squash subject |
| --- | --- | --- | --- | --- |
| 1 | 1–9 | `feat/method-bundles` | `.claude/worktrees/method-bundles` | `feat(global): methods become plugins with forced styles` |
| 2 | 10–12 | `feat/method-bundles-switch` | `.claude/worktrees/method-bundles-switch` | `feat(kit-plugin): claude-method and /kit:method switch the method` |

**How the batches run with `my:handoff`:**

- A code stage carries out one batch. It runs batch 1 while this plan's status line does not say
  "Batch 1 merged", and batch 2 after that. The worktree and branch are the ones the table names,
  so the start checks use those names, not `*/<slug>`.
- Batch 1's review stage merges batch 1 and sets the batch 1 marks below. It sets no `done` mark.
- Between the batches the user runs the rollout ("Rollout after batch 1" below).
- Then the user starts batch 2 with `/my:handoff code docs/plans/2026-10-20-method-bundles.md`.
  Batch 2's review stage sets the `done` marks.

**Batch 1 marks**, set on `main` after the squash-merge, in one `docs:` commit:

- This plan's status: `current, <date>. Batch 1 merged in <hash>; rollout, then batch 2.`
- The spec's status: `current, <date>. Batch 1 merged in <hash>.`
- `ROADMAP.md`: row 68 goes 📋 → 🚧 with "Batch 1 merged in `<hash>`; rollout and batch 2 next."
  The rows that name `global/methods/my.md`, `docs-layout.md`, `plan-format.md` or
  `global/output-styles/plain.md` as a file to edit name the `my` style
  (`plugins/my/output-styles/my.md`) or the core instead (spec, Files, `ROADMAP.md`). Find them
  with `grep -nE 'global/methods/my\.md|docs-layout|plan-format|output-styles/plain' ROADMAP.md`;
  leave ✅ rows and the "Order of work" history as they are. These edits wait for the marks so
  that the branch does not fight other sessions' roadmap edits.
- `CHANGELOG.md`: one entry for batch 1 by `my:changelog-management`: methods are plugins, the
  import line is gone, and the rollout is manual.

**Batch 2 marks** are the usual `done` marks: plan and spec `done`, row 68 ✅, a changelog entry.

## Global Constraints

- Python 3, standard library only. No new dependency (spec, Dependencies).
- Claude Code 2.1.304 or later (`force-for-plugin`, `dependencies`, in-place loading).
- A method is a `marketplace.json` entry with `"category": "method"`. Its key is
  `<name>@<marketplace name>`, here `<name>@claude-setup`. `none` means no method.
- Plugin keys come only from manifests (spec, `claude-method`). No file but `claude-method`
  reads `dependencies`.
- Every style's frontmatter has exactly `name`, `description`, `force-for-plugin: true` and
  `keep-coding-instructions: true` (spec, Method plugins).
- Moved text is moved as it is on `main` when batch 1 starts. Only the changes that the spec's
  "Rules for the moved text" name are made. Each move ends with a diff check.
- Every file under `plugins/kit/` except `tests/` and `skills/setup/` holds none of:
  `superpowers:`, `docs/plans`, `global/CLAUDE.md`, a `my:<name>` skill name
  (`test_kit_cites_no_method`).
- No `$` followed by a digit in any kit `SKILL.md` (`test_skill_placeholders.py`).
- Focused test runs: `cd plugins/kit && python3 -m unittest discover tests -p '<file>'`
  (`plugins/kit/tests` has no `__init__.py`). Full runs, once per task before its first commit:
  `cd plugins/kit && python3 -m unittest discover tests` and
  `cd plugins/my && python3 -m unittest discover tests`. While a task is in progress, run only
  the test files it touches, chained with `&&`. A fix round reruns only the test files that cover
  the fix.
- Tests live under `plugins/kit/tests/` or `plugins/my/tests/`: the test command runs only those
  two folders. `plugins/tutor/` and `plugins/sp/` get no `tests/` folder.
- Headless runs on the branch load the branch's copy: `--plugin-dir <worktree>/plugins/<p>`, and
  `claude-method` turns `<p>@claude-setup` off for a method (spec, Testing strategy). For `kit`,
  add `--settings '{"enabledPlugins":{"kit@claude-setup":false}}'` when `claude-method` is not
  the launcher. Run them in a fixture folder in the session's scratchpad, never inside this repo.
  A headless run that calls `claude-method` against the branch's marketplace sets
  `CLAUDE_METHOD_MARKETPLACE=<worktree>` (Task 2). `$SCRATCH` is the session's scratchpad
  folder; `<worktree>` is the batch's worktree as an absolute path.
- Markdown lint for each `.md` file a task writes:
  `markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc <files>`.
- Every task commit carries `--trailer "Task: <N>"`.

## Review Focus

1. **`--plugin-dir=<path>` with `=`, and a relative `--plugin-dir plugins/my`.** A person expects
   both forms to turn the method's `@claude-setup` key off, with the path read from the current
   folder. Test: Task 2, `test_plugin_dir_with_equals_and_relative_path`.
2. **`--settings=<json>` with `=`.** A person expects the same refusal as `--settings <json>`,
   exit 2, and no `claude` run. Test: Task 2, `test_settings_flag_is_refused_with_exit_2`.
3. **A dependency written as a bare name or as an object** (`"kit"`,
   `{"name": "x", "marketplace": "other"}`), as the dependencies docs allow. Expected: full keys
   `kit@claude-setup` and `x@other`, so the off set holds real keys. Test: Task 2,
   `test_bare_and_object_dependencies_get_full_keys`.
4. **The start check with no `claude-method`, or one that fails** (no marketplace entry, script
   missing). Expected: one warning naming the error, exit 0, no other judgement. Tests: Task 7,
   `test_claude_method_failure_gives_one_warning` and `test_missing_script_gives_one_warning`.
5. **An `enabledPlugins` value that is not a boolean** (`"true"`, `1`). Expected: it does not
   count as on, as today. Test: Task 7, `test_string_true_is_not_on`.

---

## Context

Today a project picks a method in two places: an import line such as `@~/.claude/methods/my.md`
in its `CLAUDE.md`, and `enabledPlugins` keys in `.claude/settings.json`. `method-guard.py`
warns when they disagree. The spec moves the rules into plugin output styles that the plugin
forces on, so rules and plugins load and unload together (spec, Context; brief, Decision A).

What exists, read on 2026-10-21:

- `global/methods/my.md` (29,666 chars), `global/rules/docs-layout.md` (11,049) and
  `global/rules/plan-format.md` (1,686) make the `my` style, about 42,400 chars.
- `global/output-styles/tutor.md` and `global/methods/tutor.md` make the `tutor` style.
- `global/CLAUDE.md` holds the core; `global/output-styles/plain.md` the `plain` style.
- `plugins/kit/hooks/method-guard.py` is the pattern for a hook script: a module docstring,
  `main()`, a `try/except Exception: pass` around it, `sys.exit(0)`.
  `plugins/kit/tests/test_method_guard.py` is the pattern for its tests: a temporary `HOME` and
  project, the real script run with `subprocess`, the environment set per call.
- `plugins/kit/bin/` is on `PATH` in Claude Code sessions. `~/bin` is on the shell's `PATH` and on
  the tmux server's `PATH` (checked 2026-10-21).
- `~/.claude/plugins/known_marketplaces.json` has the entry `claude-setup` with
  `"installLocation": "/home/dchris/projects/claude-setup"`.
- The `paths:` rule probe ran in the plan stage on Claude Code 2.1.306 (fixture repo, rule with
  a codeword, `paths: ["**/*.py"]`). The rule loaded when the session created `new.py` with the
  `Write` tool, read it with `Read`, or read it with a Bash `cat`. It did not load in a control
  run with no file, nor when a Bash redirect (`printf … > new.py`) created the file. So D2 holds
  for the tools a session uses to write code; the redirect case is in Risk.

Ten repos run `my` today, not nine as the spec says: the sweep found `~/src/scripts` too. It is
handled like the other dormant repos (start check 3), so no decision changes.

## Files to Modify/Create

From the reference sweep on 2026-10-21:
`git grep -nE 'methods/(my|tutor)\.md|global/methods|\.claude/methods|docs-layout|plan-format|output-styles|plain\.md|kit:tutor|method-guard|outputStyle|\*\*Method:\*\*|Applies only in projects whose|Engineering standards|Mandatory Exploration|Reference Sweep|Simplicity Rules|in the core|the core'"'"'s'`
outside `docs/plans/`, `docs/reports/` and `CHANGELOG.md`; `grep -n 'claude -n'` in the handoff
skill; the same tokens in every other repo's `CLAUDE.md`, `CLAUDE.local.md` and `.claude/rules/`.
Edits are anchored by quoted text, not line numbers: rows 62 and others move lines first.

| File | Change | Task |
| --- | --- | --- |
| `plugins/kit/bin/claude-method` | New, executable | 2 |
| `plugins/kit/tests/test_claude_method.py` | New | 2, 6 |
| `global/CLAUDE.md` | Split; `plain` text in; new Precedence | 3 |
| `global/rules/engineering.md` | New, path-scoped | 3 |
| `global/output-styles/plain.md` | Deleted | 3 |
| `plugins/kit/tests/test_neutral_core.py` | Core, style, plugin and sweep tests | 3, 4, 5, 6, 9 |
| `plugins/my/output-styles/my.md` | New: the `my` style | 4 |
| `plugins/my/.claude-plugin/plugin.json` | `dependencies`; description | 4 |
| `global/methods/my.md`, `global/rules/docs-layout.md`, `global/rules/plan-format.md` | Deleted | 4 |
| `plugins/my/skills/status/SKILL.md` | "in `~/.claude/methods/my.md`" → the `my` style | 4 |
| `plugins/my/skills/handoff/README.md` | "The spec rules in `~/.claude/methods/my.md`" → the `my` style | 4 |
| `plugins/my/skills/clean-plans/SKILL.md` | "(`~/.claude/rules/docs-layout.md`)" → the `my` style | 4 |
| `plugins/my/skills/architect/SKILL.md` | "where the plan-format rule loads" → the `my` style's plan format | 4 |
| `plugins/my/README.md` | "Where the parts live", and every `docs-layout.md` and `global/methods/my.md` pointer | 4 |
| `global/git-hooks/pre-commit` | Comments "see docs-layout.md" and "Rule in ~/.claude/CLAUDE.md, Git Workflow" → the `my` style | 4 |
| `global/git-hooks/pre-push` | Comment "Rules in ~/.claude/rules/docs-layout.md" → the `my` style | 4 |
| `.claude-plugin/marketplace.json` | `my` category `method`; `tutor`, `sp` added; `my`, `kit` descriptions | 4, 5, 6 |
| `plugins/tutor/.claude-plugin/plugin.json` | New | 5 |
| `plugins/tutor/output-styles/tutor.md` | New: the `tutor` style | 5 |
| `plugins/tutor/skills/tutor/` | `git mv` from `plugins/kit/skills/tutor/`; `SKILL.md` and `method.md` edits | 5 |
| `global/methods/tutor.md`, `global/output-styles/tutor.md` | Deleted (the two folders go) | 5 |
| `plugins/kit/hooks/hooks.json` | Tutor hook deleted | 5 |
| `plugins/kit/.claude-plugin/plugin.json` | Description: no tutor, the new start check | 5 |
| `plugins/kit/skills/design-router/plugins.json` | `"tutor": "not-design"`, `"sp": "not-design"` | 5, 6 |
| `plugins/kit/tests/test_design_router.py` | `test_list_states_are_valid` checks `tutor`, `sp` | 5, 6 |
| `plugins/sp/.claude-plugin/plugin.json`, `plugins/sp/output-styles/sp.md` | New | 6 |
| `plugins/kit/hooks/method-guard.py` | Rewritten | 7 |
| `plugins/kit/tests/test_method_guard.py` | Rewritten | 5, 7 |
| `plugins/kit/skills/setup/SKILL.md` | Rewritten | 8 |
| `CLAUDE.md` | Import and `**Method:**` lines go; plugin list; scopes `tutor-plugin`, `sp-plugin` | 9 |
| `projects/real-estate-webapp/claude-local.md` | Import and `**Method:**` lines go; "`docs-layout.md`" pointer | 9 |
| `README.md` | `global/` folder, methods section, `kit:tutor`, `docs-layout.md`, Hooks | 9, 12 |
| `ROADMAP.md`, `CHANGELOG.md` | At the batch marks only | — |
| `plugins/kit/skills/method/SKILL.md` | New | 11 |
| `plugins/my/skills/handoff/SKILL.md` | The four launch lines | 12 |

Not changed: `docs/plans/` and `docs/reports/` (they record what was true then), `CHANGELOG.md`
history, `plugins/kit/skills/tune-claude-instructions/SKILL.md` (it names `~/.claude/CLAUDE.md`,
which stays). `my.md`'s "the core in `~/.claude/CLAUDE.md`" (Precedence) and "Critical Thinking
(in the core)" stay true and stay.

Other repos: `maritime`, `mv3-starter`, `niche-research`, `grispy-web-ext/grispy-site`,
`grispy-web-ext/grispy-ext`, `diagoradisa/diagoradisa-palmist`, `diagoradisa/diagoradisa-annotator`
and `~/src/scripts` keep their import line until next opened (start check 3). `mv3-tab-notes`
moves in rollout step 5. None of their `CLAUDE.md` files name `docs-layout`, `plan-format`,
`kit:tutor` or `output-styles`.

## Step-by-Step Implementation

### Task 1: start conditions (batch 1)

No code and no commit.

- [ ] **Step 1: Check the blocker.** Run `grep -nE '^- ✅ 62 ' ROADMAP.md` in the main checkout.
  Expected: one line. If it prints nothing, row 62 has not merged: signal
  `code-method-bundles: batch 1 waits for row 62 (spec, Dependencies)` and stop.
- [ ] **Step 2: Check the version.** `claude --version` prints 2.1.304 or later.
- [ ] **Step 3: Note the start.** Record `git rev-parse --short main` in the session. Every "as
  on `main`" below means this commit.

### Task 2: `claude-method`

**Files:**

- Create: `plugins/kit/bin/claude-method` (mode 755, `#!/usr/bin/env python3`, no extension)
- Test: `plugins/kit/tests/test_claude_method.py`

**Interfaces:**

- Produces, as a command line:
  - `claude-method` → one line per method, `<name>\t<description>`, in marketplace order, then
    `none\tNo method: every method and its plugins off`; exit 0.
  - `claude-method <unknown> [...]` → stderr `claude-method: no method named <unknown>`, then the
    list; exit 1.
  - `claude-method --json <m>` → stdout one line, `json.dumps({"enabledPlugins": {...}},
    sort_keys=True)`; exit 0. The chosen method and its dependencies `true`, the off set `false`.
  - `claude-method --methods` → stdout `json.dumps({<method key>: [<dependency keys>]},
    sort_keys=True)`; exit 0.
  - `claude-method <m> [<args>...]` → `os.execvp("claude", ["claude", "--settings", <json>,
    *args])`, with the `--plugin-dir` rule applied to `<json>`.
  - `--settings` or `--settings=…` anywhere in `<args>` → stderr
    `claude-method: --settings is not allowed; claude-method passes its own`, exit 2.
  - An unreadable file, or no `claude-setup` entry → stderr `claude-method: <path>: <reason>`,
    exit 1.
- Marketplace folder: `$CLAUDE_METHOD_MARKETPLACE` when set (tests and branch runs), else
  `installLocation` of entry `claude-setup` in `$HOME/.claude/plugins/known_marketplaces.json`.
  Its `.claude-plugin/marketplace.json` gives the marketplace `name` and the entries; each entry's
  `source` (relative to the folder) holds `.claude-plugin/plugin.json`.
- Dependency entries become keys: `"a@b"` stays; a bare `"a"` becomes `a@<marketplace name>`;
  `{"name": "a"}` becomes `a@<marketplace name>`, and `{"name": "a", "marketplace": "b"}`
  becomes `a@b`. No `dependencies` field means none.
- `main(argv: list[str]) -> int`; the script ends with `sys.exit(main(sys.argv[1:]))`.

- [ ] **Step 1: Write the failing tests.** The module builds a fake marketplace in a temporary
  folder: `marketplace.json` named `claude-setup` with entries `my`, `kit` (category
  `development`), `sp` and `tutor` (category `method`, except `kit`), each with a `plugin.json`;
  `my` and `sp` depend on `superpowers@synced`. A fake `HOME` holds `known_marketplaces.json`
  pointing at it. Each test runs the script with `subprocess`, `HOME` set, and
  `CLAUDE_METHOD_MARKETPLACE` removed from the environment unless the test sets it.

  ```python
  MY = {"my@claude-setup": True, "superpowers@synced": True,
        "sp@claude-setup": False, "tutor@claude-setup": False}

  def test_no_argument_lists_methods_and_none(self):
      r = self.run_cm()
      self.assertEqual(r.returncode, 0)
      self.assertEqual([l.split("\t")[0] for l in r.stdout.splitlines()],
                       ["my", "sp", "tutor", "none"])

  def test_unknown_method_lists_and_exits_1(self):
      r = self.run_cm("nope")
      self.assertEqual(r.returncode, 1)
      self.assertIn("claude-method: no method named nope", r.stderr)
      self.assertIn("tutor\t", r.stderr)

  def test_json_my(self):
      self.assertEqual(self.settings("--json", "my"), {"enabledPlugins": MY})

  def test_json_tutor_turns_superpowers_off(self):
      self.assertEqual(self.settings("--json", "tutor")["enabledPlugins"],
                       {"tutor@claude-setup": True, "my@claude-setup": False,
                        "sp@claude-setup": False, "superpowers@synced": False})

  def test_json_sp_keeps_shared_dependency_on(self):
      self.assertEqual(self.settings("--json", "sp")["enabledPlugins"],
                       {"sp@claude-setup": True, "superpowers@synced": True,
                        "my@claude-setup": False, "tutor@claude-setup": False})

  def test_json_none_turns_everything_off(self):
      self.assertEqual(set(self.settings("--json", "none")["enabledPlugins"].values()), {False})

  def test_methods_maps_each_method_to_its_dependencies(self):
      self.assertEqual(self.settings("--methods"),
                       {"my@claude-setup": ["superpowers@synced"],
                        "sp@claude-setup": ["superpowers@synced"], "tutor@claude-setup": []})

  def test_bare_and_object_dependencies_get_full_keys(self):
      # tutor's plugin.json: ["kit", {"name": "x", "marketplace": "other"}, {"name": "y"}]
      self.assertEqual(self.settings("--methods")["tutor@claude-setup"],
                       ["kit@claude-setup", "x@other", "y@claude-setup"])

  def test_exec_runs_claude_with_settings_and_args(self):
      # a fake `claude` first on PATH prints json.dumps(sys.argv[1:])
      argv = json.loads(self.run_cm("my", "-n", "x", "-p", "hi").stdout)
      self.assertEqual(argv[0], "--settings")
      self.assertEqual(json.loads(argv[1]), {"enabledPlugins": MY})
      self.assertEqual(argv[2:], ["-n", "x", "-p", "hi"])

  def test_plugin_dir_naming_a_method_turns_its_marketplace_key_off(self):
      argv = json.loads(self.run_cm("my", "--plugin-dir", str(self.market / "plugins/my")).stdout)
      self.assertEqual(json.loads(argv[1])["enabledPlugins"]["my@claude-setup"], False)
      self.assertEqual(json.loads(argv[1])["enabledPlugins"]["superpowers@synced"], True)
      self.assertEqual(argv[2:], ["--plugin-dir", str(self.market / "plugins/my")])

  def test_plugin_dir_with_equals_and_relative_path(self):
      argv = json.loads(self.run_cm("my", "--plugin-dir=plugins/my", cwd=self.market).stdout)
      self.assertEqual(json.loads(argv[1])["enabledPlugins"]["my@claude-setup"], False)

  def test_plugin_dir_not_a_method_changes_nothing(self):
      argv = json.loads(self.run_cm("my", "--plugin-dir", str(self.market / "plugins/kit")).stdout)
      self.assertEqual(json.loads(argv[1]), {"enabledPlugins": MY})

  def test_settings_flag_is_refused_with_exit_2(self):
      for args in (["--settings", "{}"], ["--settings={}"]):
          r = self.run_cm("my", "-p", "x", *args)
          self.assertEqual(r.returncode, 2)
          self.assertIn("--settings is not allowed", r.stderr)
          self.assertEqual(r.stdout, "")   # the fake claude never ran

  def test_missing_marketplace_entry_exits_1_naming_the_file(self):
      # known_marketplaces.json without "claude-setup"
      r = self.run_cm("--methods")
      self.assertEqual(r.returncode, 1)
      self.assertIn("known_marketplaces.json", r.stderr)

  def test_unreadable_marketplace_json_exits_1_naming_the_file(self):
      # marketplace.json holds "{"
      r = self.run_cm("--methods")
      self.assertEqual(r.returncode, 1)
      self.assertIn("marketplace.json", r.stderr)

  def test_marketplace_variable_wins(self):
      # known_marketplaces.json points at a folder that does not exist
      r = self.run_cm("--methods", env={"CLAUDE_METHOD_MARKETPLACE": str(self.market)})
      self.assertEqual(r.returncode, 0)
  ```

- [ ] **Step 2: Run them and see them fail.**
  `cd plugins/kit && python3 -m unittest discover tests -p 'test_claude_method.py'`.
  Expected: every test fails, because the script does not exist.
- [ ] **Step 3: Write `plugins/kit/bin/claude-method`** to the Interfaces above. A module
  docstring in the style of `method-guard.py` says what it reads and prints. The off set is
  (every method key ∪ every dependency key) − ({chosen key} ∪ its dependency keys). The
  `--plugin-dir` rule reads `<dir>/.claude-plugin/plugin.json` `name` with the path resolved
  against the current folder, and ignores a folder it cannot read.
- [ ] **Step 4: Run the tests and see them pass.** Same command. Expected: `OK`.
- [ ] **Step 5: Commit.**
  `git add plugins/kit/bin/claude-method plugins/kit/tests/test_claude_method.py` and
  `git commit -m "feat(kit-plugin): add claude-method, the one reader of the method list" --trailer "Task: 2"`.

### Task 3: the core and `engineering.md`

**Files:**

- Modify: `global/CLAUDE.md`
- Create: `global/rules/engineering.md`
- Delete: `global/output-styles/plain.md`
- Test: `plugins/kit/tests/test_neutral_core.py`

**Interfaces:**

- Produces: `~/.claude/rules/engineering.md`, which Tasks 4, 5 and 9 point at by that path.

- [ ] **Step 1: Write the failing tests** in `test_neutral_core.py`. Remove
  `test_core_has_engineering_standards`. Add `ENGINEERING = REPO / "global" / "rules" /
  "engineering.md"` and:

  ```python
  def test_core_holds_plain_rules(self):
      core = CORE.read_text()
      self.assertIn("**One idea per sentence.**", core)
      self.assertIn("Check before sending", headings(core))
      self.assertNotIn("output-styles/", core)

  def test_core_keeps_neutral_sections(self):
      self.assertTrue({"Communication", "Critical Thinking", "Design work", "HTTP Requests"}
                      <= headings(CORE.read_text()))

  def test_core_has_no_engineering_sections(self):
      core = CORE.read_text()
      for heading in ["Code", "Engineering standards", "Mandatory Exploration",
                      "Reference Sweep", "Simplicity Rules"]:
          with self.subTest(heading=heading):
              self.assertNotIn(heading, headings(core))
      self.assertNotIn("Verify against ground truth", core)

  def test_core_precedence_names_rules_and_style(self):
      core = " ".join(CORE.read_text().split())
      self.assertIn("the rule files in `~/.claude/rules/`, and the active method's rules "
                    "(the output style its plugin forces on)", core)

  def test_engineering_rules_are_path_scoped(self):
      text = ENGINEERING.read_text()
      self.assertTrue(text.startswith(
          '---\npaths:\n'
          '  - "**/*.{py,js,ts,jsx,tsx,mjs,cjs,vue,php,sh,go,rs,java,rb,lua,sql,css,scss,html}"\n'
          '  - "**/{package.json,composer.json,pyproject.toml,Dockerfile}"\n'
          '  - "**/docs/plans/*.md"\n---\n'))
      self.assertTrue({"Code", "Engineering standards", "Mandatory Exploration",
                       "Reference Sweep", "Simplicity Rules"} <= headings(text))
      self.assertIn("**Verify against ground truth, not the artifact.**", text)
  ```

- [ ] **Step 2: Run them and see them fail.**
  `cd plugins/kit && python3 -m unittest discover tests -p 'test_neutral_core.py'`. Expected: the
  four new tests fail (no `engineering.md`, old core). `test_core_keeps_neutral_sections`
  passes already, because the four sections exist today; it guards that the rewrite keeps them,
  and it never went red.
- [ ] **Step 3: Write `global/rules/engineering.md`:** the frontmatter the test pins, a blank
  line, `# Engineering rules`, then, word for word from the core: the `## Code` section, and the
  `## Engineering standards` section with its intro paragraph, "Verify against ground truth",
  `### Mandatory Exploration`, `### Reference Sweep` and `### Simplicity Rules`.
  `### Critical Thinking` does not move.
- [ ] **Step 4: Rewrite `global/CLAUDE.md`** in this order (spec, "The core and
  `engineering.md`"):
  1. `# Instructions`.
  2. `**Precedence:**` followed by the spec's text, word for word: "this file, the rule files in
     `~/.claude/rules/`, and the active method's rules (the output style its plugin forces on)
     are the highest authority: when plan mode, a skill or a system default conflicts, follow
     them. The rules in this file and in `~/.claude/rules/` hold under every method. A method may
     add rules. It may name an exception to a rule in this file or in
     `~/.claude/rules/engineering.md` only by naming the rule."
  3. `**Important:**` as it is.
  4. `## Communication`: the bullet "Challenge assumptions — …" as it is, then the body of
     `plain.md` without its frontmatter. The bullet that points at the `plain` style goes. Its
     three `##` headings become `###`, so they sit under Communication; their text is unchanged.
  5. `## Critical Thinking`: the five bullets, as they are.
  6. `## Design work`, as it is.
  7. `## HTTP Requests`, as it is.
  8. The HTML comment about language rules, as it is, moved to the end (spec: "The HTML comment
     at the end"; on `main` it sits before `## HTTP Requests`).
- [ ] **Step 5: Delete `global/output-styles/plain.md`** with `git rm`.
- [ ] **Step 6: Check the moves.** Compare the non-blank lines of the old core and `plain.md`
  (from `main`) with those of the new core and `engineering.md`:

  ```bash
  python3 - <<'EOF'
  import subprocess
  def lines(text): return {l for l in text.splitlines() if l.strip()}
  show = lambda p: subprocess.run(["git", "show", f"main:{p}"], capture_output=True, text=True).stdout
  old = lines(show("global/CLAUDE.md")) | lines(show("global/output-styles/plain.md"))
  new = lines(open("global/CLAUDE.md").read()) | lines(open("global/rules/engineering.md").read())
  print("GONE:", *sorted(old - new), sep="\n  ")
  print("ADDED:", *sorted(new - old), sep="\n  ")
  EOF
  ```

  Expected GONE: the old Precedence line, the bullet that points at the `plain` style, `###
  Critical Thinking`, `plain.md`'s frontmatter lines and its three `##` headings. Expected ADDED:
  the new Precedence line, `## Critical Thinking`, the three `###` headings, the
  `engineering.md` frontmatter lines and `# Engineering rules`. Any other line means a move
  changed text: fix it.
- [ ] **Step 7: Run the tests and see them pass.** Focused run, then the full runs. Expected: `OK`.
  `test_kit_cites_no_method` still passes.
- [ ] **Step 8: Lint and commit.** Lint `global/CLAUDE.md` and `global/rules/engineering.md`.
  `git add global/CLAUDE.md global/rules/engineering.md plugins/kit/tests/test_neutral_core.py`,
  `git rm` already staged the deletion, then
  `git commit -m "feat(global): the core keeps neutral rules; engineering rules load with code" --trailer "Task: 3"`.

### Task 4: the `my` style

**Files:**

- Create: `plugins/my/output-styles/my.md`
- Modify: `plugins/my/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `plugins/my/skills/status/SKILL.md`, `plugins/my/skills/handoff/README.md`,
  `plugins/my/skills/clean-plans/SKILL.md`, `plugins/my/skills/architect/SKILL.md`,
  `plugins/my/README.md`, `global/git-hooks/pre-commit`, `global/git-hooks/pre-push`
- Delete: `global/methods/my.md`, `global/rules/docs-layout.md`, `global/rules/plan-format.md`
- Test: `plugins/kit/tests/test_neutral_core.py`

**Interfaces:**

- Consumes: `~/.claude/rules/engineering.md` (Task 3); `claude-method` (Task 2) for the headless
  check.
- Produces: `METHODS`, a test helper in `test_neutral_core.py`:
  `def methods() -> dict[str, dict]`, the marketplace entries whose `category` is `method`, by
  name. Tasks 5 and 6 reuse it. `style(name: str) -> tuple[dict[str, str], str]` returns a
  style's frontmatter and body.

- [ ] **Step 1: Write the failing tests** in `test_neutral_core.py`. Remove
  `test_method_files_exist` and `test_lazy_rules_start_with_applies_line`. Add:

  ```python
  def test_method_styles_have_forced_frontmatter(self):
      self.assertIn("my", methods())   # the loop below asserts nothing while methods() is empty
      for name in methods():
          with self.subTest(method=name):
              meta, _ = style(name)
              self.assertEqual(set(meta), {"name", "description", "force-for-plugin",
                                           "keep-coding-instructions"})
              self.assertEqual(meta["name"], name)
              self.assertEqual(meta["force-for-plugin"], "true")
              self.assertEqual(meta["keep-coding-instructions"], "true")
              self.assertTrue(meta["description"])

  def test_method_manifests_match_marketplace(self):
      self.assertIn("my", methods())
      for name, entry in methods().items():
          with self.subTest(method=name):
              self.assertEqual(entry["source"], f"./plugins/{name}")
              manifest = json.loads((REPO / "plugins" / name / ".claude-plugin"
                                     / "plugin.json").read_text())
              self.assertEqual(manifest["name"], name)
      self.assertEqual(json.loads((REPO / "plugins/my/.claude-plugin/plugin.json")
                                  .read_text())["dependencies"], ["superpowers@synced"])

  def test_no_applies_line_left(self):
      self.assertIn("my", methods())
      for name in methods():
          with self.subTest(method=name):
              self.assertNotIn("Applies only in projects whose", style(name)[1])

  def test_my_style_points_at_no_moved_file(self):
      body = style("my")[1]
      for token in ["docs-layout.md", "plan-format.md", "~/.claude/methods", "That rule loads when",
                    "importing this file", "names the method,", "Mandatory Exploration (in the core)",
                    "Engineering standards in `~/.claude/CLAUDE.md`", "the core's"]:
          with self.subTest(token=token):
              self.assertNotIn(token, body)

  def test_old_rule_files_are_gone(self):
      for rel in ["global/methods/my.md", "global/rules/docs-layout.md",
                  "global/rules/plan-format.md"]:
          with self.subTest(path=rel):
              self.assertFalse((REPO / rel).exists())
  ```

  "Critical Thinking (in the core)" stays: Critical Thinking is still in the core.

- [ ] **Step 2: Run them and see them fail.** Focused run. Expected: all five fail: the first
  three on `assertIn("my", methods())` (no entry has `category: method` yet),
  `test_my_style_points_at_no_moved_file` because the style file is missing, and
  `test_old_rule_files_are_gone` because the old files are present.
- [ ] **Step 3: Write `plugins/my/output-styles/my.md`:** the frontmatter (spec, Method plugins:
  `name: my`, `description: The my method's rules`), a blank line, the body of
  `global/methods/my.md`, a blank line, `global/rules/docs-layout.md` without its frontmatter
  and its "Applies only…" line, a blank line, `global/rules/plan-format.md` the same way. The
  three `#` headings stay as they are. Then make exactly these edits (spec rules 2 to 7), each
  anchored by the old text:

  | Old text (as on `main`) | New text |
  | --- | --- |
  | "A project uses them by importing this file from its `CLAUDE.md`." | "The `my` plugin forces them on as its output style, so they load in every session where the plugin is on." |
  | "Details, the status line and the optional index: `global/rules/docs-layout.md` (symlinked to `~/.claude/rules/`)." | "Details, the status line and the optional index: the part "Where design documents live" below." |
  | "Steps 12 and 13 in `~/.claude/rules/docs-layout.md`" | "Steps 12 and 13 of "One feature, four commits on `main`" in the part "Where design documents live" below" |
  | "the core's Simplicity Rules" | "the Simplicity Rules in `~/.claude/rules/engineering.md`" |
  | "are in `~/.claude/rules/docs-layout.md`, section "One feature, four commits on `main`". That rule loads when a file in `docs/plans/` is read or written. Before any numbered step, read it if it has not loaded." | "are in the section "One feature, four commits on `main`" of the part "Where design documents live" below." |
  | "that names the method, the commit scopes" | "that names the commit scopes" |
  | "(step 2 in `docs-layout.md`)" | "(step 2 in the part "Where design documents live")" |
  | "the Engineering standards in `~/.claude/CLAUDE.md`" | "the Engineering standards in `~/.claude/rules/engineering.md`" |
  | "Mandatory Exploration (in the core)" | "Mandatory Exploration (in `~/.claude/rules/engineering.md`)" |
  | "the core's Reference Sweep" | "the Reference Sweep in `~/.claude/rules/engineering.md`" |
  | "lives in `global/rules/plan-format.md` (symlinked to `~/.claude/rules/`), which loads automatically when a `docs/plans/*.md` file is touched — edit it there." | "is the part "Plan Output Format" at the end of this style." |
  | "the route table in `~/.claude/methods/my.md` says" (from `docs-layout.md`) | "the route table in "Pick the route" above says" |

  If an old text is not found because row 62 or another row changed it, find the sentence by
  its meaning, apply the same change, and say so in the task's output.
- [ ] **Step 4: Check the move.** Build the expected file and compare. Expected: only the lines
  of the table above (old on `<`, new on `>`), the frontmatter, and the dropped `paths:`
  frontmatter and "Applies only…" lines.

  ```bash
  { git show main:global/methods/my.md; echo; git show main:global/rules/docs-layout.md; echo; git show main:global/rules/plan-format.md; } > "$SCRATCH/my-old.md"
  diff "$SCRATCH/my-old.md" plugins/my/output-styles/my.md
  ```

- [ ] **Step 5: Manifests.** `plugins/my/.claude-plugin/plugin.json`: add
  `"dependencies": ["superpowers@synced"]`; the description becomes "The my method: its rules as
  a forced output style, workflow skills, review agents, handoff scripts and hooks for the spec,
  plan, code and review cycle. Depends on superpowers. A folder turns it on with /kit:setup my."
  `marketplace.json`: the `my` entry gets `"category": "method"` and the same description.
- [ ] **Step 6: Pointers.** In each file, replace the old pointer with "the `my` style
  (`plugins/my/output-styles/my.md`)", keeping the section name the sentence cites:
  - `plugins/my/skills/status/SKILL.md`: "in `~/.claude/methods/my.md`".
  - `plugins/my/skills/handoff/README.md`: "The spec rules in `~/.claude/methods/my.md`".
  - `plugins/my/skills/clean-plans/SKILL.md`: "(`~/.claude/rules/docs-layout.md`)".
  - `plugins/my/skills/architect/SKILL.md`: "where the plan-format rule loads" becomes "where the
    `my` style's plan format applies".
  - `global/git-hooks/pre-commit`: "(see docs-layout.md, "Cite only commits on main")" and "Rule
    in ~/.claude/CLAUDE.md, Git Workflow".
  - `global/git-hooks/pre-push`: "Rules in ~/.claude/rules/docs-layout.md".
  - `plugins/my/README.md`: "Where the parts live" says the rules are the `my` style, which the
    plugin forces on, and that `/kit:setup my` writes the plugin keys and a `## Project facts`
    block (no import line). Every `global/rules/docs-layout.md`, `docs-layout.md` and
    `global/methods/my.md` pointer names the `my` style.
- [ ] **Step 7: Delete the three rule files** with `git rm`.
- [ ] **Step 8: Run the tests and see them pass.** Focused run, then the full runs.
- [ ] **Step 9: Headless check.** In a fixture folder `$SCRATCH/my-check` (`git init`, no
  settings), run:

  ```bash
  cd "$SCRATCH/my-check" && CLAUDE_METHOD_MARKETPLACE=<worktree> <worktree>/plugins/kit/bin/claude-method my \
    --plugin-dir <worktree>/plugins/my -p 'Does your system prompt contain the headings "Method: my" and "Where design documents live"? Answer YES or NO for each, nothing else.' \
    --output-format stream-json --verbose > my-check.jsonl
  ```

  Expected: the `system` `init` event's `plugins` list names `my` and `superpowers`; the result is
  `YES YES` (in any punctuation). The init event's `output_style` shows the setting, not the
  forced style (brief, spike 2), so it is not checked.
- [ ] **Step 10: Lint and commit.** Lint the `.md` files of this task. Then
  `git add` the new and modified files and
  `git commit -m "feat(my-plugin): the my rules become the plugin's forced style" --trailer "Task: 4"`.

### Task 5: the `tutor` plugin

**Files:**

- Create: `plugins/tutor/.claude-plugin/plugin.json`, `plugins/tutor/output-styles/tutor.md`
- Move: `git mv plugins/kit/skills/tutor plugins/tutor/skills/tutor`
- Modify: `plugins/tutor/skills/tutor/SKILL.md`, `plugins/tutor/skills/tutor/method.md`,
  `plugins/kit/hooks/hooks.json`, `plugins/kit/.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `plugins/kit/skills/design-router/plugins.json`
- Delete: `global/methods/tutor.md`, `global/output-styles/tutor.md` (both folders end empty)
- Test: `plugins/kit/tests/test_neutral_core.py`, `plugins/kit/tests/test_method_guard.py`,
  `plugins/kit/tests/test_design_router.py`

**Interfaces:**

- Consumes: `methods()` and `style()` (Task 4).
- Produces: `tutor:tutor`, the skill's new name; `/kit:setup tutor <path>`, which the skill
  calls (its new form is Task 8).

- [ ] **Step 1: Write the failing tests.**

  ```python
  # test_neutral_core.py
  def test_tutor_moved_out_of_kit(self):
      self.assertFalse((KIT / "skills" / "tutor").exists())
      for name in ["SKILL.md", "method.md", "templates.md"]:
          with self.subTest(name=name):
              self.assertTrue((REPO / "plugins/tutor/skills/tutor" / name).is_file())

  def test_tutor_style_and_skill_use_new_names(self):
      body = style("tutor")[1]
      skill = (REPO / "plugins/tutor/skills/tutor/SKILL.md").read_text()
      method = (REPO / "plugins/tutor/skills/tutor/method.md").read_text()
      for text in (body, skill, method):
          self.assertNotIn("kit:tutor", text)
      self.assertIn("tutor:tutor", body)
      self.assertNotIn("plain.md", body)
      self.assertNotIn("output style is not active", body)
      self.assertIn("Exceptions to the core and to `~/.claude/rules/engineering.md`: Verify "
                    "against ground truth, Mandatory Exploration, Reference Sweep and Simplicity "
                    "Rules do not apply in a learning workspace.", " ".join(body.split()))
      self.assertNotIn("outputStyle", skill)
      self.assertNotIn("~/.claude/methods", skill)
      self.assertIn("/kit:setup tutor", skill)

  def test_global_method_folders_are_gone(self):
      for rel in ["global/methods", "global/output-styles"]:
          with self.subTest(path=rel):
              self.assertFalse((REPO / rel).exists())

  # test_method_guard.py
  def test_hooks_json_has_no_tutor_hook(self):
      hooks = json.loads((SCRIPT.parent / "hooks.json").read_text())["hooks"]
      commands = [h["command"] for e in hooks["SessionStart"] for h in e["hooks"]]
      self.assertFalse([c for c in commands if "curriculum.md" in c])
  ```

  In `test_design_router.py`, `test_list_states_are_valid` loops over
  `("kit", "my", "superpowers", "hookify", "tutor")`.
- [ ] **Step 2: Run them and see them fail.** Focused runs of the three files.
- [ ] **Step 3: Write the plugin.** `plugin.json`: `name` `tutor`, description "The tutor
  method: a learning workspace where the student writes the code; its rules as a forced output
  style and the tutor:tutor skill.", the same `author` as `kit`; no `dependencies`.
  `marketplace.json`: a `tutor` entry with that description, `"source": "./plugins/tutor"`,
  `"category": "method"`. `plugins.json`: `"tutor": "not-design"`, keys kept in their order.
- [ ] **Step 4: Write the style** `plugins/tutor/output-styles/tutor.md`: frontmatter with
  `name: tutor`, the old style's description, `force-for-plugin: true`,
  `keep-coding-instructions: true`; then the body of `global/output-styles/tutor.md`, a blank line,
  `global/methods/tutor.md`. Then rule 8: step 2 ("Read `~/.claude/output-styles/plain.md` …")
  goes and steps 3 and 4 become 2 and 3; every `kit:tutor` becomes `tutor:tutor`; the bullet "If
  the `tutor` output style is not active …" goes; the line "Exceptions to the core in
  `~/.claude/CLAUDE.md`: … The rest of the core applies." becomes the spec's text: "Exceptions to
  the core and to `~/.claude/rules/engineering.md`: Verify against ground truth, Mandatory
  Exploration, Reference Sweep and Simplicity Rules do not apply in a learning workspace." Check
  with `diff` against the two old files, as in Task 4, Step 4.
- [ ] **Step 5: Move and edit the skill** (rule 9). `git mv plugins/kit/skills/tutor
  plugins/tutor/skills/tutor`, then in `SKILL.md`:
  - "`~/.claude/methods/tutor.md` lists the rules that stay in force" → "The `tutor` style lists
    the rules that stay in force".
  - Setup step 6: the bullet "`.claude/settings.local.json` gets `"outputStyle": "tutor"` …"
    goes. The ignore-entry bullets stay. A new last bullet: "Run `/kit:setup tutor <workspace
    path>`. It writes the method's keys into `.claude/settings.json` and commits them; the
    curriculum from step 3 is what it checks for." (The batch 1 review moved this call to the end
    of step 8; see Trade-Offs.)
  - Step 10, the hand-over: the method loads from the folder's settings, so
    `cd <workspace> && claude` is enough.
  - Session start, step 2 (the check for the style) goes; steps 3 and 4 become 2 and 3.
  - `method.md` line 4: "`kit:tutor` skill" → "`tutor:tutor` skill".
- [ ] **Step 6: The kit side.** `hooks.json`: delete the first `SessionStart` entry (the
  `curriculum.md` command); the guard entry and the `PreToolUse` entry stay. `kit`'s
  `plugin.json` and its `marketplace.json` entry: the description drops "the tutor for learning
  workspaces" and "the SessionStart hooks for the tutor and the method guard", and says "the
  method start check".
- [ ] **Step 7: Delete** `global/methods/tutor.md` and `global/output-styles/tutor.md` with
  `git rm`.
- [ ] **Step 8: Run the tests and see them pass.** Focused runs, then the full runs.
- [ ] **Step 9: Lint and commit.**
  `git commit -m "feat(global): the tutor method becomes the tutor plugin" --trailer "Task: 5"`.

### Task 6: the `sp` plugin, and the real method list

**Files:**

- Create: `plugins/sp/.claude-plugin/plugin.json`, `plugins/sp/output-styles/sp.md`
- Modify: `.claude-plugin/marketplace.json`, `plugins/kit/skills/design-router/plugins.json`
- Test: `plugins/kit/tests/test_neutral_core.py`, `plugins/kit/tests/test_claude_method.py`,
  `plugins/kit/tests/test_design_router.py`

**Interfaces:**

- Consumes: `claude-method` (Task 2), `methods()` (Task 4).

- [ ] **Step 1: Write the failing tests.**

  ```python
  # test_neutral_core.py
  def test_the_three_methods(self):
      self.assertEqual(set(methods()), {"my", "tutor", "sp"})

  # test_claude_method.py — against this repo, not the fake marketplace
  def test_real_marketplace(self):
      r = self.run_cm("--methods", env={"CLAUDE_METHOD_MARKETPLACE": str(REPO)})
      self.assertEqual(json.loads(r.stdout),
                       {"my@claude-setup": ["superpowers@synced"],
                        "sp@claude-setup": ["superpowers@synced"], "tutor@claude-setup": []})
  ```

  `test_list_states_are_valid` also checks `"sp"`.
- [ ] **Step 2: Run them and see them fail.**
- [ ] **Step 3: Write the plugin.** `plugin.json`: `name` `sp`, description "The sp method:
  the superpowers workflow as superpowers defines it, with no rules of its own.",
  `"dependencies": ["superpowers@synced"]`. `marketplace.json`: an `sp` entry with that
  description and `"category": "method"`. `plugins.json`: `"sp": "not-design"`. The style, with
  the frontmatter `name: sp`, `description: The sp method's rules`, and this body:

  ```markdown
  # Method: sp

  This session runs the `sp` method: the superpowers workflow. Superpowers' skills run as
  superpowers defines them. This method adds no rules of its own.
  ```

- [ ] **Step 4: Run the tests and see them pass.** Focused runs, then the full runs.
- [ ] **Step 5: The switch for real** (spec, Testing strategy). In a fixture folder whose
  `.claude/settings.json` turns `my@claude-setup` and `superpowers@synced` on:

  ```bash
  cd "$SCRATCH/sp-check" && CLAUDE_METHOD_MARKETPLACE=<worktree> <worktree>/plugins/kit/bin/claude-method sp \
    --plugin-dir <worktree>/plugins/sp -p 'Say OK.' --output-format stream-json --verbose > sp-check.jsonl
  ```

  Expected: the init event's `plugins` list names `sp` and `superpowers`, and not `my`.
- [ ] **Step 6: Lint and commit.**
  `git commit -m "feat(global): add the sp method plugin" --trailer "Task: 6"`.

### Task 7: the start check

**Files:**

- Modify: `plugins/kit/hooks/method-guard.py` (rewritten in place; the `hooks.json` entry stays)
- Test: `plugins/kit/tests/test_method_guard.py` (rewritten)

**Interfaces:**

- Consumes: `claude-method --methods` (Task 2): the script at
  `$CLAUDE_PLUGIN_ROOT/bin/claude-method`, or, when that variable is unset,
  `Path(__file__).resolve().parent.parent / "bin" / "claude-method"`. Run as
  `[sys.executable, <path>, "--methods"]` with a 5-second timeout.
- Produces, as before: nothing when all is well; else one JSON object
  `{"systemMessage": text, "hookSpecificOutput": {"hookEventName": "SessionStart",
  "additionalContext": text}}`, text cut to 2,000 chars; always exit 0.
- Exact lines, one per finding, joined by newlines:
  - `method guard could not read <path>` (unchanged)
  - `method guard: claude-method --methods failed: <reason>`, where `<reason>` is the script's
    last stderr line, else `exit <code>`, else the exception text. When this line is printed,
    nothing else is judged.
  - `method guard: more than one method is on: <keys, comma-separated, sorted>. Claude Code applies only the first style it loads. Keep one with /kit:setup <method>.`
  - `method guard: the <m> method is on, but its dependency <key> is off. Run /kit:setup <m>.`
    One line per missing key. `<m>` is the method key without `@claude-setup`.
  - `method guard: <CLAUDE.md or CLAUDE.local.md> still has the line @~/.claude/methods/<m>.md. Run /kit:setup <m>.`

- [ ] **Step 1: Write the failing tests.** Keep `write`, `make_world` and `run_guard`, minus the
  `.claude.json` flags. `make_world` also writes a fake marketplace (as in
  `test_claude_method.py`: `my` and `sp` depend on `superpowers@synced`, a fourth method `x`
  depends on `y@claude-setup`) and `HOME/.claude/plugins/known_marketplaces.json`. `run_guard`
  removes `CLAUDE_PLUGIN_ROOT` and `CLAUDE_METHOD_MARKETPLACE` from the environment. The tests:

  ```python
  def test_my_set_up_prints_nothing(self):          # my + superpowers on in the project
  def test_synced_key_missing_counts_on(self):      # my on, superpowers named nowhere → nothing
  def test_two_methods_on_names_both(self):
      # project: my on; local: sp on → text == two_methods(["my@claude-setup", "sp@claude-setup"])
  def test_missing_dependency_names_key(self):      # my on, superpowers false → dependency line
  def test_non_synced_dependency_missing_counts_off(self):  # x on, y named nowhere → dependency line
  def test_old_import_in_claude_md(self):           # "@~/.claude/methods/my.md\n" → import line
  def test_old_import_in_claude_local_md(self):
  def test_import_line_with_crlf_counts(self):
  def test_local_settings_override_project(self):   # project my true, local my false → nothing
  def test_string_true_is_not_on(self):             # "my@claude-setup": "true" → my not on
  def test_unreadable_user_settings(self):          # "{" → could-not-read line naming the file
  def test_settings_not_an_object_is_unreadable(self):
  def test_claude_method_failure_gives_one_warning(self):  # no known_marketplaces.json; also an
      # old import line present → exactly one line, starting "method guard: claude-method --methods failed:"
  def test_missing_script_gives_one_warning(self):  # CLAUDE_PLUGIN_ROOT=<empty folder>
  def test_root_falls_back_to_git_toplevel(self):
  def test_output_is_capped(self):                  # 40 import lines → ≤ 2,000 chars
  def test_exit_code_is_zero_in_every_case(self):
  def test_hooks_json_runs_the_guard_at_session_start(self):  # unchanged
  def test_hooks_json_has_no_tutor_hook(self):                # from Task 5
  ```

  Each asserts the exact line from the Interfaces block, built by a helper per line
  (`two_methods`, `dependency`, `old_import`), as today's `stray` and `missing` helpers do.
- [ ] **Step 2: Run them and see them fail.** Focused run. Expected: the new cases fail against
  the old guard.
- [ ] **Step 3: Rewrite `method-guard.py`.** Keep `project_root`, `read_json` and the `main`
  wrapper. `enabled_plugins` drops `DEFAULTS`: a key no file names counts as on when it ends in
  `@synced`, off otherwise. The import scan keeps its regex and returns `(file name, method)`
  pairs. The approval code and the `$HOME/.claude.json` read go. The docstring states the new
  inputs and the three warnings.
- [ ] **Step 4: Run the tests and see them pass.** Focused run, then the full runs.
- [ ] **Step 5: Commit.**
  `git commit -m "feat(kit-plugin): the method start check reads methods from claude-method" --trailer "Task: 7"`.

### Task 8: `/kit:setup`

**Files:**

- Modify: `plugins/kit/skills/setup/SKILL.md` (rewritten)

**Interfaces:**

- Consumes: `claude-method` (no argument, `--json <m>`, `--methods`).
- Produces: `/kit:setup <method|none> [<project path>]`, which Task 5's tutor skill calls.

- [ ] **Step 1: Write the failing check.** A headless script, `$SCRATCH/setup-check.sh`, builds
  two fixture repos and runs the skill from the branch (`--plugin-dir <worktree>/plugins/kit`,
  `--settings '{"enabledPlugins":{"kit@claude-setup":false}}'`,
  `CLAUDE_METHOD_MARKETPLACE=<worktree>`, `--permission-mode acceptEdits`, `--add-dir` for the
  fixture and for `<worktree>/plugins/kit`, and
  `--allowedTools 'Bash(claude-method:*),Bash(git:*),Read,Edit,Write'` as one comma-separated
  argument placed after the prompt, so the flag cannot take the prompt as a tool name). The
  skill asks before it writes, and `-p` has no `AskUserQuestion`, so each case is two calls:
  `claude -p '/kit:setup <m> <fixture>' <flags>`, then
  `claude -p --continue 'Yes, write and commit it.' <flags>` in the same folder. Then it checks
  the files with `python3 -c` and `git`:
  - **Case A**, `/kit:setup sp <fixture A>`: the fixture has a `CLAUDE.md` with a facts block,
    `- **Method:** my` and `@~/.claude/methods/my.md`; `.claude/settings.json` with
    `{"enabledPlugins": {"my@claude-setup": true, "superpowers@synced": true, "other@m": true}}`;
    an ignored `.claude/settings.local.json` with
    `{"enabledPlugins": {"my@claude-setup": true}, "outputStyle": "tutor", "permissions": {}}`.
    Expected: `enabledPlugins` in `settings.json` is exactly
    `{"other@m": true, "sp@claude-setup": true, "superpowers@synced": true}`; the local file is
    exactly `{"permissions": {}}`; `CLAUDE.md` has neither line; `git show --stat --format= HEAD`
    lists only `.claude/settings.json` and `CLAUDE.md`; the subject is
    `chore: switch to the sp method`.
  - **Case B**, `/kit:setup my <fixture B>`: an empty repo with one commit. Expected:
    `settings.json` is `{"enabledPlugins": {"my@claude-setup": true, "superpowers@synced": true}}`;
    `CLAUDE.md` has a `## Project facts` block with no `**Method:**` line and no import line.
  Run it before Step 2. Expected: both cases fail against the old skill (it writes the import
  line and does not know `sp`).
- [ ] **Step 2: Rewrite `SKILL.md`** (spec, `/kit:setup`). Its parts, in order:
  1. Frontmatter: the description says it sets a folder's method in its `.claude/settings.json`
     and takes `<method|none> [<project path>]`; it also triggers on the start check's
     "Run /kit:setup <m>".
  2. What it writes: the method's keys, from `claude-method --json <m>` (keys with `true`) and
     `claude-method --methods` (every method and dependency key). Nobody edits them by hand.
  3. Arguments: `<m>` is a name that `claude-method` lists, or `none`; otherwise print
     `Usage: /kit:setup <method|none> [<project path>]` and the list, and stop. The path rule as
     today.
  4. For `my`: today's steps 1 and 2 (facts, copied rules). Step 2 reads the `my` style at
     `<marketplace folder>/plugins/my/output-styles/my.md`. The marketplace folder is the one
     `claude-method` reads: `$CLAUDE_METHOD_MARKETPLACE` when set, else `installLocation` of
     entry `claude-setup` in `~/.claude/plugins/known_marketplaces.json`. So the branch check
     reads the branch's style, which the main checkout does not have before the merge. The facts block has no
     `**Method:**` line and no import line after it.
  5. For `tutor`: today's check that `docs/learning/curriculum.md` exists, and the "Learning
     workspaces" copy check. No facts block.
  6. Every method and `none`: the uncommitted-edits check as today, for `CLAUDE.md`,
     `CLAUDE.local.md` and `.claude/settings.json`; the "already set up" check; then one diff
     with the spec's five changes: on keys `true` in `settings.json`; other methods' and their
     dependencies' keys removed there, except the chosen method's own; every method and
     dependency key, and an `outputStyle` of `plain` or `tutor`, removed from
     `settings.local.json`; the import line removed from `CLAUDE.md` and `CLAUDE.local.md`; the
     `**Method:**` line removed from "Project facts". An `enabledPlugins` left empty is removed;
     the file stays.
  7. Commit as today's step 4, with `chore: switch to the <m> method` (`chore: switch to no
     method` for `none`), staging only tracked files it changed. `settings.local.json` is never
     committed. A `CLAUDE.local.md` that git does not track is edited in place and not committed;
     when it is a symlink, name its target.
  8. Tell the user: the method loads in the next session in that folder, or after
     `/reload-plugins` in a running one. The import-approval text goes.
- [ ] **Step 3: Run the check and see it pass.** Both cases match. Count
  `"subtype":"permission_denied"` in each stream: expected 0 (a denied read makes the model
  improvise, so a pass with a denial is no pass).
- [ ] **Step 4: Run the full test runs** (`test_skill_placeholders.py` reads this file).
- [ ] **Step 5: Lint and commit.**
  `git commit -m "feat(kit-plugin): kit:setup writes a method's plugin keys, with no import line" --trailer "Task: 8"`.

### Task 9: this repo and zitamu move; the final sweep

**Files:**

- Modify: `CLAUDE.md`, `projects/real-estate-webapp/claude-local.md`, `README.md`
- Test: `plugins/kit/tests/test_neutral_core.py`

- [ ] **Step 1: Write the failing test.**

  ```python
  OLD_PATHS = (r"methods/(my|tutor)\.md|global/methods|docs-layout|plan-format"
               r"|global/output-styles|\.claude/output-styles|kit:tutor")

  def test_no_file_names_a_moved_path(self):
      r = subprocess.run(["git", "-C", str(REPO), "grep", "-n", "-E", OLD_PATHS, "--", ".",
                          ":!docs/plans", ":!docs/reports", ":!CHANGELOG.md", ":!ROADMAP.md",
                          ":!plugins/kit/tests", ":!plugins/kit/hooks/method-guard.py"],
                         capture_output=True, text=True)
      self.assertEqual(r.stdout, "")
  ```

  The guard is excluded because it detects the old line; `ROADMAP.md` because its rows change
  at the batch marks. `git grep` reads the index, so `git add` new files before the run.
- [ ] **Step 2: Run it and see it fail.** Expected hits: `CLAUDE.md`, `claude-local.md`,
  `README.md`.
- [ ] **Step 3: Edit `CLAUDE.md`.** The import line and `- **Method:** my` go. The first line
  says the repo is a marketplace of method plugins (`my`, `tutor`, `sp`) and neutral tools
  (`kit`, `vue-lsp`). "Architecture": `my`, `tutor` and `sp` are methods, `kit` holds the
  neutral tools; the folder list gains `output-styles/` (a method's forced style) and the
  manifest bullet names `dependencies` (a method's plugin set). Commit scopes gain
  `tutor-plugin` and `sp-plugin`.
- [ ] **Step 4: Edit `projects/real-estate-webapp/claude-local.md`.** The import line and
  `- **Method:** my` go; "kept by the rules in `docs-layout.md`" becomes "kept by the rules in
  the `my` style". First run `git diff HEAD -- projects/real-estate-webapp/claude-local.md` in
  the main checkout: zitamu sessions edit it through its symlink (Risk).
- [ ] **Step 5: Edit `README.md`.** The `global/` bullet: `CLAUDE.md` (the core), `rules/`
  (path-scoped rules, among them `engineering.md`) and `git-hooks/`; only `~/.claude/CLAUDE.md`
  and `~/.claude/rules` are symlinks; no `methods/` or `output-styles/`. The `plugins/` bullet
  lists `tutor` and `sp`. The methods section: a method is a plugin with `"category": "method"`
  whose forced style holds its rules and whose `dependencies` hold its plugins; a folder's
  `.claude/settings.json` names it; `/kit:setup <m>` writes the keys; the start check warns on
  two methods, a missing dependency, or an old import line. The `kit:tutor` entry becomes a
  `tutor:tutor` entry under a `tutor` heading. "`global/rules/docs-layout.md`" names the `my`
  style. "Hooks": the tutor hook goes; the guard entry describes the three warnings.
- [ ] **Step 6: Run the tests and see them pass.** Focused run, then the full runs.
- [ ] **Step 7: Lint and commit.**
  `git commit -m "docs(global): this repo and zitamu run my from the plugin" --trailer "Task: 9"`.

Batch 1 ends here. The code stage launches the review stage. Before the squash-merge, the
review stage checks that `git status --porcelain -- ROADMAP.md CHANGELOG.md
projects/real-estate-webapp/claude-local.md` prints nothing in the main checkout. If it prints
anything, it signals and asks the user to commit those edits; it never stashes them.

## Rollout after batch 1

By hand, after the batch 1 marks, in this order (spec, Batches and rollout). The session that
runs it writes step 1's result into this section and commits that edit on `main` at once, as its
own `docs(plans):` commit: batch 2's code stage needs this plan committed and clean, and its
worktree sees only committed text.

1. In a fixture folder whose `.claude/settings.json` turns `tutor@claude-setup` on, run
   `claude -p 'Say OK.' --output-format stream-json --verbose` and check the init event's
   `plugins` list names `tutor`. The same for `sp@claude-setup` with `superpowers@synced`. If
   one is missing, `claude plugin install <p>@claude-setup`, then check that
   `~/.claude/settings.json` still has it off.
2. Edit `~/.claude/settings.json`: remove `"outputStyle": "plain"`; set every plugin key outside
   D5's list to `false`. D5's list: `kit@claude-setup`, `vue-lsp@claude-setup`,
   `php-lsp@claude-plugins-official`, `pyright-lsp@claude-plugins-official`,
   `claude-md-management@claude-plugins-official`, `claude-code-setup@claude-plugins-official`,
   `hookify@claude-plugins-official`. List the installed plugins with `claude plugin list`, so
   the `@synced` ones (on when unnamed) and the design plugins get a `false` key too (D14).
3. `rm ~/.claude/methods ~/.claude/output-styles` (two symlinks). `~/.claude/rules` stays.
4. Restart running sessions.
5. In `~/projects/mv3-tab-notes`: `~/projects/claude-setup/plugins/kit/bin/claude-method tutor`
   (the `~/bin` symlink comes in Task 10), then `/kit:setup tutor`. Its curriculum
   uses `modern-web-guidance`, which step 2 turned off: turn it on there by name when a lesson
   needs it.

Result of step 1: (written after the run).

### Task 10: start conditions (batch 2)

No code and no commit.

- [ ] **Step 1: Check the blockers.** `grep -nE '^- ✅ (33|37|56) ' ROADMAP.md` prints three
  lines, and this plan's status says "Batch 1 merged". If not, signal
  `code-method-bundles: batch 2 waits for rows 33, 37 and 56 (spec, Dependencies)` and stop.
- [ ] **Step 2: Check the rollout.** `~/.claude/methods` does not exist, and the "Result of step
  1" line above is filled in. If not, signal and ask the user to finish the rollout.
- [ ] **Step 3: The symlink** (spec, manual step). Ask the user to run
  `ln -s ~/projects/claude-setup/plugins/kit/bin/claude-method ~/bin/claude-method`, then check
  `command -v claude-method` prints `/home/dchris/bin/claude-method`.

### Task 11: `/kit:method`

**Files:**

- Create: `plugins/kit/skills/method/SKILL.md`

**Interfaces:**

- Consumes: `claude-method --json <m>` and `--methods`; `claude plugin enable|disable <key>
  --scope local`.
- Produces: `/kit:method <m>` and `/kit:method default`.

- [ ] **Step 1: Write the failing check.** `$SCRATCH/method-check.sh` builds a fixture repo with
  `.claude/settings.json` turning `my` on, and `.claude/settings.local.json` holding
  `{"enabledPlugins": {"my@claude-setup": true, "superpowers@synced": true}, "permissions": {}}`.
  It runs, from the fixture, with the branch's kit (`--plugin-dir`, `kit@claude-setup` off) and
  `--allowedTools 'Bash(claude-method:*),Bash(claude plugin:*),Read,Edit'` as one
  comma-separated argument placed after the prompt:
  - `claude -p '/kit:method sp'`. Expected local `enabledPlugins`: `sp@claude-setup` true,
    `superpowers@synced` true, `my@claude-setup` false, `tutor@claude-setup` false;
    `permissions` kept; the result asks the user to submit `/reload-plugins`.
  - `claude -p '/kit:method default'`. Expected: the local file is exactly
    `{"permissions": {}}`.
  Expected before Step 2: both fail (`Unknown skill`).
- [ ] **Step 2: Write `SKILL.md`.** Frontmatter: `name: method`, a description that says it
  switches the folder's method during a session and that only the user starts it,
  `disable-model-invocation: true`. Steps (spec, `/kit:method <m>`):
  1. `<m>` is a name `claude-method` lists, `none`, or `default`; otherwise print
     `Usage: /kit:method <method|none|default>` and the list, and stop.
  2. For a method or `none`: run `claude-method --json <m>`, then one
     `claude plugin enable <key> --scope local` per `true` key and one
     `claude plugin disable <key> --scope local` per `false` key. Show each command's result. On
     the first failure, stop and say which keys changed.
  3. For `default`: read `claude-method --methods`; remove each method and dependency key from
     `enabledPlugins` in `.claude/settings.local.json` with the Edit tool (no `claude plugin`
     command removes a key); remove an `enabledPlugins` left empty; keep every other key.
  4. End by asking the user to submit `/reload-plugins`, which Claude cannot submit.
- [ ] **Step 3: Run the check and see it pass,** with no `permission_denied` events.
- [ ] **Step 4: Run the full test runs** (`test_kit_cites_no_method`,
  `test_skill_placeholders.py`).
- [ ] **Step 5: Lint and commit.**
  `git commit -m "feat(kit-plugin): add /kit:method, the switch during a session" --trailer "Task: 11"`.

### Task 12: `my:handoff` launches through `claude-method`

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md` (the four launch lines), `README.md`

- [ ] **Step 1: The failing check.** `grep -c "claude -n <name>" plugins/my/skills/handoff/SKILL.md`
  prints `4`, and `grep -c "claude-method my -n <name>"` prints `0`.
- [ ] **Step 2: Edit the four lines** (spec, `my:handoff`): in the two fallback commands and the
  two `tmux new-window` commands, `claude -n <name> <plugin-dir flags> …` becomes
  `claude-method my -n <name> <plugin-dir flags> …`; `MY_AUTORUN=<slug>` stays in front. Add one
  sentence after step 3's plugin-dir bullet: "`claude-method my` starts the stage in the `my`
  method in any folder, and turns `my@claude-setup` off when a copied `--plugin-dir` is `my`'s."
- [ ] **Step 3: The check passes.** The two counts are now `0` and `4`.
- [ ] **Step 4: Rehearse in tmux.** `tmux new-window -d -n cm-check "claude-method my --version >
  $SCRATCH/cm-version.txt 2>&1"`, then read the file: it holds the Claude Code version. This
  proves a tmux window finds `claude-method` and that it reaches `claude`.
- [ ] **Step 5: `README.md`.** The methods section names `claude-method <m> [claude args]` (one
  session) and `/kit:method <m>` (the folder, after `/reload-plugins`), and the symlink
  `~/bin/claude-method`, next to the one for `git-fold-fixups.py`.
- [ ] **Step 6: Run the full test runs.**
- [ ] **Step 7: Lint and commit.**
  `git commit -m "feat(my-plugin): my:handoff starts each stage with claude-method my" --trailer "Task: 12"`.

## Trade-Offs / Alternatives Considered

- **`CLAUDE_METHOD_MARKETPLACE`, a variable `claude-method` reads before
  `known_marketplaces.json`.** The spec names only the registry. Without the variable, a run on
  the branch reads the main checkout's marketplace, which has no `tutor`, `sp` or `dependencies`
  until the merge, so Tasks 4, 6 and 8 could not test the branch. Option: test only after the
  merge. Rejected: a failure would then show on `main`, in every session. The variable changes no
  key and no contract, and no real session sets it.
- **The ROADMAP edits wait for the batch 1 marks** instead of riding on the branch. The spec
  lists `ROADMAP.md` in batch 1; it stays in batch 1's commits on `main`. Option: edit on the
  branch. Rejected: other sessions edit the roadmap daily, so the squash would conflict.
- **The my style keeps three `#` parts** (`Method: my`, `Where design documents live`, `Plan
  Output Format`). Option: demote the two lower files' headings. Rejected: rule 1 allows only the
  changes the spec names, and pointers name the parts by heading.
- **`plain`'s three `##` headings become `###` in the core,** so they sit under Communication.
  The text does not change. Option: keep `##`. Rejected: "Challenge assumptions" and the later
  sections would then read as part of "What this does not change".
- **The tutor skill calls `/kit:setup tutor` at the end of setup step 8,** not as a new numbered
  step. A new number would shift steps 7 to 10, which the skill's own text and `templates.md`
  ("setup step 6") cite. Task 5 placed it in step 6; the batch 1 review moved it after step 8's
  commit, because `/kit:setup` stops on step 4's uncommitted `CLAUDE.md` edit.
- **Tests for the styles and plugins live in `plugins/kit/tests/test_neutral_core.py`.** Option: a
  new test file. Rejected: that file already holds the method-file and "Applies only" tests that
  these replace.
- **Execution: `superpowers:executing-plans`,** not subagent-driven: the tasks share names, the
  moves are checked by diffs that need the whole context, and the headless checks are serial.

## Dependencies

- **Row 62 merges before batch 1** (it edits `plain.md`). It is 💭 on 2026-10-21. Task 1 stops
  the code stage until it is ✅.
- **Rows 33, 37 and 56 merge before batch 2** (they fix the launch lines Task 12 edits). All 💭
  on 2026-10-21. Task 10 stops batch 2 until they are ✅.
- **Row 70 has merged** (`5dfd634`); its text is what batch 1 moves.
- **Rows 69 and 71 come after** (D18).
- Claude Code 2.1.304 or later; 2.1.306 is installed.
- No new packages.

## Risk

- **Blast radius, from the sweep:** every session reads the new core. The ten `my` repos get the
  `my` style at the merge, because the plugin loads in place. Nine of them keep a dead import line
  until opened; Claude Code skips a missing import (spec). `mv3-tab-notes` loses its tutor hook
  and style at the merge, until rollout step 5.
- **Hard to reverse:** the import lines leave `claude-setup` and zitamu in batch 1. Going back
  means restoring `global/methods/` and `global/output-styles/` from git, the two symlinks, and
  the old `/kit:setup` in each moved repo.
- **A Bash redirect that creates a code file does not load `engineering.md`** (probe, Context).
  `Write`, `Read` and a Bash `cat` do. A session that only creates files through redirects in an
  empty repo works without the engineering rules. Known limit: the spec asked to stop here, and
  the user kept D2 with this limit (2026-10-21).
- **Two forced styles win silently.** Start check 1 sees it in files, and `claude-method`'s
  `--plugin-dir` rule in flags. A `--plugin-dir` that names a method other than the chosen one
  still loads that method's inline copy beside the chosen one. Known limit; nobody launches that
  today. Likewise `claude-method none --plugin-dir plugins/my` loads `my` with
  `superpowers@synced` off, because the `--plugin-dir` rule turns off a key and turns on no
  dependency (batch 1 review).
- **The start check judges the folder's files, not `claude-method`'s flags** (spec, The start
  check). Under `claude-method tutor` in a `my` folder it stays silent; in a folder whose files
  turn on two methods, it warns even when `claude-method my` fixed the session (batch 1 review).
- **`engineering.md` loads when a matching file is read, not at session start** (D2). A planning
  or brainstorming turn that proposes changes before any code file or `docs/plans/*.md` is read
  runs without the engineering rules until that first read (batch 1 review). Only a change to D2
  would remove this.
- **`/kit:setup` removes off keys instead of writing `false`** (D10). A removed `@synced`
  dependency falls back to the user scope, where an unnamed `@synced` key counts as on. Safe
  while `~/.claude/settings.json` names `superpowers@synced: false`, as it does today and as
  rollout step 2 keeps it (batch 1 review).
- **Between the merge and rollout steps 2 and 3,** `"outputStyle": "plain"` in
  `~/.claude/settings.json` and the symlinks `~/.claude/methods` and `~/.claude/output-styles`
  point at files the merge deletes. `plain`'s text is in the core by then. Run the rollout right
  after the batch 1 marks (batch 1 review).
- **`claude-method` and `/kit:setup` step 3 read `~/.claude/plugins/known_marketplaces.json`**, a
  Claude Code internal file, as the spec says. The memory "kit stays harness-neutral" (2026-10-22,
  after the spec) records the user turning down that same file in another `kit` tool
  (batch 1 re-review). The user chose to merge batch 1 as it is and to add a roadmap row that
  drops the read, for example by finding the marketplace from the script's own path
  (2026-10-22).
- **Known limits from the batch 1 re-review**, none of them reached by today's marketplace or
  repos unless named:
  - `claude-method` reads a `dependencies` string one letter at a time, and crashes with a
    Python traceback on a method entry with no `source` or an object `source`.
  - `claude-method --settings '{}' my` exits 1 ("no method named --settings"), not 2; only a
    `--settings` after the method name gets exit 2. `claude-method --json` with no name prints
    "no method named None".
  - The start check says "Run /kit:setup `<name>`" for any old import line, also when `<name>`
    is not a method; `/kit:setup` then refuses that name.
  - The start check runs `claude-method --methods` as a second process at every session start,
    with a 5 s timeout; a slow start shows as its one warning.
  - `/kit:setup my` looks for `## Project facts` only in `CLAUDE.md`. zitamu keeps its block in
    `CLAUDE.local.md`, so `/kit:setup my` there would add a second block. zitamu is already
    set up, so nothing runs it today.
  - A tutor case 3 workspace copied from a `my` project: `/kit:setup tutor` proposes removing
    the `my` facts block, which holds the `learning` scope that setup step 4 just added. The
    user decides; a yes drops that scope line.
- **Dirty shared files block the merge.** `projects/real-estate-webapp/claude-local.md` (zitamu
  sessions edit it through its symlink), `ROADMAP.md` and `CHANGELOG.md` often hold other
  sessions' edits. `git merge --squash` refuses when a file it changes is dirty. The review stage
  checks them before the merge and asks the user; it never stashes them.
- **The off set turns off a plugin the user enabled on purpose** when it is another method's
  dependency (spec).
- **The strict bare scope turns off the design plugins** after rollout step 2 (D14):
  `kit:design-router` stops and names the plugin that is off.
- **The start check depends on `claude-method`.** If the script fails, it warns once and judges
  nothing.
- **The headless checks use `claude -p --continue`** for the skills' question step. If a run
  answers differently, read the stream before changing the skill.
- **Manual steps:** the rollout, and the `~/bin/claude-method` symlink (Task 10).

## Testing Strategy

- **Unit and end-to-end, run by the test command:** `test_claude_method.py` (the script's whole
  command line, including the real `exec` through a fake `claude`), `test_method_guard.py` (the
  hook as Claude Code runs it, with the real `claude-method` under it), `test_neutral_core.py`
  (the core, `engineering.md`, the styles, the manifests and the final sweep),
  `test_design_router.py` (the two new list entries).
- **Headless, on the branch:** the `my` style loads with `superpowers` (Task 4); `claude-method
  sp` turns `my` off (Task 6); `/kit:setup` writes and removes the right keys (Task 8);
  `/kit:method` and `/kit:method default` (Task 11). Each counts `permission_denied` events.
- **Move checks:** `diff` of each new style and of the core against the files on `main` (Tasks 3,
  4, 5).
- **By hand:** rollout step 1; the tmux rehearsal of `claude-method` (Task 12).

## Open Questions

None.
