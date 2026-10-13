# Review: docs/plans/2026-10-13-roadmap-auto-runs-spec.md

**Status:** review of docs/plans/2026-10-13-roadmap-auto-runs-spec.md, 2026-10-13. Problematic: when the call cannot fold right away, D3 leaves `fixup!` commits waiting. The next `done` mark on `<base>` makes those fixups impossible to fold, so the first queued row stops at its fold, and `resume` cannot clear the stop. Answered in the spec, in the same fixup as this review: D3 makes fixups only when the call folds them at once; the other findings were decided by the user.

## Spec Summary

The spec adds `/my:handoff auto rows <n> ...`. The command judges each roadmap row once, commits each queued spec's `approved` edit, writes a queue file under the git common dir, and starts rows through a new locked `handoff-state.py pull`. After that, each auto run that finishes, or that the user ends, runs `pull` again and launches the next row, so no supervisor is needed. `my:status` gains a `queue` block and a line that says when the first waiting row could start but nothing starts it.

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
| --- | --- | --- | --- |
| `auto rows` form in `my:handoff` (the call) | Judging rows at call time (D2); the `stage`, `after` and `exclusive` values; committing the `approved` edits and the optional fold (D3); launching the windows for rows that `pull` prints | `status-scan.py`, the `my:status` steps 4 to 6, `git-fold-fixups.py`, `locked-commit.py`, `handoff-state.py queue add` and `pull`, Launch | New, in `plugins/my/skills/handoff/SKILL.md` (Forms at `:26-40`) |
| Queue file `<git common dir>/my-handoff/queue/rows.json` | Entries: row, slug, spec, stage, after, exclusive, spec_hash, state, reason | `handoff-state.py` as its only writer | New. The subfolder avoids `live_states`, which reads only top-level `*.json` (`plugins/my/bin/handoff-state.py:176-187`) |
| `handoff-state.py queue add`, `queue drop` | Validating, ordering and pruning entries | Queue file, state files | New, beside the existing `start` (`handoff-state.py:201-223`) |
| `handoff-state.py pull --max <n>` | Picking entries (rules 1 to 6) and starting them through `start()` in the same process | Queue file, state files, `start()`, `git hash-object`; runs inside `handoff-lock.py main` | New. The lock is a per-file `fcntl.flock` (`plugins/my/bin/handoff-lock.py:71-84,123`) |
| `handoff-state.py queue show` | A read-only walk with rules 1 to 4 | Queue file, state files | New |
| Refill steps (D6) | Running `pull` and launching after a run finishes or is ended; the refill-failure signal | `pull`, Launch, review sub-step 4, "To end an abandoned run" | Changes existing text at `SKILL.md:871-877` and `SKILL.md:349-357` |
| `status-scan.py` `queue` block | Printing the `queue show` line and the waiting and skipped entries | `handoff-state.py queue show`, queue file | Changes existing code at `plugins/my/bin/status-scan.py:308-322` |
| `my:status` report lines (D7) | The needs-you line and the in-progress lines | `queue` and `runs` blocks, **Max runs** | Changes existing text at `plugins/my/skills/status/SKILL.md:91-107` |
| Per-run state file `my-handoff/<slug>.json` | `next`, `stopped`, `slot` and the rest | `handoff-state.py` | Existing, `handoff-state.py:77-91,116-141` |
| Stage sessions (plan, code, review) | The stage's work, its own fold, the `done` marks | State file, `git-fold-fixups.py` | Existing, `SKILL.md:509-911` |

| From → To | What passes | Owner of what passes |
| --- | --- | --- |
| Call → `status-scan.py` | One run; facts in blocks | `status-scan.py` |
| Call → git / `git-fold-fixups.py` | `check <spec commit>`, the fixup or normal commits, and the optional fold | Call (the commits); fold script (the refusal rules) |
| Call → `queue add` | Every entry of one call, in one command | `handoff-state.py` (queue file) |
| Call / review session / ending session → `pull` (under `handoff-lock.py main`) | `--max <n>`; one line per started row on stdout, `skipped:` lines on stderr | `handoff-state.py` |
| `pull` → `start()` | An in-process call; writes the state file | `handoff-state.py` |
| Caller → Launch | `<stage>-<new slug>`, `MY_AUTORUN=<new slug>` | The calling session |
| `pull` / `queue show` → state files | Reads `next` and `stopped` of the slugs in `after`, and the `exclusive` runs | Stage sessions (through `handoff-state.py set`) |
| `status-scan.py` → `queue show` | One line: `ready`, `waits` or `none` | `handoff-state.py` |
| Queued spec's commit (D3) → later stage fold | A waiting `fixup!` commit on `<base>` | Call creates it; a later stage must fold it |

