# Spec: brainstorming's paths replace the size table

**Status:** draft, 2026-10-18. Row 67; answers finding F1 of the superpowers-fit critique.

**Size:** Large. Under this spec's own rules it is "architectural with plan": it changes the rules
that nine projects follow, which is a contract. `my:architect` was skipped by the user's choice:
the change has no load, storage or data forces.

## How to read this spec

1. `docs/reports/2026-10-14-superpowers-fit-critique.md`, finding F1. The problem this spec
   answers.
2. `ROADMAP.md`, row 67 in "Superpowers fit", step 1 of "Order of work", and the open rows that
   carry a size (D10).
3. `global/methods/my.md`, sections "Size the process to the change", the trigger table under it,
   "Precedence", "Discovery authority", "Spec → Plan two-artifact flow", "Code Review Routing",
   "UI Design" and "One feature, four commits on `main`". The rules this spec changes.
4. The superpowers skills, version 6.4.2: `superpowers:brainstorming`, section "Three Paths"; and
   `superpowers:systematic-debugging`, Phase 4 step 5, "If 3+ Fixes Failed: Question
   Architecture". The paths and the escalation this spec adopts.
5. `global/rules/docs-layout.md`, sections "Kinds of document", "From report to roadmap",
   "Status line" and "One feature, four commits on `main`".
6. `plugins/my/skills/roadmap-management/SKILL.md`, rule 11 (line 174) and the two lines that
   repeat its order (121 and 163).
7. `plugins/my/skills/handoff/SKILL.md`, lines 37-38, 289 and 866; and
   `plugins/my/skills/handoff/README.md`, lines 54, 224, 226, 252, 273 and 285. Where the
   hand-off names a size.
8. `plugins/my/skills/design-system/SKILL.md`, line 132. Where the audit names a size.
9. `plugins/my/README.md`, sections "The size table", "Worktrees, squash-merge and four commits on
   `main`", "How each superpowers skill is used" and "Limits".
10. `projects/real-estate-webapp/claude-local.md`, zitamu's local file. Three sentences name sizes.
11. `plugins/kit/tests/test_neutral_core.py`, the list `METHOD_HEADINGS`. It names the heading this
    spec renames.
12. In the zitamu repo (`~/projects/zitamu/real-estate-webapp`),
    `docs/plans/2026-10-18-letter-case-and-crawl-checks-review.md`. The branch review of two rows
    done with no spec, which D5's two-file limit answers.

## Context

`my` has a size table: Small, Medium, Large. The size decides the documents, the reviews and the
commits. Superpowers' brainstorming has its own three paths: spike, bounded, architectural. The
two overlap, and only part of the overlap is settled. When an architecture brief exists, `my.md`
says brainstorming "classifies the task as architectural, never bounded or spike". Without a brief:

- a Medium change requires a spec, but brainstorming may call it bounded, which writes no spec;
- the rules do not say whether brainstorming may take the spike path at all.

The user's aim for `my` is to add to superpowers (the roadmap, the hand-off) and to adapt it (the
`docs/plans/` path), not to replace its thinking. The size table replaces brainstorming's own
choice of process, so it goes against that aim.

**Evidence.** Since 2026-10-03, across five projects (zitamu, claude-setup,
diagoradisa-annotator, grispy-ext, mv3-starter), 21 specs were Medium, 13 were Large and 1 is a
draft. So the Medium layout, a spec with its tasks inside, is used more than the Large one, and it
must stay. On zitamu `main` in the same period, 24 `fix:` commits landed, and only 2 had a spec.
Bugs mostly need no document.

**Evidence against a broad bounded path.** On 2026-10-18 a zitamu session did rows 156 and 161
with no spec, no plan and no hand-off. Row 156 changed the letter case of copy in 86 files of an
existing flow, so brainstorming could call it bounded. The session made eight copy decisions
without the user, and the user changed three of them after the code was written. Its branch review
(item 12) found 6 Warnings. By that session's own count of zitamu's review files, the median
workflow branch had 0 serious findings at its branch review, and about 8 at its spec and plan
reviews, before any code. The fix round was 46% of the branch's code, against a median of 9%. So
the problems were about as many, but they were found after the code. The review also found files
the edit missed, which a spec's file list would have named. This is one session with no approval
gate at all, so it cannot show how much the gate alone would have caught.

