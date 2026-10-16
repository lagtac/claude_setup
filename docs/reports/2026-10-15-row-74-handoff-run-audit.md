# Audit: where two `my:handoff` runs needed the user (zitamu rows 74a and 74b)

**Status:** current, 2026-10-16. Nine findings (H1 to H9) from the transcripts of zitamu rows 74a and 74b, from "let's spec row 74" to the `done` marks; routed to rows 60 to 63 and notes on rows 8, 43 and 55.

## How to read this report

| Document | Path | Why |
| --- | --- | --- |
| Session archives | `~/Documents/claude/sessions/zitamu-row-74a/`, `~/Documents/claude/sessions/zitamu-row-74b/` | Copies of the eleven transcripts, with their `subagents/` and `tool-results/` folders. Claude Code deletes the originals after 30 days. |
| Timeline script | `docs/reports/assets/2026-10-15-row-74-handoff-run/timeline.py` | Prints one session's timeline and its numbers. All figures below come from it. |
| Earlier timing | `docs/reports/2026-10-14-superpowers-fit-critique.md`, section B2 | The same agent/user/away split, over 54 spec sessions. |
| Handoff skill | `plugins/my/skills/handoff/SKILL.md` | The plan, code and review stages, and the stop table. |
| Method | `global/methods/my.md` | The Spec → Plan flow and the "supervised or auto?" question. |
| zitamu documents | `~/projects/zitamu/real-estate-webapp/docs/plans/2026-10-15-agent-request-list-*` | The brief, the two specs, the two plans and the reviews that the runs wrote. |
| zitamu audit | `~/projects/zitamu/real-estate-webapp/docs/reports/2026-10-16-component-extraction-audit.md` | Row 130, which the user started after H9. |
| Roadmap rows | `ROADMAP.md` rows 8, 29, 43, 53, 55 | Open rows that these findings feed. |

## Verdict

Once the spec was approved, the run needed the user twice, and both times were avoidable.

The plan, code and review stages ran for 91 minutes with no input. They wrote the plan, six tasks with tests, three reviews and one fix round, then squash-merged. The two waits came before and after them. First, a question the rules require asked the user to confirm "auto", which the spec had already chosen (H3, 8 minutes). Second, the run stopped before its last step on an uncommitted file that it had noticed 90 minutes earlier, at launch (H4, 29 minutes).

The user's time went into the spec: 117 minutes of answering, plus 77 minutes away in the middle of it. In 21 of the 24 questions that had a recommended option, the user picked that option. In 2 of the other 3, the user chose more autonomy than the agent proposed.

Row 74b ran the same night from a spec written in the same session as 74a's. It confirms the part after the spec: 103 minutes of agent time, one question at launch (H3 again), and no stop. It also shows the limit of that part. The run shipped a Medium bug that its own fix round made, recorded only in a finished plan (H8). And while the code stage ran, the user found that the spec built every drawn element inside one page, with no shared component (H9).

So the goal, "hand part of the roadmap to an agent with minimum input", is mostly met after the spec and mostly unmet before it. What the run builds is only as good as the spec, and a known bug can ship with no row to fix it. Two runs are a small sample: treat the numbers as data points, not as rates.

## Method

- **Sample.** Eleven main sessions in `~/projects/zitamu/real-estate-webapp`, 2026-10-14 to 2026-10-16, and their subagent transcripts.
  - Row 74a: four sessions in tmux session `0` (the specs, the plan, the code, the review). Two came before them: `d33555d9`, a fork session that drafted the first spec, and `5878017d`, the design dialogue.
  - Row 74b: the launch `f4a0e76e`, then the plan, the code and the review. Its spec came from `bdd67ce8`, with 74a's.
  - `5c62d226`: a session the user opened during the 74b run to ask about the roadmap. It is not part of the run; H9 cites it.
- **Times.** Shown in local time (UTC+3), to match the commit times. A session ends at its last assistant record.
- **Time classes**, as in the earlier report:
  - *Agent:* the agent is working, its subagents included.
  - *User:* the agent waits for a message or a question answer, for up to 30 minutes.
  - *Away:* any single wait over 30 minutes.
  - *Blocked:* a stop of the run that waits for the user to act; counted as user time by the script, and moved here by hand.
