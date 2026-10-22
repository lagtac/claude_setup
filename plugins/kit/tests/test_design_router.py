"""Tests for the design router: its gate, its tickets and its table.

Run from plugins/kit: python3 -m unittest discover tests

The gate tests run hooks/design-router-gate.py as a subprocess, feeding it
the JSON that Claude Code sends to a PreToolUse hook. Each test builds a
temporary plugin list, plugin home and tickets folder, and points the gate
at them with DESIGN_ROUTER_PLUGINS, DESIGN_ROUTER_PLUGIN_HOME and
DESIGN_ROUTER_TICKETS, so the user's own files cannot change a result.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
GATE = KIT / "hooks" / "design-router-gate.py"
HOOKS = KIT / "hooks" / "hooks.json"
TICKET = KIT / "bin" / "design-router-ticket.py"
LIST = KIT / "skills" / "design-router" / "plugins.json"
SKILL = KIT / "skills" / "design-router" / "SKILL.md"
ROW = re.compile(r"^\| `(?P<id>[a-z0-9-]+)` \| (?P<job>.+?) \| (?P<skills>.+?) \| "
                 r"(?P<state>decided|undecided|open) \|$")
IDS = ["visual-direction", "critique", "accessibility", "copy", "research-plan", "system-audit",
       "tokens", "interaction", "polish", "handoff", "research-synthesis", "journey-map",
       "strategy", "draw", "diagram", "chart"]

FIXTURE_LIST = {"design": "routed", "design-skills": "routed",
                "frontend-design": "routed", "design-superpowers": "excluded",
                "superpowers": "not-design"}
INSTALLED = {"version": 2, "plugins": {"newplug@market": [], "design@synced": [],
                                       "kit@claude-setup": []}}


def write(path, content):
    """Write a dict as JSON, or a string as it is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if isinstance(content, str) else json.dumps(content))


def table_rows():
    rows = []
    for line in SKILL.read_text().splitlines():
        match = ROW.match(line)
        if match:
            rows.append({"id": match["id"], "skills_cell": match["skills"],
                         "skills": re.findall(r"`([^`]+)`", match["skills"]),
                         "state": match["state"]})
    return rows


def routed_plugins():
    return {k for k, v in json.loads(LIST.read_text()).items() if v == "routed"}


