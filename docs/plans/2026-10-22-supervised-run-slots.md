# Every run gets its own slot Implementation Plan

**Status:** approved, 2026-10-22. Row 56; the plan for `docs/plans/2026-10-22-supervised-run-slots-spec.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan task-by-task. The tasks
> build on each other: `start --supervised` needs the `mode` field of Task 1,
> `pull` needs `is_auto` from Task 2, `status-scan.py` reads the `live`
> column of Task 1, and the prose names all of them. The global review rules
> replace that skill's own reviews: run no per-task reviewer and no final
> `requesting-code-review` pass. The `my:handoff` review stage runs the
> end-of-branch reviews. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** No two live runs in one project, of either mode, ever have the same
slot.

**Architecture:** `handoff-state.py` gains a `mode` field (`auto` or
`supervised`) and a second form of `start`, `start <slug> --supervised`. Both
forms take slots from one pool over every live run. Only auto runs count
toward the cap, in `start --max` and in rule 5 of `pull`. `live` and the
`runs` block of `status-scan.py` gain a sixth column, `mode`. The rest is
prompt text: the supervised code and review stages of `my:handoff` write and
finish their state, and `my:status` shows supervised runs.

**Tech Stack:** Python 3.12.3 standard library (`json`, `os`, `shutil`,
`subprocess`, `unittest`), git 2.43.0, `markdownlint-cli2`.

**Spec:** `docs/plans/2026-10-22-supervised-run-slots-spec.md`

## Context

Row 56 is a bug. A project's "Parallel runs" section can give each run its
own port through the **Isolation** line, for example
`PORT=$((54310 + <slot>))`. Only auto runs get a slot. A supervised run has no
state file and uses slot `1` (`SKILL.md` line 185). So two supervised runs
share a port, and a supervised run shares one with the first auto run. The
spec's Context section has the full root cause and decisions D1 to D16.

## Global Constraints

- Work in the worktree `.claude/worktrees/supervised-run-slots` on the branch
  `fix/supervised-run-slots`. The `my:handoff` code stage creates both.
- Conventional Commits, type `fix`, scope `my-plugin` for files under
  `plugins/my/`, none for Task 6's commit, which also touches the top-level
  `README.md`. Every message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Every task
  commit carries the trailer `Task: <N>`, with `<N>` the task's number below
  (`git commit --trailer "Task: <N>"`).
- Focused tests while a task is in progress, for example
  `cd plugins/my && python3 -m unittest tests.test_handoff_state.StartTest -v`.
  The full suites once per task, just before its commit:
  `cd plugins/kit && python3 -m unittest discover tests` and
  `cd plugins/my && python3 -m unittest discover tests`. On `main` on
  2026-10-22, 273 tests pass in `plugins/my`. All must pass.
- End-of-branch checks: the two full suites (the spec's Delegation section).
- No new dependencies (spec, Dependencies).
- Read `git diff --cached` before every commit. This repo has no "Parallel
  runs" section, so the locked commit form does not apply to this branch.
- Markdown lint: count errors with
  `markdownlint-cli2 <file> 2>&1 | grep ' error ' | grep -vc MD013`. On
  `main` on 2026-10-22 the count is 0 for every `.md` file this plan edits,
  and it must stay 0.
- Match the line style of the paragraph you edit. The handoff files and the
  status skill wrap at 80 characters. Skill prose follows the plain style:
  one idea per sentence, the common word, no idioms.
- Keep every other CLI output of `handoff-state.py` byte for byte. The auto
  refusal lines keep their words: `refused: a run for <slug> exists; use
  resume` and `refused: <k> auto runs are live (<slugs>); the most is <n>`.
- Fixed copy, word for word (spec, Design):
  - `refused: an auto run for <slug> exists`
  - `refused: a supervised run for <slug> exists`
  - `a supervised run for <slug> exists; finish or end it first` (start
    check 5, D13)
  - `<name>: the run for <slug> is supervised; run /my:handoff <stage> <doc>`
    (`resume`, D10)
  - `rows wait in the queue; run /my:handoff auto rows` (D9)

## Decisions this plan adds

The spec leaves these to the plan.

1. **`mode` values.** `parse_pairs` accepts `mode` only as `auto` or
   `supervised`. Any other value exits 2 with `unknown mode: <value>` and
   writes nothing, as an unknown `next` does today.
2. **`start` sets `mode` itself.** A `mode=` pair given to either form of
   `start` is a usage error (exit 2, nothing written). So the form is the only
   source of the mode.
3. **`--supervised` and `--max` never go together.** `start` takes exactly one
   of them, as its first argument after the slug. Anything else is a usage
   error.
4. **An unreadable state of the same slug** counts as auto, as it does for the
   cap. So a supervised `start` refuses with `refused: an auto run for <slug>
   exists`, and the file stays as it is.
5. **`start_run(slug, mode, cap, updates)`.** `cap` is an `int` for `auto`
   and `None` for `supervised`. Every refusal about the slug's own live run
   raises `Refused(..., exists=True)`, so rule 6 of `pull` skips the entry
   with `a run for <slug> exists` and goes on. The slot search stays
   `range(1, len(live) + 2)` over every live run, of both modes. A range over
   auto runs only would run out of numbers when supervised runs hold some.
6. **The `live` column.** A readable state without `mode` prints `auto`. Only
   an unreadable file prints the sixth column empty.
7. **The worktree fields in the code stage.** The auto-mode bullet "Step 1:
   after the worktree exists, run `handoff-state.py set <slug> branch=...`"
   moves into code stage step 1, for both modes. The spec says the supervised
   code stage runs it "as auto runs do"; one sentence in step 1 says it once.
8. **`status-scan.py` pads to six fields,** so a `live` from an older
   `handoff-state.py` (five columns) prints `-` for `mode`.

## Review Focus

- **A supervised start beside an unreadable state of its own slug.** It must
  refuse and leave the file, not overwrite it. Task 2 tests it.
- **A supervised start after the slug's run finished.** It must write a fresh
  state, without the old run's `branch` or `stopped`. Task 2 tests it.
- **`start` with both `--supervised` and `--max`, or with a `mode=` pair.**
  Each must be a usage error that writes nothing. Task 2 adds them to the
  usage cases.
- **A queued row whose slug has a live supervised run.** `pull` must skip it
  with `a run for <slug> exists` and start the next row, not stop the walk.
  Task 3 tests it.
- **`set <slug> mode=<bad value>`.** It must exit 2 and keep the old value.
  Task 1 tests it.

## Files to Modify/Create

| File | Change | Task |
| --- | --- | --- |
| `plugins/my/bin/handoff-state.py` | `FIELDS` and `MODES`, `parse_pairs`, `print_live`, docstring (first line, Fields, `live`) | 1 |
| `plugins/my/bin/handoff-state.py` | `is_auto`, `start_run`, `start_args`, `start`, docstring (Usage, `start`, exit codes) | 2 |
| `plugins/my/bin/handoff-state.py` | `pull` rule 5; docstring (`pull` rules 4 and 5) | 3 |
| `plugins/my/tests/test_handoff_state.py` | `FieldsTest`, `LiveTest` (the expected lines at 349 and 357 gain the sixth column) | 1 |
| `plugins/my/tests/test_handoff_state.py` | `StartTest` new tests and usage cases; `PullTest.test_start_writes_the_state_and_marks_the_entry` (lines 740 to 743) gains `"mode": "auto"` | 2 |
| `plugins/my/tests/test_handoff_state.py` | `WalkTestCase.supervised_run`, four `PullTest` tests | 3 |
| `plugins/my/bin/status-scan.py` | `run_facts` (sixth field, fallback), docstring lines 3 and 23 | 4 |
| `plugins/my/tests/test_status_scan.py` | Two new `RunsTest` tests; `test_runs_fallback_hides_finished` gains `"auto"` | 4 |
| `plugins/my/skills/handoff/SKILL.md` | Design section 2 of the spec | 5 |
| `plugins/my/skills/handoff/README.md` | Lines 311, 364, 367 and 368 | 5 |
| `plugins/my/skills/status/SKILL.md` | Design section 3 of the spec; the description's "auto runs" | 6 |
| `README.md` | Lines 192 and 197: the state and the `runs` facts cover both modes | 6 |

The Reference Sweep, run again on 2026-10-22 with `git grep` for
`handoff-state.py live`, `"live"`, `my-handoff/`, `live_states`, `start_run`,
`run_facts` and `slot` under `plugins/` and `global/`:

- `live` is run only by `status-scan.py` (`run_facts`). The handoff
  `SKILL.md` names it at line 393 and line 512. Both are in Task 5.
- `start_run` is called by `start` and `pull`. `live_states` is called by
  `print_live`, `start_run`, `walk` and `pull`. All are in Tasks 1 to 3.
- Tests that assert a whole state or a whole `live` line:
  `test_handoff_state.py` lines 349, 357 and 740 to 743, and
  `test_status_scan.py` line 277. All are in the table.
  `test_parallel_runs.py` and `test_roadmap_queue.py` write states without
  `mode`, which read as `auto`, and check only auto refusal lines. They need
  no change.
- The plan review searched the top-level `README.md` too. Its lines 192
  ("keeps the state of a `my:handoff auto` run") and 197 ("auto runs") go
  into Task 6, and the docstring's first line ("an autonomous my:handoff
  run") into Task 1.
- Hits that need no change, because "slot" there is the number and the text
  stays true: `SKILL.md` lines 553 and 570 (the `pull` output), 582 ("The new
  run keeps its slot", spec), 660 (where the state lives), 701 (`start`
  prints the slot), 856 and 939 (Isolation with `<slot>`); `README.md` line
  415 (the queue path); `handoff-lock.py` line 5 (the lock folder).
- `block-autorun-push.py` reads only `MY_AUTORUN` and does not change.

---

### Task 1: The `mode` field and the `live` column

**Files:**

- Modify: `plugins/my/bin/handoff-state.py` (`FIELDS`, new `MODES`,
  `parse_pairs`, `print_live`, the docstring's Fields and `live` paragraphs)
- Test: `plugins/my/tests/test_handoff_state.py` (`FieldsTest`, `LiveTest`)

**Interfaces:**

- Produces: `FIELDS` with `"mode"` last; `MODES = ("auto", "supervised")`;
  `live` lines with six tab-separated fields: slug, slot, next, stopped,
  branch, mode.

- [ ] **Step 1: Write the failing tests.** In `FieldsTest`:

```python
def test_mode_field_takes_only_auto_or_supervised(self):
    self.state("mode=supervised")
    self.assertEqual(self.get()["mode"], "supervised")
    result = run(self.repo, "set", "widget", "mode=manual")
    self.assertEqual((result.returncode, result.stderr.strip()),
                     (2, "unknown mode: manual"))
    self.assertEqual(self.get()["mode"], "supervised")
