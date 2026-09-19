---
name: tune-claude-instructions
description: >
  Use when the user wants to audit or tune Claude instruction files (CLAUDE.md,
  AGENTS.md, agent definitions, command templates, skill files) for
  literal-instruction-following models (Opus 4.7 and every later model). Also
  flags prompts that require tools a subagent may not receive. Trigger on requests
  like "audit my CLAUDE.md for the new model", "my agents got worse on the new model",
  "make my prompts more specific", "tune my prompts", "audit my global setup",
  or invocation via /my:tune-claude-instructions (optionally with --global or a path).
argument-hint: "[--global] [path]"
---

# Tune Claude Instructions

Audit and tune Claude instruction files for **literal-instruction-following** models. Opus 4.7 was the first; every later model behaves the same way. These models follow prompts as written and allocate less reasoning to tasks that look simple — so vague templates that worked on older models now produce shallow output.

The fix is **specificity**: enumerate scope, put reasoning before conclusions, specify output format. A literal model also cannot work around a step it has no tool for, so the audit checks that every tool a prompt requires will be present. Three more problems matter on the newest models (Fable 5.1, Opus 5): two instructions that contradict each other (the model picks one unpredictably), instructions that assume a harness feature that no longer exists, and heavy emphasis (ALL CAPS, "CRITICAL") that makes the model apply a rule too broadly. The rubric checks all three. This skill applies these fixes surgically — it grades each file, proposes targeted edits, and waits for your approval before writing.

Per-file grading is rubric-driven (see `references/grading-rubric.md` — the single source of truth, used by both grading paths) and parallelizes cleanly. With **6 or more files**, step 3 fans the work out to parallel Haiku subagents; with 1–5, the main session grades inline. Also grade inline, at any count, when the user asks for a thorough review: Haiku misses contradictions between files, because each grader sees one file. Discovery, table assembly, fix proposals, and edits (steps 1, 4, 5, 6) always run on the main model.

## Arguments

`$ARGUMENTS` — parse for the `--global` flag and an optional path. Any other words describe what the user wants from the audit; keep them as its focus.

- **No flag (default)** — audit project files: the project's `CLAUDE.md` / `AGENTS.md`, agent definitions, command templates, and skill files under the current working directory.
- **A path** — audit the files under that directory instead of the current working directory, for example a plugin that lives in another repository (`~/projects/claude-setup/my-plugin`). If the user names a plugin or folder in words instead, find its path first (`find ~ -maxdepth 4 -type d -name "<name>"`) and confirm it in one line before auditing.
- **`--global`** — audit the user's global setup instead: `~/.claude/CLAUDE.md`, `~/.claude/agents/`, `~/.claude/commands/`, `~/.claude/skills/`. Treat the flag as the explicit consent that satisfies the global-audit anti-pattern, but still confirm before writing each edit because the blast radius covers every project on the machine.

`--global` switches scope, it does not extend it. To audit both project and global in one session, run the skill twice.

## Scope: directive content, wherever it lives

This skill audits **directive content** — the parts of a file that tell Claude what to do, how to reason, what to output. Directive content includes:

- Prompt templates (agents, commands, skills) — the obvious case.
- Instruction-style passages embedded in `CLAUDE.md` / `AGENTS.md` / `.claude/docs/*.md` — e.g. *"Always use Form Requests, not inline validation"*, *"Follow Red-Green-Refactor"*, *"When the user asks X, do Y"*.

It does **not** audit **pure context** — build-command tables, architecture diagrams, env-var lists, API references, file inventories. Pure context has no S/R/F surface; grade only the directive passages within a file, not the whole file by filename. A `CLAUDE.md` is rarely all-directive or all-context — separate the two as you read.

Complementary skill: `claude-md-management:claude-md-improver` audits content **completeness** on a different rubric (commands current? architecture covered? gotchas captured?). Run that to fix gaps; run this to fix vagueness in directives that are already present. The two are orthogonal — neither replaces the other.

## Steps

### 1. Discover instruction files

Branch on `$ARGUMENTS`:

**Default (no `--global`)** — glob the project (or the given path, in place of `.`) for prompt-template files. Skip vendored and build directories, and `.claude/worktrees/`, which holds copies of the same files. If the path you audit is itself inside a worktree, drop that one filter.

```bash
# Project context
find . -maxdepth 3 -type f \( -name "CLAUDE.md" -o -name "AGENTS.md" \) \
  -not -path "*/node_modules/*" -not -path "*/vendor/*" -not -path "*/.git/*" \
  -not -path "*/.claude/worktrees/*"

# Agent definitions, command templates, skills and their supporting files
# (any depth, any plugin layout)
find . -type f \( \
    -path "*/agents/*.md" \
    -o -path "*/commands/*.md" \
    -o -path "*/skills/*/*.md" \
    -o -path "*/skills/*/references/*.md" \
  \) \
  -not -path "*/node_modules/*" -not -path "*/vendor/*" -not -path "*/.git/*" \
  -not -path "*/.claude/worktrees/*"
```

