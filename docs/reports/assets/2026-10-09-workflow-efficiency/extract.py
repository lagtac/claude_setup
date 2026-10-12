"""Extract branch lead times and spec stage times from zitamu's git history.

Follows the Method section of real-estate-webapp/docs/reports/2026-10-12-commit-size-audit.md.
Usage: python3 extract.py ~/projects/zitamu/real-estate-webapp data.json
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = sys.argv[1]
OUT = sys.argv[2]
LEFT_OUT = {"main", "client-review", "feat/app-frame", "fix/role-pages-data", "fix/lapsed-demand-pages"}
HAND = {"feat/design-tokens": "a6e64ea", "feat/landing-type-rhythm": "cda1405"}


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, check=True).stdout


def patch_id(rev_or_diff, is_diff=False):
    diff = rev_or_diff if is_diff else git("show", "--format=", rev_or_diff)
    out = subprocess.run(["git", "-C", REPO, "patch-id", "--stable"], input=diff,
                         capture_output=True, text=True).stdout.split()
    return out[0] if out else None


branches = [b for b in git("branch", "--format=%(refname:short)").split()
            if b not in LEFT_OUT and not b.startswith("backup/")]

# main commits: hash, author ts, commit ts, files
main_commits = []
for block in git("log", "--no-merges", "--name-only", "--format=@@%H %at %ct", "main").split("@@")[1:]:
    lines = block.strip().splitlines()
    h, at, ct = lines[0].split()
    main_commits.append({"h": h, "at": int(at), "ct": int(ct), "files": set(l for l in lines[1:] if l)})
by_short = {c["h"][:7]: c for c in main_commits}
main_pid = {}

branch_rows = []
for b in branches:
    revs = git("rev-list", "--no-merges", "--reverse", b, "--not", "main").split()
    if not revs:
        continue
    first_at = int(git("show", "-s", "--format=%at", revs[0]).strip())
    base = git("merge-base", "main", b).strip()
    match = None
    if b in HAND:
        match = by_short[HAND[b]]
    else:
        pid = patch_id(git("diff", base, b), is_diff=True)
        cands = [c for c in main_commits if c["at"] >= first_at - 3600]
        for c in cands:
            if c["h"] not in main_pid:
                main_pid[c["h"]] = patch_id(c["h"])
            if pid and main_pid[c["h"]] == pid:
                match = c
                break
        if match is None:
            bfiles = set(git("diff", "--name-only", base, b).split())
            after = [c for c in main_commits if c["ct"] > first_at and not c["files"] <= {f for f in c["files"] if f.startswith("docs/")}]
            match = max(after, key=lambda c: len(c["files"] & bfiles), default=None)
    branch_rows.append({"branch": b, "commits": len(revs), "first_at": first_at,
                        "squash": match["h"][:7], "squash_ct": match["ct"],
                        "hours": (match["ct"] - first_at) / 3600})

# specs
spec_rows = []
for spec in sorted(Path(REPO, "docs/plans").glob("*-spec.md")):
    rel = spec.relative_to(REPO).as_posix()
    head = spec.read_text().splitlines()[:5]
    if not any(re.match(r"\*\*Status:\*\* done", l) for l in head):
        continue
    spec_at = int(git("log", "--follow", "--format=%at", "--", rel).split()[-1])
    done = git("log", "--follow", "-G", r"\*\*Status:\*\* done", "--format=%at", "--", rel).split()
    plan = rel.replace("-spec.md", ".md")
    plan_log = git("log", "--follow", "--format=%at", "--", plan).split() if Path(REPO, plan).exists() else []
    spec_rows.append({"slug": spec.stem.removesuffix("-spec"), "spec_at": spec_at,
                      "plan_at": int(plan_log[-1]) if plan_log else None,
                      "done_at": int(done[-1])})

json.dump({"branches": branch_rows, "specs": spec_rows}, open(OUT, "w"), indent=1)
print(len(branch_rows), "branches;", len(spec_rows), "done specs")
