### Spec Summary

The spec deletes `/my:plan`, the `my:planner` agent and `/my:task`, so that Superpowers owns planning and requirements gathering. The plan template moves from `planner.md` into a new path-scoped rule, `GLOBAL-rules/plan-format.md` (`paths: ["**/docs/plans/*.md"]`). `GLOBAL-CLAUDE.md`, `README.md`, the `tune-claude-instructions` skill and the superseded 2026-05-28 plan are edited so that no live references remain. The spec and plan are deliberately merged into one file.

Review note: the spec was already carried out in commit `d853dbe`, and that commit is on `main`. I checked claims about the before state with `git show d853dbe^:<path>`. The reference sweep was text-only (`git grep` / `grep -rn`). I did not use `LSP`: it was not loaded, and every symbol involved is a Markdown or file name, which a language server would not index anyway.

### System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `/my:plan` command (deleted) | Entry point that dispatches the planner subagent | `my:planner` | Existing `d853dbe^:my-plugin/commands/plan.md:5` |
| `my:planner` agent (deleted) | A self-contained copy of the planning rules; the canonical plan template | Nothing (self-contained) | Existing `d853dbe^:my-plugin/agents/planner.md:14-103`, template `:69-97` |
| `/my:task` command (deleted) | Its own requirements-gathering and implementation routine, plus Code Quality rules | Nothing | Existing `d853dbe^:my-plugin/commands/task.md` |
| `GLOBAL-rules/plan-format.md` | The plan template with per-section prompts, and output rules | The Claude Code path-scoped rule loader; the `~/.claude/rules` symlink | New, `GLOBAL-rules/plan-format.md:1-4` |
| `GLOBAL-CLAUDE.md` Planning Standards | The planning rules (the only copy left); a pointer to where the template lives | `plan-format.md` (by reference) | Existing `d853dbe^:GLOBAL-CLAUDE.md:123-201`, pointer `:194` |
| Superpowers `brainstorming` / `writing-plans` | Requirements gathering (Bounded path) and plan writing | Superpowers plugin 6.3.0 | Existing `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/brainstorming/SKILL.md:87-92` |
| `~/.claude/rules` symlink | How rules reach every project | The main checkout's `GLOBAL-rules/` | Existing, `readlink` resolves to `/home/dchris/projects/claude-setup/GLOBAL-rules` |
| README, `tune-claude-instructions` examples, superseded-plan header | Prose that names the deleted parts | Nothing at runtime | Existing `d853dbe^:README.md:9,14,24,63`; `SKILL.md:111,166`; `grading-rubric.md:59` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| `/my:plan` → `my:planner` (removed) | A subagent dispatch carrying `$ARGUMENTS` | `/my:plan` |
| `GLOBAL-CLAUDE.md:194` → `my:planner` (removed) → `plan-format.md` (new) | A prose pointer to the canonical template | `GLOBAL-CLAUDE.md` |
| The loader → `plan-format.md` → the session | Rule text, loaded when a file matching `**/docs/plans/*.md` is touched | Claude Code runtime (the trigger); `plan-format.md` (the content) |
| `~/.claude/rules` → `GLOBAL-rules/` | The directory symlink (rule files reach sessions only from the main checkout) | The file system / the main checkout |
| `superpowers:brainstorming` → implementation | Approved design, then TDD (Bounded path, "no plan document") | Superpowers |
| Superpowers `writing-plans` format ↔ `plan-format.md` | Two competing plan formats. The conflict is settled by "Superpowers may override" (`GLOBAL-CLAUDE.md:27,125`) | `GLOBAL-CLAUDE.md` (the precedence rule) |

### Grounding

