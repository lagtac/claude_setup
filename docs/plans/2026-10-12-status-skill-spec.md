# Spec: `my:status`, where we are, what is next, and what can run in parallel

**Status:** done, 2026-10-12. Shipped in c4d3832. End-of-branch checks:
`python3 -m unittest discover plugins/my/tests`, 85 passed, 0 failed. Known
limits are in the Risk section, items 7 and 8.

## How to read this spec

1. `global/rules/docs-layout.md`, sections "From report to roadmap", "Status line" and "One
   feature, four commits on `main`". They say where the state of work is kept: the roadmap's
   order, the status line of each document, and the steps of a feature.
2. `plugins/my/skills/roadmap-management/SKILL.md`, section "Status legend" and rules 3 and 12.
   The legend gives the roadmap icons. Rule 12 defines the `## Order of work` section, and rule 3
   says only the user decides a row's place in it.
3. `docs/plans/2026-10-12-parallel-auto-runs-spec.md`, sections "Out of scope" and D1 to D6. The
   "Parallel runs" section of a project's `CLAUDE.md`, the run cap, `handoff-state.py live`, and
   the fold refusal. Its "Out of scope" gave the question "what can we do in parallel?" to a later
   `my:roadmap-management` spec; this spec takes that question instead (D1).
4. `plugins/my/bin/handoff-state.py` and `plugins/my/tests/test_handoff_state.py`. The run state
   files, and the test style the new tests copy.
5. `plugins/my/skills/handoff/SKILL.md`. The commands the report suggests.
6. `global/CLAUDE.md`, section "Assessing branch redundancy". The rule the branch check follows.
7. `ROADMAP.md` of this repo (bullet rows, no order section) and of `grispy2-web-ext` (numbered
   table rows, with an order section). The two formats the script reads.

## Context

The user starts most sessions with "where are we", "what is next" or "what can be done in
parallel". Each time, the session collects the answer by hand from five places: the roadmap,
the status lines in `docs/plans/`, git worktrees and branches, `fixup!` commits on `main`, and
the state files of `my:handoff auto` runs. The answers differ from session to session, and two
mistakes repeat:

- `git branch --no-merged main` lists every squash-merged branch as unfinished. In this repo it
  lists 18 branches on 2026-10-12, and almost all of them are on `main` already.
- "What can run in parallel" is answered by feel. Nothing checks that two items touch different
  files, or that the project allows a second auto run.

## Goal

1. One read-only skill, `my:status`, answers the three questions in one short report.
2. A script collects the facts the same way every time, and has unit tests.
3. The report never suggests two items to run together when they share a code file, when the
   order of work gates one behind the other, or when the project does not allow a second auto
   run.
4. A squash-merged branch is not reported as unfinished.

## Out of scope

- Writing anything: no roadmap edit, no status change, no commit, no session start. The report
  names commands; the user runs them.
- Deciding an order of work. The order stays the user's decision (`roadmap-management` rule 3).
- Reading issue trackers, merge requests, or other repos.
- A session-start hook that runs the skill by itself.

## Decisions

**D1: A new skill, not a part of `my:roadmap-management`.** `my:roadmap-management` edits
`ROADMAP.md`; a status report writes nothing and reads much more than the roadmap. The parallel
auto runs spec gave this question to `my:roadmap-management` in its "Out of scope". Task 5
changes that line to point here. The user chose this on 2026-10-12.

**D2: A script collects the facts, the skill judges.** `plugins/my/bin/status-scan.py` prints
facts. `SKILL.md` decides what is next and what can run together. The judgment stays in the
skill because order edges and spec "Files" sections are prose, and a script would guess wrong
about them. Rejected: a prompt-only skill (results vary, nothing to test) and a script that also
judges (see the reason above).

**D3: The script's output.** Python standard library only. It writes nothing. It runs from any
folder inside the repo or one of its worktrees. "`main`" below means the branch checked out in
the main checkout, as in `handoff-state.py`.

