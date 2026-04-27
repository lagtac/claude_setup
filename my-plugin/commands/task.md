---
description: Direct implementation with structured requirements gathering
---

# Problem-Solving Guidelines

## Approach

Ultrathink step-by-step before implementing. For complex problems:

1. **Analyze** the problem along these dimensions: (1) edge cases (empty/null inputs, boundary values, unusual sizes), (2) error paths and how failures propagate, (3) concurrency or shared-state assumptions, (4) integration points with existing code (callers, callees, shared utilities). Show your reasoning for each dimension that applies.
2. **Outline** your approach before writing code — list the files you will touch and the high-level change in each.
3. **Implement** the solution.
4. **Review** for potential issues against the same four dimensions.

## Requirement Gathering

Before implementing any solution, use the AskUserQuestion tool to fully understand the user's intent:

1. Ask clarifying questions about requirements, constraints, and expected behavior
2. Confirm your understanding of edge cases and priorities
3. Only proceed to implementation once you have sufficient context

Do not assume requirements—when in doubt, ask.

## Code Quality Standards

**Do:**

- Write self-documenting code with clear, descriptive naming
- Consider and handle edge cases explicitly
- Use concise documentation comments for public APIs
- Follow established patterns in the codebase
- Address root causes, not symptoms

**Don't:**

- Use inline comments (code should be self-explanatory)
- Implement bandaid fixes or temporary workarounds
- Add fallback logic that masks underlying issues
- Include backwards compatibility shims
- Over-engineer beyond what's required

## Output Format

Provide:

1. **Brief Analysis**: Key considerations and edge cases identified
2. **Solution**: Clean, production-ready code
3. **Summary**: One-line description of changes made

## Version Control

Commit changes in logical units — one commit per coherent change (e.g., one per feature, fix, or refactor). Do not bundle unrelated changes into a single commit. Follow conventional commits guidelines for each.

---

## Problem

$ARGUMENTS
