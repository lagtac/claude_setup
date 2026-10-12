# Review: docs/plans/2026-10-12-swappable-methods-spec.md

**Status:** review of docs/plans/2026-10-12-swappable-methods-spec.md, 2026-10-12. Mixed: the split into a neutral core, `my.md`, `tutor.md` and a `kit` plugin holds, but the setup and cutover assume 12 flat git repos with committable `.claude/settings.json`, and two of the "projects" are folders of nested repos. Answered on 2026-10-13: the two editorial findings were fixed, and the six design findings became spec decisions D13 to D18, with the four open items added as task 0 checks 3 to 6.

## Spec Summary

The spec splits `global/CLAUDE.md` into a neutral core and per-method files under `global/methods/` (`my.md`, `tutor.md`), imported by one `@~/.claude/methods/<name>.md` line in each project's `CLAUDE.md`. It splits the `my` plugin into `my` (the method, off at user scope and on per project, as is superpowers) and a new `kit` plugin (neutral tools, on everywhere), which also holds a new SessionStart guard and a `kit:setup` skill. The work ships in two batches, and the second batch is a one-sitting cutover across 13 projects.

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
| --- | --- | --- | --- |
| Neutral core `global/CLAUDE.md` | Rules that hold under every method; Core Precedence | `~/.claude/CLAUDE.md` symlink | Existing `global/CLAUDE.md:1`, trimmed |
| `global/methods/my.md` | Every section the section table marks method; Method Precedence | `~/.claude/methods` symlink, project import line, approval flag | New |
| `global/methods/tutor.md` | Tutor workspace rules | `kit:tutor`, the `tutor` output style | New; replaces `global/CLAUDE.md:12` (Learning workspaces) |
| `docs-layout.md`, `plan-format.md` | Lazy rules for `docs/plans` | `paths:` frontmatter | Existing `global/rules/docs-layout.md:1`, `global/rules/plan-format.md:1` |
| `my` plugin | Method skills, agents, scripts, hooks (orphan plans, squash-merge, autorun push) | Plugin cache, project `enabledPlugins` | Existing `plugins/my/hooks/hooks.json:1` |
| `kit` plugin | Neutral skills, agents, commands, md scripts, tutor hook, guard, `kit:setup` | Plugin cache, marketplace entry, user `enabledPlugins` | New (files exist today under `plugins/my/`) |
| `method-guard.py` | Nothing; read-only warnings | Project `CLAUDE.md`/`CLAUDE.local.md`, three settings files, `~/.claude.json` | New |
| `kit:setup` | The `## Project facts` block, import line, project `.claude/settings.json`, one commit per project | git in the target repo, the user's yes | New |
| User switches `~/.claude/settings.json` | `my`/`superpowers`/`kit` user-scope state | Outside the repo | Existing; `superpowers@synced` key absent today |
| Project switches `.claude/settings.json` | Per-project plugin state | Must be committable in the project repo | New in 12 projects; existing in `webext` |
| Approval flag in `~/.claude.json` | Whether the external import loads | Claude Code, undocumented | Existing key, verified for `/home/dchris/projects/claude-setup` (value `False`) |
| Cutover runbook | Ordering of merge, symlink, switches, setup, checks | `handoff-state.py live`, `pgrep`, the plugin cache | New |

| From → To | What passes | Owner of what passes |
| --- | --- | --- |
| Project `CLAUDE.md` → `my.md` / `tutor.md` | `@` import at session start | Project (line), method file (content) |
| `~/.claude/methods` → `global/methods/` | Symlink | Runbook step 3 |
| Settings files → Claude Code | `enabledPlugins` merge | User file and project files |
| Guard → three settings files, `CLAUDE.md`, `~/.claude.json` | File reads | Claude Code / project |
| Guard → session | `additionalContext` + `systemMessage` | Guard |
| `kit:setup` → project `CLAUDE.md`, `.claude/settings.json`, git | File edits, a commit | `kit:setup` |
| Plugin cache → session | The cached copy of `my` and `kit` at a commit | Claude Code (`claude plugin install/update`) |
| Tutor hook (`kit`) → session | "Invoke `kit:tutor`" | `kit` |
| Squash-merge hook (`my`) → session | Roadmap reminder | `my` |
| Core Precedence ↔ method file | Which rule wins, exceptions by name | Core |

The cache row (plugin cache → session) has no owner in the spec: no runbook step installs `kit` or updates the cached copies.

## Grounding

All searches were text-only (`grep -rn`, `git grep`), because no symbol-reference tool was available.

