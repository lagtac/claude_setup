# Review: docs/plans/2026-10-12-autonomous-run-spec.md

**Status:** review of docs/plans/2026-10-12-autonomous-run-spec.md, 2026-10-12. Mixed: the approach is right, but D5's merge-conflict recovery runs `git merge --abort`, which fails after `git merge --squash`, and the state-file contract has gaps. Answered in the spec on 2026-10-12: the user accepted all six Warnings, both Suggestions and the Monitor question, and each fix is in the spec.

## Spec Summary

The spec adds an `auto` mode to `my:handoff`. With it, an approved spec runs plan, code and review, then squash-merges, folds and writes the `done` marks with no user input. The mode is started by an explicit word and limited by a four-key Delegation section in the spec. A plugin `PreToolUse` hook keyed on `MY_AUTORUN` blocks `git push`. An untracked state file under the git common directory, written by a new `handoff-state.py`, records the next step. `auto resume` uses it to continue after a crash.

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `my:handoff` skill (plain + auto mode) | Stage steps, start checks, stop outcomes (D5 table), Launch command line, resume logic | Delegation section, state helper, fold script, tmux, push guard via env var | Existing `plugins/my/skills/handoff/SKILL.md:1` (380 lines); auto mode is new |
| Delegation section (in each spec) | The user's advance grant: allowed deps, `stop`/`decide`, allowed failing tests, fallback checks | Spec author; read by every auto stage | New (format, spec §D2) |
| Run-state file `<git common dir>/my-handoff/<slug>.json` | `next`, `stopped`, `squash_subject`, `head_before_fold`, `branch`, `worktree`, paths | Written only through `handoff-state.py` | New (spec §D6) |
| `plugins/my/bin/handoff-state.py` | Atomic write; `check` rules per `next` value | git | New (not found today; `plugins/my/bin/` holds three other scripts) |
| Push guard `plugins/my/hooks/block-autorun-push.py` + `hooks.json` entry | The decision to block a Bash call that pushes | `MY_AUTORUN` in the Claude Code process environment | New; `hooks.json` existing at `plugins/my/hooks/hooks.json:1` (no `PreToolUse` entry today) |
| `git-fold-fixups.py` | Fold of waiting fixups; refusal; exits 0/1/2/3 | git | Existing `plugins/my/bin/git-fold-fixups.py:26-31` |
| Global flow, step 3 (D10) | The question that offers auto mode | handoff | Existing `global/CLAUDE.md:99`, Medium paragraph `global/CLAUDE.md:61` |
| Signal (`⚠`, PushNotification, last line) | Telling the user a run stopped | tmux | Existing `plugins/my/skills/handoff/SKILL.md:66-87` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| User → handoff (Launch) | `/my:handoff auto plan|code|resume <spec>` | User |
| handoff stage → next stage | `MY_AUTORUN=<slug> claude … '/my:handoff run auto <stage> <doc>'` via `tmux new-window` | Sending stage |
| Stage → Delegation section | Read at start checks and at each consult row of D5 | Spec (user) |
| Stage → state file | `handoff-state.py set` at launch, around each step on `main`, at a stop | handoff stage (one alive at a time) |
| `auto resume` → state file | `handoff-state.py check` then `get` | handoff resume session |
| Claude Code → push guard | Hook JSON on stdin, env var inherited; exit 2 blocks | Push guard |
| Review stage / resume → git on `main` | `merge --squash`, `worktree remove`, fold, `done` commit | Review stage, or the resume session for `next` ≥ `merge` |
| Stage → fold script | Subprocess; exits 1 and 3 become stops | Fold script |
| Stage → user | Signal, plus `stopped` in the state file | Stage |

## Grounding

Text-only sweep (no symbol tool; `grep`, `ls`, `sed` through Bash). No symbol is removed or renamed.

