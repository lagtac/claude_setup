# Spec: plan-review mode for `my:code-review`

## How to read this spec

This spec is self-contained: a session with no prior context can write and execute an
implementation plan from it alone. Related material, in reading order:

1. `my-plugin/skills/code-review/SKILL.md` — the skill orchestrator being modified. Today it
   parses args, captures a diff, builds a dispatch prompt, dispatches the reviewer subagent,
   and surfaces the result. **Mode selection is added here.**
2. `my-plugin/skills/code-review/code-reviewer-prompt.md` — the dispatch-prompt template. The
   skill substitutes placeholders into it before dispatch. **Gains generalized placeholders.**
3. `my-plugin/agents/code-reviewer.md` — the `my:code-reviewer` subagent (Opus). Lean executor
   that reads the assembled prompt and writes the review file. **Contract is generalized.**
4. `docs/plans/2026-05-28-slim-code-review-skill.md` — the immediately-preceding change that
   slimmed this skill from a bug-scanner to a judgment + plan-alignment reviewer. Explains why
   today's criteria are "judgment dimensions" and why bug-finding is delegated to the built-in
   `/code-review`.
5. `GLOBAL-CLAUDE.md` (this repo; symlinked as `~/.claude/CLAUDE.md`) — its "Code Review
   Routing" section documents when to use `my:code-review`. A plan-review row is added.
6. `README.md` — the `/my:code-review` one-line description; updated to mention plan-review.

Repo root for all paths: `/home/dchris/projects/claude-setup`.

## Context

**Problem.** `my:code-review` reviews a *diff*. When the user passes a `.md` plan path, that
path is only used as an *alignment reference* — the reviewer compares an existing diff against
the plan. There is no mode where the **plan document itself is the subject** of review. Today,
running `/my:code-review docs/plans/foo.md` against a clean working tree hits SKILL.md's
empty-diff guard and bails with `No changes to review.` — the plan is never reviewed.

**Why this matters.** The user authors superpowers-style specs and plans that contain real
inline code (Red→Green→Refactor test bodies, implementation snippets, commit breakdowns).
Reviewing a plan *before* writing code catches unsound sequencing, inadequate test strategy,
stale assumptions, and snippet logic errors early — before a wasted implementation cycle. The
review that matters for a plan is a **judgment + grounding** review, not a line-level bug scan;
the slimmed `my:code-review` judgment machinery is the right fit.

**Decided design (settled in brainstorming).**
- **Trigger: auto by empty diff.** A `.md` plan path + an empty diff payload ⇒ plan-review
  (subject = the plan). A non-empty diff ⇒ today's diff+alignment behavior, with a printed
  nudge so the choice is never silent.
- **Scope: grounded.** The reviewer reads the plan *and* the repo source it references, and
  verifies the plan's claims hold.
- **Structure: one skill, branched prompt.** `my:code-review` stays the single entry point.
  The same prompt template and the same `my:code-reviewer` agent serve both modes; the skill
  substitutes a mode-specific subject, criteria, and output subsection. No new files.

## Behaviour specification

### Mode detection (in SKILL.md, after the diff is captured)

`PLAN_PATH` is the existing arg variable: a `.md` path that exists on disk (SKILL.md step 0).
The "payload" is the captured diff (working-tree or `BASE..HEAD` range).

| `PLAN_PATH` | Payload | `MODE` | Behaviour |
|---|---|---|---|
| set | empty | **plan-review** | Subject = the plan document. `RANGE`, if any, is ignored. |
| set | non-empty | **diff-review (alignment)** | Today's behaviour + print the nudge below. |
| unset | empty | — | Bail as today: `No changes to review.` / `Range <RANGE> is empty.` |
| unset | non-empty | **diff-review** | Today's plain diff review. |

**Nudge (printed to the user, not to the reviewer) when `PLAN_PATH` set + non-empty diff:**

> `(Working tree is dirty, so I'm reviewing the diff against <PLAN_PATH>. Commit or stash to review the plan document itself.)`

### Subject assembly

The skill fills the `{{SUBJECT}}` placeholder (body of the prompt's `## Subject Under Review`
section):

- **diff-review:** `The combined diff to review:` + a fenced ` ```diff ` block with the payload.
- **plan-review:** `The plan document to review (\`<PLAN_PATH>\`):` + a fenced ` ```markdown `
  block containing the **full** plan file contents.

### Criteria

The skill fills the `{{CRITERIA}}` placeholder (body of the prompt's `## Judgment Dimensions`
section) with one of two verbatim blocks.

