---
name: soundness-review
description: >
  Dual-perspective soundness judgment with anti-sycophancy framing and severity-conditioned
  surfacing, plus optional plan/spec alignment — written as a durable report to docs/plans/.
  Use when the user asks "is this change sound?", for a balanced for/against verdict, to check
  a diff against a plan, before merging, or after finishing a task. Defaults to the working-tree
  diff; pass a `BASE..HEAD` range for a committed range, and a `docs/plans/*.md` path to enable
  plan-alignment. NOT a bug scanner — low-level bug-finding, `--fix`, and deep `ultra` review are
  delegated to the built-in `/code-review`. Pointing it at a `.md` plan with a clean working tree
  reviews the plan itself (grounded against the repo + snippet-logic check) instead of a diff;
  with uncommitted changes and no range, it asks which of the two to review.
  Specs (`*-spec.md`) are not reviewed on their own here — use `my:spec-review`; checking a diff
  against a spec still belongs here.
---

# Soundness Review

Dispatch a fresh-context reviewer subagent to render a **soundness judgment** of the diff specified by the caller — the working-tree diff by default, or a committed range (`BASE..HEAD`) when invoked pre-merge. The reviewer produces dual-perspective output (arguments for *and* against) with severity-conditioned confidence labels and a reasoning paragraph before its verdict — no rubber-stamping — and an optional plan-alignment check.

This skill is deliberately **not** a bug scanner. Line-level bug-finding (secrets, injection, N+1, validation gaps, style, test coverage) and auto-fix are the built-in `/code-review`'s job — route there for those. This skill's value is the balanced judgment, the plan-alignment check, and the durable `docs/plans/` report.

The methodology, judgment dimensions, and output schema are authored once here and in `code-reviewer-prompt.md`. The agent receives the full prompt at dispatch time, and the diff or plan as a file it reads; it must not capture the diff itself.

## Steps

### 0. Classify the freeform args string

The skill's args field is a single freeform string. Split it on whitespace and classify each token by its shape. Match the rows top to bottom; the first match wins:

| Token shape | Variable |
|---|---|
| `<ref>..<ref>` or `<ref>...<ref>` (e.g. `main..HEAD`, `abc1234..def5678`) | `RANGE` |
| Two tokens next to each other that each match `^[0-9a-f]{7,40}$` | `RANGE`, joined with `..` |
| A path ending in `.md` that exists on disk and sits under a `docs/plans/` directory | `PLAN_PATH` |
| Anything else (free prose) | append to `DESCRIPTION` |

Some tokens need a note to the user, printed before step 1:

- One SHA-shaped token on its own: add it to `DESCRIPTION` and print `(arg "<token>" looks like a commit; treated as description. Pass <token>..HEAD for a range.)`
- A `.md` path that does not exist, or exists outside `docs/plans/` (such as `README.md`): add it to `DESCRIPTION` and print `(arg "<token>" treated as description; expected an existing plan under docs/plans/.)`
- Two or more tokens that qualify as `PLAN_PATH`: stop with `Pass one plan file; got <first> and <second>.` Do not dispatch.

If args is empty, all three variables are empty — the skill runs in defaults (working-tree diff, no plan-alignment block).

### 1. Capture the diff

Write the payload straight into a file with shell redirection. Do not print it, read it into the conversation, or retype it: the reviewer reads the file itself. Retyping a long diff into the dispatch prompt costs tens of thousands of output tokens and can change the diff by mistake.

First make a work directory. It must be an absolute path, because the reviewer does not share your working directory:

```bash
WORK_DIR="<scratchpad>/soundness-review/$(date +%Y%m%d-%H%M%S)"   # <scratchpad> = the session's scratchpad directory from the system prompt
mkdir -p "$WORK_DIR"                                              # no scratchpad: WORK_DIR="$(mktemp -d)"
PAYLOAD="$WORK_DIR/payload.diff"
```

**If `RANGE` is set** (committed-range mode):

Split `RANGE` on its `..` or `...` separator into `BASE` and `TIP` (an empty `TIP` means `HEAD`), then:

