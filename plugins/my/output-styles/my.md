---
name: my
description: The my method's rules
force-for-plugin: true
keep-coding-instructions: true
---

# Method: my

The rules of the `my` method. The `my` plugin forces them on as its output style, so they load in every session where the plugin is on. They add to the core in `~/.claude/CLAUDE.md`.

**Important:**

- Always write designs, specs, plans and reviews to `<project-root>/docs/plans/YYYY-MM-DD-<slug>.md` unless explicitly instructed otherwise. Determine `<project-root>` from the nearest `.git` directory, `composer.json`, `package.json`, or similar project marker. **This overrides Superpowers' default plan/spec paths** — Superpowers must also write to `docs/plans/`.
- Reports (critiques and audits: findings about a whole product or area on one day) go to `<project-root>/docs/reports/` instead. Their findings become rows in the project's roadmap, which keeps the only order of work. An `-action-plan.md` in `docs/plans/` is optional: it only routes a large report's findings into rows, then stays as a reference. Reviews of one spec, plan or diff stay in `docs/plans/`. Details, the status line and the optional index: the part "Where design documents live" below.

### Superpowers Integration

Auto-dispatch of skills is unreliable on Opus 4.7+, so invoke the relevant `superpowers:` skill via the Skill tool **before** starting work. Treat the table below as explicit triggers, not suggestions — the corresponding skill must run first, even if the task looks small enough to handle inline. "Pick the route" says when the route line comes.

#### Pick the route

Brainstorming sorts a task into spike, bounded or architectural. `my` uses
these paths as its routes. It adapts them with the risk line and the two-file
limit on bounded, and it gives bugs their own route. "An architectural change"
means either architectural route, with or without a plan; "architectural"
alone in the route table means the one without a plan. State the route in one
line with the reason and the risk check, for example "Bounded: a flag on the
existing `status` command; no risk trigger." Brainstorming says this line
before its first question. A task that hits the risk line states its route
before any skill in the table runs. A bug states no route, even when its fix
may touch the risk line (see Bug below).
The user can change the route. When unsure between two routes, pick the
heavier one. A route only moves up: when the work turns out heavier than its
route, stop and say so before going on.

**The risk line.** A change to stored data or its shape, permissions, a
message or public contract, or something hard to reverse is architectural
with plan, whatever path brainstorming would pick. A spike is exempt, because
its code never lands. The risk line also decides where the tasks go: an
architectural change without a risk trigger keeps its tasks in the spec; one
with a trigger gets a separate plan.

| Route | Who picks it | Documents | Reviews | Commits on `main` |
|---|---|---|---|---|
| **Spike** | Brainstorming | `docs/plans/YYYY-MM-DD-<slug>-spike.md` | None | One `docs:` commit, the spike file. Its code is never merged. |
| **Bounded** | Brainstorming, one or two files, no risk trigger | None. A short design in chat, approved before any code. | `/code-review high` on the branch | One: the squash-merged code. |
| **Architectural** | Brainstorming, or more than two files; no risk trigger | Architecture brief where the trigger table asks for one; one spec, with a **Tasks** section in place of a plan. | `my:spec-review` on the spec; the end-of-branch reviews. No plan review. | Three: the spec with its review, the code, the `done` mark. |
| **Architectural with plan** | The risk line | Architecture brief where the trigger table asks for one, spec, plan. | All reviews in this file. | Four, as in "One feature, four commits". |
| **Bug** | `systematic-debugging` | None, unless it goes to brainstorming. | `/code-review high` on the branch | One: the squash-merged code. |

