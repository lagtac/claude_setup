# Critique: the "Parallel runs" section

**Status:** current, 2026-10-15. Five findings (P1 to P5) on how a project opts in to parallel auto runs; not yet routed to roadmap rows.

## How to read this report

| Document | Path | Why |
| --- | --- | --- |
| Architecture brief | `docs/plans/2026-10-12-parallel-auto-runs-architecture.md` | Forces, candidates, and why Candidate A (a lock per command, no fold) won. |
| Spec | `docs/plans/2026-10-12-parallel-auto-runs-spec.md` | D1 defines the section. D5 turns off fixups for all work. Risk lists the accepted limits. |
| Handoff skill | `plugins/my/skills/handoff/SKILL.md` | "Parallel runs", and the nine "With a 'Parallel runs' section" paragraphs. |
| Lock scripts | `plugins/my/bin/handoff-lock.py`, `plugins/my/bin/locked-commit.py` | The lock and the locked commit. |
| zitamu | `~/projects/zitamu/real-estate-webapp/CLAUDE.local.md` | First real section, added 2026-10-15 for rows 76 and 77. The file is gitignored. |
| diagoradisa-annotator | `~/projects/diagoradisa/diagoradisa-annotator/CLAUDE.md`, `.claude/settings.json`, `scripts/worktree-provision.sh`, `scripts/e2e-gate.sh` | Second real section, with two shared resources and four commit-gate hooks. |
| Scriptable steps report | `docs/reports/2026-10-14-scriptable-skill-steps.md` | S4 asked for a parser of the section (row 42). |

## Verdict

The mechanism is sound. The way a project opts in is the weak part.

Locks that live for one command, no fold, and a compare-and-swap merge were the right choice over a daemon or an integrator session. The brief argues this well, and nothing found here reopens it.

The weak part is the section itself. It asks the model to carry its values by hand into every command and every subagent prompt. Its locks only bind sessions that remember to take them. Seven files read it as prose, and nothing checks it. Both real sections already show gaps: a lock that is released while its resource is still in use, and commit gates that stop running.

## What is sound

- **One command per lock.** The kernel frees the lock when the command dies, so a crash never leaves a lock held. No lease, no daemon.
- **No fold in a parallel project.** Cited hashes never change. The spec weighed "fold at once or fall back" and rejected it for a stated reason.
- **The merge as one script** (`handoff-state.py merge`), with `checked_base`. This rule lives in code and has tests, not in prose.
- **Opt-in at all.** A second auto run refuses to start without the section. That is a safe default.

## Findings

Each finding says whether it is new, an accepted limit, or already a roadmap row.

### P1. Isolation is applied by the model to each command (new, High)

**Evidence.** `SKILL.md` lines 819–825, 902–906 and 942–947. The stage must add the filled-in **Isolation** values to "every test and server command". It must also copy them into every subagent prompt it writes. If one command forgets, nothing fails at once. Two runs then share a port or a stack, and the symptom appears later in the other run. Row 56 is this kind of collision: two zitamu previews both took port 54321.

**Better.** Apply Isolation once, at launch, as process environment. Launch already does this for `MY_AUTORUN`: the tmux command is `MY_AUTORUN=<slug> claude …`. Start check 1 (`printenv MY_AUTORUN`) proves that the stage's shell inherits it. Launch can fill in `<slug>` and `<slot>`, work out `$((54320 + <slot>))`, and put `PORT=54321` in front of `claude` in the same way. Then every Bash command in the stage gets it. Subagents run in the same process, so they should get it too, but this has not been tested.

That removes the per-command rule and the two prompt lines. A supervised launch needs a slot of its own for this to fix row 56. Today a supervised run always uses slot `1`.

**Against.** The env is set when the session starts. A stage cannot change the values partway through. No current section needs that.

### P2. Shared-resource locks bind only the sessions that take them (new, High)