```bash
git diff "$(git merge-base "$BASE" "$TIP")" "$TIP" > "$PAYLOAD"
if [ -s "$PAYLOAD" ]; then
  printf '\n--- COMMITS IN RANGE ---\n' >> "$PAYLOAD"
  git log "$RANGE" --oneline >> "$PAYLOAD"
fi
```

Use the **merge base**, not the literal range. `git diff A..B` is the two-endpoint diff — identical to `git diff A B` — so on a branch that has diverged from its base it renders base-only commits as reversions the branch never made. Only the merge base gives the branch's own changes. (`git log "$RANGE"` is correct on two dots and stays as written; the asymmetry is deliberate.)

The diff is the primary payload; the log is appended after the diff under a `--- COMMITS IN RANGE ---` separator so the reviewer sees the commit boundary structure (one logical change vs many). The log is appended only when the diff is non-empty, so an empty range leaves an empty file.

**Otherwise** (working-tree mode, default):

```bash
git diff HEAD > "$PAYLOAD"
git ls-files --others --exclude-standard
```

`git diff HEAD` covers staged **and** unstaged changes to tracked files in one view. Do not also run `git diff` and `git diff --staged` separately: a file that is both staged and further modified yields two hunk sets whose line numbers do not compose, and the reviewer cannot tell which state it is judging.

The second command lists untracked files. Turn all of them into new-file diffs in one Bash call:

```bash
git ls-files --others --exclude-standard -z | while IFS= read -r -d '' f; do git diff --no-index /dev/null "$f"; done >> "$PAYLOAD"
```

This appends canonical new-file diff output (`diff --git`, `new file mode`, `--- /dev/null`, `+++ b/<path>`, `@@`, content) to the `git diff HEAD` output. (`git ls-files --others` stops listing a file once it is staged, so the two commands never cover the same file twice.) Do **not** hand-construct the diff headers — `git diff --no-index` does this correctly and consistently.

If there are untracked files, print them before dispatch: `(Including <N> untracked files: <paths>. If any do not belong to this change, add them to .gitignore or move them, and run again.)` In a shared checkout, untracked files can be tool output or another session's drafts, and the reviewer would judge them as part of the change.

The payload is empty when `[ -s "$PAYLOAD" ]` fails. Whether it is empty or not, proceed to step 1a. Its table decides when an empty payload stops the skill and what message to print.

**Size guard.** Count the payload's lines (`wc -l < "$PAYLOAD"`). If it exceeds **2000**, do not stop — warn and proceed, so the partial coverage is visible rather than silent:

- Print to the user: `(Payload is <N> lines; the reviewer's coverage may be uneven. Narrow with a tighter range or a path-scoped diff for a closer read.)`
- Add this line to the `{{SUBJECT}}` block at substitution time, after its first sentence: `Note: this payload is <N> lines. If you cannot assess all of it at the same depth, say so explicitly under "Needs Investigation" and name which parts you covered shallowly — do not present uneven coverage as complete.`

### 1a. Detect review mode

Let `PLAN_PATH` be from step 0 and `payload` be the captured diff. Set `MODE`:

| `PLAN_PATH` | `DESCRIPTION` | `payload` | `MODE` | Action |
|---|---|---|---|---|
| any, with `RANGE` set | any | empty | — | Stop: `Range <RANGE> is empty.` This row is checked first, so a mistyped range never turns into a plan review. |
| set, ends in `-spec.md` | any | empty | — | Stop: `This is a spec. Run my:spec-review <PLAN_PATH> instead.` Do not dispatch. |
| set | any | empty | `plan-review` | Subject is the plan document; ignore `DESCRIPTION` if set, and print `(description ignored: a plan review has no diff to check it against)` when `DESCRIPTION` is set. |
| set, with `RANGE` unset | any | non-empty | ask | The args do not say whether to review the plan or the changes. **Ask the question below**, then continue with the row the answer picks. |
| set | any | non-empty | `diff-review` with alignment | Build the Plan Alignment block (step 2) from the plan, and the description if set. |
| unset | set | non-empty | `diff-review` with alignment | Build the Plan Alignment block (step 2) from the description alone. |
| unset | unset | non-empty | `diff-review` | Plain diff review, no alignment block. |
| unset | any | empty | — | Stop: `No changes to review.` When `DESCRIPTION` is set, add: `(The description was not used: there are no changes to check it against.)` |

