# Review: docs/plans/2026-10-06-tutor-spec.md

**Status:** review of docs/plans/2026-10-06-tutor-spec.md, 2026-10-06. Mixed: the three-layer design is sound, but its top finding is that `progress.md` has no single source of truth across branches.

## Spec Summary

The spec adds a `my:tutor` skill (with `method.md` and `templates.md`), a `tutor` output style, and a "Learning workspaces" section in `global/CLAUDE.md`. A repo that contains `docs/learning/curriculum.md` becomes a learning workspace: the student writes the code, the tutor sets one exercise at a time on `ex/NN-<slug>` branches, gives hints by a five-level ladder, and records progress in `docs/learning/progress.md`. A real project is never touched: the skill clones it to `~/projects/<name>-learning` with a broken push URL.

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `my:tutor` skill (`SKILL.md`) | Workspace detection (D2 marker), setup case choice (D3), setup steps (D4), session steps (D5), git steps (D9) | `method.md`, `templates.md`, `anthropic-skills:learn` (optional), git | New (`plugins/my/skills/` has no `tutor`) |
| `method.md` | Hint ladder (D6), fading support and concept status (D7), write rules (D8), review steps (D5) | none | New |
| `templates.md` | Shape of `curriculum.md`, exercise file, `progress.md` | none | New |
| `tutor` output style | Per-turn behaviour (D10): read `plain.md`, invoke `learn` and `my:tutor`, student writes code, one step per turn | `~/.claude/output-styles/plain.md`, `my:tutor`, `learn` | New; folder is reachable through the existing symlink `~/.claude/output-styles -> global/output-styles` |
| "Learning workspaces" section in `global/CLAUDE.md` | Which global rules are set aside in a workspace; the style-missing warning | The D2 marker file | Existing file `global/CLAUDE.md:12` (section goes before it), Precedence at `global/CLAUDE.md:61` |
| Workspace files `docs/learning/` | Curriculum, exercises, progress (all teaching state) | The branch that is checked out | New, per workspace |
| `.claude/settings.local.json` + `.git/info/exclude` | Selects the `tutor` style per workspace | Claude Code settings | New per workspace; key in use at `~/.claude/settings.json:48` |
| Learning clone (case 3) | A copy of the real project with push disabled and branch `learning` | The user's local project repo as `origin` | New |
| `anthropic-skills:learn` | Teaching conversation moves | claude.ai sync | Existing, `~/.claude/skills/synced/<id>/learn/SKILL.md` |
| `my` plugin hooks (not named by the spec) | PostToolUse reminder on `git merge --squash`; SessionStart orphan-plan check | `my:roadmap-management` | Existing `plugins/my/hooks/hooks.json:9`, `:15` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Output style → `my:tutor` | "Invoke the skill and follow its session steps" (an instruction, each session) | `tutor` style |
| Output style → `plain.md` | A file read at session start | `plain` style |
| Output style → `learn` | A skill invocation at session start | `tutor` style (fallback `method.md`) |
| `my:tutor` → `method.md` / `templates.md` | File reads | `my:tutor` |
| `my:tutor` → `docs/learning/*` | Writes of curriculum, exercises, progress; commits | `my:tutor` |
| Session start → `progress.md` | Read before the first reply (D5) | Unclear: D5 says the style, D10 says the skill |
| `progress.md` on `ex/NN` → learning branch | Progress commits carried by the squash-merge (D5 End + D9) | Unclear: no single branch owns it |
| Global section → session | Marker check and "style is not active" warning | Global section; detector not defined |
| Setup session (case 3) → new session in the clone | Nothing defined; the user restarts | Not defined |
| Learning clone → original repo | `git fetch` only (read) | Clone |
| `git merge --squash` (D9) → `my` PostToolUse hook → `my:roadmap-management` | additionalContext telling Claude to edit ROADMAP and CHANGELOG | `my` plugin, not the spec |

## Grounding

The caller sweep was text-only (`grep`, `find`). No symbol tool was available. The spec removes or renames no symbol.

