# Opus 4.7 Prompt Tuning Plan

## Context

A community article ("Opus 4.7 'Regression': Why Your Prompts Stopped Working") documents a behavioral shift in Opus 4.7: the model now follows instructions **literally** rather than charitably guessing intent. Specifically:

- Vague instructions get vague output (no helpful padding).
- Adaptive thinking allocates less reasoning to questions that *look* simple — even if they're not.
- Output length matches perceived complexity, not user expectation.
- Tone is more direct; less "warmth"-based padding.

The article also flags an API-layer change (custom `temperature` / `top_p` rejected; use `effort` levels instead). **That fix is out of scope here** — this plugin ships prompt templates, not API calls, and has no place to set sampling parameters. Four of the article's five fixes apply; FIX 4 does not.

This plugin (`my`) ships **prompt templates** (commands, agents, skills) that downstream Claude instances execute. Several of these templates were written for 4.6's "helpful guesser" personality and now under-specify what they want. Notably, **agents do not inherit `CLAUDE.md`** (per `CLAUDE.md` in this repo), so any standards they must follow have to be embedded directly — and several agents currently aren't.

Goal: tighten the templates so they keep working on 4.7 without bloating them. The fix pattern across the article's five recommendations is identical — **add specificity** (scope, reasoning, format, thoroughness).

## Audit Summary

Files were graded on three failure modes the article calls out:

- **S** (Scope): does the prompt enumerate the dimensions to cover?
- **R** (Reasoning): does the prompt explicitly request step-by-step reasoning when needed?
- **F** (Format): does the prompt specify output structure?

| File | S | R | F | Severity |
|---|---|---|---|---|
| `my-plugin/agents/planner.md` | ❌ | ❌ | ❌ | **CRITICAL** |
| `my-plugin/commands/commit.md` | ❌ | ❌ | ❌ | **CRITICAL** |
| `my-plugin/agents/code-reviewer.md` | ✅ | ⚠️ | ✅ | Medium |
| `my-plugin/commands/push.md` | ⚠️ | n/a | ⚠️ | Medium |
| `my-plugin/commands/laravel-debug.md` | ✅ | ⚠️ | ✅ | Medium |
| `my-plugin/commands/task.md` | ⚠️ | ✅ | ✅ | Low |
| `my-plugin/commands/code-review.md` | n/a (delegates) | n/a | n/a | Low |
| `my-plugin/commands/plan.md` | n/a (delegates) | n/a | n/a | Low |
| `my-plugin/agents/laravel-fullstack-expert.md` | ✅ | ⚠️ | ✅ | Low |
| `my-plugin/agents/summarizer.md` | ✅ | ✅ | ✅ | OK |
| `my-plugin/skills/*` | ✅ | ✅ | ✅ | OK |
| `my-plugin/commands/clean-gone-branches.md` | ✅ | n/a | ✅ | OK |
| `my-plugin/commands/laravel-{code-review,migration-check}.md` | ✅ | ⚠️ | ✅ | OK |
| `my-plugin/commands/optimize-prompt.md` | ✅ | ✅ | ✅ | OK |

Skills are uniformly strong (digraphs, examples, explicit confirmation gates). The damage is concentrated in **`planner.md`** and **`commit.md`**, with smaller cuts in a handful of other files.

## Files to Modify

### Critical

**`my-plugin/agents/planner.md`** — Currently 5 numbered steps, no embedded output format, no exploration discipline, no trade-off requirement. Because agents don't inherit `CLAUDE.md`, the planner today produces under-specified plans on 4.7. Embed a self-contained spec covering:
- Mandatory exploration (Glob → Grep → Read → patterns → existing solutions)
- "Show your reasoning before proposing changes"
- Output format matching the user's `CLAUDE.md` plan structure (Context, Files, Steps, Trade-offs, Dependencies, Risk, Testing, Open Questions)
- Explicit "challenge assumptions; if the codebase already solves this, say so"
- Trade-off analysis requirement for non-trivial decisions

