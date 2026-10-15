# Method: my

The rules of the `my` method. A project uses them by importing this file from its `CLAUDE.md`. They add to the core in `~/.claude/CLAUDE.md`.

**Important:**

- Always write designs, specs, plans and reviews to `<project-root>/docs/plans/YYYY-MM-DD-<slug>.md` unless explicitly instructed otherwise. Determine `<project-root>` from the nearest `.git` directory, `composer.json`, `package.json`, or similar project marker. **This overrides Superpowers' default plan/spec paths** — Superpowers must also write to `docs/plans/`.
- Reports (critiques and audits: findings about a whole product or area on one day) go to `<project-root>/docs/reports/` instead. Their findings become rows in the project's roadmap, which keeps the only order of work. An `-action-plan.md` in `docs/plans/` is optional: it only routes a large report's findings into rows, then stays as a reference. Reviews of one spec, plan or diff stay in `docs/plans/`. Details, the status line and the optional index: `global/rules/docs-layout.md` (symlinked to `~/.claude/rules/`).

### Superpowers Integration

Auto-dispatch of skills is unreliable on Opus 4.7+, so invoke the relevant `superpowers:` skill via the Skill tool **before** starting work. Treat the table below as explicit triggers, not suggestions — once the size below is picked, the corresponding skill must run first, even if the task looks small enough to handle inline.

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

- **Small** skips the brainstorming, writing-plans and executing-plans rows.
  A bug still starts with `superpowers:systematic-debugging`, and every code
  change still starts with a failing test. It still runs in a worktree. Known
  limits from its review go into the squash commit message, because there is
  no **Risk** section to hold them. Several Small fixes may share one branch
  when each one alone is Small. Each fix is its own commit with its own
  failing test first. The branch gets one review round and one squash commit,
  whose body names each fix's roadmap row.
- **Medium** writes the Tasks section by the rules of
  `superpowers:writing-plans` "What a Step Contains": test names and assertions
  as code, signatures and files for code steps, no code bodies. It runs the
  brainstorming row and skips the writing-plans row. There is no plan stage to
  commit the `approved` status, so commit it as a fixup of the spec commit,
  fold it with `git-fold-fixups.py`, then run `/my:handoff code <spec path>`. Fold
  before the hand-off: once the worktree sits on the `fixup!` commit, the
  fold must wait until the branch is merged. In a project with a "Parallel
  runs" section, the `approved` edit is a normal commit in the locked form of
  Git Workflow, not a fixup, and nothing folds. When the spec has a Delegation
  section, ask "Hand off the code, supervised or auto?": supervised is the
  route above, and auto runs `/my:handoff auto code <spec path>` with the
  `approved` edit left uncommitted. The auto code stage commits and folds
  that edit itself. Where the project keeps a plans
  index, its row goes into the spec commit. Wherever this file says "the
  plan" for a Medium change, read "the spec": its **Tasks** section and its
  **Risk** section play the plan's part.
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
| Branch is feature-complete and ready to integrate | Steps 12 and 13 in `~/.claude/rules/docs-layout.md`, or `/my:handoff review` for a handed-off branch (not `superpowers:finishing-a-development-branch`) |
| Major work needs review before merge | The end-of-branch reviews in Code Review Routing: `my:soundness-review` and `/code-review high` on `main..<branch>` (not `superpowers:requesting-code-review`) |

Skip the table only for: single-line fixes, typo/comment edits, doc-only changes, config tweaks. For Small and Medium changes, the size table above says which rows apply.

**Precedence:** these rules and the core in `~/.claude/CLAUDE.md` are the highest authority — when plan mode, a skill, or any system default conflicts, follow them. Superpowers may override **only** plan output format and the core's Simplicity Rules (announce when it does). Everything else here is non-overridable: `docs/plans/` output path, Git Workflow (GitLab/worktrees/squash-merge), Risk + Trade-Off Analysis, and that plans include **Dependencies** + **Risk** sections and follow **Red → Green → Refactor** (tests before implementation).

