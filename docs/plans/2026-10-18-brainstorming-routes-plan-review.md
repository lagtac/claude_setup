# Review: docs/plans/2026-10-18-brainstorming-routes.md

**Status:** review of docs/plans/2026-10-18-brainstorming-routes.md, 2026-10-18. Mixed: the text edits are well grounded, but Task 5 misses open row 71, and the rehearsal checker is not proven able to pass or fail on the route itself. The plan stage fixed all five Warnings and both Suggestions in the plan before its commit.

## Change Summary

The plan carries out the row 67 spec in five tasks. Task 1 replaces `my.md`'s size table with a "Pick the route" section, renames one test heading, and runs a headless `claude -p` rehearsal before and after the change. Tasks 2 to 4 carry the route names into `docs-layout.md`, three skills and the `my` README. Task 5 rewrites the open roadmap rows and zitamu's local file. A section after the merge covers zitamu's roadmap.

## Grounding

Searches were text-only (`grep`, `sed`, `python3`). This agent has no symbol-reference tool. Most claims hold:

- Task 3, step 1 expects 11 + 2 lines. The repo gives exactly 11 (`design-system/SKILL.md:132`, `handoff/README.md:54,224,226,252,273,285`, `roadmap-management/SKILL.md:174`, `handoff/SKILL.md:38,289,866`) and 2 (`roadmap-management/SKILL.md:121,163`).
- Task 5, step 5's allowed leftovers match the repo: 4 confidence-label lines each in `spec-reviewer-prompt.md:87,98,154,171` and `code-reviewer-prompt.md:57,64,110,127`.
- A sweep of the whole repo outside `docs/`, for `Small|Medium|Large` and the size phrases, finds no live reference outside the plan's file list. The kit hits (`tune-claude-instructions`, `md-tables`) are severity labels or table sizes. The cross-repo sweep of `~/projects/*/CLAUDE*.md` finds only zitamu's `CLAUDE.local.md`, which is a symlink to `projects/real-estate-webapp/claude-local.md`, a file in the plan.
- `status-scan.py:49` `OPEN_STATUSES` lacks `answered`, and `doc_states` (`status-scan.py:125-139`) lists only open statuses. The Task 2 test and its deliberate break are valid.
- `test_neutral_core.py:17-18` holds `"Size the process to the change"`. `"Learning workspaces"` exists in no method file, as the plan says.
- The zitamu table under "After the merge" matches zitamu `HEAD:ROADMAP.md`: 13 open rows, and the Order of work lines 227 and 231.
- Plugin keys `my@claude-setup` and `superpowers@synced` exist in `~/.claude/settings.json`. The Skill tool's input key is `skill`, as checked in past transcripts. Superpowers' brainstorming announces "this looks bounded…" (`skills/brainstorming/SKILL.md:60-61` in the synced plugin), which the route regex accepts.

Stale or incomplete:

