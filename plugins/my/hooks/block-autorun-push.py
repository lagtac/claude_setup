#!/usr/bin/env python3
"""Block `git push` in an autonomous my:handoff run.

A PreToolUse hook for the Bash and Monitor tools. When the environment
variable MY_AUTORUN is set and not empty, it reads the hook's JSON on stdin
and blocks a shell command that runs `git push`: it prints
"Blocked: autonomous runs never push." to stderr and exits 2. Without the
variable it exits 0 at once, before it reads stdin, so the user's own
sessions work as before.

The command is split the way a shell would split it, roughly: heredoc bodies
are dropped, the rest is cut into words with shlex, and the words are cut
into subcommands at `;`, `&&`, `||`, `|`, parentheses and newlines. Text that
only mentions `git push`, such as a commit message, is not blocked. Shell
keywords and prefixes before a command (`if`, `do`, `then`, `{`, `!`,
`time`, `nohup`, `command`, `exec` and so on) are skipped. `#` does not
start a comment, so a comment cannot hide the line after it. Known gaps:
`bash -c "git push"`, `eval`, `env git push`, pushes from inside a script,
and a quoted `<<WORD` that is taken for a heredoc slip through.
"""

import json
import os
import re
import shlex
import sys

MESSAGE = "Blocked: autonomous runs never push."
HEREDOC = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
SEPARATORS = set(";&|()\n")
PREFIXES = {"if", "while", "until", "then", "do", "else", "elif", "!", "{",
            "time", "exec", "nohup", "command"}
VALUE_OPTIONS = ("-C", "-c", "--git-dir", "--work-tree", "--namespace")


def drop_heredoc_bodies(text):
    kept = []
    waiting = []
    for line in text.split("\n"):
        if waiting:
            if line.lstrip("\t") == waiting[0]:
                waiting.pop(0)
            continue
        kept.append(line)
        waiting = [m.group(3) for m in HEREDOC.finditer(line)
                   if not line[m.start() - 1:m.start()] == "<"]
    return "\n".join(kept)


def words(text):
    lexer = shlex.shlex(text, posix=True, punctuation_chars="();<>|&\n")
    lexer.whitespace = lexer.whitespace.replace("\n", "")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def subcommands(tokens):
    current = []
    for token in tokens:
        if token and set(token) <= SEPARATORS:
            if current:
                yield current
            current = []
        else:
            current.append(token)
    if current:
        yield current


def runs_push(command):
    while command and (ASSIGNMENT.match(command[0]) or command[0] in PREFIXES):
        command = command[1:]
    if not command or os.path.basename(command[0]) != "git":
        return False
    rest = command[1:]
    while rest and rest[0].startswith("-"):
        rest = rest[2:] if rest[0] in VALUE_OPTIONS else rest[1:]
    return bool(rest) and rest[0] == "push"


def pushes(command: str) -> bool:
    text = drop_heredoc_bodies(command)
    try:
        tokens = words(text)
    except ValueError:
        return bool(re.search(r"\bgit\b", text) and re.search(r"\bpush\b", text))
    return any(runs_push(part) for part in subcommands(tokens))


def main() -> int:
    if not os.environ.get("MY_AUTORUN"):
        return 0
    try:
        data = json.load(sys.stdin)
        command = data.get("tool_input", {}).get("command", "")
    except (ValueError, AttributeError):
        return 0
    if isinstance(command, str) and pushes(command):
        print(MESSAGE, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