```

In `LiveTest`, a new test, and the two exact lists of the existing tests:

```python
def test_live_prints_mode_last(self):
    run(self.repo, "set", "a", "slot=1", "next=code", "mode=supervised")
    run(self.repo, "set", "b", "slot=2", "next=review", "mode=auto")
    run(self.repo, "set", "c", "slot=3", "next=code")
    self.assertEqual(run(self.repo, "live").stdout.splitlines(), [
        "a\t1\tcode\t\t\tsupervised", "b\t2\treview\t\t\tauto",
        "c\t3\tcode\t\t\tauto"])

# test_live_lists_runs_that_are_not_finished, line 349:
["a\t1\tcode\t\tfeat/a\tauto", "c\t3\treview\ttests failed\t\tauto"]
# test_live_ignores_locks_and_temporary_files_and_counts_unreadable_ones, line 357:
["d\t\tunreadable\t\t\t"]
```

- [ ] **Step 2: Run them and see them fail.**
  `cd plugins/my && python3 -m unittest tests.test_handoff_state.FieldsTest tests.test_handoff_state.LiveTest -v`.
  Expected: the mode test fails with `unknown field: mode`; the three `live`
  tests fail on the missing sixth column.

- [ ] **Step 3: Implement.** Add `"mode"` to `FIELDS` and `MODES`. In
  `parse_pairs`, reject a `mode` outside `MODES` with
  `unknown mode: <value>` and return `None`. In `print_live`, print
  `state.get("mode", "auto")` as the sixth field, and an empty sixth field
  for an unreadable file. In the docstring: the first line becomes "Keep
  the state of a my:handoff run, auto or supervised, and check it against
  git."; add `mode` to the Fields list
  with "`mode` is auto or supervised; a state without it is auto", and make
  the `live` paragraph say six fields, ending in mode.

- [ ] **Step 4: Run the focused tests, then the full suites.** Expected: all
  pass.

- [ ] **Step 5: Commit.**
  `git add plugins/my/bin/handoff-state.py plugins/my/tests/test_handoff_state.py`,
  read `git diff --cached`, then
  `git commit --trailer "Task: 1" -m "fix(my-plugin): handoff-state keeps a run's mode and lists it in live"`
  with the Co-Authored-By line.

### Task 2: `start --supervised`, one slot pool, a cap for auto runs only

**Files:**

- Modify: `plugins/my/bin/handoff-state.py` (new `is_auto` and `start_args`;
  `start_run`, `start`; the docstring's Usage block, `start` paragraph and
  exit codes)
- Test: `plugins/my/tests/test_handoff_state.py` (`StartTest`; the exact
  dict in `PullTest.test_start_writes_the_state_and_marks_the_entry`)

**Interfaces:**

- Consumes: `MODES` and the `mode` field from Task 1.
- Produces: `is_auto(state: dict | None) -> bool`, true for `None` (an
  unreadable file), a state without `mode`, and `mode == "auto"`;
  `start_run(slug: str, mode: str, cap: int | None, updates: dict) -> str`
  (decision 5); the CLI form `handoff-state.py start <slug> --supervised
  <field>=<value> ...`.

- [ ] **Step 1: Write the failing tests.** In `StartTest`, a helper and these
  tests. Every assertion uses the spec's exact copy.

```python
def supervised(self, slug, *pairs):
    return run(self.repo, "start", slug, "--supervised", *(pairs or ("next=code",)))

