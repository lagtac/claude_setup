# Design Router Implementation Plan

**Status:** done, 2026-10-20. Shipped in `5dfd634`; kit 73 and my 234 tests pass; row 70.
Manual steps are in the Risk section.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this
> plan task-by-task. The tasks build on each other: the router's table tests read the real
> `plugins.json`, and the ticket tests drive the gate. The project's review rules (`my.md`, "Code
> Review Routing") replace the skill's own reviews: no per-task reviewer, no final
> `requesting-code-review` pass. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `kit:design-router` skill decides which design skill does each job and starts it with
a one-time ticket, a `PreToolUse` gate in `kit` refuses every other call to a design skill, and the
`my` method stops depending on `my:design-system`.

**Architecture:** Three new files in `kit` do the work: the gate (`hooks/design-router-gate.py`),
the ticket script (`bin/design-router-ticket.py`) and the router skill with its plugin list
(`skills/design-router/`). The gate reads the list and the tickets; the router writes tickets
through the script and then calls the skill. The core gets one "Design work" section; the method
files lose their `my:design-system` rules.

**Tech Stack:** Python 3 standard library, `unittest`, Claude Code plugin hooks, Markdown skills.

**Spec:** `docs/plans/2026-10-20-design-router-spec.md` (review:
`docs/plans/2026-10-20-design-router-spec-review.md`).

**Commit type:** `feat`. Branch `feat/design-router`, worktree `.claude/worktrees/design-router`.
Squash subject: `feat(kit-plugin): the design router decides which design skill runs`.

## Global Constraints

- Python 3, standard library only. No new dependency.
- Claude Code 2.1.304 or later (the `PreToolUse` input and the `deny` decision, spec F5).
- Every file under `plugins/kit/` except `tests/` holds none of: `superpowers:`, `docs/plans`,
  `global/CLAUDE.md`, a `my:<name>` skill name, or a bare `my` name as a whole word
  (`test_kit_cites_no_method`). Mind `design-superpowers:`, which contains `superpowers:`: never
  write a `design-superpowers` skill name in a kit file; the plugin name alone is fine.
- No `$` followed by a digit in any kit `SKILL.md` (`test_skill_placeholders.py`).
- The router's text names no method, no plans folder and no `my:` skill (spec, `kit:design-router`).
- The gate never prints `allow`, always exits 0, and fails open (spec D8).
- A ticket is fresh for 300 seconds after it is written (spec, "The ticket").
- Refusal and note texts are copied exactly from the spec's gate table.
- Focused test runs: `cd plugins/kit && python3 -m unittest discover tests -p '<file>'`
  (`plugins/kit/tests` has no `__init__.py`). Full runs, once per task before its first commit:
  `cd plugins/kit && python3 -m unittest discover tests` and
  `cd plugins/my && python3 -m unittest discover tests`.
- Every task commit carries `--trailer "Task: <N>"`.

## Review Focus

1. **A skill name with a leading `/`** (`/design-skills:ux-writing`). A person expects the gate to
   judge it as the name without the slash, not to let it pass. Test: Task 2,
   `test_leading_slash_is_judged`.
2. **Bad hook input:** stdin that is not JSON, or JSON with no `tool_input`. Expected: nothing
   printed, exit 0. Test: Task 2, `test_bad_input_passes`.
3. **A plugin known only from `synced/`,** absent from `installed_plugins.json` and from the list.
   Expected: refused as unreviewed, like an installed one. Test: Task 2,
   `test_unknown_synced_plugin_is_refused`.
4. **`installed_plugins.json` missing or broken.** Expected: an unknown prefix passes (fail open,
   D8), and listed prefixes are still judged. Test: Task 2, `test_missing_installed_list_passes`.
5. **A session ID or skill name holding `/` or `..`.** Expected: the gate reads and deletes nothing
   outside the tickets folder and judges by the list; the ticket script exits 1 and writes nothing.
   Test: Task 3, `test_ticket_path_cannot_escape`.

---

## Context

Three design plugins are on, and several of their skills do the same job. Each can start when its
description matches, so the skill that runs is chance. The user asked for a router that decides,
and asked to take `my:design-system` out of the method (spec, Context). The spec's facts F1–F8 say
what Claude Code allows: `ask` rules do nothing (F3), a `PreToolUse` hook on `Skill` can refuse a
call (F5), and a typed command never reaches the hook (F4).

What exists: `plugins/kit/hooks/hooks.json` registers two `SessionStart` hooks and no
`PreToolUse` hook. `plugins/kit/hooks/method-guard.py` is the pattern for a hook script (module
docstring, `main()`, a `try/except Exception: pass` around it, `sys.exit(0)`).
`plugins/kit/tests/test_method_guard.py` is the pattern for its tests (temporary folders, the real
script run with `subprocess`, environment set per call). `plugins/kit/bin/` is on `PATH` in Claude
Code sessions.

## Files to Modify/Create

From the reference sweep: `grep -rn 'DESIGN-SYSTEM\|design-system\|frontend-design'` over
`global/`, `plugins/`, `README.md`, plus `ls` of `plugins/kit/{hooks,bin,tests,skills}`.

