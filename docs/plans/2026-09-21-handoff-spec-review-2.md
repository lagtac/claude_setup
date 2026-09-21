# Review: docs/plans/2026-09-21-handoff-spec.md

**Status:** review of docs/plans/2026-09-21-handoff-spec.md, 2026-09-21.
Mixed: the rewrite answers the first review's Critical finding and most of its
Warnings, but the D4 fallback command `tmux rename-window` renames the wrong
window, and a stage started in `acceptEdits`, `manual` or `dontAsk` mode can
still stop at a permission prompt that nobody sees.

## Spec Summary

The spec adds one skill, `my:handoff <stage> <doc>`. A session that finishes the
spec or plan stage uses it to open the next stage (plan or code) as a new named
top-level `claude` session in a background tmux window. Each stage session checks
its input document (D8), runs its stage (D9), and stops at named gates. At each
stop it sends a `PushNotification` and adds a `⚠` mark to its tmux window name
(D4). The plan session starts the code session by itself when the plan is
"clean" (D3). The code session squash-merges only after the user types yes in
its window.

## System Model

All caller and name sweeps in this review used plain text search (`grep`). No
symbol-reference tool was available. I also ran two probes: `claude --help` on
2.1.278, and `tmux rename-window` in a separate tmux 3.4 server
(`tmux -L probe-hr`), so the user's own windows were not touched.

