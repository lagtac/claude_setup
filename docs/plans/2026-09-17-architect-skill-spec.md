# Spec: `my:architect` — design an architecture from forces before the spec

## How to read this spec

| Document | Path | Why you would read it |
|---|---|---|
| **This spec** | `docs/plans/2026-09-17-architect-skill-spec.md` | What to build, why, and the trade-offs. Start here. |
| Implementation plan | `docs/plans/2026-09-17-architect-skill.md` | Written after this spec is approved. Test steps and commit breakdown. |
| Global instructions | `GLOBAL-CLAUDE.md` | The Superpowers trigger table, the "Discovery authority" paragraph and the "Spec → Plan two-artifact flow" section, all under "Superpowers Integration". All three change. |
| Existing skill to copy from | `my-plugin/skills/spec-review/SKILL.md` | Model for the step layout, the absolute-path rule for subagents, and the worked example. |
| Existing agent wording | `my-plugin/agents/spec-reviewer.md` | Source of the search-tool wording copied into the candidate prompt ("Contract with the Calling Skill", the grounding bullet). |
| Test precedent | `docs/plans/2026-09-16-spec-review-skill.md` | "How tests run": headless `claude -p --plugin-dir` runs against a worktree plugin, with fixture inputs in the scratchpad. |
| Orphan-plan hook | `my-plugin/hooks/check-orphan-plans.sh` | Confirms a committed `YYYY-MM-DD-<slug>-architecture.md` does not trigger a warning. |
| Roadmap | `ROADMAP.md` | Gets a new row for this skill. |
| Superpowers brainstorming | `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/brainstorming/SKILL.md` | The skill that runs after this one and writes the spec. Not edited. |

## Context

Today a new system is designed inside `superpowers:brainstorming`. Brainstorming asks clarifying questions one at a time, proposes 2–3 approaches, and writes a spec. For new projects and new subsystems this has four weak points:

1. **Requirements are filled in silently.** A description rarely states load, latency, availability, consistency or team size. The agent assumes values without showing them.
2. **The common answer wins.** The agent proposes what appears most often in its training data. Its 2–3 approaches are often small variations of one idea, because one agent writes all of them in sequence.
3. **No structured evaluation.** Nothing checks who owns each piece of state, walks concrete scenarios through the design, or asks how the design would fail.
4. **No numbers before hard-to-reverse choices.** A claim like "MySQL will handle this" is not backed by an estimate.

`my:spec-review` (`my-plugin/skills/spec-review/SKILL.md`) catches some of these problems *after* the spec is written. By then the structure is already chosen. This skill works *before* the spec.

## Goal

A skill, `my:architect`, that turns a description into an **architecture brief**. The brief records the forces, the candidates, how they were evaluated, the chosen design, and the checks behind it. `superpowers:brainstorming` then reads the brief and writes the spec.

## Decisions

**D1 — Runs before brainstorming and hands off a brief.** The skill does not write the spec. It writes `docs/plans/YYYY-MM-DD-<slug>-architecture.md` and commits it. Brainstorming then runs as usual, treats the brief as settled input, and asks only about items the brief lists under "Open for brainstorming".

Rejected: running inside brainstorming. That depends on a third-party skill following an extra instruction at one of its steps, which is unreliable. Rejected: replacing brainstorming for new systems. That would copy brainstorming's spec-writing duties into this skill.

**D2 — Trigger.** Required for:

- a new project,
- a new subsystem,
- a change to a data model, a storage choice or a public contract (an API or data format other code depends on).

It also runs whenever the user asks. Other features go straight to brainstorming.

Rejected: only on request (easy to forget for the work that needs it most). Rejected: every architectural path (brainstorming classifies the path, so the order would be backwards).

**D3 — Forces first.** The skill fills a fixed list of 10 forces before any design work. Each value carries exactly one label:

- `stated` — the user said it,
- `inferred` — taken from a named source, for example `composer.json`,
- `assumed` — not confirmed. The value is written as "unknown, assumed X", with a reason.

