# Audit: which steps of the `my` and `kit` skills can be scripts

**Status:** current, 2026-10-14. Sixteen findings (S1 to S16) on steps that fixed rules decide, plus one likely live bug (B1). They are rows 41 to 52 in `ROADMAP.md`, section "Scripted skill steps", and rows 33 and 34; see "Where these went".

## How to read this

- **Subject:** every `SKILL.md` and supporting file under `plugins/my/skills/`
  and `plugins/kit/skills/`, the command templates in `plugins/*/commands/`, and
  the `my:summarizer` agent. The existing scripts in `plugins/*/bin/` and
  `plugins/*/hooks/` were read only for their usage text, to see what they
  already do.
- **Related documents:** `ROADMAP.md` rows 9, 30, 31, 33 and 34, which several
  findings overlap; `docs/reports/2026-10-12-handoff-instructions-audit.md`, the
  audit those rows come from; `docs/plans/2026-10-13-roadmap-auto-runs-spec.md`,
  the approved spec of row 9.
- **The test.** A step can become a script when all three hold:
  - its inputs are files, git output or arguments;
  - fixed rules decide its output;
  - it needs no tool call that only the model can make, such as `Agent`,
    `AskUserQuestion`, `PushNotification` or `LSP`.

  When a step mixes both kinds, the script does the preparation and prints a
  result. The skill keeps the question to the user or the subagent call.
- **Ranking:** how often the step runs, how easy the prose is to get wrong, and
  evidence that it already went wrong (roadmap rows).

## B1. Shell positional arguments in skill text

Roadmap row 33 records that Claude Code replaces `$1` and `$2` in a loaded
skill's text with the skill's arguments. This audit did not re-test that claim.
If it holds, it breaks two places:

- `plugins/my/skills/handoff/SKILL.md` line 817: the parallel squash-merge
  command uses `"$1"` and `"$2"`. Row 33 already covers this.
- `plugins/kit/skills/git-squasher/SKILL.md` lines 142–147: the `squash-todo.sh`
  example ends with `"$1"`. No row covers this one. With no arguments, `$1`
  becomes empty and `sed -i` gets no file. With the argument `main`, `sed` would
  try to edit a file named `main`.

Moving shell code out of skill text into `bin/` scripts removes this class of
bug. S1 and S7 do that for both places.

## High value

### S1. `my:handoff`: the parallel squash-merge as a script

Review stage step 8, sub-step 1, runs an inline `sh -c '…$1…$2…'` command.
Replace it with a script, or with a `-F <file>` option on `handoff-state.py
merge`. Resolves rows 33 and 34 together.

### S2. `my:handoff`: the start checks

All of these are git and `ls` queries:

- working out `<slug>`, `<name>` and `<base>`;
- the status line, `approved`, "no plan yet", "plan committed on base", "no
  branch `*/<slug>`" and "no worktree";
- restart detection: the `Task:` trailers, "a review report is already added",
  and the list of uncommitted files.

A subcommand of `handoff-state.py` could print the derived values and the first
failed check. Row 9 is changing that file, so do this after row 9. It also
shrinks the text that rows 30 and 31 plan to split.

### S3. `my:handoff`: a validator for the Delegation section

The Delegation section says what an auto run may decide alone. Its grammar is
exact: four keys, fixed values, compared by exact name. Start check 3 in auto
mode checks it in prose. It could be part of S2.

### S4. A parser for the "Parallel runs" section

`my:handoff`, `my:status` step 3, `kit:commit` and `my:architect` all read this
section, and no script parses it. The model works out `<n>` (the `--max` value)
and the rule "pass `--docs-paths` only when the list differs from the default"
by hand. A subcommand of `handoff-state.py` could print the values ready to use.

### S5. Preparation for `my:soundness-review` and `my:spec-review`

Steps 0 to 2 of both skills:

- sorting the arguments into range, plan path and description;
- writing the merge-base diff to a file;
- the 8-row mode table;
- the review file name, with the `-2`/`-3` rule for names already taken;
- filling the placeholders in the prompt template.

These skills run at the end of every branch and for every spec, so this is the
most frequent win. The skill keeps the `AskUserQuestion` call and the `Agent`
call.

### S6. `git-fold-fixups.py list <path>`

It would print the waiting fixups for one document. `my:handoff` finds them by
hand in three places: Plan stage step 8, Code stage sub-step a, and Review stage
sub-step 3. The script already has `waiting_fixups()`.

## Medium value

### S7. `kit:git-squasher`: plan and apply scripts

Steps 1 to 3 are fixed rules: the range, the backup branch, the safety checks,
the prefix classes, grouping into runs, skipping single commits, and the
mixed-author rule. An apply script that reads the messages from a file fixes B1
for this skill and drops the "no single quote in a message" rule. The model
still writes the combined messages.