- spec §Risk lists "One script for the locked commit" as an open `my:handoff` row ↔ `ROADMAP.md:153` marks it ✅ done.
- spec §Batch 1 lists where the neutral-name sweep hits ↔ it misses `plugins/my/skills/changelog-management/SKILL.md:65` (`my:dev-reports`), a file that stays in `my`. The plan reruns the sweep, so this is minor.
- spec §Decisions D3 says "the neutral sweep is about 30 lines" ↔ the text sweep for the 15 `kit` names finds 46 lines in `global/`, `plugins/`, `README.md` and `CLAUDE.md`.
- spec §Switches / §Cutover runbook step 5 assume each `my` project is one git repo ↔ `~/projects/diagoradisa` and `~/projects/grispy-web-ext` have no `.git`. They hold the nested repos `diagoradisa-{annotator,meta,ml,palmist,platform}` and `grispy-{ext,site}`, each with its own `CLAUDE.md`.
- spec §Risk "settings file written into 13 project repos" ↔ `.gitignore:2` in this repo ignores `.claude/` (`git check-ignore -v .claude/settings.json`). The other 10 single-repo projects do not ignore it.
- spec §Switches row 1 implies `superpowers@synced` is a user-settings key ↔ `~/.claude/settings.json` `enabledPlugins` has no such key today. Superpowers comes from the claude.ai sync (brief line 283).
- spec §Global files "first line after the title" ↔ both files begin with `paths:` frontmatter (`global/rules/docs-layout.md:1-4`, `global/rules/plan-format.md:1-4`). This is consistent with "after the title". Only the wording in §Testing ("start with") is loose.

Every other checked reference holds. This includes the item 6 sweep hits (`docs-layout.md:135`, `status/SKILL.md:59`, `handoff/README.md:253`), the full split of the 15 skills, 5 agents, 7 commands and 7 scripts, `handoff-state.py live`, the `hasClaudeMdExternalIncludesApproved` key, the section headings, `mv3-tab-notes` as a tutor workspace, and uncommitted work in `lequal`, `niche-research` and `notes-cli`.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Warning / High | design | Two of the 12 "projects" are not git repos but folders of 7 nested repos, each with its own `CLAUDE.md`, and sessions open in the nested repos. Setup step 4 cannot commit in the parent folder. The spec does not say whether the import, the facts block and `.claude/settings.json` go in the parent or in each nested repo. The guard reads only `<root>/CLAUDE.md`, and its root comes from `git rev-parse` in the nested repo. Risk's blast radius also leaves out the nested repos. | `~/projects/diagoradisa` and `~/projects/grispy-web-ext` (no `.git`); `~/.claude.json` project entries for `diagoradisa/diagoradisa-annotator` etc.; spec §Setup skill step 4, §Guard Inputs 1–2, §Cutover runbook step 5 | Decision for the author: set up each nested repo, or define a parent-folder mode for the setup and the guard. |
| Warning / High | design | Tutor projects gain rules they set aside today. "Learning workspaces" keeps only Critical Thinking and "No vacuous tests" from Planning Standards. The spec puts Verify against ground truth, Mandatory Exploration, Reference Sweep and Simplicity Rules into the core, so they load in tutor projects. D6's reason ("`my` is off, so its rules never load") does not cover core rules. Core Precedence allows an exception only by naming the rule, and `tutor.md`'s "workflow rules from elsewhere do not apply" names none. | `global/CLAUDE.md:18-33`; spec §Decisions D6 ↔ §Section table ↔ §Reworded text item 1 ↔ §The tutor method file | Decision for the author: have `tutor.md` name the core rules it sets aside, or accept the change and drop "behave as before" for the tutor project. |
| Warning / High | design | D5's own test is broken by two files the Plugins table puts in `kit`. `optimize-prompt` writes to `docs/plans/optimized-prompts/`. `tune-claude-instructions` cites `docs/plans/` and `/my:summarize`. In a trial project, `kit` would still write our docs layout. | `plugins/my/commands/optimize-prompt.md:133`; `plugins/my/skills/tune-claude-instructions/SKILL.md:197,203,220`; spec §Decisions D5 ↔ §Plugins | Move them to `my`, or reword them to be neutral and say so in D5. |
| Warning / High | design | `.claude/settings.json` is gitignored in `claude-setup`, so setup step 4 cannot stage it. The per-project switch in this repo would then live only in the main checkout, and no worktree would get it. The spec does not decide what setup does when the file is ignored. | `.gitignore:2`; spec §Setup skill step 4, §Risk "Hard to reverse" | Decision for the author: `git add -f`, un-ignore the file, or use `settings.local.json` and accept that it is not committed. |
| Warning / High | design | The runbooks never install or update the cached plugins. Sessions run the copy in `~/.claude/plugins/cache/`, and the cached `my` is at 2a48d5c, not HEAD. `kit` has no `installed_plugins.json` entry, and the batch 1 runbook only adds a settings key. Batch 2 adds `kit:setup` and the guard, but no step runs `claude plugin update`/restart before cutover step 5, so `/kit:setup` would not exist in the running session. After batch 1, until `my` is updated, both caches also carry the tutor hook. | `README.md:38-44`; `~/.claude/plugins/installed_plugins.json` (`my@claude-setup` at `cache/claude-setup/my/2a48d5ce401a`, no `kit`); spec §Batch 1 runbook, §Cutover runbook steps 2–5 | Add install, update and restart steps to both runbooks, and say which session runs step 5. |
| Warning / Medium | design | The guard treats a missing `superpowers@synced` key as "off", but superpowers comes from the claude.ai sync and is on today with no key in any settings file. If the task 0 spike fails and D7 falls back, or the user key is removed later, the guard reports a trial project as clean while superpowers is loaded. | `~/.claude/settings.json` (no `superpowers@synced`); brief line 283; spec §Guard Behaviour rows 1, 3, 5 | Decision for the author: define the default for a missing key per plugin (superpowers defaults to on). |
| Suggestion / High | editorial | Risk lists "One script for the locked commit" as an open row that may conflict, but it is done. | `ROADMAP.md:153`; spec §Risk | Drop it from the list. |
| Suggestion / High | editorial | The batch 1 sweep list misses `changelog-management/SKILL.md:65`, and D3's "about 30 lines" is 46 by text search. | `plugins/my/skills/changelog-management/SKILL.md:65`; spec §Batch 1, §Decisions D3 | Correct the count and add the hit. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Boundaries | Every one of the 15 skills, 5 agents, 7 commands and 7 scripts under `plugins/my/` is placed exactly once, and the section table covers every heading of `global/CLAUDE.md` (`grep -n '^#' global/CLAUDE.md`). | Strong |
| Contracts (guard) | The guard reads, never writes, always exits 0, reads `$HOME` for tests, and has an explicit parse-failure row (spec §Guard). | Strong |
| Fit | D8 moves the guard to `kit`, closing the "plugin off, import still there" gap the brief named (brief line 294). The tests follow the existing subprocess style (`plugins/my/tests/test_block_autorun_push.py:20-28`). | Moderate |
| Grounding | The item 6 sweep hits, the approval key and `handoff-state.py live` all exist as described. | Strong |
| Rollback | Batch 2 is one squash commit with a backup of the user settings (spec §Rollback). | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| Fit with the real project set | Nested repos under `diagoradisa` and `grispy-web-ext`; `.claude/` ignored in `claude-setup`. | High |
| Core boundary | The four sections moved to the core change tutor behaviour; D2's "no conflict with the method's process" is argued only for superpowers, not for outside methods with their own exploration steps. | Medium |
| Failures | The plugin cache has no owner in the runbooks; the guard cannot see the synced superpowers default. | Medium |
| D5 consistency | `optimize-prompt` and `tune-claude-instructions` fail D5's own test. | Medium |

