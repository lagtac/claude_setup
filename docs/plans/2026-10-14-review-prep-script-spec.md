# Spec: `review-prep.py`, review preparation as a script

**Status:** draft, 2026-10-14. Drafted in a fork without the user; the choices
it made alone are listed under "Choices made without the user", and it waits for
the user's reading and `my:spec-review`.

## How to read this spec

1. `docs/reports/2026-10-14-scriptable-skill-steps.md`, sections "How to read
   this" (the test for a step that can be a script), "S5" and "Where scripts go,
   and the cost". Where this work comes from.
2. `ROADMAP.md`, row 45 "Review preparation as a script", and the section "Order
   of work". Row 8 edits the same `my:spec-review` file and goes after this row.
3. `plugins/my/skills/soundness-review/SKILL.md`. Steps 0 to 2 (lines 28 to 237)
   are the prose the script replaces. Steps 3 and 4 stay.
4. `plugins/my/skills/soundness-review/code-reviewer-prompt.md`. The template
   the script fills. Its header (lines 1 to 17) lists the placeholders.
5. `plugins/my/skills/spec-review/SKILL.md`. Steps 0 to 2 (lines 24 to 57) are
   the prose the script replaces. Steps 3 to 5 stay.
6. `plugins/my/skills/spec-review/spec-reviewer-prompt.md`. The second template.
   Its header (lines 1 to 15) lists the placeholders.
7. `plugins/my/agents/code-reviewer.md` and
   `plugins/my/agents/spec-reviewer.md`. The two reviewer agents. D6 changes
   what their input is.
8. `plugins/my/bin/locked-commit.py`, `plugins/my/bin/git-fold-fixups.py` and
   `plugins/my/tests/test_locked_commit.py`. The style the new script and its
   tests copy: docstring with `Usage:` and `Exit codes:`, no `argparse`, a
   throwaway repository per test.
9. `plugins/my/skills/handoff/SKILL.md` lines 523 to 528. A caller that depends
   on the review file name rule. This spec keeps that rule, so the file does not
   change.
10. `docs/plans/2026-10-12-locked-commit-spec.md`. The model for this spec's
    layout, and the precedent for reading input from a file instead of a shell
    argument.

## Context

`my:soundness-review` and `my:spec-review` run at the end of every branch and
for every spec. Before each one dispatches its reviewer subagent, the session
works through fixed rules by hand:

- **Sorting the arguments.** `my:soundness-review` step 0 (lines 28 to 55)
  splits the args string and sorts each token by a 5-row table, prints three
  kinds of notes, and checks four mixed-argument cases for `--plan-only`.
  `my:spec-review` step 0 (lines 24 to 32) checks for exactly one existing path.
- **Writing the subject file.** `my:soundness-review` step 1 (lines 57 to 111)
  makes a work directory, writes the merge-base diff and the commit log, or the
  working-tree diff plus every untracked file as a new-file diff, prints the
  untracked list, and runs a 2000-line size guard. `my:spec-review` step 1
  (lines 34 to 45) copies the spec and runs the same guard.
- **Choosing the mode.** `my:soundness-review` step 1a (lines 113 to 146)
  matches an 8-row table to pick `plan-review`, `diff-review`, `diff-review`
  with alignment, a stop, or a question to the user.
- **Filling the template.** `my:soundness-review` step 2 (lines 148 to 237)
  substitutes nine placeholders, picks one of four quoted blocks for two of
  them, builds a Plan Alignment block, deletes the lines of empty placeholders,
  and names the review file. `my:spec-review` step 2 (lines 47 to 57) does the
  same for five placeholders.
- **Naming the review file.** Both skills add `-2`, `-3` and so on when the name
  is taken. The diff-review name depends on the range, the current branch and
  the repo folder.

All of it takes files, git output and arguments as input, and fixed rules decide
the output. Only two steps need the model: the `AskUserQuestion` call when the
args do not say what to review, and the `Agent` call that dispatches the
reviewer. The report ranks this as the most frequent win of its sixteen findings
(S5).

There is also a cost in tokens. Today the session reads the template (139 or 178
lines), the skill's four quoted blocks, and then writes the whole composed
prompt into the `Agent` call as output. The diff itself already goes through a
file for that reason (soundness step 1, line 59).

**Size: Medium.** It is a feature across several files: one new script, its
tests, one new template file, two skills and two agent files. It changes no
stored data, no permission, no build, and no contract that another skill or a
user depends on: the arguments of both skills, their stop messages and their
review file names stay exactly as they are. D6 changes the input of the two
reviewer agents, but only these two skills dispatch them (README.md lines 191
and 192), and both change in the same branch.

