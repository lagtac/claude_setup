"""Tests for hooks/method-guard.py.

Run from plugins/kit: python3 -m unittest discover tests

Each test builds a temporary HOME (with .claude/settings.json and a
known_marketplaces.json that points at a fake marketplace) and a temporary
project, then runs the script as a subprocess, the way Claude Code runs a
SessionStart hook. The guard calls the real bin/claude-method beside it, which
reads the fake marketplace. HOME and CLAUDE_PROJECT_DIR are set for each call,
so the user's own settings cannot change a result.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "method-guard.py"

MY_IMPORT = "@~/.claude/methods/my.md\n"
ON = {"my@claude-setup": True, "superpowers@synced": True}
# The fake marketplace: name, category, dependencies.
PLUGINS = [("my", "method", ["superpowers@synced"]),
           ("kit", "development", None),
           ("sp", "method", ["superpowers@synced"]),
           ("tutor", "method", None),
           ("x", "method", ["y@claude-setup"])]


def write(path, content):
    """Write a dict as JSON, or a string as it is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, newline="")
    else:
        path.write_text(json.dumps(content))


def two_methods(keys):
    return (f"method guard: more than one method is on: {', '.join(keys)}. "
            "Claude Code applies only the first style it loads. Keep one with "
            "/kit:setup <method>.")


def dependency(method, key):
    return (f"method guard: the {method} method is on, but its dependency {key} "
            f"is off. Run /kit:setup {method}.")


def old_import(name, method):
    return (f"method guard: {name} still has the line "
            f"@~/.claude/methods/{method}.md. Run /kit:setup {method}.")


