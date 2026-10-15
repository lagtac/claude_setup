"""B2 of the superpowers-fit critique: time from brainstorming start to spec commit,
split into agent work and waits for the user.

Usage: python3 -I spec_time.py [--json spec_time.json]
       python3 -I spec_time.py --summary spec_time.json
Reads ~/.claude/projects/*/*.jsonl (main sessions only, no subagent files).
The first form prints one row per spec session; --json also saves the rows.
--summary prints the medians and sums the report quotes, from saved rows.
"""
import glob
import json
import os
import re
import statistics
import sys
from datetime import datetime

AWAY = 30 * 60  # a wait longer than this counts as "away", not reading/answering
SPEC_RE = re.compile(r'docs/plans/[^"\s]*-spec\.md')


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()


def events(path):
    out = []
    for line in open(path, errors='ignore'):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get('type') not in ('user', 'assistant') or d.get('isSidechain') or not d.get('timestamp'):
            continue
        out.append(d)
    out.sort(key=lambda d: d['timestamp'])
    return out


def real_user_text(d):
    if d['type'] != 'user' or d.get('isMeta'):
        return False
    c = (d.get('message') or {}).get('content')
    if isinstance(c, str):
        return not c.startswith('<local-command-stdout>') and 'Caveat:' not in c[:200]
    if isinstance(c, list):
        return any(x.get('type') == 'text' for x in c) and not any(x.get('type') == 'tool_result' for x in c)
    return False


def tool_uses(d):
    c = (d.get('message') or {}).get('content')
    return [x for x in c if isinstance(c, list) and x.get('type') == 'tool_use'] if isinstance(c, list) else []


def tool_results(d):
    c = (d.get('message') or {}).get('content')
    return [x for x in c if x.get('type') == 'tool_result'] if isinstance(c, list) else []


def analyse(path):
    ev = events(path)
    start = write = commit = None
    spec = None
    for d in ev:
        for u in tool_uses(d):
            inp = u.get('input') or {}
            if start is None and u.get('name') == 'Skill' and inp.get('skill') == 'superpowers:brainstorming':
                start = ts(d['timestamp'])
            if start and write is None and u.get('name') == 'Write' and SPEC_RE.search(inp.get('file_path', '')):
                write = ts(d['timestamp'])
                spec = inp['file_path']
            if write and commit is None and u.get('name') == 'Bash' and 'git commit' in inp.get('command', '') \
                    and ('spec' in inp.get('command', '') or 'locked-commit' in inp.get('command', '')):
                commit = ts(d['timestamp'])
    if not (start and write):
        return None
    end = commit or ts(ev[-1]['timestamp'])

    # waits for the user, as (from, to) intervals
    waits = []
    last_asst = None
    ask_open = {}
    for d in ev:
        t = ts(d['timestamp'])
        if d['type'] == 'assistant':
            last_asst = t
            for u in tool_uses(d):
                if u.get('name') == 'AskUserQuestion':
                    ask_open[u['id']] = t
        else:
            for r in tool_results(d):
                if r.get('tool_use_id') in ask_open:
                    waits.append((ask_open.pop(r['tool_use_id']), t, 'ask'))
            if real_user_text(d) and last_asst is not None:
                waits.append((last_asst, t, 'msg'))

    def phase(a, b):
        user = away = 0.0
        turns = asks = 0
        for w0, w1, kind in waits:
            lo, hi = max(w0, a), min(w1, b)
            if hi <= lo:
                continue
            dur = hi - lo
            if w1 - w0 > AWAY:
                away += dur
            else:
                user += dur
            if a <= w1 <= b:
                turns += kind == 'msg'
                asks += kind == 'ask'
        total = b - a
        return dict(total=total, agent=total - user - away, user=user, away=away, turns=turns, asks=asks)

    return dict(file=path, spec=spec, date=datetime.fromtimestamp(start).strftime('%Y-%m-%d'),
                committed=commit is not None,
                dialogue=phase(start, write), review=phase(write, end))


def summary(rows):
    def m(xs):
        return statistics.median(xs) / 60

    for ph in ('dialogue', 'review'):
        print(f"{ph:8} n={len(rows)} median min:", ' '.join(
            f"{k} {m([r[ph][k] for r in rows]):.0f}" for k in ('total', 'agent', 'user', 'away')))
    q = [r['dialogue']['turns'] + r['dialogue']['asks'] for r in rows]
    user = sum(r['dialogue']['user'] for r in rows)
    print(f"dialogue answers: median {statistics.median(q)}, total {sum(q)}, user min per answer {user / 60 / sum(q):.1f}")
    whole = [r['dialogue']['total'] + r['review']['total'] for r in rows]
    away = [r['dialogue']['away'] + r['review']['away'] for r in rows]
    print(f"whole session median min {m(whole):.0f}; sessions with a gap over 30 min: {sum(a > 0 for a in away)};"
          f" share of elapsed hours in those gaps {100 * sum(away) / sum(whole):.0f}%")
    print(f"projects {len({r['project'] for r in rows})}, dates {rows[0]['date']} to {rows[-1]['date']}")


def main():
    if '--summary' in sys.argv:
        summary(json.load(open(sys.argv[sys.argv.index('--summary') + 1])))
        return
    rows = []
    for f in glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl')):
        proj = os.path.basename(os.path.dirname(f))
        if any(k in proj for k in ('scratchpad', 'claude-jobs', 'fixture')):
            continue
        txt = open(f, errors='ignore').read()
        if '"superpowers:brainstorming"' not in txt or '-spec.md' not in txt:
            continue
        r = analyse(f)
        if r:
            r['project'] = proj.replace('-home-dchris-projects-', '')
            rows.append(r)
    rows.sort(key=lambda r: r['date'])
    if '--json' in sys.argv:
        json.dump(rows, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    def h(s):
        return f'{s / 3600:5.2f}'

    print(f"{'date':10} {'project':28} {'spec':42} | dialogue: tot agent user away turns asks | review->commit: tot agent user away | committed")
    for r in rows:
        a, b = r['dialogue'], r['review']
        print(f"{r['date']} {r['project'][:28]:28} {os.path.basename(r['spec'])[:42]:42} | {h(a['total'])} {h(a['agent'])} {h(a['user'])} {h(a['away'])} {a['turns']:3} {a['asks']:3} | {h(b['total'])} {h(b['agent'])} {h(b['user'])} {h(b['away'])} | {r['committed']}")


main()
