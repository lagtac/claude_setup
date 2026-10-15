# Audit: what approved specs missed, and what a hardened spec must cover

**Status:** current, 2026-10-14. Sorts 262 findings from six finished or running rows by whether a harder spec could have prevented them; its findings went to `ROADMAP.md` rows 53 and 55, see "Where these went".

## How to read this

- **Question.** After a spec is first written, later stages keep finding problems: later spec reviews, the plan review and the end-of-branch code reviews. Which of those problems could a harder spec have prevented, and by which check?
- **Why.** The user is thinking about `my:draft-spec`, a skill that writes a fast draft and hardens it before approval. "Hardened" means: it survived review rounds, it is checked against the repo, every decision is signed off, it is ready for auto mode, and the end-of-branch reviews find less to fix. This audit tells what such a skill has to check.
- **Rows read.** 13 "`my:handoff auto`", 14 "Parallel auto runs", 15 "`my:status`", 16 "Swappable methods", 32 "`locked-commit.py`", and 9 "Start auto runs from roadmap rows" (spec and plan stages only; its code is not reviewed yet). Each row's spec, reviews, plan, plan review, code reviews and merge commits were read in full.
- **Method.** One subagent per row (rows 15 and 32 shared one) sorted every finding into one class, using one shared brief. The per-row tables are in the appendix.
- **Classes.**
  - **G (grounding):** the spec said something false or unchecked about the repo or a tool. Running a command at draft time would have caught it.
  - **A (adversarial design):** a design gap that a hostile reader of the spec alone could find: an edge case, a failure mode, a race, a contradiction, unclear ownership of state.
  - **D (decision):** a choice that belonged to the user, left open, made silently, or made on a false premise.
  - **E (editorial):** wording or format; it would not change the code.
  - **P (plan or code only):** the spec was right; the plan or the code was wrong.
  - **T (test design):** a missing or weak test that the spec could have prevented by stating it.

## Limits of the data

- **The bug-finder writes no report.** The `/code-review` findings of rows 13, 14, 15, 16 and 32 were rebuilt from fix commits and Risk sections. They have no severity, and which reviewer found each one is a guess.
- **One classifier per row.** Different subagents sorted different rows. Nobody checked that they drew the class lines the same way. Treat counts as rough.
- **Row 16 counts without duplicates** (58 of 62 rows). The other rows count a defect found twice as two findings (row 14 names four such pairs).
- **Row 9 is not finished.** Its code stage is running. It adds spec and plan findings only.

## Results

### Counts per class

| Row | Findings | G | A | D | E | P | T |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | 47 | 6 | 21 | 1 | 1 | 16 | 2 |
| 14 | 73 | 25 | 25 | 1 | 5 | 15 | 2 |
| 15 and 32 | 56 | 18 | 23 | 1 | 3 | 10 | 1 |
| 16 | 58 | 21 | 17 | 2 | 10 | 6 | 2 |
| 9 | 28 | 10 | 10 | 1 | 1 | 4 | 2 |
| **All** | **262** | **80** | **96** | **6** | **20** | **51** | **9** |

### Findings after the first spec review

The first spec review is the baseline: it is what a first draft misses. Everything after it is what the approved spec still missed. Rows 13, 14, 15, 16 and 32 have both a code stage and this split:

| Row | Later findings | Preventable at spec | Partly | Not |
| --- | --- | --- | --- | --- |
| 13 | 38 | 13 | 13 | 12 |
| 14 | 52 | 33 | 10 | 9 |
| 15 and 32 | 37 | 19 | 9 | 9 |
| 16 | 49 | 24 | 14 | 11 |
| **All** | **176** | **89 (51%)** | **46 (26%)** | **41 (23%)** |

Row 9 has 15 findings after its first spec review. Of all 28, its subagent judged 23 preventable and 2 partly preventable.

### Findings decided by the user

The documents record 66 findings that went to the user: 10 (row 13), 30 (row 14), 1 (rows 15 and 32), 11 (row 16) and 14 (row 9). Rows 15 and 32 sent 3 more to the author with no record of who chose.

## What the numbers say

1. **Two thirds of all findings are G or A** (176 of 262). Both can be found from the spec and the repo, with no code. G needs commands run against the real system; A needs a hostile reading.
2. **True user decisions are rare.** Only 6 of 262 findings are class D. Yet 66 findings went to the user. In other words, most questions to the user were about how to fix a G or A finding, not about what the user wants. The method sends every `design` finding to the user, so each gap that survives the draft becomes a question later.
3. **Half of what the approved spec missed was preventable at spec time** (89 of 176), and a quarter more partly. A harder spec would not have reached zero findings: about a quarter (41) needed the plan or the code to show.
4. **P findings are a fifth of the total** (51). These are plan or code mistakes. A spec prevents them only by naming the tests and their assertions.
5. **Fixes cause findings.** In row 9, six of 28 findings came from an earlier fix that nobody checked again. Row 9's two plan-stage questions both came from fix text the spec copied from a review. In row 13, the fix round made a new finding. A fix needs the same checks as the first draft.
6. **What needed something to run falls into two kinds.**
   - **Our own code.** The P findings are bugs in code the spec did not describe, such as ref-name ambiguity or a traceback on an unusual git layout. A spec prevents some of them only by naming a test.
   - **The host programs: Claude Code, git, tmux, a project's hooks.** Most of these were probes any reviewer could run in the scratchpad at draft time, such as how a shell ends a child process or how git's background cleanup holds a lock (row 14). A few appeared only in a rehearsal of the finished feature: inside a session, the installed plugin's `bin/` comes before the `--plugin-dir` copy on `PATH` (row 14); in `stream-json` output a hook event comes before the init line, and a project's broken pre-commit hook failed the setup commit (row 16); a fold suggestion appeared only on a repo with worktrees on top of the fixup targets (row 15). Some were never settled: how the Bash tool ends a timed-out command (row 14), whether Claude Code writes `~/.claude.json` atomically (row 16), and a silent stall after an API connection error (row 13).

## Draft-time checks that would have caught the most

The same checks appear in every row. Each item names the rows where it would have caught findings; the appendix gives the finding numbers.

1. **A failure table.** For each step that changes git, a state file or `main`: what a crash or a failed command leaves behind, what the next check sees, and where a restart goes on. Rows 13, 14, 15, 32 and 9. This is the largest group.
2. **An ownership table.** For each stored field or shared value: who writes it, who reads it, who deletes it, and in which modes (supervised, auto, parallel). Rows 13, 14, 9 and 16.
3. **Run every claim against the real system.** Run each shell snippet, rule, count and acceptance command in the repo or a fixture repo. Test each Claude Code or git behaviour the design depends on in the scratchpad before approval, not in a "task 0" after it. All six rows.
4. **A full reference sweep.** `git grep` every caller, step number, short name and phrase the change touches, tests included. Quote each existing section the spec hooks into, instead of restating it. Rows 14, 15, 32, 16 and 9.
5. **Hostile inputs.** For every input the design parses or every file it reads: empty, malformed, duplicated, quoted, overridden in a `.local` file, edited by another session, run twice. Rows 13, 14, 15, 32 and 16.
6. **Tests stated in the spec.** Each test with its setup, its assertion and its exit code, written so that it fails when the feature is missing. All six rows.
7. **Re-check every fix.** A fix taken from a review goes back through checks 1 to 6 before approval. Rows 9 and 13.
8. **Probe the host programs before approval.** List each behaviour of Claude Code, git, tmux or the target repos that the design depends on, and test each one in the scratchpad or a copy of the real repo. Row 16 did this in a "task 0" after approval, and it found findings #10 to #13; row 14's reviewers ran such probes during review. A probe cannot replace the rehearsal of the finished feature, which still found new things in rows 14, 15 and 16.

## What this means for `my:draft-spec`

This section is input to the brainstorming, not a design.

- **Most hardening needs no user.** Checks 1 to 8 are work an agent can do from the spec and the repo. They target G and A, which are two thirds of all findings.
- **The user's questions can shrink without losing anything.** Class D findings are rare, so a draft that has already closed its G and A gaps leaves few questions, and those are real decisions.
- **A hardened spec still has a floor.** About a quarter of later findings need the plan or the code. The spec cuts the P findings only by stating its tests, and the rehearsal of the finished feature stays necessary.
- **The skill must loop.** Fixes cause new findings, so one review round is not enough. The draft is hardened when a round finds nothing new.

## Where these went

| Part of this audit | Row |
| --- | --- |
| The draft-time checks 1 to 8, and "What this means for `my:draft-spec`" | Row 53 "`my:draft-spec`", reframed from "Draft specs in forks". |
| Few findings are real decisions; most questions to the user were about fixes | Row 55 "Decisions that go back to the user", which rows 53 and 54 use. |
| The bug-finder writes no report, so its findings cannot be counted | No action: a limit of this audit, not a defect found in a row. |

## Appendix: per-row tables

The tables below are the subagents' reports, unchanged except for heading levels.

### Row 13: `my:handoff auto` (autonomous run): what the approved spec missed

Sources read in full: the spec, its one review (`-spec-review.md`), the plan, the plan review,
the soundness review and its re-review (`-feat-autonomous-run-review.md`, `-review-2.md`). Also read:
the commit bodies of `dee3356` (spec), `df5a277` (plan), the branch `feat/autonomous-run` (fix round
commits `1de30e2`, `c70ccc7`, `8d29438`; Risk commits `19101e5`, `a7aedd2`; `389f843`) and the squash
`39737e1`.

Notes on the sources:

- The spec has only one review. Its fixes went into the spec before the first commit (`dee3356`),
  so git holds no pre-review draft. Rows 1 to 9 are the baseline.
- No report file exists for the bug-finder (`/code-review`). Its findings (rows 28 to 35, 39 to 47)
  are rebuilt from the fix-round commit bodies and the Risk entries that name "the end-of-branch
  review" or "final re-review", minus what the soundness reports list. Their severity is not
  recorded, so the table says `unrated`.
- Rows 19 to 22 are not review findings. They are gaps the plan had to fill: "Decisions this plan
  adds", which the plan review names "six decisions the spec left open". Two of the six are
  counted elsewhere (decision 3 in row 14, decision 5 in row 11).

#### Row 13: 1. Findings