- `spec §How to read this spec`, test precedent: the reason the precedent gives for headless runs ("loads through the shell alias", `docs/plans/2026-09-16-spec-review-skill.md:24`) is stale, since the plugin now runs from the cache (`README.md:36`). The conclusion, headless `--plugin-dir` runs, still holds.
- `spec §Trade-offs` names `my:clean-gone-branches`; it is the command `/my:clean-gone-branches` (`plugins/my/commands/clean-gone-branches.md`), not a skill.
- `spec §How to read this spec` says "Task 7 adds a row" to `ROADMAP.md` ↔ `spec §Task 7` says the row goes into the `done` commit on `main`, not the branch.
- `spec §D9` relies on the global "Finishing a worktree branch" rule (`global/CLAUDE.md:190`), which sits under the Git Workflow that `spec §D2` sets aside.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | `progress.md` has no single source of truth. D5 commits it "on the current branch", usually `ex/NN-*`, so the live copy sits on an unmerged branch. A session that starts on the learning branch, or after an abandoned exercise, reads stale progress, and progress edits on both branches can conflict at the squash-merge. | `spec §D5 ↔ §D9` | Decision for the author. For example: progress is committed only on the learning branch, or the tutor always checks out the learning branch before reading and writing it. |
| Warning / High | design | Setup case detection has a hole. D3 asks only for "a remote, or commits by other authors". The user is the sole developer on every project, and `mv3-tab-notes` (named as case 2) has no remote and only the user's commits, so a solo real project with no remote shows exactly the same signals as case 2. If it falls into case 2, learning commits land on the real project's `main`, which breaks the Goal. Separately, case 1 is detected as "an empty folder" but acts by creating a new folder under `~/projects/`. | `spec §D3 ↔ §Goal`; `global/CLAUDE.md:134`; `~/projects/mv3-tab-notes` (`git remote -v` empty, one author) | Decision for the author. For example: any existing repo without the marker is always asked about, with case 3 as the default. |
| Warning / High | design | The `my` plugin's PostToolUse hook fires on every `git merge --squash` and tells Claude to invoke `my:roadmap-management` and edit ROADMAP and CHANGELOG in the same commit. D9 squash-merges every exercise, so the tutor gets that instruction each time; in a case-3 clone, it would edit the real project's copied ROADMAP. The spec does not name the interaction or say how the tutor ignores it. | `plugins/my/hooks/hooks.json:9-10`; `spec §D9`; `spec §D2` | Decision for the author: have the hook skip when `docs/learning/curriculum.md` exists, or state in D2/D9 that the reminder does not apply in a workspace. |
| Warning / High | design | The first exercise is committed in two places. D4 step 7 commits all of `docs/learning/`, which includes `exercises/01-<slug>.md`, on the learning branch. D9 says the exercise branch's first commit holds the exercise file and the test. After step 7, the failing test is written but uncommitted, and the `ex/01` branch does not yet exist. | `spec §D4 ↔ §D9` | Decision for the author: state which branch owns the exercise file, and that setup ends by creating `ex/01-<slug>` and committing the test there. |
| Warning / Medium | design | Nothing detects a workspace when the style is off. D2 tells Claude to warn when a workspace session starts without the `tutor` style, but only the style and the skill tell Claude to look at `docs/learning/`, and the global section gives no instruction to check for the marker file. The repo already has a pattern for this: the `my` plugin's SessionStart hook. | `spec §D2 ↔ §D10`; `plugins/my/hooks/hooks.json:15` | Decision for the author: a SessionStart check for the marker, or an explicit "check for the file" line in the global section. |
| Warning / Medium | design | The D2 list of rules is incomplete. It names what is replaced and what stays, but says nothing about "UI Design" (every UI discussion must be drawn in the `design` canvas, which conflicts with a student designing a popup), "Planning Standards" and "Test Standards", or "Code". It also does not cover a case-3 clone's own project `CLAUDE.md`, which arrives with the clone and may restate worktree and review rules. | `spec §D2`; `global/CLAUDE.md:107`, `:202`, `:265` | Decision for the author: list every top-level section as replaced or kept, and say whether a project `CLAUDE.md` is overridden too. |
| Warning / Medium | design | The case-3 hand-off has no contract. The setup session clones the repo and stops, and "the setup conversation runs in that new session". But the new session has no marker yet, and by D3's own rule a repo with a remote (`origin`) is asked about. The spec does not say how the new session knows it is a fresh case-3 clone that needs D4. | `spec §D3 ↔ §D4` | Decision for the author. For example: detect the clone by push URL `no-push` plus branch `learning`, or write a setup-pending note in the clone. |
| Warning / Medium | design | Fit with existing work: the official `learning-output-style` plugin (in the marketplace, not installed; a SessionStart hook that has the agent ask the user to write the meaningful lines) is not weighed in Trade-offs. It has no curriculum or progress, so it would likely be rejected, but the rejection should be stated. | `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/learning-output-style/README.md:1-5`; `spec §Trade-offs` | Add a Trade-offs row. |
| Warning / Medium | design | The size may be wrong. The change edits the global Precedence paragraph, which every project reads, and adds a mode that sets aside the Git Workflow and the review rules. That arguably counts as "a new subsystem", which is a Large trigger (architecture brief, separate plan). | `global/CLAUDE.md:16-28`, `:61`; `spec §Status` | Decision for the author. |
| Warning / Medium | design | The Risk detection rule contradicts D7 and D8. **Risk** treats any `Edit` or `Write` on the exercise's target file, without a level-5 request, as the tutor writing the solution. But D7 level 2 and D8 let the tutor write a skeleton with `TODO(human)` gaps, which most naturally sits in that same file. | `spec §Risk ↔ §D7`, `§D8` | Decision for the author: say where skeletons live, or narrow the detection rule. |
| Warning / Medium | design | The clone path contract differs between D3 and Testing. D3 fixes the path as `~/projects/<name>-learning`, but scenario 2 passes a different clone parent in the prompt. So the skill needs a parent override that D3 does not define. | `spec §D3 ↔ §Task 5` | Decision for the author: make the clone parent an input of the skill (default `~/projects/`), or test with a temporary `HOME`. |
| Suggestion / High | design | The `learning` scope conflicts with project scopes. D9 uses "the project's scopes" for `feat`, but D4, D5 and D9 use `docs(learning)` and `test(learning)`, which are not in `mv3-tab-notes`' scope list. A case-1 project has no scopes at all. | `spec §D4`, `§D9`; `~/projects/mv3-tab-notes/CLAUDE.md` (scopes line) | Decision for the author. |
| Suggestion / High | editorial | D5 says "the style makes Claude read `progress.md`", but D10's list of what the style says has no such line. There, the read only happens through `my:tutor`. | `spec §D5 ↔ §D10` | Add the read to D10's list, or reword D5. |
| Suggestion / High | editorial | D9 justifies keeping branches by citing "Finishing a worktree branch", which D2 sets aside and which is about worktrees D9 forbids. | `spec §D9 ↔ §D2`; `global/CLAUDE.md:190` | State the reason directly ("kept so early attempts can be compared"). |
| Suggestion / High | editorial | Case 3 hard-codes `origin/main`. A project whose default branch is `master` or `develop` breaks the update command. | `spec §D3` | Use the clone's `origin/HEAD` branch. |
| Suggestion / High | editorial | "How to read this spec" omits `superpowers:writing-skills`, which governs Tasks 1–5, and says Task 7 adds a ROADMAP row although Task 7 defers it to the `done` commit. `my:clean-gone-branches` is a command, not a skill. | `spec §How to read this spec ↔ §Tasks`, `§Task 7`; `plugins/my/commands/clean-gone-branches.md` | Add the row, fix the wording, write `/my:clean-gone-branches`. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | Skill = occasional procedures, style = every-turn behaviour, files = state; each layer has one job (`spec §D1`) | Strong |
| Fit | The style lands in an already-symlinked folder and copies `plain`'s frontmatter (`README.md:13-16`, `global/output-styles/plain.md:1-5`); no new dependency | Strong |
| Failures (case 3) | The push guard is enforced by git, not by the agent, and the original repo is only a fetch source (`spec §D3`, `§Trade-offs`) | Strong |
| Failures (optional `learn`) | The `learn` skill is optional, with `method.md` as the fallback (`spec §D10`, `§Dependencies`) | Moderate |
| Spec rules | "How to read this spec" comes first; Risk, Dependencies and Trade-offs are present; no UI is added, so no Visual Language section is needed | Strong |
| Grounding | The paths and behaviours the spec names exist as described: the `learn` skill's sections and its no-coding description (`~/.claude/skills/synced/<id>/learn/SKILL.md`), the `anthropic-skills:` namespace (`~/.claude/cache/changelog.md:925-926`), `outputStyle` in use (`~/.claude/settings.json:48`), the Precedence wording (`global/CLAUDE.md:61`), and the `mv3-tab-notes` files (`~/projects/mv3-tab-notes/src/popup/popup.ts:1`, `src/lib/store.ts`, `test/fakes.ts`) | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Contracts and flow | `progress.md` split across branches; exercise file in two commits (`spec §D4`, `§D5`, `§D9`) | High |
| Failures and interactions | The squash-merge hook fires on every exercise (`plugins/my/hooks/hooks.json:9-10`); case-3 hand-off undefined | Medium |
| Goal safety | A solo real project with no remote cannot be told from case 2 (`spec §D3`) | Medium |
| Fit | The official learning style is not weighed; nothing detects a workspace when the style is off | Medium |
| Scope | D2 leaves several global sections, and project `CLAUDE.md` files, unclassified | Medium |