**Discovery authority:** while `superpowers:brainstorming` or `writing-plans` runs, it owns exploration — don't also run other planning workflows. `my:architect` runs before brainstorming, never during it. When an architecture brief (`docs/plans/*-architecture.md`) exists for the task:

- Brainstorming treats the brief as settled input. It asks only about items under the brief's "Open for brainstorming" section.
- The brief's Decision replaces brainstorming's "Propose 2-3 approaches" step. Brainstorming presents its design sections starting from that Decision.
- Brainstorming classifies the task as architectural, never bounded or spike.

If brainstorming upgrades a task to architectural partway through, and the task matches the `my:architect` trigger row, stop and run `my:architect` first.

#### Spec → Plan two-artifact flow

When `superpowers:brainstorming` produces a deliverable, keep spec and plan as **separate files** (Large changes only; a Medium change keeps its tasks in the spec):

1. **Spec** → `docs/plans/YYYY-MM-DD-<slug>-spec.md` — product-level (what/why, design decisions, architecture, trade-offs, risk; new UI gets a **Visual Language** section mapping elements to design-system primitives/semantic classes/motion). Self-contained: a cold reader could write the plan from it alone. First section is **"How to read this spec"** — all related docs (specs, plans, ROADMAP, CHANGELOG, sources, skills) with paths, in reading order. When an architecture brief exists, it is listed first. Ask the user whether the spec may run in auto mode (`/my:handoff auto`); on yes, add a **Delegation** section with the four keys that the `my:handoff` skill defines in its "Delegation" section.
2. Self-review the spec (placeholders, consistency, scope, ambiguity, self-containment). Then run `my:spec-review <spec path>` and act on its report: fix every `editorial` finding — but first check whether the fix changes what a component owns, a contract, the chosen option, or the scope, and if it does treat it as `design`; never fix a `design` finding — ask the user in the "No silent reinterpretation" form below; list rejected findings with one line of reasoning each. Then ask the user to review the spec, the report and the open design questions before proceeding.
3. **Plan** → `docs/plans/YYYY-MM-DD-<slug>.md` via `superpowers:writing-plans` — execution-level: TDD steps, test code, commit breakdown. After the user approves the spec, set its status to `approved`, leave that edit uncommitted (the plan stage commits it), and ask "Hand off the plan?"; on yes, run `/my:handoff plan <spec path>`, which writes the plan, then the code, then runs the end-of-branch reviews, each in a new session. When the approved spec has a Delegation section, ask "Hand off the plan, supervised or auto?" instead: supervised runs `/my:handoff plan <spec path>`, and auto runs `/my:handoff auto plan <spec path>`, which goes on to the squash-merge and the `done` marks without the user, as far as the Delegation section allows, and never pushes.

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

**The end-of-branch reviews are the only reviews, so each one gets what it needs.** Pass the explicit range `main..<branch>` to every review. Some review skills diff against `origin/main` by default, which can lag local `main`, so check each review's scope note and rerun a review that read the wrong range. Name the `/code-review` level every time (`high` unless the project says otherwise). Without a level it reuses the last one typed, which may be `low`. Each subagent's prompt names the spec, the plan, the plan's **Risk** section and the map from "Before any review", and says that a known limit in **Risk** is not a finding. When a plan runs through `superpowers:subagent-driven-development` or `superpowers:executing-plans`, skip the skill's own reviews: its pre-flight plan review, its per-task reviewer and fix loop, and its final `requesting-code-review` pass. The plan review already covered the plan, and these end-of-branch reviews replace the rest. Two checks replace the per-task reviewer. First, after each task, the controller reads `git diff` for the test files the task touched, and stops if an assertion was removed or weakened, because `npm test`-style runs still pass then. Second, `my:soundness-review` gets the plan, not the spec, as its document (`main..<branch> <plan>`), so it checks that each task did what the plan said. A Medium change has no plan, so it gets the spec. The plan links the spec, and the skill takes one document only. A project can set its own level or review list, but never a default range.

