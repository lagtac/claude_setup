# Grading Rubric

How to grade Claude instruction files for literal-instruction-following models (Opus 4.7+). Used by the `tune-claude-instructions` skill on both grading paths — inline (1–5 files) and parallel Haiku dispatch (6+ files) — so the rubric stays the single source of truth.

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

Does the file explicitly request step-by-step reasoning *before* conclusions? Power phrases that pass: "think step by step", "show your reasoning", "before drawing conclusions", "before listing recommendations". Implicit cues like "be thorough", "be careful", "analyze deeply", "use sequential thinking" do **not** pass — 4.7+ takes them at face value and skips ahead to the answer.

- ✅ "Think step by step. Show your reasoning at each diagnostic stage before drawing conclusions."
- ⚠️ "Analyze carefully"
- ❌ (no reasoning prompt at all)

### F — Format

Does the file specify the output structure?

- ✅ A literal markdown skeleton, JSON schema, or numbered template with actual `## Heading` lines
- ⚠️ Section names listed but no template shown
- ❌ "Output the result"

## Severity ladder

| Grades | Severity | Action |
|---|---|---|
| All ✅ (or all `n/a`) | **OK** | Skip. Don't pad working prompts. |
| One ⚠️ or one ❌ on a thin file | **Low** | 1–3 line addition. |
| Two ❌, or any ❌ on a workhorse agent/command | **Medium** | Targeted section edit. |
| Three ❌ on a workhorse file | **CRITICAL** | Full rewrite likely. |

A "workhorse" file is one that runs on every invocation of an important workflow — code-reviewer, commit, push. A one-line dispatcher that delegates to an agent is not a workhorse; grade its target instead.
