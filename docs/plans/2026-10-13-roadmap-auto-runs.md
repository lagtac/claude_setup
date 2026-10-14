# Start auto runs from roadmap rows Implementation Plan

**Status:** approved, 2026-10-14. Written by the `my:handoff` plan stage from the approved spec.

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan task-by-task. The tasks
> build on each other: `pull` needs the `start` refactor and the queue file of
> Task 1, `status-scan.py` needs `queue show`, the end-to-end test needs every
> subcommand, and the prose names them all. The global review rules replace
> that skill's own reviews: run no per-task reviewer and no final
> `requesting-code-review` pass. The `my:handoff` review stage runs the
> end-of-branch reviews. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One command, `/my:handoff auto rows <n> ...`, queues roadmap rows
whose specs are approved, and each finishing auto run starts the next row,
never past **Max runs**.

**Architecture:** `handoff-state.py` gains a queue file,
`<git common dir>/my-handoff/queue/rows.json`, and four subcommands:
`queue add`, `queue drop`, `queue show` and `pull` (D4, D5, D7). `pull` and
`queue show` share one walk over the queue. `status-scan.py` gains a `queue`
block (D7). The rest is prompt text: the `auto rows` forms and the refill in
`my:handoff` (D1 to D3, D6), and the report lines in `my:status` (D7).

**Tech Stack:** Python 3.12.3 standard library (`json`, `os`, `subprocess`,
`tempfile`, `unittest`), git 2.43.0, tmux, `markdownlint-cli2`.

**Spec:** `docs/plans/2026-10-13-roadmap-auto-runs-spec.md`

## Global Constraints

- Work in the worktree `.claude/worktrees/roadmap-auto-runs` on the branch
  `feat/roadmap-auto-runs`. The `my:handoff` code stage creates both.
- Conventional Commits with a scope: `my-plugin` for files under
  `plugins/my/`, none for a commit that also touches `README.md`. Every
  message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  Every task commit carries the trailer `Task: <N>`, with `<N>` the task's
  number below (`git commit --trailer "Task: <N>"`).
- Unit tests: `cd plugins/my && python3 -m unittest discover tests`. On
  `main` on 2026-10-14, 146 tests pass. Every code commit runs them, and all
  must pass.
- End-of-branch checks: `cd plugins/my && python3 -m unittest discover tests`
  (the spec's Delegation section), the lint counts below, and the rehearsal
  record from Task 8.
- No new dependencies (spec, Dependencies).
- Read `git diff --cached` before every commit. This repo has no "Parallel
  runs" section, so the locked form does not apply to this branch.
- Markdown lint: count errors with
  `markdownlint-cli2 <file> 2>&1 | grep ' error ' | grep -vc MD013`. On
  `main` on 2026-10-14 the count is 0 for every file this plan edits, and it
  must stay 0.
- Match the line style of the paragraph you edit. The handoff files, the
  status skill and `README.md` wrap at 80 characters.
- Keep every existing CLI output of `handoff-state.py` byte for byte.
  `StartTest` and `test_parallel_runs.py` check it.
- Fixed copy, word for word (spec D2, D4 to D7):
  - Skip reasons from `queue add`, `pull` and `queue drop`:
    `already waiting`, `gate cycle`, `spec changed since the call`,
    `blocker <slug> did not finish`, `a run for <slug> exists`,
    `dropped by the user`.
  - The D2 reasons, exactly as in the spec's table (`no row <n>`,
    `row <n> has no spec`, `spec is <status>, not approved`,
    `Delegation: <key> <missing, unknown or invalid>`,
    `a run for <slug> exists`, `already waiting`,
    `<plan, branch or worktree> for <slug> exists`,
    `blocked by row <m>, which nothing will start`,
    `blocker row <m> was skipped`, `waits for <what the row says>`).
  - D6: `stopped="cannot open a window: <reason>"`;
    `cannot open a window for <stage>-<new slug>; run /my:handoff auto resume <spec>`;
    `rows wait in the queue; run /my:handoff auto rows`.
  - D7: `<k> rows wait and the first can start now: run /my:handoff auto rows`,
    `<k> rows wait for <what>`, `<k> rows wait for a free slot`.

## Decisions this plan adds

The spec leaves these to the plan ("The plan fixes the argument forms").
Decisions 14 and 16 change D3 and D4. The user chose both on 2026-10-14,
after the plan review, and the spec now says so in D3 and D4.

1. **Dispatch.** `main()` routes `pull` and `queue` before the `SLUG` check,
   as it routes `live` today: `pull --max 1` and `queue add` would fail it.
   The new usage lines go inside the first `Usage:` block of the docstring,
   with no blank line, because `usage()` prints only up to the first blank
   line.
2. **`queue add --file <path>`.** The entries come from a JSON file that the
   skill writes with the Write tool to its scratchpad, because `after` is a
   list and `field=value` pairs cannot hold one. The file is a JSON list of
   objects with exactly these keys: `row` (a non-empty string), `spec` (a
   path that matches `docs/plans/YYYY-MM-DD-<slug>-spec.md`), `stage`
   (`plan` or `code`), `after` (a list of slugs) and `exclusive` (a JSON
   boolean). The script derives `slug` from `spec`, and computes
   `spec_hash` itself with `git hash-object` on the spec in the main
   checkout, inside the lock, so the skill can never pass a stale hash. It
   sets `state` to `waiting` and `reason` to empty.
3. **What `queue add` refuses.** Exit 2, nothing written, one stderr line
   `invalid entry <i>: <why>` (`<i>` counted from 1) when: the input file
   cannot be read or is not a JSON list of objects; a key is missing or
   unknown; a value has the wrong type; `stage` is not `plan` or `code`; the
   spec path does not match the pattern or its slug, or a slug in `after`,
   does not match `SLUG`; the spec file does not exist in the main checkout.
   Exit 1, nothing written, when the queue file exists but is not a JSON
   list: `refused: the queue file is not valid JSON: <path>`.
4. **What `queue add` prints.** One stdout line `added<TAB><slug>` per
   added entry, in queue order. One stderr line per entry not added:
   `skipped: <slug>: already waiting` (its slug is `waiting` in the queue,
   or appeared earlier in the same file), and `skipped: <slug>: gate cycle`.
   Exit 0 even when entries were skipped.
5. **Order and cycles.** A stable topological sort places the `waiting`
   entries, old ones first in queue order, then new ones in typed order.
   Each round takes the earliest entry whose `waiting` blockers are all
   placed. Links to slugs with no `waiting` entry do not affect the order.
   New entries the sort cannot place are in a cycle, or wait on one; each is
   skipped as `gate cycle` and not added, and the sort runs once more
   without them. That second pass always places every entry, because the
   old entries already had a valid order. An entry whose `after` names its
   own slug is a cycle of one. The queue file keeps the entries that are not
   `waiting` in front, in their order, then the sorted `waiting` entries.
   Without a re-added slug (Decision 16), no old entry names a new one, so
   this equals D4's "append the new entries after the existing ones".
6. **Prune.** After the append, `queue add` drops each `started` entry whose
   state file has `next=finished`, and each `skipped` entry whose slug no
   `waiting` entry names in `after`. A `started` entry whose state file is
   missing stays.
7. **`queue drop <slug> ...`.** Every named slug must be a `waiting` entry.
   If one is not, exit 1, nothing changed, stderr
   `refused: <slug> is not waiting`. Otherwise each becomes `skipped` with
   `dropped by the user`; exit 0, no output. A queue file that is not a
   JSON list refuses with exit 1 and the line of Decision 3, as D5 says for
   `queue drop`. The skill maps the user's row
   numbers to slugs from the `queue` block of `status-scan.py`, which prints
   row and slug side by side (Task 4).