**`my-plugin/commands/commit.md`** — Currently 2 lines. On 4.7 this can produce one giant commit with a one-line message. Replace with explicit numbered steps: (1) `git status` + `git diff` to inventory changes; (2) check for `.env`/secret files and warn; (3) group changes into logical units, one commit per coherent change; (4) write Conventional Commit subject + body explaining the *why*; (5) never use `--no-verify` unless asked.

### Medium

**`my-plugin/agents/code-reviewer.md`** — Add: "Evaluate **every** item in the Review Checklist before producing output — do not skip items even if they look inapplicable; mark them N/A explicitly." Add: "Before assigning a Verdict, show reasoning that ties checklist findings to the verdict." This forces 4.7 to allocate thinking budget rather than declaring early.

**`my-plugin/commands/push.md`** — Specify abort conditions: (a) abort if `git status` shows uncommitted changes (don't auto-stash); (b) if local diverged from upstream, stop and report — never force-push without explicit instruction; (c) if no upstream, stop and report — **do not** auto-set upstream (that's convenience the user didn't ask for, and 4.7-literal means we shouldn't add it). Auto-set-upstream behavior is moved to Open Questions for explicit decision.

**`my-plugin/commands/laravel-debug.md`** — The phrase "Use the laravel-fullstack-expert agent **and sequential-thinking**" references a non-standard concept. Replace with the article's recommended power phrase: "Think step-by-step. Show your reasoning at each diagnostic step before drawing conclusions."

### Low

**`my-plugin/commands/task.md`** — Already uses "Ultrathink step-by-step" (good). Add an explicit scope enumeration in the Approach section: "Analyze for: (1) edge cases, (2) error paths, (3) concurrency/state assumptions, (4) integration points with existing code."

**`my-plugin/agents/laravel-fullstack-expert.md`** — Add a single line in the Output Format section: "Before listing recommendations, show one-paragraph reasoning that connects the observed code to the chosen recommendations." Already heavy on structure — only one targeted addition.

**`my-plugin/commands/code-review.md`** and **`my-plugin/commands/plan.md`** — Both are one-line dispatchers. Once their target agents are tightened, the dispatchers don't need work. **No change.**

### Skipped (already strong)

- `summarizer.md`, all three skills, `clean-gone-branches.md`, the two other Laravel commands, `optimize-prompt.md`.

## Step-by-Step Implementation

Each step is a single commit on a worktree branch (`feat/opus-4-7-prompt-tuning`).

1. **`feat: tighten planner agent for Opus 4.7 literal-instruction behavior`** — rewrite `planner.md` with embedded exploration + plan output format + trade-off requirement. (Largest single change.)
2. **`feat: expand commit command with explicit step-by-step workflow`** — replace 2-line `commit.md` with the 5-step procedure.
3. **`feat: enforce checklist completeness and reasoning in code-reviewer agent`** — small additions to `code-reviewer.md`.
4. **`feat: specify abort conditions in push command`** — add explicit guards to `push.md`.
5. **`refactor: replace 'sequential-thinking' wording with explicit reasoning prompt`** — fix `laravel-debug.md`.
6. **`feat: enumerate analysis dimensions in task command`** — small addition to `task.md`.
7. **`feat: require reasoning paragraph in laravel-fullstack-expert output`** — one-line addition.
8. **`docs: note Opus 4.7 prompting principles in README`** — short section pointing at the article's takeaway: specificity > vagueness. (Optional; see Trade-offs.)

Steps 1–7 are independent and can land in any order. Step 8 is documentation and lowest priority.

## Trade-Offs / Alternatives Considered

**Option A — Surgical fixes per file (recommended).** Edit each problem file with tailored language. Pros: minimal churn; preserves the project's "agents are self-contained" principle; respects the article's own advice (don't pad templates that don't need it). Cons: seven files touched.