| # | Force | Example value |
|---|---|---|
| 1 | Load | 200 users, 5 requests/s at peak |
| 2 | Data volume and growth | 50 GB now, +10 GB per year |
| 3 | Latency target | page under 500 ms at p95 (95% of requests) |
| 4 | Availability | 1 hour of downtime per month is acceptable |
| 5 | Consistency | payments exact immediately; counts may lag 1 minute |
| 6 | Security and compliance | personal health data, GDPR applies |
| 7 | Team and operations | 1 developer, no on-call rotation |
| 8 | Rate of change | import rules change monthly; core model rarely |
| 9 | Cost | under €50/month hosting |
| 10 | Fixed constraints | must use Laravel and MySQL; one VPS |

The steps:

1. **Draft.** Read the description and, when a repo exists, the repo. Fill every force with a value and a label. A force with no evidence is `assumed`.
2. **Show.** Print the whole table in chat.
3. **Ask.** Make one `AskUserQuestion` call with at most 4 questions. Choose from `assumed` and `inferred` forces, in this priority order: 5, 1, 4, 7, 10, then the rest by number. Each question offers concrete ranges as options. A force already `stated` is never asked about.
4. **Correct.** The user may correct any row in free text before the skill continues. Answered and corrected forces become `stated`.
5. **Record.** Every force still `assumed` after step 4 is copied to "Open for brainstorming" in the brief.

One call with up to 4 questions is used instead of one question per message. The forces are closely linked and quick to answer, and ten separate messages would push the user to skip the step. Brainstorming's one-question rule still applies inside brainstorming.

**D4 — Collapse gate.** After D3, the skill decides how many candidates to make. It makes **one** candidate (shape A in D5) when all of these hold:

- force 1: peak load fits on one server (under 50 requests/s),
- force 3: no latency target, or a target of 1 s or more,
- force 4: no availability target, or downtime of an hour or more per month is acceptable,
- force 7: one developer,
- force 10: does not require more than one data store or deployable.

The gate judges the recorded value of each force, whatever its label. An `assumed` value is written down in D3, so it can be judged like any other. For each shape it skipped, the skill writes one line naming the force value that would have justified it. Otherwise it makes three candidates.

Reason: requiring three designs for a small tool invents complexity and gives it false standing in a comparison. This follows the Simplicity Rules in `GLOBAL-CLAUDE.md`.

**D5 — Three candidates from parallel subagents.** Each candidate is made by its own subagent. The subagents cannot see each other's output, so they do not copy each other.

- **Shape A is always included:** the simplest design that could meet the forces. It has one deployable process, one data store, and synchronous calls.
- The skill picks **two more shapes** from this menu. For each, it writes a one-line reason that names a force:
  - queue and background workers
  - event-driven (components react to published events)
  - separate deployables, each owning its own data
  - pipeline or batch processing
  - client-heavy or offline-first
  - managed or serverless services
- **Contrast rule.** Each pair of candidates must differ on at least two of these axes:
  - how many deployable processes there are,
  - who owns each piece of data,
  - synchronous versus asynchronous communication,
  - where computation runs (server, worker, client).

  The skill checks the rule on the chosen shapes before dispatch, and on the returned drafts after. A draft that fails the check is labelled "near-copy of candidate X" in the brief. It is not dropped and not regenerated.

**D6 — Fixed candidate schema.** Every subagent returns markdown with exactly these sections, in order, in about 800 words:

1. `### Summary` — shape name and at most 5 sentences.
2. `### Components` — table: Component | Job | Owns (state) | Runs as.
3. `### Connections` — table: From → To | What passes | Sync / async | When the receiver fails.
4. `### Forces` — two lists, "Served" and "Sacrificed", each item a force number with a reason.
5. `### Hard-to-reverse decisions` — a list.
6. `### Numbers it depends on` — a list, for example "under 50 writes/s to one MySQL instance".
7. `### Weakest point` — the candidate's best argument against itself.

A draft missing a section is recorded as malformed in the brief, with the names of the missing sections.

**D7 — Packaging: `general-purpose` agent plus a prompt file.** The skill dispatches `subagent_type: "general-purpose"` with `model: "opus"`. The prompt is built from `candidate-prompt.md`. The subagents return text only. The main agent saves each draft to `<scratchpad>/architect/<slug>/candidate-{a,b,c}.md`. `<scratchpad>` is the session's scratchpad directory from the system prompt. When there is none, it is a directory made with `mktemp -d`.

