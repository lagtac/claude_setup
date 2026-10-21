# Spec: project rules outrank the core

**Status:** draft, 2026-10-18. Row 71; the precedence order of the rule files, and two protected safety rules.

**Size:** Medium. Two rule files and one test file change, about 30 lines, and no stored data. It
changes a rule that every project follows, so the user may make it Large.

## How to read this spec

1. `global/CLAUDE.md`, the "Precedence" paragraph (line 3) and the **Important:** list under it.
   The text this spec replaces.
2. `global/methods/my.md`, the "Precedence" paragraph (line 69). Its first sentence changes.
3. `global/methods/tutor.md`, line 7. It names core rules as exceptions, the mechanism this spec
   keeps.
4. `plugins/kit/tests/test_neutral_core.py`. The core's guard tests; this spec adds one.
5. `docs/plans/2026-10-18-brainstorming-routes-spec.md`, D12. Row 67 adds one sentence to the same
   paragraph of `my.md`.
6. `docs/plans/2026-10-18-launch-method-switch-architecture.md`, the paragraph after the component
   table ("Text that tells which method is in force"). Row 68 rewrites the core's Precedence line
   so it keys on the method file's heading. This spec uses that wording now.
7. `projects/zitamu/real-estate-webapp/CLAUDE.local.md`, lines 24 and 113. A project rule that
   already conflicts with a global rule (D4).

## Context

The core `global/CLAUDE.md` says that it and the method file are "the highest authority". It says
nothing about a project's own `CLAUDE.md` or `CLAUDE.local.md`. So when a project rule conflicts
with a core rule, the outcome is not written down.

The user's aim: the core outranks every skill, but not the project's own rules. A project file is
written for that one project, so it knows things the core cannot.

**Evidence of a conflict today.** `global/rules/js-ts.md` says to install with `pnpm install`.
zitamu's `CLAUDE.local.md` says to run every npm command in the web container (line 113). The
project is right for zitamu, and nothing in the core says that it wins.

**Evidence from a session outside a project.** On 2026-10-18, a drawing session in
`~/src/play/thinker` (the anidoodle plugin) had no project file. The core's dependency rule made
the session ask before `npm install`, which helped. `js-ts.md` loaded for the project's `.ts`
files and said pnpm, while the plugin's own commands use npm. The session used npm and did not
mention the conflict.

**The risk of the change.** A project file is not always the user's own. A cloned repository can
carry a `CLAUDE.md`. If every project rule beats the core, a stranger's file could turn off the
rule that asks before adding dependencies.

## Goal

- One written order between the user's request, the project files, the method file, the core and
  skills.
- A project rule beats a core rule. The override is visible to the user.
- A short list of safety rules that no file can turn off.
- Skills still lose to every file, so the `my.md` overrides of superpowers stay in force.

## Out of scope

- Scoping "Engineering standards" to software projects. A separate row, if the user wants it.
- `js-ts.md` picking npm when a project has a `package-lock.json`. A separate row, if the user
  wants it. With this spec, a project file can already say so.
- How a session loads its method file. That is row 68.
- What superpowers may override inside `my.md`. The list after the first sentence of `my.md:69`
  does not change.
- Finished specs and reviews that quote today's Precedence wording, such as
  `docs/plans/2026-10-12-swappable-methods-spec.md:115`. They are records.

## Decisions

**D1. The order, highest first:**

1. The protected rules (D3).
2. The user's request in the session.
3. The project's `CLAUDE.md` and `CLAUDE.local.md`.
4. The method file in force: the file headed `# Method: <name>`.
5. The core `~/.claude/CLAUDE.md` and the rule files in `~/.claude/rules/`.
6. Skills, plan mode and system defaults.

**D2. The user's request ranks above the files.** A literal model that reads "the highest
authority" may refuse what the user asks in the session. The protected rules stay above the
request, but they only ask for the user's approval, so the user can always give it.

**D3. Two protected rules.**

- Never add new dependencies without approval. It moves here from the **Important:** list, so it
  is written once.
- Ask before an action that is hard to undo or that leaves this machine: deleting files or
  branches, rewriting pushed history, pushing, publishing, or sending a message. A project may
  make it stricter, never looser.

The second rule is new text in the core. Today it comes only from Claude Code's system prompt, so
a project file could argue against it. `my` already never pushes (`docs-layout.md` step 14, and
`block-autorun-push.py` in auto runs), so it changes nothing there.

