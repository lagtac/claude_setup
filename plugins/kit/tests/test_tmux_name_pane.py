"""Tests for bin/tmux-name-pane.py.

Run from plugins/kit: python3 -m unittest discover tests

Each test starts a private tmux server on its own socket, with no config file,
and runs the real script against one of its panes. The user's tmux server is
never touched: the script finds its server through the TMUX variable, and the
tests point it at the private socket.
"""

import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "tmux-name-pane.py"


@unittest.skipUnless(shutil.which("tmux"), "tmux is not installed")
class TmuxNamePaneTest(unittest.TestCase):
    def setUp(self):
        self.socket = f"name-pane-test-{os.getpid()}-{id(self)}"
        self.tmux("-f", os.devnull, "new-session", "-d", "-x", "120", "-y", "40")
        self.addCleanup(self.tmux, "kill-server", check=False)
        self.tmux("split-window", "-d")
        self.panes = self.tmux("list-panes", "-F", "#{pane_id}").split()
        self.path = self.tmux("display", "-p", "#{socket_path}")

    def tmux(self, *args, check=True):
        result = subprocess.run(["tmux", "-L", self.socket, *args],
                                capture_output=True, text=True, timeout=10)
        if check and result.returncode != 0:
            raise AssertionError(f"tmux {' '.join(args)}: {result.stderr}")
        return result.stdout.strip()

    def name(self, pane, *args, env=None):
        if env is None:
            env = {**os.environ, "TMUX": f"{self.path},0,0", "TMUX_PANE": pane}
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=env,
                              capture_output=True, text=True, timeout=10)

    def focus(self, pane):
        return self.tmux("display", "-p", "-t", pane, "#{@focus}")

    def window_name(self, pane=None, want=None):
        """The window name. tmux renames the window itself, so with want given,
        wait up to two seconds for that name before returning."""
        deadline = time.monotonic() + 2
        while True:
            name = self.tmux("display", "-p", "-t", pane or self.panes[0],
                             "#{window_name}")
            if want is None or name == want or time.monotonic() > deadline:
                return name
            time.sleep(0.05)

    def test_names_the_pane_and_the_window(self):
        result = self.name(self.panes[0], "r23: make meatballs")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.focus(self.panes[0]), "r23: make meatballs")
        self.assertEqual(self.window_name(want="r23: make meatballs"),
                         "r23: make meatballs")
        self.assertEqual(result.stdout.strip(), "r23: make meatballs")

    def test_window_name_joins_the_labels_in_pane_order(self):
        self.name(self.panes[1], "r54: put out fire")
        self.name(self.panes[0], "r23: make meatballs")
        want = "r23: make meatballs / r54: put out fire"
        self.assertEqual(self.window_name(want=want), want)

    def test_renaming_a_pane_replaces_only_its_label(self):
        self.name(self.panes[0], "r23: make meatballs")
        self.name(self.panes[1], "r54: put out fire")
        self.name(self.panes[0], "r12: bake bread")
        self.assertEqual(self.focus(self.panes[1]), "r54: put out fire")
        want = "r12: bake bread / r54: put out fire"
        self.assertEqual(self.window_name(want=want), want)

    def test_closing_a_pane_drops_its_label_from_the_window_name(self):
        self.name(self.panes[0], "r23: make meatballs")
        self.name(self.panes[1], "r54: put out fire")
        self.tmux("kill-pane", "-t", self.panes[0])
        self.assertEqual(self.window_name(self.panes[1], want="r54: put out fire"),
                         "r54: put out fire")

    def test_pane_border_keeps_the_users_own_format(self):
        self.tmux("set-option", "-g", "pane-border-format", " #{pane_index}: #{pane_title} ")
        self.name(self.panes[0], "r23: make meatballs")
        border = self.tmux("show-options", "-wAv", "-t", self.panes[0],
                           "pane-border-format")
        title = self.tmux("display", "-p", "-t", self.panes[1], "#{pane_title}")
        for pane, want in [(self.panes[0], "0: r23: make meatballs"),
                           (self.panes[1], f"1: {title}")]:
            with self.subTest(pane=pane):
                shown = self.tmux("display", "-p", "-t", pane, border)
                self.assertEqual(shown.strip(), want)

    def test_naming_twice_does_not_wrap_the_border_twice(self):
        self.name(self.panes[0], "r23: make meatballs")
        first = self.tmux("show-options", "-wv", "-t", self.panes[0], "pane-border-format")
        self.name(self.panes[0], "r12: bake bread")
        self.assertEqual(self.tmux("show-options", "-wv", "-t", self.panes[0],
                                   "pane-border-format"), first)

    def test_a_label_that_starts_with_a_dash_is_not_a_flag(self):
        result = self.name(self.panes[0], "-x fix crash")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.focus(self.panes[0]), "-x fix crash")

    def test_a_pane_that_no_longer_exists_names_nothing(self):
        env = {**os.environ, "TMUX": f"{self.path},0,0", "TMUX_PANE": "%999"}
        result = self.name("%999", "r23: make meatballs", env=env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("nothing named", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_pane_border_shows_the_label_and_falls_back_to_the_title(self):
        self.tmux("set-option", "-g", "pane-border-format", " #{pane_title} ")
        self.name(self.panes[0], "r23: make meatballs")
        border = self.tmux("show-options", "-wAv", "-t", self.panes[0],
                           "pane-border-format")
        for pane, want in [(self.panes[0], 'r23: make meatballs'),
                           (self.panes[1], self.tmux("display", "-p", "-t",
                                                     self.panes[1], "#{pane_title}"))]:
            with self.subTest(pane=pane):
                shown = self.tmux("display", "-p", "-t", pane, border)
                self.assertEqual(shown.strip(), want)

    def test_outside_tmux_it_names_nothing(self):
        before = self.window_name()
        env = {k: v for k, v in os.environ.items() if k not in ("TMUX", "TMUX_PANE")}
        result = self.name(self.panes[0], "r23: make meatballs", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not inside tmux", result.stderr)
        self.assertEqual(self.focus(self.panes[0]), "")
        self.assertEqual(self.window_name(), before)

    def test_an_empty_label_is_refused(self):
        result = self.name(self.panes[0], "  ")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empty label", result.stderr)
        self.assertEqual(self.focus(self.panes[0]), "")


if __name__ == "__main__":
    unittest.main()