def state_of(self, slug):
    return json.loads(run(self.repo, "get", slug).stdout)

def file_of(self, slug):
    return (self.repo / ".git" / "my-handoff" / f"{slug}.json").read_text()

def test_supervised_start_takes_the_lowest_slot_no_live_run_uses(self):
    self.start("a")
    result = self.supervised("b")
    self.assertEqual((result.returncode, result.stdout.strip()), (0, "2"), result.stderr)
    state = self.state_of("b")
    self.assertEqual((state["mode"], state["slot"], state["merge_retries"], state["next"]),
                     ("supervised", "2", "0", "code"))

def test_auto_start_skips_a_supervised_slot(self):
    self.supervised("a")
    self.assertEqual(self.start("b").stdout.strip(), "2")
    self.assertEqual(self.state_of("b")["mode"], "auto")

def test_supervised_run_does_not_count_toward_the_cap(self):
    result = self.supervised("a")
    self.assertEqual((result.returncode, result.stdout.strip()), (0, "1"), result.stderr)
    self.assertEqual(self.start("b", 1).returncode, 0)
    result = self.start("c", 1)
    self.assertEqual(result.returncode, 1)
    self.assertIn("refused: 1 auto runs are live (b); the most is 1", result.stderr)

def test_supervised_start_again_keeps_the_slot_and_writes_the_fields(self):
    self.start("x")
    self.supervised("a")
    run(self.repo, "set", "a", "branch=fix/a")
    run(self.repo, "set", "x", "next=finished")
    result = self.supervised("a", "next=review")
    self.assertEqual((result.returncode, result.stdout.strip()), (0, "2"), result.stderr)
    state = self.state_of("a")
    self.assertEqual((state["slot"], state["next"], state["branch"], state["mode"]),
                     ("2", "review", "fix/a", "supervised"))

def test_supervised_start_refuses_beside_a_live_auto_run_of_its_slug(self):
    self.start("a")
    before = self.file_of("a")
    result = self.supervised("a", "next=review")
    self.assertEqual((result.returncode, result.stderr.strip()),
                     (1, "refused: an auto run for a exists"))
    self.assertEqual(self.file_of("a"), before)

