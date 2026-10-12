# /// script
# dependencies = ["matplotlib", "numpy"]
# ///
"""Draw M1 to M4 of the workflow-efficiency critique as SVG.

Usage: uv run plot.py data.json .
M4 reads review_fix_classes.json from the folder of data.json.
"""
import json
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, NullLocator

data = json.load(open(sys.argv[1]))
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Inter", "DejaVu Sans"], "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "svg.fonttype": "none", "svg.hashsalt": "workflow-efficiency",
})


def title(fig, main, sub):
    fig.text(0.02, 0.97, main, fontsize=13, weight="bold", color=INK, va="top")
    fig.text(0.02, 0.97 - 0.3 / fig.get_figheight(), sub, fontsize=10, color=INK2, va="top")


# M1: branch lead time per week of the squash commit
def monday(ts):
    d = datetime.fromtimestamp(ts).date()
    return d - timedelta(days=d.weekday())


weeks = {}
for b in data["branches"]:
    weeks.setdefault(monday(b["squash_ct"]), []).append(max(b["hours"], 0.05))
order = sorted(weeks)
fig, ax = plt.subplots(figsize=(8, 4.2))
fig.subplots_adjust(left=0.17, right=0.84, top=0.8, bottom=0.14)
for i, w in enumerate(order):
    hs = sorted(weeks[w])
    jitter = [(k % 5 - 2) * 0.07 for k in range(len(hs))]
    ax.scatter(hs, [i + j for j in jitter], s=36, color=BLUE, alpha=0.75, edgecolor=SURFACE, linewidth=1.5, zorder=3)
    med = statistics.median(hs)
    ax.plot([med, med], [i - 0.3, i + 0.3], color=INK, linewidth=2, zorder=4)
    ax.text(1.02, i, f"median {med:.1f} h", transform=ax.get_yaxis_transform(), va="center", color=INK2, fontsize=9)
ax.set_xscale("log")
ax.set_xlim(0.05, 140)
ax.xaxis.set_major_locator(FixedLocator([0.25, 1, 4, 16, 64]))
ax.xaxis.set_minor_locator(NullLocator())
ax.set_xticklabels(["15 min", "1 h", "4 h", "16 h", "64 h"])
ax.set_yticks(range(len(order)))
ax.set_yticklabels([f"Week of {w:%d %b}\n{len(weeks[w])} branches" for w in order])
ax.invert_yaxis()
ax.grid(axis="x", color=GRID, linewidth=1)
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.set_xlabel("Hours from the branch's first commit to its squash-merge (log scale)")
title(fig, "M1. Most branches merge within a few hours",
      f"{len(data['branches'])} branches. Each dot is one branch; the black tick is the week's median. The last week is partial.")
fig.savefig(out / "m1-branch-lead-time.svg", metadata={"Date": None})

# M2: spec stages, one bar per done spec
specs = sorted(data["specs"], key=lambda s: s["done_at"] - s["spec_at"], reverse=True)
fig, ax = plt.subplots(figsize=(8, 7.5))
fig.subplots_adjust(left=0.36, right=0.95, top=0.88, bottom=0.12)
for i, s in enumerate(specs):
    total = (s["done_at"] - s["spec_at"]) / 3600
    if s["plan_at"] is None:
        ax.barh(i, total, height=0.62, color=AQUA, edgecolor=SURFACE, linewidth=1)
    else:
        a = max((s["plan_at"] - s["spec_at"]) / 3600, 0)
        ax.barh(i, a, height=0.62, color=BLUE, edgecolor=SURFACE, linewidth=1)
        ax.barh(i, total - a, left=a, height=0.62, color=ORANGE, edgecolor=SURFACE, linewidth=1)
    if total >= 12:
        ax.text(total + 1.5, i, f"{total:.0f} h", va="center", color=INK2, fontsize=9)
