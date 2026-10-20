#!/usr/bin/env python3
"""Write a one-time ticket that lets this session call one design skill.

kit:design-router runs it just before it calls the skill it chose. The
design-router gate lets the next call to that skill in this session through,
when the ticket is at most 5 minutes old, and deletes the ticket.

Usage:
    design-router-ticket.py SKILL

The ticket is an empty file <tickets>/<session id>/<skill>, where <tickets>
is DESIGN_ROUTER_TICKETS, else ~/.cache/design-router/tickets, and the
session ID comes from CLAUDE_CODE_SESSION_ID. One leading "/" on SKILL is
dropped, as the gate drops it. An older ticket is replaced, so its time is
now. Prints nothing. Exits with 1 when the session ID is
empty, when the skill or the session ID is ".", ".." or holds "/", or when
the write fails.
"""

import argparse
import os
import sys
from pathlib import Path


def tickets_dir():
    env = os.environ.get("DESIGN_ROUTER_TICKETS")
    return Path(env) if env else Path.home() / ".cache" / "design-router" / "tickets"


def safe(part):
    return part not in ("", ".", "..") and "/" not in part


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("skill", help="the skill to start, for example design:ux-copy")
    args = parser.parse_args()
    skill = args.skill[1:] if args.skill.startswith("/") else args.skill

    session = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if not session:
        sys.exit("design-router-ticket: CLAUDE_CODE_SESSION_ID is empty, no ticket written")
    if not safe(session) or not safe(skill):
        sys.exit(f"design-router-ticket: bad session ID or skill name: {session!r}, "
                 f"{skill!r}; no ticket written")
    ticket = tickets_dir() / session / skill
    try:
        ticket.parent.mkdir(parents=True, exist_ok=True)
        ticket.unlink(missing_ok=True)
        ticket.touch()
    except OSError as error:
        sys.exit(f"design-router-ticket: cannot write {ticket}: {error}")


if __name__ == "__main__":
    main()
