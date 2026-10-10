# Spec: `git-fold-fixups`, and the feature steps leave the always-loaded file

**Status:** approved, 2026-10-10. A script folds docs fixups with every check the prose asked for, and the fourteen feature steps move to the rule that loads with `docs/plans/`.

## How to read this spec

1. `docs/reports/2026-10-09-workflow-efficiency-critique.md`, findings G1 and G2. This spec
   answers both.
2. `global/CLAUDE.md`, section "Git Workflow", subsection "One feature, four commits on
   `main`". This is the text that changes.
3. `global/rules/docs-layout.md`. The steps move here.
4. `plugins/my/skills/handoff/SKILL.md`, Plan stage step 8 and Review stage step 8.3. Both fold
   fixups today with their own prose.
5. `plugins/my/bin/md-expand-table.py` and `plugins/my/tests/test_md_table_filters.py`. The new
   script and its tests follow their shape.
6. `ROADMAP.md`, section "Workflow efficiency".
7. `~/.claude/projects/-home-dchris-projects-claude-setup/memory/headless-skill-testing.md`.
   How to run `claude -p` against a fixture: `--add-dir` for the scratch folder and the plugin
   folder, `--permission-mode acceptEdits`, and counting denials in the stream. Task 3 uses it.

Size: **Medium**. A new script with tests, and edits to three instruction files. No stored data,
permission or public contract changes.

## Context

Git Workflow steps 4, 8 and 9 make fixup commits for spec and plan edits, then fold them with an
interactive rebase. Two bullets add checks before a fixup and before a rebase. The text is about
400 words of exact commands. Every check is fixed, and none needs judgment. `my:handoff` has a
second copy of the fold, in its Plan stage step 8 and its Review stage step 8.3.

`global/CLAUDE.md` loads in every session, including a one-line fix with no spec. The fourteen
steps only matter while a spec, plan or `done` mark is written. `docs-layout.md` already loads
only when a file in `docs/plans/` or `docs/reports/` is touched.

Two other repos point at the section by name and number:

- `grispy2-web-ext/CLAUDE.md:5` names `~/.claude/CLAUDE.md`, Git Workflow, "One feature, four
  commits on `main`".
- `zitamu/real-estate-webapp/CLAUDE.local.md:251` names the same heading. Lines 301 to 328 cite
  steps 11, 12 and 13.

## Goal

- One script does the fixup check and the fold. The rules and `my:handoff` call it.
- The fourteen steps and their checks load only when a docs file is touched.
- Every existing reference, by heading or step number, still leads to the steps.

## Out of scope

- The "project's pre-rebase check" that `my:handoff` names. It stays as it is. Git also runs a
  repository's `pre-rebase` hook during the script's rebase.
- Making the fixup commit itself. `git commit --fixup <sha>` is one command and stays in prose.
- Editing `grispy2-web-ext`, and zitamu beyond the one sentence of D6. The heading stays in
  `CLAUDE.md`, so their pointers work.

## Decisions

### D1. One script, two commands

`plugins/my/bin/git-fold-fixups.py`, Python 3 standard library only, like its siblings. It runs
in the current directory's repository.

- `git-fold-fixups.py check <sha>`: is a fixup of `<sha>` safe?
- `git-fold-fixups.py` with no argument: fold every waiting fixup on the current branch.

Exit codes: `0` done or safe; `1` refused, nothing changed (the reason is printed to stderr);
`2` usage error; `3` the rebase finished but a check after it failed, so history is rewritten
and the old `HEAD` is printed (D5).
The script never pushes, never resets, and never deletes a branch.

### D2. What "held by a worktree" means

A branch is held when a worktree other than the current one has it checked out. This is the `+`
mark of `git branch --contains`. The script reads it from
`git for-each-ref --contains <sha> refs/heads --format='%(refname:short)%00%(worktreepath)'`, and
ignores rows with an empty worktree path and the row of the current worktree. Merged branches
without a worktree do not count.

`check <sha>` exits `1` and prints each held branch with its worktree path when one exists.
Otherwise it exits `0` and prints nothing.

### D3. Finding the fixups and their targets

- A fixup is a commit in `git log --first-parent HEAD` whose subject starts with `fixup!` and a space.
  Repeated prefixes (`fixup! fixup! X`) are stripped to `X`.