ax.set_yticks(range(len(specs)))
ax.set_yticklabels([s["slug"][11:] for s in specs], fontsize=8.5)
ax.invert_yaxis()
ax.tick_params(axis="y", length=0)
ax.set_xlim(0, 130)
ax.grid(axis="x", color=GRID, linewidth=1)
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.set_xlabel("Hours from the spec's first commit (author dates)")
ax.legend(handles=[Patch(color=BLUE, label="Spec to plan committed"),
                   Patch(color=ORANGE, label="Plan committed to spec done"),
                   Patch(color=AQUA, label="Medium change: spec to done, no plan file")],
          loc="lower right", frameon=False, labelcolor=INK2)
title(fig, "M2. The long cycles are one long wait between two stages",
      f"{len(specs)} specs marked done, longest at the top. Each long bar is mostly one colour: one wait.")
fig.savefig(out / "m2-spec-stages.svg", metadata={"Date": None})

# M3: where the 105 branch fix commits came from (counts from the zitamu audit)
causes = [("The end-of-branch reviews found it", 40), ("Planned work: the branch exists to fix it", 49),
          ("Found while building", 11), ("The message does not say", 5)]
causes.sort(key=lambda c: c[1])
fig, ax = plt.subplots(figsize=(8, 3))
fig.subplots_adjust(left=0.38, right=0.93, top=0.7, bottom=0.05)
for i, (label, n) in enumerate(causes):
    ax.barh(i, n, height=0.55, color=BLUE if "reviews" in label else AXIS)
    ax.text(n + 0.8, i, str(n), va="center", color=INK, fontsize=10)
ax.set_yticks(range(len(causes)))
ax.set_yticklabels([c[0] for c in causes])
ax.tick_params(axis="y", length=0)
ax.set_xticks([])
for side in ("left", "bottom"):
    ax.spines[side].set_visible(False)
title(fig, "M3. Reviews found 40 of the 105 fix commits on branches",
      "Sorted by commit message. 29 of 55 branches had a review fix; 21 had exactly one.")
fig.savefig(out / "m3-fix-causes.svg", metadata={"Date": None})
# M4: where the review-found defects started (classes in review_fix_classes.json)
NAMES = {"C": "Code broke a rule the spec stated", "L": "Layout broke at an unchecked width or language",
         "S": "The spec missed or got a decision wrong", "P": "Browser or framework behaviour",
         "T": "The test checked the wrong thing", "D": "Comments only"}
UPSTREAM = {"L", "S", "T"}
rows = [r for r in json.load(open(Path(sys.argv[1]).parent / "review_fix_classes.json")) if r["class"] != "X"]
counts = sorted(((c, sum(r["class"] == c for r in rows)) for c in NAMES), key=lambda c: c[1])
fig, ax = plt.subplots(figsize=(8, 3.6))
fig.subplots_adjust(left=0.45, right=0.93, top=0.74, bottom=0.12)
for i, (c, n) in enumerate(counts):
    ax.barh(i, n, height=0.55, color=BLUE if c in UPSTREAM else AXIS)
    ax.text(n + 0.3, i, str(n), va="center", color=INK, fontsize=10)
ax.set_yticks(range(len(counts)))
ax.set_yticklabels([NAMES[c] for c, _ in counts])
ax.tick_params(axis="y", length=0)
ax.set_xticks([])
for side in ("left", "bottom"):
    ax.spines[side].set_visible(False)
ax.legend(handles=[Patch(color=BLUE, label="A spec or plan could prevent it"), Patch(color=AXIS, label="It could not")],
          loc="lower right", frameon=False, labelcolor=INK2)
up = sum(n for c, n in counts if c in UPSTREAM)
title(fig, f"M4. A spec or plan could have prevented {up} of the {len(rows)} review fixes",
      "Each fix sorted by hand from its commit message into the one place the defect started.")
fig.savefig(out / "m4-review-fix-sources.svg", metadata={"Date": None})
print("wrote", sorted(p.name for p in out.glob("*.svg")))