def test_auto_start_refuses_beside_a_live_supervised_run_of_its_slug(self):
    self.supervised("a")
    before = self.file_of("a")
    result = self.start("a")
    self.assertEqual((result.returncode, result.stderr.strip()),
                     (1, "refused: a supervised run for a exists"))
    self.assertEqual(self.file_of("a"), before)

def test_finished_supervised_run_frees_its_slot(self):
    self.supervised("a")
    self.start("b")
    run(self.repo, "set", "a", "next=finished")
    self.assertEqual(self.supervised("c").stdout.strip(), "1")

def test_supervised_start_after_a_finished_run_writes_a_fresh_state(self):
    self.supervised("a", "next=code", "branch=fix/a")
    run(self.repo, "set", "a", "next=finished", "stopped=ended by the user")
    self.assertEqual(self.supervised("a").returncode, 0)
    state = self.state_of("a")
    self.assertNotIn("branch", state)
    self.assertNotIn("stopped", state)

def test_supervised_start_refuses_beside_an_unreadable_state_of_its_slug(self):
    folder = self.repo / ".git" / "my-handoff"
    folder.mkdir()
    (folder / "a.json").write_text("{")
    result = self.supervised("a")
    self.assertEqual((result.returncode, result.stderr.strip()),
                     (1, "refused: an auto run for a exists"))
    self.assertEqual(self.file_of("a"), "{")

def test_concurrent_locked_supervised_starts_never_share_a_slot(self):
    # as test_concurrent_locked_starts_never_pass_the_cap, with
    # "start", f"s{i}", "--supervised", "next=code" for i in range(4)
    self.assertEqual(sorted(code for code, _ in outs), [0, 0, 0, 0])
    self.assertEqual(sorted(slot for _, slot in outs), ["1", "2", "3", "4"])
```

Add these to the list in `test_usage_errors_write_nothing`:
`["start", "a", "--supervised", "--max", "2", "next=code"]`,
`["start", "a", "--max", "2", "--supervised"]`,
`["start", "a", "--supervised", "mode=auto"]`,
`["start", "a", "--max", "2", "mode=supervised"]`,
`["start", "a", "--supervised", "next=nowhere"]`.

In `PullTest.test_start_writes_the_state_and_marks_the_entry`, the expected
dict gains `"mode": "auto"`.

- [ ] **Step 2: Write the guard test.** It passes before the change, because
  today every state counts toward the cap. It writes the file directly, so
  it needs no new CLI.

```python
def test_state_without_mode_counts_as_auto(self):
    folder = self.repo / ".git" / "my-handoff"
    folder.mkdir()
    (folder / "old.json").write_text(json.dumps({"next": "code", "slot": "1"}))
    result = self.start("a", 1)
    self.assertEqual(result.returncode, 1)
    self.assertIn("refused: 1 auto runs are live (old); the most is 1", result.stderr)
```

- [ ] **Step 3: Run them.**
  `cd plugins/my && python3 -m unittest tests.test_handoff_state.StartTest tests.test_handoff_state.PullTest -v`.
  Expected: the guard test passes; the new supervised tests fail with exit 2
  (usage, `--supervised` unknown); `test_auto_start_skips_a_supervised_slot`
  and the `PullTest` dict test fail. Of the five new usage cases, the one
  with `--max 2 mode=supervised` fails (exit 0: Task 1 made `mode` a known
  field); the other four already exit 2.

- [ ] **Step 4: Implement.**
  - `is_auto(state)` as in Interfaces.
  - `start_args(rest) -> tuple[str, int | None, list[str]] | None`: `("auto",
    n, pairs)` for `--max <n> <pairs>`, `("supervised", None, pairs)` for
    `--supervised <pairs>`, `None` for anything else. `None` also when a pair
    has no `=` or names `mode` (decision 2). `cap_arg` stays for `pull`.
  - `start(slug, rest)` uses `start_args`, then `parse_pairs`, then
    `start_run(slug, mode, cap, updates)`.
  - `start_run` follows the spec's table in Design section 1. With the slug's
    own state live: auto refuses with `a run for <slug> exists; use resume`
    when that state `is_auto`, else with `a supervised run for <slug>
    exists`; supervised refuses with `an auto run for <slug> exists` when it
    `is_auto`, else writes `{**own, **updates, "mode": "supervised"}` and
    returns the kept `slot`. All of these raise with `exists=True`. Then, for
    auto only, the cap check counts and names only the live states that
    `is_auto`. A fresh state is
    `{**updates, "mode": mode, "slot": <slot>, "merge_retries": "0"}`.
  - `pull`'s call becomes `start_run(slug, "auto", cap, updates)`.
  - The docstring: the Usage block gains
    `handoff-state.py start <slug> --supervised <field>=<value> ...` with its
    note `start a supervised run, or take its slot again`, with no blank line
    inside the block (`usage()` prints only up to the first blank line). The
    `start` paragraph gets the two forms, the state table of Design section 1,
    the slot pool over both modes, and that the cap counts only auto runs,
    an unreadable state as auto. Exit code 1 names "start refused" for both
    forms.

- [ ] **Step 5: Run the focused tests, then the full suites.** Expected: all
  pass.

- [ ] **Step 6: Prove the guard can fail.** Change `is_auto` to return
  `False` for a state without `mode`. Run
  `cd plugins/my && python3 -m unittest tests.test_handoff_state.StartTest.test_state_without_mode_counts_as_auto`.
  Expected: FAIL (exit 0, no refusal). Revert the change, and check with
  `git diff` that `is_auto` is as in Step 4.

- [ ] **Step 7: Commit.** Same two files, read `git diff --cached`, then
  `git commit --trailer "Task: 2" -m "fix(my-plugin): supervised runs take a slot from the same pool as auto runs"`.

### Task 3: `pull` counts only auto runs for its cap

**Files:**

- Modify: `plugins/my/bin/handoff-state.py` (`pull`'s `ready`; the
  docstring's `pull` rules 4 and 5)
- Test: `plugins/my/tests/test_handoff_state.py` (`WalkTestCase`,
  `PullTest`)

**Interfaces:**

- Consumes: `is_auto` and `start_run(slug, "auto", cap, updates)` from Task 2.

- [ ] **Step 1: Write the tests.** In `WalkTestCase`, a helper that writes
  the file directly, as `live_run` does with `set`:

```python
def supervised_run(self, slug):
    folder = self.repo / ".git" / "my-handoff"
    folder.mkdir(exist_ok=True)
    slot = len(list(folder.glob("*.json"))) + 1
    (folder / f"{slug}.json").write_text(json.dumps(
        {"next": "code", "slot": str(slot), "mode": "supervised"}))
