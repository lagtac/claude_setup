# Review: docs/plans/2026-10-12-status-skill-spec.md

**Status:** review of docs/plans/2026-10-12-status-skill-spec.md, 2026-10-12. Problematic: run on this repo, D4's branch check marks 17 of the 18 unmerged branches `maybe-unfinished`, so it does not remove the false "unfinished" list that the spec was written to fix.

## Spec Summary

The spec adds a read-only skill, `my:status`. It answers "where are we", "what is next" and "what can run in parallel" in one chat report. A new standard-library script, `status-scan.py`, prints the facts in tab-separated blocks: roadmap rows, the order of work, document status lines, the main checkout, worktrees, auto runs, and branches that may be unfinished. The skill then judges what comes next and which items may run together, using the order of work, the specs' "Files" sections and the project's "Parallel runs" section.

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `status-scan.py` | Fact collection and the block format (D3). Row parsing for two roadmap formats, the status filter, the fixup-target rule, and the added-line branch test (D4). | git, `ROADMAP.md`, `docs/plans/`, `docs/reports/`, `handoff-state.py live` or the state files | New (`plugins/my/bin/` holds no such file) |
| `my:status` skill (`skills/status/SKILL.md`) | The judgment: stage per item, "what is next", the four parallel conditions, the `git grep` follow-up on branches, the report format (D5, D6) | `status-scan.py`, the project's `CLAUDE.md` "Parallel runs" section, spec "Files" sections, `global/CLAUDE.md` "Assessing branch redundancy" | New (`plugins/my/skills/` has no `status`) |
| `handoff-state.py` | The run state files `<git common dir>/my-handoff/<slug>.json`; the future `live` subcommand | git | Existing `plugins/my/bin/handoff-state.py:1-34`; `live` not there yet (`main()` reaches `usage()`, exit 2) |
| Run state files | `next`, `branch`, `stopped`, and other fields per run | written by `my:handoff` | Existing `plugins/my/bin/handoff-state.py:44-45,82-83` |
| `ROADMAP.md` (two formats) | Rows, icons, order of work; gates inside rows ("Blocked by", "Waits for") | `my:roadmap-management` | Existing `ROADMAP.md:17-35`; `~/projects/grispy2-web-ext/ROADMAP.md:12-40` |
| Status lines in `docs/plans/`, `docs/reports/` | Document state | `docs-layout.md` "Status line" | Existing `global/rules/docs-layout.md:93-113` |
| "Parallel runs" section | Max runs, docs paths, shared resources | the parallel auto runs spec | Defined in `docs/plans/2026-10-12-parallel-auto-runs-spec.md:64-86` (approved, not built) |
| Parallel auto runs spec, "Out of scope" | The pointer to whoever answers "what can run in parallel" | — | Existing `docs/plans/2026-10-12-parallel-auto-runs-spec.md:51-52` |
| `README.md` | Skill list and the `bin/` paragraph | — | Existing `README.md:70-114` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| user → skill | Trigger phrase or `/my:status` | user |
| skill → `status-scan.py` | One subprocess call; stdout in blocks | `status-scan.py` (the block format, D3) |
| `status-scan.py` → git | `diff`, `log`, `worktree list`, `status`, `show main:<file>` | git |
| `status-scan.py` → `ROADMAP.md` | Text, parsed into bullet or table rows, and the order section | `my:roadmap-management` (the format) |
| `status-scan.py` → `handoff-state.py live` | Subprocess; exit 2 means "not built yet" | `handoff-state.py` (the field list, parallel spec D3) |
| `status-scan.py` → state files (fallback) | JSON read directly | `handoff-state.py` |
| skill → git (`git grep` on `main`) | 2–3 names per `maybe-unfinished` branch | skill |
| skill → `CLAUDE.md` "Parallel runs", spec "Files" sections | Prose that the skill reads | project / spec author |
| skill → user | Chat report with commands to run | skill |

## Grounding

Every caller and reference sweep below was a plain text search (`grep -rn`). No symbol-reference tool was available.

- `spec §Out of scope` ("roadmap-management rule 12") and `spec §How to read this spec` item 2 ("rules 3 and 12 … the roadmap icons") ↔ `plugins/my/skills/roadmap-management/SKILL.md:85,37-41`. The sentence "the order is the user's decision" is in rule 3, at line 85. The icons are in "Status legend", not in rule 3. Rule 12 (`:185-198`) defines the order section.
- `spec §Task 3` ("called by its plugin path, as `my:handoff` calls `handoff-state.py`") ↔ `plugins/my/skills/handoff/SKILL.md:361`. `my:handoff` calls the script by bare name, because it "is on `PATH` in every session that loads this plugin".
- `spec §D3` ("`handoff-state.py live` … prints the same fields") ↔ `docs/plans/2026-10-12-parallel-auto-runs-spec.md:117-118`. `live` is already specified to print slug, slot, `next`, stop line, branch: five fields in another order. The `runs` block has four: slug, `next`, branch, stop line.
- `spec §Task 4` relies on "the memory note on headless skill testing". That note is not in the repo, and it also needs `--add-dir` for the scratch folder, not only the plugin folder.