- **Questions.** Every `AskUserQuestion` call, with its options and the answer. An answer counts as "recommended" when its label holds `(Recommended)`.
- **Limits.**
  - "User" time may be time spent in another session. The transcripts cannot tell the two apart.
  - The fork session `d33555d9`, which wrote a first draft of the spec on 2026-10-14, is archived but not timed. Row 53 already records what it did.
  - The script counts the gap before the user's next message as a wait, even after a run has finished. The 74b review stage ended at 00:03; the next message, at 07:13, was a new question. That gap is left out by hand.

## The runs, stage by stage

### Row 74a, the API

| Stage | Session | Local time | Wall | Agent | User | Away or blocked | Input from the user |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Brief and design dialogue | `5878017d` | 15:24–18:56 | 212 min | 45 min | 89 min | 77 min away | 24 messages, 20 question prompts |
| Specs and spec reviews | `bdd67ce8` | 19:00–20:01 | 61 min | 33 min | 28 min | 0 | 2 messages, 4 question prompts |
| Plan and plan review | `a9d6a45b` | 20:01–20:30 | 29 min | 29 min | 0 | 0 | none |
| Code, six tasks | `360d3e0a` | 20:30–20:56 | 27 min | 27 min | 0 | 0 | none |
| Reviews, fix round, merge, `done` marks | `5f6b0a2c` | 20:56–22:01 | 64 min | 35 min | 0 | 29 min blocked | 1 message: "ok i commited" |
| **Total** | | 15:24–22:01 | 393 min | 169 min | 117 min | 106 min | |

### Row 74b, the page

| Stage | Session | Local time | Wall | Agent | User | Input from the user |
| --- | --- | --- | --- | --- | --- | --- |
| Launch | `f4a0e76e` | 22:18–22:21 | 4 min | 1 min | 3 min | "let tackle row 74b", then "supervised or auto?" |
| Plan and plan review | `45291d5d` | 22:21–22:47 | 26 min | 26 min | 0 | none |
| Code | `36c57db2` | 22:47–23:32 | 45 min | 45 min | 0 | none |
| Reviews, fix round, merge, `done` marks | `7e9a17f8` | 23:32–00:03 | 31 min | 31 min | 0 | none |
| **Total** | | 22:18–00:03 | 106 min | 103 min | 3 min | |

The 74b run merged as `3139ca3` and marked its documents `done` in `d7bd56c`. No fixups waited, so it had nothing to fold.

### Where the agent's time went

In row 74a's three stages that ran alone:

- **Plan, 29 minutes.** 11 minutes reading code and writing the plan, 15 minutes for the plan review, 3 minutes for fixes and the commit.
- **Code, 27 minutes.** About 3 minutes per task, each with a red step, a green step and deliberate breaks. Then 6 minutes of checks the advisor asked for, which added one more e2e check.
- **Review, 35 minutes.** 9 minutes of tests and e2e, 10 minutes for three parallel reviews, 2 minutes for the fix round, 12 minutes for the e2e rerun and the final re-review, then the merge.

Tokens, for scale. Cache reads dominate, because each tool call reads the whole context again. Rows without a prefix are 74a.

| Session | Output tokens | Cache reads |
| --- | --- | --- |
| Brief and design dialogue | 210k | 53.6M |
| Specs, with 5 subagents | 132k | 36.4M |
| Plan, with 1 subagent | 76k | 11.6M |
| Code | 100k | 21.8M |
| Review, with 7 subagents | 55k | 24.3M |
| 74b plan, with 1 subagent | 95k | 20.7M |
| 74b code | 156k | 41.3M |
| 74b review, with 9 subagents | 106k | 29.9M |

## Findings

### H1. The user's time is in the spec, not in the run

**Evidence.**

- All 117 answering minutes fall in the two spec sessions. The plan and code stages took no input. The review stage took one message, and only because of H4.
- The design dialogue ran for 3.5 hours. At its end, the user rejected a question after 8 seconds and wrote "can we please start in a new session". The session `bdd67ce8` is that restart.

**What it means.** The auto run already does what the goal asks once a spec is approved. The next gain is in the dialogue before the spec: fewer questions, and a session short enough to finish. Rows 53 "`my:draft-spec`" and 55 "Decisions that go back to the user" already aim there.

### H2. The user picked the recommended option 21 times out of 24

**Evidence.**

- 27 questions were answered. 24 had a recommended option, and 21 answers picked it.
- The longest single wait, 15 minutes, ended in "Accept all (Recommended)" for 16 design findings from the two spec reviews.
- The 3 answers against the recommendation:
  - «Απεσταλμένα» also groups by client: a product choice.
  - "May row 74's spec run in auto mode?": the agent recommended "No, supervised"; the user chose "Yes, add Delegation".
  - "Design-changing findings": the agent recommended `stop`; the user chose `decide`.

