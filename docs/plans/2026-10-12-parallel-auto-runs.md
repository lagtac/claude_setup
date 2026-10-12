# Parallel auto runs Implementation Plan

**Status:** done, 2026-10-12. Shipped in 38f6c34. End-of-branch checks: unit tests,
128 passed, 0 failed; Markdown lint counts unchanged. The Task 10 rehearsal
was not run, by the user's choice. Known limits are in the plan's Risk section.

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan task-by-task. The tasks
> build on each other: `start`'s concurrency test needs the lock script, and
> the integration test and `SKILL.md` need all three scripts. The global
> review rules replace that skill's own reviews: run no per-task reviewer and
> no final `requesting-code-review` pass. The `my:handoff` review stage runs
> the end-of-branch reviews. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 2 to 4 `my:handoff auto` runs go at once in one project that has a
"Parallel runs" section, and none of them corrupts `main` or cites a commit
that is not on `main`.

**Architecture:** One new standard-library script, `handoff-lock.py`, runs one
command under a `flock` lock (D2). `handoff-state.py` gains `live`, `start` and
`merge` and three fields (D3, D7). `git-fold-fixups.py` gains a refusal for
cited commits (D6). The rest is prompt text: `SKILL.md`, the global rules,
`/my:commit` and `my:architect` (D1, D4, D5, D8).

**Tech Stack:** Python 3.12 standard library (`fcntl`, `os`, `json`,
`subprocess`, `unittest`), git 2.43, tmux, `markdownlint-cli2`.

**Spec:** `docs/plans/2026-10-12-parallel-auto-runs-spec.md`

## Global Constraints

- Work in the worktree `.claude/worktrees/parallel-auto-runs` on the branch
  `feat/parallel-auto-runs`.
- Conventional Commits with scope: `my-plugin` for files under
  `plugins/my/`. A commit that spans `global/` and `plugins/my/` prose uses
  `docs:` with no scope. Every message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Unit tests: `cd plugins/my && python3 -m unittest discover tests`. Every
  code commit runs them, and all must pass.
- End-of-branch checks: `python3 -m unittest discover plugins/my/tests`
  (the spec's Delegation section), the lint counts below, and the rehearsal
  record from Task 10.
- No new dependencies (spec, Dependencies).
- Read `git diff --cached` before every commit. This project has no
  "Parallel runs" section, so D4's exception does not apply to this branch.
- Markdown lint: count errors with
  `markdownlint-cli2 <file> 2>&1 | grep ' error ' | grep -vc MD013`. The count
  must not rise. On `main` on 2026-10-12 it is 16 for `global/CLAUDE.md` and
  for `plugins/my/skills/architect/SKILL.md`, and 0 for every other file this
  plan edits.
- Match the line style of the paragraph you edit. The handoff files,
  `README.md` and `ROADMAP.md` wrap at 80 characters. `global/CLAUDE.md` is
  mixed: line 122 is one long line, line 61 wraps.
- Fixed copy, word for word:
  - D3: `<name>: another auto run is live (<slug>); this project has no "Parallel runs" section`
    and `<name>: <n> auto runs are live (<slugs>), the most this project allows`.
  - D2, the new last rule of "Rules for every stage": `Wait only inside one
    handoff-lock.py command. Never poll another session across tool calls,
    and never message one.` (with `handoff-lock.py` in backticks).
  - D3, an ended run: `stopped="ended by the user"`.
- The default docs paths are `docs/`, `ROADMAP.md`, `CHANGELOG.md` (D1). A
  path that ends in `/` is a folder; any other path is one file.

## Decisions this plan adds

The spec leaves these open. None changes a D1 to D8 decision. Decision 7
fills D7 for supervised runs, as the user chose after the plan review.

1. **Exit codes of `handoff-lock.py` (D2).** The command's own code passes
   through. The script's own codes are rare in practice: `75` for a lock
   timeout, `64` for a usage error, `74` when the lock file cannot be
   opened, `127` when the command is not found and `126` when it cannot be
   run. Each prints one line on stderr that starts with `handoff-lock:`.
2. **`gc` detaching (D2).** The script adds `gc.autoDetach=false` and
   `maintenance.autoDetach=false` to the command's environment through
   `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_<n>` and `GIT_CONFIG_VALUE_<n>`. It
   adds them after any pairs already there. Git 2.43 reads only the first
   key; newer git reads the second.
3. **`live` lines (D3).** One line per state file whose `next` is not
   `finished`, sorted by slug. The five fields are separated by tabs: slug,
   slot, `next`, `stopped`, branch. A missing field prints as empty. A file
   that is not valid JSON prints `<slug>\t\tunreadable\t\t` and counts as
   live: a broken file must not free a place.
4. **`start` (D3).** It writes a fresh state from the given fields, plus
   `slot` and `merge_retries=0`. A `finished` state of the same slug is
   replaced. Exit `0` prints the slot. Exit `1` refuses and writes nothing,
   with one stderr line: `refused: a run for <slug> exists; use resume` when
   the slug's own state is live, and
   `refused: <k> auto runs are live (<slugs>); the most is <n>` at the cap,
   slugs joined by a comma and a space. Exit `2` is a usage error, an unknown field or an
   unknown `next`, and writes nothing. The `SKILL.md` launch turns the cap
   line into the D3 refusal line.
5. **`merge` (D7).** `handoff-state.py merge <slug> -m <message>
   [--docs-paths <path> ...]`. `--docs-paths` comes last and takes every
   argument after it. Exit codes: `0` merged, and stdout is the squash
   commit's short hash; `1` refused, nothing changed; `2` usage; `4` the base
   moved, nothing changed, and stderr lists the code paths that moved; `5`
   the squash or its commit failed, `git reset --merge` ran, and
   `next=merge` stays. Order of work: refuse when a rebase, merge or
   cherry-pick is in progress, when `branch` or `checked_base` is empty, when
   `next` is neither `merge-retry` nor `merge`, or when the main checkout has
   staged changes (all exit 1). Then refuse with 4 when
   `git diff --name-only --no-renames <checked_base> <base>` lists a path
   outside the docs paths. Then write `squash_subject` (the message's first
   line) and `next=merge`, run `git merge --squash <branch>` and
   `git commit -m <message>`, and on success write `next=worktree-remove`.
   On exit 5, when `git status --porcelain` still prints something, the
   stderr line says `the main checkout is not clean after git reset --merge`.
6. **`merge-retry` (D7).** `NEEDS["merge-retry"]` is `branch`, `worktree`,
   `checked_base`. `check` runs the `review` facts for it: the branch exists
   and is checked out in the worktree. `resume` sends it to the review
   stage with the task doc. A restarted review stage with `next` at
   `merge-retry` is past `review`: the "fix round already ran" stop does not
   apply, and the stage starts at the merge sub-step.
7. **D7 in a supervised run: a check with no state file.** A supervised
   review stage has no state file, so it cannot use `handoff-state.py merge`.
   In a project with the section, just before the squash it runs
   `git diff --name-only --no-renames $(git merge-base <base> <branch>) <base>`.
   When that lists a path outside the docs paths, it signals
   `<name>: <base> gained code since the checks (<paths>); rebase and rerun them?`
   and waits. On the user's yes it runs `git rebase <base>` in the worktree
   (a conflict: `git rebase --abort`, then signal) and reruns the step 2
   checks, then checks again. With no code path listed, it squash-merges
   under lock `main`, as one command:
   `handoff-lock.py main -- sh -c 'git merge --squash "$1" && git commit -m "$2"' sh <branch> "<message>"`,
   which passes the message as an argument for the reason in Decision 10.
   On failure it runs `git reset --merge` and signals. The user chose this on
   2026-10-12, after the plan review, over keeping D7 for auto runs only and
   over a state file for supervised runs.
8. **D6's range.** The new refusal looks at the commits strictly after the
   oldest target, as D6 says. The target itself also gets a new hash; a
   citation of the target is a known limit (Risk). A citation is any
   word of 7 to 40 lowercase hex characters, in a file under the docs paths
   at `HEAD`, that is a prefix of a range commit's full hash. So `%h` with 8
   or more characters, and a full hash, both count. The refusal line is
   `commit <short> is cited in <file>; a fold would give it a new hash`.
9. **Where the docs paths come from.** A session reads them from the
   "Parallel runs" section, or uses the default list. It passes them to
   `git-fold-fixups.py` and `handoff-state.py merge` with `--docs-paths` only
   when the section names a list that differs from the default.
10. **D4's locked form passes the message as an argument.** The spec writes
    `git commit -m "<message>"` inside the single-quoted `sh -c` script. An
    apostrophe in the message would end that quote, and a backtick would
    run as a command; this repo's messages often hold both. So the message
    goes in as `$1`:
    `handoff-lock.py main -- sh -c 'm=$1; shift; git add -- "$@" && git commit -m "$m" -- "$@"' sh "<message>" <paths>`.
    The mechanism is D4's: one locked command that stages and commits. A
    message with a body is one quoted argument with real newlines, written
    with `"$(cat <<'EOF' … EOF)"`.

## Review Focus

- **A lock name with a slash, `..` or nothing.** It would write outside
  `locks/`. The script refuses it with exit 64 and runs nothing. Task 1 tests
  `../x`, `a/b` and the empty name.
- **Leftovers in the state folder.** `live` and `start` read
  `<git common dir>/my-handoff/`, which also holds `locks/` and, after a
  crash, a `.<slug>.*.tmp` file. Neither is a run. A file that is not valid
  JSON is a run (Decision 3). Task 3 tests all three.
- **A done mark that cites a full hash, or an 8-character `%h`.** It must
  count as a citation. Task 2 tests the full hash.
- **A merge message with a body.** `squash_subject` must be the first line
  only, or the review stage cannot find the squash commit by its subject.
  Task 4 tests a two-paragraph message.
- **A merge with `checked_base` missing.** It must refuse with exit 1 and
  change nothing, not merge unchecked code. Task 4 tests it.

## File map

| File | Change | Task |
| --- | --- | --- |
| `plugins/my/bin/handoff-lock.py` | Create (D2) | 1 |
| `plugins/my/tests/test_handoff_lock.py` | Create | 1 |
| `plugins/my/bin/git-fold-fixups.py` | Citation refusal, `--docs-paths` (D6) | 2 |
| `plugins/my/tests/test_git_fold_fixups.py` | Extend | 2 |
| `plugins/my/bin/handoff-state.py` | Fields, `merge-retry`, `live`, `start` (D3, D7) | 3 |
| `plugins/my/bin/handoff-state.py` | `merge` (D7) | 4 |
| `plugins/my/tests/test_handoff_state.py` | Extend | 3, 4 |
| `plugins/my/tests/test_parallel_runs.py` | Create: the integration test | 5 |
| `plugins/my/skills/handoff/SKILL.md` | D1 to D3, stop points, resume | 6 |
| `plugins/my/skills/handoff/SKILL.md` | The stages: D4, D5, D7, D8 | 7 |
| `global/CLAUDE.md` | Lines 60 to 62 (Medium), 170 (reread), Git Workflow lock rule | 8 |
| `global/rules/docs-layout.md` | A paragraph after step 14 | 8 |
| `plugins/my/commands/commit.md` | The locked form (D4) | 8 |
| `plugins/my/skills/architect/SKILL.md` | Line 246, the locked form (D4) | 8 |
| `plugins/my/skills/handoff/README.md` | A "Parallel runs" section | 9 |
| `README.md` | `handoff-lock.py`, lines 107 to 115 | 9 |
| `ROADMAP.md` | A row under "Design workflow" | 9 |

The reference sweep (`git grep` for `git-fold-fixups`, `handoff-state`,
`git diff --cached` and `never poll`, outside `docs/` and `CHANGELOG.md`)
found no caller beyond these files. `global/CLAUDE.md` lines 122 and 178 also
name the `git diff --cached` reread. Task 8 covers them through the
exception it adds at line 170, which says that it replaces every such reread
in the file. The fold's other callers (`docs-layout.md` steps 4, 8, 9, handoff
`README.md` lines 51, 116, 147) pass no `--docs-paths` and keep working with
the default list.