The output is plain text in blocks. Each block starts with a line `== <name>`. Each fact is one
line, with fields separated by one tab. An empty block prints one line, `none`. The blocks come
in this order:

| Block | One line per | Fields |
| --- | --- | --- |
| `roadmap` | roadmap row whose icon is not ✅ | icon, row number or `-`, bold title, every `docs/plans/` path linked in the row (space-separated) or `-`, the row's whole text on one line |
| `order` | line of the `## Order of work` section, copied as it is | the line |
| `docs` | file in `docs/plans/` or `docs/reports/` whose status is `draft`, `approved`, `planned`, `current` or `parked`, or that has no status line | status or `no-status`, date or `-`, path |
| `checkout` | uncommitted path in the main checkout, then `fixup!` commit on `main` | `dirty`, path; or `fixup`, fixup hash, target hash or `?`, target subject |
| `worktrees` | worktree other than the main checkout | path, branch, commits ahead of `main`, `clean` or `dirty` |
| `runs` | auto run whose `next` is not `finished` | slug, slot or `-`, `next`, stop line or `-`, branch |
| `branches` | branch D4 reports, then one line `skipped` with a count when the cap applies | `maybe-unfinished`, branch, missing line count, subject of its last commit |

Rows are read in two formats. A bullet row is `- <icon> **<title>** …` and may continue on
indented lines. A table row is `| <number> | **<title>** … | <icon> | … |`. Any other line is
skipped. `fixup!` commits are searched in the last 200 commits of `main`. A target is the
nearest older commit whose subject equals the fixup subject with every `fixup!` prefix and the space after it removed;
when none is found, the target hash is `?`.

The `runs` block runs `handoff-state.py live` from the script's own folder. When that exits 2
(the subcommand does not exist yet), the script reads every
`<git common dir>/my-handoff/*.json` file itself and prints the same five fields in the same
order as `live` (the parallel auto runs spec, D3). Today's state files have no slot, so the
fallback prints `-` for it. The parallel auto runs spec adds `live`; this spec does not wait for
it.

When a block's source cannot be read, for example a state file that is not valid JSON or a
`git` command that fails, the block prints one line `error`, tab, the reason, and the script goes
on with the next block. A missing `ROADMAP.md` is not an error: the `roadmap` and `order` blocks
print `none`.

Exit codes: `0` when every block printed, including `error` lines; `2` when the current folder
is not inside a git repository, or when no branch is checked out in the main checkout.

**D4: The branch check.** A local branch is a candidate when it is not `main`, no worktree has it
checked out, and it has commits that `main` does not have. The check runs on the 30 candidates
with the newest last commit. The rest are counted in the `skipped` line.

For each candidate, the script takes the lines that `git diff main...<branch>` adds and the
lines it deletes. It strips spaces at both ends, and keeps lines of 8 or more characters. It
then reads `git log -p <merge-base>..main` once, and collects the lines that commits on `main`
added and deleted since the branch split off, stripped the same way. A branch is
`maybe-unfinished` when a kept added line is not among `main`'s added lines, or a kept deleted
line is not among `main`'s deleted lines; the field is the number of such lines. A branch with
none is not printed.

The test asks "did `main` ever make this change", not "does `main` look like this today". So a
squash-merge followed by more edits to the same files still counts as merged. On this repo on
2026-10-12, 17 of the 18 old branches pass this test; the one left has 1 missing line out of 8.
Rejected: comparing with `main`'s current files (the first draft of this spec). The spec review
ran it on this repo, and 17 of 18 branches failed, because `main` kept editing those files after
each merge. Rejected: one `git grep` per added line over all of `main` (too slow for 30
branches).

