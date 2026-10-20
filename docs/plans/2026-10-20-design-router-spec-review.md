# Review: docs/plans/2026-10-20-design-router-spec.md

**Status:** review of docs/plans/2026-10-20-design-router-spec.md, 2026-10-20. Mixed: the gate-plus-router approach holds, but "Both" can hang with no sign in a detached window, and the "decided" rows rest on a false claim that no other installed skill does those jobs.

## Spec Summary

The spec adds a `PreToolUse` hook in `kit` that refuses Claude's calls to skills of design plugins, plus a `kit:design-router` skill. The router maps each design job to one skill (decided) or two (undecided), prints a command for the user to type, and can run both skills in two tmux sessions and keep the winner in `.claude/design-router.json`. A new core section sends all design work to the router. The spec also removes the `my:design-system` rules from the method (`my.md`, `docs-layout.md`, `my:handoff`, `my:spec-review`).

## System Model

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `kit:design-router` skill | The job table (IDs, skills, decided/undecided, trial points); the run steps; the "Both" flow | `plugins.json`, `.claude/design-router.json`, the session's skill list, tmux, `~/.cache/design-router/` | New (`plugins/kit/skills/design-router/` not found) |
| `plugins.json` | The state of each skill prefix: `routed`, `excluded`, `not-design` | Kit's install path (`$CLAUDE_PLUGIN_ROOT`, the cache copy) | New |
| Gate `design-router-gate.py` | The refuse or pass decision for each `Skill` call by Claude | `plugins.json`, the hook input `tool_input.skill`, `hooks.json` | New; pattern at `plugins/kit/hooks/method-guard.py:1-30` |
| `hooks.json` | The hook registrations of `kit` | Claude Code | Existing `plugins/kit/hooks/hooks.json:1-26` (SessionStart only today) |
| Project file `.claude/design-router.json` | The winner per job for one project | The router writes it; the project's own commit flow | New |
| Run folder `~/.cache/design-router/<run id>/` | `brief.md`, `A.md`, `B.md` | The router writes the brief; the child sessions write the results | New |
| Two child sessions (tmux windows) | Running one skill each on the brief | tmux, `claude`, F4 (a first prompt counts as typed), the permission mode they start in | New |
| Core section "Design work" | The trigger that sends design work to the router | `global/CLAUDE.md`, symlinked to `~/.claude/CLAUDE.md` | Existing file `global/CLAUDE.md:12-76` |
| `my.md` UI rules | The method's UI rules, without `my:design-system` | — | Existing `global/methods/my.md:117`, `:144`, `:171-213` |
| `test_neutral_core.py` | The rule that keeps kit and the core free of method names | `MY_NAMES`, `MY_BARE` | Existing `plugins/kit/tests/test_neutral_core.py:28-33`, `:73-86` |
| User settings | The `deny` rule `Skill(my:design-system)`; `design-superpowers@synced` on or off | — | Existing `~/.claude/settings.json` (deny list holds `Skill(my:design-system)`) |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Claude → gate | `Skill` tool input `{"skill": "<name>"}` | Claude Code |
| Gate → `plugins.json` | A read of the prefix state | `plugins.json` (kit, cache copy) |
| Gate → Claude Code | `permissionDecision: "deny"` with reason, or nothing, or `systemMessage` | Gate |
| Core line → Claude | An instruction to invoke the router first | Core |
| Router → `.claude/design-router.json` | Read of a winner; write of a new winner | Project (router writes, user commits) |
| Router → user | A command to type, or the question "A, B, or both?" | Router |
| User → Claude Code | A typed slash command (passes the gate, F4/F5) | User |
| Router → run folder | `brief.md` | Router |
| Router → tmux → child sessions | `claude '/<skill> Read <brief>. Write … A.md'` | Router |
| Child sessions → run folder | `A.md`, `B.md` | Each child session |
| Router `until` loop → run folder | Waits for both result files | Router (no timeout and no failure rule stated) |

## Grounding

The caller sweeps here were text-only (`grep -rn`, `find`), because no symbol-reference tool was available.

- `spec §Design › The table` ("A single-skill row is 'decided' because no other installed skill does that job") ↔ other installed skills do these jobs:
  - `research-synthesis`: `design-skills:ux-research` ("analyzing qualitative data, or synthesizing findings", `~/.claude/plugins/synced/*/64191f50-*/skills/ux-research/SKILL.md:3`), `design:user-research` ("Plan, conduct, and synthesize", `…/design/skills/user-research/SKILL.md:3`) and `product-management:synthesize-research` (`…/43a45b16-*/skills/synthesize-research/SKILL.md:3`).
  - `strategy`: `product-management:competitive-brief` (`…/43a45b16-*/skills/competitive-brief/SKILL.md:3`).
  - `chart`: `data:create-viz`, `data:build-dashboard` and `data:data-visualization` (`…/2529b2d1-*/skills/*/SKILL.md:3`).
