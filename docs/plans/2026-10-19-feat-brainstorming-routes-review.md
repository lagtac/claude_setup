# Review: main..feat/brainstorming-routes

**Status:** review of main..feat/brainstorming-routes, 2026-10-19. Mixed: the route section is sound, it matches the plan, and the rehearsal evidence holds up on a recheck. But "an architectural change" is used in the hand-off README for the no-plan case only, which goes against the definition in `my.md`, and the new risk-line timing sentence does not say how it applies to a bug.

## Change Summary

The branch replaces the `my` method's size table (Small, Medium, Large) in `global/methods/my.md` with a "Pick the route" section. The section has five routes (spike, bounded, architectural, architectural with plan, bug), a risk line, a two-file limit on bounded, and one bullet per route. It renames the sizes in `docs-layout.md`, the `my:handoff`, `my:design-system` and `my:roadmap-management` skills, the `my` README, zitamu's local file and the open roadmap rows. It adds a Spike document kind, an `answered` status, a test that `status-scan.py` treats `answered` as closed, and the renamed heading in `test_neutral_core.py`. The last commit records the code stage's rehearsal decisions in the plan.

All caller sweeps in this review were plain text searches (`grep`), because this reviewer has no symbol-reference tool.

## Plan Alignment

The implementation matches the plan task by task. I checked each of Tasks 1 to 5 against the diff and against the files on the branch head:

- The route section, the nine other `my.md` edits, Precedence (D12) and Discovery authority (D11) are as Task 1, steps 8 and 9 say (`global/methods/my.md:14-107`, `:121`, `:123`, `:129`).
- The Spike kind, the chain, the `answered` row, "Three more commits" and the four-commits sentence are as Task 2 says (`global/rules/docs-layout.md` in the diff). The test is as Task 2, step 1 says (`plugins/my/tests/test_status_scan.py:179-184`).
- The skill labels and rule 11 are word for word as Task 3 says (`plugins/my/skills/roadmap-management/SKILL.md:94`, `:122`, `:165`, `:176`).
- The README edits are as Task 4 says (`plugins/my/README.md:45-48`, `:75-95`, `:130-134`, `:146-147`, `:168-175`).
- In the roadmap, every row in Task 5, step 3's list has its expected words. Step 1's script, run again on the branch head, prints only rows 29 and 67. Row 29's "sized" sentence is kept on purpose (Task 5, step 2), and row 67's title is its own.

The deviations below were approved by the user and recorded in the plan's **Risk** section. They are not findings:

- `global/methods/my.md:23-24`: the sentence "A task that hits the risk line states its route before any skill in the table runs." This is the user's decision of 2026-10-19 (plan, Risk). The approved spec's D1 does not carry it, and the plan forbids edits under `docs/` other than the plan itself. So the spec and the rule now differ on one sentence, and only the plan records why. The `done` mark could name it.
- The rehearsal dropped the `pdf` prompt, so green is 12 runs, not 15 (plan, Risk and Testing Strategy 2). As a result the spike route is not rehearsed, which Risk lists as a known limit.
- The fixture imports a copy of `my.md` and passes its allow list through `--allowedTools` (plan, Risk).

One deviation is not recorded in the plan:

