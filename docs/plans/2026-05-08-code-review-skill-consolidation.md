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
seam produces one canonical review skill that loads a language-specific
content file at dispatch time.

**Resolved decisions:**
- Architecture: **single skill, internal language files** — one
  `my:code-review` skill with language content in
  `skills/code-review/language/{generic,laravel,python,typescript}.md`.
  No per-language shim skills. The canonical SKILL.md selects the
  language file based on an explicit `language=X` arg or
  project-marker auto-detection.
- Language coverage: **Laravel, Python, TypeScript**, plus generic.
- Discoverability of language modes: **auto-detection from project
  markers** (composer.json + artisan → laravel; pyproject.toml +
  uv.lock → python; package.json + tsconfig.json → typescript) with
  explicit `language=X` override. Trade-off accepted: the
  `/my:laravel-code-review` slash command goes away; users invoke
  `my:code-review` and auto-detection handles language selection.
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

## Phase 2: Single-Skill Architecture

One canonical skill owns methodology and dispatch. Language-specific
content lives in sibling files under `language/`. The actual review
still dispatches a subagent (fresh context, per
`superpowers:requesting-code-review` rationale), but the agent file
becomes a thin executor — discipline is authored once, in the canonical
skill.

### Components

**`my:code-review` (canonical and only review skill)** —
`my-plugin/skills/code-review/SKILL.md`
- Owns: methodology, anti-sycophancy framing, confidence rules,
  dual-perspective output, reasoning paragraph, output file location,
  language detection, range resolution, dispatch.
- References:
  - `language/generic.md` — language-agnostic 12-item checklist (default
    when no project markers match and no explicit `language=` is given)
  - `language/laravel.md` — Laravel checklist + Laravel-specific framing
  - `language/python.md` — Python checklist + Python-specific framing
  - `language/typescript.md` — TypeScript checklist + TS-specific framing
  - `code-reviewer-prompt.md` — the dispatch template (built from
    methodology + selected language file + range payload +
    optional plan-alignment block)
- Skill flow:
  1. Parse skill args: `range` (default = working tree; or
     `BASE..HEAD` / two SHAs / `since=<sha>`), `description` (optional —
     what was built), `plan` (optional — path to plan/spec/requirements),
     `language` (optional — overrides auto-detect). When `description`
     or `plan` is supplied, the dispatch prompt includes a "Plan
     alignment" check; otherwise that section is omitted.
  2. Resolve language: if `language=X` arg supplied use that. Otherwise
     auto-detect by project markers (`composer.json` + `artisan` →
     laravel; `pyproject.toml` + `uv.lock` → python; `package.json` +
     `tsconfig.json` → typescript). Fall back to generic.
  3. Load `language/<resolved>.md`
  4. Resolve git range: either capture working-tree diff (`git diff` +
     `git diff --staged` + untracked) or commit range
     (`git diff BASE..HEAD` + `git log BASE..HEAD --oneline`)
  5. Build dispatch prompt from `code-reviewer-prompt.md` + language
     file + range payload + (optional) plan-alignment block
  6. Dispatch `code-reviewer` subagent (the agent in this plugin) with
     the built prompt
  7. Surface the review output written to `$planDirectory/{feature}-review.md`

**`code-reviewer` (agent)** — refactor to lean executor. Anti-sycophancy
directives, dual-perspective output structure, reasoning-paragraph
requirement, output file location stay (these are how the agent renders
its work). The methodology *narrative* and all checklists move out to the
skill. The agent receives the full prompt (methodology + language file +
diff context) from the skill at dispatch time and must not re-fetch the
diff itself.

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
  (range/description/plan/language), language resolution, range
  resolution (working-tree vs committed range), dispatch flow
- `code-reviewer-prompt.md` — dispatch template (anti-sycophancy
  directives, dual-perspective structure, reasoning paragraph requirement,
  severity-conditioned surfacing rule, optional plan-alignment block,
  placeholder for the language file content, placeholder for the range
  payload)
- `language/generic.md` — language-agnostic 12-item checklist (extracted
  from current agent)
- `language/laravel.md` — Eloquent N+1, Blade XSS (`{!! !!}`), CSRF,
  policies/gates, Livewire `wire:*` patterns, queue jobs, validation
  rules, Pint/PHPStan, Vite asset bundling, accessibility
- `language/python.md` — type hints / mypy strictness, ruff conventions,
  async pitfalls (forgotten `await`, blocking calls in async), pytest
  coverage, exception breadth, dataclass/pydantic discipline, package
  boundaries
- `language/typescript.md` — `any` leaks / unsafe casts, React hooks
  rules (deps arrays, conditional hooks), async error propagation, ESLint
  + Prettier conventions, null/undefined narrowing, exhaustive switch
  checks

