"""Tests for bin/ds-count.py.

Run from plugins/my: python3 -m unittest discover tests

Each test builds a throwaway repository in a temporary directory. The script
runs there as a subprocess. Git runs without the user's or the system's
config, so a setting of the machine cannot change a result.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "ds-count.py"
INVENTORY = "docs/DESIGN-SYSTEM.md"
BEFORE = "# Design system\n\n## Counts\n\n"
AFTER = "\nend\n"
# The block opens on file line 5, so its first pattern is on line 6.
FIRST_LINE = 6


def clean_env(extra={}):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_EDITOR"] = "false"
    env.update(extra)
    return env


def git(repo, *args, check=True):
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=clean_env(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def run(cwd, *args, env={}):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        env=clean_env(env),
        capture_output=True,
        text=True,
        timeout=60,
    )


def make_repo(tmp):
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    commit(repo, "root", {"root.md": "root\n"})
    return repo


def commit(repo, subject, files={}):
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        git(repo, "add", name)
    git(repo, "commit", "-q", "--allow-empty", "-m", subject)
    return git(repo, "rev-parse", "HEAD")


def line(**obj):
    return json.dumps(obj, ensure_ascii=False)


def inventory(lines, before=BEFORE, after=AFTER):
    body = "".join(f"{text}\n" for text in lines)
    return f"{before}```ds-patterns\n{body}```\n{after}"


FIELD = {"name": "text field", "kind": "hand-built", "globs": ["web/**/*.vue"],
         "exclude": ["web/components/Z*.vue"], "regex": r"<input\b"}


class DsCountTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = make_repo(self.tmp.name)
        commit(self.repo, "fixture", {
            "web/a.vue": "<input>\n<input>\n",
            "web/b/c.vue": "<input>\n",
            "web/components/ZField.vue": "<input>\n",
            INVENTORY: inventory([]),
        })
        self.path = self.repo / INVENTORY

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, lines, **kw):
        self.path.write_text(inventory(lines, **kw), encoding="utf-8")

    def assert_refused(self, out, text=None):
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertEqual(out.stdout, "")
        self.assertEqual(len(out.stderr.splitlines()), 1, out.stderr)
        if text is not None:
            self.assertIn(text, out.stderr)

    def assert_unchanged_after_write(self, lines):
        self.write(lines)
        before = self.path.read_bytes()
        out = run(self.repo, "--write")
        self.assertEqual(self.path.read_bytes(), before)
        return out

    def test_counts_matches_and_files(self):
        self.write([line(**FIELD)])
        out = run(self.repo)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "text field  hand-built  new -> 3/2\n")

    def test_exclude_removes_files(self):
        field = {k: v for k, v in FIELD.items() if k != "exclude"}
        self.write([line(**field)])
        self.assertEqual(run(self.repo).stdout, "text field  hand-built  new -> 4/3\n")
        self.write([line(**FIELD)])
        self.assertEqual(run(self.repo).stdout, "text field  hand-built  new -> 3/2\n")

    def test_globs_add_up(self):
        commit(self.repo, "blade", {"web/x.blade.php": "<input>\n"})
        self.write([line(**{**FIELD, "globs": ["web/**/*.vue", "web/**/*.blade.php"]})])
        self.assertEqual(run(self.repo).stdout, "text field  hand-built  new -> 4/3\n")

    def test_double_star_matches_deep_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            commit(repo, "deep", {
                "web/a/b/c.vue": "<input>\n",
                INVENTORY: inventory([line(name="f", kind="hand-built",
                                           globs=["web/**/*.vue"], regex=r"<input\b")]),
            })
            self.assertEqual(run(repo).stdout, "f  hand-built  new -> 1/1\n")

    def test_pattern_spans_lines(self):
        commit(self.repo, "button", {"web/btn.vue": "<ZButton\n  ghost>\n"})
        self.write([line(name="ZButton ghost", kind="component", globs=["web/**/*.vue"],
                         regex=r"<ZButton\s+ghost")])
        self.assertEqual(run(self.repo).stdout, "ZButton ghost  component  new -> 1/1\n")

    def test_write_changes_only_block(self):
        obj = {"name": "text field", "kind": "hand-built", "note": "x",
               "globs": FIELD["globs"], "exclude": FIELD["exclude"], "regex": FIELD["regex"]}
        self.write([line(**obj)])
        out = run(self.repo, "--write")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "text field  hand-built  new -> 3/2\n")
        expected = inventory([line(**obj, count=3, files=2)])
        self.assertEqual(self.path.read_bytes(), expected.encode("utf-8"))
        self.assertEqual(run(self.repo).stdout, "text field  hand-built  3/2 -> 3/2\n")

    def test_zero_match_reports_zero(self):
        self.write([line(**{**FIELD, "regex": r"<select\b"})])
        out = run(self.repo)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "text field  hand-built  new -> 0/0\n")

    def test_missing_block_refused(self):
        self.path.write_text("# Design system\n\nno block here\n")
        self.assert_refused(run(self.repo), INVENTORY)

    def test_bad_json_line_refused(self):
        self.write([line(**FIELD), "{oops"])
        self.assert_refused(run(self.repo), f"line {FIRST_LINE + 1}")

    def test_bad_regex_refused(self):
        self.write([line(**{**FIELD, "regex": "("})])
        self.assert_refused(run(self.repo), f"line {FIRST_LINE}")

    def test_duplicate_name_refused(self):
        out = self.assert_unchanged_after_write([line(**FIELD), line(**FIELD)])
        self.assert_refused(out, f"line {FIRST_LINE + 1}")

    def test_untracked_files_ignored(self):
        commit(self.repo, "ignore", {".gitignore": "web/node_modules/\n"})
        for name in ["web/new.vue", "web/node_modules/x.vue"]:
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("<input>\n")
        self.write([line(**FIELD)])
        self.assertEqual(run(self.repo).stdout, "text field  hand-built  new -> 3/2\n")

    def test_empty_block_valid(self):
        self.write([])
        out = run(self.repo)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "")

    def test_glob_matching_no_file_refused(self):
        self.write([line(**{**FIELD, "globs": ["wbe/**/*.vue"]})])
        self.assert_refused(run(self.repo), f"line {FIRST_LINE}")

    def test_excludes_leaving_no_file_report_zero(self):
        self.write([line(**{**FIELD, "globs": ["web/components/Z*.vue"],
                            "exclude": ["web/components/Z*.vue"]})])
        out = run(self.repo)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "text field  hand-built  new -> 0/0\n")

    def test_missing_required_key_refused(self):
        field = {k: v for k, v in FIELD.items() if k != "regex"}
        self.write([line(**field)])
        self.assert_refused(run(self.repo), f"line {FIRST_LINE}")

    def test_wrong_kind_refused(self):
        self.write([line(**{**FIELD, "kind": "widget"})])
        self.assert_refused(run(self.repo), f"line {FIRST_LINE}")

    def test_bool_count_refused(self):
        self.write([line(**FIELD, count=True, files=1)])
        self.assert_refused(run(self.repo), f"line {FIRST_LINE}")

    def test_empty_glob_refused(self):
        self.write([line(**{**FIELD, "globs": [""]})])
        self.assert_refused(run(self.repo), f"line {FIRST_LINE}")

    def test_empty_exclude_refused(self):
        self.write([line(**{**FIELD, "exclude": [""]})])
        self.assert_refused(run(self.repo), f"line {FIRST_LINE}")

    def test_conflicted_file_counted_once(self):
        self.write([line(**FIELD)])
        git(self.repo, "add", INVENTORY)
        git(self.repo, "commit", "-q", "-m", "inventory")
        git(self.repo, "checkout", "-q", "-b", "side")
        commit(self.repo, "side", {"web/a.vue": "<input>\nX\n"})
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, "main", {"web/a.vue": "<input>\nY\n"})
        git(self.repo, "merge", "side", check=False)
        self.assertIn("web/a.vue", git(self.repo, "diff", "--name-only", "--diff-filter=U"))
        out = run(self.repo)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "text field  hand-built  new -> 2/2\n")

    def test_non_ascii_kept(self):
        self.write([line(**{**FIELD, "name": "πεδίο κειμένου"})])
        out = run(self.repo, "--write")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('"name": "πεδίο κειμένου"', self.path.read_text(encoding="utf-8"))

    def test_deleted_tracked_file_skipped(self):
        os.remove(self.repo / "web/b/c.vue")
        self.write([line(**FIELD)])
        out = run(self.repo)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "text field  hand-built  new -> 2/1\n")

    def test_outside_repo_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "plain"
            folder.mkdir()
            (folder / "inv.md").write_text(inventory([line(**FIELD)]))
            out = run(folder, "inv.md", env={"GIT_CEILING_DIRECTORIES": tmp})
            self.assert_refused(out)

    # Review Focus
    def test_empty_match_regex_refused(self):
        out = self.assert_unchanged_after_write([line(**{**FIELD, "regex": r"\b"})])
        self.assert_refused(out, f"line {FIRST_LINE}")

    def test_unclosed_block_refused(self):
        text = f"{BEFORE}```ds-patterns\n{line(**FIELD)}\n"
        self.path.write_text(text)
        out = run(self.repo, "--write")
        self.assert_refused(out, INVENTORY)
        self.assertEqual(self.path.read_text(), text)

    def test_two_blocks_refused(self):
        self.write([line(**FIELD)], after=f"\n```ds-patterns\n```\n")
        self.assert_refused(run(self.repo), INVENTORY)

    def test_blank_lines_kept(self):
        other = {**FIELD, "name": "select", "regex": r"<select\b"}
        self.write([line(**FIELD), "", line(**other)])
        out = run(self.repo, "--write")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, "text field  hand-built  new -> 3/2\n"
                                     "select  hand-built  new -> 0/0\n")
        expected = inventory([line(**FIELD, count=3, files=2), "",
                              line(**other, count=0, files=0)])
        self.assertEqual(self.path.read_text(), expected)

    def test_write_keeps_crlf(self):
        text = inventory([line(**FIELD), line(**{**FIELD, "name": "two"})])
        self.path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        out = run(self.repo, "--write")
        self.assertEqual(out.returncode, 0, out.stderr)
        data = self.path.read_bytes()
        self.assertIn(b'"count": 3', data)
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))

    def test_run_from_subfolder(self):
        self.write([line(**FIELD)])
        root = run(self.repo).stdout
        out = run(self.repo / "web", "--write", "../docs/DESIGN-SYSTEM.md")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, root)
        self.assertIn('"count": 3', self.path.read_text())


if __name__ == "__main__":
    unittest.main()
