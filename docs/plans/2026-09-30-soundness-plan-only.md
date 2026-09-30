# `--plan-only` for `my:soundness-review` Implementation Plan

**Status:** done, 2026-09-30. Shipped in 7740bf7. No end-of-branch checks run (the user chose none).

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan task-by-task. The tasks
> build on each other and are small. The global review rules replace that
> skill's own reviews: run no per-task reviewer and no final
> `requesting-code-review` pass. The `my:handoff` review stage runs the
> end-of-branch reviews. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `my:soundness-review --plan-only <plan>` reviews the plan and never
asks, and the `my:handoff` plan stage uses it, reviews before it commits, and
commits once, so a busy `main` no longer stops it.

**Architecture:** Two prompt files change. `my:soundness-review` gets one new
token class, a table of mixed-argument stops, and a short path through steps
1 and 1a (spec D1 to D3). The `my:handoff` plan stage is rewritten to
review, check, then make one commit that holds only its own paths (D4). Five
documents that describe these steps are updated (D5, D6).

**Tech Stack:** Claude Code plugin markdown (skills), Bash, git, `jq`,
headless `claude -p` runs for tests, `markdownlint-cli2`.

**Spec:** `docs/plans/2026-09-30-soundness-plan-only-spec.md`

## Global Constraints

- Conventional Commits with scope: `type(scope): sentence`. The scope for
  plugin files is `my-plugin`. For `global/CLAUDE.md` it is `global`.
- Every commit message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- No new dependencies. `jq` and `markdownlint-cli2` are already installed.
- Work happens in the worktree `.claude/worktrees/soundness-plan-only` on the
  branch `feat/soundness-plan-only`. The `my:handoff` review stage looks for
  exactly these names.
- `my:soundness-review` without `--plan-only` behaves exactly as today
  (spec, Out of scope).
- The code and review stages of `my:handoff` keep their behavior. The review
  stage's text changes in one place: its reference to the finding test (D5).
  Changed in the review stage, 2026-09-30, by the user's choice: the review
  stage's merge step also folds the deferred fixups, before the `done`
  marks.
- Read `git diff --cached` before every commit.
- Markdown lint: the error count of each touched file must not rise above its
  count on `main` on 2026-09-30. The two files that use one long line per
  paragraph, `plugins/my/skills/soundness-review/SKILL.md` and
  `global/CLAUDE.md`, are the exception: each new paragraph there adds one
  MD013 (line length) error, which is expected. For those two, count only the
  errors of other rules, and that count must not rise (Task 2 step 5 shows
  how). The totals on `main`:
  `plugins/my/skills/soundness-review/SKILL.md` 101,
  `plugins/my/skills/handoff/SKILL.md` 1,
  `plugins/my/skills/handoff/README.md` 0,
  `docs/plans/2026-09-21-handoff-spec.md` 15, `README.md` 0, `ROADMAP.md` 0,
  `global/CLAUDE.md` 71. Count with
  `markdownlint-cli2 <file> 2>&1 | grep -c ' error '`.
- Match each file's line style. `soundness-review/SKILL.md` and
  `global/CLAUDE.md` use one long line per paragraph. The handoff files,
  `README.md` and `ROADMAP.md` wrap at 80 characters.

## Review Focus

- **`--plan-only` with a plan path that does not exist.** Step 0 turns the
  path into description text and prints its note. Then the D3 row
  "`--plan-only` and no `PLAN_PATH`" must stop. A person expects both lines
  and no review. Task 2 step 4 runs it (`g-missing`).
- **A review run that reaches the collision rule.** A second plan review of
  the same plan writes `<plan>-plan-review-2.md`. The handoff plan stage must
  commit the path the review printed, not the first name. Task 3 writes this
  into plan stage step 3.
- **Another session's staged files during the plan-stage commit.** A plain
  `git commit` would take them. `git commit -- <paths>` must leave them
  staged. Task 3 step 1 proves this in a scratch repo.
- **`--plan-only` given twice, and with free words.** The run must behave as
  one token and print the "description ignored" note. Task 2 step 4 runs it
  (`g-extra`).
- **The size guard under `--plan-only`.** No payload file is written, so
  `wc -l < "$PAYLOAD"` would fail. Step 1 must skip the size guard too.
  Task 2 step 3 says so, and the `g-dirty` run in step 4 would show an error.

## How tests run

The repo has no test runner. The running session sees the installed `my`
plugin, not the worktree's copy. So every check runs a headless session
against the worktree's plugin. A probe on 2026-09-30 showed that
`--plugin-dir` replaces the installed `my@claude-setup` copy: the stream's
`init` event lists `my` once, with the `--plugin-dir` path. Every check reads
that path, so a run of the wrong copy fails.

The shell keeps no variables between Bash calls. So Task 1 step 1 writes
`WT`, `FIX`, `SCRATCH` and two helpers to `$SCRATCH/spo-env.sh`. Every later
test block starts with `source <scratchpad>/spo-env.sh`. Give every block that
runs a headless session the longest Bash timeout (600000 ms), and run one
headless session per Bash call.

