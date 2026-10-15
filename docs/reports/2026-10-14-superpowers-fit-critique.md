# Critique: how the `my` method fits with superpowers

**Status:** current, 2026-10-14. Five findings (F1 to F5) and one no-action note (N1) on where the `my` method and superpowers 6.4.1 overlap, two measurements of where the flow waits (B1, B2), two tests (T1, T2) to compare the code stages, and five options (O1 to O5) for the overlap; not yet routed to roadmap rows.

## How to read this

- **Question.** Is the workflow of the `my` method, combined with superpowers, efficient? Or is
  it bloated and redundant?
- **Baseline.** [`2026-10-09-workflow-efficiency-critique.md`](2026-10-09-workflow-efficiency-critique.md)
  answered "is it fast?" with "mostly efficient". Its fixes (rows 24 to 27) are done. Its
  findings S2, S3 and M1 to M4 are not raised again here. This report adds only what changed:
  superpowers 6.4.1, and the growth of `my:handoff`.
- **Related reports.**
  [`2026-10-12-handoff-instructions-audit.md`](2026-10-12-handoff-instructions-audit.md) (the
  length of `my:handoff`, rows 30 and 31) and
  [`2026-10-14-spec-hardening-audit.md`](2026-10-14-spec-hardening-audit.md) (what the reviews
  find).
- **Subject.** `global/CLAUDE.md`, `global/methods/my.md`, `global/rules/docs-layout.md`,
  `global/rules/plan-format.md`, `plugins/my/skills/handoff/SKILL.md`, and the superpowers 6.4.1
  skills in `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.4.1/skills/`.
  `brainstorming` and `executing-plans` were read in full; the others by search.
- **Method.** The files were read and their words counted with `wc -w`. Session transcripts
  checked two findings: F2 against 24 code-stage sessions, F5 against 48 review-stage sessions.
  F1, F3 and F4 are gaps in the text; none was seen to fail in a real session. B1 and B2 are
  timings: B1 from zitamu's git history, B2 from 54 session transcripts.
- **Scripts.** `assets/2026-10-14-superpowers-fit/` holds `stage_split.py` (B1) and
  `spec_time.py` (B2), with the usage line at the top of each. `spec_time.json` holds the rows
  B2 counts, because old transcripts may be deleted.

## Short answer

**The process is not bloated. The instructions are.**

- **The steps earn their cost.** The spec-hardening audit counted 176 findings after the first
  spec review. The 10-09 critique traced 40 of 105 branch fixes on zitamu to the end-of-branch
  reviews, and 38 of those were visible to users. So the review chain is not redundant.
- **The always-loaded text did not grow.** On 10-09, `global/CLAUDE.md` held the core and the
  method together: 4,805 words. Today `global/CLAUDE.md` and `global/methods/my.md` hold 755 +
  3,731 = 4,486 words.
- **The waste sits in two places.** The first is where the method and superpowers both try to
  decide the same thing: the size of a task, the reviews, and how a branch ends (F1 to F3). The
  second is the length of `my:handoff` (F4).
- **One gap, where the method dropped a superpowers step.** Nothing runs the full test suite
  after the review fixes, and in about 8 of 27 review stages none ran (F5).
- **The words cost minutes; the bottleneck costs hours.** The flow waits for the user, not for
  the agent (B1). Writing a spec is the longest stage, and most of its active time is the
  user's (B2).

In other words: superpowers gives the method how to think inside one step. `my` decides which
steps run, in what order, and in which session. The two collide only where superpowers also
tries to decide those things.

## Who does what, by stage

The last column is the cost of combining the two. It lists superpowers text that is loaded but
overridden.

