# Retire the planner path and `/my:task`

## How to read this spec

| Document | Path | Why you would read it |
|---|---|---|
| **This spec** | `docs/plans/2026-09-11-retire-planner-path-spec.md` | What changes, why, and the trade-offs. Start here. |
| Superseded plan | `docs/plans/2026-05-28-single-source-planning-standards.md` | The earlier, unexecuted attempt at the same problem. This spec explains why it is obsolete rather than deferred. |
| Prompt-tuning audit | `docs/plans/2026-04-27-opus-4-7-prompt-tuning.md` | Why `planner.md` and `task.md` were written the way they are. Historical context only — its recommendations are now reversed for these two files. |
| Global instructions | `GLOBAL-CLAUDE.md` | The Superpowers Integration table and Planning Standards that this change makes self-consistent. |
| Superpowers brainstorming | `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/brainstorming/SKILL.md` | The Bounded path that replaces `/my:task`. |

**Artifact note.** `GLOBAL-CLAUDE.md` normally requires a separate spec and plan. They are collapsed into this one file on purpose: the change is 3 deletions, 1 new file, and 7 edits, all enumerated below. A second document would restate this one. Flagged here rather than done silently.

## Context

`my-plugin` and the Superpowers plugin both offer planning. Until now the split was never decided, so two contradictions accumulated.

**Contradiction 1 — planning ownership.** `GLOBAL-CLAUDE.md:20` routes multi-step implementation to `superpowers:writing-plans`. `GLOBAL-CLAUDE.md:194` names the `my:planner` agent as the canonical owner of the plan template. Both statements are live. `/my:plan` still invokes the agent.

**Contradiction 2 — duplicated standards.** The planning discipline (Critical Thinking, Mandatory Exploration, Simplicity, Trade-Off, Risk, Plan Output Format) exists twice: `GLOBAL-CLAUDE.md:123-203` for the main session, `my-plugin/agents/planner.md:14-104` for the subagent. They are hand-synced. `docs/plans/2026-05-28-single-source-planning-standards.md` diagnosed this and proposed sharing the standards through one file. It was never executed — no `shared/` directory exists, `GLOBAL-CLAUDE.md` has no `@import`, and `planner.md` still carries its full copy.

**Contradiction 3 — `/my:task` versus mandatory test-first.** `my-plugin/commands/task.md` instructs Analyze, Outline, Implement, Review. It has no test-first step. `GLOBAL-CLAUDE.md:27` lists Red → Green → Refactor as non-overridable. Its Code Quality block also bans inline comments outright, which contradicts the "match the surrounding code" rule at `GLOBAL-CLAUDE.md:65`.

## Decisions

**D1 — Retire the planner path.** Delete `/my:plan` and the `my:planner` agent. Superpowers owns planning end to end.

*Why this and not the 2026-05-28 plan.* That plan removes the duplication by **sharing** the standards between two consumers. Deleting one consumer removes the duplication outright. The duplication has been known for 3.5 months without anyone executing the fix, which is evidence the planner path is not in use. Its own Risk section flagged a hardcoded absolute path in the agent and a reliability regression. Retiring the consumer avoids building machinery to manage a file nobody invokes.

**D2 — The plan template moves to a lazy rule file.** New `GLOBAL-rules/plan-format.md` with `paths: ["**/docs/plans/*.md"]`, carrying the template lifted from `planner.md:69-97`.

*Why not inline into `GLOBAL-CLAUDE.md`.* Inlining costs ~25 lines of always-loaded context on every turn in every project, for a template that Superpowers usually overrides (`GLOBAL-CLAUDE.md:125` permits the override). The 2026-05-28 plan's Open Question 4 flagged this same tension. `GLOBAL-rules/` already proves the lazy pattern with 5 files, and `~/.claude/rules` is a directory symlink, so a new file needs no manual install step.

*Why not delete the template.* The section names alone survive at `GLOBAL-CLAUDE.md:194`, but the per-section prompts are the part that makes a plan useful to write against. Keeping them costs nothing once they load lazily.

**D3 — Delete `/my:task`.** `superpowers:brainstorming`'s Bounded path covers requirements gathering and covers it better: it explores project context first, paces questions one at a time, enforces a hard approval gate, and hands off to test-first implementation. `/my:task` does none of those four things.

## Trade-offs

**Option A — Retire the planner path (chosen).**
Pros: removes both contradictions by deletion; no new machinery; the always-loaded context does not grow; matches actual usage.
Cons: loses the one-shot "plan this without ceremony" entry point; non-Superpowers planning depends on the lazy rule firing.

**Option B — Execute the 2026-05-28 plan.**
Pros: keeps both planners; single-sources the standards properly.
Cons: builds a shared file plus a runtime-read dependency to serve an unused path; that plan's own Risk section flags a hardcoded absolute path and a reliability regression; answers four open questions that only matter if the planner survives.