**D5: What the skill does.** It starts on "where are we", "what is next", "what can be done in
parallel", "status", or `/my:status`. It runs `status-scan.py` once. For each
`maybe-unfinished` branch, it picks two or three concrete names from the branch's diff (a
function, a file name, a string) and `git grep`s them on `main`, as "Assessing branch
redundancy" in `global/CLAUDE.md` asks. It reads the "Parallel runs" section of the project's
`CLAUDE.md` or `CLAUDE.local.md`, if there is one, and the file list of each item it
compares (D6, section 3). It changes nothing.

A row's linked `docs/plans/` path counts as the row's spec only when the skill confirms that the
spec is about that row: its title or Goal names the same change. Otherwise the row has no spec
of its own, and the link is only a reference. Example: the "Deny list has no effect" row in this
repo links the auto run spec, where the problem was found.

A row whose text says it waits for something ("Waits for …", "Blocked by row N", "after …") is
gated, as if the order of work said so.

**D6: The report.** Chat text, three sections, always in this order:

1. **Where we are.** Items that need the user come first: a stopped auto run with its stop line,
   a `draft` spec waiting for review, `fixup!` commits on `main`, uncommitted paths in the main
   checkout, and a branch that is still unfinished after the `git grep` check. Then one line per
   item in progress: a run whose `next` is not `finished`, a worktree, an `approved` or
   `current` document, a 🚧 row. Last, when there are `no-status` files, one line with their
   count, such as "20 files in `docs/plans/` have no status line"; they are not listed one by
   one, and they do not count as needing the user. Each line names the stage (spec, plan, code, review, merge or fold) and its
   evidence, such as "worktree `feat/x`, 4 commits ahead, clean".
2. **What is next.** At most three items, each with the exact command to run. First what is
   started and stopped: a stopped run (`/my:handoff auto resume <spec>`), a pending fold
   (`git-fold-fixups.py`). Then the first rows of the `## Order of work` that nothing gates.
   Without that section: 🚧 rows, then 📋 rows, in roadmap order, and the report says it used
   roadmap order because no order was given. A row with no spec gets "write its spec" as its
   command (`superpowers:brainstorming`).
3. **What can run in parallel.** Two items may run together only when all three remaining conditions hold:
   - the order of work does not gate one behind the other;
   - their file lists share no path outside the docs paths;
   - (Removed after shipping, on 2026-10-12.) This condition read: neither touches a
     resource listed under **Shared resources** in "Parallel runs". Now a shared resource
     does not stop a pair, because runs take turns on it under its lock. The exception:
     an item whose file list holds a file that a **Shared resources** command names or
     runs does not pair. The skill's "What can run in parallel" holds the current rule;
     see `CHANGELOG.md`;
   - runs whose `next` is not `finished`, stopped ones included, plus new runs stay within
     **Max runs**, as in the parallel auto runs spec's D3.

   Docs paths and **Max runs** come from "Parallel runs", with the defaults of that spec's D1
   (`docs/`, `ROADMAP.md`, `CHANGELOG.md`; 2). An item's file list comes from the first of
   these that exists: for a started branch, `git diff --name-only main...<branch>`; else the
   plan's "Files to Modify/Create" section; else the spec's "Files" section. An item with none
   of these has unknown overlap and is never listed as safe. Without a "Parallel runs" section,
   the report allows one auto run and offers the second item as a supervised session, because
   the parallel auto runs spec's D3 refuses a second auto run there. When a fold is pending and
   a run's `next` is not `finished`, the report says to fold before starting more runs (that spec's D6).

When nothing is open, the report is one line: "Nothing in progress. Next: …".

## Trade-offs

- **Script + skill against prompt only.** The script adds one file and its tests. In return, the
  facts are the same in every session, and the branch check cannot be skipped.
- **Line test against `git grep` per name.** The script cannot pick good names, so it uses a
  mechanical test on added and deleted lines that can err both ways (Risks 1 and 2). The skill's `git grep` runs only on the few
  branches the script lists, so it stays fast.