Rows are matched top to bottom; the first match wins. A spec with a non-empty payload still falls through to `diff-review`, which checks the change against the spec.

**The question.** Ask it with the `AskUserQuestion` tool, one question, header `Subject`:

- Question: `The working tree has uncommitted changes (<N> changed files, <U> of them untracked). What should I review?` Count `<N>` with `grep -c '^diff --git' "$PAYLOAD"`, and take `<U>` from the untracked list in step 1.
- Option 1: `The plan itself` — description `Review <PLAN_PATH> as a plan, grounded against the repo. The changes are ignored.` When `PLAN_PATH` ends in `-spec.md`, use `The spec itself` with description `Stop here and run my:spec-review <PLAN_PATH>.`
- Option 2: `Changes against the plan` — description `Review the uncommitted diff and check it against <PLAN_PATH>.`

The answer decides the row:

- **The plan itself:** continue as the `plan-review` row above, as if the payload were empty. For a spec, stop with `This is a spec. Run my:spec-review <PLAN_PATH> instead.`
- **Changes against the plan:** continue as the `diff-review` with alignment row.
- **A typed answer:** if it clearly means one of the two options, use that option. Otherwise stop and print it back; do not guess a mode.

If `AskUserQuestion` is not in your tool list (for example in a non-interactive `claude -p` run, or inside a subagent), do not stop. Use **Changes against the plan**, and print: `(Working tree is dirty, so I'm reviewing the diff against <PLAN_PATH>. Commit or stash to review the plan document itself.)`

With `RANGE` set, the range already says what to review, so there is no question: the diff of the range is checked against the plan.

### 2. Build the dispatch prompt

Read `code-reviewer-prompt.md` from this skill's directory.

Substitute, by `MODE`:

- `{{MODE}}` → `plan-review` or `diff-review`.
- `{{SUBJECT}}`:
  - diff-review → ``The combined diff to review is the file `<PAYLOAD>` (<N> lines).`` with the absolute path.
  - plan-review → first copy the plan, so the reviewer judges a fixed snapshot: `cp "$PLAN_PATH" "$WORK_DIR/plan.md"`. Then ``The plan document to review, `<PLAN_PATH>`, is copied to `<WORK_DIR>/plan.md` (<N> lines).`` with the absolute path.
  - In **either** mode, if the size guard in step 1 tripped, its `Note: this payload is <N> lines…` line follows that sentence.
  - Never paste the diff or the plan text itself into the prompt.
- `{{CRITERIA}}`:
  - diff-review → the **Diff criteria** block below.
  - plan-review → the **Plan criteria** block below.
- `{{PLAN_ALIGNMENT}}`:
  - a step 1a row marked `diff-review` with alignment → the `## Plan Alignment` block built at the end of this step.
  - otherwise (including all plan-review) → empty string.
- `{{MODE_OUTPUT_SECTION}}`:
  - diff-review with alignment → the **Plan Alignment output** block below.
  - plan-review → the **Grounding output** block below.
  - plain diff-review → empty string.
- `{{PLAN_DIRECTORY}}` → `"$(git rev-parse --show-toplevel)/docs/plans"`.
- `{{REPO_ROOT}}` → `"$(git rev-parse --show-toplevel)"`, absolute.
- `{{SUBJECT_NAME}}`:
  - plan-review → `PLAN_PATH`.
  - diff-review in range mode → `RANGE`.
  - diff-review in working-tree mode → `working tree of <current branch>`.
- `{{REVIEW_SLUG}}`:
  - diff-review → `<YYYY-MM-DD>-<branch-or-cwd>-review` (see step 4 of the composition below).
  - plan-review → `<plan-basename-without-.md>-plan-review` (e.g. `docs/plans/2026-05-28-foo.md` → `2026-05-28-foo-plan-review`).