The prompt includes the search-tool wording from `my-plugin/agents/spec-reviewer.md`: search with `grep -rn` and `find` through Bash, use `Grep`/`Glob`/`LSP` only when present, and never skip a search because they are missing. Reason: these tools are removed from subagents at run time.

Rejected: a dedicated `my:candidate-architect` agent. It would match the `spec-review` pattern and add an agent-level contract. But the candidate task has no evidence or label rules to enforce, the schema in the prompt carries the contract, and it would add a third new file.

**D8 — Evaluation in the main conversation.** This runs on every candidate. When the gate made one candidate, it runs on that one.

- **Data ownership.** Merge the "Owns" columns. Flag every piece of state with zero owners or more than one owner.
- **Scenarios.** Use 4 to 6 scenarios:
  - the normal path at peak load (force 1),
  - failure of each external dependency (force 4),
  - the most frequent change (force 8),
  - data volume after 3 years (force 2),
  - one abuse or security case, when force 6 is not "none".

  Trace each scenario step by step through the Connections table. Record the step where it breaks, or "holds".
- **Pre-mortem.** Assume the design failed one year after launch. Write the three most likely causes for each candidate.
- **Comparison.** A table with forces as rows and candidates as columns. Each cell is `meets`, `partial` or `fails`, with a reason.
- **Choice.** The skill states a recommendation with reasons. The user picks with `AskUserQuestion`. The brief records why each rejected candidate lost.

**D9 — Reversibility and checks** (chosen design only).

- List each decision from "Hard-to-reverse decisions" and the Components table. Label it:
  - `hard` — data model, storage engine, public API or data format, process boundaries, vendor lock-in,
  - `medium` — internal module boundaries, library choice behind an interface,
  - `cheap` — everything else.
- For each `hard` decision, write and run a Python standard-library script in `<scratchpad>/architect/<slug>/`. It estimates load, storage, cost or latency from the forces and from "Numbers it depends on". The script and its printed output go into the brief. Python's standard library only, so no new dependencies.
- **Near a limit** means the estimate is within a factor of 2 of a known capacity or budget. In that case, or when a force the decision depends on is `assumed`, the skill proposes a spike in 2–3 sentences: the question and what it will try. It runs the spike only after the user approves. Spike code stays in the scratchpad, labelled throwaway, and is never committed. Only the result goes into the brief.

**D10 — The brief.** Path: `docs/plans/YYYY-MM-DD-<slug>-architecture.md`. The skill commits it with `docs(plans): add architecture brief for <slug>`. Sections, in order:

1. **How to read this brief** — related documents with paths, in reading order. The spec written next lists this brief first in its own "How to read this spec".
2. **Forces** — the D3 table with labels.
3. **Collapse gate** — the result, and a skip reason for each skipped shape.
4. **Candidates** — for each: Summary, Components, Connections, and any near-copy or malformed label.
5. **Evaluation** — ownership findings, scenario traces, pre-mortem, comparison table.
6. **Decision** — the chosen candidate, and why each rejected one lost.
7. **Reversibility and checks** — the decision table, scripts and outputs, spike results.
8. **Open for brainstorming** — every `assumed` force and every unresolved question. Brainstorming may ask only about these.
9. **Appendix: candidate drafts** — the full drafts, because the scratchpad is deleted later.

After committing, the skill prints the brief path and tells the caller to invoke `superpowers:brainstorming` with the brief path as input.

**D11 — `GLOBAL-CLAUDE.md` changes.**

- New trigger table row, placed above the brainstorming row: "New project, new subsystem, or change to a data model, storage choice or public contract | `my:architect`, then `superpowers:brainstorming`".
- "Discovery authority" paragraph. Add: "`my:architect` runs before brainstorming, not during it. When an architecture brief exists, brainstorming treats it as settled input and asks only about items under its 'Open for brainstorming' section."
- "Spec → Plan two-artifact flow", step 1: when a brief exists, "How to read this spec" lists it first.

## Out of scope

- Changing `superpowers:brainstorming` or `my:spec-review`.
- Reviewing an existing architecture. Use `my:spec-review` on a spec, or `my:soundness-review` on code.
- Diagrams. The brief uses tables. A later version could add a diagram.
- Fixing the plugin description in `plugin.json`. That is an existing ROADMAP row.

## Files

