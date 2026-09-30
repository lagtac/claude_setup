# Review: docs/plans/2026-09-30-soundness-plan-only-spec.md

**Status:** review of docs/plans/2026-09-30-soundness-plan-only-spec.md, 2026-09-30. Mixed: the approach (an explicit token plus one commit before review) is right, but the new plan stage still needs a clean `main` whenever spec-stage `fixup!` commits are pending, so the Goal is not met in that case. The spec's answers on 2026-09-30 (D2, D4 steps 5 to 8, D5, Risk) answered it.

## Spec Summary

The spec adds a `--plan-only` token to `my:soundness-review`. The token makes the skill review a plan document without capturing a diff, so it never asks what to review. It also reorders the `my:handoff` plan stage to review before committing and to commit the plan, its review, the spec's `approved` edit and any index row in one path-limited commit. That lets the stage finish while other sessions have uncommitted files on `main`.

## System Model

The caller sweep was text-only (`grep -rln`); no symbol-reference tool was available.

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `--plan-only` token class (soundness-review step 0) | the `PLAN_ONLY` flag; the D3 mixed-argument stops | step 0 classifier | New, added to existing `plugins/my/skills/soundness-review/SKILL.md:27-44` |
| soundness-review step 1 (diff capture) | `WORK_DIR`, `PAYLOAD`, untracked-file note, size guard | git working tree | Existing `plugins/my/skills/soundness-review/SKILL.md:46-98` |
| soundness-review step 1a (mode table and question) | `MODE`; the `AskUserQuestion` question; the headless fallback | step 0 variables, payload | Existing `plugins/my/skills/soundness-review/SKILL.md:100-131` |
| soundness-review step 2 (prompt build) | plan snapshot `$WORK_DIR/plan.md`, review slug, collision rule | `WORK_DIR`, `MODE` | Existing `plugins/my/skills/soundness-review/SKILL.md:133-165` |
| handoff plan stage | order of write, review, fix, commit; gate list; the single commit's path list | writing-plans, soundness-review, project docs rules, git | Existing `plugins/my/skills/handoff/SKILL.md:150-177` |
| handoff start checks | "no plan exists yet" check | file system | Existing `plugins/my/skills/handoff/SKILL.md:118-124` |
| handoff spec D9 and Risk | the recorded design of the plan stage | — | Existing `docs/plans/2026-09-21-handoff-spec.md:267-285`, `:385-389` |
| Docs that name the arguments | user-facing descriptions | the two skills | Existing `global/CLAUDE.md:58`, `README.md:65`, `plugins/my/skills/handoff/README.md:93-100`, `ROADMAP.md:66-67` |
| Project docs steps (Git Workflow 1 to 9) | fixup folding, which needs a clean checkout | git rebase | Existing `global/CLAUDE.md` "One feature, four commits on `main`", step 9 |

