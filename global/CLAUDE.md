# Instructions

**Precedence:** this file and the method file a project imports are the highest authority: when plan mode, a skill or a system default conflicts, follow them. The rules in this file hold under every method. A method file may add rules. It may name an exception to a rule in this file only by naming the rule.

**Important:**

- Always use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- The full format is `type(scope): sentence`. The scope is the part of the codebase affected; each project defines its own scopes. Projects that already use `type:` without a scope keep that format.
- Common types: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`
- Never add new dependencies without approval

## Communication

- Write to be understood — short sentences, terms defined at first use, no idioms. The full ruleset is the `plain` output style (`global/output-styles/plain.md`, symlinked to `~/.claude/output-styles/`), which is enabled via `"outputStyle": "plain"` in `~/.claude/settings.json`. **Edit the style file, not this line** — this line is only a fallback for when the style is not loaded (it does not reach subagents, which run their own system prompt).
- Challenge assumptions — propose the best solution, not just a solution

## Code

- Match the surrounding code — read sibling files for naming, structure and idiom before adding new ones. Consistency with what is there beats a preference of your own.

## Engineering standards

These standards apply to every planning workflow: built-in plan mode, a method's own planning steps, and any agent that writes an implementation plan.

**Verify against ground truth, not the artifact.** Discovery — caller lists, filenames, parameters — must come from executing against the real system (search the repo, run the command), never from memory or from re-reading the plan.

### Critical Thinking

- Challenge assumptions — don't rubber-stamp ideas
- If a request is unclear, over-scoped, or misguided, say so directly
- Present arguments both for and against proposed approaches
- If the existing codebase already solves the problem, point that out instead of planning new work
- If unsure about something, say so — do not speculate

### Mandatory Exploration

Before proposing any changes:

0. Map structure with the built-in `LSP` tool — `workspaceSymbol` to locate a symbol, `findReferences` / `incomingCalls` for its callers, `documentSymbol` for a file's shape. Announce using LSP. It reads live from the language server, so there is no index to refresh and no staleness to check. It resolves against the session's project root, so run it from the repo you are asking about.

Never infer that no server is configured. The language, the absence of `.ts`
files, a `checkJs: false` tsconfig and a "vanilla JS" project shape are all
worthless as evidence — servers are enabled globally as plugins and resolve
symbols in plain `.js`. Calling `LSP` and reading its answer is the only
reliable signal, and it costs one call.

If no language server is configured for the file type, `LSP` returns an error — report that and use the builtins:

1. Use Glob to find relevant files and understand project structure
2. Use Grep to search for related patterns, imports, and usages
3. Use Read to examine the actual implementation of files you'll modify or extend
4. Identify existing patterns, conventions, and abstractions already in use
5. Check for existing solutions that might already cover the request

Do not propose changes to code you haven't read. Do not assume file contents.

### Reference Sweep

When a change removes, renames or changes the signature of a cross-file symbol (function, type, route/event name, config/DI key, field, file-naming scheme), find every reference with **both** a symbol-reference tool **and** a plain text search for the name token (string-literal refs — routes, DI keys, ORM eager-loads, templates — are invisible to symbol tools). Handle every hit, including cross-repo consumers.

### Simplicity Rules

- No over-engineering: solve the stated problem, nothing more
- No premature abstractions: three similar lines are better than a premature helper
- No hypothetical future requirements: design for what's needed now
- Prefer editing existing files over creating new ones
- If a solution requires more than ~3 new files, question whether the scope is right

<!--
Language-specific command cheatsheets (PHP/Laravel, Docker, Markdown, JS/TS, Python)
were moved to path-scoped rules in global/rules/ (symlinked to ~/.claude/rules/).
They load only when Claude reads a matching file type, keeping this file's always-loaded
context lean. See global/rules/<lang>.md.
-->

## HTTP Requests

- Always prefer `curl` over WebFetch for API calls and downloading files
- Use WebFetch only for reading documentation pages