## Goal

1. One script, `plugins/my/bin/review-prep.py`, does steps 0 to 2 of both
   skills: it sorts the arguments, writes the subject file, picks the mode,
   fills the template, names the review file, and prints the result.
2. Every stop message, note and review file name stays word for word as today.
   Unit tests pin each one.
3. The two skills keep only the `AskUserQuestion` call, the `Agent` call and the
   surfacing step. The prose the script replaces is deleted in the same change,
   so no rule exists twice.
4. The session never reads the template and never writes the composed prompt as
   output.

## Out of scope

- The review criteria, the reviewer prompts' rules, and the report layout. The
  script moves text; it does not change what a reviewer is told.
- Row 8 "`my:spec-review` checks Delegation content". It adds review criteria,
  which this spec does not touch.
- `my:handoff`. Its calls to both skills and its use of the review file name
  stay valid. Row 9 holds `plugins/my/skills/handoff/SKILL.md` until it merges,
  so this branch must not edit it.
- Step 4 of both skills (confirm the file, print the pointer, read the verdict).
  It is three short checks after the subagent returns, and the report did not
  list it.
- Deleting old work directories in the scratchpad. Neither skill does that
  today.

## Decisions

### D1. One script with two subcommands

```text
review-prep.py soundness --args-file <file> [--work-root <dir>] [--subject plan|changes]
review-prep.py spec --args-file <file> [--work-root <dir>]
```

`soundness` does steps 0 to 2 of `my:soundness-review`; `spec` does steps 0 to 2
of `my:spec-review`. The parts both need are written once: the work directory,
the size guard, the template body below the first `---` line, the placeholder
filling, and the free review file name. The script finds each template next to
its skill, as `Path(__file__).resolve().parent.parent / "skills" / <skill> /
<template>`. The plugin cache has the same layout as the repo, so the path holds
in both.

### D2. The args string is read from a file

The skill writes its args string, unchanged, to a new file in the session's
scratchpad with the Write tool, then passes `--args-file <file>`. The script
splits it on whitespace, as step 0 does today. With empty args the skill still
writes an empty file, so there is one form of the call.

A shell argument would break on an apostrophe or a backtick in a description.
And skill text must not hold `$1` or `$ARGUMENTS` in a shell line: Claude Code
replaces them with the skill's arguments (rows 33 and 41). The script deletes
the args file when it exits 0 or 1, and keeps it when it exits 3 (D4), because
the rerun reads it again. The file name carries the time, such as
`review-args-<YYYYmmdd-HHMMSS>.txt`, because the Write tool refuses to overwrite
a file it has not read.

### D3. Output: one fact per line, tab-separated

The script prints to stdout, one fact per line, the field name, a tab, the
value. This is the style of `status-scan.py`. The skill reads the lines and
prints every `note` line to the user word for word, in the order they come.

- `note`, on any exit, zero or more lines: one line to print to the user, such
  as the untracked list or `(description ignored: …)`.
- `stop`, on exit 1: the message to print. Nothing is dispatched.
- `mode`, on exit 0: `diff-review`, `plan-review` or `spec-review`.
- `prompt`, on exit 0: the absolute path of the composed prompt,
  `<work dir>/prompt.md`.
- `review`, on exit 0: the repo-relative path of the review file the agent will
  write, after the collision rule.
- `changed`, `untracked` and `plan`, on exit 3: the facts for the question, that
  is the number of changed files, the number of untracked files, and the plan
  path.

### D4. Exit codes

```text
0  ready: prompt.md is written; dispatch it
1  stop: print the stop line; dispatch nothing, write no review
2  usage error: the Usage line is on stderr
3  ask: the args do not say whether to review the plan or the changes
```

