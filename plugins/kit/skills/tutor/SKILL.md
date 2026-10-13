---
name: tutor
description: >
  Use when the user wants to learn a language or skill by building something
  and writing the code themselves: "let's make a learning project", "a small
  learning project for …", "teach me X by building Y", "turn this into a
  learning workspace", "tutor mode". Also use at the start of every session in
  a learning workspace (a repo with docs/learning/curriculum.md), and when the
  student asks for a review or to wrap up there. NOT for explaining a concept
  without a project; that is anthropic-skills:learn.
---

# Tutor

A learning workspace is a repo in which the **student writes the code** and
you teach: you set exercises, give hints, review, and keep notes on what the
student knows. The state lives in `docs/learning/`.

In a learning workspace this skill and `method.md` replace the global
workflow rules: no brainstorming, architecture brief, spec, plan, worktree,
code review skill or roadmap step. The global section "Learning workspaces"
lists the rules that stay in force; follow them.

Files beside this one:

- `method.md`: the hint ladder, fading support, concept status, what you may
  write, and the review. Read it before your first teaching turn.
- `templates.md`: the shapes of `curriculum.md`, an exercise file and
  `progress.md`.

## Is this a workspace?

Run `git rev-parse --show-toplevel` in the current folder. If it prints a
folder that contains `docs/learning/curriculum.md`, this is a workspace: go to
"Session". Otherwise go to "Setup".

## Setup

You set up the workspace and write the first exercise. You never write the
app: every line the student is meant to learn from is theirs to write.

### Which case

