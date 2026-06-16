# AI Harness Generalization — Audit & Extraction Map

**Date:** 2026-06-16
**Goal:** make the continuously-developing harness reusable in a new project without rebuilding it, and without forking copies that rot.
**Method:** read-only inventory of the global layer (`~/projects/claude-setup` + `~/.claude`) and one mature project-local layer (`diagoradisa-annotator`). Source material, not yet an implementation plan.
**Scope note:** lives in `claude-setup/docs/plans/` because extraction work happens here; it audits the annotator only as the worked example.

## Core finding
The harness is **already two layers**, and the boundary is 80% of the answer. Generalizing ≠ rebuilding; it = (a) pushing reusable project-local pieces up into the plugin, (b) making the few coupled pieces config-driven, (c) making stack/domain pieces opt-in.

## Layer 1 — Global (already generalizes, auto-applies to every project)
Symlinked into `~/.claude`, version-controlled in `claude-setup`:
- `GLOBAL-CLAUDE.md` → `~/.claude/CLAUDE.md` — instructions, planning standards, git workflow, output discipline.
- `GLOBAL-rules/` → `~/.claude/rules/` — per-language (docker, js-ts, php, python, markdown).
- `~/.claude/settings.json` — `worktree.baseRef`, statusline, `enabledPlugins`, `effortLevel`, `advisorModel`, verbosity SessionStart.
- `my` plugin — agents, commands, skills, `hooks.json`.

A new project inherits all of this for **zero work**. The only thing that doesn't travel is Layer 2.

## Layer 2 — Project-local (the actual subject)
`<repo>/.claude/settings.json` + `<repo>/scripts/hooks/*` + `<repo>/scripts/*` wrappers + project `CLAUDE.md` + the docs/plans·ROADMAP·CHANGELOG·dev-reports conventions.

## Inventory + triage
Buckets: **U**=universal (promote to plugin as-is) · **P**=parameterize (logic generic, bindings config) · **S**=stack-only (Laravel/docker) · **D**=domain-only (this product) · **C**=convention (portable if new project adopts it).

| Item | Bucket | Coupling | Action |
|---|---|---|---|
| `scripts/hooks/check-orphan-plans.sh` | U | none (docs/plans only) | move to plugin |
| `my-plugin/hooks/hooks.json` (squash→roadmap reminder) | U | none | already global ✓ |
| docs/plans + ROADMAP + CHANGELOG + dev-reports + briefings | C | naming/structure | keep as convention; bootstrap stubs |
| worktree + squash-merge workflow | C | none | already in GLOBAL-CLAUDE.md ✓ |
| `scripts/hooks/require-impl-review.sh` | P | hardcodes `resources/js/annotator`, `main`, `*impl-review.md` | params: impl_globs, integration_branch, review_glob |
| `scripts/hooks/require-seam-e2e.sh` + `seam-digest.sh` | P | seam path list; calls `e2e-gate.sh` | params: seam_globs; logic→plugin |
| `scripts/e2e-gate.sh` | P+S | `docker compose run node pnpm`, `dartisan db:seed`, `/login` | route through runtime-command contract |
| `scripts/hooks/review-gate.sh` | P+S | `docker compose exec node`, `./scripts/dpnpm test` | params: test cmd via contract |
| `scripts/dartisan`,`dpnpm`,`dpnpx`,`dcomposer` | S | `docker compose exec php/node` | per-project; they ARE the contract impl |
| `scripts/dev`, `worktree-provision.sh` | S | compose services, shared mounts | per-project; keep here |
| seam path list, `## Dataset Contract` heading | D | product internals | stays |
| plugin agent `oral-medicine-expert` | D | clinical domain | **make opt-in** (see below) |
| plugin agents/commands `laravel-*`, `laravel-fullstack-expert` | S | Laravel | **make opt-in** |
| plugin: `planner`, `commit`, `push`, `summarize`, `task`, `clean-gone-branches`, `optimize-prompt`, `soundness-review`, `dev-reports`, `roadmap/changelog-management`, `clean-plans`, `de-slop`, `git-squasher`, `tune-claude-instructions`, `briefing`, `code-reviewer`, `summarizer` | U | none | already global ✓ |

