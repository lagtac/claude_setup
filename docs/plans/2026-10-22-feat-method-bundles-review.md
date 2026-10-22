# Review: main..feat/method-bundles

**Status:** review of main..feat/method-bundles, 2026-10-22. Sound: batch 1 matches Tasks 1–9 of the plan, and the moves check out against `main`; the only finding is a README line about starting a tutor workspace that is no longer true.

## Change Summary

The branch turns the `my` and `tutor` methods into plugins whose rules are a forced output style, and adds an `sp` method plugin. A new script, `plugins/kit/bin/claude-method`, is the only code that reads the method list and each method's `dependencies`; the rewritten start check (`method-guard.py`) and the rewritten `/kit:setup` skill call it. The core `global/CLAUDE.md` takes in the `plain` style's text and gives its engineering sections to a new path-scoped `global/rules/engineering.md`. The old method files, rule files and output styles are deleted, and this repo and zitamu lose their import lines.

## Plan Alignment

The implementation matches Tasks 1–9 of the plan. I checked each task's file list, interfaces and named tests against the diff and the repo:

- Task 2: every test the plan names is in `plugins/kit/tests/test_claude_method.py`, and the script follows the Interfaces block (`plugins/kit/bin/claude-method:128-167`).
- Task 3: I reran the plan's Step 6 line-set check against `main`. GONE and ADDED hold exactly the lines the plan expects and nothing else. The core's section order is the one in Step 4 (`global/CLAUDE.md:1-67`, with the HTML comment at the end).
- Task 4: I reran the Step 4 `diff` of the three old files against `plugins/my/output-styles/my.md`. The only differences are the frontmatter, the dropped `paths:` and "Applies only…" lines, and the twelve table edits.
- Task 5: I diffed the tutor style against the two old files. It shows only the rule 8 edits and `force-for-plugin: true`. The skill move, the `hooks.json` deletion, `plugins.json` and the descriptions are as planned.
- Task 6: the `sp` plugin and style are as planned. `plugin.json` also has an `author` field, which the plan does not name. That is harmless and matches `tutor` and `kit`.
- Task 7: every test the plan lists is in `test_method_guard.py`. The guard's three warning texts match the Interfaces block word for word (`plugins/kit/hooks/method-guard.py:136-151`).
- Task 8: `plugins/kit/skills/setup/SKILL.md` has the plan's eight parts in order.
- Task 9: `CLAUDE.md`, `projects/real-estate-webapp/claude-local.md` and `README.md` are edited as planned, and `test_no_file_names_a_moved_path` passes.
- Missing items: none in scope. Tasks 10–12, the batch 1 marks and the rollout are out of scope for this branch, as the caller stated.

