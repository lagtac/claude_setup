# `my:spec-review` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `my:spec-review` skill and `my:spec-reviewer` agent that review one `-spec.md` with a system-thinking focus, and make it a required step of the Spec → Plan flow.

**Architecture:** The skill reads the spec from disk, fills a prompt template, and dispatches a lean executor agent. The agent builds a system model, judges six criteria, and writes a report to `docs/plans/`. `my:soundness-review` stops on specs and points to the new skill. `GLOBAL-CLAUDE.md` wires the review into the spec flow.

**Tech Stack:** Claude Code plugin markdown (skills, agents), Bash, `claude -p` headless runs for tests, `markdownlint-cli2`.

**Spec:** `docs/plans/2026-09-16-spec-review-skill-spec.md`

## Global Constraints

- Conventional Commits with scope: `type(scope): sentence`. Scope for plugin files is `my-plugin`; for `GLOBAL-CLAUDE.md` it is `global`.
- Every commit ends with `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- No new dependencies.
- Agents do not read CLAUDE.md. Every rule the agent must follow is written into the agent file or the prompt template.
- Subagents lose `Grep`, `Glob` and `LSP` at run time. `grep -rn` and `find` through `Bash` are the main search route.
- Work happens in a worktree on branch `feat/spec-review-skill`. Integrate with `git merge --squash`. Remove the worktree after merge. Do not delete the branch.

## How tests run

The repo has no test runner. The `my` plugin loads through the shell alias `claude --plugin-dir ~/projects/claude-setup/my-plugin`, so the running session cannot see new skills in a worktree. Every Green check runs a headless session against the worktree's plugin:

```bash
WT=<absolute worktree path>
SCRATCH=/tmp/claude-1000/-home-dchris-projects-claude-setup/5afa7d56-07d9-45a4-bd77-99fd49f5e09b/scratchpad
cd "$WT" && claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits \
  --output-format stream-json --verbose "<prompt>" > "$SCRATCH/<run-name>.jsonl"
