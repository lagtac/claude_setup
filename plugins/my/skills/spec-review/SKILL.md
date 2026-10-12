---
name: spec-review
description: >
  System-thinking review of one design spec (`docs/plans/*-spec.md`) before its implementation plan is
  written. Builds a model of the spec's components and connections, then judges boundaries, contracts
  and state ownership, failure spread and off-path events in UI, fit with existing code, grounding
  against the repo, and the spec rules (How to read this spec, self-containment,
  Risk/Dependencies/Trade-offs, Visual Language for UI). Every finding is labelled editorial (fix
  freely) or design (ask the author). Writes a durable report to docs/plans/. Use when asked to review
  a spec or design doc, and as the required review step of the Spec → Plan flow. NOT for
  implementation plans, diffs or code — those go to `my:soundness-review`.
---

# Spec Review

Dispatch a fresh-context reviewer subagent to judge whether the system a spec describes holds together. The reviewer builds a System Model first, then judges six criteria against it, and labels every finding `editorial` or `design`.

The criteria, evidence rules and report layout live in `spec-reviewer-prompt.md`. The agent receives the full prompt at dispatch time and must not improvise.

This skill ignores the working tree. It copies the spec to a work file and never runs `git diff`, so uncommitted files elsewhere do not change what it reviews. The reviewer reads the copy itself; the main session never pastes the spec into the prompt.

## Steps

### 0. Check the argument

The args string must be exactly one path to an existing file ending in `.md`. Set `SPEC_PATH` to it, relative to the repo root (`git rev-parse --show-toplevel`).

If args is empty, names more than one path, or the file does not exist, stop and print:

`Usage: my:spec-review <path/to/spec.md> — one existing spec file.`

If the filename does not end in `-spec.md`, continue, and print: `(<SPEC_PATH> does not end in -spec.md; reviewing it as a spec anyway.)`

### 1. Copy the spec

Copy it to a work directory with an absolute path, because the reviewer does not share your working directory, and count its lines:

```bash
WORK_DIR="<scratchpad>/spec-review/$(date +%Y%m%d-%H%M%S)"   # <scratchpad> = the session's scratchpad directory; else WORK_DIR="$(mktemp -d)"
mkdir -p "$WORK_DIR" && cp "$(git rev-parse --show-toplevel)/$SPEC_PATH" "$WORK_DIR/spec.md" && wc -l < "$WORK_DIR/spec.md"
```

The copy is a fixed snapshot: an edit to the spec during the review does not change what the reviewer judges. You do not need to read the spec yourself.

**Size guard.** Above **2000** lines, do not stop. Print `(Spec is <N> lines; the reviewer's coverage may be uneven.)` and add this line to `{{SUBJECT}}`, after its sentence: `Note: this spec is <N> lines. If you cannot assess all of it at the same depth, say so under "Needs Investigation" and name the parts you covered shallowly.`

### 2. Build the dispatch prompt

Read `spec-reviewer-prompt.md` from this skill's directory. Take everything below the first `---` line. Substitute:

- `{{SPEC_PATH}}` → `SPEC_PATH`.
- `{{SUBJECT}}` → ``The spec to review, `<SPEC_PATH>`, is copied to `<WORK_DIR>/spec.md` (<N> lines).`` with the absolute path, then the size note if any. Never paste the spec text itself.
- `{{REPO_ROOT}}` → `"$(git rev-parse --show-toplevel)"`, absolute.
- `{{PLAN_DIRECTORY}}` → the absolute path `"$(git rev-parse --show-toplevel)/docs/plans"`. Subagents do not reliably inherit the session's cwd, so never pass a relative path. Run `mkdir -p` on it first.
- `{{REVIEW_SLUG}}` → `<spec basename without .md>-review`. Example: `docs/plans/2026-09-16-foo-spec.md` → `2026-09-16-foo-spec-review`.

**Collision rule.** If `{{PLAN_DIRECTORY}}/{{REVIEW_SLUG}}.md` exists, append `-2`, then `-3`, until the path is free. Reviews are a record — never overwrite one. Re-reviewing a spec after fixes is the normal case.

### 3. Dispatch the reviewer

Use the Agent tool with `subagent_type: "my:spec-reviewer"`, `description: "Spec review"`, and the composed prompt. Wait for the agent's result before step 4, and do nothing else until it arrives: the caller is waiting. If your Agent tool has a `run_in_background` parameter, leave it off; if subagents always run in the background, continue at step 4 when the completion notice arrives.

### 4. Surface the result

1. Confirm `{{PLAN_DIRECTORY}}/{{REVIEW_SLUG}}.md` exists. If not, print the agent's text output verbatim and say the file write did not happen.
2. Print: `Review written to docs/plans/<filename>.`
3. Read the verdict from the review file's `**Assessment:**` line, not from the agent's summary. If it is `Problematic` or any `Critical` finding exists, print the top finding in two lines, including its class.

### 5. Inside the Spec → Plan flow

When this skill runs as the spec flow's review step, the caller then acts on the findings as follows:

- **`editorial`:** fix it in the spec. Before each fix, check whether it changes what a component owns, a contract, the chosen option, or the scope. If it does, treat it as `design`, whatever its label says.
- **`design`:** do not fix it. Ask the author: "Decision X was picked for reason Y. The review says Y is wrong because Z. Keep X or change it?"
- **Rejected findings:** list each with one line of reasoning.
- Then ask the author to review the spec, the report path and the open design questions together.

## Worked example

```text
0. Args: docs/plans/2026-09-16-foo-spec.md → exists, ends in -spec.md → SPEC_PATH set.
1. Copy to WORK_DIR/spec.md. wc -l → 180 (no size note).
2. Read spec-reviewer-prompt.md; take the body below the first `---`.
   Bash: git rev-parse --show-toplevel → PLAN_DIRECTORY="<root>/docs/plans"; mkdir -p it.
   REVIEW_SLUG=2026-09-16-foo-spec-review; the file exists → 2026-09-16-foo-spec-review-2.
   Substitute SPEC_PATH, SUBJECT, REPO_ROOT, PLAN_DIRECTORY, REVIEW_SLUG.
3. Agent: subagent_type="my:spec-reviewer", description="Spec review", prompt=<composed text>.
4. Confirm <PLAN_DIRECTORY>/2026-09-16-foo-spec-review-2.md exists. Print pointer.
```
