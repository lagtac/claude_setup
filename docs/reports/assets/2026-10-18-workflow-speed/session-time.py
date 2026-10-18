#!/usr/bin/env python3
"""Where the time goes in Claude Code sessions, from their transcripts.

Written for docs/reports/2026-10-18-workflow-speed-audit.md.

The script reads and never writes. It reads every top-level *.jsonl in the
transcript folder of the current repository (~/.claude/projects/<path with
every "/" and "." replaced by "-">), or the folder given as the argument.

Usage:
    session-time.py [<transcript folder>]

1. Timeline. Each gap between two events of a session gets the label of the
   event that ends it, so the labels add up to the session's time:

    user wait        a prompt the user typed, or a local command they ran
                     (such as /context)
    ask-user         the answer to an AskUserQuestion
    session wait     a message from another Claude session (a hand-off)
    tool             the result of any other tool call
    background wait  a <task-notification>: the session sat idle until
                     background work (an e2e run, an agent) finished
    model            an assistant message: the model reading, thinking, writing
    other            any other event, such as a skill's text being loaded
    away             any gap over AWAY (2 hours), whatever ends it

   Sessions are grouped by stage, taken from the session title's first word
   (spec, plan, code, review, fix); any other title is "other".

2. Tool calls. For each call, the time from the call to its result. A call run
   in the background (Bash with run_in_background, or an Agent) ends when its
   <task-notification> is queued, when one is found; "matched" says how many
   were. Background calls overlap with other work, so this table does not add
   up to the timeline.

    e2e-suite   Bash that runs make e2e or e2e-worktree.sh (the full suite)
    e2e-one     Bash that runs playwright test (one file or test)
    unit        Bash: npm test, make test-web, vitest, npm run typecheck
    api-tests   Bash: make test-api, artisan test, api-worktree.sh, pint
    review      Agent whose type or description names a review
    agent       any other Agent
    other       any other tool

3. Full e2e runs per session, for the sessions that ran any.
"""

import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

AWAY = 2 * 3600
STAGES = ("spec", "plan", "code", "review", "fix")
CATEGORIES = [
    ("e2e-suite", re.compile(r"(^|&&|;|\|\||\()\s*(timeout \d+ )?(make e2e\b|\S*e2e-worktree\.sh)")),
    ("e2e-one", re.compile(r"\bplaywright test\b")),
    ("unit", re.compile(r"npm (run )?test|make test-web|vitest|npm run typecheck")),
    ("api-tests", re.compile(r"make test-api|artisan test|api-worktree\.sh|pint")),
]
NOTIFY = re.compile(r"<tool-use-id>(toolu_\w+)</tool-use-id>")
TIMELINE = ["user wait", "ask-user", "session wait", "tool", "background wait", "model", "other"]
TOOLS = ["e2e-suite", "e2e-one", "unit", "api-tests", "review", "agent", "other"]


