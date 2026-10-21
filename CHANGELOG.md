<!-- markdownlint-configure-file {"MD024": {"siblings_only": true}} -->

# Changelog

Changes to the Claude harness that a session can notice: the global
instructions in `global/`, and the `my` and `vue-lsp` plugins. Refactors,
tests and internal docs are not listed.

The plugins have no version numbers. The marketplace uses the commit hash, so
every commit on `main` is a release. Entries are grouped by month, newest
first. History before 2026-09 is in `git log` and in `docs/plans/`.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
**BREAKING** marks a change that removes a command or changes how you invoke
or install something.

## 2026-10

### 2026-10-22 — Auto runs need tmux, and the parallel squash-merge is fixed (rows 33 and 37)

Two bugs in `my:handoff`. Details are in the squash commit, with its known
limits.

- **The parallel squash-merge merges the right branch (row 33).** Claude Code
  fills `$1` and `$2` in skill text with the skill's arguments, so with a
  "Parallel runs" section the review stage's merge got the stage name in
  place of the branch. The command now uses `${1}` and `${2}`. kit's
  placeholder test checks the skills and commands of every plugin, not only
  kit. Source: B1 and S1 of the
  [scriptable steps audit](docs/reports/2026-10-14-scriptable-skill-steps.md).
- **Auto runs need tmux (row 37).** Outside tmux, an auto run wrote its state,
  printed a command and held its slot until it stopped at the next stage.
  Now the auto launch, each `run auto` stage, `auto resume` and `auto rows`
  first check that Claude runs inside tmux, that the tmux server answers, and
  that the mode is `auto` or `bypassPermissions`. If not, they refuse and
  write nothing. Start Claude inside tmux for an auto run. A supervised
  launch outside tmux still prints the command, now with the reason.

### 2026-10-21 — Questions follow the `plain` style (row 62)

The `plain` output style now covers every question a session asks,
including each part of an `AskUserQuestion` prompt: the question, its
header, and each option's label and description. Its new rule 9, "Ask in
the user's words", says a question must make sense on its own. It defines
again a term that chat defined earlier, never uses an internal label such
as "Force 5" alone, says what each option will change, and names a screen
element by what the user sees. Source: finding H5 of the
[handoff run audit](docs/reports/2026-10-15-row-74-handoff-run-audit.md).

### 2026-10-21 — The roadmap and changelog skills check links by script (row 51)

`my:roadmap-management` and `my:changelog-management` no longer check links
by eye. Before each commit they run `link-check.py`, a new script in
`plugins/my/bin/`. It lists every bad link in `ROADMAP.md` and
`CHANGELOG.md`: a path that leaves the repository, a `.html` link whose `.md`
twin exists, or a path that is missing or ignored by git. Each problem is
marked `new` when its line is in the uncommitted edit, and `old` otherwise.
Details: [spec](docs/plans/2026-10-20-link-check-spec.md).

- The skills fix each `new` problem by their rule 8 and list each `old` one
  to the user without changing it.
- A paired edit (a row marked ✅ with its changelog entry) runs the check
  once on both files.
- When the script is missing or fails, the skills check the edited links by
  hand, as before.
- Known limits, such as links whose text holds brackets, are in the spec's
  Risk section.

### 2026-10-20 — `kit:design-router` chooses the design skill (row 70)

Several design plugins hold skills that do the same job. A new
`kit:design-router` skill now names one skill per design job and starts
it. Claude can no longer call a design skill directly: a `PreToolUse` gate
in `kit` refuses the call and points to the router. A command the user
types always runs. Details:
[spec](docs/plans/2026-10-20-design-router-spec.md),
[plan](docs/plans/2026-10-20-design-router.md).

- The core (`global/CLAUDE.md`) gains a "Design work" section: invoke
  `kit:design-router` before any design work.
