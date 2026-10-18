# Audit: where the time goes on zitamu, and what the steps cost

**Status:** current, 2026-10-18. Eight findings (W1 to W8) on the speed of the `my` workflow, from zitamu's git history (104 shipped rows) and 300 session transcripts; W8 became row 72, W1 to W5 are evidence for rows 29, 30, 55, 61 and 67, and W6 and W7 are zitamu proposals with no row.

## How to read this report

| Document | Path | Why |
| --- | --- | --- |
| Row metrics script | `docs/reports/assets/2026-10-18-workflow-speed/row-metrics.py` | Groups zitamu's shipped rows into units of work and measures each from git. Its output is `row-metrics.txt` and `rows.tsv` beside it. |
| Session time script | `docs/reports/assets/2026-10-18-workflow-speed/session-time.py` | Splits each session's time by what it waited for. Its output is `session-time.txt`. |
| Review findings script | `docs/reports/assets/2026-10-18-workflow-speed/review-findings.py` | Counts serious review findings before and after the code. Its output is `review-findings.txt`. |
| The experiment | `~/projects/zitamu/real-estate-webapp/docs/plans/2026-10-18-letter-case-and-crawl-checks-review.md` | zitamu rows 156 and 161, built on 2026-10-18 with no spec, no worktree and no review before the end (W4). |
| Earlier measurements | `docs/reports/2026-10-09-workflow-efficiency-critique.md`, `docs/reports/2026-10-14-superpowers-fit-critique.md` (B1, B2), `docs/reports/2026-10-15-row-74-handoff-run-audit.md` (H1) | The same questions on fewer sessions. |
| Roadmap rows | `ROADMAP.md` rows 29, 30, 55, 61, 67 and 72 | Where these findings go. |

Each script has its usage at the top. Run the zitamu ones from the zitamu checkout. Claude Code deletes transcripts after 30 days, so the `.txt` and `.tsv` files keep the numbers this report quotes.

## Verdict

**The workflow's steps are not what slows a row down. The waits between them are.**

- Of 350 session hours, the sessions spent 56% waiting for the user and 16% waiting for another session. The model's own work was 18%, and tool calls 6% (W1, W2).
- Writing documents is cheap. Large units write 3.9 lines in `docs/plans/` per code line, yet take no longer than Medium units (W3).
- The reviews earn their place. 90% of the serious findings are caught before the code exists. When the spec and its review were skipped, the findings did not go away: they all came after the code, and the fix round was much larger (W4).
- The cost jumps between Small and Medium: from a median lead time of 1.4 hours to 14.7 hours. The difference is the stop for spec approval, not the work (W3, W5).

## Method

- **Rows.** `row-metrics.py` reads every ✅ row of zitamu's `ROADMAP.md`. It finds a row's commits through the row number in commit messages, the `docs/plans/` files the row links, and hashes cited in the row or its files' status lines. Rows that share a branch or a spec are one unit of work: the 104 rows make 58 units, and 48 of them hold code written in this workflow.
- **Size.** It is inferred from the linked files: spec and plan = L, spec only = M, neither = S, plan only = P (early rows). Row 67 will replace these sizes, so this is a snapshot of the old rule.
- **Time from git** is a commit-time proxy. It cannot see work before the first commit, such as brainstorming.
- **Time from transcripts.** `session-time.py` reads the 300 top-level transcripts from 2026-09-18 to 2026-10-18. Each gap between two events gets the label of the event that ends it, so the labels add up to the session's time. Gaps over two hours count as away.
- **Stage** comes from the session title's first word (`spec-`, `plan-`, `code-`, `review-`, `fix-`). Only 88 of the 300 sessions have one.
- **Parallel sessions.** The user runs several sessions at once. A session's wait is delay for its row, not idle time for the user.

## Findings

### W1. Most of a session's time is waiting for the user

| Time ends in | Hours | Share |
| --- | --- | --- |
| a prompt the user types | 162.4 | 46% |
| an answer to a question (AskUserQuestion) | 34.1 | 10% |
| a message from another session | 55.3 | 16% |
| the model's own work | 61.4 | 18% |
| a tool call in the foreground | 22.7 | 6% |
| a background run finishing | 11.8 | 3% |

Review sessions spend 46% of their time waiting for the user, because they end with findings for the user to decide. The spec sessions' share is 50%, but only 2 are titled. This repeats the run audit's H1 on 300 sessions in place of 11.

### W2. Hand-offs between sessions cost as much as the model's own work