---

### Task 0: Worktree

The `my:handoff` code stage creates it, from the main checkout:
`git worktree add .claude/worktrees/parallel-auto-runs -b feat/parallel-auto-runs`.

- [ ] **Step 1: Confirm**

Run: `cd .claude/worktrees/parallel-auto-runs && git branch --show-current && git status --short`
Expected: `feat/parallel-auto-runs`, and no output from `git status`.

---

### Task 1: The lock script

**Files:**

- Create: `plugins/my/bin/handoff-lock.py` (mode 755)
- Test: `plugins/my/tests/test_handoff_lock.py`

**Interfaces:**

- Produces: the command line
  `handoff-lock.py <name> [--timeout <seconds>] -- <command> [<arg> ...]`;
  the lock file `<git common dir>/my-handoff/locks/<name>.lock`; the exit
  codes of Decision 1. `<name>` must match `[A-Za-z0-9][A-Za-z0-9._-]*` and
  must not contain `..`. `--timeout` takes a number of seconds, default 90,
  and `0` means one try.

- [ ] **Step 1: Write the failing tests**

The fixture follows `test_handoff_state.py`: `clean_env`, `git`, `make_repo`,
a worktree `wt` on `feat/widget`. `PATH` in `clean_env` gets the `bin` folder
first. A holder is started with `subprocess.Popen` and runs
`sh -c 'touch "$0"; exec sleep 30' <ready file>` under the lock. The `exec`
matters: `/bin/sh` is dash here, and without `exec` dash forks `sleep` as a
child that inherits the lock, so killing the holder would not free it. The test waits
until the ready file exists (poll every 0.05 s, 10 s at most). The ready file
appears only after the exec, so a lock that the exec closed fails the first
test. `addCleanup` kills every holder.