These hold: the `docs-layout.md` sections (`:29`, `:93`, `:132`); "Assessing branch redundancy" at `global/CLAUDE.md:202`; 18 branches from `git branch --no-merged main`; `handoff-state.py live` exits 2 today (`main()` → `usage()`); the "Out of scope" text that Task 5 replaces (`parallel-auto-runs-spec.md:51-52`); the README `bin/` paragraph (`README.md:107-114`); both roadmap formats; and the status values (`docs-layout.md:101-111`).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Critical / High | design | D4's added-line test does not filter squash-merged branches in this repo. I reproduced D4 with a scratch script: `git diff main...<b>`, keep added lines of 8 or more characters after stripping, compare with `main`'s copy of every touched file. Result: 17 of 18 branches are `maybe-unfinished`, and only `feat/autonomous-run` clears. Branches that are almost surely merged still fail by a few lines: `feat/tutor` (2), `feat/spec-review-off-path` (1), `fix/git-fold-fixups-check` (4), `feat/handoff-task-doc-role` (4). The cause is the normal case: `main` edited the same files after the squash. That is not Risk 2's "moved to another file" case. So the claim that the skill's `git grep` runs "only on the few branches the script lists" fails, and Goal 4 rests on the manual check of about 17 branches in every session. | `spec §Goal 4 ↔ §D4 ↔ §Trade-offs ↔ §Risk 2`; `git branch --no-merged main` = 18; scratch simulation of D4 on `/home/dchris/projects/claude-setup` | Decision for the author. Options: a threshold (missing / kept below some share), a check on the subject or content of the branch's squash commit on `main`, or a record of branches already judged. |
| Warning / High | design | Gates written inside a row are lost. Rule 12 allows `Blocked by row X.` and `Waits for <what>.` inside the blocked row. The `roadmap` block keeps only icon, number, title and links, and D6 reads gates only from `## Order of work`. This repo has two such rows, and with no order section "What is next" would suggest them. That breaks Goal 3's "the order of work gates one behind the other". | `plugins/my/skills/roadmap-management/SKILL.md:190-191`; `ROADMAP.md:67`, `ROADMAP.md:110`; `spec §D3 ↔ §D6` | Add a gate field to the `roadmap` block (the `Blocked by` / `Waits for` clause), and have D6 apply it. |
| Warning / High | design | Every `no-status` file goes under "Items that need the user". In this repo, 20 of 59 files in `docs/plans/` have no status line. They are mostly older done work, written before the rule existed, and there is no plans index. The report would list about 20 such lines at the top of every session. | `grep -L '^\*\*Status:\*\*' docs/plans/*.md` → 20; `spec §D6` item 1 | Decision for the author: one count line, a date cut-off, or only files newer than the rule. |
| Warning / High | design | The `runs` contract has two sources that disagree. The approved `live` prints 5 fields (with `slot`) in another order. D3 says the script prints "the same fields" but never says that it reorders `live` output, or how it parses it. Risk 4 treats this as a later possibility, but it is already specified. | `docs/plans/2026-10-12-parallel-auto-runs-spec.md:117-118`; `spec §D3 ↔ §Risk 4` | State that the script maps `live`'s fields onto the 4-field `runs` line, and name the separator it expects from `live`. |
| Warning / Medium | design | Failure of one source is not specified. The spec does not say whether the script exits, prints `none`, or prints an error line when `ROADMAP.md` is missing, a state JSON file is unreadable, `live` exits 1, or the main checkout has no branch. `handoff-state.py` treats "no base branch" as its own case. The skill cannot tell "none" from "could not read". | `plugins/my/bin/handoff-state.py:175-176`; `spec §D3` exit codes list only 0 and 2 | Name the result for each failure, for example an `error <reason>` line inside the block, and say how the skill reports it. |
| Warning / Medium | design | A row's linked `docs/plans/` path is taken as its spec, but rows also link other documents. This repo's 📋 "Deny list has no effect" row links the autonomous-run spec where the problem was found. The skill would read that spec's "Files" section and would not suggest "write its spec". | `ROADMAP.md:18-23`; `spec §D3` (roadmap fields) ↔ `§D6` items 2–3 | Keep only links whose text is `spec` or `plan`, or paths ending in `-spec.md`, or let the skill confirm the link. |
| Warning / Medium | design | Overlap reads only the spec's "Files" section. 5 of 11 specs here have none; for a Large change the file list lives in the plan. So most Large items are "unknown overlap", and the parallel answer is nearly always empty. | `grep -L '^## Files' docs/plans/*-spec.md` → 5 of 11; `spec §D6` item 3, `§Trade-offs` third bullet | Decision for the author: also read the plan's "Files to Modify" when a plan exists. |
| Warning / Medium | design | A branch that only deletes lines, or only adds lines shorter than 8 characters, has no kept added line, so the script never prints it. Risk 1 names only branches that move lines. An unmerged removal branch stays hidden. | `spec §D4 ↔ §Risk 1` | Treat a branch with no kept added lines as `maybe-unfinished`, or record the hole in Risk 1. |
| Warning / Medium | editorial | "Live" has two meanings. D6 item 1 separates a stopped run from a live run. D6 item 3 counts "live runs plus new runs" against Max runs, but the parallel spec counts a stopped run toward Max runs. Only one reading works: every row of the `runs` block. | `spec §D6` items 1 and 3; `docs/plans/2026-10-12-parallel-auto-runs-spec.md:143` | Write "runs in the `runs` block (stopped ones count)" in D6 item 3. |
| Suggestion / High | editorial | Wrong rule references: rule 12 is cited for "the order is the user's decision", which is in rule 3. Rule 3 is cited for the icons, which are in "Status legend". | `plugins/my/skills/roadmap-management/SKILL.md:37-41,85`; `spec §How to read this spec`, `§Out of scope` | Cite "Status legend", rule 3 (line 85) and rule 12 correctly. |
| Suggestion / High | editorial | Task 3 says the script is called by its plugin path, "as `my:handoff` calls `handoff-state.py`". `my:handoff` calls it by bare name from `PATH`. | `plugins/my/skills/handoff/SKILL.md:361` | Write "by bare name, on `PATH`, as `my:handoff` does". |
| Suggestion / High | editorial | Task 4 depends on a memory note that a cold reader does not have, and its command leaves out the `--add-dir` for the scratch folder that the note requires. | `spec §Task 4` | Inline the full `claude -p` command with both `--add-dir` flags. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | The script collects facts and the skill judges (D2). The skill writes nothing, and the order stays with the user. There is no overlap with `my:roadmap-management`, which edits. | Strong |
| Fit with what exists | It reuses `handoff-state.py`'s conventions (git common dir, base branch, standard library, test style at `plugins/my/tests/test_handoff_state.py:1-60`) and the parallel spec's "Parallel runs" defaults. The rejected options (prompt-only, a judging script, `git grep` per line) are real choices with stated reasons. | Strong |
| Contracts | The block format is precise: names, order, tab fields, `none` for an empty block, exit codes. | Moderate |
| Safety | "Unknown overlap is never safe" and the refusal without a "Parallel runs" section match the parallel spec's D3, so the report cannot suggest a start that the start check refuses. | Moderate |
| Grounding | Most references hold: the 18 branches, `live` exiting 2 today, both roadmap formats, the status values, the Task 5 text. | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Failures and interactions (D4 on the real repo) | 17 of 18 branches are flagged, so the motivating failure comes back. | High |
| Contracts and flow (gates) | In-row `Blocked by` / `Waits for` gates are dropped (`ROADMAP.md:67,110`). | Medium |
| Contracts (the `runs` source) | `live`'s 5 fields vs the block's 4 (`parallel-auto-runs-spec.md:117-118`). | Medium |
| Failures | No defined behaviour when a source cannot be read. | Medium |
| Report noise | 20 `no-status` files go to the top of every report. | Medium |

