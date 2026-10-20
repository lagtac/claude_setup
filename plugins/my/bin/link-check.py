#!/usr/bin/env python3
"""List the bad links in Markdown files such as ROADMAP.md and CHANGELOG.md,
and mark whether each one sits on a line the current uncommitted edit changed.

The script reads and never writes. Each path is read as given, relative to the
working directory. A link target is resolved from the folder of the file that
holds it. Targets with a scheme (`https:`, `mailto:`) and pure `#anchor`
targets are skipped. Code blocks and code spans are not searched.

Usage:
    link-check.py <file>...

One line per problem, fields separated by one tab, in file order then line
order:

    <kind>  <file>:<line>  <target>  <new|old>

    kind     climbs: the path leaves the repository root
             html:   a .html or .htm path whose .md twin exists
             dead:   the path does not exist, or git ignores it
    file     the path as given on the command line
    line     the line that holds the target
    target   the target as written in the file
    new|old  new when the line is in an added range of `git diff HEAD`, or
             the file is untracked, outside git, or in a repository with no
             commit yet; old otherwise

A clean run prints nothing.

Exit codes:
    0  no problems, or -h / --help
    1  at least one problem, new or old
    2  a usage error, a file that cannot be read, or a git call that failed;
       the other files are still checked, and 2 wins over 1
"""

import os
import re
from bisect import bisect_left
import subprocess
import sys
from urllib.parse import unquote

FENCE = re.compile(r"[ \t]*(`{3,}|~{3,})")
CODE_SPAN = re.compile(r"(`+)(?:(?!\n[ \t]*\n).)+?(?<!`)\1(?!`)", re.S)
INLINE = re.compile(
    r"!?\[[^\[\]]*\]\(\s*(<[^<>\n]*>|[^\s()]*)"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^()]*\)))?\s*\)")
REFERENCE = re.compile(r"^[ ]{0,3}\[(?!\^)[^\[\]]+\]:[ \t]*(<[^<>\n]*>|\S+)", re.M)
SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
HUNK = re.compile(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", re.M)


class GitError(Exception):
    pass


def git(*args, cwd, stdin=None):
    """Run git in the C locale, so its messages can be matched, and return
    the CompletedProcess."""
    command = ["git", "-c", "core.quotePath=false", *args]
    env = dict(os.environ, LC_ALL="C")
    return subprocess.run(command, cwd=cwd, input=stdin, env=env,
                          capture_output=True, text=True)


def failed(result, args):
    reason = result.stderr.strip() or f"exit {result.returncode}"
    return GitError(f"git {' '.join(args)}: {reason}")


def blank(match):
    return re.sub(r"[^\n]", " ", match.group())


def blank_code(text):
    """Replace fenced blocks and code spans with spaces, keeping newlines."""
    lines = text.split("\n")
    fence = None
    for number, line in enumerate(lines):
        match = FENCE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
                lines[number] = " " * len(line)
        else:
            if match and match.group(1)[0] == fence[0] \
                    and len(match.group(1)) >= len(fence) \
                    and not line[match.end():].strip():
                fence = None
            lines[number] = " " * len(line)
    return CODE_SPAN.sub(blank, "\n".join(lines))


def links(text):
    """The (line, target) of every link that is checked, in file order."""
    text = blank_code(text)
    found = []
    for pattern in (INLINE, REFERENCE):
        for match in pattern.finditer(text):
            target = match.group(1)
            if target.startswith("<"):
                target = target[1:-1]
            if not target or target.startswith("#") or SCHEME.match(target):
                continue
            found.append((match.start(1), target))
    found.sort()
    newlines = [match.start() for match in re.finditer("\n", text)]
    return [(bisect_left(newlines, offset) + 1, target) for offset, target in found]


def repo_root(folder):
    """The repository root of a folder, or None when it is not in a repository."""
    args = ("rev-parse", "--show-toplevel")
    result = git(*args, cwd=folder)
    if result.returncode == 0:
        return os.path.realpath(result.stdout.strip())
    if "not a git repository" in result.stderr:
        return None
    raise failed(result, args)


def resolve(target, base):
    part = unquote(target.split("#")[0].split("?")[0])
    return os.path.normpath(os.path.join(base, part))


def kind(target, base, root, ignored):
    """The problem of one target, or None when it is fine."""
    path = resolve(target, base)
    if path != root and not path.startswith(root + os.sep):
        return "climbs"
    stem, ending = os.path.splitext(path)
    if ending.lower() in (".html", ".htm") and os.path.isfile(stem + ".md"):
        return "html"
    if not os.path.exists(path) or path in ignored:
        return "dead"
    return None


def ignored_paths(paths, root):
    """The paths, of those given, that git ignores and does not track."""
    if not paths:
        return set()
    relative = [os.path.relpath(path, root) for path in paths]
    args = ("check-ignore", "--stdin")
    result = git(*args, cwd=root, stdin="\n".join(relative) + "\n")
    if result.returncode not in (0, 1):
        raise failed(result, args)
    return {os.path.normpath(os.path.join(root, line))
            for line in result.stdout.splitlines() if line}


def new_lines(path, root):
    """The line numbers the uncommitted edit added; None means every line."""
    if root is None:
        return None
    folder = os.path.dirname(path)
    if git("rev-parse", "--verify", "-q", "HEAD^{commit}", cwd=folder).returncode:
        return None
    args = ("ls-files", "--", path)
    result = git(*args, cwd=folder)
    if result.returncode:
        raise failed(result, args)
    if not result.stdout.strip():
        return None
    args = ("diff", "-U0", "--no-color", "--no-ext-diff", "HEAD", "--", path)
    result = git(*args, cwd=folder)
    if result.returncode:
        raise failed(result, args)
    added = set()
    for match in HUNK.finditer(result.stdout):
        start = int(match.group(1))
        count = 1 if match.group(2) is None else int(match.group(2))
        added.update(range(start, start + count))
    return added


def check(path):
    """The (kind, line, target, new or old) of every problem in one file."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    real = os.path.join(os.path.realpath(os.path.dirname(os.path.abspath(path))),
                        os.path.basename(path))
    base = os.path.dirname(real)
    root = repo_root(base)
    top = root or base
    found = links(text)
    ignored = set()
    if root is not None:
        inside = {resolve(target, base) for _, target in found}
        inside = [p for p in inside
                  if (p == root or p.startswith(root + os.sep)) and os.path.exists(p)]
        ignored = ignored_paths(sorted(inside), root)
    added = new_lines(real, root)
    problems = []
    for line, target in found:
        problem = kind(target, base, top, ignored)
        if problem:
            age = "new" if added is None or line in added else "old"
            problems.append((problem, line, target, age))
    return problems


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if not argv:
        print("link-check.py: no file given. Usage: link-check.py <file>...",
              file=sys.stderr)
        return 2
    code = 0
    for path in argv:
        try:
            problems = check(path)
        except (OSError, UnicodeDecodeError, GitError) as error:
            print(f"link-check.py: {path}: {error}", file=sys.stderr)
            code = 2
            continue
        for problem, line, target, age in problems:
            print(f"{problem}\t{path}:{line}\t{target}\t{age}")
        if problems and code == 0:
            code = 1
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
