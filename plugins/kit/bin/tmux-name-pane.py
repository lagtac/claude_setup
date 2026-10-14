#!/usr/bin/env python3
"""Name the tmux pane this session runs in, and its window, after the session's focus.

The label goes into the pane's @focus user option, which a program in the pane
cannot overwrite (a pane title can be: Claude Code sets it as it works). In the
window's pane border format, #{pane_title} becomes the label, or the title when
a pane has no label. The window is set to name itself after the labels of all
its panes, in pane order, joined with " / ". tmux keeps that name up to date, so
a closed pane's label leaves it. Prints the new window name.

Usage:
    tmux-name-pane.py LABEL

The pane is the one in $TMUX_PANE, never the pane the user is looking at.
Outside tmux, or when tmux refuses, it exits with 1.
"""

import argparse
import os
import subprocess
import sys

TITLE = "#{pane_title}"
LABEL_OR_TITLE = "#{?@focus,#{@focus},#{pane_title}}"
LABELS = "#{s| / $||:#{P:#{?@focus,#{@focus} / ,}}}"
WINDOW_NAME = "#{?#{P:#{@focus}}," + LABELS + ",#{pane_current_command}}"


class TmuxError(Exception):
    pass


def tmux(*args):
    result = subprocess.run(["tmux", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise TmuxError(f"tmux {args[0]}: {result.stderr.strip()}")
    return result.stdout.rstrip("\n")


def name(pane, label):
    tmux("set-option", "-p", "-t", pane, "--", "@focus", label)
    border = tmux("show-options", "-wAv", "-t", pane, "pane-border-format")
    if "@focus" not in border and TITLE in border:
        tmux("set-option", "-w", "-t", pane, "--", "pane-border-format",
             border.replace(TITLE, LABEL_OR_TITLE))
    tmux("set-option", "-w", "-t", pane, "--", "automatic-rename-format", WINDOW_NAME)
    tmux("set-option", "-w", "-t", pane, "automatic-rename", "on")
    return tmux("display-message", "-p", "-t", pane, LABELS)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("label", help="the session's focus, for example 'r54: put out fire'")
    args = parser.parse_args()

    label = " ".join(args.label.split())
    if not label:
        sys.exit("tmux-name-pane.py: empty label, nothing named")
    pane = os.environ.get("TMUX_PANE")
    if not pane or not os.environ.get("TMUX"):
        sys.exit("tmux-name-pane.py: not inside tmux, nothing named")
    try:
        print(name(pane, label))
    except TmuxError as error:
        sys.exit(f"tmux-name-pane.py: {error}, nothing named")


if __name__ == "__main__":
    main()