## Coupling taxonomy (what actually binds Layer 2)
1. **Runtime-exec** (dominant): everything reaches the app through `docker compose exec/run php|node` + `pnpm`/`artisan`. This single coupling blocks `e2e-gate`, `review-gate`, the wrappers.
2. **Path/name**: `resources/js/annotator`, seam globs, `*impl-review.md`.
3. **Stack**: artisan/composer/pnpm, Laravel agents.
4. **Convention**: docs/plans, ROADMAP/CHANGELOG structure — portable by adoption.
5. **Domain**: clinical agent, Dataset Contract.

## The one abstraction that unlocks bucket P
A **runtime-command contract** — a per-project map of named commands the generic gates call *through* instead of hardcoding:
```
.claude/harness.json
  integration_branch: "main"
  impl_globs:  ["resources/js/annotator/**"]
  seam_globs:  ["resources/js/annotator/**", "app/Http/Requests/*Annotation*", ...]
  review_glob: "docs/plans/*impl-review*.md"
  run:
    build:       "docker compose run --rm -w /var/www/html node pnpm run build"
    test:        "./scripts/dpnpm test"
    test:e2e:    "pnpm test:e2e"
    db:seed:     "./scripts/dartisan db:seed --class=E2eFixtureSeeder --force"
    serve_check: "curl -fsS -o /dev/null --max-time 10 http://localhost/login"
```
Generic logic (digest, stamp, hook, gate flow) → plugin. The `run:` map + globs → in-repo. Same `logic + injected-config` split already proven by `seam-digest.sh` (logic) × `SEAM_PATHS` (override).

## Second finding — the plugin itself isn't fully universal
`oral-medicine-expert` (domain) and `laravel-*` (stack) are installed globally but only relevant to this product/stack. In a new non-Laravel project they're dead weight or misleading triggers. **Fix (verified):** split `my` into a universal core + opt-in `laravel`/`domain` packs (the intended multi-plugin pattern). Caveat from verification: plugin *enablement is global-only*, so packs control what you *install*, not per-repo activation — for behavior that must differ per repo, pair packs with **stack-conditioned triggers** (an agent/skill/hook that no-ops unless the repo matches, keyed off `.claude/harness.json` or a repo marker). Packs remove the noise; conditional logic provides the per-repo selectivity.

## Mechanism — and why propagation decides it
Because the harness *continuously develops*, the wrong default is a copy/scaffold template (forks rot; a later fix never reaches existing projects). Choose by propagation need:

- **Generic logic → the plugin** (single source; `claude-setup` push updates every project). Use for: check-orphan-plans, the gate logic, require-impl-review logic.
- **Irreducible per-project config → in-repo** (`.claude/harness.json` + the `scripts/d*` wrappers that implement the contract). These genuinely differ per stack.
- **One-time skeleton → a bootstrap command** (`/harness-init`): drops `.claude/settings.json` hook wiring, an empty `harness.json`, docs/plans + ROADMAP/CHANGELOG stubs. Skeleton only — never logic.

Trade-off vs. a template repo: template is faster to stand up once, but every project forks and drifts from the source — fatal for something you improve weekly. Plugin-centric costs more upfront parameterization but keeps one source of truth.

## New-project bootstrap (what a fresh repo needs)
1. Enable the `my` core plugin (+ stack pack if applicable) — inherits Layer 1.
2. `/harness-init` → writes `.claude/settings.json` (hook wiring to plugin scripts), `.claude/harness.json` (fill in `run:` + globs), docs/plans + ROADMAP + CHANGELOG stubs.
3. Implement the contract: the 3–5 `run:` commands (docker wrappers, or plain `npm`/`pytest`).
4. Done — gates, review routing, roadmap/changelog skills, planning standards all active.

## Risks / don't-over-generalize
- **n=1.** The seam gate is one day old, validated in exactly one project. Freezing its config schema now bakes in annotator idiosyncrasies. **Rule of three:** extract Layer-1-obvious + the runtime contract now; let gates run in a *second* project before crystallizing `harness.json`'s schema.
- **Blast radius:** plugin changes hit *every* project at once. A bad generic-gate edit blocks all commits. Mitigate: gates must degrade to skip (not block) when config absent, as `review-gate.sh` already does for a down runner.
- **Hook bypass unchanged:** PreToolUse hooks only fire on agent commits; manual terminal commits bypass. Generalization doesn't fix this — note in bootstrap.

