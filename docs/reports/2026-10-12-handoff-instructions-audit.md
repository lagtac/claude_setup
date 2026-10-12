# Audit: the `my:handoff` instructions

**Status:** current, 2026-10-12. Four rubric findings (R1 to R4) and five findings on length and structure (P1 to P5). R1 to R4 are fixed. P1 to P5 are rows in `ROADMAP.md`, section "`my:handoff` instructions".

## How to read this

- **Subject:** `plugins/my/skills/handoff/SKILL.md` (8,383 words) and
  `plugins/my/skills/handoff/README.md` (3,097 words). The scripts on `PATH`
  (`handoff-state.py`, `handoff-lock.py`, `git-fold-fixups.py`) were not
  audited. Only their `--help` text was read.
- **Two lenses, kept apart.**
  - **Rubric:** the `my:tune-claude-instructions` rubric
    (`plugins/my/skills/tune-claude-instructions/references/grading-rubric.md`).
    It grades scope, reasoning and format, and checks tools, the harness and
    consistency. It does not grade length.
  - **Writing rules:** Matt Pocock's `writing-for-agents` skill
    (`github.com/mattpocock/skills`, `skills/productivity/writing-for-agents/SKILL.md`,
    MIT licence). Its terms used here: **sprawl** (a document too long even
    when every line is live), **disclosure by branch** (keep in the main file
    what every path needs, and move the rest behind a pointer), **scattering**
    (one meaning split across many places), **single source of truth**,
    **environment as source of truth** (do not copy what a command's `--help`
    already says), and **leading words** (one known word in place of a
    repeated phrase).
- **Method:** both files were read in full. Section sizes were counted with a
  script that skips fenced examples. Overlay sizes are approximate, because
  the script guessed where each overlay paragraph ends. External pointers
  were found with `grep -rn` over `global/` and `plugins/`.
- **Hypotheses:** claims that a shorter or better-ordered file makes a model
  follow it more reliably are hypotheses. Nothing here was measured on a run.

## Short answer

**By the rubric, the skill is sound: Medium, from two one-line problems.**
Scope and format are explicit everywhere. Every search step has a `Bash`
fallback. The emphasis is calm.

**By the writing rules, the skill has a structure problem, not a wording
problem.** Every stage session loads all 8,383 words. About 3,000 of them
apply only in auto mode, and about 1,600 only in a project with a "Parallel
runs" section. A supervised plan stage uses about 2,850. The steps are also
written as a base step plus up to three patches (auto, parallel, auto and
parallel), spread over the file.

**Correction to an earlier claim.** In the session that led to this report,
I said every gate row came from a real failure. The history does not show
that. The auto rows (`39737e1`) and the parallel rows (`38f6c34`) both
arrived on 2026-10-12, each in one commit from its spec. They came from
design. They may still be right, but they are not proven by incidents.

## Audit table

| File | S | R | F | Severity | Why |
| --- | --- | --- | --- | --- | --- |
| `skills/handoff/SKILL.md` | ✅ | ⚠️ | ✅ | Medium | Judgment steps write no classification before acting (R2), so Low; the harness check fails on `PushNotification` (R1), which raises it to Medium. |
| `skills/handoff/README.md` | n/a | n/a | n/a | OK | User-facing explanation, no directives to the agent. One cross-file note under R4. |

## Rubric findings

### R1. `PushNotification` is called without being loaded

- **Where:** `SKILL.md:184`, "Signal", action 2.
- **What:** `PushNotification` is a deferred tool. Its schema is not loaded
  at session start, and a direct call fails. The same file loads `LSP`
  correctly with `ToolSearch("select:LSP")` at `SKILL.md:729`.
- **Fix:** "Load it with `ToolSearch("select:PushNotification")` the first
  time. If it is not available, skip this action." About 20 words.

### R2. Judgment steps act without writing their judgment first

- **Where:** Plan stage, step 4 (`SKILL.md:524`). Review stage, step 6
  (`SKILL.md:770`). Plan stage, step 2 (`SKILL.md:511`), the choice of
  execution skill.
- **What:** Each finding is sorted into "fix", "gate" or "Risk" in the
  model's head, then acted on. Only a `decide` in auto mode leaves a written
  reason. A wrong sort is invisible until the diff is read.
- **Fix:** "Before fixing anything, list each finding with its class (fix,
  gate or Risk) and one line of evidence." About 25 words. This adds length.
  It is a reliability fix, not a brevity fix.

### R3. Two step lists share the same numbers in the code stage

- **Where:** `SKILL.md:656`–`693`, "In auto mode, the code stage changes as
  follows".
- **What:** A sub-list for committing the spec runs 1 to 3. The next block
  then says "Step 1: after the worktree exists", which means the code stage's
  step 1. The Parallel runs paragraph in between says "step 1 always makes a
  normal `docs:` commit … and step 2 is skipped", which means the sub-list.
  A literal reader can apply either.
- **Fix:** Letter the sub-list (a, b, c) and say "sub-step a" in the Parallel
  runs paragraph.

### R4. Small drift

- `SKILL.md:471` says "today's check". The phrase dates from the spec. Write
  "the check".
- `README.md:389` says "Run one auto run at a time". The "Parallel runs"
  default for **Max runs** is `2`. The README advice is about memory, so both
  can stand, but the README should say that the advice overrides the
  default on a 15 GB machine.

## Length and structure findings

### P1. Sprawl: every stage loads every mode

