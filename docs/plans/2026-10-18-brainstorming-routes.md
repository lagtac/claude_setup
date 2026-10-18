# Brainstorming's routes Implementation Plan

**Status:** approved, 2026-10-18. Written by the `my:handoff` plan stage from the approved spec.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. The tasks are small text edits that
> must share one set of route names, and Task 1's red rehearsal must run
> before any rule text changes, so one session works through them in order.
> The global review rules replace that skill's own reviews: run no per-task
> reviewer and no final `requesting-code-review` pass. The `my:handoff`
> review stage runs the end-of-branch reviews. Steps use checkbox (`- [ ]`)
> syntax for tracking.

**Goal:** Replace `my`'s size table (Small, Medium, Large) with brainstorming's
paths, adapted by a risk line, a two-file limit on bounded, a bug route and a
spike file, and use the new route names in every live rule file.

**Architecture:** Rule text only, plus one test name and one new test.
`global/methods/my.md` gets a "Pick the route" section in place of "Size the
process to the change". The other rule files, skills and READMEs take the
route names. A headless rehearsal (`claude -p`, which runs one prompt and
exits) proves that a session picks the right route under the new text and not
under the old.

**Tech Stack:** Markdown, Python 3 `unittest`, `claude -p`, `markdownlint-cli2`.

**Spec:** `docs/plans/2026-10-18-brainstorming-routes-spec.md`. Read it first:
its decisions D1 to D12 and its Design section hold the exact wording this
plan points at.

**Commit type:** `feat`. The branch is `feat/brainstorming-routes`, in the
worktree `.claude/worktrees/brainstorming-routes`. The squash commit's subject
is `feat(global): brainstorming's paths replace the size table (row 67)`.
Task commits use the scopes in Project facts: `global`, `my-plugin`,
`kit-plugin`, or none for `ROADMAP.md` and zitamu's local file, as earlier
commits to those files do.

## Global Constraints

- No new dependencies (spec, Dependencies; Delegation: `none`).
- The five route names, written exactly so: `spike`, `bounded`,
  `architectural`, `architectural with plan`, `bug` (D4). In running text
  they are lower case; in a table's first column or at the start of a bullet
  they are capitalised (`**Bounded**`).
- "An architectural change" means either architectural route; "architectural"
  alone in the route table means the one without a plan (Design, item 1).
- The risk line, word for word from D2: "a change to stored data or its
  shape, permissions, a message or public contract, or something hard to
  reverse".
- Finished specs, plans, reviews and reports keep their size words. They are
  records (Out of scope). Never edit a file under `docs/` except this plan.
- Name roadmap rows by number, never by line: other sessions edit
  `ROADMAP.md` on `main`, so lines move.
- The phrase "Routing a report" and "Routes a large report's findings" in
  `docs-layout.md` keep their meaning (sending findings to rows). Do not
  rename them.
- Prose follows the `plain` rules: one idea per sentence, common words, no
  idioms.

## Review Focus

1. **A bug whose fix crosses the risk line.** D6 sends it to brainstorming
   after the root cause. The rehearsal cannot set this up (spec, Testing
   strategy 2). Task 1, step 9 checks by reading that the Bug bullet names
   all three cases: the risk line, several reasonable fixes, three failed
   fixes.
2. **A spike file that cites a commit hash from its branch.** The
   `pre-commit` hook refuses it, so the spike would not land. Task 1, step 9
   checks that the Spike bullet says to name the branch and never a hash;
   Task 2 checks the same in the Spike kind row.
3. **A spike file shown as open work by `my:status`.** D7 relies on
   `status-scan.py` treating `answered` as closed. Task 2 adds a test that
   pins it.
4. **A size word left in an open roadmap row, or a new row written with a
   size.** Task 3 changes rule 11's example; Task 5 runs a check over every
   open row.
5. **A task with an architecture brief, or one that hits the risk line,
   handed the wrong layout.** D11 keeps the brief rule; the risk line decides
   the plan. Task 1, step 9 checks that "Discovery authority" says both, and
   the rehearsal's `deleted_at` prompt must give `architectural with plan`.

---

### Task 1: The route section in `my.md`

**Files:**

- Modify: `global/methods/my.md` (section "Size the process to the change"
  and its table; the nine places in the spec's "Other edits to `my.md`";
  "Precedence"; "Discovery authority")
- Modify: `plugins/kit/tests/test_neutral_core.py` (`METHOD_HEADINGS`)
- Test (not committed): the rehearsal fixture and checker in the session's
  scratchpad, `<scratchpad>/rehearsal/`

**Interfaces:**