| File | Change | Task |
| --- | --- | --- |
| `plugins/kit/tests/test_neutral_core.py` | `my` names match as whole names; new `names_in`; new tests | 1, 5 |
| `plugins/kit/hooks/design-router-gate.py` | New: the gate | 2, 3 |
| `plugins/kit/hooks/hooks.json` | Add the `PreToolUse` entry | 2 |
| `plugins/kit/skills/design-router/plugins.json` | New: plugin name → state | 2 |
| `plugins/kit/.claude-plugin/plugin.json` | `description` also names the design-router gate | 2 |
| `plugins/kit/tests/test_design_router.py` | New: gate, ticket and table tests | 2, 3, 4 |
| `plugins/kit/bin/design-router-ticket.py` | New, executable: writes one ticket | 3 |
| `plugins/kit/skills/design-router/SKILL.md` | New: the router | 4 |
| `global/CLAUDE.md` | New section "Design work" after "Code" | 5 |
| `global/methods/my.md` | Lines 117, 144, 182–183, 186–196, 212–213 | 6 |
| `global/rules/docs-layout.md` | Step 13, lines 171–174 | 6 |
| `plugins/my/skills/handoff/SKILL.md` | Lines 277 and 746–747 | 6 |
| `plugins/my/skills/handoff/README.md` | Lines 388–389 | 6 |
| `plugins/my/skills/spec-review/spec-reviewer-prompt.md` | Delete lines 70–73 | 6 |
| `plugins/my/skills/design-system/SKILL.md` | Line 176 | 6 |
| `README.md` | `kit` skills, `my:design-system` entry, Hooks | 7 |
| `ROADMAP.md`, `CHANGELOG.md` | At the `done` mark only (review stage) | — |

`plugins/my/bin/ds-count.py` and its test also read `docs/DESIGN-SYSTEM.md`. They belong to the
`my:design-system` skill, which row 69 decides on; they stay unchanged (spec, Out of scope).

## Step-by-Step Implementation

### Task 1: `my` names match only as whole names

**Files:**

- Modify: `plugins/kit/tests/test_neutral_core.py`

**Interfaces:**

- Produces: `names_in(text: str) -> list[str]`, module level in `test_neutral_core.py`: the `my`
  tokens (`my:<n>` for `n` in `MY_NAMES`, and each of `MY_BARE`) found in `text` as whole names.
  A whole name has no letter, digit, `:` or `-` just before it, and no letter, digit or `-` just
  after it. Task 4's `SKILL.md` relies on it to name `design:design-system`.

- [ ] **Step 1: Write the failing test**

```python
    def test_whole_name_match(self):
        self.assertEqual(names_in("run design:design-system now"), [])
        self.assertEqual(names_in("use design-skills:design-systems"), [])
        self.assertEqual(names_in("run the design-system audit"), ["design-system"])
        self.assertIn("my:handoff", names_in("type /my:handoff run"))
```

- [ ] **Step 2: Run it and see it fail**

Run: `cd plugins/kit && python3 -m unittest discover tests -p 'test_neutral_core.py'`
Expected: ERROR, `NameError: name 'names_in' is not defined`.

This step makes `test_kit_cites_no_method` match less text than before. That loosening is the
spec's own change (spec, "Other edits", the `test_neutral_core.py` row), not a weakened test:
`test_whole_name_match` pins what still fails.

- [ ] **Step 3: Implement `names_in`, and use it in `test_kit_cites_no_method`**

One compiled regex per token: `(?<![A-Za-z0-9:-])` + `re.escape(token)` + `(?![A-Za-z0-9-])`.
`test_kit_cites_no_method` keeps its substring check for `docs/plans`, `superpowers:` and
`global/CLAUDE.md`, and asserts `names_in(text) == []` per file for the `my` names.

- [ ] **Step 4: Run it and see it pass**

Same command. Expected: OK.

- [ ] **Step 5: Commit**

```bash
git add plugins/kit/tests/test_neutral_core.py
git commit --trailer "Task: 1" -m "test(kit-plugin): a my name matches only as a whole name"
```

### Task 2: the gate, the plugin list and the hook entry

**Files:**

- Create: `plugins/kit/hooks/design-router-gate.py`, `plugins/kit/skills/design-router/plugins.json`,
  `plugins/kit/tests/test_design_router.py`
- Modify: `plugins/kit/hooks/hooks.json`, `plugins/kit/.claude-plugin/plugin.json`

**Interfaces:**

