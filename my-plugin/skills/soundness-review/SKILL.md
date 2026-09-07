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
  reviews the plan itself (grounded against the repo + snippet-logic check) instead of a diff.
---

# Code Review

Dispatch a fresh-context reviewer subagent to render a **soundness judgment** of the diff specified by the caller — the working-tree diff by default, or a committed range (`BASE..HEAD`) when invoked pre-merge. The reviewer produces dual-perspective output (arguments for *and* against) with severity-conditioned confidence labels and a reasoning paragraph before its verdict — no rubber-stamping — and an optional plan-alignment check.

This skill is deliberately **not** a bug scanner. Line-level bug-finding (secrets, injection, N+1, validation gaps, style, test coverage) and auto-fix are the built-in `/code-review`'s job — route there for those. This skill's value is the balanced judgment, the plan-alignment check, and the durable `docs/plans/` report.

The methodology, judgment dimensions, and output schema are authored once here and in `code-reviewer-prompt.md`. The agent receives the full prompt at dispatch time and must not improvise the diff.

## Steps

### 0. Classify the freeform args string

The skill's args field is a single freeform string. Classify each whitespace-separated token (or sub-token) by content shape:

| Token shape | Variable |
|---|---|
| `<ref>..<ref>` literal (e.g. `main..HEAD`, `abc1234..def5678`) | `RANGE` |
| Two SHA-shaped tokens (`[0-9a-f]{7,40}`) appearing together | `RANGE` (joined with `..`) |
| A path ending in `.md` that exists on disk | `PLAN_PATH` |
| Anything else (free prose) | append to `DESCRIPTION` |

