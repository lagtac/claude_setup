"""Tests for bin/md-expand-table.py and bin/md-collapse-sections.py.

Run from plugins/my: python3 -m unittest discover tests
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
EXPAND = BIN / "md-expand-table.py"
COLLAPSE = BIN / "md-collapse-sections.py"


def run(script, *args, stdin=""):
    return subprocess.run(
        [sys.executable, str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


DOC = """# Log

Intro text.

## Legend

| Status | Meaning |
| --- | --- |
| open | Nobody checked. |

```markdown
| Not | A table |
| --- | --- |
| in | a fence |
```

## Claims

| ID | Claim | Level | Status |
| --- | --- | --- | --- |
| X1 | Owners buy through friends. Cold sales fail. | E | open |
| X2 | Pipes \\| survive. | C | closed |

## After

Closing text.
"""

EXPANDED_CLAIMS = """### X1

Owners buy through friends. Cold sales fail.

- **Level:** E
- **Status:** open

### X2

Pipes | survive.

- **Level:** C
- **Status:** closed
"""


class ExpandListTest(unittest.TestCase):
    def test_lists_tables_outside_code_fences(self):
        result = run(EXPAND, stdin=DOC)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "1\tline 7\t## Legend\t2 columns, 1 row\tStatus | Meaning\n"
            "2\tline 19\t## Claims\t4 columns, 2 rows\tID | Claim | Level | Status\n",
        )

    def test_reads_a_file_argument(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "doc.md"
        path.write_text(DOC)
        from_file = run(EXPAND, str(path)).stdout
        self.assertIn("## Claims", from_file)
        self.assertEqual(from_file, run(EXPAND, stdin=DOC).stdout)


class ExpandTableTest(unittest.TestCase):
    def test_replaces_only_the_chosen_table(self):
        result = run(EXPAND, "--table", "2", "--body-col", "Claim", stdin=DOC)
        self.assertEqual(result.returncode, 0, result.stderr)
        table = DOC[DOC.index("| ID |") : DOC.index("\n## After")]
        self.assertEqual(result.stdout, DOC.replace(table, EXPANDED_CLAIMS))

    def test_without_body_col_every_column_is_a_field(self):
        result = run(EXPAND, "--table", "1", stdin=DOC)
        self.assertIn("### open\n\n- **Meaning:** Nobody checked.\n", result.stdout)

    def test_level_overrides_the_heading_depth(self):
        result = run(EXPAND, "--table", "1", "--level", "5", stdin=DOC)
        self.assertIn("\n##### open\n", result.stdout)

    def test_finds_tables_without_outer_pipes(self):
        doc = "## T\n\nKey | Value\n--- | ---\na | 1\n"
        result = run(EXPAND, "--table", "1", stdin=doc)
        self.assertEqual(result.stdout, "## T\n\n### a\n\n- **Value:** 1\n")

    def test_keeps_empty_cells_as_empty_fields(self):
        doc = "| K | A | B |\n| --- | --- | --- |\n| k |  | 2 |\n"
        result = run(EXPAND, "--table", "1", stdin=doc)
        self.assertEqual(result.stdout, "## k\n\n- **A:**\n- **B:** 2\n")

    def test_pads_short_rows_with_empty_fields(self):
        doc = "| K | A | B |\n| --- | --- | --- |\n| k | 1 |\n"
        result = run(EXPAND, "--table", "1", stdin=doc)
        self.assertEqual(result.stdout, "## k\n\n- **A:** 1\n- **B:**\n")

    def test_expands_several_tables_by_their_listed_numbers(self):
        both = run(EXPAND, "--table", "1,2", stdin=DOC).stdout
        second_first = run(EXPAND, "--table", "2", stdin=DOC).stdout
        expected = run(EXPAND, "--table", "1", stdin=second_first).stdout
        self.assertIn("### open", both)
        self.assertIn("### X2", both)
        self.assertEqual(both, expected)

    def test_rejects_a_table_number_that_is_not_a_number(self):
        result = run(EXPAND, "--table", "x", stdin=DOC)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--table", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_a_table_number_out_of_range(self):
        result = run(EXPAND, "--table", "3", stdin=DOC)
        self.assertEqual(result.returncode, 2)
        self.assertIn("table 3", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_rejects_repeated_keys(self):
        doc = DOC.replace("| X2 |", "| X1 |")
        result = run(EXPAND, "--table", "2", stdin=doc)
        self.assertEqual(result.returncode, 2)
        self.assertIn("X1", result.stderr)

    def test_rejects_empty_keys(self):
        doc = DOC.replace("| X2 |", "|  |")
        result = run(EXPAND, "--table", "2", stdin=doc)
        self.assertEqual(result.returncode, 2)
        self.assertIn("empty", result.stderr)

    def test_rejects_an_unknown_body_column(self):
        result = run(EXPAND, "--table", "2", "--body-col", "Nope", stdin=DOC)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Nope", result.stderr)


SECTIONS = """# Log

