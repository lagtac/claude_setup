---
name: git-squasher
description: Use when the user wants to squash, clean up, or consolidate consecutive minor commits (fix, chore, style, formatting, cleanup) in git history. Also when invoked as /my:git-squasher.
---

# Git Squasher

Squash consecutive minor commits (fix, chore, style, cleanup) into single cohesive commits while preserving meaningful history boundaries.

## Arguments

```
/my:git-squasher                 # commits ahead of the default branch; show plan, then squash on approval
/my:git-squasher main            # only commits ahead of main
/my:git-squasher HEAD~20         # last 20 commits
/my:git-squasher --dry-run       # stop after the plan in step 4; change nothing
```

Defaults: scope = all commits ahead of the default branch (`main`, else `master`). If neither exists, `HEAD~20`.

## Steps

### 1. Determine scope and safety

Determine the commit range:
- If a base ref is given, the range is `<base>..HEAD`.
- Otherwise the range is `<default-branch>..HEAD`, where the default branch is `main`, else `master`.
- If neither exists, the range is `HEAD~20..HEAD`.

Then record the starting point. Step 6 compares against it, and it is the way back if anything goes wrong:

```bash
ORIG=$(git rev-parse HEAD)
git branch "backup/squash-$(date +%Y%m%d-%H%M%S)" "$ORIG"
```

Run these checks before any rebase:

```bash
git status --porcelain                                  # uncommitted changes
git log --oneline "origin/$(git branch --show-current)..HEAD" 2>/dev/null   # unpushed commits
git branch --show-current                               # on main/master?
```

Stop and report, without changing anything, when:

- **The working tree is dirty.** Tell the user to commit or stash first. Do not stash for them.
- **Any commit in a squash group is already pushed** (it is not in the unpushed list above). Squashing it forces a force-push. Explain that, and continue only if the user says so explicitly in this conversation.
- **The current branch is `main` or `master`.** Continue only if the user confirms explicitly.

### 2. Parse commits and identify squashable prefixes

```bash
git log --no-merges --reverse --format="%h|%an|%s" <range>
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
- `fixup!` and `squash!` commits. They are meant for `git rebase --autosquash` onto a named target, not for a run.
- Any commit the user explicitly marks as keep

### 3. Build squash groups

Walk commits in chronological order. Group consecutive squashable commits into runs:

```
Rules:
1. A run starts when a squashable commit follows a non-squashable commit (or is first)
2. A run continues while the next commit is also squashable
3. A run ends when a non-squashable commit appears — this starts a boundary
4. Single-commit runs are skipped (nothing to squash)
5. A run whose commits have more than one author (%an) is shown but left out of the plan unless the user includes it
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
- Use no single quote (`'`) in a message. Step 5 passes it inside single quotes.

With `--dry-run`, stop here.

Otherwise ask with `AskUserQuestion`: options `Squash as proposed`, `Edit messages or exclude groups` (the user types the changes) and `Cancel`. If `AskUserQuestion` is not available, print the plan, say `Reply "squash" to run it`, and end the turn. Never run step 5 without an explicit approval.

### 5. Execute squash

Never start an editor. `git rebase -i` without `GIT_SEQUENCE_EDITOR`, a `reword` line and `git commit` without `-m` all wait for an editor, and the session cannot type into one. Instead, a script edits the rebase todo, and `exec` lines set each group's message.

**Groups at the tip of the branch only** (the newest commit of the range is the last commit of the only group):

```bash
git reset --soft HEAD~<N>          # N = commits in the group
git commit -m "<proposed message>"
```

**Any other case** — one rebase for all groups:

1. Write `<scratchpad>/squash-todo.sh`. For each group, it turns every commit after the first from `pick` into `fixup`. It adds an `exec` line after the group's last commit that sets the message. For group 1 of the example:

   ```sh
   #!/bin/sh
   # $1 is the rebase todo file. Repeat the three -e lines for each group.
   sed -i \
     -e 's/^pick 431523a/fixup 431523a/' \
     -e 's/^pick d37d678/fixup d37d678/' \
     -e "/^fixup d37d678/a exec git commit --amend --no-edit -m 'fix: improve YOLO export queries and mysql.sh diagnostics'" \
     "$1"
   ```

   Use the hashes exactly as step 2 printed them. The patterns match by prefix, so a longer hash in the todo still matches.
2. Run it:

   ```bash
   chmod +x <scratchpad>/squash-todo.sh
   GIT_SEQUENCE_EDITOR=<scratchpad>/squash-todo.sh git rebase -i <base>
   ```

   `<base>` is the parent of the oldest commit in the range, usually the base ref from step 1.
3. **On a conflict or any error:** run `git rebase --abort`, report the error verbatim, and stop. Do not resolve conflicts yourself.

### 6. Verify result

```bash
git log --oneline <range>
git diff "$ORIG" HEAD      # must print nothing
```

If `git diff` prints anything, the squash changed file contents. Stop and tell the user at once. Name the backup branch from step 1; `git reset --hard <backup-branch>` restores the old history. Do not run the reset yourself.

On success, tell the user the backup branch name. Do not delete it; the user decides when.

## Common Mistakes

- Squashing across semantic boundaries (a fix commit between two feat commits should not bridge them)
- Not checking if commits are pushed — force-push consequences
- Losing commit authorship info when multiple authors contributed
- Squashing a commit that's referenced in merge request discussions or issues
- Running on main/master without explicit confirmation
- Not verifying the tree is identical after squash (data loss detection)
- Starting an editor (`reword`, bare `git commit`, `rebase -i` without `GIT_SEQUENCE_EDITOR`); the command hangs

## Edge Cases

- **Mixed authors**: see step 3, rule 5
- **Merge commits in range**: Skip merge commits entirely, treat as boundaries
- **Single commit runs**: Nothing to squash — skip silently
- **All commits are squashable**: Propose squashing into one, but confirm first
- **Rebase conflicts**: see step 5, item 3
