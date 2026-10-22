---
name: method
description: >
  Switch the method of the current folder during a session, in its
  .claude/settings.local.json, with `claude plugin enable` and
  `claude plugin disable --scope local`; `default` removes those local keys so
  the folder's committed method applies again. Takes `<method|none|default>`.
  Only the user starts it, by typing /kit:method. It ends by asking the user
  to submit /reload-plugins.
disable-model-invocation: true
---

# Switch the method in this folder

A method is a plugin whose forced output style holds its rules. Its
`dependencies` field names the plugins it needs. A folder's committed
`.claude/settings.json` names its default method. This skill switches the
method for every session in the folder, without a commit: it writes keys into
`.claude/settings.local.json`, which outranks the committed file. `claude
plugin` writes that file at the repo root.

The keys come from `claude-method`, a kit script on `PATH`, which reads the
method list:

- `claude-method` lists the methods, one `<name><TAB><description>` per line,
  then `none`.
- `claude-method --json <m>` prints `{"enabledPlugins": {...}}`. Its keys
  with `true` are the method's key and its dependencies' keys. Its keys with
  `false` are every other method and dependency key.
- `claude-method --methods` prints one JSON object that maps each method key
  to its dependency keys. Every key in it, method or dependency, is a
  **method key** below.

## Arguments

`/kit:method <method|none|default>`

- `<method>`: a name that `claude-method` lists.
- `none`: every method and its plugins off.
- `default`: remove the local method keys, so the folder's committed method
  applies again.

Run `claude-method` first. On any other argument, print
`Usage: /kit:method <method|none|default>`, then its list, and stop.

## Steps

Run each command on its own: no `cd`, no shell variables, no `;` or `echo`
between commands.

### 1. For a method or `none`: write the keys

Run `claude-method --json <m>`. If it fails, show its message and stop.

Then run `claude-method --methods`, to tell method keys from dependency keys.
Run one command per key, each on its own, in this order:

1. `claude plugin disable <key> --scope local` for each key with `false`.
   Turning keys off first means a failure leaves no method on, never two.
2. `claude plugin enable <key> --scope local` for each dependency key with
   `true`.
3. `claude plugin enable <key> --scope local` for the method key with `true`.
   `claude plugin enable` refuses a method while one of its dependencies is
   off, so the dependencies go first.

Show each command's result. A command that exits 1 with
`is already enabled at local scope` or `is already disabled at local scope`
in its output did not fail: that key already has the wanted value, and
`claude plugin` wrote nothing for it. On any other non-zero exit, stop. Say
which keys changed, which already had the wanted value, and which were not
run.

### 2. For `default`: remove the local keys

`claude plugin` can set a key but not remove one, so edit the file directly.

1. Run `claude-method --methods`. If it fails, show its message and stop.
2. Find the repo root with `git rev-parse --show-toplevel`. Outside a repo,
   use the current folder. Read `<root>/.claude/settings.local.json`. If it
   does not exist, or has no `enabledPlugins`, say that no local keys are set
   and go to "3. Ask for a reload".
3. With the Edit tool, remove each method key from `enabledPlugins`. If
   `enabledPlugins` is then empty, remove it too. Keep every other key in the
   file. Show the file as it is after the edit.

### 3. Ask for a reload

End with one line asking the user to submit `/reload-plugins`, because
Claude cannot submit it. The new method loads after the reload, in this
session and in every new session in the folder. Add one more line: a session
started by `claude-method` keeps its method, because the keys it passed with
`--settings` outrank the local file.
