# Review: docs/plans/2026-10-16-design-system-skill.md

**Status:** review of docs/plans/2026-10-16-design-system-skill.md, 2026-10-16. Mixed: the approach is sound and almost every reference holds, but the empty-match check of Decision 7 cannot pass its own red test (`\b` is not caught), and several rehearsal checks cannot fail for the right reason. The plan stage fixed every finding in the plan before its commit, 2026-10-16.

## Change Summary

The plan builds row 64 in seven tasks. Task 1 adds `plugins/my/bin/ds-count.py` with 24 subprocess tests. Task 2 adds the `my:design-system` skill (`audit`, `refresh`, `sync`) and a kit guard name. Tasks 3 to 5 edit prompt text: the method, step 13 of `docs-layout.md`, the shared-doc list of `my:handoff`, criterion 6 of the spec reviewer, and `README.md`. Task 6 runs headless `claude -p` rehearsals on fixture repos and a zitamu clone. Task 7 runs `sync` on the real zitamu artifact after the user says yes.

## Grounding

The sweep was text-only: `grep` through Bash. No symbol-reference tool was available. The change removes and renames nothing, so the sweep checked only the shared-doc list and the names the plan adds.

These claims hold:

- The shared-doc search in "File map" prints exactly three lines: `plugins/my/skills/handoff/README.md:378`, `plugins/my/skills/handoff/SKILL.md:250` and `:720`.
- `DOCS_PATHS` already covers `docs/`: `plugins/my/bin/handoff-state.py:152`.
- `MY_NAMES` sits at `plugins/kit/tests/test_neutral_core.py:28-30`. Kit has no `design-system` or `ds-count` text (`grep -rn` exits 1). `MY_BARE` (line 32) also picks up the bare name `design-system`, so the guard is a little stricter than Decision 13 says. Nothing in kit trips it today.
- The test counts match: 203 `my` tests and 40 `kit` tests pass now.
- The lint counts match: 1 for `global/methods/my.md`, and 0 for `docs-layout.md`, both handoff files, `spec-reviewer-prompt.md` and `README.md`.
- These line numbers hold: `global/methods/my.md:57` (the "New feature" row), `:84` (step 1), `:111-139` (UI Design), `global/rules/docs-layout.md:167` (step 13) and `spec-reviewer-prompt.md:69` (row 59's bullet).
- Row 59's commit `7e938b9` is on `main`. Every `.vue` file is tracked: 65 in all, and 42 after excluding `web/components/Z*.vue` (Risk 5).
- `git ls-files` exits 0 when nothing matches. `':(glob)web/**/*.vue'` matches `web/a.vue` at depth 0. Both were checked on a scratch repo, so Decision 2 and the fixture counts `3/2` and `4/3` are right.
- The `Task: <N>` trailer convention is in `plugins/my/skills/handoff/SKILL.md:865-867`.

These claims do not hold:

- Decision 7 says `re.compile(r).search("") is not None` refuses `\b`. It does not. `re.search(r"\b", "")` returns `None`, yet `\b` matches 6 times in `"<input> hello world"`. The same goes for `\B` and lookaheads. Review Focus 1's other example, `<input\s*`, cannot match the empty string at all. (Python probe, run in this review.)
- Task 7 Step 1: "HEAD~5 … so the staleness command prints something" is false. In `~/projects/zitamu/real-estate-webapp`, `git log HEAD~5..HEAD -- web/assets/css/tokens.css web/components` prints 0 lines. The last commit touching `web/assets/css/tokens.css` or `web/components/Z*.vue` is `7bada58`, 59 commits back.
- Risk 2: "This run goes first" contradicts `ROADMAP.md:37-44`. There row 64 comes after 61 and 45, and it edits `my:handoff` only after step 1's fixes (33, 37 and 56, at `ROADMAP.md:27-29`). All five rows are still 💭.
- Task 5's README line numbers (127, and the `status-scan.py` sentence ending at 188) come from the main checkout's uncommitted state. On `main`, the sentence sits at lines 179-182. The text anchors are clear, so this only matters for the merge (see Issues).

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | Decision 7's check (`search("") is not None`) does not refuse `\b`. So `test_empty_match_regex_refused`, which uses `"\\b"` and expects exit 1, stays red against the implementation the plan specifies. Task 1 Step 4 cannot pass as written, and the executor has to invent a different check. Review Focus 1's example `<input\s*` is not an empty-match regex at all. | Plan, Decisions 7 and Review Focus 1, test snippet in Task 1 Step 1. Probe: `re.compile(r"\b").search("")` returns `None`, yet `\b` matches 6 times in `"<input> hello world"`. | Refuse a regex when counting finds any zero-width match (`m.start() == m.end()`), with the line number. Decision 9 already writes only after every line is counted, so the file stays unchanged. Keep `x*` as a second case in the test. Replace the `<input\s*` example with `x*` or `(?=<input)`. |
| Warning / High | Task 7 Step 1 sets `synced from <HEAD~5>`, but no commit in `HEAD~5..HEAD` touches the tokens file or the `Z*` components. The staleness command already prints nothing, so Step 3's "prints nothing afterwards" proves nothing. | `~/projects/zitamu/real-estate-webapp`: 0 lines for `HEAD~5..HEAD`. The last hit for `web/assets/css/tokens.css 'web/components/Z*.vue'` is `7bada58`, 59 commits back. | Use the parent of the last commit that matches the exact Sources pathspecs: `$(git log -1 --format=%H -- <tokens> 'web/components/Z*.vue')~1`. Check that the command prints at least one line before the gate. |
| Warning / High | Risk 2 reverses the order recorded in the roadmap ("This run goes first"). It does so without the user's decision and without a `ROADMAP.md` edit. It also leaves out rows 33, 37 and 56, which edit `plugins/my/skills/handoff/SKILL.md`, the file Task 4 edits by line number. | `ROADMAP.md:27-44` (64 after 45 and 61, and after step 1's `my:handoff` fixes). All are 💭 at `ROADMAP.md:287,301,306,338,375`. `global/rules/docs-layout.md` says the order is a decision and is not guessed. | Needs the user's decision. Either record the user's yes to start 64 first, and edit the order in the same docs commit, or list rows 33/37/56, 45 and 61 under **Dependencies**. Name rows 33, 37 and 56 in Risk 2 either way. |
| Warning / Medium | The step-13 wiring, the main integration this plan adds, is never rehearsed on its positive path. Task 6 Step 4 runs only the "no inventory" case. Its expectation (no `ds-count.py` call, no `my:design-system` call) would also hold if the new step-13 sentence were missing, so it cannot fail for the right reason. Also, `docs-layout.md` opens with "Applies only in projects whose `CLAUDE.md` imports …", and the fixtures have no such import. | `global/rules/docs-layout.md:3,167`. Plan, Task 6 Step 4. | Add a run on fixture A: it has the inventory, plus a spec with a Visual Language section. Expect a `refresh <spec>` call, and the inventory edits inside the `done` commit. In both step-13 prompts, say to apply the file even without the import. |
| Warning / Medium | The skill's commit rule, `git commit -m … -- <paths>`, ignores the "Parallel runs" locked form. Task 4 makes `docs/DESIGN-SYSTEM.md` a shared doc for exactly those projects. Yet `audit`, a by-hand `refresh` and `sync` would commit in the main checkout without lock `main`, and without the `git diff --quiet HEAD -- <file>` check. The sibling skill `my:architect` spells out both forms. | Plan, Task 2 Step 2 item 7. `plugins/my/skills/architect/SKILL.md:246-254`. `plugins/my/skills/handoff/SKILL.md:719-724`. | Add the same two-form rule as `my:architect`: under "Parallel runs", write the message to a file and run `locked-commit.py -F <file> <paths>`, after the shared-doc check. |
| Warning / Medium | Task 6 Step 2 expects Sources to say `none yet (row <N>)`. But the prompt says "Propose rows, add none", so no row number exists. Whatever the model writes, a literal `<N>`, a guess or a bare `none yet`, the check is ill-defined. The same gap is in the skill: `audit` writes Sources (step 1) before the user decides on rows (step 5). | Plan, Task 6 Steps 1-2 and Task 2 Step 2 item 4. Spec "The inventory" part 1. | State what Sources says before the starting row exists, for example `none yet (row not added yet)`, and have `audit` update it once the row is added. Or let the rehearsal add the row and check the number. |
| Warning / Medium | Task 6 Step 3's "the input pattern at 0 has lost its line" depends on which globs and excludes the audit wrote. `components/AppField.vue` will hold an `<input>`. If the audit's text-field line covers `components/` without excluding it, the count stays at 1. `refresh` has no step that adds an exclude, and the skill text gives no rule that a `hand-built` line excludes the components folder. | Plan, Task 6 Steps 1 and 3, and Task 2 Step 2 item 3. Spec, key table (`exclude` "so a count can reach zero"). | In the template rules, require each `hand-built` line to exclude the Sources components pathspec. Check that in Task 6 Step 1's expected results. |
| Warning / Medium | Task 6 Step 5's Spec 2 (`AppButton` variant `huge`) expects an `editorial` finding. Under the new bullet, `editorial` means "a wrong name for something that exists", and `design` means "the part is new". A `huge` variant that fixture A never had reads as new, so a correct `design` result would be recorded as a failure. | Plan, Task 4 Step 4, third sub-bullet, and Task 6 Step 5. | Give `AppButton` a variant such as `ghost` in fixture A, and have Spec 2 name a misspelling (`ghots`), which is clearly editorial. Or expect `design` for `huge`. |
| Suggestion / High | Task 6 Step 1 says to run `ds-count.py` in the fixture to check the counts. The executor's session loads the installed `my` plugin, whose `bin/` has no `ds-count.py` until the merge. | `plugins/my/bin/` on `main` (no `ds-count.py`). Plan Risk 3 says the same about the installed plugin. | Run `$WT/plugins/my/bin/ds-count.py` by path. |
| Suggestion / High | `test_double_star_matches_deep_files` says `web/a/b/c.vue` "holds the only match", but the shared fixture already has `<input>` in three files. The executor must invent a unique regex or a separate fixture. | Plan, Task 1 Step 1 (shared fixture and test snippet). | Give that test its own token, such as regex `<Deep\\b` written only in `web/a/b/c.vue`, and say so. |
| Suggestion / High | Several decisions have no test: outside a git repo exits 1 (Decision 6); a listed file that is missing is skipped (Decision 8); `globs` as a string, or `count` not an integer, is refused (Decision 10); unknown keys are kept (Decision 4). Decision 8 is the one most likely to crash with a traceback. | Plan, Decisions 4, 6, 8, 10 and the 24 tests in Task 1. | Add `test_outside_repo_refused`, `test_deleted_file_skipped` (delete without staging), `test_globs_not_list_refused` and `test_unknown_keys_kept`. |
| Suggestion / High | Task 5 edits `README.md`, which holds another session's uncommitted edits in the main checkout (the `kit:briefing` and `kit:dev-reports` entries). Its line numbers come from that dirty state (+6 against `main`). If those edits are still uncommitted at the merge, `git merge --squash` refuses. | `git diff README.md` in the main checkout. `git show HEAD:README.md` puts the `status-scan.py` sentence at 179. | Use `main`'s line numbers. Add to Risk that the squash-merge needs `README.md` committed or clean in the main checkout. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Grounding of the edit sites | `plugins/my/skills/handoff/SKILL.md:250,720`, `README.md:378`, `spec-reviewer-prompt.md:69`, `global/methods/my.md:57,84`, `docs-layout.md:167` all match | Strong |
| The counting design matches git's behaviour | Scratch repo: `':(glob)web/**/*.vue'` matches depth 0 and deeper. An exclude covering everything prints nothing with exit 0 (Decision 2). Zitamu gives 65/42 | Strong |
| Red → Green order and test style | Task 1 writes 24 tests before the script, copying `plugins/my/tests/test_status_scan.py:23-75` helpers. Decision 9 keeps the file unchanged on refusal | Strong |
| Reversibility and blast radius named | Prompt text plus one script. The reference sweep was run and its output quoted. Task 7, the one outward action, is gated on the user's yes | Strong |
| Baselines measured, not guessed | 203/40 tests and lint counts 1/0 reproduce exactly | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| A specified check contradicts its own test | Decision 7 vs `test_empty_match_regex_refused`. Python probe on `\b` | Medium |
| Rehearsal checks that cannot fail for the right reason | Task 7 `HEAD~5` (0 lines in zitamu). Task 6 Step 4 negative-only. Step 5 Spec 2 label | Medium |
| The order of work overridden silently | `ROADMAP.md:27-44` vs plan Risk 2 | Medium |
| The method's locked-commit rule is missing from the new skill | `plugins/my/skills/architect/SKILL.md:246-254` vs Task 2 item 7 | Medium |
| Expected results depend on unspecified model choices | Task 6 Step 2 (`row <N>` with no row). Step 3 (excludes) | Low |

