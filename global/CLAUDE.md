# Instructions

**Important:**

- Always write designs, specs, plans and reviews to `<project-root>/docs/plans/YYYY-MM-DD-<slug>.md` unless explicitly instructed otherwise. Determine `<project-root>` from the nearest `.git` directory, `composer.json`, `package.json`, or similar project marker. **This overrides Superpowers' default plan/spec paths** — Superpowers must also write to `docs/plans/`.
- Reports (critiques and audits: findings about a whole product or area on one day) go to `<project-root>/docs/reports/` instead. Their findings become work through one `-action-plan.md` in `docs/plans/`, with one section per phase, never one file per phase. Reviews of one spec, plan or diff stay in `docs/plans/`. Details, the status line and the optional index: `global/rules/docs-layout.md` (symlinked to `~/.claude/rules/`).
- Always use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- The full format is `type(scope): sentence`. The scope is the part of the codebase affected; each project defines its own scopes. Projects that already use `type:` without a scope keep that format.
- Common types: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`
- Never add new dependencies without approval

### Superpowers Integration

Auto-dispatch of skills is unreliable on Opus 4.7+, so invoke the relevant `superpowers:` skill via the Skill tool **before** starting work. Treat the table below as explicit triggers, not suggestions — the corresponding skill must run first, even if the task looks small enough to handle inline.

#### Size the process to the change

Before any skill in the table runs, pick a size and state it in one line with
the reason, for example "Small: a fix in one file, no stored data changes". The
user can change it. If unsure between two sizes, pick the larger. If the work
turns out larger than its size, stop and say so before going on.

| Size | When | Documents | Reviews | Commits on `main` |
|---|---|---|---|---|
| **Small** | A bug fix or a small behaviour change in one or two files. No change to stored data, permissions, a message or public contract, or the build. | None. The reason goes in the commit message and, where the project keeps them, the roadmap row and the changelog. | `/code-review high` on the branch. | One: the squash-merged code. |
| **Medium** | A feature or a fix across several files, with none of the Large triggers. | One spec, with a **Tasks** section in place of a separate plan. | `my:spec-review` on the spec; the end-of-branch reviews. No plan review. | Three: the spec with its review, the code, the `done` mark. |
| **Large** | Any change to stored data or its shape, permissions, a message or public contract, or something hard to reverse; a new subsystem. | Everything as below: architecture brief where the table asks for one, spec, plan. | All reviews as below. | Four, as in "One feature, four commits". |

- **Small** skips brainstorming and the spec. A bug still starts with
  `superpowers:systematic-debugging`, and every code change still starts with a
  failing test. It still runs in a worktree.
- **Medium** writes the Tasks section by the rules of
  `superpowers:writing-plans` "What a Step Contains": test names and assertions
  as code, signatures and files for code steps, no code bodies. There is no
  plan stage to commit the `approved` status, so commit it as a fixup of the
  spec commit, then run `/my:handoff code <spec path>`.
- **Large** follows the rest of this file unchanged.

| Task class | Invoke first |
|---| ---|
| New project, new subsystem, or change to a data model, storage choice or public contract | `my:architect`, then `superpowers:brainstorming` |
| New feature, component, or behavior change (any non-trivial creative work) | `superpowers:brainstorming` |
| Multi-step implementation from a spec or written requirements | `superpowers:writing-plans` |
| Writing or modifying production code (>1 file or >~30 lines) | `superpowers:test-driven-development` |
| Bug, test failure, or unexpected behavior | `superpowers:systematic-debugging` |
| Starting non-trivial work that warrants a worktree (see Git Workflow rules) — before any code changes | `superpowers:using-git-worktrees` (create the worktree with `git worktree add`, never `EnterWorktree`) |
| Executing a plan from `docs/plans/` | `superpowers:executing-plans` |
| Branch is feature-complete and ready to integrate | `superpowers:finishing-a-development-branch` |
| Major work needs review before merge | `superpowers:requesting-code-review` |

Skip the table only for: single-line fixes, typo/comment edits, doc-only changes, config tweaks. For Small and Medium changes, the size table above says which rows apply.

**Precedence:** these project instructions are the highest authority — when plan mode, a skill, or any system default conflicts, follow this file. Superpowers may override **only** plan output format and simplicity rules (announce when it does). Everything else here is non-overridable: `docs/plans/` output path, Git Workflow (GitLab/worktrees/squash-merge), Conventional Commits, no new deps without approval, Critical Thinking + Risk + Trade-Off Analysis, and that plans include **Dependencies** + **Risk** sections and follow **Red → Green → Refactor** (tests before implementation).

**Discovery authority:** while `superpowers:brainstorming` or `writing-plans` runs, it owns exploration — don't also run other planning workflows. `my:architect` runs before brainstorming, never during it. When an architecture brief (`docs/plans/*-architecture.md`) exists for the task:

- Brainstorming treats the brief as settled input. It asks only about items under the brief's "Open for brainstorming" section.
- The brief's Decision replaces brainstorming's "Propose 2-3 approaches" step. Brainstorming presents its design sections starting from that Decision.
- Brainstorming classifies the task as architectural, never bounded or spike.

If brainstorming upgrades a task to architectural partway through, and the task matches the `my:architect` trigger row, stop and run `my:architect` first.

#### Spec → Plan two-artifact flow

When `superpowers:brainstorming` produces a deliverable, keep spec and plan as **separate files** (Large changes only; a Medium change keeps its tasks in the spec):

1. **Spec** → `docs/plans/YYYY-MM-DD-<slug>-spec.md` — product-level (what/why, design decisions, architecture, trade-offs, risk; new UI gets a **Visual Language** section mapping elements to design-system primitives/semantic classes/motion). Self-contained: a cold reader could write the plan from it alone. First section is **"How to read this spec"** — all related docs (specs, plans, ROADMAP, CHANGELOG, sources, skills) with paths, in reading order. When an architecture brief exists, it is listed first.
2. Self-review the spec (placeholders, consistency, scope, ambiguity, self-containment). Then run `my:spec-review <spec path>` and act on its report: fix every `editorial` finding — but first check whether the fix changes what a component owns, a contract, the chosen option, or the scope, and if it does treat it as `design`; never fix a `design` finding — ask the user in the "No silent reinterpretation" form below; list rejected findings with one line of reasoning each. Then ask the user to review the spec, the report and the open design questions before proceeding.
3. **Plan** → `docs/plans/YYYY-MM-DD-<slug>.md` via `superpowers:writing-plans` — execution-level: TDD steps, test code, commit breakdown. After the user approves the spec, set its status to `approved`, leave that edit uncommitted (the plan stage commits it), and ask "Hand off the plan?"; on yes, run `/my:handoff plan <spec path>`, which writes the plan, then the code, then runs the end-of-branch reviews, each in a new session.

If plan mode auto-engages mid-brainstorming, its `~/.claude/plans/` file is scratch — write the durable spec + plan to `docs/plans/` on `ExitPlanMode` regardless.

#### No silent reinterpretation of approved decisions

If implementation research (reading code, checking library behavior, running a preflight) reveals that a brainstorm or spec decision was based on a false premise, **stop and ask the user before writing or committing the plan artifact**: "Spec decision X was picked for reason Y; Y turns out to be wrong; actual reality is Z. Keep X on new grounds, or change?" Flagging the change in a plan header is a breadcrumb for the executor, not signoff. "Functionally equivalent" does not license skipping the ask — the user chose between options for reasons, and new information may reshuffle those reasons.

#### Code Review Routing

Three reviewers, complementary — route by what you want:

- **`my:soundness-review`** = soundness *judgment* + plan-alignment, durable report to `docs/plans/`. No args = working tree; `BASE..HEAD` = committed range; pass a `.md` plan to review the plan itself (clean tree; specs go to `my:spec-review`) or to check a range against it; with a dirty tree and no range, it asks which; `--plan-only <plan>` reviews the plan on any tree and never asks. Use for "is this sound?", a for/against verdict, or plan-match.
- **`my:spec-review`** = *system-thinking* review of one `-spec.md`: builds a component/connection model, judges boundaries, contracts, state ownership, failure spread, fit and the spec rules; labels findings `editorial` or `design`; report to `docs/plans/`. Required step 2 of the Spec → Plan flow.
- built-in **`/code-review`** = *bug-finder* (correctness/efficiency); `--fix` applies fixes, `ultra` is the deep multi-agent sweep. Use to find or fix bugs.
- Want both → `my:soundness-review` first, then `/code-review --fix`. Explicit security sweep → `/security-review`. An *open* PR/MR → `/review`. Both committed + uncommitted work present → run `my:soundness-review` twice (no-args, then the range).

**Before any review:** map changed symbols with the built-in `LSP` tool (`findReferences`, `incomingCalls`, `documentSymbol`) first, then a plain `Grep` for the name token — string-literal refs are invisible to symbol tools. Never review line-by-line without caller/callee context. Never invoke `feature-dev:code-reviewer` or `superpowers:requesting-code-review` — both superseded by `my:code-reviewer` (which `my:soundness-review` dispatches).

**When to review:** once, at the end of the branch. This is enough because the spec and the plan were reviewed before any code, and every code commit runs the tests. It also needs a small branch, because a review of a very large diff misses things. If a branch grows past what one review can read carefully, split the plan into batches, and give each batch its own branch, review round and squash-merge. Run the reviews in parallel on the whole range (`BASE..HEAD`): one message with one `Agent` call per review, each subagent running one review skill. Two skills called directly load into the current turn and run one after another. Each subagent's prompt says: "Do not write commit IDs from this branch. Name the change in words, like 'the fix round' or 'the branch head'." Subagents do not read CLAUDE.md, and branch IDs in a review break the "cite only commits on `main`" rule. Before each commit, only reread `git diff --cached`. Reviewing every commit and then the whole branch again only adds waits.

**The end-of-branch reviews are the only reviews, so each one gets what it needs.** Pass the explicit range `main..<branch>` to every review. Some review skills diff against `origin/main` by default, which can lag local `main`, so check each review's scope note and rerun a review that read the wrong range. Name the `/code-review` level every time (`high` unless the project says otherwise). Without a level it reuses the last one typed, which may be `low`. Each subagent's prompt names the spec, the plan, the plan's **Risk** section and the map from "Before any review", and says that a known limit in **Risk** is not a finding. When a plan runs through `superpowers:subagent-driven-development` or `superpowers:executing-plans`, skip the skill's own reviews: its pre-flight plan review, its per-task reviewer and fix loop, and its final `requesting-code-review` pass. The plan review already covered the plan, and these end-of-branch reviews replace the rest. Two checks replace the per-task reviewer. First, after each task, the controller reads `git diff` for the test files the task touched, and stops if an assertion was removed or weakened, because `npm test`-style runs still pass then. Second, `my:soundness-review` gets the plan, not the spec, as its document (`main..<branch> <plan>`), so it checks that each task did what the plan said. The plan links the spec, and the skill takes one document only. A project can set its own level or review list, but never a default range.

**One fix round per review.** A finding about input that today's code never produces goes into the plan's **Risk** section as a known limit, not into a fix. A fix gets one re-review, and that re-review is final. The one exception is a new Critical finding in the re-review: bring it to the user before the merge. A lesser finding goes into **Risk**. Without this limit, each fix invites a new edge case and the rounds do not end.

## Communication

- Write to be understood — short sentences, terms defined at first use, no idioms. The full ruleset is the `plain` output style (`global/output-styles/plain.md`, symlinked to `~/.claude/output-styles/`), which is enabled via `"outputStyle": "plain"` in `~/.claude/settings.json`. **Edit the style file, not this line** — this line is only a fallback for when the style is not loaded (it does not reach subagents, which run their own system prompt).
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

### One feature, four commits on `main`

A Large feature leaves four commits on `main` (Small and Medium leave fewer, as the size table says): the spec with its review, the plan with its review, the squash-merged code, and the `done` mark. Without this rule, most commits are small edits to one spec or plan: on zitamu, 44 of 52 commits by 2026-09-18 were `docs:`. Docs are written in the main checkout, because an `@` mention cannot reach `.claude/worktrees/`. Code is written in a worktree, because sessions often run in parallel. A project's own file names only what differs: its plans index, its scopes, its test commands.

Two more commits are allowed. `my:architect` commits the architecture brief on its own, before step 1. An edit to another document that the spec forces, such as a glossary or a data model, is its own commit, not a fixup of the spec.

**Before step 1 in a project for the first time,** check that the project's instructions name four things: the plans index (or that there is none), the commit scopes, the test command for each code commit, and whether there is a remote. If any is missing, find it from the repo: scopes from `git log`, the test command from `package.json` or a `Makefile`. Then propose a short "Git workflow" section for `CLAUDE.md`, and ask about anything the repo does not show. Write the section only after the user approves it. If the project forbids editing `CLAUDE.md`, propose `CLAUDE.local.md` instead.

1. Write the spec on `main`.
2. Write the spec review on `main`.
3. Commit the spec and the review together.
4. Fixup any later spec and review edits, with `git commit --fixup <hash>`.
5. Write the plan on `main`.
6. Write the plan review on `main`.
7. Commit the plan and the plan review together.
8. Fixup any later plan and plan-review edits.
9. Fold the fixups: `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <oldest-target>^`. `<oldest-target>` is the oldest commit that a `fixup!` commit names. Only the interactive form folds fixups. Without `-i`, the rebase reports success and leaves every `fixup!` commit in place. So check that `git log --oneline` shows no `fixup!`, and that `git diff <pre-rebase-HEAD> HEAD` is empty. The target's parent works with or without a remote, and the rebase gives new hashes only to the target and the commits after it. The rebase needs a clean main checkout, so run it when no other session has uncommitted edits there.
10. Create the worktree, and write the code there.
11. Make doc edits in the worktree as required, but never edit the project's plans index there. While the worktree exists, edit this feature's spec and plan only in the worktree.
12. Squash-merge the branch into `main`, and commit.
13. Mark the spec and plan `done` on `main`, citing the squash commit.
14. The user pushes at their own pace.

- **Before every fixup** (steps 4 and 8), run `git branch --contains <sha>`, where `<sha>` is the target commit. If it lists a branch marked `+`, a worktree has that branch checked out, so make a normal commit instead. Merged branches without a worktree do not count. A rebase gives new hashes to the target and every later commit, so an open branch built on them would conflict at its squash-merge. Always name the target by hash, never `--fixup HEAD`: a parallel session may have committed in between.
- **Before every rebase** (step 9), run the same check on every pending `fixup!` target. A worktree opened after the fixup may now sit on top of it. If one does, wait until that branch is merged and its worktree removed.
- **No commit only changes a status.** There is no "in progress" commit. A status change goes into the commit that causes it.
- **A `docs:` commit runs no tests and no code reviews.** This covers every commit that touches only `.md` files: specs, plans, their reviews, fixups, index rows and the `done` marks of step 13. The only checks are the Markdown linter and a reread of `git diff --cached`. The spec review (step 2) and the plan review (step 6) still run, because they are the content of the commit, not a check on it. A code branch that also edits docs is reviewed as a code branch.
- **Cite only commits on `main`.** Never cite a commit that lives only on a local branch. A review names the decisions and sections it read, like "D12 to D16", not a hash, because later fixups fold the answers into the reviewed commit. zitamu (`real-estate-webapp`) has uncommitted `pre-commit` and `pre-push` hooks that enforce this rule and refuse a push with `fixup!` commits.

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
- **The red step is the mutation proof.** A test that failed with the expected message before implementation has proven it can fail. Only an assertion that never went red needs an extra deliberate break.
- **Rehearse runbooks.** Operator scripts/runbooks must be dry-run against the real target before the plan is marked done.

### Plan Output Format

Plans use these sections (Superpowers may substitute its own format): **Context · Files to Modify/Create · Step-by-Step Implementation · Trade-Offs/Alternatives · Dependencies · Risk · Testing Strategy · Open Questions**. The full template with per-section field prompts lives in `global/rules/plan-format.md` (symlinked to `~/.claude/rules/`), which loads automatically when a `docs/plans/*.md` file is touched — edit it there.

<!--
Language-specific command cheatsheets (PHP/Laravel, Docker, Markdown, JS/TS, Python)
were moved to path-scoped rules in global/rules/ (symlinked to ~/.claude/rules/).
They load only when Claude reads a matching file type, keeping this file's always-loaded
context lean. See global/rules/<lang>.md.
-->

## HTTP Requests

- Always prefer `curl` over WebFetch for API calls and downloading files
- Use WebFetch only for reading documentation pages

