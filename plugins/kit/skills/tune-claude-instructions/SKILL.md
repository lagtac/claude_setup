---
name: tune-claude-instructions
description: >
  Use when the user wants to audit or tune Claude instruction files (CLAUDE.md,
  AGENTS.md, agent definitions, command templates, skill files) for
  literal-instruction-following models (Opus 4.7 and every later model). Also
  flags prompts that require tools a subagent may not receive. Trigger on requests
  like "audit my CLAUDE.md for the new model", "my agents got worse on the new model",
  "make my prompts more specific", "tune my prompts", "audit my global setup",
  or invocation via /kit:tune-claude-instructions (optionally with a path).
argument-hint: "[path]"
---

# Tune Claude Instructions

Audit and tune Claude instruction files for **literal-instruction-following** models. Opus 4.7 was the first; every later model behaves the same way. These models follow prompts as written and allocate less reasoning to tasks that look simple — so vague templates that worked on older models now produce shallow output.

The fix is **specificity**: enumerate scope, put reasoning before conclusions, specify output format. A literal model also cannot work around a step it has no tool for, so the audit checks that every tool a prompt requires will be present. Three more problems matter on the newest models (Fable 5.1, Opus 5): two instructions that contradict each other (the model picks one unpredictably), instructions that assume a harness feature that no longer exists, and heavy emphasis (ALL CAPS, "CRITICAL") that makes the model apply a rule too broadly. The rubric checks all three. It also checks for text the model does not need, such as a rule repeated in three places. This skill applies these fixes surgically — it grades each file, proposes targeted edits, and waits for your approval before writing.

Per-file grading is rubric-driven (see `references/grading-rubric.md` — the single source of truth, used by both grading paths) and parallelizes cleanly. With **6 or more files**, step 3 fans the work out to parallel Haiku subagents; with 1–5, the main session grades inline. Also grade inline, at any count, when the user asks for a thorough review: Haiku misses contradictions between files, because each grader sees one file. Discovery, table assembly, fix proposals, and edits (steps 1, 4, 5, 6) always run on the main model.

## Arguments

`$ARGUMENTS` — parse for an optional path. Any other words describe what the user wants from the audit; keep them as its focus.

- **No path (default)** — audit the instruction files under the current working directory.
- **A path** — audit the files under that directory instead, for example a plugin or a global setup that lives in another repository (`~/projects/claude-setup`). If the user names a plugin or folder in words instead, find its path first (`find ~ -maxdepth 4 -type d -name "<name>"`) and confirm it in one line before auditing.

For the user's global setup, or a path that is `~/.claude` itself, ask which folder holds the real files. When `~/.claude/CLAUDE.md` is a symbolic link, suggest the repository it points into (`git -C "$(dirname "$(readlink -f ~/.claude/CLAUDE.md)")" rev-parse --show-toplevel`): step 1's search skips symbolic links, and edits made in the repository can be committed. When the arguments hold `--global`, say that this skill takes a path instead, and ask this question.

## Scope: directive content, wherever it lives

This skill audits **directive content** — the parts of a file that tell Claude what to do, how to reason, what to output. Directive content includes:

- Prompt templates (agents, commands, skills) — the obvious case.
- Instruction-style passages embedded in `CLAUDE.md` / `AGENTS.md` / `.claude/docs/*.md` — e.g. *"Always use Form Requests, not inline validation"*, *"Follow Red-Green-Refactor"*, *"When the user asks X, do Y"*.

It does **not** audit **pure context** — build-command tables, architecture diagrams, env-var lists, API references, file inventories. Pure context has no S/R/F surface; grade only the directive passages within a file, not the whole file by filename. A `CLAUDE.md` is rarely all-directive or all-context — separate the two as you read.

Complementary skill: `claude-md-management:claude-md-improver` audits content **completeness** on a different rubric (commands current? architecture covered? gotchas captured?). Run that to fix gaps; run this to fix vagueness in directives that are already present. The two are orthogonal — neither replaces the other.

## Steps

### 1. Discover instruction files