## Not Applicable

None.

## Needs Investigation

- **Which copy of `my` loads in the zitamu clone.** Zitamu tracks `.claude/settings.json` with `"my@claude-setup": true`, so `git clone` carries it. A `claude -p --plugin-dir "$WT/plugins/my"` run in the clone may then load both the installed `my` (main's version) and the branch's copy. I could not check which `spec-review` wins. If the installed one wins, Task 6 Step 6 tests main's reviewer prompt, which has no new criterion 6 bullet, so the regression passes or fails for the wrong reason. To resolve: in the clone (scratch, not a zitamu file), set `"my@claude-setup": false` before the runs. Or grep the run's `.jsonl` for the path of the `spec-reviewer-prompt.md` it read, and check that it is under `$WT`.

## Reasoning

The plan's references hold almost everywhere: every edit site, baseline count and git behaviour it relies on checked out. The approach (a pure counter driven by stored patterns, prompt-only wiring, and a gated publish) is sound. The problems are in the checks. Decision 7 specifies a test that cannot go green. Two rehearsal checks are vacuous: Task 7's `HEAD~5`, and step 13 tested only where nothing should happen. Two more have expected results the skill text does not determine. Separately, the plan reverses a roadmap order the user set today, and the new skill misses the method's locked-commit rule for "Parallel runs" projects. Each is a fix to the plan, not a redesign, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High. The top findings were checked directly: a Python probe for Decision 7, and `git log` in zitamu for Task 7. Every edit-site line was read.
**Recommendation:** Before the code stage, change Decision 7 to refuse zero-width matches, and fix Task 7's synced-from commit. Add a positive step-13 rehearsal, and pin the Task 6 expectations (Sources before the row exists, excludes, the Spec 2 variant). Add the locked-commit form to the skill's commit rule. Ask the user whether row 64 may go before rows 33, 37, 56, 45 and 61, and record the answer in `ROADMAP.md`.
