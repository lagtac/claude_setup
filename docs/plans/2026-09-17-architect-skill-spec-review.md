### Spec Summary

The spec proposes a new skill, `my:architect`, that runs before `superpowers:brainstorming` for new projects, new subsystems and data-model, storage or public-contract changes. It fills a labelled table of 10 forces, uses a gate to decide between one and three candidate designs, has parallel `general-purpose` subagents draft the candidates to a fixed schema, then evaluates them, checks hard-to-reverse decisions with Python estimate scripts, and commits an architecture brief to `docs/plans/YYYY-MM-DD-<slug>-architecture.md`. `GLOBAL-CLAUDE.md` gains a trigger row and a handoff sentence, so that brainstorming treats the brief as settled input.

### System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `my:architect` skill (`my-plugin/skills/architect/SKILL.md`) | The forces table and its labels (D3), the gate result (D4), the choice of shapes and the contrast check (D5), the evaluation (D8), the reversibility labels, the estimate scripts and spike proposals (D9), the brief file and its commit (D10) | User (`AskUserQuestion`), the candidate subagents, `python3`, git, the scratchpad | New |
| Candidate prompt (`my-plugin/skills/architect/candidate-prompt.md`) | The candidate schema (D6) and the search-tool wording (D7) | `my-plugin/agents/spec-reviewer.md` wording | New |
| Candidate subagents (`general-purpose`, `model: "opus"`, x1 or x3) | One draft each, returned as text. No files. | Candidate prompt, repo (read-only search) | Existing agent type. Precedent for `general-purpose` with a `model:` at `my-plugin/skills/clean-plans/SKILL.md:80` and `my-plugin/skills/tune-claude-instructions/SKILL.md:87` (both `haiku`, not `opus`) |
| Scratchpad `<scratchpad>/architect/<slug>/` | Saved drafts, estimate scripts, spike code (throwaway) | Session scratchpad or `mktemp -d` | New directory convention |
| Architecture brief `docs/plans/YYYY-MM-DD-<slug>-architecture.md` | The durable record: forces, gate, candidates, evaluation, decision, checks, "Open for brainstorming", appendix | Skill | New artifact type |
| `superpowers:brainstorming` 6.3.0 | Path classification (spike / bounded / architectural), clarifying questions, "Propose 2-3 approaches", design sections, the spec | Brief (only via the `GLOBAL-CLAUDE.md` sentence) | Existing, unchanged: `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/brainstorming/SKILL.md` |
| `GLOBAL-CLAUDE.md` | Trigger table (line 17), Discovery authority (line 30), Spec → Plan step 1 (line 36) | Symlinked from `~/.claude/CLAUDE.md` | Existing `GLOBAL-CLAUDE.md:17`, `:30`, `:36`; symlink verified |
| `ROADMAP.md` | Row for the skill | none | Existing `ROADMAP.md` |
| Orphan-plan hook | Warning on undated or untracked `docs/plans/*.md` | git | Existing `my-plugin/hooks/check-orphan-plans.sh:23-29` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Main agent (via `GLOBAL-CLAUDE.md` trigger row) → `my:architect` | Invocation plus the user's description. Who classifies the task against D2 is implied (the main agent), not stated | `GLOBAL-CLAUDE.md` row (new) |
| Skill → User | Forces table in chat; one `AskUserQuestion` call (up to 4 questions); later the candidate choice (D8) and spike approval (D9) | Skill |
| User → Skill | Answers, free-text corrections, the chosen candidate, spike approval | User |
| Skill → Candidate subagent | Prompt: shape, forces table, schema, search wording (Files table). The user's description and the repo root are not listed | Skill / candidate prompt |
| Candidate subagent → Skill | Markdown draft of about 800 words (D6) | Subagent produces; skill saves it to the scratchpad |
| Skill → `python3` | Estimate script and its printed output | Skill |
| Skill → brief file → git | Brief text and the commit `docs(plans): add architecture brief for <slug>` | Skill |
| Skill → Main agent / caller | Brief path plus "invoke `superpowers:brainstorming` with the brief path" | Skill |
| Brief → `superpowers:brainstorming` | Settled forces, chosen design, "Open for brainstorming" list. Enforced only by the `GLOBAL-CLAUDE.md` Discovery-authority sentence | Brief (content); `GLOBAL-CLAUDE.md` (the rule) |
| Brainstorming → Spec | "How to read this spec" lists the brief first | `GLOBAL-CLAUDE.md` step 1 (modified) |

### Grounding