**Collision rule (both modes).** Before substituting, check whether `{{PLAN_DIRECTORY}}/{{REVIEW_SLUG}}.md` already exists. If it does, append `-2` (then `-3`, and so on) until the path is free, and use that. Neither slug is unique on its own: diff-review repeats for the same branch on the same day, and plan-review's date comes from the *plan's* filename and never changes, so every re-review of a plan would otherwise overwrite the last one. Reviews are a record — never overwrite a previous one.

**Diff criteria** (`{{CRITERIA}}` for diff-review):

> Assess the change against these soundness dimensions — **not** a line-level bug scan. Mark genuinely-inapplicable dimensions as **N/A** with a one-line reason under `## Not Applicable` in the output — do not silently skip.
>
> 1. **Solves the stated problem.** The change accomplishes its intent (and the supplied plan, if any). Judge whether it does the right thing, not whether each line is bug-free.
> 2. **Architecture & pattern fit.** Follows existing conventions, sits at the right abstraction level, respects layer boundaries; no new abstraction where three similar lines would do. You cannot judge this from the diff hunks alone — read every file the payload touches in full, plus a sibling file or two, before assessing this dimension or dimension 3.
> 3. **Soundness of approach.** Treats the root cause, not a symptom. No bandaid `try/catch`, no backwards-compatibility cruft (renamed-but-still-exported symbols, dual "migration" code paths), no fallback logic that silently masks a failure.
> 4. **Risk & blast radius.** What is hard to reverse (schema, contract, data migration), what could break elsewhere, what needs manual verification or a deploy step. When the diff **removes or renames a symbol used across files**, sweep the whole repo for orphaned callers — a plain text search for the name token, since string-literal references (route/event names, config/DI keys, ORM eager-load paths, templates) are invisible to symbol tools. An orphaned caller is a **Critical** soundness finding, not an out-of-scope line-level bug.
> 5. **Plan alignment.** When a `## Plan Alignment` block was supplied above, treat every deviation between the diff and the plan as a finding.
>
> **Out of scope — do not duplicate the built-in reviewer.** Low-level bug-finding (exposed secrets, injection, N+1 queries, input-validation gaps, style/lint, test-coverage line items) is the job of the built-in `/code-review` (which also offers `--fix` and `ultra`). Do not enumerate those here. Only surface such an item if it directly undermines one of the judgment dimensions above (e.g., a missing authorization check that makes the *approach* unsound) — and say which dimension it implicates.

**Plan criteria** (`{{CRITERIA}}` for plan-review):

> Assess the plan against these dimensions — judge whether it is **ready to implement**, not whether its code snippets compile. Mark genuinely-inapplicable dimensions as **N/A** with a one-line reason under `## Not Applicable` in the output — do not silently skip.
>
> 1. **Completeness & snippet self-sufficiency.** The plan covers the whole stated goal: no missing steps, unhandled cases, or undefined terms. A cold session could execute it without inventing requirements. This explicitly includes the snippets: any snippet meant to be executed must be runnable without the executor inventing imports, helpers, fixtures, or symbols the plan never establishes in an earlier step. A genuine omission — e.g. a snippet that references an import or helper the plan never defines — is a **completeness finding** (it forces the executor to guess), distinct from a *clearly-marked elision* (see dimension 6), which is fine.
> 2. **Sequencing & atomicity.** Steps are ordered so dependencies land before dependents; each step is a coherent, single-purpose commit. Where the plan implements behaviour, it follows Red → Green → Refactor (tests before implementation), per the project's plan standard.
> 3. **Test-strategy adequacy.** The planned tests actually pin the intended behaviour, at the right level (unit / feature / integration), and would fail for the right reason before the implementation exists. Flag tests that assert nothing meaningful or mock the code under test — specifically: matches-nothing filters/globs, degenerate parameters that make the assertion vacuous, assertions against assumed filenames/paths rather than the real producing code, and references to non-existent fixtures. A change to a public surface (route, relationship, serialized contract, CLI) needs at least one end-to-end test of the real surface, not only unit tests.
> 4. **Risk & reversibility.** Hard-to-reverse steps (schema changes, API/data contracts, migrations, deletions) are identified with a mitigation or rollback note; blast radius is named. Flag unflagged irreversible steps.
> 5. **Grounding (verify against the repo).** Use `Read` plus `Bash` searches (`grep -rn`, `find`) to confirm the plan's claims: referenced files, symbols, routes, and commands exist; stated assumptions about current behaviour hold; proposed patterns match existing conventions. Every stale reference or false assumption is a finding citing `plan-section` ↔ `repo file:line` (or "(not found)"). **Reference completeness:** for any symbol the plan removes or renames, independently sweep the repo and verify every caller appears in "Files to Modify." Run a plain text search for the name token — it also finds string-literal references (routes, DI keys, ORM eager-loads, templates), which symbol tools miss. Report that the sweep was text-only. A missing caller is a completeness finding; do not trust the plan's file list.
> 6. **Snippet logic.** Inspect embedded test/implementation snippets for **logic** errors only: off-by-ones, a test asserting the wrong thing, a snippet that cannot achieve its step's stated goal, contradictory snippets across steps. **Out of scope:** snippets the plan *clearly marks as abbreviated* (`…`, "imports omitted", "sketch"), and pure formatting/style. Do **not** flag those, and do **not** run a lint/type/style pass — that is the built-in `/code-review`'s job on real code. Note the boundary with dimension 1: a *clearly-marked elision* is fine here, but a snippet presented as executable that omits an import/helper the plan never defines is a completeness finding under dimension 1 — because a cold executor would be forced to invent it. The test is "would the executor have to guess?", not "is a line missing".

