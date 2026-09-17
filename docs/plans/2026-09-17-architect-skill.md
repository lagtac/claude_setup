# `my:architect` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `my:architect` skill that turns a system description into a committed architecture brief, and make it run before `superpowers:brainstorming` for new systems and contract changes.

**Architecture:** One skill file drives the whole method in the main conversation: forces, collapse gate, shape choice, parallel candidate dispatch, draft checks, evaluation, choice, reversibility checks and the brief. A second file is the prompt template for the `general-purpose` candidate subagents. `GLOBAL-CLAUDE.md` adds the trigger row and the handoff rules for brainstorming.

**Tech Stack:** Claude Code plugin markdown (skills), Bash, Python 3 standard library (estimate scripts and test checker), `claude -p` headless runs for tests, `markdownlint-cli2`.

**Spec:** `docs/plans/2026-09-17-architect-skill-spec.md` (read it first; this plan does not repeat its reasons).

## Global Constraints

- Conventional Commits with scope: `type(scope): sentence`. Scope for plugin files is `my-plugin`; for `GLOBAL-CLAUDE.md` it is `global`; for `ROADMAP.md` and `docs/plans/` it is `plans` or none, matching `git log`.
- Every commit ends with `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
- No new dependencies. Estimate scripts and the test checker use the Python 3 standard library only.
- Do not edit `superpowers:brainstorming` or `my:spec-review`.
- Subagents lose `Grep`, `Glob` and `LSP` at run time. `grep -rn` and `find` through `Bash` are the main search route.
- Work happens in a worktree on branch `feat/architect-skill`. Integrate with `git merge --squash`. Remove the worktree after merge. Do not delete the branch.
- Test fixtures, fixture repos, logs and briefs from test runs live in the scratchpad. They are never committed.

## Decisions made while writing this plan

Two gaps were found and confirmed with the user on 2026-09-17. The spec was updated in the same commit as this plan:

- **`AskUserQuestion` is absent in headless `claude -p` runs** (checked: the tool is not in the tool list). D3 and D9 now say what happens when a question cannot be asked: continue, keep labels, record under "Open for brainstorming".
- **The D3 correction window is the question call itself.** When nothing needs asking, the skill does not pause.

Smaller gaps this plan fills without a spec change. Review these before executing:

- **No git repository.** The skill still writes the brief to `<cwd>/docs/plans/`, skips the commit, and says so. D10 assumes a repo; a new project may not have one yet.
- **Brief name collision.** An existing brief path gets `-2`, `-3`, like `my:spec-review` reviews.
- **Contrast record.** Each candidate in the brief gets one `**Contrast:**` line naming the axes it differs on. This makes the D5 check visible and testable.
- **Starting axis values per shape.** SKILL.md gives a table of default axis values for each menu shape, adjusted to the system. It makes the D5 before-dispatch check concrete.
- **Skip lines for unpicked shapes** are written in both gate outcomes: all 6 menu shapes when one candidate is made, the 4 unpicked shapes when three are made.

## How tests run

The repo has no test runner. The `my` plugin loads through the alias `claude --plugin-dir ~/projects/claude-setup/my-plugin`, so the running session cannot see a new skill in the worktree. Every Green check runs a headless session against the worktree's plugin.

The skill commits its brief. So each run happens inside a **throwaway fixture repo** in the scratchpad, never inside the worktree. That keeps test briefs out of the branch.

```bash
WT=<absolute worktree path>
SCRATCH=<the executing session's scratchpad directory>
FX="$SCRATCH/fx/<name>"      # a fixture repo made in Task 1
cd "$FX" && claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits \
  --allowedTools "Bash(git:*)" "Bash(python3:*)" "Bash(mkdir:*)" "Bash(mktemp:*)" "Bash(date:*)" "Bash(ls:*)" \
  --max-budget-usd 20 --output-format stream-json --verbose "<prompt>" > "$SCRATCH/green/<run-name>.jsonl"
```

- `--allowedTools` lets the skill commit and run estimate scripts without a prompt. If the last line of the log lists `permission_denials`, add that command pattern and rerun.
- `--max-budget-usd 20` is a cost guard. If a run stops on it, record that, raise it once, and rerun.
- `AskUserQuestion` is absent in these runs. The skill's "cannot be asked" rules apply, and every Decision section says "chosen without the user".

## File map

| File | Status | Responsibility |
|---|---|---|
| `my-plugin/skills/architect/candidate-prompt.md` | Create | Prompt template for one candidate subagent: description, repo root, forces, shape and reason, D6 schema, search wording |
| `my-plugin/skills/architect/SKILL.md` | Create | Steps D3–D10, failure branches, "cannot be asked" rules, brief template, commit |
| `GLOBAL-CLAUDE.md` | Modify | D11: trigger row, "Discovery authority" rules, Spec → Plan step 1 |
| `ROADMAP.md` | Modify | New row for `my:architect` |
| `$SCRATCH/check_brief.py` | Create (scratch) | Test checker for brief structure and draft schema. Never committed |

---

### Task 0: Worktree

- [ ] **Step 1:** Invoke `superpowers:using-git-worktrees`. Create branch `feat/architect-skill` from `main`, at or after the commit that adds this plan. Set `WT` to the worktree path.
- [ ] **Step 2:** Confirm: `git -C "$WT" log --oneline -1` shows the plan commit, and `git -C "$WT" status --short` is empty.

---

### Task 1: Preflight, fixtures, checker and Red baseline

**Files:**

- Create: `$SCRATCH/fixtures/small.md`, `$SCRATCH/fixtures/large.md`, `$SCRATCH/fixtures/manual.md`
- Create: `$SCRATCH/fx/small`, `$SCRATCH/fx/large` (empty git repos)
- Create: `$SCRATCH/check_brief.py`, `$SCRATCH/sample-brief.md`

**Interfaces:**

- Produces: fixture texts and repos used by Tasks 2, 3 and 5; `python3 "$SCRATCH/check_brief.py" <brief> small|large` (exit 0 and `PASS` when all checks pass, exit 1 and one `FAIL: …` line per failed check); `python3 "$SCRATCH/check_brief.py" --draft <candidate.md>` (checks the 7 D6 headings); Red notes `$SCRATCH/red-baseline-notes.md`.

- [ ] **Step 1: Preflight — `general-purpose` with `model: "opus"`**

```bash
mkdir -p "$SCRATCH/preflight" && cd "$SCRATCH/preflight"
claude -p --max-budget-usd 2 --output-format stream-json --verbose \
  'Use the Agent tool once with subagent_type "general-purpose", model "opus", description "Preflight", prompt "Reply with the single word ok." Then report the reply verbatim.' \
  > opus.jsonl
grep -o '"subagent_type":"general-purpose"' opus.jsonl | head -1   # present
grep -o '"model":"opus"' opus.jsonl | head -1                      # present
tail -1 opus.jsonl | grep -o '"result":"[^"]*"'                    # contains ok, no error text
```

Expected: all three present, and the result says `ok`. **If the dispatch is rejected**, stop. Ask the user: "Spec D7 picked `model: \"opus\"` for candidates. The Agent tool rejects it for `general-purpose` with [error text]. Keep D7 with another model, or change the packaging?" Do not choose a model yourself.

