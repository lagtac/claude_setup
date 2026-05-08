# Code Review Surfaces: Comparison & Consolidation Plan

## Context

User maintains four review surfaces (`my:code-review`,
`my:laravel-code-review`, `feature-dev:code-reviewer`,
`superpowers:requesting-code-review`) and asked whether their content
justifies separation, or whether one base reviewer + language-specialized
variants would be cleaner. The first three target uncommitted diffs; the
fourth targets a committed range (`BASE..HEAD`) and is the surface that
fires pre-merge.

**Comparison finding:** The three surfaces conflate two distinct concerns —
*how to review* (methodology, anti-sycophancy framing, confidence handling,
output shape) and *what to look for* (domain checklist). Today they are
tangled across three differently-shaped files. Consolidating along that
seam produces one base review skill + per-language shim skills.

**Resolved decisions:**
- Architecture: **skill-based** (not command + agent)
- Language adapters: **Laravel, Python, TypeScript**
- Range axis: **`my:code-review` covers both working-tree and committed
  ranges** via an optional `range` argument. `superpowers:requesting-code-review`
  is retired from the routing table — its plan-alignment check and
  structured DESCRIPTION/REQUIREMENTS inputs are absorbed into the
  canonical skill so one methodology applies pre-commit and pre-merge.
- `feature-dev` plugin: **keep installed** (its `code-architect`,
  `code-explorer` agents and `/feature-dev:feature-dev` skill remain
  useful); never invoke `feature-dev:code-reviewer`, enforced by the
  routing table in `~/.claude/CLAUDE.md`
- Confidence rule: **severity-conditioned surfacing** (see Phase 3),
  applies uniformly across both range modes

## Phase 1: Comparison (reference)

| Aspect | `my:code-reviewer` agent | `feature-dev:code-reviewer` agent | `/my:laravel-code-review` (via `laravel-fullstack-expert`) | `superpowers:requesting-code-review` |
|---|---|---|---|---|
| Model | Opus | Sonnet | unspecified | inherits caller |
| Target | uncommitted diff | uncommitted diff | uncommitted diff | committed range `BASE..HEAD` |
| Anti-sycophancy | explicit | implicit (threshold) | none | none |
| Confidence | qualitative H/M/L | numeric 0–100, ≥80 cutoff | none | none |
| Dual-perspective | mandatory | no | no | no |
| Reasoning paragraph | required before verdict | no | required before recommendations | no |
| Checklist | 12-item generic | CLAUDE.md-driven | Laravel-specific 5-step + 7-section output | generic (plan-alignment + quality + arch + tests + prod) |
| Severity vocabulary | (none — qualitative confidence) | (none — threshold) | sections, no severity | Critical / Important / Minor |
| Plan-alignment check | no | no | no | yes (DESCRIPTION + PLAN_OR_REQUIREMENTS inputs) |
| Output location | `$planDirectory/{feature}-review.md` | inline | inline | inline |
| Topical scope | language-agnostic | language-agnostic | Laravel-specific | language-agnostic |
| Agent dispatched | `my:code-reviewer` | (used directly) | `laravel-fullstack-expert` (mismatch — a dev advisor, not a reviewer) | `general-purpose` with templated prompt |
| Owner | `my-plugin` | `feature-dev` plugin | `my-plugin` | superpowers (upstream) |

**Findings:** my:code-reviewer and feature-dev:code-reviewer are alternative
methodologies (qualitative dual-perspective vs numeric threshold), not
complements — redundant. /my:laravel-code-review's only unique value is
Laravel-specific checklist content; it loses anti-sycophancy and confidence
discipline by dispatching a development advisor agent rather than a
reviewer. `superpowers:requesting-code-review` is the only surface that
targets a committed range and the only one with a plan-alignment check —
both worth absorbing into the canonical skill, but its severity vocabulary
(Critical/Important/Minor) and lack of anti-sycophancy / dual-perspective
framing conflict with the methodology this plan adopts.

## Phase 2: Skill-Based Architecture

One canonical skill owns methodology and the generic checklist. Per-language
shim skills delegate to it with a language hint. The actual review still
dispatches a subagent (fresh context, per `superpowers:requesting-code-review`
rationale), but the agent file becomes a thin executor — discipline is
authored once, in the canonical skill.

### Components

**`my:code-review` (canonical skill)** — `my-plugin/skills/code-review/SKILL.md`
- Owns: methodology, anti-sycophancy framing, confidence rules, dual-perspective
  output, reasoning paragraph, output file location, generic 12-item checklist
