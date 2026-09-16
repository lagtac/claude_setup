### Spec Summary

The spec deletes `/my:plan`, the `my:planner` agent and `/my:task`, leaving Superpowers as the only planning path. It moves the per-section plan template out of `planner.md` into a new lazy-loaded rule, `GLOBAL-rules/plan-format.md`, scoped to `**/docs/plans/*.md`. It also repoints `GLOBAL-CLAUDE.md`, clears prose references in `README.md` and the `tune-claude-instructions` skill, and marks the 2026-05-28 single-source plan as superseded.

Review note: the spec has already been carried out in commit `d853dbe`. Grounding was checked against the state before that commit (`git show d853dbe~1:<file>`), because the spec's line numbers describe that state. The new rule file was checked in the current tree.

### System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `/my:plan` command (deleted) | One-line dispatch to the planner agent | `my:planner` | Existing `d853dbe~1:my-plugin/commands/plan.md:5` |
| `my:planner` agent (deleted) | A copy of the planning discipline and the canonical plan template | `$planDirectory` | Existing `d853dbe~1:my-plugin/agents/planner.md:14-103` (template at 69-97) |
| `/my:task` command (deleted) | Analyze/Outline/Implement/Review flow, its own code-quality rules | none | Existing `d853dbe~1:my-plugin/commands/task.md` |
| `GLOBAL-rules/plan-format.md` | The plan template, the per-section prompts and the output rules | `~/.claude/rules` symlink; Claude Code firing path-scoped rules | New, now at `GLOBAL-rules/plan-format.md:1-4` |
| `GLOBAL-CLAUDE.md` Planning Standards | The planning discipline (now the only copy), the section-name list, the pointer to the template | `plan-format.md` | Existing `d853dbe~1:GLOBAL-CLAUDE.md:123-194` |
| `~/.claude/rules` symlink | Delivering the rules | The main checkout of `GLOBAL-rules/` | Existing `/home/dchris/.claude/rules -> /home/dchris/projects/claude-setup/GLOBAL-rules` |
| Superpowers brainstorming (Bounded path) | Requirements gathering and the approval gate for small changes | External plugin | Existing `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/brainstorming/SKILL.md:35-44,87-92` |
| Superpowers writing-plans | Writing the plan | External plugin | Existing (routed at `d853dbe~1:GLOBAL-CLAUDE.md:17`) |
| Prose consumers (README, tune-claude-instructions SKILL and rubric) | Documentation that mentions the deleted files | none | Existing `d853dbe~1:README.md:9,14,24,63`; `SKILL.md:111,166`; `grading-rubric.md:59` |
| 2026-05-28 plan | A record of the rejected Option B | none | Existing `docs/plans/2026-05-28-single-source-planning-standards.md` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| `GLOBAL-CLAUDE.md:194` → `plan-format.md` | A text pointer: "the full template lives here" | `GLOBAL-CLAUDE.md` |
| Claude Code rule loader → session context | `plan-format.md` content, when a file matching `**/docs/plans/*.md` is touched | Claude Code runtime (outside the repo) |
| `GLOBAL-rules/` in the main checkout → `~/.claude/rules` | Rule files, through the symlink | Main checkout |
| Superpowers table (`GLOBAL-CLAUDE.md:16-17`) → brainstorming → writing-plans | Control flow: feature work, then spec, then plan | Superpowers |
| Built-in plan mode → `~/.claude/plans/` → `docs/plans/` | Scratch plan, copied to a durable plan on exit | Main session (per GLOBAL-CLAUDE Spec → Plan flow) |

### Grounding