8. **`start` split in two.** `start_run(slug, cap, updates)` holds today's
   checks and write. It returns the slot as a string, or raises
   `Refused(message, exists)`, where `exists` is `True` for the own-run
   refusal. The CLI `start` catches it and prints the message as today.
   `pull` uses `exists` for rule 6.
9. **One walk for `pull` and `queue show`.**
   `walk(entries, repo, ready) -> (skips, wait)` applies rules 1 to 4 in
   queue order. It marks skipped entries in the list it gets, and collects
   one `skipped: <slug>: <reason>` line per skip. It calls `ready(entry)` for
   each entry that passes rules 1 to 4; `ready` returns `False` to stop the
   walk. When an entry stops the walk at rule 3 or 4, `wait` is
   `<slug><TAB><what>`, with `<what>` the first blocker slug that has not
   finished, `exclusive <slug>` for a live exclusive run, or `live runs`.
   Otherwise `wait` is `None`. It reads `live_states()` again for each entry,
   so a start inside `ready` counts.
10. **`pull --max <n>`.** Its `ready` applies rules 5 and 6: stop at the cap;
    otherwise call `start_run` with `spec`, `task_doc`, `next=<stage>` and
    the empty fields `branch`, `worktree`, `squash_subject`,
    `head_before_fold`, `stopped`, `checked_base`. On success it marks the
    entry `started`, prints `<slug><TAB><stage><TAB><spec><TAB><slot>`, and
    stops the walk when the entry is `exclusive`. On `Refused` with `exists`,
    it marks the entry `skipped` with `a run for <slug> exists`. After the
    walk, `pull` writes the queue once, when anything changed, then prints
    the skip lines on stderr. Exit 0; exit 1 for an unreadable queue file
    (same line as Decision 3) or a git error; exit 2 for a usage error. No
    queue file: no output, exit 0, nothing written.
11. **`queue show`.** Same walk, with a `ready` that records the entry and
    returns `False`. It prints one line: `ready<TAB><slug>`, or
    `waits<TAB><slug><TAB><what>`, or `none`. It writes nothing and prints
    no skip lines. Exit codes as `pull`.
12. **Paths come from the main checkout.** `pull`, `queue add` and
    `queue show` hash the spec at `Repo().root`, so they give the same
    answer from a worktree. A spec file that is missing at `pull` time is
    rule 1: `spec changed since the call`. The hash helper returns `None`
    for a missing file instead of raising `GitError`.
13. **Writing the queue.** `write_json(path, data)` is the temp file and
    `os.replace` that `write_state` uses today, moved into its own function.
    `write_state` calls it, with the same temp-name prefix as today. The
    first write creates `queue/` with `os.makedirs`.