- Produces (the gate's contract, read by Task 3 and Task 4):
  - Input on stdin: `{"session_id": str, "tool_name": "Skill", "tool_input": {"skill": str}, ...}`.
  - Environment: `DESIGN_ROUTER_PLUGINS` (the list file; default
    `$CLAUDE_PLUGIN_ROOT/skills/design-router/plugins.json`, else the same path relative to the
    script), `DESIGN_ROUTER_PLUGIN_HOME` (default `~/.claude/plugins`), `DESIGN_ROUTER_TICKETS`
    (default `~/.cache/design-router/tickets`).
  - Functions: `load_states(path: Path) -> dict | None` (None when missing or not a JSON object),
    `installed_plugins(home: Path) -> set[str]`, `decide(skill: str, session_id: str) -> dict | None`
    (the object to print, or None), `main() -> int`.
  - `plugins.json`: one JSON object, plugin name → `"routed"`, `"excluded"` or `"not-design"`.
- Test helper in `test_design_router.py`, reused by Task 3:
  `run_gate(skill, session="s1", plugins=None, home=None, raw=None) -> subprocess.CompletedProcess`,
  which builds the hook JSON (or sends `raw` as stdin) and sets the three variables to temporary
  paths: the fixture list and the fixture home unless `plugins` or `home` names another path.
  The fixture home holds `installed_plugins.json` with `{"version": 2, "plugins":
  {"newplug@market": [], "design@synced": [], "kit@claude-setup": []}}` and
  `synced/acct/p1/.claude-plugin/plugin.json` with `{"name": "syncplug"}`. The fixture list is
  `{"design": "routed", "design-skills": "routed", "frontend-design": "routed",
  "design-superpowers": "excluded", "superpowers": "not-design"}`.

- [ ] **Step 1: Write the failing tests**

`decision(out)` parses stdout and returns `hookSpecificOutput.permissionDecision`, or None for
empty stdout.

```python
    def test_routed_is_refused(self):
        r = run_gate("design-skills:design-critique")
        self.assertEqual(decision(r.stdout), "deny")
        self.assertIn("kit:design-router", reason(r.stdout))

    def test_excluded_is_refused(self):
        r = run_gate("design-superpowers:design")
        self.assertEqual(decision(r.stdout), "deny")
        self.assertIn("is excluded from the design router", reason(r.stdout))

    def test_unknown_plugin_is_refused(self):
        r = run_gate("newplug:thing")
        self.assertEqual(decision(r.stdout), "deny")
        self.assertIn("plugins.json", reason(r.stdout))
        self.assertIn("claude plugin update kit@claude-setup", reason(r.stdout))

    def test_unknown_synced_plugin_is_refused(self):      # Review Focus 3
        self.assertEqual(decision(run_gate("syncplug:x").stdout), "deny")

    # A missing script also prints nothing, but exits 2: every "passes" test checks the exit code.
    def test_unknown_prefix_passes(self):
        r = run_gate("somefolder:thing")
        self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_not_design_passes(self):
        r = run_gate("superpowers:brainstorming")
        self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_no_prefix_passes(self):
        r = run_gate("dataviz")
        self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_kit_passes(self):
        # kit is installed in the fixture home and absent from the fixture list, so without
        # rule 2 it would be refused as unreviewed (rule 8).
        r = run_gate("kit:design-router")
        self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_leading_slash_is_judged(self):               # Review Focus 1
        self.assertEqual(decision(run_gate("/design-skills:ux-writing").stdout), "deny")

    def test_bad_input_passes(self):                      # Review Focus 2
        for raw in ("not json", "{}", '{"tool_input": 5}'):
            r = run_gate(None, raw=raw)
            self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_missing_installed_list_passes(self):         # Review Focus 4
        # fixture home with no installed_plugins.json and no synced/ folder
        self.assertEqual(run_gate("newplug:thing", home=EMPTY).stdout, "")
        self.assertEqual(decision(run_gate("design:ux-copy", home=EMPTY).stdout), "deny")

    def test_missing_list_fails_open(self):
        r = run_gate("design:ux-copy", plugins=MISSING_PATH)
        out = json.loads(r.stdout)
        self.assertNotIn("hookSpecificOutput", out)
        self.assertIn(str(MISSING_PATH), out["systemMessage"])
        self.assertEqual(r.returncode, 0)

    def test_broken_list_fails_open(self):
        # the list file holds "{not json"; same assertions as above

    def test_never_allows(self):
        # every input of this class, run once: '"allow"' not in stdout

    def test_hooks_json_registers_gate(self):
        entries = json.loads(HOOKS.read_text())["hooks"]["PreToolUse"]
        self.assertTrue(any(e["matcher"] == "Skill" and
                            any("design-router-gate.py" in h["command"] for h in e["hooks"])
                            for e in entries))

    def test_list_states_are_valid(self):
        states = json.loads(LIST.read_text())
        self.assertTrue(set(states.values()) <= {"routed", "excluded", "not-design"})
        self.assertEqual({k for k, v in states.items() if v == "routed"},
                         {"design", "design-skills", "frontend-design"})
        self.assertEqual({k for k, v in states.items() if v == "excluded"},
                         {"design-superpowers", "product-management", "data"})
        for name in ("kit", "my", "superpowers", "hookify"):
            self.assertEqual(states[name], "not-design")
```

`MISSING_PATH`, `EMPTY`, `HOOKS` (`plugins/kit/hooks/hooks.json`) and `LIST` (the real
`plugins.json`) are module constants or per-test temporary paths, as the implementer prefers.

- [ ] **Step 2: Run them and see them fail**

Run: `cd plugins/kit && python3 -m unittest discover tests -p 'test_design_router.py'`
Expected: the gate tests fail because the script does not exist (`can't open file`, non-empty
stderr, no JSON), `test_hooks_json_registers_gate` fails with `KeyError: 'PreToolUse'`, and
`test_list_states_are_valid` fails with `FileNotFoundError`.

- [ ] **Step 3: Write `plugins.json`**

The first version, in this order of states:

- `routed`: `design`, `design-skills`, `frontend-design`.
- `excluded`: `design-superpowers`, `product-management`, `data`.
- `not-design`: `anidoodle`, `anthropic-skills`, `chrome-devtools-mcp`, `claude-code-setup`,
  `claude-md-management`, `code-simplifier`, `commit-commands`, `context7`,
  `explanatory-output-style`, `feature-dev`, `hookify`, `kit`, `laravel-boost`,
  `modern-web-guidance`, `my`, `php-lsp`, `playwright`, `pyright-lsp`, `skill-creator`,
  `superpowers`, `typescript-lsp`, `vue-lsp`.

Source: the keys of `~/.claude/plugins/installed_plugins.json` by the name before `@`, the `name`
of each `~/.claude/plugins/synced/*/*/.claude-plugin/plugin.json`, and the prefixes in this
session's skill list (`anthropic-skills`), all read on 2026-10-20.

- [ ] **Step 4: Implement the gate in `plugins/kit/hooks/design-router-gate.py`**

Shape and docstring as `method-guard.py`. `decide` runs in this order; the first match wins:

1. `skill` is not a string, or has no `:` after one leading `/` is stripped → None.
2. Prefix (text before the first `:`) is `kit` → None.
3. (Task 3 adds the ticket check here.)
4. `load_states` returns None → `{"systemMessage": "Design router gate: cannot read <path>; it
   lets every skill through."}`.
5. `routed` → refuse with `<skill> is a design skill: invoke kit:design-router, which starts it.`
6. `excluded` → refuse with `<plugin> is excluded from the design router: tell the user, who can
   type the command or turn the plugin off.`
7. `not-design`, or any other value → None.
8. Absent and in `installed_plugins(home)` → refuse with `<plugin> is not reviewed for design
   skills: tell the user to add it to plugins.json in kit's design-router skill, commit, then run
   claude plugin update kit@claude-setup and /reload-plugins; or to type the command.`
9. Absent and not installed → None.

`<skill>` is the name without the leading `/`. "Refuse" prints
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
"permissionDecisionReason": "<text>"}}`. `installed_plugins` returns the empty set for a missing
or broken file, and skips a broken `plugin.json`.

- [ ] **Step 5: Register the gate and update the manifest**

In `plugins/kit/hooks/hooks.json`, add next to `SessionStart`:

```json
"PreToolUse": [
  {
    "matcher": "Skill",
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"$CLAUDE_PLUGIN_ROOT/hooks/design-router-gate.py\"",
        "timeout": 10
      }
    ]
  }
]
```

In `plugins/kit/.claude-plugin/plugin.json`, the `description` ends: "…, kit:setup, the
SessionStart hooks for the tutor and the method guard, and the design router with its PreToolUse
gate."

- [ ] **Step 6: Run the tests and see them pass**

Run: `cd plugins/kit && python3 -m unittest discover tests -p 'test_design_router.py'`, then the
full `kit` and `my` runs. Expected: OK. `test_kit_cites_no_method` passes on the new files.

- [ ] **Step 7: Commit**

```bash
git add plugins/kit/hooks plugins/kit/skills/design-router/plugins.json \
  plugins/kit/tests/test_design_router.py plugins/kit/.claude-plugin/plugin.json