The skill's supporting files matter most. A dispatch prompt such as `code-reviewer-prompt.md` reaches its subagent whatever the agent file says (Pattern G), so grade it like an agent file.

**`--global`** — audit the user's global Claude setup under `~/.claude/`.

```bash
ls ~/.claude/CLAUDE.md 2>/dev/null
find ~/.claude/agents   -maxdepth 2 -type f -name "*.md"      2>/dev/null
find ~/.claude/commands -maxdepth 2 -type f -name "*.md"      2>/dev/null
find ~/.claude/skills   -maxdepth 3 -type f -name "SKILL.md"  2>/dev/null
```

Do **not** descend into `~/.claude/projects/` (per-project session/memory state) or `~/.claude/plugins/` (third-party plugins the user does not own). Audit only files the user authored.

### 2. Read and grade each file

Apply the rubric in `references/grading-rubric.md` to every discovered file. The rubric covers reading discipline, directive-vs-context separation, the S/R/F dimensions with examples, dispatcher handling, and the severity ladder. Both grading paths use the same rubric so results are comparable.

- **1–5 files**: grade inline. Read each file, apply the rubric, hold the results in memory keyed by path.
- **6+ files**: fan out to parallel Haiku subagents — see step 3.

Either path produces the same `{path, s, r, f, severity, why}` shape, which feeds the step 4 audit table. The rubric's tool, harness and consistency checks do not add columns. They raise the severity and are named in `why`.

After grading each file on its own, compare the files with each other (main session only; a single-file grader cannot see this). Look for a rule stated two ways in two files, a copied block that has drifted from its source, and a skill that sends work to an agent whose own instructions disagree with it. Each such pair is a finding on both files.

### 3. Dispatch (6+ files, unless grading inline)

Skip this step entirely when grading 5 or fewer files, or when step 2 chose inline grading for a thorough review — spawn overhead exceeds the savings, and step 5 typically re-reads the source anyway when drafting fixes. The threshold exists because parallelism only pays off once there's enough work to amortise the overhead.

Spawn one Agent call per file in a **single message** so they run concurrently. Use `subagent_type: "general-purpose"` and `model: "haiku"`.

Each subagent gets this prompt — substitute `<RUBRIC_PATH>` for the absolute path to `references/grading-rubric.md` inside this skill's directory (resolve from the running SKILL.md's location), and `<PATH>` for the file being audited:

```
Read the grading rubric at <RUBRIC_PATH>, then audit the Claude instruction file at <PATH> using that rubric.

Return ONE JSON object on a single line, no prose, no code fences:
{"path": "<PATH>", "s": "✅"|"⚠️"|"❌"|"n/a", "r": "✅"|"⚠️"|"❌"|"n/a", "f": "✅"|"⚠️"|"❌"|"n/a", "severity": "OK"|"Low"|"Medium"|"CRITICAL", "why": "<one short sentence justifying the grades>", "problem_passages": ["<short quoted excerpt under 200 chars>", ...]}

problem_passages: quote up to 3 short excerpts from the audited file that drove any ⚠️ or ❌ grade. The orchestrator uses these as hints when drafting fixes. Empty array `[]` for OK files.
```

Wait until every subagent has returned. Then aggregate the returned JSON rows into a single in-memory list keyed by path before assembling the step 4 table. If any subagent returns malformed JSON or fails, grade that one file inline rather than retrying — one bad row shouldn't block the rest. The fix-proposal phase (step 5) may need to re-read files for accurate diffs; `problem_passages` is a hint, not a substitute for the source.

### 4. Output the audit table before any edits

Match this format. One row per file. Severity comes from the ladder in `references/grading-rubric.md`.

```markdown
## Claude Instructions Audit

| File | S | R | F | Severity | Why |
|---|---|---|---|---|---|
| `commands/commit.md` | ❌ | ❌ | ❌ | CRITICAL | Two-line template; produces single-commit dumps with vague messages |
| `agents/code-reviewer.md` | ✅ | ⚠️ | ✅ | Medium | Reasoning prompt is implicit ("be thorough"); needs explicit "show reasoning before verdict" |
| `commands/clean-gone-branches.md` | ✅ | n/a | ✅ | OK | Workflow command; reasoning not applicable |
| `skills/dev-reports/SKILL.md` | ✅ | ✅ | ✅ | OK | — |
| `.claude/docs/frontend.md` | ✅ | n/a | n/a | OK | Directives concrete (`pnpm`, semantic-class rule paired with rationale); no output prompts to grade |
| `.claude/docs/conventions.md` | ⚠️ | n/a | n/a | Low | Two directives use "when appropriate" / "be concise"; rest concrete |
| `CLAUDE.md` (dispatcher) | n/a | n/a | n/a | OK | Pure `<tag @path>` includes; grade the included files |
```