- The gate judges a skill by its plugin, from
  `plugins/kit/skills/design-router/plugins.json`. An installed plugin
  missing from that list is refused until someone reviews it and adds it.
- `global/methods/my.md`, `docs-layout.md`, `my:spec-review` and
  `my:handoff` no longer call or read `my:design-system` and
  `docs/DESIGN-SYSTEM.md`.
- Manual steps: run `claude plugin update kit@claude-setup` and
  `/reload-plugins`; turn off `design-superpowers@synced`; allow
  `Bash(design-router-ticket.py *)` and
  `Bash(printenv CLAUDE_CODE_SESSION_ATTENDED)`, so the router works where
  no user can answer. Until the update, the core names a skill the
  installed `kit` lacks.

### 2026-10-20 — `my:roadmap-management` offers to rewrite old rows

When a roadmap's open rows (💭, 📋, 🚧) do not follow the row order (kind
and place, what the user sees, the fix, the verdict, the link), the skill
asks once per session whether to rewrite them. On yes, it rewrites them in
a commit of its own before the requested edit, keeps every number, and
leaves ✅ rows as they are. On no, each row still moves to the order when
it is next edited.

### 2026-10-20 — Brainstorming picks the route, not a size (row 67)

`global/methods/my.md` no longer sizes work as Small, Medium or Large. A
session states a route instead, in one line with the reason and the risk
check, and brainstorming's own path picks it. The route decides the
documents, the reviews and the commits. Details:
[spec](docs/plans/2026-10-18-brainstorming-routes-spec.md),
[plan](docs/plans/2026-10-18-brainstorming-routes.md).

- **Spike** answers one question. It writes a `-spike.md` file with the
  status `answered`, and its code is never merged.
- **Bounded** is one or two files with no risk trigger: a short design in
  chat, approved before any code.
- **Architectural** keeps its tasks in the spec. **Architectural with plan**
  is forced by the risk line: a change to stored data, permissions, a
  message or public contract, or something hard to reverse.
- **Bug** starts with `superpowers:systematic-debugging` and states no route.
  It goes to brainstorming when the fix hits the risk line, has several
  reasonable options, touches more than two files, or three fixes have failed.
- Roadmap rows name their route, or `route not set` until brainstorming picks
  it. `my:clean-plans` knows the `spike` kind. The old names map as Small to
  bounded or bug, Medium to architectural, Large to architectural with plan.

### 2026-10-18 — Roadmap rows say what kind of work they are

`my:roadmap-management` now gives every row body a fixed order. First the
kind of work, where it happens and its size, as in `bug in my:handoff,
Small.` Then what the user sees, then the fix or goal, then the status and the
link. A row's short name uses the words of the person using the tool, not the
name of an internal step. A row that links no document keeps the cause and the
chosen fix, because it is their only record. Rows 33, 37, 56, 45, 46 and 62
follow the new order; other rows follow it when they are next edited.

### 2026-10-17 — `my:handoff` windows name their roadmap row (row 65)

The tmux windows that `my:handoff` opens now start with the roadmap row, as
`r<row>:`, the prefix that `kit:name-pane` uses. A code stage for row 122
opens the window `r122: code-<slug>`, and its marks follow, as in
`r122: code-<slug> ⚠`. The row is the one in `ROADMAP.md` that links the doc
and names the same change. With no such row, the window name is
`<stage>-<slug>` as before. Session names and the lines a stage prints do not
change.

### 2026-10-16 — `my:design-system`: an inventory every UI spec reads (row 64)

Each project with UI can keep `docs/DESIGN-SYSTEM.md`, an inventory of its
shared components and the patterns pages still build by hand. UI specs read
it, and spec reviews check them against it. See the
[spec](docs/plans/2026-10-16-design-system-skill-spec.md) and the
[plan](docs/plans/2026-10-16-design-system-skill.md), whose **Risk** section
lists the known limits.