**Modify:**
- `my-plugin/agents/code-reviewer.md` — strip methodology narrative and
  generic checklist (now in skill); keep anti-sycophancy directives,
  dual-perspective output schema, reasoning-paragraph requirement, output
  location. Replace flat-confidence section with severity-conditioned
  surfacing rule. Add "receives full review prompt from caller including
  the diff payload; do not re-run `git diff` or improvise a checklist if
  one is supplied."
- `~/.claude/CLAUDE.md` Code Review Routing table — convert `/my:`
  references from "command" framing to "skill" framing; remove the
  Laravel-specific row (auto-detection makes it redundant); verify
  `feature-dev:code-reviewer` row absent; reassign the "committed range,
  pre-merge" row from `superpowers:requesting-code-review` to
  `my:code-review` with `range=BASE..HEAD` and (optional) `plan=<path>`;
  refresh disambiguation rule and add a note that `range` is the axis
  between working-tree and committed-range modes.

**Delete:**
- `my-plugin/commands/code-review.md` — superseded by skill
- `my-plugin/commands/laravel-code-review.md` — superseded; Laravel
  selection now via auto-detection or `language=laravel` arg on the
  canonical skill

**No change:**
- `my-plugin/agents/laravel-fullstack-expert.md` — keeps serving debug /
  migration-check commands

## Step-by-Step

Each step is a single commit on the worktree branch (the CLAUDE.md edit
is a separate commit on the global config). Smoke-test type per step is
noted in parentheses; types are defined in Testing Strategy.

1. Author canonical skill: create `skills/code-review/SKILL.md`,
   `code-reviewer-prompt.md`, and `language/generic.md`. Wire SKILL.md
   to resolve language (default = generic for now), build prompt,
   dispatch `code-reviewer` agent. Working-tree range only at this step.
   Keep behaviour equivalent to current `/my:code-review` so the
   integration smoke test compares cleanly. (smoke type: structural)
2. Refactor `code-reviewer` agent: strip moved content; replace
   qualitative-confidence section with severity-conditioned rule;
   document the prompt-from-caller contract (no self-fetched diff, no
   improvised checklist). (smoke type: structural)
3. Integration smoke-test of step 1+2 by manual placeholder
   substitution: read SKILL.md, capture diff payload by hand, build the
   dispatch prompt, dispatch `my:code-reviewer` agent. Validates the
   agent contract and prompt template shape. **Cannot validate the
   skill's own instructions** (language detection, untracked-file diff
   synthesis, absolute-path resolution, mkdir, slug computation) —
   those execute when Claude reads SKILL.md, which only happens in a
   fresh session. (smoke type: in-session manual dispatch)
4. **Delete obsolete commands now, not at the end.** Remove
   `commands/code-review.md` and `commands/laravel-code-review.md`.
   Reason: while the command file exists with the same plugin-prefixed
   name, `/my:code-review` resolves to the **command**, not the skill —
   the command's body gets injected as a user prompt and the new skill
   never runs. Discovered during step 3 by invoking
   `Skill(skill="my:code-review")` and observing the command body
   echoed. After deletion `/my:code-review` should resolve to the skill;
   verify in a fresh session as part of step 7. (smoke type: deferred
   to fresh-session validation)
5. Add range argument + plan-alignment block. Extend SKILL.md to parse
   skill args. Use **content-shape classification**, not a rigid
   `key=value` grammar — Claude is the runtime, so let it classify the
   freeform args string by shape: a `BASE..HEAD` literal or two SHAs is
   the `range`; a path ending in `.md` is the `plan`; the words
   `laravel` / `python` / `typescript` are the `language`; remaining
   prose is the `description`. Extend `code-reviewer-prompt.md` with an
   optional plan-alignment section that fires only when description or
   plan is supplied. (smoke type: structural; deferred fresh-session
   integration test)
6. Add language files in parallel: `language/laravel.md`,
   `language/python.md`, `language/typescript.md`. Each extends
   `language/generic.md` with language-specific items per the
   descriptions in "Files to Modify/Create". Authoring is independent
   across languages — fan out to parallel subagents (one per language).
   (smoke type: structural per file)
7. Update `~/.claude/CLAUDE.md` Code Review Routing table — drop the
   Laravel row (auto-detect handles it), reassign the committed-range
   row from `superpowers:requesting-code-review` to `my:code-review`
   with a range arg, and convert `/my:code-review` framing to skill
   framing. **Final fresh-session validation:** in a new Claude Code
   session, invoke `my:code-review` and confirm the skill (not the
   deleted command) actually runs through its full flow — language
   detection, diff capture, dispatch, file write to the correct
   `docs/plans/`. Then run the real-repo smoke tests from Testing
   Strategy. (smoke type: real-repo end-user, in fresh session)

