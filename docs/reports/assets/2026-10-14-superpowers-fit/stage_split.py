"""B1 of the superpowers-fit critique: split each finished zitamu spec's time by stage.

Usage: python3 -I stage_split.py ../2026-10-09-workflow-efficiency/data.json
Reads the "specs" list that the 10-09 critique's extract.py wrote.
"""
import json
import statistics
import sys

GAP = 12  # hours; a stage this long looks like a night or a day with no session

specs = [s for s in json.load(open(sys.argv[1]))['specs'] if s.get('plan_at') and s.get('done_at')]
stages = {
    'spec commit -> plan commit': [(s['plan_at'] - s['spec_at']) / 3600 for s in specs],
    'plan commit -> done': [(s['done_at'] - s['plan_at']) / 3600 for s in specs],
}
print(f'{len(specs)} specs')
for name, hours in stages.items():
    print(f'{name}: median {statistics.median(hours):.1f} h, total {sum(hours):.0f} h')
every = [h for hours in stages.values() for h in hours]
long = [h for h in every if h >= GAP]
print(f'{len(long)} stages of {GAP} h or more hold {sum(long):.0f} of {sum(every):.0f} h '
      f'({100 * sum(long) / sum(every):.0f}%)')
