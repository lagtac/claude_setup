"""Tests for hooks/method-guard.py.

Run from plugins/kit: python3 -m unittest discover tests

Each test builds a temporary HOME (with .claude/settings.json and
.claude.json) and a temporary project, then runs the script as a subprocess,
the way Claude Code runs a SessionStart hook. HOME and CLAUDE_PROJECT_DIR are
set for each call, so the user's own settings cannot change a result.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "method-guard.py"

MY = "@~/.claude/methods/my.md\n"
TUTOR = "@~/.claude/methods/tutor.md\n"
ON = {"my@claude-setup": True, "superpowers@synced": True}
OFF = {"my@claude-setup": False, "superpowers@synced": False}


def write(path, content):
    """Write a dict as JSON, or a string as it is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, newline="")
    else:
        path.write_text(json.dumps(content))


def not_approved(name):
    return (f"method guard: the {name} method import is not approved, so its "
            f"rules are not loaded. Read ~/.claude/methods/{name}.md before "
            "your first reply, and ask the user to approve the import (start "
            "a new interactive session in this directory).")


def declined(name, root):
    return (f"method guard: the {name} method import was declined earlier, so "
            "its rules are not loaded and Claude Code will not ask again. Read "
            f"~/.claude/methods/{name}.md before your first reply. To be asked "
            f'again, set projects["{root}"].hasClaudeMdExternalIncludesWarningShown '
            "to false in ~/.claude.json while no session runs in this "
            "directory, then start a new interactive session here.")


def stray(keys):
    lines = ", ".join(f'"{k}": false' for k in keys)
    return ("method guard: this project does not import the my method, but "
            f"these plugins are on: {', '.join(keys)}. To turn them off, add to "
            f".claude/settings.json under enabledPlugins: {lines}.")


def missing(lines):
    return ("method guard: this project imports the my method, but its plugins "
            "are off. Add to .claude/settings.json under enabledPlugins: "
            f"{lines}. Or run /kit:setup my.")


