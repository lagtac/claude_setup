# The `my` plugin

`my` is a development method built on top of
[superpowers](https://github.com/obra/superpowers), a third-party plugin.
Superpowers gives the steps of one change: brainstorm, write a spec, write a
plan, build it test-first, review it, finish the branch. `my` answers four
questions that superpowers leaves open:

- **What comes next?** The roadmap holds the one order of work.
- **How much process does this change need?** Each change gets a route, from
  a short design in chat for a small fix to a brief, a spec and a plan for a
  change to stored data.
- **Who checks the work?** A second reader reviews each spec, each plan and
  each branch before anything lands.
- **What does `main` look like after?** Each branch lands as one squash
  commit, so `main` stays a short record of what shipped and why.

Each stage leaves a reviewed document behind. So a stage can run in its own
session, or without you, within the limits its spec sets.

This file explains what `my` adds and where it differs from superpowers. The
list of skills, agents, scripts and hooks is in the root
[`README.md`](../../README.md). The comparison below was checked against
superpowers 6.4.2. A later version may differ. The measured costs of the
overlap are in
[`docs/reports/2026-10-14-superpowers-fit-critique.md`](../../docs/reports/2026-10-14-superpowers-fit-critique.md).

## Where the parts live

The method has two parts, and only one of them is this plugin:

- **The rules** are the `my` style (`plugins/my/output-styles/my.md`), an
  output style that this plugin forces on, so they load in every session where
  the plugin is on. They say which skill runs when, and they hold the route
  table and the Git Workflow.
- **The tools** are this plugin: the skills, the review agents, the scripts in
  `bin/` and the hooks. The rules call them by name.

The plugin is off at user scope, and so is superpowers. A project turns both
on with `/kit:setup my`, which writes the plugin keys and a
`## Project facts` block, with no import line. A project never runs `my`
without superpowers.

## What superpowers gives

Superpowers is a chain of skills. Each skill ends by sending you to the next:

```text
brainstorming → writing-plans → subagent-driven-development or executing-plans
              → requesting-code-review → finishing-a-development-branch
```

`test-driven-development`, `systematic-debugging` and
`verification-before-completion` apply at every step.

Superpowers already does more than one fixed path:

- **It picks a path for the work.** Brainstorming picks one of three paths.
  A *spike* answers a question and writes no document. A *bounded* change gets
  a short design in chat, with no spec and no plan. An *architectural* change
  gets a written spec and then a plan.
- **It keeps the spec and the plan apart.** The spec goes to
  `docs/superpowers/specs/`, the plan to `docs/superpowers/plans/`.
- **It reviews code inside the build.** In subagent-driven mode, a reviewer
  checks each task before the next one starts. One reviewer then checks the
  whole branch, with one fix round.

What superpowers does not have: a list of work across changes, a review of
the spec or plan by a second reader, or rules for what lands on `main`.

## What `my` adds

### The roadmap is the only order of work

Each project keeps a `ROADMAP.md`. Each row is one piece of work, with a
status tier: `💭` discussed, `📋` planned, `🚧` in progress, `✅` shipped. The
`## Order of work` section holds the order. No other document holds an order,
a gate or a status of work. `my:roadmap-management` edits the roadmap.

A row is the unit of work. It enters the cycle at the start and leaves it at
the `done` mark. Rows do not share work. The only link between two rows is
that one is ordered before the other.

A report (an audit or a critique of a whole area) never becomes work itself.
Its findings become roadmap rows. The `my` style
(`plugins/my/output-styles/my.md`) has the rules for that.

### The routes

The session states the route in one line, with the reason and the risk check.
Brainstorming says it before its first question; a task that hits the risk
line states it before any skill runs; a bug states none. The route decides the
documents, the reviews and the commits:

| Route | Who picks it | Documents | Reviews |
| --- | --- | --- | --- |
| **Spike** | Brainstorming | `docs/plans/YYYY-MM-DD-<slug>-spike.md` | None |
| **Bounded** | Brainstorming, one or two files, no risk trigger | None. A short design in chat, approved before any code. | `/code-review high` on the branch |
| **Architectural** | Brainstorming, or more than two files; no risk trigger | Architecture brief where the trigger table asks for one; one spec, with a **Tasks** section in place of a plan. | `my:spec-review` on the spec; the end-of-branch reviews. No plan review. |
| **Architectural with plan** | The risk line | Architecture brief where the trigger table asks for one, spec, plan. | All reviews in `my.md`. |
| **Bug** | `systematic-debugging` | None, unless it goes to brainstorming. | `/code-review high` on the branch |

The full table, with the commits for each route, is in the `my` style
(`plugins/my/output-styles/my.md`).

The old names map as follows: Small is bounded or bug, Medium is
architectural, Large is architectural with plan. Specs, plans and reviews
finished before row 67 still use the old names.

### A review for each document

Superpowers checks its own spec and plan. `my` adds a second reader for each:

- `my:architect` writes an architecture brief before the spec, for a new
  subsystem or a change to a data model, storage choice or public contract.
- `my:spec-review` reviews the spec as a system: components, contracts, who
  owns which state, and how a failure spreads.
- `my:soundness-review` reviews the plan against the repo, and later the code
  against the plan.

### Reviews at the end of the branch, not per task

`my` turns off the reviews that superpowers runs during the build: the
pre-flight plan review, the reviewer after each task, and the final
`requesting-code-review` pass. It runs two reviews once, on the whole branch
(`main..<branch>`), in parallel:

- `my:soundness-review`, a for-and-against verdict, and a check that each
  task did what the plan said.
- `/code-review high`, the built-in bug finder.

Each review gets one fix round. Instead of the reviewer after each task, the
session reads the diff of the test files after each task, and stops if an
assertion was removed or weakened.

### Worktrees, squash-merge and four commits on `main`

Code is written in a worktree, made with `git worktree add`. The branch lands
on `main` as one squash commit. Superpowers' `finishing-a-development-branch`
does a regular merge and can delete the branch. `my` replaces it: it
squash-merges and keeps the branch as a record.

An architectural change with a plan leaves four commits on `main`: the spec
with its review, the plan with its review, the code, and the `done` mark. An
architectural change without a plan leaves three, a bounded change or a bug
fix one, and a spike one `docs:` commit, its file. The fourteen steps are in
the `my` style (`plugins/my/output-styles/my.md`).

### Where the documents go

All specs, plans and reviews go to `docs/plans/YYYY-MM-DD-<slug>.md`, not to
`docs/superpowers/`. A spec ends in `-spec.md`. Each file opens with a
`**Status:**` line.

## How each superpowers skill is used

| Superpowers skill | Under `my` |
| --- | --- |
| `brainstorming` | Used for every task that is not a bug or on the skip list. Its path picks the route; the risk line can make it heavier. Writes to `docs/plans/`. `my:architect` runs first when its trigger matches. For UI, the Design artifact replaces the Visual Companion. |
| `writing-plans` | Used for architectural changes with a plan. Writes to `docs/plans/`. The plan must have **Dependencies** and **Risk** sections. |
| `test-driven-development` | Used as is, for every code change. |
| `systematic-debugging` | Used as is, for every bug. |
| `using-git-worktrees` | Used, but the worktree is made with `git worktree add`, never the `EnterWorktree` tool. |
| `subagent-driven-development`, `executing-plans` | Used, with their own reviews turned off. |
| `requesting-code-review` | Replaced by `my:soundness-review` and `/code-review high`. |
| `finishing-a-development-branch` | Replaced by steps 12 and 13 in the `my` style (`plugins/my/output-styles/my.md`), or `/my:handoff review`. |
| `verification-before-completion`, `receiving-code-review`, `dispatching-parallel-agents` | Not named by `my`. They work as superpowers ships them. |

## `/my:handoff`: the same cycle, run faster

`/my:handoff` runs each stage (plan, code, review) in a new Claude session, in
its own tmux window. In auto mode it runs the whole cycle without the user, as
far as the spec's **Delegation** section allows. `/my:handoff auto rows` runs
several roadmap rows at once.

It does not change the cycle. Every row still goes through the same stages in
the same order. How it works: [`skills/handoff/README.md`](skills/handoff/README.md).

## Limits

- **A route only moves up.** Bounded skips the spec and the plan.
  Architectural skips the separate plan. If the work turns out heavier than
  its route, the session stops and says so.
- **Correctness is checked at fixed gates.** Documents are checked before any
  code. Code is checked once, at the end of the branch. This assumes the design
  can be decided before the code is written. It works badly when you learn the
  design only by trying things. The spike route covers that case: it writes
  an answer, not code that lands.
- **The cost is per row, not per change.** Each row carries fixed work:
  documents, reviews and commits. This cost is highest when there are many
  small rows, or when a row is exploratory.