def write_ticket(path, age=0):
    """Write an empty ticket whose time is `age` seconds ago."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    then = time.time() - age
    os.utime(path, (then, then))


def decision(out):
    if not out:
        return None
    return json.loads(out).get("hookSpecificOutput", {}).get("permissionDecision")


def reason(out):
    return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


class GateTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.list = self.root / "plugins.json"
        self.home = self.root / "home"
        self.empty = self.root / "empty"
        self.tickets = self.root / "tickets"
        write(self.list, FIXTURE_LIST)
        write(self.home / "installed_plugins.json", INSTALLED)
        write(self.home / "synced" / "acct" / "p1" / ".claude-plugin" / "plugin.json",
              {"name": "syncplug"})
        self.empty.mkdir()

    def run_gate(self, skill, session="s1", plugins=None, home=None, raw=None):
        if raw is None:
            raw = json.dumps({"session_id": session, "tool_name": "Skill",
                              "tool_input": {"skill": skill}})
        env = dict(os.environ,
                   DESIGN_ROUTER_PLUGINS=str(plugins or self.list),
                   DESIGN_ROUTER_PLUGIN_HOME=str(home or self.home),
                   DESIGN_ROUTER_TICKETS=str(self.tickets))
        return subprocess.run([sys.executable, str(GATE)], input=raw, env=env,
                              capture_output=True, text=True, timeout=10)

    def run_ticket(self, skill, session):
        env = dict(os.environ, CLAUDE_CODE_SESSION_ID=session,
                   DESIGN_ROUTER_TICKETS=str(self.tickets))
        return subprocess.run([sys.executable, str(TICKET), skill], env=env,
                              capture_output=True, text=True, timeout=10)

    def test_routed_is_refused(self):
        r = self.run_gate("design-skills:design-critique")
        self.assertEqual(decision(r.stdout), "deny")
        self.assertIn("kit:design-router", reason(r.stdout))

    def test_excluded_is_refused(self):
        r = self.run_gate("design-superpowers:design")
        self.assertEqual(decision(r.stdout), "deny")
        self.assertIn("is excluded from the design router", reason(r.stdout))

    def test_unknown_plugin_is_refused(self):
        r = self.run_gate("newplug:thing")
        self.assertEqual(decision(r.stdout), "deny")
        self.assertIn("plugins.json", reason(r.stdout))
        self.assertIn("claude plugin update kit@claude-setup", reason(r.stdout))

    def test_unknown_synced_plugin_is_refused(self):
        self.assertEqual(decision(self.run_gate("syncplug:x").stdout), "deny")

    # A missing script also prints nothing, but exits 2: every "passes" test checks the exit code.
    def test_unknown_prefix_passes(self):
        r = self.run_gate("somefolder:thing")
        self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_not_design_passes(self):
        r = self.run_gate("superpowers:brainstorming")
        self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_no_prefix_passes(self):
        r = self.run_gate("dataviz")
        self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_kit_passes(self):
        # kit is installed in the fixture home and absent from the fixture list, so without
        # the kit rule it would be refused as unreviewed.
        r = self.run_gate("kit:design-router")
        self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_leading_slash_is_judged(self):
        self.assertEqual(decision(self.run_gate("/design-skills:ux-writing").stdout), "deny")

    def test_bad_input_passes(self):
        for raw in ("not json", "{}", '{"tool_input": 5}'):
            with self.subTest(raw=raw):
                r = self.run_gate(None, raw=raw)
                self.assertEqual((r.stdout, r.returncode), ("", 0))

    def test_missing_installed_list_passes(self):
        r = self.run_gate("newplug:thing", home=self.empty)
        self.assertEqual((r.stdout, r.returncode), ("", 0))
        self.assertEqual(decision(self.run_gate("design:ux-copy", home=self.empty).stdout),
                         "deny")

    def assert_fails_open(self, plugins):
        r = self.run_gate("design:ux-copy", plugins=plugins)
        out = json.loads(r.stdout)
        self.assertNotIn("hookSpecificOutput", out)
        self.assertIn(str(plugins), out["systemMessage"])
        self.assertEqual(r.returncode, 0)

    def test_missing_list_fails_open(self):
        self.assert_fails_open(self.root / "missing.json")

    def test_broken_list_fails_open(self):
        broken = self.root / "broken.json"
        write(broken, "{not json")
        self.assert_fails_open(broken)

    def test_never_allows(self):
        missing = self.root / "missing.json"
        cases = [dict(skill=s) for s in (
            "design-skills:design-critique", "design-superpowers:design", "newplug:thing",
            "syncplug:x", "somefolder:thing", "superpowers:brainstorming", "dataviz",
            "kit:design-router", "/design-skills:ux-writing")]
        cases += [dict(skill=None, raw=raw) for raw in ("not json", "{}", '{"tool_input": 5}')]
        cases += [dict(skill="newplug:thing", home=self.empty),
                  dict(skill="design:ux-copy", plugins=missing)]
        for case in cases:
            with self.subTest(**{k: str(v) for k, v in case.items()}):
                r = self.run_gate(**case)
                self.assertNotIn('"allow"', r.stdout)
                self.assertEqual(r.returncode, 0)
        for age in (0, 301):
            with self.subTest(ticket_age=age):
                write_ticket(self.tickets / "s1" / "design-skills:ux-writing", age=age)
                r = self.run_gate("design-skills:ux-writing")
                self.assertNotIn('"allow"', r.stdout)
                self.assertEqual(r.returncode, 0)

    def test_ticket_lets_one_call_through(self):
        ticket = self.tickets / "s1" / "design-skills:ux-writing"
        write_ticket(ticket)
        self.assertEqual(self.run_gate("design-skills:ux-writing").stdout, "")
        self.assertFalse(ticket.exists())
        self.assertEqual(decision(self.run_gate("design-skills:ux-writing").stdout), "deny")

    def test_ticket_is_per_session(self):
        write_ticket(self.tickets / "s2" / "design-skills:ux-writing")
        self.assertEqual(decision(self.run_gate("design-skills:ux-writing").stdout), "deny")

    def test_ticket_is_per_skill(self):
        write_ticket(self.tickets / "s1" / "design:ux-copy")
        self.assertEqual(decision(self.run_gate("design-skills:ux-writing").stdout), "deny")

    def test_stale_ticket_is_refused(self):
        ticket = self.tickets / "s1" / "design-skills:ux-writing"
        write_ticket(ticket, age=301)
        self.assertEqual(decision(self.run_gate("design-skills:ux-writing").stdout), "deny")
        self.assertFalse(ticket.exists())

    def test_ticket_script_writes(self):
        r = self.run_ticket("design-skills:ux-writing", session="abc")
        self.assertEqual(r.returncode, 0)
        self.assertTrue((self.tickets / "abc" / "design-skills:ux-writing").is_file())

    def test_ticket_script_needs_session(self):
        r = self.run_ticket("design-skills:ux-writing", session="")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(list(self.tickets.rglob("*")), [])

    def test_ticket_script_strips_leading_slash(self):
        r = self.run_ticket("/design-skills:ux-writing", session="abc")
        self.assertEqual(r.returncode, 0)
        self.assertTrue((self.tickets / "abc" / "design-skills:ux-writing").is_file())

    def test_default_tickets_folder_is_shared(self):
        # Real sessions set no DESIGN_ROUTER_TICKETS: the script and the gate must
        # both fall back to the same folder under HOME.
        env = {k: v for k, v in os.environ.items() if k != "DESIGN_ROUTER_TICKETS"}
        env["HOME"] = str(self.root / "user")
        subprocess.run([sys.executable, str(TICKET), "design-skills:ux-writing"],
                       env=dict(env, CLAUDE_CODE_SESSION_ID="s1"), check=True, timeout=10)
        raw = json.dumps({"session_id": "s1", "tool_name": "Skill",
                          "tool_input": {"skill": "design-skills:ux-writing"}})
        r = subprocess.run([sys.executable, str(GATE)], input=raw, capture_output=True,
                           text=True, timeout=10,
                           env=dict(env, DESIGN_ROUTER_PLUGINS=str(self.list),
                                    DESIGN_ROUTER_PLUGIN_HOME=str(self.home)))
        self.assertEqual(r.stdout, "")
        self.assertEqual(list((self.root / "user").rglob("design-skills:ux-writing")), [])

    def test_leading_slash_uses_ticket(self):
        ticket = self.tickets / "s1" / "design-skills:ux-writing"
        write_ticket(ticket)
        r = self.run_gate("/design-skills:ux-writing")
        self.assertEqual((r.stdout, r.returncode), ("", 0))
        self.assertFalse(ticket.exists())

    def test_ticket_path_cannot_escape(self):
        # Each case names a routed skill (it has a ":"), and `landing` is where an
        # unguarded join of tickets/<session>/<skill> would land. The folders exist,
        # so that such a join resolves.
        (self.tickets / "s1").mkdir(parents=True)
        gate_cases = (("..", "design:ux-copy", self.root / "design:ux-copy"),
                      ("s1/..", "design:ux-copy", self.tickets / "design:ux-copy"))
        for session, skill, landing in gate_cases:
            with self.subTest(gate=session):
                write_ticket(landing)  # a gate without the guard deletes it and lets it through
                self.assertEqual(decision(self.run_gate(skill, session=session).stdout), "deny")
                self.assertTrue(landing.exists())
                landing.unlink()
        # A script without the guard creates the folders and writes `landing`.
        script_cases = gate_cases + (("s1", "design:x/../../../escape", self.root / "escape"),)
        for session, skill, landing in script_cases:
            with self.subTest(script=session, skill=skill):
                self.assertEqual(self.run_ticket(skill, session=session).returncode, 1)
                self.assertFalse(landing.exists())


class ConfigTest(unittest.TestCase):
    def test_hooks_json_registers_gate(self):
        entries = json.loads(HOOKS.read_text())["hooks"]["PreToolUse"]
        self.assertTrue(any(e["matcher"] == "Skill" and
                            any("design-router-gate.py" in h["command"] for h in e["hooks"])
                            for e in entries))

    def test_list_states_are_valid(self):
        states = json.loads(LIST.read_text())
        self.assertTrue(set(states.values()) <= {"routed", "excluded", "not-design"})
        self.assertEqual({k for k, v in states.items() if v == "routed"},
                         {"design", "design-skills", "frontend-design"})
        self.assertEqual({k for k, v in states.items() if v == "excluded"},
                         {"design-superpowers", "product-management", "data"})
        for name in ("kit", "my", "superpowers", "hookify", "tutor", "sp"):
            self.assertEqual(states[name], "not-design")



class TableTest(unittest.TestCase):
    def test_table_ids_unique(self):
        ids = [row["id"] for row in table_rows()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, IDS)

    def test_table_skills_known(self):
        routed = routed_plugins()
        for row in table_rows():
            for skill in row["skills"]:
                self.assertTrue(skill.split(":")[0] in routed
                                or skill in ("artifact-diagramming", "dataviz"), skill)
            if not row["skills"]:
                self.assertIn("Design type", row["skills_cell"])

    def test_every_routed_plugin_used(self):
        used = {s.split(":")[0] for row in table_rows() for s in row["skills"]}
        self.assertTrue(routed_plugins() <= used)

    def test_refusal_after_ticket_goes_to_the_user(self):
        text = " ".join(SKILL.read_text().split())
        self.assertIn("If the gate still refuses the call after the ticket, do not invoke "
                      "`kit:design-router` again", text)

    def test_undecided_rows_have_two(self):
        for row in table_rows():
            want = {"undecided": 2, "decided": 1}.get(row["state"])
            if want:
                self.assertEqual(len(row["skills"]), want, row["id"])


if __name__ == "__main__":
    unittest.main()