- **Spike** answers one question. Brainstorming's gate stays: the user
  approves the question and the probe first.
  - Its code lives in a worktree on a branch named `spike/<slug>`. The branch
    is never merged and is kept as a record, like any other branch. Once
    the spike file lands, remove the worktree with `git worktree remove`.
  - It writes `docs/plans/YYYY-MM-DD-<slug>-spike.md` with four parts: the
    question, what was tried (with the branch name), the answer, and the
    recommendation. The file names the branch, never a commit hash from it:
    docs cite only commits on `main`. The `pre-commit` hook catches such a
    hash only when it is written in backticks.
  - The file's status is `answered, <date>`. `my:status` treats any status
    outside its open list as closed, so a spike file never shows as open
    work.
  - One `docs:` commit lands the file. No review runs.
  - A spike needs no roadmap row. When a row exists, it links the spike file.
  - Keeping the spike's code is a new task, and brainstorming classifies it
    again.

  A spike may also run inside an architectural route, before the spec, to
  answer one design question. It writes the same file, and the spec lists
  that file under "How to read this spec". Give the spike a slug of its own,
  not the spec's: `my:handoff` refuses to start when a branch `*/<slug>` or a
  worktree `.claude/worktrees/<slug>` exists for the spec's slug. `my:architect`'s own spikes stay as
  they are: throwaway code in its work folder, never committed, with the
  result written into the brief.
- **Bounded** touches one or two files in an existing flow, with no risk
  trigger. A change to more files in an existing flow is architectural, with a
  spec that holds its tasks. Brainstorming runs, on its bounded path: a short
  design in chat, and no code starts before the user says yes. Bounded skips
  the writing-plans and executing-plans rows. Every code change still starts
  with a failing test. It still runs in a worktree. Known limits from its review go
  into the squash commit message, because there is no **Risk** section to hold
  them. Several bounded changes and bug fixes may share one branch when each
  one alone is bounded or a bug fix. Each fix is its own commit with its own
  failing test first. The branch gets one review round and one squash commit,
  whose body names each fix's roadmap row.
- **Bug** starts with `superpowers:systematic-debugging`, with no route line.
  After the root cause is found, the bug goes to brainstorming in any of four
  cases:
  - the fix hits the risk line;
  - there are several reasonable fixes;
  - the fix touches more than two files, which is bounded's limit;
  - three fixes have failed, which is the debugging skill's own "question the
    architecture" step.

  Brainstorming then picks the route as for any task, with the root cause as
  its input. A bug skips the brainstorming, writing-plans and executing-plans
  rows, unless it goes to brainstorming. Otherwise the fix follows the bounded
  rules, without the design gate.
- **Architectural** writes the Tasks section by the rules of
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
  hand-off above, and auto runs `/my:handoff auto code <spec path>` with the
  `approved` edit left uncommitted. The auto code stage commits and folds
  that edit itself. Where the project keeps a plans
  index, its row goes into the spec commit. Wherever this file says "the
  plan" for an architectural change without a plan, read "the spec": its
  **Tasks** section and its **Risk** section play the plan's part.
- **Architectural with plan** follows the rest of this file unchanged.

| Task class | Invoke first |
|---| ---|
| New project, new subsystem, or change to a data model, storage choice or public contract | `my:architect`, then `superpowers:brainstorming` |
| New feature, component, or behavior change (any non-trivial creative work) | `superpowers:brainstorming` |
| Multi-step implementation from a spec or written requirements | `superpowers:writing-plans` |
| Writing or modifying production code (>1 file or >~30 lines) | `superpowers:test-driven-development` |
| Bug, test failure, or unexpected behavior | `superpowers:systematic-debugging` |
| Starting non-trivial work that warrants a worktree (see Git Workflow rules) — before any code changes | `superpowers:using-git-worktrees` (create the worktree with `git worktree add`, never `EnterWorktree`) |
| Executing a plan from `docs/plans/` | `superpowers:executing-plans` |
| Branch is feature-complete and ready to integrate | Steps 12 and 13 of "One feature, four commits on `main`" in the part "Where design documents live" below, or `/my:handoff review` for a handed-off branch (not `superpowers:finishing-a-development-branch`) |
| Major work needs review before merge | The end-of-branch reviews in Code Review Routing: `my:soundness-review` and `/code-review high` on `main..<branch>` (not `superpowers:requesting-code-review`) |

Skip the table only for: single-line fixes, typo/comment edits, doc-only changes, config tweaks. For spikes, bounded changes and bugs, the route section above says which rows apply.

