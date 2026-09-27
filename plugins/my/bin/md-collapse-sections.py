#!/usr/bin/env python3
"""Print a Markdown table with one row per section. Reads a file or stdin, writes stdout.

A section is a heading and the lines up to the next heading. Its fields are the
top-level bullets written as `- **Name:** value`; only the first line of a value
counts. Nested bullets, code blocks and other text are ignored. Sections with none
of the wanted fields are skipped. This reads the format md-expand-table.py writes.

Usage:
    md-collapse-sections.py [FILE] [--fields A,B] [--key NAME] [--body NAME [--first-sentence]]
"""

import argparse
import re
import sys

HEADING = re.compile(r"^#{1,6}[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
FIELD = re.compile(r"^[-*] \*\*((?:(?!\*\*).)+?):\*\*\s*(.*?)\s*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


class Fences:
    """Track fenced code blocks. A fence closes only with the same character,
    at least as many of them, and nothing else on the line."""

    def __init__(self):
        self.open = None

    def inside(self, line):
        """Return True when the line is a fence line or inside a fence."""
        match = FENCE.match(line.rstrip("\n"))
        if self.open is None:
            if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
                self.open = match.group(1)
                return True
            return False
        fence = match.group(1) if match else ""
        if (
            match
            and not match.group(2).strip()
            and fence[0] == self.open[0]
            and len(fence) >= len(self.open)
        ):
            self.open = None
        return True


NOT_BODY = re.compile(r"^\s*([-*+]\s|\d+[.)]\s|\||<!--)")


def parse_sections(text):
    """Return [(heading, content_lines)], with fenced code removed."""
    sections = []
    fences = Fences()
    for line in text.splitlines():
        if fences.inside(line):
            continue
        heading = HEADING.match(line)
        if heading:
            sections.append((heading.group(1), []))
        elif sections:
            sections[-1][1].append(line)
    return sections


def fields_of(content):
    found = {}
    for line in content:
        match = FIELD.match(line)
        if match and match.group(1) not in found:
            found[match.group(1)] = match.group(2)
    return found


def body_of(content):
    blocks = "\n".join(content).split("\n\n")
    for block in blocks:
        block = block.strip("\n")
        if any(FIELD.match(line) for line in block.splitlines()):
            break
        if block.strip() and not NOT_BODY.match(block):
            return " ".join(line.strip() for line in block.splitlines())
    return ""


def cell(value):
    return value.replace("|", "\\|")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("file", nargs="?", help="Markdown file (default: stdin)")
    parser.add_argument(
        "--fields",
        help="comma-separated field names, in column order (default: all found)",
    )
    parser.add_argument(
        "--key",
        default="Section",
        help="header of the heading column (default: Section)",
    )
    parser.add_argument(
        "--body",
        metavar="NAME",
        help="add a column NAME holding each section's first paragraph",
    )
    parser.add_argument(
        "--first-sentence",
        action="store_true",
        help="with --body, keep only the first sentence",
    )
    args = parser.parse_args()

    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if args.file:
        with open(args.file, encoding="utf-8") as file:
            text = file.read()
    else:
        text = sys.stdin.read()
    sections = [
        (heading, content, fields_of(content))
        for heading, content in parse_sections(text)
    ]

    if args.fields:
        wanted = [name.strip() for name in args.fields.split(",")]
    else:
        wanted = []
        for _, _, found in sections:
            wanted += [name for name in found if name not in wanted]

    records = [s for s in sections if any(name in s[2] for name in wanted)]
    if not records:
        print("no sections with fields found", file=sys.stderr)
        return 1

    header = [args.key] + ([args.body] if args.body else []) + wanted
    rows = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    for heading, content, found in records:
        cells = [heading]
        if args.body:
            body = body_of(content)
            if args.first_sentence:
                body = re.split(r"(?<=[.!?])\s+", body)[0]
            cells.append(body)
        for name in wanted:
            if name not in found:
                print(f"{heading}: no **{name}:** field", file=sys.stderr)
            cells.append(found.get(name, ""))
        rows.append("| " + " | ".join(cell(c) for c in cells) + " |")
    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
