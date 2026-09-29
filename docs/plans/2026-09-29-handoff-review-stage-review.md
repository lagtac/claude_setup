# Review: the `my:handoff` review stage

**Status:** review of `plugins/my/skills/handoff/SKILL.md`, 2026-09-29. It
reviewed the review stage; the fixes to the skill and spec D2 answered it.

**Subject:** `plugins/my/skills/handoff/SKILL.md` after the commit that adds the
review stage ("feat(my-plugin): add a review stage to my:handoff for the
end-of-branch checks"), with its edits to `README.md`, `ROADMAP.md` and
`global/CLAUDE.md`.
**Read against:** `docs/plans/2026-09-21-handoff-spec.md` (decision D2),
`global/CLAUDE.md` ("Code Review Routing", "Git Workflow"),
`plugins/my/skills/soundness-review/SKILL.md`, and zitamu's `CLAUDE.local.md`.

## Verdict

The review stage is a sound idea and mostly well written. The fixed prompt
block, the explicit range and the written-out `/code-review` level answer real
failures. Two things need a decision before the next feature uses it:

1. The change reverses a spec decision without recording it (finding 1).
2. The review session runs in the main checkout, but the branch lives in the
   worktree. So the symbol map reads the wrong code, and review files land on
   `main` uncommitted (finding 2).

## Findings

### 1. Design — spec D2 rejected this exact session, and the spec was not updated

Spec D2 says: "Rejected: a fourth session for review and merge (the reviews
already run as fresh subagents, so a separate session adds no independence,
and the fix round would happen away from the context that wrote the code)."

The commit adds that fourth session. Its message gives new reasons: the code
session dropped end-of-branch steps, such as the e2e run and the "no branch
commit IDs" line. Those reasons may well outweigh D2's. But the skill still
names the spec as its authority, and the spec still says the opposite.

This is a `design` finding, so it is not fixed here. Question for the user:
keep the review stage on the new grounds, and amend D2 with the trade-off? The
cost D2 named is real: the fix round now runs in a session that did not write
the code.

### 2. High — the review session works from the main checkout, not the worktree

Launch always opens the window with `-c <repo root>`, the main checkout, which
is on `main`. Three effects follow:

- **Map (step 3).** `LSP` resolves against the session's project root. So it
  maps the symbols as they are on `main`, not on the branch. New symbols are
  not found at all.
- **Review reports.** `my:soundness-review` writes its report to
  `$(git rev-parse --show-toplevel)/docs/plans` (its SKILL.md, lines 155 and
  219). Run from the main checkout, the report lands uncommitted on `main`.
  That dirties `main` for parallel sessions, and for the rebase in Git
  Workflow step 9, which needs a clean main checkout.
- **Where files are committed.** The skill never says where the review reports
  and the fix round's **Risk** edits are written and committed. Git Workflow
  step 11 says: while the worktree exists, edit the feature's plan only in the
  worktree.

Suggested fix: the review stage runs every command as `cd <worktree> && …`,
the prompt block names the worktree path, and step 6 says "commit the review
reports and the Risk edits on the branch". Whether to launch the whole session
inside the worktree is a separate choice: project memory is keyed on the
session's path, so a worktree session would not see the project memory.

### 3. Medium — the per-task test-diff check is gone from the code stage

`global/CLAUDE.md` says two checks replace the skills' per-task reviewer. One
is: after each task, read `git diff` for the test files the task touched, and
stop if an assertion was removed or weakened. Code stage step 2 now says "Run
no code reviews" and does not name this check. The commit's own reason is that
rules living only in `CLAUDE.md` get dropped. This rule is one of them.

Suggested fix: add the check to code stage step 2, and add "an assertion was
removed or weakened" to the gates in step 3.

### 4. Medium — step 2 has no fallback when the project lists no end-of-branch checks

Step 2 runs "the checks the project's rules list for the end of a branch".
zitamu's `CLAUDE.local.md` does not use those words. It says e2e does not run
in CI, "so run it locally before pushing UI changes", and that a worktree runs
it with `web/scripts/e2e-worktree.sh <worktree path>`. A session could read
that as "no end-of-branch checks" and run nothing. That is the failure the
commit message cites (three branches merged with no recorded e2e run).

Suggested fix: when the rules name no end-of-branch check, signal and ask
which checks to run, and record "no checks run" in the `done` mark. Also,
consider adding an explicit "end-of-branch checks" line to zitamu's
`CLAUDE.local.md`.

### 5. Medium — step 3 names tools that may be absent

Step 3 says to use the `LSP` tool, then `Grep`. In auto mode, `Grep` can be
missing from a main session entirely. `LSP` is deferred and needs
`ToolSearch("select:LSP")` before the first call. The fix used elsewhere in
this repo: "`grep -rn '<token>'` through `Bash`", and "load `LSP` with
`ToolSearch` first".

### 6. Minor

- **Start check uses an unknown `<type>`.** The review start check names the
  branch `<type>/<slug>`, but only the code stage knows `<type>`. Use
  `git branch --list '*/<slug>'`, as the code stage does.
- **The prompt block holds one spec and one plan.** A batch has several. Say
  that the block lists every plan and spec of the batch, and that
  `my:soundness-review` runs once per plan with that plan's paths.
- **"The test in plan step 6" is unclear.** "Plan" can mean the document.
  Write "the test in Plan stage, step 6".
- **No worktree removal.** Step 8 does not mention `git worktree remove`
  (and keeping the branch). It is covered by "as the project's rules say",
  but the other merge steps are spelled out.
- **"Signal at exactly three points"** does not include the code stage's
  `done; <stop point>` signal. This was already true before this commit.

## Checked and not a problem

- **Nested dispatch works.** A review subagent that runs
  `my:soundness-review` can dispatch `my:code-reviewer`. A grispy session on
  2026-09-24 did this: the subagent made one `my:code-reviewer` dispatch and
  wrote the report.
- **`/code-review` accepts a range.** In the same session,
  `/code-review high <base>..HEAD` ran `git diff <base>..HEAD`. So a plain
  rerun in step 5 is a fair remedy.
- **Batch flow is consistent.** A non-last plan stops at code step 4. The last
  plan reaches code step 5 and launches the review with its own path, which
  matches the `<doc>` rule for `review`.
- The `README.md`, `ROADMAP.md` and `global/CLAUDE.md` edits match the skill.

## Resolution

The user kept the review stage and asked for every other finding to be fixed.

- Finding 1: spec D2 now describes four sessions and gives the reasons for
  the review session. D4, the Goal, the code stage and "Out of scope" follow
  it.
- Finding 2: the review stage runs every command in the worktree. The prompt
  block tells each subagent to do the same, so reports land on the branch.
  Step 6 commits the reports and the **Risk** edits on the branch.
- Findings 3 to 6: fixed in the skill as suggested. `<type>` is no longer
  needed at the start check; the batch prompt lists every spec and plan; step
  8 removes the worktree and keeps the branch; "Signal" lists four points.
