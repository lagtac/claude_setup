# The `my` plugin

`my` is a development method built on top of
[superpowers](https://github.com/obra/superpowers), a third-party plugin.
Superpowers gives the steps of one change: brainstorm, write a spec, write a
plan, build it test-first, review it, finish the branch. `my` adds the layer
around those steps: the roadmap that orders the work, the size of each change,
its own reviews, and the git rules for getting code onto `main`.

This file explains what `my` adds and where it differs from superpowers. The
list of skills, agents, scripts and hooks is in the root
[`README.md`](../../README.md). The comparison below was checked against
superpowers 6.4.2. A later version may differ. The measured costs of the
overlap are in
[`docs/reports/2026-10-14-superpowers-fit-critique.md`](../../docs/reports/2026-10-14-superpowers-fit-critique.md).

## Where the parts live

The method has two parts, and only one of them is this plugin:

- **The rules** are in `global/methods/my.md`. A project loads them with the
  line `@~/.claude/methods/my.md` in its `CLAUDE.md`. They say which skill
  runs when, and they hold the size table and the Git Workflow.
- **The tools** are this plugin: the skills, the review agents, the scripts in
  `bin/` and the hooks. The rules call them by name.

The plugin is off at user scope, and so is superpowers. A project turns both
on with `/kit:setup my`, which writes the import line, a `## Project facts`
block and the plugin switches. A project never runs `my` without superpowers.

## What superpowers gives

Superpowers is a chain of skills. Each skill ends by sending you to the next:

```text
brainstorming → writing-plans → subagent-driven-development or executing-plans
              → requesting-code-review → finishing-a-development-branch
```

`test-driven-development`, `systematic-debugging` and
`verification-before-completion` apply at every step.

Superpowers already does more than one fixed path:

- **It sizes the work.** Brainstorming picks one of three paths. A *spike*
  answers a question and writes no document. A *bounded* change gets a short
  design in chat, with no spec and no plan. An *architectural* change gets a
  written spec and then a plan.
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
Its findings become roadmap rows. `global/rules/docs-layout.md` has the rules
for that.

### The size table

Before any skill runs, the session picks a size and states it in one line.
The size decides the documents, the reviews and the commits:

| Size | When | Documents | Reviews |
| --- | --- | --- | --- |
| Small | A fix or small change in one or two files. | None. | `/code-review high` on the branch. |
| Medium | A feature or fix across several files. | One spec, with a **Tasks** section instead of a plan. | `my:spec-review` on the spec; the end-of-branch reviews. |
| Large | A change to stored data, permissions, a public contract, or something hard to reverse; a new subsystem. | Architecture brief when needed, spec, plan. | All reviews. |

The full table, with the commits for each size, is in
`global/methods/my.md`.

The size table and brainstorming's three paths overlap, and only part of the
overlap is settled. When an architecture brief exists, `my.md` says that
brainstorming "classifies the task as architectural, never bounded or
spike". Without a brief, brainstorming may call a Medium change bounded (no
spec) or a spike (no document), while the size table asks for a spec. This
is finding F1 of
[the superpowers-fit critique](../../docs/reports/2026-10-14-superpowers-fit-critique.md).
Roadmap row 67 plans to replace the size table with brainstorming's paths,
plus a few `my` adaptations.

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

A Large change leaves four commits on `main`: the spec with its review, the
plan with its review, the code, and the `done` mark. Medium leaves three, and
Small one. The fourteen steps are in `global/rules/docs-layout.md`.

### Where the documents go

All specs, plans and reviews go to `docs/plans/YYYY-MM-DD-<slug>.md`, not to
`docs/superpowers/`. A spec ends in `-spec.md`. Each file opens with a
`**Status:**` line.

## How each superpowers skill is used

| Superpowers skill | Under `my` |
| --- | --- |
| `brainstorming` | Used for Medium and Large. Writes to `docs/plans/`. `my:architect` runs first when its trigger matches. For UI, the Design artifact replaces the Visual Companion. Its spike and bounded paths are not mapped to a size (row 67). |
| `writing-plans` | Used for Large only. Writes to `docs/plans/`. The plan must have **Dependencies** and **Risk** sections. |
| `test-driven-development` | Used as is, for every code change. |
| `systematic-debugging` | Used as is, for every bug. |
| `using-git-worktrees` | Used, but the worktree is made with `git worktree add`, never the `EnterWorktree` tool. |
| `subagent-driven-development`, `executing-plans` | Used, with their own reviews turned off. |
| `requesting-code-review` | Replaced by `my:soundness-review` and `/code-review high`. |
| `finishing-a-development-branch` | Replaced by steps 12 and 13 in `docs-layout.md`, or `/my:handoff review`. |
| `verification-before-completion`, `receiving-code-review`, `dispatching-parallel-agents` | Not named by `my`. They work as superpowers ships them. |

## `/my:handoff`: the same cycle, run faster

`/my:handoff` runs each stage (plan, code, review) in a new Claude session, in
its own tmux window. In auto mode it runs the whole cycle without the user, as
far as the spec's **Delegation** section allows. `/my:handoff auto rows` runs
several roadmap rows at once.

It does not change the cycle. Every row still goes through the same stages in
the same order. How it works: [`skills/handoff/README.md`](skills/handoff/README.md).

## Limits

- **The size is picked once.** Small skips the spec and the plan. Medium
  skips the separate plan. After the size is picked, the row follows a fixed
  path. If the work turns out larger than its size, the session stops and
  says so.
- **Correctness is checked at fixed gates.** Documents are checked before any
  code. Code is checked once, at the end of the branch. This assumes the design
  can be decided before the code is written. It works badly when you learn the
  design only by trying things. Superpowers' brainstorming has a spike path
  for that case. Under `my`, brainstorming runs only after the size is
  picked, and a Medium or Large size requires a spec. The rules do not say
  whether brainstorming may still take the spike path.
- **The cost is per row, not per change.** Each row carries fixed work:
  documents, reviews and commits. This cost is highest when there are many
  small rows, or when a row is exploratory.