- `sr <run-name> '<args>'` runs `/my:soundness-review <args>` in the fixture
  and writes the stream to `$SCRATCH/<run-name>.jsonl`.
- `chk <run-name>` prints the facts each test reads:
  - `plugin:` the path `my` loaded from. It must be `$WT/plugins/my`.
  - `agent-calls:` how many `Agent` tool calls the run made. A stop makes 0.
  - `denials:` permission denials. This counts the events in the stream,
    because the final `permission_denials` array can be empty while a denial
    happened. It must be 0, or the run is not valid.
  - `dirty-note:` how often the headless "Working tree is dirty" note appears.
  - `new:` the untracked files under `docs/plans/` after the run.
  - The last lines of the run's final answer.
- `clean_fix` deletes the review files a run wrote, so the next run starts
  from the same state. It keeps the fixture's deliberate dirty files.

Each run needs `--add-dir` for the scratch folder and for `$WT/plugins/my`,
or the skill cannot read its own files. `TMPDIR` points into the scratch
folder, so a `mktemp -d` fallback stays in an allowed path. The mode is
`acceptEdits`: `bypassPermissions` is refused by the safety classifier.

## File map

| File | Change | Responsibility |
| --- | --- | --- |
| `plugins/my/skills/soundness-review/SKILL.md` | Modify | D1 token, D3 stops, D2 short path, description, worked example |
| `plugins/my/skills/handoff/SKILL.md` | Modify | D4 plan stage; D5 review-stage reference |
| `plugins/my/skills/handoff/README.md` | Modify | "Plan stage" list for the user (D6) |
| `docs/plans/2026-09-21-handoff-spec.md` | Modify | D9 plan stage, spec-stage step number, Risk item (D5) |
| `global/CLAUDE.md` | Modify | "Code Review Routing" names `--plan-only` (D6) |
| `README.md` | Modify | `my:soundness-review` entry names `--plan-only` (D6) |
| `ROADMAP.md` | Modify | The 💭 follow-up becomes a shipped note (D6) |

A reference sweep on 2026-09-30 found no other file that cites a plan-stage
step number. The command, run outside the dated history in `docs/plans/`:
`grep -rnE '[Pp]lan stage,? step [0-9]|step [0-9] commits|plan review would ask' --include=*.md .`
It found `plugins/my/skills/handoff/SKILL.md:166` and `:265`, and
`docs/plans/2026-09-21-handoff-spec.md:262` and `:275`. Tasks 3 and 4 change
all four.

---

### Task 0: Worktree

The `my:handoff` code stage creates the worktree before it starts this plan.
When you run the plan by hand, create it first from the main checkout:
`git worktree add .claude/worktrees/soundness-plan-only -b feat/soundness-plan-only`.
Use `git worktree add`, not `EnterWorktree`.

- [ ] **Step 1: Confirm the worktree**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && \
  git branch --show-current && \
  test -f docs/plans/2026-09-30-soundness-plan-only.md && git status --short
```

Expected: `feat/soundness-plan-only`, then no output from `git status`.

---

### Task 1: Fixture repo, helpers and Red baseline

**Files:**

- Create: `$SCRATCH/spo-fixture/` (a throwaway git repo in the scratchpad,
  outside the repo; never committed). It is not under a `.claude/` folder,
  so `acceptEdits` mode never has to ask about writes there. Every run
  passes the scratchpad with `--add-dir`.
- Create: `$SCRATCH/spo-env.sh`

**Interfaces:**

- Produces: the fixture, used by Task 2:
  - `docs/plans/2026-09-30-widget.md`, a small plan, committed.
  - `docs/plans/2026-09-30-widget-spec.md`, a spec, committed.
  - `src/widget.sh`, committed, then changed and left uncommitted.
  - `notes.txt`, untracked.
  - Two commits, so `HEAD~1..HEAD` is a non-empty range.
- Produces: `sr`, `chk` and `clean_fix` in `$SCRATCH/spo-env.sh`.

- [ ] **Step 1: Build the fixture and the helpers**

Replace `<scratchpad>` with the executing session's scratchpad directory.

```bash
SCRATCH=<scratchpad>
mkdir -p "$SCRATCH/tmp"
cat > "$SCRATCH/spo-env.sh" <<ENVEOF
WT=/home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only
FIX=$SCRATCH/spo-fixture
SCRATCH=$SCRATCH
ENVEOF
cat >> "$SCRATCH/spo-env.sh" <<'ENVEOF'
sr() {  # sr <run-name> '<args>'
  (cd "$FIX" && TMPDIR="$SCRATCH/tmp" claude -p --plugin-dir "$WT/plugins/my" \
    --add-dir "$SCRATCH" --add-dir "$WT/plugins/my" \
    --permission-mode acceptEdits --output-format stream-json --verbose \
    "/my:soundness-review $2" < /dev/null > "$SCRATCH/$1.jsonl" 2>&1)
}
chk() {  # chk <run-name>
  f="$SCRATCH/$1.jsonl"
  echo "plugin: $(jq -r 'select(.type=="system" and .subtype=="init") | .plugins[] | select(.name=="my") | .path' "$f")"
  echo "agent-calls: $(grep -o '"name":"Agent"' "$f" | wc -l)"
  echo "denials: $(grep -o '"subtype":"permission_denied"' "$f" | wc -l)"
  echo "dirty-note: $(grep -o 'Working tree is dirty' "$f" | wc -l)"
  echo "new: $(cd "$FIX" && git ls-files --others --exclude-standard docs/plans | tr '\n' ' ')"
  jq -r 'select(.type=="result") | .result' "$f" | tail -6
}
clean_fix() {
  (cd "$FIX" && git ls-files --others --exclude-standard docs/plans | xargs -r rm -f)
}
ENVEOF
source "$SCRATCH/spo-env.sh"
mkdir -p "$FIX/docs/plans" "$FIX/src" && cd "$FIX" && git init -q -b main
printf '# Spec: widget\n\n**Status:** approved, 2026-09-30.\n\nThe widget script prints its name.\n' \
  > docs/plans/2026-09-30-widget-spec.md