| Stage | From superpowers (used) | Added by `my` | Superpowers part switched off |
| --- | --- | --- | --- |
| **Sizing** | — | Small, Medium, Large, and which steps each one gets | Brainstorming's spike, bounded and architectural (mapped only when a brief exists, F1) |
| **Architecture** | — | `my:architect`: the forces table, candidate designs, estimate scripts, the brief | — |
| **Spec** | `brainstorming`: one question at a time, 2–3 approaches, design in sections, self-review, the user's approval | Spec rules: "How to read this spec", Risk, Dependencies, Trade-offs, Visual Language, Delegation. `my:spec-review` with editorial and design findings. "No silent reinterpretation". UI is drawn on a design canvas | Save path, Visual Companion, the jump straight to `writing-plans` |
| **Plan** | `writing-plans`: task format, test-first steps, self-review | `plan-format.md` sections (Files to Modify from the reference sweep, Risk, Dependencies). `my:soundness-review --plan-only`. Runs in its own session | Save path, the closing execution question, the reader of Review Focus (F3) |
| **Code** | `test-driven-development`, `systematic-debugging`, `verification-before-completion`, the execution skill's task loop and ledger | Worktree via `git worktree add`. Focused tests, then the full suite once per task. Read the test diff after each task. Stops: new dependency, out of scope, weakened assertion | Worktree setup, pre-flight review, per-task reviewers and fix loop. The rulings report still runs in 16 of 24 sessions, but nothing reads it (F2) |
| **Review** | — | `my:soundness-review` and `/code-review high` in parallel on `main..<branch>`. Callers mapped with LSP first. One fix round, one re-review. Known limits go to Risk | The execution skill's final review and fix pass. `requesting-code-review` |
| **Integrate** | — | Squash-merge, keep the branch, remove the worktree. Four commits on `main`, fixup folds, `done` marks. Roadmap and changelog skills | `finishing-a-development-branch` |
| **Running the stages** | — | `my:handoff`: one session per stage in tmux, auto mode, parallel runs, the row queue. `my:status`. `locked-commit.py` | — |
| **Glue** | — | Text that only manages superpowers: the trigger table, the precedence paragraph, "Discovery authority", "skip the skill's own reviews" (`my.md:10` to `:105`) | — |

What the table shows:

- **Superpowers is the core in three places only:** the spec dialogue, the plan's task format,
  and the coding discipline (TDD, debugging, verification). These skills mostly run as written.
- **Review, integration and running the stages are all `my`.** Superpowers has its own review
  and integration, and the method switches them off.
- **The overlap sits in the code and review stages.** The execution skill brings a full review
  cycle, and the method replaces all of it. The "Glue" row exists mainly because of this.

`finishing-a-development-branch` and `requesting-code-review` are replaced but no longer loaded,
since rows 24 and 25 fixed the trigger table. They cost nothing now.

## Findings

### F1. Two size systems, mapped only halfway

Superpowers 6.4.1 `brainstorming` has its own three sizes (its `SKILL.md`, "Three Paths"):

- **Spike:** a question to answer, no code kept.
- **Bounded:** a design in chat, then the work starts. "No spec file, no implementation plan
  document."
- **Architectural:** the full path with a written spec.

The method maps these sizes only when an architecture brief exists: "Brainstorming classifies
the task as architectural, never bounded or spike" (`global/methods/my.md:71`). A Medium change
usually has no brief. Brainstorming's own test for bounded is "a well-scoped change to code
that already exists in this repo". Many Medium changes pass that test. Then brainstorming says
"no spec, start now", while the size table says "one spec, then hand off the code".

This is the same kind of double order as C1 and C2 in the 10-09 critique.

**Fix:** one line in the size table: Small skips brainstorming; Medium and Large always take its
architectural path.

### F2. The code stage loads an execution skill, then switches most of it off

The code stage runs `superpowers:executing-plans` (3,267 words) or
`superpowers:subagent-driven-development` (7,871 words)
(`plugins/my/skills/handoff/SKILL.md:802`). The method then switches off, in
`global/methods/my.md:102`:

- the worktree setup (the code stage runs `git worktree add` itself)
- the pre-flight review
- the per-task reviewers and their fix loop (`subagent-driven-development` only)
- the final review and its fix pass
- the closing step, `finishing-a-development-branch`

Two parts still run, and the method never mentions either:

- **The ledger.** A progress file at `.superpowers/sdd/<plan>/progress.md`. It lets a run resume
  after the context is compacted.
- **The rulings.** A ruling is a ledger line where the executor records a decision it made
  without asking (`executing-plans`, "Rulings, not stalls"). The skill reports them in its final
  message under "Rulings I made", together with "Deferred minors". That step comes after the
  final review, which is switched off.

`grep -rn -i -E "ledger|ruling" plugins/my/` finds nothing. The review stage does not read the
rulings.

The switched-off parts still read as orders. `executing-plans` says "Do not dispatch a
re-review" and "Use superpowers:finishing-a-development-branch". The method allows one
re-review and does its own squash-merge. A precedence rule settles it: "the project's rules
win" (`plugins/my/skills/handoff/SKILL.md:802`).

**What the sessions show.** The transcripts in `~/.claude/projects/` hold 24 sessions since
2026-10-01 that loaded one of the two execution skills, outside scratch and test directories.
Only the agent's own tool calls and messages were counted, not the loaded skill text:

| What the skill orders | Sessions where the agent did it |
| --- | --- |
| Invoke `finishing-a-development-branch` | 0 of 24 |
| Run `review-package` for the final review | 0 of 24 |
| Dispatch a per-task or a final reviewer | 0 of 24 |
| Create the ledger (`sdd-workspace`) | 23 of 24 |
| Write `Ruling:` lines | 24 of 24 |
| Print "Rulings I made" in the final message | 16 of 24 |

- **The overrides held every time.** No session followed a switched-off order. So the cost of
  the overlap is the loaded words, not wrong actions.
- **Rulings are made in every session, and reach the user in two thirds of them.** In 8
  sessions, the final message did not list them. When it does, the list sits in the code-stage
  session's last message. The review stage never reads it, and in an auto run nobody may read
  that window.

The counts come from a text search of the transcripts. A reviewer dispatch phrased in other
words would be missed.

Upstream now does almost what the method does at the end of a branch: one whole-branch review
and one fix pass. The method differs in two ways. It runs two reviewers, and it allows one
re-review.

- **Option A: replace the execution skill.** Write the task loop into the code stage of
  `my:handoff`, about 200 words. Pros: 3,000 to 8,000 fewer loaded words per code session, and no
  conflicting orders. Cons: no upstream updates, and no ledger scripts unless they are copied.
- **Option B: keep the skill, and read what it leaves.** The review stage reads the ledger's
  `Ruling:` and `minor (deferred)` lines and passes them to the reviews and to the user. Pros:
  one step, and the parts that work keep working. Cons: the code session still loads text it
  ignores.
- **Recommendation:** B. The sessions show the overrides hold, so the conflicting orders cost
  words, not mistakes. The gap that matters is the rulings, and B closes it.

### F3. Plans write a Review Focus section that nobody reads

`writing-plans` asks each plan for a **Review Focus** section: the inputs and failure modes that
the plan's tests do not cover (its `SKILL.md`, "Self-Review", item 4). Its only reader is the
execution skill's final reviewer, which the method switches off (F2). `plan-format.md` and the
`my:soundness-review` prompts do not mention it.

**Fix:** the end-of-branch reviews get the plan's Review Focus section with the plan. It is the
list of untested cases that M4 in the 10-09 critique wanted the reviews to check.

### F4. `my:handoff` tripled, and its split waits on unrelated data

`plugins/my/skills/handoff/SKILL.md` grew from 3,246 words (10-09) to 8,526 (10-12) and 10,441
today. The 10-12 audit had already flagged its length, and 2,058 words came after it.

