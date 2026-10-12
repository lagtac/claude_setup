# Spec: `my:handoff auto`, one feature from approved spec to `done` without the user

**Status:** draft, 2026-10-12. Written from the brainstorming session that
followed the architecture brief.

## How to read this spec

| Document | Path | Why you would read it |
| --- | --- | --- |
| Architecture brief | `docs/plans/2026-10-11-autonomous-run-architecture.md` | The forces, the three candidates and why candidate A won. This spec settles its "Open for brainstorming" list. Read first. |
| **This spec** | `docs/plans/2026-10-12-autonomous-run-spec.md` | What to build and why. |
| Spec review | `docs/plans/2026-10-12-autonomous-run-spec-review.md` | The `my:spec-review` report on this spec. |
| Implementation plan | `docs/plans/2026-10-12-autonomous-run.md` | Written after this spec is approved. |
| Handoff skill | `plugins/my/skills/handoff/SKILL.md` | The skill this spec changes. Its stop points are the rows of D5. |
| Handoff spec | `docs/plans/2026-09-21-handoff-spec.md` | D1, D2 and D4: why each stage is its own top-level session, and how a stage signals. |
| Handoff README | `plugins/my/skills/handoff/README.md` | How handoff works, for a reader. Gets an auto-mode section. |
| Docs layout rule | `global/rules/docs-layout.md` | "One feature, four commits on `main`", steps 9 to 13: fold, merge and `done` marks. |
| Fold script | `plugins/my/bin/git-fold-fixups.py` | Its exits 1 (refused) and 3 (history rewritten, a check failed) are stops here. |
| Plugin hooks | `plugins/my/hooks/hooks.json` | Gets the push guard of D4. |
| Global instructions | `global/CLAUDE.md` | "Spec → Plan two-artifact flow" step 3, which gets the offer of auto mode. |
| Fold script tests | `plugins/my/tests/test_git_fold_fixups.py` | The model for the new unit tests. |

## Context

`my:handoff` already runs the plan, code and review stages of a feature, each
in its own top-level session in a tmux window. Each stage launches the next.
It stops for the user at fixed points: a design-changing finding, a new
dependency, a failed end-of-branch test, and the squash-merge, which always
waits for the user's yes.

The user wants to approve a spec and walk away. The feature should then reach
`main`, folded and marked `done`, with no further input, unless something
comes up that the user has not decided in advance.

Several of handoff's stop points exist because the global rules give the
decision to the user. Examples are "Never add new dependencies without
approval" and "No silent reinterpretation". So autonomy cannot just remove
the stops. The user decides in advance, in the spec, what the agent may
decide. Every other case still stops.

## Goal

One command, `/my:handoff auto plan <spec>` (Large) or
`/my:handoff auto code <spec>` (Medium), takes an approved spec to one of two
end states, with no input from the user:

1. The feature is squash-merged into `main`, the fixups are folded, and the
   `done` marks cite the squash commit. `origin` is unchanged.
2. The run has stopped, and its tmux window says exactly what it needs from
   the user. A state file records the next step.

## Out of scope

- Two or more features at once. The user chose to get one line of work right
  first. Parallel runs need a queue for the steps on `main`. That is a later
  spec.
- The spec stage. The user still runs `my:architect`, brainstorming and
  `my:spec-review`, and approves the spec.
- The push. It stays with the user.
- A cost or time cap (D9).
- The repo-root `settings.json` deny list, which Claude Code does not read.
  That is a separate bug with its own roadmap row.

## Decisions

These were decided with the user on 2026-10-11 and 2026-10-12.

**D1: Auto mode is a mode of `my:handoff`, started with an explicit word.**
The forms are:

- `/my:handoff auto plan <spec>`: launch the plan stage in auto mode.
- `/my:handoff auto code <spec>`: launch the code stage in auto mode, for a
  Medium spec with a Tasks section.
- `/my:handoff auto resume <spec>`: continue a stopped run whose window is
  gone (D7).
- `/my:handoff run auto <stage> <doc>`: the Run form that Launch types into
  the new window.