**Precedence:** these rules and the core in `~/.claude/CLAUDE.md` are the highest authority — when plan mode, a skill, or any system default conflicts, follow them. Superpowers may override **only** plan output format and the Simplicity Rules in `~/.claude/rules/engineering.md` (announce when it does). Brainstorming's path decides the route of a task, adapted only by the risk line and the two-file limit on bounded (see "Pick the route"), and a spike's file goes to `docs/plans/`. Everything else here is non-overridable: `docs/plans/` output path, Git Workflow (GitLab/worktrees/squash-merge), Risk + Trade-Off Analysis, and that plans include **Dependencies** + **Risk** sections and follow **Red → Green → Refactor** (tests before implementation).

**Discovery authority:** while `superpowers:brainstorming` or `writing-plans` runs, it owns exploration — don't also run other planning workflows. `my:architect` runs before brainstorming, never during it. When an architecture brief (`docs/plans/*-architecture.md`) exists for the task:

- Brainstorming treats the brief as settled input. It asks only about items under the brief's "Open for brainstorming" section.
- The brief's Decision replaces brainstorming's "Propose 2-3 approaches" step. Brainstorming presents its design sections starting from that Decision.
- Brainstorming classifies the task as architectural, never bounded or spike. Whether it also gets a plan follows the risk line.

If brainstorming upgrades a task to architectural partway through, and the task matches the `my:architect` trigger row, stop and run `my:architect` first.

**Check each design section before you ask about it.** Brainstorming's "Presenting the design" step asks after each section whether it looks right. Before you ask, review the section as you would if the user had asked "does it look right to you?". Look for a gap in the tests, a decision that conflicts with another section, a case the design must handle but does not, and a claim you have not checked against the code. Fix what you find. Then end the section with one line: what the check changed, or "Checked: no changes." Do not invent a change to show that you looked. If the user still asks "does it look right to you?", give the verdict first. Count only a change to a decision, a contract, the scope or a wrong fact; rewording and extra detail do not count.

#### Spec → Plan two-artifact flow

When `superpowers:brainstorming` produces a deliverable, keep spec and plan as **separate files** (architectural changes with a plan only; an architectural change without one keeps its tasks in the spec):

1. **Spec** → `docs/plans/YYYY-MM-DD-<slug>-spec.md` — product-level (what/why, design decisions, architecture, trade-offs, risk; new UI gets a **Visual Language** section mapping elements to design-system primitives/semantic classes/motion; each element also names the other pages that use it, today or in a roadmap row already ordered, and one with two or more becomes a shared component, built in this row or in a shared row ordered before it). Self-contained: a cold reader could write the plan from it alone. First section is **"How to read this spec"** — all related docs (specs, plans, ROADMAP, CHANGELOG, sources, skills) with paths, in reading order. When an architecture brief exists, it is listed first. Ask the user whether the spec may run in auto mode (`/my:handoff auto`); on yes, add a **Delegation** section with the four keys that the `my:handoff` skill defines in its "Delegation" section.
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

**The end-of-branch reviews are the only reviews, so each one gets what it needs.** Pass the explicit range `main..<branch>` to every review. Some review skills diff against `origin/main` by default, which can lag local `main`, so check each review's scope note and rerun a review that read the wrong range. Name the `/code-review` level every time (`high` unless the project says otherwise). Without a level it reuses the last one typed, which may be `low`. Each subagent's prompt names the spec, the plan, the plan's **Risk** section and the map from "Before any review", and says that a known limit in **Risk** is not a finding. When a plan runs through `superpowers:subagent-driven-development` or `superpowers:executing-plans`, skip the skill's own reviews: its pre-flight plan review, its per-task reviewer and fix loop, and its final `requesting-code-review` pass. The plan review already covered the plan, and these end-of-branch reviews replace the rest. Two checks replace the per-task reviewer. First, after each task, the controller reads `git diff` for the test files the task touched, and stops if an assertion was removed or weakened, because `npm test`-style runs still pass then. Second, `my:soundness-review` gets the plan, not the spec, as its document (`main..<branch> <plan>`), so it checks that each task did what the plan said. An architectural change without a plan gives it the spec. The plan links the spec, and the skill takes one document only. A project can set its own level or review list, but never a default range.