Five sections serve only auto or parallel runs: "From roadmap rows" (1,601 words), "Resume"
(772), "Stop points in auto mode" (653), "Parallel runs" (538) and "Delegation" (209). That is
3,773 words. More auto-only text sits inside "Run" (4,870). By section, a supervised stage uses
roughly a third of the file. This share was not counted line by line.

Row 30, "Split `my:handoff` by mode", waits for row 29, "Measure the auto runs". Row 29 waits
weeks to time how long specs take to reach `done`. That timing does not tell whether each stage
session should load 10,000 words. Meanwhile every handed-off session pays for them.

**Decision for the user:** keep the wait, or move row 30 ahead of row 29.

### F5. No full test run after the review fixes

**Per task, the method's test rule matches superpowers.** The code stage's rule
(`plugins/my/skills/handoff/SKILL.md:809`, added in `17a65b9`) runs only the touched test files
while a task is in progress, then the full suite once per task, before its first commit.
Superpowers says the same: its implementer prompt (`subagent-driven-development/implementer-prompt.md:47`)
and `test-driven-development` (`SKILL.md:185`) both ask for one full run before a task is done.
Fix rounds match too: both rerun only the tests that cover the fix.

The rule earns its copy. On zitamu row 103, the briefs the code stage wrote did not pass on
superpowers' rule, and 14 full runs took about 15 minutes. About 6.5 of them checked nothing a
focused run would miss.

**The gap is at the end of the branch.** The review stage runs its checks at step 2, before the
reviews (`handoff/SKILL.md:891`). Step 6 fixes the findings and says only "test and commit as
the project's rules say" (`:951`). Step 7 signals "ready to squash-merge" (`:966`). No step
requires a full run after the fixes. The code-stage rule even says a fix round "never runs the
full suite, because the review stage runs the end-of-branch checks"; but those checks ran before
the fixes. The only other line, "every code commit runs the tests" (`global/methods/my.md:100`),
describes the method rather than ordering a run, and does not say which tests.
`executing-plans` closes this: its fix pass ends only when the whole suite is green
(`executing-plans/SKILL.md:280`).

**It happens in practice.** The transcripts hold 48 review-stage sessions that reached "ready to
squash-merge", outside scratch and test directories. In 27 of them, code changed after the
reviews were dispatched. In about 8 of those 27, code changed after the last full run, and no
full run followed before the signal. Most of those last changes were small: a CSS line, a text
string, a test file. Whether any of them left a failing test on `main` was not checked.

Limits: the count comes from reading tool calls, sorted partly by hand. A full run inside a
subagent, such as a re-reviewer, is not visible. Edits that only add a test, or touch files the
suite does not cover, are counted as code changes.

**Fix:** one full run of the project's test command after the fix round, before step 7. On
zitamu that costs about one minute per branch.

### N1. The start-of-session hook overlaps the trigger table

The superpowers start-of-session hook adds `using-superpowers` (492 words) to every session. It
says: if there is even a 1% chance a skill applies, invoke it. The method's trigger table
already says which skill runs. The two do not contradict, and the cost is small.

**No action.**

## Where the flow waits

F1 to F4 cost words and, at most, minutes per branch. This section asks where the hours go.

### B1. Waits between stages

The 24 zitamu specs that reached `done` between 2026-09-14 and 2026-10-12, split by stage with
`stage_split.py` over the 10-09 critique's `data.json`:

| Stage | Median | Total |
| --- | --- | --- |
| Spec commit → plan commit | 0.6 h | 146 h |
| Plan commit → `done` | 1.4 h | 99 h |

Five stages of 12 hours or more hold 173 of the 246 hours (71%). They look like nights and days
with no session open, not slow work. A typical stage takes about an hour; the totals come from
waiting for the user to start the next one. This restates M2 of the 10-09 critique with the
split by stage.