printf 'echo hello\n' > src/widget.sh
git add -A && git -c user.name=t -c user.email=t@t commit -qm 'docs: widget spec'
cat > docs/plans/2026-09-30-widget.md <<'PLANEOF'
# Widget Implementation Plan

**Status:** approved, 2026-09-30.

**Spec:** `docs/plans/2026-09-30-widget-spec.md`

**Goal:** `sh src/widget.sh` prints `widget`.

### Task 1: Print the name

- [ ] **Step 1:** Write `tests/widget.sh`. It runs `sh src/widget.sh` and
  exits 1 unless the output is exactly `widget`.
- [ ] **Step 2:** Run `sh tests/widget.sh`. Expected: exit 1, because
  `src/widget.sh` prints `hello`.
- [ ] **Step 3:** Change `src/widget.sh` to `echo widget`.
- [ ] **Step 4:** Run `sh tests/widget.sh`. Expected: exit 0. Commit both
  files as `feat: widget prints its name`.
PLANEOF
git add -A && git -c user.name=t -c user.email=t@t commit -qm 'docs: widget plan'
printf 'echo hi\n' > src/widget.sh
printf 'scratch notes\n' > notes.txt
git status --short; git log --oneline | cat
```

Expected: `git status` shows `src/widget.sh` as modified and `notes.txt` as
untracked; `git log` shows two commits.

- [ ] **Step 2: Record Red for the dirty-tree test (spec Testing 1)**

Today `--plan-only` is not a known token. Step 0 adds it to the description,
the tree is dirty, and the headless fallback reviews the diff.

```bash
source <scratchpad>/spo-env.sh
sr r-dirty '--plan-only docs/plans/2026-09-30-widget.md'; chk r-dirty; clean_fix
```

Expected (Red): `plugin:` is `$WT/plugins/my`, `denials: 0`,
`dirty-note:` 1 or more, and `new:` lists a `*-review.md` file that is not
`2026-09-30-widget-plan-review.md`.

- [ ] **Step 3: Record Red for the stop rows (spec Testing 2)**

Run each command in its own Bash call.

```bash
source <scratchpad>/spo-env.sh
sr r-range '--plan-only HEAD~1..HEAD docs/plans/2026-09-30-widget.md'; chk r-range; clean_fix
```

```bash
source <scratchpad>/spo-env.sh
sr r-noplan '--plan-only'; chk r-noplan; clean_fix
```

```bash
source <scratchpad>/spo-env.sh
sr r-spec '--plan-only docs/plans/2026-09-30-widget-spec.md'; chk r-spec; clean_fix
```

Expected (Red) for each: `agent-calls:` 1 or more, and a review file under
`new:`. None of the D3 stop messages appears. `r-spec` must run on the dirty
tree: on a clean tree the old code already prints the spec message, so it
would not be Red.

- [ ] **Step 4: Record Red for the extra-words row (D3 rows 4 and 5)**

```bash
source <scratchpad>/spo-env.sh
sr r-extra '--plan-only --plan-only docs/plans/2026-09-30-widget.md check the steps'; chk r-extra; clean_fix
```

Expected (Red): `dirty-note:` 1 or more, and no
`2026-09-30-widget-plan-review.md` under `new:`.

- [ ] **Step 5: Record the regression guard (spec Testing 3)**

```bash
source <scratchpad>/spo-env.sh
sr r-notoken 'docs/plans/2026-09-30-widget.md'; chk r-notoken; clean_fix
```

Expected: `dirty-note:` 1 or more, and one `*-review.md` under `new:`. This
test passes before and after the change. It is a guard that D1 changed
nothing else, not a Red test. Save the Red facts: Task 2 compares against
them.

No commit: the fixture and the scratch files are never committed.

---

### Task 2: `--plan-only` in `my:soundness-review`

**Files:**

- Modify: `plugins/my/skills/soundness-review/SKILL.md` (frontmatter lines
  3-14, step 0 at lines 27-44, step 1 at lines 46-56, step 1a at lines
  100-102, worked examples at the end)

**Interfaces:**

- Consumes: `sr`, `chk`, `clean_fix` and the fixture from Task 1.
- Produces: the argument `--plan-only`. With a plan path, the skill writes
  `<plan-basename>-plan-review.md` (or `-2`, `-3` under the collision rule)
  and prints `Review written to docs/plans/<filename>.` Task 3 relies on that
  line.

- [ ] **Step 1: Add the token class and the mixed-argument stops (D1, D3)**

In step 0, add a first row to the table, above the `RANGE` row:

```markdown
| The exact token `--plan-only` | `PLAN_ONLY` is set. Two copies act as one. |
```

Replace the line `If args is empty, all three variables are empty — the skill
runs in defaults (working-tree diff, no plan-alignment block).` with:

```markdown
**Mixed arguments with `--plan-only`.** When `PLAN_ONLY` is set, run these checks after the notes above, in this order. The first match wins. A stop dispatches nothing and writes no file.

