#!/usr/bin/env python3
"""Rewrite Markdown tables as one section per row. Reads a file or stdin, writes stdout.

Each row becomes a heading (the first column's value), then an optional paragraph
(--body-col), then one `- **Column:** value` bullet per other column. The rest of
the document is copied unchanged. md-collapse-sections.py turns the sections back
into a table.

Usage:
    md-expand-table.py [FILE]                         list the tables, numbered
    md-expand-table.py [FILE] --table N[,N...] [--body-col NAME] [--level N]

Table numbers are the ones the list shows, even when you expand several at once.

To change a file, write to a new file first. `cmd < f > f` empties f before cmd reads it:
    md-expand-table.py --table 2 f.md > f.new && mv f.new f.md
"""

import argparse
import re
import sys

DELIMITER = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
HEADING = re.compile(r"^(#{1,6}) ")
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


MARKUP = re.compile(
    r"^\s*(#{1,6}(\s|$)|[-*+]\s|\d+[.)]\s|>|\||<!--|```|~~~|([-*_]\s*){3,}$)"
)


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", line)]


def find_tables(lines):
    """Return (start, end, heading) for each table; end is exclusive."""
    tables = []
    heading = None
    fences = Fences()
    i = 0
    while i < len(lines):
        line = lines[i]
        if fences.inside(line):
            pass
        elif HEADING.match(line):
            heading = line.strip()
        elif (
            "|" in line
            and i + 1 < len(lines)
            and DELIMITER.match(lines[i + 1])
            and "|" in lines[i + 1]
            and len(split_row(line)) == len(split_row(lines[i + 1]))
        ):
            end = i + 2
            while end < len(lines) and lines[end].strip() and "|" in lines[end]:
                end += 1
            tables.append((i, end, heading))
            i = end
            continue
        i += 1
    return tables


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def list_tables(lines, tables):
    for number, (start, end, heading) in enumerate(tables, 1):
        header = split_row(lines[start])
        print(
            f"{number}\tline {start + 1}\t{heading or '(no heading)'}\t"
            f"{plural(len(header), 'column')}, {plural(end - start - 2, 'row')}\t"
            + " | ".join(header)
        )


def expand(lines, table, body_col, level):
    start, end, heading = table
    header = split_row(lines[start])
    if body_col is not None and body_col not in header[1:]:
        raise ValueError(f"no column named {body_col!r}; columns: {', '.join(header)}")
    if level is None:
        level = min(len(HEADING.match(heading).group(1)) + 1, 6) if heading else 2

    sections = []
    seen = set()
    for number, line in enumerate(lines[start + 2 : end], start + 3):
        cells = split_row(line)
        if len(cells) > len(header):
            raise ValueError(
                f"line {number}: {len(cells)} cells but {len(header)} columns;"
                " the extra cells would be lost"
            )
        cells += [""] * (len(header) - len(cells))
        key = cells[0]
        if not key:
            raise ValueError(
                f"line {number}: empty first cell; every row needs a heading"
            )
        if key in seen:
            raise ValueError(
                f"line {number}: {key!r} appears twice; headings must be unique"
            )
        seen.add(key)

        parts = [f"{'#' * level} {key}", ""]
        for name, value in zip(header[1:], cells[1:]):
            if name == body_col and value:
                if MARKUP.match(value):
                    raise ValueError(
                        f"line {number}: the {body_col} cell {value!r} would read as"
                        " Markdown markup, not a paragraph; drop --body-col"
                    )
                parts += [value, ""]
        for name, value in zip(header[1:], cells[1:]):
            if name != body_col:
                parts.append(f"- **{name}:** {value}".rstrip())
        sections.append("\n".join(parts).rstrip("\n") + "\n")
    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog="To change a file: md-expand-table.py --table 2 f.md > f.new && mv f.new f.md",
    )
    parser.add_argument("file", nargs="?", help="Markdown file (default: stdin)")
    parser.add_argument(
        "--table",
        help="numbers of the tables to expand, from the list, comma-separated",
    )
    parser.add_argument(
        "--body-col", help="column to write as a paragraph instead of a bullet"
    )
    parser.add_argument(
        "--level", type=int, choices=range(1, 7), help="heading level for the rows"
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
    lines = text.splitlines(keepends=True)
    tables = find_tables(lines)

    if args.table is None:
        list_tables(lines, tables)
        return 0
    try:
        numbers = sorted({int(n) for n in args.table.split(",")}, reverse=True)
    except ValueError:
        parser.error(f"--table takes numbers such as 3 or 3,4; got {args.table!r}")
    for number in numbers:
        if not 1 <= number <= len(tables):
            print(
                f"table {number} does not exist; the document has {len(tables)}",
                file=sys.stderr,
            )
            return 2
    # Expand from the last table back, so earlier line numbers stay valid.
    for number in numbers:
        start, end, _ = tables[number - 1]
        try:
            sections = expand(lines, tables[number - 1], args.body_col, args.level)
        except ValueError as error:
            print(f"table {number}: {error}", file=sys.stderr)
            return 2
        if end < len(lines) and lines[end].strip():
            sections += "\n"
        lines[start:end] = [sections]
    sys.stdout.write("".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