Exit 2 for `spec` prints today's line, `Usage: my:spec-review <path/to/spec.md>
— one existing spec file.` For `soundness`, the usage error covers only a broken
call by the skill (no `--args-file`, an unreadable file), because every user
input has a defined stop or note today.

### D5. The question stays in the skill, and the script runs again

On exit 3 the skill asks the question of soundness step 1a (lines 132 to 146)
with `AskUserQuestion`, using `changed`, `untracked` and `plan` from the output.
Then it runs the script again with the same args file and `--subject plan` or
`--subject changes`:

- `--subject plan` follows the `plan-review` row; for a spec it stops with
  today's message.
- `--subject changes` follows the `diff-review` with alignment row.
- When `AskUserQuestion` is not in the tool list, the skill passes `--subject
  changes` and prints today's note `(Working tree is dirty, so I'm reviewing the
  diff against <PLAN_PATH>. …)`.

The rerun captures the diff again. If the tree changed between the two runs, the
review sees the newer tree, which is what the user would expect.

### D6. The reviewer reads the prompt from a file

The `Agent` call's prompt becomes one fixed sentence:

`Your full instructions are in <prompt>. Read the whole file first, then follow
it exactly.`

The session no longer reads the template or writes the composed prompt. Both
agent files change to match. In `code-reviewer.md` line 10 and
`spec-reviewer.md` line 10, "the full review prompt, which is your input"
becomes "the full review prompt, in a file your input names; read it whole
before anything else". The "If the Prompt Is Missing Sections" check then
applies to that file. Without this change, an agent given the one sentence would
stop with "Dispatch prompt is malformed".

### D7. The four quoted blocks move to a template file

Soundness step 2 holds four blocks the script must insert: **Diff criteria**
(lines 182 to 192), **Plan criteria** (194 to 203), **Plan Alignment output**
(205 to 209) and **Grounding output** (211 to 215). They move, without the `>`
quote marks and otherwise unchanged, to a new file
`plugins/my/skills/soundness-review/prompt-blocks.md`, one `## <name>` section
each: `diff-criteria`, `plan-criteria`, `plan-alignment-output`,
`grounding-output`. The script takes a section's body up to the next `##`
heading. The Plan Alignment block that soundness builds (lines 217 to 229) also
moves there as `plan-alignment`, with its two optional lines marked so the
script can drop them.

The header of `code-reviewer-prompt.md` names the new file, so an editor finds
both halves.

### D8. The rules the script keeps exactly

The script is a direct translation of today's rules. In particular:

- The token table of step 0, top to bottom, first match wins, with its three
  notes and the two-plan stop.
- The `--plan-only` checks of lines 46 to 53, after the notes, in that order.
- The range diff from the merge base, and the log appended only when the diff is
  not empty (lines 73 to 85).
- `git diff HEAD`, then every untracked file through `git diff --no-index
  /dev/null <path>` (lines 89 to 104), and the untracked note.
- With `--plan-only`, no diff, no untracked list, and no size guard (line 69).
- The size guard at more than 2000 lines, with its note to the user and its line
  in `{{SUBJECT}}` (lines 108 to 111; spec-review line 45).
- The 8-row mode table of step 1a, top to bottom.
- The review slugs and the `<branch-or-cwd>` rule of step 2 point 4 (line 235),
  with `/` replaced by `-`, and the collision rule (line 180; spec-review line
  57).
- An empty placeholder deletes its whole line and the blank line after it (line
  233).
- `mkdir -p` on `docs/plans/` (line 237; spec-review line 54).
- `--work-root` is the scratchpad. Without it, the script uses
  `tempfile.mkdtemp()`. The work directory is `<work
  root>/<skill>/<YYYYmmdd-HHMMSS>`, with `-2`, `-3` added when two runs start in
  the same second.

The script does not commit, does not dispatch, and writes nothing in the repo
except the `docs/plans/` folder when it is missing.

## Choices made without the user

A fork drafted this spec without the user, so it could not ask. Each line is a
question it would have asked, the answer it picked, and why. A reviewer may
decide any of them differently.

1. **One script with two subcommands, or one script per skill?** One script
   (D1). The shared parts are most of the code, and one test file covers both.
   See Trade-offs.
2. **Pass the args as shell arguments, or in a file?** In a file (D2). Prose in
   a description breaks shell quoting, and the `$1` class of bug (rows 33 and
   41) stays out of skill text. It costs one Write call per review.
3. **Paste the composed prompt into the `Agent` call, or point the reviewer to
   the file?** Point to the file (D6). It removes the session's longest output
   and any chance of copying it wrong, but it changes both agent files. This is
   the choice most open to a different answer.
4. **Leave the four criteria blocks in `SKILL.md`, or move them?** Move them to
   `prompt-blocks.md` (D7). A script that parses quoted blocks out of a skill
   file breaks on any edit to the skill's prose, and the skill no longer loads
   text it does not use.
5. **How does the question work?** Exit 3, then a second run with `--subject`
   (D5). The other way, the script stops halfway and the skill finishes the
   filling, would keep half the prose.