## Grounding

All checked references hold. The checks were text-only, with `grep` and `sed`; no symbol-reference tool was used. The spec renames or removes no symbol. A text search for `queue`, `pull` and `auto rows` in `plugins/my/bin`, the handoff and status skills, and `README.md` finds no existing use that would clash. Some references were confirmed directly:

- Review sub-step 4 writes `next=finished stopped=` (`SKILL.md:874-875`).
- "To end an abandoned run" writes `stopped="ended by the user"` (`SKILL.md:356`).
- Start check 1 refuses on a `MY_AUTORUN` mismatch (`SKILL.md:459-461`).
- Start check 7 (`SKILL.md:474-478`) and plan stage step 6 (`SKILL.md:538-545`) both handle an `approved` edit that is already committed.
- The README advises `Max runs: 1` on a 15 GB machine (`plugins/my/skills/handoff/README.md:390-395`).
- `status-scan.py` runs `handoff-state.py live` (`status-scan.py:188`).
- The parallel-runs spec's Out of scope matches the spec's quote (`docs/plans/2026-10-12-parallel-auto-runs-spec.md:53-55`).
- `a0144ee` is swappable-methods batch 2, by its commit message.
- Roadmap rows 9, 16, 29, 30, 31, 37, 39 and 40 all exist (`ROADMAP.md:70,116,169,180,184,206,127,76`).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Critical / High | design | **Waiting fixups from D3 become impossible to fold, so the queue stops at its first row.** D3 makes `--fixup` commits whenever `check` exits 0 at call time. It skips the fold when a run is live or the tree is dirty. On this machine at Max 1, "a run is live" is the queue's main use. The fixups then wait for "the spec's own stage". Before that stage runs, the run ahead finishes. Its `done` marks cite its squash commit, which comes after every queued spec's commit. From then on, `git-fold-fixups.py` refuses every fold whose oldest target is a queued spec. A Large row stops at plan stage step 8 (row 5). A Medium row stops at review sub-step 3 (row 17, `next=fold`). That second stop happens after the merge. The citation is permanent, so `resume` hits the same refusal each time, and at Max 1 every row behind waits. The same happens without a live run: if the first row's edit was a normal commit (`check` exit 1), its review folds nothing (sub-step 3 folds only when its own spec or task doc has waiting fixups), so the next row's fixup is stranded behind the first row's `done` mark. Without the queue, the stage's own `check` would have chosen a normal commit, so the queue creates this stop. A fixture repo reproduced it: `check` exits 0, then a later `docs/` file cites a later commit, then the fold prints `refused: commit 59377b8 is cited in docs/plans/…; a fold would give it a new hash`, exit 1. | `spec §D3` ("Each spec's own stage folds its waiting fixups later") ↔ `§Risk` ("Unfolded fixups stay on `<base>` until a stage folds them") ↔ `§Context` ("D3 fixes this"); `plugins/my/bin/git-fold-fixups.py:224-227`; `plugins/my/skills/handoff/SKILL.md:864-866` (sub-step 3 folds only the run's own fixups), `:871-874` (`done` marks cite the squash hash), `:223`, `:235` (rows 5 and 17) | Decision for the author. For example: make `--fixup` commits only when the call folds right away (no run live, clean tree, user agrees), and otherwise make one normal docs commit for all queued specs. The Trade-offs section rejected that option only for "a commit per call", which costs less than a stop that `resume` cannot clear. |
| Warning / Medium | design | **D2 handles only gates that name a row.** `my:status` step 5 also counts a row's own text, "Waits for …" and "after …", as a gate, and such text can name something that is not a row. Row 17 waits for "a second project to adopt the gates". Row 30 "also waits for 29" through prose in `## Order of work`. D2's skip table and `after` deal only with blocker rows and slugs. The spec does not say whether a row with a gate that is not a row is skipped or queued as ungated. Queuing it as ungated would break Goal 3. | `spec §D2` ↔ `§Goal` 3; `plugins/my/skills/status/SKILL.md:72-74`; `ROADMAP.md:24-26` | Decision for the author. For example, skip such a row with `gated by <text>, which no run will finish`. |
| Warning / Medium | design | **Overlap with a hand-started run is invisible to rule 4.** Rule 4 learns that a run is `exclusive` only from a `started` queue entry. In a project with a "Parallel runs" section, an auto run the user started by hand from a spec with no file list therefore counts as safe to share. `pull` can start a queued row beside it, although `my:status` never lists a pair with unknown overlap as safe. | `spec §D5` rule 4 ↔ `§D4` ("A `started` entry is the only record that a live run is `exclusive`"); `plugins/my/skills/status/SKILL.md:139-140`; `handoff-state.py:77-78` (the state file has no `exclusive` field) | Decision for the author: accept and state it in Risk, or treat any live run without a `started` entry as exclusive. |
| Suggestion / High | design | **`queue show` and the D7 lines leave two cases without output.** (a) The first entry passes rules 1 to 4, but the cap is full, for example because a stopped run holds the only slot. `queue show` prints `ready`, D7 correctly does not fire the needs-you line, but the in-progress line "`<k>` rows wait for `<what>`" has no `<what>`. (b) The first entry is itself `exclusive` while a non-exclusive run is live. Rule 4 blocks it, but `waits` is defined only for a blocker slug or a live *exclusive* run. | `spec §D7` ↔ `§D5` rule 4 | Name the output for both cases, for example `a free slot` and `no live run`. |
| Suggestion / High | design | **The "Silent stall" risk names one crash window but there are two.** A crash after `pull` has marked an entry `started` and written its state, but before Launch opens the window, leaves a live run with no window and an empty `stopped`. `my:status` lists it as in progress, not as needing the user. `resume` would fix it, but nothing says to run it. | `spec §Risk` ("Silent stall") ↔ `§D6`; `plugins/my/skills/status/SKILL.md:95,101` | Add the window to Risk, or have D7 flag a `started` run whose `next` is still its first stage. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Boundaries | `handoff-state.py` is the only writer of the queue file. Picking and starting happen in one locked command, as `start` already does (`handoff-state.py:31-36`). | Strong |
| Fit with what exists | `pull` reuses `start()`, the queue sits in a subfolder exactly as the locks already do (`handoff-lock.py:77`), and the refill reuses Launch, so no supervisor is needed (brief, Decision). | Strong |
| Contracts and flow | D5's rules decide every case the first review raised: blockers sorted first, safe pruning, a missing blocker, a refused start, and the ⚠ mark versus Finish. Rule 2 matches the real stopped values (`SKILL.md:356`, `:875`). | Strong |
| Failures and interactions | Each refill failure has a signal and a recovery command (D6). An invalid queue file refuses without writing (D5). | Moderate |
| Spec rules | "How to read this spec" comes first and lists the related documents in order. Risk, Dependencies and Trade-offs are present. | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| Failures and interactions | D3's waiting fixups are stranded by the next `done` mark (`git-fold-fixups.py:224-227`, reproduced in a fixture) | High |
| Contracts and flow | Gates that name something other than a row have no rule (`status/SKILL.md:72-74`) | Medium |
| Failures and interactions | Rule 4 cannot see a hand-started run whose overlap is unknown | Medium |
| Contracts and flow | `queue show` has no `<what>` for two blocking cases | Low |

