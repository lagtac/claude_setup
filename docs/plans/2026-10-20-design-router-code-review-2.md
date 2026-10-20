# Design router: code review, round 2

**Status:** review of main..feat/design-router, 2026-10-20. The fix round is correct and adds no new bug; three Low findings remain, none Critical, and none blocks the merge.

**Scope:** the range `main..feat/design-router`, read with `git diff main..feat/design-router`
(20 files, 1000 lines added, 41 removed). This is local `main`, not `origin/main`. This is the
final re-review after one fix round. It checks the fix round (the branch head) against the first
report, `docs/plans/2026-10-20-design-router-code-review.md`, and reads the whole range again at
level `high` for anything new: the built-in `/code-review high main..feat/design-router` ran on
the same range, and each of its findings was checked against the code, the first report and the
Risk sections before it was kept. A known limit in the spec's Risk section (R1 to R13) or the plan's
(R14 to R24) is not a finding. Both test suites pass on the branch head: kit 73 tests, my 234
tests.

**Verdict:** no Critical finding, and no High or Medium finding. The fix round does what its
commit message says, and its new tests can fail for the right reason. Three Low findings remain.
F1 is about a Risk entry that states as fact what the first report marked as unchecked. F2 and F3
come from the whole-range pass and are older than the fix round; F2 depends on Claude Code
behaviour nobody has checked.

## The fix round, item by item

- **The ticket script drops one leading `/` (first report F4).** Correct.
  `plugins/kit/bin/design-router-ticket.py:39` strips exactly one `/`, the same rule as
  `plugins/kit/hooks/design-router-gate.py:114`. The name check then runs on the stripped name, so
  `//design:x` still exits 1 in both, and `/` alone becomes the empty name, which `safe()` rejects.
  The error message now shows the stripped name, which is harmless. The test
  `test_ticket_script_strips_leading_slash` (`plugins/kit/tests/test_design_router.py:232`) would
  have failed before the fix: the old script exited 1 on any `/`.
- **A test covers the default tickets folder (first report F6).** Correct, and it can fail.
  `test_default_tickets_folder_is_shared` (`plugins/kit/tests/test_design_router.py:237`) unsets
  `DESIGN_ROUTER_TICKETS`, points `HOME` at a temporary folder, writes a ticket with the real
  script and runs the real gate. The fixture list marks `design-skills` as `routed`, so the gate
  prints nothing only when it found the ticket. Mutation check: a copy of the gate whose default
  folder was changed from `tickets` to `ticket` refused the call with the "invoke
  kit:design-router" message, so the test's `assertEqual(r.stdout, "")` fails on drift. The
  duplicated `tickets_dir()` and `safe()` remain in both files, but this test now guards the part
  that matters.
- **The router has a line for a refusal after a ticket.** Correct.
  `plugins/kit/skills/design-router/SKILL.md:41-43` and the spec's matching text tell the router
  not to invoke itself again, and to print the command. The "Both" brief (SKILL.md:99-101)
  already forbids subagents to invoke the router, so it needs no copy of the line. The chain step
  (SKILL.md:37-38) treats each skill "as above", so a refused skill in a chain gets its printed
  command and the chain goes on; the spec says the same. `test_refusal_after_ticket_goes_to_the_user`
  checks the line is present.
- **README (first report F8).** Correct. "at step 13" is gone from the `my:design-system`
  bullet. The skill's own text still names step 13, which R24 records.
