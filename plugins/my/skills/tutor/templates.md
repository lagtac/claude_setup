# Templates

The shapes of the files under `docs/learning/`. Replace every `<…>`.

## curriculum.md

Committed on the learning branch. A map that may change, not a plan:
exercises are titles here, and each one is written only when the student
reaches it.

```markdown
# Curriculum: <topic> through <project>

## Goals

<What the student wants to be able to do at the end, two or three lines.>

## Scope

<What the app does and what it leaves out. Case 3: the part of the code the
student learns through.>

## Modules

1. <Module title>
   - Concepts: <concept>, <concept>
   - Exercises: 01 <short title>, 02 <short title>
2. <Module title>
   - Concepts: <concept>
   - Exercises: 03 <short title>

## Skills

Load these before writing each exercise.

- <plugin:skill, for example modern-web-guidance:chrome-extensions>

## Scopes

Commit scopes for this workspace.

- `<scope>`: <the part of the code>
- `learning`: exercise files, tests and curriculum edits

## Test command

`<the command that runs the tests, for example npm test>`
```

## Exercise file

`docs/learning/exercises/NN-<slug>.md`, committed in the exercise branch's
first commit. It holds no hints: hints are given live.

```markdown
# Exercise NN: <title>

**Goal:** <one sentence>

**Concepts:** <concept>, <concept>

**Support:** <worked example | skeleton | test only>

**Files:** `<path>`, `<path>`

**Done when:** `<command>` passes `<test name>`, `<test name>`.

**Read:** <documentation link>, <documentation link>
```

## progress.md

`docs/learning/progress.md`, never committed: git ignores it (setup step 6).
One copy, whatever branch is checked out.

```markdown
# Progress

## Starting point

- <diagnosis answer>

## Concepts

| Concept | Status |
| --- | --- |
| <concept> | new |

## Review

Practised concepts for recall questions, oldest first.

- <concept>

## Mistakes

- <repeated mistake, in the student's words where possible>

## Exercises

| Exercise | Date | Highest hint | Note |
| --- | --- | --- | --- |
| NN <title> | <YYYY-MM-DD> | <0-5> | <one line> |

## Next

<What the next session starts with.>
```