| Arguments | Result |
| --- | --- |
| `--plan-only` and a `RANGE` | Stop: `--plan-only reviews a plan; it takes no range. Drop one of them.` |
| `--plan-only` and no `PLAN_PATH` | Stop: `--plan-only needs a plan under docs/plans/.` |
| `--plan-only` and a `PLAN_PATH` that ends in `-spec.md` | Stop: `This is a spec. Run my:spec-review <PLAN_PATH> instead.` |
| `--plan-only`, a `PLAN_PATH` and a `DESCRIPTION` | Continue. Step 1a prints `(description ignored: a plan review has no diff to check it against)`. |

If args is empty, `RANGE`, `PLAN_PATH` and `DESCRIPTION` are empty and `PLAN_ONLY` is unset — the skill runs in defaults (working-tree diff, no plan-alignment block).
```

- [ ] **Step 2: Name `--plan-only` in the description (D6)**

In the frontmatter `description`, after `with uncommitted changes and no
range, it asks which of the two to review.`, add this sentence on its own
line, indented like its neighbours:

```text
  `--plan-only` reviews the plan and never asks.
```

This is the spec's clause, word for word. Keep it this short: the
description is 953 characters today and becomes 1000, and the Agent Skills
format caps it at 1024. Check with:

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && python3 -c "
import yaml; t=open('plugins/my/skills/soundness-review/SKILL.md').read().split('---')[1]
print(len(yaml.safe_load(t)['description']))"
```

Expected: 1024 or less.

- [ ] **Step 3: Add the short path through steps 1 and 1a (D2)**

In step 1, right after the code block that sets `WORK_DIR` and `PAYLOAD`,
add:

```markdown
**If `PLAN_ONLY` is set**, stop step 1 here and go to step 1a. `WORK_DIR` exists, and the plan copy in step 2 needs it. Skip everything else in this step: the diff commands, the untracked-file list and its note, and the size guard. `PAYLOAD` is never written, so do not read or count it.
```

In step 1a, after the line `Let PLAN_PATH be from step 0 and payload be the
captured diff. Set MODE:`, add:

```markdown
**If `PLAN_ONLY` is set**, `MODE` is `plan-review`. Skip the table and the question below, and continue as the `plan-review` row: print `(description ignored: a plan review has no diff to check it against)` when `DESCRIPTION` is set. The working tree is never read, so a dirty tree changes nothing.
```

At the end of the file, after the last worked example, add:

````markdown
## Worked example: plan-review with `--plan-only` (dirty tree)

```text
0. Args: --plan-only docs/plans/2026-05-28-foo.md → PLAN_ONLY set, PLAN_PATH set; RANGE/DESCRIPTION empty.
   Mixed-argument checks: no RANGE, PLAN_PATH set, not a spec → continue.
1. mkdir -p WORK_DIR. Nothing else: no diff, no untracked list, no size guard.
1a. PLAN_ONLY set → MODE = plan-review. No question, whatever the working tree holds.
2-4. As in the plan-review (clean tree) example above.
```
````

- [ ] **Step 4: Run the Green tests**

Run each command in its own Bash call, with the 600000 ms timeout.

```bash
source <scratchpad>/spo-env.sh
sr g-dirty '--plan-only docs/plans/2026-09-30-widget.md'; chk g-dirty
test -f "$FIX/docs/plans/2026-09-30-widget-plan-review.md" && \
  grep -c '^## Grounding' "$FIX/docs/plans/2026-09-30-widget-plan-review.md"; clean_fix
```

Expected: `plugin:` is `$WT/plugins/my`, `denials: 0`, `dirty-note: 0`,
`agent-calls: 1`, `new:` is exactly `docs/plans/2026-09-30-widget-plan-review.md`,
and the `grep -c` prints `1`. No error from `wc` appears in the stream.

```bash
source <scratchpad>/spo-env.sh
sr g-range '--plan-only HEAD~1..HEAD docs/plans/2026-09-30-widget.md'; chk g-range
grep -c -- '--plan-only reviews a plan; it takes no range. Drop one of them.' "$SCRATCH/g-range.jsonl"; clean_fix
```

```bash
source <scratchpad>/spo-env.sh
sr g-noplan '--plan-only'; chk g-noplan
grep -c -- '--plan-only needs a plan under docs/plans/.' "$SCRATCH/g-noplan.jsonl"; clean_fix
```