**Evidence.** A **Shared resources** command runs as `handoff-lock.py <name> -- <command>`. The lock is taken by the caller, not by the resource. Two consequences:

- **The user's own runs bypass it.** diagoradisa's `e2e-gate.sh` refuses when the e2e stack already exists, and tells the user to run gates one at a time under `handoff-lock.py e2e`. If the user runs it in a terminal while an auto run holds the lock, one of the two fails. In an auto run, a failed check is a stop.
- **diagoradisa's `serve` lock protects nothing.** `worktree-provision.sh --serve` runs `docker compose down` on main's stack, then `docker compose up -d` for the worktree, then exits. The lock is freed when the script exits, while the switched stack stays in place. A second run can then take `serve` and switch again. `SKILL.md` line 184 forbids exactly this ("A locked command must not start a process that outlives it"), but nothing checks the project's list against that rule.

**Better.** Let the project's script take the lock itself, and stop wrapping it in the skill. `handoff-lock.py` uses `fcntl.flock` on `<git common dir>/my-handoff/locks/<name>.lock`. Python's `fcntl.flock` and util-linux `flock(1)` (installed here at `/usr/bin/flock`) both use the same `flock(2)` system call, so a shell script can share the lock. `flock -w 3600 -E 75` waits up to an hour and exits with 75 on a timeout, the code row 18 already reads. Then manual runs, supervised runs and auto runs all wait for the same lock. The **Shared resources** key would only name the resources for the reader.

Both halves must change together. A `flock(2)` lock belongs to an open file, not to a process. `handoff-lock.py` holds its open file and then runs the command. If that command opens the lock file again and calls `flock`, it waits on its own parent's lock until the timeout. So a script that locks itself must not also run under `handoff-lock.py <name>`.

Take `serve` off diagoradisa's list. A resource that stays in use after its command ends cannot be held by a per-command lock (D2 rejected leases for that reason). It is a gate, as "Rules for every stage" already says for any other busy resource.

**Against.** The project script now knows the plugin's lock path. That path is fixed by D2, which already counts it as hard to reverse. macOS has no `flock(1)`. The user works on Linux.

### P3. The section turns off Claude Code commit gates (new as a design point, Medium)

**Evidence.** diagoradisa's four commit gates are `PreToolUse` hooks in `.claude/settings.json`. Each one starts with `grep -q "git commit" || exit 0`. A `locked-commit.py -F …` or `handoff-state.py merge …` command does not contain that text, so all four gates skip. Two of them guard the squash-merge itself: `require-impl-review.sh` and `require-seam-e2e.sh`. The project lists this as a known limit and says "Check the gates by hand". In an auto run, "by hand" means the model reads that line and remembers it.

Matching the new command names would not be enough. Both scripts stage inside the lock, so a `PreToolUse` hook that reads the staged diff sees nothing yet.

**Better.** Move the cheap gates into git's own `pre-commit` hook: the impl-review file is present, the seam stamp is fresh, the plans index is regenerated. `locked-commit.py` and `handoff-state.py merge` both run `git commit` without `--no-verify`, so git hooks still run inside the lock, for the squash too. Keep the slow gate, `review-gate.sh --code` (the frontend tests), as a step before the locked command, outside the lock. Say this in the `my:handoff` "Parallel runs" text, so that the next project learns it before it adds the section.

**Against.** Anything in a git hook runs inside lock `main`. Other runs wait for that lock for 90 s by default. A hook that takes a minute makes their commits time out (row 18), and can push the locked command past the Bash tool's 120 s limit. The branch review raised the second point (`2026-10-12-feat-parallel-auto-runs-review.md`). That is why the tests must stay out of the hook.

### P4. Seven readers, no parser, no checks (row 42, extended; Medium)

**Evidence.** Seven files decide on their own whether the section exists and what it says: `my:handoff`, `my:status`, `my:architect`, `kit:setup`, `kit:commit`, `docs-layout.md` and `my.md`. Each one repeats "a heading titled `Parallel runs`, at any level, in `CLAUDE.md` or `CLAUDE.local.md`". The brief rejected Candidate B because its rules would "live twice". This rule lives seven times.