Without `auto`, handoff behaves exactly as today, even when the spec has a
Delegation section.

Why a word and not the section alone: approving a spec is not the same
decision as walking away. The user may want to run a spec that has a
Delegation section with supervision. The command typed should say what will
happen.

This changes the architecture brief's Decision, which said the Delegation
section switches the mode on. The user chose the explicit word on
2026-10-12.

Rejected: the Delegation section switches auto mode on (a run's behaviour
would depend on file content the command does not show). Rejected: a new
skill that calls handoff's stages (two skills would describe one cycle, and
the steps on `main` would have two copies that drift; brief force 8).

**D2: The Delegation section.** An auto run needs a section titled
`Delegation` in the spec, with exactly these four keys:

```markdown
## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `python3 -m unittest discover tests`
```

| Key | Allowed values | Meaning |
| --- | --- | --- |
| Dependencies | `none`, or a list of package names with an optional version | The code stage may add exactly these. Any other new dependency stops the run. |
| Design-changing findings | `stop` or `decide` | `decide`: the stage picks the fix it judges best and records it (D5). `stop`: as today. |
| Failing end-of-branch tests | `none`, or a list of test names | These tests may fail without stopping the run. Any other failure stops it. |
| End-of-branch checks | `none`, or a list of commands | The checks to run when the project's rules name none. When the rules name checks, the rules win. `none` makes the `done` mark say `no end-of-branch checks run`. |

The agent compares by exact name. A missing key, an unknown key, or a value
outside these forms fails the start check. Anything the section does not list
stops the run.

Rejected: free prose (the session that wants to go on would interpret it).
Rejected: lists plus a free-text notes line (it would be read as permission
in practice).

**D3: Start checks for auto mode.** On top of today's start checks:

- The spec's status is `approved`, and it has a valid Delegation section (D2).
- `auto plan`: the spec has no Tasks section.
- `auto code`: the spec has a Tasks section. Its `approved` edit may be
  uncommitted; D8 commits it in the stage's first step. Today's code-stage
  check "the task doc is committed on `<base>`" then runs after that step,
  not before it.
- For the command the user types (`auto plan` or `auto code`): no state file
  exists for this slug with `next` other than `finished`. If one does, the
  check fails with `a run for <slug> exists; use resume`.
- For a `run auto <stage>` session, launched by a stage or by `resume`: the
  state file exists, and its `next` equals this stage.

**D4: The push guard is a plugin hook keyed on an environment variable.**
Each Launch in auto mode opens the window as:

```bash
MY_AUTORUN=<slug> claude -n <name> <plugin-dir flags> <mode flag> '/my:handoff run auto <stage> <doc>'
```

A new `PreToolUse` entry for `Bash` in `plugins/my/hooks/hooks.json` runs
`plugins/my/hooks/block-autorun-push.py`. The entry's matcher is
`Bash|Monitor`, because both tools run a shell command from a `command`
field. Claude Code runs a `PreToolUse` hook before every tool call, in every
permission mode. When `MY_AUTORUN` is set, the script splits the command into
subcommands at `&&`, `||`, `;`, `|` and newlines, and splits each one into
words with Python's `shlex`. It blocks when a subcommand's command word is
`git` and its first word after any global options (`-C <dir>`,
`-c <k>=<v>`, `--<option>`) is `push`. Text that only mentions
`git push`, such as a commit message or a heredoc line, is not blocked. To
block, the script prints `Blocked: autonomous runs never push.` to stderr and
exits 2. Without the variable it exits 0 at once.
So the user's own sessions, and `my:push`, work as today.

Why a hook: the Claude Code docs (fetched 2026-10-12) say a plugin's
`settings.json` drops every key except `agent` and `subagentStatusLine`, so a
plugin cannot ship deny rules. A `deny` rule in settings holds in every mode
but misses `git -C <dir> push` and `git -c <k>=<v> push`. A spike on
2026-10-12 confirmed the hook: with the variable set it blocked `git push`,
`git -C <dir> push` and `git -c … push` under an allow rule, under `auto`
and under `bypassPermissions`. Without the variable, the push went through.

