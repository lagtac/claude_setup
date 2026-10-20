---
name: design-system
description: >
  Keep `docs/DESIGN-SYSTEM.md`, the project's inventory of shared components
  and the patterns pages still build by hand, which UI specs read and spec
  reviews check. Three modes: `audit` builds the inventory and proposes the
  components to build or extract as roadmap rows; `refresh` updates it at
  step 13 of a row with UI; `sync` makes or revises the Design System
  artifact that canvases draw from. Use before the first UI spec in a
  project with no inventory, at step 13, before drawing a canvas when the
  artifact is stale, or when the user types /my:design-system. NOT for
  writing component code: each component to build or extract becomes a
  roadmap row (my:roadmap-management).
---

# Design system

The inventory, `docs/DESIGN-SYSTEM.md`, lists what a project's UI is built
from: the tokens file, the shared components, and the patterns that pages
still build by hand, with counts that a script keeps. Specs read it before
they map a design to components, and `my:spec-review` checks specs against
it. Spec: `docs/plans/2026-10-16-design-system-skill-spec.md` in the
claude-setup repo.

## Arguments

- `audit` — build the inventory from the code, and propose rows.
- `refresh [<spec path>] [auto]` — update the inventory after a row merges.
  Step 13 passes the row's spec path, and `auto` in an auto run.
- `sync` — make or revise the Design System artifact.

Any other arguments: print
`Usage: /my:design-system audit | refresh [<spec path>] [auto] | sync`
and stop.

## The inventory

One file per project with UI, at `docs/DESIGN-SYSTEM.md`. Four parts, in this
order, under fixed headings:

1. **Sources** (`## Sources`). Three lines:
   - `**Tokens:** <path>`, or `none yet (row <N>)` for a new app before its
     starting row.
   - `**Components:** <folder>`, with the name pattern when the folder holds
     other files too (for example `web/components/Z*.vue`).
   - `**Design System artifact:** <url>, synced from <short commit>`, or
     `none yet`.
2. **Components** (`## Components`). A table, one row per shared component:
   name, purpose, variants, sizes, states, tests (yes or no). Words only; the
   numbers are in part 4.
3. **Hand-built patterns** (`## Hand-built patterns`). A table, one row per
   pattern that pages still build by hand: name, what it looks like, and where
   it goes. "Where it goes" is a roadmap row, "kept in the page: <the user's
   reason>", or "no row yet". Words only.
4. **Counts** (`## Counts`). A fenced block with the language tag
   `ds-patterns`, one JSON object per line. JSON lines, not a Markdown table,
   because search expressions contain `|`.

   | Key | Required | Meaning |
   | --- | --- | --- |
   | `name` | yes | Unique in the block. Matches a row name in part 2 or 3. |
   | `kind` | yes | `component` (how many files use it) or `hand-built` (copies to replace). |
   | `globs` | yes | A non-empty list of git glob pathspecs, relative to the repo root. `**/` matches any depth. Their matches add up. |
   | `exclude` | no | A list of git glob pathspecs whose files are left out, such as the component that wraps the native element, so a count can reach zero. |
   | `regex` | yes | A Python regular expression, matched over each file's whole text, so a pattern may span lines. It must not match the empty string. |
   | `count`, `files` | written by `ds-count.py --write` | Matches in total, and files with at least one match. |

   Example lines:

   ```text
   {"name": "text field", "kind": "hand-built", "globs": ["web/**/*.vue"], "exclude": ["web/components/Z*.vue"], "regex": "<input\\b", "count": 39, "files": 14}
   {"name": "ZButton", "kind": "component", "globs": ["web/**/*.vue"], "regex": "<ZButton\\b", "count": 36, "files": 13}
   ```

   Raw values outside the tokens file are `hand-built` patterns too, for
   example `:\s*#[0-9a-fA-F]{3,8}\b` (a hex colour after a colon), with the
   tokens file excluded.

Each block `name` matches a row name in part 2 or 3. This skill checks that
in `audit` and `refresh`; `ds-count.py` does not.

### The template

This is the only template for the inventory. Copy it, then fill it in.