```python
LOCK = Path(__file__).resolve().parent.parent / "bin" / "handoff-lock.py"

def test_second_holder_times_out_and_runs_nothing(self):
    self.hold("main", self.repo)
    result = self.lock(self.repo, "main", "--timeout", "0.5", "--", "touch", str(self.marker))
    self.assertEqual(result.returncode, 75)
    self.assertTrue(result.stderr.startswith("handoff-lock:"))
    self.assertFalse(self.marker.exists())

def test_waiter_runs_after_the_holder_ends(self):
    holder = self.hold("main", self.repo, seconds=1)
    result = self.lock(self.repo, "main", "--timeout", "10", "--", "touch", str(self.marker))
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertTrue(self.marker.exists())
    self.assertIsNotNone(holder.poll())

def test_different_name_does_not_wait(self):
    self.hold("main", self.repo)
    self.assertEqual(self.lock(self.repo, "e2e", "--timeout", "0.5", "--", "true").returncode, 0)

def test_killed_holder_frees_the_lock(self):
    holder = self.hold("main", self.repo)
    holder.kill(); holder.wait()
    self.assertEqual(self.lock(self.repo, "main", "--timeout", "0.5", "--", "true").returncode, 0)

def test_worktree_and_main_checkout_share_the_lock(self):
    self.hold("main", self.repo)
    result = self.lock(self.worktree, "main", "--timeout", "0.5", "--", "true")
    self.assertEqual(result.returncode, 75)
    self.assertTrue((self.repo / ".git/my-handoff/locks/main.lock").exists())

def test_exit_code_passes_through(self):
    self.assertEqual(self.lock(self.repo, "main", "--", "sh", "-c", "exit 7").returncode, 7)

def test_gc_does_not_detach_and_existing_pairs_stay(self):
    env = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.name", "GIT_CONFIG_VALUE_0": "Kept"}
    out = self.lock(self.repo, "main", "--", "sh", "-c",
                    "git config gc.autoDetach; git config maintenance.autoDetach; git config user.name",
                    env=env).stdout.split()
    self.assertEqual(out, ["false", "false", "Kept"])

def test_bad_names_are_usage_errors(self):
    for name in ("../x", "a/b", ""):
        result = self.lock(self.repo, name, "--", "touch", str(self.marker))
        self.assertEqual(result.returncode, 64, name)
    self.assertFalse(self.marker.exists())

def test_missing_separator_is_a_usage_error(self):
    self.assertEqual(self.lock(self.repo, "main", "true").returncode, 64)

def test_missing_command_exits_127_and_frees_the_lock(self):
    self.assertEqual(self.lock(self.repo, "main", "--", "no-such-command-xyz").returncode, 127)
    self.assertEqual(self.lock(self.repo, "main", "--timeout", "0.5", "--", "true").returncode, 0)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/my && python3 -m unittest tests.test_handoff_lock -v`
Expected: every test fails, because `handoff-lock.py` does not exist.

- [ ] **Step 3: Implement `main(argv: list[str]) -> int` in `plugins/my/bin/handoff-lock.py`**

A module docstring in the style of `handoff-state.py`: what it does, Usage,
the exit codes. Find the common dir with
`git rev-parse --path-format=absolute --git-common-dir`. Create `locks/` with
`os.makedirs(..., exist_ok=True)`, open the lock file with `os.open(path,
os.O_RDWR | os.O_CREAT, 0o644)`, then try `fcntl.flock(fd, LOCK_EX | LOCK_NB)`
every 0.1 s until the timeout. Call `os.set_inheritable(fd, True)` before
`os.execvpe`: Python opens files non-inheritable, and without this call the
exec closes the lock at once. Add the two `GIT_CONFIG_*` pairs of Decision 2
to the environment. Catch `FileNotFoundError` (127) and `PermissionError`
(126) from the exec.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd plugins/my && python3 -m unittest discover tests`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/bin/handoff-lock.py plugins/my/tests/test_handoff_lock.py
git commit -m "feat(my-plugin): handoff-lock.py runs one command under a named lock"
```

---

### Task 2: The fold refuses to rehash a cited commit

**Files:**

- Modify: `plugins/my/bin/git-fold-fixups.py` (docstring lines 9 to 24,
  `range_refusal` at 182, `main` at 270)
- Test: `plugins/my/tests/test_git_fold_fixups.py`

**Interfaces:**

- Produces: `git-fold-fixups.py [--docs-paths <path> ...]` and
  `git-fold-fixups.py check SHA [--docs-paths <path> ...]`. `--docs-paths`
  comes last and needs at least one path; without it, the D1 default.
  `range_refusal(targets, docs_paths)` returns the line of Decision 8 when it
  applies. `citations(span_commits: list[str], docs_paths: list[str]) ->
  tuple[str, str] | None` returns the first cited commit and its file.

- [ ] **Step 1: Write the failing tests**

The fold test's `commit` helper writes files at the repo root, so the docs
files are `ROADMAP.md` (a default docs path) and `NOTES.md` (not one).

```python
class CitationTest(FoldTestCase):
    def cited_after_target(self, cite_file="ROADMAP.md", full=False):
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        code = commit(self.repo, "feat: code", {"x.py": "x = 1\n"})
        cited = code if full else code[:7]
        commit(self.repo, "docs: done", {cite_file: f"Shipped in {cited}.\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        return target, code

    def test_fold_refuses_a_cited_commit_after_the_target(self):
        _, code = self.cited_after_target()
        before = self.head()
        result = run(self.repo)
        self.assertRefused(result, f"commit {code[:7]} is cited in ROADMAP.md", before)

    def test_check_refuses_a_cited_commit_after_the_target(self):
        target, _ = self.cited_after_target()
        self.assertRefused(run(self.repo, "check", target), "is cited in", self.head())

    def test_full_hash_counts_as_a_citation(self):
        self.cited_after_target(full=True)
        self.assertRefused(run(self.repo), "is cited in", self.head())

    def test_uncited_code_commit_does_not_refuse(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "feat: code", {"x.py": "x = 1\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        self.assertEqual(run(self.repo).returncode, 0)
        self.assertNotIn("fixup! docs: spec", subjects(self.repo))

    def test_citation_outside_the_docs_paths_does_not_refuse(self):
        self.cited_after_target(cite_file="NOTES.md")
        self.assertEqual(run(self.repo).returncode, 0)

    def test_docs_paths_option_changes_the_list(self):
        self.cited_after_target(cite_file="NOTES.md")
        before = self.head()
        self.assertRefused(run(self.repo, "--docs-paths", "NOTES.md"), "is cited in NOTES.md", before)

    def test_docs_paths_without_a_path_is_a_usage_error(self):
        self.assertEqual(run(self.repo, "--docs-paths").returncode, 2)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/my && python3 -m unittest tests.test_git_fold_fixups -v`
Expected: the refusal tests fail (the fold exits 0), the option tests fail
with exit 2, and the two "does not refuse" tests and
`test_docs_paths_without_a_path_is_a_usage_error` pass (today's `main`
rejects any single argument). Those two pass before
and after; they guard D6's limit, so they never had a red step, and Step 4
proves them by a deliberate break: make `citations` always return a hit, and
see both fail. For the usage test, make `--docs-paths` with no path fall
back to the default list, and see it fail.

- [ ] **Step 3: Implement**

Parse `--docs-paths` in `main`, then pass the list to `refusal` and
`check_refusal`, which pass it to `range_refusal`. In `range_refusal`, after
the `squash!`/`amend!` check, collect the hex words at `HEAD` with
`git grep -o -w -E '[0-9a-f]{7,40}' HEAD -- <paths>` (`check=False`: exit
1 means no match). Each line is `HEAD:<file>:<word>`; split it at the first
two colons, and keep the file for the refusal line. Then test each commit of
`git rev-list <oldest>..HEAD` against them, by prefix (Decision 8). A folder
path keeps its trailing `/`, which is a valid pathspec. Add the rule and the
option to the docstring.

- [ ] **Step 4: Run the tests to verify they pass, then the deliberate break**