Rejected: block while any run is active (it would block the user's own
pushes). Rejected: block always (it would break `my:push`).

**D5: Each stop point has a fixed outcome in auto mode.** "Delegation" means
the stage reads the key named in brackets. It goes on if the case is listed
there, and stops if it is not.

| Stage | Stop point in today's handoff | Auto mode |
| --- | --- | --- |
| any | A start check fails | stop |
| any | Launch cannot open a window (no tmux, or a mode other than `auto` or `bypassPermissions`) | stop |
| any | A shared resource is busy, or another session's edit is in a file the stage commits | stop |
| plan | A finding whose fix changes a decision, or a false premise | Delegation [Design-changing findings] |
| plan | Spec fixups wait: the pre-rebase check fails, or the fold exits 1 or 3 | stop |
| code | A new dependency | Delegation [Dependencies] |
| code | A change outside the project's scope | stop |
| code | A test still fails after `superpowers:systematic-debugging` | stop |
| code | A test assertion was removed or weakened | stop |
| review | An end-of-branch test fails | Delegation [Failing end-of-branch tests] |
| review | The project's rules name no end-of-branch checks | Delegation [End-of-branch checks] |
| review | A finding whose fix changes a decision | Delegation [Design-changing findings] |
| review | A new Critical finding in the re-review | stop |
| review | Ready to squash-merge | go on |
| review | `git merge --squash` conflicts, because `main` moved during the run (new) | run `git reset --merge`, check that `git status --porcelain` prints nothing, then stop with `next=merge`. If the tree is still not clean, the stop line says so. (`git merge --abort` does not work here: a squash merge writes no `MERGE_HEAD`.) |
| review | After the merge, `main` is not clean, so the fold must wait | stop with `next=fold` |
| review | The fold exits 1 or 3 | stop with `next=fold`. Exit 3 also records the HEAD from before the fold. |

A **stop** is today's signal: the `⚠` mark, a `PushNotification`, and the
line as the last output. Before signalling, the stage writes the state file
(D6) with the stop reason. When the user answers in that window, the stage
goes on in auto mode.

With `decide`, the stage writes one line per choice into the task doc's
**Risk** section: the finding, the choice and the reason. The task doc is the
plan (Large) or the spec (Medium). With a listed failing test, the `done`
mark names the test.

**D6: The run's state lives in one untracked file, written by a helper
script.** The file is `<git common dir>/my-handoff/<slug>.json`, where the
git common directory is `git rev-parse --path-format=absolute
--git-common-dir`. It is outside the work tree, so `git status` never shows
it, and it never blocks a fold.

Fields:

| Field | Value |
| --- | --- |
| `spec` | The spec path. |
| `task_doc` | The plan path, or the spec path for Medium. |
| `branch`, `worktree` | Set by the code stage. |
| `next` | One of `plan`, `code`, `review`, `merge`, `worktree-remove`, `fold`, `done`, `finished`. |
| `squash_subject` | The squash commit's subject, set **before** the merge. The `done` marks find the commit by this subject after the fold, because the fold changes its hash. |
| `head_before_fold` | Set just before the fold. |
| `stopped` | The stop reason, or empty. |

`plugins/my/bin/handoff-state.py` is a Python standard-library script with
three commands:

- `set <slug> <field>=<value> …`: updates the file through a temporary file
  and a rename, so a crash never leaves half a file.
- `get <slug>`: prints the file.
- `check <slug>`: compares the file with git, and prints each mismatch on
  its own line. It exits 0 when everything matches, and 1 otherwise. For
  each `next` it checks the facts that step needs. For `merge`: the branch
  exists. If a commit on `main` already has `squash_subject`, the merge
  happened before a crash: `check` prints `merge done` and sets `next` to
  `worktree-remove`, so the merge never runs twice. For `worktree-remove`:
  that commit is on `main`. For `fold`: the worktree is gone. For `done`: no
  `fixup!` commit for the spec or task doc waits on `main`. For every value:
  no rebase, merge or cherry-pick is in progress.

