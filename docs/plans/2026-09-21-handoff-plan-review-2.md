# Review: docs/plans/2026-09-21-handoff.md

**Status:** review of docs/plans/2026-09-21-handoff.md, 2026-09-21. Mixed:
six of the first review's eight findings are fully answered, but the new
refused-mode command cannot run as written, because `--allowedTools` takes a
list and swallows the prompt as a tool name.

## Change Summary

The plan builds `my:handoff`, one `SKILL.md` with a launch form and a run form
for the plan and code stages (spec D5 to D10), plus three doc edits (README,
ROADMAP, GLOBAL-CLAUDE.md step 3). This revision adds a `th` helper that runs
every tmux-touching test in a separate `handofftest` server. It also adds an
allowed-Bash refused-mode test, a worktree plugin-path assertion, a fixture
reset to a recorded init commit, an anchored plan glob and a narrower lint
grep. The skill-selection check moves into Task 2, before the commit.

## Grounding

All searches were text-only (`grep`, `ls`, `ps`, `env`, a Python read of
`~/.claude.json`). No symbol tool was available. The plan removes or renames
nothing, so there is no caller sweep to run.

Claims that hold:

- README anchor: the `my:soundness-review` bullet ends "goes to the built-in
  `/code-review`." (`README.md:35`). ROADMAP anchor: the `my:architect` row
  (`ROADMAP.md:54`). Old step 3 text (`GLOBAL-CLAUDE.md:46`) matches Task 3
  step 4 exactly.
- `.claude/` is ignored (`.gitignore:2`), so the fixture stays out of the repo.
- tmux is 3.4. `claude --help` lists `-n, --name`, `--permission-mode` and
  `--plugin-dir`.
- `ps -o args= -p "$CLAUDE_PID"` prints
  `claude --plugin-dir /home/dchris/projects/claude-setup/my-plugin`, and a
  session's Bash has `TMUX` and `TMUX_PANE` set. The `th` design, which runs
  each test in a pane of the separate server, answers this correctly.
- Task 2 step 6 greps `"skill":"my:[a-z-]*"`. Real transcripts record a Skill
  call as `"name":"Skill","input":{"skill":"my:spec-review",...}`, so the
  pattern matches the real output.
- The SKILL snippet matches spec D7 to D10 (spec lines 163-276), including the
  anchored plan glob for D8's "same slug".

False or unverified assumptions:

- Task 2 step 4 (plan line 424) passes
  `--allowedTools Bash '/my:handoff plan …'`. `claude --help` shows
  `--allowedTools, --allowed-tools <tools...>`, which takes a list. I ran
  `claude -p --permission-mode acceptEdits --allowedTools Bash '<prompt>'` and
  got `Error: Input must be provided either through stdin or as a prompt
  argument when using --print`. With `--allowedTools Bash` placed before
  `--permission-mode`, the same run answered normally.
- Task 2 step 5 cleanup (plan lines 473-477) runs `git worktree prune` before
  `rm -rf .claude`. I rebuilt this in a scratch repo. After a worktree at
  `.claude/worktrees/widget`, the plan's exact sequence left the worktree
  listed as `prunable`. `git branch --list` printed `+ feat/widget`, so the
  `grep -v` filter passed `+` to `xargs`, which gave `error: branch '+' not
  found`. Git then refused `cannot delete branch 'feat/widget' used by
  worktree`.
- Plan lines 80-82: the fixture "is inside the trusted `claude-setup` folder,
  so an interactive session started there shows no trust dialog." Only
  `/home/dchris/projects/claude-setup` is marked trusted in `~/.claude.json`.
  The plan gives no probe date for this claim, while it dates its other
  probes. See Needs Investigation.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