Plan sessions (n=19) spend 40% of their time, and code sessions (n=33) 38%, waiting for a message from another session. In total that is 55 hours, close to the model's 61. Each `my:handoff` stage boundary is a wait.

### W3. Large costs stops, not code

| Size | Units | Code lines (src + tests) | Lines in `docs/plans/` | Lead time (h) | Working time (h) |
| --- | --- | --- | --- | --- | --- |
| S | 17 | 252 | 0 | 1.4 | 2.3 |
| M | 7 | 719 | 757 | 14.7 | 4.8 |
| L | 18 | 772 | 2,726 | 15.0 | 5.3 |

Medians. Large and Medium units change about the same amount of code and take about the same time. Large writes 3.6 times the documents, but writing is fast, so the documents are not the cost. The jump is from Small to Medium: ten times the lead time for three times the code. That is the stop for spec approval and the hand-offs that follow it.

Plan reviews still find a median of 3 serious findings, against 5.5 for spec reviews (`review-findings.txt`). So the plan stage is not wasted. Git cannot tell whether a later stage would have caught those 3.

### W4. Skipping the spec moves the findings to after the code

Across the 33 features with a spec review, 90% of the serious findings (Critical and Warning) came before the code: a median of 8 before and 1 after.

On 2026-10-18, zitamu rows 156 and 161 were built with no spec and no review until the end. That review found 6 Warnings and 1 Suggestion, all after the code. The user changed 3 of the agent's 8 decisions. The fix round changed 409 code lines, 46% of the branch's 883 (`git diff --numstat` without `.md`; 19% without the taxonomy file the user added). Five fix rounds sampled from workflow branches changed between 1% and 22% of their branch. Kostas's commits, made outside the workflow, show the same pattern: about 6 findings per review.

### W5. Small work is lean, apart from its bookkeeping commits

Small units take a median of 1.4 hours from start to merge. They write nothing in `docs/plans/`, and 80% of their working time ends in a code commit. But each has a median of 3 docs-only commits for its 1 code commit: adding the row, placing it in the order, and the `done` mark. In 10 of the 15 Small units with a kept branch, the review led to a code fix, so the review still finds things.

### W6. The full e2e suite runs more than once in most sessions (zitamu)

There were 200 full e2e runs, at a mean of 4.1 minutes each: 13.7 hours. Of the 79 sessions that ran the suite, 54 (68%) ran it two or more times. A rerun of one failed test against a preview takes seconds.

### W7. Nothing shows what the security review finds on Small work (zitamu)

zitamu runs `/security-review` at the end of every branch, Small ones included (its `CLAUDE.local.md`, 2026-09-29). Small changes write no review file, so its findings there cannot be counted. The one data point, the copy change of W4, gave it nothing to find.

### W8. Each report builds its own measurement script

This is the fourth report to build one-off scripts for the same questions: `extract.py` (2026-10-09), `stage_split.py` and `spec_time.py` (2026-10-14), `timeline.py` (2026-10-15), and the three here. Row 29 will need them again.

## Limits

- **Row-metrics edge cases.**
  - One unit holds 19 tangled rows (zitamu rows 73 to 94).
  - A code commit shared by rows in different units counts in full for each.
  - Rows 20, 100, 130 and 146 have no code commit at all.
- Only 194 of the 390 background review agents were matched to their finish time, so review time is understated.
- The S, M, L split infers size from links, not from what each row's session chose.

## Where these went

Routed on 2026-10-18, with the user's yes.

| Finding | Route |
| --- | --- |
| W1 | Evidence for row 55 (which decisions go back to the user) and row 61 (start the auto run on approval). No new row. |
| W2 | Evidence for row 30 (split `my:handoff` by mode); row 29 measures the hand-off waits again. No new row. |
| W3 | Evidence for row 67: the cost is the stops between Small and Medium, not the documents. No new row. |
| W4 | Evidence for row 67: any work that makes product decisions keeps a reviewed spec. No new row. |
| W5 | Evidence for row 67: Small's 3 bookkeeping commits per code commit. One could merge the `done` mark into the squash commit. No new row. |
| W6 | zitamu proposal, no row: after a failed full run, rerun only the failed tests against a preview, then one full run at the end. |
| W7 | zitamu proposal, no row: name Small sessions `r<row>: …` so `session-time.py` can measure the security review's cost before deciding. |
| W8 | Row 72 "Workflow metrics as one `my` script". Row 29 uses it. |
