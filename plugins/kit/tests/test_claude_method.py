"""Tests for bin/claude-method.

Run from plugins/kit: python3 -m unittest discover tests

Each test builds a temporary marketplace and a temporary HOME whose
.claude/plugins/known_marketplaces.json points at it, then runs the script
as a subprocess. A fake `claude`, first on PATH in every call, prints its
arguments as JSON, so the real binary never runs.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "claude-method"
REPO = Path(__file__).resolve().parents[3]

MY = {"my@claude-setup": True, "superpowers@synced": True,
      "sp@claude-setup": False, "tutor@claude-setup": False}

FAKE_CLAUDE = "#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n"


def write(path, content):
    """Write a dict or list as JSON, or a string as it is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if isinstance(content, str) else json.dumps(content))


class ClaudeMethodTest(unittest.TestCase):
    def setUp(self):
        self.make_world()

    def make_world(self, tutor_deps=None, known=None, marketplace=None):
        """Build a marketplace, a HOME and a fake claude.

        tutor_deps: the tutor manifest's dependencies (None: no field).
        known: the whole known_marketplaces.json as a string (None: an entry
        claude-setup pointing at the marketplace). marketplace: the whole
        marketplace.json as a string (None: entries my, kit, sp, tutor).
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.market = base / "market"
        self.home = base / "home"
        self.bin = base / "bin"
        entries = []
        for name, category, deps in [("my", "method", ["superpowers@synced"]),
                                     ("kit", "development", None),
                                     ("sp", "method", ["superpowers@synced"]),
                                     ("tutor", "method", tutor_deps)]:
            entries.append({"name": name, "source": f"./plugins/{name}",
                            "description": f"The {name} plugin", "category": category})
            manifest = {"name": name}
            if deps is not None:
                manifest["dependencies"] = deps
            write(self.market / "plugins" / name / ".claude-plugin" / "plugin.json", manifest)
        write(self.market / ".claude-plugin" / "marketplace.json",
              marketplace if marketplace is not None
              else {"name": "claude-setup", "plugins": entries})
        write(self.home / ".claude" / "plugins" / "known_marketplaces.json",
              known if known is not None
              else {"claude-setup": {"installLocation": str(self.market)}})
        write(self.bin / "claude", FAKE_CLAUDE)
        (self.bin / "claude").chmod(0o755)

    def run_cm(self, *args, env=None, cwd=None):
        full = {k: v for k, v in os.environ.items() if k != "CLAUDE_METHOD_MARKETPLACE"}
        full["HOME"] = str(self.home)
        full["PATH"] = f"{self.bin}{os.pathsep}{full.get('PATH', '')}"
        full.update(env or {})
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=full,
                              cwd=cwd or self.home, capture_output=True, text=True,
                              timeout=10)

    def settings(self, *args):
        r = self.run_cm(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_no_argument_lists_methods_and_none(self):
        r = self.run_cm()
        self.assertEqual(r.returncode, 0)
        self.assertEqual([l.split("\t")[0] for l in r.stdout.splitlines()],
                         ["my", "sp", "tutor", "none"])

    def test_unknown_method_lists_and_exits_1(self):
        r = self.run_cm("nope")
        self.assertEqual(r.returncode, 1)
        self.assertIn("claude-method: no method named nope", r.stderr)
        self.assertIn("tutor\t", r.stderr)

    def test_json_my(self):
        self.assertEqual(self.settings("--json", "my"), {"enabledPlugins": MY})

    def test_json_tutor_turns_superpowers_off(self):
        self.assertEqual(self.settings("--json", "tutor")["enabledPlugins"],
                         {"tutor@claude-setup": True, "my@claude-setup": False,
                          "sp@claude-setup": False, "superpowers@synced": False})

    def test_json_sp_keeps_shared_dependency_on(self):
        self.assertEqual(self.settings("--json", "sp")["enabledPlugins"],
                         {"sp@claude-setup": True, "superpowers@synced": True,
                          "my@claude-setup": False, "tutor@claude-setup": False})

    def test_json_none_turns_everything_off(self):
        self.assertEqual(set(self.settings("--json", "none")["enabledPlugins"].values()),
                         {False})

    def test_methods_maps_each_method_to_its_dependencies(self):
        self.assertEqual(self.settings("--methods"),
                         {"my@claude-setup": ["superpowers@synced"],
                          "sp@claude-setup": ["superpowers@synced"], "tutor@claude-setup": []})

    def test_bare_and_object_dependencies_get_full_keys(self):
        self.make_world(tutor_deps=["kit", {"name": "x", "marketplace": "other"},
                                    {"name": "y"}])
        self.assertEqual(self.settings("--methods")["tutor@claude-setup"],
                         ["kit@claude-setup", "x@other", "y@claude-setup"])

    def test_exec_runs_claude_with_settings_and_args(self):
        argv = json.loads(self.run_cm("my", "-n", "x", "-p", "hi").stdout)
        self.assertEqual(argv[0], "--settings")
        self.assertEqual(json.loads(argv[1]), {"enabledPlugins": MY})
        self.assertEqual(argv[2:], ["-n", "x", "-p", "hi"])

    def test_plugin_dir_naming_a_method_turns_its_marketplace_key_off(self):
        argv = json.loads(self.run_cm("my", "--plugin-dir",
                                      str(self.market / "plugins/my")).stdout)
        self.assertEqual(json.loads(argv[1])["enabledPlugins"]["my@claude-setup"], False)
        self.assertEqual(json.loads(argv[1])["enabledPlugins"]["superpowers@synced"], True)
        self.assertEqual(argv[2:], ["--plugin-dir", str(self.market / "plugins/my")])

    def test_plugin_dir_with_equals_and_relative_path(self):
        argv = json.loads(self.run_cm("my", "--plugin-dir=plugins/my", cwd=self.market).stdout)
        self.assertEqual(json.loads(argv[1])["enabledPlugins"]["my@claude-setup"], False)

    def test_plugin_dir_not_a_method_changes_nothing(self):
        argv = json.loads(self.run_cm("my", "--plugin-dir",
                                      str(self.market / "plugins/kit")).stdout)
        self.assertEqual(json.loads(argv[1]), {"enabledPlugins": MY})

    def test_settings_flag_is_refused_with_exit_2(self):
        for args in (["--settings", "{}"], ["--settings={}"]):
            with self.subTest(args=args):
                r = self.run_cm("my", "-p", "x", *args)
                self.assertEqual(r.returncode, 2)
                self.assertIn("--settings is not allowed", r.stderr)
                self.assertEqual(r.stdout, "")   # the fake claude never ran

    def test_missing_marketplace_entry_exits_1_naming_the_file(self):
        self.make_world(known=json.dumps({"other": {"installLocation": "/nowhere"}}))
        r = self.run_cm("--methods")
        self.assertEqual(r.returncode, 1)
        self.assertIn("known_marketplaces.json", r.stderr)

    def test_unreadable_marketplace_json_exits_1_naming_the_file(self):
        self.make_world(marketplace="{")
        r = self.run_cm("--methods")
        self.assertEqual(r.returncode, 1)
        self.assertIn("marketplace.json", r.stderr)

    def test_marketplace_variable_wins(self):
        market = self.market
        self.make_world(known=json.dumps({"claude-setup": {"installLocation": "/nowhere"}}))
        r = self.run_cm("--methods", env={"CLAUDE_METHOD_MARKETPLACE": str(market)})
        self.assertEqual(r.returncode, 0, r.stderr)


    def test_real_marketplace(self):
        r = self.run_cm("--methods", env={"CLAUDE_METHOD_MARKETPLACE": str(REPO)})
        self.assertEqual(json.loads(r.stdout),
                         {"my@claude-setup": ["superpowers@synced"],
                          "sp@claude-setup": ["superpowers@synced"], "tutor@claude-setup": []})

if __name__ == "__main__":
    unittest.main()
