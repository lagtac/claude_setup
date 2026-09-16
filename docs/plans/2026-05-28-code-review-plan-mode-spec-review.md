### Spec Summary

The spec adds a "plan-review" mode to the `my:code-review` skill. When a `.md` plan path is passed and the captured diff is empty, the plan document itself becomes the review subject. The reviewer grounds it against the repo and judges it on six plan criteria. A dirty tree keeps today's diff-plus-alignment review and prints a nudge. The same prompt template and the same `my:code-reviewer` agent serve both modes through new placeholders (`{{MODE}}`, `{{SUBJECT}}`, `{{CRITERIA}}`, `{{MODE_OUTPUT_SECTION}}`).

**Context for this review:** this spec has already been implemented (commits `ded1cb1`, `c9bd8c5`, `a7bdfc1`). The skill was then renamed to `soundness-review` (`7826990`) and changed further (`4166d72`, `099654d`, `2c459be`). So this review checks the spec against a repo that has moved past it. Most findings are about drift, not about the original decisions.

### System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| Skill orchestrator (spec: `my-plugin/skills/code-review/SKILL.md`) | Arg classification, diff capture, the choice of `MODE`, the nudge, placeholder substitution, review slug, dispatch | Prompt template, reviewer agent, git | Existing, now at `my-plugin/skills/soundness-review/SKILL.md:1`. The old path is (not found). Mode detection is implemented at `SKILL.md:72-85` |
| Dispatch-prompt template (spec: `.../code-review/code-reviewer-prompt.md`) | Shared prompt text, section headings the agent checks, the `**Review mode:**` line | Skill (fills placeholders) | Existing, now at `my-plugin/skills/soundness-review/code-reviewer-prompt.md:21` (`{{MODE}}`), `:44` (`{{CRITERIA}}`), `:76` (`{{MODE_OUTPUT_SECTION}}`), `:117-119` (`## Subject Under Review`) |
| Mode-specific text blocks (diff criteria, plan criteria, Plan Alignment output, Grounding output) | The criteria and output wording for each mode | Skill (the blocks live inside SKILL.md, not in the template) | Existing, `my-plugin/skills/soundness-review/SKILL.md:115-148`. The spec does not say where these blocks live |
| Reviewer agent `my:code-reviewer` | Section check, "do not re-capture" rule, mode-aware scope, writing the review file | The assembled prompt; Read, Bash, Write | Existing, `my-plugin/agents/code-reviewer.md:1-24` |
| Review file in `docs/plans/` | The durable verdict | Agent writes it; skill confirms it exists | Existing pattern; plan-review slug at `SKILL.md:111` |
| `README.md` row | User-facing description | None | Existing, `README.md:9` (now `/my:soundness-review`) |
| `GLOBAL-CLAUDE.md` Code Review Routing | Routing guidance for every project | None | Existing, `GLOBAL-CLAUDE.md:46-54`. Plan-review was folded into the existing bullet at `:50`, not added as a new row |

| From → To | What passes | Owner of what passes |
|---|---|---|
| User → Skill | Args string (`RANGE`, `PLAN_PATH`, `DESCRIPTION`) | User |
| git → Skill | Diff payload (working tree or range) | Skill (runs git) |
| Skill → User | Nudge text when plan set and tree dirty | Skill |
| Skill → Template | Placeholder values chosen by `MODE` | Skill |
| Skill → Agent | Composed prompt: `**Review mode:**` line, subject, criteria, output section, output path | Skill |
| Agent → Repo | Read and search calls for grounding (plan-review) or context (diff-review) | Agent |
| Agent → Review file | Written review | Agent |
| Skill → Review file | Existence check and a pointer printed to the user | Skill |

### Grounding