**One fix round per review.** A finding about input that today's code never produces goes into the plan's **Risk** section as a known limit, not into a fix. A fix gets one re-review, and that re-review is final. The one exception is a new Critical finding in the re-review: bring it to the user before the merge. A lesser finding goes into **Risk**. Without this limit, each fix invites a new edge case and the rounds do not end.

## UI Design

Any discussion that turns to UI — screens, layout, controls, states, visual
language — must be **shown**, not described. Reach for the design tooling before
writing a prose description or a table of class names:

- **`design`** — the Artifact tool's **Design** type: a Claude Design canvas
  of `.dc.html` artboards on one pan/zoom canvas. **Always, for any screen,
  state or flow.** This holds inside `superpowers:brainstorming` too: that
  skill's own Visual Companion is an ephemeral local server, it is not a
  substitute, and it is not to be offered.
- **Aesthetic direction** — typography, and choices that do not read as
  templated defaults. `kit:design-router` names the skill.
- **`artifact-diagramming`** — when the point is a mechanism rather than a screen.

A bounded change or a bug fix that adds no screen and no state, such as
a label, a colour or a spacing value, needs no canvas.

Prose may summarise a design that has been drawn. It may not stand in for one.

This does not replace the **Visual Language** section a spec requires: that
section maps an already-drawn design onto real primitives and semantic classes,
verified against the stylesheet rather than assumed. Both are needed — the
drawing decides, the table records.

**Keep a canvas sorted by status.** A canvas has three pages: «Built» (what
the app looks like now), one page per row under review, and «History»
(options not chosen, earlier versions). When a row's code merges, in the same
step as its `done` marks, move its chosen boards to «Built», the rest to
«History», and retitle any board the change made untrue.

## Git Workflow

I am the sole developer on these projects. **Worktrees + squash-merge are mandatory** for non-trivial work; **MRs are optional** — used only when they add value a plain squash-merge can't (see below). This overrides Superpowers git workflow (including `finishing-a-development-branch`).

We use **GitLab** unless stated otherwise in the project. There are no "pull requests" — only **merge requests (MRs)**.

- Always squash-merge when integrating branches — no regular merges, whether via MR or local `git merge --squash`
- Use `glab` CLI (not `gh`) for MR operations when you do open an MR
- Use `glab mr create` instead of `gh pr create`
- Read `git diff --cached` before every commit. The Edit tool has silently dropped a character, and a trailer the project forbids has slipped into a commit. The exception: in a project with a "Parallel runs" section, a commit in the main checkout reads `git diff -- <paths>` and each new file whole before the locked command in the next rule (`git diff` does not show a file git does not track yet), and reads the `git show --stat` list that the command prints. This replaces every `git diff --cached` reread this file names.
- In a project whose `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs" section (the `my:handoff` skill defines it), several auto runs share `main`. There, every commit in the main checkout runs under lock `main`: write the message with the Write tool to a new file in the session's scratchpad, then run `locked-commit.py -F <message file> <paths>`. It stages, commits and lists the commit inside the lock, and no shell reads the message. Nobody makes fixups there: every later edit to a spec, plan or review is a normal commit, and nothing folds. Commits in a worktree take no lock.

### One feature, four commits on `main`

An architectural change with a plan leaves four commits on `main`: the spec with its review, the plan with its review, the squash-merged code, and the `done` mark. The other routes leave fewer, as the route table says. The fourteen steps, and when to fixup and fold, are in the section "One feature, four commits on `main`" of the part "Where design documents live" below.

**Before step 1 in a project for the first time,** check that the project's `CLAUDE.md` has a `## Project facts` block that names the commit scopes, the test command, the plans index and the remote. If it is missing or incomplete, run `/kit:setup my`.

