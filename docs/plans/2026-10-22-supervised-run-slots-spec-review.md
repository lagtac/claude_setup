# Review: docs/plans/2026-10-22-supervised-run-slots-spec.md

**Status:** review of docs/plans/2026-10-22-supervised-run-slots-spec.md, 2026-10-22. Mixed: the one-pool design holds, but slots can now exceed **Max runs**, against the README's stated range, and several prose readers of run state are missing from the edit list. Answered in the spec: editorial fixes, and decisions D12 to D16 for the design findings.

## Spec Summary

Every `my:handoff` run gets a state file and a slot from one pool, supervised runs included. `handoff-state.py start` gains a `--supervised` form and a `mode` field. The cap counts only auto runs. Exclusive rows and `after` gates see both modes. The supervised code and review stages write and end their own state, and `live`, `status-scan.py` and `my:status` gain a `mode` column.

## System Model

The caller sweep for this review was text-only (`grep -rn` through Bash); no symbol-reference tool was available. I checked the spec's LSP call-site claims by reading the code: `start_run` is called from `start` and `pull`'s `ready`, and `live_states` from `print_live`, `start_run`, `walk` and `pull`'s `ready`. Both claims hold.

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `handoff-state.py` `start` / `start_run` | Slot choice, the cap check, the same-slug refusal, writing a fresh state | `live_states`, `handoff-lock.py main` held by the caller | Existing `plugins/my/bin/handoff-state.py:274`, `:296`; supervised form is new |
| State files `<git common dir>/my-handoff/<slug>.json` | Per-run fields; `mode` is new; `next` decides liveness | `write_json` | Existing `plugins/my/bin/handoff-state.py:175`, `:233` |
| `live` / `print_live` | The list of live runs (5 columns, 6 after the change) | `live_states` | Existing `plugins/my/bin/handoff-state.py:255` |
| `pull` / `walk` / `queue show` | Queue rules 1 to 6; who may start | `live_states`, `run_state`, queue file | Existing `plugins/my/bin/handoff-state.py:691`, `:764`, `:810` |
| `handoff-lock.py main` | Mutual exclusion of starts, merges and locked commits | kernel `flock` | Existing `plugins/my/skills/handoff/SKILL.md:187-200` |
| Handoff `SKILL.md`: supervised code and review stages | Writing a supervised state (code), re-entering it (review), `next=finished` (review step 8, code step 4) | `handoff-state.py start --supervised`, `set` | Existing stages `plugins/my/skills/handoff/SKILL.md:827`, `:912`; state writes are new |
| Handoff `SKILL.md`: `resume` | Relaunching auto stages | `check`, `get`, `mode` | Existing `plugins/my/skills/handoff/SKILL.md:358` |
| Handoff `SKILL.md`: auto launch start checks | Refusing a second run of a slug before `start` | `handoff-state.py get` | Existing `plugins/my/skills/handoff/SKILL.md:639-712` (check 5 at `:673-674`) |
| Handoff `SKILL.md`: `auto rows` step 3 and step 4 | Which rows are skipped; whether to fold the `approved` edits | `status-scan.py`, `handoff-state.py get` and `live` | Existing `plugins/my/skills/handoff/SKILL.md:487`, `:496`, `:512` |
| `status-scan.py` `run_facts` | The `runs` block; fallback read when `live` exits 2 | `handoff-state.py live`, state files | Existing `plugins/my/bin/status-scan.py:190` |
| `my:status` `SKILL.md` | Counting against the cap; "needs you" lines | `status-scan.py` | Existing `plugins/my/skills/status/SKILL.md:99-150` |
| Handoff `README.md` | User-facing description of the state and of `<slot>` | — | Existing `plugins/my/skills/handoff/README.md:311`, `:364-368` |
| Project "Parallel runs" Isolation line | Turning `<slot>` into ports and stacks | `<slot>` from `get` | External; no project has one (searched `~/projects/*/CLAUDE*.md` and `zitamu/real-estate-webapp/CLAUDE*.md`) |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Supervised code stage → `handoff-lock.py main` → `start --supervised` | CLI call; the printed slot | `handoff-state.py` |
| Supervised review stage → `start --supervised next=review` | CLI call; the same slot when the state is live | `handoff-state.py` |
| Code stage step 1 → `set branch= worktree=` | Fields in the state file | Code stage |
| Review step 8 and code step 4 → `set next=finished` | Liveness | The supervised stage |
| Supervised finish → `queue show` → user | A hint line; no refill | `handoff-state.py` / the stage |
| `start_run`, `walk`, `pull` → `live_states` → state files | Slot pool, counts by `mode` | `handoff-state.py` |
| `live` → `status-scan.py` → `my:status` | 6-column lines | `handoff-state.py` (format) |
| `status-scan.py` fallback → state files | Raw JSON, `mode` default `auto` | `status-scan.py` |
| `SKILL.md` `<slot>` → Isolation commands | Slot number into ports/stacks | Project section |
| `auto rows` step 4 → `live` | "prints nothing" as a fold condition | `SKILL.md` (not in the spec) |
| Auto launch start check 5 → `get <slug>` | A live state of either mode | `SKILL.md` (not in the spec) |
| `resume` → `check`, `get` → `mode` | Refusal of a supervised run | `SKILL.md` |