**Option B — Shared "4.7 preamble" prepended to every agent.** Generate or hand-paste a common block. Pros: DRY. Cons: violates the project's `CLAUDE.md` rule that agents must embed their own standards (the rule exists *because* agents don't inherit context); also bloats files that are already strong (skills, summarizer); also requires tooling or discipline to keep in sync.

**Option C — Fix only the two CRITICAL files; leave the rest.** Pros: smallest possible diff. Cons: known medium-severity issues remain; we'd be back here in a month.

**Recommendation: Option A.** The two CRITICAL fixes carry most of the value; the medium fixes are 1–3 lines each and prevent regressions in their respective workflows.

**Secondary trade-off — README/docs note (step 8).** Argument for: helps future-me remember why these prompts look the way they do. Argument against: README is for users of the plugin, not maintainers; this rationale belongs in commit messages and this plan file. **Lean: skip step 8 unless explicitly wanted.**

## Dependencies

None. All changes are edits to existing `.md` template files. No new packages, no config changes, no manifest updates.

## Risk

- **Reversibility: High.** Every change is a text edit to a prompt template; revert via `git revert`.
- **Blast radius: Medium.** These templates run inside *every* invocation of the corresponding command/agent. If a tightened prompt over-constrains the model, it could produce *worse* output than the loose original. Mitigation: keep additions surgical; avoid stacking constraints that conflict.
- **Token cost: Slight increase.** The article notes 4.7's tokenizer is already 1.0–1.35× more expensive per input. The planner rewrite adds ~40 lines; the commit rewrite adds ~10. Acceptable.
- **What could break:**
  - Tightened planner could refuse to plan when a request is genuinely simple (over-applying "challenge assumptions").
  - Tightened code-reviewer could produce verbose output on small diffs.
- **How to detect:** Run each modified command on a small/medium/large representative task and eyeball the output for over-constraint.
- **Manual steps:** None at deploy time. Plugin reload picks up the new templates.

## Testing Strategy

There is no automated test harness for prompts in this repo. Verification is manual:

1. **Planner**: invoke `/my:plan add a /my:foo command that prints hello` against this repo. Verify the produced plan in `$planDirectory/` includes Context, Files, Step-by-Step, Trade-Offs, Dependencies, Risk, Testing, and Open Questions sections.
2. **Commit**: stage two unrelated changes and run `/my:commit`. Verify it proposes splitting into two commits with Conventional Commit messages and bodies that explain *why*.
3. **Code-reviewer**: stage a diff with one obvious bug and one stylistic issue, run `/my:code-review`. Verify the output includes a reasoning paragraph before the verdict and explicit N/A markings for inapplicable checklist items.
4. **Push**: from a clean branch with no upstream, run `/my:push`. Verify it sets upstream rather than failing silently.
5. **Laravel-debug**: invoke `/my:laravel-debug some 500 error` against any Laravel repo (or a stub). Verify the output shows step-by-step diagnostic reasoning before recommendations.
6. **Task**: invoke `/my:task implement a debounce helper`. Verify the analysis explicitly addresses the four enumerated dimensions (edge cases, error paths, concurrency, integration).

If any check fails to show the new structure, the prompt edit didn't take effect — re-check that Claude Code reloaded the plugin (`/plugin reload` or restart).

## Open Questions

1. Do you want step 8 (README note) included, or is this plan file sufficient documentation?
2. Should the planner's embedded plan format match your global `CLAUDE.md` exactly (which it should, since they describe the same artifact), or do you want a slightly trimmed variant for plugin-internal use?
3. *(Resolved before ExitPlanMode — see clarifying question.)*
4. Is there an existing project where you've already noticed degraded behavior on 4.7 that we should use as the manual-test baseline?
5. Should `/my:push` auto-set upstream when none exists (`git push -u origin <branch>`), or stop and report? Current plan: stop and report (literal-instruction-safe).