- The rehearsal checker was loosened after the red run. Task 1's commit body calls these "harness rulings": the checker accepts a route named mid-sentence next to the word "route", and it ignores a refused shell loop. Task 1, step 4 specifies a route line anchored at the start of the line, and says any denial before the judged step fails the run. The plan's Risk notes do not mention the change. See the Issues table.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | The hand-off README uses "an architectural change" for the no-plan case only. `my.md` defines the phrase as either architectural route, with or without a plan, and the spec's Goal asks for one set of names used the same way everywhere. The worst line is the one that says the supervised hand-off "for an architectural change" asks you to commit and fold the `approved` edit first. Under the definition, that also covers a change with a plan, where the plan stage commits the edit and nothing is folded by hand. The plan's Task 3, step 3 dictated the wording on line 54, but that wording conflicts with the plan's own Global Constraints. | `plugins/my/skills/handoff/README.md:54`, `:227`, `:274-276` against `global/methods/my.md:18-20` | Write "an architectural change without a plan" on all three lines, or name the route `architectural` alone, as `plugins/my/skills/handoff/SKILL.md:39` does. |
| Warning / Medium | The risk-line timing sentence and the bug rule sit side by side, and neither says which one wins. "A task that hits the risk line states its route before any skill in the table runs" is followed directly by "A bug states no route". A bug whose fix visibly touches stored data matches both. Rule 11 settles the case for roadmap rows ("even when its fix may touch the risk line"), but `my.md` does not. The `bug` rehearsal prompt does not touch the risk line, so it does not test this case. The trigger table's `my:architect` row ("change to a data model") also matches such a bug, so a session may state `architectural with plan` and go to `my:architect` instead of `systematic-debugging`. | `global/methods/my.md:23-24`, `:75-80`; `plugins/my/skills/roadmap-management/SKILL.md:176` | Add the rule 11 clause to the sentence. For example: "A task that hits the risk line, other than a bug, states its route before any skill in the table runs." Or: "A bug states no route, even when its fix may touch the risk line." |
| Suggestion / High | The plan does not record the two checker changes made after the red run. The only record is Task 1's commit body, and a squash merge may drop it. The plan's Testing Strategy is the record the `done` mark cites. I reran the current checker against both red folders, and every non-bug run still fails, so the evidence holds. But a later reader cannot see that from the plan. | Plan Task 1, step 4 (anchored route line; any earlier denial fails), against the code stage's `check.py` (`ROUTE_MID_RE`, the refused-loop skip) | Add one Risk note to the plan: what changed in the checker, and that the red runs still fail under it. Or keep the two rulings in the squash commit body. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The rehearsal shows that the rules, not the checker, make the difference | I ran the code stage's current checker on its folders. In `red` and `red2` (old `my.md`), every `quiet`, `rename`, `deleted_at` and `pdf` run fails, mostly on a size line. In `green3`, all 12 runs pass. The fixture copies in `green3` differ from `global/methods/my.md` only in line wrapping. | Strong |
| The timing sentence works as the user meant | In all three `green3/deleted_at-*.jsonl` streams, the text block "Route: architectural with plan …" comes before the `Skill` call for `my:architect`. | Strong |
| No orphaned references | Text search for the words Small, Medium and Large, "size table", "Size the process", "size not set" and "Medium change" across `global/`, `plugins/` and `projects/`. The only hits are the README's mapping (`plugins/my/README.md:93-94`), the confidence labels in the reviewer prompts and tune-claude rubric, and finished (✅) roadmap rows. No method file other than `my.md` names a size (`global/methods/tutor.md`). | Strong |
| The claims the new rules make about other tools are true | `status-scan.py:49` lists only `draft, approved, planned, current, parked` as open, and `:136` lists a matched status only when it is open. So `answered` is closed, and the new test is not vacuous: a status line that failed to parse would be listed as `no-status`. `global/git-hooks/pre-commit:8-20` refuses a doc on `main` that cites a commit that is not an ancestor of `HEAD`, which the Spike bullet relies on. No other script or hook checks status words. | Strong |
| The roadmap edits follow D9 and D10 | Task 5's step 1 script, rerun on the branch head, finds no open row with a size word except row 29 (kept on purpose) and row 67's own title. | Moderate |
| The hand-off routing does not change | `plugins/my/skills/handoff/SKILL.md:37-39` still chooses `plan` or `code` by whether the spec has a Tasks section, so specs in flight still run. | Moderate |
| zitamu gets the new local rules when the branch merges | `~/projects/zitamu/real-estate-webapp/CLAUDE.local.md` is a symlink to `projects/real-estate-webapp/claude-local.md` in the main checkout. | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Route names not used the same way everywhere | `plugins/my/skills/handoff/README.md:54`, `:227`, `:274-276` | Medium |
| The timing sentence is unclear for a bug that hits the risk line | `global/methods/my.md:23-24` | Medium |
| The rehearsal checker's changes are recorded only in a branch commit body | plan Task 1, step 4, against the code stage's `check.py` | Low |
| The spike route is not rehearsed at all (a known limit in Risk, so not a finding) | plan Risk, "The `pdf` prompt does not test the spike route" | Low |

## Not Applicable

None.

## Needs Investigation

- **How a session behaves on a bug whose fix hits the risk line.** I could not check this. No rehearsal prompt covers it, and it would need new `claude -p` runs. It matters because the timing sentence the user added pulls toward naming a route first, while the Bug route says to debug first. Either of two things would settle it: a rehearsal prompt such as "Fix: deleting a listing removes its row instead of keeping it", or the wording fix in the Issues table.

## Reasoning

The core change meets its goals: one route section, a risk line, a bug route and a spike file. It is tested by a rehearsal whose red-to-green gap I confirmed with the current checker, and the text searches find no stale references in live files. The two Warnings are wording problems at the edges, not flaws in the approach. One breaks the spec's own goal of "one set of route names, used the same way". The other leaves it unclear how two adjacent sentences in the core rule interact for a bug. Each needs a few words of fix. Because there is at least one Warning and no Critical, the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every claim the rules make about other tools was checked against the repo, and the rehearsal outputs were rechecked directly; the bug interaction is the one part I could not test.
**Recommendation:** In one fix round, change "an architectural change" to "an architectural change without a plan" in `plugins/my/skills/handoff/README.md:54`, `:227` and `:274-276`. Add the "even when its fix may touch the risk line" clause, or "other than a bug", to `global/methods/my.md:23-24`. Record the checker's two rulings in the plan's Risk section. Then squash-merge.
