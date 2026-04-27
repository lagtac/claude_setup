---
name: tune-claude-instructions
description: >
  Use when the user wants to audit or tune Claude instruction files (CLAUDE.md,
  AGENTS.md, agent definitions, command templates, skill files) for
  literal-instruction-following models like Opus 4.7+. Trigger on requests like
  "audit my CLAUDE.md for 4.7", "my agents got worse on the new model",
  "make my prompts more specific", "tune my prompts", or invocation via
  /tune-claude-instructions.
---

# Tune Claude Instructions

Audit and tune Claude instruction files for **literal-instruction-following** models (Opus 4.7+). These models follow prompts as written and allocate less reasoning to tasks that look simple — so vague templates that worked on 4.6 now produce shallow output.

The fix is **specificity**: enumerate scope, request reasoning explicitly, specify output format. This skill applies that fix surgically — it grades each file, proposes targeted edits, and waits for your approval before writing.

## What this skill is *not*

This skill audits **prompt-template specificity**. It does **not** audit general project context (build commands, architecture, gotchas) — that is the job of `claude-md-management:claude-md-improver`. The two are complementary: run this one when prompts feel thin or when migrating to a more literal model; run the other when onboarding a project to Claude Code.

## Steps

### 1. Discover instruction files

Glob the project for prompt-template files. Skip vendored and build directories.

```bash
# Project context
find . -maxdepth 3 -type f \( -name "CLAUDE.md" -o -name "AGENTS.md" \) \
  -not -path "*/node_modules/*" -not -path "*/vendor/*" -not -path "*/.git/*"

# Agent definitions, command templates, skills (any depth, any plugin layout)
find . -type f \( \
    -path "*/agents/*.md" \
    -o -path "*/commands/*.md" \
    -o -path "*/skills/*/SKILL.md" \
  \) \
  -not -path "*/node_modules/*" -not -path "*/vendor/*" -not -path "*/.git/*"
```

Only audit `~/.claude/CLAUDE.md` if the user explicitly asks — global instructions affect every project, so changing them silently is high blast radius.

### 2. Read each file in full

The audit is qualitative — there is no shortcut. Read the whole file before grading. Do not grade on filename or first paragraph alone; reasoning prompts and output formats often appear deeper down.

### 3. Grade each file on S / R / F

Three dimensions, each ✅ pass / ⚠️ partial / ❌ fail:

- **S — Scope.** Does the file enumerate the dimensions, fields, or sections the output must cover?
  - ✅ "Write a plan with Context, Files, Steps, Trade-offs, Risk, Testing, Open Questions"
  - ⚠️ "Write a thorough plan covering the main concerns"
  - ❌ "Write a plan"

- **R — Reasoning.** Does the file explicitly request step-by-step reasoning *before* conclusions? Power phrases that pass: "think step by step", "show your reasoning", "before drawing conclusions", "before listing recommendations". Implicit cues like "be thorough" or "be careful" do not pass — 4.7+ takes them at face value and skips ahead to the answer.
  - ✅ "Think step by step. Show your reasoning at each diagnostic stage before drawing conclusions."
  - ⚠️ "Analyze carefully"
  - ❌ (no reasoning prompt at all)

- **F — Format.** Does the file specify the output structure?
  - ✅ A literal markdown skeleton, JSON schema, or numbered template
  - ⚠️ Section names listed but no template shown
  - ❌ "Output the result"

**Severity ladder:**

| Grades | Severity | Action |
|---|---|---|
| All ✅ | **OK** | Skip. Don't pad working prompts. |
| One ⚠️ or one ❌ on a thin file | **Low** | 1–3 line addition. |
| Two ❌, or any ❌ on a workhorse agent/command | **Medium** | Targeted section edit. |
| Three ❌ on a workhorse file | **CRITICAL** | Full rewrite likely. |

A "workhorse" file is one that runs on every invocation of an important workflow — planner, code-reviewer, commit, push. A one-line dispatcher that delegates to an agent is not a workhorse; grade its target instead.

### 4. Output the audit table before any edits

Match this format. One row per file. Severity comes from the ladder in step 3.

```markdown
## Claude Instructions Audit

| File | S | R | F | Severity | Why |
|---|---|---|---|---|---|
| `agents/planner.md` | ❌ | ❌ | ❌ | CRITICAL | No exploration discipline, no reasoning prompt, no plan template embedded |
| `commands/commit.md` | ❌ | ❌ | ❌ | CRITICAL | Two-line template; produces single-commit dumps with vague messages |
| `agents/code-reviewer.md` | ✅ | ⚠️ | ✅ | Medium | Reasoning prompt is implicit ("be thorough"); needs explicit "show reasoning before verdict" |
| `commands/clean-gone-branches.md` | ✅ | n/a | ✅ | OK | Workflow command; reasoning not applicable |
| `skills/dev-reports/SKILL.md` | ✅ | ✅ | ✅ | OK | — |
```