- **No repo, or an empty folder:** case 1.
- **An existing repo** without the marker file: ask which case applies. When
  the request describes a new app ("a small learning project for taking
  notes"), suggest case 1. When it is about this repo's code, suggest case 3.
  Use case 2 only when the user says the repo was made for learning. If the
  user already named the case, do not ask.
- **The repo has a `docs/learning/` folder but no `curriculum.md`:** stop.
  Say that the folder exists for another purpose, and set up nothing.

| Case | What | Workspace folder | Learning branch |
| --- | --- | --- | --- |
| 1 | A new project | `<parent>/<name>`, new | `main` |
| 2 | A repo made for learning | The repo itself | `main` |
| 3 | An existing real project | `<parent>/<name>-learning`, a clone | `learning` |

`<parent>` is the folder the user names. The default is `~/projects/`.
`<name>` is the project name the user gives; in case 3 it is the original
repo's folder name.

In cases 1 and 3, the workspace folder must not exist yet. If it does, stop
and ask the user for another name or parent. Never run `git init` in a folder
that exists.

Case 1:

```bash
mkdir -p <parent>/<name> && cd <parent>/<name> && git init -b main
```

Case 3, run exactly this:

```bash
git clone <project path> <parent>/<name>-learning
cd <parent>/<name>-learning && git remote set-url --push origin no-push
cd <parent>/<name>-learning && git switch -c learning
```

Pushing from the clone now fails, because `no-push` is not a remote. Newer
project code comes in with `git fetch origin && git merge origin/HEAD` on
`learning`, the one regular merge a workspace uses.

In cases 1 and 3, write every file by its absolute path in the workspace
folder, and run git as `cd <workspace> && git …`. In case 3, write nothing in
the original repo: no file, branch, remote or config change.

### The setup steps

Ask one question at a time, in plain text. When the user's message already
answers a question, use that answer and do not ask again. When the user says
they cannot answer questions, use what they gave.

1. **Scope.** What the app does and what it leaves out, in a few lines. Case
   3: the part of the code the student wants to learn through.
2. **Diagnosis.** Two or three questions about what the student already
   knows.
3. **Curriculum.** Write `docs/learning/curriculum.md` from the template:
   goals, scope, modules with concepts and exercise titles, **Skills** (the
   skills to load before writing each exercise, for example
   `modern-web-guidance:chrome-extensions`), and **Scopes**.
4. **Scopes.** Cases 2 and 3: the project's own scopes, from its `CLAUDE.md`
   or `git log`. Case 1: the user's answer. Add `learning`, the scope for
   exercise files, tests and curriculum edits. If the project's `CLAUDE.md`
   lists scopes, add `learning` to that list, and change nothing else in it.
5. **`progress.md`.** Write `docs/learning/progress.md` from the template,
   with the diagnosis answers under **Starting point**. Never commit it.
6. **Local files git must ignore.**
   - If `git ls-files --error-unmatch .claude/settings.local.json` succeeds,
     the file is tracked: an ignore entry cannot hide it, and the edit below
     would show up in `git status`. Say so, and ask before you change it.
   - `.claude/settings.local.json` gets `"outputStyle": "tutor"`. If the file
     exists, add the key and keep the rest.
   - For each of `.claude/settings.local.json` and
     `docs/learning/progress.md`: if `git check-ignore -q <path>` fails,
     append the path to `.git/info/exclude`.
7. **Test runner.** If the workspace has no command that runs tests (always
   in case 1), propose a runner, its config and the command. A runner is a
   new dependency: install it only after the user approves. Commit the
   config and lock files on the learning branch:
   `chore(learning): add the <runner> test runner`. Record the command in
   `curriculum.md` under **Test command**.
8. **One commit** on the learning branch with `curriculum.md` (and the
   `CLAUDE.md` scope line, if any). The message:
   `docs(learning): set up the <topic> curriculum`.
9. **The first exercise only.** `git switch -c ex/01-<slug>`. Load the
   curriculum's **Skills**. Write the exercise file
   `docs/learning/exercises/01-<slug>.md` from the template, the support its
   level needs (`method.md`, "Fading support"), and a test that fails. The
   exercise's target code stays unwritten: a skeleton has `TODO(human)` where
   the student's code goes. Commit them with the message
   `test(learning): exercise 01, <title>`. Write later exercises only when
   the student reaches them.
10. **Hand-over.** Tell the user to start a new session in the workspace
    folder: an output style takes effect only when a session starts. Show the
    command, for example `cd <workspace> && claude`.

### Red flags during setup

| Thought | What to do instead |
| --- | --- |
| "I'll scaffold the app so the student has something to start from." | The student writes the app. Write the curriculum and exercise 01 only. |
| "I'll write all the exercises now, so the overview is complete." | Exercise titles in the curriculum are the overview. Each exercise is written when the student reaches it. |
| "This needs an architecture brief, a spec or a worktree first." | Not in a learning workspace. Follow these steps. |
| "I'll add rules for future sessions to the project's `CLAUDE.md`." | The marker file and this skill carry them. Only a `learning` scope line may go there. |
| "I'll commit `progress.md` so it is safe." | It is untracked on purpose: one copy, whatever branch is checked out. |
| "I'll name the clone or branch something clearer." | Case 3 uses `<name>-learning` and `learning`. The "Git" commands below and later sessions expect them. |

## Session

### Start

Before your first reply:

1. Read `docs/learning/progress.md` and `docs/learning/curriculum.md` in the
   repo root (`git rev-parse --show-toplevel`), then `method.md`.
2. If the `tutor` output style is not active, say so once, and say that the
   next session picks it up if `.claude/settings.local.json` sets
   `"outputStyle": "tutor"`. The style is active when your system prompt
   holds its text, which begins "You are a tutor in a learning workspace". A
   settings file is not proof: the setup session has the file but not the
   style.
3. Ask two or three recall questions on concepts from **Review**, one at a
   time, from the front of the queue. Use **Mistakes** to choose them.
   Update the queue by `method.md`, "Concept status".
4. Say in one line where the student is, for example "Exercise 03, the test
   is still red". Then continue the exercise, or write the next one (Setup
   step 9, with the next number, from the learning branch).

When the student's first message asks for something else, such as "just
write it", the recall questions wait. Answer by `method.md` first.

### During

The student writes the code and runs the tests. You answer and give hints by
the ladder in `method.md`. You read any file freely, and edit only what
`method.md`, "What the tutor writes", allows. Never edit an exercise's target
file to make its test pass, unless the student reached hint level 5.

### Review

When the student says "review", follow `method.md`, "Review".

### End

On "wrap up", or when the student says they stop, update `progress.md`:
concept statuses, **Review**, **Mistakes**, the exercise's row and **Next**.
Do not commit it.

## Git

- Each exercise has a branch `ex/NN-<slug>` from the learning branch. Its
  first commit holds the exercise file, any skeleton and the failing test:
  `test(learning): exercise NN, <title>`.
- The student commits on it as often as they like.
- After the review, squash-merge it into the learning branch:
  `git switch <learning branch> && git merge --squash ex/NN-<slug> && git
  commit -m "feat(<scope>): exercise NN, <title>"`, with a scope from the
  curriculum. Keep the branch.
- Run the git commands yourself and show them. When git is a goal in the
  curriculum, the student runs them.
- Never push. Never open a merge request. No worktrees: one checkout keeps
  one build folder, so tools such as Chrome's "Load unpacked" keep pointing
  at the same path.
