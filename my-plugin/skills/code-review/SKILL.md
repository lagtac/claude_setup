---
name: code-review
description: >
  Dual-perspective code review with anti-sycophancy framing and severity-conditioned
  surfacing. Auto-detects Laravel, Python, or TypeScript projects and applies a
  language-specific checklist; falls back to a generic 12-item checklist otherwise.
  Use when the user asks for a code review, /my:code-review, before merging, or after
  finishing a task. Defaults to reviewing the working-tree diff; pass a `BASE..HEAD`
  range to review a committed range pre-merge. Optionally accepts a description of
  what was built and/or a path to a plan/spec — when supplied, the reviewer also
  checks whether the diff matches the plan.
---

# Code Review

Dispatch a fresh-context reviewer subagent against the diff specified by the caller — the working-tree diff by default, or a committed range (`BASE..HEAD`) when invoked pre-merge. The reviewer renders dual-perspective output with severity-conditioned confidence labels and a reasoning paragraph before its verdict — no rubber-stamping.

The methodology, output schema, and surfacing rules are authored once here and in `code-reviewer-prompt.md`. The agent receives the full prompt at dispatch time and must not improvise the diff or the checklist.

## Steps

### 0. Classify the freeform args string

The skill's args field is a single freeform string. Classify each whitespace-separated token (or sub-token) by content shape, not by a rigid `key=value` grammar:

| Token shape | Variable |
|---|---|
| `<ref>..<ref>` literal (e.g. `main..HEAD`, `abc1234..def5678`) | `RANGE` |
| Two SHA-shaped tokens (`[0-9a-f]{7,40}`) appearing together | `RANGE` (joined with `..`) |
| A path ending in `.md` that exists on disk | `PLAN_PATH` |
| The exact word `laravel`, `python`, or `typescript` (case-insensitive) | `LANGUAGE_OVERRIDE` |
| Anything else (free prose) | append to `DESCRIPTION` |