git commit --trailer "Task: 2" -m "feat(kit-plugin): a PreToolUse gate refuses design skills by plugin"
```

### Task 3: one-time tickets

**Files:**

- Create: `plugins/kit/bin/design-router-ticket.py` (mode `0755`)
- Modify: `plugins/kit/hooks/design-router-gate.py`, `plugins/kit/tests/test_design_router.py`

**Interfaces:**

- Consumes: `run_gate` and the fixture from Task 2.
- Produces: `design-router-ticket.py SKILL`. It reads `CLAUDE_CODE_SESSION_ID` and
  `DESIGN_ROUTER_TICKETS` (same default as the gate), creates the folders, and writes an empty
  file `<tickets>/<session id>/<skill>`, replacing an older one so its time is now. It prints
  nothing and exits 0. It exits 1 with one stderr line that starts with `design-router-ticket:`
  when the session ID is empty, when the skill or the session ID is empty, `.` or `..`, or holds
  `/`, or when the write fails. The gate reads the same variable, so tests never touch `~/.cache`.
- Gate: `take_ticket(tickets: Path, session_id: str, skill: str, now: float) -> bool`. True when
  the file exists and its `mtime` is at most 300 seconds before `now`; the file is then deleted.
  A stale file is deleted and the result is False. A session ID or skill that is empty, `.`, `..`
  or holds `/` is never looked up: False. It runs as step 3 of `decide`, before the list is read.

- [ ] **Step 1: Write the failing tests**

```python
    def test_ticket_lets_one_call_through(self):
        ticket = self.tickets / "s1" / "design-skills:ux-writing"
        write_ticket(ticket)
        self.assertEqual(run_gate("design-skills:ux-writing").stdout, "")
        self.assertFalse(ticket.exists())
        self.assertEqual(decision(run_gate("design-skills:ux-writing").stdout), "deny")

    def test_ticket_is_per_session(self):
        write_ticket(self.tickets / "s2" / "design-skills:ux-writing")
        self.assertEqual(decision(run_gate("design-skills:ux-writing").stdout), "deny")

    def test_ticket_is_per_skill(self):
        write_ticket(self.tickets / "s1" / "design:ux-copy")
        self.assertEqual(decision(run_gate("design-skills:ux-writing").stdout), "deny")

    def test_stale_ticket_is_refused(self):
        ticket = self.tickets / "s1" / "design-skills:ux-writing"
        write_ticket(ticket, age=301)          # os.utime to now - 301
        self.assertEqual(decision(run_gate("design-skills:ux-writing").stdout), "deny")
        self.assertFalse(ticket.exists())

    def test_ticket_script_writes(self):
        r = run_ticket("design-skills:ux-writing", session="abc")
        self.assertEqual(r.returncode, 0)
        self.assertTrue((self.tickets / "abc" / "design-skills:ux-writing").is_file())

    def test_ticket_script_needs_session(self):
        r = run_ticket("design-skills:ux-writing", session="")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(list(self.tickets.rglob("*")), [])

    def test_leading_slash_uses_ticket(self):              # review, Needs Investigation
        ticket = self.tickets / "s1" / "design-skills:ux-writing"
        write_ticket(ticket)
        r = run_gate("/design-skills:ux-writing")
        self.assertEqual((r.stdout, r.returncode), ("", 0))
        self.assertFalse(ticket.exists())

    def test_ticket_path_cannot_escape(self):              # Review Focus 5
        # self.tickets is self.root / "tickets". Each case names a routed skill (it has a ":"),
        # and `landing` is where an unguarded join of tickets/<session>/<skill> would land.
        gate_cases = (("..", "design:ux-copy", self.root / "design:ux-copy"),
                      ("s1/..", "design:ux-copy", self.tickets / "design:ux-copy"))
        for session, skill, landing in gate_cases:
            write_ticket(landing)       # a gate without the guard deletes it and lets it through
            self.assertEqual(decision(run_gate(skill, session=session).stdout), "deny")
            self.assertTrue(landing.exists())
            landing.unlink()
        # A script without the guard creates the folders and writes `landing`.
        script_cases = gate_cases + (("s1", "design:x/../../../escape", self.root / "escape"),)
        for session, skill, landing in script_cases:
            self.assertEqual(run_ticket(skill, session=session).returncode, 1)
            self.assertFalse(landing.exists())
