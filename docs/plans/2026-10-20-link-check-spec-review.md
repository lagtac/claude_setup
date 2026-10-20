# Review: docs/plans/2026-10-20-link-check-spec.md

**Status:** review of docs/plans/2026-10-20-link-check-spec.md, 2026-10-20. Mixed: the script design is sound and well grounded. The top finding is that the spec runs row 51 ahead of row 69, which the Order of work puts first, and it does not say so.

## Spec Summary

The spec adds `plugins/my/bin/link-check.py`. The script reads the Markdown files it is given and prints one tab-separated line per bad link. A bad link has one of three kinds: `climbs` (leaves the repo), `html`, or `dead` (missing, or ignored by git). Each line is marked `new` or `old`, based on `git diff -U0 HEAD`. Rule 10 of `roadmap-management` and of `changelog-management` changes so that both skills run the script after each edit, fix the `new` problems and list the `old` ones to the user. The next-row-number half of row 51 is dropped.

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `link-check.py` | Which text counts as a link (D2, D3), the three kinds and their order (D4), the `new`/`old` mark (D5), the output format and exit codes (D6) | Python standard library; `git rev-parse`, `git diff`, `git check-ignore`; the working tree | New, in `plugins/my/bin/` (folder verified, `plugins/my/bin/status-scan.py:1`) |
| `test_link_check.py` | The end-to-end tests of the script | `link-check.py`; the helper style of `test_status_scan.py` | New; style verified at `plugins/my/tests/test_status_scan.py:24-68` |
| `roadmap-management` rule 10 | When the check runs on `ROADMAP.md`, which problems are fixed, how each kind is fixed, the fallback when the script is missing | `link-check.py` on `PATH`; rule 8 (link rules); rule 6 (paired edit) | Existing `plugins/my/skills/roadmap-management/SKILL.md:164-173` |
| `changelog-management` rule 10 | The same for `CHANGELOG.md`; `dead` to a deleted document is unlinked | `link-check.py`; its rule 8 | Existing `plugins/my/skills/changelog-management/SKILL.md:127-135` |
| `roadmap-management` rule 6 | The precondition that links resolve before a ✅ edit (kept), and the paired run with both files | `changelog-management` | Existing `plugins/my/skills/roadmap-management/SKILL.md:115-138` |
| Plugin `bin/` on `PATH` | Making the script callable by bare name | Claude Code plugin loading | Existing; stated at `README.md:174`, used at `plugins/my/skills/status/SKILL.md:29`, `plugins/my/skills/design-system/SKILL.md:116` |
| `README.md` bin paragraph | One sentence on the script | — | Existing `README.md:178-196` |
| Row 69 (future) | Moving both skills, and per the spec this script, to `kit` | — | Existing row, `ROADMAP.md:250-254`; its text names only the skills |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Skill rule 10 → `link-check.py` | Call with one or two file paths, relative to the working directory | Skill (paths); script (interface, D1) |
| `link-check.py` → git | `rev-parse --show-toplevel` per folder, `diff -U0 HEAD -- <file>`, `check-ignore --stdin` per file | Script |
| Working tree → `link-check.py` | The uncommitted edit, read through `git diff HEAD` | The skill, which must not commit before the run (not stated, see Issues) |
| `link-check.py` → skill | Tab-separated lines `<kind> <file>:<line> <target> <new\|old>`; exit 0, 1 or 2 | Script (D6) |
| Skill → user | One line per `old` problem; a question when a `new` `dead` link has no moved file | Skill (D7) |
| Skill → `ROADMAP.md` / `CHANGELOG.md` | Fixes to `new` problems, by rule 8 | Skill |
| `roadmap-management` rule 6 → `changelog-management` | Delegation of the changelog half; the spec adds "one run with both files" | Not assigned to a file (see Issues) |

## Grounding

Searches were text-only (`grep`, `sed`, `git`). No symbol-reference tool was available. The spec removes two phrases. A text search for "full-file link greps" and "link-resolution greps" across the repo, outside `docs/plans`, finds only `plugins/my/skills/roadmap-management/SKILL.md:173` and `plugins/my/skills/changelog-management/SKILL.md:135`, which are the two lines D7 edits.

