# Single-source the planning standards via a shared file (runtime-read)

## Context

The planning discipline (Critical Thinking, Mandatory Exploration, Simplicity, Trade-Off, Risk,
Test Standards, Plan Output Format) is **duplicated** between two files in `~/projects/claude-setup`:

- `GLOBAL-CLAUDE.md:138-203` — governs all **main-context** planning (built-in plan mode, `/my:task`, Superpowers brainstorming/writing-plans, inline planning).
- `my-plugin/agents/planner.md:14-104` — governs the `my:planner` **subagent** (invoked via `/my:plan`).

Both copies are hand-synced. They exist because the two execution contexts are isolated: the main
context always loads `GLOBAL-CLAUDE.md` but never the agent file; the planner subagent does **not**
inherit `CLAUDE.md` (`planner.md:12`) and cannot expand `@imports`. Verified against the docs:
`@file` imports expand **only** in CLAUDE.md memory files — agent/skill files load verbatim. So the
standards cannot be *relocated*, only *shared*.

**Goal:** one canonical `planning-standards.md`. `GLOBAL-CLAUDE.md` pulls it via `@import`; the
planner subagent (which has the `Read` tool) reads it at runtime as its mandatory first step. After
this, editing the standards is a one-file change.

## Files to Modify/Create

1. **CREATE `~/projects/claude-setup/shared/planning-standards.md`** — the canonical, context-neutral
   discipline (the *union/best-of-both* of the two current copies). Sections, in order:
   - *Verify against ground truth* (from `GLOBAL-CLAUDE.md:142`)
   - *Critical Thinking* (union of `GLOBAL:144-150` + `planner:14-20`)
   - *Mandatory Exploration* — the **built-in 5-step only** (`GLOBAL:158-166`) plus planner's
     "do all five / show your reasoning in 2-4 sentences" emphasis (`planner:24,32`). **The gkg
     step-0 stays OUT** (context-specific — the planner has no gkg/mcp tools; only Read/Grep/Glob/Bash).
   - *Reference Sweep* (`GLOBAL:168-170`)
   - *Simplicity Rules* (union)
   - *Trade-Off Analysis* (union + planner's "skip if trivial" clause `planner:49`)
   - *Risk Awareness* (union)
   - *Test Standards* (`GLOBAL:195-199`)
   - *Plan Output Format* — the **full template** currently at `planner.md:69-97`.
   - Lead line: "Canonical planning discipline. Imported by `GLOBAL-CLAUDE.md` and read at runtime
     by the `my:planner` agent. Edit here only."

2. **EDIT `~/projects/claude-setup/GLOBAL-CLAUDE.md`** (real file; `~/.claude/CLAUDE.md` symlinks to it).
   Replace the duplicated subsections (`144-203`) with:
   - keep the preamble (`138-140`, "applies to all planning workflows");
   - a short **gkg-first wrapper**: "Step 0: map structure with gkg mcp tools first (announce it);
     if unavailable, use the built-in exploration steps in the imported standards below";
   - the import line: `@~/projects/claude-setup/shared/planning-standards.md`
     (home/absolute path — **not** relative: the symlinked CLAUDE.md resolves relative imports
     against `~/.claude/`, so relative would break).
   - This also **supersedes** the earlier line-203 patch (the `planner.md` canonical-copy pointer
     becomes moot — the shared file is now canonical). Note: `GLOBAL-CLAUDE.md` already has one
     uncommitted edit (that line-203 patch); fold it into this change.

3. **EDIT `~/projects/claude-setup/my-plugin/agents/planner.md`**. Replace the duplicated discipline
   (`14-58` and `69-97`) with a mandatory load step; keep agent-specific parts:
   - Rewrite `:12` — from "self-contained, does not inherit CLAUDE.md" to "runs in an isolated
     subagent context (no CLAUDE.md inheritance), so it loads its discipline from the shared
     standards file in Step 0 below."
   - **Step 0 — Load standards (place FIRST in the prompt body, above persona/Execution/Output
     Discipline):** "Before anything else, `Read`
     `~/projects/claude-setup/shared/planning-standards.md` and follow every section. If the file is
     missing, **halt and report** — do not plan without the standards." (No fallback copy — that
     would re-introduce duplication.) Ordering matters: Step 0 must precede the agent-specific
     sections so the model loads discipline before acting on Execution.
   - Keep *Execution* (`60-67`) and *Output Discipline* (`99-104`); adjust Execution step to point
     at the loaded standards rather than inline sections, and **add a final Execution step**:
     "before emitting the plan, re-check it against every section of the standards file" — a guard
     against the model drifting from a file it read at the start of the turn.

4. **EDIT `~/projects/claude-setup/my-plugin/skills/tune-claude-instructions/SKILL.md`** (~`:129`).
   That skill currently states agents **must embed** standards because subagents lack CLAUDE.md
   context — a rule it audits other agents against. This refactor establishes the *opposite* pattern
   for the planner. Update the skill to record runtime-read (read a shared file as a mandatory first
   step) as an **allowed alternative** to embedding, so the planner doesn't fail the user's own audit.

