# Review: main..refactor/swappable-methods-kit

**Status:** review of main..refactor/swappable-methods-kit, 2026-10-13. Sound: batch 1 does what Tasks 1 and 2 ask, with no orphaned `my:` callers; the top finding is a Suggestion that the moved `/kit:commit` still depends on `locked-commit.py` in `my`'s `bin/`.

## Change Summary

The branch creates a new `kit` plugin (`plugins/kit/`, with its manifest and a marketplace row), moves 15 neutral skills, agents and commands, the two md-table filter symlinks and the tutor SessionStart hook out of `plugins/my/` with renames, and removes that hook from `plugins/my/hooks/hooks.json`. A second commit renames every `my:<kit name>` and `/my:<kit name>` reference outside `docs/` to `kit:`, and updates `README.md` and `CLAUDE.md` to describe two plugins.

## Plan Alignment

The implementation matches Tasks 1 and 2. I checked it against the repo:

- Task 1 file list: every listed skill, agent, command and `bin/` file is in `plugins/kit/`. The `bin/` entries are still symlinks to `/home/dchris/src/scripts/` (`ls -la plugins/kit/bin`). `plugins/my/` now holds only the files the spec's Plugins table keeps (`docs/plans/2026-10-12-swappable-methods-spec.md:136`).
- `plugins/kit/.claude-plugin/plugin.json:1-7` has the planned name and description, the author copied from `plugins/my/.claude-plugin/plugin.json`, and no `version` field.
- `.claude-plugin/marketplace.json:15-20`: the `kit` row comes right after `my`, as Step 3 says.
- `plugins/kit/hooks/hooks.json:1-16` is the old entry with `kit:tutor` in its text. The squash-merge hook, including its learning-workspace check, stays in `plugins/my/hooks/hooks.json:22`, as Task 1 Step 5 says (it changes in Task 7).
- Task 2 sweep: I reran the plan's `git grep` (also over `.claude-plugin`) and it prints nothing. Every listed hit was renamed, including both `subagent_type` values (`plugins/kit/commands/laravel-debug.md:11`, `plugins/kit/commands/laravel-migration-check.md:21`).
- Task 2 path hits and Step 3: `README.md:10-11` (new bullet), `README.md:112` (`plugins/kit/bin/`), `README.md:167` and `README.md:177` (one hooks list per `hooks.json`), install and update lines, separate `my`/`kit` sections for skills and commands, and the agents table. `CLAUDE.md:7` has the planned sentence word for word.
- Green checks, rerun by me: the `my` suite gives `Ran 145 tests` / `OK`, and `claude plugin validate` passes (with warnings only) for `plugins/kit`, `plugins/my` and `.`.
- No deviations found. The commit subjects match Task 1 Step 7 and Task 2 Step 5.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | The moved `/kit:commit` command calls `locked-commit.py`, which stays in `plugins/my/bin/`. A "neutral" kit command now relies on a script that is on PATH only when `my` is on. Today this holds in every project, and after batch 2 it still holds in practice, because only `my` projects have a "Parallel runs" section. But neither the spec nor the plan writes this dependency down. | `plugins/kit/commands/commit.md:11`; `plugins/my/bin/locked-commit.py` (`ls plugins/my/bin`); spec keeps `locked-commit.py` in `my` at `docs/plans/2026-10-12-swappable-methods-spec.md:136` | Add one line to the plan's Risk section, or to `commit.md`, saying that the Parallel-runs branch of the command needs the `my` plugin. No code change is needed for batch 1. |
| Suggestion / High | The "try an uncommitted edit" recipe in `README.md` still names only `plugins/my`. Editing a `kit` skill now needs `--plugin-dir .../plugins/kit`, and the warning about loading the plugin twice applies to `kit` as well. | `README.md:55-59` | Add the `plugins/kit` form next to the `plugins/my` line. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| No orphaned callers | The plan's sweep regex over `global plugins README.md CLAUDE.md .claude-plugin` returns nothing. The map's old-path sweep (`plugins/my/<moved path>`) shows no hits, and I rechecked for `plugins/my` in `plugins/kit` (only an example path at `plugins/kit/skills/tune-claude-instructions/SKILL.md:27`, which is still correct). | Strong |
| Agent dispatch keys renamed in step with the agent's plugin | `plugins/kit/commands/laravel-debug.md:11`, `plugins/kit/commands/laravel-migration-check.md:21`, with the agent at `plugins/kit/agents/laravel-fullstack-expert.md` | Strong |
| Hook moved, not duplicated | Removed from `plugins/my/hooks/hooks.json` (the old lines 37-46) and added once in `plugins/kit/hooks/hooks.json:3-14`. Both files parse as JSON. | Strong |
| Pure moves keep their history | Most files are 100% renames, and the edited ones are 86–99% similar (diff headers). This keeps `git log --follow` working. | Moderate |
| Behaviour unchanged, regressions checked | 145 `my` tests pass, and all three validators pass | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Undocumented dependency from kit to my | `plugins/kit/commands/commit.md:11` → `plugins/my/bin/locked-commit.py` | Low |
| Dev-loop docs name only one plugin | `README.md:55-59` | Low |

## Not Applicable

- Soundness of approach (bandaid or compatibility cruft): this is a move and rename with no runtime logic. No aliases or dual paths were left behind, so there is nothing to check for masking.

## Reasoning

The branch does what the plan's Tasks 1 and 2 describe. I found no deviation, and both sweeps show no leftover `my:` names or `plugins/my/` paths for the moved tools outside `docs/`. The checks the plan names (layout, three validators, 145 tests) pass when I rerun them. The two findings are a cross-plugin dependency that does not break today, and a docs gap. Neither changes the approach or the blast radius of the move, so the change is sound.

## Verdict

**Assessment:** Sound
**Confidence:** High — I verified the sweep, the JSON files, the validators and the test suite against the repo myself. Caller sweeps were text searches only (no symbol-reference tool was available).
**Recommendation:** Merge as planned and run the batch 1 runbook. Optionally, first add the `plugins/kit` line to the README's dev-loop recipe and record the `locked-commit.py` dependency in the plan's Risk section.