If a token is ambiguous (e.g., a `.md` path that doesn't exist), prefer `DESCRIPTION` and surface a one-line note: `(arg "<token>" treated as description; expected file but not found)`.

If args is empty, all three variables are empty — the skill runs in defaults (working-tree diff, no plan-alignment block).

### 1. Capture the diff

**If `RANGE` is set** (committed-range mode):

Split `RANGE` on its `..` or `...` separator into `BASE` and `TIP` (an empty `TIP` means `HEAD`), then:

```bash
git diff "$(git merge-base "$BASE" "$TIP")" "$TIP"
git log "$RANGE" --oneline
```

Use the **merge base**, not the literal range. `git diff A..B` is the two-endpoint diff — identical to `git diff A B` — so on a branch that has diverged from its base it renders base-only commits as reversions the branch never made. Only the merge base gives the branch's own changes. (`git log "$RANGE"` is correct on two dots and stays as written; the asymmetry is deliberate.)

The diff is the primary payload; the log is appended after the diff under a `--- COMMITS IN RANGE ---` separator so the reviewer sees the commit boundary structure (one logical change vs many).

**Otherwise** (working-tree mode, default):

```bash
git diff
git diff --staged
git ls-files --others --exclude-standard
```

The third command lists untracked files; for each one, run `git diff --no-index /dev/null <path>` to produce canonical new-file diff output (`diff --git`, `new file mode`, `--- /dev/null`, `+++ b/<path>`, `@@`, content). Concatenate those onto the working-tree and staged diffs. Do **not** hand-construct the diff headers — `git diff --no-index` does this correctly and consistently.

If the resulting payload is empty and `PLAN_PATH` is unset, stop with a message: `No changes to review.` (working-tree mode) or `Range <RANGE> is empty.` (range mode). Otherwise, proceed to step 1a.

### 1a. Detect review mode

Let `PLAN_PATH` be from step 0 and `payload` be the captured diff. Set `MODE`:

| `PLAN_PATH` | `payload` | `MODE` | Action |
|---|---|---|---|
| set | empty | `plan-review` | Subject is the plan document; ignore `RANGE` if it was set. |
| set | non-empty | `diff-review` | Build the Plan Alignment block (step 2). **Print the nudge below to the user.** |
| unset | empty | — | Stop: `No changes to review.` (or `Range <RANGE> is empty.` if `RANGE` was set). |
| unset | non-empty | `diff-review` | Plain diff review. |

Nudge (print to the user, not into the dispatch prompt), when `PLAN_PATH` is set and `payload` is non-empty:

> `(Working tree is dirty, so I'm reviewing the diff against <PLAN_PATH>. Commit or stash to review the plan document itself.)`

### 2. Build the dispatch prompt

Read `code-reviewer-prompt.md` from this skill's directory.

Substitute, by `MODE`:

- `{{MODE}}` → `plan-review` or `diff-review`.
- `{{SUBJECT}}`:
  - diff-review → ``The combined diff to review:`` followed by a fenced ```diff block with the payload.
  - plan-review → ``The plan document to review (`<PLAN_PATH>`):`` followed by a fenced ```markdown block with the **full** contents of `PLAN_PATH`.
- `{{CRITERIA}}`:
  - diff-review → the **Diff criteria** block below.
  - plan-review → the **Plan criteria** block below.
- `{{PLAN_ALIGNMENT}}`:
  - diff-review *with* a description/plan supplied → the existing `## Plan Alignment` block.
  - otherwise (including all plan-review) → empty string.
- `{{MODE_OUTPUT_SECTION}}`:
  - diff-review with alignment → the **Plan Alignment output** block below.
  - plan-review → the **Grounding output** block below.
  - plain diff-review → empty string.
- `{{PLAN_DIRECTORY}}` → `"$(git rev-parse --show-toplevel)/docs/plans"` (unchanged).
- `{{REVIEW_SLUG}}`:
  - diff-review → `<YYYY-MM-DD>-<branch-or-cwd>-review` (unchanged; replace `/` in branch with `-`).
  - plan-review → `<plan-basename-without-.md>-plan-review` (e.g. `docs/plans/2026-05-28-foo.md` → `2026-05-28-foo-plan-review`).

**Diff criteria** (`{{CRITERIA}}` for diff-review — this is the current text, preserved):

> Assess the change against these soundness dimensions — **not** a line-level bug scan. Mark genuinely-inapplicable dimensions as **N/A** with a one-line reason in the dual-perspective tables — do not silently skip.
>
> 1. **Solves the stated problem.** The change accomplishes its intent (and the supplied plan, if any). Judge whether it does the right thing, not whether each line is bug-free.
> 2. **Architecture & pattern fit.** Follows existing conventions, sits at the right abstraction level, respects layer boundaries; no new abstraction where three similar lines would do. You cannot judge this from the diff hunks alone — read every file the payload touches in full, plus a sibling file or two, before assessing this dimension or dimension 3.
> 3. **Soundness of approach.** Treats the root cause, not a symptom. No bandaid `try/catch`, no backwards-compatibility cruft (renamed-but-still-exported symbols, dual "migration" code paths), no fallback logic that silently masks a failure.
> 4. **Risk & blast radius.** What is hard to reverse (schema, contract, data migration), what could break elsewhere, what needs manual verification or a deploy step. When the diff **removes or renames a symbol used across files**, sweep the whole repo for orphaned callers — a plain text search for the name token, since string-literal references (route/event names, config/DI keys, ORM eager-load paths, templates) are invisible to symbol tools. An orphaned caller is a **Critical** soundness finding, not an out-of-scope line-level bug.
> 5. **Plan alignment.** When a `## Plan Alignment` block was supplied above, treat every deviation between the diff and the plan as a finding.
>
> **Out of scope — do not duplicate the built-in reviewer.** Low-level bug-finding (exposed secrets, injection, N+1 queries, input-validation gaps, style/lint, test-coverage line items) is the job of the built-in `/code-review` (which also offers `--fix` and `ultra`). Do not enumerate those here. Only surface such an item if it directly undermines one of the judgment dimensions above (e.g., a missing authorization check that makes the *approach* unsound) — and say which dimension it implicates.

**Plan criteria** (`{{CRITERIA}}` for plan-review):

> Assess the plan against these dimensions — judge whether it is **ready to implement**, not whether its code snippets compile. Mark genuinely-inapplicable dimensions as **N/A** with a one-line reason in the dual-perspective tables — do not silently skip.
>
> 1. **Completeness & snippet self-sufficiency.** The plan covers the whole stated goal: no missing steps, unhandled cases, or undefined terms. A cold session could execute it without inventing requirements. This explicitly includes the snippets: any snippet meant to be executed must be runnable without the executor inventing imports, helpers, fixtures, or symbols the plan never establishes in an earlier step. A genuine omission — e.g. a snippet that references an import or helper the plan never defines — is a **completeness finding** (it forces the executor to guess), distinct from a *clearly-marked elision* (see dimension 6), which is fine.
> 2. **Sequencing & atomicity.** Steps are ordered so dependencies land before dependents; each step is a coherent, single-purpose commit. Where the plan implements behaviour, it follows Red → Green → Refactor (tests before implementation), per the project's plan standard.
> 3. **Test-strategy adequacy.** The planned tests actually pin the intended behaviour, at the right level (unit / feature / integration), and would fail for the right reason before the implementation exists. Flag tests that assert nothing meaningful or mock the code under test — specifically: matches-nothing filters/globs, degenerate parameters that make the assertion vacuous, assertions against assumed filenames/paths rather than the real producing code, and references to non-existent fixtures. A change to a public surface (route, relationship, serialized contract, CLI) needs at least one end-to-end test of the real surface, not only unit tests.
> 4. **Risk & reversibility.** Hard-to-reverse steps (schema changes, API/data contracts, migrations, deletions) are identified with a mitigation or rollback note; blast radius is named. Flag unflagged irreversible steps.
> 5. **Grounding (verify against the repo).** Use Read / Grep / Glob to confirm the plan's claims: referenced files, symbols, routes, and commands exist; stated assumptions about current behaviour hold; proposed patterns match existing conventions. Every stale reference or false assumption is a finding citing `plan-section` ↔ `repo file:line` (or "(not found)"). **Reference completeness:** for any symbol the plan removes or renames, independently sweep the repo and verify every caller appears in "Files to Modify." Always run a plain text search for the name token — string-literal references (routes, DI keys, ORM eager-loads, templates) are invisible to symbol tools. Additionally try `LSP` `findReferences`; it errors when no language server covers the file type, and in that case report that the sweep was text-only rather than implying a symbol sweep ran. A missing caller is a completeness finding; do not trust the plan's file list.
> 6. **Snippet logic.** Inspect embedded test/implementation snippets for **logic** errors only: off-by-ones, a test asserting the wrong thing, a snippet that cannot achieve its step's stated goal, contradictory snippets across steps. **Out of scope:** snippets the plan *clearly marks as abbreviated* (`…`, "imports omitted", "sketch"), and pure formatting/style. Do **not** flag those, and do **not** run a lint/type/style pass — that is the built-in `/code-review`'s job on real code. Note the boundary with dimension 1: a *clearly-marked elision* is fine here, but a snippet presented as executable that omits an import/helper the plan never defines is a completeness finding under dimension 1 — because a cold executor would be forced to invent it. The test is "would the executor have to guess?", not "is a line missing".

**Plan Alignment output** (`{{MODE_OUTPUT_SECTION}}` for diff-review with alignment — current text):

> ### Plan Alignment
>
> State whether the implementation matches the supplied description/plan, then enumerate any deviations as bullets — each referencing a `file:line` or "(missing)" with a one-line note. Surface deviations as findings in the Issues table using the standard severity / confidence labels.

**Grounding output** (`{{MODE_OUTPUT_SECTION}}` for plan-review):

> ### Grounding
>
> State whether the plan's references and assumptions hold against the repo. Enumerate each stale reference / false assumption as a bullet citing the plan location ↔ `repo file:line` (or "(not found)"). Surface material ones as findings in the Issues table. Omit if the plan made no checkable claims.

For diff-review with a description or plan supplied, **build a plan-alignment block** as follows:

```markdown
## Plan Alignment

The work this diff implements:

<DESCRIPTION (if set, otherwise omit this paragraph)>

The plan/requirements:

<contents of PLAN_PATH file (if set, otherwise omit this paragraph)>

Apply a plan-alignment check in addition to the judgment dimensions: does the implementation match what was described? Are deviations justified or problematic? Is anything in the plan missing from the diff? Surface deviations as findings using the same severity / confidence labels.
```

If neither `DESCRIPTION` nor `PLAN_PATH` is set (or `MODE` is `plan-review`), the plan-alignment block is the empty string.

Compose the dispatch prompt by:
1. Starting with the contents of `code-reviewer-prompt.md` (skip the header above the first `---`, take the body)
2. Replacing `{{MODE}}`, `{{SUBJECT}}`, `{{CRITERIA}}`, `{{PLAN_ALIGNMENT}}`, `{{MODE_OUTPUT_SECTION}}` per the substitution rules above
3. Replacing `{{PLAN_DIRECTORY}}` with the **absolute** path to the project's `docs/plans/` directory, computed as `"$(git rev-parse --show-toplevel)/docs/plans"`. Subagents do not necessarily inherit the calling session's cwd — passing a relative path can land the review in the wrong project root (especially when working inside a git worktree).
4. Replacing `{{REVIEW_SLUG}}` per the substitution rules above (diff-review: `<YYYY-MM-DD>-<branch-or-cwd>-review`; plan-review: `<plan-basename-without-.md>-plan-review`). For diff-review, `<branch-or-cwd>` is the current branch name if it isn't `main`/`master`/`HEAD`, otherwise the basename of the project root. Replace any `/` in the branch name with `-` so the slug stays a single filename.

If `docs/plans/` does not exist, create it (`mkdir -p`) before dispatch — the agent only has `Write`, not directory-creation duties.

### 3. Dispatch the reviewer subagent

Use the Agent tool with `subagent_type: "my:code-reviewer"` and the composed prompt as the `prompt` field. Set `description: "Code review"`. Do not run the agent in the background — the user is waiting for the verdict.

### 4. Surface the result

The agent writes its review to `docs/plans/{{REVIEW_SLUG}}.md`. After dispatch returns:

1. Confirm the file exists at that path. If not, surface the agent's text output verbatim and flag that the file write did not happen.
2. Print a one-line pointer to the file: `Review written to docs/plans/<filename>.`
3. If the review's verdict is `Problematic` or contains any `Critical` issues, also print a two-line summary of the top finding.

## Worked example: default invocation, no args

```
0. Args is empty — RANGE, PLAN_PATH, DESCRIPTION all empty.
1. Bash:  git diff
   Bash:  git diff --staged
   Bash:  git ls-files --others --exclude-standard
   → For each untracked file: git diff --no-index /dev/null <path>
   → Concatenate into DIFF
2. Read:  my-plugin/skills/soundness-review/code-reviewer-prompt.md (skip the header above the first `---`, take the body)
   Bash:  git rev-parse --show-toplevel
   → PLAN_DIRECTORY = "<that path>/docs/plans"
   Bash:  mkdir -p "$PLAN_DIRECTORY"
   Bash:  git branch --show-current
   → Substitute into REVIEW_SLUG (replace any `/` with `-`)
   → Substitute MODE, SUBJECT, CRITERIA, PLAN_DIRECTORY, REVIEW_SLUG; PLAN_ALIGNMENT = "", MODE_OUTPUT_SECTION = ""
3. Agent: subagent_type="my:code-reviewer", description="Code review", prompt=<the composed text>
4. Confirm <PLAN_DIRECTORY>/<REVIEW_SLUG>.md exists. Print pointer.
```

The example is the canonical execution trace — follow it literally for the no-args case. Range mode swaps step 1 for the merge-base diff (`git diff "$(git merge-base "$BASE" "$TIP")" "$TIP"`) + `git log "$RANGE" --oneline`. Plan-alignment mode adds the substitution for `PLAN_ALIGNMENT` (otherwise empty string).

## Worked example: plan-review (clean tree)

```
0. Args: docs/plans/2026-05-28-foo.md → PLAN_PATH set; RANGE/DESCRIPTION empty.
1. git diff / --staged / ls-files → payload EMPTY.
1a. PLAN_PATH set + payload empty → MODE = plan-review.
2. Read code-reviewer-prompt.md. Substitute:
   MODE=plan-review; SUBJECT=```markdown <full plan text>```; CRITERIA=Plan criteria;
   PLAN_ALIGNMENT=""; MODE_OUTPUT_SECTION=Grounding output;
   REVIEW_SLUG=2026-05-28-foo-plan-review.
3. Agent: subagent_type="my:code-reviewer", prompt=<composed text>.
4. Confirm docs/plans/2026-05-28-foo-plan-review.md exists. Print pointer.
```