| From → To | What passes | Owner of what passes |
|---|---|---|
| handoff plan stage → soundness-review | args `--plan-only <plan path>` | handoff plan stage |
| soundness-review step 0 → step 1 / 1a | `PLAN_ONLY`, `PLAN_PATH`, `DESCRIPTION`, `RANGE` | step 0 |
| soundness-review step 1 → step 2 | `WORK_DIR` (needed by the plan-review `cp`) | step 1 (today) — unowned under D2 |
| soundness-review → handoff plan stage | the review file `docs/plans/<plan>-plan-review.md` | soundness-review |
| handoff plan stage → git | `git add -- <paths>`, `git commit -- <paths>` | handoff plan stage |
| handoff plan stage → project docs steps | "finish the project's other docs steps" (may include a fixup rebase) | project rules |
| spec stage → plan stage | the uncommitted `approved` edit; possibly pending `fixup!` commits on the spec | spec stage (user's session) |

## Grounding

All checked references hold. Checked: the step 0/1/1a structure and the existing messages (`plugins/my/skills/soundness-review/SKILL.md:40-42,107-108,129`); the current plan stage steps 3 and 4 and the stop message (`plugins/my/skills/handoff/SKILL.md:162-167`); the handoff spec's D9 and the Risk item "A busy `main` stops the plan stage" (`docs/plans/2026-09-21-handoff-spec.md:267-285,385-389`); the "(Changed 2026-09-29, see D2.)" style (`docs/plans/2026-09-21-handoff-spec.md:296`); the ROADMAP 💭 follow-up (`ROADMAP.md:66-67`); the "no plan exists yet" start check (`plugins/my/skills/handoff/SKILL.md:120-124`); `superpowers:writing-plans` only saves the plan and does not commit it (`~/.claude/plugins/cache/claude-plugins-official/superpowers/6.4.1/skills/writing-plans/SKILL.md:18,177`); the blast-radius count of 11 files outside `docs/` (`grep -rln "soundness-review" --include=*.md`, matches the spec's list).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | The Goal ("finishes without stopping" on a busy `main`) fails when the spec has pending `fixup!` commits. New step 7 still runs "the project's other docs steps", and Git Workflow step 9 folds fixups with a rebase that needs a clean checkout. D4 says only that the plan stage's own commits need no rebase. The spec does not say whether the fold is skipped, deferred, or a stop. | `spec §Goal ↔ §D4` step 7; `global/CLAUDE.md:128` ("The rebase needs a clean main checkout"); `plugins/my/skills/handoff/SKILL.md:176` ("for example a rebase of fixups") | Decision for the author: for example, defer the fold when the tree is dirty and name the pending fixups in the finish line, or make it a gate and list it as a known limit in Risk. |
| Warning / High | design | D4 renumbers the plan stage, which leaves two references pointing at the wrong step. The review stage says "apply the test in Plan stage, step 6"; under D4 the finding test is step 4 and step 6 is the commit. The handoff spec's spec-stage text says "plan stage step 2 commits it"; under the amended D9 the commit is step 6. The first fix edits the review stage, which §Out of scope and §Risk say is unchanged. | `spec §D4 ↔ §Out of scope`; `plugins/my/skills/handoff/SKILL.md:265`; `docs/plans/2026-09-21-handoff-spec.md:262` | Decision for the author: allow a cross-reference edit in the review stage and say so in Out of scope, or keep the old step numbers for the finding test. Also list the D9 spec-stage line under D5. |
| Warning / High | editorial | D2 says step 1 "does not run". Step 1 is where `WORK_DIR` is created, and the plan-review branch of step 2 copies the plan to `$WORK_DIR/plan.md`. Read literally, `--plan-only` has no work directory. The only sensible reading is: create `WORK_DIR`, skip the payload and the untracked-file note. | `spec §D2` ↔ `plugins/my/skills/soundness-review/SKILL.md:50-55,142` | Say that with `PLAN_ONLY` only the `WORK_DIR` block of step 1 runs; the payload capture, untracked note and size guard are skipped. |
| Warning / Medium | design | The new gate list is narrower than today's. Old step 7 named three gates: a decision-changing finding, a spec decision resting on a false premise, and a failed pre-rebase check. New steps 4 and 5 define a gate only by the finding test. Whether the other two gates are dropped on purpose is not stated. | `spec §D4` steps 4-5 ↔ `plugins/my/skills/handoff/SKILL.md:173-175` | Decision for the author: keep the false-premise gate (it enforces the global "No silent reinterpretation" rule), and keep or drop the pre-rebase check together with the fix for the finding above. |
| Warning / Medium | design | `git commit -- <paths>` commits the whole working-tree content of each path. If another session has uncommitted hunks in a shared file on the list (the plans index, or `ROADMAP.md` when a project uses it as its index), those hunks go into this commit. D4 claims the commit holds "only the plan stage's own files", but it holds only their paths. | `spec §D4` step 6 ↔ `§Goal`; `spec §Risk` covers `git add -A` by others but not this case | Name it in Risk as a known limit, or have the stage check `git diff -- <index path>` before the commit and gate when it holds lines it did not write. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Fit with what exists | The fix is the one the handoff spec already names (`docs/plans/2026-09-21-handoff-spec.md:385-389`), and D1's rejected option (changing the default) is a real alternative with a stated cost: it silently breaks the documented question in `global/CLAUDE.md:58`. | Strong |
| Contracts and flow | D3 gives a first-match order for every mixed-argument case and reuses the existing messages (`plugins/my/skills/soundness-review/SKILL.md:107-108`), so there is no new wording to drift. | Strong |
| Boundaries | `--plan-only` lives entirely in step 0 and bypasses step 1a's question, so behavior without the token is unchanged (spec §Out of scope; test 3). | Strong |
| Contracts and flow | Reviewing before committing removes the plan/review split, which matches Git Workflow steps 5 to 7 and removes the plan stage's own fixup. | Moderate |
| Failures and interactions | Risk names the stranded uncommitted files after a gate, the `git add -A` sweep by another session, and the rerun hitting the start check (`plugins/my/skills/handoff/SKILL.md:120-124`). | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Failures and interactions | Pending spec fixups still force a rebase on a dirty `main` (first Issues row). | Medium |
| Contracts and flow | The step renumbering leaves the review stage and the handoff spec pointing at the wrong plan-stage steps (second Issues row). | Medium |
| Contracts and flow | The gate list shrinks without a stated reason (fourth Issues row). | Medium |
| Failures and interactions | A shared file on the commit's path list can carry another session's hunks (fifth Issues row). | Medium |
| Spec rules | D2's "step 1 does not run" leaves `WORK_DIR` unowned (third Issues row). | Low |

## Not Applicable

None.

## Needs Investigation

- **Whether spec-stage fixups are common in practice.** The first finding matters only when the spec commit has pending `fixup!` commits at the time the plan stage runs. `git log --oneline` on `main` after recent handoffs would show how often a `fixup!` survives to the plan stage. If it never happens because the spec session always folds before handing off, the fix is one Risk line.

## Reasoning

The System Model shows a clean split: the token owns the "never ask" decision, and the plan stage owns the one commit. Criteria 1, 4 and 6 pass. Criterion 2 has one stale cross-reference that the renumbering creates. Criterion 3 does not fully pass: the plan stage still hands off to "the project's other docs steps", which can include a rebase that needs a clean tree, and its path-limited commit can take in shared-file hunks. Neither problem undoes the approach, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every repo reference was opened, and the open problems are clear gaps between the Goal and D4.
**Recommendation:** Fix the `WORK_DIR` wording in D2. Ask the user about four things: how the plan stage handles pending spec fixups on a dirty `main`, whether the review stage may get a cross-reference edit after the renumbering, which gates stay in the new step list, and whether the shared-file case goes into Risk or becomes a check. Then approve.