## Goal

- Brainstorming's path decides the route of a task. `my` adapts it only where `my` adds
  something: the risk line, the two-file limit on bounded, where the tasks go, the bug route and
  the spike file.
- One set of route names, used the same way in the rules, the skills, the READMEs and the
  roadmap.
- No size words left in the live rule files.

## Out of scope

- Finished specs, plans, reviews and reports that say Small, Medium or Large. They are records.
- Changes to superpowers itself.
- Row 54's own design. This spec only narrows its scope (D10).
- Row 53's own design. This spec only rewords it (D10).
- Moving `roadmap-management`, `changelog-management` and `design-system` to `kit`. That is row 69.
- Which design skill the rules call, and when it runs. That is row 70. Several design skills are
  installed, and `my:design-system` has not been tried in use yet. This row only translates the
  words of the UI rules, and leaves what they do unchanged.

## Decisions

**D1. Brainstorming picks the route.** Brainstorming already says its path aloud before its first
question. Under `my`, that line also names the risk check, for example "Bounded: a flag on the
existing `status` command; no risk trigger." The user can change it. When unsure between two
routes, pick the heavier one.

**D2. The risk line.** A change to stored data or its shape, permissions, a message or public
contract, or something hard to reverse is "architectural with plan", whatever path brainstorming
would pick. These are the Large triggers of today's table. A spike is exempt, because its code
never lands.

**D3. The risk line also decides where the tasks go.** An architectural change with no risk
trigger keeps its tasks in the spec, as a Medium change does today. One with a trigger gets a
separate plan, as a Large change does today. A new subsystem with no risk trigger now keeps its
tasks in the spec. Before, "a new subsystem" was a Large trigger. The user can still ask for a
plan, by changing the route (D1).

**D4. The route names are superpowers' words.** The five routes are `spike`, `bounded`,
`architectural`, `architectural with plan` and `bug`. The README maps the old names once: Small is
bounded or bug, Medium is architectural, Large is architectural with plan.

**D5. Bounded is one or two files, and keeps brainstorming's approval gate.** A bounded change
touches one or two files in an existing flow, with no risk trigger. That is today's Small limit,
and the scale of superpowers' own examples: "a new flag, a small endpoint, a one-file fix". A
change to more files in an existing flow is architectural, with a spec that holds its tasks, as a
Medium change is today. A bounded change gets a short design in chat, and no code starts before
the user says yes. It then follows today's Small rules: a worktree, a failing test first,
`/code-review high` on the branch, one squash commit, and known limits in the squash commit
message. Several bounded changes and bug fixes may share one branch, as several Small fixes may
today.

The limit is a `my` adaptation, like the risk line. Without it, a change to several files would
skip `my:spec-review`, and the zitamu session in Context shows what that costs: the questions and
the missed files came after the code. The user chose the limit after reading that evidence.

**D6. Bugs take superpowers' debugging route.** A bug starts with
`superpowers:systematic-debugging`, with no route line. After the root cause is found, the bug
goes to brainstorming in any of three cases:

- the fix hits the risk line;
- there are several reasonable fixes;
- three fixes have failed, which is the debugging skill's own "question the architecture" step.

Brainstorming then picks the route as for any task, with the root cause as its input. Otherwise
the fix follows the bounded rules (D5), without the design gate.

**D7. A spike writes a short file.** A spike answers one question. Brainstorming's gate stays: the
user approves the question and the probe first. Under `my`:

- Its code lives in a worktree on a branch named `spike/<slug>`. The branch is never merged and is
  kept as a record, like any other branch.
- It writes `docs/plans/YYYY-MM-DD-<slug>-spike.md` with four parts: the question, what was tried
  (with the branch name), the answer, and the recommendation. It names the branch, never a commit
  hash from it: the `pre-commit` hook refuses a doc that cites a commit not on `main`.