## Not Applicable

- Failures and interactions, the off-path events check: the spec adds no UI. Its outputs are CLI lines and skill text.
- Spec rules, the Visual Language section: the spec adds no UI.

## Needs Investigation

- **Does an auto run's `done` mark set the roadmap row to ✅?** D2 treats a blocker as done only when its row is ✅, while D5 reads the state files. The handoff skill says only "Set the `done` marks as the project's rules say" (`SKILL.md:873`), and `docs-layout.md:167` names only the spec and plan. If a finished auto run leaves its row at 🚧 or 📋, a later call skips every row gated behind it with "blocked by row `<m>`, which nothing will start". The `done` commits in this repo's history were not traced. To resolve it, read the `done` commit of a recent auto run, or state in D2 that a blocker whose state file reads `next=finished` with an empty `stopped` also counts as done.

## Reasoning

The model is clean. There is one writer for the queue, one locked pick-and-start, and the refill is placed exactly where `next=finished` is written. The fixes since the first review hold against the repo. The verdict turns on D3's interaction with the fold script. D3 exists to remove a fold stop (§Context). Instead it creates a fold stop that `resume` cannot clear, in the queue's main case on this machine, and the fixture reproduced it. The other findings are gaps the author can close without changing the approach.

## Verdict

**Assessment:** Problematic
**Confidence:** High — the Critical finding was reproduced with the real `git-fold-fixups.py` in a fixture repo, and the skill lines that lead to the stop were read directly.
**Recommendation:** Rework D3 so the call makes `--fixup` commits only when it folds them in the same call, and otherwise makes normal docs commits. Then update Trade-offs and Risk to match, close the D2 gap for gates that are not rows, and decide rule 4's handling of hand-started runs.