`my:handoff auto` (shipped 2026-10-12) and the row queue (shipped 2026-10-14) run stages without
the user. Their effect is not measured yet; row 29 "Measure the auto runs" will do that.

### B2. Writing the spec

Git starts the clock at the first spec commit, so B1 does not see how long writing the spec
takes. `spec_time.py` measures it from session transcripts.

- **Sample.** 54 sessions in 10 projects, from 2026-09-13 to 2026-10-14. Each made a `Skill`
  call to `superpowers:brainstorming` and a `Write` to a `docs/plans/*-spec.md` path.
  Sessions in scratch, job and fixture directories are left out.
- **Phases.** Dialogue: from the brainstorming call to the first `Write` of the spec. Review:
  from there to the first `git commit` whose command names a spec.
- **Time classes.**
  - *Agent:* the agent is working, its subagents included.
  - *User:* the agent waits for a message or an `AskUserQuestion` answer, for up to 30 minutes.
  - *Away:* any single wait over 30 minutes.

Medians per spec session, in minutes:

| Phase | Total | Agent | User | Away |
| --- | --- | --- | --- | --- |
| Dialogue | 44 | 7 | 17 | 0 |
| Review | 12 | 8 | 2 | 0 |

- **A spec session takes 75 minutes at the median,** from the brainstorming call to the
  commit. That is longer than either stage in B1.
- **The dialogue is the user's time.** The user spends more than twice as long answering as the
  agent spends working: 17 against 7 minutes. A spec takes a median of 7 questions or
  replies, about 2.8 minutes each.
- **The review is the agent's time.** `my:spec-review` and the fixes take about 8 minutes; the
  user spends about 2.
- **Long gaps make the totals large, as in B1.** 26 of 54 sessions have at least one gap over
  30 minutes. Those gaps hold 84% of all elapsed hours; some sessions sat open for a day or
  more.

Limits:

- **"User" is not always idle time.** The user often runs several sessions at once, so a wait
  may be time spent in another session. The transcripts cannot tell the two apart.
- **A permission prompt counts as agent time.**
- **The phase ends are found from tool calls.** Four sessions never committed; their end is
  their last event. A spec written over several sessions, or after `my:architect`, is only
  partly counted.
- **The 30-minute line is a choice.** With a 15-minute line, the dialogue's user median is 12
  minutes; with a 60-minute line, 19. The agent median stays at 7, so the user's share is
  larger at every line tried.

What it means: the spec stage costs the user about 20 minutes of attention per spec, spread
over about 7 round trips. Auto mode does not help, because it starts after the spec is
approved. Two things could:

- **Fewer round trips.** Superpowers asks one question per message. `AskUserQuestion` takes up
  to 4 questions per call. Row 53 `my:draft-spec` drafts first and asks after.
- **Fewer needless questions.** The 449 questions and replies were not read. A sample of about
  50 would show how many asked for a real decision. For review findings, the spec-hardening
  audit gives a hint: 66 went to the user, but only 6 of all 262 findings were real decisions.

## Is the method's code stage better than upstream's?

**Not known.** No data in hand compares the two fairly.

- **No side-by-side runs.** Commit `1b774af` (2026-09-29) switched off the superpowers reviews.
  Since then, every code stage has used the method's version. Before that date, about 4
  sessions ran the superpowers reviews in full, in other projects, with an older superpowers
  version and earlier models.
- **Too much changed at once.** The superpowers version, the model, the projects and the
  method's own rules all changed in the same weeks. A difference in results could come from any
  of them.
- **"Effective" has no agreed measure.** It could mean defects that reach `main`, tokens, time,
  or how often a run stops to ask the user. Git records none of the last three.
- **What is known is one-sided.** The method's reviews find real defects (M3 in the 10-09
  critique). That does not show they find more than the upstream final review would.

Two tests could answer it:

- **T1. Replay the reviews on old branches.** Merged branches are kept, so each still has its
  commits from before the review fixes. On about 10 zitamu branches, run the upstream final
  reviewer (`requesting-code-review`'s `code-reviewer.md`) on the range before the fixes.
  Compare its findings and cost with what the method's two reviewers found, as recorded in the
  fix commits and Risk sections. Cost: one reviewer run per branch.
- **T2. Rehearse the whole code stage.** Run the same plans on a fixture repo with the same
  model, once with the method's code and review stages, and once with plain `executing-plans`
  and its own final review. At least 3 runs per setup, because runs vary. Compare defects
  caught, tokens, time and rulings reported. Cost: 2 plans × 2 setups × 3 runs = 12 full runs.
  Worth it only if T1 shows a real gap.

Both give evidence, not proof: the samples are small, and the results hold for the plans
chosen.

## Ways to handle the overlap

Five options, from changing nothing to dropping the method's own version. They are not
exclusive.

### O1. Accept the overlap, and close only the rulings gap

The overrides hold (F2), so the overlap costs words, not wrong actions. Keep everything as it
is. Fix only the gap: the review stage reads the ledger's `Ruling:` lines.

- **Pros:** one small change. Upstream updates keep arriving.
- **Cons:** each code session still loads 3,000 to 8,000 words it mostly ignores.

### O2. Load only the smaller execution skill

`subagent-driven-development` (7,871 words) is built around a per-task reviewer, which the
method switches off. What it adds after that is mainly a fresh subagent for each task.
`executing-plans` (3,267 words) runs the same task loop without that machinery. Plan stage
step 2 in `my:handoff` picks between the two; it could always pick `executing-plans`.

- **Pros:** halves the largest load, and removes the largest override.
- **Cons:** no fresh context per task, so on a long plan the later tasks run in a crowded
  context. Nothing shows which skill gives better results (see T1 and T2).

### O3. Put the overrides where the skill reads them

`executing-plans` reads the plan's header and its "Global Constraints" before Task 1. Today
the overrides sit in `global/methods/my.md:102`, far from where they apply. Plan stage step 2
already writes one header line saying the project's review rules replace the skill's. That
line could become a short fixed block: no final review, no `finishing-a-development-branch`,
and at the end, write the rulings to a named file.

- **Pros:** the order sits next to the text it overrides, at the moment the agent reads it. It
  also gives O1's rulings fix a natural home.
- **Cons:** one more fixed block in every plan.

### O4. Adopt the upstream end-of-branch flow, and drop the method's

Superpowers 6.4.1 has one whole-branch review, one fix pass, a test for each fix, and a rulings
list. That is close to the method's rule. The method could run it and keep `/code-review high`
as a second reviewer.

- **Pros:** much less text in `my:handoff`, and upstream maintains the rest.
- **Cons:** loses `my:soundness-review`, which checks each task against the plan, and the one
  re-review. The review would run inside the code session, not in a fresh one. The method's
  reviews have evidence in these projects (M3); the upstream flow has none yet.

### O5. Guard against drift

The overlap moves when superpowers changes. Version 6.4.1 added the three brainstorming sizes
(F1) and the new final review. The method found out by reading, not from an alert.

- **Pin the version.** Upgrade on purpose, and diff the overridden skills before each upgrade.
- **Add a check script.** Search the installed skills for the phrases the overrides depend on,
  such as `finishing-a-development-branch`, `Review Focus` and `bounded`. Warn when one appears,
  changes or disappears.

- **Pros:** a new overlap shows up when it arrives, not weeks later.
- **Cons:** one more script, and a manual step at each upgrade.

### Recommendation

O1, O3 and O5 together. Move the overrides into the plan header (O3), with the rulings fix in
the same block (O1). Add the drift check (O5), because the overlap will keep moving. Leave O2
and O4 until T1 gives evidence: both remove a part whose value nobody has measured.

## Where these went

Not routed yet. The user decides the rows and their place in `ROADMAP.md`, section "Order of
work".