- **A `docs:` commit runs no tests and no code reviews.** This covers every commit that touches only `.md` files: specs, plans, their reviews, fixups, index rows and the `done` marks (step 13). The only checks are the Markdown linter and a reread of `git diff --cached`. The spec review (step 2 in the part "Where design documents live") and the plan review (step 6) still run, because they are the content of the commit, not a check on it. A code branch that also edits docs is reviewed as a code branch.

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

These standards add to the Engineering standards in `~/.claude/rules/engineering.md`. Critical Thinking (in the core), Risk Awareness and Trade-Off Analysis are always enforced. Mandatory Exploration (in `~/.claude/rules/engineering.md`) applies only when no superpowers discovery skill is active (see Superpowers Integration above). Plan Output Format may be overridden by Superpowers. In a plan, the "Files to Modify" list is the output of the Reference Sweep in `~/.claude/rules/engineering.md`: every hit is a row.

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

Plans use these sections (Superpowers may substitute its own format): **Context · Files to Modify/Create · Step-by-Step Implementation · Trade-Offs/Alternatives · Dependencies · Risk · Testing Strategy · Open Questions**. The full template with per-section field prompts is the part "Plan Output Format" at the end of this style.

# Where design documents live

These rules apply unless the project documents its own layout. If it does, follow the project
and do not convert it without asking. Some projects generate their index, or keep status in
`ROADMAP.md` instead of in each file. The section "One feature, four commits on `main`" is the
exception: it is part of the Git Workflow and always applies. A project names only what differs
there.

## Kinds of document

| Kind | What it is | Where | Name |
| --- | --- | --- | --- |
| Spec | What to build and why. | `docs/plans/` | `YYYY-MM-DD-<slug>-spec.md` |
| Plan | How to build it: steps, tests, commits. | `docs/plans/` | `YYYY-MM-DD-<slug>.md` |
| Review | A report on one spec, one plan or one diff. It sits next to what it reviewed. | `docs/plans/` | `…-review.md`, `…-review-2.md` |
| Spike | The answer to one question: what was tried and what it showed. Its code is never merged. The file names the spike's branch, never a commit from it. | `docs/plans/` | `YYYY-MM-DD-<slug>-spike.md` |
| Report | Findings about a whole product or area on one day, such as a design critique, an audit or an architecture critique. Other documents fix what it finds. It is never carried out itself. | `docs/reports/` | `YYYY-MM-DD-<slug>-critique.md`, `-audit.md` |
| Action plan | Optional. Routes a large report's findings into roadmap rows once, then stays as a reference. | `docs/plans/` | `YYYY-MM-DD-<slug>-action-plan.md` |
| Briefing | A plain-language write-up for readers outside engineering (`kit:briefing`). | `docs/briefings/` | `YYYY-MM-DD-<slug>.md` |

The test for "report or review": a review has one subject that someone will change in answer to
it. A report has many findings across many files, and several later documents answer it.

## From report to roadmap

A report's findings become rows in the project's roadmap. The roadmap is the one live list of
work, and it keeps the only order. The chain is:

```text
report → roadmap rows, placed in the order → spec or plan, by route → branch
```

- **The roadmap keeps the order.** It lives in the roadmap's `## Order of work` section
  (`my:roadmap-management` rule 12). No other document holds the order, a gate, or whether work
  has started or shipped. A document that did would be a second copy, and copies drift.
- **Each row cites its finding:** the report's path and the finding's reference (item letter,
  finding code or heading).
- **A row that cannot start says why, in the row:** `Blocked by row N.`, or `Waits for <what>.`
  for a blocker outside the roadmap, such as a client's answer or a missing file.
- **The report records where its findings went.** A short "Where these went" section maps each
  reference to a row, or to "no action" with a reason. The report's status line names the rows.
- **Bug fixes and features are separate rows,** so they become separate branches.
- **Shared things come first.** A row that adds tokens or components sits before the rows that
  use them in pages. This keeps each value from changing twice.
- **Decisions go where the work reads them.** A decision about one row goes into that row's
  spec. A decision for the whole product goes into the project's `CLAUDE.md`. Do not keep a
  separate decision log that work has to search.