- **Risk R18 to R24 and the manual steps.** Checked against the code and the machine:
  - R20 says no project under `~/projects` has a `design` or `data` skill folder. True on
    2026-10-20: `ls -d ~/projects/*/.claude/skills/{design,data,design-skills,frontend-design,design-superpowers,product-management}`
    finds none.
  - R21 names `test_list_states_are_valid`. It exists (`test_design_router.py:288`).
  - The manual step `Bash(design-router-ticket.py *)` matches how the router runs the script
    (`SKILL.md:27`, `design-router-ticket.py <skill>`, on the plugin's `bin/` path).
  - R19: see F1 below.

## Findings

### F1. Low: R19 states an unchecked behaviour as fact, and no manual step checks it

- **File:** `docs/plans/2026-10-20-design-router.md:785-786`.
- **What:** R19 says "The Skill tool calls plugin skills only as `plugin:skill`, so no plugin
  skill reaches the gate without its prefix." The first report (its F2) marked this as
  unconfirmed and asked for one manual check. The fix round turned it into a statement of fact.
  The new manual-steps list (plan lines 800-805) adds checks for R18 and R23, but none for R19.
- **Failure scenario:** if the Skill tool does resolve a bare name such as `ux-copy` to
  `design:ux-copy`, the gate never sees the prefix and lets a routed skill through without a
  ticket. A reader of R19 would not know to test for it, so the gap would go unnoticed.
- **Evidence:** the Skill tool's own description in a session reads "Plugin skills use
  `plugin:skill`". That supports R19, but it describes what callers should pass, not what the
  tool does with a bare name. No test or rehearsal step calls `Skill` with a bare plugin-skill
  name.
- **Fix:** soften R19 to "is expected to call", or add "call `Skill` with a bare plugin-skill
  name once and see whether it runs" to the manual steps. Either is a doc edit.

### F2. Low (unconfirmed): a name with a leading space or other capitals passes the gate

- **File:** `plugins/kit/hooks/design-router-gate.py:114-117`.
- **What:** the gate drops one leading `/` and then compares the prefix exactly. A leading space
  gives the prefix `" design"`, and `Design` differs from `design`; neither is in the list or
  installed, so the gate lets the call through without a ticket.
- **Failure scenario:** if the Skill tool trims spaces or ignores case when it resolves a name,
  Claude's call to `" design:ux-copy"` or `Design:ux-copy` runs a routed skill without the router.
- **Evidence:** run against the real gate with an empty tickets folder: `design:ux-copy` prints
  the deny decision; `" design:ux-copy"` and `Design:ux-copy` print nothing (let through). Whether
  the Skill tool resolves such names is not checked. The gate fails open by design and R10 says it
  is not a lock, so this is Low. Same family as R19, but R19 covers only names with no `:`.
- **Fix:** strip spaces and compare the prefix in lower case in the gate (and the same in the
  ticket script, so tickets still match); or add these names to the R19 manual check.

### F3. Low: the refusal sends a skill the router never names to the router

- **File:** `plugins/kit/hooks/design-router-gate.py:128-130`, with
  `plugins/kit/skills/design-router/SKILL.md:82-85`.
- **What:** every `routed` skill is refused with "invoke kit:design-router, which starts it". The
  router never starts `design:accessibility-review` or `design-skills:design-ops`, and has no step
  for a skill the user asked for by name.
- **Failure scenario:** the user writes "use design:accessibility-review on this page". Claude's
  call is refused and it invokes the router, which matches the `accessibility` row and starts
  `design-skills:accessibility-audit`. The router says which skill it ran (step 4), but not that
  the user's named skill was swapped, nor that the user can type `/design:accessibility-review`
  to get it.
- **Evidence:** the table names neither skill (SKILL.md:82-85); the spec (line 201) says they are
  never named. No Risk entry covers a user who names one.
- **Fix:** one line in the router: when the user named a skill the table never names, say so and
  print the command for the user to type.

## Findings not kept

- **The ticket script's error text shows the name after the `/` is dropped.** Harmless: the exit
  code and the "no ticket written" text are unchanged.
- **A chain does not say what happens after one refused skill.** The chain step treats each skill
  as a single job, and the refusal line covers each one; the spec says the same. No gap.
- **`my:design-system`'s description still claims design-system work and overlaps the router's
  `system-audit` row** (from `/code-review`). Covered: R24 records the stale text, and the user's
  `deny` rule for `Skill(my:design-system)` in `~/.claude/settings.json` (D10) stops Claude from
  starting it, so the two skills cannot both take the job.
- **A NUL byte in the name makes `Path.stat` raise `ValueError`** (from `/code-review`). The outer
  catch-all lets the call through, which is the gate's stated fail-open rule; the Skill tool would
  not resolve such a name.
- **The whole-name match in `test_neutral_core.py` no longer flags `my:handoff-state`-style text**
  (from `/code-review`). No such name exists: the `my` scripts are cited by file name
  (`handoff-state.py`), which neither the old nor the new check caught. A test-only trade-off made
  on purpose so that `design:design-system` is no hit.
- **The refusal names `kit@claude-setup`** (from `/code-review`). The marketplace name is fixed by
  `.claude-plugin/marketplace.json` (`"name": "claude-setup"`), so every install of this kit has
  that name.
- **`tickets_dir()` and `safe()` are copied in two files** (from `/code-review`). The first report's
  F6; the fix round chose the default-folder test, which catches a drift (see above).
- **The `kit` special case repeats the list** (from `/code-review`). The first report kept it out:
  D8 requires it, so the router runs even when the list is broken.
- **The `design` bullet in `global/methods/my.md:177` shares the `design` plugin's name** (from
  `/code-review`). The branch did not change that bullet, its text names the Artifact tool's Design
  type, and the `design` plugin has no skill that draws a screen, so no call is sent the wrong way.
