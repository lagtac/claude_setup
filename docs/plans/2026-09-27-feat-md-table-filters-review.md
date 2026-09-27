# Review: fda6f84..HEAD

**Status:** review of fda6f84..HEAD, 2026-09-27. Mixed: the design is right and the tests pass, but the expand filter drops cells without a word, which breaks the skill's promise that "a script moves every cell unchanged".

## Change Summary

The branch adds two stdlib-only stdin/stdout filters in `plugins/my/bin/`. `md-expand-table.py` lists the tables in a document, or rewrites the chosen ones as one heading section per row. `md-collapse-sections.py` prints a table built from `- **Field:** value` bullets. It also adds a 21-test unittest suite, the `my:md-tables` skill, a README entry and a `__pycache__/` ignore line.

## Plan Alignment

The branch matches the description. Every listed part is present. The filters never write files: both read a file or stdin and write to stdout (`md-expand-table.py:293,320`, `md-collapse-sections.py:117,149`). There is no stored index, and the skill says to print the overview and not store it (`SKILL.md:414-415`). The dependencies are stdlib only (`argparse`, `re`, `sys`). The suite passes: `cd plugins/my && python3 -m unittest discover tests` ran 21 tests, OK.

One deviation, against the skill's own claim rather than the brief:

- `plugins/my/bin/md-expand-table.py:252,265`: when a row has more cells than the header, the extra cells are dropped with no error. `SKILL.md:9-10` says the script moves every cell unchanged. This is issue 1 below.

The claim that "Claude Code puts that folder on PATH" (`README.md:86-87`) holds. The installed Claude Code 2.1.283 binary contains `pluginBinPaths` and the log line "plugin bin/ dirs off PATH". I checked this in the binary, not in the docs.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | Expand drops cells without a word when a row has more cells than the header. `zip(header[1:], cells[1:])` stops at the header's length. Tested: `\| a \| 1 \| extra \|` under a 2-column header gives `- **V:** 1` and loses `extra`, with exit 0. The skill's reason for using a script over a hand rewrite is that nothing is lost (`SKILL.md:9-10`). | `plugins/my/bin/md-expand-table.py:252,265` | Treat a row longer than the header like an empty or repeated key: exit 2 with the line number (`md-expand-table.py:254-261` is the pattern). |
| Warning / Medium | Collapse cannot read back all of what expand writes, so the round trip the docstrings promise (`md-expand-table.py:166-167`, `md-collapse-sections.py:37`) breaks with no warning. Tested: (a) key `C#` is written as `## C#` but read back as `C`, because the `HEADING` regex strips closing `#`s even with no space before them (CommonMark needs the space). (b) A `--body-col` value that starts with `- `, `1. `, `\|` or `<!--` is written as the paragraph, but `NOT_BODY` skips it, so the body cell comes back empty. (c) A column header that contains `*` gives a field line that `FIELD` (`[^*]+?`) does not match, so the field vanishes. | `plugins/my/bin/md-collapse-sections.py:47,49,50`; `plugins/my/bin/md-expand-table.py:264-270` | Pick one contract. Either make expand refuse values collapse cannot read (exit 2, as for empty keys), or make the readers match the writer: require whitespace before a closing `#` run, and read the paragraph slot by position rather than by what it looks like. Add a round-trip test for each case. |
| Suggestion / High | The skill says text can grow under a section (`SKILL.md:366-367`), but collapse treats any heading as the start of a new section. A `####` subheading added under `### X1` cuts X1 off there: fields after it are lost to X1, and the subheading shows up as its own row if it has fields. | `plugins/my/bin/md-collapse-sections.py:63-65`; `plugins/my/skills/md-tables/SKILL.md:363-367` | Say in the skill that subheadings are not allowed inside a section, or only count headings at or above the first section's level. |
| Suggestion / High | Expand writes no blank line after the new block. When the table is followed by a non-blank line, that line sticks to the last bullet as a lazy continuation, and the next heading loses its blank line. Tested: `\| a \| 1 \|` then `next line no pipe` gives `- **V:** 1` then `next line no pipe`, which renders as part of the V bullet. | `plugins/my/bin/md-expand-table.py:271-272,319` | End the replacement with a blank line when the next line is not blank (and start it with one when the line before is not blank). |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Right approach for the stated problem: a script moves cells mechanically, where an LLM rewrite can reword them | `plugins/my/skills/md-tables/SKILL.md:8-10` | Strong |
| The settled decisions are followed: stdout only, no stored index, stdlib only | `md-expand-table.py:293,320`; `md-collapse-sections.py:117,149`; `SKILL.md:414-415` | Strong |
| Fails loudly on the input the section format cannot hold: empty or repeated keys, unknown body column, bad table number. Exit 2 with nothing on stdout | `md-expand-table.py:243-244,254-261,304-318` | Strong |
| Tables in code fences are skipped by both tools, and escaped pipes round-trip | `md-expand-table.py:205-206`; `md-collapse-sections.py:57-62,89-90`; tests `test_md_table_filters.py:465-469,476` | Moderate |
| Multi-table expand runs from the last table back, so the listed numbers stay valid, and a test proves it | `md-expand-table.py:301,311-319`; `test_md_table_filters.py:549-555` | Moderate |
| Fits the plugin layout: `bin/` is a Claude Code plugin PATH directory (checked in the 2.1.283 binary), the files are executable (mode 100755), and the skill matches the sibling skills' frontmatter and prose | `plugins/my/skills/de-slop/SKILL.md:1-4` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Cells beyond the header are dropped silently, which goes against the tool's reason to exist | `md-expand-table.py:265` | Medium |
| Some values expand writes do not survive collapse, and nothing warns | `md-collapse-sections.py:47,49,50` | Medium |
| The round-trip test covers only one clean case, so the gaps above went unseen | `test_md_table_filters.py:679-688` | Low |
| The installed plugin is pinned at fda6f84 (`~/.claude/plugins/installed_plugins.json`), so the filters are not on PATH until the plugin is updated after the merge | `README.md:86-87` | Low |

## Not Applicable

- Risk & blast radius, the orphaned-caller part: the diff removes or renames no symbol. It adds only new files, plus one README bullet and one `.gitignore` line. The sweep was text-only (`grep`/`find` through Bash); there was no symbol tool.

## Reasoning

The approach suits the goal: deterministic filters, stdout only, strict errors on keys, and a skill that tells the agent to use them rather than rewrite by hand. Solves the stated problem: mostly. The two Warnings come from the same weak spot. The tool pair's value is that nothing is lost and collapse undoes expand. Expand still loses extra cells, and collapse misreads some values expand writes. Both are fixed by tightening validation or matching the regexes, not by a redesign. So the verdict is Mixed, not Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** High. Each finding was reproduced by running the filters on sample input, and the suite passes.
**Recommendation:** Make expand exit 2 on rows longer than the header. Then either reject or support the three round-trip gaps (closing `#` in keys, list-like body values, `*` in headers), with one round-trip test each. Then update the installed plugin so `bin/` reaches PATH.