14. **D3's clean-tree test.** At the moment D3 runs, the queued specs'
    `approved` edits are still uncommitted, so "`git status --porcelain`
    prints nothing" can never hold as written. The call reads it as the
    plan stage reads its own check (Plan stage step 6, and "Restarted
    stages": "the spec's `approved` edit is expected and does not count"):
    `git status --porcelain` lists only the queued specs. The order is: no
    live run; only those dirty paths; `git-fold-fixups.py check` exits 0
    for each spec commit; list the waiting fixups and ask about a foreign
    one; make the fixups; fold. After the fixups the tree is clean, which is
    what the fold needs. The user chose this reading on 2026-10-14, and
    spec D3 now says it.
15. **The refill failure is a fifth signal point.** D6 signals the user but
    is not a stop of the finished run. "Signal" gains it by name, and the
    auto-mode paragraph says the stop table does not cover it.
16. **A re-added slug replaces its old `skipped` entry (spec D4).** When
    `queue add` adds an entry, it first removes every older `skipped` entry
    with the same slug. It does not do this for an entry it does not add:
    a duplicate or a `gate cycle`. Then Decision 5's sort runs. A row
    already waiting behind the old entry now waits for the new one, and the
    sort puts the new one in front of it. Without that sort, the walk would
    stop at that row forever, because its blocker comes after it. The user
    chose this on 2026-10-14, after the plan review.

## Review Focus

- **A spec file deleted or renamed while its row waits.** `pull` must skip
  the entry as `spec changed since the call`, not crash with a git error.
  Task 2 tests a missing spec.
- **`pull` run from a worktree.** The refill runs in the main checkout, but
  `To end an abandoned run` may not. Hashes and paths must come from the
  main checkout. Task 2 runs `pull` from a worktree.
- **An entry gated behind itself.** `after: ["a"]` on `a` must be a
  `gate cycle`, not an entry that waits forever. Task 1 tests it.
- **The queue folder inside `my-handoff/`.** `live`, `start` and the `runs`
  block of `status-scan.py` must not count `queue/` as a run. Tasks 1 and 4
  test it.
- **A row number with a letter, such as `1b`.** It must stay a string in the
  queue and print as typed. Task 1 adds `1b`; Task 4 prints it.

## File map

| File | Change | Task |
| --- | --- | --- |
| `plugins/my/bin/handoff-state.py` | `write_json`, the queue file, `queue add`, `queue drop` (D4) | 1 |
| `plugins/my/bin/handoff-state.py` | `start_run`, `walk`, `pull`, `queue show` (D5, D7) | 2 |
| `plugins/my/tests/test_handoff_state.py` | Queue, pull and show cases | 1, 2 |
| `plugins/my/tests/test_roadmap_queue.py` | Create: the end-to-end test | 3 |
| `plugins/my/bin/status-scan.py` | The `queue` block (D7) | 4 |
| `plugins/my/tests/test_status_scan.py` | The `queue` block | 4 |
| `plugins/my/skills/status/SKILL.md` | The `queue` block and its report lines (D7) | 4 |
| `plugins/my/skills/handoff/SKILL.md` | Forms, usage, description, "From roadmap rows" (D1 to D3) | 5 |
| `plugins/my/skills/handoff/SKILL.md` | The refill, the signal point (D6) | 6 |
| `plugins/my/skills/handoff/README.md` | A "From roadmap rows" section | 7 |
| `README.md` | The `handoff-state.py` and `status-scan.py` sentences, lines 157 to 165 | 7 |

The reference sweep (`git grep -n 'handoff-state.py\|status-scan.py'` outside
`docs/`) found these callers: `plugins/my/skills/handoff/SKILL.md`,
`plugins/my/skills/handoff/README.md`, `plugins/my/skills/status/SKILL.md`,
`README.md`, `status-scan.py` (which runs `handoff-state.py live`), the three
test files, `CHANGELOG.md` (history, not edited) and `ROADMAP.md` row 34
(history). No existing subcommand changes its interface, so no caller needs
an edit beyond the table. `ROADMAP.md` row 9 already links the spec; the
`done` marks move it to ✅ and add this plan's link, as the project's rules
say.

---

### Task 1: The queue file, `queue add` and `queue drop`

**Files:**

- Modify: `plugins/my/bin/handoff-state.py` (docstring `Usage:` block and
  text, `write_state` at line 128, `main` at line 418)
- Test: `plugins/my/tests/test_handoff_state.py`

**Interfaces:**

- Produces:
  - `queue_path() -> str`: `<common dir>/my-handoff/queue/rows.json`.
  - `read_queue() -> list[dict]`: `[]` when the file is missing; raises
    `QueueError(path)` when it is not a JSON list.
  - `write_json(path: str, data) -> None` (Decision 13).
  - `spec_hash(repo: Repo, spec: str) -> str | None` (Decision 12).
  - `slug_of(spec: str) -> str | None`: the slug of a path matching
    `docs/plans/YYYY-MM-DD-<slug>-spec.md`, else `None`.
  - CLI: `handoff-state.py queue add --file <path>`,
    `handoff-state.py queue drop <slug> ...` (Decisions 2 to 7).

- [ ] **Step 1: Write the failing tests.** A new base class
  `QueueTestCase(StateTestCase)` commits three specs,
  `docs/plans/2026-10-13-{a,b,c}-spec.md`, and has helpers
  `entries_file(*entries) -> Path` (writes JSON to `self.tmp`),
  `entry(slug, after=(), stage="code", exclusive=False, row=None) -> dict`
  (`row` defaults to the slug), `add(*entries) -> CompletedProcess` (runs
  `queue add --file`), `queue_file() -> Path`
  (`.git/my-handoff/queue/rows.json`), `queue() -> list` (its JSON, `[]`
  when missing) and `get_state(slug) -> dict`.

```python
class QueueAddTest(QueueTestCase):
    def test_add_writes_a_waiting_entry_with_the_spec_hash(self):
        result = self.add(self.entry("a", row="1b"))
        self.assertEqual((result.returncode, result.stdout), (0, "added\ta\n"))
        self.assertEqual(self.queue(), [{
            "row": "1b", "slug": "a", "spec": "docs/plans/2026-10-13-a-spec.md",
            "stage": "code", "after": [], "exclusive": False,
            "spec_hash": git(self.repo, "hash-object", "docs/plans/2026-10-13-a-spec.md"),
            "state": "waiting", "reason": ""}])

    def test_add_refuses_an_invalid_entry_and_writes_nothing(self):
        bad = {"unknown key": {"colour": "red"}, "missing key": {"stage": None},
               "stage": {"stage": "review"}, "after slug": {"after": ["../x"]},
               "after type": {"after": "a"}, "exclusive type": {"exclusive": "yes"},
               "row type": {"row": 5}, "spec pattern": {"spec": "docs/plans/a.md"},
               "spec missing": {"spec": "docs/plans/2026-10-13-zz-spec.md"}}
        for name, change in bad.items():
            with self.subTest(name):
                entry = {k: v for k, v in {**self.entry("b"), **change}.items()
                         if v is not None}
                result = self.add(self.entry("a"), entry)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr.startswith("invalid entry 2: "))
                self.assertFalse(self.queue_file().exists())

    def test_add_reports_a_waiting_duplicate(self):
        self.add(self.entry("a"))
        result = self.add(self.entry("a"), self.entry("b"))
        self.assertIn("skipped: a: already waiting", result.stderr)
        self.assertEqual([e["slug"] for e in self.queue()], ["a", "b"])

    def test_add_sorts_blockers_first_and_keeps_typed_order(self):
        self.add(self.entry("c", after=["b"]), self.entry("a"), self.entry("b", after=["a"]))
        self.assertEqual([e["slug"] for e in self.queue()], ["a", "b", "c"])

    def test_add_keeps_typed_order_without_links(self):
        self.add(self.entry("b"), self.entry("a"))
        self.assertEqual([e["slug"] for e in self.queue()], ["b", "a"])

    def test_add_appends_after_existing_entries(self):
        self.add(self.entry("b"))
        self.add(self.entry("a"))
        self.assertEqual([e["slug"] for e in self.queue()], ["b", "a"])

    def test_add_skips_a_gate_cycle_and_a_self_gate(self):
        result = self.add(self.entry("a", after=["b"]), self.entry("b", after=["a"]),
                          self.entry("c", after=["c"]))
        self.assertEqual(result.returncode, 0)
        for slug in "abc":
            self.assertIn(f"skipped: {slug}: gate cycle", result.stderr)
        self.assertEqual(self.queue(), [])

    def test_add_prunes_only_what_d4_allows(self):
        # Write rows.json by hand: started s1 (state finished), started s2
        # (state code), started s3 (no state file), skipped k1 (named by w),
        # skipped k2 (named by nobody), waiting w (after k1).
        ...
        self.add(self.entry("a"))
        self.assertEqual([e["slug"] for e in self.queue()], ["s2", "s3", "k1", "w", "a"])

    def test_readded_slug_replaces_its_skipped_entry_and_goes_first(self):
        self.add(self.entry("a"), self.entry("b", after=["a"]))
        run(self.repo, "queue", "drop", "a")
        result = self.add(self.entry("a"))
        self.assertEqual(result.stdout, "added\ta\n")
        self.assertEqual([(e["slug"], e["state"]) for e in self.queue()],
                         [("a", "waiting"), ("b", "waiting")])

    def test_old_skipped_entry_stays_when_the_readd_is_a_cycle(self):
        self.add(self.entry("a"), self.entry("b", after=["a"]))
        run(self.repo, "queue", "drop", "a")
        result = self.add(self.entry("a", after=["c"]), self.entry("c", after=["a"]))
        self.assertIn("skipped: a: gate cycle", result.stderr)
        self.assertEqual([(e["slug"], e["state"]) for e in self.queue()],
                         [("a", "skipped"), ("b", "waiting")])

    def test_add_refuses_an_unreadable_queue(self):
        self.queue_file().parent.mkdir(parents=True)
        self.queue_file().write_text("{")
        result = self.add(self.entry("a"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: the queue file is not valid JSON", result.stderr)
        self.assertEqual(self.queue_file().read_text(), "{")


class QueueDropTest(QueueTestCase):
    def test_drop_marks_waiting_entries_skipped(self):
        self.add(self.entry("a"), self.entry("b"))
        self.assertEqual(run(self.repo, "queue", "drop", "a", "b").returncode, 0)
        self.assertEqual([(e["state"], e["reason"]) for e in self.queue()],
                         [("skipped", "dropped by the user")] * 2)

    def test_drop_refuses_a_slug_that_is_not_waiting(self):
        self.add(self.entry("a"))
        before = self.queue_file().read_text()
        result = run(self.repo, "queue", "drop", "a", "zz")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: zz is not waiting", result.stderr)
        self.assertEqual(self.queue_file().read_text(), before)

    def test_drop_refuses_an_unreadable_queue(self):
        self.queue_file().parent.mkdir(parents=True)
        self.queue_file().write_text("{")
        result = run(self.repo, "queue", "drop", "a")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: the queue file is not valid JSON", result.stderr)
        self.assertEqual(self.queue_file().read_text(), "{")
```

  Also add to `LiveTest`:
  `test_live_ignores_the_queue_folder` (a `queue/rows.json` with one waiting
  entry, `live` prints nothing), and to `SetGetTest.test_usage_error` the
  cases `["queue"]`, `["queue", "add"]`, `["queue", "nope"]`.

- [ ] **Step 2: Run them and see them fail.**
  Run: `cd plugins/my && python3 -m unittest tests.test_handoff_state -v 2>&1 | tail -20`
  Expected: the new tests FAIL (exit 2 from the usage error, no queue file).
  `test_live_ignores_the_queue_folder` passes already; it guards a
  regression, because `live_states` skips names that do not end in `.json`.

- [ ] **Step 3: Implement** the functions in Interfaces, `queue_add(path)`
  and `queue_drop(slugs)`, and the dispatch (Decision 1). Update the
  docstring: the two usage lines, a paragraph on the queue file and the
  exit codes.

- [ ] **Step 4: Run the whole suite.**
  Run: `cd plugins/my && python3 -m unittest discover tests 2>&1 | tail -3`
  Expected: `OK`, 146 plus the new tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/bin/handoff-state.py plugins/my/tests/test_handoff_state.py
git commit --trailer "Task: 1" -m "feat(my-plugin): handoff-state.py keeps a queue of roadmap rows"
```

---

### Task 2: `pull` and `queue show`

**Files:**

- Modify: `plugins/my/bin/handoff-state.py` (`start` at line 201, docstring,
  `main`)
- Test: `plugins/my/tests/test_handoff_state.py`

**Interfaces:**

- Consumes: `read_queue`, `write_json`, `queue_path`, `spec_hash` (Task 1);
  `live_states`, `read_state`, `Repo` (today).
- Produces:
  - `class Refused(Exception)` with `message: str`, `exists: bool`.
  - `start_run(slug: str, cap: int, updates: dict) -> str` (Decision 8).
  - `walk(entries: list, repo: Repo, ready: Callable[[dict], bool]) -> tuple[list[str], str | None]`
    (Decision 9).
  - CLI: `handoff-state.py pull --max <n>`, `handoff-state.py queue show`
    (Decisions 10 and 11).

- [ ] **Step 1: Write the failing tests.** `PullTest(QueueTestCase)` and
  `ShowTest(QueueTestCase)`, with helpers `pull(n, cwd=None)` and `show()`
  (each runs the subcommand and asserts exit 0, as `scan()` does in
  `test_status_scan.py:98-101`, so a usage error or a crash can never pass a
  test that expects empty output; `test_unreadable_queue_refuses` calls
  `run` itself),
  `finish(slug, stopped="")` (runs `set <slug> next=finished stopped=<stopped>`)
  and `live_run(slug)` (runs `set <slug> next=code slot=<k>`, a run started
  by hand). One test per rule, as D5 lists them:

```python
class PullTest(QueueTestCase):
    def test_no_queue_file_prints_nothing(self):
        self.assertEqual((self.pull(1).returncode, self.pull(1).stdout), (0, ""))
        self.assertFalse(self.queue_file().exists())

    def test_start_writes_the_state_and_marks_the_entry(self):
        self.add(self.entry("a"))
        result = self.pull(1)
        self.assertEqual(result.stdout, f"a\tcode\t{spec('a')}\t1\n")
        self.assertEqual(self.get_state("a"), {
            "spec": spec("a"), "task_doc": spec("a"), "next": "code", "branch": "",
            "worktree": "", "squash_subject": "", "head_before_fold": "",
            "stopped": "", "checked_base": "", "slot": "1", "merge_retries": "0"})
        self.assertEqual(self.queue()[0]["state"], "started")

    def test_plan_stage_task_doc_is_the_plan_path(self):
        self.add(self.entry("a", stage="plan"))
        self.pull(1)
        self.assertEqual(self.get_state("a")["task_doc"], "docs/plans/2026-10-13-a.md")

    def test_rule1_changed_or_missing_spec_is_skipped(self):
        self.add(self.entry("a"), self.entry("b"))
        (self.repo / spec("a")).write_text("changed\n")
        (self.repo / spec("b")).unlink()
        result = self.pull(2)
        self.assertEqual(result.stdout, "")
        self.assertIn("skipped: a: spec changed since the call", result.stderr)
        self.assertIn("skipped: b: spec changed since the call", result.stderr)

    def test_rule2_blocker_skipped_ended_or_unknown(self):
        cases = {"skipped entry": lambda: run(self.repo, "queue", "drop", "a"),
                 "ended by the user": lambda: (self.pull(1),
                                               self.finish("a", "ended by the user"))}
        for name, make in cases.items():
            with self.subTest(name):
                ...  # fresh queue: a, then b after a; make(); pull
                self.assertIn("skipped: b: blocker a did not finish", result.stderr)
        # b after zz, which has no entry and no state file:
        self.assertIn("skipped: b: blocker zz did not finish", result.stderr)

    def test_rule3_waiting_entry_stops_the_walk(self):
        self.live_run("a")
        self.add(self.entry("b", after=["a"]), self.entry("c"))
        self.assertEqual(self.pull(3).stdout, "")
        self.assertEqual([e["state"] for e in self.queue()], ["waiting", "waiting"])

    def test_rule3_ready_once_the_blocker_finished(self):
        self.live_run("a")
        self.add(self.entry("b", after=["a"]))
        self.finish("a")
        self.assertTrue(self.pull(2).stdout.startswith("b\t"))

    def test_rule4_exclusive_entry_waits_for_no_live_run(self):
        self.live_run("x")
        self.add(self.entry("e", exclusive=True))
        self.assertEqual(self.pull(2).stdout, "")

    def test_rule4_nothing_starts_beside_a_live_exclusive_run(self):
        self.add(self.entry("e", exclusive=True))
        self.pull(2)
        self.add(self.entry("f"))
        self.assertEqual(self.pull(2).stdout, "")

    def test_rule4_walk_stops_after_starting_an_exclusive_entry(self):
        self.add(self.entry("e", exclusive=True), self.entry("f"))
        self.assertEqual([l.split("\t")[0] for l in self.pull(2).stdout.splitlines()], ["e"])

    def test_rule5_cap_stops_the_walk(self):
        self.add(self.entry("a"), self.entry("b"), self.entry("c"))
        lines = self.pull(2).stdout.splitlines()
        self.assertEqual([(l.split("\t")[0], l.split("\t")[3]) for l in lines],
                         [("a", "1"), ("b", "2")])
        self.assertEqual(self.queue()[2]["state"], "waiting")

    def test_rule6_existing_run_is_skipped_and_the_walk_goes_on(self):
        self.add(self.entry("a"), self.entry("b"))
        self.live_run("a")
        result = self.pull(3)
        self.assertIn("skipped: a: a run for a exists", result.stderr)
        self.assertTrue(result.stdout.startswith("b\t"))

    def test_pull_from_a_worktree_reads_the_main_checkout(self):
        self.add(self.entry("a"))
        self.assertTrue(self.pull(1, cwd=self.worktree).stdout.startswith("a\t"))

    def test_unreadable_queue_refuses(self):
        ...  # rows.json is "{": exit 1, file unchanged, no state written


class ShowTest(QueueTestCase):
    def test_none_without_a_queue(self):
        self.assertEqual(self.show().stdout, "none\n")

    def test_ready_writes_nothing(self):
        self.add(self.entry("a"))
        before = self.queue_file().read_bytes()
        self.assertEqual(self.show().stdout, "ready\ta\n")
        self.assertEqual(self.queue_file().read_bytes(), before)
        self.assertEqual(run(self.repo, "get", "a").returncode, 1)

    def test_waits_for_a_blocker(self):
        self.live_run("a")
        self.add(self.entry("b", after=["a"]))
        self.assertEqual(self.show().stdout, "waits\tb\ta\n")

    def test_waits_for_a_live_exclusive_run(self):
        self.add(self.entry("e", exclusive=True))
        self.pull(2)
        self.add(self.entry("f"))
        self.assertEqual(self.show().stdout, "waits\tf\texclusive e\n")

    def test_exclusive_entry_waits_for_live_runs(self):
        self.live_run("x")
        self.add(self.entry("e", exclusive=True))
        self.assertEqual(self.show().stdout, "waits\te\tlive runs\n")

    def test_passes_over_an_entry_pull_would_skip(self):
        self.add(self.entry("a"), self.entry("b"))
        (self.repo / spec("a")).write_text("changed\n")
        before = self.queue_file().read_bytes()
        self.assertEqual(self.show().stdout, "ready\tb\n")
        self.assertEqual(self.queue_file().read_bytes(), before)

    def test_ignores_the_cap(self):
        for slug in ("x", "y", "z"):
            self.live_run(slug)
        self.add(self.entry("a"))
        self.assertEqual(self.show().stdout, "ready\ta\n")
```

  `spec(slug)` is a module helper returning `docs/plans/2026-10-13-<slug>-spec.md`.
  Add `["pull"]`, `["pull", "--max", "0"]` and `["queue", "show", "x"]` to
  `test_usage_error`.

- [ ] **Step 2: Run them and see them fail.**
  Run: `cd plugins/my && python3 -m unittest tests.test_handoff_state -v 2>&1 | tail -20`
  Expected: the new tests FAIL with exit 2 (usage); `StartTest` still passes.

- [ ] **Step 3: Implement** `Refused`, `start_run`, `walk`, `pull` and
  `queue_show`. The CLI `start` calls `start_run` and keeps its output.

- [ ] **Step 4: Run the whole suite.**
  Run: `cd plugins/my && python3 -m unittest discover tests 2>&1 | tail -3`
  Expected: `OK`. `StartTest` and `test_parallel_runs` unchanged and passing.

- [ ] **Step 5: Commit**

```bash
git add plugins/my/bin/handoff-state.py plugins/my/tests/test_handoff_state.py
git commit --trailer "Task: 2" -m "feat(my-plugin): handoff-state.py pull starts waiting rows under the cap"
```

---

### Task 3: The end-to-end test

**Files:**

- Create: `plugins/my/tests/test_roadmap_queue.py`

**Interfaces:**

- Consumes: the CLI of Tasks 1 and 2, `handoff-lock.py`, through `PATH`, as
  `test_parallel_runs.py` calls them (copy its `clean_env`, `sh` and `git`
  helpers, as the test files already copy them).

The test plays the parts that `my:handoff` plays. Every queue write and every
`pull` runs as `handoff-lock.py main -- handoff-state.py …`. A run "finishes"
with `handoff-state.py set <slug> next=finished stopped=`, as Review stage
sub-step 4 does, and the refill is the next locked `pull`.

- [ ] **Step 1: Write the tests.** The fixture repo commits five specs,
  `docs/plans/2026-10-13-{a,b,c,e,f}-spec.md`. Helpers: module-level
  `spec(slug)` and `entry(slug, after=(), exclusive=False) -> dict`; methods
  `add(*entries)` (locked `queue add --file`), `pull(n)` (locked `pull`,
  returns the process), `pulled(n) -> list[str]` (the slugs `pull` printed),
  `finish(slug, stopped="")` and `live(slug)` (a run started by hand:
  `set <slug> next=code slot=9`).

```python
class RoadmapQueueTest(unittest.TestCase):
    def test_three_rows_typed_dependent_first_run_one_at_a_time(self):
        self.add(entry("c", after=["b"]), entry("b", after=["a"]), entry("a"))
        self.assertEqual(self.pulled(1), ["a"])
        self.assertEqual(self.pulled(1), [])
        self.finish("a")
        self.assertEqual(self.pulled(1), ["b"])
        self.finish("b")
        self.assertEqual(self.pulled(1), ["c"])

    def test_after_gate_holds_a_row_until_its_blocker_finishes(self):
        self.add(entry("a"), entry("b", after=["a"]))
        self.assertEqual(self.pulled(2), ["a"])
        self.assertEqual(self.pulled(2), [])
        self.finish("a")
        self.assertEqual(self.pulled(2), ["b"])

    def test_ended_or_dropped_blocker_skips_the_rows_behind_it(self):
        self.add(entry("a"), entry("b", after=["a"]), entry("c", after=["b"]))
        self.pulled(1)
        self.finish("a", stopped="ended by the user")
        result = self.pull(1)
        self.assertIn("skipped: b: blocker a did not finish", result.stderr)
        self.assertIn("skipped: c: blocker b did not finish", result.stderr)
        # The dropped variant: a fresh queue e, f after e; `queue drop e`; pull
        # skips f with "blocker e did not finish".

    def test_changed_spec_is_skipped(self):
        self.add(entry("a"))
        (self.repo / spec("a")).write_text("edited after the call\n")
        self.assertIn("skipped: a: spec changed since the call", self.pull(1).stderr)

    def test_exclusive_row_waits_runs_alone_and_blocks_later_adds(self):
        self.live("x")
        self.add(entry("e", exclusive=True), entry("f"))
        self.assertEqual(self.pulled(2), [])
        self.finish("x")
        self.assertEqual(self.pulled(2), ["e"])
        self.add(entry("a"))
        self.assertEqual(self.pulled(2), [])
        self.finish("e")
        self.assertEqual(self.pulled(2), ["f", "a"])

    def test_concurrent_pulls_never_pass_the_cap(self):
        self.add(*(entry(s) for s in "abcef"))
        procs = [...]  # four `handoff-lock.py main -- handoff-state.py pull --max 2` at once
        started = [line.split("\t") for out in outs for line in out.splitlines()]
        self.assertEqual(len(started), 2)
        self.assertEqual(sorted(row[3] for row in started), ["1", "2"])

    def test_pull_inside_lock_main_does_not_wait_on_its_own_lock(self):
        self.add(entry("a"))
        result = sh(self.repo, "handoff-lock.py", "main", "--timeout", "5", "--",
                    "handoff-state.py", "pull", "--max", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
```

- [ ] **Step 2: Run them.**
  Run: `cd plugins/my && python3 -m unittest tests.test_roadmap_queue -v 2>&1 | tail -12`
  Expected: PASS. These tests drive code that Tasks 1 and 2 proved red
  first. To prove this file can fail, change `test_three_rows…`'s first
  expectation to `["c"]` once, see it FAIL, and change it back.

- [ ] **Step 3: Run the whole suite**, then commit.

```bash
git add plugins/my/tests/test_roadmap_queue.py
git commit --trailer "Task: 3" -m "test(my-plugin): the roadmap queue end to end, under the real lock"
```

---

### Task 4: `status-scan.py` and `my:status` show the queue

**Files:**

- Modify: `plugins/my/bin/status-scan.py` (docstring block list, `main`'s
  `blocks` at line 307)
- Modify: `plugins/my/skills/status/SKILL.md` (step 1's table, "Where we
  are", the example)
- Test: `plugins/my/tests/test_status_scan.py`

**Interfaces:**

- Consumes: `handoff-state.py queue show` (Task 2), run as `run_facts` runs
  `live`: `[sys.executable, os.path.join(HERE, "handoff-state.py"), "queue", "show"]`.
- Produces: `queue_facts(common: str) -> list[tuple]`. The block is printed
  after `runs`, before `branches`. Its first row is the `queue show` line,
  split on tabs. Then one row per `waiting` or `skipped` entry, in queue
  order: state, row, slug, `after` joined by `,` or `-`, reason or `-`. A
  non-zero exit of `queue show`, or a queue file that is not a JSON list,
  raises `ValueError`, which prints the `error` line. When the only row is
  `none`, the block prints `none`, as an empty block does.

- [ ] **Step 1: Write the failing tests.**

```python
class QueueTest(ScanTestCase):
    def test_no_queue_is_none(self):
        self.assertEqual(block(self.scan(), "queue"), [])

    def test_show_line_then_waiting_and_skipped_entries(self):
        # Specs a, b, c committed. State a: next=code (live). Queue: a started,
        # b (row "12b") waiting after a, c (row "3") skipped with
        # "spec changed since the call".
        self.assertEqual(block(self.scan(), "queue"), [
            ["waits", "b", "a"],
            ["waiting", "12b", "b", "a", "-"],
            ["skipped", "3", "c", "-", "spec changed since the call"]])

    def test_unreadable_queue_is_an_error_line(self):
        ...  # rows.json is "{"
        self.assertEqual(block(result.stdout, "queue")[0][0], "error")

    def test_queue_folder_is_not_a_run(self):
        ...  # a valid rows.json with one waiting entry, no state files
        self.assertEqual(block(self.scan(), "runs"), [])
```

- [ ] **Step 2: Run them and see them fail.**
  Run: `cd plugins/my && python3 -m unittest tests.test_status_scan -v 2>&1 | tail -8`
  Expected: the queue tests FAIL with `ValueError: '== queue' is not in list`.
  `test_queue_folder_is_not_a_run` passes already; it guards a regression.

- [ ] **Step 3: Implement** `queue_facts` and add the block. Update the
  docstring's block list and field table.

- [ ] **Step 4: Edit `plugins/my/skills/status/SKILL.md`.**
  - Step 1's table: a `queue` row: the `queue show` line (`ready`, slug; or
    `waits`, slug, what; or `none`), then state, row, slug, `after`, reason
    per waiting or skipped entry.
  - "Where we are", the items that need the user: the D7 line
    `<k> rows wait and the first can start now: run /my:handoff auto rows`,
    only when the first line is `ready` and the live runs are fewer than
    the cap `pull` uses: **Max runs** when the project has a "Parallel
    runs" section (step 3), and 1 when it has none, as section 3 of the
    report already says ("allow one auto run"). Step 3's default of 2
    applies only inside a section with no **Max runs** key. Say this in the
    skill text at the new line. `<k>` counts the `waiting` rows.
  - The items in progress: `<k> rows wait for <what>` from a `waits` line;
    `<k> rows wait for a free slot` when the line is `ready` but the live
    runs fill that same cap; then one line per `skipped` row with its reason.
  - Add one line to the example.

- [ ] **Step 5: Verify.** The whole suite: `OK`. Lint count for
  `plugins/my/skills/status/SKILL.md`: 0.

- [ ] **Step 6: Commit**

```bash
git add plugins/my/bin/status-scan.py plugins/my/tests/test_status_scan.py plugins/my/skills/status/SKILL.md
git commit --trailer "Task: 4" -m "feat(my-plugin): my:status shows the queue of roadmap rows"
```

---

### Task 5: `SKILL.md`: the `auto rows` forms (D1 to D3)

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md`: frontmatter `description`;
  "Forms" (line 26 on); the usage line (line 69) and the sentence after it;
  a new `## From roadmap rows` section after `## Resume` (before `## Run`,
  line 403).

**Interfaces:**

- Consumes: `status-scan.py` (with Task 4's `queue` block),
  `handoff-state.py get`, `live`, `queue add --file`, `queue drop`, `pull`,
  `handoff-lock.py`, `git-fold-fixups.py`, `locked-commit.py`.

- [ ] **Step 1: Write the edits.**
  - **Description:** add that `/my:handoff auto rows <row number> ...`
    queues roadmap rows with approved specs and starts them as auto runs, up
    to **Max runs**.
  - **Forms:** two forms, `auto rows [<row number> ...]` and
    `auto rows drop <row number> ...`, each sending the reader to "From
    roadmap rows". `<name>` for their signals is `rows`. A row number is
    `\d+[a-z]?`, as in `ROADMAP.md`.
  - **Usage line:**
    `Usage: /my:handoff [run] [auto] <plan|code|review> <docs/plans/…md>, /my:handoff auto resume <docs/plans/…-spec.md>, or /my:handoff auto rows [drop] [<row number> ...]`.
    The next sentence becomes: the auto launch takes only `plan` or `code`
    and a spec, or `rows` and row numbers.
  - **`## From roadmap rows`**, in this order:
    1. It runs in the user's session, which has no `MY_AUTORUN`, and does no
       stage's work itself. `<n>` is as "Parallel runs" says.
    2. **No numbers:** run `handoff-lock.py main -- handoff-state.py pull --max <n>`,
       then step 8.
    3. **`drop`:** run `status-scan.py`; map each number to its slug from
       the `queue` block's `waiting` rows (Decision 7); a number with no
       `waiting` row is printed as `row <n> is not waiting`. Run
       `handoff-lock.py main -- handoff-state.py queue drop <slugs>`. Print
       the result and stop.
    4. **Judge each row (D2).** Run `status-scan.py` once. Use `my:status`
       steps 4 to 6 (`plugins/my/skills/status/SKILL.md`) for the spec, the
       gates and the file list. Check each case of D2's table, in its order,
       and copy the table with its reasons word for word. The Delegation
       check is start check 3 of "Start checks in auto mode". The state
       check is `handoff-state.py get <slug>`. The fresh-start check is the
       anchored `ls` of the plan start check, `git branch --list '*/<slug>'`
       and `.claude/worktrees/<slug>`. For each row that can start, record
       `stage`, `after` and `exclusive` as D2 says. Print one line per
       skipped row, `row <n>: <reason>`, and the overlap warning for two
       rows that share a path outside the docs paths.
    5. **Commit the `approved` edits (D3).** The edited specs are the queued
       specs that `git status --porcelain -- <spec>` lists. Without a
       "Parallel runs" section, fold when all of these hold (Decision 14):
       `handoff-state.py live` prints nothing; `git status --porcelain`
       lists only the edited specs; and `git-fold-fixups.py check <spec commit>`
       exits 0 for each, with `<spec commit>` found as in Plan stage step 8.
       Then list the waiting fixups from the `checkout` block's `fixup`
       lines. When one targets a document outside this call, name it and
       ask the user (a gate: signal first). On yes, or with none, make one
       `git commit --fixup <spec commit> -- <spec>` per spec, check
       `git show --stat --format= HEAD` lists only that spec, and run
       `git-fold-fixups.py`. On its exit 1 or 3, print its message and
       `fixups left unfolded: <hashes>`, write no queue, launch nothing, and
       stop. Otherwise, or on the user's no, make one normal docs commit of
       every edited spec, with the docs scope of the project's rules:
       `git add -- <specs>`, read `git diff --cached`, `git commit -m … -- <specs>`,
       check the `--stat` list. With a "Parallel runs" section, that one
       commit runs through `locked-commit.py`, as in Plan stage step 7, and
       nothing folds.
    6. **Write the queue (D4).** Write the entries (Decision 2) with the
       Write tool to a new JSON file in the session's scratchpad, in the
       order the user typed the rows. Run
       `handoff-lock.py main -- handoff-state.py queue add --file <path>`.
       Print its `skipped:` lines as skipped rows. A non-zero exit: print
       its message and stop; nothing was queued.
    7. **Start (D5).** Run `handoff-lock.py main -- handoff-state.py pull --max <n>`.
       Print its `skipped:` lines. A lock timeout (exit 75 with a
       `handoff-lock:` line) or another failure: print
       `rows: rows wait in the queue; run /my:handoff auto rows` and stop.
    8. **Launch** each line `pull` printed: run "Launch" in auto mode with
       the name `<stage>-<slug>`, the stage and the spec as its doc, and
       `MY_AUTORUN=<slug>`. Launch's fallback prints the command for the
       user, who is at this window.
    9. **Report:** the rows started, the rows waiting (from
       `handoff-state.py queue show`), and the rows skipped with their
       reasons. Then stop. No session stays open to watch.

- [ ] **Step 2: Verify.**
  Run: `grep -n 'auto rows' plugins/my/skills/handoff/SKILL.md` and the lint
  count for the file.
  Expected: the description, the forms, the usage line and the section all
  match; lint count 0.

- [ ] **Step 3: Commit**

```bash
git add plugins/my/skills/handoff/SKILL.md
git commit --trailer "Task: 5" -m "feat(my-plugin): my:handoff auto rows queues roadmap rows and starts them"
```

---

### Task 6: `SKILL.md`: the refill (D6)

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md`: "Signal" (line 177 on),
  Launch step 4 (lines 293 to 297), "To end an abandoned run" (line 349), Review stage's auto-mode sub-step 4
  (line 871 on) and its "Finish" line (line 876).

**Interfaces:**

- Consumes: `pull` (Task 2), "Launch", "Signal", "Finish".

- [ ] **Step 1: Write the edits.**
  - **A "Refill" paragraph**, once, under `## From roadmap rows`, that the
    two places below point to: run
    `handoff-lock.py main -- handoff-state.py pull --max <n>`. For each line
    it prints, run "Launch" in auto mode with the name `<stage>-<new slug>`
    and `MY_AUTORUN=<new slug>`: the new slug, never this session's own
    `MY_AUTORUN`. Launch reads the plugin-dir flags and the mode as it does
    for a next stage. Launch it for every printed line, also after one
    fails, and signal once at the end, naming every failure. A failed
    Launch inside the refill follows the first bullet below, not Launch
    step 4: Launch step 4 makes it a stop of this session's run, and that
    would write `stopped` on the finished run, which rule 2 of D5 then reads
    as "ended by the user". Task 6 adds that exception to Launch step 4. On
    failure, the signal replaces "Finish", so the window shows ⚠, not ✓:
    - Launch cannot open a window: run
      `handoff-state.py set <new slug> stopped="cannot open a window: <reason>"`,
      then signal `<name>: … cannot open a window for <stage>-<new slug>; run /my:handoff auto resume <spec>`.
    - `pull` fails, a lock timeout included: signal
      `<name>: … rows wait in the queue; run /my:handoff auto rows`.
    - In the review stage, `…` is `done; squash commit <hash>.`, so the
      finish is not lost.
    - A refill failure never stops the finished run: its state stays
      `next=finished`.
  - **Review stage, auto sub-step 4:** after
    `handoff-state.py set <slug> next=finished stopped=`, run the refill.
    The "Finish" line stays as it is when the refill succeeds.
  - **"To end an abandoned run":** after the `next=finished` line, run the
    refill.
  - **Launch step 4** (`SKILL.md:293-297`): its sentence that a `run auto`
    stage's failed launch is a stop gains the exception: a launch inside
    the refill follows "Refill" instead.
  - **"Signal":** "four points" becomes five; the fifth is a failed refill.
    The auto-mode paragraph says that the stop table does not cover it,
    because it stops no run (Decision 15).

- [ ] **Step 2: Verify.**
  Run: `grep -n 'refill\|pull --max' plugins/my/skills/handoff/SKILL.md` and
  the lint count.
  Expected: the paragraph, the two call sites and the signal point; lint 0.

- [ ] **Step 3: Commit**

```bash
git add plugins/my/skills/handoff/SKILL.md
git commit --trailer "Task: 6" -m "feat(my-plugin): a finishing auto run starts the next waiting row"
```

---

### Task 7: Docs for a reader

**Files:**

- Modify: `plugins/my/skills/handoff/README.md` (a `### From roadmap rows`
  section under `## Auto mode`, before `### Known problems`, line 381)
- Modify: `README.md:157-165`

- [ ] **Step 1: Write the edits.**
  - Handoff README: the command with an example
    (`/my:handoff auto rows 9 12 30`); that each row needs an approved spec
    with a Delegation section; the rows it skips and why; that one run
    starts the next when it finishes; `auto rows` with no numbers after a
    stall, and `my:status`'s line that says so; `auto rows drop`; that on a
    machine with `Max runs: 1` the rows run one after another. Name the spec
    and this plan.
  - `README.md`: the `handoff-state.py` sentence adds that it also keeps the
    queue of `auto rows`; the `status-scan.py` sentence adds the queue to its
    list.

- [ ] **Step 2: Verify.** Lint count 0 for both files.

- [ ] **Step 3: Commit**

```bash
git add plugins/my/skills/handoff/README.md README.md
git commit --trailer "Task: 7" -m "docs: the roadmap queue in the handoff README and README"
```

---

### Task 8: Rehearsal, started by the user

**Files:**

- Create in the scratchpad only: the fixture, its bare `origin`, and
  `$SCRATCH/rehearsal.md`. The repo gets only the result summary, in Step 4.

**Interfaces:**

- Consumes: everything above, through `--plugin-dir "$WT/plugins/my"`.

- [ ] **Step 1: Build the fixture.** A repo with no "Parallel runs" section,
  `app.py` with two functions, and a `ROADMAP.md` with rows `1` and `2`. Row
  2 says `Blocked by row 1.` Each row links a Medium spec with a Tasks
  section of one task (change one function) and a Delegation section whose
  check is `python3 -c "import app"`. Commit both specs as `draft`, then set
  them to `approved` and leave that edit uncommitted, so that the call runs
  D3's fixup and fold. A bare repo is `origin`, pushed
  once without `-u`. Record `git -C <bare> show-ref`.

- [ ] **Step 2: Gate: the user starts the call.** This is a stop of the auto
  run: Delegation does not list it. Run
  `handoff-state.py set roadmap-auto-runs stopped="rehearsal fixture ready; start the call as printed"`
  and signal
  `code-roadmap-auto-runs: rehearsal fixture ready; start the call as printed`.
  Print, for the user to type:
  `tmux -L rowsq new-session -d -s rehearsal -c <fixture>`,
  `tmux -L rowsq attach -t rehearsal`, then inside it
  `claude --plugin-dir $WT/plugins/my --permission-mode auto '/my:handoff auto rows 2 1'`.
  Then wait for the user's reply. After it, run
  `handoff-state.py set roadmap-auto-runs stopped=`.

- [ ] **Step 3: Check, after the user's reply.**
  - The call made one fixup per spec and folded them: `git log main` shows
    no `fixup!` subject, and each spec's adding commit holds the
    `approved` status.
  - The call opens one window, for row 1.
  - When row 1 finishes, row 2 starts without the user.
  - Both rows end with their `done` marks on `main`.
  - `git -C <bare> show-ref` is unchanged.

  A failed expectation is a bug in Tasks 1 to 6: use
  `superpowers:systematic-debugging`, fix it with a test where one applies,
  commit, and ask the user to rerun on a new fixture.

- [ ] **Step 4: Record**

Write each check (expected, seen, pass or fail) into `$SCRATCH/rehearsal.md`.
Append a "Rehearsal, `<date>`" list with the five results to this plan's
**Testing Strategy**, and commit it in the worktree:

```bash
git add docs/plans/2026-10-13-roadmap-auto-runs.md
git commit --trailer "Task: 8" -m "docs(plans): rehearsal results for the roadmap queue"
```

Stop the server: `tmux -L rowsq kill-server`.

---

## Trade-Offs

- **`queue add` reads a JSON file** versus `field=value` pairs per entry, or
  JSON on stdin. Pairs cannot hold the `after` list. Stdin would need a
  heredoc in the skill, and this repo's rules already write messages to a
  file with the Write tool so that no shell reads them.
- **The script derives the slug and the hash** versus taking them from the
  skill. Fewer inputs, and the hash is taken inside the lock, just before
  the write. The cost: `queue add` must find the spec in the main checkout.
- **One walk with a callback** versus two copies of rules 1 to 4. The
  spec's test "`queue show` prints … as `pull` would decide" is only cheap
  to keep true with one copy.
- **Entries behind a cycle are skipped as `gate cycle`** versus queueing
  them for `pull` to skip later. Either way they never run; skipping them at
  the call tells the user at once.
- **`SKILL.md` in two tasks.** Task 5 adds the user's call; Task 6 changes
  what a finishing run does. A reviewer can accept one and reject the other.
- **The rehearsal as the last code task** versus a step of the review stage.
  The spec asks for it before the `done` marks. In the code stage, a failure
  is fixed on the branch before the reviews read it.

## Dependencies

None. Python 3 standard library, git, tmux and Claude Code, as `my:handoff`
uses today.

## Risk

The spec's **Risk** section holds for this plan. These are added or made
concrete here:

- **Hard to reverse: the queue file's format and `pull`'s output line.**
  Decision 2 fixes the input; D4 fixes the file. A later change drops
  waiting entries with a notice (spec, Risk).
- **Blast radius.** `handoff-state.py`: the CLI `start` now goes through
  `start_run`. Its callers are the auto launch in `SKILL.md`,
  `test_handoff_state.py` and `test_parallel_runs.py`; `StartTest` and the
  parallel test pin its output. `status-scan.py`: one new block; its only
  caller is `my:status`, which reads blocks by name.
- **A row the user starts by hand after the call.** `pull`'s start refuses,
  so the entry is `skipped` as `a run for <slug> exists`. Rule 2 then skips
  the rows behind it, even though the hand run may finish. The user calls
  them again. Known limit. A hand start that writes no state file, such as
  a supervised run or a plan written by hand, is caught by a new D5 rule:
  `pull` skips the row as `<plan, branch or worktree> for <slug> exists`
  (decided by the user on 2026-10-14, after the end-of-branch review).
- **`queue show` does not apply rule 6.** It runs rules 1 to 4, as D7 says.
  So it prints `ready` for a row whose slug has a run or a plan, branch or
  worktree, and `my:status` says to run `/my:handoff auto rows`, which then
  skips that row. Known limit, by the user's choice on 2026-10-14.
- **`my:status` is silent about waiting rows that the next `pull` skips.**
  When every waiting row is stale, `queue show` prints `none`, and the D7
  report rules have no line for the rows that the `queue` block still lists
  as `waiting`. Known limit, by the user's choice on 2026-10-14.
- **A failed queue write in `pull`.** `pull` writes the state files during
  its walk and the queue file at the end. If that last write fails, for
  example on a full disk, the new runs have no window and their entries stay
  `waiting`; the next `pull` skips them as `a run for <slug> exists`. Known
  limit: a failure of the machine, not input the code produces.
- **`row` is any non-empty string.** `queue add` does not check the
  `\d+[a-z]?` form. A row value with a tab would break the `queue` block of
  `status-scan.py`. Rows come from the roadmap as `status-scan.py` parses
  them, which never yields a tab. Known limit.
- **The `queue` block reads the queue twice.** `status-scan.py` runs
  `queue show` and then reads `rows.json` itself, as D7 has it. A `pull`
  between the two reads can make the first line describe another queue than
  the rows under it. The report is read-only, and the next scan is right.
  Known limit.

Known limits from the final re-reviews, 2026-10-14. None is Critical, so by
the one-fix-round rule they are recorded here, not fixed:

- **A finished exclusive row rerun by hand before any `pull`.** `pull` and
  `queue add` drop a finished `started` entry, but only when one of them runs
  between the finish and the rerun. The refill `pull` normally runs at once,
  so the gap opens only when that refill fails, for example on a lock
  timeout. The queue then waits behind the rerun until it ends.
- **`pull` copies `prune`'s rule for finished `started` entries.** A later
  change must edit both copies, or `queue add` and `pull` disagree about
  rule 4.
- **`queue add` re-adds a slug whose entry is `started`.** It checks for
  duplicates only among `waiting` entries. The judge step filters this,
  except when a refill in another session starts the row between the judge
  step and `queue add`. The next `pull` then skips the new entry and the
  rows behind it.
- **Rule 2 counts any `skipped` entry of a blocker's slug as a failure,**
  even when that slug also has a live run or a clean finish. It arises only
  from the re-add race above.
- **`auto rows drop` with no slug left.** When no named row is waiting,
  the skill still runs `queue drop` with no slug, and the script prints its
  usage and exits 2 after the skill's own `row <n> is not waiting` line.
- **Without a "Parallel runs" section, the call commits the `approved`
  edits on `main` without lock `main`.** A queued run's squash-merge or fold
  in the main checkout at the same moment can collide with it
  (`index.lock`, or a commit during a rebase).
- **`start_run` does not see a live exclusive queued run.** With "Parallel
  runs" and **Max runs** 2, a hand `/my:handoff auto plan <spec>` can start
  beside a row that was meant to run alone. The spec's limit covers only the
  opposite direction.
- **The handoff README says the call starts as many rows as Max runs
  allows.** A waiting row holds the rows behind it, so with rows `x`, `y`
  (after `x`) and `z`, only `x` starts while a slot stays free (rules 3 and
  4, by design).
- **`pull` does repeated work under lock `main`.** It lists the state folder
  up to three times per entry and runs one `git hash-object` per entry, so
  the lock is held longer.
- **`queue_facts` runs `queue show` when there is no queue file.** Each
  `my:status` scan pays one extra Python start to print `none`.
- **A failed write in `queue add` or `queue drop` prints a traceback.** The
  write is atomic, so nothing is half-written; only the message is raw.
- **Decisions 14 and 16 change spec D3 and D4,** by the user's choice on
  2026-10-14. Decision 16 also sorts old `waiting` entries again when a
  slug is re-added, which D4 did not do. The sort is needed for the
  re-add to work, and without a re-add it changes nothing.
  `test_readded_slug_replaces_its_skipped_entry_and_goes_first` pins it.
- **The rehearsal stops the auto run.** Task 8 stops the code stage until
  the user starts the call in a second tmux server and replies. Without a
  reply, the run stays stopped; `my:status` shows the stop line.
- **The refill text moves.** Rows 30 and 31 will move Review stage
  sub-step 4. Their plan must grep for `pull --max` (spec, Risk).
- **Cost.** The rehearsal runs two real auto runs, each about 3 stage
  sessions.

## Testing Strategy

- **Unit, `test_handoff_state.py`:** `queue add` (valid entry, every
  invalid form, duplicate, order, cycle and self-gate, prune, unreadable
  queue), `queue drop`, `pull` (one case per D5 rule, plan-stage task doc,
  run from a worktree, no queue, unreadable queue), `queue show` (each
  output form, writes nothing, ignores the cap), and `live` ignoring the
  queue folder.
- **End to end, `test_roadmap_queue.py`:** the seven cases of the spec's
  Testing section, through the real scripts under the real lock.
- **`test_status_scan.py`:** the `queue` block with waiting and skipped
  entries, no queue, an unreadable queue, and the `runs` block ignoring the
  queue folder.
- **Prose:** grep and the lint counts (Tasks 5 to 7).
- **Rehearsal (Task 8):** two Medium specs, the second gated behind the
  first, in a fixture repo with a bare `origin`, started by the user with
  `/my:handoff auto rows 2 1`.

### Rehearsal, 2026-10-14

Fixture: no "Parallel runs" section, two Medium specs, row 2 blocked by row
1, a bare `origin` filled with `git clone --bare` (the push guard blocks
`git push` in an auto run). The user typed `/my:handoff auto rows 2 1` in a
tmux server started with the branch's `bin/` first on `PATH`.

- **Fixups folded:** pass. `main` has no `fixup!` subject, and the commit
  that adds both specs holds their `approved` status.
- **One window, for row 1:** pass. The call opened only `code-alpha-text`.
- **Row 2 starts without the user:** pass. The review of row 1 refilled the
  slot and opened `code-beta-text`.
- **Both rows done on `main`:** pass. Rows 1 and 2 are ✅, each spec is
  `done` and cites its squash commit, each state has `next=finished` and an
  empty `stopped`.
- **`origin` unchanged:** pass. `show-ref` is the same before and after.

One fault of the fixture, not of the feature: it did not ignore
`.claude/worktrees/`, so `main` showed that folder untracked while a
worktree existed.

## Open Questions

None.
