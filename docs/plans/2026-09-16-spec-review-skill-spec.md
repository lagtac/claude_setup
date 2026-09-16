# Spec: `my:spec-review` — a system-thinking review for specs

## How to read this spec

| Document | Path | Why you would read it |
|---|---|---|
| **This spec** | `docs/plans/2026-09-16-spec-review-skill-spec.md` | What to build, why, and the trade-offs. Start here. |
| Implementation plan | `docs/plans/2026-09-16-spec-review-skill.md` | Written after this spec is approved. Test steps and commit breakdown. |
| Existing review skill | `my-plugin/skills/soundness-review/SKILL.md` | The skill whose plan-review mode this work replaces for specs. Its argument parsing, collision rule and dispatch steps are the model to copy. |
| Existing prompt template | `my-plugin/skills/soundness-review/code-reviewer-prompt.md` | Source of the shared rules this spec copies: severity and confidence labels, for-and-against tables, report layout. |
| Existing reviewer agent | `my-plugin/agents/code-reviewer.md` | The model for the new agent file, including the search-tool wording. |
| Earlier spec for plan-review mode | `docs/plans/2026-05-28-code-review-plan-mode-spec.md` | Why plan-review mode exists and what it was built to check. |
| Global instructions | `GLOBAL-CLAUDE.md` | The Spec → Plan flow (line 32), the "No silent reinterpretation" rule (line 42) and Code Review Routing (line 46). Two of these change. |
| Superpowers brainstorming | `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/brainstorming/SKILL.md` | The skill that writes the specs this new skill reviews. Not edited. |

## Context

Superpowers brainstorming writes a spec. `GLOBAL-CLAUDE.md:37` then asks Claude to review its own spec before the user reads it. That self-review checks placeholders, consistency, scope and ambiguity. It does not check whether the system the spec describes holds together.

The only reviewer that accepts a spec today is `my:soundness-review` in plan-review mode. It runs when a `.md` path is passed and the working tree is clean (`my-plugin/skills/soundness-review/SKILL.md:78`). Reviewing a spec with it has seven gaps:

1. **Plan-shaped criteria.** Four of its six criteria assume an execution plan: snippets that run on their own, step order and Red → Green, test strategy, and snippet logic (`SKILL.md:131-136`). A spec has none of these. They become N/A, or produce wrong findings.
2. **No system criteria.** Nothing asks about component boundaries, contracts, state ownership, how failures spread, or effects that only appear when parts combine.
3. **No model-building step.** The reviewer checks claims one at a time. It never lists the parts and their links, so it cannot see a gap between two parts.
4. **The evidence rule blocks structural findings.** A Critical finding must cite a repo location the reviewer opened (`code-reviewer-prompt.md`, "Every `Critical` finding must cite a repo location you actually opened"). A contradiction between two spec sections has no repo line. So the most serious kind of spec defect can never be rated Critical.
5. **No check of the spec rules.** `GLOBAL-CLAUDE.md:36` requires "How to read this spec" first, self-containment, a Risk section, trade-offs, and Visual Language for UI. The reviewer agent does not read CLAUDE.md, and its prompt does not list these rules.
6. **The mode depends on unrelated files.** Any uncommitted change anywhere switches the skill from reviewing the spec to reviewing the diff.
7. **One file only.** Checking several specs against each other is out of scope for this spec too (see Out of scope).

## Decisions

**D1 — A separate skill and a separate agent.** New `my:spec-review` skill and new `my:spec-reviewer` agent. `my:soundness-review` and `my:code-reviewer` stay as they are, apart from the routing edit in D7.

**D2 — Build a system model before judging.** The report opens with a required **System Model** section (layout under D4). A row the reviewer cannot fill in from the spec is itself a finding.

**D3 — Six criteria, each judged against the model.** A criterion that does not apply is marked **N/A** with a one-line reason.