```

`test_ticket_is_per_session` and `test_ticket_is_per_skill` pass on Task 2's gate, which has no
ticket check. Their proof that they can fail: after Step 3, change `take_ticket` once to ignore
the session (look up `<tickets>/*/<skill>`), see `test_ticket_is_per_session` fail; then to
ignore the skill (any file under `<tickets>/<session>/`), see `test_ticket_is_per_skill` fail.
Undo both.

`run_ticket(skill, session) -> CompletedProcess` runs the real script with `CLAUDE_CODE_SESSION_ID`
and `DESIGN_ROUTER_TICKETS` set. `self.tickets` and `self.root` come from Task 2's fixture, with
the tickets folder inside `self.root`. `test_never_allows` gains the ticket cases.

- [ ] **Step 2: Run them and see them fail**

Run: `cd plugins/kit && python3 -m unittest discover tests -p 'test_design_router.py'`
Expected: `test_ticket_lets_one_call_through` fails on `'' != <deny JSON>`; the script tests fail
because `design-router-ticket.py` does not exist (return code 2 from `python3`, not 0 or 1).

- [ ] **Step 3: Implement the ticket script and `take_ticket`**

The script follows `tmux-name-pane.py`: shebang, docstring with usage, `argparse` with one
positional `skill`.

- [ ] **Step 4: Run the tests and see them pass**

Same command, then the full `kit` and `my` runs. Expected: OK.

- [ ] **Step 5: Commit**

```bash
git add plugins/kit/bin/design-router-ticket.py plugins/kit/hooks/design-router-gate.py \
  plugins/kit/tests/test_design_router.py
git commit --trailer "Task: 3" -m "feat(kit-plugin): a one-time ticket lets the router start a design skill"
```

### Task 4: the router skill

**Files:**

- Create: `plugins/kit/skills/design-router/SKILL.md`
- Modify: `plugins/kit/tests/test_design_router.py`

**Interfaces:**

- Consumes: `plugins.json` (Task 2), `design-router-ticket.py SKILL` (Task 3), `names_in` (Task 1,
  through `test_kit_cites_no_method`).
- Produces: the table format the tests parse. Each table row matches this regex, and the skills
  are the backticked names in the `skills` cell:

  ```text
  ^\| `(?P<id>[a-z0-9-]+)` \| (?P<job>.+?) \| (?P<skills>.+?) \| (?P<state>decided|undecided|open) \|$
  ```

- [ ] **Step 1: Write the failing tests**

```python
IDS = ["visual-direction", "critique", "accessibility", "copy", "research-plan", "system-audit",
       "tokens", "interaction", "polish", "handoff", "research-synthesis", "journey-map",
       "strategy", "draw", "diagram", "chart"]

    def test_table_ids_unique(self):
        ids = [row["id"] for row in table_rows()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, IDS)

    def test_table_skills_known(self):
        routed = {k for k, v in json.loads(LIST.read_text()).items() if v == "routed"}
        for row in table_rows():
            for skill in row["skills"]:
                self.assertTrue(skill.split(":")[0] in routed
                                or skill in ("artifact-diagramming", "dataviz"), skill)
            if not row["skills"]:
                self.assertIn("Design type", row["skills_cell"])

    def test_every_routed_plugin_used(self):
        used = {s.split(":")[0] for row in table_rows() for s in row["skills"]}
        self.assertTrue(routed_plugins() <= used)

    def test_undecided_rows_have_two(self):
        for row in table_rows():
            want = {"undecided": 2, "decided": 1}.get(row["state"])
            if want:
                self.assertEqual(len(row["skills"]), want, row["id"])
```

`table_rows()` reads `plugins/kit/skills/design-router/SKILL.md` and returns one dict per row
(`id`, `skills`, `skills_cell`, `state`).

- [ ] **Step 2: Run them and see them fail**

Run: `cd plugins/kit && python3 -m unittest discover tests -p 'test_design_router.py'`
Expected: the four tests ERROR with `FileNotFoundError` on `SKILL.md`.

- [ ] **Step 3: Write `SKILL.md`**

Frontmatter: `name: design-router`; a `description` that says it decides which design skill does
a design job and starts it, and lists the jobs of the table by name, so it starts on its own
where the core line is missing. Body, in this order, carried over from the spec sections named
(the spec path itself is not written, per Global Constraints):

1. The steps (spec, "`kit:design-router`", steps 1–6), the ticket-failure line, and the paragraph
   on skills with no prefix.
2. The example line before a decided job's call.
3. The table, exactly the spec's 16 rows, with the `ID` column first and the row format above.
4. The paragraph on "decided" and the skills never named (`design:accessibility-review`,
   `design-skills:design-ops`, and the `excluded` plugins).
5. The trial points of the three undecided rows. Write "A's design system check" with a space:
   the spec's hyphenated "design-system check" fails `test_kit_cites_no_method`.
6. "Both", steps 1–4, and its cost line.
7. "The project file": `.claude/design-router.json`, `{"<job ID>": "<skill>"}`; written, never
   committed.

- [ ] **Step 4: Run the tests and see them pass**

Same command, then the full `kit` and `my` runs. Expected: OK, including
`test_kit_cites_no_method` and `test_no_bare_positional_placeholder` on the new `SKILL.md`.

- [ ] **Step 5: Commit**

```bash
git add plugins/kit/skills/design-router/SKILL.md plugins/kit/tests/test_design_router.py
git commit --trailer "Task: 4" -m "feat(kit-plugin): kit:design-router names and starts the design skill"
```

### Task 5: the core line

**Files:**

- Modify: `global/CLAUDE.md`, `plugins/kit/tests/test_neutral_core.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_core_sends_design_work_to_router(self):
        core = CORE.read_text()
        self.assertIn("Design work", headings(core))
        self.assertIn("invoke `kit:design-router`", core)
```

- [ ] **Step 2: Run it and see it fail**

Run: `cd plugins/kit && python3 -m unittest discover tests -p 'test_neutral_core.py'`
Expected: FAIL, `'Design work' not found in {...}`.

- [ ] **Step 3: Add the section**

In `global/CLAUDE.md`, after the "Code" section and before "Engineering standards":

```markdown
## Design work

- Before any design work — a screen, a flow, visual direction, interface copy, an accessibility
  check, a design system, user research — invoke `kit:design-router`. It names the skill for the
  job. Do not call a design skill directly; the gate refuses it.
```

`test_core_names_no_method` needs no change: it already allows a `kit:` name.

- [ ] **Step 4: Run it and see it pass**

Same command, then the full `kit` and `my` runs. Expected: OK.

- [ ] **Step 5: Commit**

```bash
git add global/CLAUDE.md plugins/kit/tests/test_neutral_core.py
git commit --trailer "Task: 5" -m "feat(global): the core sends design work to kit:design-router"
```

### Task 6: the method stops calling `my:design-system`

**Files:**

- Modify: `global/methods/my.md`, `global/rules/docs-layout.md`,
  `plugins/my/skills/handoff/SKILL.md`, `plugins/my/skills/handoff/README.md`,
  `plugins/my/skills/spec-review/spec-reviewer-prompt.md`, `plugins/my/skills/design-system/SKILL.md`

These are rule texts, not code; the check is a search that must come back empty.

- [ ] **Step 1: Run the check and see it list hits**

Run:

```bash
grep -n 'DESIGN-SYSTEM\|my:design-system\|`frontend-design`' global/methods/my.md \
  global/rules/docs-layout.md plugins/my/skills/handoff/SKILL.md \
  plugins/my/skills/handoff/README.md plugins/my/skills/spec-review/spec-reviewer-prompt.md
```

Expected: hits at `my.md:117,144,182,187,193,195`, `docs-layout.md:171,173`,
`handoff/SKILL.md:277,747`, `handoff/README.md:389`, `spec-reviewer-prompt.md:70`.

- [ ] **Step 2: Make the edits (spec, "`global/methods/my.md`" and "Other edits")**

- `my.md:117`: delete the trigger-table row "UI work (a screen, a state or a component) …".
- `my.md:144`: delete "; the spec reads `docs/DESIGN-SYSTEM.md` first and maps each element to a
  component, variant or token listed there, or labels it «new: `<name>`» when this row or a row
  ordered before it builds it as a shared component". The parenthesis then closes after
  "ordered before it".
- `my.md:182–183`: the bullet becomes "- **Aesthetic direction** — typography, and choices that
  do not read as templated defaults. `kit:design-router` names the skill."
- `my.md:186–196`: delete the paragraph "The canvas is built on the project's Design System
  artifact …" through "… skips this paragraph.", and one of the two blank lines around it.
- `my.md:212–213`: delete the sentence "The same step refreshes the inventory: see step 13 in
  `~/.claude/rules/docs-layout.md`."
- `docs-layout.md:171–174`: delete the four lines from "When `docs/DESIGN-SYSTEM.md` exists" to
  "A project with no inventory skips this."
- `handoff/SKILL.md:277`: row 19 reads "(`ROADMAP.md`, `CHANGELOG.md`, the plans index)".
- `handoff/SKILL.md:746–747`: "the plans index, `ROADMAP.md` and `CHANGELOG.md` are shared docs."
- `handoff/README.md:388–389`: "… `ROADMAP.md`, `CHANGELOG.md` or the plans index only when …".
- `spec-reviewer-prompt.md:70–73`: delete the bullet "When `docs/DESIGN-SYSTEM.md` exists …" and
  its three sub-bullets.
- `design-system/SKILL.md:176`: "That row's canvas uses `frontend-design` for the visual
  direction." becomes "That row's canvas takes its visual direction through
  `kit:design-router`."

- [ ] **Step 3: Run the check again and see it come back empty**

Same `grep`. Expected: no output, exit 1. Then
`markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc` on the six files
(the repo has no config of its own), and the full `kit` and `my` runs. Expected: no new lint
errors; tests OK.

- [ ] **Step 4: Commit**

```bash
git add global/methods/my.md global/rules/docs-layout.md plugins/my/skills
git commit --trailer "Task: 6" -m "feat(global): the my method no longer calls my:design-system"
```

### Task 7: README

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Edit**

- "### `kit` skills": a `kit:design-router` entry. It decides which design skill does each job,
  starts it with a one-time ticket (`plugins/kit/bin/design-router-ticket.py`), can run two
  skills side by side and keep the winner in `.claude/design-router.json`. Its plugin list is
  `plugins/kit/skills/design-router/plugins.json`; tests:
  `cd plugins/kit && python3 -m unittest discover tests`.
- "### `my` skills", the `my:design-system` entry gains: "The method no longer calls it; row 69
  decides whether it moves to `kit` or is deleted."
- "## Hooks", under `plugins/kit/hooks/hooks.json`: a **PreToolUse** (Skill) bullet.
  `design-router-gate.py` refuses Claude's calls to skills of `routed`, `excluded` and unreviewed
  plugins unless the router wrote a ticket. A typed command always runs. It fails open.

- [ ] **Step 2: Lint and commit**

Run `markdownlint-cli2` on `README.md`. Expected: no new errors.

```bash
git add README.md
git commit --trailer "Task: 7" -m "docs(kit-plugin): README lists the design router and its gate"
```

### Task 8: rehearsal

The user chose this form on 2026-10-20 (see Risk, R16): the code stage runs spec steps 1 to 5
headless; the user does step 6 and the default-mode permission checks after the `done` mark.

**Files:** none in the repo. Notes go to `<scratchpad>/rehearsal.md`, and the results go into
the squash commit's body.

- [ ] **Step 1: Run steps 1, 3, 4 and 5 of the spec's rehearsal headless**

From a scratch folder `<scratch>` outside the repo, with the branch's `kit`:

```bash
cd <scratch> && claude -p --plugin-dir <worktree>/plugins/kit --add-dir <scratch> \
  --add-dir <worktree>/plugins/kit --permission-mode default \
  --output-format stream-json --verbose '<prompt>' > <scratch>/run-<n>.jsonl
```

Read refusals from the `tool_result` messages in the stream, not only from `permission_denials`,
which can miss them. `--plugin-dir` loads the branch's `kit` next to the installed one; check in
the `init` message that `kit:design-router` is listed, and that a gate refusal (case 1) happens.
If the installed `kit` shadows the branch copy, run with `kit@claude-setup` off in a local
settings file of `<scratch>`.

1. A prompt that asks Claude to invoke `design-skills:ux-writing` directly. Pass: the result
   names `kit:design-router`.
2. (Spec step 2.) The prompt `/design-skills:ux-writing write a label for a save button`, a slash
   command as the first prompt (spec F4). Pass: the skill runs.
3. An accessibility request on a small HTML file. Pass: the router writes the ticket and starts
   `design-skills:accessibility-audit`. Record each `permission_denials` entry (R11).
4. A critique request. Pass: the router takes option A and says the job is undecided.
5. Compare the prefixes in the run's skill list (the `init` message of `--output-format
   stream-json`) with the keys of `plugins.json`. Pass: none is missing.

- [ ] **Step 2: Record**

Write each pass or fail, and the permission result, into the squash commit's body. A fail is a
stop for the user (code stage, row 8).

The user does spec step 6 ("both" in a scratch project) and the default-mode permission checks
(R11, R13) after the `done` mark.

## Trade-Offs / Alternatives Considered

The spec's "Trade-offs" section holds the design choices. The plan adds three:

- **Ticket folder for tests.** The ticket script reads `DESIGN_ROUTER_TICKETS` like the gate
  (chosen), or the tests set `HOME`. One variable for both keeps the two in step and needs no fake
  home for the gate's other paths.
- **Whole-name match in `test_neutral_core.py`.** A regex per token (chosen), or an allow list of
  the two design skill names. The allow list would need an entry for each new design skill whose
  name ends like a `my` skill.
- **Stale ticket.** Deleted, then the call is judged by the list (chosen). For a `routed` skill
  that is the spec's refusal; for a `not-design` skill no ticket is ever written.

## Dependencies

- Row 67, merged in `f03b0e3`: the `my.md` text this plan edits.
- Row 68 starts from the text this plan leaves; row 69 decides `my:design-system`'s place.
- Claude Code 2.1.304 or later.
- Python 3 standard library. No new package.

## Risk

The spec's R1–R13 hold unchanged. The plan adds:

- **R14. Update window.** After the merge, the live core (symlinked from `global/CLAUDE.md`)
  names `kit:design-router` at once. The installed `kit` gets the router and the gate only after
  `claude plugin update kit@claude-setup` and `/reload-plugins`. Until then, the core line names a
  skill that is not there, and no gate runs. The `done` mark lists the update as a manual step.
- **R15. The plugin list is a snapshot of one machine.** A plugin installed on another machine and
  missing from the list is refused there (D7, R4). The refusal text says how to fix it.
- **R16. The rehearsal is split.** The spec asks for a rehearsal by hand before the `done` mark,
  and its Delegation section lets the auto run reach the `done` mark without the user. The user
  chose on 2026-10-20: the code stage runs steps 1 to 5 headless (Task 8); the user runs step 6
  ("both") and the default-mode permission checks (R11, R13) after the `done` mark. A fault that
  only step 6 or an interactive session shows is found after the merge, and becomes a new row.
- **R17. Line numbers drift.** Task 6 names lines from `main` at 2026-10-20. A later commit on
  `main` may move them; the `grep` in Task 6, Step 1 finds the current lines.

Known limits from the end-of-branch reviews (code review and soundness review of 2026-10-20):

- **R18. Session IDs after `/clear` or a resume.** The ticket script files a ticket under
  `CLAUDE_CODE_SESSION_ID`; the gate looks it up under the hook's `session_id`. They match in a
  fresh session. Nobody has checked them after `/clear`, `--resume`, `--fork-session` or a
  compaction. If they differ, every routed call is refused; the router then says so and prints
  the command for the user to type (the fix round added that line).
- **R19. A bare skill name passes.** The gate lets a name without `:` through. The Skill tool's
  description says plugin skills are called as `plugin:skill`, but nobody has checked what it does
  with a bare name. Rehearsal step 5 also found three loaded plugins (`cc-plugin-agents-md`,
  `cc-plugin-plugin-authoring`, `cc-plugin-telemetry`) whose skills carry no prefix. A design
  plugin loaded that way would pass the gate.
- **R20. A project skill folder named like a listed plugin.** A folder `design` or `data` of
  project skills would be refused as `routed` or `excluded`. No project under `~/projects` has one
  on 2026-10-20.
- **R21. A broken list warns on every call.** The `systemMessage` shows on each Skill call with a
  prefix other than `kit`. The list is in this repo, and `test_list_states_are_valid` checks it.
- **R22. Unused tickets stay.** A ticket the router writes but never uses, and its session folder,
  stay under `~/.cache/design-router/tickets/`. The gate refuses a stale ticket, so they cause no
  wrong result.
- **R23. The ticket write in `auto` mode is not rehearsed.** The headless rehearsal ran in default
  mode, where the write was denied until `Bash(design-router-ticket.py *)` was allowed.
- **R24. `my:design-system`'s own text still names step 13.** Its description and body describe
  `refresh` at step 13, which the method no longer calls. Row 69 decides the skill's future.

Known limits from the re-reviews (both final, 2026-10-20):

- **R25. The attended check may prompt.** The router runs `printenv CLAUDE_CODE_SESSION_ATTENDED`
  to learn whether a user can answer. Rehearsal step 4 found that call needs approval in default
  mode. Headless, it was denied, and the router judged from the session instead.
- **R26. The spec's settings list is shorter than the plan's.** The spec's "The user's settings"
  section and its R11 do not name the `Bash(design-router-ticket.py *)` allow rule. The manual
  steps below are the full list.
- **R27. Case and spaces.** The gate matches the prefix exactly. `Design:ux-copy` or
  `" design:ux-copy"` passes it. Nobody has checked whether the Skill tool would resolve such a
  name to a routed skill.
- **R28. A skill the router never names.** `design:accessibility-review` and
  `design-skills:design-ops` are refused like every routed skill, and the router does not start
  them. A user who wants one types the command.

Manual steps at the `done` mark: turn off `design-superpowers@synced` in `~/.claude/settings.json`;
add `Bash(design-router-ticket.py *)` and `Bash(printenv CLAUDE_CODE_SESSION_ATTENDED)` to
`permissions.allow` in `~/.claude/settings.json`, so the router can start a skill where no user can
answer (R11, R25); run `claude plugin update kit@claude-setup` and `/reload-plugins`; repeat
rehearsal step 3 with `--permission-mode auto` (R23); compare the hook's `session_id` with
`CLAUDE_CODE_SESSION_ID` after `/clear` and after a resume (R18); check whether the Skill tool
resolves a bare or differently cased name to a routed skill (R19, R27); and the rehearsal parts
left to the user (Task 8).

Done marks (review stage): spec and plan `done`, citing the squash commit; `ROADMAP.md` row 70 to
✅ with `my:roadmap-management`, and the `CHANGELOG.md` entry with `my:changelog-management`. The
spec commit already edited row 69 and linked row 70, so no commit only sets 🚧.

## Testing Strategy

Unit tests: `plugins/kit/tests/test_design_router.py` (Tasks 2–4) and
`plugins/kit/tests/test_neutral_core.py` (Tasks 1 and 5). The gate and ticket tests run the real
scripts with `subprocess` on the JSON Claude Code sends, which is the gate's public surface. The
table tests read the real `SKILL.md` and `plugins.json`.

End of branch: `cd plugins/kit && python3 -m unittest discover tests` and
`cd plugins/my && python3 -m unittest discover tests` (spec, Delegation).

End to end: Task 8, the rehearsal.

## Open Questions

None. The rehearsal question was answered on 2026-10-20 (Risk, R16).
