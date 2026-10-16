# `my:design-system` Implementation Plan

**Status:** done, 2026-10-16. Merged in `eae9264`. End-of-branch checks: 2 run, 2 passed (kit 40 tests, my 230 tests; my has 233 after the fix round). Not rehearsed, by the user's choice: the zitamu regression and `sync` (Risk 11).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. The tasks build on each other: the
> skill calls `ds-count.py`, the method and the review prompt name the skill,
> and the rehearsals in Tasks 6 and 7 need all of them. The global review
> rules replace that skill's own reviews: run no per-task reviewer and no
> final `requesting-code-review` pass. The `my:handoff` review stage runs the
> end-of-branch reviews. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every project with UI keeps `docs/DESIGN-SYSTEM.md`, an inventory of
its shared components and hand-built patterns. A `my:design-system` skill
builds it (`audit`), keeps it current at step 13 (`refresh`) and makes the
Design System artifact that canvases draw from (`sync`). Specs read it, and
`my:spec-review` checks specs against it.

**Architecture:** One script, `plugins/my/bin/ds-count.py`, counts the search
patterns stored in the inventory's `ds-patterns` block (D4, D12). One skill,
`plugins/my/skills/design-system/SKILL.md`, holds the three modes and the
inventory template. The rest is prompt text: the method (`global/methods/my.md`),
step 13 (`global/rules/docs-layout.md`), the shared-doc list of `my:handoff`,
and criterion 6 of the spec reviewer.

**Tech Stack:** Python 3.12.3 standard library (`json`, `re`, `subprocess`,
`tempfile`, `unittest`), git 2.43.0, Claude Code 2.1.301 (`claude -p` for the
rehearsals), `markdownlint-cli2`.

**Spec:** `docs/plans/2026-10-16-design-system-skill-spec.md`

**Commit type:** `feat`. Branch `feat/design-system-skill`, worktree
`.claude/worktrees/design-system-skill`. The `my:handoff` code stage creates
both.

## Global Constraints

- Conventional Commits with a scope: `my-plugin` for files under
  `plugins/my/`, `kit-plugin` for files under `plugins/kit/`, `global` for
  files under `global/`, none for a commit that touches `README.md` or more
  than one of those folders. Every message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Every task commit
  carries the trailer `Task: <N>`, with `<N>` the task's number below
  (`git commit --trailer "Task: <N>"`).
- Tests: `cd plugins/my && python3 -m unittest discover tests` (203 pass on
  `main` on 2026-10-16) and `cd plugins/kit && python3 -m unittest discover tests`
  (40 pass). Every code commit runs both, and all must pass.
- End-of-branch checks: the two test commands above (the spec's Delegation
  section), the lint counts below, and the rehearsal records of Tasks 6 and 7.
- No new dependencies (spec, Dependencies). Python standard library only.
- Read `git diff --cached` before every commit. This repo has no "Parallel
  runs" section, so the locked form does not apply.
- Markdown lint: count errors with
  `markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc <file> 2>&1 | grep -c ' error '`.
  On `main` on 2026-10-16 the count is 1 for `global/methods/my.md` and 0 for
  every other file this plan edits. No count may rise. New files must count 0.
- Keep each file's line style. In `global/methods/my.md` the task-class table
  rows and step 1 of "Spec → Plan two-artifact flow" are single long lines,
  and "UI Design" wraps at 80 characters. `docs-layout.md` wraps at 100.
  The handoff files and `README.md` wrap at 80. The bullets of
  `spec-reviewer-prompt.md` are single long lines.
- Edit the files under `global/`, never the links in `~/.claude/` that point
  to them. Those links point into the main checkout, so a session reads the
  branch's `global/` files only when its prompt names their worktree path.
- Never edit a file in `~/projects/zitamu/`. The zitamu regression runs on a
  clone in the scratchpad (spec, Out of scope).
- Nothing is published to claude.ai without the user's yes (D10). Only Task 7
  publishes, and it stops for the user first.
- Fixed copy, word for word, from the spec: the inventory's three Sources
  lines (spec, "The inventory", part 1), the `ds-count.py` output line
  `<name>  <kind>  <old count>/<old files> -> <new count>/<new files>` (two
  spaces between fields), and the text of the edits in Tasks 3 to 5 where
  those tasks quote it.

## Decisions this plan adds

The spec leaves these open. None changes a contract the spec fixes.

1. **The block's edges.** The block opens on a line that is exactly
   `` ```ds-patterns `` (trailing spaces ignored) and closes on the next line
   that is exactly `` ``` ``. A second opening line, or no closing line, is
   refused like a missing block: exit 1, nothing written. Blank lines inside
   the block are allowed, skipped when counting, and kept as they are.