- `spec §Context` (Contradiction 1) cites `GLOBAL-CLAUDE.md:20` for routing to `superpowers:writing-plans`. At `d853dbe~1:GLOBAL-CLAUDE.md:20` the row is `using-git-worktrees`. The writing-plans row is at line 17.
- `spec §Context` (Contradiction 3) cites `GLOBAL-CLAUDE.md:65` for "match the surrounding code". Line 65 is in the UI Design section. The rule is at `d853dbe~1:GLOBAL-CLAUDE.md:83`.
- `spec §Testing strategy` says "11 hits across 5 files". Running the same pattern with `git grep` at `d853dbe~1` (without `docs/plans`) gives 11 hits across **6** files: GLOBAL-CLAUDE.md 1, README.md 4, planner.md 2, plan.md 1, SKILL.md 2, grading-rubric.md 1.
- `spec §How to read this spec` says "3 deletions, 1 new file, and 7 edits". `spec §Files to modify` has 8 edit rows across 5 files.
- `spec §Files to modify` says "The last four are prose examples". The last four rows include the SUPERSEDED header on the 2026-05-28 plan, which is not a prose example.
- Every other claim checked holds. Checked: `planner.md:69-97` holds the template. `GLOBAL-CLAUDE.md:27`, `:123-203`, `:125` and `:194` say what the spec says. `GLOBAL-rules/` had 5 files. `~/.claude/rules` is a directory symlink into the main checkout. `task.md` has no test-first step and bans inline comments. The 2026-05-28 plan never ran (no `shared/` directory). Its Risk section names a hardcoded absolute path and a reliability regression (`:114`, `:122`), and its Open Question 4 is the ~25-line context concern. The Bounded path matches all four claims in D3 (`brainstorming/SKILL.md:88-92`). Dropping `/plan` from `:125` is correct: the author uses bare `/plan` to mean the planner dispatcher elsewhere (`d853dbe~1:my-plugin/skills/tune-claude-instructions/SKILL.md:166`). The out-of-scope facts hold: `summarizer.md:34`, `clean-plans/SKILL.md:21-22`, `plugin.json` description, 9 skills before this branch, one hook. The sweep was text-only (`git grep` plus `grep -rn` across `/home/dchris/projects`). `LSP` was not used because the subjects are Markdown prompt files. No other repo references `/my:plan`, `/my:task` or `my:planner`.

### Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / Medium | design | The template loads only after a matching file is touched, so it arrives too late to shape a plan's first draft. Built-in plan mode drafts in `~/.claude/plans/`, which the glob never matches. For non-Superpowers planning, the template is effectively lost until a revision pass. The spec's Risk section only asks whether the rule fires on creation. It does not ask whether firing after the file is written is early enough. | `GLOBAL-rules/plan-format.md:2-3`; GLOBAL-CLAUDE Spec → Plan flow (plan mode scratch in `~/.claude/plans/`); `spec §Risk` | Decision for the author. Accept a revise-after-first-write loop, add a GLOBAL-CLAUDE line telling the model to Read `plan-format.md` before drafting a plan, or inline the section prompts. Record whichever is chosen under Risk. |
| Warning / Medium | design | The glob `**/docs/plans/*.md` also matches specs (`*-spec.md`) and reviews (`*-review*.md`). 11 such files exist today. The rule says "Every section is required", so writing a spec or review could pull in plan sections (Step-by-Step, Files to Modify). That goes against the two-artifact flow, which keeps specs product-level. | `GLOBAL-rules/plan-format.md:1-9`; `ls docs/plans` (11 spec/review files) | Tighten the rule text to "applies to implementation plans, not `-spec.md` or review files", or narrow the glob if the rule syntax allows exclusions. |
| Warning / Medium | design | D1's usage evidence is weak. "A fix went unexecuted for 3.5 months" shows that nobody prioritised the duplication. It does not show that the planner was unused. Session logs for this project only go back to 2026-08-26, and they contain no `/my:plan` or `/my:task` calls. So the log check agrees with D1 but covers only about 2 weeks. | `spec §Decisions` D1; `ls -ltr ~/.claude/projects/-home-dchris-projects-claude-setup/` (oldest 2026-08-26); log grep found no `<command-name>/my:plan` | State the evidence plainly, or keep D1 on the other grounds (contradictions, hand-sync cost). The decision holds on those alone. |
| Suggestion / High | editorial | Two `GLOBAL-CLAUDE.md` line citations in Context are wrong (`:20` should be `:17`, `:65` should be `:83`). | `d853dbe~1:GLOBAL-CLAUDE.md:17,20,65,83` | Correct the line numbers. |
| Suggestion / High | editorial | Counts disagree: "7 edits" against 8 edit rows, "11 hits across 5 files" against 6 files, and "last four are prose examples" includes a SUPERSEDED header. | `spec §How to read this spec ↔ §Files to modify`; `git grep -c` at `d853dbe~1` | Correct the counts and the wording. |

### Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | After the change, the planning discipline has one owner (`GLOBAL-CLAUDE.md`), the template has one owner (`plan-format.md`), and planning control flow belongs to Superpowers. The pass-through `/my:plan` dispatcher is removed. | Strong |
| Contracts and flow | Contradiction 1 (two named owners of the template) is resolved: `GLOBAL-CLAUDE.md:194` now points to the rule file. The one remaining overlap is the 8 section names at `:194`, which is a small summary rather than a second template. | Moderate |
| Failures and interactions | The main runtime assumption (does the rule fire) is named under Risk, with a detection step and a fallback that goes back to the user rather than being made silently. | Moderate |
| Fit with what exists | The lazy-rule pattern already exists (`GLOBAL-rules/php.md:1-6`, `markdown.md:1-4`). The Bounded path really does cover `/my:task`'s job with a stronger gate (`brainstorming/SKILL.md:87-92`). Option B was a real, written, unexecuted plan with documented risks (`2026-05-28…md:114,122`). Option C is a real low-cost choice. | Strong |
| Grounding | Every file and symbol exists or is absent as claimed. The sweep is complete: no non-Markdown or cross-repo references. Only line numbers and counts are off. | Strong |
| Spec rules | "How to read this spec" comes first, with paths. Risk, Dependencies and Trade-offs are present. The spec+plan merge is openly flagged. The file list is detailed enough to plan from. No UI, so no Visual Language section is needed. | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Failures and interactions | Loading the rule when a file is touched means the template reaches the model after the first draft, and never during plan mode's `~/.claude/plans/` scratch phase (`plan-format.md:2-3`). | Medium |
| Boundaries | The glob covers specs and reviews as well as plans, so the rule's "every section is required" can apply to the wrong kind of document. | Medium |
| Fit with what exists | The claim that the planner "is not in use" rests on an inference plus about 2 weeks of logs. | Low |
| Grounding | Two wrong line numbers and three wrong counts. | Low |

### Needs Investigation

- **When path-scoped rules load.** It is unclear whether Claude Code loads them on `Write`/`Edit` of a new file or only on `Read`. The spec's post-merge Check 4 answers this, and both design Warnings above depend on the answer.

### Reasoning

The System Model is clean after the change. Each piece of planning state has one owner, and the deleted parts were a duplicate and a pass-through. Grounding holds apart from a few wrong line numbers and counts. The real concerns are at the one new connection, the lazy rule loader. It may deliver the template too late, and to documents that are not plans. The spec names only part of that risk. None of these break the design, and all can be fixed with a sentence or a narrower rule.

### Verdict

**Assessment:** Mixed
**Confidence:** Medium — the structure and grounding are verified, but the two main concerns depend on when Claude Code loads rules, which could not be tested from this worktree.
**Recommendation:** Keep D1–D3. Add the timing and scope concerns about `plan-format.md` to Risk, and add one line to the rule (or to GLOBAL-CLAUDE.md) saying to read the template before drafting and not to apply it to specs or reviews. Correct the line numbers and counts. Run Check 4 now: `git branch --contains d853dbe` shows the commit is already on `main`, and `~/.claude/rules/plan-format.md` is live.
