#!/usr/bin/env python3
"""Count serious review findings per feature, before and after the code.

Written for docs/reports/2026-10-18-workflow-speed-audit.md (finding W4).

Usage: python3 -I review-findings.py    (run from the project root)

Reads docs/plans/*review*.md. A finding is a table row whose severity cell
reads "Critical / <confidence>", "Warning / ..." or "Suggestion / ...", the
format of my:soundness-review and my:spec-review. Code-review and
security-review files use other formats and are skipped. For each spec review
it groups every review file whose name contains the spec's slug: spec and plan
reviews count as "before the code", the others as "after".
"""

import glob
import os
import re
import statistics

FINDING = re.compile(r"^\|\s*(?:F?\d+[a-z]?\s*\|\s*)?(Critical|Warning|Suggestion)\s*/\s*(High|Medium|Low)")


def serious(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if (m := FINDING.match(line)) and m.group(1) != "Suggestion")


files = [os.path.basename(f) for f in glob.glob("docs/plans/*review*.md")]
rows, seen = [], set()
for spec in sorted(f for f in files if re.search(r"-spec-review(-\d+)?\.md$", f)):
    slug = re.sub(r"^\d{4}-\d\d-\d\d-|-spec-review(-\d+)?\.md$", "", spec)
    if slug in seen:
        continue
    seen.add(slug)
    group = [f for f in files if slug in f and not re.search(r"(code|security)-review", f)]
    before = [f for f in group if re.search(r"-(spec|plan)-review", f)]
    after = [f for f in group if f not in before]
    if after:
        rows.append((slug, sum(serious("docs/plans/" + f) for f in before),
                     sum(serious("docs/plans/" + f) for f in after)))
for slug, b, a in rows:
    print(f"{slug}\tbefore {b}\tafter {a}")
pre, post = [b for _, b, _ in rows], [a for _, _, a in rows]
print(f"\n{len(rows)} features; serious findings (Critical + Warning) per feature: median {statistics.median(pre)} "
      f"before the code, {statistics.median(post)} after; {round(100 * sum(pre) / max(sum(pre) + sum(post), 1))}% "
      f"of all of them before the code.")
spec_n = [serious("docs/plans/" + f) for f in files if "-spec-review" in f]
plan_n = [serious("docs/plans/" + f) for f in files if "-plan-review" in f]
print(f"Median serious findings: {statistics.median(spec_n)} per spec review ({len(spec_n)}), "
      f"{statistics.median(plan_n)} per plan review ({len(plan_n)}).")