## Recommended next steps (low → high commitment)
Ordered to respect the n=1 caution above — nothing that *crystallizes the `harness.json` schema* is in the "now" bucket, because committing the gates to a schema is exactly what rule-of-three says to defer.

1. **Now (low risk):** move `check-orphan-plans.sh` into the plugin (pure logic, no schema). Native mechanisms now verified (see findings), so the core/laravel/clinical pack split is safe to do — just design per-repo selectivity via conditional triggers, not native enablement.
2. **Now (low risk, paper only):** write down the runtime-command contract as a *draft* schema and one worked example (the annotator). No code changes to the gates — drafting ≠ adopting.
3. **Defer until project #2 (NOT low risk):** refactor `e2e-gate`/`review-gate`/`require-*` to read globs + `run:` from `harness.json`, promote the gate *logic* into the plugin, and build `/harness-init`. This rewrites safety machinery validated live on 2026-06-16 — any bug silently re-opens the F1/F2/F3 hole, so it **requires re-running the live rehearsal**. Validate the schema against a second, non-identical stack before freezing it.

## Open questions — verify natively BEFORE building (per the "check for existing solutions" standard)
The bespoke pieces below (`harness.json`, `/harness-init`, pack split) may duplicate native Claude Code mechanisms. Resolve via the claude-code-guide check before any build:
- **Per-project plugin enablement:** is `enabledPlugins` honored in a committed project `.claude/settings.json` (precedence user→project→local)? If yes → packs work; if no → drop the pack model.
- **Native per-project plugin config:** does Claude Code offer a project-scoped config a plugin's hooks can read, making `.claude/harness.json` redundant? Prefer native over bespoke.
- **Plugin-bundled hook scripts:** can generic hook *logic* ship in the plugin (`hooks.json` + `${CLAUDE_PLUGIN_ROOT}`-relative scripts) while config stays in-repo?
- **Packaging:** one `my` plugin vs `my-core`/`my-laravel`/`my-clinical` from one marketplace?
- If `harness.json` survives: `.claude/harness.json` vs merge into `.claude/settings.local.json`?
- Bootstrap as a plugin command (`/harness-init`) vs a `claude-setup` script run once per repo?

### Verification findings (claude-code-guide, 2026-06-16) — resolved
- **Per-project plugin enablement: NO.** `enabledPlugins` is **user-global only**; plugins activate globally regardless of project `.claude/settings.json`. → Packs can't be auto-on in repo A / off in repo B via native settings. They still help (don't install Laravel/clinical where never needed), but true per-repo behavior needs **conditional logic** (hooks/skills/agents that no-op outside relevant repos, keyed off `.claude/harness.json` or repo markers), not native enablement.
- **Native per-project plugin config: NONE → `.claude/harness.json` is the idiomatic answer, not reinvention.** No native per-repo config exists; the documented pattern is exactly a repo-local file that plugin scripts read via `$CLAUDE_PROJECT_DIR`. Existing-solution check **passes** — build it.
- **Plugin-bundled hook logic: fully supported.** Plugins ship `hooks/hooks.json` + scripts; scripts resolve their own files via `$CLAUDE_PLUGIN_ROOT` and read repo config via `$CLAUDE_PROJECT_DIR`. So "generic logic in plugin, config in repo" is the intended design. Caveat: `hooks.json` is **static** (can't be templated per-repo) → one hook that reads `harness.json` and branches, never per-repo hooks.json variants.
- **Core + opt-in packs: the intended distribution pattern** (multiple plugins from one marketplace). No native grouping/dependency enforcement; per-repo "must-have-X" is advisory only (documented intent or a harness.json check).

**Net:** the whole `logic→plugin / config→.claude/harness.json` architecture is confirmed idiomatic. Only adjustment: stop expecting native per-project *enablement*; per-repo selectivity comes from conditional logic + which packs the user installed, not settings scope.