class GuardTest(unittest.TestCase):
    def make_world(self, user_plugins=None, project_md="", local_md=None,
                   project_plugins=None, local_plugins=None, known=True):
        """Build a temporary HOME, marketplace and project; return (home, project).

        A plugins argument that is a dict becomes {"enabledPlugins": dict};
        a string is written as the file's whole content. None writes no file.
        known=False writes no known_marketplaces.json.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        home = Path(tmp.name) / "home"
        project = Path(tmp.name) / "project"
        market = Path(tmp.name) / "market"
        home.mkdir()
        project.mkdir()
        entries = []
        for name, category, deps in PLUGINS:
            entries.append({"name": name, "source": f"./plugins/{name}",
                            "category": category})
            manifest = {"name": name}
            if deps is not None:
                manifest["dependencies"] = deps
            write(market / "plugins" / name / ".claude-plugin" / "plugin.json", manifest)
        write(market / ".claude-plugin" / "marketplace.json",
              {"name": "claude-setup", "plugins": entries})
        if known:
            write(home / ".claude" / "plugins" / "known_marketplaces.json",
                  {"claude-setup": {"installLocation": str(market)}})
        for path, plugins in [
                (home / ".claude" / "settings.json", user_plugins),
                (project / ".claude" / "settings.json", project_plugins),
                (project / ".claude" / "settings.local.json", local_plugins)]:
            if plugins is not None:
                write(path, plugins if isinstance(plugins, str)
                      else {"enabledPlugins": plugins})
        write(project / "CLAUDE.md", project_md)
        if local_md is not None:
            write(project / "CLAUDE.local.md", local_md)
        return home, project

    def run_guard(self, home, project, project_dir=True, cwd=None, env=None):
        full = {k: v for k, v in os.environ.items()
                if k not in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_ROOT",
                             "CLAUDE_METHOD_MARKETPLACE") and not k.startswith("GIT_")}
        full["HOME"] = str(home)
        if project_dir is True:
            full["CLAUDE_PROJECT_DIR"] = str(project)
        elif project_dir:
            full["CLAUDE_PROJECT_DIR"] = project_dir
        full.update(env or {})
        return subprocess.run([sys.executable, str(SCRIPT)], env=full,
                              cwd=cwd or project, capture_output=True,
                              text=True, timeout=20)

    def text(self, result):
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        message = out["systemMessage"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertEqual(out["hookSpecificOutput"]["additionalContext"], message)
        return message

    def quiet(self, result):
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_my_set_up_prints_nothing(self):
        home, project = self.make_world(project_plugins=ON)
        self.quiet(self.run_guard(home, project))

    def test_synced_key_missing_counts_on(self):
        home, project = self.make_world(project_plugins={"my@claude-setup": True})
        self.quiet(self.run_guard(home, project))

    def test_two_methods_on_names_both(self):
        home, project = self.make_world(project_plugins=ON,
                                        local_plugins={"sp@claude-setup": True})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         two_methods(["my@claude-setup", "sp@claude-setup"]))

    def test_missing_dependency_names_key(self):
        home, project = self.make_world(
            project_plugins={"my@claude-setup": True, "superpowers@synced": False})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         dependency("my", "superpowers@synced"))

    def test_non_synced_dependency_missing_counts_off(self):
        home, project = self.make_world(project_plugins={"x@claude-setup": True})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         dependency("x", "y@claude-setup"))

    def test_old_import_in_claude_md(self):
        home, project = self.make_world(project_md=MY_IMPORT, project_plugins=ON)
        self.assertEqual(self.text(self.run_guard(home, project)),
                         old_import("CLAUDE.md", "my"))

    def test_old_import_in_claude_local_md(self):
        home, project = self.make_world(local_md="@~/.claude/methods/tutor.md\n",
                                        project_plugins={"tutor@claude-setup": True})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         old_import("CLAUDE.local.md", "tutor"))

    def test_import_line_with_crlf_counts(self):
        home, project = self.make_world(project_md="@~/.claude/methods/my.md  \r\n",
                                        project_plugins=ON)
        self.assertEqual(self.text(self.run_guard(home, project)),
                         old_import("CLAUDE.md", "my"))

    def test_local_settings_override_project(self):
        home, project = self.make_world(
            project_plugins={"my@claude-setup": True, "sp@claude-setup": True},
            local_plugins={"my@claude-setup": False})
        self.quiet(self.run_guard(home, project))

    def test_string_true_is_not_on(self):
        # Were "true" on, my and sp would both be on.
        home, project = self.make_world(
            project_plugins={"my@claude-setup": "true", "sp@claude-setup": True})
        self.quiet(self.run_guard(home, project))

    def test_unreadable_user_settings(self):
        home, project = self.make_world(user_plugins="{", project_plugins=ON)
        self.assertEqual(self.text(self.run_guard(home, project)),
                         f"method guard could not read {home}/.claude/settings.json")

    def test_settings_not_an_object_is_unreadable(self):
        for content in ["[]", '{"enabledPlugins": []}']:
            with self.subTest(content=content):
                home, project = self.make_world(project_plugins=content)
                lines = self.text(self.run_guard(home, project)).split("\n")
                self.assertEqual(lines[0], "method guard could not read "
                                 f"{project}/.claude/settings.json")

    def test_claude_method_failure_gives_one_warning(self):
        home, project = self.make_world(project_md=MY_IMPORT, project_plugins=ON,
                                        known=False)
        lines = self.text(self.run_guard(home, project)).split("\n")
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(
            "method guard: claude-method --methods failed: "), lines[0])
        self.assertIn("known_marketplaces.json", lines[0])

    def test_missing_script_gives_one_warning(self):
        home, project = self.make_world(project_md=MY_IMPORT, project_plugins=ON)
        empty = home / "empty-plugin-root"
        empty.mkdir()
        lines = self.text(self.run_guard(home, project, env={
            "CLAUDE_PLUGIN_ROOT": str(empty)})).split("\n")
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(
            "method guard: claude-method --methods failed: "), lines[0])

    def test_root_falls_back_to_git_toplevel(self):
        home, project = self.make_world(project_md=MY_IMPORT, project_plugins=ON)
        subprocess.run(["git", "init", "-q", str(project)], check=True,
                       env={**os.environ, "HOME": str(home)})
        sub = project / "src" / "deep"
        sub.mkdir(parents=True)
        result = self.run_guard(home, project, project_dir=False, cwd=sub)
        self.assertEqual(self.text(result), old_import("CLAUDE.md", "my"))

    def test_output_is_capped(self):
        names = [f"{i:02d}-" + "a" * 57 for i in range(40)]
        md = "".join(f"@~/.claude/methods/{n}.md\n" for n in names)
        home, project = self.make_world(project_md=md)
        message = self.text(self.run_guard(home, project))
        self.assertTrue(message.startswith(old_import("CLAUDE.md", names[0])))
        self.assertLessEqual(len(message), 2000)

    def test_exit_code_is_zero_in_every_case(self):
        worlds = [
            {}, {"project_md": MY_IMPORT}, {"project_plugins": ON},
            {"user_plugins": "{"}, {"project_plugins": "[]"},
            {"local_plugins": "not json"}, {"known": False},
            {"project_plugins": {"my@claude-setup": True, "sp@claude-setup": True,
                                 "superpowers@synced": False}},
        ]
        for world in worlds:
            with self.subTest(world=world):
                home, project = self.make_world(**world)
                self.assertEqual(self.run_guard(home, project).returncode, 0)

    def test_hooks_json_has_no_tutor_hook(self):
        hooks = json.loads((SCRIPT.parent / "hooks.json").read_text())["hooks"]
        commands = [h["command"] for e in hooks["SessionStart"] for h in e["hooks"]]
        self.assertFalse([c for c in commands if "curriculum.md" in c])

    def test_hooks_json_runs_the_guard_at_session_start(self):
        hooks = json.loads((SCRIPT.parent / "hooks.json").read_text())["hooks"]
        commands = [(entry["matcher"], h["command"], h["timeout"])
                    for entry in hooks["SessionStart"] for h in entry["hooks"]
                    if "method-guard" in h["command"]]
        self.assertEqual(commands, [(
            "startup|resume|clear",
            'python3 "$CLAUDE_PLUGIN_ROOT/hooks/method-guard.py"', 10)])


if __name__ == "__main__":
    unittest.main()