| # | Stage | Finding (one line) | Severity | Class | Preventable at spec? | What the spec would have needed (one line) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | spec-review-1 | `git merge --abort` fails after `git merge --squash` (no `MERGE_HEAD`), leaving `UU` paths | Warning | G | yes | Run each recovery git command once in a scratch repo and record the result |
| 2 | spec-review-1 | `check` for `next=merge` reads `squash_subject`, which D6 set only after the merge | Warning | A | yes | A table: each state field, the step that writes it, the steps that read it |
| 3 | spec-review-1 | D3 "no state file" check blocks the run's own later stages and every resumed stage | Warning | A | yes | For each start check, say which entry forms run it: typed, launched, resumed |
| 4 | spec-review-1 | Resume restarts plan, code, review from step 1; no restart points inside a stage | Warning | A | yes | A restart table: per stage, what may be done already, how to see it, where to go on |
| 5 | spec-review-1 | Resume runs the steps on `main` in the user's session: no `MY_AUTORUN`, no `<name>` | Warning | A | yes | List every session that can change `main`; state that each one has the guard |
| 6 | spec-review-1 | `auto code` commits and folds inside the start checks; no fold `check`; dirty `main` unhandled | Warning | A | yes | Check each new step against docs-layout steps 4 and 9, with an outcome per exit code |
| 7 | spec-review-1 | D1 overturns the architecture brief's Decision (trigger) without saying so | Suggestion | D | yes | Compare each Decision with the brief's settled Decision; name every change and its approval |
| 8 | spec-review-1 | Guard matches "contains `git … push`", so commit messages and heredocs get blocked | Suggestion | A | yes | List look-alike inputs that must pass next to the ones that must block |
| 9 | spec-review-1 | `Monitor` also runs shell commands; matcher was `Bash` only | Question | G | yes | List from the Claude Code docs every tool that runs a shell command |
| 10 | plan-review | Rehearsal "resume at the fold" cannot be reached: fixture spec already `approved`; `-u` upstream makes fold refuse | Warning | T | partly | Give each rehearsal scenario its preconditions: uncommitted `approved` edit, dirty `main`, no upstream |
| 11 | plan-review | No rule for how a `run auto` session tells a restart from a fresh start | Warning | A | yes | Name the signal a stage reads to know it is a restart |
| 12 | plan-review | Run a7's expected output depends on an unstated order of two start checks | Warning | P | no | - |
| 13 | plan-review | `shlex.punctuation_chars` cannot be set after the object is built | Suggestion | P | no | - |
| 14 | plan-review | Expected outputs wrong: Launch fallback starts with `cd`; resume session's `<name>` undefined | Suggestion | P | partly | Name the resume session's own `<name>` (row 5 raised it) |
| 15 | plan-review | Rehearsal expects `MY_AUTORUN` in the user's own launch window too | Suggestion | P | no | - |
| 16 | plan-review | `Task: <N>` trailer assumes numbered tasks; Medium Tasks may be unnumbered | Suggestion | P | no | - |
| 17 | plan-review | Task 6 commit scope breaks the plan's own scope rule | Suggestion | E | no | - |
| 18 | plan-review | Unverified that `Monitor` puts its shell text in `tool_input.command` | Investigation | G | yes | Capture one real `Monitor` hook payload in the draft-time spike |
| 19 | plan-review | Plan gap: who creates the state file, since D3 needs it before the first stage runs | Plan gap | A | yes | Same table as row 2: writer and moment for the file itself |
| 20 | plan-review | Plan gap: which stage, window name and start check run `next` = merge, fold, done | Plan gap | A | yes | Map every `next` value to a stage, a window name and its start check |
| 21 | plan-review | Plan gap: a hand-typed `run auto` would run with the guard off | Plan gap | A | yes | Make "`MY_AUTORUN` equals the slug" a start check of every `run auto` session |
| 22 | plan-review | Plan gap: where `handoff-state.py` gets `<base>` | Plan gap | A | partly | Say once where each shared value (the base branch) comes from |
| 23 | code-review (soundness) | Crash between `git merge --squash` and its commit leaves a staged squash `check` misses; rerun fails | Warning | A | yes | A crash table: one row per gap between two steps on `main`, with what `check` sees |
| 24 | code-review (soundness) | Resume clears `stopped` without showing it; an exit-3 fold is passed over | Warning | A | yes | Rule: resume shows the last stop reason and does not pass a stop that needs the user |
| 25 | code-review (soundness) | `check` writes `next` before it checks the next step, so a refused check changes state | Suggestion | P | partly | Rule: `check` writes nothing when it exits 1 |
| 26 | code-review (soundness) | Helper's `<base>` (checked-out branch) can differ from the skill's `<base>` (project rules) | Investigation | A | partly | Same as row 22 (moved to Risk) |
| 27 | code-review (soundness) | An API connection error leaves a stage idle with no stop mark (seen in rehearsal; user accepted) | Decision | A | partly | A rule for a stage that neither stops nor finishes, or a stated limit in the Goal |
| 28 | code-review (bug-finder) | Guard: `shlex` treats `#` as a comment and eats the newline, so a push on the next line passed | unrated | G | yes | Prototype the parse rule on the test list, including comment lines, before approval |
| 29 | code-review (bug-finder) | Guard: a leading `if`, `do`, `then` or `{` hid the `git` word | unrated | A | yes | List the shell positions where a command word can follow a keyword |
| 30 | code-review (bug-finder) | Guard: `--git-dir <value>` took the value as the subcommand, so `push` passed | unrated | G | yes | Take git's global options from `man git`, with which ones take a separate value |
| 31 | code-review (bug-finder) | Guard: a quoted `<<WORD` is taken for a heredoc, so later lines are not checked (Risk) | unrated | P | partly | A test case: heredoc detection must respect quotes |
| 32 | code-review (bug-finder) | Resume after the merge launched a review stage whose start checks need the removed worktree | unrated | A | yes | For each `next` value, list which start checks still hold |
| 33 | code-review (bug-finder) | A branch left by a finished run was taken for a code restart (branches are never deleted) | unrated | P | partly | Say restart detection reads the state file, not leftover branches |
| 34 | code-review (bug-finder) | `check` at worktree-remove and done skipped required fields and the one-squash-commit test | unrated | P | no | - |
| 35 | code-review (bug-finder) | `handoff-state.py` copies code from `git-fold-fixups.py`; copies can drift (Risk) | unrated | P | no | - |
| 36 | re-review | New `history rewritten` check refuses resume after a fold that succeeded (Risk) | Warning | A | partly | A crash-table row "after the fold, before `set next=done`" with a fold-done fact |
| 37 | re-review | `commenters=""` makes a comment with an apostrophe fail to parse, so it is blocked; Risk text wrong | Suggestion | P | no | - |
| 38 | re-review | The full-cycle rehearsal ran before the fix round; fixes rest on unit tests only | Investigation | T | partly | Testing: run the rehearsal on the branch head after the last fix |
| 39 | re-review | Guard: a push inside `$(...)` in double quotes, or backticks, passes (Risk) | unrated | A | partly | Decide fail-closed or parse; list command substitution as a case |
| 40 | re-review | Guard: wrappers (`timeout`, `nice`, `xargs`, `time -p`), `>log git push`, line continuation pass (Risk) | unrated | A | partly | Same adversarial list, with an outcome per form |
| 41 | re-review | Guard: git's `--config-env` option passes (Risk) | unrated | G | yes | Same as row 30: the full git global-option list |
| 42 | re-review | Guard: `<<\EOF` and a tab before a plain end word are misread (over-block only) (Risk) | unrated | P | no | - |
| 43 | re-review | A clean fix round, then a crash, blocks resume: a committed report counts as "fix round ran" (Risk) | unrated | P | partly | Same as row 11: the restart signal lives in the state file |
| 44 | re-review | With the branch gone, an older commit with the same subject is taken for the merge (Risk) | unrated | A | yes | Identify the squash commit by something unique, not only its subject |
| 45 | re-review | Detached HEAD or invalid JSON in the state file gives a traceback with no reason (Risk) | unrated | P | no | - |
| 46 | re-review | A missing branch prints two mismatch lines that say the same thing (Risk) | unrated | P | no | - |
| 47 | re-review | The hook starts Python on every `Bash` call in every session (Risk) | unrated | P | no | - |

#### Row 13: 2. Counts

##### Row 13: Per class (all 47 rows)

| Class | All rows | After spec-review-1 (rows 10 to 47) |
| --- | --- | --- |
| G grounding | 6 | 4 |
| A adversarial design | 21 | 15 |
| D decision | 1 | 0 |
| E editorial | 1 | 1 |
| P plan/implementation | 16 | 16 |
| T test design | 2 | 2 |
| **Total** | **47** | **38** |

##### Row 13: Per stage

| Stage | Rows | Count |
| --- | --- | --- |
| spec-review-1 | 1 to 9 | 9 |
| plan-review | 10 to 22 (4 are plan gaps) | 13 |
| code-review (soundness) | 23 to 27 | 5 |
| code-review (bug-finder) | 28 to 35 | 8 |
| re-review | 36 to 47 (3 soundness, 9 bug-finder) | 12 |

##### Row 13: Preventable at spec (rows 10 to 47)

yes: 13. partly: 13. no: 12.

#### Row 13: 3. Findings the user decided

10 in total.

- Rows 1 to 9: the spec review's status says the user accepted all six Warnings, both Suggestions
  and the `Monitor` question. Three of them were marked "Decision for the author" and were real
  choices: row 4 (restart points), row 6 (where the `approved` commit goes) and row 7 (the trigger
  word that overturns the brief).
- Row 27: the user accepted the silent stall after an API error as a known limit before the merge.

Rows 36 to 47 went into Risk under the one-fix-round rule, not by a recorded user choice.

#### Row 13: 4. Patterns: checks at draft time that would have caught the most

1. **A crash and restart table for every step that changes `main` or the state file.** One row
   per gap between two steps: what git holds, what the state file says, what `check` sees, where
   resume continues. Would have caught rows 2, 4, 11, 23, 32, 36, 43 and 44. Row 24 also fits:
   the table would add a "stopped" column. This is the largest group. Each review found the next
   unchecked gap, and the fix round made a new one (row 36).
2. **An ownership table for state and entry forms.** For each state field: who writes it and when.
   For each entry form (user-typed, launched by a stage, launched by resume, hand-typed `run auto`):
   which start checks run, which window name it gets, whether the guard is on. Would have caught
   rows 2, 3, 5, 14, 19, 20, 21, 22 and 26.
3. **Run a prototype of the guard's parse rule on an adversarial shell corpus before approval.**
   The corpus: comments, keywords (`if`, `do`, `{`), value options (`--git-dir`, `--config-env`),
   `$(...)` and backticks, wrappers (`timeout`, `xargs`, `env`), leading redirects, line
   continuation, heredoc forms (quoted, `<<-`, `<<\EOF`). The spec should record, per form, block or
   pass, and whether the guard fails closed. Would have caught rows 8, 28, 29, 30, 31, 39, 40, 41
   and 42, and shown the trade-off behind row 37.
4. **One command per tool fact.** Run every git recovery command in a scratch repo (row 1). Take
   the list of git global options from `man git` (rows 30, 41). Take the list of shell-running
   tools and one real hook payload per tool from Claude Code (rows 9, 18). The spec's own spike
   covered `git push` forms under `Bash` only.
5. **Rehearsal scenarios with preconditions, run on the final branch head.** The spec named "stop
   at the fold" but not how a fixture gets there, and did not say the rehearsal runs after the fix
   round. Would have caught rows 10 and 38, and made row 15's expectation exact.

#### Row 13: 5. Findings only the running code could reveal

- **Row 27, the silent stall after an API connection error.** It is how a live Claude Code session
  behaves when the network fails mid-response: the window sits at the prompt, with no hook, no
  mark and no stop. No document or command at draft time shows it. A hostile reader could only ask
  the general question "what if a stage neither stops nor finishes?", which is why it is "partly".
- **Memory use** (not in the table, because no review raised it; the rehearsal recorded it in
  Risk): four runs at once reached 13 `claude` processes and left 1.8 GB free on a 15 GB machine.
  Only a real multi-window run measures this.

Row 18 (the `Monitor` payload field) and row 23 (the staged squash) were confirmed by running
things. But a draft-time spike or a scratch repo would have shown them, so they are not in this
list.

### Row 14: Parallel auto runs — what the approved spec missed