**Option C — Keep both, reword the instructions.**
Pros: cheapest; nothing deleted.
Cons: duplication stays hand-synced indefinitely; the contradiction becomes documented rather than resolved.

## Files to modify

Output of a repo-wide text sweep, not memory. `docs/plans/` history is excluded by design — those documents record what was true when written.

| File | Line | Change |
|---|---|---|
| `my-plugin/commands/plan.md` | — | **Delete** |
| `my-plugin/agents/planner.md` | — | **Delete** |
| `my-plugin/commands/task.md` | — | **Delete** |
| `GLOBAL-rules/plan-format.md` | — | **Create** — `paths:` glob + template from `planner.md:69-97` |
| `GLOBAL-CLAUDE.md` | 125 | Drop `/plan` from the Planning Standards scope sentence |
| `GLOBAL-CLAUDE.md` | 194 | Repoint the template from `my:planner` to `GLOBAL-rules/plan-format.md` |
| `README.md` | 9, 14 | Remove the `/my:plan` and `/my:task` rows |
| `README.md` | 24 | Remove the `planner` agent row |
| `README.md` | 63 | Drop `/my:plan` from the `$planDirectory` sentence |
| `my-plugin/skills/tune-claude-instructions/SKILL.md` | 111, 166 | Two examples cite the deleted agent and command |
| `my-plugin/skills/tune-claude-instructions/references/grading-rubric.md` | 59 | "planner" named as a workhorse example |
| `docs/plans/2026-05-28-single-source-planning-standards.md` | top | Add a SUPERSEDED header |

The last four are prose examples, not functional dependencies. They are included so the sweep ends at zero live references.

## Dependencies

None. No new packages, no config changes, no build step. `~/.claude/rules` is an existing directory symlink to `GLOBAL-rules/`, so the new rule file distributes itself once merged to `main`.

## Risk

- **Reversibility: full.** Every deletion is recoverable from history, and the branch is preserved after squash-merge per `GLOBAL-CLAUDE.md`.
- **Blast radius: 8 live files**, from the sweep above. Everything else matching is `docs/plans/` history, left untouched.
- **What could break.** Non-Superpowers planning (built-in plan mode, inline planning) silently loses the plan template if the `paths:` glob does not fire on plan-file creation. This is the one unverified assumption in the design.
- **How to detect.** After merge to `main`, create a file under `docs/plans/` and check whether `plan-format.md` loads. If it does not, the fallback is inlining into `GLOBAL-CLAUDE.md` — a decision to bring back to the user, not to make silently.
- **Manual steps: none.**

## Testing strategy

This repository has no test runner. Markdown prompt files have no unit tests, so Red → Green → Refactor maps to checks defined before the change and confirmed after.

```bash
# Check 1 — zero live references to the deleted surfaces.
# RED before: 11 hits across 5 files. GREEN after: 0.
grep -rn -E '/my:plan|/my:task|planner' --include='*.md' --include='*.json' . \
  | grep -v '^docs/plans/' | grep -v CLAUDE.md_BAK

# Check 2 — the rule file exists and carries a valid paths glob.
# RED before: absent. GREEN after: present.
test -f GLOBAL-rules/plan-format.md && head -5 GLOBAL-rules/plan-format.md

# Check 3 — the deleted files are gone.
! test -e my-plugin/commands/plan.md && \
! test -e my-plugin/agents/planner.md && \
! test -e my-plugin/commands/task.md && echo "deletions confirmed"
```

**Check 4 is behavioural and cannot run before merge.** `~/.claude/rules` resolves to the main checkout's `GLOBAL-rules/`, not this worktree, so the lazy rule is not live until the branch lands on `main`. Run it after merge; report the result either way.

## Out of scope

- `my-plugin/agents/summarizer.md` writes `$planDirectory/{name}-plan.md`, which contradicts the `YYYY-MM-DD-<slug>.md` convention in `GLOBAL-CLAUDE.md`. Pre-existing and unrelated. Worth its own fix.
- `my-plugin/skills/clean-plans/SKILL.md` discovers from `docs/superpowers/plans/` and `docs/superpowers/specs/`, paths that `GLOBAL-CLAUDE.md` overrides to `docs/plans/`. A separate bug fix.
- `my-plugin/skills/tune-claude-instructions/` is scoped to "Opus 4.7+" and does not teach the subagent tool-filtering lesson from commit `2c459be`. A separate content refresh.
- `my-plugin/.claude-plugin/plugin.json` describes the plugin as "commands and agents", omitting 9 skills and a hook. Part of the same later docs pass.

## Open questions

None blocking. The single unverified assumption (does the `paths:` glob fire on file creation) has a defined test and a defined fallback, both recorded under Risk.