- Produces: the heading `#### Pick the route` and the route table, which
  Tasks 2 to 4 point at by name ("the route table in
  `~/.claude/methods/my.md`").

- [ ] **Step 1: Check that zitamu's local file holds no uncommitted edit**

Run against the main checkout, not the worktree, because a fresh worktree
never shows the user's uncommitted edits:

```bash
git -C /home/dchris/projects/claude-setup status --porcelain -- projects/real-estate-webapp/claude-local.md
```

Expected: no output. If it prints a line, stop: that is the spec's
Dependencies gate, and the user must commit the edit first.

- [ ] **Step 2: Record the size-word baseline (the red step of Testing 1)**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && grep -rnwE 'Small|Medium|Large' global/methods/my.md global/rules/docs-layout.md plugins/my/skills plugins/my/README.md projects/real-estate-webapp/claude-local.md > <scratchpad>/size-words-before.txt; wc -l < <scratchpad>/size-words-before.txt
grep -rn -i -E 'size table|size the process|size not set|sizes its work|by size|pick a size|its size' global/methods/my.md global/rules/docs-layout.md plugins/my/skills plugins/my/README.md plugins/kit/tests/test_neutral_core.py >> <scratchpad>/size-words-before.txt
```

Expected: the first count is above 8. The lines include `my.md`'s table rows
for Small, Medium and Large, and the `High / Medium / Low` lines in
`spec-reviewer-prompt.md` and `code-reviewer-prompt.md`.

- [ ] **Step 3: Build the rehearsal fixture**

A git repo at `<scratchpad>/rehearsal/fixture`, with one commit. Each prompt
in step 5 must name something that exists:

- `app.py`: an `argparse` script with a `status` command that prints how many
  listings exist, and a function
  `filter_by_date(listings: list[dict], start: date, end: date) -> list[dict]`
  whose comparison is `< end`, so it drops the last day.
- `schema.sql`: `CREATE TABLE listings (id INTEGER PRIMARY KEY, title TEXT, listed_on DATE);`
  and `models.py` with a `Listing` dataclass of the same three fields.
- `templates/index.html`, `search.html`, `detail.html`, `new.html`,
  `account.html`: each shows the label `Listing` at least once.
- `docs/DESIGN-SYSTEM.md`: one line, `Sources: none yet. No shared
  components.` Without it, the UI trigger row runs `my:design-system audit`
  before brainstorming for the rename prompt. When that audit runs is a known
  limit that row 70 settles (spec, Risk), and this rehearsal tests the route,
  not the audit.
- `CLAUDE.md`: the line `@<absolute worktree path>/global/methods/my.md`,
  then a `## Project facts` block (Method: my; Commit scopes: `app`; Test
  command: `python3 -m unittest`; Plans index: none; Remote: none). Without
  the block, the rules tell the session to run `/kit:setup my` first.
- `.claude/settings.json`:
  `{"enabledPlugins": {"my@claude-setup": true, "superpowers@synced": true, "kit@claude-setup": false}, "permissions": {"allow": ["Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(find:*)", "Bash(git log:*)", "Bash(git status:*)", "Bash(git diff:*)", "Bash(python3:*)"]}}`.
  kit is off so that its method guard, which warns about an import that is
  not `@~/.claude/methods/my.md`, adds no message to the session. The allow
  list lets brainstorming explore the fixture before its route line: the
  user's own settings allow almost no command, and a denial before the
  judged step fails the run (step 4). Each run works on its own copy of the
  fixture, so `python3` there touches nothing else.

- [ ] **Step 4: Write the checker `<scratchpad>/rehearsal/check.py`**

`check(stream_path: str, prompt_id: str) -> tuple[bool, str]` reads one
`--output-format stream-json` file and returns pass or fail with a reason.
It collects, in order, the assistant text blocks and the `tool_use` blocks.

- A **route line** is the first text line matching
  `(?i)^\W*(?:route\W*\s*|this (?:looks|is)(?: like)?\s+(?:an?\s+)?)?(spike|bounded|architectural with plan|architectural)\b`.
  It accepts `**Route:** bounded`, `Bounded: …`, `This is a spike` and
  `this looks like a spike`.
- A **size line** is any text line matching
  `(?i)^\W*(?:size\W*\s*(small|medium|large)\b|(small|medium|large)(?:\s*[:—–]|\s+-\s))`.
  It accepts `Small: …` and `**Size:** Medium`, and not ordinary prose such
  as `Small change, so …` or `Medium-sized`.
- An **edit** is a `tool_use` named `Edit`, `Write` or `NotebookEdit`.
- The **judged step** is the route line, or, for `bug`, the
  `systematic-debugging` Skill call.
- Every prompt fails when a size line appears anywhere, or when an event
  with `"subtype":"permission_denied"` comes before the judged step. A
  denial after it does not count: the user's settings allow few commands,
  so a correct run may be denied a later command, such as a `python3` run
  that reproduces the bug. Count those events in the stream: the final
  `permission_denials` array can be empty while a denial happened.

| `prompt_id` | Pass when |
| --- | --- |
| `bug` | A `Skill` tool_use with `skill` equal to `superpowers:systematic-debugging` appears, and no route line comes before it. |
| `quiet` | The route word is `bounded`, and no edit appears. |
| `rename` | The route word is `architectural` (not `architectural with plan`, not `bounded`), and the assistant text names at least three of the five template files, or says `five` or `5` files. |
| `deleted_at` | The route word is `architectural with plan`, and the route line contains one of `stored`, `schema`, `column` or `table` (any case). |
| `pdf` | The route word is `spike`, and no edit appears. |

