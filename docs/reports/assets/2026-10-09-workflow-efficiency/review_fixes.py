"""List the branch fix commits that change application code and name a review.

The output holds candidates only. Each was then read by hand and given one class in
review_fix_classes.json:
  S  the spec missed or got wrong a decision
  L  layout broke at a width, a language or a text length nobody checked
  T  the test checked the wrong thing
  C  the code broke a rule the spec already stated
  P  browser or framework behaviour
  D  comments only
  X  not a review fix (planned work, a critique, or a branch made after the audit)

Usage: python3 review_fixes.py ~/projects/zitamu/real-estate-webapp review_fixes.json
"""
import json
import re
import subprocess
import sys

REPO, OUT = sys.argv[1], sys.argv[2]
LEFT_OUT = {"main", "client-review", "feat/app-frame", "fix/role-pages-data", "fix/lapsed-demand-pages"}


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, check=True).stdout


branches = [b for b in git("branch", "--format=%(refname:short)").split()
            if b not in LEFT_OUT and not b.startswith("backup/")]
seen = {}
for b in branches:
    for h in git("rev-list", "--no-merges", b, "--not", "main").split():
        seen.setdefault(h, b)

rows = []
for h, b in seen.items():
    subject = git("show", "-s", "--format=%s", h).strip()
    if not re.match(r"fix(\(|:)", subject):
        continue
    files = git("show", "--format=", "--name-only", h).split()
    app = [f for f in files if not f.startswith("docs/") and not f.endswith(".md")
           and not f.endswith(("package-lock.json", "composer.lock"))]
    body = git("show", "-s", "--format=%B", h)
    if app and re.search(r"review", body, re.I):
        rows.append({"h": h[:7], "b": b, "s": subject, "body": body, "files": app})

json.dump(rows, open(OUT, "w"), indent=1)
print(len(rows), "candidates")
