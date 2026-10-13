---
name: setup
description: >
  Switch a project to the my method or the tutor method: write the import
  line (and, for my, a "## Project facts" block) into its CLAUDE.md, set the
  plugin switch in its .claude/settings.json, and commit the two files in that
  project's repo. Takes `<method> [<project path>]`, where method is `my` or
  `tutor` and the path defaults to the current repo root. Use when the user
  types /kit:setup, asks to "set up the my method" or "switch this repo to
  tutor", or when the method guard says to run /kit:setup my. NOT for outside
  methods: they bring their own setup.
---

# Setup a method

A project picks its method with two switches that this skill writes:

| Method | `CLAUDE.md` | `.claude/settings.json`, under `enabledPlugins` |
| --- | --- | --- |
| `my` | A `## Project facts` block, then the line `@~/.claude/methods/my.md` | `"my@claude-setup": true`, `"superpowers@synced": true` |
| `tutor` | The line `@~/.claude/methods/tutor.md` | No key that turns `my@claude-setup` or `superpowers@synced` on |

`~/.claude/methods/` is a link to the method files in the `claude-setup`
repo. Both plugins are off at user scope, so a project without these switches
runs neither. The `kit` method guard, a SessionStart hook, warns when the
switches disagree.

This skill does not read the user's `CLAUDE.md` files. Everything it needs is
written here.

## Arguments

`/kit:setup <method> [<project path>]`

- `<method>`: `my` or `tutor`.
- `<project path>`: the project to set up. Default: the current repo root,
  `git rev-parse --show-toplevel`. So one session can set up several
  projects in a row.

On any other arguments, print
`Usage: /kit:setup <my|tutor> [<project path>]` and stop.

Resolve the path to its repo root with
`git -C <path> rev-parse --show-toplevel`. If that fails, the path is not in
a git repo: say so and stop. Only a repo can take the setup commit. From here
on, `<path>` is that root, and every command runs as `git -C <path> …` or
reads files under `<path>`.

## Steps for `my`

### 1. Find the facts in the repo

Read each fact from the repo. Ask the user only about a fact the repo does
not show, in one question.

- **Commit scopes:** the scopes in recent subjects:
  `git -C <path> log --format=%s -300 | sed -nE 's/^[a-z]+\(([^)]+)\)!?:.*/\1/p' | sort | uniq -c | sort -rn`.
  If no subject has a scope, the value is `none (type: only)`.
- **Test command:** the `test` script in `package.json` (as `npm test`, or
  the package manager the lock file shows), the `test` script in
  `composer.json`, or a `test` target in a `Makefile`. If none, ask; the
  value may be `none`.
- **Plans index:** `docs/plans/README.md` if it exists, else `none`.
- **Remote:** `git -C <path> remote -v`. Write the name and host, such as
  `origin (gitlab.com)`, or `none`.
- **Parallel runs:** whether `CLAUDE.md` or `CLAUDE.local.md` has a heading
  titled `Parallel runs`. Such a section stays where it is. Do not move or
  copy it.

### 2. Find copied rules

Read `<path>/CLAUDE.md` and `~/.claude/methods/my.md`. List each section of
the project's file that repeats a rule now in `my.md`, such as a copied
"Git Workflow" or "Planning Standards". A section that only states this
project's facts (scopes, test command, remote), such as an old "Git
workflow" section, is replaced by the facts block. Propose removing each
copied section, one line each. The user decides.

### 3. Show one diff, then write

Check first that the two files hold no edits of the user's own:
`git -C <path> status --porcelain -- CLAUDE.md .claude/settings.json`. If
either is listed, show it and ask whether to include those edits in the
setup commit or to stop.

If the project already has the facts block, the import line and both keys
set to `true`, and no other method's import line, say that it is set up and
stop.

Show one diff for `CLAUDE.md` and `.claude/settings.json`. Write nothing
until the user says yes.