Run: `cd plugins/my && python3 -m unittest discover tests`
Expected: all pass. Then the break of Step 2, then undo it.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/bin/git-fold-fixups.py plugins/my/tests/test_git_fold_fixups.py
git commit -m "feat(my-plugin): git-fold-fixups refuses to rehash a cited commit"
```

---

### Task 3: State: new fields, `merge-retry`, `live` and `start`

**Files:**

- Modify: `plugins/my/bin/handoff-state.py` (docstring, `FIELDS` at 43,
  `STEPS` at 45, `NEEDS` at 47, `facts` at 173, `main` at 256)
- Test: `plugins/my/tests/test_handoff_state.py`

**Interfaces:**

- Consumes: `handoff-lock.py` (Task 1), only in the concurrency test.
- Produces: fields `slot`, `checked_base`, `merge_retries`; `next` value
  `merge-retry` with the `NEEDS` and facts of Decision 6;
  `handoff-state.py live` (no slug) with the lines of Decision 3;
  `handoff-state.py start <slug> --max <n> <field>=<value> ...` with the
  behaviour of Decision 4. `live_states() -> list[tuple[str, dict | None]]`,
  with `None` for an unreadable file, is shared by `live` and `start`.

- [ ] **Step 1: Write the failing tests**

```python
class FieldsTest(StateTestCase):
    def test_new_fields_and_next_value(self):
        self.state("slot=2", "checked_base=abc", "merge_retries=1", "next=merge-retry")
        self.assertEqual({k: self.get()[k] for k in ("slot", "checked_base", "merge_retries", "next")},
                         {"slot": "2", "checked_base": "abc", "merge_retries": "1", "next": "merge-retry"})

    def test_check_merge_retry_needs_checked_base(self):
        self.full("merge-retry")
        self.assertCheck(self.check(), 1, ["missing field: checked_base"])

    def test_check_merge_retry_matches(self):
        self.full("merge-retry", checked_base=git(self.repo, "rev-parse", "main"))
        self.assertCheck(self.check(), 0, [])

class LiveTest(StateTestCase):
    def test_live_lists_runs_that_are_not_finished(self):
        run(self.repo, "set", "a", "slot=1", "next=code", "branch=feat/a")
        run(self.repo, "set", "b", "slot=2", "next=finished")
        run(self.repo, "set", "c", "slot=3", "next=review", "stopped=tests failed")
        result = run(self.repo, "live")
        self.assertEqual(result.stdout.splitlines(),
                         ["a\t1\tcode\t\tfeat/a", "c\t3\treview\ttests failed\t"])

    def test_live_ignores_locks_and_temporary_files_and_counts_unreadable_ones(self):
        folder = self.repo / ".git" / "my-handoff"
        (folder / "locks").mkdir(parents=True)
        (folder / "locks" / "main.lock").write_text("")
        (folder / ".a.x1.tmp").write_text("{")
        (folder / "d.json").write_text("{")
        self.assertEqual(run(self.repo, "live").stdout.splitlines(), ["d\t\tunreadable\t\t"])

class StartTest(StateTestCase):
    def start(self, slug, n=2, *pairs):
        return run(self.repo, "start", slug, "--max", str(n), "next=code", *pairs)

    def test_start_takes_the_lowest_free_slot(self):
        self.assertEqual(self.start("a").stdout.strip(), "1")
        self.assertEqual(self.start("b").stdout.strip(), "2")
        run(self.repo, "set", "a", "next=finished")
        self.assertEqual(self.start("c").stdout.strip(), "1")
        state = json.loads(run(self.repo, "get", "c").stdout)
        self.assertEqual((state["slot"], state["merge_retries"], state["next"]), ("1", "0", "code"))

    def test_cap_refuses_and_writes_nothing(self):
        self.start("a"); self.start("b")
        result = self.start("c")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: 2 auto runs are live (a, b); the most is 2", result.stderr)
        self.assertEqual(run(self.repo, "get", "c").returncode, 1)

    def test_own_live_run_refuses_and_leaves_the_file(self):
        self.start("a", 2, "spec=one")
        result = self.start("a", 2, "spec=two")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: a run for a exists; use resume", result.stderr)
        self.assertEqual(json.loads(run(self.repo, "get", "a").stdout)["spec"], "one")

    def test_finished_own_run_is_replaced(self):
        run(self.repo, "set", "a", "next=finished", "stopped=old")
        self.assertEqual(self.start("a").returncode, 0)
        self.assertNotIn("stopped", json.loads(run(self.repo, "get", "a").stdout))

    def test_usage_errors_write_nothing(self):
        for args in (["start", "a", "--max", "0", "next=code"], ["start", "a", "--max", "x"],
                     ["start", "a", "next=code"], ["start", "a", "--max", "2", "colour=red"],
                     ["start", "a", "--max", "2", "next=nowhere"]):
            self.assertEqual(run(self.repo, *args).returncode, 2, args)
        self.assertEqual(run(self.repo, "get", "a").returncode, 1)

    def test_unreadable_state_counts_toward_the_cap(self):
        folder = self.repo / ".git" / "my-handoff"; folder.mkdir()
        (folder / "d.json").write_text("{")
        self.assertEqual(self.start("a", 1).returncode, 1)

    def test_concurrent_locked_starts_never_pass_the_cap(self):
        procs = [subprocess.Popen([sys.executable, str(LOCK), "main", "--", sys.executable, str(SCRIPT),
                                   "start", f"s{i}", "--max", "2", "next=code"],
                                  cwd=self.repo, env=clean_env(), stdout=subprocess.PIPE, text=True)
                 for i in range(4)]
        outs = [(p.wait(timeout=60), p.stdout.read().strip()) for p in procs]
        self.assertEqual(sorted(code for code, _ in outs), [0, 0, 1, 1])
        self.assertEqual(sorted(slot for code, slot in outs if code == 0), ["1", "2"])

    def test_lock_timeout_writes_nothing(self):
        self.hold("main", self.repo)             # the holder helper from Task 1
        result = subprocess.run([sys.executable, str(LOCK), "main", "--timeout", "0.5", "--",
                                 sys.executable, str(SCRIPT), "start", "a", "--max", "2", "next=code"],
                                cwd=self.repo, env=clean_env(), capture_output=True, text=True)
        self.assertEqual(result.returncode, 75)
        self.assertEqual(run(self.repo, "get", "a").returncode, 1)
```

`LOCK` and the holder helper are the ones from Task 1; copy them into this
file, as the test files already copy `clean_env` and `git`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/my && python3 -m unittest tests.test_handoff_state -v`
Expected: the new tests fail with exit 2 (unknown field, unknown next, or
usage). The old tests pass. Two new tests pass before and after:
`test_usage_errors_write_nothing` (today an unknown command is a usage
error) and `test_lock_timeout_writes_nothing` (Task 1 already makes it
green). Step 4 proves them by deliberate breaks: make `start` accept
`--max 0` and see the first fail; drop `main` from the lock command and run
`start` directly, and see the second fail. Undo both.

- [ ] **Step 3: Implement**

Add the fields and `merge-retry`; `NEEDS["merge-retry"] =
("branch", "worktree", "checked_base")`; in `facts`, treat `merge-retry` as
`review`. `live_states` lists `*.json` in the state folder, skips names that
start with `.`, and keeps states whose `next` is not `finished` (a missing
`next` is live). `start` validates every pair as `set_fields` does, before it
reads anything. `main` accepts `live` with no slug. Update the docstring:
Usage, Fields, the exit codes of `start`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd plugins/my && python3 -m unittest discover tests`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/bin/handoff-state.py plugins/my/tests/test_handoff_state.py
git commit -m "feat(my-plugin): handoff-state live and start keep a cap on auto runs"
```

---

### Task 4: State: `merge`

**Files:**