- **Overlap from the real diff where there is one.** A started branch has a real diff, which
  beats any list written before the code. A waiting row has only its plan or spec. Mixing the
  sources means two items may be compared on lists of different quality. Unknown overlap is
  reported as unknown, so the rule errs toward running fewer things at once.

## Dependencies

None. Python standard library and git. `handoff-state.py live` is used when it exists (D3).

## Risk

1. **A branch can look merged when it is not.** This happens when `main` made the same line
   changes on its own since the branch split off, for example two branches that apply one fix.
   That branch stays hidden. The 8-character minimum lowers the chance. Detection: none in the
   report; `git log main..<branch>` still shows it.
2. **A merged branch can look unfinished** when the squash commit differs from the branch, for
   example a line fixed during the merge. The skill's `git grep` check (D5) then clears it, at
   the cost of a few seconds.
3. **Overlap is judged from prose for items not started.** An old spec or plan may list files
   loosely, and a gate in a row's text is read by the model, not the script. The rule "unknown is
   never safe" limits the harm to fewer suggestions.
4. **Two sources for runs.** Until the parallel auto runs spec ships `live`, the script reads the
   state files itself and prints `-` for the slot. Both print the five fields of that spec's D3.
   If that spec changes the fields of `live` before it ships, the fallback must change too; the
   fallback test then fails, which shows it.
5. **Speed.** Thirty branches with large diffs, each with one `git log -p` since its merge-base,
   may take seconds. The cap and the `skipped` line
   bound it.
6. **Task 5 edits another approved spec.** If the parallel auto runs plan stage edits the same
   "Out of scope" line at the same time, the squash-merge conflicts. The edit is one line, so
   the merge stage resolves it by hand or stops.
7. **Known limits from the end-of-branch reviews.** None of these inputs exists in the repos
   checked on 2026-10-12, so they are recorded, not fixed:
   - A branch with no comparable lines (only binary files, renames, mode changes or lines under
     8 characters) gets a missing count of 0 and is not printed. Listing it would change D4.
   - A state file that is valid JSON but not an object (`null`, `[]`) stops the script with
     exit 1 in the fallback reader, and the blocks after `runs` do not print.
   - `HERE` does not follow symlinks, and every exit 2 from `handoff-state.py` reads as "no
     `live` yet". If `status-scan.py` is ever linked from another folder, it uses the fallback
     reader for good.
   - The fixup scan matches targets on its own. Unlike `git-fold-fixups.py`, it lists pushed
     fixups, and it picks the nearest target when two commits share a subject, where the fold
     refuses.
   - One `rev-list --count` runs per local branch before the cap of 30 applies, and the
     worktree list and `ROADMAP.md` are read twice. Merged branches are kept, so this grows.
   - A worktree whose folder exists but where `git` fails turns the whole `worktrees` block into
     one `error` line.
   - The rehearsal (Task 4) suggested `git-fold-fixups.py` while worktrees held branches on top
     of the fixup targets, so that fold would refuse. The skill does not check for that.
8. **Known limits from the final re-reviews.** The one-fix-round rule sends these here, not into
   a second fix. The first two happen on today's input and are the first candidates for a
   follow-up:
   - The skill's `git grep` check (step 2) can clear an unfinished branch. It may pick a name
     that `main` already had, such as an edited function, or a name from the `-` lines. For a
     branch with no shared history, the two-dot diff's `-` lines are mostly `main`'s own later
     work. Names should come only from added lines that `main` lacked at the merge base.
   - The overlap check (step 6) uses a started branch's committed diff alone. It misses
     uncommitted edits in the worktree, and the plan's files not yet touched, so it can call two
     items safe that overlap.
   - Step 3 says **Max runs** defaults to 2, while step 6 allows one auto run when there is no
     "Parallel runs" section. The default of 2 applies only when the section exists.
   - D4 does not describe the fallback for a branch with no shared history (compare with the
     whole history of `main`); only the code and its comment do.
   - The base branch goes to `git log` bare. A top-level path with the same name makes the
     `checkout` block, or the `branches` block when a branch shares no history, one `error`
     line.
   - In a repo made with `--separate-git-dir`, or in a submodule, the script stops with a
     traceback instead of exit 2.
   - The patch log is cached per fork commit, so many forks mean many overlapping logs.
   - A `#` line inside a code fence in `## Order of work` ends the section early.
   - The fallback runs reader prints JSON `null` as `None`, and a stop line with a newline
     splits one row in two.
   - No test covers the `live` path of `run_facts`, which does not exist on `main` yet.

