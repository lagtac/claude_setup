# Code review: brainstorming's routes

**Status:** review of `main..feat/brainstorming-routes`, 2026-10-19. `/code-review high`; the fix round answered it on the branch.

The review read the six commits of the branch, as `git diff main...HEAD`. It ran without
`--fix` and wrote no report of its own, so the review stage copied its findings here.

## Findings

| # | Where | Finding | Class | Answer |
| --- | --- | --- | --- | --- |
| 1 | `global/methods/my.md`, Spike | A spike before a spec, on `spike/<slug>` with the spec's slug, blocks `/my:handoff` for that spec: its start checks refuse a branch `*/<slug>` and a worktree `.claude/worktrees/<slug>`. | gate | The user chose a fix: the spike takes a slug of its own (my.md, spec D7). |
| 2 | `plugins/my/bin/status-scan.py` | Spike branches are never merged, so `my:status` reports each one as maybe-unfinished, for ever. | gate | The user chose a known limit and roadmap row 73 (plan, Risk). |
| 3 | `global/methods/my.md`, Bug | A bug that does not escalate follows the bounded rules, but D6 set no file limit, so a bug fix across many files had no clear route. | gate | The user chose a fourth case: a fix to more than two files goes to brainstorming (my.md, spec D6). |
| 4 | `global/methods/my.md`, Spike | The spike route makes a worktree and never removes it. | gate | The user chose a fix: the worktree is removed once the spike file lands (my.md, spec D7). |
| 5 | `plugins/my/skills/roadmap-management/SKILL.md`, rule 11 | A row routed to a spike keeps `route not set`, because only the 📋 and ✅ edits set the route. | gate | The user chose a fix: the edit that links the spike file sets `spike` (rule 11, spec D9). |
| 6 | `global/methods/my.md`, UI row | The design-system audit runs before brainstorming but depends on the route. | not a finding | A known limit in the spec's and the plan's Risk sections; row 70 settles it. |
| 7 | `global/methods/my.md`, Superpowers Integration | "Once the route below is picked, the corresponding skill must run first" conflicts with brainstorming stating the route. | fix | The clause is gone; the paragraph points to "Pick the route" for the timing. |
| 8 | `global/methods/my.md`, Bounded | The Bounded bullet repeats "A bug still starts with `superpowers:systematic-debugging`", left over from Small. | fix | Deleted; the Bug bullet keeps it. |
| 9 | `global/methods/my.md`, Spike | "The `pre-commit` hook refuses a doc that cites a commit not on `main`" is too strong: the hook reads only hashes in backticks. | fix | Reworded in my.md and spec D7. |
| 10 | `plugins/my/skills/clean-plans/SKILL.md` | The type list lacks `spike`, so an undated spike file is renamed as a plan. | gate | The user chose a fix: `spike` joins the type list and the name table. |

## Re-review after the fix round

The re-review read the same range, now with the fix round. It found nine findings, none
Critical. The one fix round is spent, so each is a known limit in the plan's Risk section
("Re-review, 2026-10-19").

| # | Where | Finding | New or repeat |
| --- | --- | --- | --- |
| 1 | `global/methods/my.md`, Spike | The own-slug rule covers only a spike before a spec; a standalone spike's branch also blocks a later spec with its slug. | partial repeat of 1 |
| 2 | `global/methods/my.md`, the risk line | The spike exemption cannot be reached: a risk-line task states `architectural with plan` first, and a route only moves up. | new |
| 3 | `plugins/my/skills/roadmap-management/SKILL.md`, rule 11 | A row routed to a spike gets its route word, but no rule moves its status, so it stays 💭. | new, near 5 |
| 4 | `plugins/my/skills/handoff/SKILL.md` | `auto code` is labelled "(architectural)" for the no-plan route. | repeat, new place |
| 5 | `global/methods/my.md`, Precedence | The "only" list and the next sentence disagree on who decides the route. | new |
| 6 | `global/methods/my.md`, skip line | The Spike bullet names none of the trigger rows the skip line says it names. | new |
| 7 | `global/methods/my.md`, Superpowers Integration | "The table below" now sits above the route table, which also names skills. | new |
| 8 | `plugins/my/skills/roadmap-management/SKILL.md`, rule 11 | The risk line is copied into four files. | new |
| 9 | `ROADMAP.md`, row 60 | Row 60 has no kind word and no `route not set`. | new |