```bash
source <scratchpad>/spo-env.sh
sr g-missing '--plan-only docs/plans/2026-09-30-nothing.md'; chk g-missing
grep -c -- 'treated as description; expected an existing plan under docs/plans/' "$SCRATCH/g-missing.jsonl"
grep -c -- '--plan-only needs a plan under docs/plans/.' "$SCRATCH/g-missing.jsonl"; clean_fix
```

```bash
source <scratchpad>/spo-env.sh
sr g-spec '--plan-only docs/plans/2026-09-30-widget-spec.md'; chk g-spec
grep -c -- 'This is a spec. Run my:spec-review docs/plans/2026-09-30-widget-spec.md instead.' "$SCRATCH/g-spec.jsonl"; clean_fix
```

Expected for `g-range`, `g-noplan`, `g-missing` and `g-spec`: `agent-calls: 0`,
`denials: 0`, an empty `new:`, and each `grep -c` prints 1 or more.

```bash
source <scratchpad>/spo-env.sh
sr g-extra '--plan-only --plan-only docs/plans/2026-09-30-widget.md check the steps'; chk g-extra
grep -c 'description ignored: a plan review has no diff to check it against' "$SCRATCH/g-extra.jsonl"; clean_fix
```

Expected: `dirty-note: 0`, `agent-calls: 1`, `new:` is exactly
`docs/plans/2026-09-30-widget-plan-review.md`, and the `grep -c` prints 1 or
more.

```bash
source <scratchpad>/spo-env.sh
sr g-notoken 'docs/plans/2026-09-30-widget.md'; chk g-notoken; clean_fix
```

Expected: the same facts as `r-notoken` in Task 1 step 5: `dirty-note:` 1 or
more, and one `*-review.md` under `new:` that is not a plan review.

If a Green run fails, use `superpowers:systematic-debugging` before you
change the skill again.

- [ ] **Step 5: Lint, then commit**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && \
  markdownlint-cli2 plugins/my/skills/soundness-review/SKILL.md 2>&1 | grep -c ' error '
```

The file uses one long line per paragraph, so each new paragraph adds one
MD013 (line length) error. That is expected. No other rule may gain an error:

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && \
  markdownlint-cli2 plugins/my/skills/soundness-review/SKILL.md 2>&1 | grep ' error ' | grep -vc MD013
git -C /home/dchris/projects/claude-setup show main:plugins/my/skills/soundness-review/SKILL.md > <scratchpad>/sr-main.md
markdownlint-cli2 <scratchpad>/sr-main.md 2>&1 | grep ' error ' | grep -vc MD013
```

Expected: the two counts are equal. The new table's separator is written
`| --- | --- |`, because the `|---|---|` form raises MD060 errors in this
file (plan review, 2026-09-30).

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && \
  git add plugins/my/skills/soundness-review/SKILL.md && git diff --cached
git commit -m "feat(my-plugin): my:soundness-review --plan-only reviews the plan and never asks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: The handoff plan stage reviews first and commits once

**Files:**

- Modify: `plugins/my/skills/handoff/SKILL.md` ("Plan stage", lines 150-177;
  "Review stage" step 6, line 265)
- Modify: `plugins/my/skills/handoff/README.md` ("Plan stage", lines 90-98)

**Interfaces:**

- Consumes: `my:soundness-review --plan-only <plan>` and its line
  `Review written to docs/plans/<filename>.` (Task 2).
- Produces: plan stage steps 1 to 9. The finding test is step 4. The review
  stage refers to it by that number.

The spec does not run the handoff plan stage end to end: it needs tmux and a
second session (spec, Testing). The one new git behavior it relies on is
tested here.

- [ ] **Step 1: Prove the commit behavior the new step 7 relies on**

```bash
S=<scratchpad>/commitprobe; rm -rf "$S"; mkdir -p "$S" && cd "$S" && git init -q -b main
printf 'a\n' > spec.md && git add spec.md && git -c user.name=t -c user.email=t@t commit -qm init
printf 'x\n' > other.md && git add other.md              # another session's staged file
printf 'b\n' >> spec.md; printf 'p\n' > plan.md; printf 'r\n' > plan-review.md
git add -- spec.md plan.md plan-review.md
git -c user.name=t -c user.email=t@t commit -qm 'docs: plan' -- spec.md plan.md plan-review.md
git show --stat --format=%s HEAD | cat; git status --short
```

Expected: the commit lists `plan-review.md`, `plan.md` and `spec.md` only,
and `git status` shows `A  other.md`. A probe on 2026-09-30 gave this result.

- [ ] **Step 2: Rewrite the plan stage (D4)**

In `plugins/my/skills/handoff/SKILL.md`, replace the whole numbered list
under `### Plan stage` (steps 1 to 8) with:

```markdown
1. Run `superpowers:writing-plans` on the spec. Write the plan to
   `docs/plans/<spec date>-<slug>.md`. Skip that skill's closing question about
   how to execute: the code stage is the execution. Do not commit the plan
   yet: step 7 commits it with its review.
2. Name one execution skill in the plan's header. Replace the header's
   "subagent-driven-development (recommended) or executing-plans" with one of
   them. Use the project's rule when it names one. Otherwise pick
   `superpowers:subagent-driven-development` when the plan has several
   independent tasks, and `superpowers:executing-plans` when the tasks build
   on each other or are small. The header also says that the project's review
   rules replace the skill's own reviews, when the project has such rules.
3. Run the project's plan review on the uncommitted plan. Under the global
   rules that is `my:soundness-review --plan-only <plan path>`. The
   `--plan-only` token reviews the plan even when other sessions have
   uncommitted files on `<base>`. Take the review's path from the line it
   prints, `Review written to docs/plans/<filename>.`: an older review of the
   same plan makes the name end in `-plan-review-2.md`.
4. For each finding, ask: would the fix change what a component owns, a
   contract, the chosen option, or the scope? If no, fix it. If yes, it is a
   gate.
5. Signal and stop on any gate: a finding whose fix would change a decision,
   or a spec decision that turns out to rest on a false premise. The signal
   names the files left uncommitted on `<base>`: the plan, the review and the
   spec.
6. The stage's paths are the plan, the review, the spec (with its `approved`
   status edit) and the project's plans index when the project has one.
   Check that they hold only this stage's changes. Run
   `git diff HEAD -- <paths>` and read every hunk. The plan and the review are
   new files, which `git diff HEAD` does not show; this stage wrote them
   whole. So the hunks come from the spec and the plans index. If a hunk is
   not this stage's own change, for example another session's row in the
   plans index, signal `<name>: <file> holds another session's edit` and
   stop.
7. Commit these paths, and only these, in one commit, following the
   project's rules for docs commits: `git add -- <paths>`, then
   `git commit -m "<message>" -- <paths>`. The `-- <paths>` on `git commit`
   commits only those paths, even when another session has staged files of
   its own. Then check that `git show --stat --format= HEAD` lists exactly
   these paths.
8. Fold waiting fixups only when `<base>` is clean. The spec has fixups
   waiting when `git log --format='%h %s' <base>` shows a commit whose
   subject starts with `fixup!` and names the spec's commit. If it does and
   `git status --porcelain` prints nothing, run the project's pre-rebase
   check, then the fold. A failed pre-rebase check is a gate: signal and
   stop. If `git status --porcelain` prints anything, skip the fold. The
   fixups are folded later, after the code branch is merged, as the global
   rule "Before every rebase" already says.
9. Finish the project's other docs steps, then run "Launch" with
   `code <plan path>`, then "Finish". When step 8 skipped a fold, print
   `<name>: fixups left unfolded: <their hashes>. Fold them after the code
   branch is merged.` just before Finish's last line, so that line stays
   last.
```

- [ ] **Step 3: Point the review stage at the new step number (D5)**

In the same file, review stage step 6, change
`apply the test in Plan stage, step 6.` to
`apply the test in Plan stage, step 4.`

- [ ] **Step 4: Update the handoff README (D6)**

In `plugins/my/skills/handoff/README.md`, replace the numbered list under
`### Plan stage` with:

```markdown
1. Writes the plan with `superpowers:writing-plans`. It does not commit it
   yet.
2. Names one execution skill in the plan's header.
3. Reviews the uncommitted plan with `my:soundness-review --plan-only`. Other
   sessions' uncommitted files on the main checkout do not stop it.
4. Fixes the findings that do not change a decision. A finding that would
   change a decision stops the stage, and you decide. The plan, the review
   and the spec then stay uncommitted, and the stop message names them.
5. Checks that the spec and the plans index hold only its own edits.
6. Commits the plan, the review and the spec's `approved` status in one
   commit, and nothing else, even when other files are staged.
7. Folds waiting fixups of the spec only when the main checkout is clean.
   Otherwise it names them, and you fold them after the merge.
8. Launches the code stage.
```

- [ ] **Step 5: Check the references and the lint**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && \
  grep -n 'Plan stage, step' plugins/my/skills/handoff/SKILL.md; \
  grep -c 'plan review would ask' plugins/my/skills/handoff/SKILL.md; \
  for f in plugins/my/skills/handoff/SKILL.md plugins/my/skills/handoff/README.md; do \
    echo "$f $(markdownlint-cli2 "$f" 2>&1 | grep -c ' error ')"; done
```

Expected: one line, `apply the test in Plan stage, step 4.`; then `0`; then
`SKILL.md 1` and `README.md 0`.

- [ ] **Step 6: Commit**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && \
  git add plugins/my/skills/handoff/SKILL.md plugins/my/skills/handoff/README.md && \
  git diff --cached
git commit -m "feat(my-plugin): my:handoff plan stage reviews before it commits, and commits once

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: The documents that name the steps and the argument

**Files:**

- Modify: `docs/plans/2026-09-21-handoff-spec.md` (D9 at lines 258-288, Risk
  at lines 385-389)
- Modify: `global/CLAUDE.md` (line 58)
- Modify: `README.md` (lines 65-67)
- Modify: `ROADMAP.md` (lines 66-67)

**Interfaces:**

- Consumes: the plan-stage steps from Task 3, step 2.

- [ ] **Step 1: Amend the handoff spec (D5)**

In D9, "Spec stage", change `plan stage step 2 commits it` to
`plan stage step 7 commits it`.

Replace the heading line `**Plan stage.**` and its numbered list (steps 1 to
7) with:

```markdown
**Plan stage.** (Changed 2026-09-30, see the soundness plan-only spec.)