| Component | Owns | Depends on | New / existing (verified at) |
| --- | --- | --- | --- |
| `my:handoff` launch (D7) | The name `<stage>-<slug>`, the duplicate check, the flag collection, the `tmux new-window` command, the printed fallback command | tmux, `$TMUX`, `$CLAUDE_PID` + `ps`, `ListAgents`, `claude -n/--plugin-dir/--permission-mode` | New `my-plugin/skills/handoff/SKILL.md` (not found, as expected) |
| `my:handoff` start checks (D8) | The go/no-go decision before a stage writes anything | The `**Status:**` line, `docs/plans/`, git branches `<type>/<slug>`, `.claude/worktrees/<slug>` | New |
| Plan stage session (D9) | The plan, the plan commit, the clean-tree check, the plan review run, the D3 "clean" decision, the code launch | `superpowers:writing-plans`, `my:soundness-review`, the project's docs rules | New (behaviour inside the skill) |
| Code stage session (D9) | The worktree and branch, the implementation, the end-of-branch reviews and fix round, the squash-merge after the user's yes, the `done` marks | `git worktree add`, `superpowers:executing-plans`, `superpowers:systematic-debugging`, the project's review rules | New (behaviour inside the skill) |
| Spec stage session (the user's) | The spec, its approval and `approved` status, the "Hand off the plan?" offer | One new line in `GLOBAL-CLAUDE.md` | Existing flow `GLOBAL-CLAUDE.md:40` |
| Stop signal (D4) | The notification text and the `⚠` window mark | `PushNotification` (feature flag + `agentPushNotifEnabled`), `tmux rename-window` | New use of existing tools |
| `my:soundness-review` | The plan review file and its findings | A clean tree for plan-review mode | Existing `my-plugin/skills/soundness-review/SKILL.md:96-113` |
| Status line values | `draft`, `approved`, `done` and the others | — | Existing `GLOBAL-rules/docs-layout.md:84-102` |

| From → To | What passes | Owner of what passes |
| --- | --- | --- |
| Spec session → launch | The call `plan <spec path>` after approval | Spec session |
| Launch → `ListAgents` | Lookup of the name, for the duplicate check | Harness |
| Launch → tmux → new session | Name, `--plugin-dir` flags, permission mode, first prompt `/my:handoff <stage> <doc>` | Launch |
| New session → start checks | Document path and status; any existing plan, branch or worktree | Repo (files and git) |
| Spec session → plan session | The `approved` status edit to the spec, and its index row | Unstated: neither stage says who commits it (see Issues) |
| Plan stage → `my:soundness-review` | Plan path on a clean tree; back comes a review file | `my:soundness-review` |
| Plan stage → D3 gate | The plan session's judgment of each finding (decision change or not), the pre-rebase check result | Plan stage |
| Plan stage → launch | The call `code <plan path>` | Plan stage |
| Any stage → user | `PushNotification` `<name>: <action>` and the `⚠` window mark | Stage session |
| User → stage window | Answers to gates, the yes for the squash-merge | User |

## Grounding

- `spec §D4` ("renames its own tmux window to `<name> ⚠` with
  `tmux rename-window`") ↔ probe on tmux 3.4: a command run inside a window
  opened with `tmux new-window -d` and calling `tmux rename-window 'plan-x ⚠'`
  with no `-t` renamed window 0, the active window, and left its own window
  unmarked. The same call with `-t "$TMUX_PANE"` renamed the right window.
  `$TMUX_PANE` is set in this session's Bash tool (`%100`), so the fix works from
  inside a `claude` session.
- `spec §D7` step 3 names "the mode the launching session is in" ↔
  `claude --help` on 2.1.278: the `--permission-mode` choices are
  `acceptEdits`, `auto`, `bypassPermissions`, `manual`, `dontAsk` and `plan`.
  There is no `default`. The spec's rule refuses only `plan` and an unknown mode.
- `spec §Goal` ("stops at the gates the global rules already define") ↔
  `GLOBAL-CLAUDE.md`: the new-dependency gate is global ("Never add new
  dependencies without approval"), but the pre-rebase checks, "a change outside
  the project's scope" and "a test failure that survives
  `superpowers:systematic-debugging`" are not in it (a text search for
  `rebase` in `GLOBAL-CLAUDE.md` finds nothing). D3 and D9 now word these as project rules or skill gates; only the
  Goal sentence still claims all of them are global.
- `spec §How to read this spec` lists the first review only. This review,
  `docs/plans/2026-09-21-handoff-spec-review-2.md`, is not listed.
- Holds: `claude --version` is 2.1.278; `-n, --name`, `--permission-mode`,
  `--plugin-dir` and a positional `[prompt]` are in `claude --help`;
  `$CLAUDE_PID` is set; `my:soundness-review` asks the user (`AskUserQuestion`)
  when a plan meets a non-empty payload, as D9 plan step 3 says
  (`my-plugin/skills/soundness-review/SKILL.md:101-113`); an empty payload with
  a plan path gives `plan-review` mode (`SKILL.md:103`); the test precedent's
  "How tests run" is at `docs/plans/2026-09-16-spec-review-skill.md:22-33`;
  `GLOBAL-CLAUDE.md:59` confirms that `editorial`/`design` labels belong to
  `my:spec-review` only, as D3 now says.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Warning / High | editorial | D4's fallback mark uses `tmux rename-window` with no target. From a background window it renames the window the user is looking at, and the stopped stage's window stays unmarked. Since `PushNotification` may be off, this mark is the only reliable stop signal, and as written it points at the wrong window. | `spec §D4`; tmux 3.4 probe (see Grounding) | Write the command as `tmux rename-window -t "$TMUX_PANE" "<name> ⚠"`. |
| Warning / High | design | The first review's permission-prompt finding is only partly answered. D7 refuses `plan` and an unknown mode, but passes `acceptEdits`, `manual` and `dontAsk` on as they are. In `acceptEdits` or `manual` the new session stops at its first Bash prompt (`git commit`, `git status`); in `dontAsk` it is refused the call. Neither case is a gate the skill sees, so there is no notification and no `⚠` mark, and D10 forbids polling. The Risk entry's mitigation ("D7 passes the launching session's mode") does not cover these modes. Also, "as its own context states it" may mean that only `auto` is ever known, so the launch falls back to printing a command in most sessions, which weakens D1. | `spec §D7` step 3 ↔ `§Risk` ↔ `§D10`; `claude --help` (`--permission-mode` choices) | Decision for the author: allow-list the modes that never prompt (for example `auto`, `bypassPermissions`) and print the command for every other mode, or accept the risk and say how the user finds a stalled window. |
| Warning / Medium | design | No stage owns the commit of the spec's `approved` status. D9 spec stage sets the status and launches; it does not commit. D9 plan step 3 stops on any uncommitted file on `main`, and the spec file with its new status is one. Plan step 2 commits "following the project's rules", and in zitamu a status change must go into the commit that causes it ("No commit only changes a status"), so the plan commit may be expected to carry it. Whether a session may commit another session's edit is not stated. If it does not, the plan stage stops on its own first run. | `spec §D9` Spec stage ↔ Plan stage steps 2-3; `GLOBAL-rules/docs-layout.md:111` (a file gets its index row in the commit that changes its status); `/home/dchris/projects/zitamu/real-estate-webapp/CLAUDE.local.md:283` | Decision for the author: the spec session commits the approval (with the spec review and index row) before it launches, or the plan stage's first commit takes the spec's status edit and index row with it. Then say so in D9. |
| Suggestion / High | editorial | D7 step 3's fallback prints "the command from step 4", which contains `<permission flag>`. When the mode is unknown, that placeholder has no value. | `spec §D7` steps 3-4 | Say that the printed command leaves out `--permission-mode` (or names it as a choice for the user) when the mode is unknown. |
| Suggestion / High | editorial | The Goal says the stage "stops at the gates the global rules already define". D3's pre-rebase checks and D9 code stage gates (change outside scope, a test failure after debugging) come from the project or from this skill. D3 and D9 already word them that way. | `spec §Goal ↔ §D3 ↔ §D9`; `GLOBAL-CLAUDE.md` (no such gates) | Reword the Goal: "stops at the gates this skill names, and at any the project's rules add". |
| Suggestion / High | editorial | "How to read this spec" lists the first review only. | `spec §How to read this spec` | Add a row for `docs/plans/2026-09-21-handoff-spec-review-2.md`. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Contracts and flow | D3's "clean" test is now the `GLOBAL-CLAUDE.md` Spec → Plan test (owner, contract, option, scope) and needs no labels. D8 and D9 share one naming rule for branch and worktree (`<type>/<slug>`, `.claude/worktrees/<slug>`) | Strong |
| Failures and interactions | D9 plan stage commits the plan before the review and checks `git status --porcelain`, which matches `my:soundness-review`'s plan-review row (`SKILL.md:103`) and avoids the unseen question (`SKILL.md:104`). The busy-`main` limit is stated in Risk | Strong |
| Grounding of the launch | `-n`, `--permission-mode`, `--plugin-dir` and positional `[prompt]` exist in 2.1.278; `$CLAUDE_PID` and `$TMUX_PANE` are set in a session | Strong |
| Fit: rejected options are real | D1, D2, D4 and D5 each reject an option with a reason tied to this design (context carry-over, fix round away from its context, peer messages are not approval, quoting) | Strong |
| Boundaries | One skill; D6 leaves project rules to the project's `CLAUDE.md`, which top-level sessions read. The squash-merge owner is now clear (code session, after the typed yes) | Moderate |
| Spec rules | "How to read this spec" is first; Risk, Dependencies and Trade-offs are present. No UI, so no Visual Language section is needed | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| Failures and interactions | The fallback stop mark goes to the wrong window; a stage in `acceptEdits`/`manual`/`dontAsk` can stall without any signal (`spec §D4`, `§D7`, `§Risk`; tmux probe) | Medium |
| Contracts and flow | The hand-off of the `approved` status between spec and plan stage has no owner (`spec §D9`) | Medium |
| Grounding | The Goal still credits all gates to the global rules (`spec §Goal`; `GLOBAL-CLAUDE.md`) | Low |

## Not Applicable

None.

## Needs Investigation

- **Is `PushNotification` available to this user, and does it skip the
  notification when the user is at that terminal?** Carried over from the first
  review. The tool depends on a remote feature flag that cannot be read locally.
  D4 now has the `⚠` mark as a fallback, so this matters less. To resolve it,
  call `PushNotification` once from a throwaway session in a background tmux
  window, then again with the window in front.
- **Does `ListAgents` report a session by its `-n` name?** Carried over. D7
  step 2's duplicate check depends on it. To resolve it, start `claude -n probe`
  in a tmux window and call `ListAgents` from another session.
- **Does a slash command given as the positional prompt run in an interactive
  session?** D5 and D7 depend on `claude -n <name> ... '/my:handoff <stage>
  <doc>'` running the skill, not sending the text as a plain message.
  `claude --help` shows `[prompt]` but does not say how a slash command there is
  handled. To resolve it, start `claude -n probe '/my:handoff plan <a draft
  spec>'` in a tmux window and check that the D8 check runs and refuses.
- **How does a session learn its own permission mode?** D7 step 3 relies on the
  context stating it. `auto` mode puts a reminder in the context; I could not
  check whether `acceptEdits`, `manual`, `bypassPermissions` or `dontAsk` do. If
  none do, the launch opens a window only from `auto` sessions.
- **Does the tmux target resolution differ with an attached client?** My probe
  ran on a server with no attached client. The untargeted `rename-window` could
  pick the attached client's current window instead, which is still the wrong
  window. The `-t "$TMUX_PANE"` form is correct in both cases.

## Reasoning

The System Model is one new skill, three stage behaviours inside it, one existing
reviewer skill and three harness tools. The rewrite answers these findings from
the first review: the Critical D3 label gate (D3 now uses the label-free Spec →
Plan test); the review-before-commit order (D9 plan steps 2-4, plus a Risk entry
for a busy `main`); the undefined branch and worktree names (D8 and D9 code step
1); the launch from `plan` mode (D7 step 3); the unclear squash-merge owner (D9
code step 5 and Out of scope); the Out of scope vs Files contradiction; the D7
step order; the unnamed `PushNotification` setting (D4 now names the flag
and setting and adds the tmux mark); and the global attribution of the test
rules (D9 code step 2). Two remain in part: the silent permission prompt (only
`plan` and an unknown mode are refused), and the Goal's claim that all gates are
global. New in this round: the tmux mark targets the wrong window, and the
`approved` status edit has no committing owner. None of these makes the approach
wrong, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the top finding is from a probe I ran, and the
permission-mode finding is checked against `claude --help`; the notification,
`ListAgents` name and slash-prompt behaviours remain unchecked.
**Recommendation:** Fix the four editorial rows (the `-t "$TMUX_PANE"` target,
the fallback command without a mode, the Goal wording and the reading-order row).
Ask the author to decide which permission modes may open a window and who commits
the spec's `approved` status. Run the three short probes under Needs
Investigation before the plan is written.
