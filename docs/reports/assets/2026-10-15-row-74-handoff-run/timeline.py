"""Row 74 handoff-run audit: a condensed timeline and numbers for one Claude Code transcript.

Usage: python3 -I timeline.py <session.jsonl> [<subagents dir>]
Written for docs/reports/2026-10-15-row-74-handoff-run-audit.md; row 29 may reuse it.
A session ends at its last assistant record. A wait over 30 minutes counts as "away".
Prints a timeline (human msgs, assistant text, tool calls, errors, asks, permission
prompts) and a summary (wall time, agent/user/away time, tokens, tool counts).
"""
import json
import os
import sys
import glob
import collections
from datetime import datetime, timezone

AWAY = 30 * 60


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()


def load(path):
    out = []
    for line in open(path, errors='ignore'):
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def content(d):
    c = (d.get('message') or {}).get('content')
    if isinstance(c, str):
        return [{'type': 'text', 'text': c}]
    return c or []


def short(s, n):
    s = ' '.join(str(s).split())
    return s if len(s) <= n else s[:n] + '…'


def tool_brief(u):
    i = u.get('input') or {}
    n = u.get('name')
    if n == 'Bash':
        return short(i.get('command', ''), 160)
    if n in ('Read', 'Write', 'Edit'):
        return i.get('file_path', '')
    if n == 'Skill':
        return f"{i.get('skill')} {short(i.get('args', ''), 100)}"
    if n == 'Agent':
        return f"[{i.get('subagent_type', '')}] {i.get('description', '')}"
    if n == 'AskUserQuestion':
        return ' || '.join(short(q.get('question', ''), 200) for q in i.get('questions', []))
    return short(json.dumps(i, ensure_ascii=False), 140)


def usage_sum(recs):
    tot = collections.Counter()
    seen = {}
    for d in recs:
        if d.get('type') != 'assistant':
            continue
        mid = (d.get('message') or {}).get('id')
        u = (d.get('message') or {}).get('usage') or {}
        # one message is written as several records; keep the largest count per field
        cur = seen.setdefault(mid, collections.Counter())
        for k, v in u.items():
            if isinstance(v, int):
                cur[k] = max(cur[k], v)
    for cur in seen.values():
        tot.update(cur)
    return tot


def main():
    path = sys.argv[1]
    recs = load(path)
    ev = [d for d in recs if d.get('timestamp') and d.get('type') in ('user', 'assistant', 'system')
          and not d.get('isSidechain')]
    ev.sort(key=lambda d: d['timestamp'])
    t0 = ts(ev[0]['timestamp'])
    names = {}
    tools = collections.Counter()
    errors = 0
    asks = {}
    waits = []
    last_asst = None
    lines = []

    def emit(d, tag, text):
        lines.append(f"{d['timestamp'][11:19]} +{(ts(d['timestamp']) - t0) / 60:5.1f}m {tag:6} {text}")

    for d in ev:
        t = ts(d['timestamp'])
        if d['type'] == 'system':
            if d.get('subtype') == 'turn_duration':
                emit(d, 'TURN', f"turn took {d.get('durationMs', 0) / 60000:.1f} min")
            continue
        if d['type'] == 'assistant':
            last_asst = t
            for x in content(d):
                if x.get('type') == 'text' and x['text'].strip():
                    emit(d, 'SAY', short(x['text'], 400))
                elif x.get('type') == 'tool_use':
                    names[x['id']] = x['name']
                    tools[x['name']] += 1
                    if x['name'] == 'AskUserQuestion':
                        asks[x['id']] = t
                        emit(d, 'ASK', tool_brief(x))
                    else:
                        emit(d, 'TOOL', f"{x['name']}: {tool_brief(x)}")
            continue
        # user record
        pd = d.get('permissionDecision') or {}
        if pd.get('source') == 'user_temporary' or pd.get('decision') not in (None, 'accept'):
            emit(d, 'PERM', json.dumps(pd))
        for x in content(d):
            if x.get('type') == 'tool_result':
                tid = x.get('tool_use_id')
                body = x.get('content')
                if isinstance(body, list):
                    body = ' '.join(y.get('text', '') for y in body if isinstance(y, dict))
                if tid in asks:
                    waits.append((asks.pop(tid), t, 'ask'))
                    emit(d, 'ANSWER', short(body, 400))
                elif x.get('is_error'):
                    errors += 1
                    emit(d, 'ERROR', f"{names.get(tid, '?')}: {short(body, 300)}")
            elif x.get('type') == 'text' and not d.get('isMeta'):
                txt = x['text']
                origin = d.get('turnOrigin')
                if origin == 'human' and not txt.startswith('<local-command') and 'Caveat:' not in txt[:200]:
                    if last_asst is not None:
                        waits.append((last_asst, t, 'msg'))
                    emit(d, 'HUMAN', short(txt, 600))
                elif origin in ('peer', 'task_notification'):
                    emit(d, origin.upper()[:6], short(txt, 250))

    # end at the last assistant record: later records (renames, peer notes) are not work
    t1 = max(ts(d['timestamp']) for d in ev if d['type'] == 'assistant')
    waits = [(a, min(b, t1), k) for a, b, k in waits if a < t1]
    user = sum(b - a for a, b, _ in waits if b - a <= AWAY)
    away = sum(b - a for a, b, _ in waits if b - a > AWAY)
    print('\n'.join(lines))
    print('\n==== SUMMARY', os.path.basename(path))
    print(f"start {ev[0]['timestamp'][:16]}  end {datetime.fromtimestamp(t1, timezone.utc).strftime('%H:%M')}  wall {(t1 - t0) / 60:.1f} min")
    print(f"agent {(t1 - t0 - user - away) / 60:.1f} min, user {user / 60:.1f} min, away {away / 60:.1f} min,"
          f" human msgs {sum(k == 'msg' for *_, k in waits)}, asks answered {sum(k == 'ask' for *_, k in waits)}")
    print('tools', dict(tools.most_common()), 'tool errors', errors)
    u = usage_sum(recs)
    print('tokens main', {k: u[k] for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')})
    if len(sys.argv) > 2:
        for f in sorted(glob.glob(os.path.join(sys.argv[2], 'subagents', '*.jsonl'))):
            r = load(f)
            meta = f.replace('.jsonl', '.meta.json')
            m = json.load(open(meta)) if os.path.exists(meta) else {}
            stamps = [ts(d['timestamp']) for d in r if d.get('timestamp')]
            su = usage_sum(r)
            print(f"  sub {os.path.basename(f)[:24]} {short(json.dumps(m, ensure_ascii=False), 120)}"
                  f" | {(max(stamps) - min(stamps)) / 60:.1f} min | out {su['output_tokens']} cache_read {su['cache_read_input_tokens']}")


main()