1. **Boundaries.** Each component has one clear job. No two components own the same thing. No component exists only to pass calls along.
2. **Contracts and flow.** Every connection has a defined input, output and owner. Each piece of state has exactly one source of truth. Data and control flow have no gaps, and no cycles the spec does not state.
3. **Failures and interactions.** For each connection: what happens when one side fails or changes? The spec states whether the failure stops, spreads, or is hidden. The reviewer looks for behaviour that only appears in combination: loops, races, ordering needs.
4. **Fit with what exists.** The repo does not already solve the problem. The design follows existing patterns. The rejected options were real choices with stated reasons.
5. **Grounding.** Every file, symbol, command and claim about current behaviour is checked against the repo. For a symbol the spec removes or renames, the reviewer searches the whole repo for the name as plain text. Plain text search is required because string references (route names, config keys, template names) are invisible to symbol tools.
6. **Spec rules.** Written into the prompt word for word, because the agent does not read CLAUDE.md:
   - The first section is "How to read this spec", listing related documents with paths, in reading order.
   - A reader with no other context could write the implementation plan from the spec alone.
   - The spec has Risk, Dependencies and Trade-offs sections.
   - A Visual Language section is required **only** when the spec adds or changes UI. Its absence is correct otherwise.

**Out of scope for the reviewer:** TDD steps, test code, commit order, and code snippet logic. Those belong to the plan and are checked by `my:soundness-review`.

**D4 — Report layout.** Written to `docs/plans/<spec-basename-without-.md>-review.md`. Example: `2026-09-16-foo-spec.md` → `2026-09-16-foo-spec-review.md`. If that path exists, append `-2`, then `-3`, until it is free. A second review of the same spec is the normal case in the fix-then-review flow, so no review may overwrite an earlier one.

Sections, in order:

```markdown
### Spec Summary
[2–3 sentences: what the spec proposes.]

### System Model
| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|

| From → To | What passes (call / file / event / shared state) | Owner of what passes |
|---|---|---|

### Grounding
[Each stale reference or false assumption: spec §Section ↔ repo file:line, or "(not found)".]

### Issues Surfaced
| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|

### Dual-Perspective Analysis
[Arguments this is sound / Arguments this has problems — same tables as soundness-review. "None material." is legal. N/A rows for criteria are required.]

### Needs Investigation
[Omit if empty.]

### Reasoning
[2–4 sentences linking findings to the verdict.]

### Verdict
**Assessment:** Sound / Problematic / Mixed
**Confidence:** High / Medium / Low — [one sentence]
**Recommendation:** [one next step]
```

**D5 — Evidence and labels.**

- **Evidence** is either a repo `file:line` the reviewer opened or found by a search it ran, or a spec citation `spec §<Section>`. A two-section form `spec §A ↔ §B` is allowed.
- **Critical findings** must cite evidence the reviewer checked itself. Exception, stated explicitly in the prompt: a contradiction or gap *inside the spec* may be Critical on spec citations alone.
- **Severity** (`Critical` / `Warning` / `Suggestion`) and **confidence** (`High` / `Medium` / `Low`) work as in soundness-review. The display rule is unchanged: Critical always, Warning at Medium or higher, Suggestion at High only.
- **Class** is new, and is either `editorial` or `design`.
  - `editorial`: the text is wrong, the decision is not. Missing required section, stale repo reference, placeholder, a vague sentence with one sensible reading, two sections that disagree in wording only.
  - `design`: the finding challenges an approved decision. A boundary, a contract, state ownership, the chosen option, or the scope.
  - When unsure, the reviewer uses `design`.

**D6 — Required step in the Spec → Plan flow, with split fix authority.** `GLOBAL-CLAUDE.md` step 2 becomes:

1. Self-review the spec (as today).
2. Run `my:spec-review <spec path>`.
3. Fix every `editorial` finding in the spec. Before each fix, check whether it changes what a component owns, a contract, the chosen option, or the scope. If it does, treat it as `design`, whatever its label says.
4. Do **not** fix `design` findings. Ask the user in the "No silent reinterpretation" form: "Decision X was picked for reason Y. The review says Y is wrong because Z. Keep X or change it?"
5. List any findings Claude rejects, with one line of reasoning each.
6. Ask the user to review the spec, the report path, and the open design questions together.

