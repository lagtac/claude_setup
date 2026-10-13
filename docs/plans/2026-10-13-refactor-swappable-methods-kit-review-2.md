# Review: main..refactor/swappable-methods-kit

**Status:** review of main..refactor/swappable-methods-kit, 2026-10-13. Sound: the fix round closed both findings of the first review, and this re-review found no new finding that passes the surfacing rule.

## Change Summary

The branch creates the `kit` plugin (`plugins/kit/`, its manifest and a marketplace row). It moves 15 neutral skills, agents and commands, the two md-table filter symlinks and the tutor SessionStart hook out of `plugins/my/`, and renames every `my:<kit name>` and `/my:<kit name>` reference outside `docs/` to `kit:`. The fix round reworded the `CLAUDE.md` intro, added the `plugins/kit` dev-loop line to `README.md`, wrote `/kit:push` as a command in the handoff README, and extended the kit description with the tutor clause. It also committed the first review and three Risk lines to the plan.

## Plan Alignment

The implementation matches Tasks 1 and 2, and the plan text matches the fix round's description change. I checked it against the repo:

- Task 1 file list: `find plugins/my plugins/kit -maxdepth 2` shows every listed skill, agent, command and `bin/` file under `plugins/kit/`. `plugins/my/` keeps only `architect`, `changelog-management`, `clean-plans`, `handoff`, `roadmap-management`, `soundness-review`, `spec-review`, `status`, the three review/summary agents, `summarize.md`, and its own `bin/` scripts. `plugins/kit/bin/*.py` are still symlinks to `/home/dchris/src/scripts/`.
- Task 1 Step 2: `plugins/kit/.claude-plugin/plugin.json:3` has the description the plan's updated Step 2 names (`plan.md:89`), and `.claude-plugin/marketplace.json:11` uses the same text, as Step 3 asks. The author matches `plugins/my/.claude-plugin/plugin.json`, and there is no `version`.
- Task 1 Step 5: `plugins/kit/hooks/hooks.json:5-13` is the old entry with `kit:tutor`; it is gone from `plugins/my/hooks/hooks.json`. All four JSON files parse (`python3 -m json.tool`).
- Task 2 Step 4: the plan's sweep (`git grep` over `global plugins README.md CLAUDE.md .claude-plugin`) prints nothing. A text search for the moved `plugins/my/<path>` names outside `docs/` also prints nothing.
- Task 2 Step 3: `CLAUDE.md:7` has the planned sentence. `README.md:10-11`, `:115`, `:170` and `:180` match the planned path hits. The README also has the install, update and `--plugin-dir` lines, and separate `my`/`kit` sections for skills and commands.
- Green check: the `my` suite still gives `Ran 145 tests` / `OK` (rerun by me).
- The remaining `my`-flavoured text inside `kit` is `plugins/kit/skills/tune-claude-instructions/SKILL.md:27` (an example path, still correct) and `:203` (`/my:summarize`, which Task 7 Step 2 rewords in batch 2). Neither is a batch 1 deviation.
- No deviations found.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|

No finding passed the surfacing rule.

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| No orphaned callers | The plan's name sweep and an old-path sweep both return nothing outside `docs/` (text searches I ran). Both `subagent_type` values follow the agent to `kit` (`plugins/kit/commands/laravel-debug.md:11`, `plugins/kit/commands/laravel-migration-check.md:21`). | Strong |
| Hook moved, not duplicated | Present once in `plugins/kit/hooks/hooks.json:3-14`, removed from `plugins/my/hooks/hooks.json` | Strong |
| First review's findings closed | `README.md:53-58` gives the `plugins/kit` form; the `locked-commit.py` dependency is recorded at `plan.md:532` | Strong |
| Description is consistent in all three places | `plugins/kit/.claude-plugin/plugin.json:3`, `.claude-plugin/marketplace.json:11`, `plan.md:89` | Moderate |
| Moves keep their history | Most files are 100% renames, and the edited ones are 86–99% similar, so `git log --follow` works | Moderate |
| No regression | 145 `my` tests pass | Moderate |

**Arguments this has problems:**

None material. The cross-plugin couplings left in place (`locked-commit.py`, the unprefixed `changelog-management` in `kit:dev-reports`, the gap before the runbook) are known limits in the plan's Risk section (`plan.md:532-534`).

## Not Applicable

- Soundness of approach (bandaid or compatibility cruft): a move and rename with no runtime logic. No aliases or dual paths were left behind.

## Reasoning

The fix round did what it said: each of the first review's findings is now resolved in the repo or recorded as a Risk line. My sweeps found no leftover `my:` names or old `plugins/my/` paths for the moved tools outside `docs/`, the JSON files parse, and the `my` suite passes. Caller sweeps were text searches only, because no symbol-reference tool was available. That is enough for this change, since every reference is a string in Markdown or JSON.

## Verdict

**Assessment:** Sound
**Confidence:** High. I reran the sweeps, the JSON parse and the test suite myself. I did not rerun `claude plugin validate`.
**Recommendation:** Squash-merge batch 1 with the planned subject, then run the batch 1 runbook in the same session.