- New skill `my:design-system`. `audit` builds the inventory and proposes
  roadmap rows for components to build. `refresh` updates it at step 13.
  `sync` makes or revises the project's Design System artifact, after the
  user's yes.
- New script `plugins/my/bin/ds-count.py` counts the search patterns stored
  in the inventory, in tracked files only; `--write` stores the counts.
- `global/methods/my.md`: UI work in a Medium or Large change, in a project
  with no inventory, starts with `my:design-system audit`. A UI spec maps
  each element to the inventory, or labels it «new». A canvas draws on the
  Design System artifact and checks first that it is current.
- `global/rules/docs-layout.md` step 13 runs `refresh` when the project has
  an inventory and the row touched its UI.
- `my:spec-review` flags an element built in a page where a listed component
  does the job, and a component name the inventory does not list.
- `my:handoff` treats `docs/DESIGN-SYSTEM.md` as a shared doc in a project
  with a "Parallel runs" section.
- `sync` has not been rehearsed on a real project yet.

### 2026-10-15 — A spec names the shared parts of its UI (row 59)

A spec's Visual Language section now names, for each drawn element, the
other pages that use it, today or in a roadmap row already ordered. An
element with two or more users becomes a shared component, built in the
same row or in a shared row ordered before it. `my:spec-review` checks the
claim against the pages and raises a `design` finding when a shared element
is built inside one page.

On zitamu, row 74b's spec mapped each drawn part only to the components
that already existed. Where none existed, it wrote page CSS, so the filter
toolbar, the listing summary and the empty-result box stayed inside one
page, though other pages need them.

### 2026-10-14 — The code stage runs the full test suite once per task

`my:handoff`'s code stage now says how often to run tests. While a task is
in progress, implementers run only the test files it touches. They run the
project's full test command once per task, before its first commit. A fix
round reruns only the covering test files, plus the typecheck when code
changed, and never the full suite. The code stage repeats the rule in every
brief and fix message it writes.

On zitamu's row 103, the fix messages asked for a full run after each
one-line fix, and implementers used the full suite as their first check. They
ran it 14 times, for about 15 minutes. This rule would have saved about 6.5
of them.

### 2026-10-14 — Name a tmux pane after the session's focus

`kit:name-pane` labels the tmux pane a session runs in with the session's
focus, such as `r54: put out fire`, when the user says "name it", "name pane"
or "auto name". The label names the roadmap row or goal the session chose, not
its latest step, which is what `/rename` and Claude Code's pane title follow.

- The window names itself after the labels of all its panes, joined with
  ` / `, and drops a label when its pane closes.
- Where the pane border shows the pane title, it shows the label instead.
- The skill ends with a `/rename <label>` line to paste, because a skill
  cannot run a built-in command.
- New script `plugins/kit/bin/tmux-name-pane.py` does the tmux part.

### 2026-10-14 — Start auto runs from roadmap rows (row 9)

`/my:handoff auto rows <n> ...` queues roadmap rows whose specs are
approved, and starts as many as **Max runs** allows. Each auto run that
finishes starts the next waiting row in its slot, so a list of rows runs to
the end without the user. See the
[spec](docs/plans/2026-10-13-roadmap-auto-runs-spec.md) and the
[plan](docs/plans/2026-10-13-roadmap-auto-runs.md), whose **Risk** section
lists the known limits.

- New form `/my:handoff auto rows [<row number> ...]`. It judges each row
  once, commits the specs' `approved` edits, queues the rows that can start
  and launches the first ones. Without numbers it starts waiting rows; with
  `drop <row number> ...` it cancels them.
- `handoff-state.py` gains `queue add`, `queue drop`, `queue show` and
  `pull`. `pull` starts waiting rows under lock `main`, in queue order,
  never past **Max runs**, and skips a row that can no longer start fresh.
- `my:status` shows the queue: which rows wait, for what, and which were
  skipped and why.
- Update the `my` plugin to get the new subcommands.