6. **Output as tab-separated lines or JSON?** Tab-separated lines (D3), as
   `status-scan.py` prints. The skill reads a few fields, and every note is one
   line.
7. **Name of the script.** `review-prep.py`. It prepares a review; it does not
   run one.
8. **Keep every message word for word, or reword them in plain style?** Word for
   word (D8). The change is a move, and `my:handoff` reads one of the outputs
   (`Review written to …`). Rewording is a separate change.
9. **Unit tests only, or also a headless rehearsal?** Both (Task 5). The skills
   run at the end of every branch, so a broken skill text would block every
   merge; unit tests do not load the skill.
10. **The size of this change.** Medium (see Context). Large would apply if
    another skill or project depended on the reviewer agents' input, and none
    does.
11. **Keep the placeholder lists in the two template headers?** Yes. They
    document the template for a reader; the script does not read them.

## Trade-offs

**One script or two.**

- **Option A: one script, `review-prep.py`, with `soundness` and `spec`
  subcommands.** Pros: the work directory, the size guard, the template body,
  the filling and the collision rule are written once, and a fix reaches both
  skills. One test file. Cons: a bug in a shared part breaks both reviews at
  once; the script is larger, about 300 lines.
- **Option B: two scripts, `soundness-prep.py` and `spec-prep.py`.** Pros: each
  is small, and a bug stays in one skill. Cons: the shared parts are copied, and
  the collision rule and the size guard already drifted once between the two
  skill texts (soundness puts its size note "after its first sentence",
  spec-review "after its sentence").
- **Recommendation: A.** The shared parts are the larger half, and the tests
  cover both subcommands.

**Prompt in a file or in the call (D6).**

- **Option A: point the reviewer to `prompt.md`.** Pros: the session writes one
  sentence instead of about 200 lines; nothing can change in the copy. Cons:
  both agent files change; a reviewer that skips the read would review nothing.
- **Option B: the session reads `prompt.md` and pastes it.** Pros: the agents do
  not change. Cons: the output cost stays, and the reason the diff already goes
  through a file applies here too.
- **Recommendation: A**, with the rehearsal in Task 5 as the check that the
  reviewers read the file.

## Dependencies

- Python 3 standard library and git. No new package.
- No other row must ship first.
- Row 8 "`my:spec-review` checks Delegation content" edits
  `plugins/my/skills/spec-review/` too. It goes after this row, so it adds its
  criteria to the shorter skill.
- Row 9 "Start auto runs from roadmap rows" is in flight and edits `README.md`
  lines 157 to 165, next to where this row adds a sentence. Row 46
  "`git-squasher` plan and apply scripts" may also add a line to `README.md`.
  See Risk 4.

## Risk

1. **Every review goes through the script.** A bug stops every end-of-branch
   review and every spec review, including the reviews of the branch that would
   fix it. Mitigation: each row of the token table, the `--plan-only` table and
   the mode table has a unit test, and Task 5 rehearses both skills headless
   before the merge. Recovery: `git revert` of the squash commit brings the old
   skill text back in one step.
2. **A rule changes in the move.** The tables are long, and a translation can
   drop a case. Detection: the tests assert each stop and note message word for
   word, taken from the current `SKILL.md` lines that D8 cites, and the slug and
   collision tests use real branch names.
3. **A reviewer does not read the prompt file (D6).** It would then stop with
   "Dispatch prompt is malformed" or write a review with no criteria. Detection:
   Task 5 checks that each review file has the `**Assessment:**` line and, for a
   spec, the System Model tables.
4. **`README.md` conflicts with row 9 and row 46.** Row 9 edits lines 157 to
   165, and this row adds one sentence after line 165. Whichever branch merges
   second resolves a text conflict by hand. The squash-merge shows it; nothing
   breaks silently.
5. **`plugins/my/skills/handoff/SKILL.md` must not change.** Row 9 holds it. Its
   lines 523 to 528 rely on the review file name and the `Review written to …`
   line, which this spec keeps. If the code stage finds it must edit that file,
   it stops and asks.
6. **The installed plugin moves as one piece.** The skills, the agents,
   `prompt-blocks.md` and `bin/review-prep.py` all live in `plugins/my`, so a
   plugin update brings them together. A session that loaded the old skill text
   before the update still runs the old steps, which still work, because the
   templates keep their placeholders.
7. **Line numbers drift.** The numbers here are from `main` at `e0bf1b1`,
   2026-10-14. The code stage finds each section by its heading and text.