- Modify: `plugins/my/bin/handoff-state.py`
- Test: `plugins/my/tests/test_handoff_state.py`

**Interfaces:**

- Consumes: `Repo`, `read_state`, `write_state` (existing); the fields of
  Task 3.
- Produces: `handoff-state.py merge <slug> -m <message> [--docs-paths <path> ...]`
  with the behaviour and exit codes of Decision 5.
  `merge(slug: str, message: str, docs_paths: list[str]) -> int`.

- [ ] **Step 1: Write the failing tests**

`StateTestCase` already has `main` with the spec and plan and `feat/widget`
with `widget.py`. `ready()` sets the full state with
`next=merge-retry` and `checked_base` = `git merge-base main feat/widget`. It also passes `squash_subject=` (empty), which
overrides `full`'s value, so the tests prove that `merge` writes the subject.

```python
class MergeTest(StateTestCase):
    MESSAGE = SUBJECT + "\n\nThe body.\n\nCo-Authored-By: X <x@example.com>"

    def ready(self, **extra):
        self.full("merge-retry", checked_base=git(self.repo, "merge-base", "main", "feat/widget"),
                  squash_subject="", **extra)

    def merge(self, *extra):
        return run(self.repo, "merge", "widget", "-m", self.MESSAGE, *extra)

    def test_merge_lands_the_squash_and_moves_next(self):
        self.ready()
        result = self.merge()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), git(self.repo, "rev-parse", "--short", "HEAD"))
        self.assertEqual(git(self.repo, "log", "-1", "--format=%s"), SUBJECT)
        state = self.get()
        self.assertEqual((state["next"], state["squash_subject"]), ("worktree-remove", SUBJECT))

    def test_refuses_staged_changes(self):
        self.ready(); before = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "staged.md").write_text("x\n"); git(self.repo, "add", "staged.md")
        result = self.merge()
        self.assertEqual(result.returncode, 1)
        self.assertIn("staged changes", result.stderr)
        self.assertEqual((git(self.repo, "rev-parse", "HEAD"), self.get()["next"]), (before, "merge-retry"))

    def test_refuses_when_code_moved_on_the_base(self):
        self.ready(); commit(self.repo, "feat: other", {"other.py": "y = 2\n"})
        before = git(self.repo, "rev-parse", "HEAD")
        result = self.merge()
        self.assertEqual(result.returncode, 4)
        self.assertIn("other.py", result.stderr)
        self.assertEqual((git(self.repo, "rev-parse", "HEAD"), self.get()["next"]), (before, "merge-retry"))

    def test_docs_only_move_still_merges(self):
        self.ready(); commit(self.repo, "docs: roadmap", {"ROADMAP.md": "row\n"})
        self.assertEqual(self.merge().returncode, 0)

    def test_docs_paths_option_changes_the_list(self):
        self.ready(); commit(self.repo, "docs: notes", {"NOTES.md": "n\n"})
        self.assertEqual(self.merge().returncode, 4)
        self.assertEqual(self.merge("--docs-paths", "NOTES.md").returncode, 0)

    def test_squash_conflict_resets_and_keeps_next_merge(self):
        commit(self.worktree, "docs: branch roadmap", {"ROADMAP.md": "branch\n"})
        self.ready(); commit(self.repo, "docs: main roadmap", {"ROADMAP.md": "main\n"})
        before = git(self.repo, "rev-parse", "HEAD")
        result = self.merge()
        self.assertEqual(result.returncode, 5)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), before)
        self.assertEqual((self.get()["next"], self.get()["squash_subject"]), ("merge", SUBJECT))

    def test_failed_commit_resets(self):
        self.ready()
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n"); hook.chmod(0o755)
        self.assertEqual(self.merge().returncode, 5)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_missing_checked_base_refuses(self):
        self.full("merge-retry")
        result = self.merge()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing field: checked_base", result.stderr)
        self.assertEqual(git(self.repo, "log", "-1", "--format=%s"), "docs(plans): plan for the widget")

    def test_wrong_next_refuses(self):
        self.ready(); self.state("next=review")
        self.assertEqual(self.merge().returncode, 1)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd plugins/my && python3 -m unittest tests.test_handoff_state.MergeTest -v`
Expected: all fail with exit 2 (usage: `merge` is unknown).

- [ ] **Step 3: Implement `merge`**

Follow the order in Decision 5. Run every git command in `repo.root`. A path
is a docs path when it equals an entry, or the entry ends in `/` and the path
starts with it. `-m` must come right after the slug; `--docs-paths`, when
present, comes last. Update the docstring: Usage and the exit codes of
`merge`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd plugins/my && python3 -m unittest discover tests`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/bin/handoff-state.py plugins/my/tests/test_handoff_state.py
git commit -m "feat(my-plugin): handoff-state merge lands only code checked on the base"
```

---

### Task 5: The integration test

**Files:**

- Create: `plugins/my/tests/test_parallel_runs.py`

**Interfaces:**

- Consumes: `handoff-lock.py` (Task 1), `git-fold-fixups.py` (Task 2),
  `handoff-state.py` `start`, `set`, `merge` (Tasks 3, 4). The test calls
  only these scripts and `git`, with `bin/` first on `PATH`.

- [ ] **Step 1: Write the test**

One fixture repo: `main` holds `app.py` with two functions, `alpha` and
`beta`, ten lines apart, and the specs `docs/plans/2026-10-12-a-spec.md` and
`-b-spec.md`. Helpers, each a few lines:

- `start(slug)`: `handoff-lock.py main -- handoff-state.py start <slug> --max 2 spec=… task_doc=… next=code`.
- `build(slug, func)`: a worktree `wt-<slug>` on `feat/<slug>` that changes
  only `func` in `app.py`, one commit, then
  `set <slug> branch=feat/<slug> worktree=<path>`, as the code stage does.
- `checks_pass(slug)`: in the worktree, `python3 -c "import app"` exits 0,
  then `set <slug> checked_base=$(git merge-base main feat/<slug>)
  next=merge-retry`.
- `merge(slug)`: `handoff-lock.py main -- handoff-state.py merge <slug> -m "feat(<slug>): <slug>"`.
- `retry(slug)`: in the worktree, `git rebase main`, then `checks_pass`, then
  `set <slug> merge_retries=1`.
- `on_main(short)`: `git merge-base --is-ancestor <short> main` exits 0.
- `done(slug, short)`: under lock `main`, set the spec's status line to
  `**Status:** done, 2026-10-12. Shipped in <short>.` and commit it.

```python
class ParallelRunsTest(unittest.TestCase):
    def test_a_merges_after_b_checks(self):
        self.start("a"); self.start("b")
        self.assertIn("2 auto runs are live (a, b)", self.start_result("c").stderr)
        self.build("a", "alpha"); self.build("b", "beta")
        self.checks_pass("a"); self.checks_pass("b")
        self.finish("a")
        self.assertEqual(self.merge("b").returncode, 4)
        self.retry("b")
        self.finish("b")
        self.assert_citations_on_main()

    def test_a_merges_before_b_checks(self):
        self.start("a"); self.start("b")
        self.build("a", "alpha"); self.build("b", "beta")
        self.checks_pass("a"); self.finish("a")
        self.checks_pass("b")
        self.assertEqual(self.merge("b").returncode, 4)
        self.retry("b")
        self.finish("b")
        self.assert_citations_on_main()

    def finish(self, slug):
        result = self.merge(slug)
        self.assertEqual(result.returncode, 0, result.stderr)
        git(self.repo, "worktree", "remove", str(self.tmp / f"wt-{slug}"))
        self.done(slug, result.stdout.strip())
        self.set(slug, "next=finished")

    def assert_citations_on_main(self):
        cited = re.findall(r"Shipped in ([0-9a-f]{7,})", git(self.repo, "grep", "-h", "Shipped in", "--", "docs/"))
        self.assertEqual(len(cited), 2)
        for short in cited:
            self.assertTrue(self.on_main(short), short)   # git merge-base --is-ancestor exits 0
        self.assertIn("def alpha", (self.repo / "app.py").read_text())
        # A fixup of a's spec now spans b's cited squash commit: D6 refuses it.
        spec_a = git(self.repo, "log", "--diff-filter=A", "--format=%H", "-1", "--", "docs/plans/2026-10-12-a-spec.md")
        self.assertEqual(self.fold("check", spec_a).returncode, 1)
```