def stamp(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def category(name, tool_input):
    if name == "Bash":
        for label, pattern in CATEGORIES:
            if pattern.search(tool_input.get("command", "")):
                return label
        return "other"
    if name in ("Agent", "Task"):
        words = " ".join(str(tool_input.get(k, "")) for k in ("description", "subagent_type"))
        return "review" if re.search(r"review", words, re.I) else "agent"
    return "other"


def text_of(content):
    if isinstance(content, str):
        return content
    return " ".join(part.get("text", "") for part in content if part.get("type") == "text")


def read_session(path):
    """(title, timeline events [(time, label)], calls, results, notified)."""
    title, events, calls, results, notified = "", [], {}, {}, {}
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        kind = entry.get("type")
        if kind == "custom-title":
            title = entry.get("customTitle", "")
        if kind == "queue-operation" and entry.get("timestamp"):
            for tool_id in NOTIFY.findall(str(entry.get("content", ""))):
                notified.setdefault(tool_id, stamp(entry["timestamp"]))
        if kind not in ("user", "assistant") or not entry.get("timestamp") or entry.get("isSidechain"):
            continue
        t = stamp(entry["timestamp"])
        content = entry["message"].get("content") or ""
        parts = content if isinstance(content, list) else []
        for part in parts:
            if part.get("type") == "tool_use":
                calls[part["id"]] = (t, part.get("name"), part.get("input") or {})
            elif part.get("type") == "tool_result":
                results.setdefault(part.get("tool_use_id"), t)
        if kind == "assistant":
            label = "model"
        elif any(p.get("type") == "tool_result" for p in parts):
            ids = [p.get("tool_use_id") for p in parts if p.get("type") == "tool_result"]
            label = "ask-user" if any(calls.get(i, (0, ""))[1] == "AskUserQuestion" for i in ids) else "tool"
        else:
            text = text_of(content).lstrip()
            if text.startswith("<task-notification"):
                label = "background wait"
            elif text.startswith("Another Claude session sent"):
                label = "session wait"
            elif text.startswith(("<local-command", "<command-stdout", "## Context Usage")):
                label = "user wait"
            elif entry.get("isMeta") or not text or text.startswith(("<system-reminder", "Base directory for this skill")):
                label = "other"
            else:
                label = "user wait"
        events.append((t, label))
    return title, sorted(events), calls, results, notified


def measure(path):
    title, events, calls, results, notified = read_session(path)
    if len(events) < 2:
        return None
    timeline = defaultdict(float)
    for (before, _), (t, label) in zip(events, events[1:]):
        timeline["away" if t - before > AWAY else label] += t - before
    timeline["session"] = sum(v for k, v in timeline.items() if k != "away")
    tools = defaultdict(lambda: [0.0, 0, 0, 0])  # seconds, calls, background calls, matched
    for tool_id, (start, name, tool_input) in calls.items():
        background = bool(tool_input.get("run_in_background")) or name in ("Agent", "Task")
        end = notified.get(tool_id) if background else None
        row = tools[category(name, tool_input)]
        row[2] += background
        row[3] += background and end is not None
        end = end or results.get(tool_id)
        if end is not None and end >= start:
            row[0] += min(end - start, AWAY)
            row[1] += 1
    stage = title.split("-")[0].split(" ")[0].lower()
    return dict(stage=stage if stage in STAGES else "other", timeline=timeline, tools=tools,
                suites=tools["e2e-suite"][1])


def main(argv):
    if len(argv) > 1:
        print(__doc__, file=sys.stderr)
        return 2
    folder = Path(argv[0]) if argv else Path.home() / ".claude/projects" / re.sub(r"[/.]", "-", os.getcwd())
    sessions = [m for m in (measure(p) for p in sorted(folder.glob("*.jsonl"))) if m]
    if not sessions:
        print(f"no transcripts in {folder}", file=sys.stderr)
        return 1
    print(f"{len(sessions)} sessions in {folder}\n")

    print("Timeline, hours (share of the stage's session time):\n")
    print("| stage | sessions | session h | median session min | " + " | ".join(TIMELINE) + " |")
    print("|" + "---|" * (len(TIMELINE) + 4))
    for stage in STAGES + ("other", "all"):
        group = [s for s in sessions if stage == "all" or s["stage"] == stage]
        if not group:
            continue
        total = sum(s["timeline"]["session"] for s in group)
        cells = [f"{sum(s['timeline'][k] for s in group) / 3600:.1f} ({100 * sum(s['timeline'][k] for s in group) / max(total, 1):.0f}%)"
                 for k in TIMELINE]
        med = statistics.median(s["timeline"]["session"] / 60 for s in group)
        print(f"| {stage} | {len(group)} | {total / 3600:.1f} | {med:.0f} | " + " | ".join(cells) + " |")

    print("\nTool calls (background calls overlap with other work):\n")
    print("| category | calls | hours | minutes per call | background calls | matched to a notification |")
    print("|---|---|---|---|---|---|")
    for k in TOOLS:
        secs = sum(s["tools"][k][0] for s in sessions)
        n = sum(s["tools"][k][1] for s in sessions)
        bg = sum(s["tools"][k][2] for s in sessions)
        hit = sum(s["tools"][k][3] for s in sessions)
        print(f"| {k} | {n} | {secs / 3600:.1f} | {secs / 60 / max(n, 1):.1f} | {bg} | {hit} |")

    runs = Counter(min(s["suites"], 5) for s in sessions if s["suites"])
    with_runs = sum(runs.values())
    print(f"\nFull e2e runs per session, in the {with_runs} sessions that ran any: "
          + ", ".join(f"{'5+' if k == 5 else k}: {runs[k]}" for k in sorted(runs))
          + f". Sessions with 2 or more: {with_runs - runs[1]} ({100 * (with_runs - runs[1]) // max(with_runs, 1)}%).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
