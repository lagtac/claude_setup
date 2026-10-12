# Review: docs/plans/2026-10-12-autonomous-run.md

**Status:** review of docs/plans/2026-10-12-autonomous-run.md, 2026-10-12. Mixed: the approach is right, but rehearsal Step 4 (resume at the fold) cannot reach its scenario with the fixture as described, and the plan never says how a `run auto` session tells a restart from a fresh start. The plan stage fixed all three warnings and all suggestions in the plan before its commit.

## Change Summary

The plan builds `my:handoff auto` in eight tasks: a `PreToolUse` push guard keyed on `MY_AUTORUN` (Task 1), a state helper `handoff-state.py` with `set`/`get`/`check` (Task 2), three `SKILL.md` edits for the forms and start checks, the stages in auto mode and `resume` (Tasks 3 to 5), docs (Task 6), and a four-run tmux rehearsal (Task 7). It adds six decisions the spec left open, among them who creates the state file, how the stages after the merge map to the review stage, and a `Task: <N>` commit trailer for restart detection.

## Grounding

Searches were text-only (`grep`, `sed`, `find` through Bash). No symbol tool was available. The plan removes or renames no symbol, so no caller sweep was needed.

Claims that hold:

- `plugins/my/hooks/hooks.json` has `PostToolUse` and `SessionStart` keys and no `PreToolUse` key yet. The `"$CLAUDE_PLUGIN_ROOT/hooks/..."` command form matches the existing `SessionStart` entry (`plugins/my/hooks/hooks.json:20`).
- `plugins/my/tests/test_git_fold_fixups.py:20,28,53,64` define `clean_env`, `git`, `make_repo` and `commit`, which Task 2 copies.
- Lint baselines are correct: 0 errors for `plugins/my/skills/handoff/SKILL.md`, `plugins/my/skills/handoff/README.md`, `README.md` and `ROADMAP.md`, and 16 for `global/CLAUDE.md` (counted with the plan's own command).
- `global/CLAUDE.md:99` is Spec → Plan step 3. The Medium paragraph runs from `global/CLAUDE.md:56`, and its `/my:handoff code` sentence sits near line 61.
- The handoff README has "Two ways to call it" (`plugins/my/skills/handoff/README.md:55`) and "What you need" (`:197`). `README.md:104` is the `plugins/my/bin/` paragraph.
- `ROADMAP.md:55` ("Deny list has no effect") and `ROADMAP.md:85` (`my:handoff auto`) exist, so it is right that the plan adds no rows.
- The D5 table in the spec has 17 rows, as Task 4 says.
- The guard algorithm in Task 1 Step 3 classifies all 14 BLOCKED and 8 ALLOWED cases correctly. I checked this with a scratch implementation on Python 3.12.3, built with `punctuation_chars="();<>|&\n"` (see the Suggestion row on why the plan's wording does not work as written).

Stale references or false assumptions:

- Task 1 Step 3 item 2 ↔ Python `shlex`: "`punctuation_chars=True`, with `\n` ... added to the punctuation" cannot be done after construction. `shlex.punctuation_chars` is a read-only property (`AttributeError: property 'punctuation_chars' of 'shlex' object has no setter`). The set has to be passed as a string to the constructor.
- Task 7 Step 4 ↔ `plugins/my/bin/git-fold-fixups.py:106-113` and the Task 3 fixture (plan lines 459-469): the scenario assumes D8 leaves a spec fixup waiting. See the first Warning.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | Rehearsal Step 4 cannot reach "stop in `review-widget` with `next` `fold`". D8 makes a spec fixup only when the spec's `approved` edit is uncommitted (spec D8; plan Task 4 "Code stage, auto mode"). But every Task 7 fixture is the Task 3 fixture, whose specs are committed as `approved` (plan lines 459-469). So no fixup is made, nothing waits for the fold after the merge, and the run goes straight to `next=done`. Also, if the "first `git push`" sets an upstream (`-u`), `git-fold-fixups.py check <spec commit>` refuses a target already on the upstream and exits 1, and D8 then makes a normal commit with no fixup. A plain `git push` without `-u` fails, since no `push.autoSetupRemote` is set globally. Step 5 then treats the failure as "a bug in Tasks 1 to 5", which sends the executor to debug correct code. | plan Task 7 Step 4 (lines 757-765), Task 7 intro (lines 728-731); `plugins/my/bin/git-fold-fixups.py:94-113` (`upstream()`, `target_refusal`: "already pushed to {up}") | For Step 4: leave the spec's status edit uncommitted (status `draft` committed, `approved` in the working tree). Push with `git push origin main` and no `-u`, so that no upstream is set, or push before the spec commit. Say both in Task 7. Add one check: after the code stage starts, `git log main` shows `fixup! <spec subject>`. |
| Warning / High | Restart detection is not defined. D7 says a restarted stage skips the fresh-start checks (no plan yet, no branch, no worktree) and stops on uncommitted files. But a `run auto code` launched by the plan stage and one launched by `resume` get the same command and the same state (`next=code`). The plan never says how the session tells the two apart. Decision 5 says only where a restarted code stage continues, not how it knows it is restarted. Task 5 Step 2 says only "the restart rules use decision 5". The executor has to invent a signal, for example `branch` being set, an argument, or a `stopped` value. | plan "Decisions this plan adds" item 5 (lines 84-90), Task 5 Step 2 (lines 638-642); `plugins/my/skills/handoff/SKILL.md:151-153` (the fresh-start checks a restart must skip) | Add a decision. For example: `resume` runs `set <slug> restart=1` (a new field) before it launches, and the stage clears it. Or: `run auto` treats an existing `branch` field (code, review) or an existing plan file (plan) as a restart. Add an r-run that resumes `next=code` with the branch present. |
| Warning / Medium | Run a7 expects `MY_AUTORUN is not set to widget; the push guard is off`, but it runs after `fresh`, so no state file exists. D3 also fails that session ("the state file exists"). The plan does not say which check runs first, so a correct implementation that checks the state file first fails a7. | plan Task 3 Step 4 table, row a7 (line 515); "Decisions this plan adds" item 4 (lines 81-83) | Say the order in Task 3 Step 3: the `MY_AUTORUN` check comes before the state-file check. Or give a7 a state file with `next=code`. |
| Suggestion / High | Task 1 Step 3 item 2 cannot be done as written: `shlex.punctuation_chars` cannot be changed after construction. | plan line 255-257; Python 3.12 `shlex` (AttributeError when I tried it) | Write `shlex.shlex(text, posix=True, punctuation_chars="();<>\|&\n")`, then remove `\n` from `whitespace`. |
| Suggestion / High | Some expected outputs do not match the form the plan specifies. a1, a3 and r2 expect a command that "starts `MY_AUTORUN=widget claude`", but the Launch fallback starts with `cd <repo root> &&` (`SKILL.md:113`). r1 expects `review-widget:`, but the plan never says what `<name>` a `resume` session uses (`SKILL.md:56` builds `<name>` from the args, which here would give `resume-widget`). | plan lines 509, 511, 648-649; `plugins/my/skills/handoff/SKILL.md:56,113` | Change a1, a3 and r2 to "contains `MY_AUTORUN=widget claude -n code-widget`". Say that `resume` names itself `<next stage>-<slug>`. |
| Suggestion / High | Rehearsal Step 2 expects "every `claude` process of the run has `MY_AUTORUN=widget`". The first window, which the user typed `/my:handoff auto code` into, is the launch form and has no `MY_AUTORUN` by design. | plan line 748; plan Task 3 Step 3 "Launch" (lines 496-499) | Say "every stage window (`code-widget`, `review-widget`)". |
| Suggestion / High | `Task: <N>` assumes numbered tasks. A Medium spec's Tasks section may be unnumbered, so N is undefined there. | plan decision 5 (lines 84-87); `plugins/my/skills/handoff/SKILL.md:149` ("numbered or not") | Define N as the task's position, counting from 1, in the task doc. |
| Suggestion / High | The Task 6 commit uses scope `global` for three files, against the plan's own scope rule (`my-plugin` for `plugins/my/`, `docs` for `README.md`). | plan Global Constraints (lines 35-36), Task 6 Step 5 (line 704) | Split the commit, or state that the scope names the main file. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The guard's parsing rule works on every listed case | Scratch run of the Task 1 Step 3 algorithm: 14/14 blocked, 8/8 allowed | Strong |
| Red before Green for both scripts, plus a real end-to-end guard test with a control run | plan Task 1 Steps 1, 2 and 6; Task 2 Steps 1 and 2 | Strong |
| Exact parts (push block, atomic state, crash-safe merge detection) live in tested code, not prose | plan Architecture (lines 17-23); Task 2 tests for the crash before the merge and for an older commit with the same subject | Strong |
| The plan's decisions fill real spec gaps and stay consistent with D3 and D7, such as the state file being created by the launch form and stages after the merge running as the review stage | plan lines 68-92; spec D3, D6, D7 | Moderate |
| Plain handoff is checked as unchanged (a8, rehearsal Step 1) | plan lines 516-519, 737-741 | Moderate |
| Baselines and file references are correct | Lint counts reproduced; `hooks.json`, test helpers, README sections and roadmap rows all found | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The rehearsal of resume at the fold cannot reach its scenario | plan lines 757-765 vs 459-469; `git-fold-fixups.py:106-113` | Medium |
| Restart behaviour (D7) depends on a signal the plan does not define | plan lines 84-90, 638-642 | Medium |
| Most of the 17 stop rows are tested only as text being present | plan Task 4 Step 1; Risk third bullet (already a known limit) | Low |
| Some expected outputs in headless runs are ambiguous (check order, `<name>` of resume, `cd` prefix) | plan lines 509-515, 648 | Low |

## Not Applicable

None.

## Needs Investigation

- **Does `Monitor`'s tool input carry the shell text in `tool_input.command`?** The guard reads only that field. The unit test feeds a hand-made `Monitor` payload, and the end-to-end test (Task 1 Step 6) exercises only `Bash`. If `Monitor` uses another field name, a `Monitor` push slips through without notice. To resolve it: add a second headless run to Task 1 Step 6 that asks for `git push` through `Monitor`, or log one real `Monitor` hook payload.

## Reasoning

The core design is grounded. The guard's rule works on every case the tests list, the state helper's tests pin the crash-safety cases, and every file, helper, section and lint baseline the plan cites exists as stated. The weak points are in the restart and rehearsal paths. The plan does not define how a stage knows it is a restart. Rehearsal Step 4 would fail for a reason in its fixture, not in the code, and Step 5 would then send the executor to debug correct code. Both need fixes to the plan text, not a new approach, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — both Warnings were checked against `SKILL.md`, `git-fold-fixups.py` and the plan's own fixture text.
**Recommendation:** Before handing off, make three edits. Fix the Task 7 Step 4 fixture: leave the `approved` edit uncommitted and push without setting an upstream. Add a decision that defines restart detection, and an r-run that tests it. Fix the order of the a7 checks. Then apply the Suggestions in the same edit.