````markdown
# Design system

## Sources

- **Tokens:** <path>, or none yet (row <N>)
- **Components:** <folder>
- **Design System artifact:** none yet

## Components

| Name | Purpose | Variants | Sizes | States | Tests |
| --- | --- | --- | --- | --- | --- |

## Hand-built patterns

| Name | What it looks like | Where it goes |
| --- | --- | --- |

## Counts

Written by `ds-count.py --write`. Edit the search keys by hand; never the
counts.

```ds-patterns
```
````

## `ds-count.py`

`ds-count.py [--write] [<inventory>]` is on `PATH`, from the plugin's `bin/`.
It reads the `ds-patterns` block, counts each line's `regex` in the tracked
files its globs match, and prints one line per pattern:
`<name>  <kind>  <old count>/<old files> -> <new count>/<new files>`, with
`new` in place of the old values on a line not yet counted. `--write` stores
the new counts in the block. It exits 1 with one message, and writes nothing,
on a bad line, a duplicate name, a regex that does not compile or matches the
empty string, or globs that match no tracked file. Fix the line it names and
run it again.

Counts come only from this script. Never count by hand, and never type a
number into the block.

## `audit`

A full review. Run it by hand at any time, and before the first UI spec of an
architectural change, with or without a plan, in a project with no
inventory. In a new project,
`my:architect` runs first.

1. **Sources.** Find the tokens file and the components folder by searching
   the repo. Confirm both with the user (`AskUserQuestion`; in a session
   without it, take the answers from the prompt). Write them into Sources.
   Sources says `none yet` for the artifact until step 7.
2. **Components.** Read each shared component, and fill its row in part 2.
3. **Hand-built patterns.** Search the pages for what they build by hand:
   buttons, fields, selects, messages, page shells, cards, list rows,
   toolbars, empty states, dialogs, and raw colour and size values. Write one
   `ds-patterns` line per pattern and one per component. When a pattern's
   globs also match the component that wraps the native element, exclude that
   component. Then run `ds-count.py --write`.