**One fix round per review.** A finding about input that today's code never produces goes into the plan's **Risk** section as a known limit, not into a fix. A fix gets one re-review, and that re-review is final. The one exception is a new Critical finding in the re-review: bring it to the user before the merge. A lesser finding goes into **Risk**. Without this limit, each fix invites a new edge case and the rounds do not end.

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

A Small change (see the size table) that adds no screen and no state, such as
a label, a colour or a spacing value, needs no canvas.

Prose may summarise a design that has been drawn. It may not stand in for one.

This does not replace the **Visual Language** section a spec requires: that
section maps an already-drawn design onto real primitives and semantic classes,
verified against the stylesheet rather than assumed. Both are needed — the
drawing decides, the table records.

## Git Workflow

I am the sole developer on these projects. **Worktrees + squash-merge are mandatory** for non-trivial work; **MRs are optional** — used only when they add value a plain squash-merge can't (see below). This overrides Superpowers git workflow (including `finishing-a-development-branch`).

We use **GitLab** unless stated otherwise in the project. There are no "pull requests" — only **merge requests (MRs)**.

- Always squash-merge when integrating branches — no regular merges, whether via MR or local `git merge --squash`
- Use `glab` CLI (not `gh`) for MR operations when you do open an MR
- Use `glab mr create` instead of `gh pr create`
- Read `git diff --cached` before every commit. The Edit tool has silently dropped a character, and a trailer the project forbids has slipped into a commit. The exception: in a project with a "Parallel runs" section, a commit in the main checkout reads `git diff -- <paths>` and each new file whole before the locked command in the next rule (`git diff` does not show a file git does not track yet), and reads the `git show --stat` list that the command prints. This replaces every `git diff --cached` reread this file names.
- In a project whose `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs" section (the `my:handoff` skill defines it), several auto runs share `main`. There, every commit in the main checkout runs under lock `main`: write the message with the Write tool to a new file in the session's scratchpad, then run `locked-commit.py -F <message file> <paths>`. It stages, commits and lists the commit inside the lock, and no shell reads the message. Nobody makes fixups there: every later edit to a spec, plan or review is a normal commit, and nothing folds. Commits in a worktree take no lock.

### One feature, four commits on `main`

A Large feature leaves four commits on `main`: the spec with its review, the plan with its review, the squash-merged code, and the `done` mark. Small and Medium leave fewer, as the size table says. The fourteen steps, and when to fixup and fold, are in `~/.claude/rules/docs-layout.md`, section "One feature, four commits on `main`". That rule loads when a file in `docs/plans/` is read or written. Before any numbered step, read it if it has not loaded.

**Before step 1 in a project for the first time,** check that the project's `CLAUDE.md` has a `## Project facts` block that names the method, the commit scopes, the test command, the plans index and the remote. If it is missing or incomplete, run `/kit:setup my`.

- **A `docs:` commit runs no tests and no code reviews.** This covers every commit that touches only `.md` files: specs, plans, their reviews, fixups, index rows and the `done` marks (step 13). The only checks are the Markdown linter and a reread of `git diff --cached`. The spec review (step 2 in `docs-layout.md`) and the plan review (step 6) still run, because they are the content of the commit, not a check on it. A code branch that also edits docs is reviewed as a code branch.

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

These standards add to the Engineering standards in `~/.claude/CLAUDE.md`. Critical Thinking (in the core), Risk Awareness and Trade-Off Analysis are always enforced. Mandatory Exploration (in the core) applies only when no superpowers discovery skill is active (see Superpowers Integration above). Plan Output Format may be overridden by Superpowers. In a plan, the "Files to Modify" list is the output of the core's Reference Sweep: every hit is a row.

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
