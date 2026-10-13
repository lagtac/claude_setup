---
name: changelog-management
description: >
  Use when editing CHANGELOG.md — recording a shipped feature, deployment or
  config change, user-visible bug fix, or removed capability. Trigger on
  phrases like "add a changelog entry", "note the deploy change", "we just
  shipped X", "X is fixed on main", or "the env var changed". Owns CHANGELOG
  scope, structure, and commit discipline. When the edit is paired with a
  roadmap promotion (🚧 → ✅), the roadmap-management skill drives and this
  skill handles the CHANGELOG half.
---

# Changelog Management

CHANGELOG records contract or behaviour changes that reached `main` — what users, operators, and downstream services experience. Refactors, tests, lint, and internal docs do not belong here; they go to `docs/dev-reports/`.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). For a deployed app, a `### Deployment Contract` heading at the top of `[Unreleased]` collects operator-facing deploy/config changes; libraries usually omit it, and a project may define its own contract heading (see Adapting).

## Adapting to the project

This skill works for any software project. The specifics here are **defaults**; resolve a project's real conventions in this order, and never impose one it contradicts:

1. **Match what exists** — follow the format an existing `CHANGELOG.md` already uses.
2. **Read the project's `CLAUDE.md`** (and `CLAUDE.local.md` when present) — it may document a custom contract heading, entry format, file locations, which changes earn an entry, and git workflow. Honour those over every default in this skill, including the bold rows of the decision table and the commit rules. For example, a project may want refactors logged, or may want the entry inside the feature's own commit rather than in a separate `docs(changelog)` commit.
3. **Fall back to the defaults** — Keep a Changelog 1.1.0, `docs/plans/` links, `docs/dev-reports/` for internal work.
4. **Ask when ambiguous** — especially project type (below).

**Scale entries to whoever consumes this project's main/release branch:**
- **Deployed app / service** → operators (deploy + config) and end users. Operator-facing changes go under `### Deployment Contract` (default).
- **Library / SDK / CLI** → API consumers. Breaking changes are the headline: mark them and respect semver (e.g. a `**BREAKING**` prefix under `### Changed` / `### Removed`); `### Deployment Contract` usually doesn't apply.
- **Data / ML pipeline or other** → whoever downstream depends on its output; the project may define its own contract heading (e.g. `### Dataset Contract`) — match what its CLAUDE.md documents.

If no `CHANGELOG.md` exists and the user wants one, offer to create it with a Keep a Changelog header; don't silently scaffold.

## Files

- `CHANGELOG.md` — project root (default).
- spec/plan docs — `docs/plans/` by default; use the project's documented location. Linked from entries.
- internal-work destination — `docs/dev-reports/` by default; everything that isn't contract/behaviour.

## Decision table

| Situation | Where it goes | Rule |
|---|---|---|
| Roadmap row promoted 🚧 → ✅ | Dated narrative entry inside `[Unreleased]`, paired with roadmap edit | 6, 8 |
| Deployment / config change (port, env var, runtime dep, package manager) | `### Deployment Contract` at top of `[Unreleased]` | 5 |
| User-visible feature shipped without a roadmap row | `### Added` bullet | 4 |
| Behaviour or contract changed (route, response shape, default) | `### Changed` bullet | 4 |
| Bug fix to user-visible behaviour on `main` | `### Fixed` bullet | 4 |
| Feature, route, or runtime dep removed | `### Removed` bullet | 4 |
| Notable docs reorg (cross-referenced specs, audits) | `### Docs` bullet | 4 |
| Major coherent shipment (multi-aspect, multi-paragraph) | `### YYYY-MM-DD — Title` dated narrative | 6 |
| **Refactor, test, lint, formatting, internal-only docs** | **No CHANGELOG entry** (a dev report covers it) | 2 |

If the change fits no row, ask the user before editing.

## Rules

### 1. Locate the `[Unreleased]` block

Read CHANGELOG.md and find the current `## [Unreleased]` block. Some projects date it (`## [Unreleased] — YYYY-MM-DD`), some do not; keep whichever form the file uses. Use the existing subsection conventions inside it — don't invent new heading shapes.

### 2. Scope check — does it earn an entry?

Apply the decision table. If the change is internal-only (refactor, test addition, lint config, formatting, code comments, internal docs), make no CHANGELOG edit and stop. Tell the user in one line that it is internal work, which a dev report (`kit:dev-reports`) covers. Do not write a dev report unless the user asks for one. The test: *would an operator deploying this or a user reading release notes care?* If no, it's a dev-report.

### 3. Pick a structure

Three compatible patterns inside `[Unreleased]`:

- **Categorised bullet** (rule 4) — atomic changes.
- **Deployment Contract** (rule 5) — operator-facing config/deploy changes.
- **Dated narrative** (rule 6) — major coherent shipments.

These coexist in one `[Unreleased]` block; pick whichever fits the change's shape.

### 4. Categorised bullet — Keep a Changelog standard

Use one of: `### Added`, `### Changed`, `### Fixed`, `### Removed`, `### Docs`. One bullet per change. Past tense, user-facing language, terse. Link the spec/plan if one exists:

```
### Fixed
- Upload form now surfaces inline message when Firefox 149 on Wayland delivers an empty `DataTransfer`. See [docs/plans/...](docs/plans/2026-04-29-firefox-wayland-empty-drop-followup.md).
```

### 5. Contract heading — consumer-facing changes go first

For a deployed app, place a `### Deployment Contract` heading at the **top** of `[Unreleased]`, before `### Added`. Use it for: port changes, new or renamed env vars, package-manager migrations, new runtime dependencies, infra requirements, CI/CD pipeline additions. Each bullet should tell an operator what they have to do or know.

Adapt by project type (see Adapting): use the project's own contract heading if it defines one (e.g. `### Dataset Contract`); for a **library/SDK** there's no operator step — record breaking API changes under `### Changed` / `### Removed` with a `**BREAKING**` marker and a semver note instead.

### 6. Dated narrative — major coherent shipments

When a single feature warrants more than three or four bullets, give it its own subsection inside `[Unreleased]`:

```
### YYYY-MM-DD — <Feature Name> (<Roadmap Reference>)

<one short paragraph framing what shipped and why>

- <details>
- <details>
```

This is the form a roadmap promotion (🚧 → ✅) usually takes. Include the roadmap reference (e.g., `Checkout #2b`) so a reader can locate the feature in `ROADMAP.md`.

### 7. Update the `[Unreleased]` date

Only when the heading carries a date: if the existing `## [Unreleased] — YYYY-MM-DD` date is older than today, bump it to today. Never add a date to an undated heading. The date marks the most recent contribution to the unreleased window, not the start of it.

### 8. Link to specs and plans

Every entry that has a corresponding spec/plan in `docs/plans/` should link to it inline. Roadmap rows and CHANGELOG entries are tied together through their shared link to `docs/plans/`, not to each other directly.

Same link discipline as `roadmap-management` rule 8 — a CHANGELOG is read on the Git host's web UI and is often exported to HTML for release notes, so links must survive both:

- **Same-repo targets → relative `.md`**, never hardcode `.html`. The host renders Markdown; an HTML export rewrites the extension at build time, so `.html` in source breaks the hosted and raw views.
- **Out-of-repo targets → absolute web URLs**, not relative `../other-repo/...` paths — a cross-repo relative path is dead anywhere but a local checkout with the sibling repo beside it.
- When a linked doc is moved, archived, or renamed, repoint the link; `git grep` the old path across `CHANGELOG.md`, `ROADMAP.md`, and `docs/`.
- An entry that references a now-deleted doc (e.g. a runbook removed with the feature it documented) should be **unlinked** — keep the filename as plain text so the historical entry still reads, but don't leave a dead link.

### 9. Commit discipline

- **CHANGELOG-only edits**: one commit. Conventional Commits format: `docs(changelog): note <change>`.
- **Paired with roadmap promotion (🚧 → ✅)**: one commit covers both files. Roadmap-management rule 6 owns the message — typically `docs: mark <feature> shipped on roadmap and changelog`. Don't split the edits across two commits; a reader bisecting `main` should never see a half-paired state.

### 10. Cross-check the entry you just wrote

Edit-scoped only — no full-file audits:

- The new entry sits in the right subsection (deployment-contract changes at the top of `[Unreleased]`, not under `### Added`).
- The change actually landed on `main` (you should know this from context — don't speculate; if uncertain, ask the user before committing).
- Re-run rule 2: would this have fit better in `docs/dev-reports/`?

Skip broad scans (orphan-entry sweeps, link-resolution greps across all entries). Run those only when the user explicitly asks for a CHANGELOG audit.

### 11. Entry content discipline — summarise the change, link the detail

A CHANGELOG entry records **what changed** for whoever consumes the branch; it is not a copy of the spec, plan, experiment-log, or briefing that explains the change. State the contract/behaviour delta in user/operator language and link the detail (rule 8) — don't reproduce metrics, commit SHAs, per-phase play-by-play, or full verdict reasoning that the linked doc already owns. Those facts live in one place — the linked doc, the source of truth — so a later correction there doesn't strand a stale copy here.

A dated narrative (rule 6) is still **one short framing paragraph + bullets of what changed**, not a transplanted results section. If a bullet carries a figure only to re-prove a point the linked doc already makes, cut the figure and keep the link. (The companion `roadmap-management` rule 11 enforces the same index-not-archive discipline on the roadmap side.)

## Common mistakes

- Logging a refactor or test addition because "it's a notable change." Notable to whom? Refactors → dev-reports.
- Burying a deployment-affecting change in `### Changed`. Operators read top-down; `### Deployment Contract` exists so they don't miss it.
- Adding an entry before the change has actually landed on the main/release branch. Wait for the merge.
- Editing CHANGELOG without the paired roadmap edit when promoting ✅ — see roadmap-management rule 6.
- Updating CHANGELOG entries when a plan file is renamed and forgetting that ROADMAP also linked to it. Use `git grep` on the old path.
- Transplanting an experiment-log's metrics, SHAs, or verdict reasoning into a CHANGELOG entry. Summarise the change and link the detail (rule 11).
- Hardcoding `.html`, linking a cross-repo file by a relative `../other-repo/...` path, or leaving a link to a doc that was deleted. Same-repo → relative `.md`; cross-repo → absolute URL; deleted target → unlink to plain text (rule 8).