All checked references hold. Checked: SKILL.md line count (380), Plan stage step 8, Review stage steps 7 and 8, the code-stage start check (`plugins/my/skills/handoff/SKILL.md:144-147`); the fold script's exits 1 and 3 (`plugins/my/bin/git-fold-fixups.py:26-31`); `hooks.json` has no `PreToolUse` today; `global/CLAUDE.md:61` and `:99`; `docs-layout.md` steps 9 to 13; handoff spec D1, D2, D4; the brief's "Open for brainstorming" list; `my:push` (`plugins/my/commands/push.md:18`); zitamu's own pre-push hook (`global/rules/docs-layout.md`, "Cite only commits on `main`"); the repo-root `settings.json` deny list, while the marketplace source is `./plugins/my` (`.claude-plugin/marketplace.json:12`), and no `plugins/my/settings.json` exists.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | The merge-conflict outcome runs `git merge --abort`. After `git merge --squash`, git writes no `MERGE_HEAD`, so the abort fails with `fatal: There is no merge to abort (MERGE_HEAD missing)` and exit 128. I reproduced this in a scratch repo with git 2.43.0. The run still stops, but the main checkout keeps unmerged paths (`UU f`), and the record `next=merge` no longer matches it. If `check` looks for `MERGE_HEAD`, as the fold's `in_progress()` does, it misses this state. The fold itself would refuse with exit 1, because of the uncommitted changes. | `spec §D5` (row "`git merge --squash` conflicts"); `plugins/my/bin/git-fold-fixups.py:141-145`; brief Candidate C's "Driver → git" row, which already named `git reset --merge` | Use `git reset --merge`, which works without `MERGE_HEAD`. Then check `git status --porcelain` is empty before writing `next=merge`. Have `check` treat unmerged paths or `AUTO_MERGE` / `MERGE_MSG` as "merge in progress". Add a squash-conflict case to the rehearsal. |
| Warning / High | design | The `merge` check cannot work as written. D6 sets `squash_subject` after the merge, but `check` for `next=merge` asserts "no commit on `main` has `squash_subject`". At `next=merge` the field is still empty. A crash between the squash commit and the next `set` leaves `next=merge`. `check` then passes, and resume squash-merges a second time. | `spec §D6` (field table ↔ `check` for `merge`) | Write `squash_subject` before the merge, because the subject is known in advance. Or make `check` for `merge` look for a commit on `main` whose subject the stage would write. |
| Warning / High | design | The D3 rule "no state file with `next` other than `finished`" is listed for every auto start. D6 says the first stage creates the file with `next` set to its own stage. So the `code` stage that an auto `plan` stage launches finds `next=code`, and it fails with "use resume". So does every stage that D7's resume launches, because D7 skips only the fresh-start checks (no plan, branch or worktree yet). | `spec §D3 ↔ §D6 ↔ §D7` | Apply the check only to the user-typed Launch forms `auto plan` and `auto code`. In `run auto <stage>`, require instead that the file exists and `next` equals `<stage>`. |
| Warning / High | design | Resume of `plan`, `code` or `review` "starts again from its first step". `check` defines no facts for these three `next` values, and there is no `next` value for a step done inside a stage. Example 1: the plan stage crashes after its commit (step 7) but before it launches `code`. A resume rewrites and recommits the plan, because the "no plan yet" check is skipped. Example 2: a code stage resumed after several task commits starts again at task 1. | `spec §D6` (`next` values, `check` list) ↔ `spec §D7`; `plugins/my/skills/handoff/SKILL.md:209-216` | Decision for the author. Either define per-stage restart points, such as "plan committed" leading to the fold and launch, and "tasks done so far" from `git log <base>..<branch>`, or make resume of a stage that has commits a stop that asks the user. |
| Warning / Medium | design | When `next` is `merge` or later, the resume session runs the steps on `main` itself. That session is the one the user typed into, so it has no `MY_AUTORUN`, and the push guard is off for the unattended merge, fold and `done` steps. Its `<name>` for signals is also undefined: `<name>` is `<stage>-<slug>`, and `resume` is not a stage. | `spec §D4 ↔ §D7`; `plugins/my/skills/handoff/SKILL.md:54-56` | Have resume Launch a `run auto review` window, with the env var, that enters Review step 8 at `next`. Or state that the guard does not cover this path and add that to Risk. |
| Warning / Medium | design | `auto code` commits the `approved` edit and folds it inside the start checks. Today's start checks "write nothing" when they fail. The state file is created only after they pass, so this change to `main` happens with no state recorded. D3 also leaves out `git-fold-fixups.py check <hash>` before the fixup, which docs-layout step 4 requires. When that check exits 1, the fallback would be a normal commit that only changes a status, which docs-layout forbids. D3 also does not say what happens when the main checkout is dirty and Plan step 8 skips the fold. | `spec §D3`; `plugins/my/skills/handoff/SKILL.md:134-135`, `:232-234`; `global/rules/docs-layout.md` steps 4 and "No commit only changes a status" | Decision for the author. Move the commit and fold into a numbered first step of the code stage, after the state file is created. Name the `check` step and the outcome of each branch: refused, or fold skipped. |
| Suggestion / High | design | D1 changes a settled point of the architecture brief without saying so. The brief's Decision says "The approved spec's **Delegation** section switches it on", and that trigger was not in its "Open for brainstorming" list. | `spec §D1`; `docs/plans/2026-10-11-autonomous-run-architecture.md:201`, `:222-230` | Decision for the author. Confirm with the user that this change was approved. Then name it in D1 as a change to the brief's Decision. |
| Suggestion / High | design | The guard matches when the whole command "contains" `git … push`. So a heredoc or a commit message that mentions `git push` is blocked too. Specs like this one mention it often. The test list has no such case. | `spec §D4`, `spec §Testing` | Match only at command starts: the start of the string, or after `;`, `&&`, `||`, `|` or `(`. Add a test where `git commit -m "… git push …"` exits 0. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Fit with what exists | It extends the existing stage chain. One copy of the steps on `main`, as the brief's force 8 asked. The rejected options (a new skill; the Delegation section as the trigger) are real choices with reasons. | `spec §D1`; brief Evaluation | Strong |
| Boundaries | Each new part has one job: the guard blocks, the helper writes and checks state, the skill decides. The state file has one writer at a time. | `spec §D4`, `§D6` | Strong |
| Failures (push) | The guard sits outside the model, holds under `bypassPermissions` (per the recorded spike), and covers `git -C` / `git -c`. Its gaps are stated in Risk. | `spec §D4`, `§Risk` | Moderate |
| Contracts (Delegation) | Closed keys, exact-name comparison, unknown keys fail the start check. This narrows the self-judging risk. | `spec §D2` | Moderate |
| Spec rules | "How to read this spec" comes first and has paths. Trade-offs, Dependencies and Risk exist. The Files table is complete. | spec headings | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Failures (merge conflict) | `git merge --abort` fails after `--squash`, which leaves unmerged paths in the main checkout | High |
| Contracts (state file) | `squash_subject` is used before it is set; no restart points inside a stage | High |
| Contracts (start checks) | The state-file check blocks every stage after the first, and every resumed stage | Medium |
| Failures (resume) | Resume of the steps on `main` runs without the push guard | Medium |

