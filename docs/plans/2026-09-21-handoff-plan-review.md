# Review: docs/plans/2026-09-21-handoff.md

**Status:** review of docs/plans/2026-09-21-handoff.md, 2026-09-21. Mixed:
the plan covers the spec and its repo claims hold, but several test runs reach
the user's own tmux server, which the plan's Global Constraints forbid. The
main cause is a false premise: "headless runs have no `$TMUX_PANE`".

## Change Summary

The plan builds `my:handoff`, a single `SKILL.md` with a launch form and a run
form for the plan and code stages (spec D5 to D10). It also adds three doc
lines (README, ROADMAP, GLOBAL-CLAUDE.md step 3). Tests are headless
`claude -p --plugin-dir` runs against a throwaway fixture repo, plus launch
tests in a separate tmux server (`-L handofftest`). It ends with the reviews
and a squash-merge.

## Grounding

All searches were text-only (`grep`, `sed`, `ls`, `env`). No symbol tool was
available. Nothing is removed or renamed, so there is no caller sweep to run.

Claims that hold:

- `$CLAUDE_PID` is set in a session's Bash, and `ps -o args= -p "$CLAUDE_PID"`
  prints `claude --plugin-dir /home/dchris/projects/claude-setup/my-plugin`.
  This backs SKILL "Launch" step 3 (plan lines 236-238).
- `.claude/` is ignored (`.gitignore`), so the fixture under
  `$WT/.claude/handoff-fixture` stays out of the repo (plan lines 59-60).
- The README anchor exists: the `my:soundness-review` bullet ends with "goes to
  the built-in `/code-review`." (`README.md:33-35`).
- The ROADMAP anchor exists: the `my:architect` row is under "Design workflow"
  (`ROADMAP.md:52-59`).
- The old step 3 text in Task 3 step 4 matches `GLOBAL-CLAUDE.md:46` exactly,
  and `~/.claude/CLAUDE.md` is a symlink to `GLOBAL-CLAUDE.md`, so the
  post-merge check in Task 4 step 5 is valid.
- tmux is 3.4 and `claude` is 2.1.278 (plan Dependencies).
- `my:soundness-review main..feat/handoff <spec>` (Task 4 step 1) resolves to
  "diff-review with alignment". The `-spec.md` stop row matches only an empty
  payload (`my-plugin/skills/soundness-review/SKILL.md:106-110`).

False or unverified assumptions:

- Plan line 346: "Headless runs have no `$TMUX_PANE`, so the mark is skipped."
  **False.** `TMUX` and `TMUX_PANE` are both set in this session's Bash
  environment. A `claude -p` started from the executing session's Bash
  inherits them. See the first finding.
- Plan lines 60-61: the fixture "is inside the trusted `claude-setup` folder,
  so an interactive session started there shows no trust dialog."
  `~/.claude.json` marks `/home/dchris/projects/claude-setup` as trusted, but I
  could not check whether trust is inherited by a subdirectory that is its own
  git repo. See Needs Investigation.
- Task 2 step 2 and Task 3 step 5 expect "no output" from
  `markdownlint-cli2 … 2>&1 | grep error | grep -v …`. `markdownlint-cli2`
  v0.20.0 always prints a `Summary: N error(s)` line, and a clean file prints
  `Summary: 0 error(s)`, which still matches `grep error`. I ran it on a scratch
  file to confirm. So the expected output can never occur.
- Task 3 step 3 adds a `✅` ROADMAP row, and Task 4 step 4 never adds a
  shipped commit to it. This is not a finding: of the done rows, only
  `my:architect` cites one (`ROADMAP.md:54-59`), so there is no set pattern.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
