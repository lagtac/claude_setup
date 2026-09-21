# Review: docs/plans/2026-09-21-handoff-spec.md

**Status:** review of docs/plans/2026-09-21-handoff-spec.md, 2026-09-21.
Mixed: the tmux launch checks out against the real CLI, but the D3 gate
between the plan and code stages depends on a `design` label that
`my:soundness-review` never produces, so the gate can never fire.

## Spec Summary

The spec adds one skill, `my:handoff <stage> <doc>`. A session that finishes a
stage of the spec, plan and code cycle uses it to open the next stage as a new
named top-level `claude` session in a background tmux window. Each stage session
checks its input document, runs its stage, stops at named gates and tells the
user with `PushNotification`. The plan session starts the code session by itself
when the plan is "clean" (D3). The squash-merge waits for the user.

## System Model

All caller and name sweeps in this review used plain text search (`grep`) and
`strings`-style greps of the `claude` binary. No symbol-reference tool was
available.

| Component | Owns | Depends on | New / existing (verified at) |
| --- | --- | --- | --- |
| `my:handoff` skill, launch part (D7) | The window/session name `<stage>-<slug>`, the duplicate check, the flag collection, the `tmux new-window` command | tmux, `$TMUX`, `$CLAUDE_PID` + `ps`, `ListAgents`, `claude -n/--plugin-dir/--permission-mode` | New `my-plugin/skills/handoff/SKILL.md` (not found, as expected) |
| `my:handoff` skill, start checks (D8) | The go/no-go decision before a stage writes anything | The document's `**Status:**` line, the plans directory, git worktrees and branches | New |
| Plan stage session (D9) | Writing the plan, running the plan review, the docs commit, the D3 "clean" decision, launching the code stage | `superpowers:writing-plans`, `my:soundness-review`, the project's docs and pre-rebase rules | New (behaviour inside the new skill) |
| Code stage session (D9) | The worktree, implementation, end-of-branch reviews, the fix round, the "ready to squash-merge" notice | `git worktree add`, `superpowers:executing-plans`, `superpowers:systematic-debugging`, the project's review rules | New (behaviour inside the new skill) |
| Spec stage session (user's) | The spec, its approval, the "Hand off the plan?" offer | A new line in `GLOBAL-CLAUDE.md` | Existing flow `GLOBAL-CLAUDE.md:40-47` |
| `my:soundness-review` | The plan review file and its findings | A clean tree for plan-review mode | Existing `my-plugin/skills/soundness-review/SKILL.md:96-113` |
| `PushNotification` tool | Delivery of a notification to the user | Feature flag and `agentPushNotifEnabled` setting | Existing in the `claude` 2.1.278 binary (strings only) |
| `ListAgents` tool | The list of local sessions | Local session messaging | Existing in the `claude` 2.1.278 binary (strings only) |
| Status line values | `draft`, `approved`, and the others | — | Existing `GLOBAL-rules/docs-layout.md:84-102` |

| From → To | What passes | Owner of what passes |
| --- | --- | --- |
| Spec session → launch | The call `plan <spec path>` after approval | Spec session |
| Launch → tmux → new session | The command line: name, `--plugin-dir` flags, permission mode, first prompt `/my:handoff <stage> <doc>` | Launch |
| Launch → `ListAgents` | Name lookup for the duplicate check | `ListAgents` (the harness) |
| New session → start checks | The document path; its status line; the existing plan, worktree or branch | Repo (the files and git) |
| Plan stage → `my:soundness-review` | The plan path; back comes a review file with findings | `my:soundness-review` |
| Plan stage → D3 gate | Review findings labelled `design` or `editorial`, the false-premise result, the pre-rebase check result | Undefined for the labels (see Issues) |
| Plan stage → launch | The call `code <plan path>` | Plan stage |
| D8 code check → D9 code step 1 | The name of the worktree and branch "for that plan" | Undefined (see Issues) |
| Any stage → user | `PushNotification` text `<name>: <action>` | Stage session |
| User → stage window | Answers to gates, the yes for the squash-merge | User |

## Grounding

- `spec §Goal` ("the gates the global rules already define") and `spec §D3`
  (rejected option: "it adds a gate the global rules do not define") ↔
  `GLOBAL-CLAUDE.md`: no rule on pre-rebase checks exists there (text search for
  `rebase` finds nothing). The pre-rebase checks come from one project's
  `CLAUDE.local.md` (zitamu), not the global rules.
- `spec §D9` Code stage step 2 ("Under the global rules: tests per commit,
  reviews and e2e once at the end of the branch") ↔ `GLOBAL-CLAUDE.md`: no
  match for `e2e`, `per commit` or `tests per`. The global file has "review once
  at the end of the branch" and "one fix round per review", but the e2e and
  per-commit test rules are the zitamu project's.
- `spec §D9` Plan stage step 2-3 ("Fix `editorial` findings") and `spec §D3`
  ("the plan review has no `design` finding") ↔
  `my-plugin/skills/soundness-review/code-reviewer-prompt.md:88-92`: the
  soundness-review output table has no class column. `editorial` and `design`
  are `my:spec-review` labels only.
- `spec §Dependencies` lists `PushNotification` as a plain tool ↔ the 2.1.278
  binary gates it behind a feature flag and an `agentPushNotifEnabled` setting,
  both defaulting to false; `~/.claude.json` and `~/.claude/settings.json` have
  no `agentPushNotifEnabled` key (only `pushNotifUpsellSeenCount`).
- Holds: `claude --version` is 2.1.278; `claude --help` lists `-n, --name`,
  `--permission-mode` and `--plugin-dir`; `$CLAUDE_PID` is set and
  `ps -o args= -p "$CLAUDE_PID"` returns
  `claude --plugin-dir /home/dchris/projects/claude-setup/my-plugin`; the
  binary's `ListAgents` description covers "other local Claude sessions on this
  machine"; every path in "How to read this spec" exists except the review and
  plan, which are marked as future; the test precedent's "How tests run"
  section exists at `docs/plans/2026-09-16-spec-review-skill.md:22-33`.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Critical / High | design | The D3 auto-launch gate asks whether the plan review has a `design` finding, and D9 step 3 fixes `editorial` findings. The named reviewer, `my:soundness-review`, labels neither. The first D3 condition is always true, so the plan session always launches the code session unless one of the other two conditions fails. | `spec §D3 ↔ §D9`; `my-plugin/skills/soundness-review/code-reviewer-prompt.md:88-92` | Decision for the author: add the class label to soundness-review's plan mode (a change to another skill, now in scope), or define "clean" on what soundness-review does output (e.g. no Critical/Warning row, or Verdict `Sound`). |
| Warning / High | design | D9 runs the plan review (step 2) before committing (step 3). `my:soundness-review` reviews the plan document only when the working tree is clean. It includes untracked files in its payload, so an uncommitted plan makes it do a diff review against the plan instead. On a shared `main` checkout, other sessions' uncommitted files end up in that payload too. | `spec §D9` Plan stage; `my-plugin/skills/soundness-review/SKILL.md:72-84, 96-113` | Decision for the author: commit the plan first and add the review in a second commit, or say how the stage gets a clean tree. |
| Warning / High | design | Every gate reaches the user only through `PushNotification` (D4). That tool is behind a feature flag and an `agentPushNotifEnabled` setting, both off by default, and this user's config does not set the setting. If it is off, every gate is silent and a stopped stage looks like a running one. Neither Dependencies nor Risk mentions this. | `spec §D4`, `§Dependencies`, `§Risk`; `~/.claude.json` (no `agentPushNotifEnabled` key) | Name the setting in Dependencies. Give a fallback when the tool is unavailable (terminal bell, or `SendMessage` to the spec session), or make D8 check that the tool is available. |
| Warning / High | design | D8 says the code stage fails when "a worktree or branch for that plan" exists. No section names that worktree or branch. D7 names only the session, and D9 code step 1 has no naming rule, so the check has no defined input. | `spec §D8 ↔ §D7, §D9` | Give a naming rule (e.g. branch and worktree `<slug>`) and use it in both D8 and D9. |
| Warning / High | design | Risk says "D7 passes the launching session's mode" as the fix for a window stuck on a permission prompt. D7 step 4 drops the flag when the session cannot tell its mode, and a session in the default mode has no reminder that states it. That is exactly the stuck case. Detection relies on `ListAgents` showing `waiting`, but D10 forbids polling, so the stuck window stays hidden. | `spec §Risk ↔ §D7 ↔ §D10` | Decision for the author: pass an explicit mode for each stage, or accept the risk and say how the user finds out. |
| Warning / Medium | design | D7 copies the launching session's mode as it is. If the spec session is in `plan` mode (one of the `--permission-mode` choices), the plan session starts in plan mode and cannot write the plan or commit. | `spec §D7` step 4; `claude --help` (`--permission-mode` choices include `plan`) | Map `plan` to a writable mode, or refuse to launch from plan mode. |
| Warning / Medium | design | The skill's own gates are presented as ones "the global rules already define". D3's pre-rebase checks and D9's code gates (test failure after debugging, change outside scope), plus the "tests per commit, e2e at end" rule, come from the zitamu project or from this spec, not from `GLOBAL-CLAUDE.md`. In a project without pre-rebase rules that D3 condition passes by default. D6 says the skill carries only what is the same in every project. | `spec §Goal ↔ §D3 ↔ §D6 ↔ §D9`; `GLOBAL-CLAUDE.md` (no `rebase`, `e2e` or per-commit test rule) | Decision for the author: either the skill owns these gates and says so, or it defers to the project's rules and D3 says what happens when a project defines none. |
| Warning / Medium | design | Who carries out the squash-merge is unclear. Out of scope says "The squash-merge and the push. Both stay with the user". D9 says the merge and the `done` marks "wait for the user's yes, typed in that window", which suggests the code session does the merge after the yes. | `spec §Out of scope ↔ §D9` Code stage step 4 | Say whether the code session merges after the yes or the user merges by hand. |
| Warning / High | editorial | Out of scope and "How to read this spec" both say the spec does not change the global rules. The Files table changes `GLOBAL-CLAUDE.md`, adding a line to the Spec → Plan flow. | `spec §Out of scope ↔ §Files`; `spec §How to read this spec` (Global instructions row) | Say that the spec adds one offer line and changes no existing rule. |
| Suggestion / High | editorial | D7 step 1 prints "the full command from step 5" before steps 2 to 4 have built the name and flags. That command is also a `tmux new-window` command, which a user without tmux cannot run. | `spec §D7` | Build the name and flags first, then print the inner `claude -n ...` command when `$TMUX` is empty. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Grounding of the launch mechanism | `-n`, `--permission-mode` and `--plugin-dir` are in `claude --help` for 2.1.278; `ps -o args= -p "$CLAUDE_PID"` returns the `--plugin-dir` flag from the alias, so D7 step 4 works as described | Strong |
| Fit: rejected options are real | D1 (manual start, standing worker), D2 (four sessions, two sessions), D4 (relay through the spec session) and D5 (three skills, launcher script) each give a concrete reason tied to this design | Strong |
| Boundaries | One skill owns launch, checks and stage rules. D6 leaves project rules to each project's `CLAUDE.md`, which top-level sessions read | Moderate |
| Fit: no existing solution | No skill under `my-plugin/skills/` launches sessions; `briefing` is for non-technical write-ups (`my-plugin/skills/briefing/SKILL.md:1-13`) | Moderate |
| Spec rules | "How to read this spec" comes first. Risk, Dependencies and Trade-offs sections are present. No UI, so no Visual Language section is needed | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| Contracts and flow | The D3 gate reads a label the reviewer does not emit; D8's branch/worktree name is undefined (`spec §D3`, `§D8`; `code-reviewer-prompt.md:88-92`) | High |
| Failures and interactions | Silent failures: notifications may be off, a stuck permission prompt goes unseen, the plan review runs in the wrong mode on a dirty tree (`spec §D4`, `§Risk`, `§D9`) | High |
| Grounding | Gates and test rules credited to the global rules come from one project (`GLOBAL-CLAUDE.md`, no match) | Medium |
| Self-containment | A plan writer cannot decide what "clean" means, who merges, or what the code-stage check searches for without asking the author | Medium |

## Not Applicable

None.

## Needs Investigation

- **Is `PushNotification` available to this user at all?** The binary gates it
  behind a remote feature flag (`tengu_kairos_push_notifications`) as well as
  the local setting. The flag cannot be read locally. It matters because D4 is
  the only way a gate reaches the user. To resolve it, call `PushNotification`
  once from a throwaway session in tmux and see whether the notification
  arrives.
- **Does `PushNotification` skip the notification when the user is at that
  terminal, and does it work inside a background tmux window?** I could not
  check the claim in D4 without running the tool. To resolve it, run the same
  test as above with the window in front and in the background.
- **Does `ListAgents` report a session by its `-n` name?** D7 step 3 depends on
  this. The binary confirms that `ListAgents` lists local sessions, but not
  which name it shows. To resolve it, start `claude -n probe` in a tmux window
  and call `ListAgents` from another session.

## Reasoning

The System Model is simple: one new skill, two existing skills it calls, and
three harness tools. Every launch-side reference holds against the real CLI.
The weak points are the connections into things the skill does not own. The D3
gate reads a label that `my:soundness-review` does not produce. The review runs
before the commit, so it runs in the wrong mode. The only way to tell the user
may be switched off, and the code-stage check has no defined input. None of
these makes the approach wrong, but the automatic plan-to-code launch (D3)
depends on all of them, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — I checked the Critical and top Warning findings
against the soundness-review skill, `GLOBAL-CLAUDE.md`, `claude --help` and the
user's config. Only the notification delivery details remain unchecked.
**Recommendation:** Ask the author to decide what "clean" means for D3 and how
the plan review gets a clean tree. Ask for a fallback for `PushNotification`
and a naming rule for the code-stage branch and worktree. Fix the
out-of-scope wording and the D7 step order as editorial changes. Do this before
the plan is written.
