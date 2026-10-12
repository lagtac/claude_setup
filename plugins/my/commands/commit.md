---
description: Structured commit workflow with conventional commits
---

# Commit instructions

Follow these steps in order. Do not skip steps. Do not bundle unrelated changes into a single commit.

**Project rules first.** Read the project's `CLAUDE.md` (and `CLAUDE.local.md` when present) before step 4. Its commit rules win over the defaults below: allowed types and scopes, whether a body is required, trailers it forbids or requires, and CHANGELOG entries that must go in the same commit.

**Parallel runs.** When the project's `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs" section, and `git rev-parse --path-format=absolute --git-dir` equals `git rev-parse --path-format=absolute --git-common-dir` (this is the main checkout), several sessions may commit here at once. Then step 3 does not stage. Step 5 reads `git diff -- <paths>` for the group, and each new file in it whole, instead of `git diff --cached`: `git diff` does not show a file git does not track yet. Step 4 writes each message with the Write tool to a new file in the session's scratchpad, instead of the HEREDOC it asks for. Each group then commits with `locked-commit.py -F <message file> <paths>`, which stages, commits and lists the commit inside lock `main`, so no shell reads the message. Step 7 reads the `git show --stat` list each command printed. Never make a `--fixup` commit there.

1. **Inventory the changes.** Run `git status` and `git diff` (and `git diff --cached` if anything is staged). Read the actual diff — do not infer changes from filenames.

2. **Refuse secrets.** If any staged or unstaged file looks like a secret (`.env`, `.env.*`, files containing API keys, tokens, private keys), stop and warn the user explicitly. Do not commit it.

3. **Group changes into logical units.** One commit per coherent change (one feature, one fix, one refactor). If the diff spans unrelated concerns, make multiple commits, one per group, and stage each group with `git add <specific-files>` — do not use `git add -A` or `git add .`. Print the planned groups and messages before the first commit. If a single file holds changes for two groups, stop and ask how to split it; do not use `git add -p`, which waits for input.

4. **Write a Conventional Commit message** for each commit. Subject line: `<type>(<scope>): <imperative summary under 72 chars>`, or `<type>: …` when the project's history uses no scopes (check `git log --oneline -20`). Use `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `style`, `perf`, `build`, `ci`. Add a body when the *why* is non-obvious — the body should explain motivation and consequences, not restate the diff. Use a HEREDOC to preserve formatting.

5. **Reread the staged diff.** Before each `git commit`, run `git diff --cached` and read it in full. Check that only this group's files are staged, that no edit dropped or garbled a character, and that the message matches what the diff does.

6. **Run hooks; do not bypass.** Never use `--no-verify`, `--no-gpg-sign`, or other hook-skipping flags unless the user explicitly asked. If a pre-commit hook fails, fix the underlying issue and create a *new* commit — do not `--amend` past it.

7. **Verify.** After committing, run `git status` to confirm a clean tree and `git log --oneline -n <N>` (where N is the number of commits you created) to confirm the messages landed as intended.

Reference: <https://www.conventionalcommits.org/en/v1.0.0/#specification>
