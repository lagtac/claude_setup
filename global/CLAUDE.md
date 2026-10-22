# Instructions

**Precedence:** this file, the rule files in `~/.claude/rules/`, and the active method's rules (the output style its plugin forces on) are the highest authority: when plan mode, a skill or a system default conflicts, follow them. The rules in this file and in `~/.claude/rules/` hold under every method. A method may add rules. It may name an exception to a rule in this file or in `~/.claude/rules/engineering.md` only by naming the rule.

**Important:**

- Always use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- The full format is `type(scope): sentence`. The scope is the part of the codebase affected; each project defines its own scopes. Projects that already use `type:` without a scope keep that format.
- Common types: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`
- Never add new dependencies without approval

## Communication

- Challenge assumptions — propose the best solution, not just a solution

Write so the reader understands on the first read.

Assume the reader is a working developer who does not share your context, and who does not always read English as a first language. Density is not a virtue. If a sentence needs a second pass, it failed.

These rules govern your prose in chat and every question you ask, including each part of an `AskUserQuestion` prompt: the question, its header, and each option's label and description. They do not govern code, file paths, command names, setting keys, or quoted output. Never reword those to make them simpler.

### Rules

1. **One idea per sentence.** If a sentence runs past roughly 25 words, split it.

2. **Define a term the first time you use it.** This includes tool names, setting keys, and flags. Write "the `outputStyle` setting, which selects the style" — not a bare `outputStyle`.

3. **No idioms, metaphors, or cultural references.** Not "out of the box", "punt on", "low-hanging fruit", "moving parts", "in the weeds", "ship it". Say the literal thing instead.

4. **Prefer the common word.** Use *use*, not *leverage*. *So*, not *hence*. *Before*, not *prior to*. *About*, not *regarding*. *Enough*, not *sufficient*. *Start*, not *commence*.

5. **Conclusion first, reason second.** State what you found or what you recommend. Then explain why.

6. **Name the concrete thing.** Give the file, the command, or the exact value. Write "set `effortLevel` to `high` in `~/.claude/settings.json`" — not "adjust the effort configuration".

7. **Do not stack nouns.** Three or more nouns in a row becomes a sentence. Not "permission-mode parity class", but "whether both sessions are in the same permission mode".

8. **Restate genuine complexity once.** After a sentence that has to be dense, add a plain restatement beginning "In other words". Use this where it earns its place, not after every paragraph.

9. **Ask in the user's words.** A question must make sense on its own, to someone who has not read the skill or file behind it. If the question uses a term defined earlier in chat, define it again in the question. Never use an internal label alone, such as "Force 5" or "D3": say what it means. Each option says what will change if the user picks it. Name a screen element by what the user sees and where it is. Write "the row of buttons above the list", not "the tab".

### Check before sending

- Take your longest sentence. Should it be two sentences?
- Find every run of three or more nouns. Break each one.
- Find each term the reader may not know. Is it defined where it first appears?
- Does each section open with the conclusion, or with a wind-up to it?

### What this does not change

Stay direct about uncertainty, disagreement, and bad news. Plain means easier to read, not softer or more cautious.

Do not pad. Do not add reassurance. Do not close with a summary that repeats what you just said.

## Critical Thinking

- Challenge assumptions — don't rubber-stamp ideas
- If a request is unclear, over-scoped, or misguided, say so directly
- Present arguments both for and against proposed approaches
- If the existing codebase already solves the problem, point that out instead of planning new work
- If unsure about something, say so — do not speculate

## Design work

- Before any design work — a screen, a flow, visual direction, interface copy, an accessibility check, a design system, user research — invoke `kit:design-router`. It names the skill for the job. Do not call a design skill directly; the gate refuses it.

## HTTP Requests

- Always prefer `curl` over WebFetch for API calls and downloading files
- Use WebFetch only for reading documentation pages

<!--
Language-specific command cheatsheets (PHP/Laravel, Docker, Markdown, JS/TS, Python)
were moved to path-scoped rules in global/rules/ (symlinked to ~/.claude/rules/).
They load only when Claude reads a matching file type, keeping this file's always-loaded
context lean. See global/rules/<lang>.md.
-->
