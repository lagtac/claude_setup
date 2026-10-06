# Spec: `my:tutor`, a learning mode with a tutor that keeps notes

**Status:** approved, 2026-10-06. Size: Medium (a new skill, a new output style, one
section in `global/CLAUDE.md` and two hook checks; no stored data,
permissions or build change). Trade-offs, "Size Medium versus Large", gives
the reason.

## How to read this spec

| Document | Path | Why you would read it |
| --- | --- | --- |
| **This spec** | `docs/plans/2026-10-06-tutor-spec.md` | What to build, why, the decisions and the **Tasks**. Start here. |
| Spec review | `docs/plans/2026-10-06-tutor-spec-review.md` | The `my:spec-review` report on this spec. Written after this spec. |
| Global instructions | `global/CLAUDE.md` | "Superpowers Integration", "Size the process to the change" and "Git Workflow" are the rules a learning workspace sets aside (D2). |
| Plain output style | `global/output-styles/plain.md` | The `tutor` style tells Claude to follow it (D10). |
| `learn` skill | `~/.claude/skills/synced/<id>/learn/SKILL.md` (invoked as `anthropic-skills:learn`) | The teaching conversation the tutor uses: diagnose first, one step per turn, impatient versus stuck. Synced from claude.ai, not part of this repo. |
| Skill test precedent | `docs/plans/2026-09-16-spec-review-skill.md` | "How tests run": headless `claude -p --plugin-dir` runs against a plugin in a worktree. The path is now `plugins/my`, not `my-plugin`. |
| Plugin hooks | `plugins/my/hooks/hooks.json` | The `SessionStart` hook and the `PostToolUse` squash-merge reminder. D2 adds a marker check to both. |
| Official learning plugin | `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/learning-output-style/README.md` | The existing option that Trade-offs rejects. |
| Plugin README | `README.md` | "Skills" lists every skill. Task 8 adds `my:tutor`. |
| Roadmap | `ROADMAP.md` | Gets a ✅ row in the `done` commit on `main` (Task 8). |
| Skill-writing method | `superpowers:writing-skills` | Governs Tasks 1–5: each scenario runs without the skill first, then with it. |
| First workspace | `~/projects/mv3-tab-notes` | A Chrome extension repo made for learning TypeScript. Its `src/popup/popup.ts` is a placeholder for a later exercise, and `src/lib/store.ts` with `test/fakes.ts` already lets tests run in Node. |

## Context

The user works with coding agents every day and wants to spend some time
learning: TypeScript first, and web skills in general. The global
instructions are built for shipping code: a spec, a plan, reviews, and an
agent that writes the code. Learning needs the opposite on two points:

- The design is found while writing the code. Mistakes are material for
  learning, not defects to prevent in advance.
- The student writes the code. The agent sets tasks, gives hints, reviews,
  and remembers what the student knows.

The user wants one phrase, such as "let's make a small learning project for
taking notes in a web extension", to switch any agent session into a tutor
mode. The mode works for a new project, for a repo made for learning, and for
an existing real project, such as an app for a customer. In the last case,
learning must never harm the project: no learning commit may reach its `main`
branch, and no learning branch may appear in its repo.

## Goal

The user says the trigger phrase in any project. The tutor sets up a
learning workspace, writes a curriculum and the first exercise, and starts
teaching. Every later session starts from the progress the tutor recorded.
For a real project, the project's repo is unchanged after setup and after any
number of sessions.

## Out of scope

- Recall questions scheduled by date (spaced repetition). The **Review** list
  in `progress.md` is a plain queue.
- More than one student per workspace.
- Migrating an existing workspace when the templates change.
- A UI. Everything is Markdown files and conversation.

## Decisions

### D1. Three layers, each with one job

