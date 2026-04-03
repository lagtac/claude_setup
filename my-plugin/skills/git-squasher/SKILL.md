---
name: git-squasher
description: Use when the user wants to squash, clean up, or consolidate consecutive minor commits (fix, chore, style, formatting, cleanup) in git history. Also when invoked via /git-squasher.
---

# Git Squasher

Squash consecutive minor commits (fix, chore, style, cleanup) into single cohesive commits while preserving meaningful history boundaries.

## Arguments

```
/git-squasher                    # analyze current branch, show squash candidates
/git-squasher --hierarchical     # group by topic (file/area) not just adjacency
/git-squasher main               # only commits ahead of main
/git-squasher HEAD~20            # last 20 commits
/git-squasher --dry-run          # show plan without executing
```

Defaults: scope=all commits ahead of main (or HEAD~20 if no upstream), dry-run=false

## Steps

### 1. Determine scope and safety

Determine commit range:
- If base ref given, use `git log <base>..HEAD`
- Otherwise, detect main/master branch and use commits ahead of it
- Fallback: `HEAD~20`

**Safety checks before ANY rebase:**

```bash
# Check for uncommitted changes
git status --porcelain

# Check if commits are pushed to remote
git log --oneline origin/<branch>..HEAD 2>/dev/null
```

- If working tree is dirty: STOP. Tell user to commit or stash first.
- If squashing pushed commits: WARN explicitly. Require user confirmation. Explain force-push consequences.
- If on main/master: WARN. Confirm before proceeding.

### 2. Parse commits and identify squashable prefixes

```bash
git log --no-merges --reverse --format="%h|%s" <range>
```

**Squashable prefixes** (case-insensitive):
- `fix:` `fix(scope):` — bugfixes, corrections, typo fixes
- `chore:` `chore(scope):` — maintenance, cleanup, config
- `style:` — formatting, whitespace
- `docs:` — documentation-only changes
- Unprefixed trivial messages: "cleanup", "formatting", "update gitignore", "fix typo", etc.

**Non-squashable (boundary) commits:**
- `feat:` `feature:` — new functionality
- `refactor:` — structural changes
- `test:` — test additions
- `breaking:` `BREAKING CHANGE`
- Any commit the user explicitly marks as keep

### 3. Build squash groups

Walk commits in chronological order. Group consecutive squashable commits into runs:

```
Rules:
1. A run starts when a squashable commit follows a non-squashable commit (or is first)
2. A run continues while the next commit is also squashable
3. A run ends when a non-squashable commit appears — this starts a boundary
4. Single-commit runs are skipped (nothing to squash)
5. --hierarchical mode: also group by changed files/directories, may split runs
```

Example from real history:
```
081e510 feat: add disease grouping mode          ← boundary (keep)
d3e054d fix: exclude multi-disease annotations   ┐
431523a chore: add reference SQL queries          │ RUN 1 (3 commits)
d37d678 fix: redirect mysql.sh diagnostic output  ┘
474fdcf fix: improve tar archive paths            ┐ RUN 2 (2 commits)
9ade9d4 fix: set default path var to secrets      ┘
ca80ac1 fix: fix SECRETS_DIR default assignment   ← single, skip
3e36e1f refactor: extract ensure_resize_tool      ← boundary (keep)
```

### 4. Present squash plan to user

For each run, show:

```
Group 1 (3 commits):
  d3e054d fix: exclude multi-disease annotations from YOLO export queries
  431523a chore: add reference SQL queries for annotations and stats
  d37d678 fix: redirect mysql.sh diagnostic output to stderr
  → Proposed message: "fix: improve YOLO export queries and mysql.sh diagnostics"

Group 2 (2 commits):
  474fdcf fix: improve tar archive paths and record generating command in YOLO export
  9ade9d4 fix: set default path var to secrets, instead of hardcoded path
  → Proposed message: "fix: improve tar archive paths and secrets path defaults in YOLO export"
```

**Proposed message rules:**
- Use the most significant prefix from the group (fix > chore > style > docs)
- Synthesize a message that captures all changes — don't just use the first commit's message
- Keep under 72 characters for the subject line
- If changes span unrelated areas, note both areas

**Ask user to confirm, edit messages, or exclude groups.**

### 5. Execute squash

Use `git rebase -i` with a prepared sequence. For each group, working from oldest to newest:

```bash
# Create the rebase todo automatically
GIT_SEQUENCE_EDITOR="sed -i '<sed_commands>'" git rebase -i <base>
```

The sed commands should mark the first commit in each group as `pick` and subsequent commits as `fixup` (or `squash` if preserving messages in body).

**After rebase completes:**
- For each group, amend the pick commit with the proposed message using:
  ```bash
  git rebase -i <parent> # with 'reword' on the target commit
  ```

**Alternative simpler approach** when groups are at HEAD:
```bash
git reset --soft HEAD~N
git commit -m "proposed message"
```

Use the simpler approach when possible (groups at tip of branch). Use rebase for groups in the middle of history.

### 6. Verify result

```bash
# Show the new log
git log --oneline <range>

# Verify no commits were lost (compare file tree)
git diff <original-HEAD> HEAD  # should be empty
```

If diff is not empty, something went wrong. Alert the user immediately.

## Common Mistakes

- Squashing across semantic boundaries (a fix commit between two feat commits should not bridge them)
- Not checking if commits are pushed — force-push consequences
- Losing commit authorship info when multiple authors contributed
- Squashing a commit that's referenced in PR discussions or issues
- Running on main/master without explicit confirmation
- Not verifying the tree is identical after squash (data loss detection)

## Edge Cases

- **Mixed authors**: If a run contains commits from different authors, warn and skip unless user confirms
- **Merge commits in range**: Skip merge commits entirely, treat as boundaries
- **Single commit runs**: Nothing to squash — skip silently
- **All commits are squashable**: Propose squashing into one, but confirm first
- **Rebase conflicts**: If conflicts arise, abort and report. Do not attempt auto-resolution.
