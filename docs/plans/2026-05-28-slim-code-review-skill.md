# Slim `my:code-review` to its differentiator

## Context

The built-in `/code-review` (effort levels, `ultra` cloud, `--fix`, `--comment`) is a more
capable, zero-maintenance, first-party bug-finder that can also *act* on its findings. An
audit showed `my:code-review`'s value was mostly redundant with it — the language checklists
(`laravel.md` 16 items, `generic.md` 12 items) were almost entirely bug-finding/quality-gate
items (secrets, N+1, input validation, test coverage, performance) the built-in already covers.

The plugin's only durable advantages: **dual-perspective soundness judgment**, **plan/spec
alignment**, and a **durable dated report in `docs/plans/`**. Decision: slim to those; route
raw bug-finding/fixing/`ultra` to the built-in `/code-review`.

A true wrapper is impossible — the built-in is opaque (compiled in, not on disk) and Claude
Code skills cannot capture another skill's output. The two tools stay separate; coordination
is a routing rule, not orchestration.

## Changes shipped (commit `f1fb0c1` on `main`)

- **`my-plugin/skills/code-review/code-reviewer-prompt.md`** — replaced the `{{LANGUAGE_FILE}}`
  checklist with a fixed **`## Judgment Dimensions`** section (intent, architecture fit,
  soundness of approach, risk, plan-alignment) plus an explicit out-of-scope note delegating
  low-level bug-finding to the built-in. Anti-sycophancy, severity-conditioned surfacing,
  plan-alignment, and dual-perspective output schema unchanged.
- **`my-plugin/skills/code-review/SKILL.md`** — removed language detection and the
  `LANGUAGE_OVERRIDE` arg; dropped `{{LANGUAGE_FILE}}` substitution; rewrote the frontmatter
  description and worked example. Retained `RANGE` / `PLAN_PATH` / `DESCRIPTION` parsing, diff
  capture, dispatch, surface.
- **`my-plugin/agents/code-reviewer.md`** — lean-executor contract now references
  `## Judgment Dimensions` instead of `## Checklist`; soundness-judgment framing.
- **Deleted** `my-plugin/skills/code-review/language/` (generic, laravel, python, typescript).
- **`README.md`** — updated the `/my:code-review` row.

Integration: worktree `slim-code-review` (retained), squash-merged to `main`, worktree removed.

## Trade-offs

- **Slim (chosen)** — keeps the genuine differentiator, sheds duplicated checklists. Loses the
  explicit secrets/validation/N+1 line-items from the plugin path (now the built-in's job —
  the point of the change).
- Retire entirely — rejected; loses plan-alignment + `docs/plans/` report.
- Dispatcher skill — rejected; over-engineered, depends on 4.7 chaining mid-skill.

## Outstanding

- **Global instructions routing edit — NOT YET APPLIED.** The Code Review Routing section in
  the live `~/.claude/CLAUDE.md` still claims `my:code-review` auto-detects Laravel/Python/
  TypeScript. It needs rewriting to: (a) reframe `my:code-review` as judgment + plan-alignment,
  (b) add the built-in `/code-review` as the bug-finder / `--fix` / `ultra` surface, (c) drop
  the language-detection claims. The edit was blocked by the auto-mode self-modification
  guardrail and awaits explicit user authorization. The repo source copy (`GLOBAL-CLAUDE.md`,
  formerly `_CLAUDE.md-copytohomeclaudedir`, mid-rename in the user's working tree) does **not**
  contain the routing section, so this fix targets the live file only.

## Verification

- `grep -rn "LANGUAGE_FILE\|LANGUAGE_OVERRIDE\|skills/code-review/language" my-plugin/` on
  `main` → empty (passed).
- `ls my-plugin/skills/code-review/language/` → no such directory (passed).
- Fresh-session functional test (pending — skill metadata loads at session start): run
  `/my:code-review` on a small diff, confirm a dual-perspective + verdict report lands in
  `docs/plans/` with no language-checklist line items; and `/my:code-review <spec>.md`
  populates a `### Plan Alignment` section.
