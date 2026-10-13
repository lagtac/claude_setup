---
name: md-tables
description: Turn a Markdown table into one section per row, or sections back into a table, with two stdin/stdout filters on PATH (md-expand-table.py, md-collapse-sections.py). Use when the user asks to expand, unfold or convert a table into sections, says a table is hard to read because its cells hold long text, or wants an overview table of sections with bold field bullets. NOT for editing a few cells, or for tables whose cells are short.
---

# Markdown tables and sections

Two filters on PATH move text between a table and sections. They never change a
file. Use them instead of rewriting a table by hand: a script moves every cell
unchanged, while a hand rewrite can drop or reword text.

## When a table should become sections

A table suits short cells that a reader compares down a column. When a column
holds sentences, or a row needs room to grow (a list of findings, say), one
section per row reads better. If the cells are short, leave the table alone.

## The section format

Both tools use this shape, one section per row:

```markdown
### X5

Optional paragraph: the column named with --body-col.

- **Level:** E
- **Status:** untested
```

The heading is the table's first column, so its values must be unique and not
empty. Every other column is a `- **Column:** value` bullet at the start of the
line. The collapse tool reads only those top-level bullets and the first
paragraph before them. Nested bullets, later paragraphs and code blocks inside
a section are allowed and ignored. So text can grow under a section, as long as
the field lines keep their shape. Keep each field value on one line, because
only the first line is read. A heading of any level ends the section, so do not
put subheadings inside one.

## Expand a table

1. List the tables. The command changes nothing:

   ```bash
   md-expand-table.py --list doc.md
   ```

   Each line shows the table number, its line, the heading above it, its size
   and its columns. Without `--list` or `--table`, the command expands every
   table. One table it refuses stops the whole run, so pass `--table` with only
   the tables it can expand.

2. Pick the tables with the user when it is not obvious which ones. Keep short
   lookup tables (a legend, a status list) as tables.

3. Expand into a new file, then move it into place:

   ```bash
   md-expand-table.py --table 3,4,5 --body-col Hypothesis doc.md > doc.new \
     && mv doc.new doc.md
   ```

   Never write `cmd doc.md > doc.md` or `cat doc.md | cmd > doc.md`: the shell
   empties the file before the command reads it.

   - `--table` takes the numbers from the list, even for several tables.
     Without it, every table is expanded.
   - `--body-col NAME` writes that column as a paragraph. Pick the long-text
     column that states what the row is.
   - `--level N` sets the heading level. By default it is one below the heading
     above the table.

4. Fix the prose around the tables, which the tool does not touch. Look for
   words like "row", "column" and "table" in the document and in files that
   describe it, such as `CLAUDE.md` or a template.

5. Run the project's Markdown linter.

The tool exits with code 2 and prints nothing to stdout when:

- a table number does not exist;
- a heading cell is empty or repeated;
- a column name, other than the first, is empty or repeated;
- a table is indented, because it may sit in a list item. Unindent it first;
- a row has more cells than the header;
- `--body-col` names no column, or one of its cells starts like Markdown markup
  (`#`, a list marker such as `-`, `*`, `+`, `1.` or `1)`, `>`, `|`, `<!--`, a
  code fence, or a rule such as `---` or `***`).
  Such a cell would become a heading, a list or a code block. Drop
  `--body-col` for that column.

It skips tables inside code fences, and lines whose header and dash line differ
in cell count, because GitHub does not render those as tables. It also skips
tables indented by four spaces or a tab, as code blocks (see Known limits).

## Collapse sections into a table

```bash
md-collapse-sections.py doc.md --key ID --fields Level,Status --body Claim --first-sentence
```

This prints the table to stdout. Use it to show an overview, not to store one. A
table written back into the document would drift when someone edits a section.

- `--fields A,B` picks the columns, in order. Without it, every field found is a
  column. Sections that have none of the fields are skipped.
- `--key NAME` names the heading column (default `Section`).
- `--body NAME` adds a column with each section's first paragraph, always as the
  second column. `--first-sentence` shortens it, but stops early at
  abbreviations such as "e.g.".
- A section that lacks one of the fields gets an empty cell, and a warning on
  stderr. Report those warnings to the user rather than hiding them.

## Known limits

- Rows under a level-6 heading stay at level 6, because Markdown has no level 7.
- Windows line endings (CRLF): with a FILE argument, every line ending in the
  output becomes LF. With stdin, the new sections use LF and the rest keeps
  CRLF, so endings can be mixed.
- A `--body-col` cell that starts with an HTML tag such as `<div>` is written as
  a paragraph, which GitHub reads as raw HTML.
- A table inside a list item that is indented by four spaces or more is
  skipped as a code block, so the tool does not list it. GitHub still renders
  it as a table.
- When text sits right above a table, the first new heading follows it with no
  blank line. The page renders correctly, but markdownlint rule MD022 flags it.