- `spec §How to read this spec` item 3 says rule 10 is at lines 165–173. It starts at `plugins/my/skills/roadmap-management/SKILL.md:164`. Off by one.
- `spec §How to read this spec` item 6 says the README paragraph is at lines 180–196. It starts at `README.md:178`.
- `spec §Risk` 3 calls `guide/saved-details/` in `grispy-site` a false `dead`: "a path the site serves but the repo does not hold". The site no longer serves it. `grispy-site/CHANGELOG.md:93` says "`/guide/saved-details/` now returns GitHub's 404", and the folder is gone (`ls guide/` lists no `saved-details`). The link is truly dead, as `spec §Context` says.
- `spec §Risk` 7: the counts (1 and 3 errors) hold only with the global config `~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc`. A bare `markdownlint-cli2` run reports 90 and 55. The spec does not name the config.

The other references hold. Row 51 is in step 5 (`ROADMAP.md:61-62`, `:415`). `**Next number:** 74` is at `ROADMAP.md:13`, and 73 is the highest row. Report S12 is at `docs/reports/2026-10-14-scriptable-skill-steps.md:141`. Rule 8 of each skill is at `roadmap-management/SKILL.md:147` and `changelog-management/SKILL.md:111`. The rule 6 precondition is at `roadmap-management/SKILL.md:122`. `status-scan.py` never reads `CHANGELOG.md`. The test helpers `clean_env`, `git`, `run` and `make_repo` exist (`test_status_scan.py:24-58`). The Delegation keys match `plugins/my/skills/handoff/SKILL.md:130-141`. `real-estate-webapp/CHANGELOG.md` has 4,482 lines. All 6 bad links in Context exist in those projects. No existing link checker is in the repo.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | The Order of work puts row 69 (step 3) before row 51 (step 5), and "the steps run top to bottom". The spec assumes row 51 lands first in `plugins/my/` and hands the move to row 69. It does not say that it jumps ahead or why, and row 69's text does not mention a script, a test file or a README sentence to move. | `ROADMAP.md:24-27`, `:46-51`, `:61-62`, `:250-254` ↔ `spec §Out of scope`, `§Risk` 6, `§D8` | Decision for the author: say that row 51 runs ahead of row 69 with the user's consent, and add one clause to row 69 in this row's commit. Or wait for row 69 and use `kit` paths. |
| Warning / Medium | design | The only real `html` hit is a link to a real, tracked HTML file: `assets/grispy-landing.html` in `webext`, with no `.md` beside it. D7's fix, "`html` → the `.md` path", has no target there. Rule 8's reason (an `.md` exported to HTML) does not fit this file. The skill will list it on every edit and cannot fix it. | `webext/ROADMAP.md:82`; `git ls-files assets` in `webext` lists only `README.md`, images and `grispy-landing.html` ↔ `spec §D4`, `§D7` | Decision for the author: flag `html` only when a sibling `.md` exists or the `.html` file is missing, or tell the skill to ask when no `.md` exists. |
| Warning / Medium | design | `new` means "on a line the edit changed", not "added by the edit" (Goal) and not "in the row you touched" (today's rule 10). In this repo's bullet roadmap, a row wraps over several lines, so a status-only edit leaves the row's link line `old`: a bad link in the touched row is only listed, where today's rule 10 requires it to resolve. In a table roadmap, one line is one row, so the same status edit makes an old `../` link `new`, and the skill must fix it. | `ROADMAP.md:250-254` (wrapped row); `diagoradisa-annotator/ROADMAP.md:143` (one-line row); `roadmap-management/SKILL.md:169` ↔ `spec §Goal`, `§D5`, `§D7` | Decision for the author: state the intended scope (changed lines, or the whole touched row) and word the Goal to match. |
| Warning / Medium | design | D5 works only while the edit is uncommitted, and D7 does not say that rule 10 runs before the commit. Rule 9 (commit) comes before rule 10 in both skills, and `roadmap-management` says "the rules are sequential". If the model commits first, every problem reads `old`, and nothing is fixed. | `roadmap-management/SKILL.md:65`, `:156-173`; `changelog-management/SKILL.md:122-135` ↔ `spec §D5`, `§D7` | Add to the rule 10 bullet: "Run it before the commit." |
| Warning / Medium | design | D7 sets a fallback only for "not on `PATH`". It does not say what the skill does on exit 2, or when a `git` call inside the script fails. D6 also does not say whether one unreadable file stops the output for the other file in a paired run. | `spec §D6` ↔ `§D7` | Decision for the author: on exit 2, report the stderr line and fall back to the hand check; say whether the script reports the other file. |
| Suggestion / High | design | D4 compares a `normpath` path with `git rev-parse --show-toplevel`, which git returns resolved. An absolute file path given through a symlinked folder makes every relative link `climbs`. A probe confirmed it: toplevel `…/real` against normpath `…/alias/ROADMAP.md`. Relative input is safe, because `os.path.abspath` uses the resolved working directory. | Probe in a scratch repo; `spec §D1` "read as given", `§D4` | Resolve the file's folder with `realpath` before joining, and keep `normpath` for the target only. |
| Suggestion / High | editorial | Risk 3's example of a false `dead` is a truly dead link. Context counts it as one of the 6 bad links. | `grispy-site/CHANGELOG.md:93` ↔ `spec §Context` ↔ `§Risk` 3 | Drop the example, or replace it with a real site-only path. |
| Suggestion / High | editorial | Risk 7 and Task 3 compare lint counts, but they do not name the config. The counts hold only with the global config. | `spec §Risk` 7, `§Tasks` Task 3 | Name `--config ~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc`. |
| Suggestion / High | design | "A paired edit runs the script once with both files" is not assigned to a skill file. `changelog-management` rule 10 will still run its own check when rule 6 delegates to it. | `spec §D7`; `roadmap-management/SKILL.md:133` | Say which rule's text holds the paired run, and whether `changelog-management` skips its own run then. |
| Suggestion / High | editorial | D6's exit table has no row for `--help`, which the test expects to exit 0. Two line references in "How to read this spec" are off by one or two (see Grounding). | `spec §D1`, `§D6` | Add "or `-h`/`--help`" to exit `0`; fix the line numbers. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | The script owns detection and the `new`/`old` mark. The skills own the fixes and what to tell the user. `status-scan.py` stays a row reader and never reads `CHANGELOG.md`. | Strong |
| Grounding | Nearly every claim checked out: all 6 bad links, the 4,482-line changelog, the `PATH` claim, the rule line numbers within two lines, the test helper style, the Delegation keys. | Strong |
| Fit | No link checker exists in the repo. The script follows the shape of `status-scan.py` (docstring usage, tab fields, exit 2 for usage errors). The rejected options are real and have reasons: a `status-scan.py` flag, `lychee` (a dependency that needs approval), a hook that other projects do not run. | Strong |
| Failures (fallback) | A session with an old plugin falls back to today's hand check (`spec §D7`, `§Risk` 4). The script reads and never writes. | Moderate |
| Contracts | D6 fixes the output format, the order, the file field and the exit codes. The skill reads field 4, not the exit code, to tell `new` from `old`. | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Fit with the order | Row 69 is ordered before row 51, and the spec assumes the reverse without saying so. | Medium |
| Contracts (`new` scope) | Line granularity differs from the row scope of today's rule 10. Bullet and table roadmaps behave in opposite ways. | Medium |
| Flow (timing) | The `new` mark depends on the run happening before the commit, and the rule text does not say so. | Medium |
| Kinds (`html`) | The one real `html` hit has no `.md` to fix to. | Medium |
| Failures | The skill's behaviour on exit 2 is not decided. | Low |

## Not Applicable

None. The off-path UI events check under criterion 3 and the Visual Language checks under criterion 6 were skipped by rule, because the spec adds no UI.

## Needs Investigation

- `spec §Context` says the 6 bad links come from "15 roadmap and changelog files in 9 projects". I confirmed each of the 6 links, but not the count of files or projects, nor that the 15 files hold no other bad link. Task 5 step 1 runs the script on all 15 and settles this.

## Reasoning

The System Model is clean. One new script owns detection, the two existing rule 10s own the response, and every connection has a defined format. The weak points are at the edges of the D5 contract: when the run happens relative to the commit, and what "new" covers. There is also one unstated ordering choice against row 69, and one `html` case with no fix. None of these changes the approach. Each needs a decision from the author, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High. Every Warning rests on a repo line I opened or a contradiction inside the spec.
**Recommendation:** Ask the user the five `design` Warnings in the "No silent reinterpretation" form, starting with the row 69 order and the `new` scope. Then fix the `editorial` Suggestions (Risk 3 example, lint config, help exit code, line numbers) and approve.