8. **The args file is left behind on exit 2 or 3.** It sits in the scratchpad,
   which the session owns, and does no harm.
9. **Lint.** The changed Markdown files gain no `markdownlint-cli2` error. Files
   that already have errors on `main` are not rewrapped.

## Testing

`plugins/my/tests/test_review_prep.py`, run with the whole suite: `cd plugins/my
&& python3 -m unittest discover tests`. Each test builds a throwaway repository
in a temporary directory, without the user's git config, and runs the real
script there as a subprocess, as `test_locked_commit.py` does. Task 5 rehearses
both skills headless in a scratch repository.

## Files

- Create: `plugins/my/bin/review-prep.py` (executable).
- Create: `plugins/my/tests/test_review_prep.py`.
- Create: `plugins/my/skills/soundness-review/prompt-blocks.md`.
- Modify: `plugins/my/skills/soundness-review/SKILL.md` (steps 0 to 2 and the
  worked examples replaced).
- Modify: `plugins/my/skills/soundness-review/code-reviewer-prompt.md` (header
  only: name `prompt-blocks.md` and the script).
- Modify: `plugins/my/skills/spec-review/SKILL.md` (steps 0 to 2 and the worked
  example replaced).
- Modify: `plugins/my/skills/spec-review/spec-reviewer-prompt.md` (header only:
  name the script).
- Modify: `plugins/my/agents/code-reviewer.md`,
  `plugins/my/agents/spec-reviewer.md` (D6).
- Modify: `README.md` (one sentence in the `plugins/my/bin/` paragraph, after
  line 165).

## Tasks

Run in a worktree of `claude-setup`. Commit type `feat`, scope `my-plugin`.

### Task 1: tests (Red)

File: `plugins/my/tests/test_review_prep.py`.

Helpers, no bodies here: `clean_env(extra={}) -> dict` and `git(repo, *args,
check=True) -> str` (as in `test_locked_commit.py`); `make_repo(tmp) -> Path`
(git init on `main`, user set, one root commit, a `docs/plans/` folder with one
plan `2026-01-01-foo.md` and one spec `2026-01-01-foo-spec.md`, both committed);
`run(repo, sub, args_text, *extra) -> CompletedProcess` (writes `args_text` to a
new file in the temporary directory, runs `review-prep.py <sub> --args-file
<file> --work-root <tmp>/work *extra` in `repo`); `fields(stdout) ->
list[tuple[str, str]]` (the lines split on the first tab); `field(stdout, name)
-> str` (the one value of a field); `prompt(stdout) -> str` (the text of the
`prompt` file).

