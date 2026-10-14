---
name: name-pane
description: Name the tmux pane this session runs in, and its window, after the session's focus (the roadmap row, task or goal it committed to), then print a /rename line for the Claude session. Use when the user says "name it", "name pane", "name this pane/window/session", "auto name" or types /kit:name-pane, optionally with a label. NOT for naming a variable, file, branch or anything else in code.
---

# Name the pane after the session's focus

Give this session's tmux pane a short label that says what the session is for.
The window is then renamed to the labels of all its panes, for example
`r23: make meatballs / r54: put out fire`. The user keeps several windows of one
or two panes, and the labels tell them which session does what.

## 1. Pick the label

If the user gave a label ("name it billing fix"), use it as given.

Otherwise, name the **focus**: the goal the session committed to. Do not name
the step it is on now. A session whose focus is "meet your maker" must not be
labelled "row row row your boat" because that is the sub-task of the last few
turns. Claude Code's own pane title and `/rename` without a name both follow the
latest activity, which is why this skill exists.

Take the first of these that the conversation has:

1. **A roadmap row the session chose to work on.** Use `r<number>: <title>`,
   with the title taken from the row in `ROADMAP.md`, shortened. Do not reword
   it in your own terms.
2. **A spec, plan or design document the session works on.** Use its file
   name without the date and the extension, for example `review-prep-script`.
3. **The goal stated near the start of the session**, in a few words.

Keep the label to about 25 characters, because two labels share one window
name in the status bar. Cut the title, never the row number.

## 2. Name the pane

Run the script, which is on PATH in Claude Code sessions. Put the label in
single quotes, and drop any `'` from it:

```bash
tmux-name-pane.py '<label>'
```

It sets the label on the pane this session runs in (`$TMUX_PANE`), never on
the pane the user is looking at. It sets the window to name itself after its
panes' labels, and prints the new window name. Where the user's
`pane-border-format` shows `#{pane_title}`, the border shows the label instead.
A border appears only when `pane-border-status` is on in the user's tmux
config. The script does not turn it on.

If the script ends with `nothing named` (outside tmux, or tmux refused), tell
the user its message in one line, and go on to step 3.

## 3. Print the /rename line

A skill cannot run a built-in command, so give the user the line to paste. It
makes the session's name match the label, for example in `claude --resume`:

```text
/rename <label>
```

End with that line and the window name the script printed. Nothing else.

## What stays and what does not

- The label stays fixed. Nothing updates it as the session moves on. Run the
  skill again when the session switches to another focus.
- tmux keeps the window name up to date. When a pane closes, its label leaves
  the window name.
- Another tool may rename the window later, for example to mark it as waiting
  or done. That stops tmux's own naming, so the window shows the other tool's
  name until a pane is named again. The pane labels stay.
