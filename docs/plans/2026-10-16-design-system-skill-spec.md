# Spec: `my:design-system`, a design-system inventory that every UI spec reads

**Status:** done, 2026-10-16. Shipped in `eae9264`; row 64; plan: `docs/plans/2026-10-16-design-system-skill.md`, whose status line gives the checks.

**Size:** Large. It changes rules that every project on the `my` method follows, and it adds a
skill. `my:architect` was skipped by the user's choice: the change has no load, storage or data
forces, and `my:spec-review` and `my:status` shipped as Large without a brief.

## How to read this spec

1. `global/methods/my.md`, sections "Spec → Plan two-artifact flow" (step 1, the Visual Language
   rule with row 59's sentence) and "UI Design". The rules this spec changes.
2. `plugins/my/skills/spec-review/spec-reviewer-prompt.md`, criterion 6. Row 59 added its last
   bullet; this spec adds one more.
3. `global/rules/docs-layout.md`, sections "One feature, four commits on `main`" (step 13), "From
   report to roadmap" and "Status line". Where the refresh runs, and how an audit's findings
   become rows.
4. `plugins/my/skills/handoff/SKILL.md`, Review stage step 8 (sub-step 4, the `done` marks), Plan
   stage step 6 (the shared-doc check, line 720) and stop row 19 (line 250). The shared-doc list
   this spec extends.
5. `plugins/my/bin/status-scan.py` and `plugins/my/tests/test_status_scan.py`. The script and
   test style that `ds-count.py` and its test copy.
6. The zitamu evidence, in `~/projects/zitamu/real-estate-webapp/`:
   `docs/plans/2026-10-15-agent-request-list-page-spec.md` §5 (row 74b's Visual Language table),
   `docs/reports/2026-09-18-design-system-audit.md` (the first audit, its "Missing primitives"
   table and its withdrawn count) and `docs/reports/2026-10-16-component-extraction-audit.md`
   (row 130, the extraction that this spec should make rare).
7. The zitamu Design System artifact, <https://claude.ai/artifact/8vKHqdSLDqZtiGSvz8vmB8>, made in
   the spike (D8). Its README shows what `sync` writes.
8. `ROADMAP.md`, row 59 in "Design workflow", and `CHANGELOG.md`, entry "2026-10-15 — A spec
   names the shared parts of its UI (row 59)".

## Context

On zitamu, frontend work wrote markup inside pages, or reused existing components such as
`ZButton`. It rarely grew the set of shared components. Zitamu now extracts them afterwards:
row 130's audit routed six extractions to rows 133 to 138.

The method did not ignore the design system. Zitamu has a tokens file
(`web/assets/css/tokens.css`), 23 `Z*` components and two audits, and its specs map every drawn
element to tokens with care. Four gaps let page-local markup through:

1. **No rule for a missing component.** Row 74b's Visual Language table says "scoped to the page
   as `pages/match.vue` does (no shared field component exists)". Neither the method nor
   `my:spec-review` said what should happen then. Row 59 (`7e938b9`) closed most of this gap: an
   element with two or more users now becomes a shared component.
2. **The canvas is not drawn from the system.** 74b's canvas "uses raw colours and Inter", and
   the boards are mapped to tokens only afterwards. A board made of raw shapes cannot show which
   parts exist and which are new.
3. **No standing inventory.** The 2026-09-18 audit was a one-off report. No document lists the
   components and the patterns pages still build by hand, so a spec has nothing to consult, and
   `my:spec-review` has nothing to check a spec against.
4. **No start for a new app.** Nothing sets up tokens and base components before the first page.
   Zitamu's first audit found it had no field, no inline message and no page shell, and 39 raw
   `<input>` elements.

## Goal

- Every project with UI keeps one inventory, `docs/DESIGN-SYSTEM.md`, that specs read and
  reviews check.
- A skill builds and refreshes the inventory, advises what to build or extract, and routes each
  proposal to a roadmap row.
- A canvas is drawn with the project's exact tokens, and labels each part with its component
  name or «new: `<name>`».
- A new app gets its tokens and base components as one row before its first page row.

## Out of scope

- Zitamu's own rework. Rows 130 to 138 stay in zitamu, and this branch edits no zitamu file.
- Live component previews in the Design System artifact (D8).
- A general converter from CSS variables to the artifact's `tokens.json` (D9).
- Any check at the end of a branch. The spec review catches the gap before code is written.

## Decisions

- **D1. The inventory lives in the repo, at a fixed path.** `docs/DESIGN-SYSTEM.md`. Specs and
  the reviewer subagent read it with plain file tools; the reviewer has only Bash, and `cat` is
  enough. It is versioned with the code. A fixed path needs no new line in "Project facts", so
  `kit:setup` and every project's `CLAUDE.md` stay as they are. Zitamu forbids edits to its
  `CLAUDE.md`, so that matters. (The user chose the repo file over an artifact-only record.)
- **D2. A Design System artifact is made from the code.** The canvas builds on it. `sync` writes
  it; the inventory's Sources part holds its link and the commit it was synced from. The Artifact
  tool's contract for the Design type says a visual design first lists the design systems the
  user can open and uses the one named, before choosing any typeface or palette. So naming the
  project's system is enough; no token is copied into a board by hand.
- **D3. The skill advises and routes; it writes no component code.** Each component to build or
  extract becomes a roadmap row with its own spec and tests. (The user chose this over
  scaffolding code directly, which would skip the spec, the tests-first rule and the reviews.)
- **D4. Counts come from a script, from search expressions stored in the inventory.** A model
  that recounts each time phrases the search differently. Zitamu's first audit withdrew a
  spacing count for exactly that reason ("used a looser pattern and is withdrawn"). The numbers
  live in one place only, the `ds-patterns` block.
- **D5. The inventory is refreshed at step 13 of a row whose spec has a Visual Language section,
  or whose squash commit touches the tokens file or the components folder.** The method requires
  that section exactly when a spec adds or changes UI. The second test catches a pure extraction,
  which may change no UI. `refresh` also adds any component in the Sources folder that the
  inventory lacks, so a component added by a Small change, which has no spec and no step 13, is
  listed at the next run. Step 13 runs `refresh` only when `docs/DESIGN-SYSTEM.md` exists:
  rows already in flight in a project with no inventory skip it, so an auto run does not stop
  at its last step. The skill can also run by hand at any time.
- **D6. Row 59's rule holds for every new spec.** An element with two or more users becomes a
  shared component. So `refresh` adds no `hand-built` lines; it adds only a `component` line for
  a new component. Part 3 deliberately leaves out a part with one user: it is not a pattern yet,
  and when a second page needs it, row 59's search catches it in that page's spec. New
  `hand-built` lines come only from `audit`, which finds copies made before the rule existed.
  For those, "kept in the page" stays a destination, with the user's reason, because it is a
  choice about existing code. `refresh` retires a `hand-built` pattern whose count reaches 0: it
  removes the line and its part 3 row.
- **D7. The audit trigger skips Small changes, and comes after `my:architect`.** It runs before
  the first UI spec. A Small change has no spec, so a colour fix never triggers a full audit. In
  a new project, `my:architect` runs first, because it decides the system the UI sits in; then
  `audit`; then brainstorming.
- **D8. The artifact holds exact tokens and named components, not component previews.** The spike
  (2026-10-16) read the type's `from-code.md`. Tokens convert exactly, in both themes. Live
  components exist only for React: the "Built" route bundles a React library into one plain
  script that reads `window.React`. Zitamu's components are Vue single-file components, so they
  could only be hand-written static copies, which drift, or a new Vite build target in every
  project. The user chose exact tokens and named components: boards label each part with its
  name from the inventory, such as «ZButton ghost sm», or «new: `<name>`».
- **D9. `sync` is the model's work, following the type's guide.** Each project names its CSS
  variables in its own way. The spike used a throwaway converter written for zitamu. A general
  one would need a case for every naming scheme. Each artifact's README lists what was not
  synced, so a gap is visible.
- **D10. An auto run skips `sync`.** Publishing to claude.ai is an outward-facing action, and the
  core rules require confirmation for those unless authorized. The Sources line keeps its old
  commit, and the staleness command (D11) shows it to the next session the user runs.
- **D11. The artifact is stale when its sources changed.** The test is one command over the paths
  in Sources: `git log --oneline <synced commit>..HEAD -- <tokens file> <components folder>`. Any
  output means: run `sync` before drawing. It needs no record of which rows were UI rows. When
  Sources says `none yet` for the artifact, there is no commit to test from: run `sync` before
  drawing. When it says `none yet` for the tokens file (a new app before its starting row), skip
  the test; that row's canvas takes its direction from `frontend-design`.
- **D12. Counts come only from tracked files, matched by git.** The script passes each pattern's
  globs to `git ls-files` as glob pathspecs, `':(glob)<glob>'`, and its excludes as
  `':(glob,exclude)<glob>'`. One call does both the tracked-only filter and the matching. An
  installed dependency folder such as `node_modules` would otherwise change the counts: in
  zitamu, `web/**/*.vue` matches 8 files under `web/node_modules`, and the hex-colour example
  matches inside two of them. Python's `PurePath.match` is not used: on Python 3.12 it treats
  `**` as `*`, so `web/**/*.vue` does not match `web/pages/requests/index.vue` (checked
  2026-10-16). With git's pathspecs, zitamu's `web/**/*.vue` matches all 64 tracked `.vue` files,
  and 41 after excluding `web/components/Z*.vue`.

## Design

### The inventory, `docs/DESIGN-SYSTEM.md`

One per project with UI. Four parts, in this order:

1. **Sources.** Three lines:
   - `**Tokens:** <path>`, or `none yet (row <N>)` for a new app before its starting row
   - `**Components:** <folder>`, with the name pattern when the folder holds other files too
     (zitamu: `web/components/Z*.vue`)
   - `**Design System artifact:** <url>, synced from <short commit>`, or `none yet`
2. **Components.** A table, one row per shared component: name, purpose, variants, sizes,
   states, tests (yes or no). Words only; the numbers are in part 4.
3. **Hand-built patterns.** A table, one row per pattern that pages still build by hand: name,
   what it looks like, and where it goes. "Where it goes" is a roadmap row, "kept in the page:
   <the user's reason>", or "no row yet". Words only.
4. **The `ds-patterns` block.** A fenced block with the language tag `ds-patterns`, one JSON
   object per line:

   ```text
   {"name": "text field", "kind": "hand-built", "globs": ["web/**/*.vue"], "exclude": ["web/components/Z*.vue"], "regex": "<input\\b", "count": 39, "files": 14}
   {"name": "ZButton", "kind": "component", "globs": ["web/**/*.vue"], "regex": "<ZButton\\b", "count": 36, "files": 13}
   ```

   JSON lines, not a Markdown table, because search expressions contain `|`.

   | Key | Required | Meaning |
   | --- | --- | --- |
   | `name` | yes | Unique in the block. Matches a row name in part 2 or 3. |
   | `kind` | yes | `component` (how many files use it) or `hand-built` (copies to replace). |
   | `globs` | yes | A non-empty list of git glob pathspecs, relative to the repo root (D12). `**/` matches any depth. Their matches add up. |
   | `exclude` | no | A list of git glob pathspecs whose files are left out, such as the component that wraps the native element, so a count can reach zero. |
   | `regex` | yes | A Python regular expression, matched over each file's whole text, so a pattern may span lines. |
   | `count`, `files` | written by `--write` | Matches in total, and files with at least one match. |

   Raw values outside the tokens file are `hand-built` patterns too, for example
   `:\s*#[0-9a-fA-F]{3,8}\b` (a hex colour after a colon) with the tokens file excluded.

Each block `name` matches a row name in part 2 or 3. The skill checks this in `audit` and
`refresh`; the script does not, so it stays a pure counter.

The skill's `SKILL.md` holds the template for this file. It is the only template.

### `plugins/my/bin/ds-count.py`

Python 3, standard library only. It sits with the other scripts in `plugins/my/bin/`, which the
plugin puts on `PATH`.

- `ds-count.py [<inventory>]` reads the `ds-patterns` block of `<inventory>` (default:
  `docs/DESIGN-SYSTEM.md` at the repo root, found with `git rev-parse --show-toplevel`). For each
  pattern it runs `git ls-files -z -- ':(glob)<glob>' … ':(glob,exclude)<exclude>' …` from the
  repo root (D12), and prints one line per pattern:
  `<name>  <kind>  <old count>/<old files> -> <new count>/<new files>`, with `new` in place of
  the old values for a line that has no count yet. It writes nothing.
- `ds-count.py --write [<inventory>]` prints the same, then rewrites the `count` and `files` of
  each line. Each line stays one JSON object with its keys in their order, written with
  `ensure_ascii=False`. Every byte outside the block stays as it was.
- A pattern whose files contain no match prints `0/0`. A component nobody uses is a real finding.
- An empty block is valid: it prints nothing and exits `0`.
- Files are read as UTF-8 with `errors="replace"`.
- It exits `1` with one message on stderr, and writes nothing, when: the block is missing; a line
  is not a JSON object; a required key is missing or of the wrong type; two lines share a name;
  a `regex` does not compile; or a pattern's globs match no tracked file at all, which is a typo,
  not an unused component. The message names the line number in the inventory.
- Otherwise it exits `0`, whether or not counts changed.

### The skill, `plugins/my/skills/design-system/SKILL.md`

Frontmatter `name: design-system`, and a description that names the three modes, the inventory
path and "NOT for writing component code". Three modes:

**`audit`** — a full review, by hand at any time, and before the first UI spec of a project with
no inventory (D7).

1. Find the tokens file and the components folder by searching the repo. Confirm them with the
   user. Write them into Sources.
2. Read each shared component and fill its row in part 2.
3. Search the pages for what they build by hand: buttons, fields, selects, messages, page
   shells, cards, list rows, toolbars, empty states, dialogs, and raw colour and size values.
   Write one `ds-patterns` line per pattern and one per component, then run
   `ds-count.py --write`.
4. Judge each finding against this checklist:
   - A pattern with two or more users becomes a shared component (row 59).
   - A variant is named by how it looks, not by a colour token it does not use (zitamu's `sky`
     variant used the primary tokens).
   - Every control has focus, disabled and loading states, and a target of at least 24px.
   - A component nobody uses is deleted.
   - A token defined but never used is deleted, after a check for tokens read from script.
5. Propose each component to build or extract as a row. The user decides which rows to add;
   `my:roadmap-management` writes them, and the user places them.
6. Check that each block `name` matches a row in part 2 or 3.
7. Run `sync`, with the user's yes, so Sources gets the artifact's link and commit. A new app
   with no tokens file skips this until its starting row ships.
8. Write the report to `docs/reports/YYYY-MM-DD-design-system-audit.md`, with the sections of
   zitamu's 2026-09-18 audit: summary, naming, token coverage, component completeness, missing
   components, priority actions, where these go. Its status line names the rows. Commit the
   report and the inventory as one `docs:` commit.

**A new app** is an `audit` that finds no shared components. The report proposes one starting row,
placed before the first page row: the token families (colour, type roles, spacing, radius, motion,
the focus ring) and a button, a field (label, input, hint, error), a select, an inline message, a
page shell and a visually hidden class. That row's canvas uses `frontend-design` for the visual
direction.

**`refresh <spec path> [auto]`** — step 13 of a row that D5 selects. Step 13 passes the row's
spec path, and `auto` when an auto run sets the `done` marks. Run by hand, the spec path is
optional.

1. Run `ds-count.py --write`.
2. Update the part 2 rows of each component the spec's row added or changed. Add a row and a
   `component` line for any component in the Sources folder that the inventory lacks (D5).
   Remove the row and the line of any component no longer in the Sources folder, so a deleted
   component is not proposed for deletion again.
3. Retire each `hand-built` pattern whose count is now 0: remove its line and its part 3 row
   (D6). Add no `hand-built` lines.
4. Check that each block `name` matches a row in part 2 or 3.
5. Run the staleness test (D11). Only when it prints something, run `sync`, and never with
   `auto` (D10).
6. Write no report. At step 13 the edits go into the step-13 `docs:` commit. Run by hand, they
   are their own `docs:` commit.

**`sync`** — the Design System artifact (D2, D8, D9).

1. With no link in Sources: create the artifact from the Design System type, titled with the
   project's name. With a link: revise it; the type's re-sync rules merge and keep the README's
   prose and anything added on the page.
2. Follow the type's `from-code.md`: exact tokens in both themes, the font files, the logos, and a
   README of usage rules that name tokens. The README's component table is generated from part 2
   of the inventory: names and purposes, no previews. Its "Not synced" list names each value the
   format cannot hold.
3. Write the link and `synced from <short HEAD>` into Sources.
4. Never in an auto run (D10). Run by hand on its own, commit the Sources edit as its own
   `docs:` commit.

### Edits to existing files

**`global/methods/my.md`**

1. A row in the task-class table: "UI work (a screen, a state or a component) in a Medium or
   Large change, in a project with no `docs/DESIGN-SYSTEM.md`" → `my:design-system audit`, then
   `superpowers:brainstorming`. When the `my:architect` row also matches, it runs first (D7).
2. Step 1 of "Spec → Plan two-artifact flow", after row 59's sentence: the spec reads
   `docs/DESIGN-SYSTEM.md` first and maps each element to a component, variant or token listed
   there. Row 59's sentence stays as it is.
3. "UI Design":
   - The `design` bullet names the Artifact tool's **Design** type. Today it says only "`design`",
     which is also the name of the `design-superpowers:design` skill.
   - New paragraph: the canvas is built on the project's Design System artifact, whose link is in
     the inventory's Sources. Boards use its tokens. Each part is labelled with its component
     name from the inventory, or «new: `<name>`». Before drawing, run the staleness command (D11);
     on any output, or when Sources says `none yet` for the artifact, run `my:design-system sync`
     first. A new app with no tokens file yet skips this, and its canvas takes its direction from
     `frontend-design`.
   - "Keep a canvas sorted by status" gains one sentence that points to step 13 for the refresh.

**`global/rules/docs-layout.md`**, step 13: when `docs/DESIGN-SYSTEM.md` exists, and the spec
has a Visual Language section or the squash commit touches the tokens file or the components
folder named in it, also run `my:design-system refresh <spec path>`, adding `auto` in an auto run, and commit its
inventory edits with the `done` marks (D5). This is the only place the call is stated, because
`my:handoff` sets the `done` marks "as the project's rules say".

**`plugins/my/skills/handoff/SKILL.md`** and **`plugins/my/skills/handoff/README.md`**:
`docs/DESIGN-SYSTEM.md` joins the shared docs, in the skill's Plan stage step 6 (line 720) and
stop row 19 (line 250), and in the README's "Shared docs" bullet (line 378). Two auto runs that
both refresh would otherwise edit it at the same time.

**`plugins/my/skills/spec-review/spec-reviewer-prompt.md`**, criterion 6, one bullet after row
59's: when `docs/DESIGN-SYSTEM.md` exists, read it.

- An element built in the page where a listed component does the job is a `Warning` and a
  `design` finding.
- An element labelled «new» that this spec builds as a shared component, or that a row the
  roadmap orders before this one builds, is not a finding: row 59 allows both, and the inventory
  lists the component only after its row merges.
- Any other element mapped to a component or variant that the inventory does not list is a
  `Warning`: `editorial` when it is a wrong name for something that exists, `design` when the
  part is new.

**`README.md`**: an entry for `my:design-system` under the `my` skills, and a sentence for
`ds-count.py` beside `status-scan.py`.

**`ROADMAP.md`**: row 64 was added under "Design workflow" with this spec; the `done` marks set
it to ✅. **`CHANGELOG.md`**: the entry, at the `done` marks.

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `cd plugins/kit && python3 -m unittest discover tests`, `cd plugins/my && python3 -m unittest discover tests`

## Files

| File | Change |
| --- | --- |
| `plugins/my/skills/design-system/SKILL.md` | New: the three modes, the checklist, the inventory template |
| `plugins/my/bin/ds-count.py` | New |
| `plugins/my/tests/test_ds_count.py` | New |
| `global/methods/my.md` | Task-class row, Visual Language sentence, UI Design paragraph and bullet |
| `global/rules/docs-layout.md` | Step 13 |
| `plugins/my/skills/handoff/SKILL.md` | Shared-doc list, two places |
| `plugins/my/skills/handoff/README.md` | Shared-doc bullet |
| `plugins/my/skills/spec-review/spec-reviewer-prompt.md` | Criterion 6, one bullet |
| `README.md` | Skill entry and script sentence |
| `ROADMAP.md`, `CHANGELOG.md` | Row 64 set to ✅, and its entry, at the `done` marks |

Edit the files under `global/`, never the links in `~/.claude/` that point to them.

## Trade-offs

- **Approach.** A, the skill with a counting script, was chosen. B, the skill alone: one new file,
  but counts drift between runs (D4). C, no new skill, with the method routing to the installed
  `design:design-system` and the type's `from-code.md`: no skill to maintain, but a new dependency
  on a third-party plugin, and no inventory file, no stored counts and no routing into rows.
- **Where the record lives.** The repo file plus a generated artifact was chosen. An artifact
  alone is not versioned with the code and cannot be read by the reviewer subagent. A repo file
  alone keeps canvases on raw values.
- **What the artifact holds.** Exact tokens and named components were chosen (D8). Static copies
  look closer to the app but drift, and a copy wrong from the start is never caught. A live Vue
  build needs a new build target in every project, and has no answer for apps without a component
  framework.
- **When to refresh.** At step 13 was chosen. By hand only lets the inventory drift between runs.
  A failing test when counts are stale is strictest, but adds a test to every project and depends
  on each stack's markup.

## Dependencies

- Row 59, committed in `7e938b9`. It edits the same two lines this spec extends.
- The Artifact tool's Design System and Design types. They are part of the platform, not
  packages.
- Python 3, standard library only. No new dependency.

## Risk

1. **Blast radius.** `global/methods/my.md` reaches every project on the `my` method. Criterion
   6 reaches every spec review. The shared-doc list reaches projects with a "Parallel runs"
   section. Every change is prompt text plus one new script, so one revert undoes it. Nothing is
   hard to reverse.
2. **Components are named, not shown (D8).** A board shows exact tokens and a label, not the
   component's real look. A wrong label flows into Visual Language, where the new criterion 6
   bullet catches a name or variant the inventory does not list.
3. **Counts are a trend, not exact (D4).** A search expression can over- or under-count. The
   numbers are stable between runs, because only tracked files count (D12), which is what
   `refresh` needs.
4. **`sync` quality depends on the model (D9).** The "Not synced" list in each artifact's README
   makes a gap visible.
5. **An auto run leaves the artifact stale (D10)** until the user's next session runs `sync`. The
   staleness command shows it before any drawing.
6. **A project mid-flight.** Zitamu's next Medium or Large UI spec triggers the first `audit`
   (D7). Row 130's report already holds most of the findings, so that audit is mostly
   transcription into the inventory.

## Testing strategy

1. **`ds-count.py`, tests first**, in `plugins/my/tests/test_ds_count.py`, on a fixture repo in a
   temporary folder, in the style of `test_status_scan.py`. Each test fails before the script
   exists.

   ```python
   def test_counts_matches_and_files(self): ...      # 3 matches in 2 files -> "3/2"
   def test_exclude_removes_files(self): ...         # the excluded file's matches leave both counts
   def test_globs_add_up(self): ...                  # *.vue and *.blade.php matches summed
   def test_double_star_matches_deep_files(self): ... # web/**/*.vue counts web/a/b/c.vue, two folders down
   def test_pattern_spans_lines(self): ...           # a regex across a newline is counted once
   def test_write_changes_only_block(self): ...      # bytes outside the block are identical
   def test_zero_match_reports_zero(self): ...       # "0/0", exit 0
   def test_missing_block_refused(self): ...         # exit 1, message names the file
   def test_bad_json_line_refused(self): ...         # exit 1, message names the line number
   def test_bad_regex_refused(self): ...             # exit 1, message names the line number
   def test_duplicate_name_refused(self): ...        # exit 1, file unchanged
   def test_untracked_files_ignored(self): ...       # a match in an untracked or ignored file is not counted
   def test_empty_block_valid(self): ...             # nothing printed, exit 0
   def test_glob_matching_no_file_refused(self): ... # exit 1, message names the line number
   ```

2. **Four runs of the skill without a user**, with `claude -p` on fixture projects in the
   scratchpad, with `--add-dir` for the scratchpad and the plugin folder. Each run is told to
   answer no to `sync`, so nothing is published:
   - `audit` on a project with a tokens file, two components and three pages that each build an
     input by hand. Expected: an inventory with all four parts; block counts equal to what
     `ds-count.py` prints; a report that proposes a field component as a row; Sources says
     `none yet` for the artifact.
   - `audit` on a project with pages but no components and no tokens file. Expected: the report
     proposes the starting row with the listed token families and base components; Sources says
     `none yet (row <N>)` for the tokens.
   - `refresh <spec path>` on the first fixture, after a component is added and one page's
     hand-built input is replaced so a pattern reaches 0. Expected: the counts change; the new
     component gets a row and a `component` line; the pattern at 0 loses its line and its row;
     no new `hand-built` line appears. A second `refresh`, after a component file is deleted:
     its row and its line are gone.
   - Step 13 in a fixture with no `docs/DESIGN-SYSTEM.md`, with a spec that has a Visual Language
     section: `refresh` is skipped, and the `done` marks commit without it.
3. **The new criterion 6 bullet, in isolation.** In the first fixture, a spec styles a button by
   hand, and its inventory lists `Button`. No other page builds a button by hand, so row 59's
   rule cannot fire. Run `my:spec-review` with the inventory: expect the `design` finding. Run it
   with the inventory removed: expect no such finding. A second spec names `Button` with a variant
   the inventory lacks: expect the `editorial` name finding. A third spec labels a part
   «new: `Field`» and builds it as a shared component: expect no finding about it.
4. **Regression on a zitamu clone**, in the scratchpad, never in the zitamu checkout. First run
   `audit` on the clone, answering no to `sync`, so the clone has an inventory. Then
   `my:spec-review` on row 74b's spec still raises the finding on the find input and the selects.
5. **`sync` by the skill**, from the same clone, with the user's yes, on the zitamu artifact from
   the spike: write its link into the clone's Sources first. Expected: the README's prose is
   kept, its component table is regenerated from the clone's inventory, the Sources line moves to
   the clone's current commit, and the staleness command prints nothing afterwards. The clone is
   deleted after this test.

## Open questions

None. The spike answered the one about the artifact's components (D8).