Search the project for instruction files. With a path, put its absolute path in place of `$(pwd -P)`: the skip filters below match only full paths. Skip vendored and build directories, and `.claude/worktrees/`, which holds copies of the same files. If the path you audit is itself inside a worktree, drop that one filter. Also skip `.claude/plugins/` (plugins installed from elsewhere) and `.claude/projects/` (session and memory state), which a search of a `.claude` folder would reach.

```bash
# Project context
find "$(pwd -P)" -maxdepth 3 -type f \( -name "CLAUDE.md" -o -name "AGENTS.md" \) \
  -not -path "*/node_modules/*" -not -path "*/vendor/*" -not -path "*/.git/*" \
  -not -path "*/.claude/worktrees/*" \
  -not -path "*/.claude/plugins/*" -not -path "*/.claude/projects/*"

# Agent definitions, command templates, skills and their supporting files,
# and rules folders (any depth, any plugin layout)
find "$(pwd -P)" -type f \( \
    -path "*/agents/*.md" \
    -o -path "*/commands/*.md" \
    -o -path "*/skills/*/*.md" \
    -o -path "*/skills/*/references/*.md" \
    -o -path "*/rules/*.md" \
  \) \
  -not -path "*/node_modules/*" -not -path "*/vendor/*" -not -path "*/.git/*" \
  -not -path "*/.claude/worktrees/*" \
  -not -path "*/.claude/plugins/*" -not -path "*/.claude/projects/*"
```

The skill's supporting files matter most. A dispatch prompt such as `code-reviewer-prompt.md` reaches its subagent whatever the agent file says (Pattern G), so grade it like an agent file.

When the path is a single file, grade that file. When it is a folder where no file matches the search, such as a folder of output styles, grade each `.md` file directly in it. Grade a file that both searches find once.

Audit only files the user wrote. Drop copies, caches, and files synced or installed from elsewhere, and name the folders you dropped in one line.

### 2. Read and grade each file

Apply the rubric in `references/grading-rubric.md` to every discovered file. The rubric covers reading discipline, directive-vs-context separation, the S/R/F dimensions with examples, dispatcher handling, and the severity ladder. Both grading paths use the same rubric so results are comparable.

- **1–5 files**: grade inline. Read each file, apply the rubric, hold the results in memory keyed by path.
- **6+ files**: fan out to parallel Haiku subagents — see step 3.

Either path produces the same `{path, s, r, f, severity, why}` shape, which feeds the step 4 audit table. The rubric's tool, harness, consistency and prose checks do not add columns. They raise the severity and are named in `why`.

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

Patterns K–Q fix a failed prose check. Each one makes the file shorter.

**Pattern K — One rule, one home.** When a rule appears in two or more places in a file, keep the fullest statement where the model needs it. Delete the other copies, or replace each with a pointer ("see rule 2"). Across files, the copy that is not the source becomes a pointer, except a copy that Pattern A requires: its reader cannot load the source.

*Why it works:* copies drift apart. After one is edited, the model sees two versions and picks one (Pattern H).

**Pattern L — Move notes for the maintainer out.** The date a rule was added, a row or ticket number, a spec link, a count of past failures, and the story behind a rule are for the person who edits the file. Test each clause: would the model act differently without it? If not, it is a note, and evidence counts are notes. Move notes to the file's spec, design doc or commit message, and ask where when the project has none. Never delete a note that exists nowhere else without asking. Keep a reason that changes how the model applies the rule.

*Why it works:* the model reads a note as part of the instruction. It costs attention on every run, and the model may act on the history instead of the rule.

**Pattern M — Cut what the model already knows.** Delete general facts about a tool ("git keeps the history of every commit"), a claim that the file works for any project, and lists of common values ("often `main`, but can be `master` or `develop`"). When the value matters, replace the list with the command that finds it.

*Why it works:* such a sentence gives no instruction, and a literal model may read a list of examples as the complete set.

**Pattern N — Cut the recap.** Delete a sentence after a list, table or template that says again what it showed ("That is three sections: …", "These coexist; pick whichever fits"). When the recap holds a new rule, keep only the rule.

*Why it works:* the model has just read the list, so the recap adds words and no instruction.