- References:
  - `checklists/generic.md` — the 12-item default
  - `checklists/laravel.md` — Laravel checklist
  - `checklists/python.md` — Python checklist
  - `checklists/typescript.md` — TypeScript checklist
  - `code-reviewer-prompt.md` — the dispatch template (built from
    methodology + selected checklist)
- Skill flow:
  1. Parse skill args: `range` (default = working tree; or
     `BASE..HEAD` / two SHAs / `since=<sha>`), `description` (optional —
     what was built), `plan` (optional — path to plan/spec/requirements).
     When `description` or `plan` is supplied, the dispatch prompt
     includes a "Plan alignment" check; otherwise that section is omitted.
  2. Detect language: explicit hint from invoking shim skill, OR
     project-marker auto-detect (`composer.json` + `artisan` → Laravel;
     `pyproject.toml` + `uv.lock` → Python; `package.json` + `tsconfig.json`
     → TypeScript). Fall back to generic.
  3. Load corresponding checklist file
  4. Resolve git range: either capture working-tree diff (`git diff` +
     `git diff --staged` + untracked) or commit range
     (`git diff BASE..HEAD` + `git log BASE..HEAD --oneline`)
  5. Build dispatch prompt from `code-reviewer-prompt.md` + checklist +
     range payload + (optional) plan-alignment block
  6. Dispatch `my:code-reviewer` subagent with the built prompt
  7. Surface the review output written to `$planDirectory/{feature}-review.md`

**`my:laravel-code-review` (shim skill)** — one-paragraph SKILL.md:
"Specialized entry point for Laravel review. Delegates to `my:code-review`
with `language=laravel`." No methodology, no checklist content — pure UX
discoverability.

**`my:python-code-review`, `my:ts-code-review` (shim skills)** — same
pattern.

**`my:code-reviewer` (agent)** — refactor to lean executor. Anti-sycophancy
directives, dual-perspective output structure, reasoning-paragraph
requirement, output file location stay (these are how the agent renders
its work). The methodology *narrative* and all checklists move out to the
skill. The agent receives the full prompt (methodology + checklist + diff
context) from the skill at dispatch time.

**`feature-dev:code-reviewer`** — never invoked; routing table enforces.

