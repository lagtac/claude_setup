#!/usr/bin/env python3
"""Commit paths in the main checkout under lock `main`, with the message read from a file.

The script checks its input, then replaces itself with `handoff-lock.py main`,
found next to this script. Under the lock, a `sh -c` runs these steps, each
only if the one before succeeded:

    git add -- <path> ...
    git commit -F <message file> -- <path> ...
    git show --stat --format= HEAD
    rm -f -- <message file>

When the commit fails, for example because a pre-commit hook rejects it, the
script runs `git reset -q -- <path> ...` under the lock, so the paths do not stay
staged in the shared checkout, and exits with git's code.

`git commit -- <path> ...` commits only those paths: anything else already
staged stays staged and stays out of the commit. No shell reads the message,
so an apostrophe, a backtick or `$(` in it is committed as written. The
message file must lie outside the current repository's work tree. Write it to
the session's scratchpad. It is deleted after a commit succeeds, and kept when
a step fails.

Usage:
    locked-commit.py [--timeout <seconds>] -F <message file> <path> ...

--timeout is passed to handoff-lock.py unchanged; its default is 90 seconds.

Exit codes:
    0                 committed; the stat is printed; the message file is deleted
    64                input refused, or handoff-lock.py's usage error (nothing run)
    74, 75, 126, 127  as in handoff-lock.py --help (nothing run)
    other             a git step failed under the lock, with git's own code;
                      the message file is kept
"""

import os
import subprocess
import sys
from pathlib import Path

LOCK = Path(__file__).resolve().parent / "handoff-lock.py"
STEPS = ('f=$1; shift; git add -- "$@" || exit;'
         ' git commit -F "$f" -- "$@" || { rc=$?; git reset -q -- "$@"; exit $rc; };'
         ' git show --stat --format= HEAD && rm -f -- "$f"')


def fail(code, message):
    print(f"locked-commit: {message}", file=sys.stderr)
    return code


def parse(argv):
    """Return (timeout, message file, paths), or None for a usage error."""
    timeout, message, rest = None, None, list(argv)
    while rest and rest[0].startswith("-"):
        option = rest.pop(0)
        if option == "--":
            break
        if option not in ("--timeout", "-F") or not rest:
            return None
        value = rest.pop(0)
        if option == "--timeout":
            timeout = value
        else:
            message = value
    if message is None or not rest:
        return None
    return timeout, message, rest


def check_message(path):
    """Return the reason to refuse the message file, or None."""
    try:
        text = Path(path).read_bytes()
    except OSError as error:
        return f"cannot read the message file {path}: {error.strerror}"
    if not text.strip():
        return f"the message file {path} holds only whitespace"
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        return result.stderr.strip() or "not inside a git repository"
    top = Path(result.stdout.strip()).resolve()
    if Path(path).resolve().is_relative_to(top):
        return (f"the message file {path} is inside the work tree {top};"
                " write it to the scratchpad")
    return None


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    parsed = parse(argv)
    if parsed is None:
        fail(64, "usage error")
        print(__doc__[__doc__.index("Usage:"):].split("\n\n")[0], file=sys.stderr)
        return 64
    timeout, message, paths = parsed
    reason = check_message(message)
    if reason:
        return fail(64, reason)
    options = ["--timeout", timeout] if timeout is not None else []
    command = [sys.executable, str(LOCK), "main", *options, "--", "sh", "-c", STEPS,
               "sh", str(Path(message).resolve()), *paths]
    os.execv(command[0], command)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
