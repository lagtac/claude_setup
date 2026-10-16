#!/usr/bin/env python3
"""Count the search patterns of a design-system inventory.

The inventory is `docs/DESIGN-SYSTEM.md` (my:design-system). Its `ds-patterns`
block holds one JSON object per line. For each line the script lists the
tracked files that the line's globs match, with git, and counts the matches of
its regular expression in them. Untracked and ignored files never count.

Usage:
    ds-count.py [--write] [<inventory>]

<inventory> is relative to the current folder; the default is
docs/DESIGN-SYSTEM.md at the repository root. Globs are relative to the root,
wherever the script runs. The script prints one line per pattern, in block
order, with two spaces between fields:

    <name>  <kind>  <old count>/<old files> -> <new count>/<new files>

`new` takes the place of the old values on a line with no counts yet. With
--write it then stores the new `count` and `files` in each line. Every byte
outside the block stays as it was.

Keys of a line:
    name     unique in the block
    kind     `component` or `hand-built`
    globs    non-empty list of git glob pathspecs; their matches add up
    exclude  optional list of git glob pathspecs whose files are left out
    regex    Python regular expression over each file's whole text
    count    matches in total, written by --write
    files    files with at least one match, written by --write

Exit codes:
    0  every pattern counted, whether or not counts changed
    1  refused, with one line on stderr: not in a git repository, no block or
       more than one, an unclosed block, a bad line, a duplicate name, a regex
       that does not compile or matches the empty string, or globs that match
       no tracked file. Nothing is written.
"""

import json
import os
import re
import subprocess
import sys
import tempfile

DEFAULT = "docs/DESIGN-SYSTEM.md"
OPEN = "```ds-patterns"
CLOSE = "```"
KINDS = ("component", "hand-built")


class Refusal(Exception):
    pass


def find_block(lines, path):
    """The indexes of the opening and the closing fence."""
    opens = [i for i, text in enumerate(lines) if text.rstrip() == OPEN]
    if not opens:
        raise Refusal(f"{path}: no ds-patterns block")
    if len(opens) > 1:
        raise Refusal(f"{path}: more than one ds-patterns block")
    start = opens[0]
    for i in range(start + 1, len(lines)):
        if lines[i].rstrip() == CLOSE:
            return start, i
    raise Refusal(f"{path}: the ds-patterns block is not closed")


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_str_list(value):
    # An empty glob, as ":(glob)", would match every tracked file.
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def check(obj):
    """The first problem of one pattern object, or None."""
    for key in ("name", "kind", "globs", "regex"):
        if key not in obj:
            return f"missing key {key}"
    if not isinstance(obj["name"], str) or not obj["name"]:
        return "name is of the wrong type"
    if obj["kind"] not in KINDS:
        return "kind is of the wrong type"
    if not is_str_list(obj["globs"]) or not obj["globs"]:
        return "globs is of the wrong type"
    if "exclude" in obj and not is_str_list(obj["exclude"]):
        return "exclude is of the wrong type"
    if not isinstance(obj["regex"], str):
        return "regex is of the wrong type"
    for key in ("count", "files"):
        if key in obj and not is_int(obj[key]):
            return f"{key} is of the wrong type"
    try:
        re.compile(obj["regex"])
    except re.error as error:
        return f"regex does not compile: {error}"
    return None


def parse_patterns(lines, start, end, path):
    """Each non-blank line's 1-based line number in the file, and its object."""
    patterns = []
    names = set()
    for i in range(start + 1, end):
        text = lines[i].strip()
        if not text:
            continue
        number = i + 1
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            obj = None
        if not isinstance(obj, dict):
            raise Refusal(f"{path} line {number}: not a JSON object")
        problem = check(obj)
        if problem:
            raise Refusal(f"{path} line {number}: {problem}")
        if obj["name"] in names:
            raise Refusal(f"{path} line {number}: the name {obj['name']} is used twice")
        names.add(obj["name"])
        patterns.append((number, obj))
    return patterns


def ls_files(root, specs):
    result = subprocess.run(
        # A file in a merge conflict is listed once per stage without --deduplicate.
        ["git", "ls-files", "-z", "--deduplicate", "--", *specs],
        cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        raise Refusal(f"git ls-files failed: {result.stderr.strip()}")
    return [name for name in result.stdout.split("\0") if name]


def tracked(root, globs, exclude):
    return ls_files(root, [f":(glob){g}" for g in globs]
                    + [f":(glob,exclude){e}" for e in exclude])


def count(root, files, regex):
    """Matches in total, and files with a match. Raises on an empty match."""
    pattern = re.compile(regex)
    total = with_match = 0
    for name in files:
        try:
            with open(os.path.join(root, name), encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except (FileNotFoundError, IsADirectoryError):
            continue
        found = 0
        for match in pattern.finditer(text):
            if match.start() == match.end():
                raise Refusal("matches the empty string")
            found += 1
        total += found
        with_match += 1 if found else 0
    return total, with_match


def old_values(obj):
    if is_int(obj.get("count")) and is_int(obj.get("files")):
        return f"{obj['count']}/{obj['files']}"
    return "new"


def ending(text):
    stripped = text.rstrip("\r\n")
    return text[len(stripped):]


def write(path, lines):
    folder = os.path.dirname(os.path.abspath(path))
    mode = os.stat(path).st_mode & 0o7777
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".ds-count-")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as out:
            out.write("".join(lines))
        os.chmod(temp, mode)
        os.replace(temp, path)
    except BaseException:
        if os.path.exists(temp):
            os.remove(temp)
        raise


def repo_root():
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise Refusal("not inside a git repository")
    return result.stdout.strip()


def main(argv):
    args = list(argv)
    do_write = "--write" in args
    args = [a for a in args if a != "--write"]
    if len(args) > 1 or any(a.startswith("-") for a in args):
        raise Refusal("usage: ds-count.py [--write] [<inventory>]")
    root = repo_root()
    path = args[0] if args else os.path.join(root, DEFAULT)
    shown = args[0] if args else DEFAULT
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            lines = handle.read().splitlines(keepends=True)
    except OSError as error:
        raise Refusal(f"{shown}: cannot read: {error.strerror}")
    start, end = find_block(lines, shown)
    patterns = parse_patterns(lines, start, end, shown)

    results = []
    for number, obj in patterns:
        if not ls_files(root, [f":(glob){g}" for g in obj["globs"]]):
            raise Refusal(f"{shown} line {number}: the globs match no tracked file")
        files = tracked(root, obj["globs"], obj.get("exclude", []))
        try:
            results.append((number, obj, *count(root, files, obj["regex"])))
        except Refusal as refusal:
            raise Refusal(f"{shown} line {number}: the regex {refusal}")

    for _, obj, total, with_match in results:
        print(f"{obj['name']}  {obj['kind']}  {old_values(obj)} -> {total}/{with_match}")
    if do_write and results:
        for number, obj, total, with_match in results:
            obj["count"] = total
            obj["files"] = with_match
            old = lines[number - 1]
            lines[number - 1] = json.dumps(obj, ensure_ascii=False) + ending(old)
        write(path, lines)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Refusal as refusal:
        print(f"ds-count: {refusal}", file=sys.stderr)
        sys.exit(1)