`main()` takes a folder of `<prompt_id>-<n>.jsonl` files, prints one line per
file (`<file> PASS|FAIL <reason>`), and exits 1 if any file fails.

Then prove the checker before any real run. Write hand-made streams in
`<scratchpad>/rehearsal/selftest/`, one JSON line per event in the
stream-json shape, and check each against its expected result:

| File | Holds | Expected |
| --- | --- | --- |
| `quiet-1.jsonl` | text `**Route:** bounded: a flag on status; no risk trigger.` | PASS |
| `quiet-2.jsonl` | text `Small: one file, no stored data.` | FAIL (size line) |
| `quiet-3.jsonl` | the route line of `quiet-1`, then an `Edit` tool_use | FAIL (edit) |
| `pdf-1.jsonl` | text `This is a spike: can the library render Greek?` | PASS |
| `pdf-2.jsonl` | text `this looks like a spike`, then text `Small change, so I will just try it.` | PASS (prose is no size line) |
| `rename-1.jsonl` | text `Architectural with plan: …` and five template names | FAIL (wrong route) |
| `deleted_at-1.jsonl` | text `Architectural with plan: a stored column.` | PASS |
| `bug-1.jsonl` | a `systematic-debugging` Skill call, then a `permission_denied` event | PASS |
| `bug-2.jsonl` | a `permission_denied` event, then the Skill call | FAIL (denial first) |
| `bug-3.jsonl` | text `Bounded: …`, then the Skill call | FAIL (route line first) |

Run `python3 <scratchpad>/rehearsal/check.py <scratchpad>/rehearsal/selftest`
and compare each line with the table. Every result must match before step 6.

- [ ] **Step 5: Write the runner `<scratchpad>/rehearsal/run.sh <out dir>`**

It runs each of the five prompts three times, five runs at a time
(`xargs -P 5`), each as:

```bash
cd <fixture> && TMPDIR=<scratchpad>/rehearsal/tmp claude -p "<prompt>" \
  --output-format stream-json --verbose --max-turns 10 \
  --permission-mode acceptEdits --add-dir <scratchpad>/rehearsal \
  > <out dir>/<prompt_id>-<n>.jsonl
```

Runs that shared one fixture at once would see each other's edits, so each
run gets its own copy, `cp -r <fixture> <out dir>/fx-<prompt_id>-<n>`, and
runs there. The prompts, exactly:

| `prompt_id` | Prompt |
| --- | --- |
| `bug` | `Fix: the date filter drops the last day` |
| `quiet` | ``Add a `--quiet` flag to the existing `status` command`` |
| `rename` | `Rename the label 'Listing' to 'Property' on every page` |
| `deleted_at` | ``Add a `deleted_at` column so listings can be restored`` |
| `pdf` | `Can the PDF library render Greek fonts?` |

Also one load probe, run once before the fifteen:
`Quote, word for word, the heading of the section in your method rules that says how to choose the process for a task. Do nothing else.`
Its text must contain the expected heading, or the rules did not load.

- [ ] **Step 6: Run the red rehearsal against the old `my.md`**

Run `run.sh <scratchpad>/rehearsal/red` with `run_in_background`, then
`python3 <scratchpad>/rehearsal/check.py <scratchpad>/rehearsal/red`.

Expected: the load probe quotes `Size the process to the change`, and the 12
runs of `quiet`, `rename`, `deleted_at` and `pdf` FAIL. The old rules print a
size line (`Small: …`, `Medium: …`, `Large: …`), which fails them. The 3
`bug` runs may PASS: the old rules also send a bug to `systematic-debugging`,
so a red `bug` pass only means the old session printed no size line. Record
the `bug` count; it is not a checker fault.

If the load probe does not quote that heading, the absolute import did not
load. Then copy the worktree's `my.md` into the fixture as
`.claude/method/my.md`, import it as `@.claude/method/my.md`, run the probe
again, and recopy the file before the green run in step 12. Record the
change in the plan's **Risk** section.

If a run of the other four prompts passes under the old rules, the checker
does not test what it claims. Fix the checker, not the rules, rerun the
self-test of step 4, then rerun.

- [ ] **Step 7: Rename the heading in `METHOD_HEADINGS`**

In `plugins/kit/tests/test_neutral_core.py`, replace
`"Size the process to the change"` with `"Pick the route"`. This test only
checks that the core lacks these headings, so it cannot fail first. Step 11
checks the rename with `grep` instead. Do not add a test that every listed
heading exists in a method file: `"Learning workspaces"` exists in none, and
this row does not touch it.

- [ ] **Step 8: Write the route section in `my.md`**

Replace the heading `#### Size the process to the change`, its paragraph,
its table and its three bullets with `#### Pick the route`, holding, in
this order:

1. **The opening.** Write it as one paragraph with this content, in this
   order. Brainstorming sorts a task into spike, bounded or architectural.
   `my` uses these paths as its routes. It adapts them with the risk line
   and the two-file limit on bounded, and it gives bugs their own route.
   Then the meaning of "an architectural change" (Global Constraints). Then:
   "State the route in one line with the reason and the risk check, for
   example "Bounded: a flag on the existing `status` command; no risk
   trigger." Brainstorming says this line before its first question. A bug
   states no route (see Bug below). The user can change the route. When
   unsure between two routes, pick the heavier one. A route only moves up:
   when the work turns out heavier than its route, stop and say so before
   going on." This is D1, D6 and D8 in the spec's words; add no rule on when
   the line comes beyond them.