**Plan Alignment output** (`{{MODE_OUTPUT_SECTION}}` for diff-review with alignment):

> ## Plan Alignment
>
> State whether the implementation matches the supplied description/plan, then enumerate any deviations as bullets — each referencing a `file:line` or "(missing)" with a one-line note. Surface deviations as findings in the Issues table using the standard severity / confidence labels.

**Grounding output** (`{{MODE_OUTPUT_SECTION}}` for plan-review):

> ## Grounding
>
> State whether the plan's references and assumptions hold against the repo. Enumerate each stale reference / false assumption as a bullet citing the plan location ↔ `repo file:line` (or "(not found)"). Surface material ones as findings in the Issues table. Omit if the plan made no checkable claims.

For diff-review with a description or plan supplied, **build a plan-alignment block** as follows. When `PLAN_PATH` is set, first copy the plan: `cp "$PLAN_PATH" "$WORK_DIR/plan.md"`. Keep the lines marked "if … set" only when that value is set, and drop the marker text:

```markdown
## Plan Alignment

[if DESCRIPTION is set] The work this diff implements: <DESCRIPTION>

[if PLAN_PATH is set] The plan it implements is `<PLAN_PATH>`, copied to `<WORK_DIR>/plan.md`. Read that copy in full.

Apply a plan-alignment check in addition to the judgment dimensions: does the implementation match what was described? Are deviations justified or problematic? Is anything in the plan missing from the diff? Surface deviations as findings using the same severity / confidence labels.
```

If neither `DESCRIPTION` nor `PLAN_PATH` is set (or `MODE` is `plan-review`), the plan-alignment block is the empty string.

Compose the dispatch prompt by:
1. Starting with the contents of `code-reviewer-prompt.md` (skip the header above the first `---`, take the body)
2. Replacing `{{MODE}}`, `{{SUBJECT}}`, `{{SUBJECT_NAME}}`, `{{REPO_ROOT}}`, `{{CRITERIA}}`, `{{PLAN_ALIGNMENT}}`, `{{MODE_OUTPUT_SECTION}}` per the substitution rules above. Remove the leading `> ` from each quoted block you substitute. When a placeholder becomes an empty string, delete its whole line and the blank line after it, so the review has no double blank lines.
3. Replacing `{{PLAN_DIRECTORY}}` with the **absolute** path to the project's `docs/plans/` directory, computed as `"$(git rev-parse --show-toplevel)/docs/plans"`. Subagents do not necessarily inherit the calling session's cwd — passing a relative path can land the review in the wrong project root (especially when working inside a git worktree).
4. Replacing `{{REVIEW_SLUG}}` per the substitution rules above (diff-review: `<YYYY-MM-DD>-<branch-or-cwd>-review`; plan-review: `<plan-basename-without-.md>-plan-review`). For diff-review, `<branch-or-cwd>` is: in range mode, `TIP` when it is a branch name; otherwise the current branch name if it isn't `main`/`master`/`HEAD`; otherwise the basename of the project root. So `main..feature-x` run from the main checkout is named after `feature-x`. Replace any `/` in the branch name with `-` so the slug stays a single filename.

