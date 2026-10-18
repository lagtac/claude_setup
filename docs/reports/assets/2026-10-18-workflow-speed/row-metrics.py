#!/usr/bin/env python3
"""Measure the work behind each shipped (✅) row of ROADMAP.md.

Written for docs/reports/2026-10-18-workflow-speed-audit.md.

The script reads and never writes. Run it from inside the repository.

A row's commits are the commits on main that:
  - name the row in their message ("row 133", "rows 156 and 161"), or
  - touch a docs/plans/ file the row links to, or
  - are cited by hash in the row, or in the status line of a linked file,
    when no commit found by the two rules above changes code (a cited hash
    is often only background).
A kept local branch adds its commits that touch the row's files (code time,
fix rounds). The branch's last commit must come at most WINDOW (7 days) before the
row's code reached main. Among those, a branch named in a linked file (as
`name` or main..name) wins, then the one whose changed files overlap most with
the row's code; an unnamed branch must have changed at least half of them.

Usage:
    row-metrics.py           per-unit table, then medians by size
    row-metrics.py --tsv     the per-unit table only, tab-separated

Size is inferred from the linked files: spec and plan = L, spec only = M,
plan only = P (the early, plan-only rows), neither = S.

A file linked by SHARED (10) or more shipped rows, such as an action plan, is
ignored: its commits belong to no single row.

Rows that share a branch or a linked spec or plan are one unit of work (a
batch), and the tables report units, not rows. A code commit shared by rows in
different units still counts in full for each. The "row" column
lists the unit's rows. "fixes" counts branch commits that change code and name
a review, a fix round or a finding.

Times use author dates, which survive a rebase or a fold. "lead" runs from the
first commit of the work (a linked file, the branch or the code, a linked file's
commits counted only from the first docs commit that names the row) to the last code commit on main. "active" adds up the gaps between successive commits
(main and branch), each gap capped at one hour, as a rough measure of working
time. "code_share" is the part of it whose gap ends in a commit that changes
code; the rest ends in a docs-only commit. "plans_md" counts lines added to the
row's linked files and to the reviews named after its spec or plan; "other_md"
counts lines added to Markdown outside docs/plans/ (ROADMAP, CHANGELOG, docs).
"""

import os
import re
import statistics
import subprocess
import sys
from collections import defaultdict