2. **The risk line** (D2), one paragraph: the risk line's words, then
   "is architectural with plan, whatever path brainstorming would pick. A
   spike is exempt, because its code never lands. The risk line also decides
   where the tasks go: an architectural change without a risk trigger keeps
   its tasks in the spec; one with a trigger gets a separate plan (D3)."
3. **The route table**, copied from the spec's Design, item 3, with its five
   rows and five columns.
4. **One bullet per route:**
   - **Spike:** every point of D7's bullet list, plus its paragraph on a
     spike inside an architectural route, plus the sentence that
     `my:architect`'s own spikes stay as they are. It must say: the branch is
     `spike/<slug>` and never merged; the file is
     `docs/plans/YYYY-MM-DD-<slug>-spike.md` with four parts (the question,
     what was tried with the branch name, the answer, the recommendation);
     the file names the branch, never a commit hash from it, because the
     `pre-commit` hook refuses a doc that cites a commit not on `main`; its
     status is `answered, <date>`; one `docs:` commit, no review; no roadmap
     row needed; keeping the code is a new task, classified again.
   - **Bounded:** D5's first paragraph (one or two files in an existing flow,
     no risk trigger; more files is architectural; a short design in chat,
     approved before any code). Then today's Small bullet, with "Small"
     replaced: brainstorming runs on its bounded path, and the bullet skips
     the writing-plans and executing-plans rows. A bug still starts with
     `superpowers:systematic-debugging`; every code change starts with a
     failing test; it runs in a worktree; known limits go into the squash
     commit message; "Several bounded changes and bug fixes may share one
     branch when each one alone is bounded or a bug fix", with the rest of
     today's sentence on commits, review round and squash body kept.
   - **Bug:** D6, with its three cases as a list. "It skips the
     brainstorming, writing-plans and executing-plans rows, unless it goes to
     brainstorming. Otherwise the fix follows the bounded rules, without the
     design gate."
   - **Architectural:** today's Medium bullet, word for word, except: "Medium
     writes" becomes "Architectural writes"; "supervised is the route above"
     becomes "supervised is the hand-off above"; "the plan" for a Medium
     change becomes "the plan" for an architectural change without a plan.
   - **Architectural with plan:** "follows the rest of this file unchanged."

- [ ] **Step 9: Make the other edits in `my.md`**

Each row of the spec's table "Other edits to `my.md`", in full. Its
Precedence row is the first bullet below, so make it once; the second bullet
is one more edit:

- **Precedence**, after the sentence that ends "(announce when it does).":
  "Brainstorming's path decides the route of a task, adapted only by the
  risk line and the two-file limit on bounded (see "Pick the route"), and a
  spike's file goes to `docs/plans/`." (D12)
- **Discovery authority**, the bullet "Brainstorming classifies the task as
  architectural, never bounded or spike.": add "Whether it also gets a plan
  follows the risk line." (D11)

Then check by reading (Review Focus 1, 2 and 5): the Bug bullet lists the
three cases; the Spike bullet says to name the branch and never a hash;
"Discovery authority" holds both sentences.

- [ ] **Step 10: Run the unit tests**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes/plugins/kit && python3 -m unittest discover tests
```

Expected: `OK`.

- [ ] **Step 11: Check the heading by `grep`**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && grep -c '^#### Pick the route$' global/methods/my.md && ! grep -rn 'Size the process' global/methods/my.md plugins/kit/tests/test_neutral_core.py
```

Expected: `1`, and exit status 0.

- [ ] **Step 12: Run the green rehearsal**

Run `run.sh <scratchpad>/rehearsal/green` with `run_in_background`, then
`python3 <scratchpad>/rehearsal/check.py <scratchpad>/rehearsal/green`.

Expected: the load probe quotes `Pick the route`; 15 PASS, so each prompt
passes all three runs. A failing run is a test failure: use
`superpowers:systematic-debugging`. A fix that changes what a rule decides,
rather than how it is worded, is a design change: stop. A `deleted_at` run
that fails because `my:architect` ran before the route line is such a case
(Risk): stop, and do not add a timing rule. Keep both result
folders until the branch is merged; the `done` mark cites their counts.

- [ ] **Step 13: Lint and commit**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc global/methods/my.md && git add global/methods/my.md plugins/kit/tests/test_neutral_core.py && git diff --cached
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && git commit --trailer "Task: 1" -m "feat(global): brainstorming's paths replace the size table in my.md"
```

Expected: the lint prints no new error compared with `main`.

### Task 2: The spike file and `answered` in `docs-layout.md`

**Files:**

- Modify: `global/rules/docs-layout.md` (sections "Kinds of document", "From
  report to roadmap", "Status line", "One feature, four commits on `main`")
- Test: `plugins/my/tests/test_status_scan.py` (class `DocsTest`). It pins
  D7's claim that a spike file never shows as open work (Review Focus 3).

**Interfaces:**

- Consumes: the route table's name from Task 1.

- [ ] **Step 1: Write the test**

```python
def test_answered_spike_is_not_open(self):
    commit(self.repo, "docs: spike", {
        "docs/plans/2026-10-18-fonts-spike.md":
            "# Fonts\n\n**Status:** answered, 2026-10-18. Yes, with a bundled font.\n",
    })
    self.assertNotIn("fonts-spike.md", self.scan())