No deviation rises to a finding.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | The README still says the tutor starts when you "Say 'let's make a learning project for …'". After this branch, `tutor:tutor` lives in the `tutor` plugin, which is off everywhere except a tutor folder. So in an ordinary session, that phrase reaches no skill. The spec accepts that the plugin must be on first (Trade-offs, "Starting a new learning project"). But the README entry was moved as it was, and the batch 2 README step (Task 12 Step 5) edits the methods section, not this line. | `README.md:185-189`; `docs/plans/2026-10-20-method-bundles-spec.md:432-433` | Change the last sentence: start a session with the `tutor` plugin on (`claude-method tutor` in the workspace folder), then say "let's make a learning project for …". This can wait for batch 2, once `claude-method` is on the shell's `PATH`. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| One owner for the method list and the off set. The guard and `/kit:setup` call the script instead of copying its logic. | `plugins/kit/bin/claude-method:71-108`; `plugins/kit/hooks/method-guard.py:56-75`; `plugins/kit/skills/setup/SKILL.md:62-70` | Strong |
| Moved text is moved word for word. I reran the plan's checks against `main`, and they show only the named edits. | `global/CLAUDE.md`, `global/rules/engineering.md`, `plugins/my/output-styles/my.md`, `plugins/tutor/output-styles/tutor.md` | Strong |
| No orphaned references. Text searches for `.claude/methods`, `methods/my`, `kit:tutor`, `outputStyle`, `**Method:**`, `docs-layout`, `plan-format`, `output-styles`, "Engineering standards", "in the core" and "the core's" find only deliberate hits. Those are the guard's import regex, `/kit:setup`'s removal rules, tests, and the my style's updated pointers. | Searches run on the branch head; `plugins/kit/tests/test_neutral_core.py` (`test_no_file_names_a_moved_path`) | Strong |
| The guard keeps its contract: it always exits 0, prints at most 2,000 characters, and reads files only. When `claude-method` fails, it gives one warning and judges nothing else, so it cannot give a wrong answer from a missing list. | `plugins/kit/hooks/method-guard.py:154-176` | Strong |
| End-to-end tests run the real script, with a fake `claude` on `PATH`. The guard runs the real `claude-method` under it. `test_real_marketplace` checks the repo's own manifests. | `plugins/kit/tests/test_claude_method.py`, `test_method_guard.py`; both suites pass (103 and 292 tests, rerun at the branch head) | Strong |
| The `engineering.md` brace globs use a form that already works here. `global/rules/markdown.md` (`**/*.{md,mdx}`) and `js-ts.md` use the same syntax, and `markdown.md` loaded in this session. | `global/rules/engineering.md:1-6`; `global/rules/markdown.md`, `global/rules/js-ts.md` frontmatter | Moderate |
| The script reads the real `known_marketplaces.json` shape. The `claude-setup` entry has `installLocation` as a string at the top level, which is what `marketplace_folder()` expects. | `plugins/kit/bin/claude-method:51-62`; `~/.claude/plugins/known_marketplaces.json` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The entry point for a new learning workspace is documented as a phrase that no longer reaches the skill in an ordinary session. | `README.md:188-189` | Low |
| `/kit:setup` is a prose skill. Its correctness (the right keys removed, only tracked files committed) rests on the headless check of Task 8, which leaves nothing in the diff. See Needs Investigation. | `plugins/kit/skills/setup/SKILL.md:113-206` | Low |

## Not Applicable

None.

## Needs Investigation

- **The headless checks are not visible in the diff.** These are Task 4 Step 9 (the `my` style loads with `superpowers`), Task 6 Step 5 (`claude-method sp` turns `my` off) and Task 8 Steps 1 and 3 (`/kit:setup` cases A and B, with zero `permission_denied` events). They write to the scratchpad, not the repo, so I could not check that they ran or passed. They matter most for `/kit:setup`: it has no unit test, and the skill was rewritten. The code stage's output or the saved stream files would settle this.
- **Coverage note.** I read the whole 2,919-line payload. I checked the moved bodies (`plugins/my/output-styles/my.md`, `plugins/tutor/output-styles/tutor.md`, the plain text in `global/CLAUDE.md`, and `global/rules/engineering.md`) by rerunning the plan's diffs against `main`, not line by line. I read the new and rewritten code (`claude-method`, `method-guard.py`, the two test files and `/kit:setup`) in full. Every caller sweep was a plain text search (`git grep`). I had no symbol-reference tool.

## Reasoning

The change does what the spec and plan describe. Rules and plugin keys now load together, through one script that owns the method list. The moves were checked against `main`, not trusted. The removed symbols and paths have no orphaned callers. The design limits I noticed are listed in the plan's Risk section or the spec's Trade-offs, so they are not findings: the dangling `outputStyle: plain` and `~/.claude/methods` links until the rollout, the `mv3-tab-notes` gap, the off set turning off a plugin enabled on purpose, and a start check that cannot see flags. The one surfaced item is a stale README sentence, a Suggestion. So by the table, the assessment is Sound.

## Verdict

**Assessment:** Sound
**Confidence:** Medium. The Python, the tests and the text moves are verified at the branch head, but `/kit:setup`'s behaviour rests on headless checks I could not see.
**Recommendation:** Merge batch 1 as planned, after the review stage's dirty-file check. Ask the code stage to confirm that the Task 8 headless check passed with zero `permission_denied` events. Fix the README tutor entry in batch 2, when Task 12 edits the README.
