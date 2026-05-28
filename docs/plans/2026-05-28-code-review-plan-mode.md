# Plan-Review Mode for `my:code-review` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a plan-review mode to `my:code-review` so that pointing it at a `.md` plan with a clean working tree reviews the plan itself (grounded against the repo + snippet-logic check), reusing the existing reviewer prompt and agent via mode-branched placeholders.

**Architecture:** One skill, branched prompt. `SKILL.md` selects `MODE` (plan-review when a `.md` plan is given and the diff is empty; otherwise diff-review), assembles a mode-specific subject, criteria, and output subsection, and substitutes them into a generalized `code-reviewer-prompt.md`. The same `my:code-reviewer` agent serves both modes.

**Tech Stack:** Markdown skill/prompt/agent files in `my-plugin/`. Verification is grep-based structural assertions + a manual functional smoke test (no code test harness exists for prompt content).

**Spec:** `docs/plans/2026-05-28-code-review-plan-mode-spec.md` (read it — this plan implements it verbatim).

**Execution note:** Per the project git workflow this is multi-commit work → do it in a worktree created via `superpowers:using-git-worktrees` (e.g. `git worktree add .claude/worktrees/code-review-plan-mode -b code-review-plan-mode`). Squash-merge to `main` at the end; keep the branch; remove the worktree.

---

### Task 1: Generalize the dispatch-prompt template

Turn `code-reviewer-prompt.md` into a mode-agnostic template: a `**Review mode:**` line, a generalized "What to Review" scope, and the `{{SUBJECT}}` / `{{CRITERIA}}` / `{{MODE_OUTPUT_SECTION}}` placeholders. No criteria text lives here anymore — `SKILL.md` supplies it.

**Files:**
- Modify: `my-plugin/skills/code-review/code-reviewer-prompt.md` (full rewrite)

- [ ] **Step 1: Write the failing check**

Run (on current `main`, before editing):

```bash
cd my-plugin/skills/code-review
grep -q '{{SUBJECT}}' code-reviewer-prompt.md \
  && grep -q '{{CRITERIA}}' code-reviewer-prompt.md \
  && grep -q '{{MODE_OUTPUT_SECTION}}' code-reviewer-prompt.md \
  && grep -q '## Subject Under Review' code-reviewer-prompt.md \
  && grep -q 'Review mode:' code-reviewer-prompt.md \
  && ! grep -q '## Diff Payload' code-reviewer-prompt.md \
  && ! grep -q 'Solves the stated problem' code-reviewer-prompt.md \
  && echo PASS || echo FAIL
```

Expected: **FAIL** (placeholders absent; old `## Diff Payload` and hardcoded dimensions still present).

- [ ] **Step 2: Rewrite the file**

Replace the entire contents of `code-reviewer-prompt.md` with:

````markdown
# Code Reviewer Dispatch Prompt

This file is the prompt template the `my:code-review` skill sends to the `my:code-reviewer` subagent. The skill substitutes the placeholders before dispatch:

- `{{MODE}}` — `plan-review` or `diff-review`
- `{{SUBJECT}}` — the subject body (a diff, or a plan document's full text)
- `{{CRITERIA}}` — the mode-specific judgment-dimension block
- `{{PLAN_ALIGNMENT}}` — a `## Plan Alignment` block when a description or plan was supplied in diff-review; empty string otherwise
- `{{MODE_OUTPUT_SECTION}}` — the optional second output subsection (Plan Alignment / Grounding / empty)
- `{{PLAN_DIRECTORY}}` — the absolute directory the review file should land in
- `{{REVIEW_SLUG}}` — the filename stem for the review file (no `.md` suffix)

The body below this header is the prompt itself. Send everything below the `---` line.

---

You are a senior reviewer committed to factual, balanced analysis. Provide objective assessment regardless of developer expectations.

**Review mode:** {{MODE}}

## Anti-Sycophancy Directives

- NEVER sugarcoat issues to avoid conflict.
- Present arguments BOTH for and against the subject.
- Require specific `file:line` references for every claim.
- Label every finding with **both** a severity and a confidence (rules below). Surfacing is conditioned on the pair, not on either alone.
- Question assumptions before concluding.
- Prioritize objective truth over developer agreement.
- If unsure whether something is an issue, do **not** suppress — say "Needs Investigation" with the reason. "Don't know" is a legal output.

## What to Review

Your subject is below under `## Subject Under Review` — the calling skill has already assembled it; do **not** re-capture it (no `git diff`, `git status`, or re-reading a plan from disk). What you may read *beyond* the subject depends on the mode stated above:

- **diff-review:** the surface under review is the payload. Use `Read` / `Grep` only to assess a finding's context (chase a caller, inspect an imported helper); do not widen the review beyond the payload.
- **plan-review:** the plan is your subject and you are expected to **ground** it — actively use `Read` / `Grep` / `Glob` to verify the plan's claims against the repo (referenced files/symbols exist, assumptions hold, patterns match).

{{PLAN_ALIGNMENT}}

## Judgment Dimensions

{{CRITERIA}}

## Severity-Conditioned Surfacing

Every finding gets:

- **Severity:** `Critical` / `Warning` / `Suggestion`
- **Confidence:** `High` (very likely real) / `Medium` (probably real, some ambiguity) / `Low` (worth a look, not certain)

Surface a finding if and only if its (severity, confidence) pair satisfies the table:

| Severity | Surface at confidence |
|---|---|
| Critical | Low or higher (always) |
| Warning | Medium or higher |
| Suggestion | High only |

Rationale (do not repeat in the output): critical findings are cheap to investigate and expensive to miss; suggestions at low confidence are pure noise; warnings sit in the middle.

If you considered something but it didn't pass the surfacing rule, drop it silently — do not mention "considered but didn't surface" in the output.

## Output Structure

Write the review to `{{PLAN_DIRECTORY}}/{{REVIEW_SLUG}}.md` with this structure:

```markdown
### Change Summary

[2–3 sentences describing what the subject is/does. Stick to facts visible in the subject.]

{{MODE_OUTPUT_SECTION}}

### Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Critical / High | [one-line description] | `path/to/file.ext:42` | [how to fix, or "needs design discussion"] |

(One row per surfaced finding. Order rows by severity then confidence, both descending.)

### Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| [category] | `path/to/file.ext:line` | Strong / Moderate / Weak |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| [category] | `path/to/file.ext:line` | High / Medium / Low |

### Needs Investigation

[Anything you couldn't fully assess. Each item: what's unclear, why it matters, what additional context would resolve it. Omit this section entirely if there's nothing to flag.]

### Reasoning

[2–4 sentences linking the judgment-dimension findings and dual-perspective evidence to the verdict below. Required before the Verdict block — do not skip.]

### Verdict

**Assessment:** Sound / Problematic / Mixed
**Confidence:** High / Medium / Low — [one-sentence justification]
**Recommendation:** [specific actionable next step]
```

## Subject Under Review

{{SUBJECT}}
````

- [ ] **Step 3: Run the check to verify it passes**

Run the Step 1 command. Expected: **PASS**.

- [ ] **Step 4: Commit**

```bash
git add my-plugin/skills/code-review/code-reviewer-prompt.md
git commit -m "refactor(code-review): generalize dispatch prompt with mode placeholders"
```

---

### Task 2: Generalize the agent contract

Make `code-reviewer.md` mode-agnostic: section-name check, mode-aware scope rule (grounding allowed in plan-review), and "don't re-capture the subject" instead of "don't re-run git diff".

**Files:**
- Modify: `my-plugin/agents/code-reviewer.md`

- [ ] **Step 1: Write the failing check**

```bash
cd my-plugin/agents
grep -q '## Subject Under Review' code-reviewer.md \
  && grep -qi 'plan-review' code-reviewer.md \
  && grep -qi 'ground' code-reviewer.md \
  && ! grep -q '`## Diff Payload`' code-reviewer.md \
  && echo PASS || echo FAIL
```

Expected: **FAIL** (agent still references `## Diff Payload`, no plan-review/grounding language).

- [ ] **Step 2: Edit the contract**

In `my-plugin/agents/code-reviewer.md`:

(a) Replace the intro line under `# Code Reviewer (lean executor)`:

> You are dispatched by the `my:code-review` skill. The skill has already done the work of capturing the subject (a diff, or a plan document) and assembling the full review prompt — it is in your input. You render a soundness judgment, not a line-level bug scan (that is the built-in `/code-review`'s job). The prompt's `**Review mode:**` line tells you whether the subject is a diff (diff-review) or a plan (plan-review).

(b) Replace the first contract bullet ("Do not re-run `git diff`…") with:

> - **Do not re-capture the subject.** It is already in your prompt under `## Subject Under Review` — do not run `git diff`/`git status` or re-read a plan from disk. Treat it as authoritative.

(c) Replace the "Do investigate context when needed" bullet with a mode-aware pair:

> - **Diff-review: stay within the payload.** Use `Read` / `Grep` / `Glob` only to assess a finding's context (chase a caller, inspect an imported helper); do not widen the review beyond the payload.
> - **Plan-review: ground the plan.** Actively use `Read` / `Grep` / `Glob` to verify the plan's claims against the repo (referenced files/symbols exist, assumptions hold, patterns match). This is in scope and expected.

(d) Update the malformed-prompt check (last section) to:

> If your input lacks a `## Subject Under Review`, `## Judgment Dimensions`, or `## Output Structure` section, stop and return: `Dispatch prompt is malformed — required section <name> missing.` Do not improvise.

(e) Update the frontmatter `description` to drop "diff payload" specificity:

> description: Expert reviewer dispatched by the my:code-review skill. Receives a fully-specified prompt with the subject (a diff or a plan) and judgment dimensions; renders a dual-perspective soundness verdict with severity-conditioned confidence labels.

- [ ] **Step 3: Run the check to verify it passes**

Run the Step 1 command. Expected: **PASS**.

- [ ] **Step 4: Commit**

```bash
git add my-plugin/agents/code-reviewer.md
git commit -m "refactor(code-review): make reviewer agent contract mode-aware"
```

---

### Task 3: Add mode detection, criteria, and subject assembly to SKILL.md

The core task. Add a mode-detection step, the two criteria blocks, the two output-section blocks, subject assembly, the slug branch, the dirty-tree nudge, and update the frontmatter description.

**Files:**
- Modify: `my-plugin/skills/code-review/SKILL.md`

- [ ] **Step 1: Write the failing check**

```bash
cd my-plugin/skills/code-review
grep -qi 'plan-review' SKILL.md \
  && grep -q 'Working tree is dirty' SKILL.md \
  && grep -q '{{MODE}}' SKILL.md \
  && grep -q 'plan-review' SKILL.md \
  && grep -q 'Completeness & snippet self-sufficiency' SKILL.md \
  && grep -q '\-plan-review' SKILL.md \
  && echo PASS || echo FAIL
```

Expected: **FAIL** (none of the mode machinery exists yet).

- [ ] **Step 2: Insert a "Detect review mode" step after the diff-capture step**

After the current `### 1. Capture the diff` section (the one that ends with the empty-payload bail), insert a new section. Note the empty-payload bail must move *into* this logic — an empty payload no longer always bails:

````markdown
### 1a. Detect review mode

Let `PLAN_PATH` be from step 0 and `payload` be the captured diff. Set `MODE`:

| `PLAN_PATH` | `payload` | `MODE` | Action |
|---|---|---|---|
| set | empty | `plan-review` | Subject is the plan document; ignore `RANGE` if it was set. |
| set | non-empty | `diff-review` | Build the Plan Alignment block (step 2). **Print the nudge below to the user.** |
| unset | empty | — | Stop: `No changes to review.` (or `Range <RANGE> is empty.` if `RANGE` was set). |
| unset | non-empty | `diff-review` | Plain diff review. |

Nudge (print to the user, not into the dispatch prompt), when `PLAN_PATH` is set and `payload` is non-empty:

> `(Working tree is dirty, so I'm reviewing the diff against <PLAN_PATH>. Commit or stash to review the plan document itself.)`
````

(Adjust step 1's "If the resulting payload is empty, stop…" line so it defers to this table — the empty-payload stop only fires when `PLAN_PATH` is unset.)

- [ ] **Step 3: Update the "Build the dispatch prompt" step with mode-specific substitutions**

In `### 2. Build the dispatch prompt`, after reading `code-reviewer-prompt.md`, substitute the new placeholders. Add these substitution rules verbatim into the step:

````markdown
Substitute, by `MODE`:

- `{{MODE}}` → `plan-review` or `diff-review`.
- `{{SUBJECT}}`:
  - diff-review → ``The combined diff to review:`` followed by a fenced ```diff block with the payload.
  - plan-review → ``The plan document to review (`<PLAN_PATH>`):`` followed by a fenced ```markdown block with the **full** contents of `PLAN_PATH`.
- `{{CRITERIA}}`:
  - diff-review → the **Diff criteria** block below.
  - plan-review → the **Plan criteria** block below.
- `{{PLAN_ALIGNMENT}}`:
  - diff-review *with* a description/plan supplied → the existing `## Plan Alignment` block.
  - otherwise (including all plan-review) → empty string.
- `{{MODE_OUTPUT_SECTION}}`:
  - diff-review with alignment → the **Plan Alignment output** block below.
  - plan-review → the **Grounding output** block below.
  - plain diff-review → empty string.
- `{{PLAN_DIRECTORY}}` → `"$(git rev-parse --show-toplevel)/docs/plans"` (unchanged).
- `{{REVIEW_SLUG}}`:
  - diff-review → `<YYYY-MM-DD>-<branch-or-cwd>-review` (unchanged; replace `/` in branch with `-`).
  - plan-review → `<plan-basename-without-.md>-plan-review` (e.g. `docs/plans/2026-05-28-foo.md` → `2026-05-28-foo-plan-review`).

**Diff criteria** (`{{CRITERIA}}` for diff-review — this is the current text, preserved):

> Assess the change against these soundness dimensions — **not** a line-level bug scan. Mark genuinely-inapplicable dimensions as **N/A** with a one-line reason in the dual-perspective tables — do not silently skip.
>
> 1. **Solves the stated problem.** The change accomplishes its intent (and the supplied plan, if any). Judge whether it does the right thing, not whether each line is bug-free.
> 2. **Architecture & pattern fit.** Follows existing conventions, sits at the right abstraction level, respects layer boundaries; no new abstraction where three similar lines would do.
> 3. **Soundness of approach.** Treats the root cause, not a symptom. No bandaid `try/catch`, no backwards-compatibility cruft (renamed-but-still-exported symbols, dual "migration" code paths), no fallback logic that silently masks a failure.
> 4. **Risk & blast radius.** What is hard to reverse (schema, contract, data migration), what could break elsewhere, what needs manual verification or a deploy step.
> 5. **Plan alignment.** When a `## Plan Alignment` block was supplied above, treat every deviation between the diff and the plan as a finding.
>
> **Out of scope — do not duplicate the built-in reviewer.** Low-level bug-finding (exposed secrets, injection, N+1 queries, input-validation gaps, style/lint, test-coverage line items) is the job of the built-in `/code-review` (which also offers `--fix` and `ultra`). Do not enumerate those here. Only surface such an item if it directly undermines one of the judgment dimensions above (e.g., a missing authorization check that makes the *approach* unsound) — and say which dimension it implicates.

**Plan criteria** (`{{CRITERIA}}` for plan-review):

> Assess the plan against these dimensions — judge whether it is **ready to implement**, not whether its code snippets compile. Mark genuinely-inapplicable dimensions as **N/A** with a one-line reason in the dual-perspective tables — do not silently skip.
>
> 1. **Completeness & snippet self-sufficiency.** The plan covers the whole stated goal: no missing steps, unhandled cases, or undefined terms. A cold session could execute it without inventing requirements. This explicitly includes the snippets: any snippet meant to be executed must be runnable without the executor inventing imports, helpers, fixtures, or symbols the plan never establishes in an earlier step. A genuine omission — e.g. a snippet that references an import or helper the plan never defines — is a **completeness finding** (it forces the executor to guess), distinct from a *clearly-marked elision* (see dimension 6), which is fine.
> 2. **Sequencing & atomicity.** Steps are ordered so dependencies land before dependents; each step is a coherent, single-purpose commit. Where the plan implements behaviour, it follows Red → Green → Refactor (tests before implementation), per the project's plan standard.
> 3. **Test-strategy adequacy.** The planned tests actually pin the intended behaviour, at the right level (unit / feature / integration), and would fail for the right reason before the implementation exists. Flag tests that assert nothing meaningful or mock the code under test.
> 4. **Risk & reversibility.** Hard-to-reverse steps (schema changes, API/data contracts, migrations, deletions) are identified with a mitigation or rollback note; blast radius is named. Flag unflagged irreversible steps.
> 5. **Grounding (verify against the repo).** Use Read / Grep / Glob to confirm the plan's claims: referenced files, symbols, routes, and commands exist; stated assumptions about current behaviour hold; proposed patterns match existing conventions. Every stale reference or false assumption is a finding citing `plan-section` ↔ `repo file:line` (or "(not found)").
> 6. **Snippet logic.** Inspect embedded test/implementation snippets for **logic** errors only: off-by-ones, a test asserting the wrong thing, a snippet that cannot achieve its step's stated goal, contradictory snippets across steps. **Out of scope:** snippets the plan *clearly marks as abbreviated* (`…`, "imports omitted", "sketch"), and pure formatting/style. Do **not** flag those, and do **not** run a lint/type/style pass — that is the built-in `/code-review`'s job on real code. The test is "would the executor have to guess?", not "is a line missing" — a genuine omission belongs to dimension 1.

**Plan Alignment output** (`{{MODE_OUTPUT_SECTION}}` for diff-review with alignment — current text):

> ### Plan Alignment
>
> State whether the implementation matches the supplied description/plan, then enumerate any deviations as bullets — each referencing a `file:line` or "(missing)" with a one-line note. Surface deviations as findings in the Issues table using the standard severity / confidence labels.

**Grounding output** (`{{MODE_OUTPUT_SECTION}}` for plan-review):

> ### Grounding
>
> State whether the plan's references and assumptions hold against the repo. Enumerate each stale reference / false assumption as a bullet citing the plan location ↔ `repo file:line` (or "(not found)"). Surface material ones as findings in the Issues table. Omit if the plan made no checkable claims.
````

- [ ] **Step 4: Update the frontmatter `description` and the worked example**

(a) Append to the frontmatter `description` (after the existing text), a sentence:

> Pointing it at a `.md` plan with a clean working tree reviews the plan itself (grounded against the repo + snippet-logic check) instead of a diff.

(b) In the "Worked example" section, add a second short trace for plan-review:

````markdown
## Worked example: plan-review (clean tree)

```
0. Args: docs/plans/2026-05-28-foo.md → PLAN_PATH set; RANGE/DESCRIPTION empty.
1. git diff / --staged / ls-files → payload EMPTY.
1a. PLAN_PATH set + payload empty → MODE = plan-review.
2. Read code-reviewer-prompt.md. Substitute:
   MODE=plan-review; SUBJECT=```markdown <full plan text>```; CRITERIA=Plan criteria;
   PLAN_ALIGNMENT=""; MODE_OUTPUT_SECTION=Grounding output;
   REVIEW_SLUG=2026-05-28-foo-plan-review.
3. Agent: subagent_type="my:code-reviewer", prompt=<composed text>.
4. Confirm docs/plans/2026-05-28-foo-plan-review.md exists. Print pointer.
```
````

- [ ] **Step 5: Run the check to verify it passes**

Run the Step 1 command. Expected: **PASS**.

- [ ] **Step 6: Commit**

```bash
git add my-plugin/skills/code-review/SKILL.md
git commit -m "feat(code-review): add plan-review mode (subject=plan, grounded)"
```

---

### Task 4: Documentation — README row + routing row

**Files:**
- Modify: `README.md`
- Modify: `GLOBAL-CLAUDE.md` (**requires user authorization — guardrail**)

- [ ] **Step 1: Update the README `/my:code-review` row**

Change the row to:

```markdown
| `/my:code-review` | Dual-perspective soundness verdict + plan-alignment, written to `docs/plans/`; or, on a clean tree with a `.md` plan, reviews the plan itself (bug-finding/fix delegated to built-in `/code-review`) |
```

- [ ] **Step 2: Commit the README change**

```bash
git add README.md
git commit -m "docs(code-review): note plan-review mode in README"
```

- [ ] **Step 3: Add the routing row to `GLOBAL-CLAUDE.md`** *(needs user authorization)*

In the "Code Review Routing" table, add:

```markdown
| Review an implementation plan/spec before coding | `my:code-review <plan>.md` (clean tree) |
```

Ask the user to authorize the `GLOBAL-CLAUDE.md` edit (auto-mode self-modification guardrail). It is live-symlinked to `~/.claude/CLAUDE.md`, so the edit takes effect immediately. Commit:

```bash
git add GLOBAL-CLAUDE.md
git commit -m "docs(global): route plan review to my:code-review"
```

---

### Task 5: Functional smoke test (manual, fresh session)

Structural greps prove the wiring; this proves the behaviour. Skill metadata loads at session start, so run this in a **new** session after merge.

- [ ] **Step 1: Plan-review happy path**

On a clean working tree, run `/my:code-review docs/plans/2026-05-28-code-review-plan-mode.md`.
Expected: a file `docs/plans/2026-05-28-code-review-plan-mode-plan-review.md` is written, containing `### Grounding`, dual-perspective tables, and a `### Verdict` (Sound/Problematic/Mixed). No language-checklist line items.

- [ ] **Step 2: Boundary check (the dimension 1 vs 6 line)**

Create a throwaway plan with (a) a snippet clearly marked `# imports omitted` and (b) a snippet referencing an undefined helper the plan never defines and a function in a file path that does not exist. Run plan-review.
Expected: the marked elision is **not** flagged; the undefined helper + non-existent file path **are** flagged — the helper under Completeness (dimension 1, "executor would have to guess"), the bad path under Grounding (dimension 5, "(not found)").

- [ ] **Step 3: Diff-mode regression**

(a) With a clean tree and no plan arg → `No changes to review.` unchanged.
(b) With uncommitted changes + a plan arg → the dirty-tree nudge prints and it does diff+alignment (not plan-review).
(c) With uncommitted changes, no plan arg → normal diff-review, unchanged output shape.

- [ ] **Step 4: Integrate**

Squash-merge the worktree branch to `main`, keep the branch, remove the worktree (per project git workflow). Promote the spec/plan status if you track it.

---

## Self-Review

**Spec coverage:**
- Mode detection table → Task 3 Step 2. ✓
- Dirty-tree nudge → Task 3 Step 2. ✓
- Subject assembly (diff/plan) → Task 3 Step 3 (`{{SUBJECT}}`). ✓
- Diff & Plan criteria verbatim → Task 3 Step 3. ✓
- Explicit `**Review mode:**` signal → Task 1 (prompt) + Task 3 (`{{MODE}}` substitution). ✓
- Output `{{MODE_OUTPUT_SECTION}}` (Grounding/Plan Alignment) → Task 1 + Task 3 Step 3. ✓
- Verdict semantics (plan = ready-to-implement) → carried by Plan criteria + shared Verdict block. ✓
- Slug rule (`-plan-review`) → Task 3 Step 3. ✓
- Prompt template changes → Task 1. ✓
- Agent contract changes → Task 2. ✓
- README + GLOBAL-CLAUDE.md routing → Task 4. ✓
- Snippet boundary (dim 1 vs dim 6) → encoded in Plan criteria (Task 3) + tested in Task 5 Step 2. ✓

**Placeholder scan:** No "TBD"/"similar to"/"add error handling". Criteria and prompt bodies are reproduced in full (not referenced).

**Type/name consistency:** Placeholder names (`{{MODE}}`, `{{SUBJECT}}`, `{{CRITERIA}}`, `{{MODE_OUTPUT_SECTION}}`, `{{PLAN_ALIGNMENT}}`, `{{PLAN_DIRECTORY}}`, `{{REVIEW_SLUG}}`) match between the prompt (Task 1) and the substitution rules (Task 3). Section names (`## Subject Under Review`, `## Judgment Dimensions`, `## Output Structure`) match between prompt (Task 1) and agent check (Task 2). Slug suffix `-plan-review` consistent (Task 3 ↔ Task 5).

## Dependencies

None — no packages, config, or new files. The `my:code-reviewer` agent already has Read/Grep/Glob/Bash/Write.

## Risk

- **False positives on partial snippets** — mitigated by the dim-1-vs-dim-6 boundary (Task 3 criteria) and explicitly exercised in Task 5 Step 2.
- **Mode misfire on dirty tree** — mitigated by the printed nudge (Task 3) and Task 5 Step 3b.
- **Empty-payload bail regression** — the bail moves into the mode table; Task 5 Step 3a guards it.
- **`GLOBAL-CLAUDE.md` edit** — global blast radius + guardrail; isolated to one routing row, done only with user authorization (Task 4 Step 3).
- Reversible: markdown-only; pre-change state on `main` history and the retained branch.