Both runs' changes must be on `main` at the end: also assert that `app.py`
holds both new function bodies. The two tests share all helpers;
`start_result` returns the `CompletedProcess` that `start` asserts on.

- [ ] **Step 2: Run the test**

Run: `cd plugins/my && python3 -m unittest tests.test_parallel_runs -v`
Expected: both tests pass. Tasks 1 to 4 already make them green, so this
test has no red step of its own. Prove it by a deliberate break: in
`handoff-state.py`, make the base-moved check compare against `<base>`'s tip
instead of `checked_base`. Then `test_a_merges_after_b_checks` fails at
`assertEqual(self.merge("b").returncode, 4)`, because B's first merge
succeeds. Undo the break.

- [ ] **Step 3: Commit**

```bash
git add plugins/my/tests/test_parallel_runs.py
git commit -m "test(my-plugin): two simulated auto runs merge through the real scripts"
```

---

### Task 6: `SKILL.md`: the section, the start, the rules, the stop points, resume

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md`

**Interfaces:**

- Consumes: the command lines and exit codes of Tasks 1, 3, 4; Decisions 3,
  4, 6, 9.

- [ ] **Step 1: Add a section "## Parallel runs"** after "### Delegation"
  (line 85) and its table. It says: what D1's four keys mean and their
  defaults (the D1 table, copied); that a project "has the section" when its
  `CLAUDE.md` or `CLAUDE.local.md` holds a heading titled `Parallel runs`;
  that without it only the locked start (`--max 1`) and the fold refusal of
  D6 apply; how sessions pass the docs paths (Decision 9); and the
  `handoff-lock.py` command line with its exit codes (Decision 1).

- [ ] **Step 2: Replace the auto launch's state creation** (lines 390 to
  400). The `handoff-state.py set <slug> spec=… stopped=` block becomes
  `handoff-lock.py main -- handoff-state.py start <slug> --max <n> spec=<spec>
  task_doc=<task doc> next=<stage> branch= worktree= squash_subject=
  head_before_fold= stopped= checked_base= merge_retries=0`, with `<n>` from
  **Max runs**, or `1` without the section. Then the refusals: exit 1 with the
  cap line becomes one of the two D3 lines (the first when there is no
  section); exit 1 with `a run for <slug> exists; use resume` stays that
  line; any other non-zero exit, a timeout included, prints the script's
  message. All of them are failed start checks: signal, write nothing (D3).
  Start check 5 stays as it is.

- [ ] **Step 3: Add "To end an abandoned run"** under "## Resume", as D3's last
  paragraph says, with `--force` only after the user's yes.

- [ ] **Step 4: Resume and restarts for `merge-retry`** (Decision 6). Resume
  step 3: `merge-retry` joins the list that maps to the review stage. Resume
  step 4: in a project with the section, also run
  `handoff-state.py set <slug> merge_retries=0`. Start check 6 (line 377):
  `merge-retry` joins the list for `run auto review`. "Restarted stages":
  `merge-retry` is past `review`, so the stage starts at the merge sub-step
  and the "fix round already ran" stop does not apply.

- [ ] **Step 5: Stop points.** Add rows 18 to 23 to the table at line 141:
  the six rows of the spec's "Stop points" section, in its order, with its
  `next` values. Below the table, add the spec's note that rows 5, 16 and 17
  cannot arise with the section, and that a refused start is not a stop.

- [ ] **Step 6: Rules for every stage** (line 698). Replace "After a signal,
  stop. Never poll for another session." with "After a signal, stop." plus
  the D2 rule from Global Constraints, word for word, and D2's sentence on
  busy resources: a resource named under **Shared resources** is waited for
  under its lock; any other busy resource is still a gate. The rule before
  it, "When a shared resource … is busy … that is a gate", gets the same
  exception.

- [ ] **Step 7: Verify**

Run: `grep -c 'handoff-lock.py main -- handoff-state.py start' plugins/my/skills/handoff/SKILL.md`
Expected: 1 or more. Then
`grep -F 'this project has no "Parallel runs" section' plugins/my/skills/handoff/SKILL.md`
and `grep -F 'the most this project allows' plugins/my/skills/handoff/SKILL.md`
each print one line, and `grep -c 'Never poll for another session' …` prints
`0`. Lint count stays 0.

- [ ] **Step 8: Commit**

```bash
git add plugins/my/skills/handoff/SKILL.md
git commit -m "feat(my-plugin): handoff starts auto runs under a lock with a cap"
```

---

### Task 7: `SKILL.md`: the stages with the section

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md`

**Interfaces:**

- Consumes: Task 6's "Parallel runs" section; `merge` (Task 4); Decision 7.

Each change below is one paragraph headed **With a "Parallel runs" section,**
placed after the step it changes, in the style of the existing **In auto
mode,** paragraphs. Without the section, every step reads as today.

- [ ] **Step 1: D4, the locked commit.** Plan stage step 7 (line 439): the
  commit becomes D4's locked form as Decision 10 writes it, with `git diff -- <paths>` read before it
  and `git show --stat --format= HEAD` after it. The same form for the auto
  code stage's `approved` commit (line 516), and for the `done` marks in
  Review stage step 8.4 and auto sub-step 4. Subagents commit only in their
  worktree, so their prompts do not change.

- [ ] **Step 2: D5, no fixups and shared docs.** Plan stage step 8, the auto
  code stage's steps 1 and 2, Review stage step 8.3 and auto sub-step 3: skip
  the fold; the auto code stage commits the `approved` edit as a normal
  `docs:` commit, never `--fixup`. Plan stage step 6 and every `done` mark:
  before editing `ROADMAP.md`, `CHANGELOG.md` or the plans index, run
  `git diff --quiet HEAD -- <file>`; before the commit, check that every hunk
  in the file is this stage's own. Either check failing is a stop (row 19).

- [ ] **Step 3: D7, the merge in auto mode.** Review stage, auto mode: right
  after the step 2 checks, run
  `handoff-state.py set <slug> checked_base=$(git -C <worktree> merge-base <base> <branch>)`.
  After the step 6 fix round is committed, run
  `handoff-state.py set <slug> next=merge-retry`. Auto sub-step 1 becomes
  `handoff-lock.py main -- handoff-state.py merge <slug> -m "<message>"`
  (plus `--docs-paths` per Decision 9), and it no longer runs
  `set squash_subject`, `git merge --squash` or `set next=worktree-remove`,
  because `merge` does all three. Exit 4: in the worktree, `git rebase <base>`
  (a conflict: `git rebase --abort`, row 20), rerun the step 2 checks, set
  `checked_base` again, add 1 to `merge_retries`, run `merge` again; when
  `merge_retries` would pass 3, stop (row 21). Exit 5 is row 22. Any other
  failure is row 23. A session whose state has `next` at `merge-retry` starts
  at this sub-step.

