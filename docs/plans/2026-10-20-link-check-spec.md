# Spec: `link-check.py`, the link check for the roadmap and the changelog

**Status:** approved, 2026-10-21. Roadmap row 51, cut to the link check; the next-number part is dropped.

## How to read this spec

1. `ROADMAP.md`, row 51 "Link check for the roadmap and changelog", and its place in `## Order of work`
   (step 2, moved there by the user on 2026-10-20). The row this spec answers.
2. `docs/reports/2026-10-14-scriptable-skill-steps.md`, finding S12. Where the row comes from.
3. `plugins/my/skills/roadmap-management/SKILL.md`, rule 8 "Linking discipline" (lines 147–154)
   and rule 10 "Cross-check the row you just touched" (lines 164–173). The rules the script
   checks, and the step that runs it.
4. `plugins/my/skills/changelog-management/SKILL.md`, rule 8 "Link to specs and plans" (lines
   111–120) and rule 10 "Cross-check the entry you just wrote" (lines 127–135). The same for the
   changelog.
5. `plugins/my/bin/status-scan.py` and `plugins/my/tests/test_status_scan.py`. The script style
   (docstring with Usage and exit codes, tab-separated output) and the test style (a throwaway
   repo, git without the user's config, the script run as a subprocess) that this work copies.
6. `README.md`, the paragraph on the scripts in `plugins/my/bin/` (lines 178–196).

## Context

`roadmap-management` rule 8 and `changelog-management` rule 8 say how links in `ROADMAP.md` and
`CHANGELOG.md` must look. A same-repo target is a relative `.md` path, never `.html`. An
out-of-repo target is an absolute web URL, never a `../other-repo/…` path. A link to a moved or
deleted document is repointed or removed. Today the model checks this by hand, and only for the
row or entry it touched: rule 10 of both skills forbids full-file link checks unless the user
asks for an audit.

On 2026-10-20 the 15 roadmap and changelog files in the user's 9 projects held 5 bad links:

| Problem | Hits | Where |
| --- | --- | --- |
| `.html` link to a doc whose source is `.md` | 0 | The one `.html` link, in `webext/ROADMAP.md`, points to a real tracked HTML file, `assets/grispy-landing.html`, with no `.md` twin. It is correct (D4). |
| `../` link that leaves the repo | 3 | `diagoradisa-ml/CHANGELOG.md` (2), `diagoradisa-annotator/ROADMAP.md` (1) |
| Dead link | 2 | `diagoradisa-palmist/CHANGELOG.md` (a file git ignores, under `.claude/docs/`), `grispy-site/CHANGELOG.md` (`guide/saved-details/`) |

Row 51 also asked for the next row number. Only this repo has a `**Next number:**` line, and it
was right (74, one above the highest row). The other projects number rows per table or not at
all, and `roadmap-management` rule 3 already covers each scheme in one sentence. The user chose
to drop that part.

## Goal

A script, `link-check.py`, lists every bad link in the files it is given, and marks whether it
sits on a line the current uncommitted edit changed. Both skills run it after each edit, before
the commit. They fix the problems on changed lines, and list the others to the user without
touching them.

## Out of scope

- The next row number (dropped, see Context).
- `#anchor` targets: `docs/x.md#section` passes when `docs/x.md` exists.
- HTML `<a href>` tags. None of the 15 files uses them.
- Other Markdown files. Links to a moved file across the whole repo stay with
  `docs-layout.md` "Moving a document" and row 47 ("`clean-plans` moves by script").
- Fixing the 5 bad links found above. Each project fixes its own when a skill next reports them.
- Moving the script to `kit`. Row 69, later in the order of work, moves both skills to `kit`,
  and with them the script, its test and its `README.md` sentence; its row text says so.

## Decisions

### D1. The interface

`link-check.py <file>...`. One or more paths, read as given (relative to the working
directory). `-h` or `--help` prints the docstring. The script reads and never writes.

### D2. What counts as a link

- Inline links `[text](target)` and images `![alt](target)`.
- Reference definitions at the start of a line: `[label]: target`.
- A target wrapped in `<…>` loses the brackets. A title in quotes after the target is dropped.
- Code is blanked before the search: fenced blocks (```` ``` ```` and `~~~`) and inline code
  spans. Blanking keeps every newline, so line numbers stay right. Indented lines are **not**
  code: roadmap rows wrap with indented continuation lines, and nested lists indent four spaces
  or more.
- The search runs over the whole text, not line by line, so a link whose text wraps over two
  lines is found. The reported line is the line that holds the target.

### D3. Skipped targets

A target with a scheme (`https:`, `mailto:`, any `<letters>:` at the start) and a pure
`#anchor` target are skipped.

### D4. The three kinds

For every other target, the script strips `#…` and `?…`, decodes percent escapes (`%20`), and
resolves the path from the folder of the file that holds the link. That folder is resolved
with `os.path.realpath` first, so it matches git's root even when the file was named through a
symlinked folder. The link part is joined with `os.path.normpath`, never `os.path.realpath`: a
symlink inside the repo that points outside it still works on the Git host. Each link gets at
most one problem, the first that applies:

1. `climbs`: the path ends up outside the repo root. The root is `git rev-parse
   --show-toplevel` run from the file's folder, or the file's folder when it is not in a git
   repo. A file in `docs/` may link `../ROADMAP.md`, because that stays inside the repo.
2. `html`: the path ends in `.html` or `.htm`, and the same path with `.md` in place of that
   ending exists. That marks a doc exported to HTML, which rule 8 forbids linking. A link to a
   real HTML file with no `.md` twin is correct, and gets no `html` problem.
3. `dead`: the path (a file or a folder) does not exist on disk, or git ignores it. A file git
   ignores exists locally but is missing on the Git host. The ignore check is one
   `git check-ignore --stdin` call per file; it does not report a file git already tracks, even
   when an ignore pattern matches it. A file git does not track yet counts as present, because a
   new spec is often committed in the same commit as its roadmap row.

An `.html` link whose `.md` twin exists shows `html`, whether or not the `.html` file exists, and
the fix is always the twin's path. An `.html` link with no twin and no file shows `dead`.

### D5. `new` or `old`

The script runs `git diff -U0 HEAD -- <file>` and reads the `+` side of each hunk header. A line
in an added range is `new`; every other line is `old`. `HEAD` covers both staged and unstaged
edits. When the file is untracked, outside a git repo, or the repo has no commit yet, every line
is `new`: nothing about it has been committed.

`new` works per line, not per row. In this repo a roadmap row spans several lines, so an edit to
its status line leaves a bad link on another line of the row `old`: listed, not fixed. In a table
roadmap a row is one line, so touching it marks its links `new`, as today's rule 10 checks the
row it touched. Row level would need a row parser for both roadmap forms, about twice the
script.

### D6. Output and exit codes

One line per problem, fields separated by one tab (shown as `<TAB>`), in file order then line
order:

```text
<kind><TAB><file>:<line><TAB><target><TAB><new|old>
```

`<file>` is the path as given on the command line. `<target>` is the target as written in the
file. A clean run prints nothing.

| Exit | Meaning |
| --- | --- |
| `0` | No problems, or `-h` / `--help`. |
| `1` | At least one problem, `new` or `old`. |
| `2` | A usage error, a file that cannot be read, or a git call that failed for another reason than "not a repo" or "untracked". Each message goes to stderr, starting `link-check.py:`. |

An error in one file does not stop the others: their problems still print, and the exit is `2`,
which wins over `1`. A git failure on a file is an error for that file, never a reason to mark
its lines `new`: that would make the skill fix old links. A skill that wants to know whether its
edit added a problem reads the fourth field, not the exit code.

### D7. How the skills use it

`roadmap-management` rule 10. The bullet "The Spec / Plan column links resolve." becomes:

> Before the commit in rule 9, run `link-check.py ROADMAP.md`. Fix every `new` problem by
> rule 8: `html` → the `.md` twin's path; `climbs` → the absolute web URL on the Git host;
> `dead` → the moved file's path, or ask the user when no moved file exists. List every `old`
> problem to the user, one line each, and leave it. If `link-check.py` is not on `PATH`, or it
> exits `2`, show its stderr line (or say it is missing) and check by hand that the links in the
> row you touched resolve.

The last line of rule 10 drops "full-file link greps" from its list and gains: "The link check
reads the whole file, but fixing old links is audit work."

`changelog-management` rule 10 gains the same bullet for `CHANGELOG.md`, with one difference by
its rule 8: a `dead` link to a deleted document is unlinked, keeping the name as plain text. Its
last line drops "link-resolution greps across all entries" in the same way.

The check needs the edit uncommitted, because `new` compares with `HEAD`. Rule 9 of each skill
(commit discipline) comes before rule 10 in the text, so rule 9 of each gains one line: "Run
rule 10's link check first."

A paired edit (`roadmap-management` rule 6, a row marked ✅ with its changelog entry) runs the
script once with both files: `link-check.py ROADMAP.md CHANGELOG.md`. `roadmap-management`, which
drives the paired edit, owns that run; `changelog-management`'s new bullet says to skip its own
run when it is the changelog half of a paired edit. Rule 6's precondition "The plan/spec links in the Spec / Plan
column still resolve." (line 122) stays: it runs before the edit, rule 10 after it.

### D8. Where it lives

`plugins/my/bin/link-check.py`, next to `status-scan.py` and `ds-count.py`. The plugin puts
`bin/` on `PATH` in Claude Code sessions, so it works in every project that has the `my` plugin.
The skill text and the script ship in the same plugin update.

## Trade-offs

- **A new script against a `--links` flag on `status-scan.py`.** The flag adds no file and keeps
  one roadmap reader. But `status-scan.py` belongs to `my:status` and reads rows, not links; it
  never reads `CHANGELOG.md`. Two jobs in one script make both harder to change. The user chose
  the new script.
- **Against an existing tool (`lychee`, `markdown-link-check`).** No code to write. But each is a
  new dependency, which needs approval, and neither knows the two house rules (no `.html`, no
  `../`).
- **Against a `pre-commit` hook check.** It would run without the model. But the hooks run only
  where `core.hooksPath` points at them, and all 5 bad links are in other projects.
- **Fix only new problems against fixing all.** Fixing all cleans each file once, but a one-line
  row edit could grow into unrelated fixes in the same commit. The user chose to fix only the
  edit's own problems and list the rest.
- **`html` only with a `.md` twin against every `.html` link.** Flagging every `.html` link is
  simpler, but `webext`'s correct link to its HTML draft would be listed on every edit, and a
  `new` one would have no `.md` path to fix to.
- **`new` per line against per row.** See D5: per row needs a row parser for both roadmap forms.
- **Sorting in the script against in the skill.** The model could map line numbers to the diff
  itself, but that means reading hunk headers by hand, the kind of fixed step row 51 moves into
  scripts.

## Dependencies

None. Python 3 standard library and git.

## Risk

No risk trigger: the script reads and never writes, and no stored data, permission or contract
changes.

1. **Every skill edit now runs a full-file read.** `real-estate-webapp/CHANGELOG.md` has about
   4,500 lines. The script makes one regex pass, one `git diff` and one `git check-ignore` per
   file, so it should stay under a second. Detection: Task 5 times the run on that file.
2. **Old problems are listed on every edit until someone fixes them.** In `diagoradisa-ml` the
   two `../` links print each time the changelog is edited. This is the chosen trade-off: the
   user sees them and decides when to run an audit.
3. **A false `dead`.** A link to a path a site serves but the repo does not hold shows as
   `dead`. None of the 15 files has one today: `grispy-site`'s `guide/saved-details/` is truly
   gone (its `CHANGELOG.md` records the 404). Such a link is `old`, so the skill only lists it.
4. **Old plugin installs.** A session whose plugin lacks the script falls back to today's hand
   check (D7), so it loses nothing.
5. **Known limits.** A target that contains `)` is cut at the first `)`. A file never committed
   passes as present. `#anchor` targets and `<a href>` tags are not checked (Out of scope).
   From the end-of-branch reviews; none of the 22 roadmap and changelog files under
   `~/projects` holds any of these today:
   - A line that starts with three backticks used as inline code (```` ```x``` text ````) opens
     a fence, so the links after it, up to the next fence, are not checked.
   - A link whose text holds brackets (`[see [1]](x)`, a linked badge `[![b](i.png)](x)`) is
     not matched, so its target is not checked.
   - A link inside an HTML comment, or written with escaped brackets (`\[x\](y)`), is checked
     as a link and may be listed.
   - A root-relative target (`/docs/a.md`) shows as `climbs`, though the Git host resolves it
     from the repo root.
   - A link through a symlinked folder or into a submodule makes `git check-ignore` fail, so
     the file exits `2` and the skill falls back to its hand check.
   - `git check-ignore` reads and writes one path per line without `-z`, so a target that
     starts with `"` or holds a tab, a newline or a backslash can make the file exit `2`.
   - git's output is decoded in the locale's encoding, not always UTF-8; the locale here is
     UTF-8.
   - Against D6: any failure of `git rev-parse --verify -q HEAD^{commit}` counts as "no commit
     yet", so a repo with a broken HEAD, whose root git still finds, marks every line `new`.
     `-q` hides the message that would tell the two apart.

   From the final re-review, kept as known limits by the one-fix-round rule. The first two are
   the ones worth a later row:
   - `git diff -U0` obeys `diff.interHunkContext` and textconv drivers. With either set, unchanged
     lines between two edited lines count as `new`. The fix is `--inter-hunk-context=0
     --no-textconv`. The user's git config sets neither today.
   - In a paired run, the exit-`2` fallback in `roadmap-management` rule 10 hand-checks only "the
     row you touched", and `changelog-management` skips its own run, so a changelog that exits
     `2` leaves the new entry's links unchecked. The fix is one wording change: hand-check the
     changed lines of both files.
   - `git ls-files` and `git diff` read the path as a glob, so a file name with `[`, `*` or `?`
     can match another file and get the wrong `new` or `old`.
   - An escaped backtick (`` \` ``) opens a code span, so links between two of them are not
     checked. A `` `` `` opener with no closer can match as a shorter span and end too early.
   - A target that holds `(` (`gone(1).md`) is not matched, so it is not checked.
   - A reference definition whose target sits on the next line is not matched.
   - `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE` from the caller reach git, so a run from a
     git hook can read another repository.
   - A file that starts with a byte-order mark hides a fence or a reference definition on line 1.
6. **Row 69 comes after.** When `roadmap-management` and
   `changelog-management` move to `kit`, the script, its test and its `README.md` sentence move
   too, and D8's path changes. Row 69's text names them (Out of scope).
7. **Lint: no new errors, not zero.** On `main`, `roadmap-management/SKILL.md` has 1
   `markdownlint-cli2` error and `changelog-management/SKILL.md` has 3, with the global config
   `~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc` (the repo has none). No changed file may
   gain one; rewrapping whole files is out of scope.
8. **Choices made in the code stage.** The behaviour follows D4 and D5; these are the places
   where the code differs from the Task 2 text, recorded here so a review does not redo them:
   - `repo_root(folder)` returns `None` outside git, not the folder, so `check` can tell a
     file at the repo root from a file outside git. `new_lines` takes `(path, root)`. Two
     helpers were added: `resolve` (the D4 path) and `ignored_paths` (the one
     `git check-ignore --stdin` call).
   - A fence line may have any indentation, because fences inside list items are indented.
     Indented lines that are not fences are still searched (D2). Known limit: a line that
     starts with three backticks deep in a list blanks text up to the next fence.
   - git runs with `LC_ALL=C`. "Not a repo" is found by git's English message, and a Greek
     message locale would otherwise make every file outside git exit `2`.
   - The 13 tests that expect no problem check exit `0` and empty stderr too: with stdout
     alone they passed while the script did not exist.
   - `roadmap-management` rule 10 also says how a paired edit runs the check (both files, the
     changelog's `new` problems fixed by `changelog-management` rule 8). D7 gives that skill
     the paired run but no text for it.
   - Task 5 changed no file. Its results are in the body of an empty commit on the branch, so
     the squash message carries them.

## Testing strategy

`plugins/my/tests/test_link_check.py`, run with the suite: `cd plugins/my && python3 -m unittest
discover tests`. Each test builds a throwaway git repo on `main` in a temporary folder, with git
running without the user's or the system's config, and runs the real script as a subprocess, as
`test_status_scan.py` does. So every test exercises the command line end to end. Task 5
rehearses both skills headless in a scratch project.

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `cd plugins/my && python3 -m unittest discover tests`

## Files

- Create: `plugins/my/bin/link-check.py` (executable), `plugins/my/tests/test_link_check.py`.
- Modify: `plugins/my/skills/roadmap-management/SKILL.md`,
  `plugins/my/skills/changelog-management/SKILL.md`, `README.md`.
- At the `done` step: `ROADMAP.md` (row 51), `CHANGELOG.md` (the entry).

## Tasks

Run in a worktree of `claude-setup`. Commit type `feat`, scope `my-plugin`.

### Task 1: tests (Red)

File: `plugins/my/tests/test_link_check.py`, one `unittest.TestCase` class.

Helpers, no bodies here, as in `test_status_scan.py`: `clean_env(extra={}) -> dict`,
`git(repo, *args, check=True) -> str`, `make_repo(tmp) -> Path` (git init on `main`, user set,
one root commit), `write(repo, path, text) -> Path`, `commit(repo, message) -> None` (adds all
and commits), `run(cwd, *files, env=None) -> CompletedProcess` (runs `bin/link-check.py` with
`sys.executable`; `env` adds to `clean_env()`).

```python
# Exit codes
def test_clean_file_prints_nothing(self):
    # ROADMAP.md links docs/a.md, which exists and is committed
    r = run(repo, "ROADMAP.md")
    assert r.returncode == 0 and r.stdout == ""

def test_problems_exit_1(self):
    # uncommitted ROADMAP.md links docs/gone.md
    assert run(repo, "ROADMAP.md").returncode == 1

def test_only_old_problems_exit_1(self):
    # the dead link is committed; no edit since
    r = run(repo, "ROADMAP.md")
    assert r.returncode == 1 and r.stdout.endswith("\told\n")

def test_no_args_exit_2(self):
    assert run(repo).returncode == 2

def test_unreadable_file_exit_2(self):
    r = run(repo, "missing.md")
    assert r.returncode == 2 and r.stderr.startswith("link-check.py:")

def test_unreadable_file_others_still_checked(self):
    # ROADMAP.md links docs/gone.md; missing.md does not exist
    r = run(repo, "missing.md", "ROADMAP.md")
    assert r.returncode == 2 and r.stdout.startswith("dead\tROADMAP.md:")

def test_git_failure_exit_2(self):
    # a stub `git` first on PATH exits 1 for `diff`; ROADMAP.md is committed with a dead link
    r = run(repo, "ROADMAP.md", env={"PATH": stub_dir + ":" + path})
    assert r.returncode == 2 and "\tnew\n" not in r.stdout

def test_help_exit_0(self):
    r = run(repo, "--help")
    assert r.returncode == 0 and "Usage:" in r.stdout

# Kinds
def test_html_reported(self):
    # line 3: [x](docs/a.html); docs/a.md and docs/a.html exist
    assert run(repo, "ROADMAP.md").stdout == "html\tROADMAP.md:3\tdocs/a.html\tnew\n"

def test_html_without_md_twin_ok(self):
    # [x](assets/page.html); assets/page.html exists, no assets/page.md
    assert run(repo, "ROADMAP.md").stdout == ""

def test_html_without_twin_or_file_is_dead(self):
    # [x](docs/gone.html); neither docs/gone.html nor docs/gone.md exists
    assert run(repo, "ROADMAP.md").stdout.startswith("dead\t")

def test_climbs_outside_repo_reported(self):
    # [x](../other/README.md)
    assert run(repo, "ROADMAP.md").stdout.startswith("climbs\tROADMAP.md:")

def test_parent_link_inside_repo_ok(self):
    # docs/plans/x.md links ../../ROADMAP.md
    assert run(repo, "docs/plans/x.md").stdout == ""

def test_dead_reported(self):
    assert run(repo, "ROADMAP.md").stdout == "dead\tROADMAP.md:1\tdocs/gone.md\tnew\n"

def test_ignored_file_is_dead(self):
    # .gitignore holds "secret/"; secret/x.md exists on disk
    assert run(repo, "ROADMAP.md").stdout.startswith("dead\t")

def test_tracked_but_ignored_pattern_ok(self):
    # secret/x.md added with git add -f and committed
    assert run(repo, "ROADMAP.md").stdout == ""

def test_untracked_file_ok(self):
    # docs/new-spec.md exists, never added
    assert run(repo, "ROADMAP.md").stdout == ""

def test_symlink_inside_repo_not_climbs(self):
    # docs/out.md is a symlink to a file outside the repo
    assert run(repo, "ROADMAP.md").stdout == ""

def test_file_through_symlinked_folder_not_climbs(self):
    # link_dir is a symlink to repo; ROADMAP.md links docs/a.md, which exists
    assert run(tmp, str(link_dir / "ROADMAP.md")).stdout == ""

def test_one_problem_per_link(self):
    # [x](docs/a.html): docs/a.md exists, docs/a.html does not
    assert run(repo, "ROADMAP.md").stdout.splitlines() == ["html\tROADMAP.md:1\tdocs/a.html\tnew"]

# What is a link
def test_scheme_and_anchor_skipped(self):
    # https://x/y.html, mailto:a@b, #section
    assert run(repo, "ROADMAP.md").stdout == ""

def test_fragment_and_query_stripped(self):
    # docs/a.md#part and docs/a.md?x=1, docs/a.md exists
    assert run(repo, "ROADMAP.md").stdout == ""

def test_percent_decoded(self):
    # docs/a%20b.md, "docs/a b.md" exists
    assert run(repo, "ROADMAP.md").stdout == ""

def test_image_checked(self):
    # ![logo](img/gone.png)
    assert "\timg/gone.png\t" in run(repo, "ROADMAP.md").stdout

def test_reference_definition_checked(self):
    # line 5: [spec]: docs/gone.md
    assert "ROADMAP.md:5\tdocs/gone.md" in run(repo, "ROADMAP.md").stdout

def test_angle_brackets_and_title_removed(self):
    # [x](<docs/a.md> "Title"), docs/a.md exists
    assert run(repo, "ROADMAP.md").stdout == ""

def test_link_over_two_lines_reports_target_line(self):
    # line 2: "[spec of", line 3: "thing](docs/gone.md)"
    assert run(repo, "ROADMAP.md").stdout.startswith("dead\tROADMAP.md:3\t")

# Code
def test_fence_backticks_ignored(self):
    assert run(repo, "ROADMAP.md").stdout == ""   # dead link inside a ``` block

def test_fence_tildes_ignored(self):
    assert run(repo, "ROADMAP.md").stdout == ""   # dead link inside a ~~~ block

def test_code_span_ignored(self):
    assert run(repo, "ROADMAP.md").stdout == ""   # `[x](docs/gone.md)`

def test_indented_line_still_checked(self):
    # "    [x](docs/gone.md)" in a list continuation
    assert run(repo, "ROADMAP.md").stdout.startswith("dead\t")

# new / old
def test_committed_line_is_old(self):
    assert run(repo, "ROADMAP.md").stdout.endswith("\told\n")

def test_other_line_of_edited_row_is_old(self):
    # a committed two-line row; line 1 edited, the dead link on line 2 untouched
    assert run(repo, "ROADMAP.md").stdout == "dead\tROADMAP.md:2\tdocs/gone.md\told\n"

def test_unstaged_edit_is_new(self):
    # committed clean, then a dead link appended, not staged
    assert run(repo, "ROADMAP.md").stdout.endswith("\tnew\n")

def test_staged_edit_is_new(self):
    # the same, then git add ROADMAP.md
    assert run(repo, "ROADMAP.md").stdout.endswith("\tnew\n")

def test_untracked_file_all_new(self):
    assert run(repo, "NOTES.md").stdout.endswith("\tnew\n")

def test_outside_git_all_new(self):
    # a plain temporary folder, no git init
    assert run(folder, "ROADMAP.md").stdout.endswith("\tnew\n")

def test_repo_without_commit_all_new(self):
    # git init, ROADMAP.md added but never committed
    assert run(repo, "ROADMAP.md").stdout.endswith("\tnew\n")
```

Each test must fail first because the script does not exist.

### Task 2: the script (Green)

File: `plugins/my/bin/link-check.py`, executable, with a docstring holding a Usage block, the
output format of D6 and the exit codes, in the style of `status-scan.py`.

Functions: `blank_code(text) -> str` (D2), `links(text) -> list[tuple[int, str]]` (line and
target, D2 and D3), `repo_root(folder) -> str` (D4), `kind(target, base, root, ignored) ->
str | None` (D4, with the `.md` twin rule), `new_lines(path) -> set[int] | None` (D5; `None` means every line is new),
`check(path) -> list[tuple]`, `main(argv) -> int`.

All Task 1 tests pass. Run the whole suite.

### Task 3: the skills

Files: `plugins/my/skills/roadmap-management/SKILL.md` and
`plugins/my/skills/changelog-management/SKILL.md`, rules 9 and 10 of each, as D7 says. Then:

- `git grep -n "full-file link greps" -- plugins` prints nothing.
- `git grep -n "link-resolution greps" -- plugins` prints nothing.
- `git grep -n "link-check.py" -- plugins/my/skills` prints at least one line in each skill.
- `markdownlint-cli2` gives no changed file more errors than on `main` (Risk 7).

### Task 4: `README.md`

One sentence in the `plugins/my/bin/` paragraph, after `ds-count.py`: `link-check.py`, in the
same folder, lists bad links in `ROADMAP.md` and `CHANGELOG.md` and marks the ones on lines the
current edit changed; both skills run it after each edit, before the commit; its tests run with
the same command.

### Task 5: rehearsal

No repo change.

1. Run `link-check.py` on the 15 files from Context. Pass: it reports the 5 links from the table
   there, all `old`, and not `webext`'s link to its HTML draft. The ignore check may find more `dead` links than that probe did; check
   each other line by hand: a real problem is listed in the commit message, a false one is a
   bug to fix. Time the run on `real-estate-webapp/CHANGELOG.md`: under one second.
2. Make a scratch git repo with a committed `ROADMAP.md` that holds one `.html` link to
   `docs/a.html`, with `docs/a.md` present. The file has no `## Order of work` section, and its
   one row follows `roadmap-management` rule 11's order, so neither rule 1 nor rule 3 asks a
   question: `claude -p` cannot answer one. Run
   `claude -p "/my:roadmap-management add a row: test the link check, linking docs/plans/gone.md"`
   headless with `--add-dir <scratch dir> --add-dir <plugin dir>`. Pass: the session ran
   `link-check.py`, fixed or questioned the new dead link, and listed the old `.html` link
   without changing it.

Record both results in the squash commit message.

## Open questions

None.
