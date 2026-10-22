---
paths:
  - "**/*.{py,js,ts,jsx,tsx,mjs,cjs,vue,php,sh,go,rs,java,rb,lua,sql,css,scss,html}"
  - "**/{package.json,composer.json,pyproject.toml,Dockerfile}"
  - "**/docs/plans/*.md"
---

# Engineering rules

## Code

- Match the surrounding code — read sibling files for naming, structure and idiom before adding new ones. Consistency with what is there beats a preference of your own.

## Engineering standards

These standards apply to every planning workflow: built-in plan mode, a method's own planning steps, and any agent that writes an implementation plan.

**Verify against ground truth, not the artifact.** Discovery — caller lists, filenames, parameters — must come from executing against the real system (search the repo, run the command), never from memory or from re-reading the plan.

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