- Task 5, step 1 lists the rows found on 2026-10-18 and only allows for row 72 ↔ the working tree's `ROADMAP.md:249-253` holds row 71 (📋, "Medium; spec drafted"), which the plan never names. The script prints it.
- Task 5, step 3's check list omits rows 71 and 72, although step 2 handles 72.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | Open row 71 is missed. Its text says "Medium; spec drafted". Task 5, step 2's catch-all rule has no case for a 📋 row whose route brainstorming already picked, so it would turn 71 into `route not set`. The plan's own zitamu rule for row 149 handles exactly this case ("It is 📋, so brainstorming has picked its route"). Row 71's draft spec also edits the same Precedence paragraph as D12 (`2026-10-18-project-precedence-spec.md:12,240`). | `ROADMAP.md:249-253` (working tree); plan Task 5, steps 1-3 | Add row 71 next to row 72: "if its commit has landed". Add a fourth catch-all case: a 📋 row with a spec takes the route its spec picked. Add 71 and 72 to step 3's check list. |
| Warning / High | The red rehearsal never shows that the route checks can fail or pass. Every red run fails on the size-line clause, so a route regex that matches nothing still gives 15/15 FAIL. Tested by hand: the route regex rejects `**Route:** bounded`, `Route: **bounded**`, `This is a spike` and `this looks like a spike`. The size regex accepts ordinary prose such as `Small change, so…` and `Large files are…`. So a green run can fail for a wording reason, and a bug run can pass vacuously when the regex finds no route line at all. Step 6's advice "If a run passes under the old rules … fix the checker" is also wrong for `bug`: its pass rule (a Skill call, and no route line) is what the old rules also ask for. | Plan Task 1, steps 4 and 6; `my.md:16-19,28` (old rules already send bugs to `systematic-debugging`) | In step 4, run `check.py` against hand-made streams first: one pass and one fail per prompt, including the bold and "a spike" forms, and a line that starts with "Small" in prose. Widen the route regex, or anchor the size regex to `Small:`, `Medium:`, `Large:`. In step 6, say that a red pass on `bug` means the old session printed no size line, not that the checker is broken. |
| Warning / Medium | Failing on any permission denial will likely fail correct runs. User settings allow only `Bash(git push:*)`. Under `acceptEdits`, `systematic-debugging` tries to reproduce the bug with `python3 …`, which is denied. That run then fails after it already made the right first step. `my:architect` on `deleted_at`, and the worktree step of the bounded and spike routes, can be denied in the same way. | `~/.claude/settings.json` (`permissions.allow` has 1 entry); plan Task 1, step 4, "Every prompt fails when … permission_denied" | Count only the denials that come before the route line or the first Skill call. Or give the fixture's `.claude/settings.json` a `permissions.allow` list for `python3`, `git worktree` and `git -C`. |
| Warning / Medium | The plan adds a rule that the approved spec does not contain. A task that hits the risk line must state its route "before any skill runs". D1 says that brainstorming states the route. The plan records this only in Trade-Offs and Risk, and the method says a header note is "a breadcrumb, not signoff". It changes when the route is stated, which is a decision, not wording. | Plan Task 1, step 8 item 1; Trade-Offs, first point; spec D1 (`2026-10-18-brainstorming-routes-spec.md:91-94`) | Confirm with the user before Task 1, in the "No silent reinterpretation" form, or record the user's yes in the plan. |
| Warning / Medium | Several commands run with no `cd <worktree> &&`. These are `git add`/`git commit` in Task 2, step 5 and Task 5, step 6, and `sed … ROADMAP.md` in Task 5, step 3. The code stage opens in the main checkout (`handoff/SKILL.md:822-823`), and `my.md` says to run each worktree command as `cd <worktree> && …`. If the working folder is not the worktree, Task 5, step 6 stages the main checkout's `ROADMAP.md`. Another session has uncommitted edits in that file, so they would be committed on `main`. | `plugins/my/skills/handoff/SKILL.md:822-823`; `global/methods/my.md` (Git Workflow, "When to use worktrees") | Start every block with `cd .claude/worktrees/brainstorming-routes &&`, or use `git -C <worktree>`. |
| Suggestion / High | The Precedence edit is listed twice. Task 1, step 9 says "each row of the spec's table … plus two", and the spec's table already has a "Precedence paragraph → D12's sentence" row. An executor could add the sentence twice. | Spec `2026-10-18-brainstorming-routes-spec.md:264`; plan Task 1, step 9 | Say "plus one (Discovery authority); the Precedence row's sentence is the one below". |
| Suggestion / High | The check and commit blocks put each command on its own line, with no `&&` and no `set -e`. In Task 1, step 13, Task 3, step 5 and Task 4, step 2, `git commit` still runs after a failed `grep` check, lint or test run. | Plan Task 3, step 5 (first line `! grep …`, then `git commit` on a later line) | Chain the checks to the commit with `&&`, or split each block into "check" and "commit". |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Exact, verified red counts for the skill edits | `roadmap-management/SKILL.md:121,163,174`; `handoff/SKILL.md:38,289,866`; `handoff/README.md:54…285` | Strong |
| Complete file list: the text sweep found no live size word outside the planned files | repo-wide `grep -rnwE` outside `docs/` | Strong |
| The new status test can really fail: adding `answered` to `OPEN_STATUSES` makes the doc show in the `docs` block | `plugins/my/bin/status-scan.py:49,136` | Strong |
| Rehearsal fixture design anticipates real pitfalls: absolute import with a load probe and fallback, `DESIGN-SYSTEM.md` to keep the audit out, kit's method guard off, copies per run | plan Task 1, steps 3, 5 and 6; `plugins/kit/hooks/method-guard.py:4-12` | Moderate |
| The zitamu edit is worked out row by row, and kept out of the `Task:` trailers so a restart does not redo it | zitamu `HEAD:ROADMAP.md:227,231,325-516` | Moderate |
| Reversible: text only, one squash commit | plan Risk, last point | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Open row 71 is missed, and the catch-all rule would mislabel it | `ROADMAP.md:249-253` | Medium |
| The rehearsal checker's route clauses are never shown to work; the red step tests only the size-line clause | plan Task 1, steps 4 and 6; regex tested by hand | Medium |
| The denial rule probably fails correct runs, given the user's allow list | `~/.claude/settings.json` | Medium |
| An unconfirmed addition to D1 | spec `:91-94`; plan Trade-Offs | Medium |
| Commands that depend on the working folder carrying over between calls | `handoff/SKILL.md:822-823` | Medium |

## Not Applicable

- Snippet logic (dimension 6), for executable code beyond the checker: the only full snippets are the Task 2 test and the roadmap script. Both were run or checked, and they are correct. The checker is specified in prose and covered under dimension 3.

## Needs Investigation

- **What `claude -p` does with an unapproved external `@/abs/path` import.** If it is skipped silently, the load probe catches it and the fallback runs, so the plan copes either way. A single probe run before Task 1 would settle it and save one round of 16 runs.
- **Whether `acceptEdits` auto-approves the read-only Bash commands that brainstorming uses to explore** (`ls`, `git log`). If it does not, even the `rename` and `quiet` runs hit denials. One headless run in the fixture with `grep -c permission_denied` would show it.

## Reasoning

The text edits are the bulk of the plan, and they hold up against the repo: exact counts, a complete reference sweep, and a valid red step for the one new unit test. The weak points are at the edges. Task 5 does not cover a row that is in the working tree today. The rehearsal checker's route and denial rules are untested, and one of them is likely to fail runs that made the right choice. The plan adds one rule to the approved spec without the user's sign-off, and some commands depend on the working folder carrying over between calls. Each has a local fix, and none needs a new approach.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. The grounding of the text edits is strong. The rehearsal findings rest on regex tests and the user's settings, not on a real `claude -p` run.
**Recommendation:** Before the code stage, add row 71 and the 📋 case to Task 5. Add hand-made stream tests to the checker, and limit the denial rule to denials before the route line. Get the user's yes on the risk-line timing rule. Put `cd <worktree> &&` on every command.