Print the table first, then propose fixes. The user should be able to scan it and scope the change down ("only fix the CRITICAL ones for now").

### 5. Propose fixes per non-OK file

Pick from the **fix-pattern catalog** below and show a diff (or, for a full rewrite, the new file content). Wait for explicit user approval before applying any edit.

#### Fix-pattern catalog

**Pattern A — Embed inherited standards.** Subagents do *not* inherit project `CLAUDE.md`. Any rule the agent must follow has to live in the agent file itself. When auditing an agent that references "the project's planning standards" or assumes shared context, copy the relevant standards from `CLAUDE.md` directly into the agent. *Why it works:* a subagent loads only its own definition + its tools list. If the rule is not in that file, the agent never sees it.

**Pattern B — Replace vague directives with power phrases.** Phrases like "use sequential thinking", "analyze deeply", "be thorough" are ambient and 4.7+ ignores them. Replace with explicit reasoning prompts:
- "Think step by step. Show your reasoning at each numbered stage before drawing conclusions."
- "Before assigning a verdict, write 2–4 sentences connecting your findings to the verdict."

*Why it works:* literal-following models allocate thinking budget to whatever the prompt explicitly asks for. "Show your reasoning" is a budget-allocation request; "be thorough" is not.

**Pattern C — Enumerate dimensions.** When a prompt says "analyze X", the output covers whatever the model lands on first. Enumerate:
- "Analyze for: (1) edge cases (empty/null inputs, boundary values), (2) error paths, (3) concurrency or shared-state assumptions, (4) integration points."

*Why it works:* the model now has a checklist of dimensions to address rather than a vague "analyze".

**Pattern D — Force checklist completeness.** Checklists in prompts get partially evaluated — the model picks the items that look interesting. Add:
- "Evaluate **every** item in the checklist below — do not skip items even when they appear inapplicable. Mark genuinely-inapplicable items as **N/A** with a one-line reason."

*Why it works:* it converts "review against the checklist" from optional advice into a per-item requirement.

**Pattern E — Add explicit abort conditions.** Destructive commands (push, delete, migrate, deploy) should enumerate the exact preconditions that stop execution rather than auto-recover. Example for a push command:
- "Stop and report if: (a) `git status` shows uncommitted changes — do not auto-stash; (b) the branch has no upstream — do not auto-set upstream; (c) local has diverged from upstream — do not force-push."

*Why it works:* 4.7+ executes literally. If the prompt does not say "stop", the model fills in the gap with a guess. Abort conditions remove the guess.

**Pattern F — Add an output template.** When the format grade is ❌, paste a literal markdown skeleton showing every required heading. Don't just list section names in prose — show the actual template with `## Heading` lines, so the model emits matching structure.

*Why it works:* templates anchor structure deterministically; prose descriptions of structure get loosely interpreted.

### 6. Apply approved edits and re-grade

Use the Edit tool for surgical changes; use Write only for full rewrites of CRITICAL files. After editing each file, re-grade it inline and confirm the severity dropped.

If the user wants a durable record, offer to write the audit table plus applied-fixes summary to `docs/plans/YYYY-MM-DD-claude-instructions-audit.md` (matching the user's plan-output convention). Default off — only write when asked.

## Anti-patterns to avoid

- **Don't pad already-strong files.** If S/R/F all pass, skip. Adding more constraints to a working prompt over-constrains and bloats tokens.
- **Don't propose a shared preamble.** It's tempting to write one "4.7 specificity block" and prepend it everywhere. Don't — agents and commands have different jobs and over-shared boilerplate dilutes their actual instructions. Each file owns its standards.
- **Don't grade dispatcher files.** A one-line command like `/plan` that just invokes the planner agent inherits its target's quality — grade the target, not the dispatcher.
- **Don't pile on MUSTs.** Capitalised commands feel forceful but read as noise. Explain *why* the model should do something — literal-following is also literal-understanding. A two-sentence rationale beats a one-word imperative.
- **Don't audit `~/.claude/CLAUDE.md` without explicit consent.** Changing global instructions silently affects every project on the user's machine.
- **Don't conflate "thin" with "broken".** A skill that's 30 lines but specific in all three dimensions is fine. Length is not the metric.

## Common Mistakes

- Grading files by length instead of S/R/F. A 5-line file can be specific; a 100-line file can be vague.
- Treating "be careful", "be thorough", "think hard" as passing the Reasoning dimension. They don't — only explicit reasoning prompts do.
- Forgetting to re-grade after editing. Without the re-grade, you can't tell if the fix landed.
- Over-fitting to the article that motivated this skill. The pattern (specificity > vagueness) generalises beyond Opus 4.7 — apply it whenever a model behaves more literally than expected.

## Reference

This skill encodes the audit pattern from `docs/plans/2026-04-27-opus-4-7-prompt-tuning.md` (in the `claude-setup` repo), which applied the same S/R/F grading and fix-pattern catalog to seven of this plugin's own templates. Read that file for a worked example showing the audit table, severity ladder, and per-file rationale.
