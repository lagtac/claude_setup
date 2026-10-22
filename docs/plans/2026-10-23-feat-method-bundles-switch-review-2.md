# Review: main..feat/method-bundles-switch

**Status:** review of main..feat/method-bundles-switch, 2026-10-23. Mixed: the fix round resolves both findings of the earlier review, but in a git worktree `/kit:method <m>` writes the main checkout's `.claude/settings.local.json` while `/kit:method default` reads the worktree's, so `default` cannot undo a switch made there. Answered in the plan's Risk section as a known limit, under the one-fix-round rule.

## Change Summary

The branch adds the skill `/kit:method <method|none|default>` in `plugins/kit/skills/method/SKILL.md`. For a method or `none`, it writes the keys from `claude-method --json` with `claude plugin disable|enable --scope local`: first the off keys, then the dependencies, then the method. For `default`, it removes the method keys and dependency keys from `.claude/settings.local.json` with the Edit tool. The three `my:handoff` launch lines now start `claude-method my -n …`. `README.md`, the handoff `README.md` and the plan's Risk section document both switches, the `claude-method` limit and the `~/bin/claude-method` symlink. The branch also adds the earlier review report.

## Plan Alignment

The branch matches Tasks 11 and 12. Task 10 has no artifact; its Step 3 symlink exists (`~/bin/claude-method` points at `plugins/kit/bin/claude-method`).

The earlier report's findings, checked one by one:

- **Warning, "loads in this session" is false under `claude-method`: resolved.** The skill now adds a line that a session started by `claude-method` keeps its method (`plugins/kit/skills/method/SKILL.md:88-92`). `README.md:115-118` says the same, naming the `my:handoff` stages. The plan's Risk section names the limit (plan lines 1191-1195).
- **Suggestion, "four launch lines": resolved.** The plan now says three, with the reason (plan lines 193, 1059-1069).
- **Needs Investigation, where `claude plugin --scope local` writes from a subfolder or a worktree.** The subfolder half is resolved: the caller's real run shows it writes at the repo root, which matches `git rev-parse --show-toplevel` in step 2.2. The worktree half is now answered by my own fixture runs, and the answer is a new Warning below.

Deviations from the plan's text, all documented:

- `plugins/kit/skills/method/SKILL.md:58-64`: the plan's Task 11 Step 2.2 does not fix an order. The skill runs `disable` first, then dependency `enable`, then method `enable`. The Risk section records why (plan lines 1196-1199). Justified. I also checked that the order of the `false` keys among themselves does not matter: in a fixture, `claude plugin disable superpowers@synced --scope local` succeeded while `my@claude-setup` was still on.
- `plugins/kit/skills/method/SKILL.md:66-71`: an exit 1 that says "already enabled/disabled at local scope" counts as no change, not as the failure that the plan's "On the first failure, stop" would mean. Named in Risk (plan lines 1181-1186). Not a finding.
- `plugins/kit/skills/method/SKILL.md:78-79`: the `default` step finds the file through `git rev-parse --show-toplevel`. The plan names only `.claude/settings.local.json`. This choice is the source of the Warning below.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | In a git worktree, `/kit:method <m>` and `/kit:method default` work on different files. `claude plugin --scope local` run from a worktree writes the **main checkout's** `.claude/settings.local.json`. A session in the worktree loads its plugins from that file too. But step 2.2 finds `<root>` with `git rev-parse --show-toplevel`, which returns the **worktree** path. So `default` reads a file that does not exist there, says "no local keys are set", and leaves the keys on. Editing the worktree's own file would not help either: a worktree-local `tutor@claude-setup: false` did not stop `tutor` from loading. A second effect: the skill says it switches "every session in the folder", but from a worktree it also switches the main checkout and every sibling worktree. The Risk section does not name either effect. | `plugins/kit/skills/method/SKILL.md:78-81` (the root lookup), `:17-20` ("every session in the folder"; "writes that file at the repo root"). My fixture runs, in a scratch git repo with one worktree: `claude plugin enable superpowers@synced --scope local` from the worktree changed `<main>/.claude/settings.local.json` and created no `<worktree>/.claude/`. A `claude -p` init event from the worktree listed `tutor` when only the main checkout's local file turned it on. It still listed `tutor` after I added `<worktree>/.claude/settings.local.json` with `tutor@claude-setup: false`. `git rev-parse --show-toplevel` in the worktree printed the worktree path. | In step 2.2, find the main checkout's root as `plugins/my/skills/handoff/SKILL.md:313` already does: `git rev-parse --path-format=absolute --git-common-dir`, then drop the trailing `/.git`. Do it as two steps, because the skill forbids shell variables, so `dirname "$(…)"` does not fit its rules. Say in the intro (`:17-20`) that in a worktree the switch applies to the main checkout and all its worktrees. Add one Risk bullet. The kit skill must not name `my:handoff`: `test_kit_cites_no_method` forbids a `my:<name>` reference in kit. So write the command out instead of pointing at that skill. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The fix round answers the earlier Warning in the skill, the README and Risk, with the reason (`--settings` outranks the local file) | `plugins/kit/skills/method/SKILL.md:88-92`; `README.md:115-118`; plan lines 1191-1195 | Strong |
| The disable-first order means a failure partway leaves no method on rather than two. Dependencies go before the method, because `claude plugin enable` refuses a method while a dependency is off. The caller's headless run confirms the order and the end state | `plugins/kit/skills/method/SKILL.md:58-64`; `plugins/kit/bin/claude-method:154` (`sort_keys=True`) | Strong |
| The order of the `false` keys among themselves does not matter: `claude plugin disable` does not check what depends on the plugin | My fixture run: a dependency disable succeeded with `my@claude-setup` on | Moderate |
| One reader of the method list: the skill takes every key from `claude-method` and lists none of its own, as the spec requires | `plugins/kit/skills/method/SKILL.md:22-32`, `:53-55` | Strong |
| The skill follows its sibling `kit:setup`: the same intro on `claude-method`, the same usage rule, the same one-command-per-call rule | `plugins/kit/skills/setup/SKILL.md:21-32`, `:44-58` against `plugins/kit/skills/method/SKILL.md:22-49` | Strong |
| No launch site is left behind. A text search over `plugins/`, `global/`, `README.md` and `CLAUDE.md` for `claude -n`, `claude --resume` and `exec claude` finds no other launch line. This was a text search: I have no symbol tool, and the branch changes only Markdown | `plugins/my/skills/handoff/SKILL.md:324`, `:344`, `:354` | Moderate |
| Kit stays neutral: `test_neutral_core.py` (20 tests) and `test_skill_placeholders.py` pass on the branch | `plugins/kit/tests/` | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| In a worktree, `default` reads the worktree's file while the keys live in the main checkout's file, so it reports no keys and changes nothing | `plugins/kit/skills/method/SKILL.md:78-81` | Medium |
| In a worktree, the switch reaches the main checkout and every sibling worktree, which the skill does not say | `plugins/kit/skills/method/SKILL.md:17-20` | Low |

## Not Applicable

None.

## Reasoning

Both findings of the earlier review are fixed, and the new ordering in step 1 is right and backed by a real run. The approach (`claude plugin --scope local` to set keys, the Edit tool to remove them, `claude-method` as the only key source) stays sound. The one remaining problem is a wrong root lookup in the `default` step for worktrees, which I confirmed with fixture runs. That is a targeted fix of one step and one sentence, not a redesign, so it is a Warning.

## Verdict

**Assessment:** Mixed
**Confidence:** High. The worktree behaviour comes from real `claude plugin` and `claude -p` runs in a fixture, not from documentation.
**Recommendation:** Before the merge, change step 2.2 of `plugins/kit/skills/method/SKILL.md` to find the root from `git rev-parse --path-format=absolute --git-common-dir`. Say in the skill's intro that in a worktree the switch reaches the main checkout, and add that to the plan's Risk section. Then rerun the `default` check once from a worktree of a fixture repo.
