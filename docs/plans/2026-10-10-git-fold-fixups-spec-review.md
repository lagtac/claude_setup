# Review: docs/plans/2026-10-10-git-fold-fixups-spec.md

**Status:** review of docs/plans/2026-10-10-git-fold-fixups-spec.md, 2026-10-10. Mixed: the script and the move are the right approach, but the spec's claim that D3 matches targets "as `git rebase --autosquash` does" is false (git picks the oldest match, not the nearest), and several contracts around the move and the exit codes need a decision. Answered in the spec the same day: both editorial findings fixed, and the user decided all nine design findings as the review's fixes suggest (ambiguous targets refused, exit 3, fold scope accepted in Risk, zitamu sentence edited).

## Spec Summary

The spec adds `plugins/my/bin/git-fold-fixups.py`, which checks whether a fixup is safe (`check <sha>`) and folds every waiting fixup on the current branch, refusing six unsafe cases. It moves the fourteen "One feature, four commits on `main`" steps from `global/CLAUDE.md` into the path-scoped rule `global/rules/docs-layout.md`, leaving a pointer under the old heading. `my:handoff` replaces its own prose fold with a call to the script.

## System Model

All caller and reference sweeps below were text-only (`grep -rn`); no symbol-reference tool was available.

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `git-fold-fixups.py check <sha>` | The "held by a worktree" decision (D2) | `git for-each-ref --contains … %(worktreepath)` | New (sibling dir `plugins/my/bin/` exists) |
| `git-fold-fixups.py` (fold) | Finding fixups and targets (D3), the six refusals (D4), the rebase and its post-checks (D5), exit codes | git ≥ 2.23, `@{upstream}`, the repo's `pre-rebase` hook | New |
| `test_git_fold_fixups.py` | Script behaviour proof | `unittest`, throwaway repos | New; pattern verified at `plugins/my/tests/test_md_table_filters.py:6-18` |
| `global/rules/docs-layout.md` | After D6: the fourteen steps, "No commit only changes a status", "Cite only commits on `main`" | Claude Code `paths:` loading | Existing `global/rules/docs-layout.md:1-5` |
| `global/CLAUDE.md` Git Workflow | After D6: the pointer text, the `docs:` bullet, "Before step 1" paragraph | docs-layout rule | Existing `global/CLAUDE.md:168-195` |
| `my:handoff` Plan step 8, Review step 8.3 | Whether to fold (finds the spec's fixups), the clean-`<base>` test, the project's pre-rebase check | The script | Existing `plugins/my/skills/handoff/SKILL.md:217-231`, `:337-345` |
| External pointers (grispy2, zitamu) | Their own text naming the heading and steps | `global/CLAUDE.md` heading | Existing `~/projects/grispy2-web-ext/CLAUDE.md:5`, `~/projects/zitamu/real-estate-webapp/CLAUDE.local.md:250-253, 301-328` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Session (steps 4, 8) → `check` | target sha; exit 0/1 + held branches on stderr | Script |
| Session (step 9) / Medium flow (`CLAUDE.md:61`) → fold | no args; exit 0/1/2 + one line | Script |
| `my:handoff` → fold | call after its own "fixups waiting" and clean tests; non-zero exit becomes `fold refused` signal | handoff decides whether, script decides safety |
| fold → git rebase | `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <base>`; git's own autosquash matching | git |
| `CLAUDE.md` pointer → `docs-layout.md` | Reader is sent to the steps; rule auto-loads on `docs/plans/` touch | `docs-layout.md` |
| `CLAUDE.md:78`, `:194` → steps | Step numbers 2, 6, 12, 13 | Not addressed by the spec |

## Grounding

- `spec §Risk` ("Subject matching … D3 picks the nearest older one, as `git rebase --autosquash` does") ↔ scratch experiment: commits `root`, `X`(a), `X`(b), `fixup! X`(c), then `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash HEAD~3`. Git folded `c` into the *older* `X` (with `a`). Git attaches a fixup to the first (oldest) match in the todo list, not the nearest.
- `spec §Risk` blast radius lists `global/CLAUDE.md` lines 61 and 168 to 195 only. It misses `global/CLAUDE.md:78` ("Git Workflow steps 12 and 13"), a step-number reference outside that range.
- `spec §Context` / `§Out of scope` say the zitamu pointer keeps working. The pointer does, but `zitamu/real-estate-webapp/CLAUDE.local.md:250-253` also states that the CLAUDE.md section "has the fourteen steps, the checks before a fixup or a rebase, and the rules for `docs:` commits and for citing commits". After D6 that sentence is false.
- All other checked references hold: `plugins/my/bin/md-expand-table.py` docstring/Usage style, `test_md_table_filters.py` subprocess + tempfile pattern, `handoff/README.md:50,110,138`, `SKILL.md:217-231, 337-345`, `CLAUDE.md:61`, ROADMAP rows G1/G2 (`ROADMAP.md:88-92`), the critique G1/G2 sections, git 2.43, and `for-each-ref --contains … %(worktreepath)` (verified: prints the worktree path for a branch checked out elsewhere, empty for others, matching `git branch --contains` `+` marks).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | D3 picks the nearest older target; git's autosquash picks the oldest matching commit in the todo list. With duplicate subjects and an older second target (A, X, Y, X, `fixup! A`, `fixup! X`), the rebase range covers both X commits and git folds into the first one. The D5 check `git diff <before> HEAD` still passes (same final tree), so the misfold is silent. The Risk claim "as git does" is false. | Scratch repo experiment (see Grounding); `spec §D3 ↔ §Risk` | Decision for the author: e.g. refuse when the rebase range holds two non-fixup commits with the same subject, or match git (oldest in range) and fix the Risk text. |
| Warning / High | design | Exit `1` means both "refused, nothing changed" (D4) and "rebase done, post-check failed, history rewritten, `<before>` printed" (D5). D7 reports every non-zero exit as `fold refused`, so handoff and the user cannot tell the state is now rewritten. | `spec §D1 ↔ §D5 ↔ §D7` | Give the post-check failure its own exit code (e.g. 3) and its own handoff signal. |
| Warning / High | design | D6 says `CLAUDE.md` keeps the heading with the quoted text "and nothing else under it", then says the `docs:` bullet and the "Before step 1" paragraph stay in `CLAUDE.md`. Both sit under that heading today (`global/CLAUDE.md:174`, `:194`). Where they go is not stated. | `spec §D6`; `global/CLAUDE.md:168-195` | State the placement (under the heading after the pointer, or a new heading). |
| Warning / High | design | Step-number references that stay in `CLAUDE.md` are not handled: `:78` sends a finishing session to "Git Workflow steps 12 and 13", and `:194` (kept by D6) cites steps 2, 6 and 13. Goal 3 ("every existing reference … still leads to the steps") is not shown for these, and a code-finishing session may never touch `docs/plans/`, so the rule may not be loaded at step 12. The pointer only says "read it before step 1". | `global/CLAUDE.md:78`, `:194`; `spec §Goal ↔ §D6 ↔ §Risk` | Add `:78` to D6 and the blast radius; make the pointer say "read it before any numbered step" or name the file in `:78`. |
| Warning / High | design | The script folds every waiting fixup on the branch, while `my:handoff` decides per spec. With parallel sessions, another feature's fixup whose target is held by its open worktree makes the script refuse the whole fold, even when this spec's fold alone would be safe (its target is newer than that worktree's base). D7's split "handoff decides whether, script decides safety" does not cover this. | `spec §D1 ↔ §D3 ↔ §D7`; `handoff/SKILL.md:217-227`; `CLAUDE.md:170` ("sessions often run in parallel") | Decision for the author: accept the stricter behaviour and say so in Risk, or let the fold take a target/limit. |
| Warning / High | design | Deleting the "Before every fixup" bullet drops guidance the script does not hold: "Always name the target by hash, never `--fixup HEAD`: a parallel session may have committed in between", and the reason a rebase breaks open branches. D6 says "The script holds them", which is only true for the `branch --contains` part. | `global/CLAUDE.md:191`; `spec §D6` | Keep the "by hash, never `--fixup HEAD`" sentence in steps 4 and 8. |
| Warning / Medium | design | A `squash!` or `amend!` commit in the rebase range makes the rebase wait for a commit-message editor. In the scratch repo with stdin not a terminal, it failed ("There was a problem with the editor 'nano'") and left a rebase in progress; the D5 abort would recover, but with a TTY it can hang. D4 does not refuse these subjects. | Scratch experiment (`squash! X` commit, `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash`, exit 1, rebase in progress) | Add a D4 refusal for `squash!`/`amend!` subjects in the range. |
| Warning / Medium | design | The zitamu sentence "It has the fourteen steps, the checks before a fixup or a rebase, and the rules … for citing commits" becomes false after D6; the spec scopes out zitamu edits on the ground that the heading stays. | `zitamu/real-estate-webapp/CLAUDE.local.md:250-253`; `spec §Out of scope` | Decision for the author: accept a stale sentence, or bring a one-line zitamu edit into scope. |
| Warning / Medium | design | Task 3 tests a project-level rule (`.claude/rules/canary.md`) while the real rule is user-level (`~/.claude/rules/docs-layout.md`). A pass does not prove the user-level rule loads on write. | `spec §Task 3 ↔ §Risk`; `~/.claude/rules/docs-layout.md` | Put the canary in the user-level rules (or a `--settings`-equivalent user dir) for the test, or state why project-level is equivalent. |
| Suggestion / High | editorial | D5 runs `git rebase --abort` on any non-zero exit. When the `pre-rebase` hook refuses (which §Out of scope says git runs), no rebase starts and `git rebase --abort` fails with "No rebase in progress?" (exit 128, verified). | `spec §D5 ↔ §Out of scope`; scratch experiment | Abort only when a rebase is in progress. |
| Suggestion / High | editorial | Task 3 says "`--add-dir` as the headless testing notes say" but those notes are not in "How to read this spec"; a cold reader cannot find them. | `spec §How to read this spec ↔ §Task 3` | List the notes file with its path, or state the flags inline. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Fit: one copy of fold logic replaces two prose copies | `global/CLAUDE.md:184,191-192`; `handoff/SKILL.md:217-227, 339-345` | Strong |
| Contracts: D2 reproduces the existing `+` rule exactly | Scratch: `for-each-ref --contains` shows `feat|<path>` exactly where `git branch --contains` shows `+ feat` | Strong |
| Failures: D4 refusals change nothing; dirty tree, in-progress ops, pushed targets and merges are all refused up front | `spec §D4` | Strong |
| Risk handling: rule-loading uncertainty has a test gate and a fallback before anything moves | `spec §Risk`, `§Task 3`, `§Task 4` | Moderate (see Task 3 finding) |
| Fit: follows sibling script and test patterns | `plugins/my/bin/md-expand-table.py:1-18`; `test_md_table_filters.py:6-18`; `README.md:94-100` | Strong |
| Trade-offs are real choices with reasons | `spec §Trade-offs` (handoff-only fails sessions that never hand off; split rule with same paths saves nothing) | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Grounding: autosquash matching claim is false; misfold is silent | Scratch experiment; `spec §Risk` | Medium |
| Contracts: exit 1 conflates "unchanged" and "rewritten" | `spec §D1, §D5, §D7` | Medium |
| Boundaries: D6 placement of retained text is contradictory | `spec §D6`; `global/CLAUDE.md:174,194` | Medium |
| Interactions: whole-branch fold vs per-spec handoff under parallel sessions | `spec §D3, §D7` | Medium |
| Grounding: blast radius misses `CLAUDE.md:78`; zitamu sentence goes stale | `global/CLAUDE.md:78`; zitamu `CLAUDE.local.md:250-253` | Medium |

## Not Applicable

None.

## Needs Investigation

- Whether a user-level rule in `~/.claude/rules/` with `paths:` loads when a session *writes* (not reads) a matching file. The spec's Task 3 is designed to answer this but uses a project-level fixture (see the Warning above). Resolve by running the canary as a user-level rule.

## Reasoning

The System Model is clear: the script owns safety, handoff owns the per-spec decision, and the rule file owns the steps. The approach is right and fits the repo. The findings are all at contract edges: the script's target matching differs from git's (shown by experiment), its exit code hides a rewritten state, its whole-branch scope does not match handoff's per-spec decision, and the move leaves step-number references and the retained bullets without a stated home. None of them breaks the approach, so the verdict is Mixed rather than Problematic; the D6 placement contradiction was rated Warning because both readings are recoverable and nothing is lost.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the two main findings were verified by experiment in a scratch repo, and the rest are direct `spec §` or `file:line` reads.
**Recommendation:** Decide the D3 matching rule, a distinct exit code for post-check failure, and the D6 placement and `CLAUDE.md:78` handling; then fix the two editorial items and re-run the spec review.
