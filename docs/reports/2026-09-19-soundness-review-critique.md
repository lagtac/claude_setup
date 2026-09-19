# Critique: `my:soundness-review`, efficiency and clarity

**Status:** current, 2026-09-19. Findings on how clear and how costly the skill is; no fix is planned yet.

## How to read this

- **Subject:** `my-plugin/skills/soundness-review/SKILL.md` (226 lines),
  `my-plugin/skills/soundness-review/code-reviewer-prompt.md` (119 lines) and
  `my-plugin/agents/code-reviewer.md` (24 lines).
- **Earlier audit:** `docs/plans/2026-09-07-soundness-review-audit.md`. It asked whether the skill
  can catch bugs and architectural mistakes. Commits `4166d72`, `099654d` and `2c459be` answered
  it. This report asks three different questions: is the skill efficient, does it confuse the
  agent, and is it vague.
- **Method:** all three files were read in full. No review was dispatched, so the two findings in
  "Mismatches to check" are not confirmed.
- **Context:** the findings about project fit come from a session in
  `zitamu/real-estate-webapp`, whose `CLAUDE.local.md` changed the review workflow on 2026-09-19.

## Short answer

- **Confusing: yes, in four places.** Each of the four gives the agent two instructions that
  cannot both be followed (C1 to C4).
- **Vague: in several smaller places.** Most are wording left over from earlier refactors (V1 to
  V6).
- **Efficient: no.** The main session retypes the whole diff into the reviewer's prompt, and the
  same rules exist in three copies (E1 to E3).

## Contradictions that change behaviour

### C1. The example to "follow literally" breaks the rule it illustrates

`SKILL.md:63` says not to run `git diff` and `git diff --staged` separately, and explains why:
their line numbers do not compose. The plan-review worked example at `SKILL.md:218` runs exactly
that (`git diff / --staged / ls-files`). `SKILL.md:212` says the worked examples are the canonical
trace to follow literally. A model that follows instructions literally gets two opposite orders,
and the wrong one is labelled canonical.

**Fix:** change line 218 to `git diff HEAD + ls-files`.

### C2. The N/A rows have no place in the output

Both criteria blocks (`SKILL.md:122` and `:134`) say to mark an inapplicable dimension "**N/A**
with a one-line reason in the dual-perspective tables". Those tables
(`code-reviewer-prompt.md:90` and `:98`) have the columns `Aspect | Evidence | Strength` and
`Aspect | Evidence | Severity`. Neither has a slot for N/A. `code-reviewer-prompt.md:94` then says
N/A rows "still appear" when the first table is replaced by `None material.`, but not where.

**Fix:** give N/A dimensions their own short list, for example `### Dimensions not applicable`,
and point both criteria blocks at it.

### C3. `DESCRIPTION` changes the output, but the mode table ignores it

Step 0 collects free text into `DESCRIPTION`. The table in step 1a (`SKILL.md:78` to `:84`) keys
only on `PLAN_PATH` and the payload. Its row "no plan, non-empty payload" says "Plain diff
review". Step 2 (`SKILL.md:107`) then adds the plan-alignment block whenever a description was
supplied, so the table's label is wrong for that case. A description with an empty payload and no
plan stops with "No changes to review", and the description is dropped without a word.

**Fix:** add a `DESCRIPTION` column to the table, or key the alignment block on the table row
instead of on step 2's own condition.

### C4. Unsure findings are both kept and dropped

`code-reviewer-prompt.md:31` says: if unsure whether something is an issue, do not suppress it;
put it under "Needs Investigation". `code-reviewer-prompt.md:65` says: a finding that fails the
surfacing table is dropped silently. A Suggestion at Low confidence is covered by both rules.

**Fix:** say which rule wins. One option: "Needs Investigation" is for questions the reviewer
could not check, and the surfacing table is for findings it did check.

## Vague or unclear wording

### V1. Leftover words from earlier refactors

`SKILL.md` refers to versions the reader never saw: "this is the current text, preserved" (`:120`),
"(unchanged)" (`:113`, `:115`), "the existing `## Plan Alignment` block" (`:107`) and "current
text" (`:143`). "Unchanged" has no meaning without the earlier version. The "existing" block is
first used at line 107 and defined at line 155.

**Fix:** delete the words, and move the Plan Alignment block above the substitution list.

### V2. The `>` quote markers

Every `{{CRITERIA}}` and `{{MODE_OUTPUT_SECTION}}` block (`SKILL.md:122` to `:153`) is written as
a blockquote. The composition steps (`SKILL.md:173` to `:177`) say only "replace". They do not say
whether to remove the `> ` before substitution.

**Fix:** move the blocks into fenced sections, or say "remove the leading `> `".

### V3. Step 0 token rules

- "Two SHA-shaped tokens appearing together" and "or sub-token" are not defined.
- Any `.md` file that exists becomes `PLAN_PATH`, including `README.md` or `CHANGELOG.md`.
- Two `.md` paths have no rule.
- A single SHA becomes description text, with no note to the user.

### V4. An empty range plus a plan silently becomes a plan review

