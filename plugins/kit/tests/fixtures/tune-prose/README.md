# Fixtures for the prose check of `kit:tune-claude-instructions`

Two fake skills, each planted with text that Patterns K–Q should flag and
text the rubric says to keep. They are not loaded as skills: the names are
flat, so step 1's search of this repository does not find them either.

Run the skill on one file without the interactive screen, from the repo
root:

```bash
f=plugins/kit/tests/fixtures/tune-prose/prose-only.md
ask="this is a non-interactive run: print the audit table and the fixes"
ask="$ask you would propose, then stop. Do not edit any file."
claude -p "/kit:tune-claude-instructions $f — $ask" \
  --plugin-dir plugins/kit --add-dir plugins/kit --permission-mode acceptEdits \
  --output-format stream-json --verbose > run.jsonl
```

Grep `run.jsonl` for `grading-rubric.md` to see which copy of the skill
loaded. Run each fixture at least twice: results vary between runs.

A pass flags every planted case, keeps every keep item, and proposes only
diffs that shorten the file, except fixes for the gaps listed below.

## `prose-only.md`

| Pattern | Planted text |
| --- | --- |
| K | "Breaking commits go under Upgrade steps" in the template and in Rules twice |
| L | "(Added on 2026-04-11 after row 31 …; 12 of 40 releases …)" |
| M | "Git keeps the history of every commit …" |
| N | "That is three sections: … Use them as given." |
| O | "Do not overwrite an existing file." after "stop and say so" |
| Q | The `description` summarizes every step |
| Keep | "NOT for CHANGELOG edits", the `AskUserQuestion` fallback, the stop conditions, "The project's `CLAUDE.md` wins", "because a reader follows Upgrade steps one by one" |

Unintended gap: a commit marked breaking with `!` has no footer to take the
upgrade step from, so the consistency check also fails.

## `mixed.md`

The same planted cases, plus P ("usually go in `other`") and a second M
("This skill works for any project that uses git"). It also has problems
that are not prose: the `Spec:` line clashes with "It works in any git
repository", and the scope grade (S) drops for the hedge.
