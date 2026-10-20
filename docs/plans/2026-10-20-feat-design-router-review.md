# Review: main..feat/design-router

**Status:** review of main..feat/design-router, 2026-10-20. Mixed: the gate, the ticket and the router are built as planned and the method no longer calls `my:design-system`, but the router has no step for a call the gate still refuses after the ticket was written, and its refusal text then sends Claude back into the router.

## Change Summary

The branch adds three parts to `kit`. The first is a `PreToolUse` hook on `Skill`, `plugins/kit/hooks/design-router-gate.py`. It refuses Claude's calls to skills of plugins that `plugins.json` marks `routed` or `excluded`, and of installed plugins that the list does not name, unless a fresh one-time ticket exists. The second is the ticket writer, `plugins/kit/bin/design-router-ticket.py`. The third is the `kit:design-router` skill, with its table of jobs. The global core gets a "Design work" section that sends design work to the router. The `my` method, `docs-layout.md` step 13, `my:handoff` and the spec-review prompt lose their `my:design-system` and `docs/DESIGN-SYSTEM.md` rules. The `my` names test in `test_neutral_core.py` now matches only whole names.

The caller sweep was done with text search only (`grep -rn`). I had no symbol tool.

## Plan Alignment

The code matches the plan closely. Tasks 1 to 7 are each present as specified:

- the gate's decision order and its texts (`plugins/kit/hooks/design-router-gate.py:111-141`);
- the 28-entry `plugins.json`;
- the hook entry and the manifest description;
- the ticket script, with its path guard;
- the 16-row table, written in the regex format the tests parse;
- the core section;
- all eleven method-file edits that Task 6, Step 2 lists;
- the README entries.

The kit and my suites pass: 70 and 234 tests.

Deviations and gaps:

- **Task 8, Step 2** says the rehearsal results go "into the squash commit's body". They are in the body of an empty commit on the branch, the rehearsal commit. `handoff-state.py` makes the squash commit with the message it is given (`plugins/my/bin/handoff-state.py:470-472`). So the results reach `main` only if the review stage copies them in.
- **Manual steps (missing).** The rehearsal commit body records two results. Headless in default mode, the ticket write was denied. It ran only with `--allowedTools 'Bash(design-router-ticket.py *)'`. R11 names this allow rule as the remedy. But neither the plan's manual steps (`docs/plans/2026-10-20-design-router.md:778-780`) nor the spec's "The user's settings" add it.
- **Stale `my:design-system` text.** The plan scoped the skill's own text to line 176 only, on purpose (row 69 decides the skill). But the README paragraph that this payload edits still says step 13 runs `refresh`. That contradicts the sentence the payload adds two lines later (`README.md:132` against `README.md:134-135`).

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | The router has no step for a refusal that comes after a ticket was written. The gate's refusal then reads "invoke kit:design-router, which starts it", although the router is already running. That invites a loop, or a design job that silently drops. It fires whenever the ticket does not match: a session ID that differs between the hook and the Bash environment (see Needs Investigation), or a ticket that is gone or stale. The router covers only a failed ticket script. | `plugins/kit/skills/design-router/SKILL.md:26-27`, `:40-41`; `plugins/kit/hooks/design-router-gate.py:68-77`, `:129-130` | Add one line under the ticket-failure line: "If the gate still refuses the call, do not invoke the router again; say so and print `/<skill> <arguments>` for the user to type." |
| Suggestion / High | The allow rule `Bash(design-router-ticket.py *)` is not among the manual steps. R11 names it as the remedy, and the rehearsal showed a headless default-mode run cannot start any design skill without it. That defeats D2's "the router decides, also where no user can answer". | `docs/plans/2026-10-20-design-router.md:778-780`; the rehearsal commit body, step 3 | Add "add `Bash(design-router-ticket.py *)` to the user's `permissions.allow`" to the `done`-mark manual steps. |
| Suggestion / High | The README entry this payload edits still says `refresh` "updates it at step 13". Two lines later it says the method no longer calls the skill. The skill's own description and `refresh` section also still say step 13 runs it, and that `my:spec-review` checks specs against it. Those parts are row 69's to decide, but the README sentence is in the edited paragraph. | `README.md:132` against `README.md:134-135`; `plugins/my/skills/design-system/SKILL.md:8`, `:10`, `:21`, `:29`, `:181-182` | Drop "at step 13" from `README.md:132`. Leave the skill's own text to row 69, and name it there. |
| Suggestion / High | The rehearsal results sit in an empty branch commit, not in the squash body that Task 8, Step 2 names. The handoff merge commits with an explicit message, so the results are lost unless someone copies them. | `plugins/my/bin/handoff-state.py:470-472`; plan Task 8, Step 2 (`docs/plans/2026-10-20-design-router.md:732-735`) | At the review stage, copy the rehearsal commit's body into the squash message. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| It fails open and never grants permission. A missing or broken list gives only a `systemMessage`, and no path prints `allow`. A crash is swallowed with exit 0, as in the sibling hook. | `plugins/kit/hooks/design-router-gate.py:124-126`, `:158-163`; `plugins/kit/hooks/method-guard.py:174-179` | Strong |
| Path safety. Session IDs and skill names that are `.`, `..`, empty or hold `/` are never joined, in either script. A test proves the unguarded join would escape. | `plugins/kit/hooks/design-router-gate.py:64-73`; `plugins/kit/bin/design-router-ticket.py:31-32`, `:40-44`; `plugins/kit/tests/test_design_router.py:239-257` | Strong |
| The tests use the real surface. Every gate and ticket test runs the real script as a subprocess, on the JSON that Claude Code sends, with all three paths redirected. The table tests read the real `SKILL.md` and `plugins.json`. | `plugins/kit/tests/test_design_router.py:95-110`, `:47-59` | Strong |
| It fits the existing patterns. The gate mirrors `method-guard.py`'s docstring and its `main` with `try/except` and `exit 0`. The ticket script sits in `kit/bin`, next to the other scripts on `PATH`. | `plugins/kit/hooks/method-guard.py:1-27`, `:174-179` | Moderate |
| The method removal leaves no orphaned caller. After the change, `DESIGN-SYSTEM`, `my:design-system` and `frontend-design` occur outside `docs/` only in the skill itself, `ds-count.py` and its test (out of scope per the plan), the history rows in `ROADMAP.md` and `CHANGELOG.md`, and the README. The skill still guards its own shared-doc check, so dropping it from `my:handoff`'s list orphans nothing. | `plugins/my/skills/design-system/SKILL.md:255-260`; grep sweep | Strong |
| The end-to-end rehearsal passed spec steps 1 to 5 with the branch's `kit` loaded. | the rehearsal commit body | Moderate |
| `kit` stays method-neutral. The whole-name matcher lets `design:design-system` through and still catches a bare `design-system`. A test pins both. | `plugins/kit/tests/test_neutral_core.py:35-43`, `:87-91` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| A refusal after a ticket is not handled, and the refusal text points back into the router. | `plugins/kit/skills/design-router/SKILL.md:40-41`; `plugins/kit/hooks/design-router-gate.py:129-130` | Medium |
| The headless path depends on an allow rule that no step adds. | `docs/plans/2026-10-20-design-router.md:778-780` | Low |
| Leftover text says step 13 still runs `my:design-system`. | `README.md:132` | Low |
| `tickets_dir` and `safe` are copied between the two scripts. They must stay in step by hand: a change to the default folder in one script alone would break every ticket. | `plugins/kit/hooks/design-router-gate.py:59-65`; `plugins/kit/bin/design-router-ticket.py:26-32` | Low |