4. **Judge.** Check each finding against this list:
   - A pattern with two or more users becomes a shared component.
   - A variant is named by how it looks, not by a colour token it does not
     use (zitamu's `sky` variant used the primary tokens).
   - Every control has focus, disabled and loading states, and a target of at
     least 24px.
   - A component nobody uses is deleted.
   - A token defined but never used is deleted, after a check for tokens read
     from script.
5. **Propose rows.** Propose each component to build or extract as a roadmap
   row. The user decides which rows to add (`AskUserQuestion`; without it,
   follow the prompt). `my:roadmap-management` writes them, and the user
   places them in the order. A pattern the user keeps in the page gets "kept
   in the page: <the user's reason>" in part 3.
6. **Names.** Check that each block `name` matches a row name in part 2 or 3.
7. **Artifact.** Run `sync`, with the user's yes, so Sources gets the
   artifact's link and commit. A new app with no tokens file skips this until
   its starting row ships.
8. **Report.** Write `docs/reports/YYYY-MM-DD-design-system-audit.md`, with
   these sections: summary, naming, token coverage, component completeness,
   missing components, priority actions, where these go. Its status line
   names the rows. Commit the report and the inventory as one `docs:` commit
   (see "Rules").

**A new app** is an `audit` that finds no shared components. The report
proposes one starting row, placed before the first page row: the token
families (colour, type roles, spacing, radius, motion, the focus ring) and a
button, a field (label, input, hint, error), a select, an inline message, a
page shell and a visually hidden class. Sources says `none yet (row <N>)` for
the tokens, with that row's number. That row's canvas uses `frontend-design`
for the visual direction.

## `refresh`

Step 13 of a row whose spec has a Visual Language section, or whose squash
commit touches the tokens file or the components folder. Step 13 passes the
row's spec path, and `auto` in an auto run. Run by hand, the spec path is
optional. With no `docs/DESIGN-SYSTEM.md`, print
`No docs/DESIGN-SYSTEM.md; run /my:design-system audit first.` and stop.

1. Run `ds-count.py --write`.
2. **Components.** When a Sources line says `none yet (row <N>)` and its
   tokens file or components folder now exists, write the path there.
   Update the part 2 rows of each component that the spec's row added or
   changed. Add a part 2 row and a `component` line for any
   component in the Sources folder that the inventory lacks. Remove the row
   and the line of any component no longer in the Sources folder. When a new
   component wraps the native element of a `hand-built` pattern, add the
   component's file to that pattern's `exclude`, so the count can reach 0.
   Then run `ds-count.py --write` again, so the new lines get their counts.
3. **Retire.** Remove the line and the part 3 row of each `hand-built`
   pattern whose count is now 0. Add no `hand-built` lines: only `audit`
   adds them.
4. **Names.** Check that each block `name` matches a row name in part 2 or 3.
5. **Staleness.** When Sources says `none yet` for the tokens file, skip this
   step. Otherwise read the tokens file, the components folder and the
   synced commit from Sources, and run, with the paths quoted so that git,
   not the shell, matches them, and a deleted file still counts:

   ```bash
   git log --oneline <synced commit>..HEAD -- '<tokens file>' '<components folder>'
   ```

   The artifact is stale when the command prints something, or when Sources
   says `none yet` for the artifact. Only when it is stale, run `sync`. With
   `auto`, never run `sync`: leave Sources as it is, and print
   `The Design System artifact is stale; run /my:design-system sync.`
6. Write no report. At step 13 the edits go into the step-13 `docs:` commit
   with the `done` marks. Run by hand, they are their own `docs:` commit (see
   "Rules").

## `sync`

The Design System artifact on claude.ai. Canvases are drawn on it, so their
boards use the project's exact tokens. It holds tokens and named components,
not component previews.

1. **Ask first.** Publishing to claude.ai is outward-facing. Before any
   publish, ask the user for a yes. With `auto`, or without a yes, stop here
   and leave Sources as it is.
2. **Create or revise.** With no link in Sources: create the artifact from
   the Artifact tool's **Design System** type, titled with the project's
   name. With a link: revise that artifact; the type's re-sync rules merge,
   and keep the README's prose and anything added on the page.
3. **Fill it.** Follow the type's `from-code.md`: exact tokens in both
   themes, the font files, the logos, and a README of usage rules that name
   tokens. Generate the README's component table from part 2 of the
   inventory: names and purposes, no previews. The README must have a "Not
   synced" list that names each value the format cannot hold.
4. **Sources.** Write the link and `synced from <short HEAD>` into Sources,
   with `git rev-parse --short HEAD`.
5. Run by hand on its own, commit the Sources edit as its own `docs:` commit
   (see "Rules"). Inside `audit`, it joins the audit's commit.

## Rules

- **No component code.** This skill writes no component, token or page
  code. Each component to build or extract becomes a roadmap row, with its
  own spec and tests.
- **No new `hand-built` line outside `audit`.** A part with one user is not a
  pattern yet. When a second page needs it, that page's spec makes it a
  shared component.
- **Counts come only from `ds-count.py`.**
- **Commits.** Every commit this skill makes is a `docs:` commit, with the
  docs scope of the project's rules, of `docs/DESIGN-SYSTEM.md` and, for
  `audit`, the report. Name the paths, so another session's staged files
  stay out: `git add -- <paths>`, read `git diff --cached`, then
  `git commit -m "<message>" -- <paths>`.
- **Parallel runs.** In a project whose `CLAUDE.md` or `CLAUDE.local.md` has
  a "Parallel runs" section, `docs/DESIGN-SYSTEM.md` is a shared doc. Before
  editing it, run `git diff --quiet HEAD -- docs/DESIGN-SYSTEM.md`; when it
  exits non-zero, someone else has uncommitted edits there: stop and tell
  the user. Commit with the locked form: write the message with the Write
  tool to a new file in the session's scratchpad, read each new file whole
  and `git diff -- <paths>`, then run
  `locked-commit.py -F <message file> <paths>`, and check that the
  `git show --stat` list it prints holds only those paths.
