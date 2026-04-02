## Instructions

**Important:**

- Always write plans, designs, and specs to `docs/plans/YYYY-MM-DD-<slug>.md`
- Always write code reviews to `docs/reviews/YYYY-MM-DD-<slug>.md`
- Always use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- Common prefixes: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`
- Do not add new dependencies without approval

## Communication

- Be concise and direct
- Challenge assumptions — propose the best solution, not just a solution
- Follow existing patterns — check sibling files before creating new ones

## Git Workflow

All non-trivial work (features, refactors, multi-file changes) MUST use feature branches with squash-merge. Two git aliases are available:

- **`git start <name>`** — creates `feat/<name>` from latest main
- **`git finish "commit message"`** — squash-merges to main, commits, deletes branch

### When to use feature branches

- Any task that will produce 2+ commits
- Any task from a plan or spec
- Any task involving code changes + tests

### When NOT to use (commit directly to main)

- Single-commit fixes (typo, stale test assertion)
- Documentation-only changes
- Config/gitignore tweaks

## Planning Standards

These standards apply to all planning workflows — built-in plan mode, the `/plan` command, and any agent producing implementation plans.

### Critical Thinking

- Challenge assumptions — don't rubber-stamp ideas
- If a request is unclear, over-scoped, or misguided, say so directly
- Present arguments both for and against proposed approaches
- If the existing codebase already solves the problem, point that out instead of planning new work
- If unsure about something, say so — do not speculate

### Mandatory Exploration

Before proposing any changes:

1. Use Glob to find relevant files and understand project structure
2. Use Grep to search for related patterns, imports, and usages
3. Use Read to examine the actual implementation of files you'll modify or extend
4. Identify existing patterns, conventions, and abstractions already in use
5. Check for existing solutions that might already cover the request

Do not propose changes to code you haven't read. Do not assume file contents.

### Simplicity Rules

- No over-engineering: solve the stated problem, nothing more
- No premature abstractions: three similar lines are better than a premature helper
- No hypothetical future requirements: design for what's needed now
- Prefer editing existing files over creating new ones
- If a solution requires more than ~3 new files, question whether the scope is right

### Trade-Off Analysis

For any non-trivial decision, present alternatives:

- **Option A**: [approach] — Pros: ... / Cons: ...
- **Option B**: [approach] — Pros: ... / Cons: ...
- **Recommendation**: [which and why]

### Risk Awareness

- Flag anything that's hard to reverse (schema changes, API contracts, data migrations)
- Note the blast radius: how many files/modules are affected?
- Identify what could break and how to detect it
- Call out if manual testing or deployment steps are needed

### Plan Output Format

Plans written to `docs/plans/YYYY-MM-DD-<slug>.md` must follow this structure:

```
# {Feature} Plan

## Context
[What problem are we solving? Why? What exists today?]

## Files to Modify/Create
[List each file with a brief description of what changes]

## Step-by-Step Implementation
[Numbered steps, each small enough to be a single commit]

## Trade-Offs / Alternatives Considered
[Options evaluated and why this approach was chosen]

## Dependencies
[External packages, env vars, config changes needed — or "None"]

## Testing Strategy
[What tests to add/modify, how to verify the feature works]

## Open Questions
[Anything that needs user input before implementation starts]
```

## HTTP Requests

- Always prefer `curl` over WebFetch for API calls and downloading files
- Use WebFetch only for reading documentation pages

## Editing Plugin Files

- Command files are prompt templates — `$ARGUMENTS` is a placeholder, not a variable to define.
- Agent frontmatter fields (`name`, `description`, `tools`, `model`) are parsed by Claude Code; keep them accurate.
- The plugin manifest (`.claude-plugin/plugin.json`) must accurately list the `commands` and `agents` directory paths.
