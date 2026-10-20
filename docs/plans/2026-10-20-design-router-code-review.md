# Design router: code review

**Status:** review of main..feat/design-router, 2026-10-20. No Critical or High findings; the fix round answered F4, F6 and F8, and plan Risk R18–R22 records the rest.

**Scope:** the range `main..feat/design-router`, read with `git diff main..feat/design-router`
(16 files, 737 lines added, 37 removed), up to the branch head (the headless rehearsal). This is
local `main`, not `origin/main`. The review ran the built-in `/code-review` at level `high`, and
then checked each finding against the code, the spec
(`docs/plans/2026-10-20-design-router-spec.md`) and the plan
(`docs/plans/2026-10-20-design-router.md`). A known limit in the spec's Risk section (R1 to R13)
or the plan's (R14 to R17) is not a finding. Both test suites pass: kit 70 tests, my 234 tests.

**Verdict:** no Critical or High finding. Nothing crashes, and no result was shown to be wrong.
Two findings are unconfirmed guesses about how Claude Code behaves (F1, F2). Each needs one short
manual check. The rest are Low.

## Findings

### F1. Medium (unconfirmed): the ticket's session ID and the hook's may differ after `/clear` or `--resume`

- **File:** `plugins/kit/bin/design-router-ticket.py:39`, with `plugins/kit/hooks/design-router-gate.py:71`.
- **What:** the ticket script files the ticket under `CLAUDE_CODE_SESSION_ID`, which it reads from
  the Bash environment. The gate looks it up under the hook input's `session_id`. Nothing checks
  that the two stay equal when the session ID changes inside one process: after `/clear`,
  `--resume` or `--fork-session`.
- **Failure scenario:** after `/clear` in a long session, the Bash environment might keep the old
  ID while the hook gets the new one. The ticket then lands in the wrong folder. Every routed call
  is refused with "invoke kit:design-router", even though the router ran, so the router cannot
  start any design skill for the rest of that session. The user's fallback is to type the command.
- **Evidence:** the rehearsal (Task 8) used only fresh `claude -p` sessions. Spec R11 and R16 do
  not cover a session-ID change. The map file already notes that both values must be the same.
- **Check:** in one interactive session, run the router once, `/clear`, then run it again.

### F2. Low (unconfirmed): a skill name with no `:` passes the gate unchecked

- **File:** `plugins/kit/hooks/design-router-gate.py:115`.
- **What:** `decide` returns `None` for any name without `:`.
- **Failure scenario:** if the Skill tool resolves a bare name such as `accessibility-review` to
  `design:accessibility-review`, the gate lets it through. The router never names that skill on
  purpose (it lists 2.5.5 as AA).
- **Evidence:** the spec's gate table lets "a name with no `:`" through, so the code matches the
  spec. Whether the Skill tool resolves bare names to plugin skills is not checked anywhere.
- **Check:** call `Skill` with a bare plugin-skill name in a test session and see whether it runs.

### F3. Low: a project skill folder named like a listed plugin is refused

- **File:** `plugins/kit/hooks/design-router-gate.py:127-133`.
- **What:** the `routed` and `excluded` states are checked before the "installed" check, so they
  apply whether or not that plugin is installed.
- **Failure scenario:** a project keeps its own skills under `.claude/skills/data/` or
  `.claude/skills/design/`. These show as `data:<name>` or `design:<name>` (D7 says project
  subfolders appear as `<folder>:<name>`). Claude's call is refused with "data is excluded from the
  design router", which is wrong for a project skill. The user can still type the command.
- **Evidence:** D7 lets an uninstalled prefix pass so that project folders work, but `data` and
  `design` are common folder names and are in `plugins.json`. Spec R2 covers two plugins sharing a
  name, not a project folder sharing a plugin's name.

### F4. Low: the ticket script rejects a leading `/` that the gate accepts

- **File:** `plugins/kit/bin/design-router-ticket.py:42`, against
  `plugins/kit/hooks/design-router-gate.py:114`.
- **What:** the gate strips one leading `/` from the skill name. The ticket script rejects any
  name that holds `/`.
- **Failure scenario:** the router's fallback text writes skills as `/<skill>`. If Claude passes
  `/design:ux-copy` to the script, it exits 1 with "bad session ID or skill name", and the skill
  does not start, although the gate would have taken the same name. It fails safe: the router then
  prints the command for the user.
- **Fix:** strip one leading `/` in the script too, as the gate does.

### F5. Low: a broken `plugins.json` warns on every prefixed Skill call

- **File:** `plugins/kit/hooks/design-router-gate.py:120-126`.
- **What:** the list is read for every name with a prefix other than `kit`, so the warning shows
  on `superpowers:*` and `my:*` calls too, not only on design skills.
- **Failure scenario:** after a syntax error in `plugins.json`, every `superpowers:brainstorming`
  or `my:status` call shows "Design router gate: cannot read …". Many repeats in one session can
  teach the user to ignore the message that R1 relies on for detection.
- **Evidence:** the spec's gate table asks for this message when the list cannot be read, so the
  code matches the spec. The finding is about how often it shows.

### F6. Low: `tickets_dir()` and `safe()` are copied in two files, and the copies already differ

- **File:** `plugins/kit/bin/design-router-ticket.py:25-31` and
  `plugins/kit/hooks/design-router-gate.py:59-65`.
- **What:** both scripts define the ticket folder and the name check. Only the gate's `safe()`
  checks that the value is a string.
- **Failure scenario:** a later change to the default folder or to the name rule in one file only
  makes the script write where the gate does not read, and every ticket is lost. The tests set
  `DESIGN_ROUTER_TICKETS` for both scripts, so they would not catch the drift.
- **Fix:** a test that runs the script and then the gate with the default folder (a temporary
  `HOME`), or one shared module.

### F7. Low: ticket folders are never removed

- **File:** `plugins/kit/bin/design-router-ticket.py:46-49`.
- **What:** each session that runs the router leaves a folder under
  `~/.cache/design-router/tickets/`. A ticket whose call never happens stays until the same skill is
  called again in that same session, which for a closed session is never.
- **Failure scenario:** empty folders and dead tickets pile up over months. No wrong result, since
  a stale ticket is refused by age.

### F8. Low: the README entry for `my:design-system` contradicts itself

- **File:** `README.md:130-135`.
- **What:** the edited bullet still says "`refresh` updates it at step 13", then adds "The method no
  longer calls it". This branch removed the step 13 call from `global/rules/docs-layout.md`.
- **Related, out of this branch's scope:** the skill's own description in
  `plugins/my/skills/design-system/SKILL.md:3-12` still says "Use … at step 13" and that "spec
  reviews check" the inventory. The user's `deny` rule for `Skill(my:design-system)` (D10) stops
  Claude from starting it on this machine, and row 69 decides the skill's future, so only the
  README sentence is a finding here.
- **Fix:** drop "at step 13" from the README bullet.

## Findings not kept

- **The `kit` special case repeats the list's `"kit": "not-design"` entry** (gate line 118). Not a
  finding: D8 requires that `kit`'s skills are never refused, so the router can run even when the
  list is broken or lacks `kit`. The list entry cannot replace that.
- **The gate checks for a ticket before it reads the list.** It costs one `stat` of a missing file
  per prefixed call, and the order follows the spec's gate table. No failure follows from it.