**What it means.** Most questions confirmed a default the agent had already chosen. A list of defaults that apply unless the user vetoes them would have cost the user one read, not 24 answers. Row 55 decides which choices must still go back to the user; this is evidence for it.

The two answers that went against the agent both asked for more autonomy. Row 8 plans to flag `decide` on a spec that changes a contract. Row 74a changes a public contract, and its user chose `decide` on purpose. So row 8's flag should inform the user, not push them toward `stop`.

### H3. A default confirmed by hand

**Evidence.** At 19:52, after "i approve", the agent asked "Hand off 74a's plan, supervised or auto?". The user answered "Auto" at 20:00, 8 minutes later. The spec already had a Delegation section, which the user had asked for at 18:54 with "Yes, add Delegation".

It happened again in row 74b. The launch asked "Hand off the plan for row 74b, supervised or auto?", and the user answered "Auto (Recommended)" after 3 minutes. 74b's spec has a Delegation section too.

**Cause.** `global/methods/my.md`, Spec → Plan flow, step 3: "When the approved spec has a Delegation section, ask 'Hand off the plan, supervised or auto?' instead." The rule asks again what the Delegation section already answered.

**Proposal.** When the approved spec has a Delegation section, approval starts the auto run. The agent says so in one line, and the user can still say "supervised". Small. A new row.

### H4. The method looks for project facts only in `CLAUDE.md`

**Evidence.**

- `/kit:setup my` committed a `## Project facts` block and the method import into zitamu's `CLAUDE.md` on 2026-10-13 (`8f31ae7`). The user keeps both in `CLAUDE.local.md`, which git ignores.
- At 17:37, in the design dialogue, the user rejected a question with "the project facts are in claude.local".
- The user's edit that removed the block from `CLAUDE.md` sat uncommitted in the main checkout during the run.
- At 20:01, the launching session warned: "`CLAUDE.md` has an uncommitted change that is not mine … will stop it near the end".
- At 20:30, the plan stage skipped the fold of the spec's fixups for the same reason.
- At 21:31, the review stage merged, then stopped: the fold needs a clean `main`. It sent a push notification.
- The user committed the edit at 22:00 as `1a6a2da` ("clean CLAUDE.md from unintended write"). The run finished at 22:01, after a 29-minute wait.
- The fold rewrote the squash commit from `9be5f5e` to `5a83fcf`. The push notification and the stage's report had already cited `9be5f5e`.

**Cause.** Two gaps combined:

- `global/methods/my.md` checks for the facts block only in `CLAUDE.md`, and `kit:setup` writes it only there. It does not accept `CLAUDE.local.md`, although the "Parallel runs" section already may live in either file.
- In a project without a "Parallel runs" section, the approval edits are fixups. Folding them needs a clean `main`, and the run noticed the dirty file at launch but did not ask about it then.

**Proposal.**

- The facts check in `global/methods/my.md` and `kit:setup` accept `CLAUDE.local.md` too, as the "Parallel runs" rule does. `kit:setup` asks which file to use. Small. A new row.
- As a safety net, the auto run checks at launch, while the user is still present, whether `main` holds changes that it does not own and that would block the fold. If so, it asks once: commit them, stash them, or start anyway. This moves a stop from the end of the run to its start. It belongs with row 43 "`handoff` start checks as a script". Small.

It did not recur in row 74b: `main` was clean, and no fixups waited.

### H5. Questions in words the user does not use

**Evidence.** The user rejected 2 question prompts, holding 5 questions, because the words were unclear:

- The `my:architect` force table, 4 questions asked as "Force 5, consistency …", was followed at 15:29 by "explain the difference between the options you presented". After the answer came the 77-minute gap.
- "Which group choices should each tab offer?" was rejected at 17:38 with "wtf is a tab. i don't understand the question".

Two more prompts were rejected for other reasons: one over the facts file (H4), and one at the end of the 3.5-hour session (H1).

**Cause.** The questions used the agent's terms: "force", "tab", internal labels. The `plain` output style defines terms in chat prose, but the question text did not follow it.

**Proposal.** One line in `global/output-styles/plain.md`: question prompts follow the same rules, and name a screen element by what the user sees on the screen. Small. A new row.

### H6. Addressed while the run was going