Print the table first, then propose fixes. The user should be able to scan it and scope the change down ("only fix the CRITICAL ones for now").

### 5. Propose fixes per non-OK file

Pick from the **fix-pattern catalog** below and show a diff (or, for a full rewrite, the new file content). Wait for explicit user approval before applying any edit.

#### Fix-pattern catalog

**Pattern A — Embed inherited standards.** Subagents do *not* inherit project `CLAUDE.md`. Any rule the agent must follow has to live in the agent file itself. When auditing an agent that references "the project's planning standards" or assumes shared context, copy the relevant standards from `CLAUDE.md` directly into the agent. *Why it works:* a subagent loads only its own definition + its tools list. If the rule is not in that file, the agent never sees it.

**Pattern B — Replace vague directives with reasoning the output must contain.** Phrases like "use sequential thinking", "analyze deeply", "be thorough" ask for nothing a reader can check, and literal-following models pass over them. Replace them with a reasoning step that appears in the output, before the conclusion:
- "At each numbered stage, write what you checked and what it showed before moving on."
- "Before the verdict, write 2–4 sentences connecting your findings to the verdict."

*Why it works:* the newest models already reason internally, so a bare "think step by step" adds little. What still changes the result is making the reasoning part of the required output and placing it before the verdict: the model then cannot state a conclusion its written evidence does not support.

**Pattern C — Enumerate dimensions.** When a prompt says "analyze X", the output covers whatever the model lands on first. Enumerate:
- "Analyze for: (1) edge cases (empty/null inputs, boundary values), (2) error paths, (3) concurrency or shared-state assumptions, (4) integration points."

*Why it works:* the model now has a checklist of dimensions to address rather than a vague "analyze".

**Pattern D — Force checklist completeness.** Checklists in prompts get partially evaluated — the model picks the items that look interesting. Add:
- "Evaluate **every** item in the checklist below — do not skip items even when they appear inapplicable. Mark genuinely-inapplicable items as **N/A** with a one-line reason."

*Why it works:* it converts "review against the checklist" from optional advice into a per-item requirement.

**Pattern E — Add explicit abort conditions.** Destructive commands (push, delete, migrate, deploy) should enumerate the exact preconditions that stop execution rather than auto-recover. Example for a push command:
- "Stop and report if: (a) `git status` shows uncommitted changes — do not auto-stash; (b) the branch has no upstream — do not auto-set upstream; (c) local has diverged from upstream — do not force-push."

*Why it works:* a literal-following model executes what is written. If the prompt does not say "stop", the model fills in the gap with a guess. Abort conditions remove the guess.

**Pattern F — Add an output template.** When the format grade is ❌, paste a literal markdown skeleton showing every required heading. Don't just list section names in prose — show the actual template with `## Heading` lines, so the model emits matching structure.

*Why it works:* templates anchor structure deterministically; prose descriptions of structure get loosely interpreted.

**Pattern G — Require only tools the reader will have.** An agent's `tools:` line is not a promise. In 310 subagent transcripts on this machine (September 2026), subagents called `Bash` 7445 times, `Grep` once, and `Glob`, `LSP`, `Task` and `Agent` never. So treat `Grep`, `Glob` and `LSP` as unreliable in a subagent. A main session in auto mode can also lack `Grep` and `Glob`. Rewrite each such step as a `Bash` command.

Spawning is different. A subagent can spawn its own subagents (Claude Code v2.1.172 and later) only when its `tools:` line lists `Agent` and nesting is on; `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` turns it off. A prompt that spawns sub-agents from an agent whose `tools:` line lacks `Agent` cannot run. Add `Agent` to the line, or do the work in the agent itself.

Examples:
- "Use Grep to find every caller" → "Find every caller with Bash: `grep -rn '<name>' .`"
- "Spawn a sub-agent to read the diff", in an agent with no `Agent` tool → "Read the diff yourself with Bash: `git diff <range> -- <file>`, one file at a time."

Check two places. The agent file is one. The dispatch prompt that a skill or command builds for that agent is the other, and it matters more: it reaches the agent whatever the agent file says.

*Why it works:* a model with no tool for a step skips the step or invents a substitute, and nothing reports it. `Bash` is the one search tool that is always present.