**Pattern O — Cut the rule said again in negative form.** In "Stop and say so. Do not overwrite the file.", the second sentence repeats the first. Keep the form that names the action. Keep a negative only when it rules out a step that the positive form allows.

*Why it works:* two wordings invite the model to look for a difference between them. When the wordings differ slightly ("do not replace it without asking"), the model finds a difference that was never meant.

**Pattern P — Firm up or drop hedge words.** "usually", "typically", "often", "as needed" and "where possible" make a rule optional for a literal model. State the rule firmly. When the hedge marks a real exception, name that exception. Do not add a clause that lists every case. This is also the fix for an S grade lowered by a hedge.

*Why it works:* a firm rule is followed the same way every time, and naming one exception is shorter than listing every case.

**Pattern Q — Trim the frontmatter description.** A skill's `description` decides when the skill loads, and it is read in every session. Keep what the skill does in one sentence, its trigger phrases and its "NOT for" clauses. Cut any summary of the steps or the output.

*Why it works:* the description costs words in every session, and a model may follow a summary of the steps in place of the body, skipping its stop conditions.

The prose check in `references/grading-rubric.md` lists the text to keep even when it looks like K–Q. When unsure whether a cut changes behaviour, keep the sentence, or run the file on one fixed task before and after the cut and compare the results.

### 6. Apply approved edits and re-grade

Use the Edit tool for surgical changes; use Write only for full rewrites of CRITICAL files. After editing each file, re-grade it inline and confirm the severity dropped.

If the user wants a durable record, offer to write the audit table plus applied-fixes summary to a path the user names. There is no default path. Default off — only write when asked.

## Anti-patterns to avoid

- **Don't pad already-strong files.** If S/R/F and every check in the rubric pass, skip. Adding more constraints to a working prompt over-constrains and bloats tokens.
- **Don't propose a shared preamble.** It's tempting to write one "specificity block" and prepend it everywhere. Don't — agents and commands have different jobs and over-shared boilerplate dilutes their actual instructions. Each file owns its standards.
- **Don't grade dispatcher files.** A one-line command that only invokes an agent, or a `CLAUDE.md` that's only `<tag @path>` includes, has no S/R/F surface — grade the targets/included files, not the dispatcher.
- **Don't dismiss `CLAUDE.md` / docs files by filename.** A context-heavy file with embedded directives ("Always X", "Never Y", "When X, do Y") has a real S/R/F surface in those passages even though the rest of the file is pure reference. Read for directive content before deciding `n/a`.
- **Don't pile on MUSTs.** Capitalised commands feel forceful but read as noise. Explain *why* the model should do something — literal-following is also literal-understanding. A two-sentence rationale beats a one-word imperative, when the rationale changes how the model applies the rule; history and evidence are notes (Pattern L).
- **Don't edit shared files without a confirmation per edit.** Confirm before each write to a file outside the current repository, and to a file of a global setup or a shared plugin even from inside its own repository: it affects every project that loads it.
- **Don't conflate "thin" with "broken".** A skill that's 30 lines but specific in all three dimensions is fine. Length is not the metric.

## Common Mistakes

- Grading files by length instead of S/R/F. A 5-line file can be specific; a 100-line file can be vague.
- Treating "be careful", "be thorough", "think hard" as passing the Reasoning dimension. They don't — only reasoning the output must contain, before its conclusion, does.
- Grading each file alone and missing the contradiction between two of them (Pattern H). Compare the files after grading them.
- Forgetting to re-grade after editing. Without the re-grade, you can't tell if the fix landed.
- Trusting an agent's `tools:` line. `Grep`, `Glob` and `LSP` rarely reach a subagent, whatever that line says. Grade what the prompt requires against what the agent will really get (Pattern G).
- Over-fitting to the article that motivated this skill. The pattern (specificity > vagueness) is not tied to one model — apply it whenever a model behaves more literally than expected.

## Reference

This skill encodes an audit pattern: it grades each file on the S/R/F rubric in `references/grading-rubric.md`, then applies the fix-pattern catalog to the files that fail.