If a token is ambiguous (e.g., a `.md` path that doesn't exist), prefer `DESCRIPTION` and surface a one-line note: `(arg "<token>" treated as description; expected file but not found)`.

If args is empty, all four variables are empty — the skill runs in defaults (working-tree diff, auto-detected language, no plan-alignment block).

### 1. Detect language

If `LANGUAGE_OVERRIDE` was set in step 0, use it directly — skip auto-detection.

Otherwise, resolve the language adapter from project markers. Check the current working directory (project root, found via the nearest `.git`):

| Markers | Language adapter |
|---|---|
| `composer.json` AND `artisan` | `laravel` |
| `pyproject.toml` AND (`uv.lock` OR `poetry.lock`) | `python` |
| `package.json` AND `tsconfig.json` | `typescript` |
| (none of the above match) | `generic` |

The corresponding language file is `language/<resolved>.md` relative to this skill directory. **If the resolved language file does not exist**, fall back to `language/generic.md` — this allows the canonical skill to land before per-language adapters are authored.

### 2. Capture the diff

**If `RANGE` is set** (committed-range mode):

```bash
git diff "$RANGE"
git log "$RANGE" --oneline
```

The diff is the primary payload; the log is appended after the diff under a `--- COMMITS IN RANGE ---` separator so the reviewer sees the commit boundary structure (one logical change vs many).

**Otherwise** (working-tree mode, default):

```bash
git diff
git diff --staged
git ls-files --others --exclude-standard
```

The third command lists untracked files; for each one, run `git diff --no-index /dev/null <path>` to produce canonical new-file diff output (`diff --git`, `new file mode`, `--- /dev/null`, `+++ b/<path>`, `@@`, content). Concatenate those onto the working-tree and staged diffs. Do **not** hand-construct the diff headers — `git diff --no-index` does this correctly and consistently.

If the resulting payload is empty, stop with a message: `No changes to review.` (working-tree mode) or `Range <RANGE> is empty.` (range mode).

### 3. Build the dispatch prompt

Read `code-reviewer-prompt.md` from this skill's directory. Read the resolved `language/<resolved>.md` file from step 1.

If `DESCRIPTION` or `PLAN_PATH` is set, **build a plan-alignment block** as follows:

```markdown
## Plan Alignment

The work this diff implements:

<DESCRIPTION (if set, otherwise omit this paragraph)>

The plan/requirements:

<contents of PLAN_PATH file (if set, otherwise omit this paragraph)>

Apply a plan-alignment check in addition to the standard checklist: does the implementation match what was described? Are deviations justified or problematic? Is anything in the plan missing from the diff? Surface deviations as findings using the same severity / confidence labels.
```

If neither `DESCRIPTION` nor `PLAN_PATH` is set, the plan-alignment block is the empty string.

Compose the dispatch prompt by:
1. Starting with the contents of `code-reviewer-prompt.md`
2. Replacing `{{LANGUAGE_FILE}}` with the contents of the language file (whole file, including any sub-headings)
3. Replacing `{{PLAN_ALIGNMENT}}` with the plan-alignment block from above (or empty string)
4. Replacing `{{DIFF}}` with the combined diff from step 2
5. Replacing `{{PLAN_DIRECTORY}}` with the **absolute** path to the project's `docs/plans/` directory, computed as `"$(git rev-parse --show-toplevel)/docs/plans"`. Subagents do not necessarily inherit the calling session's cwd — passing a relative path can land the review in the wrong project root (especially when working inside a git worktree).
6. Replacing `{{REVIEW_SLUG}}` with `<YYYY-MM-DD>-<branch-or-cwd>-review` where:
   - `<YYYY-MM-DD>` is today's date
   - `<branch-or-cwd>` is the current branch name if it isn't `main`/`master`/`HEAD`, otherwise the basename of the project root
   - Replace any `/` in the branch name with `-` so the slug stays a single filename (e.g., `feature/auth` → `feature-auth`). Slashes would land the file in an unintended subdirectory or fail the write.

If `docs/plans/` does not exist, create it (`mkdir -p`) before dispatch — the agent only has `Write`, not directory-creation duties.

### 4. Dispatch the reviewer subagent

Use the Agent tool with `subagent_type: "my:code-reviewer"` and the composed prompt as the `prompt` field. Set `description: "Code review"`. Do not run the agent in the background — the user is waiting for the verdict.

### 5. Surface the result

The agent writes its review to `docs/plans/{{REVIEW_SLUG}}.md`. After dispatch returns:

1. Confirm the file exists at that path. If not, surface the agent's text output verbatim and flag that the file write did not happen.
2. Print a one-line pointer to the file: `Review written to docs/plans/<filename>.`
3. If the review's verdict is `Problematic` or contains any `Critical` issues, also print a two-line summary of the top finding.

## Worked example: default invocation, no args

```
1. Args is empty — RANGE, PLAN_PATH, LANGUAGE_OVERRIDE, DESCRIPTION all empty.
2. Bash:  ls composer.json artisan pyproject.toml uv.lock package.json tsconfig.json 2>/dev/null
   → none match → language = generic
3. Bash:  git diff
   Bash:  git diff --staged
   Bash:  git ls-files --others --exclude-standard
   → For each untracked file: git diff --no-index /dev/null <path>
   → Concatenate into DIFF
4. Read:  my-plugin/skills/code-review/code-reviewer-prompt.md (skip the header above the first `---`, take the body)
   Read:  my-plugin/skills/code-review/language/generic.md
5. Bash:  git rev-parse --show-toplevel
   → PLAN_DIRECTORY = "<that path>/docs/plans"
   Bash:  mkdir -p "$PLAN_DIRECTORY"
   Bash:  git branch --show-current
   → Substitute into REVIEW_SLUG (replace any `/` with `-`)
   → Substitute LANGUAGE_FILE, DIFF, PLAN_DIRECTORY, REVIEW_SLUG; PLAN_ALIGNMENT = ""
6. Agent: subagent_type="my:code-reviewer", description="Code review", prompt=<the composed text>
7. Confirm <PLAN_DIRECTORY>/<REVIEW_SLUG>.md exists. Print pointer.
```

The example is the canonical execution trace — follow it literally for the no-args case. Range mode swaps step 3 for `git diff $RANGE` + `git log $RANGE --oneline`. Plan-alignment mode adds the substitution for `PLAN_ALIGNMENT` (otherwise empty string).