## Testing

Unit tests in `plugins/my/tests/test_status_scan.py`, in the style of `test_handoff_state.py`: a
throwaway repo per test, git run without the user's or the system's config, the script run as a
subprocess. Run with `cd plugins/my && python3 -m unittest discover tests`.

The skill's judgment has no unit test. One headless rehearsal on this repo (Task 4) checks the
three sections and that no squash-merged branch shows as unfinished.

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `python3 -m unittest discover plugins/my/tests`

## Files

- New: `plugins/my/bin/status-scan.py`
- New: `plugins/my/tests/test_status_scan.py`
- New: `plugins/my/skills/status/SKILL.md`
- Edit: `README.md` (the skills list and the `plugins/my/bin/` paragraph)
- Edit: `docs/plans/2026-10-12-parallel-auto-runs-spec.md` (one line in "Out of scope", Task 5)

## Tasks

Run in a worktree of `claude-setup`. Commit type `feat`, scope `my-plugin`.

### Task 1: tests (Red)

File: `plugins/my/tests/test_status_scan.py`.

Helpers, no bodies here: `clean_env() -> dict` (as in `test_handoff_state.py`),
`make_repo(tmp) -> Path` (git init on `main`, user set, one root commit),
`commit(repo, subject, files={}) -> str` (writes the files, returns the hash),
`run(cwd, *args) -> CompletedProcess`, `block(stdout, name) -> list[list[str]]` (the lines of one
block, split on tabs; `[]` for `none`).

```python
def test_bullet_rows_skip_shipped(self):
    # ROADMAP.md: "- 💭 **A** — x", "- ✅ **B** — y", "- 📋 **C** — [spec](docs/plans/c-spec.md)"
    rows = block(out, "roadmap")
    assert [r[:4] for r in rows] == [["💭", "-", "A", "-"],
                                     ["📋", "-", "C", "docs/plans/c-spec.md"]]
    assert rows[0][4] == "- 💭 **A** — x"

def test_table_rows_keep_number(self):
    # "| 3 | **Choose** — y. Waits for row 1. | 🚧 | — |"
    rows = block(out, "roadmap")
    assert [r[:4] for r in rows] == [["🚧", "3", "Choose", "-"]]
    assert "Waits for row 1." in rows[0][4]

def test_bullet_row_continuation_joined(self):
    # "- 💭 **A** — first line" then "  Waits for B."
    assert block(out, "roadmap")[0][4] == "- 💭 **A** — first line Waits for B."

def test_order_copied_or_none(self):
    assert block(out_with, "order") == [["- **1 and 2, then 3.** reason"]]
    assert "== order\nnone" in out_without

def test_docs_status_filter(self):
    # draft spec, done spec, review file, file without a status line
    assert block(out, "docs") == [["draft", "2026-10-12", "docs/plans/a-spec.md"],
                                  ["no-status", "-", "docs/plans/c.md"]]

def test_fixup_lists_target(self):
    # "docs: spec" then "fixup! docs: spec" on main
    assert block(out, "checkout") == [["fixup", fixup, spec, "docs: spec"]]

def test_dirty_path_listed(self):
    assert ["dirty", "notes.md"] in block(out, "checkout")

def test_worktree_ahead_and_dirty(self):
    # worktree feat/x, 2 commits, one uncommitted edit
    assert block(out, "worktrees") == [[str(wt), "feat/x", "2", "dirty"]]

def test_squash_merged_branch_hidden(self):
    # feat/y adds lines; main gets the same content in one squash commit
    assert block(out, "branches") == []

def test_squash_merged_then_edited_hidden(self):
    # as above, then a later commit on main rewrites the merged lines
    assert block(out, "branches") == []

def test_delete_only_branch_listed(self):
    # feat/d only deletes two long lines that main still has
    assert block(out, "branches") == [["maybe-unfinished", "feat/d", "2", "feat: d"]]

def test_unmerged_branch_listed(self):
    # feat/z adds two lines main does not have
    assert block(out, "branches") == [["maybe-unfinished", "feat/z", "2", "feat: z"]]

def test_short_lines_ignored(self):
    # feat/s adds only "}" and "return", lines main does not have
    assert block(out, "branches") == []

def test_branch_cap(self):
    # 31 unmerged branches
    rows = block(out, "branches")
    assert len(rows) == 31 and rows[-1] == ["skipped", "1"]

def test_runs_fallback_hides_finished(self):
    # my-handoff/a.json next=code, b.json next=finished
    assert block(out, "runs") == [["a", "-", "code", "-", "feat/a"]]

def test_bad_state_file_is_error_line(self):
    # my-handoff/c.json holds "{not json"
    r = run(repo)
    assert r.returncode == 0 and block(r.stdout, "runs")[0][0] == "error"

def test_missing_roadmap_is_none(self):
    assert "== roadmap\nnone" in out and "== order\nnone" in out

def test_outside_repo_exits_2(self):
    assert run(tmp).returncode == 2
```