```

- [ ] **Step 2: Run it, then break it on purpose**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes/plugins/my && python3 -m unittest tests.test_status_scan.DocsTest.test_answered_spike_is_not_open
```

Expected: PASS, because no code changes. So prove it can fail: add
`"answered"` to `OPEN_STATUSES` in `plugins/my/bin/status-scan.py`, rerun,
expect FAIL with `fonts-spike.md` found in the output, then undo the edit and
check `git diff plugins/my/bin/status-scan.py` prints nothing.

- [ ] **Step 3: Edit `docs-layout.md`**

The five edits in the spec's Design, "`global/rules/docs-layout.md`":

- the Spike row in "Kinds of document", copied from the spec;
- the chain becomes `report → roadmap rows, placed in the order → spec or plan, by route → branch`;
- a status row placed after `done`: `answered` in the first column, and "A
  spike. The sentence gives the answer in short." in the second;
- under "Two more commits are allowed": change "Two" to "Three", and add
  "The spike file of a spike that runs inside an architectural route, before
  the spec, is its own `docs:` commit, before step 1." The Spike kind row
  must also say the file names the spike's branch, never a commit from it
  (Review Focus 2);
- the four-commits sentence, as the spec words it.

- [ ] **Step 4: Run the tests and lint**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes/plugins/my && python3 -m unittest discover tests && cd ../.. && markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc global/rules/docs-layout.md
```

Expected: `OK`, and no new lint error.

- [ ] **Step 5: Commit**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && git add global/rules/docs-layout.md plugins/my/tests/test_status_scan.py && git diff --cached
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && git commit --trailer "Task: 2" -m "feat(global): docs-layout gains the spike file and the answered status"
```

### Task 3: The skills name routes

**Files:**