### Routing a report

1. **Read the whole report.** Note each finding's reference.
2. **Sort the findings.** Mark each one as a bug, a feature, a shared definition (tokens,
   components), a use of shared things in pages, a product decision, blocked outside the
   project's scope, or no action.
3. **Propose rows and their place in the order** to the user. Group the findings that one branch
   would fix into one row. Wait for the user's answer: the order is a decision, so it is not
   guessed.
4. **Write it down.** Add the rows and their place in `## Order of work`. Add "Where these went"
   to the report and update its status line. If the project has an index, update the report's
   row in the same commit.
5. **Run the checklist** below, then commit. This is documentation only, so it needs no
   worktree.

### When an action plan helps

Route directly when you can. Write an action plan only when a report is too large to route in
one sitting, or when the grouping needs several rounds with the user.

- **It is a working file for the routing,** nothing more: the groups, the user's answers with
  their dates, and the questions still open.
- **It ends when every finding has a row or a reason.** Its status becomes `done`, naming the
  commit that added the rows. After that it is a reference, and nobody edits it.
- **It never holds the order, a gate, or the state of work.** Those are in the roadmap from the
  first row on.
- **A later report gets its own routing.** It does not join an old action plan.

### Checklist

- Every finding in the report has a row, or a reason in "Where these went". None is missing.
- Every row cites its finding's reference.
- No row mixes a bug fix and a feature.
- No row uses a shared definition before the row that defines it, in the order.
- Every row that cannot start says what it waits for.
- The order lives only in the roadmap. An action plan, if there is one, is `done` and holds no
  order.
- After any move or rename, `git grep` finds no link to the old path.

## Status line

Every file in `docs/plans/` and `docs/reports/` opens with one line, just under its title:

```markdown
**Status:** <status>, <YYYY-MM-DD>. <one sentence>.
```

| Status | Meaning |
| --- | --- |
| `draft` | Written, waiting for the user's approval. |
| `approved` | Approved, not started yet. |
| `planned` | An agreed later step, not started. |
| `current` | Work in progress, or a report that is still the live source of findings. |
| `parked` | A draft set aside until a named step decides what happens to it. |
| `done` | Shipped. The sentence names the commit. |
| `answered` | A spike. The sentence gives the answer in short. |
| `superseded` | Will not be carried out. The sentence names what replaces it. |
| `withdrawn` | Dropped. Nothing replaces it. |
| `review of <file>` | A review. The sentence names what it reviewed and what answered it. |

Update the status when it changes: a spec is approved, a plan's branch is merged, or a document
is replaced or dropped.

## Index

An index at `docs/plans/README.md` is optional. It lists every file in `docs/plans/` and
`docs/reports/`, gives the reading order for the current work, and tells how the work got here.
A file gets its row in the same commit that creates it or changes its status.

The line `<!-- plans-index: strict -->` in that README turns on two checks in the
`check-orphan-plans.sh` session hook: a file missing from the index, and a file with no status
line. Without the line, the hook checks only that files are committed and dated.

## Moving a document

When a document moves or is renamed, update every link to it. Search the repo for the old path
with `git grep`. Keep superseded documents in place, marked `superseded`, instead of deleting
them.

## One feature, four commits on `main`

An architectural change with a plan leaves four commits on `main` (the other routes leave fewer, as
the route table in "Pick the route" above says): the spec with its review, the plan with its
review, the squash-merged code, and the `done` mark. Without this rule, most commits are small edits to one spec or plan: on
zitamu, 44 of 52 commits by 2026-09-18 were `docs:`. Docs are written in the main checkout,
because an `@` mention cannot reach `.claude/worktrees/`. Code is written in a worktree, because
sessions often run in parallel. A project's own file names only what differs: its plans index, its
scopes, its test commands.

Three more commits are allowed. `my:architect` commits the architecture brief on its own, before
step 1. An edit to another document that the spec forces, such as a glossary or a data model, is
its own commit, not a fixup of the spec. The spike file of a spike that runs inside an
architectural route, before the spec, is its own `docs:` commit, before step 1.