- [ ] **Step 2: Preflight — `AskUserQuestion` in headless runs**

```bash
cd "$SCRATCH/preflight"
claude -p --model haiku --max-budget-usd 0.5 --output-format stream-json --verbose \
  "Use the AskUserQuestion tool once to ask 'Pick a colour' with options Red and Blue. Report what happened." > aq.jsonl
grep -c '"name":"AskUserQuestion"' aq.jsonl    # 0: the tool is not available
```

Expected: `0`. This was already seen on 2026-09-17. If the tool **is** available now, the headless runs may block on a question. Then add `--disallowedTools AskUserQuestion` to every Green command in this plan.

- [ ] **Step 3: Write the fixtures**

`$SCRATCH/fixtures/small.md` states every force, and every gate force passes D4:

```markdown
Build a command-line tool for me that reads my bank's monthly CSV export and writes a categorised spending summary to a Markdown file.

All of these are confirmed by me:

- Load: I run it by hand once a month, one run at a time.
- Data volume: about 2 MB of CSV per year.
- Latency: no target; a few seconds per run is fine.
- Availability: no target; it runs on my laptop.
- Consistency: each run reads one file and writes one file; nothing runs at the same time.
- Security: personal financial data; it stays on my laptop and never uses the network.
- Team: one developer (me), no on-call.
- Rate of change: category rules change about twice a year.
- Cost: zero; no hosting.
- Fixed constraints: Python 3 standard library only; at most one local SQLite file.
```

`$SCRATCH/fixtures/large.md` states forces 1–8 and 10, with high write load, strict consistency for one entity and a team of 3. Force 9 (cost) is left out on purpose, to test the D3 "cannot be asked" rule:

```markdown
Design the order and seat-inventory service for a concert ticketing platform.

All of these are confirmed by me:

- Load: 2,000 purchase writes per second at on-sale peaks, 200 at normal times; 20,000 seat-map reads per second at peak.
- Data volume: 400 GB now, growing by 150 GB per year.
- Latency: purchase confirmation under 300 ms at p95.
- Availability: at most 5 minutes of downtime per month.
- Consistency: a seat is never sold twice — seat reservations must be exact immediately. Sales reports may lag up to 5 minutes.
- Security: card payments go through an external payment provider; we store buyer names and email addresses; GDPR applies.
- Team: 3 developers, one on-call rotation.
- Rate of change: pricing rules change weekly; the seat model rarely changes.
- Fixed constraints: PostgreSQL is required; everything runs in one cloud region.
```

`$SCRATCH/fixtures/manual.md` states forces 1–3 only, for the interactive run in Task 5:

```markdown
Design a small internal web app where our clinic's receptionists book patient appointments.

Confirmed by me:

- Load: under 2 requests per second.
- Data volume: 1 GB now, growing by 0.5 GB per year.
- Latency: pages under 1 second.
```

- [ ] **Step 4: Make the fixture repos**

```bash
for n in small large manual; do
  mkdir -p "$SCRATCH/fx/$n" && git -C "$SCRATCH/fx/$n" init -q \
    && git -C "$SCRATCH/fx/$n" commit -q --allow-empty -m "chore: fixture root"
done
mkdir -p "$SCRATCH/green"
```

- [ ] **Step 5: Write the checker `$SCRATCH/check_brief.py`**

```python
#!/usr/bin/env python3
"""Structure checks for a my:architect brief or one candidate draft. Test tool; never committed."""
import re
import sys

SECTIONS = [
    "How to read this brief", "Forces", "Collapse gate", "Candidates", "Evaluation",
    "Decision", "Reversibility and checks", "Open for brainstorming", "Appendix: candidate drafts",
]
PLAN_SECTIONS = [
    "Context", "Files to Modify/Create", "Step-by-Step Implementation",
    "Trade-Offs / Alternatives Considered", "Dependencies", "Risk", "Testing Strategy", "Open Questions",
]
DRAFT = ["Summary", "Components", "Connections", "Forces", "Hard-to-reverse decisions",
         "Numbers it depends on", "Weakest point"]
FORCE_NAMES = {1: "load", 2: "data volume", 3: "latency", 4: "availability", 5: "consistency",
               6: "security", 7: "team", 8: "rate of change", 9: "cost", 10: "fixed constraints"}
MENU = ["queue", "event-driven", "separate deployables", "pipeline", "client-heavy", "serverless"]


def section(text, name):
    m = re.search(r"^## " + re.escape(name) + r"\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def check_draft(path):
    text = open(path, encoding="utf-8").read()
    found = re.findall(r"^### (.+?)\s*$", text, re.M)
    return [] if found == DRAFT else [f"draft headings are {found}, expected {DRAFT}"]


def check_brief(path, mode):
    fails = []
    text = open(path, encoding="utf-8").read()
    found = re.findall(r"^## (.+?)\s*$", text, re.M)
    if found != SECTIONS:
        fails.append(f"sections are {found}, expected {SECTIONS}")
    for p in PLAN_SECTIONS:
        if p in found:
            fails.append(f"plan-format section present: {p}")
    rows = {}
    for line in section(text, "Forces").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].isdigit():
            labels = [c for c in cells if c in ("stated", "inferred", "assumed")]
            rows[int(cells[0])] = labels
    if sorted(rows) != list(range(1, 11)):
        fails.append(f"forces table rows are {sorted(rows)}, expected 1..10")
    for n, labels in rows.items():
        if len(labels) != 1:
            fails.append(f"force {n} has labels {labels}, expected exactly one")
    gate = section(text, "Collapse gate").lower()
    want = "one candidate" if mode == "small" else "three candidates"
    if want not in gate:
        fails.append(f"collapse gate does not say '{want}'")
    if mode == "small":
        for shape in MENU:
            if shape not in gate:
                fails.append(f"no skip reason for shape '{shape}'")
    open_items = section(text, "Open for brainstorming").lower()
    for n, labels in rows.items():
        if labels == ["assumed"] and FORCE_NAMES[n] not in open_items:
            fails.append(f"assumed force {n} ({FORCE_NAMES[n]}) not in Open for brainstorming")
    if "chosen without the user" not in section(text, "Decision").lower():
        fails.append("headless run but Decision lacks 'chosen without the user'")
    return fails


if __name__ == "__main__":
    if sys.argv[1] == "--draft":
        fails = check_draft(sys.argv[2])
    else:
        fails = check_brief(sys.argv[1], sys.argv[2])
    for f in fails:
        print("FAIL:", f)
    print("PASS" if not fails else f"{len(fails)} failure(s)")
    sys.exit(1 if fails else 0)
```

- [ ] **Step 6: Prove the checker can pass and can fail**

Write `$SCRATCH/sample-brief.md`, a minimal brief that should pass in `small` mode:

```markdown
# Architecture brief: sample

## How to read this brief

- This brief.

## Forces

| # | Force | Value | Label | Source or reason |
|---|---|---|---|---|
| 1 | Load | once a month | stated | user |
| 2 | Data volume and growth | 2 MB/year | stated | user |
| 3 | Latency target | none | stated | user |
| 4 | Availability | none | stated | user |
| 5 | Consistency | single writer | stated | user |
| 6 | Security and compliance | local only | stated | user |
| 7 | Team and operations | 1 developer | stated | user |
| 8 | Rate of change | twice a year | stated | user |
| 9 | Cost | unknown, assumed zero | assumed | no hosting mentioned |
| 10 | Fixed constraints | Python stdlib | stated | user |

## Collapse gate

One candidate. Skipped: queue (needs force 1 above 50/s), event-driven, separate deployables, pipeline, client-heavy, serverless — each needs a force value this system does not have.

## Candidates

A.

## Evaluation

None.

## Decision

A, chosen without the user.

## Reversibility and checks

None.

## Open for brainstorming

- Force 9 cost.

## Appendix: candidate drafts

A.
```

```bash
python3 "$SCRATCH/check_brief.py" "$SCRATCH/sample-brief.md" small; echo "exit=$?"   # PASS, exit=0
sed 's/- Force 9 cost./- nothing/' "$SCRATCH/sample-brief.md" > "$SCRATCH/sample-bad.md"
python3 "$SCRATCH/check_brief.py" "$SCRATCH/sample-bad.md" small; echo "exit=$?"    # FAIL: assumed force 9 (cost) …, exit=1
python3 "$SCRATCH/check_brief.py" "$SCRATCH/sample-brief.md" large; echo "exit=$?"  # FAIL: … 'three candidates', exit=1
```

Expected: exactly the results in the comments. If not, fix the checker, not the sample.

- [ ] **Step 7: Red — the skill does not exist**

Run: `ls "$WT/my-plugin/skills/architect"`
Expected: `No such file or directory`.

- [ ] **Step 8: Red baseline — brainstorming alone**

Run each fixture through brainstorming only, in the main checkout's plugin setup:

```bash
for n in small large; do
  cd "$SCRATCH/fx/$n" && claude -p --max-budget-usd 10 --output-format stream-json --verbose \
    "Use superpowers:brainstorming to design this system. This is a headless run and nobody can answer questions: answer your own clarifying questions from the description, then continue through proposing approaches. Do not write or commit files.

$(cat "$SCRATCH/fixtures/$n.md")" > "$SCRATCH/red-$n.jsonl"
done
```

Read the final `result` of each log. Record yes or no for each fixture in `$SCRATCH/red-baseline-notes.md`:

1. It shows all 10 forces, each with a `stated` / `inferred` / `assumed` label. (Expected: no.)
2. Its approaches differ on at least two of the D5 axes: process count, data ownership, sync versus async, where computation runs. (Record what it does.)
3. It runs an estimate: `grep -c 'python3' "$SCRATCH/red-$n.jsonl"` is above 0. (Expected: no.)

No commit. Everything in this task lives in the scratchpad.

---

### Task 2: Candidate prompt and skill; Green on the small fixture

**Files:**

- Create: `my-plugin/skills/architect/candidate-prompt.md`
- Create: `my-plugin/skills/architect/SKILL.md`

**Interfaces:**

- Consumes: fixtures, fixture repos and checker from Task 1.
- Produces: skill name `my:architect` (argument: a description, or a path to a file with one); template placeholders `{{CANDIDATE_LETTER}}`, `{{SHAPE}}`, `{{SHAPE_REASON}}`, `{{DESCRIPTION}}`, `{{REPO_ROOT}}`, `{{FORCES_TABLE}}`; brief path `docs/plans/YYYY-MM-DD-<slug>-architecture[-N].md`; brief section names exactly as in `SECTIONS` in `check_brief.py`; draft files `<work dir>/candidate-{a,b,c}.md`; the printed lines `Architecture brief written to <path>.` and `Next: invoke superpowers:brainstorming with <path> as input.`

- [ ] **Step 1: Create `my-plugin/skills/architect/candidate-prompt.md`**

````markdown
# Architecture Candidate Dispatch Prompt

This file is the prompt template the `my:architect` skill sends to each `general-purpose` candidate subagent. The skill substitutes the placeholders before dispatch:

- `{{CANDIDATE_LETTER}}` — `A`, `B` or `C`
- `{{SHAPE}}` — the assigned shape name
- `{{SHAPE_REASON}}` — one line naming the force that justifies the shape
- `{{DESCRIPTION}}` — the user's description of the system, word for word
- `{{REPO_ROOT}}` — the absolute repository root, or the text `none`
- `{{FORCES_TABLE}}` — the confirmed forces table, with labels

Copied rules: the search-tool wording is copied from the grounding bullet in `my-plugin/agents/spec-reviewer.md`. When you edit it there, check this file too.

The body below this header is the prompt itself. Send everything below the `---` line.

---

You are a software architect. Draft **one** candidate architecture for the system below, in the shape assigned to you.

Other agents draft other candidates in other shapes. You cannot see their work. Do not cover their shapes. Write the strongest honest version of your own shape, including where it is weak.

## Assigned shape

Candidate {{CANDIDATE_LETTER}}: **{{SHAPE}}**.

Why this shape was picked: {{SHAPE_REASON}}

If the shape is "simplest design", it means: one deployable process, one data store, synchronous calls. Stay inside that.

## System description

The user's words, unchanged:

{{DESCRIPTION}}

## Repository

Repository root: `{{REPO_ROOT}}`

- If it is `none`, no repository exists yet. Design from the description and the forces only.
- If it is a path, read the code that matters for the design: the stack, existing modules, data models, configuration. Use absolute paths under that root. Do not rely on the current working directory.
- Search with `Read` plus `Bash` searches (`grep -rn`, `find`) — `Bash` is always available. Use the `Grep` / `Glob` tools, and `LSP`, only when they are in your tool list; they often are not, so never let their absence cancel a search.
- You are read-only. Do not write, edit or commit any file. Return your draft as text.

## Forces

Each force has one label: `stated` (the user said it — treat as fixed), `inferred` (taken from a named source — treat as likely), `assumed` (not confirmed — a guess).

{{FORCES_TABLE}}

If your design depends on an `assumed` force, say so under `### Weakest point`.

## Output schema

Return only markdown, about 800 words. Use exactly these seven headings, in this order. Put no text before the first heading, and add no other headings.

```markdown
### Summary

Shape: {{SHAPE}}. [At most 5 sentences.]

### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| [name] | [one job] | [the state it is the source of truth for, or "none"] | [deployable process, worker, client, managed service] |

### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| [A → B] | [call, message, file, event] | sync / async | [what the sender does: retry, queue, fail the request, …] |

### Forces

Served:

- [force number] ([name]): [reason]

Sacrificed:

- [force number] ([name]): [reason]

### Hard-to-reverse decisions

- [decision]

### Numbers it depends on

- [a number and what it is compared to, for example "under 50 writes/s to one PostgreSQL instance"]

### Weakest point

[The best argument against this candidate.]
```
````