2. **The no-match refusal is checked before the excludes.** The script first
   runs `git ls-files -z -- ':(glob)<glob>' …` without the excludes. When that
   prints nothing, the globs are a typo: exit 1. Then it runs the call with
   the excludes. When the excludes leave no file, the pattern prints `0/0`,
   because a pattern can reach zero that way (the spec's `exclude` row).
   `git ls-files` exits 0 when nothing matches, so the test is on its output,
   not its exit code.
3. **A line with no counts yet** prints `new` in place of
   `<old count>/<old files>`: `text field  hand-built  new -> 39/14`.
4. **Writing a line.** `json.dumps(obj, ensure_ascii=False)` with the default
   separators, so a line keeps the spec's `{"name": "…", "kind": …}` form.
   Keys keep their order. A line that gains `count` and `files` gets them at
   the end, in that order. Keys the script does not know are kept.
5. **Line endings** are kept: the file is read and written with
   `newline=""`, and each rewritten line keeps its own ending.
6. **Paths.** An inventory argument is relative to the current folder. Git
   always runs from the repo root (`git rev-parse --show-toplevel`, run from
   the current folder), so globs are relative to the root wherever the script
   runs. Outside a git repo the script exits 1 with one message.
7. **A regex that matches the empty string** is refused: exit 1, with the
   line number. The check runs while counting: any match with
   `m.start() == m.end()` refuses the pattern. A check on `""` alone is not
   enough, because `re.search(r"\b", "")` is `None` while `\b` matches at
   every word edge of a real file. Such a regex, like `\b` or `x*`, counts
   positions, not elements, so its count means nothing. The refusal comes
   before any write (Decision 9).
8. **A listed file that is gone from the working tree** (deleted, not yet
   staged) is skipped. It is not an error, because the count is a trend
   (spec, Risk 3).
9. **Validation before counting.** Every line is checked first. The script
   counts only when all lines pass, and writes only when it has counted every
   line. The write goes to a temporary file in the same folder, then
   `os.replace`, keeping the file's mode.
10. **Value checks.** `name` is a non-empty string; `kind` is `component` or
    `hand-built`; `globs` is a non-empty list of strings; `exclude`, when
    present, is a list of strings; `regex` is a string; `count` and `files`,
    when present, are integers. Any other value is "of the wrong type".
11. **The inventory template's headings** are fixed, so `audit`, `refresh` and
    the spec reviewer find the parts: `# Design system`, then `## Sources`,
    `## Components`, `## Hand-built patterns`, `## Counts`. The `ds-patterns`
    block sits under `## Counts`.
12. **The skill's arguments:** `audit`, `refresh [<spec path>] [auto]`,
    `sync`. Anything else prints
    `Usage: /my:design-system audit | refresh [<spec path>] [auto] | sync`
    and stops.
13. **The new name joins the kit guard.** `design-system` joins `MY_NAMES` in
    `plugins/kit/tests/test_neutral_core.py`, so a kit file that cites
    `my:design-system` fails a test. Kit cites neither name today (checked
    with `grep -rn "design-system\|ds-count" plugins/kit`), so the test passes
    at once: it is a guard, not a red test.

## Review Focus

1. **A regex that matches the empty string.** A user writes `\b`, or
   `(<input)?` with a stray `?`. Expected: refused with the line number, not
   a count in the thousands. Test: `test_empty_match_regex_refused` (Task 1).
2. **A block left open, or pasted twice.** Expected: exit 1 with a message,
   the file unchanged. Tests: `test_unclosed_block_refused`,
   `test_two_blocks_refused` (Task 1).
3. **Blank lines in the block.** A user separates components from hand-built
   lines with an empty line. Expected: counted as usual, the blank line kept.
   Test: `test_blank_lines_kept` (Task 1).
4. **CRLF line endings** in an inventory edited on Windows. Expected: `--write`
   keeps every `\r\n`. Test: `test_write_keeps_crlf` (Task 1).
5. **Run from a subfolder** with a relative inventory path, as a user in
   `web/` would. Expected: the same counts as from the root. Test:
   `test_run_from_subfolder` (Task 1).

## File map

| File | Task | Change |
| --- | --- | --- |
| `plugins/my/tests/test_ds_count.py` | 1 | New: the script's tests |
| `plugins/my/bin/ds-count.py` | 1 | New, executable |
| `plugins/my/skills/design-system/SKILL.md` | 2 | New: three modes, checklist, inventory template |
| `plugins/kit/tests/test_neutral_core.py` | 2 | `design-system` joins `MY_NAMES` |
| `global/methods/my.md` | 3 | Task-class row, step 1 sentence, UI Design bullet, paragraph and sentence |
| `global/rules/docs-layout.md` | 3 | Step 13 |
| `plugins/my/skills/handoff/SKILL.md` | 4 | Shared-doc list: stop row 19 (line 250), Plan stage step 6 (lines 719–720) |
| `plugins/my/skills/handoff/README.md` | 4 | "Shared docs" bullet (line 378) |
| `plugins/my/skills/spec-review/spec-reviewer-prompt.md` | 4 | Criterion 6, one bullet after line 69 |
| `README.md` | 5 | Skill entry after `my:status`; script sentence after `status-scan.py`'s |
| `docs/plans/2026-10-16-design-system-skill.md` | 6, 7 | Rehearsal records in Testing Strategy |

`ROADMAP.md` and `CHANGELOG.md` change at the `done` marks, in the review
stage, not in a task.

Reference sweep: the change removes and renames nothing. The shared-doc list
appears in exactly the three places above. This search, run on 2026-10-16,
prints those three lines and no other:

```bash
grep -rn 'CHANGELOG.md` or the plans\|`CHANGELOG.md`, the plans index\|CHANGELOG.md` are shared' plugins global
```

The handoff mentions at lines 1012 and 1091 point back to step 6 and need no
edit. `DOCS_PATHS` in `handoff-state.py` already covers `docs/`, so
`docs/DESIGN-SYSTEM.md` is a docs path there with no change.

---

### Task 1: `ds-count.py`, tests first

**Files:**

- Create: `plugins/my/tests/test_ds_count.py`
- Create: `plugins/my/bin/ds-count.py` (mode 755)

**Interfaces:**

- Produces: the command `ds-count.py [--write] [<inventory>]`, on `PATH`
  through the plugin's `bin/`. Exit 0 on success, 1 on any refusal with one
  stderr line. stdout: one line per pattern, in block order. Task 2's skill
  calls it.

- [ ] **Step 1: Write the failing tests**

Copy the helpers of `plugins/my/tests/test_status_scan.py`: `clean_env`,
`git`, `make_repo`, `commit`, and a `run(cwd, *args)` that runs
`SCRIPT = .../bin/ds-count.py`. Add a helper
`inventory(lines, before="# Design system\n\n## Counts\n\n", after="\nend\n")`
that returns the inventory text with each line of `lines` inside a
`` ```ds-patterns `` block. A shared fixture commits `web/a.vue` with
`<input>\n<input>`, `web/b/c.vue` with `<input>`, `web/components/ZField.vue`
with `<input>`, and `docs/DESIGN-SYSTEM.md`.

```python
def test_counts_matches_and_files(self):
    # pattern {"globs": ["web/**/*.vue"], "exclude": ["web/components/Z*.vue"], "regex": "<input\\b"}
    out = run(repo)
    self.assertEqual(out.returncode, 0)
    self.assertEqual(out.stdout, "text field  hand-built  new -> 3/2\n")

def test_exclude_removes_files(self):
    # same pattern without "exclude" -> "new -> 4/3"; with it -> "new -> 3/2"

def test_globs_add_up(self):
    # add web/x.blade.php with one <input>; globs ["web/**/*.vue", "web/**/*.blade.php"]
    # -> "new -> 4/3" (exclude kept)

def test_double_star_matches_deep_files(self):
    # a repo of its own, not the shared fixture: web/a/b/c.vue holds the only match;
    # globs ["web/**/*.vue"] -> "new -> 1/1"

def test_pattern_spans_lines(self):
    # file "<ZButton\n  ghost>"; regex "<ZButton\\s+ghost" -> "new -> 1/1"

def test_write_changes_only_block(self):
    # --write; bytes before and after the block equal the original bytes;
    # the line holds an unknown key "note": "x" between "kind" and "globs";
    # it becomes json.dumps({...same keys in the same order..., "count": 3, "files": 2},
    # ensure_ascii=False), with "note" kept (Decision 4)
    # a second plain run prints "3/2 -> 3/2"

def test_zero_match_reports_zero(self):
    # regex "<select\\b" -> "new -> 0/0", exit 0

def test_missing_block_refused(self):
    # no ds-patterns fence; exit 1; stderr names the inventory path; stdout ""

def test_bad_json_line_refused(self):
    # block line 2 is "{oops"; exit 1; stderr names the inventory line number

def test_bad_regex_refused(self):
    # regex "(" ; exit 1; stderr names the line number

def test_duplicate_name_refused(self):
    # two lines named "text field"; exit 1; with --write the file bytes are unchanged

def test_untracked_files_ignored(self):
    # untracked web/new.vue, and web/node_modules/x.vue ignored by .gitignore, each hold <input>;
    # counts stay "3/2"

def test_empty_block_valid(self):
    # empty block; stdout ""; exit 0

def test_glob_matching_no_file_refused(self):
    # globs ["wbe/**/*.vue"]; exit 1; stderr names the line number

def test_excludes_leaving_no_file_report_zero(self):
    # globs ["web/components/Z*.vue"], exclude the same -> "new -> 0/0", exit 0 (Decision 2)

def test_missing_required_key_refused(self):
    # line without "regex"; exit 1; stderr names the line number

def test_wrong_kind_refused(self):
    # "kind": "widget"; exit 1

def test_non_ascii_kept(self):
    # name "πεδίο κειμένου"; --write keeps it unescaped in the file

def test_deleted_tracked_file_skipped(self):
    # remove web/b/c.vue from the working tree, not from the index -> "new -> 2/1", exit 0 (Decision 8)

def test_outside_repo_refused(self):
    # run in a temporary folder that is not a git repo, with an inventory path; exit 1 (Decision 6)

# Review Focus
def test_empty_match_regex_refused(self):
    # regex "\\b"; exit 1; stderr names the line number; with --write the file is unchanged
def test_unclosed_block_refused(self):
    # no closing fence; exit 1; file unchanged
def test_two_blocks_refused(self):
    # two ds-patterns blocks; exit 1
def test_blank_lines_kept(self):
    # a blank line between two pattern lines; --write; the blank line is still there; both counted
def test_write_keeps_crlf(self):
    # inventory written with "\r\n" endings; --write; every line still ends "\r\n"
def test_run_from_subfolder(self):
    # run(repo / "web", "--write", "../docs/DESIGN-SYSTEM.md") -> same stdout as from the root
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/my && python3 -m unittest tests.test_ds_count -v`
Expected: every test fails, because `bin/ds-count.py` does not exist (the
subprocess exits 2 with "can't open file").

- [ ] **Step 3: Implement `plugins/my/bin/ds-count.py`**

`#!/usr/bin/env python3`, a module docstring in the form of
`status-scan.py`'s (what it does, usage, the keys, exit codes), then
`chmod 755`. Functions:

- `find_block(lines: list[str]) -> tuple[int, int]`: the index of the opening
  and the closing fence (Decision 1); raises `Refusal(message)` otherwise.
- `parse_patterns(lines, start, end) -> list[tuple[int, dict]]`: each
  non-blank line's 1-based line number in the file, and its object, checked as
  Decisions 7 and 10 and the spec's refusal list say.
- `tracked(root: str, globs: list[str], exclude: list[str]) -> list[str]`:
  `git ls-files -z --` with `':(glob)<g>'` and `':(glob,exclude)<e>'`, run
  with `cwd=root`.
- `count(root, files, regex) -> tuple[int, int]`: matches in total and files
  with a match; each file read as UTF-8 with `errors="replace"`; a missing
  file skipped (Decision 8); a zero-length match raises `Refusal`
  (Decision 7).
- `main(argv) -> int`.

`Refusal` is printed to stderr as `ds-count: <message>` and gives exit 1.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd plugins/my && python3 -m unittest tests.test_ds_count -v`
Expected: all pass. Then run both full test commands of Global Constraints.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/tests/test_ds_count.py plugins/my/bin/ds-count.py
git commit --trailer "Task: 1" -m "feat(my-plugin): add ds-count.py, which counts the design-system patterns"
```

Check that `git diff --cached --summary` shows mode `100755` for the script.

---

### Task 2: The skill, `my:design-system`

**Files:**

- Create: `plugins/my/skills/design-system/SKILL.md`
- Modify: `plugins/kit/tests/test_neutral_core.py:28-30` (`MY_NAMES`)

**Interfaces:**

- Consumes: `ds-count.py [--write] [<inventory>]` (Task 1).
- Produces: the skill `my:design-system` with the arguments of Decision 12.
  Tasks 3 to 5 name it by `my:design-system audit`,
  `my:design-system refresh <spec path>` (with `auto` in an auto run) and
  `my:design-system sync`.

- [ ] **Step 1: Add `design-system` to `MY_NAMES`**

Append `"design-system"` to the list in `test_neutral_core.py`, and update the
comment above it if it names a count. Run
`cd plugins/kit && python3 -m unittest tests.test_neutral_core -v`.
Expected: pass (Decision 13: a guard, not a red test).

- [ ] **Step 2: Write `SKILL.md`**

Frontmatter in the form of `plugins/my/skills/status/SKILL.md`:
`name: design-system`, and a `description: >` block that names the three
modes, the path `docs/DESIGN-SYSTEM.md`, when to use it (before the first UI
spec in a project with no inventory, at step 13, before drawing a canvas when
the artifact is stale) and ends with
`NOT for writing component code: each component to build or extract becomes a roadmap row (my:roadmap-management).`

Body, in this order. The content of each part is fixed by the spec section
named; write it as numbered steps in the skill's own words.

1. A title and one paragraph: what the inventory is, and
   `Spec: docs/plans/2026-10-16-design-system-skill-spec.md in the claude-setup repo.`
2. **Arguments** (Decision 12) and the usage line.
3. **The inventory**: the four parts and their rules (spec, "The inventory"),
   the key table of the `ds-patterns` block, and the rule that each block
   `name` matches a row name in part 2 or 3. Then **the template**, a fenced
   `markdown` block with the headings of Decision 11, the three Sources lines
   word for word with their `none yet` forms, empty tables with the spec's
   columns (part 2: name, purpose, variants, sizes, states, tests; part 3:
   name, what it looks like, where it goes), and an empty `ds-patterns`
   block. Use a four-backtick outer fence so the inner block survives. State
   that this is the only template.
4. **`audit`**: steps 1 to 8 of the spec, the checklist of step 4, and the
   "A new app" paragraph with its token families and base components word for
   word. Step 1 and step 5 ask the user; in a session without
   `AskUserQuestion`, take the answers from the prompt. The report path is
   `docs/reports/YYYY-MM-DD-design-system-audit.md`, its sections the seven
   the spec lists.
5. **`refresh`**: steps 1 to 6 of the spec. Step 5 runs the staleness command
   of D11, word for word:
   `git log --oneline <synced commit>..HEAD -- <tokens file> <components folder>`,
   with its two `none yet` cases. With `auto`, never `sync`.
6. **`sync`**: steps 1 to 4 of the spec. The Artifact tool's Design System
   type and its `from-code.md` are named; the README's component table comes
   from part 2; the "Not synced" list is required. Before any publish, ask the
   user; with `auto` or without a yes, stop and leave Sources as it is (D10).
7. **Rules**: the skill writes no component code (D3); it never adds a
   `hand-built` line outside `audit` (D6); counts come only from
   `ds-count.py` (D4); every commit it makes is a `docs:` commit of
   `docs/DESIGN-SYSTEM.md` and, for `audit`, the report, named by path with
   `git commit -m … -- <paths>`. In a project whose `CLAUDE.md` or
   `CLAUDE.local.md` has a "Parallel runs" section, the commit is
   `locked-commit.py -F <message file> <paths>` instead, with the message
   written by the Write tool to a file in the scratchpad, as
   `plugins/my/skills/architect/SKILL.md` lines 246–254 say. There,
   `docs/DESIGN-SYSTEM.md` is a shared doc: before editing it, run
   `git diff --quiet HEAD -- docs/DESIGN-SYSTEM.md`, and stop when it exits
   non-zero.

- [ ] **Step 3: Lint and test**

Run the lint command of Global Constraints on `SKILL.md`: expected 0. Run both
full test commands: expected all pass.

- [ ] **Step 4: Commit**

```bash
git add plugins/my/skills/design-system/SKILL.md plugins/kit/tests/test_neutral_core.py
git commit --trailer "Task: 2" -m "feat: add the my:design-system skill"
```

---

### Task 3: The method and step 13

**Files:**

- Modify: `global/methods/my.md` (task-class table at lines 54–64; step 1 at
  line 84; "UI Design" at lines 111–140)
- Modify: `global/rules/docs-layout.md:167` (step 13)

**Interfaces:**

- Consumes: the skill name and arguments (Task 2).

- [ ] **Step 1: Task-class row.** In `my.md`, insert after the row
  "New feature, component, or behavior change …" (line 57), as one line:

  ```markdown
  | UI work (a screen, a state or a component) in a Medium or Large change, in a project with no `docs/DESIGN-SYSTEM.md` | `my:design-system audit`, then `superpowers:brainstorming`. When the `my:architect` row also matches, `my:architect` runs first |
  ```

- [ ] **Step 2: Step 1 of the two-artifact flow.** In line 84, after "built
  in this row or in a shared row ordered before it", and before the closing
  `)`, insert this text. Row 59's words stay as they are.

  ```markdown
  ; the spec reads `docs/DESIGN-SYSTEM.md` first and maps each element to a component, variant or token listed there
  ```

- [ ] **Step 3: UI Design.** Three edits, wrapped at 80:
  - The `design` bullet's first line becomes the first line below. The rest
    of the bullet stays.

    ```markdown
    - **`design`** — the Artifact tool's **Design** type: a Claude Design canvas of `.dc.html` artboards on one pan/zoom
    ```

  - After the bullet list, a new paragraph:

    ```markdown
    The canvas is built on the project's Design System artifact, whose link is
    in the Sources part of `docs/DESIGN-SYSTEM.md`. Boards use its tokens. Each
    part is labelled with its component name from the inventory, or
    «new: `<name>`». Before drawing, run the staleness
    command, `git log --oneline <synced commit>..HEAD -- <tokens file>
    <components folder>`, with the paths and the commit from Sources. On any
    output, or when Sources says `none yet` for the artifact, run
    `my:design-system sync` first. A new app with no tokens file yet skips
    this, and its canvas takes its direction from `frontend-design`.
    ```

  - At the end of "Keep a canvas sorted by status", add:
    `The same step refreshes the inventory: see step 13 in
    `~/.claude/rules/docs-layout.md`.` (with the path in backticks).

- [ ] **Step 4: Step 13.** In `docs-layout.md`, after "Mark the spec and plan
  `done` on `main`, citing the squash commit.", add, wrapped at 100 and
  indented as a continuation of step 13:

  ```markdown
  When `docs/DESIGN-SYSTEM.md` exists, and the spec has a Visual Language section or the squash
  commit touches the tokens file or the components folder named in its Sources, also run
  `my:design-system refresh <spec path>`, adding `auto` in an auto run, and commit its inventory
  edits with the `done` marks. A project with no inventory skips this.
  ```

- [ ] **Step 5: Check.** Lint both files: `my.md` stays at 1, `docs-layout.md`
  at 0. Run both full test commands (`test_neutral_core.py` reads these
  files): expected all pass. Read `git diff` once against the spec's "Edits to
  existing files" for these two files.

- [ ] **Step 6: Commit**

```bash
git add global/methods/my.md global/rules/docs-layout.md
git commit --trailer "Task: 3" -m "feat(global): UI specs read docs/DESIGN-SYSTEM.md, and step 13 refreshes it"
```

---

### Task 4: The shared-doc list and the spec reviewer

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md:250` and `:719-720`
- Modify: `plugins/my/skills/handoff/README.md:378-380`
- Modify: `plugins/my/skills/spec-review/spec-reviewer-prompt.md:69` (insert
  after)

- [ ] **Step 1: Stop row 19.** Its fourth cell becomes:

  ```markdown
  A shared doc (`ROADMAP.md`, `CHANGELOG.md`, the plans index, `docs/DESIGN-SYSTEM.md`) holds someone else's edits
  ```

- [ ] **Step 2: Plan stage step 6.** "the plans index, `ROADMAP.md` and
  `CHANGELOG.md` are shared docs" becomes "the plans index, `ROADMAP.md`,
  `CHANGELOG.md` and `docs/DESIGN-SYSTEM.md` are shared docs". Rewrap the
  paragraph at 80.

- [ ] **Step 3: README bullet.** "A run edits `ROADMAP.md`, `CHANGELOG.md` or
  the plans index only when …" becomes "A run edits `ROADMAP.md`,
  `CHANGELOG.md`, the plans index or `docs/DESIGN-SYSTEM.md` only when …".
  Rewrap at 80.

- [ ] **Step 4: Criterion 6.** After the bullet that ends "… in a shared row
  ordered before it." (line 69), add one bullet with three sub-bullets, each a
  single line:

  ```markdown
     - When `docs/DESIGN-SYSTEM.md` exists, read it with `cat`. Check each element of the Visual Language section against its Components and Hand-built patterns parts:
       - An element built in the page where a listed component does the job is a `Warning` and a `design` finding.
       - An element labelled «new» that this spec builds as a shared component, or that a row the roadmap orders before this one builds, is not a finding: the rule above allows both, and the inventory lists a component only after its row merges.
       - Any other element mapped to a component or variant that the inventory does not list is a `Warning`: `editorial` when it is a wrong name for something that exists, `design` when the part is new.
  ```

- [ ] **Step 5: Check.** Lint the three files: each stays at 0. Run both full
  test commands: expected all pass.

- [ ] **Step 6: Commit**

```bash
git add plugins/my/skills/handoff/SKILL.md plugins/my/skills/handoff/README.md plugins/my/skills/spec-review/spec-reviewer-prompt.md
git commit --trailer "Task: 4" -m "feat(my-plugin): the inventory is a shared doc, and the spec review checks specs against it"
```

---

### Task 5: `README.md`

**Files:**

- Modify: `README.md` (`my` skills list, after the entry that starts
  `` - `my:status` — `` (line 127 on `main`); the scripts paragraph, after the
  sentence that starts `` `status-scan.py`, in the same folder `` (line 179
  on `main`)). Find them by their text: the main checkout holds another
  session's uncommitted edit of `README.md`, so its line numbers differ.

- [ ] **Step 1: Skill entry**, wrapped at 80:

  ```markdown
  - `my:design-system` — Keeps `docs/DESIGN-SYSTEM.md`, the inventory of shared
    components and hand-built patterns that UI specs read and spec reviews
    check. `audit` builds it, `refresh` updates it at step 13, and `sync` makes
    the Design System artifact that canvases draw from. It writes no component
    code: each component to build becomes a roadmap row.
  ```

- [ ] **Step 2: Script sentence**, appended to the paragraph:
  "`ds-count.py`, in the same folder, counts the search patterns in the
  `ds-patterns` block of `docs/DESIGN-SYSTEM.md`, and with `--write` stores
  the counts there; its tests run with the same command."

- [ ] **Step 3: Check and commit.** Lint: stays at 0.

```bash
git add README.md
git commit --trailer "Task: 5" -m "docs: README lists my:design-system and ds-count.py"
```

---

### Task 6: Headless rehearsals

Spec, Testing strategy items 2, 3 and 4. No repo file changes until Step 6.

**Files:**

- Create in the scratchpad only: `$SCRATCH/ds/` with the fixtures and
  `$SCRATCH/ds/rehearsal.md`. `$SCRATCH` is the session's scratchpad.

**Interfaces:**

- Consumes: everything above, through `--plugin-dir "$WT/plugins/my"`, with
  `WT` the worktree's absolute path.

Every run is:

```bash
cd <fixture> && TMPDIR=$SCRATCH/ds/tmp claude -p --plugin-dir "$WT/plugins/my" \
  --add-dir "$SCRATCH/ds" --add-dir "$WT" --permission-mode acceptEdits \
  --output-format stream-json --verbose '<prompt>' > $SCRATCH/ds/<run>.jsonl
```

After each run, count `"subtype":"permission_denied"` in the `.jsonl`: any
denial makes the run invalid; widen `--add-dir` and run it again. Also check
that the stream reads the skill files from `$WT/plugins/my/`: a run that
read an installed copy is invalid. When this plan checks counts itself, it
runs the branch's script by path, `python3 "$WT/plugins/my/bin/ds-count.py"`,
because the installed plugin has no `ds-count.py`. Every prompt
says: "Answer no to any question about `sync`; publish nothing." `claude -p`
has no `AskUserQuestion`, so each prompt gives the answers the skill would
ask for.

- [ ] **Step 1: Fixture A and `audit`.** A git repo with
  `assets/tokens.css` (six CSS variables, two of them colours),
  `components/AppButton.vue` and `components/AppCard.vue`, and three pages
  `pages/one.vue`, `pages/two.vue`, `pages/three.vue`, each with a hand-built
  `<input class="…">`. A `ROADMAP.md` with one row. All committed. Prompt:
  `/my:design-system audit` plus "The tokens file is `assets/tokens.css`; the
  components folder is `components/`. Propose rows, add none." Expected:
  `docs/DESIGN-SYSTEM.md` has the four parts under the headings of Decision 11;
  the branch's `ds-count.py`, run by path in the fixture, prints the same old
  and new values on every line, so the block's counts are the script's; the
  input pattern counts 3 in 3 files, and if its globs would count a
  `components/` file, it excludes that file;
  the report in `docs/reports/` proposes a field component as a row; Sources
  says `none yet` for the artifact; one `docs:` commit holds both files.

- [ ] **Step 2: Fixture B and `audit` of a new app.** Pages with hand-built
  inputs, no components folder, no tokens file, and a `ROADMAP.md` with row 1.
  Same prompt shape, with "There is no tokens file and no components folder.
  The starting row, if you propose one, will be row 2; add no rows."
  Expected: the report proposes one starting row with the token families and
  base components of the spec's "A new app" paragraph; Sources says
  `none yet (row 2)` for the tokens.

- [ ] **Step 3: `refresh` on fixture A.** Commit `components/AppField.vue`,
  replace the inputs of all three pages with `<AppField>`, and commit
  `docs/plans/2026-10-16-field-spec.md` with a Visual Language section. Run
  `/my:design-system refresh docs/plans/2026-10-16-field-spec.md`. Expected:
  the counts change; `AppField` has a part 2 row and a `component` line; the
  input pattern at 0 has lost its line and its part 3 row; no new `hand-built`
  line. Then delete `components/AppCard.vue`, commit, and run `refresh` again:
  its row and line are gone.

- [ ] **Step 4: Step 13, both cases.** Prompt for both: "Read
  `$WT/global/rules/docs-layout.md`, section 'One feature, four commits on
  `main`', step 13, and carry it out for `<spec>`, squash commit `<hash>`."
  (The branch's file, because `~/.claude/rules/` points to the main
  checkout.)
  - Fixture C: fixture A's state before Step 1 (no `docs/DESIGN-SYSTEM.md`),
    plus a merged change and a spec with a Visual Language section, both
    `approved`. Expected: the stream has no `ds-count.py` call and no
    `my:design-system` call; the `done` marks commit.
  - Fixture A after Step 3, plus a merged change that adds
    `components/AppBadge.vue` and a spec with a Visual Language section.
    Expected: the stream calls `my:design-system refresh <spec>`; `AppBadge`
    gets a part 2 row and a `component` line; those inventory edits are in the
    same commit as the `done` marks.

- [ ] **Step 5: Criterion 6 (item 3).** In fixture A after Step 1, where the
  inventory lists `AppButton`:
  - Spec 1 styles a `<button>` by hand in one page. Run
    `/my:spec-review <spec 1>`. Expected: a `design` finding on the button.
    Remove `docs/DESIGN-SYSTEM.md`, commit, run again: no such finding.
    Restore it.
  - Spec 2 names `AppBtn` for the button that part 2 lists as `AppButton`, a
    wrong name for a part that exists. Expected: an `editorial` finding on
    the name.
  - Spec 3 labels a part «new: `Field`» and builds it as a shared component.
    Expected: no finding about it.

- [ ] **Step 6: Zitamu regression (item 4).**
  `git clone -q ~/projects/zitamu/real-estate-webapp $SCRATCH/ds/zitamu`.
  The clone's `.claude/settings.json` turns on the installed `my` plugin
  (`"my@claude-setup": true`), which would load beside the branch's copy.
  Remove that one key in the clone, and leave the clone's other settings.
  Run
  `/my:design-system audit` there with "The tokens file is
  `web/assets/css/tokens.css`; the components are `web/components/Z*.vue`.
  Propose rows, add none." Then run
  `/my:spec-review docs/plans/2026-10-15-agent-request-list-page-spec.md`.
  Expected: a finding on the find input and on the selects. Keep the clone
  for Task 7.

- [ ] **Step 7: Record.** Write each check (expected, seen, pass or fail)
  into `$SCRATCH/ds/rehearsal.md`. A failed check is a bug in Tasks 1 to 5:
  use `superpowers:systematic-debugging`, fix it with a test where one
  applies, commit, and rerun that step on a fresh fixture. Append a
  "Rehearsal, `<date>`" list with the results to this plan's **Testing
  Strategy**, and commit it in the worktree:

```bash
git add docs/plans/2026-10-16-design-system-skill.md
git commit --trailer "Task: 6" -m "docs(plans): rehearsal results for my:design-system"
```

---

### Task 7: `sync`, with the user's yes

Spec, Testing strategy item 5. It revises the user's real artifact on
claude.ai, which needs the user's yes (D10). The Delegation section does not
list it, so in an auto run it is a stop.

- [ ] **Step 1: Prepare.** In the clone from Task 6, write into Sources:
  `**Design System artifact:** https://claude.ai/artifact/8vKHqdSLDqZtiGSvz8vmB8, synced from <hash>`.
  `<hash>` is the parent of the last commit that touches the Sources paths:
  `git rev-parse --short "$(git log -1 --format=%H -- web/assets/css/tokens.css 'web/components/Z*.vue')~1"`
  (that last commit was `7bada58` on 2026-10-16). Then run the staleness
  command and check that it prints at least one line. Without this, the check
  after the sync proves nothing.

- [ ] **Step 2: Gate.** Run
  `handoff-state.py set design-system-skill stopped="sync rehearsal ready; it revises the zitamu Design System artifact"`
  and signal
  `code-design-system-skill: sync rehearsal ready; reply yes to revise the zitamu Design System artifact`.
  Wait for the reply. After it, run
  `handoff-state.py set design-system-skill stopped=`. On a no, record
  "skipped by the user" in Step 4 and go on.

- [ ] **Step 3: Run `sync`.** This session has the installed plugin, not the
  branch's. So read `$WT/plugins/my/skills/design-system/SKILL.md` and carry
  out its `sync` mode with the clone as the project, with
  `cd $SCRATCH/ds/zitamu && …` for every command. Expected: the artifact's
  README keeps its prose; its component table is regenerated from the
  clone's part 2; Sources says `synced from <the clone's HEAD short hash>`;
  the staleness command prints nothing afterwards.

- [ ] **Step 4: Record and clean up.** Append the result to the
  "Rehearsal" list, and commit in the worktree:

```bash
git add docs/plans/2026-10-16-design-system-skill.md
git commit --trailer "Task: 7" -m "docs(plans): sync rehearsal result for my:design-system"
```

Delete the clone: `rm -rf $SCRATCH/ds/zitamu`.

---

## Trade-Offs

- **Refuse an empty-matching regex** (Decision 7) versus count it. Counting
  gives numbers in the thousands that mean nothing and change with every
  edit. Refusing costs one check per line and names the line to fix.
- **Check the no-match refusal before the excludes** (Decision 2) versus
  after. After would refuse a pattern whose excludes remove its last file,
  which is the state a finished extraction reaches. Before keeps that a
  `0/0` and still catches a typo in the globs.
- **One rehearsal task for items 2 to 4, and a separate one for item 5.**
  Item 5 is the only step that needs the user. Keeping it last lets every
  headless check finish before the stop.
- **Fixed headings in the template** (Decision 11) versus free headings.
  Fixed headings let `refresh` and the reviewer find each part without
  guessing, at the cost of one more rule in the template.

## Dependencies

- None new. Python 3 standard library, git 2.43.0, and `claude` 2.1.301 for
  the rehearsals.
- The Artifact tool's Design System type, for Task 7 only.
- Row 59 (`7e938b9`) is on `main`; Tasks 3 and 4 extend its two sentences.

## Risk

1. **Blast radius.** `global/methods/my.md` and `docs-layout.md` reach every
   project on the `my` method; criterion 6 reaches every spec review; the
   shared-doc list reaches projects with a "Parallel runs" section. All of it
   is prompt text plus one new script, so one revert undoes it.
2. **The order of work.** `ROADMAP.md` ("Order of work", steps 1 and 2)
   orders row 64 after step 1 (rows 33, 37, 56, 45, 46 and 62) and after row
   61. All of them are still 💭 on 2026-10-16. The user started this run
   before them, which is their call; this plan changes no order. Those rows
   edit the same files: 33, 37 and 56 edit `handoff/SKILL.md`; 45 edits
   `spec-reviewer-prompt.md` and `README.md`; 61 edits `global/methods/my.md`.
   Whichever merges second rebases onto the other's text. Detect: a conflict
   in that row's squash-merge.
3. **The rehearsals read the branch's skills, and the main checkout's rules.**
   `~/.claude/` links into the main checkout, so a headless run sees the
   branch's `global/` text only when its prompt names the worktree path, as
   Task 6 Step 4 does. Task 7 reads the branch's `SKILL.md` by path for the
   same reason.
4. **The rehearsals cost model time.** Task 6 makes about ten `claude -p`
   runs, two of them on the zitamu clone.
5. **Counts drift between the spec and today.** The spec's zitamu numbers
   (64 and 41 `.vue` files) are 65 and 42 on 2026-10-16. No test depends on
   them.
6. **A regex can still over-count** (spec, Risk 3). Decision 7 refuses only
   the empty-match case.
7. **Task 7 changes a real artifact.** It runs only after the user's yes, and
   the type's re-sync rules keep the README's prose.
8. **Another session's uncommitted `README.md` edit** sits in the main
   checkout. If it is still uncommitted when this branch squash-merges,
   `git merge --squash` refuses, because it would overwrite that edit. The
   review stage stops there (row 15). The user commits or stashes it first.
9. **Sources has no `none yet` form for the components folder.** The spec
   gives one only for the tokens. The new-app rehearsal wrote
   `none yet (row 2)` on the Components line too, which reads well. Known
   limit; a later row can add the form.
10. **The hex-colour example misses a colour that is not right after a
    colon,** such as `border:1px solid #ccc`. The example is the spec's,
    word for word; `audit` writes its own regex per project, as the new-app
    rehearsal did (`#[0-9a-fA-F]{3,8}\b`). Known limit.
11. **`sync` and the zitamu regression never ran** (end-of-branch review).
    The user skipped both (Testing Strategy, "Rehearsal"). So the first real
    `sync` changes a live claude.ai artifact with untested steps: create or
    revise, the "Not synced" list, the Sources write. `sync` asks for a yes
    before any publish, so the user sees it first. Detect: read the artifact
    and the Sources line after the first `sync`.
12. **The new spec-review bullet was not tested on its own** (end-of-branch
    review). Without the inventory, the reviewer raised the same finding
    through criterion 4, because the fixture's `AppButton` is findable in the
    code. So the bullet is shown to work, but not shown to add a finding that
    code search would miss. Detect: a spec review that cites the inventory
    for a component that the code names differently.
13. **A glob over `docs/` counts the inventory's own text** (end-of-branch
    review). A pattern such as `**/*.md` matches its own `regex` in
    `docs/DESIGN-SYSTEM.md`, so its count never reaches 0. No pattern today
    covers `docs/`. Known limit, next to item 6.