- **"Does it look right to you?"** The user typed it, or "can you find any gaps?", 5 times in the design dialogue. Commit `d5a3a37` (18:26) made the check part of each section. The user still asked twice after it, at 18:30 and 18:35, because a running session keeps the rules it loaded at its start. No later session has presented design sections yet, so the fix is not tested.
- **The canvas mixed chosen and dropped designs.** The user said "the organization is not at all clear" at 18:44. Commit `a1caae5` added "Keep a canvas sorted by status".
- **The fork draft of the spec was replaced.** Row 53 already records this.

No new row. Row 29 checks whether the section check works in the next design dialogue.

### H7. Two small slips in the review stage

- **A rule read after the step it governs.** The stage edited the plans index in the worktree. Five minutes later it read rule 11 of `docs-layout.md`, which forbids that, and undid it. Cost: about 2 minutes.
- **A review read the wrong range.** The security review's skill diffed against `origin/main` and saw about 200 files. The reviewer noticed and read the 11 branch files by hand. `global/methods/my.md` already warns about this. It happened again in row 74b, and the reviewer recovered again.

No row yet: both slips cost minutes, and the reviewer recovered each time. Row 29 keeps counting them.

### H8. A known bug shipped with no row to fix it

**Evidence.**

- Row 74b's end-of-branch `/code-review high` found 2 Medium, 6 Low and 3 Nit findings, and the soundness review found three more. One fix round answered the findings the run classed as fixes.
- The re-review then found one new Medium bug that the fix round itself had made. With a link to a deleted client, a switch of lists during the retry leaves the dead client in the address and the filter, with no warning.
- The stop table says only a new Critical finding goes back to the user. So the run recorded the bug, with its steps and its known fix, in the plan's **Risk** section, merged, and marked the plan `done`.
- zitamu's roadmap says only "one Medium regression from the review's fix round" in its "Done" note for 74b. No open row fixes it.
- The next morning, the user asked "which rule is this exactly that allows only one fix round".

**Cause.** "One fix round per review" in `global/methods/my.md` sends every lesser re-review finding to **Risk**. **Risk** was meant for "input that today's code never produces". This bug is reachable today. A finished plan is never read again, so the bug has no owner.

**Proposal.** A re-review finding that today's code can reach becomes a roadmap row, a bug fix, in the same commit as the `done` marks. **Risk** keeps only the limits about input that today's code never produces. The rule of one fix round stays, so the rounds still end. Small. A new row.

### H9. The spec built every drawn element inside one page

**Evidence.**

- While 74b's code stage ran, the user asked in `5c62d226` whether the spec created shared components. The answer: no. The spec built about 15 drawn elements inside `pages/requests/index.vue`, on purpose.
- The user replied "it's too late for this, 74b code stage is already running".
- No review flagged it. The spec review rated the spec's fit with existing code "Strong", because it reuses `ZSegmented`, `ZButton` and other components. It did not ask whether the new elements should become shared ones.
- The same session added a spec rule in claude-setup, `7e938b9` ("a spec names the other pages that use each drawn element"). In zitamu it added row 130, a component extraction audit, done on 2026-10-16. That audit produced rows 132 to 138.

**What it means.** The auto run builds what the spec says, and builds it well. The user's attention paid off here at the spec, as in H1. A gap the spec review does not check reaches `main`.

No new row: `7e938b9` adds the rule, and zitamu's rows 130 to 138 handle the code. Row 29 checks that the next spec with drawn elements follows the rule.

## Where these went

Routed on 2026-10-16, with the user's yes.

| Finding | Route |
| --- | --- |
| H1 | Evidence for rows 53 and 55, cited in row 55. No new row. |
| H2 | Evidence for row 55 (a veto list of defaults), cited there, and a note on row 8 (inform, do not push toward `stop`). |
| H3 | Row 61 "Delegation approval starts the auto run". |
| H4 | Row 60 "Project facts in `CLAUDE.local.md`", and a note on row 43: the launch asks about changes on `main` that would block the fold. |
| H5 | Row 62 "Question prompts follow `plain`". |
| H6 | No new row: addressed by `d5a3a37` and `a1caae5`, and recorded in row 53. Row 29 checks `d5a3a37` in the next design dialogue. |
| H7 | No row yet; row 29 counts both slips. |
| H8 | Row 63 "A reachable re-review finding becomes a bug row". 74b's Medium bug gets its own row in zitamu's roadmap. |
| H9 | No new row: addressed by `7e938b9` and zitamu rows 130 to 138. Row 29 checks the rule in the next spec. |
| Method | Row 29 "Measure the auto runs" can reuse `timeline.py`, and rechecks H6, H7 and H9 on the next runs. |