- Its target is the older commit in the same list whose subject is exactly `X` and is not
  itself a fixup. `git commit --fixup` writes the target's subject, not its hash. When two or
  more older commits have the subject `X`, the target is ambiguous and D4.7 refuses. Git would
  pick the oldest one in the rebase range, which may not be the one the fixup meant, and the
  diff check of D5 cannot see the difference.
- Fixups are looked for only in commits not yet on the upstream (`@{upstream}..HEAD`) when the
  branch has one. A fixup already pushed is not waiting. Targets are looked for in the whole
  first-parent history, so a pushed target is found and then refused by D4.5.

### D4. The fold refuses, and changes nothing, when

1. a rebase, merge or cherry-pick is in progress;
2. `git status --porcelain --untracked-files=no` prints anything (untracked files are allowed,
   since a rebase leaves them alone);
3. a fixup has no target (D3);
4. a target is held by a worktree (D2);
5. a target is reachable from `@{upstream}`, so the fold would rewrite pushed history;
6. the range from the oldest target to `HEAD` holds a merge commit, because `rebase -i` would
   flatten it;
7. a fixup's subject matches two or more older commits (D3);
8. the range holds a commit whose subject starts with `squash!` or `amend!`, because the
   autosquash rebase stops for a message editor on those.

Each refusal prints one line naming the rule and the commits involved, and exits `1`.

### D5. The fold

- Record `HEAD` as `<before>`.
- Run `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <oldest target>^`, or with `--root`
  when the oldest target has no parent.
- If the rebase exits non-zero, run `git rebase --abort` only when a rebase is in progress
  (a `pre-rebase` hook that refuses starts none), print the rebase's stderr and exit `1`. The
  abort restores `<before>`.
- After success, check that no commit from the new base to `HEAD` has a subject that starts with `fixup!` and a space, and
  that `git diff <before> HEAD` is empty. If either check fails, print `<before>` and the reason,
  and exit `3`. The script does not reset. The user decides, for example
  `git reset --hard <before>`.
- On success, print `folded <n> fixups into <m> commits; HEAD <before> -> <after>` and exit `0`.
- With no waiting fixup, print `nothing to fold` and exit `0`.

### D6. Where the steps go

`global/rules/docs-layout.md` gets a new section, "One feature, four commits on `main`", holding
the current subsection unchanged except:

- step 4 and step 8 say: "Run `git-fold-fixups.py check <hash>` first. If it exits 1, make a
  normal commit instead. Always name the target by hash, never `--fixup HEAD`: a parallel
  session may have committed in between."
- step 9 says: "Fold the fixups with `git-fold-fixups.py`. It refuses, and changes nothing, when
  the fold is not safe; its message says why. Run it when no other session has uncommitted
  edits in the main checkout."
- the bullets "Before every fixup" and "Before every rebase" are deleted. The script holds
  their checks; the one piece of advice it cannot hold, "name the target by hash", moves into
  steps 4 and 8.

The step numbers stay 1 to 14.

`global/CLAUDE.md` keeps the heading "One feature, four commits on `main`". Under it, first
this text:

> A Large feature leaves four commits on `main`: the spec with its review, the plan with its
> review, the squash-merged code, and the `done` mark. Small and Medium leave fewer, as the
> size table says. The fourteen steps, and when to fixup and fold, are in
> `~/.claude/rules/docs-layout.md`, section "One feature, four commits on `main`". That rule
> loads when a file in `docs/plans/` is read or written. Before any numbered step, read it if
> it has not loaded.

Then, under the same heading and in this order, the two parts that apply to changes with no
spec:

- the paragraph "Before step 1 in a project for the first time", unchanged;
- the bullet "A `docs:` commit runs no tests and no code reviews". Its step numbers become
  "the spec review (step 2 in `docs-layout.md`)", "the plan review (step 6)" and "the `done`
  marks (step 13)".

Every other Git Workflow subsection stays as it is.

The bullets "No commit only changes a status" and "Cite only commits on `main`" move with the
steps, since both are about docs in `docs/plans/`.

Two more references in `CLAUDE.md` change:

- `CLAUDE.md:61` ("fold it (Git Workflow step 9)") becomes "fold it with `git-fold-fixups.py`".
- `CLAUDE.md:78` ("Git Workflow steps 12 and 13") becomes "steps 12 and 13 in
  `~/.claude/rules/docs-layout.md`". A session that finishes a branch may never touch
  `docs/plans/`, so the reference names the file.

Outside this repo, `zitamu/real-estate-webapp/CLAUDE.local.md:250-253` says the global section
"has the fourteen steps". That file is ignored by git (`.gitignore:65`). Its sentence changes to
name `~/.claude/rules/docs-layout.md` for the steps and checks, and `~/.claude/CLAUDE.md` for
the rules for `docs:` commits. No commit in zitamu.

### D7. `my:handoff` calls the script

- Plan stage step 8: keep the test for a clean `<base>` and the project's pre-rebase check.
  Replace the fold itself with `git-fold-fixups.py`. Exit `1` is a signal and a stop:
  `<name>: fold refused: <its message>`. Exit `3` is a different signal and a stop:
  `<name>: fold rewrote history and a check failed; HEAD before was <hash>`.
- Review stage step 8.3: the same replacement. The existing "wait for a clean `<base>`" signal
  stays.
- The way step 8 finds waiting fixups of the spec stays. It decides whether to fold; the script
  decides whether folding is safe. The script folds every waiting fixup on the branch, not
  only this spec's, so another feature's open worktree can make it refuse. That is accepted
  (see Risk): the refusal names the worktree, and the fixup waits until that branch merges.
- `handoff/README.md` lines 50, 110 and 138 name the fold in words. They get the script's name.

## Trade-offs

- **One script with two commands** (chosen). Pros: one copy of the logic, which the rules and
  `my:handoff` share. Cons: one more file and its tests to maintain.
- **A script that only folds.** Pros: smaller. Cons: the `branch --contains` check stays as
  prose in two places.
- **A shell alias.** Pros: shortest. Cons: no checks, and the checks are why the script exists.
- **Steps to `docs-layout.md`** (chosen). Pros: less text in every session. Cons: if the rule
  does not load when a new spec is written, a session misses the steps. Task 3 tests this
  before Task 4 moves anything.
- **Steps to `my:handoff`.** Pros: the stages already run there. Cons: the spec stage runs
  before any hand-off, and a session that never hands off would miss the steps.
- **A separate rule file with the same paths.** Pros: `docs-layout.md` stays shorter. Cons: the
  user chose `docs-layout.md` on 2026-10-10; and two files with the same paths always load
  together, so the split saves nothing.

## Dependencies

None. Python 3 standard library and Git 2.23 or later for `%(worktreepath)`. Git here is 2.43.

## Risk

- **Rule loading.** The move depends on `docs-layout.md` loading when a session writes a new
  file in `docs/plans/`, not only when it reads one. This is not documented. Task 3 tests it.
  If writing does not load the rule, the steps stay in `CLAUDE.md`; only steps 4, 8 and 9 and
  the two deleted bullets change. Detection: the Task 3 test, before any move.
- **History rewrite.** The script rewrites `main`. D4 refuses the unsafe cases, the abort
  restores `HEAD` on a failed rebase, and a failed check prints `<before>` for a manual
  `git reset --hard <before>`. A rebase on a dirty tree is refused, so no edit is lost.
- **Subject matching.** When two commits share the subject a fixup names, the script refuses
  (D4.7) instead of guessing. A fixup whose target was reworded is refused too (D4.3).
- **Fold scope.** The script folds every waiting fixup on the branch. With parallel sessions,
  another feature's fixup whose target an open worktree holds makes the whole fold refuse,
  even when this spec's fixups alone would be safe. Accepted on 2026-10-10: the refusal names
  the worktree, and the fold waits until that branch merges, as `my:handoff` already waits for
  a dirty main checkout.
- **Upstream.** A branch with no upstream has nothing to protect, so D4.5 does not apply. A
  repository whose upstream lags local `main` protects only what is pushed, which is the point.