14. **`"design-system"` in `MY_NAMES` bans the word from every kit file**
    (end-of-branch review). `test_neutral_core.py` derives `MY_BARE` from
    names with a hyphen, so a future kit file that writes "design-system
    primitives" fails `test_kit_names_no_my_skill`. No kit file does today.
    The fix then is the `code-reviewer` exception the test already has.
15. **`ds-count.py` reruns `git ls-files` and rereads files per pattern**
    (end-of-branch review). The work grows as patterns times files. Today's
    largest project has about 65 `.vue` files, so this is speed, not
    correctness.
16. **Low script limits found by the final re-review.** Each is input that
    today's inventories never hold:
    - The empty-match regex check runs only while reading files, so `x*`
      over globs whose excludes leave no file prints `0/0` and exits 0.
    - `--write` writes U+2028, U+2029 and U+0085 unescaped, and
      `splitlines()` then breaks the line, so the next run refuses it.
    - The fences are found only at column 0; an indented Counts block reads
      as "no ds-patterns block". The template puts them at column 0.
    - A tracked file name that is not valid UTF-8 ends in a traceback, not a
      one-line refusal.
    - `--write` replaces a symlinked inventory with a plain file.
17. **The staleness rule is written out twice,** in `refresh` step 5 and in
    the UI Design paragraph of `global/methods/my.md`. A later edit to one
    must be made to both.