```

In `PullTest`:

```python
def test_rule5_cap_ignores_supervised_runs(self):
    self.supervised_run("x")
    self.add(self.entry("a"))
    self.assertEqual(self.pull(1).stdout, f"a\tcode\t{spec('a')}\t2\n")

def test_rule4_exclusive_entry_waits_for_a_live_supervised_run(self):
    self.supervised_run("x")
    self.add(self.entry("a", exclusive=True))
    self.assertEqual(self.pull(2).stdout, "")
    self.assertEqual(self.show().stdout, "waits\ta\tlive runs\n")

def test_rule3_after_waits_for_a_live_supervised_run(self):
    self.supervised_run("x")
    self.add(self.entry("a", after=["x"]))
    self.assertEqual(self.pull(2).stdout, "")
    self.assertEqual(self.show().stdout, "waits\ta\tx\n")
    self.finish("x")
    self.assertTrue(self.pull(2).stdout.startswith("a\t"))

def test_rule6_a_live_supervised_run_of_the_slug_is_skipped(self):
    self.add(self.entry("a"), self.entry("b"))
    self.supervised_run("a")
    result = self.pull(3)
    self.assertIn("skipped: a: a run for a exists", result.stderr)
    self.assertTrue(result.stdout.startswith("b\t"))
    self.assertEqual(self.get_state("a")["mode"], "supervised")
```

- [ ] **Step 2: Run them.**
  `cd plugins/my && python3 -m unittest tests.test_handoff_state.PullTest -v`.
  Expected: `test_rule5_cap_ignores_supervised_runs` fails (empty stdout:
  the cap counts `x`). The rule 3, rule 4 and rule 6 tests pass: `walk`
  already reads every live state, and Task 2's refusal carries
  `exists=True`. They are guards.

- [ ] **Step 3: Implement.** In `pull`'s `ready`, keep one list of every
  live slug for rule 6 (`slug in live`), and count only the live states that
  `is_auto` for rule 5 (`>= cap`). `walk` does not change: rule 4 keeps
  every live run (D6). In the docstring, rule 4 says "no run of either mode
  is live", and rule 5 says "`<n>` auto runs are live; an unreadable state
  counts as auto".

- [ ] **Step 4: Run the focused tests, then the full suites.** Expected: all
  pass.

- [ ] **Step 5: Prove the three guards can fail,** one break at a time, each
  reverted before the next. Run the guard's test after each break; each must
  FAIL.
  - Rule 4: in `walk`, build `live` from the states that `is_auto` only.
    `test_rule4_exclusive_entry_waits_for_a_live_supervised_run` fails.
  - Rule 3: in `walk`, read a blocker's state as `None` when it is not
    `is_auto`. `test_rule3_after_waits_for_a_live_supervised_run` fails
    (the row is skipped as `blocker x did not finish`).
  - Rule 6: in `start_run`, raise the auto refusal for a supervised own run
    with `exists=False`. `test_rule6_a_live_supervised_run_of_the_slug_is_skipped`
    fails (the walk stops before `b`).

  Then check with `git diff` that `walk` and `start_run` are as before the
  breaks.

- [ ] **Step 6: Commit.** Same two files, read `git diff --cached`, then
  `git commit --trailer "Task: 3" -m "fix(my-plugin): the queue's cap counts only auto runs"`.

### Task 4: `status-scan.py` shows each run's mode

**Files:**

- Modify: `plugins/my/bin/status-scan.py` (`run_facts`; docstring lines 3
  and 23)
- Test: `plugins/my/tests/test_status_scan.py` (`RunsTest`)

**Interfaces:**

- Consumes: the six-field `live` lines of Task 1.
- Produces: `runs` block lines with six fields: slug, slot, next, stop line,
  branch, mode; `-` for an empty field.

- [ ] **Step 1: Write the failing tests.** In `RunsTest` (add
  `import shutil`):

```python
def test_runs_block_shows_mode(self):
    self.state("a", '{"next": "code", "slot": "1", "mode": "supervised"}')
    self.state("b", '{"next": "review", "slot": "2"}')
    self.assertEqual(block(self.scan(), "runs"), [
        ["a", "1", "code", "-", "-", "supervised"],
        ["b", "2", "review", "-", "-", "auto"]])