- spec §Context (Contradiction 1) cites `GLOBAL-CLAUDE.md:20` for the `writing-plans` routing ↔ it is at `d853dbe^:GLOBAL-CLAUDE.md:17`. Line 20 is the `using-git-worktrees` row.
- spec §Context (Contradiction 3) cites `GLOBAL-CLAUDE.md:65` for "match the surrounding code" ↔ it is at `d853dbe^:GLOBAL-CLAUDE.md:83`. Line 65 is in the UI Design section.
- spec §Context (Contradiction 2) cites `planner.md:14-104` ↔ the file has 103 lines (`d853dbe^:my-plugin/agents/planner.md`), and the shared rules end at line 58. Lines 60-103 are Execution, the template and Output Discipline.
- All other checked references hold: `GLOBAL-CLAUDE.md:27` (Red → Green → Refactor, non-overridable), `:125` (`/plan` and the Superpowers override), `:194` (the `my:planner` pointer); template at `planner.md:69-97`; `README.md:9,14,24,63`; `SKILL.md:111,166`; `grading-rubric.md:59`; 5 existing files in `GLOBAL-rules/`; the `~/.claude/rules` directory symlink; the 2026-05-28 plan's Risk entries (`:114` reliability regression, `:122` hardcoded absolute path) and Open Question 4 (`:157`); the four Bounded-path claims (`brainstorming/SKILL.md:88-92`); `/my:task` has no test-first step and bans inline comments.
- Sweep check: a text search of the before state, excluding `docs/plans/`, found no live reference outside the spec's table. A sweep of the after state found no live reference except `ROADMAP.md:34-39`, which is a record of the change. A search under `~/.claude` (plugin cache excluded) found no reference.

### Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / Medium | design | The one flagged assumption ("does the `paths:` glob fire on plan-file *creation*") already has contrary evidence in the repo. The repo's own note says path rules "load only when Claude reads a matching file type". A new plan is written, not read, so the template may be missing when the first draft is written, which is exactly when it is needed. The spec treats this as an open unknown with a fallback to check after merge, and does not cite this note. | `d853dbe^:GLOBAL-CLAUDE.md:198-200` (now `GLOBAL-CLAUDE.md:200`) ↔ spec §Risk "What could break" | Decision for the author. Run Check 4 now (the commit is on `main`) and record the result. If it fails on creation, choose between the inline fallback and accepting a template that only appears on edit. |
| Warning / Medium | design | The glob `**/docs/plans/*.md` matches every file in `docs/plans/`, not just plans. Specs (`-spec.md`), reviews and designs live there too. So "Every section is required" plan text loads while a spec or review is being written, and it may push those files toward the plan layout. The spec does not discuss this. | `GLOBAL-CLAUDE.md:5` (all specs, plans and reviews go to `docs/plans/`), `:35` (`-spec.md` naming); `GLOBAL-rules/plan-format.md:1-4,8` | Decision for the author. Either narrow the rule text ("applies to implementation plans, not `-spec.md` or review files") or accept the overlap and say so in the spec. |
| Warning / Medium | design | The spec says trigger-on-creation is unverified, but the carried-out edit states it as fact in always-loaded instructions: "loads automatically when a `docs/plans/*.md` file is touched". The repo has no record that Check 4 ran, even though the spec says "report the result either way". | `GLOBAL-CLAUDE.md:195`; spec §Testing strategy (Check 4); a search for `Check 4` / `plan-format` found only `ROADMAP.md:40`, the superseded header and `GLOBAL-CLAUDE.md:195` | Record the Check 4 result. Until it passes, word `GLOBAL-CLAUDE.md:195` so it does not claim that loading is guaranteed. |
| Suggestion / High | editorial | Three stale line citations in §Context (`:20` should be `:17`; `:65` should be `:83`; `planner.md:14-104` should be `:14-58`, file is 103 lines). | See §Grounding | Correct the numbers. |
| Suggestion / High | editorial | "How to read this spec" leaves out `ROADMAP.md`, which the spec rule lists as a related document. The carried-out change added a ROADMAP section that links back to this spec and holds the §Out of scope follow-ups. The spec's file table does not list `ROADMAP.md` either. | `GLOBAL-CLAUDE.md:35`; `d853dbe` diff of `ROADMAP.md` (+23 lines); spec §How to read this spec, §Files to modify | Add `ROADMAP.md` to both tables. |
| Suggestion / High | editorial | The change counts do not match. The artifact note says "7 edits", but the file table has 8 edit rows across 5 files, and §Risk says "8 live files". | spec §How to read this spec (Artifact note) ↔ §Files to modify ↔ §Risk | State one count with a unit (files or rows). |

### Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | Before the change, two components owned the planning rules and the template (`d853dbe^:GLOBAL-CLAUDE.md:123-201`, `d853dbe^:my-plugin/agents/planner.md:14-97`). Afterwards `GLOBAL-CLAUDE.md` owns the rules and `plan-format.md` owns the template, one owner each. `/my:plan` was a one-line pass-through (`plan.md:5`), so removing it removes a component that only forwarded calls. | Strong |
| Contracts and flow | The contradictory pointer (`GLOBAL-CLAUDE.md:194` → `my:planner` while `:17` routes to `writing-plans`) is replaced by a single pointer. The Superpowers-versus-template precedence is already written down (`:27`, `:125`). | Moderate |
| Failures and interactions | The spec names the one runtime dependency (the rule loader), the symptom (the template is silently missing), a detection step (Check 4) and a fallback that goes back to the user (spec §Risk). All deletions can be restored from git. | Moderate |
| Fit with what exists | It reuses the existing lazy-rule pattern: 5 files in `GLOBAL-rules/` with `paths:` frontmatter, reached through the `~/.claude/rules` symlink. The rejected Option B was a real, written plan whose own Risk section records the costs cited (`2026-05-28-...md:114,122,157`). The D3 claims about the Bounded path hold (`brainstorming/SKILL.md:88-92`), and `/my:task` really lacks test-first. | Strong |
| Grounding | Almost every file, line and behaviour claim checks out. The sweep is complete: no missed live references before or after the change. | Strong |
| Spec rules | The spec opens with "How to read this spec". It has Trade-offs, Dependencies and Risk sections. It openly flags that spec and plan were merged instead of doing it silently. No UI is involved, so a Visual Language section is correctly absent. | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Failures and interactions | The loader trigger (read versus write) is the only runtime link. The repo's own note suggests it fires on read (`GLOBAL-CLAUDE.md:200`). The glob also covers specs and reviews (`GLOBAL-CLAUDE.md:5`). Neither interaction is analysed. | Medium |
| Contracts and flow | The carried-out text claims that loading is guaranteed (`GLOBAL-CLAUDE.md:195`), but the spec calls it unverified, and no Check 4 result is recorded. | Medium |
| Fit with what exists | D1's evidence that the planner path is unused is indirect: an unexecuted plan sitting 3.5 months, not actual usage data (spec §D1). The conclusion is probably right, given the routing at `GLOBAL-CLAUDE.md:17`, but the reasoning is weaker than the wording suggests. | Low |
| Grounding | Three stale line citations (see §Grounding). | Low |
| Spec rules | `ROADMAP.md` is missing from the reading list and the file table. The edit counts do not match. Merging spec and plan goes against `GLOBAL-CLAUDE.md:30-37`, though it is flagged. | Low |
| Boundaries | N/A for any further problem: every remaining component has one owner. | — |

### Needs Investigation

- **Was Check 4 run after merge, and what did it show?** `d853dbe` is on `main`, so the rule is live. It matters because the only functional replacement for the planner's template depends on it. To resolve it, create a new file under `docs/plans/` in a fresh session (Write only, no prior Read). Check whether `plan-format.md` shows in `/memory` or loaded context, then repeat with a Read, and record both results.
- **Do user-level `~/.claude/rules` path globs match against the project-relative path?** The `**/` prefix probably makes this safe, but I could not confirm it from the repo. It matters for the same reason. The Check 4 run above settles it.

### Reasoning

The System Model shows a clean simplification. Duplicate ownership of the planning rules and template becomes single ownership, and the one pass-through component goes away. The grounding and the sweep hold up, apart from a few cosmetic slips. The weak spot is the single new runtime link, the path-scoped rule loader. The repo's own note suggests it fires on read rather than on write. Its glob covers specs and reviews as well as plans. And the carried-out wording states as fact something the spec calls unverified. None of these undermine the decision to retire the planner path. They all bear on whether the template replacement actually works.

### Verdict

**Assessment:** Mixed
**Confidence:** Medium. The retirement decision is well grounded, but the replacement template's loading behaviour is unverified and there is contrary evidence in the repo.
**Recommendation:** Keep the retirement. Run and record Check 4 now (Write-only and Read cases). Soften `GLOBAL-CLAUDE.md:195` or add a scope line to `plan-format.md` depending on the result. Fix the three stale line citations and add `ROADMAP.md` to the spec's reading list.