```python
# soundness: argument sorting (step 0)
def test_one_sha_is_description_with_note(self):
    r = run(repo, "soundness", "abc1234")          # tree dirty
    assert ("note", '(arg "abc1234" looks like a commit; treated as description.'
            ' Pass abc1234..HEAD for a range.)') in fields(r.stdout)

def test_two_shas_join_as_range(self):
    # base = short hash of main, tip = short hash of feature-x
    r = run(repo, "soundness", f"{base} {tip}")
    assert r.returncode == 0
    # SUBJECT_NAME is the joined range
    assert f"# Review: {base}..{tip}" in prompt(r.stdout)

def test_md_outside_plans_is_description_with_note(self):
    r = run(repo, "soundness", "README.md")
    assert ("note", '(arg "README.md" treated as description;'
            ' expected an existing plan under docs/plans/.)') in fields(r.stdout)

def test_two_plans_stop(self):
    r = run(repo, "soundness", "docs/plans/2026-01-01-foo.md docs/plans/2026-01-02-bar.md")
    assert r.returncode == 1
    assert field(r.stdout, "stop") == ("Pass one plan file; got docs/plans/2026-01-01-foo.md"
                                       " and docs/plans/2026-01-02-bar.md.")

# soundness: --plan-only checks, messages word for word (SKILL.md lines 50-53)
def test_plan_only_with_range_stops(self):
    r = run(repo, "soundness", "--plan-only main..HEAD docs/plans/2026-01-01-foo.md")
    assert r.returncode == 1
    assert field(r.stdout, "stop") == (
        "--plan-only reviews a plan; it takes no range. Drop one of them.")

def test_plan_only_without_plan_stops(self):
    assert field(run(repo, "soundness", "--plan-only").stdout, "stop") == \
        "--plan-only needs a plan under docs/plans/."

def test_plan_only_with_spec_stops(self):
    r = run(repo, "soundness", "--plan-only docs/plans/2026-01-01-foo-spec.md")
    assert field(r.stdout, "stop") == ("This is a spec. Run my:spec-review"
                                       " docs/plans/2026-01-01-foo-spec.md instead.")

def test_plan_only_on_dirty_tree_is_plan_review_without_payload(self):
    # an untracked file exists
    r = run(repo, "soundness", "--plan-only docs/plans/2026-01-01-foo.md")
    assert r.returncode == 0 and field(r.stdout, "mode") == "plan-review"
    assert not (Path(field(r.stdout, "prompt")).parent / "payload.diff").exists()

def test_plan_only_description_ignored_note(self):
    r = run(repo, "soundness",
            "--plan-only docs/plans/2026-01-01-foo.md check the order")
    assert ("note", "(description ignored: a plan review has no diff"
            " to check it against)") in fields(r.stdout)

# soundness: the subject file (step 1)
def test_range_payload_is_merge_base_diff_then_log(self):
    # branch feature-x diverged from main; main gained a commit after the fork point
    r = run(repo, "soundness", "main..feature-x")
    payload = (Path(field(r.stdout, "prompt")).parent / "payload.diff").read_text()
    mb = git(repo, "merge-base", "main", "feature-x")
    assert payload == (git(repo, "diff", mb, "feature-x") + "\n"
                       "\n--- COMMITS IN RANGE ---\n"
                       + git(repo, "log", "main..feature-x", "--oneline") + "\n")

def test_empty_range_stops(self):
    r = run(repo, "soundness", "main..main")
    assert r.returncode == 1
    assert field(r.stdout, "stop") == "Range main..main is empty."

def test_untracked_files_become_new_file_diffs_with_note(self):
    # new.txt untracked, a.md modified
    r = run(repo, "soundness", "")
    payload = (Path(field(r.stdout, "prompt")).parent / "payload.diff").read_text()
    assert "--- /dev/null\n+++ b/new.txt" in payload
    assert ("note", "(Including 1 untracked files: new.txt. If any do not"
            " belong to this change, add them to .gitignore or move them,"
            " and run again.)") in fields(r.stdout)

def test_size_guard_over_2000_lines(self):
    # an untracked file of 2100 lines
    r = run(repo, "soundness", "")
    notes = [v for k, v in fields(r.stdout) if k == "note"]
    assert any(v.startswith("(Payload is ") for v in notes)
    assert "Note: this payload is " in prompt(r.stdout)

# soundness: the mode table (step 1a), top to bottom
def test_clean_tree_no_args_stops(self):
    assert field(run(repo, "soundness", "").stdout, "stop") == "No changes to review."

def test_clean_tree_description_only_stops_with_extra_line(self):
    r = run(repo, "soundness", "fix the order")
    assert field(r.stdout, "stop") == (
        "No changes to review. (The description was not used:"
        " there are no changes to check it against.)")

def test_clean_tree_spec_stops(self):
    r = run(repo, "soundness", "docs/plans/2026-01-01-foo-spec.md")
    assert field(r.stdout, "stop") == ("This is a spec. Run my:spec-review"
                                       " docs/plans/2026-01-01-foo-spec.md instead.")

def test_clean_tree_plan_is_plan_review(self):
    r = run(repo, "soundness", "docs/plans/2026-01-01-foo.md")
    assert field(r.stdout, "mode") == "plan-review"
    assert field(r.stdout, "review") == "docs/plans/2026-01-01-foo-plan-review.md"
    assert "## Grounding" in prompt(r.stdout) and "## Plan Alignment" not in prompt(r.stdout)

def test_dirty_tree_plan_without_range_asks(self):
    # a.md modified, new.txt untracked
    r = run(repo, "soundness", "docs/plans/2026-01-01-foo.md")
    assert r.returncode == 3
    assert (field(r.stdout, "changed"), field(r.stdout, "untracked")) == ("2", "1")
    assert field(r.stdout, "plan") == "docs/plans/2026-01-01-foo.md"

def test_args_file_kept_on_ask_deleted_on_ready(self):
    # run() returns the args file path on the result object as r.args_file
    assert run(repo, "soundness", "docs/plans/2026-01-01-foo.md").args_file.exists()
    assert not run(repo, "soundness", "--plan-only docs/plans/2026-01-01-foo.md").args_file.exists()

def test_subject_plan_answer_is_plan_review(self):
    r = run(repo, "soundness", "docs/plans/2026-01-01-foo.md", "--subject", "plan")
    assert r.returncode == 0 and field(r.stdout, "mode") == "plan-review"

def test_subject_changes_answer_is_diff_review_with_alignment(self):
    r = run(repo, "soundness", "docs/plans/2026-01-01-foo.md", "--subject", "changes")
    assert field(r.stdout, "mode") == "diff-review"
    assert "## Plan Alignment" in prompt(r.stdout)

def test_range_with_plan_never_asks(self):
    # tree dirty
    r = run(repo, "soundness", "main..feature-x docs/plans/2026-01-01-foo.md")
    assert r.returncode == 0 and "## Plan Alignment" in prompt(r.stdout)

def test_plain_diff_review_has_no_alignment_or_output_section(self):
    r = run(repo, "soundness", "")   # tree dirty, no args
    text = prompt(r.stdout)
    assert "## Plan Alignment" not in text and "## Grounding" not in text

# soundness: the filled prompt and the review name (step 2)
def test_prompt_has_no_placeholder_and_no_double_blank_line(self):
    for args in ("", "docs/plans/2026-01-01-foo.md", "main..feature-x fix the order"):
        text = prompt(run(repo, "soundness", args, "--subject", "changes").stdout)
        assert "{{" not in text and "\n\n\n" not in text

def test_prompt_starts_below_the_header(self):
    text = prompt(run(repo, "soundness", "").stdout)
    assert text.startswith("You are a")
    assert "Code Reviewer Dispatch Prompt" not in text

def test_range_review_is_named_after_tip_branch_with_slash_replaced(self):
    r = run(repo, "soundness", "main..feat/x")
    assert field(r.stdout, "review") == f"docs/plans/{today}-feat-x-review.md"

def test_working_tree_on_main_is_named_after_repo_folder(self):
    r = run(repo, "soundness", "")
    assert field(r.stdout, "review") == f"docs/plans/{today}-repo-review.md"

def test_collision_appends_2_then_3(self):
    # docs/plans/2026-01-01-foo-plan-review.md and -2.md exist
    r = run(repo, "soundness", "docs/plans/2026-01-01-foo.md")
    assert field(r.stdout, "review") == "docs/plans/2026-01-01-foo-plan-review-3.md"

def test_plans_folder_created_when_missing(self):
    # repo without docs/plans/, tree dirty
    run(repo, "soundness", "")
    assert (repo / "docs" / "plans").is_dir()

# spec
def test_spec_usage_on_no_path_two_paths_or_missing_file(self):
    for args in ("", "a-spec.md b-spec.md", "docs/plans/nope-spec.md"):
        r = run(repo, "spec", args)
        assert r.returncode == 2
        assert r.stderr.strip() == ("Usage: my:spec-review <path/to/spec.md>"
                                    " — one existing spec file.")

def test_spec_without_spec_suffix_note(self):
    r = run(repo, "spec", "docs/plans/2026-01-01-foo.md")
    assert ("note", "(docs/plans/2026-01-01-foo.md does not end in -spec.md;"
            " reviewing it as a spec anyway.)") in fields(r.stdout)

def test_spec_copy_prompt_and_review_name(self):
    r = run(repo, "spec", "docs/plans/2026-01-01-foo-spec.md")
    work = Path(field(r.stdout, "prompt")).parent
    assert (work / "spec.md").read_text() == (repo / "docs/plans/2026-01-01-foo-spec.md").read_text()
    assert field(r.stdout, "mode") == "spec-review"
    assert field(r.stdout, "review") == "docs/plans/2026-01-01-foo-spec-review.md"
    assert "{{" not in prompt(r.stdout)

def test_spec_collision_appends_2(self):
    # docs/plans/2026-01-01-foo-spec-review.md exists
    r = run(repo, "spec", "docs/plans/2026-01-01-foo-spec.md")
    assert field(r.stdout, "review") == "docs/plans/2026-01-01-foo-spec-review-2.md"
```