- **Blast radius**, from `grep` of the repo and of `~/projects/*/CLAUDE*.md`:
  `global/CLAUDE.md` lines 61, 78, 168 to 195; `global/rules/docs-layout.md`;
  `plugins/my/skills/handoff/SKILL.md` lines 217 to 231 and 339 to 345;
  `plugins/my/skills/handoff/README.md` lines 50, 110, 138; `grispy2-web-ext/CLAUDE.md:5` and
  zitamu `CLAUDE.local.md:250-253` (one sentence, D6); zitamu `CLAUDE.local.md:301-328` (step
  numbers kept, no edit).
- **Manual step.** The shell finds the script through a symlink in `~/bin`, as the md-tables
  filters do. Claude Code sessions get `plugins/my/bin/` on PATH by themselves.

## Testing

- Unit tests in `plugins/my/tests/test_git_fold_fixups.py`, run with
  `cd plugins/my && python3 -m unittest discover tests`. Each test builds a throwaway repo in a
  temporary directory and runs the script as a subprocess, like `test_md_table_filters.py`.
- The rule-loading test of Task 3 runs headless `claude -p` in a scratch fixture.
- End to end: the first real fold after the merge is this feature's own `approved` fixup, if
  one is made.

## Tasks

Run in a worktree of `claude-setup`. Commit type `feat`, scope `my-plugin` for the script and
`global` for the rule move; the squash commit uses `feat(my-plugin,global)`.

### Task 1: tests (Red)

File: `plugins/my/tests/test_git_fold_fixups.py`.

Helpers, no bodies here: `make_repo(tmp) -> Path` (git init, user name and email set, one root
commit), `commit(repo, subject, files={}) -> str` (returns the hash),
`run(repo, *args) -> CompletedProcess`, `subjects(repo) -> list[str]` (newest first).

```python
def test_check_safe_without_worktree(self):
    r = run(repo, "check", target)
    assert r.returncode == 0 and r.stdout == ""

def test_check_refuses_when_worktree_holds_branch(self):
    # git worktree add ../wt -b feat <after target>
    r = run(repo, "check", target)
    assert r.returncode == 1 and "feat" in r.stderr

def test_check_ignores_merged_branch_without_worktree(self):
    assert run(repo, "check", target).returncode == 0

def test_nothing_to_fold(self):
    r = run(repo)
    assert r.returncode == 0 and "nothing to fold" in r.stdout

def test_folds_one_fixup(self):
    # spec commit, unrelated commit, fixup! spec commit
    r = run(repo)
    assert r.returncode == 0
    assert subjects(repo) == ["unrelated", "docs: spec", "root"]
    assert git(repo, "diff", before, "HEAD") == ""

def test_folds_nested_fixup_prefix(self):
    # "fixup! fixup! docs: spec" folds into "docs: spec"
    assert not any(s.startswith("fixup!") for s in subjects(repo))

def test_folds_into_root_commit(self):
    assert run(repo).returncode == 0  # uses --root

def test_refuses_dirty_tracked_file(self):
    r = run(repo)
    assert r.returncode == 1 and "uncommitted" in r.stderr
    assert git(repo, "rev-parse", "HEAD") == before

def test_allows_untracked_file(self):
    assert run(repo).returncode == 0

def test_refuses_fixup_without_target(self):
    r = run(repo)
    assert r.returncode == 1 and "no target" in r.stderr

def test_refuses_target_held_by_worktree(self):
    r = run(repo)
    assert r.returncode == 1 and "feat" in r.stderr
    assert git(repo, "rev-parse", "HEAD") == before

def test_refuses_target_on_upstream(self):
    # bare clone as origin, push the target, then add the fixup locally
    r = run(repo)
    assert r.returncode == 1 and "pushed" in r.stderr

def test_refuses_merge_in_range(self):
    r = run(repo)
    assert r.returncode == 1 and "merge" in r.stderr

def test_refuses_during_rebase(self):
    r = run(repo)
    assert r.returncode == 1 and "in progress" in r.stderr

def test_conflict_aborts_and_restores_head(self):
    # the fixup's change conflicts with a later commit on the same line
    r = run(repo)
    assert r.returncode == 1
    assert git(repo, "rev-parse", "HEAD") == before
    assert not Path(git(repo, "rev-parse", "--git-path", "rebase-merge")).exists()

def test_refuses_ambiguous_target(self):
    # two commits "docs: spec", then "fixup! docs: spec"
    r = run(repo)
    assert r.returncode == 1 and "ambiguous" in r.stderr
    assert git(repo, "rev-parse", "HEAD") == before

def test_refuses_squash_commit_in_range(self):
    # "squash! docs: spec" after the target
    r = run(repo)
    assert r.returncode == 1 and "squash!" in r.stderr

def test_pre_rebase_hook_refusal_restores_nothing_to_abort(self):
    # .git/hooks/pre-rebase exits 1
    r = run(repo)
    assert r.returncode == 1
    assert "No rebase in progress" not in r.stderr
    assert git(repo, "rev-parse", "HEAD") == before

def test_usage_error(self):
    assert run(repo, "check").returncode == 2
```