**Pattern H — Resolve contradictions and state precedence.** When two instructions cannot both be followed, a literal model picks one, and not always the same one. Worked examples count as instructions, and an example usually beats the rule it breaks, especially one labelled "follow literally". Fix the losing side so both say the same thing. Where two sources may legitimately differ (a skill's defaults and a project's `CLAUDE.md`), add one sentence that names the winner:
- "The project's `CLAUDE.md` wins over every default here, including the bold rows of the table."

*Why it works:* the model no longer has to guess which instruction the author meant.

**Pattern I — Update harness assumptions.** Prompts go stale when the harness changes. Check each instruction that names a tool parameter, a command or a user interaction:
- A parameter the tool no longer has (for example `run_in_background` on an Agent tool whose subagents always run in the background). Replace it with the outcome: "Wait for the agent's result before step 4, and do nothing else until it arrives."
- A command that opens an editor or waits for input (`git rebase -i` without `GIT_SEQUENCE_EDITOR`, `reword`, `git commit` without `-m`). Replace it with a non-interactive form.
- A question to the user through `AskUserQuestion` with no fallback. Add one: "If `AskUserQuestion` is not available, print the plan, say what reply runs it, and end the turn."

*Why it works:* a literal model tries the stale step exactly as written; it hangs, fails, or improvises a substitute nobody reviewed.

**Pattern J — Calm the emphasis.** Replace ALL CAPS, "CRITICAL", "you MUST" and "NEVER" with a plain sentence and a reason, except for the one or two rules that truly override everything else. A persona line ("You are a senior engineer with 15+ years…") adds little; replace it with the task and the standard it must meet.

*Why it works:* the newest models respond strongly to emphasis. A shouted rule gets applied beyond its intended scope and crowds out the rules around it.

### 6. Apply approved edits and re-grade

Use the Edit tool for surgical changes; use Write only for full rewrites of CRITICAL files. After editing each file, re-grade it inline and confirm the severity dropped.

If the user wants a durable record, offer to write the audit table plus applied-fixes summary to `docs/plans/YYYY-MM-DD-claude-instructions-audit.md` (matching the user's plan-output convention). Default off — only write when asked.

## Anti-patterns to avoid

- **Don't pad already-strong files.** If S/R/F all pass, skip. Adding more constraints to a working prompt over-constrains and bloats tokens.
- **Don't propose a shared preamble.** It's tempting to write one "specificity block" and prepend it everywhere. Don't — agents and commands have different jobs and over-shared boilerplate dilutes their actual instructions. Each file owns its standards.
- **Don't grade dispatcher files.** A one-line command like `/my:summarize` that just invokes the summarizer agent, or a `CLAUDE.md` that's only `<tag @path>` includes, has no S/R/F surface — grade the targets/included files, not the dispatcher.
- **Don't dismiss `CLAUDE.md` / docs files by filename.** A context-heavy file with embedded directives ("Always X", "Never Y", "When X, do Y") has a real S/R/F surface in those passages even though the rest of the file is pure reference. Read for directive content before deciding `n/a`.
- **Don't pile on MUSTs.** Capitalised commands feel forceful but read as noise. Explain *why* the model should do something — literal-following is also literal-understanding. A two-sentence rationale beats a one-word imperative.
- **Don't audit global files (`~/.claude/...`) without explicit consent.** Either the user asks directly or `--global` is passed. Even with consent, confirm before each write — global edits affect every project on the machine.
- **Don't conflate "thin" with "broken".** A skill that's 30 lines but specific in all three dimensions is fine. Length is not the metric.

## Common Mistakes

- Grading files by length instead of S/R/F. A 5-line file can be specific; a 100-line file can be vague.
- Treating "be careful", "be thorough", "think hard" as passing the Reasoning dimension. They don't — only reasoning the output must contain, before its conclusion, does.
- Grading each file alone and missing the contradiction between two of them (Pattern H). Compare the files after grading them.
- Forgetting to re-grade after editing. Without the re-grade, you can't tell if the fix landed.
- Trusting an agent's `tools:` line. `Grep`, `Glob` and `LSP` rarely reach a subagent, whatever that line says. Grade what the prompt requires against what the agent will really get (Pattern G).
- Over-fitting to the article that motivated this skill. The pattern (specificity > vagueness) is not tied to one model — apply it whenever a model behaves more literally than expected.

## Reference

This skill encodes the audit pattern from `docs/plans/2026-04-27-opus-4-7-prompt-tuning.md` (in the `claude-setup` repo), which applied the same S/R/F grading and fix-pattern catalog to seven of this plugin's own templates. Read that file for a worked example showing the audit table, severity ladder, and per-file rationale.