| File | Status | Responsibility |
|---|---|---|
| `my-plugin/skills/architect/SKILL.md` | Create | Steps D3–D10: forces, gate, dispatch, evaluation, checks, brief |
| `my-plugin/skills/architect/candidate-prompt.md` | Create | Candidate subagent prompt: shape, forces table, schema (D6), search wording (D7) |
| `GLOBAL-CLAUDE.md` | Modify | D11 |
| `ROADMAP.md` | Modify | New row for `my:architect` |

## Trade-offs

- **Brief before brainstorming (D1) vs inside it.** Pro: this skill controls its own method, and the brief is a durable record. Con: two artifacts before the plan, and the handoff depends on brainstorming following one sentence in `GLOBAL-CLAUDE.md`.
- **Parallel subagents (D5) vs one agent writing three.** Pro: real independence, so fewer near-copies. Con: three agent runs per use, and each draft must be checked against the schema.
- **One question call of up to 4 (D3) vs one question per message.** Pro: the user sees all assumptions at once and answers quickly. Con: at most 4 forces are confirmed by question. The rest stay `assumed` unless the user corrects them in free text.
- **Collapse gate (D4).** Pro: no invented complexity for small tools. Con: the thresholds are judgment calls. A borderline system may get one candidate when two would help. The user can override by asking for three.
- **`general-purpose` + prompt (D7) vs dedicated agent.** Pro: two new files, not three. Con: no agent-level "malformed prompt" stop. The schema check after return partly covers this.

## Dependencies

- No new packages. Estimate scripts use the Python 3 standard library. `python3` must be on `PATH`.
- `superpowers:brainstorming` 6.3.0, unchanged.
- The Agent tool accepting `model: "opus"` for `general-purpose`.
- `AskUserQuestion`, limited to 4 questions per call.

## Risk

1. **`AskUserQuestion` may fail in headless `claude -p` runs**, so tests cannot answer questions. Mitigation: test fixtures state all forces the skill would ask about, so they are `stated` and no question is asked. The first plan task confirms this works. The question step is tested once by hand in an interactive session.
2. **Brainstorming may ignore the brief** and ask about `stated` forces again. Detection: in the large-fixture handoff test, count re-asked `stated` forces. If this happens, strengthen the `GLOBAL-CLAUDE.md` sentence. Do not edit brainstorming.
3. **Cost.** Each full run uses 3 subagents plus evaluation. Limited by the D2 trigger and the D4 gate.
4. **Too much process for mid-sized work.** Detection: after 3 real uses, check whether each brief changed the resulting spec. If none did, narrow the D2 trigger.
5. **Blast radius.** The `GLOBAL-CLAUDE.md` edit changes the start of the design flow in every project, because `~/.claude/CLAUDE.md` links to it. Easy to reverse: revert one commit. No data or contract changes.

## Testing strategy

Same method as `docs/plans/2026-09-16-spec-review-skill.md`: headless `claude -p --plugin-dir <worktree>/my-plugin` runs, with output saved as `stream-json` in the scratchpad. Fixtures live in the scratchpad and are never committed.

- **Red baseline.** Run both fixtures through `superpowers:brainstorming` only, without the new skill. Record whether it shows forces, makes structurally different approaches, and runs any estimate.
- **Small fixture.** A solo-developer tool with no targets, stated in the description. Pass when:
  - the gate makes one candidate,
  - every skipped shape has a skip reason,
  - the brief has all 9 sections.
- **Large fixture.** A description with stated high write load, strict consistency for one entity, and a team of 3. Pass when:
  - three drafts exist with all D6 sections,
  - the contrast rule holds, or a near-copy label appears,
  - every force has a label,
  - at least one estimate script was run (a Bash tool call runs `python3` in the run log),
  - "Open for brainstorming" lists every `assumed` force.
- **Handoff.** Continue the large-fixture run into brainstorming. Pass when no `stated` force is asked about again.
- **Manual.** One interactive run to check the D3 question step and the D9 spike approval.

## Open questions

The four design choices (D1, D2, D5, D9) and the D7 packaging were confirmed with the user on 2026-09-17.

1. **D4 thresholds** (50 requests/s, 1 s latency, 1 hour downtime per month) were added while writing this spec. The user approved the gate and its forces, but not these numbers.