`today` is `datetime.date.today().isoformat()`. Run `cd plugins/my && python3 -m
unittest tests.test_review_prep`: every test fails, because the script does not
exist.

### Task 2: the script and the blocks file (Green, then Refactor)

Files: `plugins/my/skills/soundness-review/prompt-blocks.md` (D7: the four
blocks and the Plan Alignment block, moved from `SKILL.md` lines 182 to 229,
without the `>` quote marks), and `plugins/my/bin/review-prep.py`, executable,
with a docstring that holds `Usage:` and `Exit codes:` as in `locked-commit.py`
and the full account of D8's rules.

Functions, no bodies here:

- `git(*args, check=True) -> str`
- `read_args(path: Path) -> list[str]`
- `classify(tokens: list[str]) -> Parsed`, where `Parsed` holds `plan_only`,
  `range`, `plan_path`, `description`, `notes` and `stop`
- `plan_only_stop(parsed: Parsed) -> str | None`
- `work_dir(root: Path | None, skill: str) -> Path`
- `capture(parsed: Parsed, payload: Path) -> list[str]` (returns the untracked
  paths)
- `size_note(lines: int, kind: str) -> tuple[str, str] | None` (the user note
  and the subject note)
- `pick_mode(parsed: Parsed, payload_empty: bool, subject: str | None) -> Mode`,
  where `Mode` is the mode, the alignment flag, a stop message, or "ask"
