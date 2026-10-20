# Review: main..feat/link-check

**Status:** review of main..feat/link-check, 2026-10-21. Mixed: the approach is right and matches the spec, but two link forms are missed with no signal, and Risk does not list them as known limits. Answered in the fix round: the code review's run-time finding was fixed; every other finding of both reviews became a known limit in the spec's Risk 5.

## Change Summary

The branch adds `plugins/my/bin/link-check.py`, a read-only script. It lists `climbs`, `html` and `dead` links in the Markdown files it is given, and marks each one `new` or `old` from the `+` side of `git diff -U0 HEAD`. It also adds 39 subprocess tests in `plugins/my/tests/test_link_check.py`. Rules 9 and 10 of `roadmap-management` and `changelog-management` now run the script before each commit: they fix `new` problems by rule 8, list `old` ones, and fall back to a hand check when the script is missing or exits `2`. The branch also adds one README sentence and Risk item 8 of the spec, which records the code stage's choices.

## Plan Alignment

The implementation matches the spec (`docs/plans/2026-10-20-link-check-spec.md`, which holds the Tasks; there is no separate plan). Every difference from the Task 2 text is recorded in Risk item 8 (`docs/plans/2026-10-20-link-check-spec.md:230-247`), so none is a finding:

- `repo_root` returns `None` outside git. `new_lines` takes `(path, root)`. The helpers `resolve`, `ignored_paths`, `git`, `failed` and `blank` were added (`plugins/my/bin/link-check.py:57-152`). This is recorded in Risk 8.
- Fences may be indented (`plugins/my/bin/link-check.py:43`), and git runs with `LC_ALL=C` (`plugins/my/bin/link-check.py:61`). Both are recorded in Risk 8.
- `roadmap-management` rule 10 adds a sentence for the paired run (`plugins/my/skills/roadmap-management/SKILL.md:170`). This is recorded in Risk 8.
- Task 1 asks for 38 tests. The file has 39: the extra one is `test_outside_git_all_new_in_any_locale`. Several assertions are stricter than the spec's, since they also check exit `0` and an empty stderr. This adds to the plan and takes nothing away.
- Task 3 checks: both `git grep` commands for the removed phrases print nothing. `link-check.py` appears in both skills (`roadmap-management/SKILL.md:161,170`, `changelog-management/SKILL.md:126,135`). `markdownlint-cli2` with the global config reports the same errors on the merge base and the branch: 1 in `roadmap-management/SKILL.md` and 3 in `changelog-management/SKILL.md`, with none added (Risk 7).
- Task 4: the README sentence (`README.md:204-207`) matches the Task 4 text word for word.
- Task 5: the empty rehearsal commit's body records the results. Exactly the 5 known links were reported, all `old`. `webext`'s HTML link was not reported. The 4,482-line changelog took 0.22 s. The headless skill run asked about the new dead link and listed the old `.html` link without changing it. One check in this review supports the record: run on this repo's own files, the script reports `ROADMAP.md:278` as `dead`. In the worktree that file is missing, but in the main checkout it exists untracked, so the script counts it as present there (Risk 5). That fits the record's "exactly the 5 links".
- No deviation is surfaced as an issue.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | Two link forms are missed with no signal, and Risk does not list either one. (1) A line that starts with three backticks used as inline code, such as ```` ```foo``` text ````, opens a "fence". Every line after it is blanked up to the next fence or the end of the file. CommonMark does not allow a backtick in a backtick fence's info string, so this line is not a fence. Risk 8's limit covers only the "deep in a list" case. (2) Link text that holds brackets, such as `[see [1]](x)` or a linked badge `[![b](img.png)](docs/gone.md)`, is never matched. Probes of both cases gave exit `0` with a dead link present. A clean run makes the skill skip its hand check, so these links now get less checking than before. None of the 22 real files has either form today. | `plugins/my/bin/link-check.py:43`, `plugins/my/bin/link-check.py:80-84` (the opening test does not check the rest of the line), `plugins/my/bin/link-check.py:46` (`[^\[\]]*` in the link text) | Following the method's rule for input that today's files never produce, add both to Risk 5 as known limits. Optional fix for (1), one condition: a backtick fence does not open when the rest of its line holds a backtick. |
| Suggestion / High | A link through a symlinked folder inside the repo (for example `linkdir/r.md`, where `linkdir` is a symlink) makes `git check-ignore` fail with "beyond a symbolic link". `check()` raises before it returns any problem, so the whole file exits `2` and every other problem in it is lost. The skill falls back to a hand check, so the failure is visible, not silent. The tests cover a symlinked file (`test_symlink_inside_repo_not_climbs`), not a symlinked folder. No real file has such a link today. | `plugins/my/bin/link-check.py:148-150`, `plugins/my/bin/link-check.py:195`, `plugins/my/tests/test_link_check.py:208` | Add it to Risk 5 as a known limit, or leave out of the `check-ignore` input any path whose parent folder is a symlink. |
| Suggestion / High | A root-relative link (`[x](/docs/a.md)`) is reported as `climbs`: `os.path.join(base, "/docs/a.md")` discards the base folder. The skill text then says to fix a `new` `climbs` link with an absolute web URL, which is the wrong fix for a link that stays inside the repo. No real file uses this form today. | `plugins/my/bin/link-check.py:124-126`, `plugins/my/bin/link-check.py:132`, `plugins/my/skills/roadmap-management/SKILL.md:170` | Add it to Risk 5 as a known limit. Or, in `resolve`, join a target that starts with `/` to the repo root. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Tests pass and are end-to-end | `python3 -m unittest tests.test_link_check`: 39 tests, OK. Each test runs the real script as a subprocess in a throwaway repo (`plugins/my/tests/test_link_check.py:68-76`) | Strong |
| Real-file rehearsal and speed | This review ran the script on the repo's own `ROADMAP.md` and `CHANGELOG.md`: 0.09 s, one correct `old` hit. The rehearsal record reports exactly the 5 known links on 22 files, and 0.22 s on the 4,482-line changelog | Strong |
| A git failure is never turned into "all new" | `new_lines` raises on a failed `ls-files`/`diff` (`plugins/my/bin/link-check.py:164-171`). `main` turns that into exit `2` per file (`plugins/my/bin/link-check.py:218-221`), as D6 requires | Strong |
| Locale-safe "not a repo" detection | `LC_ALL=C` (`plugins/my/bin/link-check.py:61`), with a test in a Greek locale (`plugins/my/tests/test_link_check.py:324-330`) | Strong |
| Fits the existing script and skill style | The docstring holds Usage, the output format and exit codes, as in `plugins/my/bin/status-scan.py:1-40`. Other skills call `bin/` scripts by bare name (`plugins/my/skills/design-system/SKILL.md:116`) | Moderate |
| Skill text keeps a fallback | A missing script or exit `2` falls back to the old hand check (`plugins/my/skills/roadmap-management/SKILL.md:170`, `plugins/my/skills/changelog-management/SKILL.md:135`). The paired edit runs once, owned by `roadmap-management`, as D7 says | Strong |
| No lint regression | `markdownlint-cli2` with the global config reports the same errors on the merge base and the branch | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Silent misses that Risk does not list (a column-0 triple-backtick inline line; link text that holds brackets, including linked badges) | `plugins/my/bin/link-check.py:43`, `plugins/my/bin/link-check.py:46`, `plugins/my/bin/link-check.py:80-84` | Medium |
| One link through a symlinked folder hides every problem in its file (exit `2`) | `plugins/my/bin/link-check.py:148-150` | Low |
| A root-relative link is classed `climbs`, and the skill would turn it into an absolute URL | `plugins/my/bin/link-check.py:124-132` | Low |

## Not Applicable

- Risk & blast radius, orphaned-caller part: the branch removes and renames no symbol. Every symbol in `link-check.py` is new and private to the script. A text search found `link-check.py` only in the two skills, the README, the test file and `ROADMAP.md` rows. Every caller sweep in this review was a text search (`grep`/`git grep`), because no symbol-reference tool was available.

## Reasoning

The script does what D1 to D8 describe. The skill wording matches D7, and every difference from Task 2 is recorded in Risk 8. Tests, lint, the Task 3 greps and a rerun on real files all agree. The approach treats the root cause, moving a manual per-row check into a script, and it fails loudly on git errors rather than marking lines `new`. The surfaced issues are edge inputs that no current file holds. Only the silent ones reach Warning, because a clean run now replaces the hand check. Each issue can be fixed by adding one line to the Risk known limits, so no rework is needed. That makes the verdict Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every claim was checked by running the script, the tests or the linter, not read off the diff.
**Recommendation:** Add the three edge cases (a column-0 triple-backtick inline line, link text that holds brackets, a link through a symlinked folder) and the root-relative `climbs` case to Risk 5 as known limits. Optionally add the one-condition backtick-fence fix. Then merge.