- `spec §Risk R3` ("None of the three routed plugins mixes today") is true as written, but the mixed-plugin problem it describes already exists in two plugins the spec marks `not-design`: `product-management` and `data` (paths above).
- `spec §How to read this spec` leaves out `docs/plans/2026-10-18-brainstorming-routes-spec.md`. That spec hands two limits to row 70 (`:443-450`).
- `spec §Design › The user's settings` and `§Decisions D1` say the gate "ships with `kit`, so every machine with `kit` has it". The gate runs from the cache copy at `~/.claude/plugins/cache/claude-setup/kit/da05a3478280` (`~/.claude/plugins/installed_plugins.json`, `kit@claude-setup`). That copy is behind HEAD `a35663c`, so it reaches a machine only after a plugin update.

Checked and found true:

- the `my.md` trigger row (`global/methods/my.md:117`), the step-1 clause (`:144`), the `frontend-design` bullet (`:182`), the canvas paragraph (`:186-196`) and the inventory sentence (`:212-213`);
- `docs-layout.md` step 13 (`global/rules/docs-layout.md:171-174`);
- `handoff` row 19 (`plugins/my/skills/handoff/SKILL.md:277`), the shared-docs step (`:747`) and the README bullet (`plugins/my/skills/handoff/README.md:388-391`);
- the four lines in the spec-reviewer prompt (`plugins/my/skills/spec-review/spec-reviewer-prompt.md:70-73`) and `design-system` SKILL.md line 176;
- commit `f03b0e3`;
- the skill counts: 7 in `design`, 10 in `design-skills`, 9 in `design-superpowers`;
- `frontend-design` installed from `claude-plugins-official`;
- that `test_core_names_no_method` already accepts `kit:`;
- the Delegation keys (`plugins/my/skills/handoff/SKILL.md:130-133`).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | "Both" can hang with no sign. The two windows open detached (`-d`) with no permission-mode flag. Each child must read `brief.md` and write `A.md`/`B.md` under `~/.cache`, which is outside the project, so in default mode (user settings set no `defaultMode`) each one waits at a prompt nobody sees. The `until` loop has no timeout and no rule for a session that fails or never writes. The `$TMUX`-empty fallback does not say whether the router then waits and compares. A child session also loads the core line, which tells it to invoke the router before design work, and that could re-enter the router in a window nobody watches. `my:handoff` already solved the launch part: it opens a window only when `$TMUX` is set **and** the mode is `auto` or `bypassPermissions`, and it prints the command otherwise, because "in manual or acceptEdits mode it will wait at its first command". R6 names the prompt as untested but does not decide what happens. | `spec §Both` ↔ `plugins/my/skills/handoff/SKILL.md:314-321`, `:344-345`; `spec §Risk R6`; `spec §The core line` | Decision for the author: the mode flag or the fallback rule, a wait limit and what the router reports when it is reached, what the fallback path does after printing, and a brief line that tells the child not to invoke the router |
| Warning / High | design | The "decided" rows rest on a false claim. `research-synthesis` has routed competitors (`design-skills:ux-research`, `design:user-research`). `strategy` and `chart` have competitors in `product-management` and `data`, which the spec marks `not-design`, so the gate lets them through. Goal 1 ("No third-party design skill starts unless the user chose it") does not hold for those jobs, and Goal 3's trials never run for `research-synthesis`. | `spec §Design › The table` ↔ the SKILL.md paths under Grounding; `spec §Goal 1, 3`; `spec §plugins.json` | Decision for the author: make `research-synthesis` undecided or state why it is decided; decide whether `product-management` and `data` stay `not-design` (and update R3) or whether their overlapping skills are accepted as a known limit |
| Warning / High | design | Row 70's scope is only partly answered. The roadmap row says row 70 also settles "the checks a bounded UI change skips", and row 67's spec hands that limit to row 70. Deleting the audit row settles the timing limit, but the spec never says what a bounded UI change now checks, or that row 70 stops owning that limit. | `ROADMAP.md:225-226`; `docs/plans/2026-10-18-brainstorming-routes-spec.md:443-450` ↔ `spec §Goal`, `§Out of scope` | Decision for the author: settle it, or move it to Out of scope with the row that takes it; then list the row 67 spec in "How to read" |
| Warning / Medium | design | The gate's remedy for an unknown prefix costs more than the spec says. The gate reads `plugins.json` from `$CLAUDE_PLUGIN_ROOT`, which is the cached copy pinned to a commit. "Add it to the design router's plugins.json" therefore means a commit in claude-setup plus `claude plugin update` (or an edit to the cache that the next update wipes). Prefixes that are not plugins are also refused, and the user cannot "turn them off": nested project skills appear as `<dir>:<name>` on a name clash, and claude.ai skills use their own namespaces. Row 68 will add method plugins (`tutor` and others), and each one's skills are refused until it is listed. | `spec §The gate`, `§Risk R4`, `§Dependencies` (row 68) ↔ `~/.claude/plugins/installed_plugins.json` (`kit` at `da05a3478280`); `~/.claude/cache/changelog.md:4872`, `:1799-1801`; `docs/plans/2026-10-20-method-bundles-architecture.md:495` | Decision for the author: name the file to edit and the update step in the refusal text and R4; decide how non-plugin prefixes and row 68's new plugins are handled |
| Warning / Medium | design | No user is present in some sessions, and the spec does not say what the router does there. The router's only output is "the user types this" or a question. A `my:handoff auto` code stage, a `claude -p` run or a subagent that meets design work gets a refusal whose text says to invoke the router for a command to type, and nobody will type it. The spec does not say whether such a session goes on without the skill or stops. | `spec §Design` steps 4-5, `§The gate` refusal text, `§Decisions D1` ("also in auto mode") ↔ `plugins/my/skills/handoff/SKILL.md:324-331` (auto runs with no user) | Decision for the author: the router's behaviour when no user can answer |
| Warning / Medium | design | D6 says `my.md` "names jobs and the router, never a design skill", but the `my.md` edits keep the `artifact-diagramming` bullet and the Design-type bullet. The router's table also lists both, as the `diagram` and `draw` rows. Either D6 means only routed third-party skills, or these bullets must change too. | `spec §Decisions D6` ↔ `spec §global/methods/my.md`; `global/methods/my.md:177-184` | Decision for the author: narrow D6's wording or change the bullets |
| Warning / Medium | design | The reason given for skipping `my:architect` does not match the trigger. The spec says the change "has no load, storage or data forces". The trigger row fires on "new subsystem, or change to a data model, storage choice or public contract". This change adds a gate that runs in every session, plus a new committed per-project file format (`.claude/design-router.json`) that the router reads and writes. | `spec` header "Route" ↔ `global/methods/my.md:115` | Decision for the author: state why neither the subsystem test nor the contract test applies, or run `my:architect` |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Boundaries | The gate only decides refuse or pass. The router only picks the skill. Picks per project live in one file the router owns, and the prefix states live in one file the gate owns. Nothing is shared between two owners. | Strong |
| Fit | The gate follows `method-guard.py`'s shape: stdlib Python, always exits 0, notes in `systemMessage` (`plugins/kit/hooks/method-guard.py:21-27`). The rejected options (`ask` rule, `skillOverrides`, `deny` rules, a prompt hook) each have a stated, tested reason (F1-F3). | Strong |
| Failures | Fail-open on a broken list (D8) and the never-`allow` rule are explicit. The gate cannot block `kit` itself, so the router stays reachable. | Strong |
| Grounding | Every edit target for the removed `my:design-system` rules was found at the cited place (see Grounding). | Strong |
| Neutrality | The test change to whole-name matching lets `design:design-system` and `design-skills:design-systems` pass while a bare `design-system` still fails (`plugins/kit/tests/test_neutral_core.py:31-33`). | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Failures and interactions | "Both" has no mode handling, no wait limit and no failure rule, and it can re-enter the router (`spec §Both` ↔ `handoff/SKILL.md:314-321`) | High |
| Grounding / Goal | The "decided" basis is false for three jobs, and `not-design` plugins carry design skills past the gate | High |
| Scope | Row 70's bounded-UI limit is not addressed (`ROADMAP.md:225-226`) | Medium |
| Contracts | The remedy for an unknown prefix depends on the plugin cache and a commit, and nothing in the spec says so | Medium |
| Failures | The behaviour with no user present is not stated | Medium |