The table row at `SKILL.md:81` says: plan set and payload empty, so review the plan and "ignore
`RANGE`". If the range is empty because of a typo in a branch name, the user asked for a diff
check and gets a plan review instead.

**Fix:** when `RANGE` is set and empty, stop with `Range <RANGE> is empty.` whatever the plan.

### V5. The verdict values and step 4

`Sound`, `Mixed` and `Problematic` have no definitions, so the line between the last two is the
model's guess. Step 4.3 (`SKILL.md:191`) needs the verdict, but does not say whether to read it
from the file or from the agent's summary.

### V6. The review filename in range mode

The slug rule (`SKILL.md:177`) uses the current branch, or the project folder name on `main`. A
range review run from the main checkout, such as `main..feature-x`, is therefore named after the
project folder, not after `feature-x`.

**Fix:** in range mode, name the slug after `TIP`.

## Efficiency

### E1. The diff passes through the main session twice

The main session reads the whole diff as Bash output. It then writes the diff again, token by
token, into the Agent call's `prompt`, together with about 120 lines of template. Output tokens
are the slowest part of a model call. A 2000-line diff, which the size guard allows, means tens
of thousands of retyped tokens. Retyping also lets the model change the diff by mistake.

The rule "do not re-capture the subject" (`code-reviewer-prompt.md:35`) exists so that the
reviewer judges a fixed input. A file gives the same guarantee.

**Fix:** write the payload to a scratch file, and pass the path under `## Subject Under Review`.
The template itself could also be read by the agent from disk, so only the substituted values
travel in the prompt.

### E2. The same rules exist in three copies

- The "Required widening" grep paragraph is word for word the same in `agents/code-reviewer.md:18`
  and `code-reviewer-prompt.md:37`.
- The plan-grounding rule is in `agents/code-reviewer.md:19`, `code-reviewer-prompt.md:38` and
  plan criterion 5 (`SKILL.md:140`).
- `code-reviewer-prompt.md:13` names a third copy of the surfacing rules in
  `my-plugin/skills/spec-review/spec-reviewer-prompt.md`.

The subagent reads each rule twice, and every edit must be made in up to three places. The
2026-09-07 audit's first finding was a drift between two of these copies.

**Fix:** keep the rules in the dispatch prompt only. Cut the agent file to its contract bullets:
do not re-capture, use the given criteria and schema, write the file.

### E3. One Bash call per untracked file

Step 1 (`SKILL.md:65`) runs `git diff --no-index` once for each untracked file. One loop in a
single Bash call does the same work.

## Mismatches to check

### M1. The granted tools and the warnings disagree

`agents/code-reviewer.md:4` grants `Read, Grep, Glob, Bash, Write, LSP, ToolSearch`. The prompt
warns four times that `Grep`, `Glob` or `LSP` "may be absent" (`code-reviewer-prompt.md:37`, `:38`,
`SKILL.md:140`, `agents/code-reviewer.md:19`). Commit `2c459be` added the warnings on purpose. The
session that wrote this report had no `Grep` or `Glob` tool, and `LSP` there had to be loaded
through `ToolSearch` first. So the grant is probably the wrong half.

**Check:** dispatch `my:code-reviewer` once and list the tools it receives. Then cut the grant to
what arrives, and state the fallback once.

### M2. A parallel-review wrapper nests two subagents

`real-estate-webapp/CLAUDE.local.md` now says to run each end-of-branch review inside its own
`Agent` subagent, all in one message. Step 3 of this skill starts a further subagent
(`my:code-reviewer`), so the review runs two levels deep. Commit `af086f1` records that this
works since Claude Code v2.1.172, when the wrapper's `tools:` line lists `Agent`, up to
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`. A `general-purpose` wrapper, which gets all tools, should
therefore be able to dispatch the reviewer. If the wrapper lacks `Agent`, it will likely write
the review itself, without this prompt, and nothing will say so.

**Check:** run the wrapper once, and confirm that the review file has this template's sections.

## Fit with projects that use it

### F1. The report fails strict doc rules

The output template (`code-reviewer-prompt.md:71` to `:115`) starts at `### Change Summary`. It
has no H1 title and no `**Status:**` line. `GLOBAL-rules/docs-layout.md` requires a status line
(`review of <file>`) in every file in `docs/plans/`, and markdownlint flags the missing H1 (MD041).
So every review needs a manual fix before it can be committed.

**Fix:** open the template with `# Review: <subject>` and a `**Status:** review of <file>, <date>.`
line.

### F2. Working-tree mode picks up unrelated files

In a shared main checkout, the default mode adds every untracked file to the payload: tool output
folders such as `.playwright-mcp/`, backup copies, and other sessions' drafts. Binary files add
`Binary files differ` lines.

**Fix:** list the untracked files to the user before dispatch, or skip untracked files outside
the paths that the tracked diff touches.

### F3. The trigger list is broader than the newest project rule

The skill's `description` lists "before merging" and "after finishing a task" as triggers. As of
2026-09-19, `real-estate-webapp/CLAUDE.local.md` runs this skill only on a branch built from a
spec written for that branch. This is not a defect in the skill. It means the description will
keep offering the skill in cases that project has ruled out.