The first auto stage creates the file after its start checks pass, with
`next` set to its own stage. Each stage runs `set` when it launches the next
stage, before and after every step that changes `main`, and when it stops.

**D7: `resume` continues a run whose window is gone.** After a crash, a
reboot or a closed window, `/my:handoff auto resume <spec>` runs
`handoff-state.py check <slug>`.

- If `check` exits 1, it signals `<name>: resume refused: <first mismatch>`
  and stops. It never guesses.
- Otherwise it never does the work in the user's own session, which has no
  `MY_AUTORUN`. It launches a new window, with `MY_AUTORUN` set, running
  `/my:handoff run auto <next> <doc>`. For `merge` and later steps, that
  session runs the remaining steps of Review stage step 8, in order.
- A restarted stage skips the start checks that expect a fresh start: no plan
  yet, no branch yet, no worktree yet. `check` has already verified the
  state. If the crashed session left uncommitted files (in the main checkout
  for `plan`, in the worktree for `code` and `review`), the stage stops with
  `uncommitted files from the earlier session: <paths>`. The user decides
  whether to keep them.
- Where each stage restarts:
  - `plan`: if the plan is already committed on `<base>`, set `next=code`
    and launch the code stage. Otherwise start the plan stage again.
  - `code`: continue at the first task of the task doc that has no commit on
    the branch.
  - `review`: start the reviews again. If the branch already has commits
    from the fix round, stop instead: a second fix round would break the
    one-fix-round rule.

**D8: Medium changes are covered.** The code stage in auto mode gets a new
first step, after the start checks, when the spec's `approved` edit is
uncommitted:

1. Run `git-fold-fixups.py check <spec commit>`. If it exits 1, commit the
   edit as a normal `docs:` commit (docs-layout step 4). Otherwise commit it
   with `git commit --fixup <spec commit>`.
2. If `<base>` is clean, run the fold under the Plan stage step 8 rules: a
   failed pre-rebase check, or a fold exit of 1 or 3, is a stop. If `<base>`
   is not clean, skip the fold. The review stage folds waiting spec fixups
   after the merge (Review stage step 8).

This mirrors the plan stage, which already commits the `approved` edit for a
Large change.

**D9: No cost or time cap.** Interactive Claude Code has no per-session token
limit. A cap enforced by the model counting its own work is weak. The
existing stops bound the longest loops: debugging that fails stops the run,
and each review gets one fix round. The cost is recorded in Risk.

**D10: The global flow offers auto mode.** In `global/CLAUDE.md`, "Spec → Plan
two-artifact flow" step 3, when the approved spec has a Delegation section,
the question becomes "Hand off the plan, supervised or auto?". The answer
runs `/my:handoff plan <spec>` or `/my:handoff auto plan <spec>`. The same
applies to the Medium paragraph's `/my:handoff code`.

## Files

| File | Change |
| --- | --- |
| `plugins/my/skills/handoff/SKILL.md` | The `auto` forms and usage line (D1), the Delegation format (D2), the auto start checks (D3), the env var in Launch (D4), the stop table (D5), the state writes (D6), `resume` (D7), and review step 7 going on without a yes. |
| `plugins/my/skills/handoff/README.md` | An "Auto mode" section for a reader. |
| `plugins/my/hooks/hooks.json` | A `PreToolUse` entry, matcher `Bash\|Monitor`, that runs the guard. |
| `plugins/my/hooks/block-autorun-push.py` | New: the push guard (D4). |
| `plugins/my/bin/handoff-state.py` | New: the state helper (D6). |
| `plugins/my/tests/test_block_autorun_push.py` | New: unit tests for the guard. |
| `plugins/my/tests/test_handoff_state.py` | New: unit tests for the helper. |
| `global/CLAUDE.md` | D10. |
| `README.md` | A line on auto mode under `my:handoff`, and on the new script in `plugins/my/bin/`. |
| `ROADMAP.md` | A row for this feature, and a row for the settings bug. |

