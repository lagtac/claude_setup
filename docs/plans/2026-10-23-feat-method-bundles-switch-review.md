# Review: main..feat/method-bundles-switch

**Status:** review of main..feat/method-bundles-switch, 2026-10-23. Mixed: the approach is right, but `/kit:method` says the new method loads "in this session", and that is false in a session started by `claude-method`, which every `my:handoff` stage now is. Answered by the fix round: the skill, `README.md` and the plan's Risk section name the limit, and the plan counts three launch lines.

## Change Summary

The branch adds the skill `/kit:method <method|none|default>` in `plugins/kit/skills/method/SKILL.md`. For a method or `none`, it writes the method's keys into `.claude/settings.local.json` with `claude plugin enable|disable --scope local`. For `default`, it removes every method key and dependency key from that file with the Edit tool. It also changes the three `my:handoff` launch lines from `claude -n …` to `claude-method my -n …`. Finally, it documents both switches and the `~/bin/claude-method` symlink in `README.md` and the handoff `README.md`, and adds two Risk bullets to the plan.

## Plan Alignment

The branch matches Tasks 11 and 12 in substance. Task 10 has no artifact; its checks are manual. There are two deviations. Both are justified.

- `plugins/my/skills/handoff/SKILL.md:324`, `:344`, `:354`: the branch edits three launch lines, while the plan says four (plan Task 12 Steps 1–3, and the Files table at plan line 193). `main` has only three `claude -n <name>` lines (322, 342 and 352). A repo-wide text search found no fourth launch site. So the edit is complete, but Task 12 Step 1 ("prints `4`") and Step 3 ("`0` and `4`") could never pass as written. This is a Suggestion row below.
- `plugins/kit/skills/method/SKILL.md:60-65`: plan Task 11 Step 2.2 says "On the first failure, stop". The skill instead counts an exit 1 that says `is already enabled at local scope` or `is already disabled at local scope` as no change. The branch records this choice and its known limit in the plan's Risk section (plan lines 1180-1185). Justified and documented, so no Issues row.
- `plugins/kit/skills/method/SKILL.md:72-75`: the `default` step finds the file through `git rev-parse --show-toplevel`, with the current folder as a fallback. The plan names only `.claude/settings.local.json`. This is a refinement, not a deviation.
- `plugins/my/skills/handoff/README.md:97-99`: this file is not in Task 12's file list. The edit keeps it consistent with the skill. Harmless.
- The sentence that Task 12 Step 2 asks for is at `plugins/my/skills/handoff/SKILL.md:306-308`, word for word. The README text that Task 12 Step 5 asks for is at `README.md:106-124`.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | `/kit:method` says the new method loads "in this session" after `/reload-plugins`. In a session started by `claude-method`, the `--settings` flag outranks `.claude/settings.local.json`, so the switch does nothing there. Task 12 makes every `my:handoff` stage such a session. The skill would report a switch that did not happen, and the start check stays silent because it reads only files. | `plugins/kit/skills/method/SKILL.md:82-84` and `README.md:115-118` make the claim. `plugins/kit/bin/claude-method:98-108` puts every method key and dependency key into the JSON, and `:163` passes it as `--settings`. `plugins/my/skills/handoff/SKILL.md:324`, `:344` and `:354` launch every stage that way. Claude Code documents this order of scopes: command-line arguments, then local, then project, then user. The result holds whether `enabledPlugins` merges per key or as one object, because the flag names every key. Not run: I could not start `claude` to watch it. The plan's Risk bullet at plan lines 1136-1138 covers only the start check, not this. | Needs a decision. The simplest fix: state the limit in the skill's step 3, in `README.md`, and in Risk. For example: "a session started by `claude-method` keeps its method; the switch applies to new plain `claude` sessions in the folder." To detect such a launch inside kit, the skill would have to read the process arguments, and that pushes against the rule that kit stays neutral to the harness. |
| Suggestion / High | The plan still says Task 12 edits "four launch lines". Its Step 1 check expects a count of `4`, but `main` has three lines. | Plan lines 193 and 1059-1068. `git show main:plugins/my/skills/handoff/SKILL.md` has `claude -n` only at lines 322, 342 and 352. | Change "four" to "three" in the plan, with one clause on why: the spec counted the lines before rows 33, 37 and 56 merged. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| One reader of the method list: the skill takes every key from `claude-method` and spells out no key of its own, as the spec requires | `plugins/kit/skills/method/SKILL.md:22-32`, `:53` | Strong |
| `default` removes dependency keys as well as method keys, as D16 requires | `plugins/kit/skills/method/SKILL.md:30-32`, `:76-78` | Strong |
| The skill follows its sibling `kit:setup`: the same intro on `claude-method`, the same usage rule, the same one-command-per-call rule | `plugins/kit/skills/setup/SKILL.md:22-32`, `:49-58` against `plugins/kit/skills/method/SKILL.md:22-49` | Strong |
| `MY_AUTORUN=<slug>` still reaches `claude`, because `os.execvp` keeps the environment, so the push guard still turns on | `plugins/kit/bin/claude-method:163`; `plugins/my/skills/handoff/SKILL.md:354` | Strong |
| A copied `--plugin-dir plugins/my` does not load `my` twice: `claude-method` turns `my@claude-setup` off for it | `plugins/kit/bin/claude-method:157-161`; `plugins/my/skills/handoff/SKILL.md:306-308` | Strong |
| No launch site is left behind. A text search over `plugins/`, `global/`, `README.md` and `CLAUDE.md` for `tmux new-window`, `claude -n` and `exec claude` finds only the edited lines. This was a text search: I have no symbol tool, and the branch changes only Markdown. | `plugins/my/skills/handoff/SKILL.md:343`, `:353`; `plugins/my/skills/handoff/README.md:97` | Moderate |
| `disable-model-invocation: true` makes only the user able to switch, as the spec says | `plugins/kit/skills/method/SKILL.md:10` | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The skill and the README say the switch works "in this session", but a session started by `claude-method` keeps its method | `plugins/kit/skills/method/SKILL.md:82-84`; `README.md:115-118`; `plugins/kit/bin/claude-method:163` | Medium |
| The plan's Task 12 checks expect a count of 4 that `main` never had | Plan lines 1061-1068 | Low |