**D4. An override names the rule it replaces, with one fallback for project files.** A method file
overrides the core only by naming the rule, as today; row 16 chose this, and `tutor.md` relies on
it. A project file should also name the rule. When a project file conflicts with a lower file and
does not name the rule, the session follows the project file and says in one line which rule it
set aside. A strict "only by naming" for project files would break zitamu's npm rule (Context) on
the day of the merge, and that rule is right. The one line makes each unnamed override visible, so
the user can add the name or remove the rule.

**D5. The method file stays below the project and above the core.** The project chose its method,
so the method is a project choice. A project can then make one exception to `my.md` without
editing the shared file. `tutor.md` keeps naming core rules as exceptions, as today.

**D6. The method file is named by its heading, not by "the project imports".** Row 68 will load
the method by a flag as well as by an import line. Its brief already asks the Precedence line to
key on `# Method: <name>`. Writing it that way now means row 68 does not reword it again.

## Choices made without the user

The user approved a draft in chat on 2026-10-18. These points differ from it or were not in it:

- **D2, the user's request as rank 2.** The chat draft had no rank for the user.
- **D4, the fallback for project files.** The chat draft said an override names the rule, with no
  fallback. The fallback keeps zitamu's npm rule working. Method files keep named-only overrides.
- **D6, naming the method file by its heading.** Taken from row 68's approved brief.
- **"Engineering standards" scoping and the `js-ts.md` npm change are out of scope.** Both were
  proposed in the same chat. The user asked for a spec of the precedence draft only.

## Design

### `global/CLAUDE.md`

The Precedence paragraph (line 3) becomes:

```markdown
**Precedence:** rules come from these sources, highest first:

1. The protected rules below. No file overrides them.
2. The user's request in the session.
3. The project's `CLAUDE.md` and `CLAUDE.local.md`.
4. The method file in force, headed `# Method: <name>`.
5. This file and the rule files in `~/.claude/rules/`.
6. Skills, plan mode and system defaults.

When a skill, plan mode or a system default conflicts with a file in 3 to 5, follow the file.
A higher file overrides a rule of a lower file by naming that rule. A project file that conflicts
without naming the rule still wins: follow it, and say in one line which rule you set aside. A
method file overrides this file only by naming the rule. Any file may add rules.

**Protected rules:**

- Never add new dependencies without approval.
- Ask before an action that is hard to undo or that leaves this machine: deleting files or
  branches, rewriting pushed history, pushing, publishing, or sending a message. A project may
  make this stricter, never looser.
```

In the **Important:** list, the line "Never add new dependencies without approval" is removed.

### `global/methods/my.md`

The first sentence of the Precedence paragraph (line 69), "these rules and the core in
`~/.claude/CLAUDE.md` are the highest authority — when plan mode, a skill, or any system default
conflicts, follow them.", becomes:

```markdown
**Precedence:** these rules and the core in `~/.claude/CLAUDE.md` outrank any skill, plan mode and
system default. The order between files is in the core's Precedence paragraph.
```

The rest of the paragraph does not change. Row 67's D12 sentence goes after it, whichever row
merges first.

### `plugins/kit/tests/test_neutral_core.py`

One new test, `test_core_protects_safety_rules`. It finds the line `**Protected rules:**` in the
core, and checks that both protected rules follow it before the next blank-line-separated
paragraph or heading. It also checks that "Never add new dependencies without approval" appears in
the core exactly once. The existing test `test_core_names_no_method` already keeps `my:` and
`docs/plans` out of the new text.

## Files

| File | Change |
| --- | --- |
| `global/CLAUDE.md` | The Precedence paragraph and the protected rules; one line out of **Important:** |
| `global/methods/my.md` | The first sentence of the Precedence paragraph |
| `plugins/kit/tests/test_neutral_core.py` | One test |
| `ROADMAP.md` | Row 71, added with this spec; its `done` mark after the merge |

No script reads the Precedence text. `method-guard.py` checks the import line, not this paragraph.

## Tasks

Run in a worktree of `claude-setup`. Commit type `docs`, scope `global`, for the squash commit.

### Task 1: the test (Red)

File: `plugins/kit/tests/test_neutral_core.py`.

```python
def test_core_protects_safety_rules(self):
    core = CORE.read_text()
    block = protected_block(core)   # the text after "**Protected rules:**" up to the next heading
    self.assertIn("Never add new dependencies without approval.", block)
    self.assertIn("Ask before an action that is hard to undo", block)
    self.assertEqual(core.count("Never add new dependencies without approval"), 1)