LOCK = re.compile(r"(^|/)(package-lock\.json|composer\.lock|yarn\.lock|pnpm-lock\.yaml)$")
TEST = re.compile(r"(^|/)(tests?|e2e)/|\.spec\.|\.test\.|Test\.php$")
REVIEW = re.compile(r"-review(-\d+)?\.md$")
ROW_REF = re.compile(r"\brows? (\d+[a-z]?(?:(?:,? and |, | or )\d+[a-z]?)*)", re.I)
HASH = re.compile(r"`([0-9a-f]{7,40})`")
LINK = re.compile(r"\((docs/plans/[^)#\s]+\.md)")
CAP = 3600
WINDOW = 7 * 86400
SHARED = 10


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def shipped_rows(text):
    """(number, title, links cell) for every ✅ table row."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"\d+[a-z]?", cells[0]) and cells[1] == "✅":
            title = re.search(r"\*\*(.+?)\*\*", cells[2])
            rows.append((cells[0], title.group(1) if title else cells[2][:40], " ".join(cells[2:])))
    return rows


def read_commits(rev):
    """hash -> dict(time, author, message, files[(added, deleted, path)])."""
    out = git("log", "--no-merges", "--format=%x1e%H%x1f%at%x1f%an%x1f%B%x1f", "--numstat", rev)
    commits = {}
    for chunk in out.split("\x1e")[1:]:
        sha, at, author, message, stat = chunk.split("\x1f")
        files = []
        for line in stat.strip().splitlines():
            a, d, path = line.split("\t", 2)
            if "=>" in path:
                path = re.sub(r"\{[^}]*=> ([^}]*)\}", r"\1", path).split(" => ")[-1]
            files.append((0 if a == "-" else int(a), 0 if d == "-" else int(d), path))
        commits[sha] = dict(time=int(at), author=author, message=message, files=files)
    return commits


def mentioned_rows(message):
    rows = set()
    for match in ROW_REF.finditer(message):
        rows.update(n.lower() for n in re.findall(r"\d+[a-z]?", match.group(1)))
    return rows


def is_code(commit):
    return any(not path.endswith(".md") for _, _, path in commit["files"])


def active_seconds(times):
    times = sorted(times)
    return sum(min(b - a, CAP) for a, b in zip(times, times[1:]))


def hours(seconds):
    return None if seconds is None else round(seconds / 3600, 1)


def resolve(short, known):
    hits = [sha for sha in known if sha.startswith(short)]
    return hits[0] if len(hits) == 1 else None


def measure(numbers, title, cell, main, by_path, by_row, branches, me, shared, plan_files):
    links = sorted(set(LINK.findall(cell)) - shared)
    named_in = {sha for n in numbers for sha in by_row.get(n, ())}
    texts = {}
    for path in links:
        try:
            texts[path] = open(path, encoding="utf-8").read()
        except OSError:
            texts[path] = ""
    specs = [p for p in links if p.endswith("-spec.md")]
    plans = [p for p in links if not p.endswith("-spec.md") and not REVIEW.search(p)]
    size = "L" if specs and plans else "M" if specs else "P" if plans else "S"

    shas = set(named_in)
    for path in links:
        shas.update(by_path.get(path, ()))
    cited = set(HASH.findall(cell))
    for text in texts.values():
        status = next((l for l in text.splitlines() if l.startswith("**Status")), "")
        cited.update(HASH.findall(status))
    if not any(is_code(main[s]) for s in shas):
        for short in cited:
            sha = resolve(short, main)
            if sha:
                shas.add(sha)
    commits = [main[s] for s in shas]
    code = [c for c in commits if is_code(c)]
    docs = [c for c in commits if not is_code(c)]

    slugs = {re.sub(r"^\d{4}-\d\d-\d\d-|(-spec)?\.md$", "", p.split("/")[-1]) for p in specs + plans}
    reviews = {p for p in plan_files if REVIEW.search(p) and any(slug in p for slug in slugs)}
    reviews |= {p for p in links if REVIEW.search(p)}
    own_docs = set(links) | reviews
    src = tests = lock = 0
    code_files, doc_plans, doc_other = set(), 0, 0
    for c in commits:
        for a, d, path in c["files"]:
            if path.endswith(".md"):
                if path in own_docs:
                    doc_plans += a
                elif not path.startswith("docs/plans/"):
                    doc_other += a
            else:
                code_files.add(path)
                if LOCK.search(path):
                    lock += a + d
                elif TEST.search(path):
                    tests += a + d
                else:
                    src += a + d

    merge_t = max((c["time"] for c in code), default=None)
    named = {b for b in branches if any(
        re.search(rf"`{re.escape(b)}`|\.\.{re.escape(b)}(?![\w/-])", t) for t in texts.values())}
    branch, best = None, (0, 0)
    for name, info in branches.items():
        overlap = len(info["changed"] & code_files)
        if not overlap or not merge_t:
            continue
        if not 0 <= merge_t - info["tip"] <= WINDOW:
            continue
        if name not in named and overlap < 0.5 * len(code_files):
            continue
        score = (overlap / len(code_files) + (1 if name in named else 0), -abs(merge_t - info["tip"]))
        if score > best:
            branch, best = name, score
    bcommits = []
    if branch:
        own = code_files | set(links)
        bcommits = [c for sha, c in read_commits(f"{branches[branch]['base']}..{branch}").items()
                    if sha not in main and any(p in own for _, _, p in c["files"])]
    fixes = sum(1 for c in bcommits if is_code(c) and re.search(
        r"review|fix round|finding", c["message"].split("\n")[0], re.I))

    times = [c["time"] for c in commits] + [c["time"] for c in bcommits]
    work = sorted((c["time"], is_code(c)) for c in commits + bcommits)
    gaps = [(min(t - prev, CAP), kind) for (prev, _), (t, kind) in zip(work, work[1:])]
    active_code = sum(g for g, kind in gaps if kind)
    starts = [main[s]["time"] for p in links for s in by_path.get(p, ())]
    named_at = [main[s]["time"] for s in named_in if not is_code(main[s])]
    if named_at:
        starts = [t for t in starts if t >= min(named_at)]
    starts += [c["time"] for c in bcommits] + [c["time"] for c in code]
    spec_t = min((main[s]["time"] for p in specs for s in by_path.get(p, ())), default=None)
    btimes = sorted(c["time"] for c in bcommits)
    build = btimes[-1] - btimes[0] if len(btimes) > 1 else None
    to_code = (btimes[0] - spec_t) if btimes and spec_t else None
    wait = (merge_t - btimes[-1]) if btimes and merge_t else None
    authors = {c["author"] for c in code}
    return dict(
        row=",".join(numbers), title=title[:38], size=size, links={p for p in specs + plans},
        who="own" if not code else ("own" if authors <= {me} else "other" if me not in authors else "mixed"),
        commits=len(commits), docs=len(docs), code=len(code), files=len(code_files),
        src=src, tests=tests, lock=lock, plans_md=doc_plans, other_md=doc_other,
        reviews=len(reviews), branch=branch or "-", bcommits=len(bcommits), fixes=fixes,
        lead=hours(merge_t - min(starts) if merge_t and starts else None), active=hours(active_seconds(times)),
        docs_per_code=round(doc_plans / (src + tests), 2) if src + tests else None,
        shas=shas, code_shas={s for s in shas if is_code(main[s])},
        code_share=round(active_code / sum(g for g, _ in gaps), 2) if gaps and sum(g for g, _ in gaps) else None,
        spec_to_code=hours(to_code), build=hours(build), wait_merge=hours(wait),
    )


COLUMNS = ["row", "size", "who", "commits", "docs", "code", "files", "src", "tests", "lock",
           "plans_md", "other_md", "reviews", "bcommits", "fixes", "lead", "active",
           "docs_per_code", "code_share", "spec_to_code", "build", "wait_merge", "branch", "title"]


def median(values):
    values = [v for v in values if v is not None]
    return round(statistics.median(values), 1) if values else "-"


def main(argv):
    if argv not in ([], ["--tsv"]):
        print(__doc__, file=sys.stderr)
        return 2
    os.chdir(git("rev-parse", "--show-toplevel").strip())
    me = git("config", "user.name").strip()
    main_commits = read_commits("HEAD")
    by_path, by_row = defaultdict(set), defaultdict(set)
    for sha, c in main_commits.items():
        for _, _, path in c["files"]:
            if path.startswith("docs/plans/"):
                by_path[path].add(sha)
        for n in mentioned_rows(c["message"]):
            by_row[n].add(sha)
    branches = {}
    for name in git("branch", "--format=%(refname:short)").split():
        if name in ("main", "master"):
            continue
        base = git("merge-base", "HEAD", name).strip()
        changed = {p for p in git("diff", "--name-only", base, name).split() if not p.endswith(".md")}
        branches[name] = dict(base=base, changed=changed, tip=int(git("log", "-1", "--format=%at", name)))
    shipped = shipped_rows(open("ROADMAP.md", encoding="utf-8").read())
    uses = defaultdict(int)
    for _, _, cell in shipped:
        for path in set(LINK.findall(cell)):
            uses[path] += 1
    shared = {path for path, n in uses.items() if n >= SHARED}
    plan_files = [p for p in by_path if os.path.exists(p)]
    args = (main_commits, by_path, by_row, branches, me, shared, plan_files)
    single = [measure([n], t, cell, *args) for n, t, cell in shipped]

    # One unit of work per group of rows that share a branch, or a spec or plan.
    parent = list(range(len(single)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(single):
        for j in range(i):
            b = single[j]
            if a["links"] & b["links"] or (a["branch"] != "-" and a["branch"] == b["branch"]):
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in range(len(single)):
        groups[find(i)].append(shipped[i])
    rows = [measure([n for n, _, _ in g], g[0][1], " ".join(c for _, _, c in g), *args)
            for g in groups.values()]

    if argv == ["--tsv"]:
        print("\t".join(COLUMNS))
        for r in rows:
            print("\t".join("-" if r[k] is None else str(r[k]) for k in COLUMNS))
        return 0

    print("| " + " | ".join(COLUMNS) + " |")
    print("|" + "---|" * len(COLUMNS))
    for r in rows:
        print("| " + " | ".join("-" if r[k] is None else str(r[k]) for k in COLUMNS) + " |")

    own = [r for r in rows if r["who"] == "own" and r["code"]]
    print(f"\n{len(shipped)} shipped rows in {len(rows)} units of work; {len(own)} units with code"
          f" written in this workflow. No code commit found for rows:"
          f" {', '.join(r['row'] for r in rows if not r['code']) or 'none'}.\n")
    keys = ["commits", "docs", "code", "files", "src", "tests", "plans_md", "reviews",
            "bcommits", "fixes", "lead", "active", "docs_per_code", "code_share", "spec_to_code", "build", "wait_merge"]
    print("Medians by size (own units with code):\n")
    print("| size | n | " + " | ".join(keys) + " |")
    print("|" + "---|" * (len(keys) + 2))
    for size in ("S", "P", "M", "L", "all"):
        group = [r for r in own if size == "all" or r["size"] == size]
        if group:
            print(f"| {size} | {len(group)} | " + " | ".join(str(median(r[k] for r in group)) for k in keys) + " |")
    unique = {sha for r in own for sha in r["shas"]}
    code_lines = doc_lines = 0
    for sha in unique:
        for added, deleted, path in main_commits[sha]["files"]:
            if path.endswith(".md"):
                doc_lines += added if path.startswith("docs/plans/") else 0
            elif not LOCK.search(path):
                code_lines += added + deleted
    docs_only = sum(1 for sha in unique if not is_code(main_commits[sha]))
    print(f"\nAcross own rows, each commit counted once: {len(unique)} commits, {docs_only} of them"
          f" docs-only ({round(100 * docs_only / max(len(unique), 1))}%); {doc_lines} lines added in docs/plans/"
          f" for {code_lines} code lines changed ({round(doc_lines / max(code_lines, 1), 2)} per code line).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