### 2026-10-13 — Swappable methods (row 16)

The global rules are now a neutral core plus one file per method, and each
project picks its method. The `my` plugin holds the method; a new `kit`
plugin holds the tools that any method can use. See the
[spec](docs/plans/2026-10-12-swappable-methods-spec.md) and the
[plan](docs/plans/2026-10-12-swappable-methods.md), whose **Risk** section
lists the known limits.

- **BREAKING:** 15 neutral skills, agents and commands moved from `my` to
  `kit`, so `/my:<name>` became `/kit:<name>` for them, for example
  `/kit:commit` and `kit:briefing`.
- `global/CLAUDE.md` keeps only the rules that hold under any method. The
  `my` and `tutor` rules are in `global/methods/my.md` and
  `global/methods/tutor.md`, which `~/.claude/methods/` links to.
- `my` and superpowers are off at user scope. A project turns its method on
  with one import line in its `CLAUDE.md` and a plugin switch in its
  `.claude/settings.json`.
- New skill `kit:setup` writes both, plus a "Project facts" block for `my`,
  and commits them in that project.
- New `SessionStart` hook `method-guard.py` warns when a project's method
  import is not approved, or when its plugin switch does not match.
- The cutover set up the 11 repos active at the time. In any other repo,
  run `/kit:setup my` to use the method.

### 2026-10-12 — Parallel auto runs (Design workflow)