## Not Applicable

None.

## Needs Investigation

- **Where `claude plugin --scope local` writes, when the session's folder is a subfolder or a git worktree.** The skill says the CLI writes `.claude/settings.local.json` "at the repo root" (`plugins/kit/skills/method/SKILL.md:19-20`). The `default` step relies on that to find the file through `git rev-parse --show-toplevel` (`:72-73`). The plan's headless check ran from the fixture's root only. If the CLI writes in the current folder instead, `default` would read a different file and say that no local keys are set. To resolve it, run `claude plugin enable <key> --scope local` from a subfolder and from a worktree of a fixture repo, and see which file changes. I could not run `claude` in this review.

## Reasoning

The skill and the launch change both use only the channels the spec names. They follow the sibling `kit:setup` closely, keep the push guard working, and leave no launch site behind. So the approach is sound. The one real problem comes from the two tasks together. Task 12 starts every stage with `--settings`, and Task 11's last step promises a switch in the current session that `--settings` blocks. That is a wrong claim to the user, not a wrong design, so it is a Warning. The plan's wrong line count is a record fix only.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. The main finding rests on Claude Code's documented order of settings scopes, which I could not test here.
**Recommendation:** Before the merge, add one sentence to step 3 of `plugins/kit/skills/method/SKILL.md`, to `README.md` and to the plan's Risk section. It should say that a session started by `claude-method` keeps its method until it ends. Also correct "four" to "three" launch lines in Task 12.