## Step-by-Step Implementation

1. Create `shared/planning-standards.md` by assembling the union content above. Diff its sections
   against the two originals to confirm **no discipline is dropped**.
2. Edit `planner.md`: insert Step 0, rewrite `:12`, delete the now-shared sections, keep
   Execution + Output Discipline.
3. Edit `GLOBAL-CLAUDE.md`: insert gkg wrapper + `@import` line, delete shared subsections, remove
   the stale Plan-Output-Format pointer.
4. Verify (below). Squash-merge to `main` as one commit:
   `refactor(planning): single-source planning standards via shared file`.

## Trade-Offs / Alternatives Considered

- **Runtime-read (chosen)** — one canonical file; `GLOBAL` imports it, planner reads it. No build
  tooling, files stay hand-editable. Cons: planner gains a runtime file dependency (a hardcoded
  absolute path) it previously avoided by being self-contained.
- **Build-step generation** — splice a partial into both files via a generate script + pre-commit
  guard. Strongest dedup but adds tooling and makes both files generated artifacts. Rejected as
  over-engineered for two files.
- **Drift-guard only** (keep both copies + a divergence test) — no single source. Rejected: user
  wants one source.

## Dependencies

None. Uses the existing CLAUDE.md `@import` feature and the planner's existing `Read` tool. No new
packages.

## Risk

- **Reliability regression (the headline trade-off, not the path).** Today the planner's discipline
  lives in its system prompt — *guaranteed loaded* every turn. After this change it lives in a file
  the model must (a) actually read in Step 0 and (b) keep following while drafting later sections.
  Both are LLM-behavioral, not deterministic: it could skip the read, or read it and drift by the
  time it writes Open Questions. This is the genuine cost of runtime-read. Mitigations baked into
  the design: Step 0 is placed **first** in the prompt body, and a final Execution step re-checks
  the draft against the standards. Residual risk remains — accept it as the price of single-source,
  or fall back to "drift-guard only" (keep the embedded copy + a divergence test).
- **Hardcoded absolute path** in `planner.md` (no `${CLAUDE_PLUGIN_ROOT}` exists for subagents,
  confirmed). Breaks if the repo is moved/renamed or used on another machine. Acceptable for a
  personal config repo; documented in the file. Detect: planner's Step-0 halt-and-report fires.
- **Behavior change (intended), flag for sign-off:** the planner currently lacks *Reference Sweep*
  and *Test Standards*; pointing it at the full shared file **adds** them. This makes the planner
  more rigorous and consistent with `GLOBAL` — desired, but it *is* a change to planner behavior.
- **Always-loaded context grows ~25 lines** in `GLOBAL-CLAUDE.md` (the full Plan Output Format
  template is now imported inline instead of a names+pointer). Net the section still shrinks
  (~60 duplicated lines removed). Acceptable.
- **Import path through a symlink** — mitigated by using the home/absolute form, not relative.
- Reversible: revert the commit; the two inline copies return.

## Testing Strategy

Read-only rehearsal (run during execution, not plan mode):

1. **Import resolves:** fresh `claude` session → `/memory` → confirm `shared/planning-standards.md`
   appears in the loaded import tree (proves `@~/...` resolved through the symlink).
2. **Subagent reads it:** `/my:plan "<trivial task>"` → confirm the planner announces reading the
   standards and its output contains every required section (incl. the full Plan Output Format and
   Reference-Sweep behavior) → proves runtime read works.
3. **Single-source assertion:** `grep -n "Critical Thinking\|Mandatory Exploration\|Trade-Off"`
   both `GLOBAL-CLAUDE.md` and `planner.md` → only the import line / the Step-0 read directive
   should remain; no duplicated subsection bodies.
4. **No content lost:** diff the new `shared/` file against the pre-refactor union of the two
   copies; every prior rule must be present.

## Open Questions

1. **Shared-file location** — plan assumes repo-root `shared/planning-standards.md`. Alternatives:
   `GLOBAL-rules/` (currently for path-scoped lazy rules — different purpose) or `my-plugin/shared/`.
   OK with repo-root `shared/`?
2. **Scope** — `commands/task.md` (`/my:task`) is currently independent of these standards. Leave it
   out of this refactor? (Recommended: yes, out of scope.)
3. Confirm the intended planner enrichment (gaining Reference Sweep + Test Standards) is wanted.
4. **GLOBAL leanness** — inlining the full Plan Output Format template via import adds ~25 lines to
   always-loaded context, which cuts against the user's lean-context pattern (`.claude/rules`
   lazy-load, the old names+pointer). Alternative: **two shared files** — `planning-standards.md`
   (discipline) + `plan-output-format.md` (template); `GLOBAL` imports only the discipline and keeps
   its names+pointer, the planner reads both. Keep one file (simpler) or split for leanness?
