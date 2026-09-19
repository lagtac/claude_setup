# Grading Rubric

How to grade Claude instruction files for literal-instruction-following models (Opus 4.7 and every later model). Used by the `tune-claude-instructions` skill on both grading paths — inline and parallel Haiku dispatch — so the rubric stays the single source of truth.

## Read the file in full

The audit is qualitative — there is no shortcut. Read the whole file before grading. Reasoning prompts and output formats often appear deeper down, so don't grade on filename or first paragraph alone.

## Separate directive content from pure context

For mixed files (`CLAUDE.md`, `AGENTS.md`, `.claude/docs/*.md`), split the two kinds of content as you read:

- **Directive content** — imperatives ("Always X", "Never Y"), workflow rules ("When X, do Y"), discipline statements ("Follow Red-Green-Refactor"), conventions ("Use Form Requests for validation"). These get graded.
- **Pure context** — command tables, architecture diagrams, env-var lists, API references, file inventories. No grading surface; mark as `n/a`.

For embedded directives, **R** (reasoning prompt) and **F** (output format) often legitimately become `n/a` because the directive doesn't produce structured output — that's fine, only **S** (specificity of the rule itself) is universal. A directive scores well on S when it's concrete and ideally pairs the rule with its rationale ("Use semantic classes only — never hardcode colors, because themes are DaisyUI `themes: all`"); it scores poorly when it leans on vague qualifiers like "appropriately", "when needed", "as required".

## Dispatcher files

A pure-dispatcher `CLAUDE.md` (just `<tag @path>` includes) is `n/a` overall — grade the included files instead. A one-line `/cmd` that just invokes an agent is also a dispatcher; grade its target. Mark dispatchers as severity **OK** with the why "dispatcher".

## Grade on S / R / F

Three dimensions, each ✅ pass / ⚠️ partial / ❌ fail (or `n/a`):

### S — Scope

Does the file enumerate the dimensions, fields, or sections the output must cover?

- ✅ "Write a plan with Context, Files, Steps, Trade-offs, Risk, Testing, Open Questions"
- ⚠️ "Write a thorough plan covering the main concerns"
- ❌ "Write a plan"

### R — Reasoning

Does the output have to contain the reasoning, placed *before* the conclusion it supports? Passing forms: a required "Reasoning" section above the verdict, "at each stage, write what you checked and what it showed", "before the recommendations, write the evidence". A bare "think step by step" earns ⚠️ at most: the newest models already reason internally, so the phrase adds little unless the reasoning must appear in the output. Implicit cues like "be thorough", "be careful", "analyze deeply", "use sequential thinking" do **not** pass.

- ✅ "At each diagnostic stage, write what you checked and what it showed before moving on." / a template with `### Reasoning` above `### Verdict`
- ⚠️ "Think step by step" or "Analyze carefully", with nothing required in the output
- ❌ (no reasoning asked for at all, in a file that produces a judgment)

R is `n/a` for files that produce no judgment, such as a command that runs a fixed sequence of git steps.

### F — Format

Does the file specify the output structure?

- ✅ A literal markdown skeleton, JSON schema, or numbered template with actual `## Heading` lines
- ⚠️ Section names listed but no template shown
- ❌ "Output the result"

## Tool check

Does the file require a tool its reader will not have? This is not a fourth column. It feeds severity and `why`.

- An agent file, or a prompt a skill or command dispatches to a subagent, fails the check when it requires `Grep`, `Glob` or `LSP` without a `Bash` fallback. Subagents rarely receive these, whatever the agent's `tools:` line says. It also fails when an agent's prompt spawns sub-agents but its `tools:` line does not list `Agent`. See Pattern G in `SKILL.md` for the evidence.
- A step that names one of these tools **with a `Bash` fallback** passes, e.g. "the `Grep` tool, or `grep -rn` through `Bash` when `Grep` is absent".
- Main-session files (commands, skills, `CLAUDE.md`) pass when they name `Grep` or `Glob`, but note it in `why`: auto mode can remove both.

A failed tool check raises the severity by one step (OK → Low, Low → Medium). Quote the passage in `problem_passages`.

## Harness check

Does the file assume a harness feature that does not work? It fails when it:

- names a tool parameter the tool does not have (for example "do not run it in the background" when subagents always run in the background and the Agent tool has no such parameter);
- runs a command that opens an editor or waits for input: `git rebase -i` without `GIT_SEQUENCE_EDITOR`, a `reword` step, `git commit` without `-m`, `git add -p`;
- asks the user with `AskUserQuestion` and gives no fallback for when the tool is absent (a headless run, some subagents);
- takes a destructive step (delete, force, reset, migrate, push) without a stop condition or a confirmation.

## Consistency check

Does the file give two instructions that cannot both be followed? Check:

- two rules in the file that conflict;
- a worked example that breaks a rule of the same file (the example usually wins);
- a default that conflicts with the user's standing rules, with no sentence saying which wins;
- text left from an earlier version that names a step, file or command that no longer exists;
- emphasis (ALL CAPS, "CRITICAL", "you MUST") on more than the one or two rules that truly override the rest.

A failed harness or consistency check raises the severity by one step, like the tool check. Quote the passage in `problem_passages`.

## Severity ladder

| Grades | Severity | Action |
|---|---|---|
| All ✅ (or all `n/a`) | **OK** | Skip. Don't pad working prompts. |
| One ⚠️ or one ❌ on a thin file | **Low** | 1–3 line addition. |
| Two ❌, or any ❌ on a workhorse agent/command | **Medium** | Targeted section edit. |
| Three ❌ on a workhorse file | **CRITICAL** | Full rewrite likely. |

A "workhorse" file is one that runs on every invocation of an important workflow — code-reviewer, commit, push. A one-line dispatcher that delegates to an agent is not a workhorse; grade its target instead.