- The file's status is `answered, <date>`, a new value in the status table. `my:status` treats any
  status outside its open list as closed, so a spike file never shows as open work.
- One `docs:` commit lands the file. No review runs.
- A spike needs no roadmap row. When a row exists, it links the spike file.
- Keeping the spike's code is a new task, and brainstorming classifies it again. Superpowers
  already says this.

A spike may also run inside an architectural route, before the spec, to answer one design
question. It writes the same file, and the spec lists that file under "How to read this spec".

`my:architect`'s own spikes stay as they are: throwaway code in its work folder, never committed,
with the result written into the brief. They answer a question for the brief, and the brief is
already the committed record of that answer. D7's file is for a spike that brainstorming picks,
or one run before a spec, where no brief holds the answer.

**D8. A route only moves up.** This is superpowers' ratchet. When the work turns out heavier than
its route, stop and say so before going on. It replaces today's "if the work turns out larger than
its size" sentence.

**D9. Rule 11 names a route only when it is already known.** A roadmap row is written before
brainstorming runs, so it cannot know the route brainstorming will pick. Rule 11 changes from
"kind, place and size" to "kind, place and route":

- a row of kind `bug` names no route;
- a row that hits the risk line names `architectural with plan`, because the risk line is a fact
  that can be seen when the row is written;
- every other row names `route not set` until brainstorming runs.

A bug row names no route even when the fix may touch the risk line: D6 sends such a bug to
brainstorming after the root cause, and the route is written then. The route replaces `route not
set` in the row's next edit after brainstorming picks it:

- an architectural route: in the 📋 edit that links the spec (rule 4);
- a bounded route: in the ✅ edit (rule 6), since no spec lands before it.

A bug that brainstorming routed follows the same two cases for the route it got.

The skill's sentence for projects without `my` stays neutral, in new words: "In a project that
routes its work (spike, bounded, architectural in the `my` method)". Today it reads "In a project
that sizes its work". Row 69 later moves the skill to `kit` with this wording.

**D10. The open roadmap rows follow D9.** Fourteen open rows carry a size label, row 56 says
`size not set`, rows 40, 53 and 54 use size words in their text, and so do three steps of "Order
of work":

| Row | Today | After |
| --- | --- | --- |
| 33, 37 | `bug …, Small.` | the size is dropped |
| 56 | `bug …, size not set.` | the size is dropped |
| 60 | `fix: …, Small.` | the size is dropped |
| 8, 20, 35, 44, 51, 61, 62 | Small | `route not set` |
| 45, 46 | Medium | `route not set` |
| 68 | Large | `architectural with plan`: it replaces the import line and the plugin keys that every project uses |
| 69 | Medium | `architectural with plan`: it renames three skills that projects call by their `my:` names |
| Order of work, step 2 | "33 and 37 are Small fixes and may share one branch" | "33 and 37 are bug fixes and may share one branch" |
| Order of work, step 3 | "its spec uses the new sizing" | "its spec uses the new routes" |
| Order of work, step 4 | row 54's old title | row 54's new title |
| 40 | "a Medium spec's Tasks section counts" | "a spec's Tasks section counts" |
| 54 | "Small rows in forks while the user is away" | "Bugs and approved bounded rows in forks while the user is away". Its scope narrows to bug rows, and bounded rows whose chat design the user approved before leaving. |
| 53 | "a second route to an approved spec"; the intake call asks "goal, scope, size, limits"; "A 10-line server change got a 340-line spec, so the route needs a size check of its own" | "a second way to an approved spec"; the intake call asks "goal, scope, route, limits"; "A 10-line server change got a 340-line spec, so the intake must first ask whether the row is bounded and needs no spec" |

Row 67 itself is rewritten when it moves to 📋 with this spec's link.

zitamu's roadmap (`~/projects/zitamu/real-estate-webapp/ROADMAP.md`) has 13 open rows with a size
label on 2026-10-18. After this row's squash-merge, one `docs:` commit in zitamu applies D9 to
them, with the same rules as the table above. It is a separate commit because it is a separate
repo.

