---
name: roadmap-management
description: >
  Use when updating ROADMAP.md — adding a feature, promoting between status
  tiers (💭 → 📋 → 🚧 → ✅), splitting or reframing a row, or marking
  something shipped. Trigger on phrases like "update the roadmap", "mark X
  as shipped", "X is done", "move X to in progress", "we just merged Y", or
  whenever a feature transitions lifecycle stages. Owns the roadmap;
  delegates the CHANGELOG half of a 🚧 → ✅ promotion to the
  `changelog-management` skill.
---

# Roadmap Management

A roadmap is **forward-looking** — what's next, in flight, or shipped recently. A CHANGELOG is **backward-looking** — what reached `main` and changed contract or behaviour. They couple at one moment: the integration (squash-merge by default) that promotes a row from 🚧 to ✅. At that moment both files update in the same commit (rule 6).

This skill owns the roadmap. The companion `changelog-management` skill owns the CHANGELOG. When a 🚧 → ✅ promotion happens, this skill drives the commit and delegates the CHANGELOG half to `changelog-management`.

## Adapting to the project

This skill works for any software project. The paths, git workflow, and legend below are **defaults**, not law. Resolve a project's real conventions in this order, and never impose one the project contradicts:

1. **Match what exists.** If `ROADMAP.md` is already present, follow its format, legend, and section scheme.
2. **Read the project's `CLAUDE.md`.** It documents the spec/plan location, git workflow (worktrees or not, default/release branch name, squash vs PR vs direct merge), and dev-report destination. Honour those over the defaults.
3. **Fall back to the defaults** in this skill (`docs/plans/`, squash-merge to `main`, the legend below, `docs/dev-reports/`).
4. **Ask when ambiguous** — e.g. project type, or where specs live if the project documents nothing. Don't guess a convention into existence.

If no `ROADMAP.md` exists and the user wants one, offer to create it (default legend + a one-line intro); don't silently scaffold.

## Files

- `ROADMAP.md` — project root (default). Living index of features. Owned by this skill.
- spec/plan docs — `docs/plans/` by default; use the project's documented location. Linked from roadmap rows.
- `CHANGELOG.md` — project root. Touched only via `changelog-management` (delegated at rule 6).
- internal-work destination — `docs/dev-reports/` by default; refactors / tests / lint / internal docs. Owned by `changelog-management` rule 2.

## Status legend

Default — match a project's own legend if its `ROADMAP.md` already uses one:

`✅ shipped` · `🚧 in progress` · `📋 planned` · `💭 discussed, not scheduled`

## Decision table

Look up the situation, then jump to the rule. Bold rows are the easy ones to get wrong.

| Situation | Files touched | Rule |
|---|---|---|
| Idea raised but user hasn't agreed yet | None — wait | — |
| User agreed to add an idea | ROADMAP only — new row, status `💭`, no link | 3 |
| Spec landed at `docs/plans/...-spec.md` | ROADMAP only — `💭 → 📋`, link spec | 4 |
| Plan landed + work started | ROADMAP only — `📋 → 🚧`, link plan | 5 |
| **Integration to the main/release branch just landed** (squash, PR, or direct merge) | **ROADMAP + CHANGELOG in the same commit** — `🚧 → ✅` and add changelog entry | 6 |
| Scope or framing changed mid-flight | ROADMAP only — edit row in place, note pivot | 7 |
| One row growing into multiple sub-tasks | ROADMAP only — suffixed numbering (`1`, `1b`, `1c`) | 7 |
| Speculative `💭` / `📋` row now off-table | ROADMAP only — delete row | 7 |
| Already-shipped feature later removed from `main` | The ✅ row **stays**; CHANGELOG gets the `### Removed` entry | 7 + `changelog-management` |
| **Any CHANGELOG-only edit** (deploy change, hotfix, removal, behaviour change with no roadmap row) | CHANGELOG only — use **`changelog-management`** | `changelog-management` |
| **Refactor, test, lint, formatting, internal-only docs** | **Neither** — write to `docs/dev-reports/` | `changelog-management` rule 2 |
| Plan file renamed or moved | Both files where the path is linked | 8 |

If a request fits no row, ask the user — premature roadmap entries and speculative changelog lines are noise.

## Rules

The rules are sequential and keyed by the decision table above.

### 1. Read ROADMAP.md before editing it

Open `ROADMAP.md` and find the area section the row belongs to (Design System, Clinician-on-Phone, Admin, Marketing, etc.) plus the row's existing numbering context. Don't open `CHANGELOG.md` from this skill — if the edit pairs with a CHANGELOG entry (rule 6), `changelog-management` owns that file.

### 2. Identify the lifecycle transition

Look up the user's request in the decision table above and jump to the rule it points to. The table is the source of truth for which files to touch — don't edit anything until the situation matches a row.

### 3. New row — idea → 💭

A new row goes in only **after** the user has agreed to the idea in conversation. Casual mentions and brainstorm tangents do not earn a row.

