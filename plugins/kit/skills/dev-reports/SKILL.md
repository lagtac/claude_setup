---
name: dev-reports
description: >
  Use when the user asks to generate a developer report, weekly report, daily report,
  dev log, or activity summary from git history. Also when invoked via /kit:dev-reports.
  NOT for CHANGELOG.md entries (use changelog-management).
---

# Developer Report Generator

Generate concise developer reports from git history. No fluff — developer audience.

## Arguments

```
/kit:dev-reports weekly                       # weekly, current week (see Monday rule)
/kit:dev-reports weekly 2026-W10              # specific ISO week
/kit:dev-reports weekly 2026-W10 path/to/dir  # custom output path
/kit:dev-reports today                        # today only
/kit:dev-reports daily                        # one report per day since the newest existing daily report
/kit:dev-reports daily 2026-03-20             # that day only
```

Defaults: type=today, path=docs/dev-reports/

## Steps

### 1. Parse arguments and determine date range

- **`today`** (default): one file, `YYYY-MM-DD.md`, for today.
- **`daily <date>`**: one file, `YYYY-MM-DD.md`, for that day.
- **`daily`** with no date: find the newest `YYYY-MM-DD.md` in the output directory. Make one report for each day after it, up to and including today, that has commits. Days with no commits get no file. If no daily report exists yet, do today only.
- **`weekly`**: ISO week, Monday–Sunday, one file `YYYY-WNN.md`. With no week given, use the current week. If today is Monday and the current week has no commits yet, use the previous week.

**Existing file.** If the target file already exists, ask with `AskUserQuestion` whether to overwrite it or stop. If `AskUserQuestion` is not available, stop and say the file exists. Never overwrite silently.

Compute ISO week boundaries:
```bash
# Current ISO week number
date +%G-W%V

# Monday and Sunday of a given ISO week (GNU date can't parse ISO weeks directly)
python3 -c "
from datetime import datetime, timedelta
year, week = 2026, 10  # adjust as needed
mon = datetime.strptime(f'{year}-W{week:02d}-1', '%G-W%V-%u')
sun = mon + timedelta(days=6)
print(mon.strftime('%Y-%m-%d'))
print(sun.strftime('%Y-%m-%d'))
"
```

### 2. Extract source material

**Weekly reports**: prefer existing daily reports as input. If every day in the Mon–Sun range either has a `YYYY-MM-DD.md` in the output directory or no commits, read those dailies and synthesize the weekly from them — the dailies have already done the commit-grouping work, so this is faster and produces a more coherent narrative. Fall back to `git log` for any uncovered days, then merge.

**Daily reports** (and weekly fallback for uncovered days): extract commits from the default branch (`main`, else `master`).

```bash
git log <default-branch> --first-parent --no-merges \
  --after="START 00:00:00" --before="END 23:59:59" \
  --date=short --format="%h|%cd|%s"
```

`START` and `END` are the first and last day of the range, as `YYYY-MM-DD`. Always give the times. A date without a time means that date at the current clock time, so `--after=<day before>` pulls in commits from the evening before and the morning after.

Read the default branch, not `--all`. When work is squash-merged and the feature branch is kept, `--all` shows each change twice: once as the branch's commits, once as the squash commit. The default branch is what shipped. Work that exists only on an unmerged branch is left out; if the user asks for it, add `git log <branch> --not <default-branch>` for that branch and label it "in progress".

If zero commits are found (and no daily report exists for the range), tell the user and stop.

### 3. Check for milestones (optional)

Read `docs/MILESTONES.md` if it exists. List a milestone only when a commit in the range names it, its number, or the feature it describes. If unsure, leave it out. If no milestones file exists, or none matches, omit the Milestone(s) line.

### 4. Read project TODOs (optional)

Read `docs/TODO.md` if it exists. Extract pending items — lines that do NOT start with `DONE` and are not empty lines, section headers (`##`, `###`), or the top-level title (`#`).

- Group items by their nearest preceding section header (e.g., `## 2026-02-10`)
- Items before any section header go under a general "Ungrouped" heading
- List the first 5 items in file order, counted across all groups, and append: `*...and N more pending items*` when more exist
- If no TODO file exists or no pending items found, omit the Pending TODOs section entirely

### 5. Group commits into Changes

- Merge related commits into logical bullets (don't mirror commits 1:1)
- Drop noise (formatting, typos, merge commits) unless that's all there is
- Active past tense: "Fixed...", "Added...", "Refactored..."
- Order by significance
- Target: 3–8 bullets (weekly), 1–4 (daily)
- **Thematic sub-headers**: When there are 5+ bullets spanning distinct themes, group them under `###` sub-headers (e.g., `### Exports`, `### Bug Fixes`, `### Infrastructure`). Use short, descriptive names. On light days (1–4 bullets), keep a flat list — sub-headers add noise when there's little to organize.

### 6. Write Summary

One paragraph, 2–4 sentences. Synthesize the Changes into a narrative. Mention the most impactful work first. No filler words, no pleasantries.

### 7. Assemble and write

```markdown
# [Weekly|Daily] Report — YYYY-MM-DD to YYYY-MM-DD   ← daily: just YYYY-MM-DD

**Milestone(s):** #N — Name, #M — Name

## Summary
[paragraph]

## Changes
### [Theme 1]  ← only when 5+ bullets span distinct themes
- [bullets]
### [Theme 2]
- [bullets]

## Pending TODOs
- [pending items from docs/TODO.md, grouped by section]

```

Output path: `docs/dev-reports/` (create if needed) or user-specified path.

## Common Mistakes

- Giving `--after` / `--before` a date without a time; git then uses the current clock time and the range leaks into the neighbouring days
- Using `git log --all` in a squash-merge repository; every change is counted twice
- Listing every commit as a separate Change bullet instead of grouping
- Writing management-speak summaries — keep it technical and direct
