# Code re-review: feat/swappable-methods-cutover

**Status:** review of the batch 2 branch after the fix round, 2026-10-13. A `/code-review high` re-review of the branch head against local `main` finds the fix round sound for its stated cases, one gap left in it (`CLAUDE.local.md`), and a new Medium gap: `kit:tutor` can build a learning workspace that runs the `my` method.

- **Range reviewed:** `main..feat/swappable-methods-cutover` (local `main`, not `origin/main`, which differs). The `/code-review high` run read `git diff main...HEAD` with `HEAD` at the branch head. `main` is an ancestor of the branch, so this is the same diff as `main..feat/swappable-methods-cutover`: 13 commits, 28 files.
- **Level:** `high`.
- **Documents:** spec `docs/plans/2026-10-12-swappable-methods-spec.md`, plan `docs/plans/2026-10-12-swappable-methods.md`. The known limits in the plan's Risk section ("Known limits from batch 2's review") and in the spec's Risk section are not reported again.
- **Earlier review:** `docs/plans/2026-10-13-feat-swappable-methods-cutover-code-review.md`. "Carried over" below means the finding repeats or continues one of its findings. "New" means that review did not report it.
- **Tests:** the kit tests pass (28 run, OK).
- **Severity scale:** High (blocks the stated goal), Medium (wrong result in a plausible case), Low (edge case or misleading output).

## The fix round

The fix round changed `plugins/kit/skills/setup/SKILL.md` only, for the earlier findings 2, 4 and 10:

- **Finding 2 (other method's import, tutor idempotence):** fixed for `CLAUDE.md`. Both step lists now remove the other method's import line, the tutor steps have an "already set up" check, and the tutor import is not added twice. The removal does not reach `CLAUDE.local.md`; see finding 6 below.
- **Finding 4 (`.gitignore` edits):** fixed. Sub-step 1 of step 4 now runs `git status --porcelain -- .gitignore` before the edit and asks, as step 3 does for the other two files.
- **Finding 10 (`my` "already set up" check):** fixed in part. The check now requires "no other method's import line", but it does not say which files it reads, and the skill reads `CLAUDE.local.md` only for the "Parallel runs" heading. The earlier finding's own scenario (a stray tutor import in `CLAUDE.local.md`) still stops at "set up". See finding 6.

The other fix-round commits only reword docs (`README.md` install notes, two `my` skill sentences) and add the reviews and the Risk entries. They raise no finding.

## Findings

### 1. `kit:tutor` never sets the tutor method, so a learning workspace can run the `my` method

- **Where:** `plugins/kit/skills/tutor/SKILL.md:146` (the setup steps, lines 89 to 137, and the red-flag row at line 146)
- **Severity:** Medium
- **New or carried over:** new
- **Defect:** the `kit:tutor` setup never writes `@~/.claude/methods/tutor.md`, never runs or names `/kit:setup tutor`, and never removes a `my` switch the repo already has. Its red-flag row allows only a `learning` scope line in `CLAUDE.md`. The spec's D6 and its hook note (spec line 141) rest on "in a tutor project `my` is off", which nothing makes true for a new workspace.
- **Failure scenario:** after the cutover, the project repos commit `@~/.claude/methods/my.md` and `"my@claude-setup": true`, `"superpowers@synced": true`. Case 3 runs `git clone <project path> <parent>/<name>-learning` (line 76), so the clone inherits both switches. Case 2 runs in place in such a repo. The learning workspace then loads `my.md` and superpowers: brainstorming, specs, worktrees and roadmap steps, which the tutor skill says must not run. In case 1, the workspace never gets the tutor import, so the four core exceptions in `tutor.md` (D14) never load.

### 2. The squash-merge hook now fires in a learning workspace that keeps the `my` switch

- **Where:** `plugins/my/hooks/hooks.json:22`
- **Severity:** Low
- **New or carried over:** new (a consequence of finding 1)
- **Defect:** the branch removes the hook's `docs/learning/curriculum.md` early exit, as the spec says, on the premise that `my` is off in every learning workspace. Finding 1 shows a path where it is on.
- **Failure scenario:** in a case 3 clone that kept the `my` switch, each exercise ends with `git merge --squash`. Each one now adds "Invoke the my:roadmap-management skill…" to the tutor session's context. Before this branch the hook stayed silent there.

### 3. The guard does not link `docs/learning/curriculum.md` to the tutor method

- **Where:** `plugins/kit/hooks/method-guard.py:122`
- **Severity:** Low
- **New or carried over:** new (a consequence of finding 1)
- **Defect:** the guard checks only that the imports and the plugin switches agree. A learning workspace that imports `my`, with `my` and superpowers on, passes as consistent.
- **Failure scenario:** a new case 3 clone sits at a new path, so its import is not approved yet. The guard prints "Read ~/.claude/methods/my.md before your first reply", which pushes the `my` rules into a tutor session. After the user approves the import, the guard prints nothing, so the wrong method is never reported.

### 4. `kit:setup` commits without the lock in a project with a "Parallel runs" section

- **Where:** `plugins/kit/skills/setup/SKILL.md:149`
- **Severity:** Low
- **New or carried over:** new
- **Defect:** step 4 always commits with a plain `git -C <path> commit` in the main checkout. Step 1 detects a "Parallel runs" section, and `my.md` (Git Workflow) says that every commit in the main checkout of such a project runs under lock `main` through `locked-commit.py`. `kit:commit` follows that rule; `kit:setup` does not.
- **Failure scenario:** the user reruns `/kit:setup my` on a project with a "Parallel runs" section while an auto run commits on its `main`. The setup commit hits `index.lock`, or stages between the auto run's stage and commit and races it.

### 5. The tutor commit runs the `settings.json` ignore gate even when it does not touch that file

- **Where:** `plugins/kit/skills/setup/SKILL.md:191` (gate at `:128`)
- **Severity:** Low
- **New or carried over:** new (the fix round leaves it as it was)
- **Defect:** tutor step 4 says "Commit as in step 4 for `my`". That step's sub-step 1 always runs `git check-ignore -q .claude/settings.json` and stops on exit 0. The tutor steps stage `settings.json` only when they changed it, and never create it.
- **Failure scenario:** a learning repo ignores `.claude/` and has no `settings.json`. `check-ignore` exits 0 for the path that does not exist. The skill stops and proposes a `.gitignore` rewrite. If the user says no, it stops with "the switch cannot be committed", although the only file to commit is `CLAUDE.md`.

### 6. The fix round removes the other method's import from `CLAUDE.md` only

- **Where:** `plugins/kit/skills/setup/SKILL.md:96` (also the "already set up" checks at `:86` and `:179`)
- **Severity:** Low
- **New or carried over:** carried over (the `CLAUDE.local.md` part of earlier findings 2 and 10, which the fix round did not cover)
- **Defect:** the new removal sits under the `CLAUDE.md` bullet only. The guard reads `CLAUDE.md` and `CLAUDE.local.md`. The new "no other method's import line" checks do not say which files they read. The Risk entry for duplicate imports says "`kit:setup` removes other import lines", which holds only for `CLAUDE.md`, and no Risk entry names `CLAUDE.local.md`.
- **Failure scenario:** a repo has the `my` facts block, the `my` import and both keys in `CLAUDE.md` and `settings.json`, plus a stray `@~/.claude/methods/tutor.md` in `CLAUDE.local.md`. The guard warns "imports more than one method file: my, tutor", and both rule files load. `/kit:setup my` reads `CLAUDE.md`, sees no other import, says the project is set up and stops. Or it runs the full steps and leaves the tutor line in place. Either way the warning stays.

### 7. A read of `~/.claude.json` during another session's write gives a false "could not read"

- **Where:** `plugins/kit/hooks/method-guard.py:106`
- **Severity:** Low
- **New or carried over:** new
- **Defect:** the guard parses `~/.claude.json` at every session start. Every running Claude Code session rewrites that file. If a write is not atomic, a read in the middle of it fails to parse, `approval()` returns `None`, and the approval warnings are skipped. Whether Claude Code writes the file atomically (a temporary file, then a rename) was not checked, so this finding is uncertain.
- **Failure scenario:** with about ten sessions open, a new session starts while another rewrites `~/.claude.json`. The guard prints "method guard could not read /home/…/.claude.json" and no `not_approved` or `declined` line, in a project whose import really is not approved. The model runs without the method rules and is not told to read them.

### 8. The proposed `.gitignore` change cannot work when the ignore rule is outside the repo's `.gitignore`

- **Where:** `plugins/kit/skills/setup/SKILL.md:128`
- **Severity:** Low
- **New or carried over:** new
- **Defect:** sub-step 1 shows where `check-ignore -v` found the rule, but always proposes to edit the repo's `.gitignore`. When the rule `.claude/` comes from `core.excludesFile` or `.git/info/exclude`, the folder stays excluded, and git does not look inside an excluded folder, so `!.claude/settings.json` in `.gitignore` has no effect.
- **Failure scenario:** the user's global excludes file holds `.claude/`. The skill adds `.claude/*` and `!.claude/settings.json` to `.gitignore` and commits it. `git add .claude/settings.json` still refuses the file, so the switch is not committed, and worktrees of the repo do not get it.
