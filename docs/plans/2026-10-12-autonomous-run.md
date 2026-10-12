# `my:handoff auto` Implementation Plan

**Status:** approved, 2026-10-12. Written by the `my:handoff` plan stage from the approved spec.

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan task-by-task. The tasks
> build on each other: the `SKILL.md` tasks call both new scripts, and the
> rehearsal runs everything. The global review rules replace that skill's own
> reviews: run no per-task reviewer and no final `requesting-code-review`
> pass. The `my:handoff` review stage runs the end-of-branch reviews. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/my:handoff auto plan <spec>` and `/my:handoff auto code <spec>`
take an approved spec with a Delegation section to its `done` marks on `main`
with no input from the user, never push, and can be resumed after a crash.

**Architecture:** Two new standard-library Python scripts carry the parts
that must be exact: a `PreToolUse` hook that blocks `git push` when
`MY_AUTORUN` is set (D4), and a state helper that writes and checks
`<git common dir>/my-handoff/<slug>.json` (D6). The rest is prompt text in
`plugins/my/skills/handoff/SKILL.md`: the `auto` forms, the Delegation
format, the start checks, a fixed outcome for each stop point, `resume`
(D1 to D3, D5, D7, D8). Docs follow (D10).

**Tech Stack:** Python 3 standard library (`json`, `shlex`, `os`,
`subprocess`, `unittest`), Claude Code plugin hooks and skills, git, tmux,
headless `claude -p` runs, `markdownlint-cli2`.

**Spec:** `docs/plans/2026-10-12-autonomous-run-spec.md`

## Global Constraints

- Work in the worktree `.claude/worktrees/autonomous-run` on the branch
  `feat/autonomous-run`. The `my:handoff` review stage looks for these names.
- Conventional Commits with scope: `my-plugin` for files under
  `plugins/my/`, `global` for `global/CLAUDE.md`, `docs` for `README.md`.
  A docs commit that spans these scopes uses `docs:` with no scope.
  Every message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Unit tests: `cd plugins/my && python3 -m unittest discover tests`. Every
  code commit runs them, and all must pass.
- End-of-branch checks for this branch: the unit tests above, the lint
  counts below, and the rehearsal record from Task 7.
- No new dependencies. Python 3, `markdownlint-cli2`, `jq` and tmux are
  installed.
- Without the word `auto`, `my:handoff` behaves exactly as today, even when
  the spec has a Delegation section (D1).
- The push guard prints exactly `Blocked: autonomous runs never push.` to
  stderr and exits 2 (D4).
- Fixed copy in `SKILL.md`, word for word: `a run for <slug> exists; use resume`
  (D3), `resume refused: <first mismatch>` (D7),
  `uncommitted files from the earlier session: <paths>` (D7), and
  `merge done`, printed by `handoff-state.py check` (D6).
- Read `git diff --cached` before every commit.
- Markdown lint: count errors with
  `markdownlint-cli2 <file> 2>&1 | grep ' error ' | grep -vc MD013`. The
  count must not rise. On `main` on 2026-10-12 it is 0 for
  `plugins/my/skills/handoff/SKILL.md`, `plugins/my/skills/handoff/README.md`,
  `README.md` and `ROADMAP.md`, and 16 for `global/CLAUDE.md`.
- Match the line style of the paragraph you edit. The handoff files and
  `README.md` wrap at 80 characters. `global/CLAUDE.md` is mixed: line 99
  is one long line, line 61 wraps.

## Decisions this plan adds

The spec leaves these open. None changes a D1 to D10 decision; the plan
review checks that.

1. **Who creates the state file.** D6 says "the first auto stage creates
   the file after its start checks pass", and D3 says a `run auto` session
   needs the file to exist. Both hold only if the launch form
   (`auto plan` or `auto code`, in the user's session) runs the D3 checks,
   creates the file with `next` set to the stage, and then launches.
2. **Stage names after the merge.** `next` values `merge`,
   `worktree-remove`, `fold` and `done` all run as the review stage:
   `run auto review <task doc>`, window name `review-<slug>`. That session
   reads `next` and starts at the matching part of Review stage step 8. So
   the D3 check for a `run auto review` session is "`next` is one of
   `review`, `merge`, `worktree-remove`, `fold`, `done`".
3. **`resume` finds `<doc>` in the state file:** `task_doc` for `code` and
   later, `spec` for `plan`. The `resume` session's own `<name>` is
   `resume-<slug>`; the window it launches is named `<stage>-<slug>`.
4. **A `run auto` session checks that `MY_AUTORUN` equals `<slug>`, first,**
   before every other start check. If not, the start check fails with
   `MY_AUTORUN is not set to <slug>; the push guard is off`. Without this, a
   hand-typed `run auto` runs unguarded.
5. **Restart detection (D7).** A `run auto` session is a restart when the
   facts a fresh start expects to be absent are present: for `plan`, the plan
   file exists; for `code`, the branch `*/<slug>` or its worktree exists; for
   `review`, every start is treated as a restart. A restart skips those
   fresh-start checks and follows D7's rules instead. A fresh start finds
   them absent and runs as today. This needs no new state field. In auto
   mode, every task commit of the code stage carries the git trailer
   `Task: <N>`, with N the task's position in the task doc's task list,
   counted from 1, so unnumbered Tasks sections work too. A restarted code
   stage continues at the first position no commit on the branch carries. A
   restarted review stage counts the fix round as done when the branch has a
   commit that adds a file matching `docs/plans/*review*.md`, because review
   step 6 commits the reports in the fix round.
6. **`<base>` in `handoff-state.py`** is the branch checked out in the main
   checkout, as in `SKILL.md`. The state file gets no `base` field.

## Review Focus

- **A heredoc or a quoted string that mentions `git push`.** Splitting at
  newlines alone would block a commit message body or a heredoc line. Task 1
  tests both, and `-m "a; git push"`.
- **A command the word splitting cannot parse** (an unbalanced quote) while
  `MY_AUTORUN` is set. The guard blocks it when the text holds the words
  `git` and `push`, and allows it otherwise. Bash would refuse the command
  anyway, so blocking costs nothing. Task 1 tests both.
- **A second commit on `main` with the same subject as `squash_subject`.**
  `check` counts only commits on `<base>` that are not on the branch. An
  older commit with that subject is on the branch's history, so it is not
  counted. Task 2 tests it.
- **The guard on the user's own sessions.** It runs on every `Bash` call
  in every session. With `MY_AUTORUN` unset or empty it must exit 0 before it
  reads stdin, even on input that is not JSON. Task 1 tests both.
- **A crash between the squash commit and `set next=worktree-remove`.**
  `check` must see the commit and move `next` on, so the merge never runs
  twice. Task 2 tests it.

## File map

| File | Change | Task |
| --- | --- | --- |
| `plugins/my/hooks/block-autorun-push.py` | Create: the push guard (D4) | 1 |
| `plugins/my/tests/test_block_autorun_push.py` | Create | 1 |
| `plugins/my/hooks/hooks.json` | Add a `PreToolUse` entry | 1 |
| `plugins/my/bin/handoff-state.py` | Create: the state helper (D6) | 2 |
| `plugins/my/tests/test_handoff_state.py` | Create | 2 |
| `plugins/my/skills/handoff/SKILL.md` | D1 to D8 | 3, 4, 5 |
| `plugins/my/skills/handoff/README.md` | An "Auto mode" section | 6 |
| `global/CLAUDE.md` | D10 | 6 |
| `README.md` | Auto mode under `my:handoff`; the new script | 6 |

`ROADMAP.md` gets no new rows: the spec's Files table asks for a row for
this feature and one for the settings bug, and both already exist (the
`my:handoff auto` row and "Deny list has no effect"). The review stage's
`done` marks move the feature row to ✅.

## How the headless tests run

Tasks 3 and 5 test `SKILL.md` with headless runs, as the sibling plan
`docs/plans/2026-09-30-soundness-plan-only.md` did. The running session sees
the installed plugin, so each run passes `--plugin-dir "$WT/plugins/my"`,
plus `--add-dir` for the scratch folder and for `$WT/plugins/my`. The mode is
`acceptEdits`, so Launch never opens a window: it prints its fallback
command, which the tests read. Each run clears `TMUX` and `TMUX_PANE`.
Count denials as `"subtype":"permission_denied"` events in the stream; a run
with a denial is not valid.

---

### Task 0: Worktree

The `my:handoff` code stage creates the worktree. By hand, from the main
checkout: `git worktree add .claude/worktrees/autonomous-run -b feat/autonomous-run`.

- [ ] **Step 1: Confirm**

Run: `cd .claude/worktrees/autonomous-run && git branch --show-current && git status --short`
Expected: `feat/autonomous-run`, and no output from `git status`.

---

### Task 1: The push guard

**Files:**

- Create: `plugins/my/hooks/block-autorun-push.py`
- Create: `plugins/my/tests/test_block_autorun_push.py`
- Modify: `plugins/my/hooks/hooks.json`

**Interfaces:**

- Produces: a script that reads the hook's JSON on stdin and uses only
  `tool_input.command`. It does not filter on `tool_name`. Exit 0 allows,
  exit 2 blocks.
- Produces: `pushes(command: str) -> bool` in the script, for the tests to
  import with `importlib`.

- [ ] **Step 1: Write the failing tests**

Follow `test_git_fold_fixups.py`: a module docstring with the run command,
`SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "block-autorun-push.py"`,
and a helper that runs the script as a subprocess.

```python
def guard(command, autorun="widget", tool="Bash", raw=None):
    env = {k: v for k, v in os.environ.items() if k != "MY_AUTORUN"}
    if autorun is not None:
        env["MY_AUTORUN"] = autorun
    stdin = raw if raw is not None else json.dumps(
        {"tool_name": tool, "tool_input": {"command": command}})
    return subprocess.run([sys.executable, str(SCRIPT)], input=stdin,
                          env=env, capture_output=True, text=True, timeout=10)

BLOCKED = [
    "git push", "git push origin main", "git -C /x push", "git -c a=b push",
    "cd /x && git push", "git --no-pager push", "git status; git push",
    "git status || git push", "true | git push", "git status\ngit push",
    "(cd /x && git push)", "FOO=1 git push", "/usr/bin/git push",
    'git push "unbalanced',
]
ALLOWED = [
    "git stash push", "echo push", "git status", 'git commit -m "never git push"',
    'git commit -m "a; git push"', "cat <<'EOF'\ngit push\nEOF",
    "cat <<-EOF\n\tgit push\n\tEOF\ngit status", 'echo "unbalanced',
]

class GuardTest(unittest.TestCase):
    def test_blocks_a_push(self):
        for command in BLOCKED:
            with self.subTest(command=command):
                result = guard(command)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr.strip(),
                                 "Blocked: autonomous runs never push.")

    def test_monitor_push_is_blocked(self):
        self.assertEqual(guard("git push", tool="Monitor").returncode, 2)

    def test_allows_text_that_only_mentions_push(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertEqual(guard(command).returncode, 0)

    def test_every_command_passes_without_the_variable(self):
        for command in BLOCKED + ALLOWED:
            with self.subTest(command=command):
                self.assertEqual(guard(command, autorun=None).returncode, 0)
                self.assertEqual(guard(command, autorun="").returncode, 0)

    def test_bad_json_passes_without_the_variable(self):
        self.assertEqual(guard("", autorun=None, raw="not json").returncode, 0)

    def test_hooks_json_runs_the_guard_for_bash_and_monitor(self):
        hooks = json.loads((SCRIPT.parent / "hooks.json").read_text())["hooks"]
        commands = [h["command"] for entry in hooks["PreToolUse"]
                    if entry["matcher"] == "Bash|Monitor" for h in entry["hooks"]]
        self.assertEqual(commands,
                         ['python3 "$CLAUDE_PLUGIN_ROOT/hooks/block-autorun-push.py"'])
```

- [ ] **Step 2: Run the tests and see them fail**

Run: `cd plugins/my && python3 -m unittest tests.test_block_autorun_push -v`
Expected: every test fails or errors: the script and the `PreToolUse` key do
not exist.

- [ ] **Step 3: Write `block-autorun-push.py`**

`main() -> int`: read `MY_AUTORUN` first; when it is unset or empty, return
0 without reading stdin. Otherwise parse stdin, take
`tool_input.command`, and when `pushes(command)` is true print the block
line to stderr and return 2.

`pushes(command: str) -> bool`, in this order:

1. Drop heredoc bodies: after a line with `<<WORD`, `<<-WORD`, `<<'WORD'` or
   `<<"WORD"`, drop the lines up to the one that is `WORD` after stripping
   leading tabs.
2. Tokenize with `shlex.shlex(text, posix=True, punctuation_chars=True)`,
   passing `punctuation_chars="();<>|&\n"` as a string when the object is
   built (it cannot be changed later), and with `\n` removed from
   `whitespace`, so a newline becomes its own token. Quotes keep `-m "a; git push"` as one word.
3. On `ValueError`, return true when the text has the words `git` and
   `push` (`re.search(r"\bgit\b", …)` and `r"\bpush\b"`), else false.
4. Split the tokens into subcommands at every token made only of the
   characters `;&|()\n`.
5. In each subcommand, skip leading `NAME=value` words. Block when the
   command word's basename is `git` and the first word after the global
   options is `push`. Global options: `-C` and `-c` take the next word;
   any other word starting with `-` is one option.

- [ ] **Step 4: Add the hook entry**

In `plugins/my/hooks/hooks.json`, add a `"PreToolUse"` key with one entry:
matcher `Bash|Monitor`, one hook of type `command` with the command
`python3 "$CLAUDE_PLUGIN_ROOT/hooks/block-autorun-push.py"` and
`"timeout": 10`. Make the script executable.

- [ ] **Step 5: Run the tests and see them pass**

Run: `cd plugins/my && python3 -m unittest discover tests -v`
Expected: all pass, the fold tests included. `jq . hooks/hooks.json` exits 0.

- [ ] **Step 6: End-to-end through Claude Code**

In the scratchpad, make a repo with one commit and a bare repo as `origin`.
Record `git -C <bare> rev-parse main` (empty before the first push is
fine: then record `git -C <bare> show-ref`). Run one headless session from
the repo, with `MY_AUTORUN=e2e`, `--plugin-dir "$WT/plugins/my"`,
`--add-dir` for the scratch folder, `--permission-mode acceptEdits`,
`--allowedTools 'Bash(git push:*)'` and the prompt
`Run exactly: git push origin main. Report its output.`

Expected: the stream holds `Blocked: autonomous runs never push.`, and
`git -C <bare> show-ref` prints the same as before. Run it again without
`MY_AUTORUN`: the push goes through. That second run proves the first was not
stopped by something else. Then reset the bare repo, and run once more with
`MY_AUTORUN=e2e` and the prompt
`Use the Monitor tool to run exactly: git push origin main. Report its output.`
Expected: blocked, the bare repo unchanged. This shows that `Monitor` passes
its shell text in `tool_input.command`. If it does not, the guard misses it:
fix the field the script reads, and add a unit test with that shape.

- [ ] **Step 7: Commit**

```bash
git add plugins/my/hooks/block-autorun-push.py plugins/my/hooks/hooks.json \
  plugins/my/tests/test_block_autorun_push.py
git commit -m "feat(my-plugin): a hook blocks git push in autonomous runs"
```

---

### Task 2: The state helper

**Files:**

- Create: `plugins/my/bin/handoff-state.py`
- Create: `plugins/my/tests/test_handoff_state.py`

**Interfaces:**

- Produces, for Tasks 3 to 5 (run from anywhere inside the repo or a
  worktree):
  - `handoff-state.py set <slug> <field>=<value> …`: exit 0. Creates the
    folder and the file when missing. Fields: `spec`, `task_doc`, `branch`,
    `worktree`, `next`, `squash_subject`, `head_before_fold`, `stopped`.
    An unknown field, or a `next` outside `plan`, `code`, `review`, `merge`,
    `worktree-remove`, `fold`, `done`, `finished`, prints
    `unknown field: <f>` or `unknown next: <v>` and exits 2, writing
    nothing. The write goes to a temporary file in the same folder, then
    `os.replace`.
  - `handoff-state.py get <slug>`: prints the JSON (`indent=2`,
    `sort_keys=True`), exit 0. With no file: prints `no state for <slug>`
    to stderr, exit 1.
  - `handoff-state.py check <slug>`: one mismatch per line on stdout, exit
    1 when there is any, else exit 0. With no file, the one mismatch is
    `no state for <slug>`. When it finds the squash commit for
    `next=merge`, it prints `merge done`, sets `next=worktree-remove`, checks
    that, and exits 0 when that matches.
  - Wrong arguments: a usage line, exit 2.
  - The mismatch lines, exactly: `no state for <slug>`, `no base branch`,
    `in progress: <name>`, `missing field: <field>`,
    `spec missing: <path>`, `task doc not committed on <base>: <path>`,
    `branch missing: <branch>`, `worktree not on <branch>: <path>`,
    `no squash commit: <subject>`, `squash subject matches <n> commits`,
    `worktree still listed: <path>`, `fixup waits: <short hash> <subject>`.
    `check` tests the in-progress state first, then missing fields, then
    the row's facts in the table's order.
- `<base>` and the main checkout are found as in "Decisions this plan
  adds", item 6. The squash commit is a commit in
  `git log <base> --not <branch>` whose subject equals `squash_subject`.
  A spec or task-doc fixup waits when `git log <added>..<base>` has the
  subject `fixup! <subject of added>`, where `<added>` is
  `git log --diff-filter=A --format=%H -1 <base> -- <path>`.

- [ ] **Step 1: Write the failing tests**

Reuse the fold tests' `clean_env`, `git`, `make_repo` and `commit`
helpers by copying them; the test files stay independent. A fixture
`setUp` builds a repo on `main` with the spec and the plan committed, and a
branch `feat/widget` with one commit, checked out in a worktree under the
temporary folder. Tests, each asserting the exit code and the exact lines:

```python
def test_set_then_get_round_trips_every_field(self): ...
    # get prints all eight fields with the values set; exit 0
def test_set_rejects_an_unknown_field(self): ...
    # exit 2, "unknown field: colour", and no file written
def test_set_rejects_an_unknown_next(self): ...
    # exit 2, "unknown next: shipping"
def test_get_without_a_file_exits_1(self): ...
    # stderr "no state for widget"
def test_file_is_in_the_git_common_dir_and_untracked(self): ...
    # path is <repo>/.git/my-handoff/widget.json, also when run from the
    # worktree; `git status --porcelain` prints nothing
def test_no_temporary_file_is_left(self): ...
    # the my-handoff folder holds only widget.json after three sets
def test_check_matches_for_each_next(self): ...
    # subTest per value: plan, code, review, merge, worktree-remove, fold,
    # done, finished; each in the state where that step can start; exit 0
def test_check_mismatch_for_each_next(self): ...
    # subTest per value, exit 1 and one line naming the failed fact:
    # plan: spec missing; code: task doc not committed on main;
    # review: branch missing; merge: branch missing and no squash commit;
    # worktree-remove: no squash commit; fold: worktree still listed;
    # done: a fixup of the spec waits; finished: a rebase is in progress
def test_check_finds_a_merge_that_happened_before_a_crash(self): ...
    # next=merge, squash commit already on main: prints "merge done",
    # exit 0, and get shows next=worktree-remove
def test_check_ignores_an_older_commit_with_the_squash_subject(self): ...
    # main has the subject before the branch forked; next=merge: no
    # "merge done", next stays merge
def test_check_refuses_during_a_rebase(self): ...
    # a stopped `git rebase -i` (GIT_SEQUENCE_EDITOR "sed -i 1s/pick/edit/")
    # makes check exit 1 for next=done
def test_check_names_a_missing_field(self): ...
    # next=review without branch: "missing field: branch"
```

- [ ] **Step 2: Run the tests and see them fail**

Run: `cd plugins/my && python3 -m unittest tests.test_handoff_state -v`
Expected: every test fails: the script does not exist.

- [ ] **Step 3: Write `handoff-state.py`**

Standard library only, in the style of `bin/git-fold-fixups.py`: a `git()`
helper, `usage()`, `main(argv) -> int`. Per `next`, `check` tests:

| `next` | Facts |
| --- | --- |
| `plan` | `spec` is a file in the main checkout |
| `code` | `task_doc` is committed on `<base>` |
| `review` | `branch` exists, and `git worktree list --porcelain` shows `worktree` on it |
| `merge` | the squash commit exists (then `merge done`), or `branch` exists |
| `worktree-remove` | exactly one squash commit |
| `fold` | the squash commit exists, and `worktree` is not listed |
| `done` | no fixup of `spec` or `task_doc` waits |
| `finished` | nothing more |

For every value: no `rebase-merge`, `rebase-apply`, `MERGE_HEAD`,
`CHERRY_PICK_HEAD` or `REVERT_HEAD` in the main checkout's git dir, and every
field the row reads is set (else `missing field: <f>`). Make it executable.

- [ ] **Step 4: Run the tests and see them pass**

Run: `cd plugins/my && python3 -m unittest discover tests -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/bin/handoff-state.py plugins/my/tests/test_handoff_state.py
git commit -m "feat(my-plugin): handoff-state.py keeps an autonomous run's state"
```

---

### Task 3: `SKILL.md`: forms, Delegation, start checks, Launch

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md`: "Forms", "Launch",
  "Start checks", and the frontmatter `description`.
- Create in the scratchpad: `$SCRATCH/ar-env.sh` and the fixture
  `$SCRATCH/ar-fixture/`, never committed.

**Interfaces:**

- Consumes: `handoff-state.py set|get` (Task 2).
- Produces, for Tasks 4 and 5: the state file exists from the launch on,
  with `spec`, `task_doc`, `next`; a `run auto` session runs with
  `MY_AUTORUN=<slug>`.

- [ ] **Step 1: Build the fixture and the helpers**

`$SCRATCH/ar-env.sh` sets `WT`, `FIX`, `SCRATCH` and defines:

- `hr <run-name> '<args>'`: from `$FIX`, runs
  `env -u TMUX -u TMUX_PANE TMPDIR="$SCRATCH/tmp" claude -p --plugin-dir "$WT/plugins/my" --add-dir "$SCRATCH" --add-dir "$WT/plugins/my" --permission-mode acceptEdits --output-format stream-json --verbose "/my:handoff $2"`,
  writing `$SCRATCH/<run-name>.jsonl`. Extra environment, such as
  `MY_AUTORUN=widget`, goes before the call.
- `chk <run-name>`: prints the `my` plugin path from the `init` event (must
  be `$WT/plugins/my`), the denial count (must be 0), and the last 15 lines
  of the final answer.
- `fresh`: rebuilds `$FIX` from scratch.

The fixture, on branch `main`: a `CLAUDE.md` with a "Git workflow" section
(no plans index; scope `widget`; test command `python3 -m unittest`; no
remote), and these committed specs:

- `docs/plans/2026-10-12-widget-spec.md`: `approved`, a Tasks section, and
  the D2 example Delegation section.
- `docs/plans/2026-10-12-big-spec.md`: `approved`, the same Delegation
  section, no Tasks section.
- `docs/plans/2026-10-12-nodel-spec.md`: `approved`, Tasks, no Delegation.
- `docs/plans/2026-10-12-badkey-spec.md`: `approved`, Tasks, Delegation
  with a fifth key `- **Budget:** \`none\``.

- [ ] **Step 2: Run the Red baseline**

```bash
source <scratchpad>/ar-env.sh
hr a1 'auto code docs/plans/2026-10-12-widget-spec.md'; chk a1
```

Expected: the old usage line `Usage: /my:handoff [run] <plan|code|review> …`.
This fails Step 4's expectation for `a1`.

- [ ] **Step 3: Edit `SKILL.md`**

- **Forms:** add `auto <plan|code> <spec>`, `auto resume <spec>` and
  `run auto <stage> <doc>` (D1). The usage line becomes
  `Usage: /my:handoff [run] [auto] <plan|code|review> <docs/plans/…md>, or /my:handoff auto resume <docs/plans/…-spec.md>`.
  Without `auto`, every step reads as today.
- **A "Delegation" subsection** under Forms: the D2 example block, the D2
  table, "compare by exact name", and "a missing key, an unknown key, or a
  value outside these forms fails the start check".
- **Start checks:** an "Auto mode" list with D3, plus decisions 1, 2 and 4
  of this plan. `auto code` skips today's "committed on `<base>`" check
  until D8 has run (Task 4). The launch form, after its checks pass, runs
  `handoff-state.py set <slug> spec=<spec> task_doc=<doc> next=<stage> stopped=`,
  where `<doc>` is the spec for `code` and
  `docs/plans/<spec date>-<slug>.md` for `plan`.
- **Launch:** in auto mode, the command in step 4 and step 5 starts with
  `MY_AUTORUN=<slug>` and types `/my:handoff run auto <stage> <doc>` (D4).
  In auto mode, a fallback is a stop (D5, row 2), except for the user's own
  launch and `resume`, which print the command as today.
- **Frontmatter `description`:** add the `auto` forms in one sentence.

- [ ] **Step 4: Run the checks and see them pass**

Run each with `fresh` before it, one headless session per Bash call, with
the 600000 ms timeout:

| Run | Args (and env) | Expected last lines |
| --- | --- | --- |
| a1 | `auto code docs/plans/2026-10-12-widget-spec.md` | a fallback command that contains `MY_AUTORUN=widget claude -n code-widget` and ends `'/my:handoff run auto code docs/plans/2026-10-12-widget-spec.md'`; `handoff-state.py get widget` shows `next` `code` |
| a2 | a1 again, without `fresh` | `code-widget: start check failed: a run for widget exists; use resume` |
| a3 | `auto plan docs/plans/2026-10-12-big-spec.md` | a fallback command that contains `MY_AUTORUN=big claude -n plan-big`; state `next` `plan`, `task_doc` `docs/plans/2026-10-12-big.md` |
| a4 | `auto plan docs/plans/2026-10-12-widget-spec.md` | a start check failure naming the Tasks section |
| a5 | `auto code docs/plans/2026-10-12-nodel-spec.md` | a start check failure naming Delegation; no state file |
| a6 | `auto code docs/plans/2026-10-12-badkey-spec.md` | a start check failure naming `Budget` |
| a7 | `run auto code docs/plans/2026-10-12-widget-spec.md`, no `MY_AUTORUN` | `MY_AUTORUN is not set to widget; the push guard is off` |
| a8 | `code docs/plans/2026-10-12-widget-spec.md` (plain) | a command with no `MY_AUTORUN` and `'/my:handoff run code …'`; no state file |
| a9 | `auto bogus docs/plans/2026-10-12-widget-spec.md` | the new usage line |

a8 is the D1 check that plain handoff is unchanged.

- [ ] **Step 5: Lint**

Run: `markdownlint-cli2 plugins/my/skills/handoff/SKILL.md 2>&1 | grep ' error ' | grep -vc MD013`
Expected: `0`.

- [ ] **Step 6: Commit**

```bash
git add plugins/my/skills/handoff/SKILL.md
git commit -m "feat(my-plugin): my:handoff auto forms, Delegation and start checks"
```

---

### Task 4: `SKILL.md`: the stages in auto mode

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md`: "Signal", "Plan stage",
  "Code stage", "Review stage", "Finish".

**Interfaces:**

- Consumes: `handoff-state.py set|check` (Task 2), the state file from Task 3.
- Produces, for Task 5: the state writes below, and the `Task: <N>`
  trailer.

- [ ] **Step 1: Write the content check, and see it fail**

```bash
cd "$WT" && for s in 'Delegation \[Design-changing findings\]' \
  'Delegation \[Dependencies\]' 'Delegation \[Failing end-of-branch tests\]' \
  'Delegation \[End-of-branch checks\]' 'git reset --merge' 'next=merge' \
  'next=fold' 'head_before_fold' 'squash_subject' 'Task: <N>' \
  'git-fold-fixups.py check <spec commit>' 'next=finished'; do
  grep -q -- "$s" plugins/my/skills/handoff/SKILL.md || echo "missing: $s"; done
```

Expected before the edit: twelve `missing:` lines. This is a guard against
dropped rows, not a behaviour test. Task 7 tests the behaviour.

- [ ] **Step 2: Edit `SKILL.md`**

- **Signal:** in auto mode, before the three actions, run
  `handoff-state.py set <slug> stopped="<the line>"`. After the user's reply,
  `set <slug> stopped=` and go on in auto mode (D5).
- **A "Stop points in auto mode" table:** the D5 table, all 17 rows, in the
  spec's words. Place it after "Signal". Each stage step that today
  signals names its row. With `decide`, the stage writes one line into the
  task doc's **Risk** section: the finding, the choice, the reason (D5).
- **Code stage, auto mode:** a new first step, D8 (both sub-steps). Then
  today's "committed on `<base>`" check. After the worktree exists:
  `set <slug> branch=<branch> worktree=<worktree>`. Every task commit
  carries the trailer `Task: <N>` (decision 5).
- **State writes when a stage launches the next one:** plan stage
  `set <slug> task_doc=<plan path> next=code`; code stage `set <slug> next=review`.
- **Review stage step 2:** when the rules name no checks, use
  Delegation [End-of-branch checks]. A failing test listed in Delegation
  [Failing end-of-branch tests] goes on, and the `done` mark names it.
- **Review stage step 7:** in auto mode, go on to step 8 without a yes.
- **Review stage step 8, auto mode,** in order:
  1. `set <slug> squash_subject="<subject>" next=merge`, then
     `git merge --squash`. On a conflict: the D5 row. After the commit:
     `set <slug> next=worktree-remove`.
  2. `git worktree remove`, then `set <slug> next=fold`.
  3. When fixups wait: `set <slug> head_before_fold=$(git rev-parse HEAD)`,
     then the fold. After it, or when none wait: `set <slug> next=done`.
     Main not clean, or the fold exits 1 or 3: the D5 rows.
  4. The `done` marks find the squash commit by `squash_subject`. After
     them: `set <slug> next=finished stopped=`.
  A `run auto review` session whose `next` is past `review` starts at the
  matching sub-step (decision 2).
- **Finish:** unchanged. In auto mode, the last line also names the squash
  commit's short hash.

- [ ] **Step 3: Run the content check and see it pass**

Run the Step 1 loop. Expected: no output.

- [ ] **Step 4: Lint, then commit**

Lint as in Task 3 step 5, expected `0`.

```bash
git add plugins/my/skills/handoff/SKILL.md
git commit -m "feat(my-plugin): my:handoff stages follow Delegation in auto mode"
```

---

### Task 5: `SKILL.md`: `resume`

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md`: a "Resume" section after
  "Launch".

**Interfaces:**

- Consumes: `handoff-state.py check|get` (Task 2), the `Task: <N>` trailer
  (Task 4).

- [ ] **Step 1: Run the Red baseline**

With `fresh`, set a state that `check` refuses, then resume:

```bash
source <scratchpad>/ar-env.sh; fresh
(cd "$FIX" && "$WT/plugins/my/bin/handoff-state.py" set widget \
  spec=docs/plans/2026-10-12-widget-spec.md \
  task_doc=docs/plans/2026-10-12-widget-spec.md next=review branch=feat/widget \
  worktree=.claude/worktrees/widget)
hr r1 'auto resume docs/plans/2026-10-12-widget-spec.md'; chk r1
```

Expected before the edit: no `resume refused:` line.

- [ ] **Step 2: Write the Resume section**

D7, all four bullets, with the fixed copy from Global Constraints. The
launched command is `run auto <stage> <doc>`, with `<stage>` and `<doc>` from
decisions 2 and 3. The restart rules use decision 5.

- [ ] **Step 3: Run the checks and see them pass**

| Run | Setup | Expected last lines |
| --- | --- | --- |
| r1 | Step 1's state | `resume-widget: resume refused: branch missing: feat/widget` |
| r2 | `fresh`; `set widget spec=… task_doc=docs/plans/2026-10-12-widget-spec.md next=code` | a fallback command that contains `MY_AUTORUN=widget claude -n code-widget` and ends `'/my:handoff run auto code docs/plans/2026-10-12-widget-spec.md'` |
| r3 | `fresh`; no state | a stop naming `no state for widget` |

- [ ] **Step 4: Lint, then commit**

Lint as in Task 3 step 5, expected `0`.

```bash
git add plugins/my/skills/handoff/SKILL.md
git commit -m "feat(my-plugin): my:handoff auto resume continues a stopped run"
```

---

### Task 6: Docs

**Files:**

- Modify: `plugins/my/skills/handoff/README.md`: a new "Auto mode" section
  before "What you need", and the `auto` forms in "Two ways to call it".
- Modify: `global/CLAUDE.md`: line 99 (Spec → Plan step 3) and the Medium
  paragraph at line 61 (D10).
- Modify: `README.md`: the `my:handoff` entry, and the paragraph on
  `plugins/my/bin/` names `handoff-state.py`.

- [ ] **Step 1: Write the README section**

For a reader: the commands; the Delegation block with its four keys; that a
run never pushes, and the guard's known gap (Risk, third item); where the
state lives; what `resume` does; what a stop looks like.

- [ ] **Step 2: Edit `global/CLAUDE.md`**

Step 3: when the approved spec has a Delegation section, the question is
"Hand off the plan, supervised or auto?", and the answer runs
`/my:handoff plan <spec path>` or `/my:handoff auto plan <spec path>`. The
Medium paragraph: the same for `/my:handoff code` and
`/my:handoff auto code`. With `auto code`, the stage commits and folds the
`approved` edit itself (D8).

- [ ] **Step 3: Edit `README.md`**

One sentence on `/my:handoff auto` under `my:handoff`. In the
`plugins/my/bin/` paragraph, one sentence: `handoff-state.py` keeps an auto
run's state, and its tests run with the same command.

- [ ] **Step 4: Lint**

Count as in Global Constraints. Expected: 0, 0 and 16 for the handoff
`README.md`, `README.md` and `global/CLAUDE.md`.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/skills/handoff/README.md README.md global/CLAUDE.md
git commit -m "docs: offer my:handoff auto after a spec with Delegation"
```

---

### Task 7: Rehearsal of the full cycle

**Files:**

- Create in the scratchpad: one fixture per run, each with a bare repo as
  `origin`; `$SCRATCH/rehearsal.md`, the record. Nothing is committed in
  the repo except the record's summary, in Step 6.

**Interfaces:**

- Consumes: everything above. The rehearsal uses the worktree's plugin
  through `--plugin-dir "$WT/plugins/my"`. Launch copies that flag into each
  window it opens, so every stage, and the guard, comes from the worktree.

Use a separate tmux server, `tmux -L autorun`. Start each run as
`tmux -L autorun new-window -c <fixture> "claude --plugin-dir $WT/plugins/my --permission-mode auto '<prompt>'"`.
A new fixture path shows the trust dialog once: press Enter only when
`tmux -L autorun capture-pane -p` shows it. Wait for a run with `Monitor`
and an until-loop on `tmux -L autorun list-windows -F '#{window_name}'`
until a name ends in `✓` or `⚠`. Each fixture is the Task 3 fixture's
`widget` spec, with a `widget.py` the task changes, plus
`git remote add origin <bare>` and a first `git push origin main`, without
`-u`. With no upstream, `git-fold-fixups.py check` does not refuse a target
as already pushed, so D8 can make a fixup. Record
`git -C <bare> show-ref` before each run.

To read a window's environment, list its processes:
`tmux -L autorun list-panes -a -F '#{window_name} #{pane_pid}'`, then for
each pid and its children (`pgrep -P`), read `/proc/<pid>/environ`.

- [ ] **Step 1: Plain run**

Prompt `/my:handoff code docs/plans/2026-10-12-widget-spec.md`. Expected:
the review window stops with `review-widget: ready to squash-merge feat/widget`;
no process of any window has `MY_AUTORUN`. Kill the server's windows.

- [ ] **Step 2: Auto run**

New fixture. Prompt `/my:handoff auto code docs/plans/2026-10-12-widget-spec.md`.
Expected: the review window ends with `review-widget ✓`; `main` has the squash
commit and the `done` marks citing it; `handoff-state.py get widget` shows
`next` `finished`; every `claude` process in the windows the run launched has
`MY_AUTORUN=widget` (the first window is the launch form and has none by
design);
`git -C <bare> show-ref` is unchanged.

- [ ] **Step 3: Unlisted dependency**

New fixture whose spec's task adds `requests` to `requirements.txt`, with
Dependencies `none`. Expected: a stop in `code-widget`; `get` shows
`next` `code` and a `stopped` reason naming `requests`.

- [ ] **Step 4: Resume after a closed window**

New fixture whose widget spec is committed as `draft`, with the `approved`
edit left uncommitted, so D8 commits it as a fixup. Add an untracked
`notes.txt` in the main checkout, so D8 leaves
the spec fixup unfolded and the fold must wait after the merge. Prompt as in
Step 2. Expected: a stop in `review-widget` with `next` `fold`. Then
`tmux -L autorun kill-window` it, `rm notes.txt`, and start
`/my:handoff auto resume docs/plans/2026-10-12-widget-spec.md` in a new
window. Expected: a new `review-widget` window that folds, sets the `done`
marks and ends `✓`; no `fixup!` commit on `main`; the bare repo unchanged.

- [ ] **Step 5: When a step fails**

A failed expectation is a bug in Tasks 1 to 5. Use
`superpowers:systematic-debugging`, fix it in its task's file with a test
where one applies, commit, and run the failed step again on a new fixture.
A failure that survives debugging is a gate.

- [ ] **Step 6: Record**

Write the result of each step (expected, seen, pass or fail) into
`$SCRATCH/rehearsal.md`. Append a short "Rehearsal, 2026-10-12" list with
the four results to this plan's **Testing Strategy** section, and commit it:

```bash
git add docs/plans/2026-10-12-autonomous-run.md
git commit -m "docs(plans): rehearsal results for my:handoff auto"
```

Stop the server: `tmux -L autorun kill-server`.

---

## Trade-Offs

- **A `Task: <N>` trailer versus matching commit subjects.** Subjects are
  written by the executor and differ between plans and Medium Tasks
  sections. A trailer is exact and costs one line per commit. Its cost: a
  new convention that only auto mode writes, so a supervised branch resumed
  in auto mode would not have it. `resume` only resumes auto runs.
- **The launch form creates the state file** rather than the first stage
  session. This keeps D3's "the state file exists" check for every `run
  auto` session, and fails fast in the user's own session.
- **Headless runs for start checks, a tmux rehearsal for the stages.** The
  stop table cannot be reached in a headless run without a whole cycle. The
  rehearsal covers four of the 17 rows; the others rest on the prompt text.

## Dependencies

None. Python 3 standard library, tmux, Claude Code and `markdownlint-cli2`,
all installed.

## Risk

- **The rehearsal is costly and slow.** Three full cycles plus one stopped
  run, each with review sessions. Assumed several million tokens in total,
  never measured.
- **Auto mode's safety classifier may deny a step inside the rehearsal,**
  such as `git reset --merge` or the fold. That shows as a stall, not a
  stop. Detection: the Monitor loop's timeout, then `capture-pane`.
- **Most stop rows are tested only as prompt text.** Task 4's content check
  catches a dropped row, not a wrong behaviour. Rows not exercised in
  Task 7: design findings with `decide`, a merge conflict, fold exits 1 and
  3, a weakened assertion, a re-review Critical finding.
- **The guard's word splitting is an approximation of the shell.**
  `bash -c "git push"`, `eval`, `env git push`, `sudo git push` and pushes
  from a script slip through (spec Risk). A parse failure that mentions
  `git` and `push` blocks the command. Since the fix round, `#` is not a
  comment, so a command that bash accepts can also fail to parse and be
  blocked, such as `git status  # don't push yet`. This only blocks too
  much. A quoted
  `<<WORD`, as in `echo "use <<EOF"`, is taken for a heredoc, so the lines
  after it are not checked. This has the same cause as the gaps above: the
  guard reads the heredoc before it reads quotes. The end-of-branch review
  found it; the fix round fixed the other gaps it found (comments, shell
  keywords, `--git-dir`).
- **More pushes the guard does not see (final re-review).** None is fixed,
  because the re-review is final. With `MY_AUTORUN` set, each of these exits
  0: a push inside a double-quoted `$(...)` or inside backticks, such as
  `out="$(git push 2>&1)"`; the wrappers `timeout`, `nice`, `stdbuf`,
  `xargs` and `time -p`; a leading redirect, `>log git push`; the git option
  `--config-env`; and a backslash-newline line continuation between `git`
  and `push`. Of these, `$(...)` is the most likely in an agent's commands.
  The guard is a second line of defence: the stages never run `git push`
  by their own text. Detection: `git -C <bare> show-ref`, or the remote's
  log, after a run.
- **Heredoc forms the guard misreads.** `<<\EOF` is not recognised, and a
  tab before the end word also ends a plain `<<WORD`. Both only block too
  much, never too little.
- **A fold that succeeded, then a crash, blocks resume.** Since the fix
  round, `check` refuses `next=fold` when `head_before_fold` is no longer on
  `<base>`. A successful fold also rewrites history, so a crash between the
  fold's exit 0 and `set next=done` makes every resume print
  `history rewritten`, though nothing is wrong. The way out: read
  `git log <base>`. When no `fixup!` commit is left and the tree looks
  right, run `handoff-state.py set <slug> next=done head_before_fold=`,
  then resume. A row-17 exit 3 that the user accepts needs the same step.
- **A finished fix round, then a crash, blocks resume.** The review restart
  stops with `the fix round already ran` whenever the branch has a
  committed review report, also when the fix round ended cleanly and only
  the merge was left. The way out: run
  `handoff-state.py set <slug> next=merge` after checking the branch, then
  resume. It fails safe.
- **Small `check` gaps.** When the work branch is gone, `next=merge` looks
  for the squash subject in all of `<base>`, so an older commit with the
  same subject is taken for the merge. A detached HEAD in the main checkout,
  or a state file that is not valid JSON, ends in a traceback, so resume's
  refusal shows no reason. A missing branch prints two lines that say the
  same thing. Each needs a hand edit or a deleted branch first.
- **The hook starts Python on every call.** A shell test of `MY_AUTORUN`
  in `hooks.json`, before Python, would remove the cost (see "Blast radius
  of the hook").
- **`handoff-state.py` repeats code from `git-fold-fixups.py`:** the `git()`
  wrapper, the list of in-progress files and the search for waiting fixups.
  The two copies can drift, and then `check` and the fold disagree about
  whether fixups wait. Both scripts are standalone on `PATH`, so sharing a
  module would need an import path. Detection: a resume that `check` passes
  while the fold refuses, or the reverse.
- **`handoff-state.py` takes `<base>` from the main checkout's branch.**
  `SKILL.md` takes it from the project's rules first. In a project whose
  rules name another base, the two disagree, and `check` compares with the
  wrong branch. No project in use names one today.
- **The `Task: <N>` trailer is a new convention.** If the executor forgets it
  on a commit, a restarted code stage redoes that task. Detection: the
  redone task fails its "test fails first" step, which stops the run.
- **Blast radius of the hook.** It runs on every `Bash` and `Monitor` call
  in every session with the plugin. Without `MY_AUTORUN` it exits before it
  reads stdin; Task 1 tests that. A Python start-up costs about 20 ms per
  call.
- **An API error stalls a run silently.** In the rehearsal, `review-autow`
  lost its connection mid-response and sat idle at the prompt. That is not a
  stop point: no `⚠` mark, no notification, nothing in `stopped`. The state
  file still names the right `next`. A typed `continue` in that window
  recovers at once. `resume` works only after the stalled window is closed:
  it launches a window with the same name, and Launch refuses a name that
  is still in use. Detection: a window with no mark that has not changed for
  a long time. This breaks the spec's Goal, end state 2, where a stopped
  run's window says what it needs. Not fixed in this branch; the user
  accepted it as a known limit on 2026-10-12.
- **Memory.** Every stage is a full `claude` process. The rehearsal ran four
  runs at once and reached 13 processes, which left 1.8 GB free on a 15 GB
  machine. One run at a time keeps about 3 processes.

## Testing Strategy

- Unit: `test_block_autorun_push.py` (Task 1) and `test_handoff_state.py`
  (Task 2), run with `cd plugins/my && python3 -m unittest discover tests`.
- End-to-end, guard: Task 1 step 6, a real headless session with an allow
  rule for `git push`.
- Skill start checks and `resume`: headless runs a1 to a9 and r1 to r3.
- The full cycle: Task 7, the four runs of the spec's Testing section.

Rehearsal, 2026-10-12. Each run used its own slug, so Launch's check for a
session with the same name could not collide.

- Plain run (`plainw`): pass. The review stage stopped at
  `ready to squash-merge feat/plainw`, and no window had `MY_AUTORUN`.
- Auto run (`autow`): pass, with one input. After an API connection error,
  `review-autow` sat idle until a typed `continue` (Risk). It then
  squash-merged, set the `done` mark citing the squash commit, and set
  `next` to `finished`. Every launched window had `MY_AUTORUN=autow`, and
  the bare `origin` was unchanged.
- Unlisted dependency (`depw`): pass. The code stage stopped before it made
  a worktree, with `next` `code` and a `stopped` reason naming `requests`.
- Resume (`resw`): pass. The run stopped with `next` `fold` while
  `notes.txt` was untracked. After the window was closed and the file
  removed, `auto resume` launched the review stage, which folded the fixup
  and set the `done` mark. No `fixup!` commit was left, and `origin` was
  unchanged. This run shows a run without input: its code stage, reviews,
  fix round, re-review and merge all ran with none, up to the planned stop
  at the fold.

## Open Questions

None. The silent stall after an API error (Risk) was accepted as a known
limit by the user on 2026-10-12, before the squash-merge.
