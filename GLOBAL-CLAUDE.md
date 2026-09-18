# Instructions

**Important:**

- Always write designs, specs, plans and reviews to `<project-root>/docs/plans/YYYY-MM-DD-<slug>.md` unless explicitly instructed otherwise. Determine `<project-root>` from the nearest `.git` directory, `composer.json`, `package.json`, or similar project marker. **This overrides Superpowers' default plan/spec paths** — Superpowers must also write to `docs/plans/`.
- Reports (critiques and audits: findings about a whole product or area on one day) go to `<project-root>/docs/reports/` instead. Their findings become work through one `-action-plan.md` in `docs/plans/`, with one section per phase, never one file per phase. Reviews of one spec, plan or diff stay in `docs/plans/`. Details, the status line and the optional index: `GLOBAL-rules/docs-layout.md` (symlinked to `~/.claude/rules/`).
- Always use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- The full format is `type(scope): sentence`. The scope is the part of the codebase affected; each project defines its own scopes. Projects that already use `type:` without a scope keep that format.
- Common types: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`
- Never add new dependencies without approval

### Superpowers Integration

Auto-dispatch of skills is unreliable on Opus 4.7+, so invoke the relevant `superpowers:` skill via the Skill tool **before** starting work. Treat the table below as explicit triggers, not suggestions — the corresponding skill must run first, even if the task looks small enough to handle inline.

| Task class | Invoke first |
|---| ---|
| New project, new subsystem, or change to a data model, storage choice or public contract | `my:architect`, then `superpowers:brainstorming` |
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

**Discovery authority:** while `superpowers:brainstorming` or `writing-plans` runs, it owns exploration — don't also run other planning workflows. `my:architect` runs before brainstorming, never during it. When an architecture brief (`docs/plans/*-architecture.md`) exists for the task:

- Brainstorming treats the brief as settled input. It asks only about items under the brief's "Open for brainstorming" section.
- The brief's Decision replaces brainstorming's "Propose 2-3 approaches" step. Brainstorming presents its design sections starting from that Decision.
- Brainstorming classifies the task as architectural, never bounded or spike.

If brainstorming upgrades a task to architectural partway through, and the task matches the `my:architect` trigger row, stop and run `my:architect` first.

#### Spec → Plan two-artifact flow

When `superpowers:brainstorming` produces a deliverable, keep spec and plan as **separate files**:

1. **Spec** → `docs/plans/YYYY-MM-DD-<slug>-spec.md` — product-level (what/why, design decisions, architecture, trade-offs, risk; new UI gets a **Visual Language** section mapping elements to design-system primitives/semantic classes/motion). Self-contained: a cold reader could write the plan from it alone. First section is **"How to read this spec"** — all related docs (specs, plans, ROADMAP, CHANGELOG, sources, skills) with paths, in reading order. When an architecture brief exists, it is listed first.
2. Self-review the spec (placeholders, consistency, scope, ambiguity, self-containment). Then run `my:spec-review <spec path>` and act on its report: fix every `editorial` finding — but first check whether the fix changes what a component owns, a contract, the chosen option, or the scope, and if it does treat it as `design`; never fix a `design` finding — ask the user in the "No silent reinterpretation" form below; list rejected findings with one line of reasoning each. Then ask the user to review the spec, the report and the open design questions before proceeding.
3. **Plan** → `docs/plans/YYYY-MM-DD-<slug>.md` via `superpowers:writing-plans` — execution-level: TDD steps, test code, commit breakdown.

If plan mode auto-engages mid-brainstorming, its `~/.claude/plans/` file is scratch — write the durable spec + plan to `docs/plans/` on `ExitPlanMode` regardless.

#### No silent reinterpretation of approved decisions

If implementation research (reading code, checking library behavior, running a preflight) reveals that a brainstorm or spec decision was based on a false premise, **stop and ask the user before writing or committing the plan artifact**: "Spec decision X was picked for reason Y; Y turns out to be wrong; actual reality is Z. Keep X on new grounds, or change?" Flagging the change in a plan header is a breadcrumb for the executor, not signoff. "Functionally equivalent" does not license skipping the ask — the user chose between options for reasons, and new information may reshuffle those reasons.

#### Code Review Routing

Three reviewers, complementary — route by what you want:

- **`my:soundness-review`** = soundness *judgment* + plan-alignment, durable report to `docs/plans/`. No args = working tree; `BASE..HEAD` = committed range; pass a `.md` plan to add alignment (dirty tree) or review a plan itself (clean tree; specs go to `my:spec-review`). Use for "is this sound?", a for/against verdict, or plan-match.
- **`my:spec-review`** = *system-thinking* review of one `-spec.md`: builds a component/connection model, judges boundaries, contracts, state ownership, failure spread, fit and the spec rules; labels findings `editorial` or `design`; report to `docs/plans/`. Required step 2 of the Spec → Plan flow.
- built-in **`/code-review`** = *bug-finder* (correctness/efficiency); `--fix` applies fixes, `ultra` is the deep multi-agent sweep. Use to find or fix bugs.
- Want both → `my:soundness-review` first, then `/code-review --fix`. Explicit security sweep → `/security-review`. An *open* PR/MR → `/review`. Both committed + uncommitted work present → run `my:soundness-review` twice (no-args, then the range).

**Before any review:** map changed symbols with the built-in `LSP` tool (`findReferences`, `incomingCalls`, `documentSymbol`) first, then a plain `Grep` for the name token — string-literal refs are invisible to symbol tools. Never review line-by-line without caller/callee context. Never invoke `feature-dev:code-reviewer` or `superpowers:requesting-code-review` — both superseded by `my:code-reviewer` (which `my:soundness-review` dispatches).

## Communication

- Write to be understood — short sentences, terms defined at first use, no idioms. The full ruleset is the `plain` output style (`GLOBAL-output-styles/plain.md`, symlinked to `~/.claude/output-styles/`), which is enabled via `"outputStyle": "plain"` in `~/.claude/settings.json`. **Edit the style file, not this line** — this line is only a fallback for when the style is not loaded (it does not reach subagents, which run their own system prompt).
- Challenge assumptions — propose the best solution, not just a solution

## UI Design

Any discussion that turns to UI — screens, layout, controls, states, visual
language — must be **shown**, not described. Reach for the design tooling before
writing a prose description or a table of class names:

- **`design`** — a Claude Design canvas of `.dc.html` artboards on one pan/zoom
  canvas. **Always, for any screen, state or flow.** This holds inside
  `superpowers:brainstorming` too: that skill's own Visual Companion is an
  ephemeral local server, it is not a substitute, and it is not to be offered.
- **`frontend-design`** — aesthetic direction, typography, and choices that do
  not read as templated defaults.
- **`artifact-diagramming`** — when the point is a mechanism rather than a screen.

Prose may summarise a design that has been drawn. It may not stand in for one.

This does not replace the **Visual Language** section a spec requires: that
section maps an already-drawn design onto real primitives and semantic classes,
verified against the stylesheet rather than assumed. Both are needed — the
drawing decides, the table records.

## Code

- Match the surrounding code — read sibling files for naming, structure and idiom before adding new ones. Consistency with what is there beats a preference of your own.

## Git Workflow

I am the sole developer on these projects. **Worktrees + squash-merge are mandatory** for non-trivial work; **MRs are optional** — used only when they add value a plain squash-merge can't (see below). This overrides Superpowers git workflow (including `finishing-a-development-branch`).

We use **GitLab** unless stated otherwise in the project. There are no "pull requests" — only **merge requests (MRs)**.

- Always squash-merge when integrating branches — no regular merges, whether via MR or local `git merge --squash`
- Use `glab` CLI (not `gh`) for MR operations when you do open an MR
- Use `glab mr create` instead of `gh pr create`
- Read `git diff --cached` before every commit. The Edit tool has silently dropped a character, and a trailer the project forbids has slipped into a commit.

### Splitting scope before branching

If a roadmap row, issue, or task list mixes a bug fix and a feature, split into separate branches **before** writing any spec — two branches, two spec files, two commit trails. Bundling violates conventional-commit discipline, the brainstorming-first rule for new features, and review hygiene. Bug fixes route directly to `superpowers:systematic-debugging`; features must go through `superpowers:brainstorming` first. The roadmap row itself can be edited or split into two rows after the user approves the split.

### When to use worktrees

- Any task that will produce 2+ commits
- Any task from a plan or spec
- Any task involving code changes + tests

Create the worktree with `git worktree add`, not the `EnterWorktree` tool, and run each command as `cd <worktree> && …`. The `EnterWorktree` guard refuses combined commands, `git -C` and script files, so one mutation check took three or four calls.

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

These standards apply to **all** planning workflows — built-in plan mode, Superpowers brainstorming/writing-plans, and any agent producing implementation plans. Critical Thinking, Risk Awareness, and Trade-Off Analysis are always enforced. Mandatory Exploration applies only when no superpowers discovery skill is active (see Superpowers Integration above). Plan Output Format may be overridden by Superpowers.

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

Plans use these sections (Superpowers may substitute its own format): **Context · Files to Modify/Create · Step-by-Step Implementation · Trade-Offs/Alternatives · Dependencies · Risk · Testing Strategy · Open Questions**. The full template with per-section field prompts lives in `GLOBAL-rules/plan-format.md` (symlinked to `~/.claude/rules/`), which loads automatically when a `docs/plans/*.md` file is touched — edit it there.

<!--
Language-specific command cheatsheets (PHP/Laravel, Docker, Markdown, JS/TS, Python)
were moved to path-scoped rules in GLOBAL-rules/ (symlinked to ~/.claude/rules/).
They load only when Claude reads a matching file type, keeping this file's always-loaded
context lean. See GLOBAL-rules/<lang>.md.
-->

## HTTP Requests

- Always prefer `curl` over WebFetch for API calls and downloading files
- Use WebFetch only for reading documentation pages