- Pick the area section that fits (or propose a new `## Section` if none does — confirm with the user).
- Choose the next free `#` in that table (continue the section's numbering, including suffix forms like `1b`, `1c` when the row clearly extends a previous one).
- Status: `💭`. Spec/plan column: `—`. No link required at this stage.
- Title format: `**<Short Name>** — <one-clause framing>`. Match the style of existing rows.

### 4. Promote 💭 → 📋 — spec landed

Verify a spec file exists at `docs/plans/YYYY-MM-DD-<slug>-spec.md` (or the project's documented spec path). If it doesn't, refuse the promotion — `📋` means "spec is written," not "we plan to write a spec."

- Update the status cell to `📋`.
- Add a markdown link to the spec in the Spec / Plan column: `[spec](docs/plans/YYYY-MM-DD-<slug>-spec.md)`.
- If the row body needs to grow (e.g., the spec materially reframed the feature), edit the title's tail clause to match — never leave the row title contradicting its linked spec.

### 5. Promote 📋 → 🚧 — plan written and work started

Two preconditions, both required:

- A plan file exists (default `docs/plans/YYYY-MM-DD-<slug>.md`; use the project's location).
- Implementation has actually started in an isolated workspace appropriate to the project's git workflow. If the project uses worktrees (see its CLAUDE.md), a worktree exists; if it uses branches, the feature branch exists; if it legitimately works on the main branch, "started" is enough. The point is real work underway — not a worktree per se. Don't withhold 🚧 in a project that doesn't use worktrees.

Then:

- Status → `🚧`.
- Spec / Plan column → `[spec](...), [plan](...)`. Keep both links if both exist.
- Do **not** touch the CHANGELOG yet. In-progress work has not changed any contract.

### 6. Promote 🚧 → ✅ — integrated to the main/release branch (couples with CHANGELOG)

This is the only transition that touches both files. **Both edits go in the same commit.**

Preconditions:

- The integration to the project's main/release branch has already happened — squash-merge, PR merge, or direct, whatever the project uses (verify with `git log` on that branch if uncertain — do not pre-emptively mark ✅ before it lands).
- The plan/spec links in the Spec / Plan column still resolve.

Roadmap edit:

- Status → `✅`.
- Update the row body if the implementation diverged from the plan (this is common — the row should describe what shipped, not what was planned). Keep it terse; deep narrative belongs in CHANGELOG.

CHANGELOG edit (in the **same commit**): hand off to the `changelog-management` skill for scope, structure, dating, and linking. Both edits land in one commit (rule 9 below).

Commit message:

```
docs: mark <feature> shipped on roadmap and changelog
```

If multiple shipments land in one go, list them in the body.

### 7. Reframes, splits, deletions

- **Reframe** (scope or framing changed mid-flight): edit the row in place. Add one short clause to the row body explaining the pivot ("originally framed as X; reframed to Y after Z became clear"). Do **not** re-date the row.
- **Split** (one row grew into multiple sub-tasks): keep the parent's number, give children suffixed numbers (`1`, `1b`, `1c`). Match the existing pattern in the file — do not invent new numbering schemes.
- **Delete a 💭 / 📋 row**: allowed when the row is speculative and the user has agreed it's off the table. Note the deletion briefly in the next CHANGELOG entry's `### Removed` (or `### Docs`) section if a follow-up reader would otherwise wonder where it went.
- **Delete a ✅ row**: don't. Shipped rows are historical record. They stay even if the feature was later removed — note the removal as a fresh CHANGELOG entry under `### Removed`.

### 8. Linking discipline (roadmap side)

- Every roadmap row in `📋`, `🚧`, or `✅` status **must** link to its spec and/or plan. A row without a link is by definition `💭`.
- Use relative paths: `docs/plans/YYYY-MM-DD-<slug>.md`.
- If a plan moves or is renamed (per the `clean-plans` skill), update the roadmap row's link. CHANGELOG-side updates are owned by `changelog-management`. When renaming, run `git grep` once on the old path to find every reference across both files.

CHANGELOG-side linking lives in `changelog-management`. The two files are tied together by their shared link down to `docs/plans/`, not to each other directly.

### 9. Commit discipline (roadmap side)

- Roadmap-only edits (rules 3–5, 7): one commit. Message: `docs: <verb> ROADMAP for <feature>`.
- Roadmap + CHANGELOG paired edits (rule 6): **one commit**, never two. Message: `docs: mark <feature> shipped on roadmap and changelog`. Splitting them breaks atomicity — a reader bisecting `main` should never see a ✅ row whose CHANGELOG entry hasn't landed yet, or vice versa.
- CHANGELOG-only edits: see `changelog-management` rule 9.

Use Conventional Commits in all cases (project rule).

### 10. Cross-check the row you just touched

Edit-scoped only — no full-file audits:

- The status reflects reality (the integration has actually landed for ✅; plan file actually exists for 🚧; spec file actually exists for 📋).
- The Spec / Plan column links resolve.
- The markdown table is still well-formed (no broken pipes, no missing cells).

Skip broad audits (stale-💭 sweeps, orphan-row scans, full-file link greps). Run those only when the user explicitly asks for a roadmap audit.

## Common mistakes

- Promoting 📋 → 🚧 just because a workspace was created — the plan file must exist first.
- Promoting 🚧 → ✅ before the integration has actually landed on the main/release branch (`git log` not yet showing it).
- Editing only the roadmap on a shipment, forgetting the CHANGELOG entry — or vice versa. The same-commit rule (9) is the safety net.
- Putting a refactor or a test addition in CHANGELOG. It belongs in `docs/dev-reports/` (see `changelog-management` rule 2).
- Deleting a ✅ row when the feature was later removed. Add a `### Removed` CHANGELOG entry instead; the historical row stays.
- Adding a 💭 row for a casual brainstorm tangent. Wait for explicit user agreement first.
