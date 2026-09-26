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
   - Otherwise make **one** `AskUserQuestion` call with one question per chosen force. Header: `Force <n>`. Each question offers 2–4 concrete ranges as options, for example for force 1: `Under 5 req/s`, `5–50 req/s`, `50–500 req/s`, `Over 500 req/s`. Build the options from the description and the repo. Never copy a value from the "Example value" column above. Name a concrete product, framework or vendor in an option **only** when the description or the repo names it. Otherwise keep the options shape-level, for example `one server, one database`, `managed cloud`, `nothing fixed`. The first question's text ends with: `To correct any other row of the table, choose "Type something" on any question, write your answer, then the correction.`
   - Never ask about a `stated` force.
   - **Cannot be asked:** keep every label as it is. Print `(AskUserQuestion is not available; the forces keep their labels.)` and continue.
4. **Correct.** Each answered force becomes `stated` with the chosen value. Each row corrected in a typed answer becomes `stated` with the corrected value; its source is `user correction, typed with the force <n> answer`.
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

Read `candidate-prompt.md` from this skill's directory. If the read fails or is denied, stop. Print `Cannot read <path>: <error>` and write no brief. Never write a candidate prompt of your own. Take everything below the first `---` line. For each candidate, substitute:

- `{{CANDIDATE_LETTER}}` → `A`, `B` or `C`.
- `{{SHAPE}}` → the shape name. `{{SHAPE_REASON}}` → its one-line reason (for A: `Always included: the simplest design that could meet the forces.`).
- `{{DESCRIPTION}}` → `DESCRIPTION`, word for word.
- `{{REPO_ROOT}}` → `REPO_ROOT`. It must be absolute: subagents do not reliably inherit the session's working directory.
- `{{FORCES_TABLE}}` → the table after step 1, with labels.

Dispatch all candidates **in one message**, so they run in parallel. Use the Agent tool with `subagent_type: "general-purpose"`, `model: "opus"`, `description: "Architecture candidate <letter>"`, and the composed prompt. Wait until every candidate has returned before step 5, and do nothing else meanwhile. If your Agent tool has a `run_in_background` parameter, leave it off; if subagents always run in the background, continue when the last completion notice arrives.

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
4. **Near a limit** means the estimate is within a factor of 2 of a known capacity or budget. When a decision is near a limit, or depends on an `assumed` force, propose a spike in 2–3 sentences: the question and what the spike will try.
   - **Only a testable question gets a spike.** If no experiment can answer it (for example, an assumed budget), do not propose a spike and do not ask. Add the question to the "Open for brainstorming" list.
   - Ask with `AskUserQuestion`. The question text is `Run this spike: <what it does>?`. The options are `Run the spike` and `Skip`.
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
