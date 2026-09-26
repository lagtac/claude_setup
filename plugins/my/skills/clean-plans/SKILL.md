---
name: clean-plans
description: >
  Use when the user wants to clean up, rename, or organize auto-generated plan/spec/review
  files with random names like adjective-verb-noun.md. Also when invoked via /my:clean-plans.
  Renames important project-specific documents and offers to delete trivial or unrelated ones.
---

# Plan File Cleaner

Organize plan/spec/review `.md` files in `docs/plans/`: give undated documents a dated name, and offer to delete the few that do not belong. Renaming never loses information; deleting does, so deletion is rare and always asked.

| Type | New name |
|---|---|
| `plan` | `{YYYY-MM-DD}-{feature}.md` — no suffix |
| `spec` | `{YYYY-MM-DD}-{feature}-spec.md` |
| `review` | `{YYYY-MM-DD}-{feature}-review.md` (or `-spec-review`, `-plan-review` when it reviews one spec or plan) |
| `architecture` | `{YYYY-MM-DD}-{feature}-architecture.md` |
| `action-plan` | `{YYYY-MM-DD}-{feature}-action-plan.md` |

These match the global layout rules (`~/.claude/rules/docs-layout.md`). A plan has no `-plan` suffix. If the project's `CLAUDE.md` documents a different layout, follow the project and say so.

The per-file classification in step 3 fans out to parallel Haiku subagents — independent rubric-driven extraction with no shared state. The main session handles discovery, approval, and execution.

## Steps

### 1. Discover files

List the `.md` files directly in `docs/plans/`. Skip `README.md`, which is an index, not a plan.

Superpowers' default folders (`docs/superpowers/plans/`, `docs/superpowers/specs/`) are not scanned. The global instructions send all plans and specs to `docs/plans/`.

### 2. Pick the candidates

- A name that starts with `YYYY-MM-DD-` is already correct. Skip it.
- Every other file is a candidate:
  - **Random name** — three words with no link to the content, as plan mode generates them (`vivid-discovering-papert.md`). The feature name comes from the content (step 3).
  - **Descriptive name** — the words describe the content (`annotation-data-quality-evaluation.md`). Keep those words as the feature name; drop a trailing `-plan`. Only the date is added.

Examples:
- `vivid-discovering-papert.md` → candidate, random name
- `annotation-data-quality-evaluation.md` → candidate, descriptive name → `2026-03-02-annotation-data-quality-evaluation.md`
- `2026-03-10-batch-export.md` → skip
- `2026-03-10-auth-redesign-spec.md` → skip

If there are no candidates, report `All files in docs/plans/ are already dated.` and stop.

### 3. Triage each candidate (dispatched in parallel)

Each candidate is triaged into one of two buckets, with metadata extraction for the rename bucket. The criteria below are the rubric — they apply identically whether you triage inline or via dispatch.

#### RENAME — the default

Every document about this project's work is renamed, including finished work: a plan whose work is done still records why the code is the way it is. Extract metadata:

- **feature**: Main topic in 2-4 kebab-case words (e.g., `batch-export`, `dev-report-todos`). For a descriptive name, use its existing words.
- **type**: One of `plan`, `spec`, `review`, `architecture`, `action-plan` — infer from:
  - H1 heading (e.g., "# Plan: ..." -> `plan`)
  - Content keywords ("review", "evaluation", "specification", "design")
  - Existing suffix (e.g., `*-spec.md` or `*-design.md` -> `spec`)
  - Default to `plan` if ambiguous

#### DELETE — only these three cases

Offer deletion only for a document that matches one of these:

- **Another project**: it is about a different repository or product than the one this `docs/plans/` belongs to.
- **Empty or boilerplate**: under about ten lines of real content, or a template never filled in.
- **Duplicate**: another file in `docs/plans/` holds the same content, dated or not. Name that file in the reason.

Finished work, small scope and "about tooling" are not reasons to delete: in a repository whose product is tooling, tooling plans are the project's own work. When in doubt, choose RENAME.

#### Dispatch

