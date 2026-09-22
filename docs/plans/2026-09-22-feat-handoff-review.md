# Review: main..feat/handoff

**Status:** review of main..feat/handoff, 2026-09-22. Sound: the skill follows the approved spec step by step, and the top finding is a small gap: the new `GLOBAL-CLAUDE.md` line does not tell the spec session to leave its `approved` edit uncommitted, as spec D9 says. Answered in 88afd8a.

## Change Summary

The range adds `my-plugin/skills/handoff/SKILL.md`, a skill with two forms: a launch form, which opens the plan or code stage in a new tmux window as a named top-level `claude` session, and a run form, which runs that stage with start checks, fixed gates and a "signal" (window mark, `PushNotification`, last output line). It adds a row for the skill to `README.md` and `ROADMAP.md`, and one sentence to step 3 of the Spec → Plan flow in `GLOBAL-CLAUDE.md` that offers the handoff. It also edits the implementation plan so the launch test accepts the trust dialog in the fixture repo.

## Plan Alignment

The implementation matches the spec (`docs/plans/2026-09-21-handoff-spec.md`) closely. It also matches the implementation plan (`docs/plans/2026-09-21-handoff.md`, Task 3 steps 2 to 4): the README, ROADMAP and `GLOBAL-CLAUDE.md` text is the same as the plan's text, word for word. Every spec decision has a matching section in the skill:

- D4 signal: `my-plugin/skills/handoff/SKILL.md:37-51` (mark only when `$TMUX_PANE` is set, `-t` always passed, no retry of `PushNotification`).
- D5 forms and slug: `SKILL.md:20-35`.
- D7 launch: `SKILL.md:53-90`. The spec's mode refusal (D7 step 3) and no-tmux fallback (D7 step 4) are merged into one "Fallback" step at `SKILL.md:72-80`, and a quote-character guard was added at `SKILL.md:69-70`. The behaviour does not change; the guard is an addition, not a deviation.
- D8 start checks: `SKILL.md:94-114`. The spec's checks become concrete commands (anchored `ls` glob, `git log`/`git status` on `main`, `git branch --list '*/<slug>'`).
- D9 stages: `SKILL.md:116-155`. D10 rules: `SKILL.md:157-162`.

Deviations:

- `GLOBAL-CLAUDE.md:46`: spec D9 ("Spec stage") says the spec session sets the status to `approved` **and leaves that edit uncommitted** for plan stage step 2. The new line only says "set its status to `approved`". The start check at `SKILL.md:102-103` accepts either case, so nothing breaks. But a spec session that follows its usual commit habit will make a status-only commit, which D9 was written to avoid.
- `ROADMAP.md:60`: the row is marked ✅ on the branch before the merge and has no commit hash. The sibling row at `ROADMAP.md:55` names its commit (`Shipped in 3d9a7f9`). The plan's Task 4 step 3 updates only the spec and plan statuses after the merge, not this row. The ✅ reaches `main` in the squash commit itself, so the timing is acceptable.
- Spec Dependencies lists `superpowers:using-git-worktrees`, and the skill never names it (`SKILL.md:141-145` uses raw `git worktree add`). I checked the superpowers skill (`using-git-worktrees/SKILL.md:67`, `:166`): an explicit path in the instructions beats its default, so the two agree. No finding.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | The global handoff line leaves out spec D9's "leave the `approved` edit uncommitted", so the spec session may make a status-only commit. | `GLOBAL-CLAUDE.md:46`; spec D9 "Spec stage"; `my-plugin/skills/handoff/SKILL.md:102-103`, `:122-124` | Add "and leave that edit uncommitted; the plan stage commits it" after "set its status to `approved`". |
| Suggestion / High | The ✅ ROADMAP row has no commit hash, unlike its sibling, and no plan step adds one after the merge. | `ROADMAP.md:60`; sibling `ROADMAP.md:55`; `docs/plans/2026-09-21-handoff.md` Task 4 step 3 | In Task 4 step 3, also add `Shipped in <squash commit>` to the row. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Faithful to the approved spec: every decision D4 to D10 has a matching section, and the added text only makes the spec's checks concrete | `my-plugin/skills/handoff/SKILL.md:37-162` | Strong |
| Fits the sibling skill layout (frontmatter with a "NOT for" clause, numbered steps, exact usage string) | `my-plugin/skills/spec-review/SKILL.md:1-32` vs `SKILL.md:1-31` | Strong |
| Safety defaults fail closed: refuses to open a window unless the mode is `auto`/`bypassPermissions`, refuses a duplicate name, refuses quotes, and start checks write nothing on failure | `SKILL.md:58-80`, `:96-98` | Strong |
| The plan-stage clean-tree check lines up with soundness-review's real rule that a `.md` plan plus a dirty tree asks a question | `SKILL.md:125-126`; `my-plugin/skills/soundness-review/SKILL.md:109` | Strong |
| No project names in the skill (D6); project rules are left to the top-level session's own `CLAUDE.md` | `SKILL.md:122-124`, `:147-155` | Moderate |
| No symbol removed or renamed; the only cross-file token is `my:handoff`, and every reference is new | text search `grep -rn handoff` over the repo (no symbol tool was available) | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The global line does not carry D9's "leave uncommitted" instruction | `GLOBAL-CLAUDE.md:46` | Low |
| The behaviour depends on tools and harness facts that no unit test can check (`CLAUDE_PID`, the mode being visible in context, `ListAgents` names); only the planned pilot exercises the full chain | `SKILL.md:58-66`; plan "Facts checked by probes" | Low |
| The ROADMAP row lacks the commit-hash convention | `ROADMAP.md:60` | Low |

## Not Applicable

None.

## Needs Investigation

- **The full plan → code chain has not run end to end.** The launch path from a plan-stage session (the `auto` mode inherited through `--permission-mode`, `$TMUX` inherited in the new window, `$CLAUDE_PID` of the nested session) rests on probes from 2026-09-21 and on the Task 2 launch test. It does not rest on a run of a real plan stage. This matters because a wrong fact in that chain leaves a window waiting unseen. The spec's pilot (Testing strategy item 4) settles it.

## Reasoning

The change solves the stated problem as the spec defines it. It follows the existing skill layout, and it adds no abstraction, script or dependency. The gates and refusals fail closed. The payload removes or renames nothing, so there is no orphaned caller. Callers were checked with a text search only, because no symbol tool was available. The two findings are small documentation gaps next to the skill, not flaws in the approach. Neither passes the Warning bar.

## Verdict

**Assessment:** Sound
**Confidence:** Medium — the text matches the spec and the repo conventions, but the runtime chain through tmux and the harness is proven only by probes, not by a real stage run.
**Recommendation:** Add the "leave uncommitted" clause to `GLOBAL-CLAUDE.md:46`, add the commit hash to the ROADMAP row in plan Task 4 step 3, then integrate and run the pilot.