*Why the split.* The review runs after the user approved each design section in brainstorming. A design finding therefore challenges a decision the user made. `GLOBAL-CLAUDE.md:42-44` forbids changing such a decision without asking, even when the change looks equivalent.

**D7 — Routing edits.**

- `my-plugin/skills/soundness-review/SKILL.md`: when step 1a selects `plan-review` **and** the path ends in `-spec.md`, stop and print `This is a spec. Run my:spec-review <path> instead.` Its `description` gains one sentence saying specs go to `my:spec-review`. Diff-review against a spec (dirty tree, checking code matches a spec) is unchanged. That use is still correct.
- `GLOBAL-CLAUDE.md` Code Review Routing (line 46): the intro line at line 48, "Two diff reviewers, complementary", becomes "Three reviewers, complementary". A new bullet names `my:spec-review`: system-thinking review of one `-spec.md`, report to `docs/plans/`. The `my:soundness-review` bullet's "review the plan itself (clean tree)" becomes "review a plan itself (clean tree; specs go to `my:spec-review`)".

**D8 — The skill ignores the working tree.** It reads the spec file from disk. It never runs `git diff`. Uncommitted files do not change what it reviews.

## Architecture

| Component | Owns | Depends on |
|---|---|---|
| `my-plugin/skills/spec-review/SKILL.md` | Argument check (one existing `.md` path; otherwise stop with a usage line), reading the spec, report path and collision rule, filling the template, starting the agent in the foreground, printing the report path and top finding | `spec-reviewer-prompt.md`, `my:spec-reviewer`, `git rev-parse --show-toplevel` |
| `my-plugin/skills/spec-review/spec-reviewer-prompt.md` | Criteria (D3), evidence and label rules (D5), report layout (D4), anti-agreement rules | Nothing at run time. Copies rules from `soundness-review/code-reviewer-prompt.md` |
| `my-plugin/agents/spec-reviewer.md` | Following the prompt exactly; writing the report file | Tools `Read, Grep, Glob, Bash, Write, LSP, ToolSearch`; `model: opus` |

**Flow.** Caller → skill reads spec → skill fills placeholders `{{SPEC_PATH}}`, `{{SUBJECT}}` (full spec text in a fenced markdown block), `{{PLAN_DIRECTORY}}` (absolute), `{{REVIEW_SLUG}}` → agent reads the repo and writes the report → skill confirms the file exists and prints `Review written to docs/plans/<file>.` If the verdict is `Problematic` or any Critical finding exists, it also prints the top finding in two lines.

**Failure handling.**

- Path missing, or not a `.md` file: the skill stops with a usage line and does not start the agent.
- Agent returns but no report file exists: the skill prints the agent's text output and says the write failed. Same as `soundness-review/SKILL.md:184`.
- Agent prompt missing a required section: the agent stops with `Dispatch prompt is malformed — required section <name> missing.` Same contract as `agents/code-reviewer.md`.
- The spec is over 2000 lines: the skill warns and continues, and the prompt tells the reviewer to name any parts it covered only shallowly. Same guard as `soundness-review/SKILL.md:67-70`.

**Search tools in the agent.** The runtime removes `Grep`, `Glob` and `LSP` from subagents even when listed (commit `2c459be`). The agent and the prompt must name `grep -rn` and `find` through `Bash` as the main search route. They may use the other tools only when present, and their absence must never cancel a search. Copy the wording from `agents/code-reviewer.md`.

**Copied rules.** The severity/confidence table, the anti-agreement rules and the dual-perspective tables are copied from `code-reviewer-prompt.md`. Each template's header gets one line naming the other file as holding a copy of these rules, so an edit to one points to the other.

**Manifest.** `my-plugin/.claude-plugin/plugin.json` has no `commands` or `agents` keys. Skills and agents are found by directory, so no manifest change is needed.

## Visual Language

N/A. This spec adds no UI.

## Trade-offs

**Option A — New skill and new agent (chosen).**
Pros: each file has one job; changing spec review cannot break diff or plan review.
Cons: about 30 lines of shared rules exist in two templates and can drift apart.