**D11. The brief rule stays.** When an architecture brief exists, brainstorming classifies the task
as architectural (`my.md`, "Discovery authority"). Whether it also gets a plan follows the risk
line.

**D12. The precedence paragraph gets one sentence.** It says that brainstorming's path decides the
route, adapted only by the risk line and the two-file limit, and that the spike file goes to
`docs/plans/`. The list of
what superpowers may override does not change.

## Design

### The new route section in `my.md`

"Size the process to the change" is replaced by "Pick the route". It holds, in this order:

1. **The opening.** Brainstorming sorts a task into spike, bounded or architectural. `my` uses
   these paths as its routes, adapts them with the risk line and the two-file limit on bounded
   (D5), and gives bugs their own route. "An architectural change" means either architectural
   route, with or without a plan; "architectural" alone in the route table means the one without.
   State the route in one line with the reason (D1), except for a bug (D6). The user can change it. When unsure, pick the
   heavier route. A route only moves up (D8).
2. **The risk line** (D2), in one paragraph.
3. **The route table:**

   | Route | Who picks it | Documents | Reviews | Commits on `main` |
   | --- | --- | --- | --- | --- |
   | **Spike** | Brainstorming | `docs/plans/YYYY-MM-DD-<slug>-spike.md` | None | One `docs:` commit, the spike file. Its code is never merged. |
   | **Bounded** | Brainstorming, one or two files, no risk trigger | None. A short design in chat, approved before any code. | `/code-review high` on the branch | One: the squash-merged code. |
   | **Architectural** | Brainstorming, or more than two files; no risk trigger | Architecture brief where the trigger table asks for one; one spec, with a **Tasks** section in place of a plan. | `my:spec-review` on the spec; the end-of-branch reviews. No plan review. | Three: the spec with its review, the code, the `done` mark. |
   | **Architectural with plan** | The risk line | Architecture brief where the trigger table asks for one, spec, plan. | All reviews in this file. | Four, as in "One feature, four commits". |
   | **Bug** | `systematic-debugging` | None, unless it goes to brainstorming (D6). | `/code-review high` on the branch | One: the squash-merged code. |

4. **One bullet per route:**
   - **Spike:** D7.
   - **Bounded:** D5, with today's Small bullet text for the worktree, the failing test, the limits
     in the commit message and the shared branch. It skips the writing-plans and executing-plans
     rows. Brainstorming runs, on its bounded path.
   - **Bug:** D6. It skips the brainstorming, writing-plans and executing-plans rows, unless it
     goes to brainstorming.
   - **Architectural:** today's Medium bullet, unchanged except for its words: the Tasks rules
     from `superpowers:writing-plans`, the `approved` edit as a fixup, `/my:handoff code`, the
     "Parallel runs" exception, the Delegation question and "read 'the spec' where this file says
     'the plan'".
   - **Architectural with plan:** follows the rest of this file unchanged.

### Other edits to `my.md`

| Place | Today | After |
| --- | --- | --- |
| Line 12 | "once the size below is picked" | "once the route below is picked" |
| Trigger table, UI row | "in a Medium or Large change" | "in an architectural change, with or without a plan" |
| Line 67, after the skip list | "For Small and Medium changes, the size table above says which rows apply." | "For spikes, bounded changes and bugs, the route section above says which rows apply." |
| Precedence paragraph | — | D12's sentence |
| Spec → Plan flow, line 83 | "Large changes only; a Medium change keeps its tasks in the spec" | "architectural changes with a plan only; an architectural change without one keeps its tasks in the spec" |
| Code Review Routing, line 108 | "A Medium change has no plan, so it gets the spec." | "An architectural change without a plan gives it the spec." |
| UI Design, line 139 | "A Small change (see the size table) that adds no screen and no state" | "A bounded change or a bug fix that adds no screen and no state" |
| Medium bullet, line 46 (kept in the Architectural bullet) | "supervised is the route above" | "supervised is the hand-off above" |
| Git Workflow, line 170 | "A Large feature leaves four commits … Small and Medium leave fewer, as the size table says." | "An architectural change with a plan leaves four commits … The other routes leave fewer, as the route table says." |