## Not Applicable

- Criterion 3, off-path UI events: the spec adds no screen, flow or record view.
- Criterion 6, Visual Language and the `docs/DESIGN-SYSTEM.md` checks: the spec adds no UI.

## Needs Investigation

- **`artifact-diagramming` as a skill name.** It was not found on disk under `~/.claude/skills`, `~/.claude/plugins` or the changelog (`dataviz` does appear in the changelog, at lines 551 and 4163). It is probably bundled with the Artifact tool. If its listed name has a prefix, the gate's "no `:`" rule and `test_table_skills_known` would treat it differently. A look at the session skill list would resolve this.
- **F1-F5 behaviour claims.** These are claims about Claude Code 2.1.303 and 2.1.304 that cannot be checked from the repo. The most load-bearing is that the hook sees the full `<plugin>:<skill>` name and never a bare name that Claude Code resolves to a plugin skill (changelog line 2657 suggests an unknown bare name errors rather than resolves). The rehearsal's step 1 checks one case.
- **The write to `.claude/design-router.json`.** `.claude/` is a protected path (changelog lines 5871 and 6922), so the router's write may prompt even in auto mode. Rehearsal step 4 would show it. The spec could record the result next to R6.

## Reasoning

The System Model has clean boundaries: one owner for the prefix states, one for the per-project picks, and one for the decision. The fail-open and never-`allow` choices are explicit, which is why the approach itself stands. The problems sit at the edges the model exposes. The router → child-session connection has no failure contract, and an existing pattern in the repo shows the exact hang it risks. The table's "decided" premise is false against the installed skills. The `plugins.json` remedy hides a commit-and-update step. None of these breaks the design, but each needs an author decision, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the two top findings rest on files opened in the repo and in the installed plugin folders.
**Recommendation:** Decide the "Both" failure contract (mode flag or fallback, wait limit, no re-entry) and the status of the `research-synthesis`, `strategy` and `chart` rows, then settle or move the bounded-UI limit before asking the user to approve the spec.