- [ ] **Step 2: Create `my-plugin/skills/architect/SKILL.md`**

`````markdown
---
name: architect
description: >
  Design an architecture from forces before the spec is written. Fills a labelled table of 10 forces
  (load, data volume, latency, availability, consistency, security, team, rate of change, cost, fixed
  constraints), uses a collapse gate to decide between one and three candidate designs, drafts the
  candidates in parallel subagents to a fixed schema, evaluates them (data ownership, scenario traces,
  pre-mortem, comparison), checks hard-to-reverse decisions with Python estimate scripts, and commits
  an architecture brief to docs/plans/YYYY-MM-DD-<slug>-architecture.md. Required before
  superpowers:brainstorming for a new project, a new subsystem, or a change to a data model, storage
  choice or public contract; also whenever asked. Does not write the spec. NOT for reviewing a spec
  (my:spec-review) or code (my:soundness-review).
---

# Architect

Turn a description of a system into an **architecture brief**: the forces, the candidates, how they were evaluated, the chosen design and the checks behind it. `superpowers:brainstorming` reads the brief next and writes the spec. This skill never writes the spec.

The candidate prompt lives in `candidate-prompt.md`. Everything else runs here, in the main conversation.

**The brief is not a plan.** It lives in `docs/plans/`, where the plan-format rule loads, but it follows only the sections in step 9. Do not add Context, Files to Modify/Create, Step-by-Step Implementation, Trade-Offs, Dependencies, Risk, Testing Strategy or Open Questions sections.

**When a question cannot be asked.** Steps 1, 7 and 8 ask the user with `AskUserQuestion`. If that tool is not in your tool list (as in a headless `claude -p` run), or the call fails, do **not** ask in plain text and do **not** end your turn. Use the "cannot be asked" rule written in that step and continue.

## Steps

### 0. Set up

- **Description.** The args string is the description. If it is a path to an existing file, the file's contents are the description. If args is empty and the conversation holds no description, stop and print: `Usage: my:architect <description of the system, or a path to a file with it>`. Keep the description word for word as `DESCRIPTION`.
- **Slug.** `SLUG` is 2–4 kebab-case words naming the system, for example `ticket-inventory`.
- **Repo root.** Run `git rev-parse --show-toplevel`. On success, `REPO_ROOT` is that absolute path. Otherwise `REPO_ROOT` is `none`, and the brief goes to `<cwd>/docs/plans/` without a commit (step 9).
- **Brief path.** `BRIEF_PATH` is `docs/plans/$(date +%F)-<SLUG>-architecture.md`, under the repo root (or cwd). If it exists, append `-2`, then `-3`, until the path is free. Never overwrite a brief.
- **Work directory.** `WORK_DIR` is `<scratchpad>/architect/<SLUG>`, where `<scratchpad>` is the session's scratchpad directory from the system prompt. If there is none, use `$(mktemp -d)/architect/<SLUG>`. Run `mkdir -p` on it.

### 1. Forces (D3)

1. **Draft.** Read the description and, when `REPO_ROOT` is a path, the repo. Fill all 10 forces. Each gets a value and exactly one label:
   - `stated` — the user said it.
   - `inferred` — taken from a named source, for example `composer.json`. Name the source.
   - `assumed` — not confirmed. Write the value as `unknown, assumed <X>` and give a reason.

   | # | Force | Example value |
   |---|---|---|
   | 1 | Load | 200 users, 5 requests/s at peak |
   | 2 | Data volume and growth | 50 GB now, +10 GB per year |
   | 3 | Latency target | page under 500 ms at p95 |
   | 4 | Availability | 1 hour of downtime per month is acceptable |
   | 5 | Consistency | payments exact immediately; counts may lag 1 minute |
   | 6 | Security and compliance | personal health data, GDPR applies |
   | 7 | Team and operations | 1 developer, no on-call rotation |
   | 8 | Rate of change | import rules change monthly; core model rarely |
   | 9 | Cost | under €50/month hosting |
   | 10 | Fixed constraints | must use Laravel and MySQL; one VPS |

   A force with no evidence is `assumed`.
2. **Show.** Print the whole table in chat, with columns `# | Force | Value | Label | Source or reason`.
3. **Ask.** Collect the forces labelled `assumed` or `inferred`. Order them: 1, 3, 4, 7 first (the gate forces), then 5, 10, then 2, 6, 8, 9. Take the first 4.
   - If the list is empty, make no call and do not pause. Go to step 5.
   - Otherwise make **one** `AskUserQuestion` call with one question per chosen force. Header: `Force <n>`. Each question offers 2–4 concrete ranges as options, for example for force 1: `Under 5 req/s`, `5–50 req/s`, `50–500 req/s`, `Over 500 req/s`. The first question's text ends with: `To correct any other row of the table, write the correction in the notes of any answer.`
   - Never ask about a `stated` force.
   - **Cannot be asked:** keep every label as it is. Print `(AskUserQuestion is not available; the forces keep their labels.)` and continue.
4. **Correct.** Each answered force becomes `stated` with the chosen value. Each row corrected in the notes becomes `stated` with the corrected value.
5. **Record.** Every force still `assumed` goes on the "Open for brainstorming" list for step 9.

### 2. Collapse gate (D4)

Make **one** candidate (shape A only) when all of these hold:

- force 1: peak load fits on one server (under 50 requests/s),
- force 3: no latency target, or a target of 1 s or more,
- force 4: no availability target, or downtime of an hour or more per month is acceptable,
- force 7: one developer,
- force 10: does not require more than one data store or deployable.

If any of forces 1, 3, 4, 7 or 10 is still `assumed`, the gate does not collapse. Make three candidates. The choice between one and three must not rest on an invented value.

Otherwise make three candidates.

Record the result as `One candidate.` or `Three candidates.`, with the force values that decided it. Then write one skip line for every menu shape (step 3) that is not used: the shape name and the force value that would have justified it. Do not show the gate result to the user yet; step 7 does that.

### 3. Shapes and contrast (D5)

**Shape A** is always used: the simplest design that could meet the forces — one deployable process, one data store, synchronous calls.

With three candidates, pick **two more** shapes from this menu. For each, write a one-line reason that names a force.

Starting axis values for each shape. Adjust them to this system before the check:

| Shape | Deployable processes | Data ownership | Communication | Computation runs on |
|---|---|---|---|---|
| A: simplest design | one | one store shared by all components | sync | server |
| queue and background workers | two or more (app + workers) | one store | async to workers | server + worker |
| event-driven | two or more | each consumer keeps its own view | async events | server + workers |
| separate deployables, each owning its own data | two or more | each deployable owns its own store | sync or async between deployables | server |
| pipeline or batch processing | two or more (app + jobs) | each stage owns its output | async, staged | worker |
| client-heavy or offline-first | server + client | client holds a local copy | async sync-up | client |
| managed or serverless services | many functions or managed services | managed stores | sync + async | managed runtime |

**Contrast rule.** Each pair of candidates must differ on at least two of the four axes. Check the pairs A–B, A–C and B–C before dispatch:

- If a pair fails, replace the later shape with the next menu shape, in table order, that is not already used and passes against both others.
- If no menu shape passes, dispatch anyway. Label the pair `contrast rule not met` for the brief.

### 4. Dispatch the candidates (D5–D7)

Read `candidate-prompt.md` from this skill's directory. Take everything below the first `---` line. For each candidate, substitute:

- `{{CANDIDATE_LETTER}}` → `A`, `B` or `C`.
- `{{SHAPE}}` → the shape name. `{{SHAPE_REASON}}` → its one-line reason (for A: `Always included: the simplest design that could meet the forces.`).
- `{{DESCRIPTION}}` → `DESCRIPTION`, word for word.
- `{{REPO_ROOT}}` → `REPO_ROOT`. It must be absolute: subagents do not reliably inherit the session's working directory.
- `{{FORCES_TABLE}}` → the table after step 1, with labels.

Dispatch all candidates **in one message**, so they run in parallel. Use the Agent tool with `subagent_type: "general-purpose"`, `model: "opus"`, `description: "Architecture candidate <letter>"`, and the composed prompt. Do not run them in the background.

**Failure.** A subagent that errors, times out or returns empty text is dispatched once more, alone. If it fails again, continue without it and record `Candidate <letter> missing: <error>` for the brief. If no candidate is left, stop. Print each error. Write no brief.

Save each returned text, unchanged, with `Write` to `WORK_DIR/candidate-<letter lowercase>.md`.

### 5. Check the drafts (D5–D6)

**Schema.** A draft must have exactly these headings, in order: `### Summary`, `### Components`, `### Connections`, `### Forces`, `### Hard-to-reverse decisions`, `### Numbers it depends on`, `### Weakest point`.

- A draft missing a heading is labelled `malformed: missing <names>`. It still takes part in evaluation.
- A draft missing `### Components` or `### Connections` is **excluded** from step 6 and from the choice. It is kept in the appendix only.

**Contrast after return.** For each pair of drafts, read the four axis values from the drafts themselves: process count and computation from the Components "Runs as" column, data ownership from "Owns", sync or async from Connections. A pair that differs on fewer than two axes labels the later draft `near-copy of candidate <X>`. Do not drop it. Do not regenerate it.

If the gate made three candidates but only one draft is left to evaluate, step 7 uses its one-candidate case.

### 6. Evaluate (D8)

Run on every candidate that is not excluded. With one candidate, run on that one.

- **Data ownership.** Merge the "Owns" columns. Flag every piece of state with zero owners or more than one owner.
- **Scenarios.** Use 4 to 6:
  - the normal path at peak load (force 1),
  - failure of each external dependency (force 4),
  - the most frequent change (force 8),
  - data volume after 3 years (force 2),
  - one abuse or security case, when force 6 is not "none".

  Trace each scenario step by step through the Connections table. Record the step where it breaks, or `holds`.
- **Pre-mortem.** Assume the design failed one year after launch. Write the three most likely causes for each candidate.
- **Comparison.** A table with forces as rows and candidates as columns. Each cell is `meets`, `partial` or `fails`, with a reason.

### 7. Choose (D8)

State a recommendation with reasons. Then:

- **Two or more candidates:** one `AskUserQuestion` question, header `Candidate`, one option per candidate, the recommended one first with `(Recommended)` in its label.
- **One candidate** (the gate collapsed, or only one survived steps 4–5): print the gate result and its force values. Ask `Accept candidate A, or make three candidates?` with options `Accept (Recommended)` and `Make three`. On `Make three`, record `Gate overridden by the user`, go back to step 3 with three shapes, and repeat steps 3–7. This is the only override of the gate, and it is offered once.
- **Cannot be asked:** take the recommended candidate. Write `chosen without the user` in the brief's Decision section. Add `Candidate choice: <letter> was chosen without the user.` to the "Open for brainstorming" list.

For each rejected candidate, record why it lost.

### 8. Reversibility and checks (D9)

Chosen design only.

1. List each decision from its "Hard-to-reverse decisions" section and its Components table. Label each:
   - `hard` — data model, storage engine, public API or data format, process boundaries, vendor lock-in,
   - `medium` — internal module boundaries, library choice behind an interface,
   - `cheap` — everything else.
2. For each `hard` decision that depends on a load, storage, cost or latency number: write `WORK_DIR/estimate-<n>-<short-name>.py`. Python 3 standard library only. It prints its inputs (from the forces and "Numbers it depends on"), the formula, the estimate, and the capacity or budget it is compared to. Run it with `python3 <path>`. Copy the script and its printed output into the brief.
3. A `hard` decision with no such number gets no script. Write `no quantity to check` and one line of reason.
4. **Near a limit** means the estimate is within a factor of 2 of a known capacity or budget. When a decision is near a limit, or depends on an `assumed` force, propose a spike in 2–3 sentences: the question and what the spike will try. Ask with `AskUserQuestion`: options `Run the spike` and `Skip`.
   - **Approved:** write the spike code under `WORK_DIR/spike-<n>/`. Its first line is a comment: `THROWAWAY SPIKE — never commit`. Run it. Put only the result in the brief. Never copy spike code into the repo.
   - **Skipped, or cannot be asked:** record `spike proposed, not run` with the proposal, and add the spike's question to the "Open for brainstorming" list.

### 9. Write and commit the brief (D10)

Write `BRIEF_PATH` with exactly these `##` sections, in this order. Nothing else at `##` level.

````markdown
# Architecture brief: <system name>

## How to read this brief

[Related documents with paths, in reading order: this brief, the description source if it is a file, repo files the forces were inferred from. The spec written next lists this brief first in its own "How to read this spec".]

## Forces

| # | Force | Value | Label | Source or reason |
|---|---|---|---|---|
| 1 | Load | … | stated / inferred / assumed | … |

[All 10 rows, final labels after step 1.]

## Collapse gate

[`One candidate.` or `Three candidates.` with the deciding force values. `Gate overridden by the user` if it was. One skip line per unused menu shape: the shape and the force value that would have justified it.]

## Candidates

### Candidate A: <shape>

**Reason:** [one line naming a force]
**Contrast:** [vs B: axes that differ; vs C: axes that differ — or `contrast rule not met`]
**Labels:** [`near-copy of candidate X`, `malformed: missing …`, `excluded`, or `none`]

[Its Summary, Components table and Connections table, with headings demoted to `####`.]

[Repeat per candidate. A missing candidate gets `Candidate <letter> missing: <error>`.]

## Evaluation

### Data ownership

### Scenarios

### Pre-mortem

### Comparison

## Decision

[The chosen candidate and why. `chosen without the user` when step 7 could not ask. One line per rejected candidate: why it lost.]

## Reversibility and checks

| Decision | Label | Check |
|---|---|---|

[For each script: the script in a ```python block and its output in a ```text block. `no quantity to check` lines. Spike results, or `spike proposed, not run`.]

## Open for brainstorming

- [Every force still `assumed`, by number and name, for example `Force 9 (cost): unknown, assumed …`.]
- [Every unresolved question: a choice made without the user, a spike not run.]