### `global/rules/docs-layout.md`

- **Kinds of document:** a new row.

  | Kind | What it is | Where | Name |
  | --- | --- | --- | --- |
  | Spike | The answer to one question: what was tried and what it showed. Its code is never merged. | `docs/plans/` | `YYYY-MM-DD-<slug>-spike.md` |

- **From report to roadmap:** the chain reads `spec or plan, by route`.
- **Status line:** a new value, `answered`: "A spike. The sentence gives the answer in short."
- **One feature, four commits, "Two more commits are allowed":** a third one, the spike file of a
  spike that runs inside an architectural route, before step 1.
- **One feature, four commits:** "A Large feature leaves four commits on `main` (Small and Medium
  leave fewer, as the size table … says)" becomes "An architectural change with a plan leaves four
  commits on `main` (the other routes leave fewer, as the route table … says)".

### `my:roadmap-management`

- Rule 11 (line 174): D9. The example becomes `bug in my:handoff.`, with a second example
  `feature in my:status, route not set.`
- Lines 121 and 163 repeat rule 11's order: "kind, place and size" becomes "kind, place and
  route".
- Rules 4 and 6 each get one sentence: the edit replaces `route not set` with the route, in the
  cases D9 names.

### `my:handoff`

Labels only. The routing already uses the Tasks section, not the size.

- `SKILL.md` line 38: "(Large)" becomes "(architectural with plan)", and "(Medium)" becomes
  "(architectural)".
- `SKILL.md` line 289: "the plan (Large) or the spec (Medium)" becomes "the plan, or the spec when
  there is no plan".
- `SKILL.md` line 866: "for a Large change" becomes "for a change with a plan".
- `README.md` lines 54, 224, 226, 252, 273 and 285: the same mapping. Line 273 also says "The
  supervised hand-off for an architectural change" in place of "The supervised route for a Medium
  change", so "route" keeps one meaning.

"Route" keeps its other meaning in `docs-layout.md`'s "Routing a report" and "Routes a large
report's findings". There it means sending findings to rows, and the context makes that clear.

### `my:design-system`

`SKILL.md` line 132: "a Medium or Large change" becomes "an architectural change, with or without
a plan". Both this line and the UI row of the trigger table run `my:design-system audit` before
brainstorming, in a project with no `docs/DESIGN-SYSTEM.md`. Today "Medium or Large" means "a change
that gets a spec", and the new words mean the same. The audit's timing is a known limit (Risk).

### `plugins/my/README.md`

- The intro (line 7) and "Where the parts live" (line 23) say "route" for "size".
- "The size table" becomes "The routes": the route table from `my.md` without the commits column,
  the mapping from the old names (D4), and one sentence that finished documents still use the old
  names.
- "Worktrees, squash-merge and four commits on `main`" (lines 132-134): "A Large change leaves
  four commits … Medium leaves three, and Small one" takes the route names, as in the
  `docs-layout.md` edit.
- The brainstorming row in "How each superpowers skill is used": "Used for every task that is not
  a bug or on the skip list. Its path picks the route; the risk line can make it heavier." The `writing-plans` row:
  "Used for architectural changes with a plan."
- "Limits": "The size is picked once" becomes "A route only moves up". The spike sentences in the
  second point are replaced by "The spike route covers that case: it writes an answer, not code
  that lands."

### zitamu's local file