## Not Applicable

- Criterion 3, off-path events: the spec adds no UI. The output is chat text.
- Criterion 6, Visual Language: no UI, so its absence is correct.

## Needs Investigation

- How well D5's manual `git grep` clears the flagged branches. Superseded branches that the workflow keeps on purpose (for example `slim-code-review`, `code-review-plan-mode`) may have names that are truly absent from `main`. If so, they show as "still unfinished" in every session, and the spec has no way to mark them as judged. A headless run of the skill on this repo would settle this; I did not run the skill.

## Reasoning

The component split is clean, and most references hold. But the one mechanical test that Goal 4 depends on (D4) fails on the repo the spec names for its rehearsal: it lets through 17 of 18 branches, because `main` keeps editing files after a squash. Several smaller contract gaps also weaken Goal 3: in-row gates, a row link taken as the row's spec, and overlap read from the spec only. So does the noise from `no-status` files. Because the Critical finding challenges a decision rather than its wording, the author has to choose a new branch test.

## Verdict

**Assessment:** Problematic
**Confidence:** High — the Critical finding comes from running D4's own rule against this repo's 18 branches, not from reading alone.
**Recommendation:** The author picks a branch test that passes squash-merged branches whose files changed later on `main`. Then answer the Warning design rows (in-row gates, the `no-status` flood, the `runs` field mapping, failure handling, row-link meaning, the plan's file list) and fix the editorial rows before approval.