class GuardTest(unittest.TestCase):
    def make_world(self, user_plugins=None, project_md="", local_md=None,
                   project_plugins=None, local_plugins=None, approved=None,
                   warning_shown=None, claude_json=None):
        """Build a temporary HOME and project; return (home, project).

        A plugins argument that is a dict becomes {"enabledPlugins": dict};
        a string is written as the file's whole content. None writes no file.
        approved and warning_shown set the project's flags in .claude.json;
        claude_json, a string, replaces that file's whole content.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        home = Path(tmp.name) / "home"
        project = Path(tmp.name) / "project"
        home.mkdir()
        project.mkdir()
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
        if claude_json is not None:
            write(home / ".claude.json", claude_json)
        else:
            entry = {}
            if approved is not None:
                entry["hasClaudeMdExternalIncludesApproved"] = approved
            if warning_shown is not None:
                entry["hasClaudeMdExternalIncludesWarningShown"] = warning_shown
            projects = {str(project): entry} if entry else {}
            write(home / ".claude.json", {"projects": projects})
        return home, project

    def run_guard(self, home, project, project_dir=True, cwd=None):
        env = {k: v for k, v in os.environ.items()
               if k != "CLAUDE_PROJECT_DIR" and not k.startswith("GIT_")}
        env["HOME"] = str(home)
        if project_dir is True:
            env["CLAUDE_PROJECT_DIR"] = str(project)
        elif project_dir:
            env["CLAUDE_PROJECT_DIR"] = project_dir
        return subprocess.run([sys.executable, str(SCRIPT)], env=env,
                              cwd=cwd or project, capture_output=True,
                              text=True, timeout=10)

    def text(self, result):
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        message = out["systemMessage"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertEqual(out["hookSpecificOutput"]["additionalContext"], message)
        return message

    def test_my_with_plugins_off_names_each_missing_line(self):
        home, project = self.make_world(user_plugins=OFF, project_md=MY, approved=True)
        self.assertEqual(self.text(self.run_guard(home, project)), missing(
            '"my@claude-setup": true, "superpowers@synced": true'))

    def test_my_with_only_superpowers_missing(self):
        home, project = self.make_world(
            user_plugins=OFF, project_md=MY, approved=True,
            project_plugins={"my@claude-setup": True})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         missing('"superpowers@synced": true'))

    def test_my_not_approved(self):
        home, project = self.make_world(project_md=MY, project_plugins=ON, approved=False)
        self.assertEqual(self.text(self.run_guard(home, project)), not_approved("my"))

    def test_tutor_missing_approval_flag(self):
        home, project = self.make_world(user_plugins=OFF, project_md=TUTOR)
        self.assertEqual(self.text(self.run_guard(home, project)), not_approved("tutor"))

    def test_declined_import_gives_reset_advice(self):
        home, project = self.make_world(project_md=MY, project_plugins=ON,
                                        approved=False, warning_shown=True)
        self.assertEqual(self.text(self.run_guard(home, project)),
                         declined("my", str(project)))

    def test_neutral_with_stray_plugins(self):
        home, project = self.make_world(project_plugins=ON)
        self.assertEqual(self.text(self.run_guard(home, project)),
                         stray(["my@claude-setup", "superpowers@synced"]))

    def test_neutral_with_superpowers_by_default(self):
        home, project = self.make_world(user_plugins={"my@claude-setup": False})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         stray(["superpowers@synced"]))

    def test_tutor_with_my_on_is_stray(self):
        home, project = self.make_world(
            user_plugins=OFF, project_md=TUTOR, approved=True,
            project_plugins={"my@claude-setup": True})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         stray(["my@claude-setup"]))

    def test_two_imports(self):
        home, project = self.make_world(project_md=MY, local_md=TUTOR,
                                        project_plugins=ON, approved=True)
        self.assertEqual(self.text(self.run_guard(home, project)),
                         "method guard: this project imports more than one "
                         "method file: my, tutor. Keep one.")

    def test_neutral_and_off_prints_nothing(self):
        home, project = self.make_world(user_plugins=OFF)
        result = self.run_guard(home, project)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_my_set_up_prints_nothing(self):
        home, project = self.make_world(project_md=MY, project_plugins=ON, approved=True)
        result = self.run_guard(home, project)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_unreadable_user_settings(self):
        home, project = self.make_world(user_plugins="{", project_md=MY,
                                        project_plugins=ON, approved=True)
        self.assertEqual(self.text(self.run_guard(home, project)),
                         f"method guard could not read {home}/.claude/settings.json")

    def test_unreadable_claude_json_skips_approval(self):
        home, project = self.make_world(project_md=MY, project_plugins=ON,
                                        claude_json="{")
        self.assertEqual(self.text(self.run_guard(home, project)),
                         f"method guard could not read {home}/.claude.json")

    def test_local_settings_override_project(self):
        home, project = self.make_world(
            project_md=MY, project_plugins=ON, approved=True,
            local_plugins={"superpowers@synced": False})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         missing('"superpowers@synced": true'))

    def test_trailing_slash_in_project_dir_still_finds_approval(self):
        home, project = self.make_world(project_md=MY, project_plugins=ON, approved=True)
        result = self.run_guard(home, project, project_dir=f"{project}/")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_import_line_with_crlf_counts(self):
        home, project = self.make_world(project_md="@~/.claude/methods/my.md  \r\n",
                                        project_plugins=ON, approved=True)
        result = self.run_guard(home, project)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_string_true_is_not_on(self):
        home, project = self.make_world(
            project_md=MY, approved=True,
            project_plugins={"my@claude-setup": "true", "superpowers@synced": True})
        self.assertEqual(self.text(self.run_guard(home, project)),
                         missing('"my@claude-setup": true'))

    def test_settings_not_an_object_is_unreadable(self):
        for content in ["[]", '{"enabledPlugins": []}']:
            with self.subTest(content=content):
                home, project = self.make_world(project_md=MY, approved=True,
                                                project_plugins=content)
                lines = self.text(self.run_guard(home, project)).split("\n")
                self.assertEqual(lines[0], "method guard could not read "
                                 f"{project}/.claude/settings.json")

    def test_root_falls_back_to_git_toplevel(self):
        home, project = self.make_world(project_md=MY, project_plugins=ON, approved=True)
        subprocess.run(["git", "init", "-q", str(project)], check=True,
                       env={**os.environ, "HOME": str(home)})
        sub = project / "src" / "deep"
        sub.mkdir(parents=True)
        result = self.run_guard(home, project, project_dir=False, cwd=sub)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_output_is_capped(self):
        names = [f"{i:02d}-" + "a" * 57 for i in range(40)]
        md = "".join(f"@~/.claude/methods/{n}.md\n" for n in names)
        home, project = self.make_world(user_plugins=OFF, project_md=md)
        message = self.text(self.run_guard(home, project))
        self.assertTrue(message.startswith("method guard: this project imports more"))
        self.assertLessEqual(len(message), 2000)

    def test_exit_code_is_zero_in_every_case(self):
        worlds = [
            {}, {"user_plugins": OFF}, {"project_md": MY},
            {"project_md": MY, "project_plugins": ON, "approved": True},
            {"user_plugins": "{"}, {"claude_json": "{"}, {"claude_json": "[]"},
            {"project_plugins": "[]"}, {"local_plugins": "not json"},
            {"project_md": MY + TUTOR, "approved": False, "warning_shown": True},
        ]
        for world in worlds:
            with self.subTest(world=world):
                home, project = self.make_world(**world)
                self.assertEqual(self.run_guard(home, project).returncode, 0)

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
