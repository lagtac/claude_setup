---
description: Structured commit workflow with conventional commits
---

# Commit instructions

Follow these steps in order. Do not skip steps. Do not bundle unrelated changes into a single commit.

1. **Inventory the changes.** Run `git status` and `git diff` (and `git diff --cached` if anything is staged). Read the actual diff — do not infer changes from filenames.

2. **Refuse secrets.** If any staged or unstaged file looks like a secret (`.env`, `.env.*`, files containing API keys, tokens, private keys), stop and warn the user explicitly. Do not commit it.

3. **Group changes into logical units.** One commit per coherent change (one feature, one fix, one refactor). If the diff spans unrelated concerns, propose multiple commits and stage each group with `git add <specific-files>` — do not use `git add -A` or `git add .`.

4. **Write a Conventional Commit message** for each commit. Subject line: `<type>(<scope>): <imperative summary under 72 chars>`. Use `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `style`, `perf`, `build`, `ci`. Add a body when the *why* is non-obvious — the body should explain motivation and consequences, not restate the diff. Use a HEREDOC to preserve formatting.

5. **Run hooks; do not bypass.** Never use `--no-verify`, `--no-gpg-sign`, or other hook-skipping flags unless the user explicitly asked. If a pre-commit hook fails, fix the underlying issue and create a *new* commit — do not `--amend` past it.

6. **Verify.** After committing, run `git status` to confirm a clean tree and `git log --oneline -n <N>` (where N is the number of commits you created) to confirm the messages landed as intended.

Reference: <https://www.conventionalcommits.org/en/v1.0.0/#specification>
