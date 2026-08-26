# Instructions

**Important:**

- Always write designs, specs, plans and reviews to `<project-root>/docs/plans/YYYY-MM-DD-<slug>.md` unless explicitly instructed otherwise. Determine `<project-root>` from the nearest `.git` directory, `composer.json`, `package.json`, or similar project marker. **This overrides Superpowers' default plan/spec paths** — Superpowers must also write to `docs/plans/`.
- Always use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- Common prefixes: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`
- Never add new dependencies without approval

### Superpowers Integration

Auto-dispatch of skills is unreliable on Opus 4.7+, so invoke the relevant `superpowers:` skill via the Skill tool **before** starting work. Treat the table below as explicit triggers, not suggestions — the corresponding skill must run first, even if the task looks small enough to handle inline.

| Task class | Invoke first |
|---| ---|
| New feature, component, or behavior change (any non-trivial creative work) | `superpowers:brainstorming` |
| Multi-step implementation from a spec or written requirements | `superpowers:writing-plans` |
| Writing or modifying production code (>1 file or >~30 lines) | `superpowers:test-driven-development` |
| Bug, test failure, or unexpected behavior | `superpowers:systematic-debugging` |
| Starting non-trivial work that warrants a worktree (see Git Workflow rules) — before any code changes | `superpowers:using-git-worktrees` |
| Executing a plan from `docs/plans/` | `superpowers:executing-plans` |
| Branch is feature-complete and ready to integrate | `superpowers:finishing-a-development-branch` |
| Major work needs review before merge | `superpowers:requesting-code-review` |

Skip the table only for: single-line fixes, typo/comment edits, doc-only changes, config tweaks.

**Precedence:** these project instructions are the highest authority — when plan mode, a skill, or any system default conflicts, follow this file. Superpowers may override **only** plan output format and simplicity rules (announce when it does). Everything else here is non-overridable: `docs/plans/` output path, Git Workflow (GitLab/worktrees/squash-merge), Conventional Commits, no new deps without approval, Critical Thinking + Risk + Trade-Off Analysis, and that plans include **Dependencies** + **Risk** sections and follow **Red → Green → Refactor** (tests before implementation).

**Discovery authority:** while `superpowers:brainstorming` or `writing-plans` runs, it owns exploration — don't also run other planning workflows. 

#### Spec → Plan two-artifact flow

When `superpowers:brainstorming` produces a deliverable, keep spec and plan as **separate files**:

1. **Spec** → `docs/plans/YYYY-MM-DD-<slug>-spec.md` — product-level (what/why, design decisions, architecture, trade-offs, risk; new UI gets a **Visual Language** section mapping elements to design-system primitives/semantic classes/motion). Self-contained: a cold reader could write the plan from it alone. First section is **"How to read this spec"** — all related docs (specs, plans, ROADMAP, CHANGELOG, sources, skills) with paths, in reading order.
2. Self-review the spec (placeholders, consistency, scope, ambiguity, self-containment), then ask the user to review it before proceeding.
3. **Plan** → `docs/plans/YYYY-MM-DD-<slug>.md` via `superpowers:writing-plans` — execution-level: TDD steps, test code, commit breakdown.

If plan mode auto-engages mid-brainstorming, its `~/.claude/plans/` file is scratch — write the durable spec + plan to `docs/plans/` on `ExitPlanMode` regardless.

#### No silent reinterpretation of approved decisions

If implementation research (reading code, checking library behavior, running a preflight) reveals that a brainstorm or spec decision was based on a false premise, **stop and ask the user before writing or committing the plan artifact**: "Spec decision X was picked for reason Y; Y turns out to be wrong; actual reality is Z. Keep X on new grounds, or change?" Flagging the change in a plan header is a breadcrumb for the executor, not signoff. "Functionally equivalent" does not license skipping the ask — the user chose between options for reasons, and new information may reshuffle those reasons.

#### Code Review Routing

Two diff reviewers, complementary — route by what you want:

- **`my:soundness-review`** = soundness *judgment* + plan-alignment, durable report to `docs/plans/`. No args = working tree; `BASE..HEAD` = committed range; pass a `.md` plan to add alignment (dirty tree) or review the plan itself (clean tree). Use for "is this sound?", a for/against verdict, or plan-match.
- built-in **`/code-review`** = *bug-finder* (correctness/efficiency); `--fix` applies fixes, `ultra` is the deep multi-agent sweep. Use to find or fix bugs.
- Want both → `my:soundness-review` first, then `/code-review --fix`. Explicit security sweep → `/security-review`. An *open* PR/MR → `/review`. Both committed + uncommitted work present → run `my:soundness-review` twice (no-args, then the range).

**Before any review:** map changed symbols with `mcp__gkg__repo_map` / `get_references` / `import_usage` first; grep only when gkg can't answer. Never review line-by-line without caller/callee context. Never invoke `feature-dev:code-reviewer` or `superpowers:requesting-code-review` — both superseded by `my:code-reviewer` (which `my:soundness-review` dispatches).

## Communication

- Write to be understood — someone without your context must be able to follow and act on it. Define a term before relying on it; never compress an explanation into an idiom or a slogan. Length is Output Discipline's job, and where the two conflict clarity wins.
- Challenge assumptions — propose the best solution, not just a solution

## Output Discipline

**Verbosity: medium** *(global default)*

This switch controls token-consuming output across all sessions. Override per-project by adding `**Verbosity: <level>**` to that project's CLAUDE.md.

### Levels

**min** — strongest reduction.

- No preamble before tool calls; no end-of-turn summary.
- One-line status only at non-obvious moments (finding, blocker, direction change). Skip status entirely for short reactive tasks.
- Code: zero comments unless required by the language (shebangs, type stubs).
- Plan/report/spec/review artifacts: bullet lists, no prose paragraphs.
- Exploratory questions: ≤2 sentences total.
- no recaps

**medium** — moderate reduction *(default)*.

- Optional one-sentence preamble when starting non-trivial work; ≤1 sentence end-of-turn summary.
- Status updates at key inflection points only (per default Tone and style rules).
- Code comments only when WHY is non-obvious (per default rules).
- Plan/report artifacts: concise prose OK, no filler.
- Exploratory questions: ≤3 sentences with a recommendation and main tradeoff.
- Do not suppress recaps

**off** — switch disabled.

- Native Claude Code behavior plus any output-style plugins (explanatory-output-style, etc.) and skill/agent verbosity instructions all apply unmodified.
- Use for teaching mode, unfamiliar codebases, or when you explicitly want explanation over brevity.

### Override authority

When verbosity is `min` or `medium`, these rules **override** verbosity instructions inside individual skills, agents, commands, and plugins (including third-party). If a skill says "provide a detailed summary" and verbosity is `min`, follow `min`. When verbosity is `off`, yield to the skill or plugin.

### Soft cap, not hard cap

These are instructions, not enforced limits. The model follows them well but not perfectly. Don't try to enforce via `CLAUDE_CODE_MAX_OUTPUT_TOKENS` — it cuts mid-tool-call and breaks more than it saves.

## Code

- Match the surrounding code — read sibling files for naming, structure and idiom before adding new ones. Consistency with what is there beats a preference of your own.

## Git Workflow

I am the sole developer on these projects. **Worktrees + squash-merge are mandatory** for non-trivial work; **MRs are optional** — used only when they add value a plain squash-merge can't (see below). This overrides Superpowers git workflow (including `finishing-a-development-branch`).

We use **GitLab** unless stated otherwise in the project. There are no "pull requests" — only **merge requests (MRs)**.

- Always squash-merge when integrating branches — no regular merges, whether via MR or local `git merge --squash`
- Use `glab` CLI (not `gh`) for MR operations when you do open an MR
- Use `glab mr create` instead of `gh pr create`

### Splitting scope before branching

If a roadmap row, issue, or task list mixes a bug fix and a feature, split into separate branches **before** writing any spec — two branches, two spec files, two commit trails. Bundling violates conventional-commit discipline, the brainstorming-first rule for new features, and review hygiene. Bug fixes route directly to `superpowers:systematic-debugging`; features must go through `superpowers:brainstorming` first. The roadmap row itself can be edited or split into two rows after the user approves the split.

### When to use worktrees

- Any task that will produce 2+ commits
- Any task from a plan or spec
- Any task involving code changes + tests

### When NOT to use worktrees

- Single-commit fixes (typo, stale test assertion)
- Documentation-only changes
- Config/gitignore tweaks

### Finishing a worktree branch

After squash-merging a feature branch, only run `git worktree remove <path>`. **Do not delete the underlying branch** with `git branch -D` or `git branch -d`. Merged branches stay in the repo as a record of superseded approaches that can be diffed against later if a replacement regresses behaviour. Treat worktree removal and branch deletion as separate decisions: worktree removal is always safe; branch deletion is not the default. This overrides Superpowers `finishing-a-development-branch` if it suggests deletion. Applies to both `glab` MR flows and plain local squash-merges.

### Assessing branch redundancy

Don't judge a branch's unique work by `git log main..branch` alone — squash-merges land features under new SHAs, so "unique" commits may already be on `main`. Before recommending preserve/split/delete, extract concrete artifacts (class/method names, routes, filenames, string literals) from the branch's commits and `git grep` them on `main`; trust "unique" only when the tokens truly don't appear there.

### When to open an MR (optional)

MRs add no review value solo, but open one as a **CI gate** or a **durable/linkable record** (schema/data/contract changes, anything hard to reverse, or when you need a URL). Otherwise integrate locally: `git checkout main && git merge --squash <branch>` + a Conventional Commit. The squash discipline, not the MR, keeps history clean. If unsure, ask before integrating.

## Planning Standards

These standards apply to **all** planning workflows — built-in plan mode, the `/plan` command, Superpowers brainstorming/writing-plans, and any agent producing implementation plans. Critical Thinking, Risk Awareness, and Trade-Off Analysis are always enforced. Mandatory Exploration applies only when no superpowers discovery skill is active (see Superpowers Integration above). Plan Output Format may be overridden by Superpowers.

**Verify against ground truth, not the artifact.** Discovery — caller lists, filenames, parameters — must come from executing against the real system (search the repo, run the command), never from memory or from re-reading the plan.

### Critical Thinking

- Challenge assumptions — don't rubber-stamp ideas
- If a request is unclear, over-scoped, or misguided, say so directly
- Present arguments both for and against proposed approaches
- If the existing codebase already solves the problem, point that out instead of planning new work
- If unsure about something, say so — do not speculate

### Mandatory Exploration

Before proposing any changes:

0. Use gkg mcp tools to understand project structure. Announce using gkg.

If gkg mcp tools are not available report this fact and use builtins:

1. Use Glob to find relevant files and understand project structure
2. Use Grep to search for related patterns, imports, and usages
3. Use Read to examine the actual implementation of files you'll modify or extend
4. Identify existing patterns, conventions, and abstractions already in use
5. Check for existing solutions that might already cover the request

Do not propose changes to code you haven't read. Do not assume file contents.

### Reference Sweep

When a plan removes/renames/changes the signature of a cross-file symbol (function, type, route/event name, config/DI key, field, file-naming scheme), the "Files to Modify" list must be the output of a **repo-wide sweep**, not memory: run **both** a symbol-reference tool **and** a plain text search for the name token (string-literal refs — routes, DI keys, ORM eager-loads, templates — are invisible to symbol tools). Every hit, including cross-repo consumers, is a row.

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
- State the blast radius from the Reference Sweep output (actual caller list), not an estimate
- Identify what could break and how to detect it
- Call out if manual testing or deployment steps are needed

### Test Standards

- **End-to-end coverage.** A change to a public surface (route, relationship, serialized contract, CLI) needs at least one test exercising the real surface end-to-end — not only unit tests of the changed unit.
- **No vacuous tests.** Each test must fail for the right reason before implementation. Assertions on generated artifacts must reference the real producing code, not an assumed pattern. Reject degenerate parameters, matches-nothing filters, and references to non-existent fixtures.
- **Rehearse runbooks.** Operator scripts/runbooks must be dry-run against the real target before the plan is marked done.

### Plan Output Format

Plans use these sections (Superpowers may substitute its own format): **Context · Files to Modify/Create · Step-by-Step Implementation · Trade-Offs/Alternatives · Dependencies · Risk · Testing Strategy · Open Questions**. The full template with per-section field prompts is the canonical copy in the `my:planner` agent (`~/projects/claude-setup/my-plugin/agents/planner.md`) — edit it there.

<!--
Language-specific command cheatsheets (PHP/Laravel, Docker, Markdown, JS/TS, Python)
were moved to path-scoped rules in GLOBAL-rules/ (symlinked to ~/.claude/rules/).
They load only when Claude reads a matching file type, keeping this file's always-loaded
context lean. See GLOBAL-rules/<lang>.md.
-->

## HTTP Requests

- Always prefer `curl` over WebFetch for API calls and downloading files
- Use WebFetch only for reading documentation pages

