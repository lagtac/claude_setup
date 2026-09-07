# Audit: `my:soundness-review` — is it in good shape, and can it truthfully catch bugs and architectural mistakes?

**Date:** 2026-09-07
**Subject:** `my-plugin/skills/soundness-review/SKILL.md`, `my-plugin/skills/soundness-review/code-reviewer-prompt.md`, `my-plugin/agents/code-reviewer.md`
**Method:** read all three files in full; checked git history of the skill; read the one review artifact on disk produced by it; checked the agent's tool grant against what its criteria demand. No synthetic repo was built — one finding (#3) is stated conditionally because it only manifests on a diverged branch.

## Short answer

- **Bugs: no, and that is deliberate.** The skill disclaims line-level bug-finding in three places and routes it to the built-in `/code-review`. It is not a bug net.
- **Architectural mistakes in *plans*: yes, this is its strongest mode.** Dimension 5 forces the reviewer to verify the plan's claims against the repo, which is the mechanism that actually catches false premises, stale references and missing callers.
- **Architectural mistakes in *diffs*: weakly, and for a structural reason** — the reviewer is told to stay inside the payload, which is not enough context to judge abstraction level or layer boundaries (finding #4).

The design is coherent and unusually well-specified for a prompt artifact: mode detection, placeholder substitution, an explicit out-of-scope boundary, severity-conditioned surfacing, and a mandatory reasoning paragraph before the verdict. The problems below are specific and mostly one-line fixes; none require rethinking the approach.

## Findings that change whether it works

### 1. The agent file contradicts the dispatch prompt on the one sweep that yields a Critical finding

`my-plugin/agents/code-reviewer.md` states, with no exception:

> **Diff-review: stay within the payload.** Use `Read` / `Grep` / `Glob` only to assess a finding's context … do not widen the review beyond the payload.

`code-reviewer-prompt.md` states the opposite for the removed/renamed-symbol case:

> **Exception:** if the payload removes or renames a symbol that may be referenced elsewhere, you MUST widen — text-search the whole repo for the name token … This is the one case where widening is required.

The agent definition is the system prompt; the dispatch text arrives as user input. A conflict here is resolved unpredictably, and the casualty is the orphaned-caller sweep — which diff dimension 4 designates a **Critical** finding. This is the single highest-value check the skill performs on a diff, and it is the one the two files disagree about.

**Fix:** copy the exception sentence into the agent file's "stay within the payload" bullet.

### 2. Plan dimension 5 demands a tool the agent does not have

Plan criteria, dimension 5:

> independently sweep the repo — **both** a symbol-reference tool **and** a plain text search for the name token

The agent's grant is `tools: Read, Grep, Glob, Bash, Write`. There is no symbol-reference tool (no `LSP`), and the string `LSP` appears nowhere in the skill or the agent. Per the project's own rule that agents are self-contained and do not inherit `CLAUDE.md`, the agent cannot infer it either. The reviewer will either silently do text-search-only while the report implies a two-tool sweep, or claim compliance it cannot deliver.

**Fix:** either add `LSP` to the agent's `tools:` and name it explicitly in the criteria, or drop the requirement to "a plain text search for the name token (`grep`), which catches string-literal references symbol tools miss." The second is honest and loses little — text search is the half that finds the references symbol tools cannot see.

### 3. `git diff "$RANGE"` is a two-endpoint diff, not a merge-base diff

Step 1, committed-range mode, runs `git diff "$RANGE"` on the user's literal `BASE..HEAD` token. Git treats `git diff A..B` as identical to `git diff A B` — the endpoint-to-endpoint diff. Only `A...B` (three dots) diffs from the merge base.

Consequence, on a branch that has diverged from its base (base has commits the branch does not): the payload includes base-only changes rendered as *reversions*, and the reviewer will report deletions the branch never made. On linear history the two forms are identical, which is exactly why this survives casual testing. The paired `git log "$RANGE"` two-dot form *is* correct, which makes the mismatch easy to overlook.

**Fix:** for the diff, use the merge base explicitly — `git diff "$(git merge-base BASE HEAD)" HEAD` — or normalise a `..` token to `...` for the diff command only, leaving `git log` on two dots.

### 4. "Stay within the payload" structurally undercuts dimensions 2 and 3

Diff dimensions 2 (*Architecture & pattern fit* — "follows existing conventions, sits at the right abstraction level, respects layer boundaries") and 3 (*Soundness of approach* — "treats the root cause, not a symptom") cannot be judged from changed lines plus three lines of context. Judging whether a change fits the codebase's conventions requires seeing the conventions; judging root-cause-vs-symptom requires seeing the cause. The instruction permits `Read`/`Grep` "only to assess a finding's context" — i.e. only *after* a finding already exists — which inverts the order: the reading is what produces the finding.

This is the reason the diff mode is weaker at architectural judgment than the plan mode, where grounding is mandatory rather than discouraged.

**Fix:** replace the restriction with a positive instruction — read every file the payload touches *in full*, plus one or two sibling files in the same directory, before assessing dimensions 2 and 3. Keep the prohibition where it belongs: on *reporting* on code outside the payload.

## Secondary findings

- **No verification pass.** Severity and confidence are self-assessed in a single agent turn, with no adversarial check that a finding is real. The built-in `/code-review` runs a verify step; this skill does not. A confidently-worded false positive reaches the report with a `High` label and no counterweight. Mitigation short of a second agent: require each Critical finding to cite a repo location the reviewer actually opened, not only a diff line.
- **Report filenames collide and overwrite silently.** Diff-review writes `<YYYY-MM-DD>-<branch>-review.md`; two reviews of the same branch on the same day overwrite. Plan-review's slug (`<plan-basename>-plan-review`) carries **no date at all**, so every re-review of a plan destroys the previous one. Step 4 only checks the file exists, never whether it already existed. Suggest a `-2` suffix on collision, or at minimum a date prefix on the plan-review slug.
- **The mandatory "Arguments this is sound" table manufactures filler.** The output schema requires the table, so when a change has no affirmative case the reviewer invents one. The evidence is on disk in `docs/plans/2026-05-08-skill-consolidation-smoke-review.md`, which filled it with "Small surface area, easy to review and revert — Weak" and "filename suggests this is a deliberate fixture" — neither is an argument that the change is sound. This quietly erodes the anti-sycophancy framing the rest of the prompt works to build. **Fix:** state that "None material." is a legal value for either table.
- **Default diff capture concatenates overlapping views.** `git diff` (worktree vs index) plus `git diff --staged` (index vs HEAD) yields two separate hunk sets for any file that is both staged and further modified, with line numbers that do not compose. `git diff HEAD` gives the single combined view; the untracked-file handling via `git diff --no-index` stays as is.
- **No diff-size guard.** Nothing caps the payload or degrades gracefully on a large range. A big pre-merge range can exhaust the reviewer's context with no signal to the caller that coverage was partial.
- **Background-dispatch wording.** Step 3 says "Do not run the agent in the background," but subagent dispatch is asynchronous by construction in the current harness; the caller waits regardless. Harmless, but the sentence promises control the caller does not have.

## Resolution

All findings above were fixed on 2026-09-07, in two commits.

**The four blocking findings** (commit `4166d72`): the agent/prompt contradiction now reads identically in both files; `LSP` was added to the agent's grant with a text-search fallback that reports a text-only sweep as such (the grant was verified live — the agent loads and its malformed-prompt guard fires); committed ranges diff from the merge base; and the payload restriction was replaced by an instruction to read every touched file in full before judging dimensions 2 and 3.

**The secondary findings** (this commit): a single collision rule now covers both slugs — the review path is checked before dispatch and suffixed `-2`, `-3` rather than overwriting, which closes the plan-review case (its date comes from the plan's filename and never changes) and the diff-review case (same branch, same day) together. `None material.` became a legal answer for the dual-perspective tables in *both* places it had to be legal: the schema, and the "present arguments BOTH for and against" directive that was the actual source of the filler — scoped so it does not erase the N/A rows the dimensions require. The default capture is now `git diff HEAD` plus the untracked loop, which is complete and non-overlapping. A 2000-line size guard warns and proceeds, passing the payload size into the prompt so uneven coverage is declared instead of hidden. And in place of a second reviewer pass, every `Critical` finding must now cite a repo location the reviewer actually opened, or be downgraded — the label has to be earned in-pass.

The "no verification pass" finding is therefore mitigated, not eliminated: labels remain self-assessed. A genuine adversarial check would need a second agent, which is a design change, not a fix.

## Track record

There is **no empirical evidence for the current version.** The only review artifact on disk, `docs/plans/2026-05-08-skill-consolidation-smoke-review.md`, cites "checklist item 6, item 4, item 9" and the old `/my:code-review` name — it was produced *before* commit `f1fb0c1` ("slim skill to judgment + plan-alignment, delegate bug-finding to built-in") replaced the bug checklist with the current soundness dimensions, and before `a7bdfc1` added plan-review mode at all. That smoke review is, ironically, a demonstration of the bug-scanning behaviour the current version explicitly disowns.

The skill has changed shape three times since (`f1fb0c1`, `a7bdfc1`, `7826990`) with no artifact from any of them. Plan-review mode in particular has never been observed running.

**Recommendation:** after fixes 1–4, run it once in each mode on real work — a diff that touches 2+ layers, and a plan from `docs/plans/` with a clean tree — and keep both artifacts as the baseline.

## Verdict

**Assessment:** Mixed — sound design, four specific defects, unproven.

The methodology is the good part and should not be rewritten. Findings 1 and 2 are contradictions between files that will produce silently degraded reviews rather than errors; 3 produces a wrong payload on diverged branches; 4 is the reason diff-mode architectural judgment underperforms plan-mode. All four are small edits.

The honest framing for the user: **this is a judgment instrument, not a bug detector.** It is at its best grounding a plan against the repo, and at its weakest reviewing a diff in isolation. Pairing it with `/code-review` — as the routing rule in `CLAUDE.md` already prescribes — is not optional polish; it is what makes the pair cover both halves.