- `review_slug(mode: str, parsed: Parsed, today: str, top: Path) -> str`
- `free_name(plan_dir: Path, slug: str) -> str`
- `template_body(path: Path) -> str`
- `block(name: str) -> str`
- `fill(body: str, values: dict[str, str]) -> str`
- `soundness(rest: list[str]) -> int`, `spec(rest: list[str]) -> int`,
  `main(argv) -> int`

All Task 1 tests pass, and the whole suite still passes. Refactor only with the
tests green: the two subcommands share `work_dir`, `size_note`, `template_body`,
`fill` and `free_name`.

### Task 3: the skills and the agents

- `plugins/my/skills/soundness-review/SKILL.md`: delete steps 0, 1, 1a and 2
  (lines 28 to 237) and the three worked examples (lines 251 to 296). Write in
  their place: step 0, write the args string to a new scratchpad file and run
  `review-prep.py soundness --args-file <file> --work-root <scratchpad>`; print
  every `note`; on exit 1 print the `stop` line and end; on exit 2 print stderr
  and end. Step 1, on exit 3, the question of today's lines 132 to 146 (kept,
  with `<N>`, `<U>` and `<PLAN_PATH>` from the output), then the rerun with
  `--subject` (D5). Step 2, dispatch with D6's one sentence. Step 3, surface the
  result, as today's step 4, using the `review` path. One worked example for the
  no-args case. Change the intro (line 24) to say the script composes the prompt
  into a file the reviewer reads.
- `plugins/my/skills/spec-review/SKILL.md`: delete steps 0 to 2 (lines 24 to 57)
  and the worked example (lines 78 to 89). Write step 0 as `review-prep.py spec
  --args-file <file> --work-root <scratchpad>` with the same exit handling, then
  today's steps 3 to 5 with D6's dispatch. Change line 18 and line 20 to match.
- `plugins/my/skills/soundness-review/code-reviewer-prompt.md` and
  `plugins/my/skills/spec-review/spec-reviewer-prompt.md`: in the header only,
  one sentence that `review-prep.py` fills the placeholders, and for the first
  one, that the criteria blocks live in `prompt-blocks.md`.
- `plugins/my/agents/code-reviewer.md` and `plugins/my/agents/spec-reviewer.md`:
  line 10 as D6 says.

Check: `grep -n '\$1\|\$ARGUMENTS\|{{'
plugins/my/skills/soundness-review/SKILL.md
plugins/my/skills/spec-review/SKILL.md` prints nothing.

### Task 4: docs

`README.md`: one sentence after line 165 in the `plugins/my/bin/` paragraph:
`review-prep.py`, in the same folder, prepares a `my:soundness-review` or
`my:spec-review` run: it writes the subject file and the reviewer's prompt, and
names the review file; its tests run with the same command.

### Task 5: rehearsal

No repo change. In a scratch repository with one commit on a branch and one
spec, run headless: `claude -p "/my:soundness-review main..<branch>" --add-dir
<scratch dir> --add-dir <plugin dir>` and `claude -p "/my:spec-review <spec>"`
with the same folders. Pass: each prints `Review written to
docs/plans/<filename>.`, the file has an `**Assessment:**` line, the spec review
has its System Model tables, and the session output shows no Read of a template
file. Record the result in the squash commit message.

## Open questions

1. May this spec run in auto mode (`/my:handoff auto`)? If yes, it needs a
   Delegation section.
2. D6 changes the input of both reviewer agents. Is that change wanted, or
   should the session keep pasting the composed prompt (Trade-offs, second
   Option B)?
3. Should Task 1's tests stay this long? They pin each message word for word,
   which is the main guard against a lost rule (Risk 2), but they are about 40
   tests.