## Not Applicable

None.

## Needs Investigation

- Spec D4 cites the Claude Code docs (fetched 2026-10-12): a plugin's `settings.json` keeps only `agent` and `subagentStatusLine`. I could not fetch the docs offline. This claim only explains why a deny rule was rejected. The spike carries the chosen design. One fetch of the plugin reference page would settle it.
- The guard's matcher is `Bash`. Whether other tools that run shell commands, such as `Monitor`, also need it depends on the Claude Code version. A check of the hook matcher docs would settle it.

## Reasoning

The components and their ownership are clean. The approach, a mode of handoff with a hook guard and a helper-owned state file, fits the brief and the repo. The problems sit at the edges of the state machine. These are the merge-conflict recovery, which I verified fails in git; the `merge` check, which reads a field that is not yet set; the start check that blocks the run's own later stages; and resume restarting stages that already did work. Each needs a contract fix, not a new approach. There is no Critical finding, because the bad abort still ends at a stop the user is told about.

## Verdict

**Assessment:** Mixed
**Confidence:** High — I reproduced the abort failure in a scratch repo, and the other Warnings are contradictions between spec sections that I quoted.
**Recommendation:** Replace `git merge --abort` with `git reset --merge` plus a clean-tree check. Then settle the state-file contract with the user: when `squash_subject` is written, restart points inside a stage, which starts run the state-file check, and how resume keeps the guard. Then re-run `my:spec-review`.