Each test must fail first because the script does not exist.

### Task 2: the script (Green)

File: `plugins/my/bin/status-scan.py`, executable, docstring with a Usage block in the style of
`handoff-state.py`.

Functions: `git(*args, cwd=None) -> str`, `base_branch() -> str`,
`roadmap_rows(text) -> list[tuple]`, `order_lines(text) -> list[str]`,
`doc_states(root) -> list[tuple]`, `checkout_facts() -> list[tuple]`,
`worktree_facts() -> list[tuple]`, `run_facts() -> list[tuple]`,
`branch_facts(limit=30) -> list[tuple]`, `print_block(name, rows)`, `main(argv) -> int`.

All Task 1 tests pass. Run the whole suite.

### Task 3: the skill

File: `plugins/my/skills/status/SKILL.md`. Frontmatter `name: status` and a `description` that
names the trigger phrases of D5 and says "NOT for editing the roadmap
(`my:roadmap-management`)". Body: D5 and D6 as steps, the report format with one short example,
and the rule that it writes nothing. The script is called by its bare name, `status-scan.py`,
because the plugin's `bin/` folder is on `PATH`, as `my:handoff` calls `handoff-state.py`.

### Task 4: rehearsal

No repo change. Run the skill headless on this repo:
`claude -p "/my:status" --add-dir <scratch dir> --add-dir <plugin dir>`. `claude -p` needs both
folders added, or it cannot read them; a refused tool call may not show in `permission_denials`,
so read the whole output. Pass: the three sections appear, every
branch in "Where we are" survives a manual `git grep` check, and no command in the report
writes. Record the result in the squash commit message.

### Task 5: docs

- `README.md`: one line for `my:status` in the skills list, and one sentence for
  `status-scan.py` in the `plugins/my/bin/` paragraph.
- `docs/plans/2026-10-12-parallel-auto-runs-spec.md`, "Out of scope", first bullet: replace "A
  later spec for `my:roadmap-management`. Until then the user picks the specs." with "Answered by
  `my:status` ([spec](2026-10-12-status-skill-spec.md)); the auto runs still start only when the
  user starts them."

## Open questions

None.