## Claims

Intro with no fields.

### X1

Owners buy through friends. Cold sales fail.

- **Level:** E
- **Status:** open
- **Evidence:**
  - **Level:** B interview, not a field.

### X2

Pipes | survive.

- **Status:** closed

### Legend

| Status | Meaning |
| --- | --- |

```markdown
### X9

- **Level:** A
```
"""


class CollapseTest(unittest.TestCase):
    def test_uses_every_field_found_by_default(self):
        result = run(COLLAPSE, stdin=SECTIONS)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "| Section | Level | Status | Evidence |\n"
            "| --- | --- | --- | --- |\n"
            "| X1 | E | open |  |\n"
            "| X2 |  | closed |  |\n",
        )

    def test_fields_choose_columns_and_warn_about_gaps(self):
        result = run(
            COLLAPSE, "--fields", "Status,Level", "--key", "ID", stdin=SECTIONS
        )
        self.assertEqual(
            result.stdout,
            "| ID | Status | Level |\n"
            "| --- | --- | --- |\n"
            "| X1 | open | E |\n"
            "| X2 | closed |  |\n",
        )
        self.assertIn("X2: no **Level:** field", result.stderr)

    def test_skips_sections_with_none_of_the_fields(self):
        result = run(COLLAPSE, "--fields", "Evidence", stdin=SECTIONS)
        self.assertEqual(
            result.stdout, "| Section | Evidence |\n| --- | --- |\n| X1 |  |\n"
        )
        self.assertEqual(result.stderr, "")

    def test_body_column_holds_the_first_paragraph(self):
        result = run(COLLAPSE, "--body", "Claim", "--fields", "Status", stdin=SECTIONS)
        self.assertIn(
            "| X1 | Owners buy through friends. Cold sales fail. | open |",
            result.stdout,
        )
        self.assertIn("| X2 | Pipes \\| survive. | closed |", result.stdout)

    def test_first_sentence_shortens_the_body(self):
        result = run(
            COLLAPSE,
            "--body",
            "Claim",
            "--first-sentence",
            "--fields",
            "Status",
            stdin=SECTIONS,
        )
        self.assertIn("| X1 | Owners buy through friends. | open |", result.stdout)

    def test_reports_when_no_section_has_fields(self):
        result = run(COLLAPSE, stdin="# Only prose\n\nText.\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no sections", result.stderr)


class RoundTripTest(unittest.TestCase):
    def test_collapse_undoes_expand(self):
        table = DOC[DOC.index("| ID |") : DOC.index("\n## After")]
        expanded = run(
            EXPAND, "--table", "1", "--body-col", "Claim", stdin=table
        ).stdout
        collapsed = run(
            COLLAPSE, "--key", "ID", "--body", "Claim", stdin=expanded
        ).stdout
        self.assertEqual(collapsed, table)


class ReviewFixTest(unittest.TestCase):
    """Cases found by the end-of-branch reviews."""

    def test_expand_rejects_rows_with_more_cells_than_the_header(self):
        doc = "| K | A |\n| --- | --- |\n| k | 1 | extra |\n"
        result = run(EXPAND, "--table", "1", stdin=doc)
        self.assertEqual(result.returncode, 2)
        self.assertIn("line 3", result.stderr)

    def test_expand_leaves_a_blank_line_before_following_text(self):
        doc = "| K | A |\n| --- | --- |\n| k | 1 |\n\nAfter.\n"
        tight = "| K | A |\n| --- | --- |\n| k | 1 |\n- next\n"
        self.assertTrue(
            run(EXPAND, "--table", "1", stdin=doc).stdout.endswith(
                "- **A:** 1\n\nAfter.\n"
            )
        )
        self.assertTrue(
            run(EXPAND, "--table", "1", stdin=tight).stdout.endswith(
                "- **A:** 1\n\n- next\n"
            )
        )

    def test_expand_rejects_body_values_that_read_as_markup(self):
        for value in ["# note", "- item", "1. first", "> quote", "<!-- c -->"]:
            doc = f"| K | B |\n| --- | --- |\n| k | {value} |\n"
            result = run(EXPAND, "--table", "1", "--body-col", "B", stdin=doc)
            self.assertEqual(result.returncode, 2, value)
            self.assertIn("--body-col", result.stderr)

    def test_expand_ignores_fence_markers_inside_a_longer_fence(self):
        doc = "````\n```\n````\n\n| K | A |\n| --- | --- |\n| k | 1 |\n"
        self.assertIn("1\tline 5", run(EXPAND, stdin=doc).stdout)
        tilde = "~~~\n```\n| X | Y |\n| --- | --- |\n~~~\n"
        self.assertEqual(run(EXPAND, stdin=tilde).stdout, "")

    def test_expand_skips_rows_whose_cell_count_differs_from_the_dash_line(self):
        uneven = "a | b | c\n--- | ---\nx | y | z\n"
        self.assertEqual(run(EXPAND, stdin=uneven).stdout, "")

    def test_collapse_keeps_a_hash_at_the_end_of_a_heading(self):
        doc = "## C#\n\n- **A:** 1\n\n## D ##\n\n- **A:** 2\n"
        result = run(COLLAPSE, stdin=doc)
        self.assertIn("| C# | 1 |", result.stdout)
        self.assertIn("| D | 2 |", result.stdout)

    def test_collapse_reads_field_names_that_contain_a_star(self):
        result = run(COLLAPSE, stdin="## k\n\n- **Cost (*):** 5\n")
        self.assertIn("| Section | Cost (*) |", result.stdout)

    def test_collapse_body_is_the_paragraph_before_the_fields(self):
        doc = "## A\n\n- **X:** 1\n\nA later note.\n"
        result = run(COLLAPSE, "--body", "Claim", stdin=doc)
        self.assertIn("| A |  | 1 |", result.stdout)

    def test_collapse_ignores_fence_markers_inside_a_longer_fence(self):
        doc = "## A\n\n- **X:** 1\n\n~~~\n```\n~~~\n\n## B\n\n- **X:** 2\n"
        self.assertIn("| B | 2 |", run(COLLAPSE, stdin=doc).stdout)

    def test_both_tools_read_and_write_utf8_whatever_the_locale(self):
        doc = "| K | A |\n| --- | --- |\n| Πειραιάς | CO₂ |\n"
        env = {
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
            "PYTHONCOERCECLOCALE": "0",
            "PYTHONUTF8": "0",
        }
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "doc.md"
        path.write_text(doc, encoding="utf-8")
        expanded = subprocess.run(
            [sys.executable, str(EXPAND), "--table", "1", str(path)],
            capture_output=True,
            env=env,
        )
        self.assertEqual(
            expanded.stdout.decode("utf-8"), "## Πειραιάς\n\n- **A:** CO₂\n"
        )
        collapsed = subprocess.run(
            [sys.executable, str(COLLAPSE)],
            input=expanded.stdout,
            capture_output=True,
            env=env,
        )
        self.assertIn("| Πειραιάς | CO₂ |", collapsed.stdout.decode("utf-8"))


class ReReviewFixTest(unittest.TestCase):
    """Cases found by the final re-review of the fix round."""

    def test_expand_rejects_body_cells_that_open_a_fence_or_draw_a_rule(self):
        for value in ["```py", "~~~", "---", "* * *"]:
            doc = f"| K | B |\n| --- | --- |\n| k | {value} |\n"
            result = run(EXPAND, "--table", "1", "--body-col", "B", stdin=doc)
            self.assertEqual(result.returncode, 2, value)

    def test_collapse_ignores_bold_text_before_a_later_label(self):
        result = run(COLLAPSE, stdin="## A\n\n- **Bold** note: **x:** y\n- **L:** 1\n")
        self.assertEqual(result.stdout, "| Section | L |\n| --- | --- |\n| A | 1 |\n")

    def test_expand_lists_a_table_inside_a_nested_list_item(self):
        doc = "- outer\n  - inner\n\n    | a | b |\n    |---|---|\n    | 1 | 2 |\n"
        self.assertIn("1\tline 4", run(EXPAND, stdin=doc).stdout)


if __name__ == "__main__":
    unittest.main()