- **Evidence:** section sizes in words.

  | Section | Words | Used by |
  | --- | --- | --- |
  | Forms | 514 | all |
  | Delegation | 230 | auto only |
  | Parallel runs | 535 | parallel only |
  | Signal | 269 | all |
  | Stop points in auto mode | 646 | auto only |
  | Launch | 451 | all |
  | Resume, ending a run, restarted stages | 744 | auto only |
  | Start checks | 328 | all runs |
  | Start checks in auto mode | 616 | auto only |
  | Plan stage | 1,083 | plan stage |
  | Code stage | 673 | code stage |
  | Review stage | 1,819 | review stage |
  | Finish, rules for every stage | 212 | all |

  In addition, about 750 words of "In auto mode" paragraphs and about 1,100
  words of "With a 'Parallel runs' section" paragraphs sit inside the stage
  sections.
- **Disclosure by branch:** the branches are the form (launch, run, resume),
  the stage, auto or not, and parallel or not. Only Forms, Signal, Launch,
  Finish and the rules serve every branch.
- **Proposal:** keep these in `SKILL.md`. Move auto mode (Delegation, stop
  points, auto start checks, Resume, and the auto paragraphs) to `auto.md`.
  Move parallel material to `parallel.md`. Optionally move each stage to its
  own file.
- **Pointers the move would affect:**
  - `global/CLAUDE.md:103` names the skill's "Delegation" section.
  - `README.md` points at "`SKILL.md`, Stop points in auto mode".
  - `global/CLAUDE.md:173` and `global/rules/docs-layout.md:168` say "the
    `my:handoff` skill defines it" about the "Parallel runs" section.
  - Inside `SKILL.md`: 9 references to "Plan stage, step N", plus "Review
    stage, step 8" and "Code stage, step 1".
  - `my:status`, `commands/commit.md` and `my:architect` read the project's
    "Parallel runs" section, not the skill's. They are not affected.
- **Risk:** a literal model may not open a file behind a weak pointer. Each
  pointer must be a step with a condition, for example "Before any step of an
  auto form, read `auto.md` in this skill's folder." Rehearse one supervised
  and one auto run headless before and after the move.

### P2. Scattering: steps are written as patches

- **Evidence:** 7 "In auto mode" paragraphs and 9 "With a 'Parallel runs'
  section" paragraphs patch steps by number. Review step 8 exists in four
  versions: supervised (`SKILL.md:781`), parallel (`:798`), auto (`:841`),
  and auto with parallel (`:868`). A run in a parallel project in auto mode
  must merge all four in its head.
- **Options:**
  - **A, write each version whole** inside its mode file (after P1). Pros:
    the agent reads one list. Cons: some steps are copied, so a fix must be
    made in each copy.
  - **B, keep patches, but put each patch directly under the step it
    changes.** Pros: no copies. Cons: the file stays long, and a supervised
    run still reads the patches.
- **Recommendation:** A for review step 8, the only step with four versions.
  B for the rest.

### P3. One command in five copies

- **Evidence:** the locked commit command,
  `handoff-lock.py main -- sh -c 'm=$1; shift; git add -- "$@" && …'`,
  appears 5 times across `global/CLAUDE.md`, `global/rules/docs-layout.md`,
  `commands/commit.md`, `skills/architect/SKILL.md` and
  `skills/handoff/SKILL.md`. The copies match today. The rule that the
  heredoc lines start at column 0 appears 3 times in `SKILL.md`.
- **Proposal:** a small script on `PATH`, for example
  `locked-commit.py <paths> …`, that reads the message from stdin, then
  locks, stages, commits and prints the stat. Every copy shrinks to one line,
  and the heredoc rule is no longer needed. No new dependency: it is a
  Python script beside `handoff-lock.py`.

### P4. Text that copies a command or explains the design

- **Copies the environment:** the exit-code table for `handoff-lock.py`
  (`SKILL.md:163`–`172`) repeats `handoff-lock.py --help`. The steps use only
  exit 75 (row 18) and "any other failure" (row 23). Keep two lines and the
  rule about the `handoff-lock:` stderr line. About 70 words saved.
- **Explains the design to a maintainer, not the agent:**
  `SKILL.md:491`–`493` (why two starts cannot both pass the cap),
  `:157`–`159` (the kernel frees the lock), `:911`–`913` (cache expiry).
  These belong in the specs, which already hold them.
- **Keep:** the gotchas the agent cannot find on its own. Examples are
  "Always pass `-t`" (`:182`), "`git merge --abort` does not work here"
  (`:230`), and the column-0 heredoc rule until P3 removes it.

### P5. Leading words

- **Already good:** *signal*, *gate*, *stop*, *task doc*, *design doc* and
  `<base>` are each defined once and reused.
- **Candidates:**
  - *Locked commit* for "the locked form of Plan stage, step 7" (4 places).
  - *Shared-doc check* for "edits a shared doc only as Plan stage, step 6
    says" (2 places).
  - *Waiting fixups* for "found as in Plan stage, step 8" (4 places).
- Each named term also removes a "Plan stage, step N" reference, which P1
  would otherwise have to keep pointing across files.

## Not findings

- **Tools:** every search step has a `Bash` fallback (`SKILL.md:734`).
- **Emphasis:** a few "Never" rules (`never push`, `never use
  origin/<base>`), each paired with what to do instead.
- **Negation:** prohibitions are paired with the positive step.