def test_runs_fallback_reads_mode_with_auto_by_default(self):
    # The fallback runs only when `handoff-state.py live` exits 2. The scan
    # finds that script next to itself, so a copy runs beside a stub.
    bin_dir = self.tmp / "bin"
    bin_dir.mkdir()
    shutil.copy(SCRIPT, bin_dir / "status-scan.py")
    (bin_dir / "handoff-state.py").write_text(
        "import sys\n"
        "if sys.argv[1:] == ['queue', 'show']:\n"
        "    print('none')\n"
        "    sys.exit(0)\n"
        "sys.exit(2)\n")
    self.state("a", '{"next": "code", "mode": "supervised"}')
    self.state("b", '{"next": "code", "branch": "feat/b"}')
    result = subprocess.run([sys.executable, str(bin_dir / "status-scan.py")],
                            cwd=self.repo, env=clean_env(), capture_output=True,
                            text=True, timeout=120)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(block(result.stdout, "runs"), [
        ["a", "-", "code", "-", "-", "supervised"],
        ["b", "-", "code", "-", "feat/b", "auto"]])
```

In `test_runs_fallback_hides_finished` (line 277), the expected row becomes
`["a", "-", "code", "-", "feat/a", "auto"]`. Despite its name, it runs the
`live` path.

- [ ] **Step 2: Run them and see them fail.**
  `cd plugins/my && python3 -m unittest tests.test_status_scan.RunsTest -v`.
  Expected: all three fail on a five-field row.

- [ ] **Step 3: Implement.** In `run_facts`, pad and cut the `live` fields to
  six (decision 8). In the fallback, read
  `state.get("mode", "auto")` as the sixth field. The docstring of
  `run_facts` and the module docstring say "runs", not "auto runs"; the
  `runs` line of the module docstring ends with ", mode".

- [ ] **Step 4: Run the focused tests, then the full suites.** Expected: all
  pass.

- [ ] **Step 5: Commit.**
  `git add plugins/my/bin/status-scan.py plugins/my/tests/test_status_scan.py`,
  read `git diff --cached`, then
  `git commit --trailer "Task: 4" -m "fix(my-plugin): status-scan shows whether each run is auto or supervised"`.

### Task 5: `my:handoff` writes and ends a supervised run's state

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md`,
  `plugins/my/skills/handoff/README.md`

**Interfaces:**

- Consumes: `handoff-state.py start <slug> --supervised` (Task 2), the
  `mode` field (Task 1), `handoff-state.py queue show` (unchanged).

Each edit below names the current text, because earlier edits move the
lines. Row 68 edits only the four launch lines of this `SKILL.md`; none of
these edits touch them.

- [ ] **Step 1: "Parallel runs", the values.**
  - "Without the section, only two parts of this apply: the locked start,
    with `--max 1`, ...; and the fold's refusal to give a cited commit a new
    hash." becomes three parts. The third: "the supervised `start`, under
    `handoff-lock.py main`, which gives each supervised run its own state
    file".
  - "A supervised run has no state file and uses slot `1`." goes. The
    `<slot>` bullet keeps "the `slot` field that `handoff-state.py get
    <slug>` prints".

- [ ] **Step 2: "Start checks", a new paragraph after the `review` stage's
  list,** before "When something already exists". Title: **The state of a
  supervised run.** Its content, from Design section 2: without `auto`, the
  code and review stages run, once their start checks pass,

```bash
handoff-lock.py main -- handoff-state.py start <slug> --supervised \
  spec=<design doc> task_doc=<task doc> next=<stage>
```

  with `<stage>` `code` or `review`. The review stage gets the slot the code
  stage got. The session that does the work writes the state, so this holds
  too when Launch fell back to printing a command. A refusal or a lock
  timeout is a failed start check: signal
  `<name>: start check failed: <the script's message>`. The plan stage writes
  no state. A supervised run never writes `stopped`: its stops wait in its
  window, as today.