## Grounding

- `spec §Decisions` D7, "Today a row gated behind supervised work cannot name it, so it starts at once" ↔ `plugins/my/skills/handoff/SKILL.md:487`. Today such a row is skipped with `blocked by row <m>, which nothing will start`, because its blocker is not done and is none of a row in the call, a live auto run or a waiting entry. It does not start at once. The decision still makes sense. Only its stated reason is wrong.
- `spec §Files`, "The only reader of `live` outside the script is `status-scan.py`" ↔ `plugins/my/skills/handoff/SKILL.md:393` ("`handoff-state.py live` lists the runs that count") and `:512` (fold condition "`handoff-state.py live` prints nothing"). These are prose readers that the spec neither lists nor edits. `spec §Risk` ("Their only readers, `status-scan.py`, `my:status` and `my:handoff`, change here") names `my:handoff` but does not change these two lines.
- `spec §Design` 2, "Line 495, `after`: 'live auto runs'" ↔ `plugins/my/skills/handoff/SKILL.md:496`. The phrase is on line 496.
- `spec §Context`, "`SKILL.md` line 184 says it 'uses slot `1`'" ↔ `plugins/my/skills/handoff/SKILL.md:185`. The sentence is on line 185, and the bullet starts on line 184.

The other references hold. These include `FIELDS` (`handoff-state.py:135`), the cap message (`:281`), the slot rule (`:283-284`), the rules of `walk` and `pull`, `test_concurrent_locked_starts_never_pass_the_cap` (`test_handoff_state.py:413`), the `live` assertions near lines 346 and 357, the push guard reading only `MY_AUTORUN` (`block-autorun-push.py:93`), and row 68's plan touching only "the four launch lines" (`docs/plans/2026-10-20-method-bundles.md:193`, `:1052`).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | Slots are no longer bounded by **Max runs**. Supervised runs take numbers from the same pool but do not count toward the cap, so an auto run can get slot `Max runs + 1` or higher. The README tells projects that `<slot>` is "the run's place, 1 to **Max runs**". A project that reserves ports or stacks for that range gets an unplanned value. The spec does not state the new range, and it does not edit that line. | `plugins/my/skills/handoff/README.md:367-368`; `plugins/my/bin/handoff-state.py:284`; `spec §Decisions` D4 ↔ D5 | Decision for the author. Either state that the range is unbounded and edit the README and the Isolation guidance, or bound the pool, for example by a separate supervised range. |
| Warning / High | design | Auto launch start check 5 runs before `start` and refuses any live state with "a run for <slug> exists; use resume". With a live supervised run of the same slug, that fires first, so the spec's new refusal `refused: a supervised run for <slug> exists` is never seen on this path. It also tells the user to resume, which D10 refuses. | `plugins/my/skills/handoff/SKILL.md:673-674`; `spec §Design` 1 (refusal table), D10 | Add start check 5 to the text edits: give it a supervised branch with its own message, or let `start` alone decide. |
| Warning / High | design | Row 56 was moved to the head of the order because "zitamu hits it now". The spec has no effect in zitamu, or in any project, until that project has a "Parallel runs" section. None does, and row 39, which offers one, is blocked by row 29. The spec states this gap but leaves it open, so shipping row 56 would not stop the reported clash. | `ROADMAP.md:28-31`, `ROADMAP.md:241-248`; search of `~/projects/*/CLAUDE*.md` and `zitamu/real-estate-webapp/CLAUDE*.md` found no section; `spec §Risk` "No effect without the section", `§Open questions` | Decision for the author: add zitamu's section (by hand) as part of this row, or re-word the order-of-work reason and the row so they do not promise relief now. |
| Warning / High | editorial | D7 has no effect unless the row-skip table in `auto rows` step 3 changes. Today it accepts only "a live auto run" as a blocker, so a row gated behind a live supervised run is skipped with "nothing will start" before `after` is ever written. The spec edits line 496 but not line 487. | `plugins/my/skills/handoff/SKILL.md:487`; `spec §Design` 2 "Text edits" | Add line 487 to the text edits: "a live auto run" becomes "a live run". |
| Warning / Medium | design | In a project without the section, `auto rows` step 4 folds the `approved` edits only when `handoff-state.py live` prints nothing. Under D2 every project now writes supervised states, so any live supervised session turns the fold into a normal docs commit. That changes behaviour, and the spec does not decide or mention it. | `plugins/my/skills/handoff/SKILL.md:510-512`; `spec §Decisions` D2, `§Files` sweep | Decision for the author: keep the condition as "no live run" (and say so in Risk), or narrow it to auto runs. |
| Warning / Medium | design | A supervised run becomes `finished` only in review step 8 or code step 4. A supervised session the user closes, or merges by hand, stays live with no stop line. `my:status` never lists it as needing the user, yet under D6 it blocks every exclusive queued row, and it holds a slot. §Risk names the stale `my:status` line but not the queue stall. | `spec §Design` 2 "How a supervised run ends", `§Design` 3 ("It never needs the user"), D6; `plugins/my/bin/handoff-state.py:735-736` | Decision for the author: flag a supervised run that blocks a waiting row as "needs you" in `my:status`, or add the stall to Risk. |
| Warning / Medium | design | D1 rejects "slot lives as long as the worktree" because a process can outlive its worktree. But in a supervised batch, code step 4 sets `next=finished` while the shared worktree, and any server in it, stays up. The freed slot can then go to the next run that starts, which is the same kind of clash D1 argues against. | `spec §Decisions` D1 ↔ `§Design` 2 (code stage step 4); `plugins/my/skills/handoff/SKILL.md:866-868` | Decision for the author: state the batch case in Risk, or keep the slot across a batch's runs. |
| Suggestion / High | editorial | The text edits miss two more lines that become false. `SKILL.md:393` says `live` "lists the runs that count", but it will also list supervised runs, which do not count toward the cap. `README.md:364` says **Max runs** is "the most runs live at once", but it is now the most auto runs. | `plugins/my/skills/handoff/SKILL.md:393`; `plugins/my/skills/handoff/README.md:364` | Add both lines to the text edits. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | One owner for slots and counts (`handoff-state.py`). Every caller goes through `start` under lock `main`, as auto runs already do (`handoff-state.py:274-286`, `SKILL.md:693-702`). | Strong |
| Contracts | The refusal table covers every (state, form) pair. The counting table names each `pull` rule and matches the code's rule numbering (`handoff-state.py:88-107`). | Strong |
| Fit | It reuses the existing lowest-free-slot rule and lock instead of adding a second mechanism. The rejected options (worktree lifetime, worktree list position, a separate supervised record) were real choices with stated reasons. | Moderate |
| Grounding | Function names, call sites, test classes and test names all exist as described. | Strong |
| Spec rules | "How to read this spec" comes first. Risk, Dependencies, Trade-offs and Testing are all present. Unreadable states are handled conservatively (they count as auto). | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Contracts | The slot range is no longer bounded by **Max runs**, which the README promises (`README.md:367-368`). | Medium |
| Flow | Three prose readers of run state, start check 5 and `SKILL.md:487`/`:512`, are not in the edit list. | Medium |
| Failures and interactions | A dropped supervised run plus D6 stalls exclusive rows. A batch's finished run frees a slot while its worktree lives. | Medium |
| Scope | The reported symptom (zitamu) is unchanged until a project section exists. | Medium |
| Spec wording | D2 says "every run has a state file", but D8 writes none at the plan stage. A row gated behind a supervised run that is still at the plan stage is still skipped at `SKILL.md:487`. | Low |

## Not Applicable

None.

## Reasoning

The System Model has one clear owner for slot choice and counting. The connections are defined, except the four `SKILL.md` and README readers of run state that the spec does not list. Those gaps, the unbounded slot range, and the batch and dropped-run interactions are all Warnings that need the author's decision or a text edit. None of them breaks the one-pool design itself. No finding is Critical, so the assessment is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — every finding cites a repo line I opened or a search I ran, and the script's code matches the spec's description of today's behaviour.
**Recommendation:** Add `SKILL.md:393`, `:487` and `:512`, start check 5 and `README.md:364-368` to the text edits. Then put four questions to the user: the slot range beyond **Max runs**, the `auto rows` fold condition, the batch and dropped-run cases in Risk, and whether zitamu gets a section within this row.
