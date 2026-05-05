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

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with one project extension: a custom `### Deployment Contract` heading at the top of `[Unreleased]` for changes that affect how operators deploy or configure the app.

## Files

- `CHANGELOG.md` — project root.
- `docs/plans/` — specs and plans linked from entries.
- `docs/dev-reports/` — destination for everything that isn't contract/behaviour.

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
| **Refactor, test, lint, formatting, internal-only docs** | **Nowhere — write to `docs/dev-reports/`** | 2 |

If the change fits no row, ask the user before editing.

## Rules

### 1. Locate the `[Unreleased]` block

Read CHANGELOG.md and find the current `## [Unreleased] — YYYY-MM-DD` block. Use the existing subsection conventions inside it — don't invent new heading shapes.

### 2. Scope check — does it earn an entry?

Apply the decision table. If the change is internal-only (refactor, test addition, lint config, formatting, code comments, internal docs) write to `docs/dev-reports/` instead and stop. The test: *would an operator deploying this or a user reading release notes care?* If no, it's a dev-report.

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

### 5. Deployment Contract — operator-facing changes go first

Place a `### Deployment Contract` heading at the **top** of `[Unreleased]`, before `### Added`. Use it for: port changes, new or renamed env vars, package-manager migrations, new runtime dependencies, infra requirements, CI/CD pipeline additions. Each bullet should tell an operator what they have to do or know.

### 6. Dated narrative — major coherent shipments

When a single feature warrants more than three or four bullets, give it its own subsection inside `[Unreleased]`:

```
### YYYY-MM-DD — <Feature Name> (<Roadmap Reference>)

<one short paragraph framing what shipped and why>

- <details>
- <details>
```

This is the form a roadmap promotion (🚧 → ✅) usually takes. Include the roadmap reference (e.g., `Clinician-on-Phone #2b`) so a reader can locate the feature in `ROADMAP.md`.

### 7. Update the `[Unreleased]` date

If the existing `## [Unreleased] — YYYY-MM-DD` date is older than today, bump it to today. The date marks the most recent contribution to the unreleased window, not the start of it.

### 8. Link to specs and plans

Every entry that has a corresponding spec/plan in `docs/plans/` should link to it inline. Roadmap rows and CHANGELOG entries are tied together through their shared link to `docs/plans/`, not to each other directly. Use relative paths.

### 9. Commit discipline

- **CHANGELOG-only edits**: one commit. Conventional Commits format: `docs(changelog): note <change>`.
- **Paired with roadmap promotion (🚧 → ✅)**: one commit covers both files. Roadmap-management rule 6 owns the message — typically `docs: mark <feature> shipped on roadmap and changelog`. Don't split the edits across two commits; a reader bisecting `main` should never see a half-paired state.

### 10. Cross-check the entry you just wrote

Edit-scoped only — no full-file audits:

- The new entry sits in the right subsection (deployment-contract changes at the top of `[Unreleased]`, not under `### Added`).
- The change actually landed on `main` (you should know this from context — don't speculate; if uncertain, ask the user before committing).
- Re-run rule 2: would this have fit better in `docs/dev-reports/`?

Skip broad scans (orphan-entry sweeps, link-resolution greps across all entries). Run those only when the user explicitly asks for a CHANGELOG audit.

## Common mistakes

- Logging a refactor or test addition because "it's a notable change." Notable to whom? Refactors → dev-reports.
- Burying a deployment-affecting change in `### Changed`. Operators read top-down; `### Deployment Contract` exists so they don't miss it.
- Adding an entry before the squash-merge has actually landed on `main`. Wait for the merge.
- Editing CHANGELOG without the paired roadmap edit when promoting ✅ — see roadmap-management rule 6.
- Updating CHANGELOG entries when a plan file is renamed and forgetting that ROADMAP also linked to it. Use `git grep` on the old path.