## Not Applicable

None.

## Needs Investigation

- **Second approval key.** `~/.claude.json` also stores `hasClaudeMdExternalIncludesWarningShown` next to the approval flag. If a project's prompt was shown and declined once, it is unclear whether a new interactive session asks again. Cutover step 7 and the guard's text ("start a new interactive session") both depend on this. To resolve it, run a scratch project with the flag `false` and the "shown" flag `true`.
- **Nested-root sessions.** It is unclear whether a parent folder's `CLAUDE.md` import and `.claude/settings.json` reach a session rooted in `diagoradisa/diagoradisa-palmist`. Claude Code reads ancestor `CLAUDE.md` files, but whether it reads ancestor project settings, and whether an ancestor import counts against the nested path's approval, was not checked. A scratch spike resolves both.
- **Import through a symlink into the same repo.** In `claude-setup`, `~/.claude/methods/my.md` resolves into the project itself. If Claude Code compares real paths, it may treat the import as internal and never set the approval flag. The guard would then warn forever, and step 7's "prints nothing in any of the 13 projects" would fail there. To resolve it, test after the step 3 symlink.
- **Rollback claim.** The claim that a missing import target "is skipped without a message" (spec §Rollback) was not verified.

## Reasoning

The component split holds: placement is complete, each piece of state has one owner, and the guard's contract is clear. The findings sit where the model meets the real environment: the project set is not 12 flat repos, one repo ignores the switch file, the plugin cache needs steps the runbooks lack, and superpowers' on/off state does not live where the guard looks. Separately, the core boundary changes tutor behaviour, which D6 does not account for. None of these needs a new approach. Each needs a decision or added steps, so there is no Critical row.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. The repo-side findings were checked directly; the nested-repo and approval-prompt behaviour of Claude Code could not be tested here.
**Recommendation:** Decide the nested-repo layout, the tutor override and the ignored-settings case. Add install, update and restart steps to both runbooks. Add the nested-repo and approval-prompt checks to task 0 before writing the plan.