1. Write the spec on `main`.
2. Write the spec review on `main`.
3. Commit the spec and the review together.
4. Fixup any later spec and review edits, with `git commit --fixup <hash>`. Run
   `git-fold-fixups.py check <hash>` first. If it exits 1, make a normal commit instead. Always
   name the target by hash, never `--fixup HEAD`: a parallel session may have committed in between.
5. Write the plan on `main`.
6. Write the plan review on `main`.
7. Commit the plan and the plan review together.
8. Fixup any later plan and plan-review edits. Run `git-fold-fixups.py check <hash>` first. If it
   exits 1, make a normal commit instead. Always name the target by hash, never `--fixup HEAD`: a
   parallel session may have committed in between.
9. Fold the fixups with `git-fold-fixups.py`. It refuses, and changes nothing, when the fold is not
   safe; its message says why. Run it when no other session has uncommitted edits in the main
   checkout.
10. Create the worktree, and write the code there.
11. Make doc edits in the worktree as required, but never edit the project's plans index there.
    While the worktree exists, edit this feature's spec and plan only in the worktree.
12. Squash-merge the branch into `main`, and commit.
13. Mark the spec and plan `done` on `main`, citing the squash commit.
14. The user pushes at their own pace.

In a project whose `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs" section (the `my:handoff`
skill defines it), several auto runs share `main`. There, every commit in the main checkout runs
under lock `main`, as one command that stages, commits and lists the commit. Write the message
with the Write tool to a new file in the session's scratchpad, then run:

```bash
locked-commit.py -F <message file> <paths>
```

Before it, read `git diff -- <paths>` and each new file whole: `git diff` does not show a file git
does not track yet. After it, read the `git show --stat` list it printed. Steps 4 and 8 make normal
commits, not fixups, and step 9 is skipped: a fold could give another run's cited commit a new hash.
Four commits remain the goal elsewhere.

- **No commit only changes a status.** There is no "in progress" commit. A status change goes into
  the commit that causes it.
- **Cite only commits on `main`.** Never cite a commit that lives only on a local branch. A review
  names the decisions and sections it read, like "D12 to D16", not a hash, because later fixups fold
  the answers into the reviewed commit. The `pre-commit` and `pre-push` hooks in
  `~/projects/claude-setup/global/git-hooks/` enforce this rule and refuse a push with `fixup!`
  commits. zitamu (`real-estate-webapp`) uses them: an `includeIf` in `~/.gitconfig` (in
  `~/.dotfiles`) sets its `core.hooksPath`, so a fresh clone at the same path gets them.

# Plan Output Format

Every section is required. Superpowers may substitute its own format; when it
does not, plans use this one. **Dependencies** and **Risk** are non-overridable.

```markdown
# {Feature} Plan

## Context
[What problem are we solving? Why? What exists today? What prompted this change?]

## Files to Modify/Create
[Each file with a brief description of what changes and why. Reference existing functions/utilities to reuse with file paths.]

## Step-by-Step Implementation
[Numbered steps, each small enough to be a single commit. Concrete enough that a developer doesn't need to re-derive the design.]

## Trade-Offs / Alternatives Considered
[Options evaluated, pros/cons, and why this approach was chosen. Skip with a one-liner only if the decision is genuinely trivial.]

## Dependencies
[External packages, env vars, config changes needed — or "None"]

## Risk
[Reversibility, blast radius, what could break, how to detect, manual steps. Required.]

## Testing Strategy
[What tests to add/modify; how to verify the feature works end-to-end. If no automated tests are possible, describe the manual verification.]

## Open Questions
[Anything that needs user input before implementation starts. If none, write "None."]
```

## Output discipline

- Do not skip sections to be brief. Each section is short by default; expand only where the task warrants it.
- If a section genuinely does not apply, write "N/A — [one-line reason]" rather than omitting it.
- Do not write code beyond illustrative snippets inside the plan.
