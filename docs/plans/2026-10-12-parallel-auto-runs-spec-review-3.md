# Review: docs/plans/2026-10-12-parallel-auto-runs-spec.md

**Status:** review of docs/plans/2026-10-12-parallel-auto-runs-spec.md, 2026-10-12. Problematic: the approach is right, but D6's first new fold refusal fires on a run's own squash commit, so the post-merge fold that the review stage runs today refuses in every project without the section.

## Spec Summary

The spec lets 2 to 4 `my:handoff auto` runs go at once in one project that opts in with a "Parallel runs" section. It adds a per-command lock script (`handoff-lock.py`), a capped start with slots, `live`, `start` and `merge` subcommands in `handoff-state.py`, a merge that refuses when `main` gained code since the last checks (rebase, recheck, retry up to three times), no fixups in opted-in projects, and two new refusals in `git-fold-fixups.py` that apply in every project.

Scope note: every caller sweep in this review was a plain text search (`grep -rn`) through Bash. No symbol-reference tool was available.

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| "Parallel runs" section (project `CLAUDE.md` / `CLAUDE.local.md`) | Max runs, docs paths, isolation line, shared-resource commands and lock names | Read by sessions; passed to scripts as arguments | New (format in spec §D1) |
| `handoff-lock.py` | Lock files `<git common dir>/my-handoff/locks/<name>.lock`; the wait and timeout; passes the command's exit code | `fcntl.flock`, git common dir | New (spec §D2) |
| `handoff-state.py` | State files `<git common dir>/my-handoff/<slug>.json`; new fields `slot`, `checked_base`, `merge_retries`; new `next` value `merge-retry`; subcommands `live`, `start`, `merge` | git, the lock script (as caller of `start`/`merge`) | Existing `plugins/my/bin/handoff-state.py:1-286` |
| `git-fold-fixups.py` | Fold and `check` refusals; new `--docs-paths` and two range refusals | git | Existing `plugins/my/bin/git-fold-fixups.py:20-24,183-201` |
| `my:handoff` skill (`SKILL.md`) | Stage steps, stop table, "Rules for every stage", fold steps, merge sub-steps | The three scripts, the project section | Existing `plugins/my/skills/handoff/SKILL.md:141-165,447-464,509-527,619-674,691-698` |
| Main checkout of `<base>` | Shared index and working tree; shared docs (`ROADMAP.md`, `CHANGELOG.md`, plans index) | Lock `main` (advisory) | Existing |
| Run worktree | The branch, its own index; rebase on retry | `<base>` | Existing (`SKILL.md:489-493`) |
| User sessions in the main checkout | Their own commits, which must take lock `main`; no fixups | `global/CLAUDE.md` rule text, `/my:commit`, `my:architect` | Existing `global/CLAUDE.md` (Git Workflow), `plugins/my/commands/commit.md:15,19`, `plugins/my/skills/architect/SKILL.md:246` |
| Rule text (`docs-layout.md`, `global/CLAUDE.md`) | The four-commit steps 4, 8, 9 and their exception; the Medium paragraph | — | Existing `global/rules/docs-layout.md:132-173` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Stage session → `handoff-lock.py main` | A commit command (`git add && git commit -- paths`) | Stage session |
| Auto launch → `handoff-lock.py main` → `handoff-state.py start` | Slug, `--max n`, initial fields; returns slot or refusal | `handoff-state.py` (state file) |
| Review stage → `handoff-lock.py main` → `handoff-state.py merge` | Branch, message, docs paths; reads `checked_base`; writes `squash_subject`, `next=merge` | `handoff-state.py` (state), main checkout (squash commit) |
| Review stage → worktree | `git rebase <base>`, rerun checks, `set checked_base`, `merge_retries+1` | Review stage |
| Stage → `handoff-lock.py <resource> --timeout 3600` | A shared-resource command, in the background | Project section (command, lock name) |
| Stage → subagent prompt | Filled Isolation values, locked shared-resource commands | Stage session |
| Review stage / user → `git-fold-fixups.py --docs-paths` | Docs paths; reads the range and docs files at HEAD for cited hashes | `git-fold-fixups.py` |
| `auto resume` → `handoff-state.py check` | `next` incl. `merge-retry`; resets `merge_retries` | `handoff-state.py` |
| Shared docs ← every run's `done` marks and plan commits | Edits in the main checkout's working tree, made in a tool call outside any lock | No single owner; D5's dirty-check and hunk check guard it |

## Grounding