## Not Applicable

None.

## Needs Investigation

- **Does the style take effect in the setup session?** In cases 1 and 2, D4 step 6 writes `outputStyle: tutor` and then "starts teaching" in the same session. `~/.claude/cache/changelog.md:6216` says the output style is fixed at session start; `:1733` later re-added `/output-style` to switch it. If the setting only applies to the next session, the first lesson runs without the style, and the spec should either tell the user to restart (as case 3 already does) or run `/output-style tutor`. Resolve this with one manual run during Task 1.
- **Case 1 in a session started elsewhere.** Case 1 creates a new folder under `~/projects/`, but the session's project root stays where it was started. It is not checked whether `.claude/settings.local.json` and later sessions behave as expected without a restart in the new folder. The same Task 1 run would answer it.

## Reasoning

The System Model shows a clean three-layer split with one owner per file, and every grounding claim held. The problems all sit on connections the spec leaves undefined: which branch owns `progress.md` and the first exercise, how a case-3 clone hands setup to the next session, how a workspace is detected without the style, and how an existing hook reacts to the exercise squash-merges. None of these needs a different approach; each needs a stated rule. The case-detection hole touches the Goal's "never harm the project", so it should be settled before the plan.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every Warning cites either a spec contradiction or a repo file I opened.
**Recommendation:** Settle the `progress.md` home, the case-detection default and the squash-merge hook interaction with the user as design questions. Fix the four editorial rows. Then confirm the size (Medium or Large) before writing Tasks further.