## Trade-offs

- **Mode of handoff versus a new skill.** A mode keeps one copy of the stage
  steps. Its cost is a longer `SKILL.md`, about 380 lines today, which every
  stage session reads, auto or not.
- **Hook versus deny rule.** The hook catches `git -C` and `git -c`, and it
  ships with the plugin to every project. It does not see a push from inside
  a script that the agent writes and then runs. A git `pre-push` hook would
  see that too, but each project would need it installed, and zitamu already
  has its own. Not built now (Risk).
- **Helper script versus prompt-written JSON.** The script adds a file and
  tests. In return, the atomic write and the git checks for `resume` are
  tested code, not prose that each stage must get right.
- **`decide` exists at all.** It lets a run go past design findings, which is
  the most common stop in practice. Each choice is recorded in Risk, where
  the user reads it before pushing.

## Dependencies

None. Python 3 standard library, tmux and Claude Code, as handoff uses today.

## Risk

- **Hard to reverse: the Delegation format.** Every spec that uses auto mode
  carries the four keys. A later change to the keys means editing those
  specs, or keeping the old keys valid.
- **Unattended changes to `main`.** The squash-merge and the fold rewrite
  local `main` with nobody watching. Recovery is through the reflog and
  `head_before_fold` in the state file. Nothing is pushed, so `origin` is
  never affected. Detection: the finish line names the squash commit; the
  user reads `main` before pushing.
- **The push guard has a known gap.** A push from inside a script the agent
  writes is not seen. Command forms the word splitting does not expect, such
  as `bash -c "git push"` or a command built from variables, may slip
  through.
  Detection: none inside the run. The user's `git log origin/main` after a
  run would show it.
- **The agent judges its own Delegation.** The session that wants to go on
  is the one that decides whether a case is listed. The closed lists and the
  exact-name comparison narrow this, but do not remove it.
- **Cost.** Assumed, never confirmed: about 3 stage sessions per feature at
  1.5M to 8M tokens each, with no cap (D9). A run that loops inside one
  stage costs until a stop ends it.
- **Blast radius.** `my:handoff` is called from `global/CLAUDE.md` (step 3
  of the Spec → Plan flow and the Medium paragraph) and from its own
  stages. Plain handoff must behave exactly as today; the tests in Testing
  check this.
- **Manual steps.** None for the user. The plan must rehearse the full cycle
  (Testing) before the feature is marked `done`.

## Testing

- **Guard unit tests** (`test_block_autorun_push.py`). Feed the script the
  hook's JSON on stdin. With `MY_AUTORUN` set, these exit 2: `git push`,
  `git push origin main`, `git -C /x push`, `git -c a=b push`,
  `cd /x && git push`, `git --no-pager push`, and a `Monitor` call whose
  command is `git push`. These exit 0: `git stash push`, `echo push`,
  `git status`, `git commit -m "never git push"`, and a heredoc whose body
  says `git push`. Every command exits 0 when the variable is not set.
- **Helper unit tests** (`test_handoff_state.py`). In a temporary fixture
  repo: `set` then `get` round-trips the fields; `check` exits 0 for a
  matching state and 1 with the mismatch printed for each `next` value in
  D6; `check` exits 1 while a rebase is in progress.
- **Rehearsal of the full cycle.** In a separate tmux server, run against a
  fixture repo whose `origin` is a local bare repo. The fixture has a tiny
  Medium spec with a Delegation section:
  - Plain `/my:handoff code <spec>`, without `auto`, must still stop at
    "ready to squash-merge", and its windows must not carry `MY_AUTORUN`.
    Answer no, and reset the fixture.
  - `/my:handoff auto code <spec>` must end with the `done` marks on `main`,
    the `✓` mark, and the bare repo unchanged.
  - A second spec whose task adds a dependency that is not listed must stop
    at the code stage, with `next=code` and a stop reason in the state file.
  - Close the window of a third run while it is stopped at the fold, then
    `/my:handoff auto resume <spec>` must finish it.

## Open questions

None.