- spec §How to read this spec (items 1-3), §Prompt template changes, §Agent contract changes ↔ `my-plugin/skills/code-review/` (not found). The skill now lives at `my-plugin/skills/soundness-review/` (renamed in commit `7826990`). The skill name `my:code-review` and the command `/my:code-review` are now `my:soundness-review` (`README.md:9`, `GLOBAL-CLAUDE.md:50`). A text search for `skills/code-review/` and `/my:code-review` outside `docs/plans/` found no hits.
- spec §Criteria "The full current text lives in `code-reviewer-prompt.md` lines 36–44" ↔ the diff criteria now live in `my-plugin/skills/soundness-review/SKILL.md:117-125`. The template holds only the `{{CRITERIA}}` placeholder (`code-reviewer-prompt.md:44`). The line reference no longer points at the text. I could not open the file as it was when the spec was written, because `git show` needed approval.
- spec §Dependencies "The `my:code-reviewer` agent already has Read/Grep/Glob/Bash/Write — sufficient for grounding" ↔ `my-plugin/agents/code-reviewer.md:4` lists those tools, but the runtime removes `Grep`/`Glob`/`LSP` from subagents. The contract now routes searches through `Bash` (`code-reviewer.md:18-19`, `code-reviewer-prompt.md:38`, `SKILL.md:135`; fixed in commit `2c459be`). The spec's plan criterion 5 ("Use Read / Grep / Glob") carries the same false assumption.
- spec §Agent contract changes "in diff-review, do not widen beyond the payload (Read/Grep only to assess a finding's context)" ↔ `my-plugin/agents/code-reviewer.md:18` now requires diff-review to read every touched file in full and to sweep the whole repo for removed symbols. The current behaviour contradicts the spec.
- spec §Documentation changes "add a row" to Code Review Routing ↔ `GLOBAL-CLAUDE.md:50` puts plan-review inside the existing `my:soundness-review` bullet. The section has no table rows. The intent was met; the wording is stale.
- spec §Criteria (plan-review block, dimensions 3 and 5) ↔ `SKILL.md:133` and `SKILL.md:135` add vacuous-test checks, an end-to-end test rule and a reference-completeness sweep. The spec's "verbatim" block no longer matches what ships.

### Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | editorial | Every path and name the spec's plan depends on (`skills/code-review/`, `my:code-review`, `/my:code-review`) is stale after the rename. A cold reader following "How to read this spec" hits missing files. | spec §How to read this spec ↔ `my-plugin/skills/soundness-review/SKILL.md:2`; `my-plugin/skills/code-review/` (not found) | Mark the spec as implemented and superseded, with a pointer to `soundness-review` and commit `7826990`. Or update the paths. |
| Warning / High | design | The spec does not deal with re-reviews overwriting earlier ones. The plan-review slug comes from the plan's filename, so every re-review of the same plan writes to the same file. The implementation later had to add a collision rule. | spec §Output ("Output file slug") ↔ `my-plugin/skills/soundness-review/SKILL.md:113` | Decision for the author: add the `-2`/`-3` suffix rule to the spec, or note that `099654d` replaced this part. |
| Warning / High | design | Dependencies assumes the agent can use Grep/Glob. Subagents do not get those tools, so grounding as written ("Use Read / Grep / Glob") cannot run as the spec describes. | spec §Dependencies, §Criteria dim. 5 ↔ `my-plugin/agents/code-reviewer.md:4` vs `:19`; `code-reviewer-prompt.md:38` | Change the grounding instructions to `Bash` searches (already done in the code). Update the spec, or mark it superseded. |
| Warning / Medium | design | Scope overlap with the new `my:spec-review` skill. The spec routes "plan/spec" documents to plan-review, but `my:spec-review` now claims specs and sends plans to `my:soundness-review`. A `-spec.md` file passed to `my:soundness-review` on a clean tree still gets the plan criteria (TDD, snippet logic). No rule separates the two skills. | spec §Documentation changes ("review a plan/spec document") ↔ `my-plugin/skills/spec-review/SKILL.md:10-11`; `my-plugin/skills/soundness-review/SKILL.md:10-11`, `:78` | Decision for the author: limit plan-review to implementation plans, and have `soundness-review` redirect or warn when it gets a `-spec.md` file. |
| Warning / Medium | design | The trigger depends on the whole working tree being clean. Any unrelated uncommitted file (for example, this worktree right now) silently switches the review to alignment against an unrelated diff. The only fix offered is "commit or stash". The spec treats the nudge as enough. The newer `my:spec-review` rejects this coupling outright ("This skill ignores the working tree"). | spec §Mode detection, §Trade-offs (trigger) ↔ `my-plugin/skills/spec-review/SKILL.md:21`; `my-plugin/skills/soundness-review/SKILL.md:79-85` | Decision for the author: consider an explicit override (for example, a `plan` keyword) as an escape hatch. The spec rejected that option for "zero new syntax", but the cost is now visible. |
| Warning / Medium | design | When a plan is passed with an empty range, the skill switches to plan-review with no message ("`RANGE`, if any, is ignored"). A mistyped or already-merged range therefore gives a plan review with no signal. This is the same silent-mode risk the nudge exists to prevent. | spec §Mode detection (row 1) ↔ `my-plugin/skills/soundness-review/SKILL.md:78` | Print a nudge in this case too: `(Range <RANGE> is empty; reviewing <PLAN_PATH> itself.)` |
| Warning / Medium | design | The spec is out of date on how diff-review reads the repo. It says diff-review does not widen beyond the payload. Current behaviour requires reading touched files in full and sweeping the repo. Anyone treating the spec as the design record would take the wrong contract. | spec §Agent contract changes ↔ `my-plugin/agents/code-reviewer.md:18` | Mark the spec superseded, or add a note linking the later audit (`docs/plans/2026-09-07-soundness-review-audit.md`). |
| Suggestion / High | editorial | The diff-criteria block is shortened with `…` and relies on a line range that no longer exists. A cold reader cannot rebuild the "verbatim" text. | spec §Criteria ↔ `my-plugin/skills/soundness-review/SKILL.md:117-125` | Point to `SKILL.md` "Diff criteria", or paste the full text. |

### Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | Skill owns mode choice and substitution; the agent only reads a literal `**Review mode:**` line and never guesses. One owner for `MODE`. Confirmed in the implementation at `code-reviewer-prompt.md:21`, `code-reviewer.md:10` | Strong |
| Contracts and flow | Mode table covers all four `PLAN_PATH` × payload cases. Each placeholder has a value defined for every mode, including empty strings. `SKILL.md:76-111` implements it one-to-one | Strong |
| Failures and interactions | The spec names the main silent failure (dirty tree picks alignment) and adds a user-facing nudge. The malformed-prompt check is carried over to the renamed sections | Moderate |
| Fit with what exists | Reuses the existing template, agent and output schema; no new files. The rejected options (keyword trigger, separate skill) were real choices with stated costs | Moderate |
| Grounding | At the time of writing, the structure matched the repo closely enough that the implementation followed it with no structural changes (`SKILL.md:72-148`) | Moderate |
| Spec rules | Has "How to read this spec" first, plus Trade-offs, Dependencies, Risk and a correct Visual Language N/A. Plan criteria are given in full | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Grounding | Old skill path, command name, prompt line range and the Grep/Glob tool assumption are all stale (see Grounding) | Medium |
| Failures and interactions | Silent switch when a range is empty; working-tree coupling fixed only by stashing; re-reviews overwrite each other | Medium |
| Boundaries | Overlaps with `my:spec-review` over who reviews specs | Medium |
| Contracts and flow | The spec does not say where the mode-specific text blocks live (skill or template). The implementation put them in SKILL.md; it could equally have gone the other way | Low |
| Spec rules | Self-containment is broken for the diff criteria (the text is shortened with `…` and points to a line range that no longer exists) | Low |

### Needs Investigation

- **Whether the "lines 36–44" reference was correct when the spec was written.** I could not open `my-plugin/skills/code-review/code-reviewer-prompt.md` at commit `1a8242e`, because `git show` needed approval. It matters only if the spec is kept as a live document. Running `git show 1a8242e:my-plugin/skills/code-review/code-reviewer-prompt.md` would settle it.
- **Whether this spec should still be reviewed as a live design at all.** It was implemented and then superseded by the rename and two audit rounds. If it is kept only as history, a "superseded by" header resolves most findings. If it is meant to stay the design record for plan-review, it needs the updates listed above.
- The reference sweep for the renamed names was text-only (`grep`). `LSP` was not used, because these are markdown string references that no language server indexes.

### Reasoning

The design holds together as a system. `MODE` has one owner, every placeholder has a value in every mode, and the implementation matches the structure closely (`SKILL.md:72-148`). The problems come mostly from drift. The spec's paths, command name, tool assumptions and diff-review scope rule no longer match the repo. Two design gaps also appeared later: re-reviews overwrite each other, and the scope overlaps with the new `my:spec-review`. The working-tree trigger, and the lack of a message when an empty range falls through to plan-review, are real design costs the spec underrated. No finding is Critical, because nothing in the spec contradicts itself and the shipped code already fixes the grounding errors.

### Verdict

**Assessment:** Mixed
**Confidence:** High — every stale reference was checked against the current files and commit history. The one unverified point (the old line range) does not change the verdict.
**Recommendation:** Add a "Status: implemented; superseded by the `soundness-review` rename (`7826990`) and audit fixes (`4166d72`, `099654d`, `2c459be`)" header. Then decide two design points: (1) whether `soundness-review` plan-review should decline `-spec.md` files now that `my:spec-review` exists, and (2) whether an empty range or a dirty tree needs an explicit override instead of only a nudge.