- **`CLAUDE.md`:** add this block at the end, or update an existing
  `## Project facts` block in place. Keep the blank line before the import
  line. If `CLAUDE.md` does not exist, create it with only this block.
  Remove any other method's import line, such as
  `@~/.claude/methods/tutor.md`. Apply the removals the user accepted in
  step 2.

  ```markdown
  ## Project facts

  - **Method:** my
  - **Commit scopes:** <scopes>
  - **Test command:** <command, or "none">
  - **Plans index:** <path, or "none">
  - **Remote:** <name and host, or "none">

  @~/.claude/methods/my.md
  ```

- **`.claude/settings.json`:** if it exists, read it as JSON, set only
  `enabledPlugins["my@claude-setup"]` and
  `enabledPlugins["superpowers@synced"]` to `true`, and keep every other
  key as it is. If it does not exist, create it as:

  ```json
  {
    "enabledPlugins": {
      "my@claude-setup": true,
      "superpowers@synced": true
    }
  }
  ```

### 4. Commit in that project's repo

1. Run `git -C <path> check-ignore -q .claude/settings.json`. Exit 0 means
   the file is ignored. Then stop before committing. Show the rule with
   `git -C <path> check-ignore -v .claude/settings.json`, and propose to
   replace an ignore line such as `.claude/` with these two lines:

   ```text
   .claude/*
   !.claude/settings.json
   ```

   Before you edit it, run `git -C <path> status --porcelain -- .gitignore`.
   If it is listed, the user has edits of their own there: show them and ask
   whether to include them in the setup commit or to stop.
   On the user's yes, edit `.gitignore` and add it to the commit. On no,
   stop: the switch cannot be committed, so worktrees of this repo would not
   get it.
2. Stage and commit only this skill's files. Other uncommitted work in the
   repo stays as it is:

   ```bash
   git -C <path> add -- CLAUDE.md .claude/settings.json
   git -C <path> commit -m "chore: switch to the my method" -- CLAUDE.md .claude/settings.json
   ```

   If a hook of the project's repo rejects the commit, read the project's
   `CLAUDE.md` for how its hooks run, such as inside a virtualenv or with a
   folder on `PATH`, and retry that way. Never skip a hook with
   `--no-verify`. On the user's yes in sub-step 1, add `.gitignore` to both
   commands. When the project's `git log` shows a scope for config commits, such as
   `chore(config):`, use it.
3. Check that `git -C <path> show --stat --format= HEAD` lists only those
   files.

### 5. Tell the user

Tell the user to start a new interactive session in `<path>`, so that
Claude Code asks once to approve the import from outside the project. Until
the import is approved, its rules are not loaded, and the method guard says
so at each session start.

If the user declined that prompt before, Claude Code does not ask again. To
be asked again, set `projects["<path>"].hasClaudeMdExternalIncludesWarningShown`
to `false` in `~/.claude.json` while no session runs in that directory.

## Steps for `tutor`

1. Check that `<path>/docs/learning/curriculum.md` exists. If not, say that
   this is not a learning workspace (the `kit:tutor` skill sets one up) and
   stop.
2. If the project's `CLAUDE.md` holds a copy of the old "Learning
   workspaces" text, propose removing it.
3. Check the two files as in step 3 for `my`. If `CLAUDE.md` already has
   the line `@~/.claude/methods/tutor.md` and no other method's import line,
   and no `enabledPlugins` key turns `my@claude-setup` or
   `superpowers@synced` on, say that it is set up and stop. Otherwise show
   one diff, and write nothing until the user says yes:
   - `CLAUDE.md`: add the line `@~/.claude/methods/tutor.md` at the end,
     after a blank line, unless it is already there. No facts block. Remove
     any other method's import line, such as `@~/.claude/methods/my.md`. If a
     `## Project facts` block names the `my` method, propose removing it.
   - `.claude/settings.json`, if it exists: remove the `enabledPlugins` keys
     that turn `my@claude-setup` or `superpowers@synced` on, and keep every
     other key. Do not create the file.
4. Commit as in step 4 for `my`, with the message
   `chore: switch to the tutor method`, staging `.claude/settings.json` only
   when this skill changed it.
5. Tell the user as in step 5 for `my`.