Nothing validates the section, unlike Delegation, which refuses a missing or unknown key. Nothing refuses a typo such as `- **Max run:** 3`. What the model then does with it is unknown, and the most likely result is the default `2`. An empty heading gives two runs that share every port and stack. The scripts never learn whether the mode is on. The model turns prose into `--max <n>` and decides whether to pass `--docs-paths` ("only when the list differs from the default").

**Docs paths** is not a parallel setting. The fold uses it in every project. A project without the section has no way to set it, and a manual fold always uses the default. The spec's Risk names that case.

**Better.** Row 42 proposes a `handoff-state.py` subcommand that prints the values for the model. Go one step further: let the scripts read the values themselves. `handoff-state.py start` takes the cap from the section, and `merge` and `git-fold-fixups.py` take the docs paths from it. Then the model passes no flags, and a manual fold gets the right list. The parser refuses an unknown key and a value outside its form, as the Delegation check does, and that ends the start. It also requires **Isolation** to be stated, with no default, so that "two runs share everything" is a choice someone wrote down.

**Against.** Parsing Markdown from `CLAUDE.md` in a script is fragile. A JSON file (for example `.claude/parallel-runs.json`) would be easier to parse, but the model would no longer see the values in its context. The `## Project facts` block already sets the pattern of keys in Markdown. A strict parser for one fixed form is enough.

### P5. A permanent switch for all work, in a file git may not track (D5 cost and new; Low)

**Evidence.** Spec D5 extends "no fixups" to the user's own sessions, on purpose. The cost is larger than the spec's "5 to 7 commits per feature" suggests. Once the heading exists, the four-commit history ends for all work in that project. That includes weeks with no auto run live. zitamu added the section for two rows (76 and 77).

zitamu keeps its section in `CLAUDE.local.md`, which its `.gitignore` excludes (line 89). diagoradisa keeps its section in the tracked `CLAUDE.md`. The switch changes committed history: no fixups, and every commit goes through a lock. Yet in zitamu, nothing in git records why fixups stopped on 2026-10-15.

**Better.** Keep D5. Name the cost where the switch is made. Row 39 (`kit:setup` offers the section) should say "this ends fixups and folds for all work in this project" before it asks. Put the heading, **Max runs** and **Docs paths** in the tracked `CLAUDE.md`. These are the workflow switch. Put **Isolation** values, which hold ports for this machine, in `CLAUDE.local.md`. The parser from P4 reads both files.

**Against.** Two files for one section is harder to read. The user works alone on one machine, so the gitignored switch has no practical cost yet.

## Accepted limits, not repeated as findings

- **Two writers of one shared doc can still mix** (spec Risk). The clean check, the edit and the locked commit are separate tool calls, and `locked-commit.py` stages whole files.
- **Locks are advisory**, and plain terminal commits take no lock (spec Risk).
- **A stopped run holds a slot** until it is resumed or ended (spec Risk).
- **The skill text spreads** across nine "With a 'Parallel runs' section" paragraphs (rows 30 and 31, audit P1).
- **Supervised runs share slot 1** (row 56). P1 depends on its fix.
- **The rehearsal was never run** (spec Testing, Task 10, by the user's choice). zitamu's adoption on 2026-10-15 is the first real use, and row 56 came from it.

## Order of fixes

1. P2 first: diagoradisa's `serve` lock is wrong today. The fix is one `flock` line per resource script, plus dropping the `handoff-lock.py` wrapper for those commands in the skill, in the same change.
2. P1 together with row 56: both change how Launch fills in the slot.
3. P3: move diagoradisa's squash gates into its git `pre-commit` hook, and add one paragraph to the skill.
4. P4 as an extended row 42.
5. P5 as wording in row 39 and a split of zitamu's section.