**Option B — New skill that reuses `my:code-reviewer`.**
Pros: no new agent; shared rules stay in one agent file.
Cons: that agent's contract describes diff and plan review only. A third mode edits a file `soundness-review` depends on and couples the two skills.

**Option C — One shared rules file read by both templates.**
Pros: no copied text.
Cons: one skill reads a file from inside another skill's folder, and a rename breaks it without warning. It adds a file only to avoid 30 copied lines.

**Alternative rejected for D6 — fix and review again until no Critical findings remain.** Costs several Opus runs per spec, and a loop would tempt Claude to fix design findings to make the loop end.

**Alternative rejected for D7 — a `-spec.md` mode inside `soundness-review`.** The user chose a separate skill. `soundness-review/SKILL.md` is already 222 lines.

## Dependencies

- No new packages.
- `my:spec-review` must exist before `GLOBAL-CLAUDE.md` names it as a required step. Both land in the same squash-merge.
- `~/.claude/CLAUDE.md` is a symlink to this repo's `GLOBAL-CLAUDE.md` on `main`. The new flow step is live only after the merge to `main`, not in the worktree.

## Risk

- **Reversibility: full.** Three new files and three edits to markdown. Revert the squash commit to undo.
- **Blast radius.** Every future spec written through brainstorming in every project runs this review. Existing `soundness-review` diff and plan use is unchanged, except a `-spec.md` in plan-review now stops with a pointer.
- **Wrong class label.** A design finding labelled `editorial` could lead Claude to change an approved decision without asking. Mitigations: "unsure → design" in the prompt; the owner/contract/option/scope check before each fix in D6. Detect by reading the "fixed" list Claude gives the user.
- **Two skills match one request.** Skill choice is by description. Mitigation: the D7 description sentence and the plan-review stop. Detect with Test 3.
- **Cost.** One extra Opus run per spec. Accepted by the user.
- **Copied rules drift.** Mitigation: the cross-reference header lines.
- **Manual step.** Test 3 needs a fresh Claude Code session after merge.

## Testing strategy

The repo has no test runner, and skills have no test harness. Each test is a real run with checks on the written report. Red is recorded before the new files exist.

1. **Planted defects.** A test spec in the session scratchpad (full text in the plan) with four defects:
   - two components that both own the same state — expect `design`, `Critical`, citing `spec §A ↔ §B`
   - no "How to read this spec" section — expect `editorial`
   - a reference to a repo file that does not exist — expect `editorial`, listed under Grounding with "(not found)"
   - a UI change with no Visual Language section — expect `editorial`

   **Red:** run today's `my:soundness-review` plan-review on it. Record that the report has no class column, and that the ownership contradiction is missing or not Critical. **Green:** the new report contains all four findings, with the expected classes and citations.
2. **Real specs.** Run `my:spec-review` on `docs/plans/2026-05-28-code-review-plan-mode-spec.md` and `docs/plans/2026-09-11-retire-planner-path-spec.md`. Each report has a filled System Model. The planner-retirement report does not flag missing Visual Language. Neither report has TDD, commit-order or snippet findings.
3. **Routing.** `my:soundness-review docs/plans/2026-09-11-retire-planner-path-spec.md` on a clean tree prints the pointer and starts no agent. After merge, in a fresh session, "review docs/plans/2026-09-11-retire-planner-path-spec.md" selects `my:spec-review`.
4. **Collision.** Run Test 2 twice on one spec. The second report is written to `…-review-2.md`.
5. **Lint.** `markdownlint-cli2` on every changed and new file. The repo has no lint config, so existing files already fail MD013 (line length) and MD060 (table spacing). Pass means no rule fails beyond those two.

## Out of scope

- Reviewing several specs against each other. Deferred by the user.
- Changing the Superpowers brainstorming skill. It lives in a versioned plugin cache that updates overwrite. `GLOBAL-CLAUDE.md` already overrides it.
- Removing plan-review mode from `soundness-review`. It still serves execution plans.

## Open questions

None blocking.