### S8. `my:clean-plans`: steps 1, 2, 4 and 6

- picking the candidates by name pattern;
- the date from git, falling back to the file's modified time;
- the rename, with `git mv` for tracked files and `mv` otherwise;
- repointing every link to the old name.

The "move a doc and fix its links" part is also needed by "Moving a document" in
`global/rules/docs-layout.md` and by `my:roadmap-management` rule 8. The model
still sorts each file into rename or delete.

### S9. `kit:setup`: fact discovery and the `settings.json` merge

Step 1 collects the scopes, the test command, the plans index, the remote and
the Parallel runs section. The merge sets two `enabledPlugins` keys and keeps
the rest of the file. The "already set up" check can reuse what
`method-guard.py` already parses. Removing copied rules (step 2) stays a
judgment.

### S10. `kit:dev-reports`: dates, commits and TODOs

The ISO week range, the Monday rule, the list of days with commits since the
last daily report, the `git log` with full times, and the TODO extraction
("first 5, then …and N more"). The model still groups the commits and writes the
summary.

### S11. `kit:clean-gone-branches`

Everything except the approval is fixed: fetch, list `[gone]` branches, check
worktrees for uncommitted work, build the table, then delete.

## Low value

### S12. `my:roadmap-management`: next row number and a link check

The next free row number, and a link check for `ROADMAP.md` and `CHANGELOG.md`:
`.html` targets, `../other-repo` paths and dead links. `status-scan.py` already
parses the rows.

### S13. `my:status`: gates, file lists and overlap

Steps 5 and 6, and the overlap test in "What can run in parallel". Row 9's
approved spec reuses these steps as model judgment, so scripting them changes
that spec. Wait until row 9 is done.

### S14. `my:architect`: draft schema and contrast checks

The heading list of each candidate draft (step 5) and the contrast check between
candidates (steps 3 and 5). Small rules, and the skill runs rarely.

### S15. `kit:tune-claude-instructions`: a lint for hints

A script could report hints for the model to judge: `Grep`, `Glob` or `LSP` in a
subagent prompt (Pattern G), `rebase -i` without an editor set,
`AskUserQuestion` with no fallback (Pattern I), and the amount of ALL-CAPS
emphasis (Pattern J).

### S16. Small items

The checks in `kit:push`, the case 1 and case 3 commands in `kit:tutor` setup,
and steps 1 and 3 of the `my:summarizer` agent.

## What stays as judgment

- choosing forces, candidates and the evaluation in `my:architect`;
- the content of every review, and sorting findings into gate, risk or fix;
- sorting files in `my:clean-plans`;
- whether a change belongs in the changelog, and the wording of roadmap rows;
- squash and commit messages, and how to group a commit;
- the report text in `my:status`;
- `kit:briefing`, `kit:de-slop`, `kit:optimize-prompt`, the two Laravel
  commands, and the teaching in `kit:tutor`.

## Where scripts go, and the cost

- Scripts for `my` skills go in `plugins/my/bin`. They are on `PATH` only while
  `my` is on, so a helper that a `kit` skill needs goes in `plugins/kit/bin`.
  S7, S9, S10 and S11 belong in `kit`.
- Each script needs a `unittest` file in that plugin's `tests/` folder, as the
  existing scripts have.
- Each script is new code to maintain. When a script lands, delete the prose it
  replaces in the same change. Otherwise the rules exist twice and drift apart.
- Changes to `my:handoff` need a headless rehearsal of a supervised and an auto
  run, as row 30 says.

## Where these went

| Finding | Where |
| --- | --- |
| B1 | Row 41 "`git-squasher` loses `$1`" (the `kit` half); row 33 has the `my:handoff` half. |
| S1 | Rows 33 "Skill text loses `$1` and `$2`" and 34 "Merges read a message file". |
| S2, S3 | Row 43 "`handoff` start checks as a script". |
| S4 | Row 42 "Parallel runs parser". |
| S5 | Row 45 "Review preparation as a script". |
| S6 | Row 44 "`git-fold-fixups.py list <path>`". |
| S7 | Row 46 "`git-squasher` plan and apply scripts". |
| S8 | Row 47 "`clean-plans` moves by script". |
| S9 | Row 48 "`setup` facts by script", folded into row 68 "Methods as plugins" (then "Launch method switch") on 2026-10-18. |
| S10 | Row 49 "`dev-reports` dates and TODOs by script". |
| S11 | Row 50 "`clean-gone-branches` as a script". |
| S12 | Row 51 "Roadmap number and link check". |
| S13 | Row 52 "`status` gates and overlap by script". |
| S14 | No action: the rules are small, and `my:architect` runs rarely. |
| S15 | No action: the script would give hints only, and the skill already reads every file in full. |
| S16 | No action: each step is a few lines, and none has gone wrong. |