1. Run `superpowers:writing-plans` on the spec. Do not commit the plan yet.
2. Name one execution skill in the plan's header.
3. Run the project's plan review on the uncommitted plan. Under the global
   rules that is `my:soundness-review --plan-only <plan>`. It never asks,
   so other sessions' uncommitted files on `main` do not stop the stage.
4. For each finding, fix it or treat it as a gate, with the test in D3.
5. Stop and notify on any gate: a finding that needs a change to a decision,
   or a spec decision that rests on a false premise. The message names the
   files left uncommitted: the plan, the review and the spec.
6. Check with `git diff HEAD -- <paths>` that the stage's paths (the plan,
   the review, the spec and the plans index) hold only its own changes.
   Stop and notify when one holds another session's edit.
7. Commit these paths, and only these, in one commit:
   `git add -- <paths>`, then `git commit -- <paths>`. The status change goes
   into this commit, so no commit only changes a status.
8. Fold the spec's waiting fixups only when `git status --porcelain` prints
   nothing, after the project's pre-rebase check. A failed check is a gate.
   On a busy `main`, leave them and name them; they are folded after the
   code branch is merged.
9. Finish the project's other docs steps and run the launch with
   `code <plan path>`.
```

In "Risk", delete the whole bullet titled "A busy `main` stops the plan
stage" (five lines, starting at line 385). Keep the `**Status:**` line as it
is.

- [ ] **Step 2: Update the routing line in the global instructions (D6)**

In `global/CLAUDE.md`, line 58, change

```text
with a dirty tree and no range, it asks which.
```

to

```text
with a dirty tree and no range, it asks which; `--plan-only <plan>` reviews the plan on any tree and never asks.
```

- [ ] **Step 3: Update the plugin README (D6)**

In `README.md`, replace the `my:soundness-review` bullet with:

```markdown
- `my:soundness-review` — Gives a for/against verdict on a diff, or checks a
  diff or plan against its plan. `--plan-only <plan>` reviews the plan and
  never asks, even when the tree is dirty. Output: a review in `docs/plans/`.
  Bug-finding goes to the built-in `/code-review`.
```

- [ ] **Step 4: Turn the roadmap follow-up into a shipped note (D6)**

In `ROADMAP.md`, replace the two lines

```markdown
  💭 Follow-up: a `--plan-only` argument for `my:soundness-review`, so a busy
  `main` does not stop the plan stage.
```

with

```markdown
  `my:soundness-review --plan-only` shipped on 2026-09-30, so a busy `main`
  no longer stops the plan stage. Spec:
  [`docs/plans/2026-09-30-soundness-plan-only-spec.md`](docs/plans/2026-09-30-soundness-plan-only-spec.md).
```

The squash commit's hash does not exist yet, and only commits on `main` may
be cited. The step "After the merge" below adds it.

- [ ] **Step 5: Check the lint and the sweep**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && \
  for f in docs/plans/2026-09-21-handoff-spec.md global/CLAUDE.md README.md ROADMAP.md; do \
    echo "$f $(markdownlint-cli2 "$f" 2>&1 | grep -c ' error ')"; done; \
  grep -n 'busy `main` stops\|plan stage step 2\|plan review would ask' docs/plans/2026-09-21-handoff-spec.md
```

Expected: `handoff-spec.md 15` or fewer, `global/CLAUDE.md 71`,
`README.md 0`, `ROADMAP.md 0`. The `grep` prints nothing.

- [ ] **Step 6: Commit**