- Modify: `plugins/my/skills/roadmap-management/SKILL.md` (rules 4, 6 and 11,
  and the two lines in rules 6 and 10 that repeat rule 11's order)
- Modify: `plugins/my/skills/handoff/SKILL.md` (the `auto` form, "Stop points
  in auto mode", the code stage's auto preamble)
- Modify: `plugins/my/skills/handoff/README.md` (six lines)
- Modify: `plugins/my/skills/design-system/SKILL.md` (the `audit` intro)

- [ ] **Step 1: Confirm the red lines**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && grep -nwE 'Small|Medium|Large|size not set|sizes its work' plugins/my/skills/roadmap-management/SKILL.md plugins/my/skills/handoff/SKILL.md plugins/my/skills/handoff/README.md plugins/my/skills/design-system/SKILL.md; grep -n 'kind, place and size' plugins/my/skills/roadmap-management/SKILL.md
```

Expected: 11 lines from the first command, 2 from the second.

- [ ] **Step 2: Edit `roadmap-management`**

Rule 11's first bullet becomes, word for word:

```markdown
- **Kind, place and route** — the kind of work (`bug`, `feature`, `rule` for a change to instruction text, or another kind the roadmap already uses), where it happens (the skill, file or area), and the route when it is already known. In a project that routes its work (spike, bounded, architectural in the `my` method): a row of kind `bug` names no route, even when its fix may touch the risk line; a row that hits the risk line (a change to stored data or its shape, permissions, a message or public contract, or something hard to reverse) names `architectural with plan`; every other row names `route not set` until brainstorming picks its route (rules 4 and 6). A bug that brainstorming routed follows rules 4 and 6 for the route it got. In a project that does not route its work, leave the route out. Examples: `bug in my:handoff.` and `feature in my:status, route not set.`
```

The two lines that repeat the order: "kind, place and size" becomes "kind,
place and route".

Rule 4, a new bullet after the link bullet: "In a project that routes its
work, replace `route not set` with the route brainstorming picked (rule 11)."

Rule 6, a new bullet after the status bullet: "In a project that routes its
work, a row that still says `route not set` gets its route here: a bounded
change has no spec, so no 📋 edit set it (rule 11)."

- [ ] **Step 3: Edit `handoff`**

The three `SKILL.md` labels and the six `README.md` lines, as in the spec's
Design, "`my:handoff`". The README lines that say "for a Medium change" about
the **Risk** section become "or of the spec when there is no plan". The line
that says "(a Medium change)" becomes "(an architectural change)".

- [ ] **Step 4: Edit `design-system`**

"before the first UI spec of a Medium or Large change in a project with no
inventory" becomes "before the first UI spec of an architectural change, with
or without a plan, in a project with no inventory". The words "sizes" in
`audit` step 2 and "size values" in step 3 are about UI components and stay.

- [ ] **Step 5: Check, lint and commit**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && ! grep -nwE 'Small|Medium|Large|size not set|sizes its work' plugins/my/skills/roadmap-management/SKILL.md plugins/my/skills/handoff/SKILL.md plugins/my/skills/handoff/README.md plugins/my/skills/design-system/SKILL.md && ! grep -n 'kind, place and size' plugins/my/skills/roadmap-management/SKILL.md
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes/plugins/my && python3 -m unittest discover tests && cd ../.. && markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc plugins/my/skills/roadmap-management/SKILL.md plugins/my/skills/handoff/SKILL.md plugins/my/skills/handoff/README.md plugins/my/skills/design-system/SKILL.md && git add plugins/my/skills/roadmap-management/SKILL.md plugins/my/skills/handoff/SKILL.md plugins/my/skills/handoff/README.md plugins/my/skills/design-system/SKILL.md && git diff --cached
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && git commit --trailer "Task: 3" -m "feat(my-plugin): the skills name routes, not sizes"
```

Expected: both `grep` checks exit 0, the tests print `OK`, no new lint error.

### Task 4: The `my` README

**Files:**

- Modify: `plugins/my/README.md`

- [ ] **Step 1: Edit the README**

Every point of the spec's Design, "`plugins/my/README.md`", plus three it
leaves implicit:

- Line 7 and "Where the parts live": "size" becomes "route".
- "What superpowers gives": "**It sizes the work.**" becomes "**It picks a
  path for the work.**" The rest of that bullet describes superpowers alone,
  and stays.
- "The size table" becomes "### The routes": one sentence that the session
  states the route in one line; the route table from `my.md` without the
  "Commits on `main`" column; "The full table, with the commits for each
  route, is in `global/methods/my.md`."; the mapping, word for word: "The old
  names map as follows: Small is bounded or bug, Medium is architectural,
  Large is architectural with plan."; and "Specs, plans and reviews finished
  before row 67 still use the old names."
- Delete the paragraph that starts "The size table and brainstorming's three
  paths overlap" and ends "plus a few `my` adaptations.". Row 67 settles
  what it describes, so it is untrue after the merge.
- "Worktrees, squash-merge and four commits on `main`": "An architectural
  change with a plan leaves four commits on `main`: the spec with its review,
  the plan with its review, the code, and the `done` mark. An architectural
  change without a plan leaves three, a bounded change or a bug fix one, and
  a spike one `docs:` commit, its file."
- The `brainstorming` and `writing-plans` rows, as the spec words them. Keep
  the rest of the `brainstorming` cell (`docs/plans/`, `my:architect` first,
  the Design artifact) and drop its last sentence, "Its spike and bounded
  paths are not mapped to a size (row 67)."
- "Limits", first point: "**A route only moves up.** Bounded skips the spec
  and the plan. Architectural skips the separate plan. If the work turns out
  heavier than its route, the session stops and says so." Second point: the
  three sentences from "Superpowers' brainstorming has a spike path" to the
  end of the point become "The spike route covers that case: it writes an
  answer, not code that lands."

- [ ] **Step 2: Check, lint and commit**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && grep -nwE 'Small|Medium|Large' plugins/my/README.md; grep -n -i -E 'size table|the size|sizes the' plugins/my/README.md
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc plugins/my/README.md && git add plugins/my/README.md && git diff --cached
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && git commit --trailer "Task: 4" -m "docs(my-plugin): the README describes the routes"
```

Expected: the first `grep` prints only the mapping sentence (one or two
lines, as it wraps); the second prints
nothing; no new lint error.

### Task 5: The roadmap, zitamu's local file, and the final checks

**Files:**

- Modify: `ROADMAP.md` (the open rows that name a size, three steps of
  "Order of work")
- Modify: `projects/real-estate-webapp/claude-local.md` (three sentences)

- [ ] **Step 1: List the open rows that name a size**

Run this from the worktree. It prints each open row (💭, 📋, 🚧) whose text
names a size:

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && python3 - <<'EOF'
import re
row = icon = None
for n, line in enumerate(open("ROADMAP.md", encoding="utf-8"), 1):
    m = re.match(r"- (\S+) (\d+[a-z]?) \*\*", line)
    if m:
        icon, row = m.groups()
    elif not line.startswith(" "):
        row = None
    if row and icon != "✅" and re.search(r"\b(Small|Medium|Large)\b|size\s*$|size not set", line):
        print(row, n, line.rstrip())
EOF
```

Expected on 2026-10-18: rows 8, 20, 33, 35, 37, 40, 44, 45, 46, 51, 53, 54,
56, 60, 61, 62, 67, 68, 69 and 70, and rows 71 and 72 if their commits have
landed on `main` by then. Row 56's `size not set` spans two lines, and row 53's "needs
a size" ends a line.

- [ ] **Step 2: Apply D10, and D9 to the rows D10 does not list**

Apply the spec's D10 table to each row it names. Then apply D9's three rules
to every other row the list printed:

- **Row 67** is already 📋 with its spec link, but still says `Large`. Its
  spec's Size line says "architectural with plan", and it changes a contract
  (D2). So `Large` becomes `architectural with plan`.
- **Row 70** (`Choose the design skill`) and **row 72** (`Workflow metrics as
  one my script`) say `size not set`. Neither is a bug, and neither hits the
  risk line. So each becomes `route not set`.
- **A row that links its own spec** already has a route, because
  brainstorming ran to write the spec. D9 writes it in the 📋 edit, and D4
  maps the old names: `Medium` becomes `architectural`, `Large` becomes
  `architectural with plan`. Row 71 ("Project rules outrank the core"), if
  it has landed on `main`, reads "Medium; spec drafted": it becomes
  "Architectural; spec drafted".
- Any other row: a bug drops its size; a row that hits the risk line names
  `architectural with plan`; every other row names `route not set`.

Also the three "Order of work" steps in D10. In step 4, use row 54's new
title. Leave step 1's sentence "It changes how every row is sized" as it is:
it describes row 67 itself, and row 67's `done` mark edits that step.

- [ ] **Step 3: Check the roadmap**

Run step 1's script again. Expected: no output. Then check "Order of work":

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && sed -n '/^## Order of work/,/^## [^O]/p' ROADMAP.md | grep -nwE 'Small|Medium|Large|sizing'
```

Expected: no output. Then read each row that step 1 listed, and confirm its
new words: rows 8, 20, 35, 44, 45, 46, 51, 61, 62 and 70 name `route not
set`; rows 67, 68 and 69 name `architectural with plan`; rows 33, 37, 56 and
60 name no route; rows 40, 53 and 54 read as D10 says; row 71, if present,
names `architectural`.

- [ ] **Step 4: Edit zitamu's local file**

The three sentences in the spec's Design, "zitamu's local file", word for
word. Find them by text, not by line:
`is Large` / `under the global size rules`, `Small ones`, and
`A Small change records`.

- [ ] **Step 5: Run the final checks**

Testing 1, the size-word check:

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && grep -rnwE 'Small|Medium|Large' global/methods/my.md global/rules/docs-layout.md plugins/my/skills plugins/my/README.md projects/real-estate-webapp/claude-local.md
```

Expected: exactly these lines, and no other:

- `plugins/my/README.md`: the mapping sentence from Task 4, on one or two
  lines;
- `plugins/my/skills/spec-review/spec-reviewer-prompt.md`: the four lines
  with the confidence labels `High`, `Medium`, `Low`;
- `plugins/my/skills/soundness-review/code-reviewer-prompt.md`: the four
  lines with the same labels.

Then:

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && grep -rn -i -E 'size table|size the process|size not set|sizes its work|by size|pick a size' global/methods/my.md global/rules/docs-layout.md plugins/my/skills plugins/my/README.md plugins/kit/tests/test_neutral_core.py
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes/plugins/kit && python3 -m unittest discover tests && cd ../my && python3 -m unittest discover tests
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc global/methods/my.md global/rules/docs-layout.md plugins/my/skills/roadmap-management/SKILL.md plugins/my/skills/handoff/SKILL.md plugins/my/skills/handoff/README.md plugins/my/skills/design-system/SKILL.md plugins/my/README.md projects/real-estate-webapp/claude-local.md ROADMAP.md
```

Expected: the `grep` prints nothing; both test suites print `OK`; the lint
shows no error that `main` does not already have for the same files.

- [ ] **Step 6: Commit**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && git add ROADMAP.md projects/real-estate-webapp/claude-local.md && git diff --cached
cd /home/dchris/projects/claude-setup/.claude/worktrees/brainstorming-routes && git commit --trailer "Task: 5" -m "docs: the roadmap and zitamu's local file name routes"
```

## After the merge

This section is not a task. Its commit lands in another repo, so no `Task:`
trailer reaches this branch, and a restarted code stage must not redo it.

**Owner: the user,** or a session the user starts in zitamu
(`~/projects/zitamu/real-estate-webapp`), after the squash-merge. The
review stage's `done` mark on the spec and on this plan adds: "zitamu's
roadmap edit (D10) is pending; see the plan's After the merge section."

First run `git -C ~/projects/zitamu/real-estate-webapp status --porcelain -- ROADMAP.md`.
If it prints anything, someone else has edits there: wait for them.

Then make one `docs:` commit in zitamu that applies D9 to its open table rows.
On 2026-10-18 there were 13, worked out here so the edit needs no new
decisions. A sentence that names a size changes as follows:

| Row | Today | After |
| --- | --- | --- |
| 17, 18, 49, 55, 59, 122, 124 | `Large` (each changes stored data, permissions or a contract) | `architectural with plan` |
| 97 | `Large, because it changes infra/, CI and the deploy` | `Route not set; it changes infra/, CI and the deploy`. The build is not on the risk line (spec, Risk), so D9 gives it no route yet. |
| 149 | `Medium: a canvas, then a spec.` | `Architectural: a canvas, then a spec.` It is 📋, so brainstorming has picked its route. |
| 93 | `Two Small fixes on one branch.` | `Two bug fixes on one branch.` |
| 46 | title `Seed data fixes, one Small branch` | `Seed data fixes, one branch`. A bug row names no route. |
| 113, 153 | `Small.` | the size is dropped: both rows describe faults, so they are bugs. |

In its Order of work, the two live steps for rows 49, 55 and 59 ("Large, and
it changes the request page", "each Large, because each changes stored
data") take `architectural with plan`. The "Done:" items, and "one Medium
regression" in row 74b, stay: the first are records, and the second is a
review's confidence label, not a size.

If zitamu's roadmap has changed by then, apply the same three rules of D9 to
the rows as they are.

## Trade-Offs / Alternatives Considered

- **When the route line is said.** D1 says brainstorming says the route
  before its first question. But the trigger table runs `my:architect`
  before brainstorming for a change to a data model, and the spec's
  rehearsal expects `architectural with plan` as the first step of the
  `deleted_at` prompt. **Chosen:** the spec's words only, and the rehearsal
  shows whether they are enough. **Rejected:** a sentence that a task on the
  risk line states its route before any skill runs. The plan review found it
  is a rule the approved spec does not have, so only the user can add it.
  Also rejected: "state the route before any skill runs" for every task,
  which would also settle when the design-system audit runs, a limit the
  spec leaves to row 70.
- **The rehearsal fixture has a `docs/DESIGN-SYSTEM.md`.** Without it, the
  rename prompt runs the audit first, whose timing is a known limit. The
  alternative, a non-UI rename prompt, would change the spec's prompt.
- **One task for `my.md`, its test and the rehearsal.** The rehearsal files
  live in the scratchpad and are not committed, so a separate rehearsal task
  would have no commit and no `Task:` trailer, and a restarted code stage
  would count it as not done.
- **The zitamu commit is a section, not a task,** for the same reason.

## Dependencies

- The user's edits to `projects/real-estate-webapp/claude-local.md` are
  committed first. Task 1, step 1 checks it against the main checkout.
- Row 69 comes after this row and inherits rule 11's neutral wording.
- No new packages.

## Risk

- **Blast radius: every project that imports `my.md`.** The nine projects
  the spec names get the new rules at the merge, through the symlink in
  `~/.claude/methods/`. A session that is already open finishes under the
  old rules. `my:handoff` routes by the Tasks section, not by a size word, so
  specs in flight still run.
- **The rehearsal costs 31 headless runs** (one probe and 15 runs, twice).
  A run's answer varies; three passes per prompt guard against one lucky
  pass, but a flaky prompt can still fail one of three. That is a stop
  (Delegation: no failing tests allowed).
- **The rehearsal may not load the rules by the absolute import.** Task 1,
  step 6's probe detects it, and the fallback copies the file into the
  fixture.
- **The `deleted_at` rehearsal may fail on the route line's timing.** The
  trigger table runs `my:architect` before brainstorming for a change to a
  data model, and D1 places the route line in brainstorming. If the session
  runs `my:architect` before it states a route, the run fails. The plan adds
  no rule to prevent it (Trade-Offs, first point), because that would be a
  rule the approved spec does not have. Then the code stage stops, and the
  user decides whether the rule text needs a timing sentence.
- **Row 71's draft spec also edits a Precedence paragraph.** Row 71
  ("Project rules outrank the core") was another session's uncommitted
  draft on 2026-10-18. D12 adds a sentence to `my.md`'s Precedence
  paragraph. Whichever lands second must keep the other's sentence.
- **`ROADMAP.md` will conflict at the merge** if other sessions edit the same
  rows on `main`. On a conflict, apply Task 5, step 2 again to the rows as
  they are on `main`. On 2026-10-18 another session already had uncommitted
  edits in `ROADMAP.md` on `main`, and row 72 was new.
- **zitamu's roadmap edit waits for the user** (After the merge). Until it
  lands, zitamu's open rows say Small, Medium or Large under rules that no
  longer use them.
- **Found, not fixed:** `METHOD_HEADINGS` in `test_neutral_core.py` lists
  `"Learning workspaces"`, which no method file has. The test still passes,
  because it only checks that the core lacks each heading.
- **Known limits the spec carries:** a change to the build in one or two
  files is bounded; the two-file limit is rough; a route moves up only if
  the session notices; a bounded UI change skips the UI checks; the
  design-system audit's timing waits for row 70. A known limit is not a
  finding.
- **Not hard to reverse.** Every edit is text, and the squash commit can be
  reverted.

## Testing Strategy

1. **No size words in the live rules:** Task 1, step 2 records the red
   lines; Task 5, step 5 checks that only the listed lines remain.
2. **The rehearsal:** Task 1, steps 3 to 6 (red: the 12 runs of the four non-bug prompts fail) and step 12
   (green, 15 passing, three per prompt). The bug escalation (D6) is checked
   by reading, in Task 1, step 9.
3. **Unit tests:** both suites, after each task that touches code or skill
   text, and once more in Task 5, step 5. Task 2 adds
   `test_answered_spike_is_not_open`, proven able to fail by a deliberate
   break.
4. **Markdown lint** on every edited `.md` file, with the user's config.

## Open Questions

None.