| --- | --- | --- | --- |
| Warning / High | The refused-mode test (Task 2 step 4) cannot run. `--allowedTools <tools...>` takes a list, so it eats the prompt `'/my:handoff plan …'` as a second tool name. `claude -p` then exits with "Input must be provided" before the skill loads. The `grep -F "claude -n plan-widget"` finds nothing, and the executor has to debug the harness. | Plan line 424; `claude --help` line 22; the scratch run described under Grounding | Put the list option before another option: `claude -p --plugin-dir $WT/my-plugin --allowedTools Bash --permission-mode acceptEdits '/my:handoff plan …'`. I checked that this order works. |
| Warning / Medium | The fixture cleanup after Task 2 step 5 cannot remove a worktree that the launched session made. `git worktree prune` runs before `rm -rf .claude`, so it prunes nothing. The branch filter does not strip the `+` that marks a branch checked out in a worktree. Git also refuses to delete a branch that a registered worktree still uses. The expected "one worktree, branches `feat/sprocket` and `main` only" then fails. It only matters if `plan-widget` got as far as creating a worktree before `kill-server`, so the trigger is uncertain. The mechanism itself is verified. | Plan lines 473-477; Risk bullet plan lines 656-658; the scratch repo run described under Grounding | Run `rm -rf .claude` first, then `git worktree prune`. Strip both markers in the filter: `git branch --format='%(refname:short)' \| grep -v -x -E 'main\|feat/sprocket' \| xargs -r git branch -D`. |
| Suggestion / High | The shell does not persist between the executor's Bash calls, but the plan defines `WT`, `FIX`, `SCRATCH` and the `th` function once, in "How tests run". Task 1 step 1 already uses `$SCRATCH` without defining it. Task 2 step 3 runs three headless sessions one after another in one call, which can pass the Bash tool's default 120-second timeout. | Plan lines 51-73, 146-158, 372-382 | Write the variables and `th` to `$SCRATCH/handoff-env.sh`. Start each test block with `source` of that file. Run step 3 with the tool's longest timeout, or run one `th` per call. |
| Suggestion / High | The wait loop in Task 2 step 5 has no expected exit status. If the launched session never shows its prompt (a trust dialog, or a crash that `remain-on-exit` keeps on screen), `timeout` ends with 124. The next `grep -ci 'unknown'` then prints `0`, which is the pass value. | Plan lines 450-454 | Add "Expected: the loop exits 0" (for example `…; echo "wait=$?"`, expecting `wait=0`) before the `unknown` count. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Test isolation is now structural. Every tmux-touching run goes through `th` in `-L handofftest`, or runs with `TMUX` unset. The mark is asserted in the test server's window list. | Plan lines 64-73, 374-396, 490 | Strong |
| The launch test checks the worktree plugin path in `#{pane_start_command}`, which closes the wrong-plugin gap | Plan lines 437-444 | Strong |
| The spec is covered, and the SKILL snippet follows D7 to D10 step by step | Plan lines 251-360; spec lines 163-276 | Strong |
| The repo anchors, the Skill-call format and the tool versions match the real repo and transcripts | `README.md:35`, `ROADMAP.md:54`, `GLOBAL-CLAUDE.md:46` | Strong |
| Skill selection now runs before the Task 2 commit and the reviews, and it asserts a clean fixture | Plan lines 483-499 | Moderate |
| Easy to reverse: one new directory and three doc edits | Plan lines 97-102, 665 | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| The refused-mode command fails before the skill runs | Plan line 424 | Medium |
| The fixture reset promises more than its commands deliver | Plan lines 473-477 | Low |
| The harness assumes a shell that persists between calls | Plan lines 51-73 | Low |
| The plan and code stages are not exercised before merge. The plan leaves this to a pilot. | Plan lines 662-664 | Low |

## Not Applicable

- Risk & reversibility, schema and data side: the change adds prompt text and
  doc lines only, with no schema, API or data migration. The dimension was
  applied to the test side effects (the cleanup finding).

## Needs Investigation

- **Trust dialog in the nested fixture repo.** This is carried over from the
  first review, and the plan asserts it without a probe. If Claude Code does
  not extend the parent's trust to `$FIX`, the `plan-widget` window stops at
  the dialog. The duplicate check would still pass, and the "knows the skill"
  check passes vacuously unless the second Suggestion is applied. To resolve:
  one `claude -n x` probe in a nested repo under `claude-setup`.
- **`ListAgents` from a headless session, and auto mode allowing
  `tmux new-window "claude … --permission-mode auto …"`.** This is carried over
  from the first review, and the plan does not address it. The dated probes
  show only that `ListAgents` lists a named session. If either call is blocked,
  Task 2 steps 5 and 6 fail loudly, not vacuously. So this costs time, not
  correctness. To resolve: run both calls once in a headless auto session at
  the start of Task 2.

## Reasoning

The first review's findings are answered as follows:

- Six are fully answered:
  - the start checks run in `handofftest` and the mark is asserted there;
  - skill selection runs with `TMUX` unset;
  - the launch asserts the `$WT/my-plugin` path, and the capture-pane check
    was added;
  - the anchored glob;
  - the `' error MD'` lint filter;
  - skill selection moved into Task 2 before the commit.
- Two are only partly answered:
  - The refused-mode test has the right idea (let Bash through and require
    the fallback grep), but `--allowedTools` swallows the prompt.
  - The fixture cleanup now records the init commit and kills the server
    first, but it runs `prune` too early and does not handle the `+` branch
    marker.

Both remaining problems are local command fixes that change no spec decision.
The approach is right, so the verdict is Mixed, not Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** High — both Warnings were reproduced here, one with a real
`claude -p` run and one with a scratch git repo.
**Recommendation:** Move `--allowedTools Bash` before `--permission-mode` in
Task 2 step 4. Reorder the cleanup to `rm -rf .claude` then
`git worktree prune`, with a `--format` branch list. Optionally apply the two
Suggestions. This is the final re-review, so these can be fixed in the plan
without another review round.
