"""Tests for bin/link-check.py.

Run from plugins/my: python3 -m unittest discover tests

Each test builds a throwaway repository in a temporary directory, with `main`
checked out and one root commit. The script runs there as a subprocess. Git
runs without the user's or the system's config, so a hook path or other
setting of the machine cannot change a result.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "link-check.py"


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


def make_repo(tmp):
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    write(repo, "root.md", "root\n")
    commit(repo, "root")
    return repo


def write(repo, path, text):
    target = Path(repo) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return target


def commit(repo, message):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", message)


def run(cwd, *files, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *files],
        cwd=cwd,
        env=clean_env(env or {}),
        capture_output=True,
        text=True,
        timeout=60,
    )


class LinkCheckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = make_repo(self.tmp)

    def tearDown(self):
        self._tmp.cleanup()

    def assertClean(self, result):
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    # Exit codes

    def test_clean_file_prints_nothing(self):
        write(self.repo, "docs/a.md", "a\n")
        write(self.repo, "ROADMAP.md", "[a](docs/a.md)\n")
        commit(self.repo, "clean")
        r = run(self.repo, "ROADMAP.md")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_problems_exit_1(self):
        write(self.repo, "ROADMAP.md", "[x](docs/gone.md)\n")
        self.assertEqual(run(self.repo, "ROADMAP.md").returncode, 1)

    def test_only_old_problems_exit_1(self):
        write(self.repo, "ROADMAP.md", "[x](docs/gone.md)\n")
        commit(self.repo, "dead link")
        r = run(self.repo, "ROADMAP.md")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.endswith("\told\n"), r.stdout)

    def test_no_args_exit_2(self):
        r = run(self.repo)
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.startswith("link-check.py:"), r.stderr)

    def test_unreadable_file_exit_2(self):
        r = run(self.repo, "missing.md")
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.startswith("link-check.py:"), r.stderr)

    def test_unreadable_file_others_still_checked(self):
        write(self.repo, "ROADMAP.md", "[x](docs/gone.md)\n")
        r = run(self.repo, "missing.md", "ROADMAP.md")
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stdout.startswith("dead\tROADMAP.md:"), r.stdout)

    def test_git_failure_exit_2(self):
        write(self.repo, "ROADMAP.md", "[x](docs/gone.md)\n")
        commit(self.repo, "dead link")
        stub_dir = self.tmp / "stub"
        stub_dir.mkdir()
        stub = stub_dir / "git"
        stub.write_text(
            "#!/bin/sh\n"
            'for a in "$@"; do [ "$a" = diff ] && exit 1; done\n'
            f'exec {shutil.which("git")} "$@"\n'
        )
        stub.chmod(0o755)
        path = clean_env()["PATH"]
        r = run(self.repo, "ROADMAP.md", env={"PATH": f"{stub_dir}:{path}"})
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("\tnew\n", r.stdout)
        self.assertTrue(r.stderr.startswith("link-check.py:"), r.stderr)

    def test_help_exit_0(self):
        r = run(self.repo, "--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Usage:", r.stdout)

    # Kinds

    def test_html_reported(self):
        write(self.repo, "docs/a.md", "a\n")
        write(self.repo, "docs/a.html", "<p>a</p>\n")
        commit(self.repo, "docs")
        write(self.repo, "ROADMAP.md", "# Roadmap\n\n[x](docs/a.html)\n")
        self.assertEqual(run(self.repo, "ROADMAP.md").stdout,
                         "html\tROADMAP.md:3\tdocs/a.html\tnew\n")

    def test_html_without_md_twin_ok(self):
        write(self.repo, "assets/page.html", "<p>page</p>\n")
        write(self.repo, "ROADMAP.md", "[x](assets/page.html)\n")
        commit(self.repo, "page")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_html_without_twin_or_file_is_dead(self):
        write(self.repo, "ROADMAP.md", "[x](docs/gone.html)\n")
        self.assertTrue(run(self.repo, "ROADMAP.md").stdout.startswith("dead\t"))

    def test_climbs_outside_repo_reported(self):
        write(self.tmp, "other/README.md", "other\n")
        write(self.repo, "ROADMAP.md", "[x](../other/README.md)\n")
        self.assertTrue(
            run(self.repo, "ROADMAP.md").stdout.startswith("climbs\tROADMAP.md:"))

    def test_parent_link_inside_repo_ok(self):
        write(self.repo, "ROADMAP.md", "roadmap\n")
        write(self.repo, "docs/plans/x.md", "[r](../../ROADMAP.md)\n")
        commit(self.repo, "plan")
        self.assertClean(run(self.repo, "docs/plans/x.md"))

    def test_dead_reported(self):
        write(self.repo, "ROADMAP.md", "[x](docs/gone.md)\n")
        self.assertEqual(run(self.repo, "ROADMAP.md").stdout,
                         "dead\tROADMAP.md:1\tdocs/gone.md\tnew\n")

    def test_ignored_file_is_dead(self):
        write(self.repo, ".gitignore", "secret/\n")
        commit(self.repo, "ignore")
        write(self.repo, "secret/x.md", "x\n")
        write(self.repo, "ROADMAP.md", "[x](secret/x.md)\n")
        self.assertTrue(run(self.repo, "ROADMAP.md").stdout.startswith("dead\t"))

    def test_tracked_but_ignored_pattern_ok(self):
        write(self.repo, ".gitignore", "secret/\n")
        write(self.repo, "secret/x.md", "x\n")
        git(self.repo, "add", "-f", "secret/x.md")
        write(self.repo, "ROADMAP.md", "[x](secret/x.md)\n")
        commit(self.repo, "forced")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_untracked_file_ok(self):
        write(self.repo, "ROADMAP.md", "[x](docs/new-spec.md)\n")
        commit(self.repo, "roadmap")
        write(self.repo, "docs/new-spec.md", "new\n")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_symlink_inside_repo_not_climbs(self):
        outside = write(self.tmp, "outside.md", "outside\n")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "out.md").symlink_to(outside)
        write(self.repo, "ROADMAP.md", "[x](docs/out.md)\n")
        commit(self.repo, "symlink")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_file_through_symlinked_folder_not_climbs(self):
        write(self.repo, "docs/a.md", "a\n")
        write(self.repo, "ROADMAP.md", "[x](docs/a.md)\n")
        commit(self.repo, "clean")
        link_dir = self.tmp / "link"
        link_dir.symlink_to(self.repo)
        self.assertClean(run(self.tmp, str(link_dir / "ROADMAP.md")))

    def test_one_problem_per_link(self):
        write(self.repo, "docs/a.md", "a\n")
        commit(self.repo, "docs")
        write(self.repo, "ROADMAP.md", "[x](docs/a.html)\n")
        self.assertEqual(run(self.repo, "ROADMAP.md").stdout.splitlines(),
                         ["html\tROADMAP.md:1\tdocs/a.html\tnew"])

    # What is a link

    def test_scheme_and_anchor_skipped(self):
        write(self.repo, "ROADMAP.md",
              "[a](https://x/y.html) [b](mailto:a@b) [c](#section)\n")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_fragment_and_query_stripped(self):
        write(self.repo, "docs/a.md", "a\n")
        write(self.repo, "ROADMAP.md", "[a](docs/a.md#part) [b](docs/a.md?x=1)\n")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_percent_decoded(self):
        write(self.repo, "docs/a b.md", "a\n")
        write(self.repo, "ROADMAP.md", "[a](docs/a%20b.md)\n")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_image_checked(self):
        write(self.repo, "ROADMAP.md", "![logo](img/gone.png)\n")
        self.assertIn("\timg/gone.png\t", run(self.repo, "ROADMAP.md").stdout)

    def test_reference_definition_checked(self):
        write(self.repo, "ROADMAP.md",
              "# Roadmap\n\nSee [the spec][spec].\n\n[spec]: docs/gone.md\n")
        self.assertIn("ROADMAP.md:5\tdocs/gone.md",
                      run(self.repo, "ROADMAP.md").stdout)

    def test_angle_brackets_and_title_removed(self):
        write(self.repo, "docs/a.md", "a\n")
        write(self.repo, "ROADMAP.md", '[x](<docs/a.md> "Title")\n')
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_link_over_two_lines_reports_target_line(self):
        write(self.repo, "ROADMAP.md", "# Roadmap\n[spec of\nthing](docs/gone.md)\n")
        self.assertTrue(
            run(self.repo, "ROADMAP.md").stdout.startswith("dead\tROADMAP.md:3\t"))

    # Code

    def test_fence_backticks_ignored(self):
        write(self.repo, "ROADMAP.md", "```markdown\n[x](docs/gone.md)\n```\n")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_fence_tildes_ignored(self):
        write(self.repo, "ROADMAP.md", "~~~\n[x](docs/gone.md)\n~~~\n")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_code_span_ignored(self):
        write(self.repo, "ROADMAP.md", "Write `[x](docs/gone.md)` like this.\n")
        self.assertClean(run(self.repo, "ROADMAP.md"))

    def test_indented_line_still_checked(self):
        write(self.repo, "ROADMAP.md",
              "- 📋 1 **Row**\n    [x](docs/gone.md)\n")
        self.assertTrue(run(self.repo, "ROADMAP.md").stdout.startswith("dead\t"))

    # new / old

    def test_committed_line_is_old(self):
        write(self.repo, "ROADMAP.md", "[x](docs/gone.md)\n")
        commit(self.repo, "dead link")
        self.assertTrue(run(self.repo, "ROADMAP.md").stdout.endswith("\told\n"))

    def test_other_line_of_edited_row_is_old(self):
        write(self.repo, "ROADMAP.md", "- 📋 1 **Row**\n  [s](docs/gone.md)\n")
        commit(self.repo, "row")
        write(self.repo, "ROADMAP.md", "- 🚧 1 **Row**\n  [s](docs/gone.md)\n")
        self.assertEqual(run(self.repo, "ROADMAP.md").stdout,
                         "dead\tROADMAP.md:2\tdocs/gone.md\told\n")

    def test_unstaged_edit_is_new(self):
        write(self.repo, "ROADMAP.md", "# Roadmap\n")
        commit(self.repo, "clean")
        write(self.repo, "ROADMAP.md", "# Roadmap\n[x](docs/gone.md)\n")
        self.assertTrue(run(self.repo, "ROADMAP.md").stdout.endswith("\tnew\n"))

    def test_staged_edit_is_new(self):
        write(self.repo, "ROADMAP.md", "# Roadmap\n")
        commit(self.repo, "clean")
        write(self.repo, "ROADMAP.md", "# Roadmap\n[x](docs/gone.md)\n")
        git(self.repo, "add", "ROADMAP.md")
        self.assertTrue(run(self.repo, "ROADMAP.md").stdout.endswith("\tnew\n"))

    def test_untracked_file_all_new(self):
        write(self.repo, "NOTES.md", "[x](docs/gone.md)\n")
        self.assertTrue(run(self.repo, "NOTES.md").stdout.endswith("\tnew\n"))

    def test_outside_git_all_new(self):
        folder = self.tmp / "plain"
        write(folder, "ROADMAP.md", "[x](docs/gone.md)\n")
        r = run(folder, "ROADMAP.md", env={"GIT_CEILING_DIRECTORIES": str(self.tmp)})
        self.assertEqual(r.stdout, "dead\tROADMAP.md:1\tdocs/gone.md\tnew\n")

    def test_outside_git_all_new_in_any_locale(self):
        folder = self.tmp / "plain"
        write(folder, "ROADMAP.md", "[x](docs/gone.md)\n")
        r = run(folder, "ROADMAP.md", env={"GIT_CEILING_DIRECTORIES": str(self.tmp),
                                           "LANGUAGE": "el", "LC_ALL": "el_GR.UTF-8"})
        self.assertEqual((r.returncode, r.stdout),
                         (1, "dead\tROADMAP.md:1\tdocs/gone.md\tnew\n"), r.stderr)

    def test_repo_without_commit_all_new(self):
        fresh = self.tmp / "fresh"
        fresh.mkdir()
        git(fresh, "init", "-q", "-b", "main")
        write(fresh, "ROADMAP.md", "[x](docs/gone.md)\n")
        git(fresh, "add", "ROADMAP.md")
        self.assertTrue(run(fresh, "ROADMAP.md").stdout.endswith("\tnew\n"))


if __name__ == "__main__":
    unittest.main()