[Brainstorming may ask only about these items. Write `None.` if the list is empty.]

## Appendix: candidate drafts

### Candidate A

[The full draft from `WORK_DIR/candidate-a.md`, headings demoted to `####`.]
````

Then commit only the brief:

```bash
git add <BRIEF_PATH> && git commit -m "docs(plans): add architecture brief for <SLUG>" -- <BRIEF_PATH>
```

If `REPO_ROOT` is `none`, skip the commit and print `(No git repository: the brief is written but not committed.)`.

Finally print:

```text
Architecture brief written to <BRIEF_PATH>.
Next: invoke superpowers:brainstorming with <BRIEF_PATH> as input.
```

## Worked example

```text
0. Args: "An order and seat-inventory service …" → DESCRIPTION. SLUG=ticket-inventory.
   git rev-parse --show-toplevel → /home/u/tix → REPO_ROOT. BRIEF_PATH=docs/plans/2026-09-17-ticket-inventory-architecture.md (free).
   WORK_DIR=<scratchpad>/architect/ticket-inventory; mkdir -p.
1. Draft 10 forces: 1–8 and 10 stated, 9 assumed. Print table.
   Ask list = [9]. AskUserQuestion is absent → "(AskUserQuestion is not available; the forces keep their labels.)"
   Open list = [Force 9 (cost)].
2. Gate: force 1 = 2,000 writes/s ≥ 50 → Three candidates.
3. A: simplest. B: queue and background workers (force 1 peak writes). C: event-driven (force 5 reports may lag).
   B–C: same process count, same sync/async, same computation → fails. Replace C with separate deployables → passes.
   Skip lines for event-driven, pipeline, client-heavy, serverless.
4. One message, three Agent calls (general-purpose, opus). B errors → re-dispatch B alone → ok. Save candidate-{a,b,c}.md.
5. All 7 headings present. After-return contrast: all pairs pass.
6. Ownership, 5 scenarios, pre-mortem, comparison.
7. Recommend B. AskUserQuestion absent → take B, "chosen without the user", add to Open list.
8. Hard: seat table in PostgreSQL → estimate-1-seat-writes.py → 2,000 writes/s vs ~3,000 capacity → near limit → spike proposed.
   AskUserQuestion absent → "spike proposed, not run", question added to Open list.
9. Write the brief (9 sections). git commit -- BRIEF_PATH. Print the two lines.
```
`````

- [ ] **Step 3: Green — small fixture**

```bash
FX="$SCRATCH/fx/small"; LOG="$SCRATCH/green/small.jsonl"
cd "$FX" && claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits \
  --allowedTools "Bash(git:*)" "Bash(python3:*)" "Bash(mkdir:*)" "Bash(mktemp:*)" "Bash(date:*)" "Bash(ls:*)" \
  --max-budget-usd 20 --output-format stream-json --verbose \
  "Run my:architect $SCRATCH/fixtures/small.md" > "$LOG"