- [ ] **Step 3: The code stage.**
  - Step 1: after "Create the worktree from the main checkout's root", one
    sentence for both modes: after the worktree exists, run
    `handoff-state.py set <slug> branch=<branch> worktree=<worktree path>`,
    with the path as given to `git worktree add`. In "**In auto mode,** the
    code stage changes as follows", the bullet "Step 1: after the worktree
    exists, run `handoff-state.py set <slug> branch=<branch> worktree=<worktree path>`, ..."
    goes (decision 7).
  - Step 4 ("When the project's rules or the plan end this work before the
    branch is done"): without `auto`, before the signal, first stop every
    server this stage started under **Isolation** (D16), then run
    `handoff-state.py set <slug> next=finished`, then the queue line of
    Step 4 below. Here the queue line goes just before the signal line,
    because this step signals and never reaches Finish. The next plan of the
    batch is a new run with its own slug. Auto runs keep this step as it is.

- [ ] **Step 4: The review stage, step 8, sub-step 4** ("Set the `done`
  marks as the project's rules say"): add, for a run without `auto`, "Then
  run `handoff-state.py set <slug> next=finished`, then the queue line." The
  queue line, defined once in this step: run `handoff-state.py queue show`;
  when its first field is `ready`, print
  `rows wait in the queue; run /my:handoff auto rows` just before Finish's
  last line. A supervised finish runs no refill (D9).

- [ ] **Step 5: "Resume" and "To end an abandoned run".**
  - "Resume", a new first step, before the `check` of today's step 1: run
    `handoff-state.py get <slug>`. "If it prints a state whose `mode` is
    `supervised` and whose `next` is not `finished`, print
    `<name>: the run for <slug> is supervised; run /my:handoff <stage> <doc>`
    and stop", with `<stage>` the state's `next` and `<doc>` its `task_doc`
    (D10). The spec places this after step 2; it moves first because
    step 1's `check` stops on any mismatch, such as a supervised state
    without `branch`, and would hide the refusal (plan review). The later
    steps keep their numbers' order.
  - "`handoff-state.py live` lists the runs that count." becomes "lists the
    live runs of both modes; only auto runs count toward the cap". Add: "This
    section applies to supervised runs too."
  - "the ended run freed its slot" becomes "the ended run may let waiting
    rows start".

- [ ] **Step 6: "From roadmap rows", "Refill" and the auto start check.**
  - The skip table's "a live auto run (a state whose `next` is not
    `finished`)" becomes "a live run, of either mode (...)" (D7).
  - The `after` bullet's "live auto runs" becomes "live runs" (D7).
  - Step 4's fold condition "`handoff-state.py live` prints nothing" stays.
    It now also waits for supervised runs (D14).
  - "the runs refill their own slots" becomes "the runs refill their own
    places under the cap". "A run that finishes frees its slot" becomes "A
    run that finishes frees its place under the cap" (D11). "The new run
    keeps its slot" stays.
  - Start check 5 of "Start checks in auto mode": "If not, the reason is `a
    run for <slug> exists; use resume`." becomes: when the live state's
    `mode` is `supervised`, the reason is
    `a supervised run for <slug> exists; finish or end it first`; otherwise
    it stays `a run for <slug> exists; use resume` (D13).

- [ ] **Step 7: `README.md`.**
  - Line 311, "A run keeps its state in `.git/my-handoff/<slug>.json`": add
    "A supervised run keeps one too, from its code stage on. The field
    `mode` says `auto` or `supervised`."
  - Line 364: "**Max runs** is the most runs live at once" becomes "the
    most auto runs live at once".
  - Lines 367 and 368 (D12): "`<slot>` is the run's place, 1 to **Max
    runs**" becomes "`<slot>` is the run's number, from 1 up. Supervised
    runs take numbers too, so leave room above **Max runs** for them".

- [ ] **Step 8: Check the text.**
  - `grep -c 'A supervised run has no state file' plugins/my/skills/handoff/SKILL.md`
    prints `0`.
  - `grep -c -- '--supervised' plugins/my/skills/handoff/SKILL.md` prints at
    least `1`.
  - `grep -n 'frees its slot\|refill their own slots\|live auto run' plugins/my/skills/handoff/SKILL.md`
    prints nothing.
  - The lint count of both files stays 0. The full suites pass.

- [ ] **Step 9: Commit.** Both files, read `git diff --cached`, then
  `git commit --trailer "Task: 5" -m "fix(my-plugin): supervised handoff stages write and end their run's state"`.

### Task 6: `my:status` shows supervised runs

**Files:**

- Modify: `plugins/my/skills/status/SKILL.md`, `README.md` (top level)

**Interfaces:**

- Consumes: the six-field `runs` block of Task 4.

- [ ] **Step 1: Edit, from Design section 3.**
  - The description's "auto runs" (line 7) becomes "runs".
  - The `runs` row of the facts table: "slug, slot, `next`, stop line,
    branch, `mode` (`auto` or `supervised`) (`-` for empty)".
  - "the live runs are fewer than the cap" (the "first can start now" line)
    becomes "the live auto runs are fewer than the cap".
  - "`<k> rows wait for a free slot` when the line is `ready` but the live
    runs fill that same cap" becomes "`<k> rows wait for a free place under
    the cap` when the line is `ready` but the live auto runs fill that same
    cap" (D11).
  - The parallel rule "the runs whose `next` is not `finished`, stopped ones
    included, plus the new runs, stay within **Max runs**" counts auto runs
    only. "allow one auto run" stays.
  - In-progress lines: a supervised run shows as one line, such as
    "supervised run `<slug>`, at code, branch `fix/x`".
  - A new "needs the user" bullet (D15): a live supervised run when the
    `queue` block's first line is `waits` and its reason is that run's slug,
    or `live runs` while that run is live. The line is "Needs you: the queue
    waits for supervised run `<slug>`; finish it or end it with the steps in
    "To end an abandoned run"".
  - "What is next", item 1: "a stopped auto run
    (`/my:handoff auto resume <spec>`)". `auto resume` is offered only for
    auto runs.
  - Top-level `README.md`, line 192: "keeps the state of a `my:handoff
    auto` run" becomes "keeps the state of a `my:handoff` run, auto or
    supervised". Line 197: "auto runs" in the `status-scan.py` sentence
    becomes "runs".

- [ ] **Step 2: Check.**
  `grep -n 'free slot' plugins/my/skills/status/SKILL.md` prints nothing;
  `grep -c 'supervised' plugins/my/skills/status/SKILL.md` prints at least
  `3`; `grep -n 'state of a .my:handoff auto. run' README.md` prints
  nothing. The lint count of both files stays 0. The full suites pass.

- [ ] **Step 3: Commit.** Both files, read `git diff --cached`, then
  `git commit --trailer "Task: 6" -m "fix: my:status lists supervised runs and what waits on them"`.

### Task 7: Rehearsal

**Files:**

- None in the repo. The fixture lives in the session's scratchpad.

**Interfaces:**

- Consumes: the branch's `plugins/my/bin`, first on `PATH`.

- [ ] **Step 1: Build the fixture.** A new repo in the scratchpad with one
  commit on `main`. Put the worktree's `plugins/my/bin` first on `PATH`.

- [ ] **Step 2: Run the commands, each under `handoff-lock.py main --`,
  and check each result.**

| Command | Expected |
| --- | --- |
| `handoff-state.py start s1 --supervised spec=x task_doc=x next=code` | `1` |
| `handoff-state.py start s2 --supervised spec=x task_doc=x next=code` | `2` |
| `handoff-state.py start a1 --max 1 spec=x task_doc=x next=code` | `3` |
| `handoff-state.py start s1 --supervised spec=x task_doc=x next=review` | `1` |
| `handoff-state.py set s1 next=finished` (no lock needed) | exit 0 |
| `handoff-state.py start s3 --supervised spec=x task_doc=x next=code` | `1` |
| `handoff-state.py queue show` | `none` |
| `status-scan.py`, the `runs` block | `a1 3 code - - auto`, `s2 2 code - - supervised`, `s3 1 code - - supervised` (tab-separated) |

- [ ] **Step 3: Report.** Print the table with the real outputs in the code
  stage's last message. Nothing is committed: the review stage reads the
  branch's tests, and this rehearsal checks the commands the skill text
  names.

## Trade-Offs / Alternatives Considered

The spec's Trade-offs section chose the slot design. The plan adds three
choices:

- **A `mode=` pair given to `start`: refuse (chosen), or let the form win.**
  Refusing keeps one source for the mode and costs nothing: no caller passes
  `mode` today. Letting the form win would hide a caller's mistake.
- **The guard tests write state files directly (chosen), or use the CLI.**
  The CLI needs `--supervised` or `set mode=`, which do not exist before the
  change, so a CLI-built guard could never pass first.
- **The fallback test copies `status-scan.py` beside a stub (chosen), or
  patches `HERE`.** The tests run the scripts as commands. A copy keeps that,
  and needs no change to the script.

## Dependencies

- No new package. `handoff-lock.py` and `handoff-state.py` are already on
  `PATH` in every project that loads the `my` plugin.
- Tasks run in order: 2 needs 1, 3 needs 2, 4 needs 1, 5 and 6 need 1 to 4.
- Row 68 "Methods as plugins" edits the same handoff `SKILL.md`, but only its
  four launch lines, which this plan does not touch. The order of work puts
  row 56 first.

## Risk

- **Stored state changes shape:** a `mode` field and new supervised files in
  `<git common dir>/my-handoff/`. To undo, delete the supervised files and
  revert. If the plugin is rolled back while supervised files exist, the old
  script counts them toward the cap. `live` shows them, and ending those runs
  fixes it.
- **Two outputs change:** `live` and the `runs` block gain a sixth column.
  The readers found by the sweep are `status-scan.py`, `my:status` and the
  handoff `SKILL.md` (line 393 and the fold condition at line 512). All are
  handled here.
- **`start` refuses more input:** a `mode=` pair and `--supervised` with
  `--max` are now usage errors. No caller passes either today.
- **Runs started before the change.** A supervised run whose code stage ran
  before the change has no state. Its review stage writes one, and may get a
  slot other than `1`, so its ports can differ from the code stage. This repo
  had no worktrees on 2026-10-22; other projects may.
- **A dropped supervised run stays live** in `my:status` until the user ends
  it. While live it holds its slot, blocks exclusive queued rows and `after`
  gates, and blocks the fold of `auto rows` step 4 in a project without the
  section (D14). `my:status` names it as needing the user when the queue
  waits on it (D15).
- **Slots above Max runs** (D12). A project whose Isolation reserves exactly
  **Max runs** ports can get a slot outside them. The README tells projects
  to leave room.
- **Batch servers** (D16). Code stage step 4 stops only the servers that the
  stage started. A server the user started by hand can still hold a freed
  slot's port.
- **A supervised stage can wait** up to 90 seconds for the `main` lock while
  an auto run merges. A timeout is a failed start check; the user reruns the
  stage.
- **Judgement steps are not tested by a command:** `resume` refusing a
  supervised run, start check 5's supervised case, code stage step 4 stopping
  servers and finishing a batch run, and `my:status` naming a supervised run
  that the queue waits on. The end-of-branch review reads the `SKILL.md`
  diff for them.
- **No effect without the section.** Until a project has a "Parallel runs"
  section, its runs use no slot. Row 56's `done` mark says so.
- **How to detect a break:** the full suites, and the rehearsal table of
  Task 7. A wrong count would show as an auto start refused beside a
  supervised run, or two runs with one slot in the `runs` block.

## Testing Strategy

The tests run the real `handoff-state.py` and `status-scan.py` as commands in
a fixture repo, so they cover the public surface end to end.

- **New tests, failing first:** Task 1 (mode field, `live` column), Task 2
  (ten `StartTest` tests besides the guard, and one of the five usage
  cases), Task 3 (rule 5), Task 4 (two
  `RunsTest` tests).
- **Changed expectations:** `LiveTest` lines 349 and 357, the `PullTest` dict
  at lines 740 to 743, and `RunsTest` line 277.
- **Guards with a deliberate break:** the state without `mode` (Task 2,
  Step 6), and rules 3, 4 and 6 of `pull` (Task 3, Step 5). Each passes
  before its change, then fails under its named break.
- **Concurrency:** four locked supervised starts at once get slots 1 to 4
  (Task 2).
- **Rehearsal:** Task 7 runs the commands the skill text names, in a fixture
  repo.
- **Prose:** the `grep` checks of Tasks 5 and 6, and the lint count. The
  end-of-branch review reads the `SKILL.md` diffs for the judgement steps.

## Open Questions

None. The spec's open question, per-run values for a project without a
"Parallel runs" section, is out of scope here.