In a project whose `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs"
section, 2 to 4 `my:handoff auto` runs can go at once. Commits in the main
checkout take turns under a lock, and a run merges only code whose checks
ran on the current `main`. See the
[spec](docs/plans/2026-10-12-parallel-auto-runs-spec.md) and the
[plan](docs/plans/2026-10-12-parallel-auto-runs.md), whose **Risk** section
lists the known limits.

- New script `handoff-lock.py` runs one command under a named lock.
- `handoff-state.py` gains `start`, which keeps a cap on live runs, `live`,
  which lists them, and `merge`, which squash-merges under the lock.
- `git-fold-fixups.py` refuses a fold that would give a commit cited in
  `docs/`, `ROADMAP.md` or `CHANGELOG.md` a new hash, in every project.
- In a project with the section, the global rules, `/my:commit` and
  `my:architect` commit in the main checkout with one locked command, and
  nobody makes fixups there. Projects without the section are unchanged.

### 2026-10-12 — `my:handoff auto` (Design workflow)

`my:handoff` can take an approved spec to its `done` marks on `main` without
the user. A **Delegation** section in the spec says what the run may decide
alone. Anything else stops the run. It never pushes. See the
[spec](docs/plans/2026-10-12-autonomous-run-spec.md) and the
[plan](docs/plans/2026-10-12-autonomous-run.md), whose **Risk** section lists
the known limits.

- New forms: `/my:handoff auto plan <spec>`, `/my:handoff auto code <spec>`
  and `/my:handoff auto resume <spec>`.
- A `PreToolUse` hook blocks `git push` in any session where `MY_AUTORUN` is
  set. Sessions without the variable are not affected.
- `handoff-state.py` keeps a run's state in `.git/my-handoff/<slug>.json`.
- `global/CLAUDE.md` asks, while a spec is written, whether it may run in
  auto mode, and offers "supervised or auto?" at the hand-off.

### Added

- `/my:status` answers "where are we", "what is next" and "what can run in
  parallel" in one short report, and writes nothing. A new script,
  `status-scan.py`, collects the facts: roadmap rows, open documents, the
  main checkout, worktrees, auto runs, and branches that may hold unmerged
  work. See the [spec](docs/plans/2026-10-12-status-skill-spec.md).
- `git-fold-fixups.py` folds waiting `docs:` fixup commits into their target
  in one step, or refuses with a reason. See the
  [spec](docs/plans/2026-10-10-git-fold-fixups-spec.md).
- The global instructions size each change as Small, Medium or Large, and
  scale the documents and reviews to the size.
- `my:handoff` code and review stages accept a spec with a **Tasks**
  section, for a Medium change that has no separate plan.
- `my:tutor`, a learning mode: the student writes the code, the tutor sets
  exercises and keeps notes in `docs/learning/`. It comes with a `tutor`
  output style. See the [spec](docs/plans/2026-10-06-tutor-spec.md).

### Changed

- `kit:name-pane` no longer ends with a `/rename <label>` line to paste.
  After naming the pane, it goes back to the work the session was doing, in
  the same reply.
- `kit:briefing` covers two more events: changes since a point the reader
  knows (the last briefing, deploy or request list), and where the product
  stands, for a first briefing. A new "Scope" section names what goes
  elsewhere. `kit:dev-reports` says it is for developers only, and a
  briefing can use its report as a source.
- A bullet roadmap row can carry a number between its icon and its title, as
  in `- 💭 12 **Title**`. `status-scan.py` passes that number to `my:status`,
  as it already did for table rows. `my:roadmap-management` gives a new row
  the next free number in the roadmap's scheme and never reuses a number.
- In a project with a "Parallel runs" section, a commit in the main checkout
  writes its message to a scratchpad file and runs
  `locked-commit.py -F <file> <paths>`. The script takes lock `main` through
  `handoff-lock.py`, and no shell reads the message, so the commit needs no
  heredoc. The global rules, `/my:commit`, `my:architect` and `my:handoff`
  use it. A commit that fails leaves its paths unstaged. Update the `my`
  plugin to get the script. See the
  [spec](docs/plans/2026-10-12-locked-commit-spec.md), whose **Risk** section
  lists the known limits.
- `my:handoff` prints one line per review finding, with its class (fix, gate
  or Risk) and the evidence, before the plan stage or the fix round fixes
  anything. The plan stage also prints why it picked the execution skill.
  The fix round tests gate before Risk, so a finding whose fix would change
  a contract reaches the user, and a gate stops the round before any fix. A
  new Critical finding in the re-review always stops the run, even with
  `decide`.
  See the [audit](docs/reports/2026-10-12-handoff-instructions-audit.md), R2.
- `/my:status` lists two items that use the same **Shared resources** lock
  as safe to run together, and says they take turns on that lock. Before,
  any item that used a shared resource could not pair with another, so two
  code items in a project with one Docker stack never paired. An item whose
  files include one that a shared-resource command names or runs, such as
  its script, still does not pair.
- `my:spec-review` checks that a spec which adds UI decides off-path events:
  browser Back and Forward, a reload or deep link, a record deleted or
  restored while shown, an element that hides with focus or a panel open, a
  language change, and empty and error text. A missing decision is a
  `design` finding, so the author decides it.
- The fourteen feature steps moved from `global/CLAUDE.md` to
  `global/rules/docs-layout.md`, which loads only when a file in
  `docs/plans/` is touched.
- The roadmap keeps the only order of work. An action plan only routes a
  report's findings into roadmap rows.
- A Small UI change that adds no screen and no state needs no design canvas.
- The "Invoke first" table names the end-of-branch reviews and merge steps
  it means.

### Fixed

- `my:handoff` loads the deferred `PushNotification` tool before a signal
  calls it, and skips the notification when the tool is absent. The code
  stage's auto sub-steps are lettered a to c, so "step 1" no longer names two
  steps. The README says that its advice of one auto run at a time is
  stricter than the **Max runs** default of 2. Audit R1, R3 and R4.
- `my:handoff auto code` checks that the spec is committed also when its
  `approved` edit was committed before the run started.
- `git-fold-fixups.py check` runs the fold's own rules, so it no longer
  passes a target that the fold then refuses.
- The md-tables docs describe the scripts' current command line in
  `~/src/scripts/`.
- `kit:git-squasher` keeps its rebase script's own first argument. Claude
  Code replaced `"$1"` in the skill text with the skill's second argument, so
  `/kit:git-squasher main --dry-run` gave the script `--dry-run` in place of
  the rebase todo file. The script now writes `"${1}"`, which Claude Code
  leaves alone. Row 41.
- `CLAUDE.md` and `README.md` no longer describe a deny list of unsafe
  commands as active. It sat in a repo-root `settings.json` that Claude Code
  never read, and that file is deleted. No rule that was in force changed.
  Row 1.

### Docs

- A critique of the workflow's efficiency, with its findings as roadmap
  rows: [report](docs/reports/2026-10-09-workflow-efficiency-critique.md).

## 2026-09

### 2026-09-22 — `my:handoff` (Design workflow)

The plan, code and review stages each run in their own top-level session,
opened in a tmux window, so each stage reads the real `CLAUDE.md` rules. See
the [spec](docs/plans/2026-09-21-handoff-spec.md) and the
[plan](docs/plans/2026-09-21-handoff.md).

- `/my:handoff <stage> <doc>` opens the stage in a new window. Each stage
  launches the next.
- The review stage (added 2026-09-29) runs the end-of-branch checks and
  reviews, one fix round, then the squash-merge after the user's yes.
- A finished stage marks its window with `✓`. A stage that waits marks it
  with `⚠`. Stages no longer message other sessions.

### Added

- `my:soundness-review --plan-only` reviews a plan on any working tree, so a
  busy `main` no longer stops the handoff plan stage. See the
  [spec](docs/plans/2026-09-30-soundness-plan-only-spec.md).
- `my:md-tables`, with filters that turn a Markdown table into one section
  per row and back.
- `my:architect` writes an architecture brief from labelled forces before
  brainstorming. The global instructions run it for new systems and contract
  changes. See the [spec](docs/plans/2026-09-17-architect-skill-spec.md).
- `my:spec-review`, a system-thinking review of one spec, required in the
  spec flow. See the [spec](docs/plans/2026-09-16-spec-review-skill-spec.md).
- The `plain` output style, enabled globally: short sentences, terms defined
  at first use, no idioms.
- The `vue-lsp` plugin, so the `LSP` tool also covers `.vue` files.
- `tune-claude-instructions` flags prompts that need a tool a subagent never
  receives.

### Changed

- **BREAKING** The repo is a plugin marketplace, and the plugins live in
  `plugins/`. Install from the marketplace instead of a `--plugin-dir`
  alias. Sessions now run a cached copy of the last commit, and
  `claude plugin update` refreshes it.
- The orphan-plan hook also checks the `docs/plans/` index and
  `docs/reports/`, but only in a project whose README opts in.
- Reports go to `docs/reports/`, and their findings become roadmap rows.
- Reviews run once, at the end of the branch, with one fix round. A failing
  red step counts as the proof that a test can fail.
- Commit messages carry a scope: `type(scope): sentence`.
- UI work must be drawn on a design canvas, not described in prose.
- A session must call the `LSP` tool before it concludes that no language
  server is configured.
- `clean-plans`, `summarizer` and `optimize-prompt` read and write dated
  files in `docs/plans/`.

### Removed

- **BREAKING** `/my:plan`, the `my:planner` agent and `/my:task`.
  Superpowers owns planning. See the
  [spec](docs/plans/2026-09-11-retire-planner-path-spec.md).

### Fixed

- `my:soundness-review`: four defects that lowered review quality, the
  contradictions its critique found, and the argument rules. It now asks
  what to review when a plan meets a dirty working tree, and stops on a
  mistyped range. See the [audit](docs/plans/2026-09-07-soundness-review-audit.md)
  and the [critique](docs/reports/2026-09-19-soundness-review-critique.md).
- Agents search the repo through `Bash`, because subagents never receive
  `Grep`, `Glob` or `LSP`.
- Subagents can start subagents when their agent file lists `Agent`.