```bash
cd /home/dchris/projects/claude-setup/.claude/worktrees/soundness-plan-only && \
  git add docs/plans/2026-09-21-handoff-spec.md global/CLAUDE.md README.md ROADMAP.md && \
  git diff --cached
git commit -m "docs(global): name --plan-only in the routing, the README, the roadmap and the handoff spec

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### After the merge: the roadmap hash

This step runs on `main`, in the `done`-mark commit that the `my:handoff`
review stage makes after the squash-merge. It is not a task on the branch.

- [ ] In `ROADMAP.md`, change `shipped on 2026-09-30` to
  `shipped on 2026-09-30 in <hash>`, where `<hash>` is the short hash of the
  squash commit on `main`. Put this edit in the same commit as the spec's and
  this plan's `done` marks.

---

## Trade-Offs

The spec settles the design choices (D1 to D4). This plan adds two of its
own:

- **Headless runs as tests.** Pros: they load the real skill and the real
  reviewer agent, as in earlier plans. Cons: each run that dispatches a
  review takes minutes, and there are 13 runs. A cheaper check that reads
  the skill text would prove nothing about behavior.
- **No end-to-end run of the handoff plan stage.** The spec chose this. Task
  3 step 1 tests the one git behavior the new steps rely on. The first real
  use tests the rest.

## Dependencies

None. No new packages. The tests use `claude`, `git`, `jq` and
`markdownlint-cli2`, which are installed.

## Risk

- **Grounding reads other sessions' edits.** A `--plan-only` review reads the
  working tree, so another session's uncommitted edit can change a
  grounding result. Known limit from the spec.
- **Uncommitted plan after a gate stop.** After a gate, the plan, the review
  and the spec edit sit uncommitted on `main`. Another session's
  `git add -A` could take them. The gate message names the files. Known limit
  from the spec.
- **A rerun after a gate stop fails its start check.** An uncommitted plan
  exists, so the start check stops, and the user decides. Intended.
- **A shared file with another session's edit.** Step 6 reads hunks, so two
  edits inside one hunk look like one. The user's reread of the commit is
  the last protection. Known limit from the spec.
- **Blast radius.** Two files call the skill: `global/CLAUDE.md` and
  `plugins/my/skills/handoff/SKILL.md` (spec, Risk). Only the handoff plan
  stage adds the token. No other caller changes behavior.
- **Tests run the wrong plugin copy.** The installed `my@claude-setup` is a
  cached copy of `main`. `chk` prints the loaded path in every run. A run
  that shows another path is not valid.
- **Headless runs cannot show the question.** `AskUserQuestion` is absent in
  `claude -p`, so the tests see the old code's fallback note, not its
  question. The note is the Red signal. An interactive check of the question
  is not needed: D1 leaves the question's code path unchanged.
- **The headless tests depend on the model's reading.** Found in the code
  stage, 2026-09-30. The old skill guessed that `--plan-only` means "review
  the plan", so `r-dirty` wrote a plan review and was not Red. `r-spec`
  already printed the spec message, because step 1a's table holds it, so
  `g-spec` has no Red. The runs were therefore judged on exact messages,
  with backticks stripped before the `grep`, and `g-dirty` and `g-extra`
  also check that the answer has no "not a flag" guess note. An `r-missing`
  run was added. The model paraphrased a stop message once, so the D3
  paragraph now says a stop prints its message word for word. Every run
  had one or more Bash denials from `acceptEdits` mode, the old code
  included; a run counts when no `Write` or `Agent` call was denied.
- **Found in the review stage, 2026-09-30. Known limits:**
  - An older `-plan-review.md` of the same plan stays untracked when a
    second review writes `-plan-review-2.md`. Today a rerun stops at the
    start check first, because the plan exists, so the plan stage never
    reaches a second review.
  - A review that writes no file prints no `Review written to` line. With
    `--plan-only` and one existing plan, the skill's only stops are the
    mixed-argument stops, which the plan stage never triggers. A failed
    subagent is the remaining case, and step 7's `git add` of the missing
    path then fails loudly.
  - The spec-stop and description-ignored messages appear in more than one
    place in `my:soundness-review`. Each copy sits in the step the model
    reads at that point, so they stay. An edit to one must edit all.
- **Found in the final re-reviews, 2026-09-30. Known limits, not fixed:**
  - **Medium: the review-stage fold rewrites other features' hashes.** The
    fold rebases from the spec commit's parent, so every later commit on
    `main` gets a new hash. A feature merged while this one ran then has
    `done` marks that cite a commit no longer on `main`. The pre-rebase
    check looks only at worktrees, so it does not catch this. A possible
    follow-up: fold in a temporary worktree and move `main` with
    `git update-ref`, at plan-stage step 8.
  - The review stage's step 6 commits the first round's reports, but no
    step names the re-review reports. Uncommitted, they make step 8's
    `git worktree remove` fail. Commit them with the Risk edits.
  - The review stage says "run every command as `cd <worktree> && …`", but
    review step 8 runs in the main checkout: the merge needs it, and the
    fold and the `done` marks come after the worktree is removed.
  - Plan-stage step 7 checks `git show --stat HEAD`. `--stat` shortens long
    paths, and on a busy `main` another commit can land first. Use
    `git show --name-only --format= <hash of the plan commit>`.
  - Review step 8.3 prints "wait for a clean `<base>`" also when the
    pre-rebase check is what failed, and offers no path for a user who does
    not want to wait.
  - The handoff README's plan-stage step 6 leaves out the plans-index row.
  - The fixup search finds only `fixup! <spec subject>`, not `amend!`,
    `squash!` or `fixup! fixup!`. The global rules create none of these.
  - The spec's Out of scope and D5 still say the review stage changes in
    one place, and the handoff spec's D9 review paragraph has no dated
    change note. Plan-stage step 8 has two sentences between the `git log`
    test and "If one does".
- **Hard to reverse:** nothing. All changes are prompt text and docs.

## Testing Strategy

- Task 1 records Red for every new behavior, on a dirty fixture tree.
- Task 2 runs the same arguments after the change. Each run checks the
  loaded plugin path, the permission denials, the number of `Agent` calls,
  the exact message, and the new files under `docs/plans/`.
- The no-token run is a regression guard, the same before and after.
- Task 3 proves `git commit -- <paths>` in a scratch repo.
- Tasks 3 and 4 check the step references and the lint counts.
- The review stage of `my:handoff` runs the end-of-branch reviews.

## Open Questions

None. The spec review's design findings were settled before approval (D5
allows the review-stage reference edit).