```

`protected_block(text) -> str` is a helper beside `headings()`. Run
`cd plugins/kit && python3 -m unittest discover tests`. The new test fails, because the core has no
`**Protected rules:**` line yet.

### Task 2: the core (Green)

File: `global/CLAUDE.md`. Replace the Precedence paragraph with the text in "Design", and remove
the dependency line from **Important:**. Run the kit tests: all pass.

### Task 3: `my.md`

File: `global/methods/my.md`. Replace the first sentence of the Precedence paragraph with the text
in "Design". If row 67 merged first, keep its D12 sentence after the new one. Run both test
commands.

### Task 4: lint

Run `markdownlint-cli2 --config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc
global/CLAUDE.md global/methods/my.md`. Fix only what the change introduced.

## Trade-offs

- **Option A, this spec: the project outranks the core, with protected rules and a one-line
  notice.**
  - Pros: the more specific file wins, as the user asked. Overrides are visible. A cloned repo
    cannot turn off the two safety rules.
  - Cons: a stranger's project file can still override every other core rule, such as Conventional
    Commits or the exploration rules. The notice adds a line to sessions that hit a conflict.
- **Option B: overrides only by naming the rule, with no fallback.**
  - Pros: every override is deliberate.
  - Cons: zitamu's npm rule and any other unnamed project rule stop working at the merge. Each
    project file needs an edit first.
- **Option C: keep the core on top, and let projects name exceptions, as method files do today.**
  - Pros: the smallest change.
  - Cons: it goes against the user's aim. A project rule loses by default.
- **Recommendation: A.**

## Dependencies

- **Row 67 edits the same paragraph of `my.md`** (its D12). The two edits touch different
  sentences. Task 3 says how to keep both.
- **Row 68 rewrites the core's Precedence line.** This spec writes it in the form row 68's brief
  asks for (D6). If this row merges before row 68, row 68's spec only checks the line. If it
  merges after, this row takes row 68's wording instead.
- No new packages.

## Risk

- **Blast radius: every session on this machine.** The core is symlinked as
  `~/.claude/CLAUDE.md`, so the new order applies in every project at the merge, with or without a
  method. A session open at the merge finishes under the old text.
- **Project rules that lost before now win.** A project rule that conflicts with the core used to
  lose, or the outcome was unclear. A keyword scan on 2026-10-18 of the 11 project files that
  import a method found one conflict: zitamu's npm rule (Context). It is the intended result. The
  scan searched for words such as "override", "precedence", "npm" and "push", so it can miss a
  conflict worded another way.
- **A cloned repo can override most of the core.** Only the two protected rules are safe from it.
  This is the price of D1. A third protected rule can be added later.
- **The model may not give the one-line notice.** No check enforces D4. A missed notice hides an
  override, but the project rule is still followed, as the user intends.
- **"Pushing" now always asks.** Two projects end their merge step with "then push":
  `grispy-ext/CLAUDE.md:160` and `grispy-site/CLAUDE.md:68`. There, each merge gets one more
  question before the push. `grispy-site` already says a push "puts the change on the live public
  web", so the question fits it. Under D4, a project that wants no question must name the rule,
  and the protected rule cannot be loosened, so it gets the question anyway.
- **Reversal:** revert the squash commit. No data changes.

## Testing strategy

- The new unit test (Task 1) guards the protected rules against a later edit, such as row 68's.
- The existing neutral-core tests keep method names out of the new text.
- Manual: in a new session in zitamu, ask which package manager to use. The answer follows the
  project file and names the `js-ts.md` rule it sets aside.

## Open questions

- Does the user want the second protected rule to include "pushing"? D3 says yes. It adds one
  question per merge in the two grispy projects (Risk).
- Should "Engineering standards" scoping and the `js-ts.md` npm change become rows of their own?
- Where does row 71 go in "Order of work"? The roadmap says rows after row 67 are specced under its
  new rules, and row 68 edits the same line (Dependencies).
- May this spec run in auto mode (`/my:handoff auto`)? On yes, it gets a Delegation section.