Sources: the spec and its three reviews, the plan and its review, the two soundness reviews, and the branch `feat/parallel-auto-runs` (fix commits and the plan's Risk section). The squash-merge is 38f6c34.

#### Row 14: Notes on the sources

- **Timeline.** The spec's first commit (f866356) already held review 1, answered. Review 2 followed. Then commit 9a87dca rewrote the spec smaller: it cut the roadmap answer, `handoff-merge-file.py` and the fold script's `commit` mode. Review 3 reviewed the smaller spec. The spec became `approved` in the plan commit (473e67f). Review 1 is the baseline. Reviews 2 and 3 came later.
- **Decision numbers.** Reviews 1 and 2 cite the old D numbers, which do not match the final D1 to D8. The rows below name the topic, not a D number, for those two reviews.
- **Mooted by the cut.** Eight findings were about parts that 9a87dca removed. Nobody fixed them: the part went away. They are marked "(mooted by the cut)".
- **Bug-finder rows are inferred.** Neither `/code-review high` round wrote a report file (commits 78a166f and 850ba6b say so). Rows 57 to 65 and 68 to 73 are rebuilt from fix commits and the plan's Risk bullets. Each such row names its source. Their severity is "unknown". Commit 3890035 mixes soundness fixes with bug-finder fixes, so the split of rows 59 to 62 between the two reviewers is a best guess.
- **NI** in the Severity column marks a "Needs Investigation" item, not a row of "Issues Surfaced".
- **Shipped spec text still holds three defects** that later stages found. They are at `docs/plans/2026-10-12-parallel-auto-runs-spec.md:157-162`: `git commit -m "<message>"` inside a single-quoted `sh -c` (rows 46, 53); "`git diff -- <paths>` … shows what it will stage", false for untracked files (row 54); "`git show --stat HEAD` after it", a race (row 60). So these are spec-text defects, not plan-only ones.

#### Row 14: 1. Findings

| # | Stage | Finding (one line) | Severity | Class | Preventable at spec? (yes/partly/no) | What the spec would have needed (one line) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | spec-review-1 | `checked_base` defined as the base tip lets B merge a combination nobody tested | Critical | A | yes | Define `checked_base` as the fork point; trace both merge orders |
| 2 | spec-review-1 | The `Max runs` start check runs in every `run auto` session and refuses the run's own later stages | Critical | G | yes | Read where SKILL.md runs the auto start checks (`:354-356`) |
| 3 | spec-review-1 | Rebase and merge-retry stops leave `next=review`; the restart rule then refuses ("fix round already ran") | Warning | G | yes | Trace each new stop row through the existing restart rule (`SKILL.md:301-305`) |
| 4 | spec-review-1 | The start check reads `ROADMAP.md`, which the spec itself rejected as an ownership leak (mooted by the cut) | Warning | A | yes | Check each decision against the reasons given for rejected options |
| 5 | spec-review-1 | The merge-file script commits with `commit-tree`, so zitamu's `pre-commit` hook never runs (mooted by the cut) | Warning | G | yes | List the hooks of each target project and say whether they run |
| 6 | spec-review-1 | Lock `main` covers the commit but not `git add`; `merge` would commit whatever is staged | Warning | A | yes | Name every write to the index and put each inside the lock |
| 7 | spec-review-1 | Isolation applied only in the code stage, but the review stage reruns the checks | Warning | A | yes | List every stage that runs a command in the worktree |
| 8 | spec-review-1 | The `commit`-mode undo (`reset --soft`) can drop a terminal commit that took no lock (mooted by the cut) | Warning | A | yes | Check each "safe because locked" claim against the unlocked writers the spec allows |
| 9 | spec-review-1 | `handoff-state.py` already uses exit 1 for every git error, so a new "conflict = 1" mislabels errors | Warning | G | yes | Read the script's existing exit codes before assigning new ones |
| 10 | spec-review-1 | `merge_retries` is never reset, so a resumed run stops again at once | Warning | A | yes | For each new counter, say when it resets |
| 11 | spec-review-1 | `check` for `next=done` reports `fixup waits`, so a fixup stuck behind a squash blocks resume forever | Warning | G | yes | Read `check`'s facts for each `next` value the change affects |
| 12 | spec-review-1 | `commit` mode folds without the project's pre-rebase check (mooted by the cut) | Warning | G | yes | Read the existing fold steps in SKILL.md before adding a new fold path |
| 13 | spec-review-1 | The lock rule goes in `docs-layout.md`, which loads only for `docs/plans/` paths | Warning | G | yes | Check each rule file's load scope before placing a rule there |
| 14 | spec-review-1 | Lock wait of 300 s exceeds the Bash tool's 120 s limit, so the timeout exit never fires | Warning | G | yes | State the Bash tool's timeout and size every wait below it |
| 15 | spec-review-1 | A stopped run holds a `Max runs` place, but no step ends an abandoned run | Warning | A | yes | For each state that counts against a cap, name how it leaves |
| 16 | spec-review-1 | The Isolation example uses a "run number" that nothing defines | Warning | A | yes | Define every placeholder the config may use |
| 17 | spec-review-1 | The merge-file script does not say where its base copy comes from (mooted by the cut) | Warning | A | yes | Name the source of every input a script takes |
| 18 | spec-review-1 | "Without the section, behaves exactly as today" is false: a second run starts today | Suggestion | G | yes | Check each "as today" claim against current SKILL.md |
| 19 | spec-review-1 | Blast radius misses three callers of the fold script (handoff README, root README, zitamu) | Suggestion | G | yes | Run `git grep` for each changed script name, in every target repo |
| 20 | spec-review-1 | What a Bash tool timeout does to the locked child (does the child keep the lock?) | NI | G | partly | Probe how the Bash tool kills a command, or record it as unknown in Risk |
| 21 | spec-review-1 | Which projects define the "pre-rebase check" the fold step names | NI | G | yes | `grep` the target projects for the term |
| 22 | spec-review-2 | Lock-busy and crash stops in the merge loop leave `next=review`, which restart refuses | Warning | A | yes | A table: each stop and crash point, the `next` it leaves, and what resume does |
| 23 | spec-review-2 | A refused squash commit leaves a staged squash in the shared checkout and blocks every other run | Warning | A | yes | Name the state left behind after each failing git command in the shared checkout |
| 24 | spec-review-2 | The fold refusal protects only code-changing commits; a cited docs-only commit can be rehashed | Warning | A | yes | Test each "never" in the Goal against every kind of commit it covers |
| 25 | spec-review-2 | `commit` mode has no outcome for a hook refusing its own commit (mooted by the cut) | Warning | A | yes | Give every script command an outcome for its own commit failing |
| 26 | spec-review-2 | Isolation does not reach subagents, which read no `CLAUDE.md` | Warning | G | yes | State that subagents read no `CLAUDE.md` and how each value reaches them |
| 27 | spec-review-2 | A locked `git commit` can detach `git gc --auto`, which keeps the lock after the command exits | Warning | G | yes | Run the lock wrapper on a real commit and check the lock is free after |
| 28 | spec-review-2 | "How long a stopped run has waited" is promised, but no field holds a time | Suggestion | A | yes | Check each promised output against the fields that exist |
| 29 | spec-review-2 | The "busy resource is a gate" rule is not rewritten with the "never poll" rule | Suggestion | E | yes | Quote every rule sentence the change touches |
| 30 | spec-review-2 | Removing `docs-layout.md` step 9 does not say whether later steps renumber | Suggestion | E | yes | `grep` for step numbers cited elsewhere |
| 31 | spec-review-2 | The new `next` value `merge-retry` is missing from three lists of `next` values | Suggestion | G | yes | `grep` every list of `next` values and name each place |
| 32 | spec-review-2 | `AskUserQuestion` option limit unchecked for the multi-select (mooted by the cut) | NI | G | yes | Check the tool's schema |
| 33 | spec-review-2 | Whether one session can launch several runs in a row (mooted by the cut) | NI | G | partly | Try it once in a live session |
| 34 | spec-review-3 | The new fold refusal fires on the run's own squash, breaking the review stage's post-merge fold everywhere | Critical | G | yes | `grep` every caller of the fold script and run each against the new refusal |
| 35 | spec-review-3 | A failed start becomes a stop, and `set stopped=` creates a phantom live run that takes a slot | Warning | A | yes | Trace each stop row at the start step against "a refused start writes nothing" |
| 36 | spec-review-3 | The one-call locked add+commit leaves no place for the required `git diff --cached` reread; `/my:commit` and `my:architect` missing | Warning | G | yes | `grep` the global rules and commands for every rule about commits |
| 37 | spec-review-3 | The shared-doc race (check, edit, hunk check, commit are separate calls) is narrowed, not closed | Warning | A | yes | Write the interleaving for every check-then-act across tool calls |
| 38 | spec-review-3 | D1 says nothing else applies without the section, but D6 applies everywhere | Suggestion | E | yes | Cross-check every "only" and "every" claim between sections |
| 39 | spec-review-3 | The quoted 28% retry rate assumes a shorter window than `checked_base` defines (about 51%) | Suggestion | E | yes | Recompute borrowed estimates under the spec's own definitions |
| 40 | spec-review-3 | Unclear whether the new `merge` and lock rule also apply to supervised runs | NI | A | yes | Say for each guarantee which modes it covers (auto, supervised, no section) |
| 41 | spec-review-3 | Who sets `next=worktree-remove` after `merge`, and what `check` needs for `merge-retry` | NI | A | yes | Give each new `next` value its owner, its `NEEDS` and its facts |
| 42 | plan-review | Lock test holder under dash forks `sleep`, which keeps the lock after the kill | Warning | P | partly | Spec could have stated "a forked child keeps the lock" (see row 50) |
| 43 | plan-review | `git grep -h` drops the file name the refusal line must print | Warning | P | no | — |
| 44 | plan-review | The integration test never sets `branch`, so `merge` refuses | Warning | P | no | — |
| 45 | plan-review | Rehearsal `tmux new-window` fails with no server on the socket | Warning | P | no | — |
| 46 | plan-review | Spec's locked form puts the message in single-quoted `sh -c`; an apostrophe or backtick breaks it (spec `:157`) | Warning | G | yes | Run the snippet with a real message holding `'`, a backtick, `$(` and a body |
| 47 | plan-review | Plan Decision 7 silently limits the merge guarantee to auto runs; supervised merges lose it | Warning | D | yes | Say which modes the merge guarantee covers (row 40 had flagged it) |
| 48 | plan-review | No test proves `merge` writes `squash_subject`: the fixture already sets it | Warning | T | partly | Name the test and say the fixture must not pre-set the field under test |
| 49 | plan-review | Three new tests pass before their code exists | Suggestion | T | partly | Rule: each test lists its red reason, or a deliberate break |
| 50 | plan-review | "The kernel frees the lock when the command dies" fails when a child outlives a killed parent | NI | G | yes | Probe kill of `sh -c` with a child under the lock (same defect as rows 42, 71) |
| 51 | plan-review | No way out named when the fold refuses a waiting fixup in a project without the section | NI | A | yes | For each new refusal, name what the user does next |
| 52 | plan-review | Plan's git-version claim for `gc.autoDetach` keys checked on one git only | NI | P | no | — |
| 53 | code-review (soundness) | A backtick or `$(` in the double-quoted message runs outside the lock (same defect as row 46) | Warning | G | yes | Run the locked form with a hostile message; give the heredoc form in the spec |
| 54 | code-review (soundness) | `git diff -- <paths>` shows no untracked file, so new files are never reread (spec `:160-161`) | Suggestion | G | yes | Run the reread on a new file before claiming it "shows what it will stage" |
| 55 | code-review (soundness) | Supervised squash runs `git reset --merge` after the lock is released | Low | P | partly | Spec could have said "every cleanup runs inside the same lock" |
| 56 | code-review (soundness) | Lock wait plus hook run time can pass the Bash 120 s limit and leave `index.lock` (to Risk) | NI | A | yes | Budget the command's run time, not only the wait, under the tool limit |
| 57 | code-review (bug-finder) | Citation search used cwd-relative paths, so a fold from a subfolder found nothing (8efd975) | unknown | P | partly | Name a "run from a subfolder" test |
| 58 | code-review (bug-finder) | `--timeout nan` or `inf` waited forever (7b54f53) | unknown | P | no | — |
| 59 | code-review (bug-finder) | The command's own exit 75 read as a lock timeout (3890035) | unknown | A | yes | Exit-code contract: the script's codes must be told apart from the command's |
| 60 | code-review (bug-finder) | `git show --stat HEAD` after the lock may list another run's commit (3890035; spec `:162`) | unknown | A | yes | Any read of `HEAD` for "my commit" goes inside the same locked command |
| 61 | code-review (bug-finder) | Launch passed `merge_retries=0`, which `start` already sets (3890035) | unknown | P | no | — |
| 62 | code-review (bug-finder) | Supervised squash did not refuse staged changes (3890035) | unknown | P | partly | Same merge guarantees for every mode (row 40) |
| 63 | code-review (bug-finder) | A docs path without `/` is a file to `handoff-state.py` but a folder to git (plan Risk) | unknown | G | yes | Define docs-path matching once, checked against git pathspec rules |
| 64 | code-review (bug-finder) | `gc.autoDetach=false` runs a long gc inside lock `main`, timing out other runs (plan Risk) | unknown | A | yes | Weigh the cost of each lock-holding choice in Risk |
| 65 | code-review (bug-finder) | `live` crashes on a non-string state value (plan Risk) | unknown | P | no | — |
| 66 | re-review | Soundness: heredoc `EOF` indented inside list items is a bash syntax error | Warning | P | partly | Spec gives the exact command block, at column 0, run once |
| 67 | re-review | Soundness: the plan still records the unsafe quoting forms | Suggestion | E | no | — |
| 68 | re-review | Bug-finder: supervised squash reads the hash from `HEAD` after the lock (850ba6b, fixed 1db3f19; same defect as row 60) | unknown | A | yes | Same rule as row 60 |
| 69 | re-review | Bug-finder: cleanness check after reset reads the whole shared checkout (plan Risk) | unknown | P | partly | Say "clean" means this run's paths only, in a shared checkout |
| 70 | re-review | Bug-finder: `squash_subject` is the raw first line, not git's `%s` (plan Risk) | unknown | P | partly | Define `squash_subject` as git's `%s` of the commit made |
| 71 | re-review | Bug-finder: every child of a locked command holds the lock (hooks, fsmonitor) (plan Risk; same defect as row 50) | unknown | G | yes | Same probe as row 50; state the lock's real lifetime |
| 72 | re-review | Bug-finder: `--max` checked with `isdigit()` accepts `²` and crashes (plan Risk) | unknown | P | no | — |
| 73 | re-review | Bug-finder: default docs paths and their matching copied into two scripts (plan Risk; same defect as row 63) | unknown | A | yes | One owner for the docs-path rule |

#### Row 14: 2. Counts

Main counts use every row of the table (73), NI rows included. Bug-finder rows have no report, so they count as ordinary rows. Classes follow what would have prevented a finding, not who decided it. That is why D has 1 row while 30 findings went to the user (section 3). Row 34, a decision made on a false premise, could also be D; it is G because grounding would have caught it.

##### Row 14: Per class

| Class | All stages | Without spec-review-1 |
| --- | --- | --- |
| G | 25 | 13 |
| A | 25 | 16 |
| D | 1 | 1 |
| E | 5 | 5 |
| P | 15 | 15 |
| T | 2 | 2 |
| **Total** | **73** | **52** |

**Without NI rows** ("Issues Surfaced" only): G 20, A 21, D 1, E 5, P 14, T 2 = 63. Without spec-review-1: G 10, A 12, D 1, E 5, P 14, T 2 = 44. The 10 NI rows: G 5 (rows 20, 21, 32, 33, 50), A 4 (rows 40, 41, 51, 56), P 1 (row 52).

##### Row 14: Per stage

| Stage | Issues | NI | G | A | D | E | P | T |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spec-review-1 | 19 | 2 | 12 | 9 | 0 | 0 | 0 | 0 |
| spec-review-2 | 10 | 2 | 5 | 5 | 0 | 2 | 0 | 0 |
| spec-review-3 | 6 | 2 | 2 | 4 | 0 | 2 | 0 | 0 |
| plan-review | 8 | 3 | 2 | 1 | 1 | 0 | 5 | 2 |
| code-review (soundness) | 3 | 1 | 2 | 1 | 0 | 0 | 1 | 0 |
| code-review (bug-finder) | 9 | 0 | 1 | 3 | 0 | 0 | 5 | 0 |
| re-review | 8 | 0 | 1 | 2 | 0 | 1 | 4 | 0 |

(Class columns include NI rows.)

**Mooted by the cut:** 8 rows (4, 5, 8, 12, 17 from review 1; 25, 32, 33 from review 2).

**Preventable at spec, after spec-review-1 (52 rows):** yes 33, partly 10, no 9.

#### Row 14: 3. Findings decided by the user

| Basis | Rows | Count |
| --- | --- | --- |
| Explicit: review-1 status line ("Answered with the user … every finding accepted"), design rows | 1–17 | 17 |
| Explicit: review-2 status line, same words, design rows | 22–28 | 7 |
| Explicit: plan line "Decision 7 fills D7 for supervised runs, as the user chose" | 47 | 1 |
| Inferred: review-3 design rows, from commit 064ee8d and the method rule that design findings go to the user | 34–37 | 4 |
| Inferred: plan Decision 10 (row 46); the review said to ask, but no line says the user chose it | 46 | 1 |

Total 30: 25 explicit, 5 inferred. After spec-review-1: 13 (8 explicit, 5 inferred). The scope cut in 9a87dca was also a user decision, though not a finding. No code-review finding went to the user: the one-fix-round rule sent the leftovers to the plan's Risk section.

#### Row 14: 4. Patterns: checks at draft time that would have caught the most

1. **Run every shell snippet in the spec, with hostile input, against a fixture repo.** Use a commit message holding `'`, a backtick, `$(`, a body, and an indented block. Also run each "this command shows X" claim on a new, untracked file. Catches rows 46, 53, 54, 66, and the same defect found twice (46 then 53). The flawed text is still in the shipped spec at `:157-162`.
2. **Probe every claim about process and tool behaviour, in a scratchpad, before writing it.** Kill a `sh -c` holder that has a child; commit over many loose objects and check the lock after; check the Bash tool's timeout. Catches rows 14, 20, 27, 42, 50, 71. Row 50 and row 71 are one defect ("the kernel frees the lock") found twice.
3. **Sweep every existing caller and rule that the change touches, with `git grep`, and run each one against the new behaviour.** Grep each changed script name, each `next` value, each commit rule, each step number. Catches rows 2, 3, 9, 11, 13, 18, 19, 31, 34, 36. Row 34 (the review stage's own fold) was the one Critical after review 1.
4. **Write a state table and a race table.** State table: for every stop row and crash point, the `next` value left behind, then what `resume`, `check`, `live` and restart do with it. Race table: for every check-then-act across tool calls, and every read of `HEAD` after a lock, write the bad interleaving. Catches rows 3, 10, 15, 22, 23, 35, 41 (state) and 6, 37, 56, 60, 64, 68 (race). Rows 60 and 68 are one defect found twice.
5. **Give each shared value and guarantee one owner and one stated scope.** Exit codes, docs-path matching, `squash_subject`, `checked_base`, and which modes (auto, supervised, no section) each guarantee covers. Catches rows 1, 40, 47, 59, 62, 63, 70, 73. Rows 63 and 73 are one defect found twice. Row 40 (an NI) left the scope open, and the plan then narrowed it silently (row 47).

#### Row 14: 5. Findings that only running code could reveal

- **The cheap probes were all possible at draft time.** Every probe a reviewer ran was a scratchpad test of git, a shell or tmux, not of the feature: the dash fork (row 42), the gc detach (row 27), `git grep -h` (row 43), the tmux socket (row 45), `git reset --merge`, and the heredoc syntax (rows 53, 66). None needed the new code.
- **The implementation bugs (rows 57, 58, 61, 65, 69, 70, 72).** The bug-finder rounds wrote no report, so the record does not show whether they ran anything. Each fix commit or Risk line names a bug that a reader can see in the code. The spec could not have prevented most of them.
- **Only the host program's behaviour needed a live Claude Code session:**
  - The rehearsal (not a review, so not in the table) found that inside a session the installed plugin's `bin/` comes before the `--plugin-dir` copy on `PATH`. So `start` reached the old script, and the rehearsal could not run before the merge.
  - How the Bash tool ends a timed-out command, and whether the child keeps the lock (rows 20, 56). Never resolved.
  - Whether a model keeps list indentation when it copies a heredoc (row 66's Medium confidence).
  - Whether one session goes on to a second launch (row 33, mooted).

### What the approved spec missed: rows 15 (`my:status`) and 32 (`locked-commit.py`)

Both rows were Medium changes. Each had one spec with a Tasks section and one spec review. There
was no plan and no plan review. Each had one round of end-of-branch reviews, one fix round, and one
re-review.

#### Row 15 and 32: Sources and how stages were assigned

- **Row 15:** `docs/plans/2026-10-12-status-skill-spec.md`, its review, and
  `2026-10-12-feat-status-skill-review.md` / `-review-2.md`. Squash-merge `c4d3832`. The first
  committed spec, `f9512db`, already held the answers to the spec review. The review itself read
  the first draft.
- **Row 32:** `docs/plans/2026-10-12-locked-commit-spec.md`, its review, and
  `2026-10-12-feat-locked-commit-review.md` / `-review-2.md`. Squash-merge `39000ec`. The spec
  was approved in `a372fa5`.
- **The bug-finder (`/code-review high`) wrote no report file.** Its findings exist only as Risk
  bullets in the spec and as fix-commit bodies. A Risk bullet or fix counts as **bug-finder
  (inferred)** when it is not in the soundness review file of the same round. The round comes from
  the commit that added the bullet. For row 15, that is Risk 7 in `c4b8adf` and Risk 8 in
  `f1b1c92`, plus the fix commit `cfb5e72`. For row 32, it is Risk 8 in `f273e98` and Risk 9 in
  `84476ba`, plus the fix commit `ffc6acd`.
- **Two stages are not in the brief's list.** "Code stage" means the implementing session found
  the problem itself, during a task or a rehearsal. "After merge" means a fix commit after the
  `done` mark. Both are kept, because they are findings made after the first spec draft.
- **Severity:** reviewer files give a severity. A bug-finder item has no recorded severity. It is
  marked "Fixed" when a fix commit closed it, or "Known limit" when it went into Risk.
- **A finding found by two stages is listed once, under the first stage that found it.** The one
  exception is L12. It is listed again because the spec ignored the spec-review finding (L6), and
  the problem came back in code review.

#### Row 15: `my:status`

| # | Stage | Finding (one line) | Severity | Class | Preventable at spec? | What the spec would have needed (one line) |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | spec-review-1 | D4 line test flags 17 of 18 squash-merged branches on this repo, so Goal 4 fails | Critical | G | yes | Run the D4 rule on this repo's 18 branches before writing it down |
| S2 | spec-review-1 | In-row gates ("Blocked by row N", "Waits for") are dropped; only `## Order of work` is read | Warning | A | yes | List every gate form rule 12 allows and say which component reads each |
| S3 | spec-review-1 | 20 `no-status` files would sit at the top of every report as "needs the user" | Warning | G | yes | Count `no-status` files in `docs/plans/` before choosing how to report them |
| S4 | spec-review-1 | `runs` block has 4 fields; the approved `live` prints 5 in another order | Warning | G | yes | Copy the field list from the parallel spec's D3, with its line number |
| S5 | spec-review-1 | No outcome is defined when one source fails (bad JSON, missing roadmap, no branch) | Warning | A | yes | A table of each source's failure and the line the block prints |
| S6 | spec-review-1 | A row's linked `docs/plans/` path is taken as its spec, but rows link other documents | Warning | G | yes | Read the real roadmap rows' links and define what a link means |
| S7 | spec-review-1 | Overlap reads only the spec's "Files"; 5 of 11 specs have none, and Large items keep it in the plan | Warning | G | yes | Grep the specs for a Files section; name the plan's file list as a source |
| S8 | spec-review-1 | A branch that only deletes lines, or adds only short ones, is never printed | Warning | A | yes | Ask "what if nothing is kept?" for each filter in D4 |
| S9 | spec-review-1 | "Live run" means two things; the Max runs count is ambiguous about stopped runs | Warning | A | yes | Define each term once and reuse the owning spec's definition |
| S10 | spec-review-1 | Wrong rule numbers cited for the order decision and the icons | Suggestion | G | yes | Open the cited skill and quote the rule numbers |
| S11 | spec-review-1 | Task 3 says plugin path; `my:handoff` calls its script by bare name on `PATH` | Suggestion | G | yes | Read the sibling skill's call before citing it as the model |
| S12 | spec-review-1 | Task 4 relies on a memory note and omits the scratch `--add-dir` | Suggestion | G | yes | Inline the full headless command and run it once |
| S13 | spec-review-1 | Branches kept on purpose may show as unfinished every session; no way to mark them judged | Needs inv. | A | partly | Say how a branch that was judged and kept stops being reported |
| S14 | code-review (soundness) | A branch with no merge base turns the whole `branches` block into one empty error line | Warning | A | yes | Name the no-merge-base case in D4 (git-squasher makes such branches) and its output |
| S15 | code-review (soundness) | SKILL.md hard-codes `main`; the script uses the branch in the main checkout | Warning | P | no | Spec D3 already defined it; the skill text did not carry it over |
| S16 | code-review (bug-finder, inferred) | A branch name that a tag shares is misread | Fixed | P | no | Could name `refs/heads/<b>` as the form to pass to git |
| S17 | code-review (bug-finder, inferred) | The second path of a rename on the work-tree side is listed as dirty | Fixed | P | no | Could name a rename in the `test_dirty_path_listed` case |
| S18 | code-review (bug-finder, inferred) | A branch with no comparable lines (binary, renames, short lines) counts 0 and is hidden | Known limit | A | yes | Extend S8's "nothing kept" question to the no-lines case |
| S19 | code-review (bug-finder, inferred) | A state file that is valid JSON but not an object stops the script with exit 1 | Known limit | P | partly | Name `null` and `[]` next to "not valid JSON" in D3, with a test |
| S20 | code-review (bug-finder, inferred) | Exit 2 doubles as "no `live` yet"; via a symlink, the fallback is used for good | Known limit | A | yes | Do not reuse a usage-error exit code as a feature probe; name a real probe |
| S21 | code-review (bug-finder, inferred) | The fixup scan's target rule differs from `git-fold-fixups.py` (pushed fixups, duplicate subjects) | Known limit | G | yes | Read the fold script and reuse or cite its target rule |
| S22 | code-review (bug-finder, inferred) | One `rev-list --count` per branch before the cap; worktrees and roadmap read twice | Known limit | P | no | Implementation cost; the spec's cap was right |
| S23 | code-review (soundness) | One worktree where git fails turns the whole `worktrees` block into an error line | Known limit | A | yes | Say errors are per item, not per block, where items are independent |
| S24 | code stage (rehearsal) | The report suggests `git-fold-fixups.py` while worktrees hold the fixup targets, so it would refuse | Known limit | G | partly | Read the fold's refusal rules before naming it as the "next" command |
| S25 | re-review (soundness) | The skill's `git grep` names may come from `-` lines or from names `main` had, so it clears unfinished work | Warning | A | yes | D5 says: take names only from added lines that `main` lacked at the merge base |
| S26 | re-review (soundness) | The no-shared-history rule is in the code only, not in D4 or the docstring | Suggestion | E | partly | Follows S14: had D4 named the case, the record would match |
| S27 | re-review (bug-finder, inferred) | Overlap uses the committed diff only; misses uncommitted worktree edits and untouched plan files | Known limit | A | yes | File list = committed diff, plus worktree status, plus the plan's list |
| S28 | re-review (bug-finder, inferred) | Max runs "defaults to 2", yet without a Parallel runs section only one auto run is allowed | Known limit | A | yes | Remove the contradiction inside D6 item 3 |
| S29 | re-review (bug-finder, inferred) | The base branch goes to `git log` bare; a same-named path errors the block | Known limit | P | no | Could require `--` after every revision argument |
| S30 | re-review (bug-finder, inferred) | `--separate-git-dir` or a submodule gives a traceback instead of exit 2 | Known limit | P | no | Implementation bug; D3's exit rule was right |
| S31 | re-review (bug-finder, inferred) | The patch log is cached per fork commit, so many forks mean many overlapping logs | Known limit | P | no | Implementation cost |
| S32 | re-review (bug-finder, inferred) | A `#` line inside a code fence ends `## Order of work` early | Known limit | P | no | Parser detail; could say how the section ends |
| S33 | re-review (bug-finder, inferred) | The fallback prints JSON `null` as `None`; a newline in a stop line splits a row | Known limit | A | yes | D3 defines a tab-line format but not how a null, tab or newline in a field is written |
| S34 | re-review (bug-finder, inferred) | No test covers the `live` path of `run_facts` | Known limit | T | partly | Name a test with a stub `handoff-state.py` that has `live` |
| S35 | after merge (`2a48d5c`) | The Shared resources condition blocked every code pair, but runs take turns on a lock | Fixed | D | yes | Check how the parallel spec uses Shared resources (a lock) before excluding pairs |

#### Row 32: `locked-commit.py`

| # | Stage | Finding (one line) | Severity | Class | Preventable at spec? | What the spec would have needed (one line) |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | spec-review-1 | The "prints nothing" `git grep` checks can never pass; the old text stays in docs and the spec | Warning | G | yes | Run each acceptance command on the tree before writing it |
| L2 | spec-review-1 | No `my:handoff` stop row covers the script's exit 64 or its git failures | Warning | A | yes | Trace each new exit code to the reader that acts on it |
| L3 | spec-review-1 | ROADMAP edits are in no Task or Files list, and no commit is named | Warning | E | yes | List every file the spec edits, with its commit |
| L4 | spec-review-1 | D3 cites the fold check, which never runs in a parallel project | Suggestion | G | yes | Check that each stated reason applies where the script runs |
| L5 | spec-review-1 | `commit.md` step 4 still says to use a heredoc, which conflicts with the new line | Suggestion | G | yes | Read each edited file whole, not only the cited line |
| L6 | spec-review-1 | Exit 126/127 can also come from `sh` when git is missing, so "Nothing ran" is not exact | Low (not acted on) | A | yes | Separate the lock script's codes from codes the shell can return |
| L7 | code stage (Task 4) | "0 lint errors" is impossible: the files already had 79, 70, 10 and 95 errors | Known limit | G | yes | Run `markdownlint-cli2` on the files before setting the target |
| L8 | code-review (soundness) | `test_parallel_runs.py` kept a sixth copy of the old `sh -c` command | Suggestion | G | yes | Sweep for copies with a loose token, including tests |
| L9 | code-review (bug-finder, inferred) | A commit a hook rejects leaves its paths staged in the shared main checkout; the next merge refuses | Fixed | A | yes | For each step in D2, state what a failure leaves behind and who sees it |
| L10 | code-review (bug-finder, inferred) | A message file that is a symlink: the script deletes the link's target | Known limit | A | partly | Add "is a symlink" to D3's refusals |
| L11 | code-review (bug-finder, inferred) | `git show --stat` failing after a good commit gives non-zero and keeps the file | Known limit | A | yes | Order the steps so a display failure cannot report a commit as failed |
| L12 | code-review (bug-finder, inferred) | git or `handoff-lock.py` missing gives exit codes that do not match D4 | Known limit | A | yes | Same as L6; the spec review raised it and the spec did not act |
| L13 | code-review (bug-finder, inferred) | Options after paths, a repeated `-F`, or `-F` followed by an option are not refused | Known limit | A | partly | List these in D3's refusals and in Task 1's tests |
| L14 | code-review (bug-finder, inferred) | The rules go live at the merge, before the installed plugin has the script | Known limit | G | yes | Check how `~/.claude` links into the repo and when the plugin updates |
| L15 | re-review (soundness) | D2 and D4 do not name the new unstage step | Suggestion | E | partly | Follows L9: had D2 named it, the record would match |
| L16 | re-review (soundness) | Risk 7 says `docs-layout.md` is a plain copy; the `~/.claude/rules` folder is a symlink | Suggestion | G | partly | Run `readlink -f` on each global file the spec says goes live |
| L17 | re-review (bug-finder, inferred) | When `git add` fails partway, the good paths stay staged; the reset runs only after the commit | Known limit | A | yes | The L9 question asked of every step, not only the commit |
| L18 | re-review (bug-finder, inferred) | The reset after a failed commit drops a partial staging of the same path made before | Known limit | A | partly | State what the index holds before and after a failure |
| L19 | re-review (bug-finder, inferred) | After a failed commit the kept file blocks the Write tool, so a retry needs a Read or a new name | Known limit | A | yes | D5 reasons about the Write tool for success only; apply it to failure |
| L20 | re-review (bug-finder, inferred) | `global/CLAUDE.md` and `my:architect` still say "the locked form" | Known limit | G | yes | Grep the short token "locked form", not only "locked form of Plan stage" |
| L21 | re-review (bug-finder, inferred) | `fail()` and the help text repeat `handoff-lock.py` code; steps stay a `sh -c` string | Known limit | P | no | Code quality; the spec's design was right |

#### Row 15 and 32: Counts

##### Row 15 and 32: Per class

| Class | Row 15 | Row 32 | Both | Both, after spec-review-1 only |
| --- | --- | --- | --- | --- |
| G grounding | 10 | 8 | 18 | 7 |
| A adversarial design | 13 | 10 | 23 | 16 |
| D decision | 1 | 0 | 1 | 1 |
| E editorial | 1 | 2 | 3 | 2 |
| P plan/implementation | 9 | 1 | 10 | 10 |
| T test design | 1 | 0 | 1 | 1 |
| **Total** | **35** | **21** | **56** | **37** |

The spec reviews had already pushed G down: only 7 of the 37 later findings are grounding. Most
of what got through is A (16 of 37). The 10 P findings are all in row 15, and all are bug-finder
items in code that the spec did not describe.

##### Row 15 and 32: Per stage

| Stage | Row 15 | Row 32 | Both |
| --- | --- | --- | --- |
| spec-review-1 | 13 | 6 | 19 |
| code stage (self-found) | 1 | 1 | 2 |
| code-review (soundness) | 3 | 1 | 4 |
| code-review (bug-finder, inferred) | 7 | 6 | 13 |
| re-review (soundness) | 2 | 2 | 4 |
| re-review (bug-finder, inferred) | 8 | 5 | 13 |
| after merge | 1 | 0 | 1 |
| **Total** | **35** | **21** | **56** |

There were no spec-review-2, plan-review or plan stages. The bug-finder found 26 of the 37 later
findings, and wrote none of them to a file.

##### Row 15 and 32: Preventable at spec, after spec-review-1 only (37 findings)

| | Row 15 | Row 32 | Both |
| --- | --- | --- | --- |
| yes | 10 | 9 | 19 |
| partly | 4 | 5 | 9 |
| no | 8 | 1 | 9 |

#### Row 15 and 32: Findings the user decided

- **Recorded as decided by the user: 1.** L2: the spec review's status line says "the author
  decided finding 2", and stop row 23 now names `locked-commit.py`.
- **Sent to the author as decisions, with no record of who chose: 3.** S1 (a new branch test), S3
  (one count line for `no-status` files), and S7 (read the plan's file list). The spec records
  each answer, and the user approved the spec as a whole. No line says the user picked these
  options.
- No later finding went to the user. The one-fix-round rule sent every unfixed code-review item to
  Risk. S35 was fixed after the merge, and its commit does not say who raised it.

#### Row 15 and 32: Patterns: draft-time checks that would have caught the most

1. **Ask what each failing step leaves behind, and who reads it.** For every step and every exit
   code, write down the state after a failure (index, files, output block) and the component that
   acts on it. This covers 12 findings: S5, S14, S19, S20, S23, L2, L6, L9, L11, L12, L17 and L19.
   L19 is the clearest case. D5 already reasoned about the Write tool after a success, but not
   after a failure.
2. **List the empty, odd and malformed inputs for every input the spec parses, and give each an
   outcome and a named test.** Examples: a branch with no merge base, only deletions, or no kept
   lines; a null, tab or newline inside a field; options in the wrong order; a symlinked message
   file. This covers S8, S13, S14, S18, S19, S33, S34, L10 and L13. Two of these (S8, then S18)
   are the same question asked once and then not extended.
3. **Run every rule, count and acceptance command in the spec against the real repo before
   writing it.** S1 was caught only because the spec reviewer ran a prototype of D4 on 18 real
   branches. The same check catches S3, S7, L1 and L7 (the lint target was impossible on `main`).
   It also catches S24: the "next" command would have been refused in the repo's real state.
4. **Sweep with the short token, in every file, and read each edited file whole.** The spec
   counted "five copies" by grepping the full command and missed the test copy (L8). It grepped
   "locked form of Plan stage" and missed "locked form" (L20). It cited one line of `commit.md`
   and missed step 4 (L5). Checking install links with `readlink -f` covers L14 and L16. Reading
   the sibling script covers S21.
5. **Quote the owning spec's definition; do not restate it.** S4 (the `live` fields), S9 (a
   stopped run counts), S28 (the Max runs default) and S35 (Shared resources is a lock, not a
   ban) all restated a concept owned by the parallel auto runs spec, and got it wrong or left
   it ambiguous. S35 was the only finding that needed a fix after shipping.

A smaller point: a spec-review finding that is not acted on can come back. L6 was listed only in
the review's "problems" table. The spec did not answer it, and it returned in code review as L12.

#### Row 15 and 32: Findings that only running code could reveal

- **S24, the fold suggestion.** It appeared only when the skill ran on a repo whose worktrees held
  branches on top of the fixup targets. Reading the fold's refusal rules could have predicted it,
  so it is "partly" preventable. In practice, the rehearsal is what showed it.
- **The P findings (S15–S17, S19, S22, S29–S32, L21)** are bugs or costs in code the spec did not
  describe: ref-name ambiguity, rename parsing, caching, a traceback on an unusual git layout. A
  spec could name a test for some of them (S16, S19, S29), but these problems exist only in the
  code.
- **Not code-only: S1.** It looks like a finding that needs real data, but the spec reviewer found
  it by running a prototype of the rule against the real repo at spec time. That supports
  pattern 3. S14 is similar: it was reproduced on a real repo (`grispy2-web-ext`), but a reader of
  D4 could have asked "what if there is no merge base?"

### Row 16: swappable methods — what the approved spec missed

Inputs: spec, spec review, plan, plan review, batch 1 reviews (`refactor-…-kit-review`, `-review-2`), batch 2 reviews (`feat-…-cutover-review`, `-review-2`, `-code-review`, `-code-review-2`), the squash commits `1fe2d57` and `a0144ee`, and the branch commits `b87da53`, `f30c6b0`, `3dead9b`.

**Row rule.** A row is each row of a review's Issues table, each "Needs Investigation" item, and each grounding note that names a defect not already in the Issues table. The same rule applies at every stage. When two reviewers found the same thing, each gets a row, and the later one says "same as #n".

**Severity.** Each review's own scale is kept. Soundness reviews: Warning / Suggestion. Bug-finder (`/code-review high`): High / Medium / Low. "Investigation" marks a Needs Investigation item. "Note" marks a grounding note.

**Gaps in the record.**

- The batch 1 bug-finder report was not saved. Its commit message says "eight issues: five fixed, three in Risk". Rows 25 to 31 come from the fix commit `b87da53` and the Risk lines added in `f30c6b0`. Seven of the eight can be named. The fifth fix is probably the kit description, counted once per file (`plugin.json` and `marketplace.json`). These rows are marked "reconstructed", and their severity is unknown.
- The batch 1 soundness re-review ran and found nothing. It has no row for that reason.
- The spec was committed once (`ddfd52a`), after its review findings were folded in as D13 to D18. So there is one spec review stage.

#### Row 16: 1. Findings

| # | Stage | Finding (one line) | Severity | Class | Preventable at spec? | What the spec would have needed (one line) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | spec-review-1 | `diagoradisa/` and `grispy-web-ext/` are folders of 7 nested repos, not repos. | Warning | G | yes | Build the repo list from `find ~/projects -maxdepth 3 -name .git`, not from memory. |
| 2 | spec-review-1 | Tutor projects gain 4 core rules they set aside today; D6's "my is off" reason does not cover core rules. | Warning | D | yes | Check each decision's reason against the section table: which core rules does tutor drop today? |
| 3 | spec-review-1 | `optimize-prompt` and `tune-claude-instructions` fail D5's own test but sit in `kit`. | Warning | G | yes | Run D5's grep (`docs/plans`, `superpowers:`, `my:`) over every file placed in `kit`. |
| 4 | spec-review-1 | `.claude/settings.json` is gitignored in `claude-setup`, so setup cannot commit it. | Warning | G | yes | Run `git check-ignore -v .claude/settings.json` in every target repo. |
| 5 | spec-review-1 | No runbook installs or updates the plugin cache, so `/kit:setup` would not exist at cutover. | Warning | G | yes | Read `README.md` "Updating" and `installed_plugins.json`; give each runbook install, update and restart. |
| 6 | spec-review-1 | Guard treats a missing `superpowers@synced` key as off, but sync turns it on. | Warning | G | yes | Read the live settings file and state the default of each missing key. |
| 7 | spec-review-1 | Risk lists a `ROADMAP.md` row as open that is done. | Suggestion | G | yes | Re-read the roadmap status of every row the spec cites. |
| 8 | spec-review-1 | Batch 1 sweep list misses `changelog-management/SKILL.md:65`; "about 30 lines" is 46. | Suggestion | G | yes | Paste the sweep command and its full output, not a hand-made list. |
| 9 | spec-review-1 | Testing says the lazy rules "start with" the new line, but both start with frontmatter. | Note | E | yes | Name the exact position: first line after the title. |
| 10 | spec-review-1 | Unknown: after one decline, does Claude Code ask for the import again? (It does not.) | Investigation | G | yes | Spike decline-then-restart before writing the guard's advice text. |
| 11 | spec-review-1 | Unknown: does a parent folder's import reach a nested repo, and under which approval key? | Investigation | G | yes | Spike a nested repo under a parent with an import. |
| 12 | spec-review-1 | Unknown: does an import that resolves into the same repo ever set the approval flag? | Investigation | G | yes | Spike the symlinked import in a scratch repo. |
| 13 | spec-review-1 | Rollback assumes a missing import target is skipped silently; not checked. | Investigation | G | yes | Run one `claude -p` with a missing import target and record the output. |
| 14 | plan-review | Rehearsal check (size table in context) cannot fail: the whole global file is still live. | Warning | T | yes | Task 0 check 2 should ask for a marker only in `my.md`, and expect NONE before approval. |
| 15 | plan-review | `test_output_is_capped` cannot fail: 12 short names stay far under 2,000 characters. | Warning | T | partly | State the cap test: an input whose uncut text is over 2,000 characters. |
| 16 | plan-review | The `done` marks run in a session where `my` is not loaded yet. | Warning | A | yes | Trace which plugins each runbook session has, step by step; restart after setting up `claude-setup`. |
| 17 | plan-review | Batch 1 backup is taken after `claude plugin install`, which already writes the settings file. | Warning | A | yes | The spec's batch 1 runbook had no backup at all, yet its Rollback restores one; start with a backup. |
| 18 | plan-review | Text-move script prefixes do not match the old lines; the script exits 1 as written. | Suggestion | P | no | — (the spec described the check; the plan's script was wrong) |
| 19 | plan-review | `test_tutor_with_my_on_is_stray` expects the wrong text under D18's default. | Suggestion | P | no | — (the plan forgot the D18 default the spec stated) |
| 20 | plan-review | `README.md:52` and `:115` are in neither path-hit list. | Note | P | no | — (the plan's list; both lines still hold) |
| 21 | plan-review | Unknown: does `--plugin-dir` win over an installed plugin of the same name? | Investigation | G | partly | List every tool behaviour the rehearsal depends on, and spike each one. |
| 22 | plan-review | Unknown: do running sessions reread `~/.claude/settings.json` during check 1? | Investigation | G | partly | Same: spike settings reload before relying on a "one-minute window". |
| 23 | code-review (soundness) | B1 soundness: `/kit:commit` needs `locked-commit.py`, which stays in `my`. | Suggestion | G | yes | Apply D5's test to scripts too: grep `kit` files for every name in `plugins/my/bin/`. |
| 24 | code-review (soundness) | B1 soundness: README dev-loop recipe names only `--plugin-dir …/plugins/my`. | Suggestion | E | partly | List every README section that names `plugins/my`. |
| 25 | code-review (bug-finder) | B1 bug-finder (reconstructed): `CLAUDE.md` intro still says one plugin (`my`). | unknown | E | partly | Name `CLAUDE.md`'s intro line in batch 1's file list. |
| 26 | code-review (bug-finder) | B1 bug-finder (reconstructed): handoff README writes `kit:push`, not the command `/kit:push`. | unknown | E | no | — (a form error carried over by the rename) |
| 27 | code-review (bug-finder) | B1 bug-finder (reconstructed): `kit` description omits the tutor and its hook. | unknown | E | partly | Give the manifest description text in the spec. |
| 28 | code-review (bug-finder) | B1 bug-finder (reconstructed): README dev-loop names only `plugins/my` (same as #24). | unknown | E | partly | Same as #24. |
| 29 | code-review (bug-finder) | B1 bug-finder (reconstructed): `/kit:commit` needs `locked-commit.py` from `my` (same as #23). | unknown | G | yes | Same as #23. |
| 30 | code-review (bug-finder) | B1 bug-finder: `kit:dev-reports` names `changelog-management` without a `my:` prefix. | unknown | G | yes | Sweep for the bare names of `my` skills, not only the `my:` prefix. |
| 31 | code-review (bug-finder) | B1 bug-finder: between merge and runbook, `kit:tutor` is named but `kit` is not installed. | unknown | A | yes | Test "behaviour does not change" at each step from merge to the end of the runbook. |
| 32 | re-review | B1 bug-finder: `~/bin` md-table links could point straight at `~/src/scripts/`. | Low | D | yes | Offer both link targets to the user as a choice. |
| 33 | re-review | B1 bug-finder: README Hooks omits `block-autorun-push.py`, so "my off drops the push guard" is hidden. | Low | E | partly | Require the README to list every hook with its plugin. |
| 34 | re-review | B1 bug-finder: `CLAUDE.md` puts the deny-list `settings.json` in the plugin folder (false before). | Low | E | no | — (an older error) |
| 35 | re-review | B1 bug-finder: `CLAUDE.md` says manifests "must list" paths that are auto-discovered (false before). | Low | E | no | — (an older error) |
| 36 | re-review | B1 bug-finder: the `my` description does not tell the method apart from `kit`. | Low | E | partly | Give both manifest descriptions in the spec. |
| 37 | re-review | B1 bug-finder: README `--plugin-dir` example does not show both flags in one command. | Low | E | no | — (docs polish) |
| 38 | re-review | B1 bug-finder: learning-workspace check exists twice (kit hook, my squash hook) until batch 2. | Low | A | partly | List the states between batches in Risk. |
| 39 | code-review (soundness) | B2 soundness: guard is silent in a subfolder session; `CLAUDE_PROJECT_DIR` is the start folder. | Warning | G | yes | Print `CLAUDE_PROJECT_DIR` from a hook in a subfolder session; reuse the tutor hook's root rule. |
| 40 | code-review (soundness) | B2 soundness: README install block turns `my` on at user scope, against D7. | Suggestion | A | yes | Walk the fresh-machine install path under D7, step by step. |
| 41 | code-review (soundness) | B2 soundness: two `my` skills still call the method rules "global". | Suggestion | G | yes | Sweep prose phrases ("global rules", "global instructions") as well as paths. |
| 42 | code-review (soundness) | B2 soundness: unknown which settings file Claude Code reads in a subfolder session. | Investigation | G | partly | Spike a subfolder session and read the init line's plugin list. |
| 43 | code-review (bug-finder) | B2 bug-finder: plugin warnings name `settings.json` when `settings.local.json` holds the value. | Medium | A | yes | For each warning, say which of the three merged files the fix goes in. |
| 44 | code-review (bug-finder) | B2 bug-finder: `kit:setup` never removes the other method's import; tutor steps not idempotent. | Medium | A | yes | Define setup for a rerun and for a switch from one method to the other. |
| 45 | code-review (bug-finder) | B2 bug-finder: `kit:setup` ignores `.claude/settings.local.json`. | Medium | A | yes | Make setup read the same three files the guard reads. |
| 46 | code-review (bug-finder) | B2 bug-finder: the `.gitignore` edit can commit the user's unrelated edits. | Low | A | yes | Apply "other uncommitted work is left alone" to `.gitignore` too. |
| 47 | code-review (bug-finder) | B2 bug-finder: the same import twice reads as "more than one method file: my, my". | Low | A | yes | Say "two different method names", not "two or more method files". |
| 48 | code-review (bug-finder) | B2 bug-finder: guard does not resolve `CLAUDE_PROJECT_DIR` to the git top level (same as #39). | Medium | G | yes | Same as #39. |
| 49 | code-review (bug-finder) | B2 bug-finder: import regex counts lines inside code fences, which Claude Code does not import. | Low | G | yes | Check how Claude Code treats `@` lines inside fences, and say so in the regex rule. |
| 50 | code-review (bug-finder) | B2 bug-finder: an unreadable `CLAUDE.md` counts as "no import", with no warning. | Low | P | no | — (the spec's row covered any input file; the plan narrowed it to JSON) |
| 51 | code-review (bug-finder) | B2 bug-finder: the guard does not run after compaction. | Low | A | yes | List each SessionStart source, `compact` included, and say why each is in or out. |
| 52 | code-review (bug-finder) | B2 bug-finder: the "already set up" check misses a stray tutor import and local overrides. | Low | A | partly | Define "already set up" as the guard's own clean state. |
| 53 | re-review | B2 bug-finder: `kit:tutor` never sets the tutor method, so a new workspace can run `my`. | Medium | A | yes | Trace D6's premise "my is off in a tutor project" to the step that makes it true. |
| 54 | re-review | B2 bug-finder: the squash-merge hook now fires in such a learning workspace. | Low | A | yes | Same trace as #53, before dropping the hook's learning check. |
| 55 | re-review | B2 bug-finder: the guard does not tie `docs/learning/curriculum.md` to the tutor method. | Low | A | partly | Same trace; decide whether the guard checks it. |
| 56 | re-review | B2 bug-finder: `kit:setup` commits without the lock in a project with "Parallel runs". | Low | G | yes | Check the spec's commit steps against the method's own Git Workflow rules. |
| 57 | re-review | B2 bug-finder: the tutor commit runs the `settings.json` ignore check it does not need. | Low | A | yes | Write the tutor steps in full, not "steps 4 and 5 as above". |
| 58 | re-review | B2 bug-finder: the fix removes the other import from `CLAUDE.md` only, not `CLAUDE.local.md`. | Low | P | no | — (an incomplete fix of #44 and #52) |
| 59 | re-review | B2 bug-finder: a read of `~/.claude.json` during another session's write may fail. | Low | A | partly | List the other writers of each input file. |
| 60 | re-review | B2 bug-finder: the `.gitignore` exception fails when the rule is in global excludes. | Low | G | yes | Run `git check-ignore -v` with a rule in `core.excludesFile` on a fixture. |
| 61 | re-review | B2 soundness: import removal reaches `CLAUDE.md` only (same as #58). | Suggestion | P | no | — (an incomplete fix) |
| 62 | re-review | B2 soundness: README install block now turns off `my`, but not superpowers. | Suggestion | P | no | — (an incomplete fix of #40) |

#### Row 16: 2. Counts

By class (62 rows; 58 without the four "same as" rows #28, #29, #48, #61):

| Class | All rows | Without duplicates |
| --- | --- | --- |
| G — grounding | 23 | 21 |
| A — adversarial design | 17 | 17 |
| D — decision | 2 | 2 |
| E — editorial | 11 | 10 |
| P — plan/implementation only | 7 | 6 |
| T — test design | 2 | 2 |
| **Total** | **62** | **58** |

By stage and class:

| Stage | G | A | D | E | P | T | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| spec-review-1 | 11 | 0 | 1 | 1 | 0 | 0 | 13 |
| plan-review | 2 | 2 | 0 | 0 | 3 | 2 | 9 |
| code-review (soundness) | 4 | 1 | 0 | 1 | 0 | 0 | 6 |
| code-review (bug-finder) | 4 | 8 | 0 | 4 | 1 | 0 | 17 |
| re-review | 2 | 6 | 1 | 5 | 3 | 0 | 17 |

Preventable at spec: yes 37, partly 14, no 11.

After the spec was approved, later stages found 49 rows (#14 to #62). For 24 of them a harder spec was a "yes", for 14 "partly", and for 11 "no". Of the 29 G or A rows among them, 22 are "yes".

Why D is rare even though 11 decisions went to the user: most user decisions answered a G or A finding. The finding was a false fact or a gap. The user then chose the fix. A row is D only when the original choice rested on a false premise (#2) or was made without asking (#32).

#### Row 16: 3. Findings decided by the user

11 decisions, covering 13 rows:

- #1 to #6: decisions D13 to D18, approved by the user on 2026-10-13.
- #10: the new `declined` guard warning, after Task 0 check 3, with the user's yes.
- #23 and #29: a note in `commit.md`; the script stays in `my`.
- #39 and #48: the subfolder limit goes to Risk, not to a fix.
- #43: the "names `settings.json`" limit goes to Risk.
- #51: the compaction limit goes to Risk.

All other Risk entries went there by the one-fix-round rule, not by a user choice. The user also accepted 31 new MD013 lint errors; that was not a review finding.

Outside the review stages: D19 and D20 (four more repos, and existing worktrees) came from the author's own sweep of session folders. The user approved them before the spec commit. This was a G-type miss in the first draft, caught without a reviewer.

#### Row 16: 4. Patterns: which draft-time check would have caught the most

1. **Spike every Claude Code behaviour the design rests on, before approval, not in "task 0" after it.** One scratch session per question would have answered: plugin cache, synced plugin default, decline-then-restart, parent imports, symlinked import, missing target, `--plugin-dir` override, settings reload, `CLAUDE_PROJECT_DIR` in a subfolder, `@` lines inside fences. Findings #5, #6, #10, #11, #12, #13, #21, #22, #39, #42, #48, #49 (12). This spec listed most of these as checks, but only after approval, so two of them (#39, #49) were never asked.
2. **Back every claim about the repo set and the files with a pasted command.** Use `find … -name .git` for the repo list. Run `git check-ignore -v` in every target. Grep the spec's own placement test (D5) over every moved file, including the script names in `plugins/my/bin/` and bare skill names without `my:`. Sweep prose phrases ("global rules") as well as paths. Findings #1, #3, #4, #7, #8, #23, #29, #30, #41, #56, #60 (11).
3. **Fill an input-by-state table for each new component (guard, setup).** Rows: each input file (`CLAUDE.md`, `CLAUDE.local.md`, three settings files, `~/.claude.json`, `.gitignore`). Columns: missing, unreadable, duplicate, set against the method, edited by the user, written by another session. Add rerun, method switch and compaction. Findings #43, #44, #45, #46, #47, #51, #52, #57, #59, and the incomplete fixes #58, #61 that follow from #44 (11).
4. **Trace each decision's premise to the step that makes it true, and trace the state of each session through each runbook step.** "My is off in a tutor project" (#2, #53, #54, #55). "Behaviour does not change" in batch 1 (#31, #38). Which plugins the final session has (#16). What a fresh machine gets under D7 (#40, #62). What the rollback restores (#17). Findings: 10.
5. **Write each check as an assertion with its red case.** The rehearsal had to fail if the import did not load (#14). The cap test had to exceed the cap (#15). Running the plan's checks once against real data also catches #18 and #19.

#### Row 16: 5. Findings that only running code could reveal

Two kinds need to be told apart.

**Needed Claude Code or git to run, but not our code.** Spikes at draft time catch these. The review findings are #10 to #13, #21, #22, #39, #42, #48, #49, #60. Task 0 and the rehearsal also found things that no stage in the table covers:

- A declined import is never asked again (check 3). This added the `declined` warning.
- In `--output-format stream-json`, the init line is not the first line; a hook event comes first (check 1).
- `notes-cli`'s pre-commit hook points at a `.venv` path that no longer exists, so the setup commit first failed (rehearsal). Only a real commit in a copy of the real repo showed this. `kit:setup` then gained a sentence on hooks.

**Needed our own code to run.** These are the P rows: #18 (the script's prefixes fail on the real lines), #19, #20, #50, #58, #61, #62. A harder spec would not have prevented them.

**Still unconfirmed:** #59, the read of `~/.claude.json` during another session's write. It needs real concurrent writers, and whether Claude Code writes that file atomically was never checked. Even a spike might not reproduce it.

### Row 9: start auto runs from roadmap rows — what the spec missed

Sources: `docs/plans/2026-10-13-roadmap-auto-runs-spec.md` (as of `51dc317`), its two
reviews, the plan `docs/plans/2026-10-13-roadmap-auto-runs.md` and its review, the
architecture brief (context only), commits `82bb904` and `51dc317`, and the state file
`<git common dir>/my-handoff/roadmap-auto-runs.json`.

#### Row 9: Where this row stands (checked 2026-10-14)

The task said there is no code yet and the plan stage stopped on two design questions.
Both are out of date:

- Commit `51dc317` committed the plan and its review. Its body says the user decided both
  questions on 2026-10-14. The spec diff `82bb904..51dc317` adds the two decisions to D3
  and D4.
- The state file reads `next=code`, `stopped="rehearsal fixture ready; start the call as
  printed"`. The branch `feat/roadmap-auto-runs` holds seven task commits (Tasks 1 to 7)
  in `.claude/worktrees/roadmap-auto-runs`. The code stage waits at the Task 8 rehearsal
  gate.
- `git diff --stat main...feat/roadmap-auto-runs -- docs/` is empty: no code review exists
  yet, and the branch has not edited the spec or plan.

So this report covers the spec reviews and the plan review only, as asked. Code reviews
do not exist yet.

Note on versions: `82bb904` committed the spec as `draft`, already in its third version
(the answers to both spec reviews were folded into it). The first and second drafts are
not in git. Review 1's "Spec Summary" describes the first draft: three batches, D8 to D10.
The first `approved` version is `51dc317`, after the plan review.

#### Row 9: 1. Findings

| # | Stage | Finding (one line) | Severity | Class | Preventable at spec? | What the spec would have needed (one line) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | spec-review-1 | Call order deadlocks the queue: a dependent typed first stops the walk before its blocker | Critical | A | yes | Trace each walk rule against a dependent-typed-first input; state an ordering rule |
| 2 | spec-review-1 | Pruning drops `skipped` and `started` entries that `pull` still reads (blocker facts, `exclusive`) | Critical | A | yes | A table per field: who writes, who reads, who deletes it, and when |
| 3 | spec-review-1 | D3 folds `<base>` under a live run; a refused fold blocks the whole call; no branch for "no" | Warning | A | yes | Step through D3 with a run live and with a dirty tree; name the outcome of every refusal and answer |
| 4 | spec-review-1 | D2 does not check that the stage can start fresh (plan, branch, worktree exist) | Warning | G | yes | Read the "Start checks" of the target stage and copy each into D2 |
| 5 | spec-review-1 | D10's three batches cannot run under one auto run (one branch, one squash per slug) | Warning | G | yes | Read how an auto run holds one branch and one merge before choosing batches plus Delegation |
| 6 | spec-review-1 | D7's "needs you" line fires while a rerun would start nothing (gated, exclusive, deadlock) | Warning | A | yes | Check each status line against Goal 4: would the named command do anything in this state? |
| 7 | spec-review-1 | A live or queued blocker outside the call is treated as unwakeable; D2 skips not said to be written | Warning | A | yes | List every kind of blocker and say which one wakes the row, and whether skips go to the queue |
| 8 | spec-review-1 | Refill failure is a "signal" but "never a stop"; Signal stops and waits, Finish marks ✓ | Warning | G | yes | Read the existing "Signal" and "Finish" rules and say which mark and last line win |
| 9 | spec-review-1 | D5 does not say what `pull` does when `start()` refuses an entry | Suggestion | A | yes | For every call into existing code, state the behaviour on each refusal it can return |
| 10 | spec-review-1 | D3 hardcodes the commit scope `docs(plans)`, which is only this repo's scope | Suggestion | G | yes | Copy the code stage's wording "the scope the project's rules give docs" |
| 11 | spec-review-1 | Out of scope says refills always run in tmux; D6's second place may run outside tmux | Suggestion | E | yes | Cross-read Out of scope against every Decision |
| 12 | spec-review-1 | D9's locked commit has no working directory; `locked-commit.py` has no `-C` | Suggestion | G | yes | Read `locked-commit.py`'s arguments before naming it in a path-taking skill |
| 13 | spec-review-1 | Blast radius omits `status-scan.py` and `my:status` as callers of `handoff-state.py` | Minor | G | yes | Run `git grep -l handoff-state -- ':!docs'` and paste the list |
| 14 | spec-review-2 | D3's waiting fixups become unfoldable once the next `done` mark cites a newer commit | Critical | G | yes | Run `git-fold-fixups.py` in a fixture: fixup, later cited commit, fold (refusal at :224-227) |
| 15 | spec-review-2 | D2 handles only gates that name a row; `my:status` step 5 also has "Waits for …" text | Warning | G | yes | Read `my:status` step 5 and the real gate texts in `ROADMAP.md` |
| 16 | spec-review-2 | Rule 4 cannot see that a hand-started run is exclusive (no `exclusive` in state files) | Warning | A | yes | Same field table as #2: where `exclusive` lives decides who can see it |
| 17 | spec-review-2 | `queue show` and D7 have no output for a full cap, or an exclusive entry behind a non-exclusive run | Suggestion | A | yes | Enumerate the walk's stop cases and give each an output line |
| 18 | spec-review-2 | Risk names one crash window; a crash between `pull` and Launch is a second | Suggestion | A | yes | List every step pair with a write between them and say what a crash there leaves |
| 19 | spec-review-2 | Needs investigation: does a `done` mark set the roadmap row to ✅? | Open question | G | yes | Read a recent auto run's `done` commit before defining "done" in D2 |
| 20 | plan-review | A re-added slug's old `skipped` entry makes rule 2 skip the rows behind the new entry | Warning | A | yes | A per-slug state table: can a slug have two entries, and which one does rule 2 read? |
| 21 | plan-review | Three `pull` tests check only empty stdout, so they pass before `pull` exists | Warning | T | partly | Testing states that every CLI test asserts the exit code, plus one positive fact |
| 22 | plan-review | Plan Decision 14 silently rereads D3's "tree is clean", which can never hold at that step | Warning | D | yes | Check each D3 condition against Context bullet 2: the `approved` edits are still uncommitted then |
| 23 | plan-review | Refill failure conflicts with Launch step 4, which would mark the finished run as stopped | Warning | G | yes | Read Launch step 4 (`SKILL.md:293-297`) and name the exception in D6 |
| 24 | plan-review | Task 4 takes D7's cap from `my:status` step 3 (default 2), not D5's `<n>` (1) | Warning | P | partly | D7 says "the `<n>` of D5" instead of a bare **Max runs** |
| 25 | plan-review | Nothing tests D3; the rehearsal may run with the `approved` edits already committed | Warning | T | yes | Testing names a D3 case: rehearsal specs keep `approved` uncommitted; check no `fixup!` on `main` |
| 26 | plan-review | Task 1 step 2 says every new test fails; `test_live_ignores_the_queue_folder` passes already | Suggestion | P | no | Nothing: plan wording |
| 27 | plan-review | Decision 7 and the tests omit `queue drop`'s refusal on an unreadable queue file, which D5 asks for | Suggestion | P | no | Nothing: the spec already said it |
| 28 | plan-review | Reference sweep names only `ROADMAP.md` row 34; rows 42, 43 and an order line also match | Minor | P | no | Nothing: no edit needed in this branch |

Class reading notes:

- #3 rests partly on the fold script's refusal rules (G). The race with a live run is
  visible from the spec alone, so it is A.
- #5 is also a contradiction between Delegation and D10. The fact that settles it (one
  branch per auto run) is in `SKILL.md`, so it is G.
- #22 is D because D3's fold condition was chosen on a false premise, and the user had
  to choose again. The defect itself is a contradiction between D3 and Context.

#### Row 9: 2. Counts

Per class:

| Class | Count | Findings |
| --- | --- | --- |
| G — grounding | 10 | 4, 5, 8, 10, 12, 13, 14, 15, 19, 23 |
| A — adversarial design | 10 | 1, 2, 3, 6, 7, 9, 16, 17, 18, 20 |
| D — decision | 1 | 22 |
| E — editorial | 1 | 11 |
| P — plan only | 4 | 24, 26, 27, 28 |
| T — test design | 2 | 21, 25 |
| **Total** | **28** | |

Per stage:

| Stage | Count | G | A | D | E | P | T |
| --- | --- | --- | --- | --- | --- | --- | --- |
| spec-review-1 | 13 | 6 | 6 | 0 | 1 | 0 | 0 |
| spec-review-2 | 6 | 3 | 3 | 0 | 0 | 0 | 0 |
| plan-review | 9 | 1 | 1 | 1 | 0 | 4 | 2 |

Preventable at spec: 23 yes, 2 partly (21, 24), 3 no (26, 27, 28). Without the
spec-review-1 baseline, the later stages hold 15 findings: 10 yes (14 to 20, 22, 23, 25),
2 partly (21, 24) and 3 no (26 to 28).

#### Row 9: 3. Findings decided by the user

At face value, the documents name **14** user decisions:

- **Spec review 1: 8.** Its status line says "eight design findings decided by the user".
  It has nine design rows (1 to 9) and does not say which one was not decided by the
  user. The four editorial fixes are 10 to 13.
- **Spec review 2: 4.** Its status line says D3 was reworked to fold at once (#14) and
  "the other findings were decided by the user": 15, 16, 17, 18. #19 was answered in D2's
  text ("a `done` mark does not always set ✅").
- **Plan review: 2.** #20 (plan Decision 16) and #22 (plan Decision 14), recorded in the
  body of `51dc317`.

Footnote: review 2 does not say who chose the fix for its Critical #14. The method asks
that every design finding go to the user, so the true count may be 15, but no document
says so.

#### Row 9: 4. The two questions the plan stage stopped on

1. **D3's clean-tree test (#22).** D3 said the call folds only when
   "`git status --porcelain` prints nothing". At that moment the queued specs' `approved`
   edits are still uncommitted, which is the spec's own Context, bullet 2, and the reason
   D3 exists. So the fold could never run. The user chose the reading "lists only the
   edited specs", the same rule the plan stage uses for its own check.
2. **A re-added slug (#20).** D4 refuses a duplicate only when the slug is `waiting`.
   Prune keeps a `skipped` entry while a `waiting` entry names it. Rule 2 skips a row
   whose blocker "belongs to a `skipped` entry". So drop `a`, re-add `a` and `b` after
   `a`: `pull` starts the new `a` and skips `b`. The user chose: a re-added slug removes
   its old `skipped` entries, and `queue add` sorts the waiting entries again.

**Would a harder spec have settled them? Yes, both, and for the same reason.** Each came
from fix text the spec took from a review's own Fix column and never traced again:

- #22 came from review 2's Fix for its Critical #14: "no run live, clean tree, user
  agrees". The spec copied "clean tree" without checking it against Context. A
  step-by-step trace of D3 (what does `git status` show at each step?) shows the
  condition can never pass. No repo knowledge is needed.
- #20 came from two options taken from review 1's Fix for #2: keep `skipped` entries that
  a waiting entry names, and add `queue drop`. Together with D4's waiting-only duplicate
  check they make the bug. A table of a slug's states and the moves each command makes
  (add, drop, pull, prune) exposes it from the spec alone.

No third spec review ran after the D3 rework. The spec went to approval with its Critical
fix never reviewed, and the plan review found the defect in it.

#### Row 9: 5. Patterns: draft-time checks that would have caught the most

1. **Re-trace every fix taken from a review before approval.** Six findings were made by
   an earlier fix: #14 (from the fix of #3), #16 (from #2's choice to keep `exclusive` in
   queue entries only), #17 (from #6's `queue show`), #20 (from #2's prune and drop),
   #22 (from #14's fix), #23 (from #8's refill-failure branch). A cheap form: after each
   review round, diff the spec and run the review's model only on the changed decisions.
   Or run a third spec review whenever a Critical was fixed.
2. **Write a state table for every stored fact.** For each field and each queue entry:
   who writes it, who reads it, who deletes it, and which states a slug can be in. Then
   walk each command (add, drop, pull, prune, show) through it. This catches #1, #2, #7,
   #9, #16, #17, #18, #20.
3. **Read every existing skill section the spec hooks into, and quote the line.** The
   spec reused start checks, Signal, Finish, Launch step 4, `my:status` step 5 and the
   one-branch auto run without reading them closely. This catches #4, #5, #8, #10, #15,
   #23, and #12 and #13 with a `git grep`.
4. **Run the tools the design depends on in a fixture repo, in the order the spec gives.**
   A fixture with an uncommitted `approved` edit, a fixup and a later `done` commit shows
   the fold refusal (#14), the never-clean tree (#22) and the fold under a live run (#3).
   Reading one recent `done` commit settles #19.
5. **State each test's assertion in the spec, with its exit code and setup.** "Every CLI
   test asserts the exit code and one positive fact" prevents #21. Naming a D3 case and
   "the rehearsal keeps `approved` uncommitted" prevents #25. Naming the cap as "D5's
   `<n>`" wherever D7 uses it prevents #24.

#### Row 9: 6. Findings only running code could reveal

None. Every finding came from reading the spec, the plan and the repo. #14 was
reproduced in a fixture repo, but `git-fold-fixups.py:224-227` predicts it on reading.

The Task 8 rehearsal is still pending. It is the first point where running behaviour can
show something no document does: Launch from a review session (plugin-dir flags,
`MY_AUTORUN` of the new slug), the tmux window marks, the real fold in the call, and the
real cost of two auto runs.
