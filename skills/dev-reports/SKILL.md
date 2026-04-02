---
name: dev-report
description: >
  Use when the user asks to generate a developer report, weekly report, daily report,
  dev log, changelog, or activity summary from git history. Also when invoked via /dev-report.
---

# Developer Report Generator

Generate concise developer reports from git history. No fluff — developer audience.

## Arguments

```
/dev-report weekly                       # weekly, current/last week
/dev-report weekly 2026-W10              # specific ISO week
/dev-report weekly 2026-W10 path/to/dir  # custom output path
/dev-report today                        # today
/dev-report daily                        # all days since last report
/dev-report daily 2026-03-20             # specific day
```

Defaults: type=today, date=today, path=docs/reports/

## Steps

### 1. Parse arguments and determine date range

- **Today**: (default): Filename: `YYYY-MM-DD.md`. Range: single day
- **Daily**: Filename: `YYYY-MM-DD.md`. Range: single day.
- **Daily**: Filename: `YYYY-MM-DD.md`. Range: single day.
- **Weekly**: ISO week. Filename: `YYYY-WNN.md`. Range: Monday–Sunday.

When in doubt use current ISO date/week. If today is Monday and current week has no commits, use previous week.

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

### 2. Extract commits

```bash
git log --all --no-merges --after="DAY_BEFORE_START" --before="DAY_AFTER_END" \
  --date=short --format="%h|%ad|%s"
```

Boundaries are exclusive — offset by one day. If zero commits found, tell the user and stop.

### 3. Check for milestones (optional)

Read `docs/MILESTONES.md` if it exists. Match commits against milestone descriptions to identify relevant milestones. If no milestones file, omit the Milestone(s) line.

### 4. Read project TODOs (optional)

Read `docs/TODO.md` if it exists. Extract pending items — lines that do NOT start with `DONE` and are not empty lines, section headers (`##`, `###`), or the top-level title (`#`).

- Group items by their nearest preceding section header (e.g., `## 2026-02-10`)
- Items before any section header go under a general "Ungrouped" heading
- list the first 5 and append: `*...and N more pending items*`
- If no TODO file exists or no pending items found, omit the Pending TODOs section entirely

### 5. Group commits into Changes

- Merge related commits into logical bullets (don't mirror commits 1:1)
- Drop noise (formatting, typos, merge commits) unless that's all there is
- Active past tense: "Fixed...", "Added...", "Refactored..."
- Order by significance
- Target: 3–8 bullets (weekly), 1–4 (daily)

### 6. Write Summary

One paragraph, 2–4 sentences. Synthesize the Changes into a narrative. Mention the most impactful work first. No filler words, no pleasantries.

### 7. Build commit table

Include ALL commits (even noise) in the table:

```
| Hash | Date | Message |
|------|------|---------|
| `abc1234` | Mar 14 | commit message here |
```

Date format: `Mon DD` (e.g., `Mar 14`, `Dec 03`).

### 8. Assemble and write

```markdown
# [Weekly|Daily] Report — YYYY-MM-DD to YYYY-MM-DD

**Milestone(s):** #N — Name, #M — Name

## Summary
[paragraph]

## Changes
- [bullets]

## Pending TODOs
- [pending items from docs/TODO.md, grouped by section]

## Commits
| Hash | Date | Message |
|------|------|---------|
| `hash` | Mon DD | message |
```

Output path: `docs/reports/` (create if needed) or user-specified path.

## Common Mistakes

- Using `--since`/`--until` instead of `--after`/`--before` (same behavior, but be consistent)
- Forgetting the one-day offset on boundaries (git treats them as exclusive)
- Listing every commit as a separate Change bullet instead of grouping
- Writing management-speak summaries — keep it technical and direct