`projects/real-estate-webapp/claude-local.md` names sizes in three places today (lines 17-18,
267 and 271; the numbers move with the user's edits):

- "An API change to stored data, permissions or a response shape is Large under the global size
  rules" becomes "… hits the risk line, so it is architectural with plan under the global route
  rules".
- "every code branch, Small ones" becomes "every code branch, bounded ones and bug fixes".
- "A Small change records the e2e result in its squash" becomes "A bounded change or a bug fix
  records …".

The user's earlier uncommitted edits to this file were committed on 2026-10-18, in the commit
that records the letter-case rule. The start check in Dependencies still guards against new ones.

### `plugins/kit/tests/test_neutral_core.py`

`METHOD_HEADINGS` lists the headings of `my.md` that must not appear in the core. "Size the process
to the change" becomes "Pick the route", so the guard keeps checking a heading that exists.

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `cd plugins/kit && python3 -m unittest discover tests`, `cd plugins/my && python3 -m unittest discover tests`

## Files

| File | Change |
| --- | --- |
| `global/methods/my.md` | The route section, and the nine edits in "Other edits to `my.md`" |
| `global/rules/docs-layout.md` | The Spike kind, the `answered` status, the allowed spike commit, two wording edits |
| `plugins/my/skills/roadmap-management/SKILL.md` | Rule 11, lines 121 and 163, one sentence each in rules 4 and 6 |
| `plugins/my/skills/handoff/SKILL.md` | Three labels |
| `plugins/my/skills/handoff/README.md` | Six labels |
| `plugins/my/skills/design-system/SKILL.md` | One label |
| `plugins/my/README.md` | The routes section, the commits paragraph, the skill table, "Limits" |
| `projects/real-estate-webapp/claude-local.md` | Three sentences |
| `plugins/kit/tests/test_neutral_core.py` | One heading in `METHOD_HEADINGS` |
| `ROADMAP.md` | The eighteen rows and three "Order of work" steps in D10 |
| zitamu's `ROADMAP.md` | Its 13 sized open rows (D10), in a separate `docs:` commit in zitamu after the squash-merge |

No script reads the size words. One test names the old heading: `test_neutral_core.py`, above.
`status-scan.py` reads any status word, and `answered` is not in its open list.

## Trade-offs

- **Option A, this spec: brainstorming's paths with `my`'s adaptations.**
  - Pros: one choice of process instead of two, and it is superpowers' own. It keeps the Medium
    layout, which most specs use. A spike gets a place.
  - Cons: small features now stop for an approval. The two-file limit is a `my` rule on top of
    brainstorming's judgment. The route names are longer to say than the sizes.
- **Option B, F1's fix: keep the size table and map it onto the paths.** Brainstorming would be
  told that Medium means architectural, and Small means it does not run.
  - Pros: the smallest edit, and no names change.
  - Cons: two choices of process remain, and `my` still overrides brainstorming's judgment. The
    spike stays without a place.
- **Option C: brainstorming's paths exactly, with no adaptations.**
  - Pros: no `my` rules to keep.
  - Cons: a change to stored data could be called bounded. It loses the Medium layout, so every
    architectural change gets a separate plan. Bugs have no rule.
- **Recommendation: A.** It follows the user's aim: add to superpowers and adapt it, without
  replacing its judgment.

## Dependencies

- **The user commits their edits to zitamu's local file first.** The first task checks
  `git status --porcelain -- projects/real-estate-webapp/claude-local.md`, and stops if it prints
  anything.
- **Row 69 comes after this row.** It moves `roadmap-management`, `changelog-management` and
  `design-system` to `kit`, and inherits this wording. Its spec must keep rule 11 neutral.
- No new packages.

## Risk

- **Blast radius: every project that imports `my.md`.** The symlink in `~/.claude/methods/`
  applies the new rules in all nine at the merge: claude-setup, maritime, mv3-starter,
  niche-research, diagoradisa-annotator, diagoradisa-palmist, grispy-ext, grispy-site, and zitamu
  through its local file.
  - Specs in flight still work. `my:handoff` picks its route from the Tasks section, not from a
    size word.
  - A session reads `my.md` when it starts, so a session open at the merge finishes under the old
    rules.
- **A change to the build may be bounded.** Today's Small excludes "the build", but the risk line
  does not name it, as today's Large triggers do not. So a change to the build in one or two files
  is bounded, with no spec, where today it is at least Medium. The user accepted this. The chat
  design and `/code-review high` still run.
- **The two-file limit is a rough measure.** A two-file change can still hide a design question,
  and a three-file rename gets a spec it may not need. "Pick the heavier route" covers the first
  case; the second costs one spec and one review.
- **A route moves up only if the session notices.** In the zitamu session (Context), the copy work
  reached seeded data partway through, which crossed the risk line, and nothing stopped it. D8
  asks the session to stop, but no check enforces it. The end-of-branch review is the last place
  to catch it.
- **Small features now stop for an approval.** Today a Small change skips brainstorming. A bounded
  change waits for the user's yes. Bugs do not wait.
- **Two sets of names for a while.** Finished documents say Small, Medium and Large. The README's
  mapping (D4) lets a reader translate.
- **`my` now depends on superpowers' path names.** A later superpowers version could rename or
  drop a path. On a superpowers update, check "Three Paths" against the route table.
- **The design-system audit's timing is unclear.** The UI row runs `my:design-system audit` before
  brainstorming, but the route is now named when brainstorming starts. Today the size is named
  before any skill, so the condition is known in time. Row 70 settles it, once it has chosen the
  design skill. It applies only in a project with no `docs/DESIGN-SYSTEM.md`.
- **A bounded UI change skips the UI checks.** It has no spec, so it has no Visual Language
  section, `my:spec-review` does not check its shared components, and the audit does not run.
  This is no change from today: a UI change in one or two files is Small, and skips all three.
  Row 70 settles it.
- **A bounded change has no Risk section.** Known limits go into the squash commit message, as for
  Small today.
- **`ROADMAP.md` may conflict at the merge.** Other sessions edit it on `main`. On a conflict,
  apply D10 again to the rows as they are on `main`.
- **Not hard to reverse.** Every edit is to text, and the squash commit can be reverted.

## Testing strategy

The change is rule text, not code. The tests check the text, and how a session behaves under it.

1. **No size words in the live rules.** Run
   `grep -rnwE 'Small|Medium|Large' global/methods/my.md global/rules/docs-layout.md plugins/my/skills plugins/my/README.md`.
   It must print only two kinds of line: those that name the old sizes on purpose, such as the
   README's mapping, and the reviewers' confidence labels (`High`, `Medium`, `Low`) in
   `spec-reviewer-prompt.md` and `code-reviewer-prompt.md`. Before the change it also prints the
   lines listed in Design, which is the red step.
2. **A rehearsal with `claude -p`, the headless mode that runs one prompt and exits.**
   - **The fixture** is a small git repo in the session's scratchpad. It has a script with a
     `status` command, a listings model with a stored table, and five page templates that each
     show the label "Listing", so that each prompt names something that exists. Its `CLAUDE.md` imports the worktree's `global/methods/my.md` by its
     absolute path. The `~/.claude/methods/` symlink points to the main checkout, so through it
     the rehearsal would read the old rules. The fixture's settings turn on the `superpowers` and
     `my` plugins.
   - **The prompts and what each must produce first:**

     | Prompt | Expected first step |
     | --- | --- |
     | "Fix: the date filter drops the last day" | `systematic-debugging`, no route line |
     | "Add a `--quiet` flag to the existing `status` command" | a bounded route line, a short design in chat, then a stop for approval |
     | "Rename the label 'Listing' to 'Property' on every page" | an architectural route line that names the files (more than two), not bounded |
     | "Add a `deleted_at` column so listings can be restored" | `architectural with plan`, naming stored data |
     | "Can the PDF library render Greek fonts?" | a spike route line, the question and the probe, then a stop |

   - **Runs:** each prompt three times, and all three must pass. A session's answer varies between
     runs, so one pass could be luck.
   - **The red step:** the same fifteen runs against the old `my.md` first. The old rules print a
     size line, so the check for a route line fails there.
   - The bug escalation (D6) is not rehearsed. It needs a debugging session that finds a root
     cause, and one prompt cannot set that up. It is checked by reading the text.
3. **The unit tests** of both plugins still pass. `test_neutral_core.py` reads the renamed heading;
   the rest only check that nothing else broke.
4. **Markdown lint** on every edited `.md` file, with the user's config.

## Open questions

None.