Reading and classifying each file is independent work that benefits from cheaper-model parallelism. With **3 or more candidates**, fan out via the Agent tool — one call per file, all dispatched in a **single message** so they run concurrently. Use `subagent_type: "general-purpose"` and `model: "haiku"`. With 1–2 candidates, classify inline; spawn overhead exceeds the savings. Wait until every subagent has returned before step 4.

Each subagent gets this self-contained prompt (substitute `<PATH>` for the candidate's absolute path, and `<PROJECT>` for the repository's directory name):

```
Classify the plan/spec/review file at <PATH>. It lives in the docs/plans/ folder of the repository <PROJECT>.

Read the file in full, then return ONE JSON object on a single line, no prose, no code fences:
{"path": "<PATH>", "decision": "RENAME"|"DELETE", "feature": "<kebab-case-2-to-4-words>"|null, "type": "plan"|"spec"|"review"|"architecture"|"action-plan"|null, "reason": "<one short sentence>"}

Decision rules:

RENAME is the default. Every document about this repository's work is renamed,
including finished work. For RENAME, populate feature and type:
- feature: 2-4 kebab-case words for the main topic (e.g. "batch-export")
- type: infer from the H1 heading ("# Plan: ..." -> plan), content keywords
  (review, evaluation, specification, design), existing suffix
  (*-spec.md or *-design.md -> spec); default to "plan" if ambiguous.

DELETE only when one of these holds:
- Another project: the document is about a different repository or product than <PROJECT>.
- Empty or boilerplate: under about ten lines of real content, or an unfilled template.
- Duplicate: another document holds the same content (name it in the reason).
Finished work, small scope and tooling topics are NOT reasons to delete.

For DELETE, set feature and type to null. The reason field is required for both
buckets: for DELETE name the case it matched; for RENAME give a brief justification.

When in doubt, choose RENAME.
```

Aggregate the returned JSON rows into a single in-memory list keyed by path before moving to step 4. If any subagent returns malformed JSON or fails, classify that one file inline rather than retrying — one bad row shouldn't block the rest.

### 4. Determine date

Use **git creation date first**, fall back to file mtime:

```bash
# Git first-commit date for the file
git log --diff-filter=A --follow --format="%as" -- "PATH" | tail -1

# Fallback: file modification time
stat -c '%y' PATH | cut -d' ' -f1
```

**Do NOT use today's date** unless both methods fail.

If the new name already exists, append `-2`, then `-3`, until it is free. Never overwrite a file.

### 5. Present confirmation table

**Always show both tables (if applicable) and wait for user confirmation before acting:**

```
Proposed renames:
| Current                         | New                                    |
|---------------------------------|----------------------------------------|
| vivid-discovering-papert.md     | 2026-03-20-batch-export.md             |

Proposed deletions:
| File                            | Reason                                 |
|---------------------------------|----------------------------------------|
| drifting-stargazing-flurry.md   | Another project: plans the xyz website |
```

Then ask with `AskUserQuestion`, one question with these options:
- "Rename and delete as proposed"
- "Rename only, skip deletions"
- "Skip all"

If `AskUserQuestion` is not available, print the tables, say `Reply "rename and delete", "rename only" or "skip"`, and end the turn. Change nothing without an explicit answer.

### 6. Execute actions

**Renames** — for each approved rename:

```bash
# Check if tracked
git ls-files --error-unmatch PATH 2>/dev/null

# Tracked: git mv (preserves history)
git mv OLD NEW

# Untracked: plain mv
mv OLD NEW
```

Then fix every link to the old name. A rename that leaves a dead link breaks the index, the roadmap and other plans:

```bash
git grep -n "<old basename>"
```

Update each hit to the new basename, with the path form the linking file already uses. This includes the `docs/plans/README.md` index row when the project has one. If the project's other plans open with a `**Status:**` line and the renamed file has none, list it in the report; do not invent a status.

**Deletions** — for each approved deletion:

```bash
# Check if tracked
git ls-files --error-unmatch PATH 2>/dev/null

# Tracked: git rm
git rm PATH

# Untracked: plain rm
rm PATH
```

Run `git grep -n "<deleted basename>"` too. Report each hit; do not edit them, because what replaces a link to a deleted file is the user's call.

Report each action. Continue on individual failures. Do not commit; the user decides how the change is committed.
