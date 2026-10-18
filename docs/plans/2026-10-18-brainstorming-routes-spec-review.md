# Review: docs/plans/2026-10-18-brainstorming-routes-spec.md

**Status:** review of docs/plans/2026-10-18-brainstorming-routes-spec.md, 2026-10-18. Mixed: the approach is sound, but the UI trigger row now depends on a route that brainstorming picks only after that row should have fired, and several edit lists (the test, the README, the roadmaps) are incomplete. Answered in the spec before its first commit: every editorial finding fixed; the UI audit's timing and the bounded UI checks left to row 70 as known limits; the other design findings decided by the user; the Evidence counts kept, as the author's own count.

## Spec Summary

The spec replaces the `my` method's Small/Medium/Large size table with five routes taken from superpowers' brainstorming paths (`spike`, `bounded`, `architectural`) plus two `my` adaptations: a "risk line" that forces `architectural with plan`, and a `bug` route through `systematic-debugging`. It adds a spike document kind with an `answered` status, rewrites roadmap rule 11 to name a route instead of a size, and relabels the size words in `my.md`, `docs-layout.md`, the `my:handoff` and `my:design-system` skills, the `my` README, zitamu's local file and sixteen open roadmap rows.

## System Model

All caller and reference sweeps in this review were text-only (`grep`, plus `command grep` where the shell's `grep` wrapper skipped files). No symbol-reference tool was available.

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| Route section in `my.md` ("Pick the route") | The five routes, the route line, the ratchet, the route table (documents, reviews, commits per route) | brainstorming's Three Paths; risk line; trigger table | Replaces existing `global/methods/my.md:14-52` |
| Risk line (D2) | The decision "stored data, permissions, message/public contract, hard to reverse → architectural with plan" | Today's Large triggers `global/methods/my.md:25` | New (rule text) |
| `superpowers:brainstorming` | The choice of spike / bounded / architectural, the spoken path line, the approval gates | — | Existing, superpowers 6.4.2 `skills/brainstorming/SKILL.md:58-88` |
| `superpowers:systematic-debugging` | The bug route; the "3+ fixes failed" escalation | — | Existing `skills/systematic-debugging/SKILL.md:198-212` |
| Trigger table in `my.md` | Which skill runs first (`my:architect`, `my:design-system audit`, brainstorming, debugging) | Route (UI row, after the edit) | Existing `global/methods/my.md:54-65` |
| `my:architect` | Architecture brief; its own throwaway spikes in `WORK_DIR` | Trigger table | Existing `plugins/my/skills/architect/SKILL.md:167-171` |
| Spike document (D7) | `docs/plans/…-spike.md`, branch `spike/<slug>`, status `answered` | Status table, `status-scan.py`, pre-commit hook | New |
| `docs-layout.md` | Kinds of document, status values, the report→roadmap chain, four-commit rule | Route table | Existing `global/rules/docs-layout.md:17-27, 37, 103-113, 136` |
| `status-scan.py` / `my:status` | Open-document list | Status values | Existing `plugins/my/bin/status-scan.py:49` |
| `my:roadmap-management` rule 11 | Row-body order "kind, place and size/route" | Route names | Existing `plugins/my/skills/roadmap-management/SKILL.md:121,163,174` |
| `my:handoff` | Stage routing by Tasks section; labels | Spec's Tasks section | Existing `plugins/my/skills/handoff/SKILL.md:37-38,289,866`; `README.md:54,224,226,252,273,285` |
| `my:design-system` audit | When the audit runs before a UI spec | Route label | Existing `plugins/my/skills/design-system/SKILL.md:131-132` |
| `plugins/my/README.md` | Human explanation of the method | Route table | Existing `plugins/my/README.md:7,23,75-97,132-134,146-147,166-178` |
| zitamu local file | zitamu's size-dependent rules | Route names | Existing `projects/real-estate-webapp/claude-local.md:17,267,271` |
| Roadmaps (claude-setup; zitamu) | Open rows' size labels and order prose | Rule 11 | Existing `ROADMAP.md`; `/home/dchris/projects/zitamu/real-estate-webapp/ROADMAP.md` |
| Neutral-core test | Guards that `my` headings stay out of the core | Heading names in `my.md` | Existing `plugins/kit/tests/test_neutral_core.py:17-23` (not named by the spec) |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Brainstorming → route section | The path line (spike / bounded / architectural) | brainstorming |
| Risk line → route | Override to `architectural with plan` | `my.md` route section |
| Route → trigger table UI row | "architectural change" gate for `my:design-system audit` | `my.md` (but see Issues: the route is not known yet when the row fires) |
| Trigger table → `my:architect` → brainstorming | Brief; brief forces `architectural` (D11) | `my:architect` / `my.md` "Discovery authority" |
| Debugging → brainstorming (D6) | Root cause, on one of three escalation cases | systematic-debugging |
| Route → spike file → `docs/plans/` | Spike document, `answered` status | Spike route (D7) |
| Spike file → `status-scan.py` | Status word, treated as closed | `status-scan.py` |
| Route → roadmap row (rule 11) | `route not set` / `architectural with plan` / nothing | Unclear after brainstorming runs (see Issues) |
| Spec Tasks section → `my:handoff` | `auto plan` vs `auto code` choice | `my:handoff` (unchanged) |
| `my.md` heading → neutral-core test | Heading string "Size the process to the change" | `plugins/kit/tests/test_neutral_core.py` |

## Grounding

- `spec §Files` ("No script or test reads the size words") and `spec §Testing strategy` item 3 ("Nothing in them reads the changed text") ↔ `plugins/kit/tests/test_neutral_core.py:18`, which lists the heading "Size the process to the change" that the spec renames. A plain `grep` through the shell's wrapper missed this line; `command grep` found it.
- `spec §Testing strategy` item 1 ("Before the change it prints the lines listed in Design") ↔ the grep also prints `plugins/my/README.md:132-134` (not in Design) and the confidence labels at `plugins/my/skills/spec-review/spec-reviewer-prompt.md:87,98,154,171` and `plugins/my/skills/soundness-review/code-reviewer-prompt.md:57,64,110,127`, which no edit removes.
- `spec §D10` ("Fourteen open rows carry a size label") is true for Small/Medium/Large only; row 56 carries `size not set` (`ROADMAP.md:326-327`). The Order of work prose also uses size words (`ROADMAP.md:38`, `ROADMAP.md:51`).
- `spec §Out of scope` and `spec §Dependencies` say row 69 moves `roadmap-management` and `design-system`; row 69 also moves `changelog-management` (`ROADMAP.md:235-238`), and `spec §D10` itself says "three skills".
- `spec §zitamu's local file` ("The file has the user's uncommitted edits today") ↔ the file is now committed on `main` (`git status --porcelain` prints nothing for it; the commit of 2026-10-18 that records the letter-case rule). The Dependencies check still works; only the sentence is stale.
- `spec §D9` ("The skill keeps its neutral wording") ↔ today's wording is "In a project that sizes its work (`Small`, `Medium`, `Large` …)" (`plugins/my/skills/roadmap-management/SKILL.md:174`); the quoted sentence is new text, not kept text.
- Everything else checked holds: the cited line numbers in `my.md`, `docs-layout.md`, `roadmap-management`, `handoff` and `design-system`; nine projects import the method (eight `CLAUDE.md` files plus zitamu's symlinked `CLAUDE.local.md`); superpowers is 6.4.2 with "Three Paths" and Phase 4 step 5; `OPEN_STATUSES` excludes `answered` (`plugins/my/bin/status-scan.py:49`); `my:handoff` routes on the Tasks section (`plugins/my/skills/handoff/SKILL.md:37-38`); Option B is F1's real proposed fix (`docs/reports/2026-10-14-superpowers-fit-critique.md:101-102`).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | The UI trigger row becomes "UI work … in an architectural change → `my:design-system audit`, then brainstorming". But the route is now spoken by brainstorming at its start (D1), so the audit's gate depends on a decision made after the audit should already have run. Today the size line comes before any skill, so the gate was known. The spec states no order for this. | `spec §Other edits to my.md` (UI row) ↔ `spec §D1`; `global/methods/my.md:58`, `:71` ("`my:architect` runs before brainstorming"); brainstorming `SKILL.md:60-63` | Decision for the author: e.g. brainstorming pauses after an architectural route line to run the audit (mirror `my.md:77` for `my:architect`), or key the row on something knowable before brainstorming. |
| Warning / High | design | "Architectural" is used two ways. D4 makes `architectural` and `architectural with plan` separate routes, yet the UI row, `design-system/SKILL.md:132` and D3 use "an architectural change" to mean both (replacing "Medium or Large"). Read strictly, a Large UI change loses the design-system audit. | `spec §D4` ↔ `spec §D3`, `§Other edits to my.md` (UI row), `§my:design-system`; `global/methods/my.md:58`; `plugins/my/skills/design-system/SKILL.md:131-132` | Decide whether "architectural change" names the family of both routes, and define it once in the route section; otherwise write "architectural, with or without a plan" in those edits. |
| Warning / High | design | Two spike conventions after this change. `my:architect` already runs spikes as throwaway code in `WORK_DIR`, "never commit", result in the brief. D7 defines a spike as a worktree on `spike/<slug>`, kept, with a `docs/plans/` file. D7 also lets a spike run "inside an architectural route, before the spec", which overlaps the architect's spikes. The spec does not mention the architect's form. | `plugins/my/skills/architect/SKILL.md:167-171` ↔ `spec §D7` | Decision for the author: align the architect's spikes with D7, or state that the brief's spikes stay separate and why. |
| Warning / High | design | zitamu's open roadmap rows keep size labels (13 open rows with Small/Medium/Large, e.g. rows 17, 18 and 46). D10 migrates only claude-setup's open rows, and §Risk "Two sets of names" covers finished documents only, yet open rows are live input to rule 11. | `/home/dchris/projects/zitamu/real-estate-webapp/ROADMAP.md:325`, `:326`, `:486` ↔ `spec §D10`, `§Out of scope`, `§Risk` | Decision for the author: migrate zitamu's open rows in this row, or list them as a known limit in Risk. |
| Warning / High | editorial | The neutral-core test lists the heading the spec renames. After the rename that guard entry checks nothing. The file is missing from §Files and §How to read, and two claims say no test reads the text. | `plugins/kit/tests/test_neutral_core.py:18` ↔ `spec §Files`, `§Testing strategy` item 3 | Add the file to §Files: "Pick the route" replaces the old heading in `METHOD_HEADINGS`. Correct both claims. |
| Warning / High | editorial | The README edit list misses "A Large change leaves four commits … Medium leaves three, and Small one" in "Worktrees, squash-merge and four commits on `main`". | `plugins/my/README.md:132-134` ↔ `spec §plugins/my/README.md` | Add the edit: the route names, as in the `docs-layout.md` edit. |
| Warning / High | editorial | D10 is incomplete. Row 56 is a bug row that says `size not set`, and under D9 a bug row names no route. The Order of work prose says "33 and 37 are Small fixes" and quotes row 54's old title, which D10 renames. | `ROADMAP.md:326-327`, `ROADMAP.md:38`, `ROADMAP.md:51` ↔ `spec §D10`, `§Files` ("sixteen rows") | Add row 56 (drop the size), the two Order of work lines, and fix the count. |
| Warning / Medium | design | D2's risk line drops one exclusion from today's Small row: "or the build". Today a build change cannot be Small, so it gets at least a spec. Under D2 it can be bounded with no spec. D5's accepted consequence and §Risk do not name it. | `global/methods/my.md:23` ↔ `spec §D2`, `§D5`, `§Risk` | Decision for the author: add the build to the risk line, or record it as accepted in Risk. |
| Warning / Medium | design | A UI change that is Medium today (several files in an existing flow) can now be bounded. Then there is no spec, so no Visual Language section, no shared-component check by `my:spec-review`, and no design-system audit (the UI row is architectural only). §Risk names only "may get no spec". | `global/methods/my.md:85`, `:58` ↔ `spec §D5`, `§Risk` | Decision for the author: route UI work that adds a screen or state as architectural, or record the loss in Risk. |
| Warning / Medium | design | D9 does not say who replaces `route not set` with the chosen route, or when. For a bounded row, the roadmap row is the only lasting record of the route. D9 also leaves open which bullet wins for a bug row whose risk-line hit is visible when the row is written. | `spec §D9`; `plugins/my/skills/roadmap-management/SKILL.md:121` (the ✅ edit rewrites the row body) | Decision for the author: name the step that writes the route (e.g. the ✅ edit or the spec commit), and say whether a bug row may name `architectural with plan`. |
| Warning / Medium | design | Row 53 is dropped from D10 without a reason. Row 67's own text names "the open rows that use the sizes (40, 53, 54, 61)". Row 53 uses "size" in its intake call and says "the route needs a size check of its own". The bounded route may answer part of that. | `ROADMAP.md:421-428`, row 53 at `ROADMAP.md:127-149` ↔ `spec §D10` | Decision for the author: rewrite row 53's text or its scope, or state why it stays. |
| Warning / Medium | design | The route table's Architectural row lists only "One spec". But a new subsystem with no risk trigger, which D3 now routes as architectural, still matches the `my:architect` trigger row and gets a brief. The table lists the brief only for architectural with plan. | `global/methods/my.md:56` ↔ `spec §Design` (route table), `§D3`, `§D11` | Decision for the author: add "architecture brief where the trigger table asks for one" to the Architectural row, or say a new subsystem without a trigger skips the brief. |
| Warning / Medium | editorial | §How to read omits files the spec edits or depends on: `plugins/my/skills/design-system/SKILL.md`, `projects/real-estate-webapp/claude-local.md`, and `plugins/kit/tests/test_neutral_core.py`. | `spec §How to read this spec` ↔ `spec §Files` | Add them to the reading list. |
| Suggestion / High | design | "Route" already means other things in the files this spec edits: "supervised is the route above" inside the Medium bullet that the Architectural bullet keeps "unchanged except for its words"; "Routing a report" and "Routes a large report's findings"; "the supervised route"; row 53's "second route to an approved spec". The Goal asks for one set of route names "used the same way". | `global/methods/my.md:46`; `global/rules/docs-layout.md:25,56`; `plugins/my/skills/handoff/README.md:273`; `ROADMAP.md:127` ↔ `spec §Goal`, `§D4` | Decision for the author: reword the clashing uses, or pick another term. |
| Suggestion / High | editorial | The skip list stays ("single-line fixes, typo/comment edits, doc-only changes, config tweaks" skip the table). But the new README row says brainstorming is "Used for every task that is not a bug". | `global/methods/my.md:67` ↔ `spec §plugins/my/README.md` | Say "every task that is not a bug or on the skip list". |
| Suggestion / High | editorial | The opening of the route section says "State the route in one line", but D6 says a bug starts "with no route line". | `spec §Design` (opening, item 1) ↔ `spec §D6` | Add "except a bug (D6)" to the opening. |
| Suggestion / High | editorial | The spike file names its never-merged branch. The pre-commit hook on `main` refuses any doc line that cites a commit not on `main`, so a hash from the spike branch would block D7's commit. | `global/git-hooks/pre-commit:11-20` ↔ `spec §D7` | Say "the branch name, no commit hashes". |
| Suggestion / High | editorial | A spike that runs inside an architectural route adds a commit that the four-commit rule does not allow. Its "Two more commits are allowed" list names only the brief and forced doc edits. | `global/rules/docs-layout.md:144-146` ↔ `spec §D7`, `§global/rules/docs-layout.md` | Add the spike file to that list in the `docs-layout.md` edits. |
| Suggestion / High | editorial | Out of scope and Dependencies name two skills for row 69; row 69 and D10 name three. | `ROADMAP.md:235-238` ↔ `spec §Out of scope`, `§Dependencies`, `§D10` | Add `changelog-management`. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Fit with what exists: it removes a real double decision | `global/methods/my.md:71-75` maps the paths only when a brief exists; brainstorming `SKILL.md:58-88` has its own paths; F1 at `docs/reports/2026-10-14-superpowers-fit-critique.md:84-102` | Strong |
| Contracts: hand-off routing is not coupled to size words | `plugins/my/skills/handoff/SKILL.md:7,37-38` route on the Tasks section, so specs in flight keep working | Strong |
| Fit: the adaptations reuse superpowers' own rules | Ratchet and "pick the heavier" (`SKILL.md:85-88`); spike "keeping the code is a new request" (`SKILL.md:105`); debugging 3+ fixes step (`systematic-debugging/SKILL.md:198-212`) | Strong |
| Failures: new status does not leak into open work | `plugins/my/bin/status-scan.py:49,136` treats unknown statuses as closed | Moderate |
| Trade-offs are real choices | Option B is F1's own proposed fix; Option C is upstream as shipped | Moderate |
| Spec rules: required sections present | How to read, Risk, Dependencies, Trade-offs, Delegation with the four keys (`plugins/my/skills/handoff/SKILL.md:121-140`) | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Contracts and flow: the UI trigger is ordered before the route that gates it | `global/methods/my.md:58` ↔ `spec §D1` | Medium |
| Boundaries: two owners of "spike" | `plugins/my/skills/architect/SKILL.md:167-171` ↔ `spec §D7` | Medium |
| Grounding: edit lists miss live references | `plugins/kit/tests/test_neutral_core.py:18`; `plugins/my/README.md:132-134`; `ROADMAP.md:38,51,326`; zitamu `ROADMAP.md:325,326,486` | Medium |
| Scope: checks that silently disappear for work that becomes bounded | `global/methods/my.md:23` (the build), `:85` (Visual Language) ↔ `spec §D2`, `§D5` | Medium |
| State ownership: the row's route has no writer after brainstorming | `spec §D9` | Low |

## Not Applicable

- Criterion 3, off-path UI events: the spec adds no UI.
- Criterion 6, Visual Language and design-system checks: the spec adds no UI.

## Needs Investigation

- **The Evidence counts in §Context** ("21 specs were Medium, 13 were Large and 1 is a draft" across five projects; "24 `fix:` commits, only 2 had a spec" on zitamu). A quick count by spec header could not classify 18 of the spec files, so the 21/13 split is unverified. zitamu shows 26 `fix:` commits since 2026-10-03 today, two of them from today, so the 24 matches the time of writing. Which commits "had a spec" was not checked. The claim supports keeping the Medium layout, which no finding disputes. To settle it, count each spec's `**Size:**` line and match each `fix:` squash to a spec link.

## Reasoning

The System Model holds together at its core. Brainstorming owns the path, the risk line owns the override, and `my:handoff` keys on the Tasks section, not on size words, so the main flow has a single owner per decision. The problems sit at the edges. The UI trigger row and the "architectural" label rely on a route that is now known later, and under one name more than before. The architect's spike and D7's spike overlap. Several edit lists (a test, a README paragraph, three roadmap places, zitamu's roadmap) miss live references. Two checks quietly drop for work that becomes bounded. None of this argues for a different approach, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every Warning cites a repo line or spec section that was opened or searched directly; no finding challenges the chosen option.
**Recommendation:** Fix the seven editorial rows. Bring the design rows to the user in the "No silent reinterpretation" form, starting with the UI-trigger order and the meaning of "architectural change". Then rerun `my:spec-review`.