- [ ] **Step 4: Decision 7, the supervised merge.** Review stage step 8.1,
  with the section and without auto: the base-moved check, its signal and
  the rebase on the user's yes, then the locked one-command squash merge,
  all as Decision 7 says.

- [ ] **Step 5: D8, test stacks.** Code stage step 2 and Review stage step 2:
  apply the **Isolation** line, with `<slug>` and `<slot>` filled in (the slot
  from `handoff-state.py get <slug>`; a supervised run uses slot `1`), to
  every test and server command. Every **Shared resources** command runs as
  `handoff-lock.py <name> --timeout 3600 -- <command>` with
  `run_in_background`. Review stage step 4's prompt block, and any subagent
  prompt the code stage writes, gains two lines: the filled-in Isolation
  values, and the locked form of each shared-resource command.

- [ ] **Step 6: Verify**

Run: `grep -c 'With a "Parallel runs" section,' plugins/my/skills/handoff/SKILL.md`
Expected: 8 or more (plan steps 6 to 8, the auto code stage, code step 2,
review steps 2, 4 and 8). Then
`grep -c 'handoff-lock.py main -- handoff-state.py merge' …` prints 1 or
more. Lint count stays 0. Read the whole Review stage once from top to bottom
and check that a run without the section reads exactly as before.

- [ ] **Step 7: Commit**

```bash
git add plugins/my/skills/handoff/SKILL.md
git commit -m "feat(my-plugin): handoff stages lock main, skip folds and retry the merge"
```

---

### Task 8: Rule text for every session

**Files:**

- Modify: `global/CLAUDE.md:60-62`, `global/CLAUDE.md:170`
- Modify: `global/rules/docs-layout.md` (after the list at line 166)
- Modify: `plugins/my/commands/commit.md` (after the "Project rules first"
  paragraph, line 9)
- Modify: `plugins/my/skills/architect/SKILL.md:243-247`

**Interfaces:**

- Consumes: D4's locked form as Decision 10 writes it, in every file,
  because a reader of one file must not need another:
  `handoff-lock.py main -- sh -c 'm=$1; shift; git add -- "$@" && git commit -m "$m" -- "$@"' sh "<message>" <paths>`.

- [ ] **Step 1: `global/CLAUDE.md`.** Line 170: add the D4 exception. In a
  project with a "Parallel runs" section, a commit in the main checkout reads
  `git diff -- <paths>` before the locked form and `git show --stat HEAD`
  after it, and this replaces every `git diff --cached` reread this file
  names. A new bullet after it: in such a project, every commit in the main
  checkout runs under `handoff-lock.py main`, and nobody makes fixups.
  Lines 60 to 62, the Medium paragraph: in a project with the section, the
  `approved` edit is a normal commit, not a fixup, and there is no fold.

- [ ] **Step 2: `global/rules/docs-layout.md`.** One paragraph after step 14:
  in a project with a "Parallel runs" section, every commit in the main
  checkout runs under `handoff-lock.py main`, steps 4 and 8 make normal
  commits, and step 9 is skipped. Four commits remain the goal elsewhere.

- [ ] **Step 3: `plugins/my/commands/commit.md`.** A paragraph headed
  **Parallel runs.**: when the project has the section and `git rev-parse
  --git-dir` equals `git rev-parse --git-common-dir` (the main checkout),
  step 3 does not stage; step 5 reads `git diff -- <paths>`; each group
  commits with the locked form; step 7 also runs `git show --stat HEAD`.

- [ ] **Step 4: `plugins/my/skills/architect/SKILL.md`.** After the commit
  block at line 246: in a project with the section, commit the brief with the
  locked form instead.

- [ ] **Step 5: Verify**

Run: `grep -l 'handoff-lock.py main' global/CLAUDE.md global/rules/docs-layout.md plugins/my/commands/commit.md plugins/my/skills/architect/SKILL.md`
Expected: all four paths. Lint counts: 16, 0, 0, 16.

- [ ] **Step 6: Commit**

```bash
git add global/CLAUDE.md global/rules/docs-layout.md plugins/my/commands/commit.md plugins/my/skills/architect/SKILL.md
git commit -m "docs: commits in the main checkout take lock main in a project with parallel runs"
```

---

### Task 9: Docs for a reader

**Files:**

- Modify: `plugins/my/skills/handoff/README.md` (a new "### Parallel runs"
  section under "## Auto mode", before "### Known problems" at line 331)
- Modify: `README.md:107-115`
- Modify: `ROADMAP.md` (the "Design workflow" list at line 35)

- [ ] **Step 1: Write the three edits.**
  - Handoff README: what the section is, with the D1 example block; the cap
    and how to end an abandoned run; that a merge reruns the checks when
    `main` moved; that nobody makes fixups there. Name the spec and this plan.
  - `README.md`: one sentence after the `handoff-state.py` sentence:
    `handoff-lock.py`, in the same folder, runs one command under a named
    lock, so that parallel auto runs take turns in the main checkout.
  - `ROADMAP.md`: a 🚧 row **Parallel auto runs** after the `my:handoff auto`
    row, with links to the brief, the spec and this plan. The `done` marks
    move it to ✅.

- [ ] **Step 2: Verify**

Run: the lint count for the three files.
Expected: 0 each.

- [ ] **Step 3: Commit**

```bash
git add plugins/my/skills/handoff/README.md README.md ROADMAP.md
git commit -m "docs: parallel auto runs in the handoff README, README and roadmap"
```

---

### Task 10: Rehearsal, started by the user

**Files:**

- Create in the scratchpad only: the fixture, its bare `origin`, and
  `$SCRATCH/rehearsal.md`. The repo gets only the result summary, in Step 4.

**Interfaces:**

- Consumes: everything above, through `--plugin-dir "$WT/plugins/my"`.

- [ ] **Step 1: Build the fixture.** A repo with `app.py` (functions `alpha`
  and `beta`, ten lines apart), a `CLAUDE.md` with a "Parallel runs" section
  (`Max runs: 2`, the default docs paths, `Isolation: none needed`,
  `Shared resources: none`), and three approved Medium specs, `alpha`, `beta`
  and `gamma`, each with a Tasks section of one task and a Delegation section
  whose check is `python3 -c "import app"`. `alpha` changes only `alpha`,
  `beta` only `beta`. A bare repo is `origin`, pushed once without `-u`.
  Record `git -C <bare> show-ref`.

- [ ] **Step 2: Gate: the user starts the runs.** Signal
  `code-parallel-auto-runs: rehearsal fixture ready; start the runs as printed`,
  and print, for the user to type: first
  `tmux -L parallel new-session -d -s rehearsal -c <fixture>` and
  `tmux -L parallel attach -t rehearsal` (no server runs on that socket
  yet), then `tmux -L parallel new-window -c <fixture>
  "claude --plugin-dir $WT/plugins/my --permission-mode auto '/my:handoff auto code docs/plans/<date>-alpha-spec.md'"`,
  the same for `beta`, and once both are live, the same for `gamma`. Then
  stop and wait for the user's reply.