**`superpowers:requesting-code-review`** — never invoked; routing table
reassigns the committed-range row to `my:code-review` with a `range` arg.
The skill itself remains installed (it's part of the upstream superpowers
plugin and we don't manage it), but our routing never reaches it.

**`laravel-fullstack-expert`** — keep, but stop using for review. Continues
serving `/my:laravel-debug` and `/my:laravel-migration-check`.

## Phase 3: Confidence Rule (Rethought)

**Why `≥80` is wrong for review.** Flat numeric cutoff treats all issues
equally. But the cost of missing a finding scales with severity: a
"possible auth bypass, 60% confident" is worth surfacing; "variable name
could be clearer, 90% confident" is noise. Suppressing the first while
keeping the second is exactly backwards. It also pulls toward sycophancy
("if unsure, stay quiet") — the opposite of the anti-sycophancy framing
the agent already commits to.

**Severity-conditioned surfacing rule:**

Every potential issue gets:
- **Severity:** Critical / Warning / Suggestion
- **Confidence:** High (very likely real) / Medium (probably real, some
  ambiguity) / Low (worth a look, not certain)

Surface rule:

| Severity | Surface at confidence |
|---|---|
| Critical | Low or higher |
| Warning | Medium or higher |
| Suggestion | High only |

Rationale: critical findings are cheap to investigate and expensive to
miss, so a tentative one is still worth surfacing. Suggestions at low
confidence are pure noise. Warnings sit in the middle.

**Output shape:** every surfaced issue carries both labels (e.g.
`Critical / Low — possible auth bypass at AuthController.php:42`). The
reader sees the reasoning, not just the verdict.

**"Don't know" is a legal output.** When the reviewer cannot determine
whether something is an issue without more context (missing test fixture,
unclear caller intent), it says so explicitly in a "Needs Investigation"
section rather than suppressing or guessing. Anti-sycophancy applied to
uncertainty itself.

This replaces the existing qualitative H/M/L (which had no severity
coupling) and the proposed `≥80` cutoff (which had no severity coupling
either).

## Files to Modify/Create

**Create (in `my-plugin/skills/code-review/`):**
- `SKILL.md` — canonical skill: methodology, arg parsing
  (range/description/plan), language detection, range resolution
  (working-tree vs committed range), dispatch flow
- `code-reviewer-prompt.md` — dispatch template (anti-sycophancy
  directives, dual-perspective structure, reasoning paragraph requirement,
  severity-conditioned surfacing rule, optional plan-alignment block,
  placeholder for the language checklist, placeholder for the range
  payload)
- `checklists/generic.md` — 12-item default (extracted from current agent)
- `checklists/laravel.md` — Eloquent N+1, Blade XSS (`{!! !!}`), CSRF,
  policies/gates, Livewire `wire:*` patterns, queue jobs, validation
  rules, Pint/PHPStan, Vite asset bundling, accessibility
- `checklists/python.md` — type hints / mypy strictness, ruff conventions,
  async pitfalls (forgotten `await`, blocking calls in async), pytest
  coverage, exception breadth, dataclass/pydantic discipline, package
  boundaries
- `checklists/typescript.md` — `any` leaks / unsafe casts, React hooks
  rules (deps arrays, conditional hooks), async error propagation, ESLint
  + Prettier conventions, null/undefined narrowing, exhaustive switch
  checks

**Create (shim skills):**
- `my-plugin/skills/laravel-code-review/SKILL.md` — one paragraph,
  delegates to `my:code-review` with `language=laravel`
- `my-plugin/skills/python-code-review/SKILL.md` — same, `language=python`
- `my-plugin/skills/ts-code-review/SKILL.md` — same, `language=typescript`

**Modify:**
- `my-plugin/agents/code-reviewer.md` — strip methodology narrative and
  generic checklist (now in skill); keep anti-sycophancy directives,
  dual-perspective output schema, reasoning-paragraph requirement, output
  location. Replace flat-confidence section with severity-conditioned
  surfacing rule. Add "receives full review prompt from caller; do not
  improvise checklist if one is supplied."
- `~/.claude/CLAUDE.md` Code Review Routing table — convert `/my:`
  references from "command" framing to "skill" framing; add rows for
  Python and TypeScript; verify `feature-dev:code-reviewer` row absent;
  reassign the "committed range, pre-merge" row from
  `superpowers:requesting-code-review` to `my:code-review` with
  `range=BASE..HEAD` and (optional) `plan=<path>`; refresh
  disambiguation rule for language match precedence and add a note that
  `range` is the axis between working-tree and committed-range modes.

**Delete:**
- `my-plugin/commands/code-review.md` — superseded by skill
- `my-plugin/commands/laravel-code-review.md` — superseded by shim skill

**No change:**
- `my-plugin/agents/laravel-fullstack-expert.md` — keeps serving debug /
  migration-check commands

## Step-by-Step

Each step is a single commit on the `my-plugin` repo (the CLAUDE.md edit
is a separate commit on the global config). Smoke-test after each step.

1. Author canonical skill: create `skills/code-review/SKILL.md`,
   `code-reviewer-prompt.md`, and `checklists/generic.md`. Wire SKILL.md
   to detect language (default = generic for now), build prompt, dispatch
   `my:code-reviewer`. Working-tree range only at this step. Keep
   behaviour equivalent to current `/my:code-review` so the smoke test
   compares cleanly.
2. Refactor `my:code-reviewer` agent: strip moved content; replace
   confidence section with severity-conditioned rule; document the
   prompt-from-caller contract.
3. Smoke-test step 1+2 on a known-buggy diff (see Verification). Iterate
   on the agent and prompt template until the dual-perspective output is
   right.
4. Add range argument + plan-alignment block. Extend SKILL.md to parse
   `range=` (working-tree default; `BASE..HEAD` or two SHAs accepted),
   `description=`, `plan=`. Extend `code-reviewer-prompt.md` with an
   optional plan-alignment section that fires only when description or
   plan is supplied. Smoke-test on a committed range with a plan path
   (see Verification).
5. Add `checklists/laravel.md`. Create `skills/laravel-code-review/SKILL.md`
   shim. Smoke-test on a Laravel diff.
6. Add `checklists/python.md`. Create `skills/python-code-review/SKILL.md`
   shim. Smoke-test on a Python diff.
7. Add `checklists/typescript.md`. Create `skills/ts-code-review/SKILL.md`
   shim. Smoke-test on a TypeScript diff.
8. Update `~/.claude/CLAUDE.md` Code Review Routing table — including
   reassigning the committed-range row from
   `superpowers:requesting-code-review` to `my:code-review` with a
   range arg.
9. Delete obsolete `commands/code-review.md` and
   `commands/laravel-code-review.md`.

## Trade-Offs / Alternatives Considered

- **Single skill with internal language branching, no shim skills.**
  Cleanest internally, but loses discoverable per-language entry points
  the user explicitly asked for. Rejected.
- **Per-language skills with duplicated methodology (no canonical base).**
  No coupling, but methodology drifts across files over time. Rejected.
- **Keep command + agent architecture.** Doesn't address the user's
  preference for skills. Rejected.
- **Flat numeric confidence cutoff (≥80).** Feature-dev's design.
  Suppresses high-severity-low-confidence findings — wrong shape for
  review. Rejected in favour of severity-conditioned surfacing.
- **Leave `superpowers:requesting-code-review` running as a separate
  surface for committed ranges (option A).** Cheapest — no new args,
  no new skill flow. Cost: the discipline this plan invents
  (anti-sycophancy, dual-perspective, severity-conditioned confidence,
  "needs investigation") never reaches pre-merge review, which is the
  surface that fires most often. Rejected.
- **Treat `superpowers:requesting-code-review` as the canonical
  methodology and build shims around it (option C).** Inverts the
  consolidation. Cost: loses anti-sycophancy framing, dual-perspective
  output, and severity-conditioned confidence — exactly the
  differentiators motivating this plan. Rejected.
- **Chosen: extend `my:code-review` with a `range` arg covering both
  working-tree and committed-range modes (option B).** One methodology
  pre-commit and pre-merge; absorbs superpowers' plan-alignment check
  via optional `description` / `plan` args. Cost: bigger surface to
  design and smoke-test; walks away from an upstream skill the routing
  table previously relied on.

## Dependencies

None — all changes local to `~/.claude/CLAUDE.md` and the `my-plugin`
worktree. No new packages, no env vars.

## Testing Strategy

After step 1+2, the canonical skill should produce output equivalent to
the current `/my:code-review` on a known diff (modulo the new
severity-conditioned confidence labels). Each subsequent step adds one
language adapter; verify each independently.

End-to-end smoke tests:

- **Generic, working-tree range** (no project markers): plant an obvious
  bug + a debatable style choice in a small uncommitted diff. Run
  `my:code-review` with no args. Confirm dual-perspective tables,
  severity-conditioned surfacing (Critical-Low surfaces, Suggestion-Low
  does not), reasoning paragraph before verdict, output file at
  `$planDirectory/{feature}-review.md`.
- **Generic, committed range with plan-alignment:** on a small feature
  branch with 2–3 commits and an existing plan file, run `my:code-review`
  with `range=main..HEAD` and `plan=<path>`. Confirm the plan-alignment
  section fires, the diff is read from the committed range (not working
  tree), and the same severity rules and dual-perspective output apply.
- **Laravel:** in a Laravel repo, plant an N+1 (`->count()` in a loop)
  and a Blade `{!! $userInput !!}`. Run `my:laravel-code-review`. Confirm
  both surface as Critical or Warning at adequate confidence; confirm the
  Laravel checklist drove the finding, not the generic one.
- **Python:** in `diagoradisa-ml`, plant a missing `await` in an async
  path and a function lacking type hints. Run `my:python-code-review`.
  Confirm both flagged.
- **TypeScript:** plant an `any` cast and a React hook with missing deps.
  Run `my:ts-code-review`. Confirm both flagged.
- Confirm `feature-dev:code-reviewer` and
  `superpowers:requesting-code-review` are never auto-suggested across
  the above runs (the routing table should redirect both moments to
  `my:code-review`).
- Confirm "Needs Investigation" section appears when the diff lacks
  context to fully assess a finding.

## Risk

Low. Reverting is `git revert` on `my-plugin` plus a CLAUDE.md edit. No
shared state, no production code, no external services.

Specific risk: severity-conditioned surfacing is a behavioural change. On
the first run it may surface more low-confidence Critical findings than
the user expects. Mitigation: smoke-test on a known-buggy diff first; if
too noisy, narrow Critical to "Medium or higher" instead of "Low or
higher" before declaring the consolidation done.

Second risk: walking away from `superpowers:requesting-code-review`
means an upstream improvement to that skill won't reach our pre-merge
flow automatically. Mitigation: low cost — the upstream template is
~150 lines and changes rarely; on the rare upstream improvement, a
manual port into `code-reviewer-prompt.md` is straightforward and
keeps our methodology consistent.

## Open Questions

None remaining — all design choices resolved.