- `spec §D6` says the refused commit "is another feature's squash". In a project without the section, the review stage folds the spec's and plan's fixups *after* its own squash-merge, on purpose, so that the `done` marks cite the folded hash: `plugins/my/skills/handoff/SKILL.md:624-632` (supervised) and `:661-667` (auto), and `plugins/my/skills/handoff/README.md:116-118,146-149`. The range of that fold always holds the run's own squash commit, which changes code. So the premise is false for this caller.
- `spec §D7` quotes estimate 1's "about 28% of runs rebase once". That figure assumes a 0.5 h window covering checks, reviews and the fix round (`docs/plans/2026-10-12-parallel-auto-runs-architecture.md:245-275`). D7 defines `checked_base` as `git merge-base <base> <branch>`, which is the fork point until the first rebase. So any code merge since the code stage began triggers a retry, and the window is the branch's whole life, 1.1 h at the median (critique M1, cited at architecture brief line 16). The same formula then gives about 51%. The stop rate stays far under 1%, so the decision holds; the number is wrong.
- All other checked references hold: rows 5, 15, 16, 17 (`SKILL.md:153,163-165`), Plan stage step 6's hunk check (`SKILL.md:428-438`), Plan step 8 and the auto code stage's steps 1 and 2 (`SKILL.md:447-464,516-526`), "never poll" (`SKILL.md:698`), docs-layout steps 4, 8, 9 (`global/rules/docs-layout.md:148-160`), the auto-run spec's D2, D5, D6, D7 (`docs/plans/2026-10-12-autonomous-run-spec.md:97,170,204,242`), critique M1 (`docs/reports/2026-10-09-workflow-efficiency-critique.md:158`), the brief's "auto mode makes no fixups" (architecture brief line 225), estimate 2's 30 minutes, the "Design workflow" heading (`ROADMAP.md:35`), and the fold-script callers named under Risk "Blast radius" (text sweep: `docs-layout.md`, `global/CLAUDE.md`, handoff `SKILL.md` and `README.md`, root `README.md`; `ROADMAP.md` and `CHANGELOG.md` only mention it historically).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Critical / High | design | D6's first refusal ("a commit after the oldest target changes a path outside the docs paths") fires on the run's own squash commit. The review stage folds waiting fixups after its own merge, in every project without the section, so that fold now always refuses: an auto run stops at row 17 after merging, and a supervised run cannot fold. This breaks D5's promise "without the section, folds work as today" and would hit this repo, which has no section. §Testing's fold cases do not cover it. | `spec §D6 ↔ §D5`; `plugins/my/skills/handoff/SKILL.md:624-632,661-667`; `plugins/my/skills/handoff/README.md:116-118`; `plugins/my/bin/git-fold-fixups.py:183-201` (range is oldest target to HEAD) | Decision for the author. Options: exempt the run's own squash commit (for example pass it, or the `squash_subject`, to the fold), or stop deferring folds past the merge everywhere (a fixup that cannot fold before the code stage becomes a normal commit), or limit D6 to projects with the section. |
| Warning / High | design | A start-time failure writes a phantom live run. The stop rows "lock `main` times out" (stage *any*) and "any other failure of `handoff-state.py start`" make a failed start a stop, and a stop runs `handoff-state.py set <slug> stopped=…`. `set` creates the file when none exists, with no `next`, so `live` (next ≠ `finished`) counts it and it takes a slot. With `--max 1` it then blocks every later auto start in the project. This conflicts with the spec's own "a refused start writes nothing" and with today's rule that a failed start check writes nothing. | `spec §Stop points ↔ §D3`; `plugins/my/bin/handoff-state.py:111-124` (`read_state(slug) or {}`); `plugins/my/skills/handoff/SKILL.md:357-359` | Say that every failure of the start command, timeout included, is a failed start check: signal and write nothing. |
| Warning / Medium | design | D4's single locked `git add && git commit` conflicts with the standing rule "Read `git diff --cached` before every commit" and with `/my:commit`, which stages in one call and rereads the staged diff before committing in another. Staging outside the lock also leaves staged changes in the main checkout, which make D7's `merge` refuse, and so stop another run. `/my:commit` and `my:architect` (which commits in the main checkout) are not in §Files. | `spec §D4 ↔ §D7`; `global/CLAUDE.md` Git Workflow ("Read `git diff --cached` before every commit"); `plugins/my/commands/commit.md:15,19`; `plugins/my/skills/architect/SKILL.md:246` | Decision for the author: where the reread happens under D4 (for example `git diff -- paths` before, `git show --stat` after), and whether `/my:commit` and `my:architect` change. Add them to §Files if so. |
| Warning / Medium | design | D5 narrows but does not close the shared-doc race that the brief left open ("Lock `main` covers the commit command, not the edit before it"). The dirty check, the edit, the hunk check and the locked commit are separate tool calls. Run B can pass its clean check, then edit after run A's hunk check and before A's locked commit; A's `git commit -- ROADMAP.md` then commits B's hunk. Context item 1 says this is one of the three things the spec fixes. | `spec §D5 ↔ §Context`; `docs/plans/2026-10-12-parallel-auto-runs-architecture.md` "Open for brainstorming", last bullet | Decision for the author: accept and list it under Risk, or move the verification into the locked command (for example the locked command checks that the file's diff matches what the stage expects). |
| Suggestion / High | editorial | D1 says that without the section "nothing else in this spec applies" (beyond the D3 refusal), but D6 says its refusals "apply in every project, with or without the section". | `spec §D1 ↔ §D6` | Name D6 as the second exception in D1's sentence. |
| Suggestion / High | editorial | D7 quotes "about 28% of runs rebase once", but with `checked_base` as the fork point the retry window is the branch's whole life, which gives about 51% with the brief's own formula. | `spec §D7`; architecture brief lines 245-275 and line 16 | Restate the figure, or say the 28% assumes a shorter window. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | Each script owns one thing: the lock script owns waiting, `handoff-state.py` owns run state and the merge, the fold script owns rewrite safety. The skill only orchestrates (spec §D2, §D3, §D7). | Strong |
| Failures and interactions | A lock lives exactly as long as one command, and the kernel frees it on a crash (spec §D2), which avoids the stuck-lease problem of a session that dies. The cap check and the state write are one locked step, so two starts cannot both pass the cap (spec §D3). | Strong |
| Contracts and flow | The merge's compare-and-swap uses `checked_base` as the merge-base, not the base tip, which is the correct condition for "the checks saw this code" (spec §D7). | Strong |
| Fit with what exists | Extends the existing state file, stop table and fold script rather than adding a daemon; the rejected options (lease, queue daemon, fold-at-once mode, three-way merge) were real candidates in the brief and earlier drafts with stated costs (spec §Trade-offs; brief Candidates B and C). | Strong |
| Spec rules | "How to read this spec" is first with the brief first; Risk, Dependencies, Trade-offs present; the brief's "Open for brainstorming" items each get an answer (cost under Risk, timeout in D2, diagoradisa out of scope, user commits in D4, docs-layout exception in Rule text, code definition in D1, user folds in D5/D6). | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Fit with what exists | D6's range refusal cannot tell another feature's squash from the run's own, and the existing post-merge fold always has its own squash in range (`SKILL.md:624-632,661-667`). | High |
| Failures and interactions | A start-time stop creates a state file that `live` counts (`handoff-state.py:111-124`). | Medium |
| Contracts and flow | D4's one-call commit has no place for the required staged-diff reread, and `/my:commit` stages outside any lock (`commit.md:15,19`). | Medium |
| Failures and interactions | Shared-doc edits remain outside the lock; D5's checks run in separate tool calls from the locked commit. | Medium |
| Grounding | The quoted retry rate understates the window D7 itself defines. | Low |

## Not Applicable

None.

## Needs Investigation

- **Whether D7's `merge` and the D4 lock rule also replace `git merge --squash` and plain commits in projects without the section.** D1 reads as "no", which leaves two merge paths in `SKILL.md` (row 15 today, `handoff-state.py merge` with the section). That is a workable reading, but the spec does not say it, and the §Files row for `SKILL.md` ("D2 to D8") does not separate them. The author's one-line answer resolves it.
- **Who sets `next=worktree-remove` after a successful `merge`, and what `check` requires for `next=merge-retry`.** The spec says `merge` sets `next=merge` before the squash and that `check` detects an interrupted merge "as today", but not the step after success, nor the `NEEDS` and facts for `merge-retry` (`handoff-state.py:47-56,175-209`). The plan can likely infer these; a sentence in D7 would make it certain.

## Reasoning

The System Model is coherent: one lock script, one state owner and one fold guard, each with a clear job, and the compare-and-swap merge is the right shape for 2 to 4 runs. The defect is at the edge between the new D6 refusal and an existing caller the spec did not trace: the review stage's post-merge fold always has its own squash commit in range, so a refusal meant for other features' squashes breaks the single-run flow everywhere. Two Warnings concern unguarded edges of the new start and commit paths. None of this requires rework of the chosen candidate.

## Verdict

**Assessment:** Problematic
**Confidence:** High — the Critical finding rests on the fold script's range rule and two `SKILL.md` steps that were read directly.
**Recommendation:** Decide how D6 treats a run's own squash commit (exempt it, or stop deferring folds past the merge), make every failed start write nothing, decide D4's reread and the `/my:commit` and `my:architect` changes, then run `my:spec-review` again. The approach itself does not need rework.