| --- | --- | --- | --- |
| Warning / High | Task 2 step 3 runs three failing start checks as headless `claude -p` from the executing session, and that session is inside the user's tmux. Each run inherits `$TMUX_PANE`, so the skill's "Signal" step 1 runs `tmux rename-window -t "$TMUX_PANE" "<name> ⚠"` and renames the executor's own window in the user's server. This breaks the Global Constraint "Never touch the user's tmux server in a test". It also leaves a false `⚠` mark behind. | Plan line 346 (false premise). The plan contradicts itself here: Task 2 step 4 (plan line 381) already runs `env -u TMUX -u TMUX_PANE`, so the author knew a headless child inherits both. Also plan lines 34-35 (constraint), SKILL snippet plan lines 216-218, and `env` in a session Bash, which shows `TMUX` and `TMUX_PANE` set | Run the start-check tests inside `tmux -L handofftest` (a `new-window` plus `wait-for`, as in Task 2 steps 4 and 5). Then assert the mark: `tmux -L handofftest list-windows -a -F '#{window_name}' \| grep -F 'plan-gadget ⚠'`. Adding `env -u TMUX -u TMUX_PANE` alone would close the leak, but then no test runs the mark at all. Spec D4 calls the mark "the main signal", and the plan already says the notification cannot be asserted, so neither signal channel would be tested. |
| Warning / High | Task 4 step 2 (skill selection) runs `claude -p --permission-mode auto` with the executor's `$TMUX` still set. If the skill works, it takes the launch form. "Launch" does no start checks, so it runs `tmux new-window` in the **user's** server. That starts an auto-mode `plan-gadget` session there, which then fails its start check on `draft` and marks its window. | Plan lines 556-561; the SKILL "Launch" steps (plan lines 230-266) have no status check; plan lines 34-35 | Run it with `env -u TMUX -u TMUX_PANE`, so a correct skill prints the fallback command and opens nothing. Alternatively, run it inside `tmux -L handofftest` and kill that server afterwards. |
| Warning / High | The refused-mode test in Task 2 step 4 proves nothing. It passes "when no `plan-widget` window exists" even if the run blocked. In a headless `acceptEdits` run, a Bash call that is not auto-approved is denied anyway. So no window opens whether or not the skill applies the mode rule, and the rule "only `auto` or `bypassPermissions` opens a window" is never shown to fail for the right reason. | Plan lines 402-405; Risk bullet plan lines 616-617 | Let Bash through so that only the skill can refuse, for example `--permission-mode acceptEdits --allowedTools Bash`. Then require the `grep` for the fallback command to match. Drop the "passes if blocked" escape. |
| Warning / Medium | Task 2 step 5 only checks that the start command contains `--plugin-dir`, not that it contains the worktree path `$WT/my-plugin`. The handofftest server copies the executor's environment when it starts, and that includes the executor's `CLAUDE_PID`. If the nested `claude -p` does not replace `CLAUDE_PID`, `ps` reads the executor's command line. The launch then passes the main checkout's plugin, which has no `my:handoff`. The `ListAgents` row still shows `plan-widget`, so the test passes while the launched session answers "unknown skill" (the spec's own Risk bullet on `ps` output). | Plan lines 417-423; `ps -o args= -p "$CLAUDE_PID"` in this session prints the main-checkout plugin path | Assert `--plugin-dir $WT/my-plugin` in `#{pane_start_command}`. Run `tmux -L handofftest capture-pane -p -t plan-widget` and check that the output has no "Unknown" skill line. |
| Warning / Medium | The fixture cleanup after Task 2 step 5 cannot undo what `plan-widget` may already have done. `git reset --hard` resets to the current HEAD, so a plan commit that `plan-widget` made stays. A `code-widget` launch leaves a branch and a `.claude/worktrees/widget` worktree, and `git clean -fd` skips nested git directories. The step's "no output from `git status`" can then fail, or it can pass on a fixture that has quietly changed. | Plan lines 438-446; the Risk bullet (plan lines 613-615) claims a full reset | Record the init commit in Task 1 (`INIT=$(git rev-parse HEAD)`). Kill the test server right after the duplicate check, then run `git reset --hard "$INIT"`, `git worktree prune`, delete every branch except `main` and `feat/sprocket`, and `rm -rf .claude`. Re-check the branch list. |
| Suggestion / High | The plan-stage check `ls docs/plans/*-<slug>.md` also matches plans whose slug ends with this slug. For slug `match-grade`, the file `2026-09-21-landing-match-grade.md` counts as "a plan exists", so the stage stops falsely. Spec D8 says "the same slug". | SKILL snippet plan lines 279-280; spec D8 | Anchor the glob to the date prefix: `docs/plans/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-<slug>.md`. |
| Suggestion / High | The two lint steps can never show their expected "no output": `grep error` matches the summary line `Summary: 0 error(s)` that `markdownlint-cli2` prints even for a clean file. | Plan lines 341-342 and 529-532; a scratch run of `markdownlint-cli2` v0.20.0 | Filter on the finding lines only, for example `grep ' error MD' \| grep -v -E 'MD013\|MD060'`. |
| Suggestion / High | Skill selection (Task 4 step 2) runs after the end-of-branch reviews (step 1). If it fails, the plan tells the executor to edit the `description` and rerun, so that edit lands after the final review. | Plan lines 549-565 | Move the skill-selection check to the end of Task 2, before the commit. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Covers the spec completely: every part of D5 to D10 appears in the SKILL snippet, and all four files in the spec's file table are in the file map | Plan lines 76-81 and 175-337; spec "Files" table | Strong |
| Anchors and commands are grounded: README, ROADMAP and GLOBAL-CLAUDE text, the `CLAUDE_PID` and `ps` approach, tool versions, and the lint output format all match the repo | `README.md:33-35`, `ROADMAP.md:54`, `GLOBAL-CLAUDE.md:46`, `my-plugin/skills/soundness-review/SKILL.md:106-110` | Strong |
| Launch tests are isolated in a separate tmux server (`-L handofftest`) with `wait-for` synchronisation, and the window count before and after catches a leak | Plan lines 380-399 and 410-414 | Moderate |
| Red runs before Green, and the start-check tests check side effects (files, branches, git status), not only output text | Plan lines 142-153 and 361-373 | Moderate |
| Easy to reverse: one new directory and three doc lines | Plan lines 76-81 and 624 | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| A false environment premise sends test signals to the user's tmux server | Plan line 346; plan lines 556-561 | Medium |
| The mode-refusal test passes whatever the skill does | Plan lines 402-405 | Medium |
| The launch test cannot tell a right plugin path from a wrong one | Plan lines 417-420 | Medium |
| Fixture cleanup does not match what the launched session can do | Plan lines 438-446 | Low |
| The plan and code stages are not exercised before merge; the plan accepts this and leaves it to a pilot | Plan lines 621-623 | Low |

## Not Applicable

- Risk & reversibility, schema and data side: the change adds prompt text and
  doc lines only. It has no schema, API or data migration. The dimension was
  still applied to the test side effects (findings above).

## Needs Investigation

- **Trust dialog in the fixture.** The launched interactive `plan-widget`
  session starts in `$FIX`. That directory is its own git repo nested under the
  trusted `claude-setup` path. If Claude Code does not inherit trust from the
  parent directory, the session stops at the trust dialog. `ListAgents` may
  then not list it, or may list it as waiting, and Task 2 step 5 fails or
  passes for the wrong reason. To resolve: one probe with `claude -n x` in a
  nested repo under `claude-setup`, or a check of whether `~/.claude.json`
  gains a new entry for `$FIX`.
- **`ListAgents` and the auto-mode classifier in a headless launcher.** The
  probes cited on plan lines 67-70 show that `ListAgents` lists a named
  session. They do not show that a `claude -p` session can *call*
  `ListAgents`, or that auto mode lets Bash run `tmux new-window "claude ...
  --permission-mode auto ..."`. A classifier could treat starting another
  autonomous agent as an escalation and block it. Either failure would make
  Task 2 steps 4 and 5 fail without any fault in the skill. To resolve: run
  both calls once in a headless auto session before Task 2.
- **Whether a nested `claude` process overwrites `CLAUDE_PID`.** This decides
  whether the fourth finding is only a weak assertion or a real
  wrong-plugin launch. To resolve: from a nested `claude -p`, print
  `$CLAUDE_PID` and compare it with the parent's value.

## Reasoning

The plan is complete against the spec, the steps are in a sensible order, and
its repo references hold. So the approach is right. The problems are in the
test harness. The false belief that headless children have no tmux variables
lets two test steps act on the user's tmux server, which the plan itself
forbids. Two launch assertions are too weak to fail for the right reason, and
the fixture reset promises more than it delivers. Each of these has a local
fix, and none of them changes a spec decision, so the verdict is Mixed, not
Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the environment findings rest on variables seen
directly in a session's Bash, and the other findings rest on the plan's own
text.
**Recommendation:** Before execution, move Task 2 step 3 into the
`handofftest` server and assert the `⚠` mark there. Add
`env -u TMUX -u TMUX_PANE` to Task 4 step 2. Make the refused-mode test allow Bash and require the
fallback grep. Assert `$WT/my-plugin` in the launch test. Reset the fixture to
a recorded init commit. Then run the three probes listed under Needs
Investigation, or do so at the start of Task 2.