BRIEF=$(ls "$FX"/docs/plans/*-architecture.md); echo "$BRIEF"                  # exactly one path
git -C "$FX" log --oneline -1                                                  # docs(plans): add architecture brief for …
git -C "$FX" status --short                                                    # empty
grep -o '"skill":"my:architect"' "$LOG" | head -1                             # present
grep -o '"subagent_type":"general-purpose"' "$LOG" | wc -l                    # 1 (2 only if the brief names a retry)
grep -c 'Next: invoke superpowers:brainstorming' "$LOG"                       # ≥ 1
python3 "$SCRATCH/check_brief.py" "$BRIEF" small                              # PASS
```

The checker covers four spec pass conditions: one candidate, a skip reason for each of the 6 shapes, "chosen without the user" in Decision, and all 9 sections with no plan-format sections. Also read the brief once in full. The checks prove structure, not quality.

If a check fails, rerun once (model output varies). If it fails twice, fix `SKILL.md` or `candidate-prompt.md`, not the checker. Before a rerun, reset the fixture repo: `rm -rf "$FX/docs" && git -C "$FX" reset -q --hard HEAD~1`, only when the last commit is the brief commit.

- [ ] **Step 4: Lint**

Run: `markdownlint-cli2 "my-plugin/skills/architect/*.md" 2>&1 | grep error | grep -v -E 'MD013|MD060'` from `$WT`.
Expected: no output.

- [ ] **Step 5: Commit**

```bash
cd "$WT" && git status --short    # only my-plugin/skills/architect/
git add my-plugin/skills/architect
git commit -m "feat(my-plugin): add my:architect forces-first architecture skill

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Green on the large fixture

**Files:**

- Modify (only if a check fails): `my-plugin/skills/architect/SKILL.md`, `my-plugin/skills/architect/candidate-prompt.md`

**Interfaces:**

- Consumes: the skill from Task 2; `$SCRATCH/fixtures/large.md`, `$SCRATCH/fx/large`, the checker.
- Produces: the large-fixture session ID and brief path, used by the handoff test in Task 5.

- [ ] **Step 1: Run**

```bash
FX="$SCRATCH/fx/large"; LOG="$SCRATCH/green/large.jsonl"
cd "$FX" && claude -p --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits \
  --allowedTools "Bash(git:*)" "Bash(python3:*)" "Bash(mkdir:*)" "Bash(mktemp:*)" "Bash(date:*)" "Bash(ls:*)" \
  --max-budget-usd 20 --output-format stream-json --verbose \
  "Run my:architect $SCRATCH/fixtures/large.md" > "$LOG"
grep -o '"session_id":"[^"]*"' "$LOG" | head -1 | cut -d'"' -f4 > "$SCRATCH/green/large-session.txt"
```

- [ ] **Step 2: Check**

```bash
BRIEF=$(ls "$FX"/docs/plans/*-architecture.md); echo "$BRIEF"
git -C "$FX" log --oneline -1                                                   # docs(plans): add architecture brief for …
python3 "$SCRATCH/check_brief.py" "$BRIEF" large                               # PASS
# three drafts with all D6 sections
DRAFTS=$(grep -o '/[^"]*/architect/[a-z0-9-]*/candidate-[abc]\.md' "$LOG" | sort -u); echo "$DRAFTS"   # 3 paths
for d in $DRAFTS; do python3 "$SCRATCH/check_brief.py" --draft "$d"; done      # PASS ×3
# contrast rule held, or a label says otherwise
grep -n -E '^\*\*Contrast:\*\*|near-copy of candidate|contrast rule not met' "$BRIEF"   # one Contrast line per candidate
# at least one estimate script ran
grep -o '"command":"[^"]*python3 [^"]*"' "$LOG" | head                          # ≥ 1 line
grep -c -E '^`{3}python' "$BRIEF"                                               # ≥ 1
# force 9 stayed assumed and reached Open for brainstorming (the checker also tests this)
grep -n -i 'force 9' "$BRIEF"                                                   # in Forces and in Open for brainstorming
```

Expected: every comment holds. The checker covers "every force has a label", "Open for brainstorming lists every `assumed` force" and "three candidates". Read the Candidates section: for each pair, the Contrast line names at least two differing axes, or a near-copy label is present. Read the whole brief once.

If a check fails, rerun once. If it fails twice, fix the skill files, rerun, then amend the Task 2 commit (`git commit --amend --no-edit` after `git add my-plugin/skills/architect`). Before a rerun, reset the fixture repo as in Task 2 Step 3.

No new commit unless the skill files changed.

---

### Task 4: `GLOBAL-CLAUDE.md` wiring and the ROADMAP row

**Files:**

- Modify: `GLOBAL-CLAUDE.md` — trigger table in "Superpowers Integration", the "Discovery authority" paragraph, step 1 of "Spec → Plan two-artifact flow"
- Modify: `ROADMAP.md`

**Interfaces:**

- Consumes: skill name `my:architect`; brief section name `Open for brainstorming`; brief file pattern `docs/plans/*-architecture.md`.
- Produces: the handoff text the Task 5 brainstorming run is tested against.

- [ ] **Step 1: Red**

```bash
grep -c 'my:architect' "$WT/GLOBAL-CLAUDE.md"     # 0
grep -c 'my:architect' "$WT/ROADMAP.md"           # 0
```

- [ ] **Step 2: Add the trigger row**

In the table under "Superpowers Integration", insert directly above the row that starts `| New feature, component, or behavior change`:

```markdown
| New project, new subsystem, or change to a data model, storage choice or public contract | `my:architect`, then `superpowers:brainstorming` |
```

- [ ] **Step 3: Replace the "Discovery authority" paragraph**

Old (one line; it ends with a trailing space):

```markdown
**Discovery authority:** while `superpowers:brainstorming` or `writing-plans` runs, it owns exploration — don't also run other planning workflows. 
```

New:

```markdown
**Discovery authority:** while `superpowers:brainstorming` or `writing-plans` runs, it owns exploration — don't also run other planning workflows. `my:architect` runs before brainstorming, never during it. When an architecture brief (`docs/plans/*-architecture.md`) exists for the task:

- Brainstorming treats the brief as settled input. It asks only about items under the brief's "Open for brainstorming" section.
- The brief's Decision replaces brainstorming's "Propose 2-3 approaches" step. Brainstorming presents its design sections starting from that Decision.
- Brainstorming classifies the task as architectural, never bounded or spike.

If brainstorming upgrades a task to architectural partway through, and the task matches the `my:architect` trigger row, stop and run `my:architect` first.
```

- [ ] **Step 4: Edit Spec → Plan step 1**

In step 1 of "Spec → Plan two-artifact flow", replace:

```markdown
First section is **"How to read this spec"** — all related docs (specs, plans, ROADMAP, CHANGELOG, sources, skills) with paths, in reading order.
```

with:

```markdown
First section is **"How to read this spec"** — all related docs (specs, plans, ROADMAP, CHANGELOG, sources, skills) with paths, in reading order. When an architecture brief exists, it is listed first.
```

- [ ] **Step 5: Green for `GLOBAL-CLAUDE.md`**

```bash
grep -c 'my:architect' "$WT/GLOBAL-CLAUDE.md"                        # 3
grep -n 'Open for brainstorming' "$WT/GLOBAL-CLAUDE.md"               # 1 line
grep -n 'never bounded or spike' "$WT/GLOBAL-CLAUDE.md"               # 1 line
grep -n 'When an architecture brief exists, it is listed first' "$WT/GLOBAL-CLAUDE.md"   # 1 line
awk '/^\| New project, new subsystem/{a=NR} /^\| New feature, component/{b=NR} END{print (a && b==a+1) ? "order ok" : "order wrong"}' "$WT/GLOBAL-CLAUDE.md"   # order ok
```

- [ ] **Step 6: ROADMAP row**

Invoke `my:roadmap-management` to add a row. Suggested content, status 🚧 while the branch is open:

```markdown
- 🚧 **`my:architect`** — forces-first architecture brief before brainstorming:
  labelled forces, collapse gate, parallel candidates, evaluation and estimate
  scripts. Spec:
  [`docs/plans/2026-09-17-architect-skill-spec.md`](docs/plans/2026-09-17-architect-skill-spec.md).
```

The skill decides the section. Promotion to ✅ happens in Task 5 after the merge. The repo has no `CHANGELOG.md`, so there is no changelog half.

- [ ] **Step 7: Lint and commit**

```bash
cd "$WT" && markdownlint-cli2 GLOBAL-CLAUDE.md ROADMAP.md 2>&1 | grep error | grep -v -E 'MD013|MD060'   # no new errors versus main
git add GLOBAL-CLAUDE.md ROADMAP.md
git commit -m "docs(global): run my:architect before brainstorming for new systems

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

If the lint shows errors, run the same lint in the main checkout (`/home/dchris/projects/claude-setup`). Fix only the errors that do not appear there.

---

### Task 5: Handoff test, manual test, integrate

- [ ] **Step 1: Handoff — continue the large-fixture run into brainstorming**

The headless session reads `~/.claude/CLAUDE.md`, which still has the old text until merge. So the new `GLOBAL-CLAUDE.md` is appended to the system prompt. The old "Discovery authority" line is a subset of the new one, so the two do not conflict.

```bash
FX="$SCRATCH/fx/large"; LOG="$SCRATCH/green/handoff.jsonl"
BRIEF_REL=$(cd "$FX" && ls docs/plans/*-architecture.md)
cd "$FX" && claude -p --resume "$(cat "$SCRATCH/green/large-session.txt")" \
  --plugin-dir "$WT/my-plugin" --permission-mode acceptEdits --max-budget-usd 10 \
  --append-system-prompt "$(cat "$WT/GLOBAL-CLAUDE.md")" \
  --output-format stream-json --verbose \
  "Invoke superpowers:brainstorming with $BRIEF_REL as input. This is a headless run: when you would ask a question, write it and stop. Do not write the spec yet." > "$LOG"
grep -o '"skill":"superpowers:brainstorming"' "$LOG" | head -1    # present
tail -1 "$LOG" | grep -o '"result":"[^"]*"' > "$SCRATCH/green/handoff-result.txt"
grep -i -o -E 'architectural|bounded|spike' "$SCRATCH/green/handoff-result.txt" | sort | uniq -c
```

Read `handoff-result.txt` and the assistant text in the log. Record in `$SCRATCH/green/handoff-notes.md`:

1. **Path.** It names the architectural path, and does not pick bounded or spike. (Pass: architectural.)
2. **No re-asked forces.** Count questions about forces 1–8 or 10, which are `stated` in the brief. (Pass: 0.) Questions about force 9 (cost), the candidate choice or the spike are allowed.
3. **No new approaches.** It does not propose 2–3 new approaches. It starts its design from the brief's Decision. (Pass: no new approach list.)

If a check fails, rerun once. If it fails twice, strengthen the "Discovery authority" wording in `GLOBAL-CLAUDE.md`, amend the Task 4 commit, and rerun. Never edit brainstorming (spec Risk 2).

- [ ] **Step 2: Manual test — ask the user**

`AskUserQuestion` works only in an interactive session. Ask the user to run this in a separate terminal, then report back:

```bash
cd "$SCRATCH/fx/manual" && claude --plugin-dir "$WT/my-plugin"
# then type:  Run my:architect <SCRATCH>/fixtures/manual.md
```

Expected, in order:

1. The forces table shows forces 1–3 `stated` and the rest `assumed` or `inferred`.
2. **One** `AskUserQuestion` call with 4 questions, on forces 4, 7, 5 and 10, in that order. The first question mentions corrections in the notes. The user answers with small values (for example 1 hour downtime acceptable, 1 developer), and writes a correction for force 8 in a note.
3. If the gate collapses: the one-candidate question `Accept candidate A, or make three candidates?` appears. The user picks `Make three`. Three candidates are then dispatched, and a candidate-choice question appears.
4. If a spike is proposed, an approval question appears with `Run the spike` and `Skip`. The user picks `Skip`.
5. The brief: force 8 is `stated`; forces 6 and 9 are `assumed` and appear under "Open for brainstorming"; Collapse gate says `Gate overridden by the user`; the Decision does **not** say "chosen without the user"; a skipped spike says `spike proposed, not run`.

Then run `python3 "$SCRATCH/check_brief.py" <brief> large` on the brief. It fails only on "chosen without the user", which is correct for an interactive run. Record the results in `$SCRATCH/green/manual-notes.md`. If an item fails, fix the skill, amend the Task 2 commit, and repeat this step.

- [ ] **Step 3: Final lint over all changed files**

Run: `git -C "$WT" diff --name-only main... | grep '\.md$' | (cd "$WT" && xargs markdownlint-cli2) 2>&1 | grep error | grep -v -E 'MD013|MD060'`
Expected: no errors that are not also present on `main`.

- [ ] **Step 4: Integrate**

Invoke `superpowers:finishing-a-development-branch`, overridden by `GLOBAL-CLAUDE.md`:

```bash
cd /home/dchris/projects/claude-setup && git status --short   # empty
git merge --squash feat/architect-skill
git commit -m "feat(my-plugin): add my:architect and run it before brainstorming

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
git worktree remove "$WT"
```

Do not delete the branch.

- [ ] **Step 5: Post-merge**

- `grep -c 'my:architect' ~/.claude/CLAUDE.md` → `3`. The symlink now resolves to the new text.
- Invoke `my:roadmap-management` to promote the row to ✅ with the squash commit SHA. Commit it.
- The running session still has the old plugin loaded. A new `claude` session picks up the skill.

---

## Dependencies

- No new packages.
- `python3` on `PATH` (checked: `/usr/bin/python3`). Standard library only.
- `claude` CLI with `-p`, `--plugin-dir`, `--permission-mode`, `--allowedTools`, `--max-budget-usd`, `--resume`, `--append-system-prompt`, `--output-format stream-json` (checked with `claude --help` on 2026-09-17).
- `markdownlint-cli2` (checked on `PATH`).
- Agent tool accepting `model: "opus"` for `general-purpose` — confirmed in Task 1 Step 1; no repo precedent (`my-plugin/skills/clean-plans/SKILL.md` and `my-plugin/skills/tune-claude-instructions/SKILL.md` use `haiku`).
- `AskUserQuestion` schema: 1–4 questions per call, 2–4 options per question. So the D8 one-candidate question (2 options) and the D3 call (up to 4 questions) fit.
- `superpowers:brainstorming` 6.3.0, unchanged.
- Task order is fixed: Task 3 uses the Task 2 skill; Task 5 Step 1 uses the Task 3 session and the Task 4 text.

## Risk

- **Headless runs cost money and time.** At least: Red 2 runs, small 1, large 1 (4 Opus agents: evaluation plus 3 candidates), handoff 1, preflight 2. Reruns on failure add more. `--max-budget-usd` caps each run.
- **Checks are structural.** The checker and greps prove sections, labels and tool calls, not design quality. Mitigation: read each brief in full (Task 2 Step 3, Task 3 Step 2).
- **Model output varies between runs.** Rerun once before editing; fix the skill after a second failure.
- **Test briefs leak into the branch.** Prevented by running every test inside `$SCRATCH/fx/*` repos, never in `$WT`. Guard: `git -C "$WT" status --short` before each commit shows only the task's files.
- **Handoff test uses an appended system prompt**, not the real `~/.claude/CLAUDE.md`. The two texts overlap. A pass here is strong evidence, not proof. The post-merge session is the real check; Risk 2 of the spec covers the follow-up.
- **The manual test needs the user.** It cannot be automated because `AskUserQuestion` is absent headless. The plan stops and asks at Task 5 Step 2.
- **Blast radius of the `GLOBAL-CLAUDE.md` edit:** every project, because `~/.claude/CLAUDE.md` links to it. It changes when brainstorming starts and what it asks. Reversible by reverting the squash commit. The branch is kept.

## Self-review against the spec

| Spec item | Task |
|---|---|
| D1 brief before brainstorming, skill does not write the spec | Task 2 Step 2 (intro, step 9 last lines); handoff Task 5 Step 1 |
| D2 trigger | Task 2 Step 2 (description); Task 4 Step 2 |
| D3 forces, labels, one call of ≤4, priority order, corrections, record, cannot-be-asked | Task 2 Step 2 (step 1); Task 3 (force 9); Task 5 Step 2 |
| D4 collapse gate, `assumed` gate force blocks it, skip lines, shown at choice | Task 2 Step 2 (step 2, step 7); Task 2 Step 3; Task 3 |
| D5 shape A, two menu shapes with reasons, contrast before and after | Task 2 Step 2 (steps 3, 5); Task 3 Step 2 |
| D6 schema, malformed, exclusion, subagent failure and retry | Task 2 Steps 1–2 (steps 4, 5); Task 3 Step 2 |
| D7 `general-purpose` + `opus`, prompt inputs, absolute root, scratch drafts, search wording | Task 1 Step 1; Task 2 Steps 1–2 (steps 0, 4) |
| D8 ownership, scenarios, pre-mortem, comparison, choice incl. one-candidate and cannot-be-asked | Task 2 Step 2 (steps 6, 7); Tasks 2–3 checker; Task 5 Step 2 |
| D9 reversibility labels, estimate scripts, no-quantity line, near-limit spike, approval, not-run | Task 2 Step 2 (step 8); Task 3 Step 2; Task 5 Step 2 |
| D10 brief path, 9 sections, not the plan format, commit, handoff print | Task 2 Step 2 (steps 0, 9); checker in Tasks 2–3 |
| D11 trigger row, Discovery authority rules, Spec → Plan step 1 | Task 4 Steps 2–5 |
| ROADMAP row | Task 4 Step 6; Task 5 Step 5 |
| Orphan-plan hook | No change: a committed brief matches `^[0-9]{4}-[0-9]{2}-[0-9]{2}-` (`my-plugin/hooks/check-orphan-plans.sh:28`) |
| Testing: Red baseline, small, large, handoff, manual | Task 1 Step 8; Task 2 Step 3; Task 3; Task 5 Steps 1–2 |