All checked references hold. Checked: `GLOBAL-CLAUDE.md` lines 17, 30, 32–40 and 36 hold the text the spec names. `my-plugin/skills/spec-review/SKILL.md` has the step layout, the absolute-path rule (step 2, `{{PLAN_DIRECTORY}}`) and the worked example. `my-plugin/agents/spec-reviewer.md:12` ("Contract with the Calling Skill") and `:19` (grounding bullet) exist. `docs/plans/2026-09-16-spec-review-skill.md:22-33` ("How tests run") and its scratchpad fixtures (`:59`) exist. `check-orphan-plans.sh:28-29` flags only undated or untracked files, so a committed, dated `-architecture.md` is silent. `ROADMAP.md` has the "Plugin docs drift" row about `plugin.json`. The brainstorming 6.3.0 path exists, and the skill does ask one question per message and propose 2–3 approaches. `~/.claude/CLAUDE.md` links to `GLOBAL-CLAUDE.md`. `python3` is on `PATH` (`/usr/bin/python3`). The spec removes or renames no symbol. The sweep was text-only (`grep`/`find` through Bash); `LSP`, `Grep` and `Glob` are not in this reviewer's tool list.

### Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Critical / High | design | The D3 question budget skips a gate input. D3 asks at most 4 questions, in the order 5, 1, 4, 7, 10. The D4 gate reads forces 1, 3, 4, 7 and 10. Force 5 (consistency) is not a gate input but takes the first slot. Force 3 (latency) is a gate input but comes 6th, so it is never asked. When forces 5, 1, 4 and 7 are all unconfirmed, force 10 is not asked either. The gate then decides one versus three candidates on a latency value, and maybe a constraints value, that the agent invented. | `spec §D3` (step 3 order) ↔ `spec §D4` (gate forces) | Decision for the author: for example, ask gate inputs first (1, 3, 4, 7, 10), or let an `assumed` gate input block the collapse. |
| Warning / High | design | Two components own candidate generation. D1 says brainstorming "runs as usual". On its architectural path, brainstorming's checklist step 4 is "Propose 2-3 approaches" and step 5 is "Present design … get user approval". The D11 sentence only limits which *questions* brainstorming asks. It does not stop brainstorming from proposing new approaches or reopening the chosen design. Risk 2 covers re-asked forces only. | `spec §D1`, `§D11` ↔ brainstorming `SKILL.md` "Architectural" checklist items 4–5 | Decision for the author: say in the D11 sentence that the brief's Decision replaces brainstorming's approach step, or accept brainstorming re-choosing and say so. |
| Warning / Medium | design | The trigger and brainstorming's path classes can disagree in both directions. (a) A D2 trigger such as a data-model change in an existing repo may be classified by brainstorming as **bounded**. A bounded task gets "no spec file", so the D10 promise that "the spec written next lists this brief first" fails. (b) Brainstorming's ratchet ("hidden complexity … upgrades the path … Nothing downgrades") can move a task to architectural midway. The terminal-state rule allows only writing-plans after that, so there is no route back to `my:architect`. | `spec §D2`, `§D10` item 1 ↔ brainstorming `SKILL.md` "Three Paths" (bounded: "No spec file") and "Terminal states are path-bound" | Decision for the author: state what happens when brainstorming picks bounded after a brief exists, and whether an upgrade mid-brainstorming should stop and run `my:architect`. |
| Warning / High | design | Some failure branches are undefined. D5 and D6 handle near-copy and malformed drafts. Nothing covers a subagent that errors, times out or returns nothing. Nothing covers a failed contrast check *before* dispatch: pick another shape, or dispatch anyway? D8 then "runs on every candidate", but ownership merge and scenario traces need the Components and Connections tables. A malformed draft that lacks them cannot be evaluated, and the spec does not say whether it is skipped or still offered as a choice. | `spec §D5` (contrast rule), `§D6` (malformed), `§D7`, `§D8` | Decision for the author: define the stop / continue / exclude rule for each case. |
| Warning / High | design | The contract with the candidate subagents is missing inputs. The Files table lists the prompt contents as "shape, forces table, schema (D6), search wording (D7)". It leaves out the user's description of the system and the absolute repo root. The subagent needs the first to design anything. It needs the second because `my:spec-review` passes absolute paths, since subagents do not reliably inherit cwd. | `spec §Files` (candidate-prompt row), `§D7` ↔ `my-plugin/skills/spec-review/SKILL.md` step 2 (`{{PLAN_DIRECTORY}}` absolute-path note) | Add the description, the repo root (when one exists) and the chosen-shape reason to the prompt's inputs. |
| Warning / High | design | The candidate choice has no non-interactive path and no single-candidate path. The D8 choice always uses `AskUserQuestion`, and it comes before the D9 estimate scripts. Risk 1 says `AskUserQuestion` may fail headless and removes only the D3 question. With one candidate (gate collapsed), "the user picks" has only one option, and the spec does not say what the user is asked. | `spec §D8` Choice ↔ `spec §Risk` item 1, `§D4` | Decision for the author: define the one-candidate case (for example, confirm or ask for three), and what happens when the question cannot be asked. |
| Warning / High | design | The Trade-offs section says "The user can override by asking for three". D4 has no step that shows the gate result to the user before dispatch, so there is no point at which to override. | `spec §Trade-offs` (Collapse gate) ↔ `spec §D4` | Decision for the author: add a show-and-confirm point after the gate, or drop the override claim. |
| Warning / Medium | editorial | D3's step order is wrong. Step 4 copies every `assumed` force to "Open for brainstorming". Step 5 then lets the user correct rows, which makes them `stated`. A corrected row would already have been copied. The only sensible reading is that the list is built from the final labels. | `spec §D3` steps 4–5 ↔ `§D10` item 8 | Move the copy to "Open for brainstorming" after step 5, or say it uses the final labels. |
| Warning / Medium | design | D9 requires a numeric script for every `hard` decision. Several `hard` categories, such as "public API or data format" and "vendor lock-in", have no load, storage, cost or latency quantity to estimate. The rule invites empty scripts. | `spec §D9` (hard labels ↔ script rule) | Decision for the author: require a script only when the decision has a number it depends on. |
| Suggestion / High | editorial | D11 inserts a row above line 17. That shifts the lines the spec and D11 cite: line 30 becomes 31, and line 36 becomes 37. | `spec §D11`, `§How to read this spec` ↔ `GLOBAL-CLAUDE.md:17,30,36` | Cite by heading ("Discovery authority", "Spec → Plan flow step 1") instead of line number. |

### Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | Skill, prompt file and subagents each have one job. Subagents return text and own no files; the skill owns every write (`spec §D7`, `§Files`). | Moderate |
| Contracts and flow | The candidate schema is fixed and checked on return (`spec §D6`). The brief's sections are fixed (`§D10`). The force labels have a defined meaning (`§D3`). | Moderate |
| Failures and interactions | Near-copy and malformed drafts are kept and labelled rather than silently dropped (`spec §D5`, `§D6`). Spikes need approval and are never committed (`§D9`). | Moderate |
| Fit with what exists | Follows the `general-purpose` + `model:` dispatch pattern (`my-plugin/skills/clean-plans/SKILL.md:80`) and the search-wording lesson (`my-plugin/agents/spec-reviewer.md:19`). The rejected options are real and have reasons: the dedicated agent in D7, running inside brainstorming in D1. Nothing in the repo already does forces-first design (text search for "architect" found no such skill). | Strong |
| Grounding | Every path and line checked holds (see Grounding). | Strong |
| Spec rules | "How to read this spec" is first and lists documents in order. Risk, Dependencies and Trade-offs sections are present. The spec adds no UI, so no Visual Language section is correct. | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Contracts and flow | The D3 question budget does not match the D4 gate inputs (`spec §D3 ↔ §D4`). The candidate prompt lacks the description and repo root (`§Files`). | High |
| Boundaries | Brainstorming still owns "Propose 2-3 approaches" while the brief owns the decision (`spec §D1` ↔ brainstorming checklist). | Medium |
| Failures and interactions | No branch for subagent errors, a failed contrast check before dispatch, or a single-candidate choice. The brainstorming path classes (bounded, ratchet) can break the handoff (`spec §D2`, `§D5`, `§D8`). | Medium |
| Spec rules (self-containment) | A plan writer would need to invent the failure branches and the one-candidate choice path. That makes the gaps design decisions, not plan details. | Medium |

### Needs Investigation

- **`plan-format.md` scope.** `GLOBAL-rules/plan-format.md:1-3` loads for `**/docs/plans/*.md` and says "Every section is required". The brief lives in `docs/plans/` with 9 different sections. Specs and reviews already live there, so this tension already exists, and "Superpowers may substitute its own format" may not cover a `my:` skill. The fix is to decide whether the skill should tell the agent that the brief is not a plan, or whether the rule's glob should exclude it. Check by running the skill once and seeing whether the agent adds plan sections to the brief.
- **`AskUserQuestion` option limits.** The spec relies on "at most 4 questions per call". The D8 one-candidate case may need a minimum number of options. This cannot be checked from the repo; confirm against the tool schema.
- **`model: "opus"` for `general-purpose`.** The repo precedents use only `haiku`. The spec lists this as a dependency; the first plan task should confirm it.
- **D4 thresholds.** These are already flagged as unapproved under `spec §Open questions`, so they are not raised as a finding.

### Reasoning

The System Model is clean at the component level. One skill owns every decision and every write, subagents only return text, and every repo reference holds. The problems are at the two connections that cross into things the skill does not control. Inside the skill, the D3 question step does not feed the D4 gate the inputs it needs. Outside it, brainstorming's own checklist, path classes and ratchet can override or skip the brief, and the one-sentence handoff does not address them. Several failure and single-candidate branches are also undefined, and a plan writer would have to decide them. The chosen approach is still defensible, so the spec is Mixed rather than Problematic.

### Verdict

**Assessment:** Mixed
**Confidence:** High — every finding cites the spec text or the brainstorming 6.3.0 skill file that was read directly.
**Recommendation:** Put the D3/D4 question-budget finding and the brainstorming handoff findings (approach step, bounded path, ratchet) to the author as design questions. Fix the D3 step order and the line-number citations editorially. Define the failure and single-candidate branches before writing the plan.