## Not Applicable

None.

## Needs Investigation

- **The session ID after `/clear`, `--resume`, `--fork-session` or compaction.** The gate keys tickets by the hook's `session_id`. The script keys them by `CLAUDE_CODE_SESSION_ID`. F8 and the rehearsal checked only fresh sessions. If `/clear` gives the hook a new ID while Bash keeps the old one, every routed call fails after a successful ticket write. That makes the Warning above fire on every routed call. To resolve it: in one interactive session, run `/clear`, then compare `printenv CLAUDE_CODE_SESSION_ID` with the `session_id` that a logging hook receives. Do the same after `--resume`. The Warning's fix is worth making whatever this shows.
- **The ticket write in `auto` permission mode.** Auto hand-offs open only in `auto` or `bypassPermissions` mode (`plugins/my/skills/handoff/SKILL.md:306-309`). The rehearsal ran in default mode only. Nobody has checked whether the auto-mode classifier allows a Bash call that writes under `~/.cache`. If it refuses, a design job in an auto run falls back to "type the command", and no user can type it. To resolve it: repeat rehearsal step 3 with `--permission-mode auto`.
- **Project skill folders that share a name with a listed plugin.** D7 says project skills in subfolders appear as `<folder>:<name>`. A project folder named `design` would then be refused as `routed`, with a pointer to a router that does not know the skill. A folder named `data` would be refused as `excluded`. R2 covers two plugins with one name, not a folder name. I could not test the `<folder>:<name>` form from here. To resolve it: in a scratch project, create a skill folder named `data`, call one of its skills, and read the refusal.

## Reasoning

The approach is the one the spec chose, and it is built faithfully. The gate fails open, never grants permission, guards its paths, and is tested through its real surface. The method edits leave no orphaned caller. None of the findings questions the design. The one Warning is a missing recovery step in the router. That gap turns any ticket mismatch into a confusing refusal that points back at the router. How often it fires depends on the open session-ID question. The other findings are small gaps in manual steps and docs. With a Warning and no Critical, the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. The happy path is proven by tests and the rehearsal, but the session-ID behaviour after `/clear` or resume, and the ticket write in `auto` mode, are unchecked. They decide how much the Warning matters.
**Recommendation:** Add the one-line refusal fallback to `plugins/kit/skills/design-router/SKILL.md`. Drop "at step 13" from `README.md:132`. Add the allow rule to the `done`-mark manual steps, and carry the rehearsal results into the squash body. Then check the session ID after `/clear` and resume, and run rehearsal step 3 in `auto` mode, as part of the user's post-`done` checks (R16).