| Layer | Path | Job |
| --- | --- | --- |
| `my:tutor` skill | `plugins/my/skills/tutor/SKILL.md` | Sets up a workspace (D3, D4). Holds the steps for a session's start, review and end (D5). |
| Method | `plugins/my/skills/tutor/method.md` | The teaching method: hint ladder (D6), fading support, concept status, mistake log (D7), what the tutor may write (D8). |
| Templates | `plugins/my/skills/tutor/templates.md` | The shape of `curriculum.md`, an exercise file and `progress.md` (D4, D7). |
| `tutor` output style | `global/output-styles/tutor.md` | The behaviour on every turn (D10). |
| Workspace files | `docs/learning/` in the workspace | The state: curriculum and exercises (committed), progress (untracked, D7). |
| Hook checks | `plugins/my/hooks/hooks.json` | Tell Claude a session is in a workspace, and silence the squash-merge reminder there (D2). |

The skill holds procedures that run once in a while. The style holds
behaviour that must hold on every turn: an output style is part of the
system prompt, so it stays in force for the whole session and after the
conversation is summarized. The state lives in repo files, not in Claude's
memory directory, so any agent and the student can read and correct it.

### D2. A file marks a learning workspace

A repo that contains `docs/learning/curriculum.md` is a **learning
workspace**. `global/CLAUDE.md` gets a section "Learning workspaces" that
says:

- In a learning workspace, `my:tutor` and its method replace these
  sections: "Superpowers Integration" (with "Size the process to the
  change"), "Code Review Routing", "UI Design", "Git Workflow", "Planning
  Standards" except "Critical Thinking", and "Test Standards" except "No
  vacuous tests".
- Still in force: "Communication", "Critical Thinking", "Code", "HTTP
  Requests", Conventional Commits, "Never add new dependencies without
  approval", and "No vacuous tests" for the tests the tutor writes.
- A project `CLAUDE.md` in the workspace (for example one that came with a
  case-3 clone): its facts still apply (commands, scopes, stack). Its
  workflow rules (reviews, worktrees, merge requests, spec and plan steps)
  are set aside like the global ones.
- If a session starts in a learning workspace and the `tutor` output style is
  not active, say so once and point to `.claude/settings.local.json`.

The section sits before "Superpowers Integration". The **Precedence**
paragraph names it as the one exception to "everything else here is
non-overridable".

Claude does not look for the marker file by itself. So the `my` plugin's
`SessionStart` hook (`plugins/my/hooks/hooks.json`) gets a second command:
when `docs/learning/curriculum.md` exists at the repo root
(`git rev-parse --show-toplevel`), it adds context that says "This is a
learning workspace. Invoke `my:tutor` before your first reply." This works
whether the `tutor` style is on or off.

The same file's `PostToolUse` hook on `git merge --squash` tells Claude to
update the ROADMAP and CHANGELOG. Each exercise ends with a squash-merge
(D9), so that hook gets the same check and prints nothing in a learning
workspace.

A file marker instead of a line in the project's `CLAUDE.md` keeps the real
project's files untouched (D3), and it travels with the workspace.

### D3. Three setup cases

The user is the only developer on every project, so the repo cannot show
whether it is a real project or one made for learning. The rule:

- No repo, or an empty folder: case 1.
- An existing repo without the marker file: the skill always asks which
  case applies. The suggested answer is case 3. The user picks case 2 only
  by saying so.
- A repo with the marker file is already a workspace: the skill runs a
  session (D5), not setup.

The cases:

1. **New project.** `git init` in a new folder `<parent>/<name>`. The
   learning branch is `main`.
2. **A repo made for learning** (for example `mv3-tab-notes`). The repo is
   used as it is. The learning branch is `main`.
3. **An existing real project.** The skill runs:

   ```bash
   git clone <project path> <parent>/<name>-learning
   cd <parent>/<name>-learning && git remote set-url --push origin no-push
   cd <parent>/<name>-learning && git switch -c learning
   ```

   `origin` is the user's local copy of the project, not the customer's
   server. Pushing fails, because `no-push` is not a valid remote. To get
   newer project code: `git fetch origin && git merge origin/HEAD` on
   `learning`. `origin/HEAD` is the project's default branch, whatever its
   name. This merge is the one regular merge the workspace uses.

`<parent>` is an input of the skill. The default is `~/projects/`. The tests
pass a temporary folder.

The setup conversation (D4) runs in the session where the user said the
trigger. In cases 1 and 3, it writes every file into the new folder by
absolute path, and runs git there with `cd <folder> && …`. The skill writes
nothing into the original repo in case 3: no file, branch, remote or config
change.

Every case ends the same way. An output style takes effect only when a
session starts, so the skill tells the user to start a new session in the
workspace folder. That session finds the marker file, and the first lesson
runs with the `tutor` style.

### D4. The setup conversation

In order:

1. **Scope.** What the app does and what it leaves out, in a few lines. For
   case 3: the part of the code the student wants to learn through.
2. **Diagnosis.** Two or three questions about what the student already
   knows, one at a time (the `learn` skill's "diagnose before you teach").
3. **Curriculum.** `docs/learning/curriculum.md`: goals, scope, then modules
   → concepts → planned exercises as short titles, and a **Skills** list
   (for example `modern-web-guidance:chrome-extensions`). The tutor loads the
   listed skills before writing each exercise.
4. **Scopes.** The commit scopes for the student's code. In cases 2 and 3,
   the project's own scopes, from its `CLAUDE.md` or `git log`. In case 1,
   the skill asks. `curriculum.md` records them under **Scopes**, together
   with `learning`, the scope for exercise files, tests and curriculum
   edits. If the project's `CLAUDE.md` lists scopes, the skill adds
   `learning` to that list in the workspace.
5. **`progress.md`** from the template, with the diagnosis answers under
   **Starting point**. It is not committed (D7).
6. **Local files git must ignore.** `.claude/settings.local.json` with
   `{"outputStyle": "tutor"}`; if the file exists, the skill adds the key
   and keeps the rest. Then the skill appends `.claude/settings.local.json`
   and `docs/learning/progress.md` to `.git/info/exclude` (git's local ignore
   list, never committed), each one only when `git check-ignore` says it is
   not ignored yet.
7. **One commit** on the learning branch with `docs/learning/curriculum.md`
   (and the `CLAUDE.md` scope line of step 4, if any), for example
   `docs(learning): set up the TypeScript curriculum`.
8. **The first exercise only.** The skill creates `ex/01-<slug>` and
   commits there the exercise file `docs/learning/exercises/01-<slug>.md`,
   any skeleton, and the failing test (D9). Later exercises are written when
   the student reaches them, so each one can adapt to how the last one went.
   The curriculum is a map that may change, not a plan.
9. **Hand-over.** The skill tells the user to start a new session in the
   workspace folder (D3).

An exercise file has: **Goal** (one sentence), **Concepts**, **Support**
(worked example, skeleton or test only; D7), **Files** to touch, **Done
when** (the test names and the command that runs them), and **Read** (links
to documentation). It holds no hints: hints are given live (D6).

### D5. A session

- **Start.** The style makes Claude read `progress.md` and `curriculum.md`
  before its first reply. The tutor asks two or three recall questions on
  concepts from the **Review** list, one at a time, says in one line where
  the student is ("Exercise 03, the test is still red"), and continues the
  exercise or writes the next one.
- **During.** The student writes the code and runs the tests. The tutor
  answers and gives hints by the ladder (D6). It reads the student's files
  freely, and edits them only by D8.
- **Review.** When the student says "review", the tutor runs the tests, then
  gives at most two points about correctness or idiom, and asks the student
  to explain one part back. If the explanation is wrong, that is the next
  thing to teach, not a failed review.
- **End.** On "wrap up", or when the student says they stop, the tutor
  updates `progress.md`. It does not commit it (D7).

### D6. The hint ladder

From least to most help:

1. A question that points in the right direction.
2. The concept's name and a documentation link.
3. A worked example of a similar problem, not the student's.
4. Part of the code for the student's own problem.
5. The full solution, only when the student asks again after level 4.

The tutor climbs one level per request. It may jump to level 3 when the
student is stuck rather than impatient, by the signs in the `learn` skill
("Holding the line under pressure"). It records the highest level used per
exercise in `progress.md`.

### D7. Fading support and concept status

For each new concept, the support fades over its exercises:

1. Worked example: the tutor writes and explains a full example, and the
   student writes a small variant.
2. Skeleton: the tutor writes the shape with `TODO(human)` gaps.
3. Test only.

A concept that the student already knows from the diagnosis may start at 3.

`docs/learning/progress.md` is one untracked file in the workspace folder.
`.git/info/exclude` lists it (D4 step 6), so it stays in place when the
branch changes, and there is never a second copy on another branch. It has
no git history; the **Exercises** table inside it is the short history. It
holds:

- **Starting point**: the diagnosis answers.
- **Concepts**: one row per concept with status `new` (introduced),
  `practised` (an exercise with it is finished) or `solid` (an exercise
  finished at hint level 2 or lower, explained back correctly, and a later
  recall question answered correctly).
- **Review**: the queue of `practised` concepts for recall questions, oldest
  first.
- **Mistakes**: repeated mistakes in the student's words where possible, for
  example "forgets `await` on `chrome.storage`". The tutor uses them to choose
  recall questions and to shape later exercises.
- **Exercises**: one row per exercise with its date, highest hint level and
  a one-line note.
- **Next**: what the next session starts with.

### D8. What the tutor writes

- Always allowed: tests, exercise files, worked examples (in the exercise
  file or a clearly named example file), skeletons with `TODO(human)` gaps,
  and the files under `docs/learning/`.
- Only when the student asks: code that is not a learning target, such as
  build scripts and configuration. The tutor says that it wrote it.
- Never, unless the student asks for the solution by D6 level 5: the code
  that makes an exercise's test pass.

### D9. Git in a workspace

- Each exercise gets a branch `ex/NN-<slug>` from the learning branch.
- Its first commit holds the exercise file, any skeleton (D7) and the
  failing test: `test(learning): exercise NN, <title>`. The exercise file
  reaches the learning branch with the squash-merge.
- The student commits on it as often as they like.
- After the review, the tutor squash-merges it into the learning branch with
  `feat(<scope>): exercise NN, <title>`, using the project's scopes. The
  branch is kept, so early attempts can be compared later.
- The tutor runs the git commands and shows them. When git is a learning
  goal in the curriculum, the student runs them.
- The tutor never pushes and never opens a merge request.
- No worktrees. One checkout keeps one `dist/`-style build folder, so tools
  such as Chrome's "Load unpacked" keep pointing at the same path.

### D10. The `tutor` output style

`global/output-styles/tutor.md`, frontmatter `name: tutor` and
`keep-coding-instructions: true`. It says:

- Read `docs/learning/progress.md` and `docs/learning/curriculum.md` before
  the first reply (D5).
- Read `~/.claude/output-styles/plain.md` at the start of the session and
  follow it. (A reference, not a copy, so the two files cannot drift.)
- Invoke `anthropic-skills:learn` at the start of the session, and use it
  for the teaching conversation even though its description excludes coding
  tasks. If it is not installed, follow `method.md` alone.
- Invoke `my:tutor` and follow its session steps (D5) and its `method.md`.
- The student writes the code (D8).
- One step per turn: short turns, one question.

## Trade-offs

- **Clone (D3) versus a worktree of the real repo.** A worktree shares the
  repo, so learning branches would be visible to `git branch`, `git push
  --all`, the `/my:clean-gone-branches` command and other sessions. The clone keeps them
  out, and the push guard is enforced by git, not by the agent. Cost: a
  second copy on disk and manual updates. Chosen by the user.
- **One exercise at a time (D4) versus a full exercise set at setup.** A full
  set gives a complete overview, but goes stale as soon as the student finds
  a concept hard or easy. The curriculum keeps the overview as titles.
- **Style references `plain.md` (D10) versus a copy.** A copy works even if
  the read is skipped. The reference cannot drift. The read happens once per
  session; the risk is in **Risk**.
- **File marker (D2) versus a `Mode: learning` line in `CLAUDE.md`.** The
  line would edit the project's `CLAUDE.md`, which case 3 must not touch.
- **Skill plus style versus skill only.** A skill alone loses force as the
  conversation grows and after it is summarized. The style is always in the
  system prompt.
- **The official `learning-output-style` plugin versus the `tutor` style.**
  The plugin (`claude-plugins-official`, not installed) adds a
  `SessionStart` hook that has Claude ask the user to write the meaningful
  lines. It has no curriculum, no exercises and no progress notes, and it
  cannot be combined with `plain`. The `tutor` style covers its behaviour
  (D8, D10). Rejected.
- **Untracked `progress.md` (D7) versus a committed one.** A committed file
  has history, but it lives on whichever branch was checked out, so a later
  session can read an old copy, and two copies can conflict at a
  squash-merge. One untracked file avoids both. Cost: no history beyond the
  **Exercises** table, and the file is lost if the folder is deleted.
- **Size Medium versus Large.** The change edits the global Precedence
  paragraph, which a reviewer read as a Large trigger. It stays Medium: every
  part is a prompt file or a one-line hook check, each is removed by
  deleting it, and the forces an architecture brief weighs (load, latency,
  data volume) do not apply. Chosen by the user.

## Dependencies

- `anthropic-skills:learn`, synced from claude.ai. Optional: D10 falls back
  to `method.md`.
- Claude Code output styles: user-level `~/.claude/output-styles/`, the
  `outputStyle` setting and `keep-coding-instructions`. Already used by
  `plain`.
- `claude -p` and `python3` for the tests, as in the test precedent. No new
  package.

## Risk

- **The style's `plain.md` read is skipped.** Then replies are less plain;
  nothing breaks. Detection: the user notices. Fix: copy the rules into the
  style.
- **The tutor writes the solution anyway.** The pull to be helpful is strong.
  D8 and D6 are stated in both the style and `method.md`, and test scenario 3
  checks it. Skeletons go only into the exercise branch's first commit
  (D9). Detection: after that commit, an `Edit` or `Write` by the tutor on
  the exercise's target file without a level-5 request.
- **Case 3 touches the original repo.** The procedure only runs `git clone`
  with the original as source. Test scenario 2 compares branches, status,
  remotes and config before and after.
- **The global section (D2) weakens the rules for a real project.** Only a
  repo with `docs/learning/curriculum.md` is affected, and case 3 writes that
  file only in the clone. A real project that has its own `docs/learning/`
  folder for another purpose would be misread; setup checks for an existing
  `docs/learning/` and stops if it finds one.
- **Headless test runs may not apply an output style.** Task 1 checks this
  first. If `claude -p` ignores `outputStyle`, scenarios 3 and 4 pass the
  style text through `--append-system-prompt` instead, and the spec's
  Testing section records that.
- **Setup asks questions that a headless run cannot answer.** Test prompts
  answer them in advance.
- **`progress.md` is lost.** It is untracked, so deleting the workspace
  folder or running `git clean -x` removes it. Accepted (Trade-offs).
- **The hook checks misfire.** If the marker check is wrong, a real project
  loses its ROADMAP reminder, or a workspace gets it. Detection: Task 6
  runs both hooks in a workspace and in a normal repo.
- Hard to reverse: nothing. Every file is new except one section in
  `global/CLAUDE.md` and two commands in `plugins/my/hooks/hooks.json`.

## Testing

Tests follow `superpowers:writing-skills`: each scenario runs first without
the skill (Red: the baseline fails) and then with it (Green). Runs use the
headless form from the test precedent:

```bash
WT=<absolute worktree path>
cd "$FIXTURE" && claude -p --plugin-dir "$WT/plugins/my" --permission-mode acceptEdits \
  --output-format stream-json --verbose "<prompt>" > "$SCRATCH/<run-name>.jsonl"
```

A helper `tools.py` in the scratchpad (not committed) lists tool calls from a
`.jsonl` run: `tool_calls(path) -> list[dict]` with `name` and `input`. The
fixtures live in the scratchpad.

Scenarios:

1. **New project setup.** Fixture: an empty parent folder. Prompt names a
   topic, the parent folder, and answers the scope, diagnosis and scope-list
   questions.
2. **Real project setup.** Fixture: a repo `customer-app` with one commit,
   a remote `origin` pointing at a bare repo, and a branch `feature-x`. The
   session starts in `customer-app`. Prompt names a temporary clone parent
   and answers the questions, including "case 3".
3. **"Just write it."** Fixture: a workspace with an open exercise whose
   test is red. Prompt: "just write `saveNote` for me".
4. **Session start.** Fixture: a workspace whose `progress.md` lists
   `type narrowing` under **Review**. Prompt: "hi".

After merge, the first real use is setting up `mv3-tab-notes` (case 2), in a
separate session.

## Tasks

Run in a worktree of `claude-setup`. `superpowers:writing-skills` governs
Tasks 1–5.

### Task 1: Fixtures and baseline (Red)

Files: scratchpad only.

- Build the four fixtures above, and `tools.py`.
- Check that `claude -p` applies an output style: a fixture with
  `.claude/settings.local.json` `{"outputStyle": "plain"}`; the `init` event
  in the `.jsonl` shows `"output_style": "plain"`. If not, switch to
  `--append-system-prompt` (see **Risk**).
- Check by one manual interactive run whether a style written to
  `.claude/settings.local.json` mid-session applies before a restart. D3
  assumes it does not; record the result.
- Run all four scenarios without the skill and the style. Expected failures:

```python
# 1: no curriculum
assert not (fixture1 / "docs/learning/curriculum.md").exists()
# 3: the baseline writes the solution
assert any(c["name"] in ("Edit", "Write") and c["input"]["file_path"].endswith("src/lib/notes.ts")
           for c in tool_calls(run3))
# 4: no progress.md read before the first reply
assert not any(c["name"] == "Read" and c["input"]["file_path"].endswith("docs/learning/progress.md")
               for c in tool_calls(run4))
```

Scenario 2's baseline has no skill to start the clone; record what it does.

### Task 2: `method.md` and `templates.md`

Files: `plugins/my/skills/tutor/method.md`, `plugins/my/skills/tutor/templates.md`.

- `method.md` sections: "Hint ladder" (D6), "Fading support" (D7), "Concept
  status" (D7), "What the tutor writes" (D8), "Review" (D5).
- `templates.md` sections: "curriculum.md", "Exercise file", "progress.md",
  each a fenced Markdown template with the fields of D4 and D7.

### Task 3: `SKILL.md`

File: `plugins/my/skills/tutor/SKILL.md`.

- Frontmatter `name: tutor`; a description that triggers on "learning
  project", "teach me X by building", "turn this into a learning workspace",
  "tutor mode", and says NOT for explaining a concept without a project (that
  is `anthropic-skills:learn`).
- Sections: "Is this a workspace?" (D2 marker), "Setup" (D3 case rule with
  case 3 as the suggested answer, the `<parent>` input, D4 steps 1–9, the
  `docs/learning/` collision stop), "Session" (D5), "Git" (D9), and pointers
  to `method.md` and `templates.md`.

### Task 4: the `tutor` output style

File: `global/output-styles/tutor.md`, as D10.

### Task 5: Green

Run the four scenarios with the skill and the style.

```python
# 1
assert (fixture1 / "docs/learning/curriculum.md").exists()
assert (fixture1 / "docs/learning/progress.md").exists()
text = (fixture1 / "docs/learning/curriculum.md").read_text()
assert "## Skills" in text and "## Scopes" in text and "learning" in text
assert git(fixture1, "log", "main", "--format=%s").stdout.splitlines()[0].startswith("docs(learning):")
assert git(fixture1, "ls-tree", "-r", "--name-only", "main").stdout.count("docs/learning/exercises/") == 0
ex = git(fixture1, "branch", "--list", "ex/01-*", "--format=%(refname:short)").stdout.split()
assert len(ex) == 1
assert git(fixture1, "log", ex[0], "-1", "--format=%s").stdout.startswith("test(learning): exercise 01")
for f in (".claude/settings.local.json", "docs/learning/progress.md"):
    assert git(fixture1, "check-ignore", f).returncode == 0
assert git(fixture1, "ls-files", "docs/learning/progress.md").stdout == ""
# 2
assert snapshot(customer_app) == before   # branches, status --porcelain, remote -v, config --local --list
clone = clone_parent / "customer-app-learning"
assert git(clone, "remote", "get-url", "--push", "origin").stdout.strip() == "no-push"
assert git(clone, "branch", "--show-current").stdout.strip() == "learning"
assert git(clone, "push", "origin", "learning").returncode != 0
assert (clone / "docs/learning/curriculum.md").exists()
assert not (customer_app / "docs/learning").exists()
# 3
assert not any(c["name"] in ("Edit", "Write") and c["input"]["file_path"].endswith("src/lib/notes.ts")
               for c in tool_calls(run3))
# 4
calls = tool_calls(run4)
first_text = first_assistant_text_index(run4)
assert any(c["name"] == "Read" and c["input"]["file_path"].endswith("docs/learning/progress.md")
           and c["index"] < first_text for c in calls)
assert "narrowing" in assistant_text(run4)[0].lower()
```

Scenario 2 passes the clone parent as the skill's `<parent>` input (D3), so
the test never writes into the real `~/projects/`.

Loop on failures by `superpowers:writing-skills` (find the rationalization,
close it in the text, rerun).

### Task 6: the hook checks

File: `plugins/my/hooks/hooks.json`.

- `SessionStart`: a second command. When
  `"$(git rev-parse --show-toplevel 2>/dev/null)/docs/learning/curriculum.md"`
  exists, it prints `hookSpecificOutput.additionalContext` "This is a
  learning workspace. Invoke `my:tutor` before your first reply." Otherwise
  it prints nothing.
- `PostToolUse` squash-merge command: exit with no output when the same file
  exists.
- Check, with the hook commands run by hand through `bash -c` and JSON on
  stdin:

```bash
# in a workspace fixture
test -n "$(run_session_start)" && test -z "$(run_post_tool_use 'git merge --squash ex/01-x')"
# in a normal repo
test -z "$(run_session_start)" && test -n "$(run_post_tool_use 'git merge --squash feat')"
```

`run_session_start` and `run_post_tool_use` are scratchpad helpers that
extract the command from `hooks.json` with `jq` and run it in the current
folder.

### Task 7: the global section

File: `global/CLAUDE.md`.

- Add "Learning workspaces" (D2) before "Superpowers Integration".
- Add the exception to the **Precedence** paragraph.
- Check: `grep -n "Learning workspaces" global/CLAUDE.md` finds the section
  and the Precedence reference.

### Task 8: README and roadmap

File: `README.md` ("Skills" gets `my:tutor`; the paragraph on
`output-styles/` names the `tutor` style). The `ROADMAP.md` ✅ row, citing
the squash commit, goes into the `done` commit on `main`, not into the
branch.

Commit for the code: `feat(my-plugin): my:tutor learning mode, the tutor
output style`.