```

This loads the real agent with the real tool filtering, so the result matches production.

## File map

| File | Status | Responsibility |
|---|---|---|
| `my-plugin/agents/spec-reviewer.md` | Create | Lean executor contract for the reviewer subagent |
| `my-plugin/skills/spec-review/spec-reviewer-prompt.md` | Create | Criteria, evidence and label rules, report layout |
| `my-plugin/skills/spec-review/SKILL.md` | Create | Argument check, subject assembly, dispatch, result |
| `my-plugin/skills/soundness-review/SKILL.md` | Modify | Stop on `-spec.md` in plan-review; description sentence |
| `my-plugin/skills/soundness-review/code-reviewer-prompt.md` | Modify | Header line naming the copied rules |
| `GLOBAL-CLAUDE.md` | Modify | Spec → Plan step 2; Code Review Routing |

---

### Task 0: Worktree

- [ ] **Step 1:** Invoke `superpowers:using-git-worktrees`. Create branch `feat/spec-review-skill` from `main` (at or after `7c3709b`). Set `WT` to the worktree path.
- [ ] **Step 2:** Confirm: `git -C "$WT" log --oneline -1` shows the spec commit, and `git -C "$WT" status --short` is empty.

---

### Task 1: Planted-defect test spec and Red baseline

**Files:**

- Create: `$SCRATCH/seeded/2026-09-16-review-dashboard-spec.md` (outside the repo, never committed)

**Interfaces:**

- Produces: the test spec path used by Task 2 Step 5, and the Red report `$SCRATCH/red-baseline-report.md`.

- [ ] **Step 1: Write the test spec**

It has four planted defects:

- **D-own:** §Architecture says the skill owns `index.json`; §Dashboard behaviour says the page rewrites `index.json`.
- **D-howto:** no "How to read this spec" section.
- **D-ground:** it cites `my-plugin/lib/review-parser.sh` as existing. That file does not exist.
- **D-visual:** it adds a UI page with no Visual Language section.

````markdown
# Spec: review dashboard

## Context

Review reports pile up in `docs/plans/`. Nobody can see which reviews are open. This spec adds a small dashboard.

## Architecture

Two components:

- **`my:review-index` skill.** Scans `docs/plans/*-review*.md`, parses each verdict with the existing parser at `my-plugin/lib/review-parser.sh`, and writes `docs/plans/index.json`. The skill is the only writer of `index.json`; it regenerates the whole file on every run.
- **Dashboard page.** A static HTML page, `docs/plans/dashboard.html`, that reads `index.json` and lists reviews with their verdict.

## Dashboard behaviour

The page shows one row per review: file name, verdict, date. Each row has a "Mark done" button. Clicking it sets `"done": true` on that entry and saves `index.json` back to disk through the File System Access API. Done rows are hidden.

## Trade-offs

**Option A — static page plus index file (chosen).** Pros: no server. Cons: the browser needs file access permission.

**Option B — print a table in the terminal.** Pros: nothing to open. Cons: no way to mark reviews done.

## Dependencies

None new. Uses the browser File System Access API.

## Risk

- Reversible: delete two files.
- The API is not available in Firefox.
````

- [ ] **Step 2: Confirm the planted grounding defect is real**

Run: `test -e /home/dchris/projects/claude-setup/my-plugin/lib/review-parser.sh; echo $?`
Expected: `1`

- [ ] **Step 3: Record Red with today's reviewer**

In the main checkout, with a clean tree (commit this plan first), run the current skill in plan-review mode:

```bash
cd /home/dchris/projects/claude-setup && git status --short   # must be empty
claude -p --plugin-dir /home/dchris/projects/claude-setup/my-plugin --permission-mode acceptEdits \
  "Run my:soundness-review $SCRATCH/seeded/2026-09-16-review-dashboard-spec.md" \
  > "$SCRATCH/red-baseline.txt"
```

Move the report it wrote out of the repo, so `main` stays clean:

```bash
ls docs/plans/2026-09-16-review-dashboard-spec-plan-review*.md
mv docs/plans/2026-09-16-review-dashboard-spec-plan-review.md "$SCRATCH/red-baseline-report.md"
git status --short   # must be empty again
```

Expected Red, record each as yes or no in `$SCRATCH/red-baseline-notes.md`:

1. The report has no `Class` column. (Expected: yes, no class.)
2. It has no System Model section. (Expected: yes, none.)
3. D-own is missing, or is not rated Critical, or cites no `spec §`. (Expected: at least one holds.)
4. It gives findings or N/A rows about TDD, snippets or test strategy. (Expected: yes.)

Red also covers routing. Today `my:soundness-review` on a `-spec.md` with a clean tree runs a plan review instead of stopping. Step 3 already shows this.

No commit. The test spec lives in the scratchpad.

---

### Task 2: Reviewer agent, prompt template and skill

**Files:**

- Create: `my-plugin/agents/spec-reviewer.md`
- Create: `my-plugin/skills/spec-review/spec-reviewer-prompt.md`
- Create: `my-plugin/skills/spec-review/SKILL.md`
- Modify: `my-plugin/skills/soundness-review/code-reviewer-prompt.md` (header, one line)

**Interfaces:**

- Consumes: the test spec from Task 1.
- Produces: skill name `my:spec-review` (single argument: a spec path); agent type `my:spec-reviewer`; template placeholders `{{SPEC_PATH}}`, `{{SUBJECT}}`, `{{PLAN_DIRECTORY}}`, `{{REVIEW_SLUG}}`; report path `docs/plans/<spec-basename>-review[-N].md`; `Class` values `editorial` and `design`.

- [ ] **Step 1: Confirm Red for the new surfaces**

Run: `ls "$WT/my-plugin/skills/spec-review" "$WT/my-plugin/agents/spec-reviewer.md"`
Expected: both `No such file or directory`.

- [ ] **Step 2: Create `my-plugin/agents/spec-reviewer.md`**

```markdown
---
name: spec-reviewer
description: Expert reviewer dispatched by the my:spec-review skill. Receives a fully-specified prompt containing one spec and system-thinking criteria; builds a system model first, then renders a dual-perspective verdict with severity, confidence and an editorial/design class on every finding.
tools: Read, Grep, Glob, Bash, Write, LSP, ToolSearch
model: opus
---

# Spec Reviewer (lean executor)

You are dispatched by the `my:spec-review` skill. The skill has already read the spec and assembled the full review prompt — it is in your input. You judge whether the system the spec describes holds together. You do not review an implementation plan or code.

## Contract with the Calling Skill

- **Do not re-capture the subject.** The spec is in your prompt under `## Subject Under Review`. Do not re-read it from disk and do not run `git diff`. Treat it as authoritative.
- **Build the System Model first.** Fill the `### System Model` tables before you judge any criterion. Every criterion is judged against that model.
- **Do not improvise criteria.** Assess against the six criteria under `## Criteria`. Mark a genuinely-inapplicable criterion **N/A** with a one-line reason. Respect the out-of-scope list.
- **Do not invent your own output schema.** Use the structure under `## Output Structure`.
- **Label every finding three ways:** severity, confidence and class, as defined under `## Evidence and Labels`. Surface a finding only when its (severity, confidence) pair passes the table there. When unsure between `editorial` and `design`, use `design`.
- **Ground the spec against the repo.** Use `Read` plus `Bash` searches (`grep -rn`, `find`) — `Bash` is always available. Use the `Grep` / `Glob` tools when they are in your tool list; they often are not, so never let their absence cancel a search. For a symbol the spec removes or renames, always run a plain text search for the name token across the repo; additionally try `LSP` `findReferences` **when it is in your tool list**. If `LSP` is missing or errors, say the sweep was text-only.
- **Do write the review file.** Use `Write` to write to the path under `## Output Structure`. Then return a one-paragraph summary as text: verdict, top finding and its class.

## If the Prompt Is Missing Sections

If your input lacks a `## Subject Under Review`, `## Criteria`, or `## Output Structure` section, stop and return: `Dispatch prompt is malformed — required section <name> missing.` Do not improvise.
```

- [ ] **Step 3: Create `my-plugin/skills/spec-review/spec-reviewer-prompt.md`**

````markdown
# Spec Reviewer Dispatch Prompt

This file is the prompt template the `my:spec-review` skill sends to the `my:spec-reviewer` subagent. The skill substitutes the placeholders before dispatch:

- `{{SPEC_PATH}}` — the spec's repo-relative path
- `{{SUBJECT}}` — the spec's full text in a fenced markdown block (plus the size note when the guard trips)
- `{{PLAN_DIRECTORY}}` — the absolute directory the review file lands in
- `{{REVIEW_SLUG}}` — the filename stem for the review file (no `.md` suffix)

Copied rules: the Anti-Sycophancy Directives, the surfacing table and the Dual-Perspective tables are copied from `my-plugin/skills/soundness-review/code-reviewer-prompt.md`. When you edit them here, check that file too.

The body below this header is the prompt itself. Send everything below the `---` line.

---

You are a senior systems reviewer committed to factual, balanced analysis. Provide objective assessment regardless of the author's expectations.

**Review mode:** spec-review of `{{SPEC_PATH}}`

## Anti-Sycophancy Directives

- NEVER sugarcoat issues to avoid conflict.
- Present arguments BOTH for and against the spec — *when both exist*. If there is no material affirmative case, write `None material.` in that table rather than manufacturing a weak row.
- Cite evidence for every claim, in one of the forms under `## Evidence and Labels`.
- Question assumptions before concluding.
- Prioritize objective truth over author agreement.
- If unsure whether something is an issue, do **not** suppress — put it under "Needs Investigation" with the reason. "Don't know" is a legal output.

## What to Review

Your subject is the spec below under `## Subject Under Review`. Do not re-read it from disk. You are expected to read the repo beyond it: every file, symbol, command and behaviour the spec claims exists must be checked. Use `Read` plus `Bash` searches (`grep -rn`, `find`); `Bash` is always available. Use the `Grep` / `Glob` tools when they are in your tool list; they often are not, and their absence never cancels a search.

## Step 1 — Build the System Model

Before judging anything, fill the two System Model tables in the output:

- **Components:** every part the spec introduces or changes. For each: what it owns (state, files, decisions), what it depends on, and whether it is new or existing. For an existing part, give the repo location where you verified it.
- **Connections:** every link between components. For each: what passes along it (a call, a file, an event, shared state) and which component owns that thing.

A row you cannot fill from the spec is itself a finding (usually `design`).

## Criteria

Judge each criterion against the System Model. Mark a genuinely-inapplicable criterion **N/A** with a one-line reason in the dual-perspective tables — do not silently skip.

1. **Boundaries.** Each component has one clear job. No two components own the same thing. No component exists only to pass calls along.
2. **Contracts and flow.** Every connection has a defined input, output and owner. Each piece of state has exactly one source of truth. Data and control flow have no gaps, and no cycles the spec does not state.
3. **Failures and interactions.** For each connection: what happens when one side fails or changes? The spec must say whether the failure stops, spreads, or is hidden. Look for behaviour that only appears in combination: loops, races, ordering needs.
4. **Fit with what exists.** The repo does not already solve the problem. The design follows existing patterns. The rejected options were real choices with stated reasons, not options added only to be rejected.
5. **Grounding.** Every file, symbol, command and claim about current behaviour is checked against the repo. For a symbol the spec removes or renames, run a plain text search for the name token across the whole repo — string references (route names, config keys, template names) are invisible to symbol tools. Additionally try `LSP` `findReferences` when it is in your tool list; if it is missing or errors, say the sweep was text-only. Each false claim goes under `### Grounding`.
6. **Spec rules.** The author's standing rules for a spec:
   - The first section is "How to read this spec", listing all related documents with paths, in reading order.
   - A reader with no other context could write the implementation plan from the spec alone.
   - The spec has Risk, Dependencies and Trade-offs sections.
   - A Visual Language section, mapping UI elements to design-system primitives, is required **only** when the spec adds or changes UI. When the spec adds no UI, its absence is correct — do not flag it.

**Out of scope:** TDD steps, test code, commit order and code-snippet logic. Those belong to the implementation plan, which a different reviewer checks. Do not raise findings or N/A rows about them.

## Evidence and Labels

**Evidence** takes one of two forms:

- a repo location `path/to/file.ext:line` that you opened with `Read` or found with a search you ran; or `(not found)` for a claimed file or symbol your search did not find;
- a spec location `spec §<Section heading>`, or `spec §<A> ↔ §<B>` for a conflict between two sections.

Every finding gets three labels:

- **Severity:** `Critical` / `Warning` / `Suggestion`
- **Confidence:** `High` (very likely real) / `Medium` (probably real, some ambiguity) / `Low` (worth a look, not certain)
- **Class:**
  - `editorial` — the text is wrong, the decision is not: a missing required section, a stale repo reference, a placeholder, a vague sentence with only one sensible reading, two sections that disagree in wording only.
  - `design` — the finding challenges a decision: a boundary, a contract, state ownership, the chosen option, or the scope.
  - When unsure, use `design`. An `editorial` label means the author may fix it without being asked, so it must be earned.

Surface a finding if and only if its (severity, confidence) pair satisfies the table:

| Severity | Surface at confidence |
|---|---|
| Critical | Low or higher (always) |
| Warning | Medium or higher |
| Suggestion | High only |

**Every `Critical` finding must cite evidence you checked yourself** — a repo location you opened or searched. **Exception:** a contradiction or gap *inside the spec* may be Critical on `spec §` citations alone, because it has no repo line. A Critical claim about the repo that you could not verify is not Critical: downgrade it to `Warning` and say what you could not check, or move it to Needs Investigation.

If you considered something but it did not pass the surfacing rule, drop it silently.

## Output Structure

Write the review to `{{PLAN_DIRECTORY}}/{{REVIEW_SLUG}}.md` with this structure:

```markdown
### Spec Summary

[2–3 sentences: what the spec proposes. Facts visible in the spec only.]

### System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| [name] | [state, files, decisions] | [components, repo files] | New / Existing `path:line` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| [A → B] | [call / file / event / shared state] | [component] |

### Grounding

[One bullet per stale reference or false assumption: `spec §Section` ↔ `repo file:line` or "(not found)". Write "All checked references hold." when there are none.]

### Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Critical / High | design | [one-line description] | `spec §A ↔ §B` | [fix, or "decision for the author"] |

(One row per surfaced finding. Order by severity then confidence, both descending.)

### Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| [criterion] | [evidence] | Strong / Moderate / Weak |

(`None material.` in place of the table is legal. N/A rows for inapplicable criteria still appear.)

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| [criterion] | [evidence] | High / Medium / Low |

### Needs Investigation

[What is unclear, why it matters, what would resolve it. Omit this section if empty.]

### Reasoning

[2–4 sentences linking the System Model and findings to the verdict. Required.]

### Verdict

**Assessment:** Sound / Problematic / Mixed
**Confidence:** High / Medium / Low — [one-sentence justification]
**Recommendation:** [specific next step]
```

## Subject Under Review

{{SUBJECT}}
````

- [ ] **Step 4: Create `my-plugin/skills/spec-review/SKILL.md`**

````markdown
---
name: spec-review
description: >
  System-thinking review of one design spec (`docs/plans/*-spec.md`) before its implementation plan is
  written. Builds a model of the spec's components and connections, then judges boundaries, contracts
  and state ownership, failure spread, fit with existing code, grounding against the repo, and the
  spec rules (How to read this spec, self-containment, Risk/Dependencies/Trade-offs, Visual Language
  for UI). Every finding is labelled editorial (fix freely) or design (ask the author). Writes a
  durable report to docs/plans/. Use when asked to review a spec or design doc, and as the required
  review step of the Spec → Plan flow. NOT for implementation plans, diffs or code — those go to
  `my:soundness-review`.
---

# Spec Review

Dispatch a fresh-context reviewer subagent to judge whether the system a spec describes holds together. The reviewer builds a System Model first, then judges six criteria against it, and labels every finding `editorial` or `design`.

The criteria, evidence rules and report layout live in `spec-reviewer-prompt.md`. The agent receives the full prompt at dispatch time and must not improvise.

This skill ignores the working tree. It reads the spec from disk and never runs `git diff`, so uncommitted files elsewhere do not change what it reviews.

## Steps

### 0. Check the argument

The args string must be exactly one path to an existing file ending in `.md`. Set `SPEC_PATH` to it, relative to the repo root (`git rev-parse --show-toplevel`).

If args is empty, names more than one path, or the file does not exist, stop and print:

`Usage: my:spec-review <path/to/spec.md> — one existing spec file.`

If the filename does not end in `-spec.md`, continue, and print: `(<SPEC_PATH> does not end in -spec.md; reviewing it as a spec anyway.)`

### 1. Read the spec

Read the full file. Count its lines (`wc -l`).

**Size guard.** Above **2000** lines, do not stop. Print `(Spec is <N> lines; the reviewer's coverage may be uneven.)` and put this line first inside `{{SUBJECT}}`: `Note: this spec is <N> lines. If you cannot assess all of it at the same depth, say so under "Needs Investigation" and name the parts you covered shallowly.`

### 2. Build the dispatch prompt

Read `spec-reviewer-prompt.md` from this skill's directory. Take everything below the first `---` line. Substitute:

- `{{SPEC_PATH}}` → `SPEC_PATH`.
- `{{SUBJECT}}` → ``The spec to review (`<SPEC_PATH>`):`` then (size note if any) then a fenced ```markdown block with the **full** spec text.
- `{{PLAN_DIRECTORY}}` → the absolute path `"$(git rev-parse --show-toplevel)/docs/plans"`. Subagents do not reliably inherit the session's cwd, so never pass a relative path. Run `mkdir -p` on it first.
- `{{REVIEW_SLUG}}` → `<spec basename without .md>-review`. Example: `docs/plans/2026-09-16-foo-spec.md` → `2026-09-16-foo-spec-review`.

**Collision rule.** If `{{PLAN_DIRECTORY}}/{{REVIEW_SLUG}}.md` exists, append `-2`, then `-3`, until the path is free. Reviews are a record — never overwrite one. Re-reviewing a spec after fixes is the normal case.

### 3. Dispatch the reviewer

Use the Agent tool with `subagent_type: "my:spec-reviewer"`, `description: "Spec review"`, and the composed prompt. Do not run it in the background — the caller is waiting.

### 4. Surface the result

1. Confirm `{{PLAN_DIRECTORY}}/{{REVIEW_SLUG}}.md` exists. If not, print the agent's text output verbatim and say the file write did not happen.
2. Print: `Review written to docs/plans/<filename>.`
3. If the verdict is `Problematic` or any `Critical` finding exists, print the top finding in two lines, including its class.

### 5. Inside the Spec → Plan flow

When this skill runs as the spec flow's review step, the caller then acts on the findings as follows:

- **`editorial`:** fix it in the spec. Before each fix, check whether it changes what a component owns, a contract, the chosen option, or the scope. If it does, treat it as `design`, whatever its label says.
- **`design`:** do not fix it. Ask the author: "Decision X was picked for reason Y. The review says Y is wrong because Z. Keep X or change it?"
- **Rejected findings:** list each with one line of reasoning.
- Then ask the author to review the spec, the report path and the open design questions together.

## Worked example

```
0. Args: docs/plans/2026-09-16-foo-spec.md → exists, ends in -spec.md → SPEC_PATH set.
1. Read the file. wc -l → 180 (no size note).
2. Read spec-reviewer-prompt.md; take the body below the first `---`.
   Bash: git rev-parse --show-toplevel → PLAN_DIRECTORY="<root>/docs/plans"; mkdir -p it.
   REVIEW_SLUG=2026-09-16-foo-spec-review; the file exists → 2026-09-16-foo-spec-review-2.
   Substitute SPEC_PATH, SUBJECT, PLAN_DIRECTORY, REVIEW_SLUG.
3. Agent: subagent_type="my:spec-reviewer", description="Spec review", prompt=<composed text>.
4. Confirm <PLAN_DIRECTORY>/2026-09-16-foo-spec-review-2.md exists. Print pointer.
```
````

- [ ] **Step 5: Add the copy note to the soundness-review template**

In `my-plugin/skills/soundness-review/code-reviewer-prompt.md`, insert after the placeholder list (before `The body below this header is the prompt itself.`):

```markdown
Copied rules: the Anti-Sycophancy Directives, the surfacing table and the Dual-Perspective tables are copied into `my-plugin/skills/spec-review/spec-reviewer-prompt.md`. When you edit them here, check that file too.
```

- [ ] **Step 6: Green — planted-defect run**

```bash
mkdir -p "$SCRATCH/green" && cp "$SCRATCH/seeded/2026-09-16-review-dashboard-spec.md" "$WT/docs/plans/"
cd "$WT" && claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits \
  --output-format stream-json --verbose \
  "Run my:spec-review docs/plans/2026-09-16-review-dashboard-spec.md" > "$SCRATCH/green/seeded.jsonl"
R="$WT/docs/plans/2026-09-16-review-dashboard-spec-review.md"
grep -c '"subagent_type":"my:spec-reviewer"' "$SCRATCH/green/seeded.jsonl"   # ≥ 1
grep -n '### System Model' "$R"                                              # present
grep -n -i 'index.json' "$R" | grep -i 'design' | grep -i 'critical'        # D-own
grep -n 'spec §' "$R"                                                        # ≥ 1
grep -n 'review-parser.sh' "$R" | grep -i 'not found'                        # D-ground
grep -n -i 'how to read' "$R" | grep -i 'editorial'                          # D-howto
grep -n -i 'visual language' "$R" | grep -i 'editorial'                      # D-visual
grep -n -i -E 'TDD|red → green|snippet|commit order' "$R"                    # no findings about these
```

Expected: every check prints the stated result. Also read the report once in full. The grep lines prove presence, not quality. If a check fails, fix the prompt template, not the test, and rerun.

Then remove the test files from the worktree, which must not be committed:

```bash
mv "$R" "$SCRATCH/green/" && rm "$WT/docs/plans/2026-09-16-review-dashboard-spec.md"
git -C "$WT" status --short   # only the Task 2 files
```

- [ ] **Step 7: Green — real specs and collision**

```bash
cd "$WT"
for s in 2026-05-28-code-review-plan-mode-spec 2026-09-11-retire-planner-path-spec; do
  claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits \
    "Run my:spec-review docs/plans/$s.md" > "$SCRATCH/green/$s.txt"
done
claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits \
  "Run my:spec-review docs/plans/2026-09-11-retire-planner-path-spec.md" > "$SCRATCH/green/collision.txt"
ls docs/plans/*-spec-review*.md
grep -L '### System Model' docs/plans/*-spec-review*.md                      # prints nothing
grep -n -i 'visual language' docs/plans/2026-09-11-retire-planner-path-spec-review*.md
grep -n -i -E 'TDD|red → green|snippet|commit order' docs/plans/*-spec-review*.md
```

Expected:

- Three reports: `2026-05-28-code-review-plan-mode-spec-review.md`, `2026-09-11-retire-planner-path-spec-review.md` and `…-review-2.md`.
- Every report has a System Model.
- The planner-retirement reports do not flag missing Visual Language. An N/A mention is fine.
- No TDD, commit-order or snippet findings.

These three reports are real reviews of real specs, so keep them and commit them with this task.

- [ ] **Step 8: Lint**

Run: `markdownlint-cli2 my-plugin/agents/spec-reviewer.md "my-plugin/skills/spec-review/*.md" 2>&1 | grep error | grep -v -E 'MD013|MD060'`
Expected: no output.

- [ ] **Step 9: Commit**

```bash
git add my-plugin/agents/spec-reviewer.md my-plugin/skills/spec-review my-plugin/skills/soundness-review/code-reviewer-prompt.md docs/plans/*-spec-review*.md
git commit -m "feat(my-plugin): add my:spec-review system-thinking spec reviewer

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Route specs away from soundness-review

**Files:**

- Modify: `my-plugin/skills/soundness-review/SKILL.md` (description lines 3-11; step 1a table and nudge, lines 72-85)

**Interfaces:**

- Consumes: skill name `my:spec-review` from Task 2.
- Produces: the stop message `This is a spec. Run my:spec-review <PLAN_PATH> instead.`

- [ ] **Step 1: Red**

Run: `grep -n 'spec-review' "$WT/my-plugin/skills/soundness-review/SKILL.md"`
Expected: no output. Task 1 Step 3 already showed that a spec currently gets a plan review.

- [ ] **Step 2: Edit the description**

Replace the last sentence of the `description` (line 10-11):

```
  delegated to the built-in `/code-review`. Pointing it at a `.md` plan with a clean working tree
  reviews the plan itself (grounded against the repo + snippet-logic check) instead of a diff.
```

with:

```
  delegated to the built-in `/code-review`. Pointing it at a `.md` plan with a clean working tree
  reviews the plan itself (grounded against the repo + snippet-logic check) instead of a diff.
  Specs (`*-spec.md`) are not reviewed on their own here — use `my:spec-review`; checking a diff
  against a spec still belongs here.
```

- [ ] **Step 3: Edit step 1a**

Replace the first table row:

```
| set | empty | `plan-review` | Subject is the plan document; ignore `RANGE` if it was set. |
```

with:

```
| set, ends in `-spec.md` | empty | — | Stop: `This is a spec. Run my:spec-review <PLAN_PATH> instead.` Do not dispatch. |
| set | empty | `plan-review` | Subject is the plan document; ignore `RANGE` if it was set. |
```

Rows are checked top to bottom; the first match wins. Add this sentence directly under the table:

```
Rows are matched top to bottom; the first match wins. A spec with a non-empty payload still falls through to `diff-review`, which checks the change against the spec.
```

- [ ] **Step 4: Commit**

The Green run needs a clean tree to reach plan-review mode, so commit first.

```bash
git add my-plugin/skills/soundness-review/SKILL.md
git commit -m "feat(my-plugin): route specs from soundness-review to spec-review

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 5: Green**

```bash
cd "$WT" && git status --short   # empty
claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits --output-format stream-json --verbose \
  "Run my:soundness-review docs/plans/2026-09-11-retire-planner-path-spec.md" > "$SCRATCH/green/route.jsonl"
grep -c 'Run my:spec-review' "$SCRATCH/green/route.jsonl"                   # ≥ 1
grep -c '"subagent_type":"my:code-reviewer"' "$SCRATCH/green/route.jsonl"   # 0
git status --short                                                          # still empty: no report written
```

If a check fails, fix the SKILL.md edit, amend the Task 3 commit, and rerun.

---

### Task 4: Wire the review into GLOBAL-CLAUDE.md

**Files:**

- Modify: `GLOBAL-CLAUDE.md:37` (Spec → Plan step 2), `GLOBAL-CLAUDE.md:48-50` (Code Review Routing)

**Interfaces:**

- Consumes: skill names `my:spec-review` and `my:soundness-review`; class values `editorial` and `design`.

- [ ] **Step 1: Red**

Run: `grep -c 'my:spec-review' "$WT/GLOBAL-CLAUDE.md"`
Expected: `0`

- [ ] **Step 2: Replace step 2 of the Spec → Plan flow (line 37)**

Old:

```
2. Self-review the spec (placeholders, consistency, scope, ambiguity, self-containment), then ask the user to review it before proceeding.
```

New:

```
2. Self-review the spec (placeholders, consistency, scope, ambiguity, self-containment). Then run `my:spec-review <spec path>` and act on its report: fix every `editorial` finding — but first check whether the fix changes what a component owns, a contract, the chosen option, or the scope, and if it does treat it as `design`; never fix a `design` finding — ask the user in the "No silent reinterpretation" form below; list rejected findings with one line of reasoning each. Then ask the user to review the spec, the report and the open design questions before proceeding.
```

- [ ] **Step 3: Edit Code Review Routing (lines 48-50)**

Old line 48:

```
Two diff reviewers, complementary — route by what you want:
```

New:

```
Three reviewers, complementary — route by what you want:
```

In the `my:soundness-review` bullet (line 50), replace `or review the plan itself (clean tree)` with `or review a plan itself (clean tree; specs go to `my:spec-review`)`.

Insert a new bullet directly after the `my:soundness-review` bullet:

```
- **`my:spec-review`** = *system-thinking* review of one `-spec.md`: builds a component/connection model, judges boundaries, contracts, state ownership, failure spread, fit and the spec rules; labels findings `editorial` or `design`; report to `docs/plans/`. Required step 2 of the Spec → Plan flow.
```

- [ ] **Step 4: Green**

```bash
grep -c 'my:spec-review' "$WT/GLOBAL-CLAUDE.md"          # 3
grep -n 'Three reviewers' "$WT/GLOBAL-CLAUDE.md"          # 1 line
grep -n 'Two diff reviewers' "$WT/GLOBAL-CLAUDE.md"       # no output
```

- [ ] **Step 5: Commit**

```bash
git add GLOBAL-CLAUDE.md
git commit -m "docs(global): require my:spec-review in the Spec → Plan flow

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Skill selection, then integrate

- [ ] **Step 1: Skill selection (fresh headless session)**

```bash
cd "$WT" && claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits --output-format stream-json --verbose \
  "Review docs/plans/2026-09-11-retire-planner-path-spec.md" > "$SCRATCH/green/select.jsonl"
grep -o '"skill":"my:[a-z-]*"' "$SCRATCH/green/select.jsonl" | sort -u
```

Expected: `"skill":"my:spec-review"` and not `my:soundness-review`. The headless session loads the worktree plugin but the main checkout's `~/.claude/CLAUDE.md`, so this tests the skill descriptions alone. That is the risk being tested. Move the review it writes to `$SCRATCH/green/` so it is not committed.

If it selects the wrong skill, sharpen the `description` of `my:spec-review`, amend the Task 2 commit, and rerun.

- [ ] **Step 2: Final lint over all changed files**

Run: `git -C "$WT" diff --name-only main... | grep '\.md$' | xargs markdownlint-cli2 2>&1 | grep error | grep -v -E 'MD013|MD060'`
Expected: no output.

- [ ] **Step 3: Integrate**

Invoke `superpowers:finishing-a-development-branch`, overridden by `GLOBAL-CLAUDE.md`:

```bash
cd /home/dchris/projects/claude-setup && git status --short   # empty
git merge --squash feat/spec-review-skill
git commit -m "feat(my-plugin): add my:spec-review and require it in the spec flow

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
git worktree remove "$WT"
```

Do not delete the branch.

- [ ] **Step 4: Post-merge check**

`~/.claude/CLAUDE.md` now resolves to the new text. Run `grep -c 'my:spec-review' ~/.claude/CLAUDE.md` → `3`. The running session still has the old plugin loaded; a new `claude` session picks up the skill.

---

## Dependencies

- No new packages.
- `claude` CLI with `-p`, `--plugin-dir`, `--permission-mode`, `--output-format stream-json` (confirmed with `claude --help`).
- `markdownlint-cli2` (already used per `GLOBAL-rules/markdown.md`).
- Task order is fixed: Task 3 and Task 4 name the skill created in Task 2.

## Risk

- **Headless runs cost money and time.** About seven Opus review runs (Task 1: 1, Task 2: 4, Task 3: 1, Task 5: 1). Accepted to get real, tool-filtered results.
- **Report checks are grep-based.** They prove the right labels appear near the right words, not that the reasoning is good. Mitigation: read the planted-defect report in full (Task 2 Step 6).
- **LLM output varies between runs.** A check can pass once and fail once. If a Green check fails, rerun once before editing. If it fails twice, fix the prompt.
- **Test files leak into commits.** The planted spec and its report are moved out of the worktree before each commit; `git status --short` checks guard it.
- **Task 3 needs a clean tree** to reach plan-review mode, so its commit comes before its Green run. Amend if the run fails.
- **Reversibility: full.** One squash commit on `main`; revert it to undo. The branch is kept.

## Self-review against the spec

| Spec item | Task |
|---|---|
| D1 separate skill and agent | Task 2 |
| D2 System Model first | Task 2 Steps 2-3, checked in Steps 6-7 |
| D3 six criteria, out-of-scope list | Task 2 Step 3, checked in Steps 6-7 |
| D4 report path, layout, collision | Task 2 Steps 3-4, checked in Step 7 |
| D5 evidence, Critical exception, class | Task 2 Step 3, checked in Step 6 |
| D6 flow step and split fix authority | Task 2 Step 4 (§5), Task 4 Step 2 |
| D7 routing edits | Task 3, Task 4 Step 3 |
| D8 ignores working tree | Task 2 Step 4 (§0-1: no git diff) |
| Failure handling (usage, missing file, malformed prompt, size guard) | Task 2 Steps 2 and 4 |
| Copied-rules cross-reference | Task 2 Steps 3 and 5 |
| Tests 1-5 | Task 1, Task 2 Steps 6-8, Task 3 Step 4, Task 5 Steps 1-2 |