If `docs/plans/` does not exist, create it (`mkdir -p`) before dispatch — the agent only has `Write`, not directory-creation duties.

### 3. Dispatch the reviewer subagent

Use the Agent tool with `subagent_type: "my:code-reviewer"` and the composed prompt as the `prompt` field. Set `description: "Code review"`. Wait for the agent's result before step 4, and do nothing else until it arrives: the user is waiting for the verdict. If your Agent tool has a `run_in_background` parameter, leave it off; if subagents always run in the background, continue at step 4 when the completion notice arrives.

### 4. Surface the result

The agent writes its review to `docs/plans/{{REVIEW_SLUG}}.md`. After dispatch returns:

1. Confirm the file exists at that path. If not, surface the agent's text output verbatim and flag that the file write did not happen.
2. Print a one-line pointer to the file: `Review written to docs/plans/<filename>.`
3. Read the verdict from the review file's `**Assessment:**` line, not from the agent's summary. If it is `Problematic`, or the Issues table has any `Critical` row, also print a two-line summary of the top finding.

## Worked example: default invocation, no args

```
0. Args is empty — RANGE, PLAN_PATH, DESCRIPTION all empty.
1. Bash:  mkdir -p WORK_DIR; git diff HEAD > PAYLOAD
   Bash:  git ls-files --others --exclude-standard
   → One loop over the untracked files: git diff --no-index /dev/null <path> >> PAYLOAD; print their list
   Bash:  wc -l < PAYLOAD   (the diff itself is never read into the conversation)
2. Read:  plugins/my/skills/soundness-review/code-reviewer-prompt.md (skip the header above the first `---`, take the body)
   Bash:  git rev-parse --show-toplevel
   → PLAN_DIRECTORY = "<that path>/docs/plans"
   Bash:  mkdir -p "$PLAN_DIRECTORY"
   Bash:  git branch --show-current
   → Substitute into REVIEW_SLUG (replace any `/` with `-`)
   → Substitute MODE, SUBJECT, SUBJECT_NAME, REPO_ROOT, CRITERIA, PLAN_DIRECTORY, REVIEW_SLUG; PLAN_ALIGNMENT = "", MODE_OUTPUT_SECTION = ""
3. Agent: subagent_type="my:code-reviewer", description="Code review", prompt=<the composed text>
4. Confirm <PLAN_DIRECTORY>/<REVIEW_SLUG>.md exists. Print pointer.
```

The example is the canonical execution trace — follow it literally for the no-args case. Range mode swaps step 1 for the merge-base diff (`git diff "$(git merge-base "$BASE" "$TIP")" "$TIP" > PAYLOAD`) + `git log "$RANGE" --oneline >> PAYLOAD`. Plan-alignment mode adds the substitution for `PLAN_ALIGNMENT` (otherwise empty string).

## Worked example: plan-review (clean tree)

```
0. Args: docs/plans/2026-05-28-foo.md → PLAN_PATH set; RANGE/DESCRIPTION empty.
1. git diff HEAD + ls-files --others > PAYLOAD → payload EMPTY.
1a. PLAN_PATH set + payload empty → MODE = plan-review.
2. Read code-reviewer-prompt.md. Substitute:
   cp docs/plans/2026-05-28-foo.md WORK_DIR/plan.md
   MODE=plan-review; SUBJECT="…copied to <WORK_DIR>/plan.md (N lines)."; SUBJECT_NAME=docs/plans/2026-05-28-foo.md;
   CRITERIA=Plan criteria;
   PLAN_ALIGNMENT=""; MODE_OUTPUT_SECTION=Grounding output;
   REVIEW_SLUG=2026-05-28-foo-plan-review.
3. Agent: subagent_type="my:code-reviewer", prompt=<composed text>.
4. Confirm docs/plans/2026-05-28-foo-plan-review.md exists. Print pointer.
```
