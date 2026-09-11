---
paths:
  - "**/docs/plans/*.md"
---

# Plan Output Format

Every section is required. Superpowers may substitute its own format; when it
does not, plans use this one. **Dependencies** and **Risk** are non-overridable.

```markdown
# {Feature} Plan

## Context
[What problem are we solving? Why? What exists today? What prompted this change?]

## Files to Modify/Create
[Each file with a brief description of what changes and why. Reference existing functions/utilities to reuse with file paths.]

## Step-by-Step Implementation
[Numbered steps, each small enough to be a single commit. Concrete enough that a developer doesn't need to re-derive the design.]

## Trade-Offs / Alternatives Considered
[Options evaluated, pros/cons, and why this approach was chosen. Skip with a one-liner only if the decision is genuinely trivial.]

## Dependencies
[External packages, env vars, config changes needed — or "None"]

## Risk
[Reversibility, blast radius, what could break, how to detect, manual steps. Required.]

## Testing Strategy
[What tests to add/modify; how to verify the feature works end-to-end. If no automated tests are possible, describe the manual verification.]

## Open Questions
[Anything that needs user input before implementation starts. If none, write "None."]
```

## Output discipline

- Do not skip sections to be brief. Each section is short by default; expand only where the task warrants it.
- If a section genuinely does not apply, write "N/A — [one-line reason]" rather than omitting it.
- Do not write code beyond illustrative snippets inside the plan.