- [ ] **Step 3: Check, after the user's reply.**
  - The `gamma` start printed `<n> auto runs are live (alpha, beta), the most this project allows` and wrote no state file.
  - Both runs end with `done` marks on `main`; one of them has
    `merge_retries` `1` or more in `handoff-state.py get`.
  - Every hash in the `done` marks is on `main`.
  - `git -C <bare> show-ref` is unchanged.

  A failed expectation is a bug in Tasks 1 to 7: use
  `superpowers:systematic-debugging`, fix it with a test where one applies,
  commit, and ask the user to rerun on a new fixture.

- [ ] **Step 4: Record**

Write each check (expected, seen, pass or fail) into `$SCRATCH/rehearsal.md`.
Append a "Rehearsal, `<date>`" list with the four results to this plan's
**Testing Strategy**, and commit it in the worktree:

```bash
git add docs/plans/2026-10-12-parallel-auto-runs.md
git commit -m "docs(plans): rehearsal results for parallel auto runs"
```

Stop the server: `tmux -L parallel kill-server`.

---

## Trade-Offs

- **One holder helper copied into two test files** versus a shared test
  module. The test files already copy `clean_env` and `git` each; a shared
  module would be the first in `tests/`. Copying matches the code around it.
- **`SKILL.md` in two tasks.** Task 6 changes what runs at the start and
  across stages; Task 7 changes the stages. A reviewer can accept one and
  reject the other.
- **The rehearsal as a gate in the code stage** versus a step of the review
  stage. The spec asks for it before the `done` marks, started by the user.
  In the code stage, a failure is fixed on the branch before the reviews read
  it.

## Dependencies

None. Python 3 standard library, git, tmux and Claude Code, as the spec says.

## Risk

- **Every risk in the spec's Risk section holds,** unchanged.
- **A citation of the fold's target itself is not refused** (Decision 8). The
  target gets a new hash too. Specs are seldom cited by hash, because reviews
  name sections, not hashes ("Cite only commits on `main`").
- **The locked start runs in every project** (D1, D3). A state file left
  live by a crashed run blocks every later auto start in a project without
  the section, until the user ends it (D3's paragraph). This repo has no
  state files today.
- **A hex word in a doc that is not a citation**, such as a colour or a
  checksum, can make the fold refuse a safe fold. The refusal is the safe
  direction, and its line names the file.
- **`SKILL.md` has no automated test.** Its new paragraphs are checked by the
  greps in Tasks 6 and 7 and by the rehearsal. The rehearsal does not cover a
  shared resource, a rebase conflict or the supervised merge (Decision 7).
- **The supervised base-moved check runs once, just before the squash.** An
  auto run that merges code between that check and the locked squash, a few
  seconds, lands unchecked. The auto path closes this inside `merge`, under
  the lock; the supervised path does not.
- **A fix-round change in the review stage is not rehearsed again.**
- **A killed command's children keep the lock.** D2's "the kernel frees the
  lock when the command dies" holds only when no child outlives it. A
  `sh -c` that forks a test runner, then is killed, leaves the runner
  holding the lock until it ends. Detection: the next lock times out, and
  its line names the lock. The Task 1 holder uses `exec` for this reason.
- **A fixup that D6 refuses to fold stays on `main`.** In a project without
  the section, the run stops at row 17, and `check` reports `fixup waits`
  for the `done` step until the user acts. The way out is the user's: keep
  the fixup as it is and fold it once the citation is gone, or leave it.
  No commit after this spec's target is cited in this repo's docs today.
- **A docs path without a trailing `/` means one file in `handoff-state.py`,
  but git reads it as a folder too.** So `**Docs paths:** docs` would make
  `merge` treat every `docs/` change as code (exit 4, then row 21), while
  `git-fold-fixups.py` would search the folder. The default list and the
  "Parallel runs" rule both write folders with `/`, so no project produces
  this today. Found by the end-of-branch code review.
- **`gc.autoDetach=false` (Decision 2) runs git's automatic cleanup inside
  lock `main`.** In a large repo a cleanup longer than the 90 s timeout makes
  the other waiting runs time out (row 18). Keeping the cleanup inside the
  lock is Decision 2's choice: a detached cleanup would outlive the lock.
  Found by the end-of-branch code review; the decision stands unchanged.
- **`live` joins state values as text.** A state value that is not a string,
  for example from a hand edit, would crash `live` and `status-scan.py`'s
  `runs` block. Every write path stores strings today. Found by the
  end-of-branch code review.
- **A locked command's own run time comes on top of the lock wait.** The
  lock waits up to 90 s, and a slow commit hook can push the whole command
  past the Bash tool's 120 s limit. A command killed mid-commit can leave
  `index.lock` behind, which blocks later commits until it is removed.
  Detection: the next commit names `index.lock`. Found by the end-of-branch
  soundness review; it depends on each project's hooks.
- **Decisions 7 and 10 and Task 8's Interfaces line still show the
  pre-review forms:** a double-quoted `"<message>"`, the claim that a
  backtick in it is safe, and a supervised squash that resets outside the
  lock. The end-of-branch fix round replaced them; the prose files on the
  branch, not this plan, hold the current forms. Found by the soundness
  re-review.
- **`merge`'s cleanness check after `git reset --merge` reads the whole
  main checkout.** Another session's uncommitted file makes the exit 5 line
  say the checkout is not clean, though the reset worked. Found by the code
  re-review.
- **`squash_subject` stores the message's raw first line.** A message whose
  first paragraph has two lines, or whose subject ends in a space, no longer
  matches git's `%s`, so `check` and the `done` step cannot find the squash
  commit. The handoff messages have a one-line subject and a blank line
  today. Found by the code re-review.
- **Every child of a locked command holds the lock.** Turning off gc's
  detaching covers one kind of long-lived child. A hook that starts a
  background process, or git's fsmonitor daemon on macOS or Windows, would
  hold lock `main` until it ends (row 18). Found by the code re-review.
- **`start` checks `--max` with `isdigit()`,** which accepts digits such as
  `²` that `int()` rejects, so such a value crashes instead of exiting 2.
  The skill always passes an ASCII number. Found by the code re-review.
- **The default docs paths and `--docs-paths` are copied into two
  scripts,** which match paths in two ways (a git pathspec and a Python
  prefix). A change in one script only makes them disagree. Found by the
  code re-review.
- **Blast radius of the fold change:** the callers listed under "File map".
  None passes `--docs-paths`; each gets the default list.

## Testing Strategy

- Unit tests in `plugins/my/tests/`, red first, in temporary fixture repos:
  Tasks 1 to 4. Task 5's integration test drives two runs through the real
  scripts in both orders.
- The deliberate breaks in Tasks 2 and 5 prove the tests that never went red.
- The Review Focus items are pinned by tests in Tasks 1 to 4.
- Lint counts and greps for the prose tasks (6 to 9).
- The rehearsal (Task 10), started by the user, before the `done` marks.

Rehearsal, 2026-10-12: not run to the end. The three starts, `alpha`, `beta`
and `gamma`, each refused and wrote nothing. Inside a Claude session, the
installed plugin's `bin/` (the main checkout's) comes before the
`--plugin-dir` copy on `PATH`, even when the tmux server starts with the
branch's `bin/` first. So `handoff-state.py start` reached the old script,
which exits 2. The user then chose to skip the rehearsal for now. It can run
only after the squash-merge, or with the installed `my` plugin turned off.
The spec asks for it before the spec is marked `done`, so the `done` marks
wait for it, or for the user's explicit choice to mark `done` without it. The
fixture also needs `__pycache__/` in `.gitignore`.

## Open Questions

None.