## Trade-Offs / Alternatives Considered

- **Chosen: single skill with internal language files
  (`language/{generic,laravel,python,typescript}.md`).** Auto-detection
  from project markers selects the language file at dispatch; explicit
  `language=X` arg overrides. One skill, one methodology, one place to
  evolve discipline. Cost: the `/my:laravel-code-review` slash command
  goes away; users discover Laravel mode via auto-detection rather than
  a named entry point.
- **Per-language shim skills (`my:laravel-code-review`,
  `my:python-code-review`, `my:ts-code-review`) wrapping a canonical
  base skill.** Discoverable per-language entry points; explicit
  trigger names. Cost: four skills instead of one; "delegation" is just
  Claude reading two SKILL.md files in sequence, which adds friction
  without adding capability. Rejected — auto-detection covers the
  discoverability need.
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
- **Range axis: extend `my:code-review` with a `range` arg covering
  both working-tree and committed-range modes (option B).** One
  methodology pre-commit and pre-merge; absorbs superpowers'
  plan-alignment check via optional `description` / `plan` args.
  Chosen.

## Dependencies

None — all changes local to `~/.claude/CLAUDE.md` and the `my-plugin`
worktree. No new packages, no env vars.

## Testing Strategy

Three smoke-test types are referenced by the step list:

- **Structural** (cheap, fastest, runs after most steps): the file
  parses as YAML/markdown, frontmatter validates, all referenced sibling
  files exist. No skill invocation. Run via `ls`/`grep`/inspection.
- **In-session integration** (after step 3 and step 4): invoke
  `my:code-review` via the Skill tool in this session, against a
  planted-bug working-tree diff (step 3) or committed range with a plan
  path (step 4). Compare output against expectations below.
- **Real-repo end-user** (after step 6): user invokes the skill in a
  real Laravel/Python/TS project in a separate session and inspects
  output. This is the only test that truly verifies auto-detection and
  language-file selection in the wild.

Expectations the integration smoke tests must confirm:

- **Generic, working-tree range** (after step 3, no project markers):
  plant an obvious bug + a debatable style choice in a small
  uncommitted diff. Invoke `my:code-review` with no args. Confirm
  dual-perspective tables render, severity-conditioned surfacing works
  (Critical-Low surfaces, Suggestion-Low does not), reasoning paragraph
  appears before verdict, output file lands at
  `$planDirectory/{feature}-review.md`, and "Needs Investigation"
  section appears when the diff lacks context.
- **Generic, committed range with plan-alignment** (after step 4): on
  a small feature branch with 2–3 commits and an existing plan file,
  invoke `my:code-review` with `range=main..HEAD` and `plan=<path>`.
  Confirm the plan-alignment section fires, the diff is read from the
  committed range (not working tree), and the same severity rules and
  dual-perspective output apply.

Expectations for the real-repo end-user tests after step 6 (you invoke
in a fresh session):

- **Laravel:** in a Laravel repo, plant an N+1 (`->count()` in a loop)
  and a Blade `{!! $userInput !!}`. Run `my:code-review`. Confirm
  auto-detection picks Laravel, both findings surface as Critical or
  Warning at adequate confidence, and the Laravel-specific checklist
  drove them (not the generic one).
- **Python:** in a Python repo (e.g. `diagoradisa-ml`), plant a
  missing `await` in an async path and a function lacking type hints.
  Run `my:code-review`. Confirm auto-detection picks Python and both
  are flagged.
- **TypeScript:** in a TS repo, plant an `any` cast and a React hook
  with missing deps. Run `my:code-review`. Confirm auto-detection
  picks TypeScript and both are flagged.
- **Override path:** in any project, run `my:code-review language=python`
  on a non-Python file (e.g. a README) — confirm the override forces
  the Python language file even when auto-detection would pick
  something else.
- Across all real-repo runs, confirm `feature-dev:code-reviewer` and
  `superpowers:requesting-code-review` are never auto-suggested.

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

Third risk: losing the `/my:laravel-code-review` named entry point may
hurt discoverability — a user searching available skills for "laravel"
will only find debug/migration-check skills. Mitigation: the canonical
skill's `description:` frontmatter should explicitly mention "auto-detects
Laravel/Python/TypeScript" so the unified skill still appears for
language-keyword searches. If discoverability turns out to matter more
than expected, the shim-skill option remains available — it's an
additive change, not a redesign.

## Open Questions

None remaining — all design choices resolved.
