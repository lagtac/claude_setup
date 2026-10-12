#!/usr/bin/env python3
"""Run one command under a named lock, shared by the repository and its worktrees.

The lock for <name> is `fcntl.flock` on
`<git common dir>/my-handoff/locks/<name>.lock`. The script takes the lock,
then replaces itself with the command and keeps the lock open, so the lock
lives exactly as long as the command. The kernel frees it when the command
ends or dies. A child process that outlives the command keeps it too, so a
locked command must not start a server that outlives it.

Usage:
    handoff-lock.py <name> [--timeout <seconds>] -- <command> [<arg> ...]

<name> matches [A-Za-z0-9][A-Za-z0-9._-]* and holds no `..`. --timeout is the
most seconds to wait for the lock, default 90; 0 means one try. The command
runs with gc.autoDetach and maintenance.autoDetach set to false, added after
any GIT_CONFIG_COUNT pairs already set, so that a detached `git gc --auto`
does not keep the lock after the command ends.

Exit codes:
    the command's own code, once it has run
    64   usage error, or a bad name (nothing run)
    74   the lock file cannot be opened (nothing run)
    75   the wait timed out (nothing run)
    126  the command cannot be run
    127  the command is not found
"""

import fcntl
import math
import os
import re
import subprocess
import sys
import time

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
DEFAULT_TIMEOUT = 90.0
RETRY = 0.1


def fail(code, message):
    print(f"handoff-lock: {message}", file=sys.stderr)
    return code


def parse(argv):
    """Return (name, timeout, command), or None for a usage error."""
    if "--" not in argv:
        return None
    split = argv.index("--")
    head, command = argv[:split], argv[split + 1:]
    if not head or not command:
        return None
    name, options = head[0], head[1:]
    if not NAME.fullmatch(name) or ".." in name:
        return None
    timeout = DEFAULT_TIMEOUT
    if options:
        if len(options) != 2 or options[0] != "--timeout":
            return None
        try:
            timeout = float(options[1])
        except ValueError:
            return None
        if not math.isfinite(timeout) or timeout < 0:
            return None
    return name, timeout, command


def lock_path(name):
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True)
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or "not inside a git repository")
    return os.path.join(result.stdout.strip(), "my-handoff", "locks", f"{name}.lock")


def acquire(fd, timeout):
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(RETRY)


def command_env():
    env = dict(os.environ)
    try:
        count = int(env.get("GIT_CONFIG_COUNT", "0"))
    except ValueError:
        count = 0
    for key in ("gc.autoDetach", "maintenance.autoDetach"):
        env[f"GIT_CONFIG_KEY_{count}"] = key
        env[f"GIT_CONFIG_VALUE_{count}"] = "false"
        count += 1
    env["GIT_CONFIG_COUNT"] = str(count)
    return env


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    parsed = parse(argv)
    if parsed is None:
        block = __doc__[__doc__.index("Usage:"):].split("\n\n")[0]
        print(block, file=sys.stderr)
        return fail(64, "usage error")
    name, timeout, command = parsed
    try:
        path = lock_path(name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    except OSError as error:
        return fail(74, f"cannot open the lock {name}: {error}")
    if not acquire(fd, timeout):
        return fail(75, f"lock {name} is still held after {timeout:g} s; nothing ran")
    os.set_inheritable(fd, True)
    try:
        os.execvpe(command[0], command, command_env())
    except FileNotFoundError:
        return fail(127, f"command not found: {command[0]}")
    except PermissionError:
        return fail(126, f"command cannot be run: {command[0]}")
    except OSError as error:
        return fail(126, f"command cannot be run: {command[0]}: {error}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