**diff-review `{{CRITERIA}}` (unchanged — this is today's hardcoded Judgment Dimensions body):**

> Assess the change against these soundness dimensions — **not** a line-level bug scan. Mark
> genuinely-inapplicable dimensions as **N/A** with a one-line reason in the dual-perspective
> tables — do not silently skip.
>
> 1. **Solves the stated problem.** …
> 2. **Architecture & pattern fit.** …
> 3. **Soundness of approach.** …
> 4. **Risk & blast radius.** …
> 5. **Plan alignment.** When a `## Plan Alignment` block was supplied above, treat every
>    deviation between the diff and the plan as a finding.
>
> **Out of scope — do not duplicate the built-in reviewer.** Low-level bug-finding … is the
> job of the built-in `/code-review`. …

*(The full current text lives in `code-reviewer-prompt.md` lines 36–44; preserve it verbatim
when extracting it into the substitution.)*

**plan-review `{{CRITERIA}}` (new — verbatim):**

> Assess the plan against these dimensions — judge whether it is **ready to implement**, not
> whether its code snippets compile. Mark genuinely-inapplicable dimensions as **N/A** with a
> one-line reason in the dual-perspective tables — do not silently skip.
>
> 1. **Completeness & snippet self-sufficiency.** The plan covers the whole stated goal: no
>    missing steps, unhandled cases, or undefined terms. A cold session could execute it
>    without inventing requirements. This explicitly includes the snippets: any snippet meant
>    to be executed (copied into a file or run) must be runnable without the executor inventing
>    imports, helpers, fixtures, or symbols the plan never establishes in an earlier step. A
>    genuine omission — e.g. a snippet that references an import or helper the plan never
>    defines — is a **completeness finding** (it forces the executor to guess), distinct from a
>    *clearly-marked elision* (see dimension 6), which is fine.
> 2. **Sequencing & atomicity.** Steps are ordered so dependencies land before dependents;
>    each step is a coherent, single-purpose commit. Where the plan implements behaviour, it
>    follows Red → Green → Refactor (tests before implementation), per the project's plan
>    standard.
> 3. **Test-strategy adequacy.** The planned tests actually pin the intended behaviour, at the
>    right level (unit / feature / integration), and would fail for the right reason before the
>    implementation exists. Flag tests that assert nothing meaningful or mock the code under test.
> 4. **Risk & reversibility.** Hard-to-reverse steps (schema changes, API/data contracts,
>    migrations, deletions) are identified with a mitigation or rollback note; blast radius is
>    named. Flag unflagged irreversible steps.
> 5. **Grounding (verify against the repo).** Use Read / Grep / Glob to confirm the plan's
>    claims: referenced files, symbols, routes, and commands exist; stated assumptions about
>    current behaviour hold; proposed patterns match existing conventions. Every stale reference
>    or false assumption is a finding citing `plan-section` ↔ `repo file:line` (or "(not found)").
> 6. **Snippet logic.** Inspect embedded test/implementation snippets for **logic** errors only:
>    off-by-ones, a test asserting the wrong thing, a snippet that cannot achieve its step's
>    stated goal, contradictory snippets across steps. **Out of scope:** snippets the plan
>    *clearly marks as abbreviated* (`…`, "imports omitted", "sketch"), and pure formatting/style.
>    Do **not** flag those, and do **not** run a lint/type/style pass — that is the built-in
>    `/code-review`'s job on real code. Note the boundary with dimension 1: a *clearly-marked
>    elision* is fine here, but a snippet presented as executable that omits an import/helper the
>    plan never defines is a completeness finding under dimension 1 — because a cold executor
>    would be forced to invent it. The test is "would the executor have to guess?", not "is a
>    line missing".

### Explicit mode signal

To avoid reviewer guesswork, the skill writes a literal `**Review mode:** plan-review` or
`**Review mode:** diff-review` line near the top of the dispatch prompt (recommended: a
`{{MODE}}` placeholder, or skill-written literal text). The agent keys its scope behaviour off
this line (see agent contract).

### Output

The dual-perspective schema, severity-conditioned surfacing, `Issues Surfaced`,
`Needs Investigation`, `Reasoning`, and `Verdict` sections are **shared, unchanged**. Only the
optional second subsection varies, filled via a `{{MODE_OUTPUT_SECTION}}` placeholder that
replaces the prompt's current static `### Plan Alignment` output block:

- **diff-review (alignment):** the current `### Plan Alignment` output block (verbatim).
- **plan-review:** a `### Grounding` block:
  > State whether the plan's references and assumptions hold against the repo. Enumerate each
  > stale reference / false assumption as a bullet citing the plan location ↔ `repo file:line`
  > (or "(not found)"). Surface material ones as findings in the Issues table. Omit if the plan
  > made no checkable claims.
- **plain diff-review:** empty string.

**Verdict semantics in plan-review:** `Assessment` stays `Sound` / `Problematic` / `Mixed`,
read as — Sound = ready to implement as written; Problematic = do not implement until fixed;
Mixed = implementable with the noted changes. `Recommendation` must be actionable (e.g.,
"fix steps 3 and 5, then implement").

**Output file slug (`{{REVIEW_SLUG}}`):**
- diff-review: unchanged — `<YYYY-MM-DD>-<branch-or-cwd>-review`.
- plan-review: `<plan-basename-without-.md>-plan-review`. Example: plan
  `docs/plans/2026-05-28-foo.md` → review `docs/plans/2026-05-28-foo-plan-review.md`. This keeps
  the plan review beside its plan and avoids colliding with the branch-based diff-review name.

### Prompt template changes (`code-reviewer-prompt.md`)

- Replace the hardcoded `## Judgment Dimensions` body with `{{CRITERIA}}` (keep the heading so
  the agent's section check still matches).
- Rename the `## Diff Payload` section to `## Subject Under Review` with body `{{SUBJECT}}`.
- Replace the static `### Plan Alignment` output block with `{{MODE_OUTPUT_SECTION}}`.
- Generalize the "What to Review" prose so it is subject-neutral and defers scope to the mode:
  diff-review stays within the payload (Read/Grep only to assess a finding's context);
  plan-review actively grounds the plan against the repo.
- Add the `**Review mode:**` line near the top.
- Retain `{{PLAN_ALIGNMENT}}`, `{{PLAN_DIRECTORY}}`, `{{REVIEW_SLUG}}`. In plan-review,
  `{{PLAN_ALIGNMENT}}` = empty string.

### Agent contract changes (`code-reviewer.md`)

- Generalize section names: the malformed-prompt check requires `## Subject Under Review`,
  `## Judgment Dimensions`, `## Output Structure` (was `## Diff Payload`).
- Make the scope rule mode-aware, keyed off the `**Review mode:**` line: in **plan-review**,
  actively use Read/Grep/Glob to ground-check the plan's claims against the repo — this is in
  scope and expected; in **diff-review**, do not widen beyond the payload (Read/Grep only to
  assess a finding's context).
- Keep the "render a soundness judgment, not a line-level bug scan" framing for both; add that
  in plan-review the agent also grounds the plan and sanity-checks snippet logic (logic only).
- The "do not re-capture the subject" rule generalizes from "do not re-run git diff" to also
  "do not re-read the plan from disk — the skill embedded it."

### Documentation changes (scope)

- `README.md`: update the `/my:code-review` row to mention plan-review (e.g. "… or review a
  plan/spec document before coding").
- `GLOBAL-CLAUDE.md` "Code Review Routing": add a row — *Review an implementation plan/spec
  before coding → `my:code-review <plan>.md` (clean tree)*. **Note:** editing `GLOBAL-CLAUDE.md`
  (live-symlinked to `~/.claude/CLAUDE.md`) trips the auto-mode self-modification guardrail and
  needs explicit user authorization at implementation time.

## Visual Language

N/A — this is a CLI/skill behaviour change with no UI surface.

## Trade-offs / alternatives considered

- **Trigger — auto by empty diff (chosen)** vs. explicit `plan` keyword vs. auto+keyword.
  Chosen: zero new syntax, matches the natural "review my plan before I code" moment. Accepted
  cost: when the tree is dirty *and* the user wants the plan reviewed, the skill picks alignment
  — mitigated by the printed nudge.
- **Scope — grounded (chosen)** vs. internal-only. Grounded catches stale file/symbol
  references and false assumptions, which is where plans most often rot. Cost: slower, the agent
  must explore the repo.
- **Structure — one skill, branched prompt (chosen)** vs. second prompt file vs. separate
  `my:plan-review` skill. Chosen: smallest surface, shared judgment machinery, one "review"
  mental model. Cost: the prompt template carries mode-conditional placeholders.

## Dependencies

None. No new packages, config, or files. The `my:code-reviewer` agent already has
Read/Grep/Glob/Bash/Write — sufficient for grounding.

## Risk

- **False positives on partial snippets** — the central failure mode. Mitigated by the
  "would the executor have to guess?" test: dimension 6 ignores clearly-marked elisions and
  runs no lint/type/style pass, while dimension 1 flags genuine omissions (an undefined
  import/helper the plan never establishes) as completeness gaps. The line is intent
  (abbreviation) vs. defect (omission), not "is a line missing".
- **Mode misfire** — a dirty tree silently doing alignment instead of plan-review. Mitigated by
  the printed nudge.
- **Behaviour change is plugin-wide** — affects `my:code-review` in every project. Plan-review
  is purely additive (new branch on empty-diff + plan); diff-review behaviour is unchanged.
- **`GLOBAL-CLAUDE.md` edit** — global blast radius + guardrail; isolated to one routing row,
  done only with user authorization.
- Reversible: all changes are markdown skill content; the pre-change state is on `main` history
  and the retained `slim-code-review` branch lineage.

## Open questions

None outstanding — trigger, scope, structure, criteria, output, and slug are all decided above.
