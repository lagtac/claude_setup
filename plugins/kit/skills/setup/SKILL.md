---
name: setup
description: >
  Set a folder's method in its .claude/settings.json: write the method's
  plugin keys and those of its dependencies, remove other methods' keys, drop
  an old method import line, and (for my) write a "## Project facts" block,
  then commit in that project's repo. Takes `<method|none> [<project path>]`,
  where method is a name that claude-method lists and the path defaults to the
  current repo root. Use when the user types /kit:setup, asks to "set up the my
  method" or "switch this repo to tutor", or when the method start check says
  "Run /kit:setup <m>". NOT for outside methods: they bring their own setup.
---

# Set up a method

A method is a plugin whose forced output style holds its rules. Its
`dependencies` field names the plugins it needs. A folder picks its method in
`.claude/settings.json`, under `enabledPlugins`: the method's key and its
dependencies' keys are `true`. This skill writes those keys. Nobody edits them
by hand.

The keys come from `claude-method`, a kit script on `PATH`, which reads the
method list:

- `claude-method` lists the methods, one `<name><TAB><description>` per line,
  then `none`.
- `claude-method --json <m>` prints `{"enabledPlugins": {...}}`. Its keys
  with `true` are the method's key and its dependencies' keys: the **on
  keys**.
- `claude-method --methods` prints one JSON object that maps each method key
  to its dependency keys. Every key in it, method or dependency, is a
  **method key** below.

The `kit` start check, a SessionStart hook, warns when two methods are on,
when a dependency is off, or when an old import line is left.

This skill does not read the user's `CLAUDE.md` files. Everything it needs is
written here.

## Arguments

`/kit:setup <method|none> [<project path>]`

- `<method>`: a name that `claude-method` lists, or `none` (no method).
- `<project path>`: the project to set up. Default: the current repo root,
  `git rev-parse --show-toplevel`. So one session can set up several
  projects in a row.

Run `claude-method` first. On any other arguments, print
`Usage: /kit:setup <method|none> [<project path>]`, then its list, and stop.

Resolve the path to its repo root with
`git -C <path> rev-parse --show-toplevel`. If that fails, the path is not in
a git repo: say so and stop. Only a repo can take the setup commit. From here
on, `<path>` is that root, and every command runs as `git -C <path> …` or
reads files under `<path>`. Write `<path>` out in full in each command. Run
each command on its own: no `cd`, no shell variables, no `;` or `echo` between
commands.

## Steps

### 1. Read the keys

Run `claude-method --json <m>` and `claude-method --methods`. If either
fails, show its message and stop. Note the on keys and the method keys. The
**off keys** are the method keys that are not on keys: other methods and
their dependencies, except the chosen method's own.

### 2. For `my`: find the facts in the repo

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

### 3. For `my`: find copied rules

Read `<path>/CLAUDE.md` and the `my` style, at
`<marketplace folder>/plugins/my/output-styles/my.md`. The marketplace folder
is the one `claude-method` reads: `$CLAUDE_METHOD_MARKETPLACE` when it is
set, else the `installLocation` of entry `claude-setup` in
`~/.claude/plugins/known_marketplaces.json`. List each section of the
project's file that repeats a rule now in the style, such as a copied "Git
Workflow" or "Planning Standards". A section that only states this project's
facts (scopes, test command, remote), such as an old "Git workflow" section,
is replaced by the facts block. Propose removing each copied section, one
line each. The user decides.

### 4. For `tutor`: check the workspace

1. Check that `<path>/docs/learning/curriculum.md` exists. If not, say that
   this is not a learning workspace (the `tutor:tutor` skill sets one up)
   and stop.
2. If the project's `CLAUDE.md` holds a copy of the old "Learning
   workspaces" text, propose removing it.

`tutor` gets no facts block. If a `## Project facts` block is there for the
`my` method, propose removing it.

### 5. Show one diff, then write

Check first that the files hold no edits of the user's own:
`git -C <path> status --porcelain -- CLAUDE.md CLAUDE.local.md .claude/settings.json`.
If any is listed, show it and ask whether to include those edits in the
setup commit or to stop.

The folder is set up when all of these hold: every on key is `true` in
`.claude/settings.json`; no off key is there; `.claude/settings.local.json`
has no method key and no `outputStyle` of `plain` or `tutor`; neither
`CLAUDE.md` nor `CLAUDE.local.md` has a line `@~/.claude/methods/<name>.md`;
no `**Method:**` line is left; and, for `my`, the facts block is there. Then
say that it is set up and stop.

Otherwise show one diff for every file it changes. Write nothing until the
user says yes.

1. **`.claude/settings.json`:** set each on key to `true` under
   `enabledPlugins`. Read the file as JSON and keep every other key. If it
   does not exist and there are on keys, create it with only those keys
   under `enabledPlugins`.
2. **`.claude/settings.json`:** remove each off key.
3. **`.claude/settings.local.json`,** if it exists: remove every method key,
   and an `outputStyle` key whose value is `plain` or `tutor`. Keep every
   other key. Do not create the file.
4. **`CLAUDE.md` and `CLAUDE.local.md`:** remove every line
   `@~/.claude/methods/<name>.md`, and the blank line before it when the
   line ends the file.
5. **"Project facts":** remove the `- **Method:** …` line. The settings file
   names the method now.

In either settings file, an `enabledPlugins` left empty is removed; the file
stays.

For `my`, also add this block at the end of `CLAUDE.md`, or update an
existing `## Project facts` block in place. If `CLAUDE.md` does not exist,
create it with only this block. Apply the removals the user accepted in
step 3.

```markdown
## Project facts

- **Commit scopes:** <scopes>
- **Test command:** <command, or "none">
- **Plans index:** <path, or "none">
- **Remote:** <name and host, or "none">
```

### 6. Commit in that project's repo

1. If this skill changed `.claude/settings.json`, run
   `git -C <path> check-ignore -q .claude/settings.json`. Exit 0 means the
   file is ignored. Then stop before committing. Show the rule with
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
2. Stage and commit only the files this skill changed or created among
   `CLAUDE.md`, `.claude/settings.json` and a `CLAUDE.local.md` that git
   tracks. Other uncommitted work in the repo stays as it is. The message is
   `chore: switch to the <m> method`, or `chore: switch to no method` for
   `none`:

   ```bash
   git -C <path> add -- <files>
   git -C <path> commit -m "chore: switch to the <m> method" -- <files>
   ```

   `.claude/settings.local.json` is never committed. A `CLAUDE.local.md`
   that git does not track is edited in place and not committed; when it is
   a symlink, name its target.

   If a hook of the project's repo rejects the commit, read the project's
   `CLAUDE.md` for how its hooks run, such as inside a virtualenv or with a
   folder on `PATH`, and retry that way. Never skip a hook with
   `--no-verify`. On the user's yes in sub-step 1, add `.gitignore` to both
   commands. When the project's `git log` shows a scope for config commits,
   such as `chore(config):`, use it.
3. Check that `git -C <path> show --stat --format= HEAD` lists only those
   files.

### 7. Tell the user

The method loads in the next session started in `<path>`, or after the user
submits `/reload-plugins` in a session that runs there.