18. **Two branch commits have no scope** ("feat: add the my:design-system
    skill", "docs: README lists …"). The squash commit has one; the kept
    branch keeps the two subjects.
19. **A line whose files are gone blocks `refresh`** (end-of-branch review;
    the user chose to keep spec D7 as written). When a row deletes or
    renames the last files a line covers, `ds-count.py --write` refuses
    with "the globs match no tracked file", so `refresh` stops at step 1
    and step 13 stops with it. The refusal is loud and loses no data: the
    user fixes the line's globs, or removes the line, and runs it again. A
    fix round tried "retire the line" and was reverted, because a folder
    rename gives the same refusal and the pattern would be lost silently.
    Detect: a step 13 that stops on that message.
20. **The synced commit in Sources blocks a fold after it** (final
    re-review). `synced from <short HEAD>` sits in `docs/DESIGN-SYSTEM.md`,
    and `git-fold-fixups.py` (`citations()`) refuses to fold across any
    commit that a file under `docs/` cites. So a `sync` made after the spec
    or plan commit makes that fold exit 1 with "cited in
    docs/DESIGN-SYSTEM.md". The refusal is safe and names its cause; auto
    runs never `sync`. Because of it, a fold never gives the synced commit a
    new hash, so the staleness test needs no case for that (a fix round
    added one and it was reverted). Changing the Sources format would change
    a contract; a later row can decide it. Detect: that fold message.

## Testing Strategy

- **Unit:** `plugins/my/tests/test_ds_count.py`, 27 tests from Task 1 (one more
  than planned, `test_bool_count_refused`) and three from the end-of-branch
  fix round, 30 in all, in the
  style of `test_status_scan.py`: a fixture repo per test, the script run as
  a subprocess, git without the user's config.
- **Guard:** `test_neutral_core.py` with `design-system` in `MY_NAMES`
  (Task 2).
- **Prompt text:** the headless rehearsals of Task 6 (spec items 2 to 4) and
  the `sync` rehearsal of Task 7 (item 5). Their records go below.
- **Lint:** the counts of Global Constraints, at each task and at the end of
  the branch.

### Rehearsal, 2026-10-16

Each run was `claude -p` with `--plugin-dir` set to the worktree's
`plugins/my`. Every stream read the skill files from the worktree and had 0
`permission_denied` events.

- **Step 1, `audit` on fixture A: pass.** The inventory has the four parts
  under the fixed headings. The branch's `ds-count.py`, run by path, prints
  equal old and new values on all five lines. The input pattern counts 3 in
  3 files; no `components/` file held an `<input>`, so no exclude was needed.
  The report proposes a text field component as a row. Sources says
  `none yet` for the artifact. One `docs:` commit holds both files.
- **Step 2, `audit` of a new app (fixture B): pass.** The report proposes one
  starting row, row 2, with the token families and the six base components
  of the spec's "A new app" paragraph. Sources says `none yet (row 2)` for
  the tokens. The run raised two points, recorded as known limits in Risk
  items 9 and 10.
- **Step 3, `refresh` on fixture A: pass.** After `AppField` replaced the
  three inputs, the counts changed, `AppField` got a part 2 row and a
  `component` line, the three patterns at 0 lost their lines and rows, and no
  `hand-built` line was added. The text field pattern stayed at 1/1 at first,
  because `AppField.vue` holds the `<input>`; the model added that file to the
  pattern's `exclude` on its own. The skill now says so in `refresh` step 2,
  and a rerun on a fresh copy passed the same way. After `AppCard.vue` was
  deleted, a second `refresh` removed its row and its line.
- **Step 4, step 13 without an inventory (fixture C): pass.** The stream has
  no `ds-count.py` call and no `my:design-system` call. The `done` marks
  committed.
- **Step 4, step 13 with an inventory (fixture A): pass.** The stream calls
  `my:design-system refresh docs/plans/2026-10-16-badge-spec.md`. `AppBadge`
  got a part 2 row and a `component` line, in the same commit as the `done`
  marks.
- **Step 5, criterion 6, spec 1 (in-page button) with the inventory: pass.**
  A `Warning`, `design` finding on the button, citing the inventory's
  `AppButton` row.
- **Step 5, spec 1 without the inventory: partial.** Expected no such
  finding; seen a `Warning`, `design` finding on the button through criterion
  4, citing `components/AppButton.vue` and the pages, not the inventory. The
  fixture's `AppButton` is findable in the code, so it cannot isolate the new
  bullet. The bullet itself works (the line above); the gap is in the test's
  premise, not in Tasks 1 to 5.
- **Step 5, spec 2 (`AppBtn` for `AppButton`): pass.** A `Warning`,
  `editorial` finding on the name.
- **Step 5, spec 3 («new: `Field`», built shared): pass.** No finding about
  it; the review lists it under criterion 6 as matching the rule.
- **Step 6, zitamu regression: skipped by the user.** The auto-mode safety
  check refused `git clone` of the zitamu repo into the scratchpad (personal
  data handling), and the user chose to skip rather than allow it.
- **Task 7, `sync` on the zitamu artifact: skipped by the user.** It needs the
  same clone. Nothing was published.

## Open Questions

None.