Each test must fail first with "No such file" for the script. Exit `3` has no test: a check
after a rebase that git reports as successful cannot be made to fail from outside without
patching git. The code path is short and is read in the end-of-branch review.

### Task 2: the script (Green)

File: `plugins/my/bin/git-fold-fixups.py`, executable, docstring in the style of
`md-expand-table.py` with a Usage block.

Functions: `git(*args, check=True) -> str`, `held_branches(sha) -> list[tuple[str, str]]` (D2),
`waiting_fixups() -> list[tuple[str, str]]` (fixup hash, target hash; D3),
`refusal(fixups) -> str | None` (D4, the first rule that applies), `fold(fixups) -> int` (D5),
`main(argv) -> int`.

All Task 1 tests pass. Run the whole suite.

### Task 3: does a written plan file load the rule?

No repo change. A fixture repo in the scratch folder, named `canary-fixture`, and a user-level
rule `~/.claude/rules/canary.md`, because the real rule is user-level too:

```markdown
---
paths:
  - "**/canary-fixture/docs/plans/*.md"
---
End every reply with the word CANARY-7.
```

The path pattern matches only the fixture, so other sessions never load it. Delete
`~/.claude/rules/canary.md` as soon as both runs end, also when a run fails.

- Run A: `claude -p "Create docs/plans/2026-01-01-x-spec.md containing only a title line."`
  with `--permission-mode acceptEdits`, and `--add-dir` as the headless testing notes say.
- Run B: the same fixture with the file present, prompt "Read docs/plans/2026-01-01-x-spec.md
  and say its title."

```python
assert "CANARY-7" in final_text(run_b)   # the mechanism works on a read
write_loads = "CANARY-7" in final_text(run_a)
```

If `run_b` fails, the fixture is wrong; fix it before deciding. If `write_loads` is false, Task 4
takes its fallback (see Risk). Record the result in this spec's Risk section.

### Task 4: move the steps

Files: `global/CLAUDE.md`, `global/rules/docs-layout.md`; outside the repo,
`~/projects/zitamu/real-estate-webapp/CLAUDE.local.md` (one sentence, not committed).

- As D6. When Task 3 found that a write does not load the rule, apply only the step 4, 8 and 9
  edits and the deletion of the two bullets, inside `CLAUDE.md`.
- Check: `grep -rn "Before every fixup\|Before every rebase\|GIT_SEQUENCE_EDITOR\|Git Workflow step" global/`
  finds nothing; `grep -n "One feature, four commits" global/CLAUDE.md global/rules/docs-layout.md`
  finds one heading in each.
- Lint: `markdownlint-cli2` on both files reports no error other than MD013, as today.

### Task 5: `my:handoff`

Files: `plugins/my/skills/handoff/SKILL.md`, `plugins/my/skills/handoff/README.md`, as D7.

- Check: `grep -rn "GIT_SEQUENCE_EDITOR\|rebase -i" plugins/my/skills/handoff/` finds nothing,
  and `SKILL.md` names both signals of D7, for exit `1` and exit `3`.

### Task 6: docs and roadmap

Files: `README.md` (the `bin/` paragraph names the new script and its test command),
`ROADMAP.md` (the spec commit moves rows G1 and G2 to 📋 with a link to this spec; they
become ✅ with the `done` mark of step 13).

Manual, outside the repo, after the merge: `ln -s
~/projects/claude-setup/plugins/my/bin/git-fold-fixups.py ~/bin/git-fold-fixups.py`.

## Open questions

None.
