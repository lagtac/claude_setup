# Review: docs/plans/2026-10-16-design-system-skill-spec.md

**Status:** review of docs/plans/2026-10-16-design-system-skill-spec.md, 2026-10-16. Mixed: the approach (a repo inventory, a counting script, a skill that routes to rows) is sound, but `ds-count.py` counts vendored files, and the new criterion 6 bullet flags every component that row 59 itself asks a spec to create. The spec answers all eleven findings: the editorial one is fixed in its text, and the author decided the ten design findings, all as recommended (D5 to D7, D11, D12, the criterion 6 bullet, `refresh`, the script's refusals and the Size line).

## Spec Summary

The spec adds a `my:design-system` skill with three modes (`audit`, `refresh`, `sync`). The skill keeps one inventory per UI project at `docs/DESIGN-SYSTEM.md`: its sources, its components, the patterns pages still build by hand, and a `ds-patterns` block of search expressions. A new script, `ds-count.py`, fills in the counts. The inventory is refreshed at step 13 of every row whose spec has a Visual Language section. A claude.ai Design System artifact is generated from the code so that canvases use exact tokens. The method, `docs-layout.md`, the handoff shared-doc list and spec-review criterion 6 each gain a rule that points to the inventory.

## System Model

All caller sweeps in this review were text-only (`grep -rn`). The reviewer had no symbol-reference tool.

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| Inventory `docs/DESIGN-SYSTEM.md` | Sources (tokens path, components folder, artifact link + synced commit), part 2 Components table, part 3 Hand-built table, `ds-patterns` block (the only home of counts, D4) | The skill (writes words), `ds-count.py` (writes counts), `sync` (writes the Sources artifact line) | New |
| `plugins/my/bin/ds-count.py` | Running each pattern, and the `count`/`files` values | Inventory block, repo files matched by `globs` minus `exclude`, `git rev-parse` | New (sibling style `plugins/my/bin/status-scan.py:1`) |
| `my:design-system` skill, `audit` | The search for components and hand-built patterns, the checklist judgement, the audit report, row proposals | `ds-count.py`, the user (confirms sources, picks rows), `my:roadmap-management` | New |
| `my:design-system` skill, `refresh` | Part 2 updates for components the merged row added or changed, new `component` lines | `ds-count.py`, the merged row (input not defined, see Issues), `sync` | New |
| `my:design-system` skill, `sync` | Publishing the artifact; the Sources link and synced commit | The Artifact tool's Design System type and its `from-code.md`, inventory part 2 | New |
| Design System artifact (claude.ai) | Published tokens in both themes, fonts, logos, README with component table and "Not synced" list | `sync` | New (external; link in spec §How to read item 7, not checkable from the repo) |
| Audit report `docs/reports/YYYY-MM-DD-design-system-audit.md` | One day's findings and "Where these went" | `audit` | New per run (format modelled on zitamu `docs/reports/2026-09-18-design-system-audit.md`) |
| Method rules in `global/methods/my.md` | Task-class trigger for `audit`; Visual Language rule; UI Design canvas rule and staleness check | Inventory, skill | Existing `global/methods/my.md:84`, `:111-139`, task table near `:52` |
| `docs-layout.md` step 13 | Where `refresh` is called and committed | Skill `refresh` | Existing `global/rules/docs-layout.md:167` |
| `my:handoff` shared-doc list and review step 8 | Shared-doc check before editing; `done` marks "as the project's rules say" | `docs-layout.md` step 13 | Existing `plugins/my/skills/handoff/SKILL.md:250`, `:719-720`, `:981`, `:1052` |
| Spec-review criterion 6 | The rule that checks a spec's Visual Language against the inventory | Inventory (read with `cat`) | Existing `plugins/my/skills/spec-review/spec-reviewer-prompt.md:63-69` |
| `git-fold-fixups.py` citation guard | Refusing a fold that rehashes a commit cited under the docs paths | Docs paths include `docs/`, so it covers the Sources synced commit | Existing `plugins/my/bin/git-fold-fixups.py:28`, `:48`, `:190-227` |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Task-class row → `audit` | Trigger: Medium/Large UI work with no inventory | Method (`my.md`) |
| `audit` → inventory | All four parts | Skill |
| `audit` / `refresh` → `ds-count.py` | A call with `--write` | Skill calls; script owns counts |
| `ds-count.py` → repo files | Glob expansion and regex reads | Script (file set is not defined as tracked-only, see Issues) |
| `ds-count.py` → inventory | Rewritten `count`/`files` keys | Script |
| `audit` → `my:roadmap-management` → `ROADMAP.md` | Row proposals the user accepts | Roadmap |
| Handoff review step 8 sub-step 4 → `docs-layout.md` step 13 | "Set the `done` marks as the project's rules say" | Handoff |
| Step 13 → `refresh` | A call with no stated input (which row merged, whether this is an auto run) | Undefined |
| `refresh` → `sync` | A call, skipped in an auto run | Skill |
| `sync` → artifact | Published tokens and README | Skill |
| `sync` → inventory Sources | Link and `synced from <short HEAD>` | Skill |
| UI Design rule → staleness command → `sync` | `git log <synced commit>..HEAD -- <paths>`; any output means sync first | Method; reads Sources |
| Artifact → Design canvas | Tokens the boards use | Artifact (mechanism not checkable from the repo) |
| Inventory → spec Visual Language | Component, variant and token names | Inventory |
| Inventory → spec reviewer | `cat docs/DESIGN-SYSTEM.md` | Inventory |
| Inventory Sources hash → fold guard | A citation under `docs/` | Fold script reads it |

## Grounding

Checked and holding: zitamu's `web/assets/css/tokens.css` exists, `web/components/Z*.vue` holds 23 files, row 74b's spec says "scoped to the page as `pages/match.vue` does (no shared field component exists)" (`~/projects/zitamu/real-estate-webapp/docs/plans/2026-10-15-agent-request-list-page-spec.md:369`) and "uses raw colours and Inter" (`:359`). The 2026-09-18 audit has the 39 raw inputs (`docs/reports/2026-09-18-design-system-audit.md:83`) and the withdrawn spacing count (`:49`). The extraction audit proposes rows 133 to 138 (`docs/reports/2026-10-16-component-extraction-audit.md:18`). Zitamu forbids `CLAUDE.md` edits (`CLAUDE.local.md:8`). Handoff stop row 19 is at `plugins/my/skills/handoff/SKILL.md:250`, and the Plan stage shared-doc sentence is at `:719-720`. `7e938b9` changes one line each in `global/methods/my.md` and `spec-reviewer-prompt.md`. `ROADMAP.md:13` says the next number is 64. The skill names `design:design-system` and `design-superpowers:design` exist in the installed plugins.

- spec §Edits to existing files ("joins the shared docs, in Plan stage step 6 and in stop row 19") and spec §Files ("Shared-doc list, two places") ↔ `plugins/my/skills/handoff/README.md:378`. That line also lists the shared docs ("A run edits `ROADMAP.md`, `CHANGELOG.md` or the plans index only when they hold no uncommitted edits"). The text sweep finds a third place that the spec does not name.

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Warning / High | design | `ds-count.py` expands globs over the working tree with no tracked-only or ignore rule. The spec's own example glob `web/**/*.vue` matches 72 files in zitamu, but only 64 are tracked: 8 are under `web/node_modules`. The spec's hex-colour example regex matches inside them (2 hits in `welcome.vue`, 1 in `error-404.vue`). Counts then change when dependencies are installed or upgraded, and differ between a checkout and a fresh worktree. That breaks Risk 3's claim that "the numbers are stable between runs". | `spec §ds-count.py`, `spec §Risk` 3; `~/projects/zitamu/real-estate-webapp/web/node_modules/nuxt/dist/app/components/welcome.vue` (found by the glob run) | Decision for the author: for example, match globs only against `git ls-files`, or add a default exclude. Either way it changes the script's contract. |
| Warning / High | design | The new criterion 6 bullet conflicts with row 59. Row 59 lets a shared component be "built in this row or in a shared row ordered before it". The inventory gains a `component` line only at the step 13 `refresh`, after that row merges. So a spec that labels a part «new: `<name>`» (as D8 asks), or maps to a component from an approved but unmerged row, always gets the "not listed … `design` when the part is new" finding. The bullet also gives no severity for that case, which the surfacing table needs. | `spec §Edits to existing files` (criterion 6 bullet) ↔ `spec §D8`, `§D6`; `global/methods/my.md:84` | Decision for the author: for example, exempt a part labelled new that the spec builds, or that an ordered row builds, and give the remaining case a severity. |
| Warning / High | design | The flow for a first project is undefined. `audit` never runs `sync`, so Sources reads `none yet`. The UI Design paragraph then tells the next canvas to run the staleness command, which needs a synced commit. For a new app with no tokens file, Sources cannot be filled. The spec also does not say whether an empty `ds-patterns` block counts as "missing" (exit 1) or valid. A new project also matches the `my:architect` trigger row, and the spec does not order that row against the new `audit` row. | `spec §The skill` (`audit` steps 1–6, "A new app"), `spec §D11`, `spec §Edits to existing files` (UI Design paragraph), `spec §ds-count.py` (exit rules); `global/methods/my.md` task table (architect row) | Decision for the author: for example, `audit` ends with `sync`, or `none yet` means "run `sync` first". Also state the empty-block rule and the order of the architect and audit rows. |
| Warning / Medium | design | `refresh` has no defined input. Step 2 updates "each component the merged row added or changed", but step 13 calls `my:design-system refresh` with no argument: no spec path, no squash commit. Step 3 skips `sync` "in an auto run", but no existing non-handoff skill has a way to know that it runs inside an auto stage. A hand run of `sync` or `refresh` also has no stated commit (only `audit` and the step 13 `refresh` do). | `spec §The skill` (`refresh`, `sync`), `spec §D10`; `grep "auto run\|auto mode"` over `plugins/my/skills/*/SKILL.md` finds the signal only inside `handoff/SKILL.md` (e.g. `:50`) | State the call's arguments (for example the spec path and an auto flag) and who commits a hand run. |
| Warning / Medium | design | The D5 trigger misses rows that create components. A pure-refactor extraction changes no UI, so its spec may have no Visual Language section. Zitamu's extraction audit calls those rows "a pure refactor" with no visual change. A Small change has no spec at all. In both cases `refresh` never runs for the row that added the component. A later `refresh` touches only components *its* row changed, so the component stays unlisted until the next `audit`. | `spec §D5`, `spec §The skill` (`refresh` step 2); `~/projects/zitamu/real-estate-webapp/docs/reports/2026-10-16-component-extraction-audit.md:44-46` | Decision for the author: for example, trigger on "the merged diff touches the components folder", or have `refresh` add any component under the Sources folder that the inventory lacks. |
| Warning / Medium | design | Nothing owns part 3 after `audit`. D6 says `refresh` adds no `hand-built` lines because row 59 makes every two-user element shared. But row 59 keeps a one-user element in its page, which is new hand-built markup that part 3 never records. And when a destination row ships and a pattern's count reaches 0, no mode updates "where it goes" or removes the row and its line. The Context names part 3 as the list a spec consults, so it goes stale in both directions. | `spec §D6`, `spec §The inventory` part 3, `spec §Context` gap 3; `global/methods/my.md:84` ("one with two or more becomes a shared component") | Decision for the author: say which mode adds single-user patterns (or that part 3 deliberately omits them), and which mode retires a pattern whose count reaches 0. |
| Warning / Medium | design | A glob that matches no file prints `0/0`, the same as "a component nobody uses is a real finding". The `audit` checklist then says "A component nobody uses is deleted". A typo in `globs` therefore leads to a proposal to delete a used component. | `spec §ds-count.py` ("A pattern that matches nothing prints `0/0`"), `spec §The skill` (`audit` step 4) | Decision for the author: for example, report "globs matched no files" apart from "no matches", or refuse it. |
| Warning / Medium | design | The spec states no size. It has no **Tasks** section, which implies Large with a separate plan. Under the size table it could also read as Medium (several files, no stored data), which would need Tasks inside the spec. The size decides the next artifact and the number of commits. | `spec` header and section list; `global/methods/my.md` size table; sibling specs state it (`docs/plans/2026-10-14-review-prep-script-spec.md:74`) | Decision for the author: state the size and the reason. |
| Suggestion / High | design | `refresh` runs `sync` at every UI row, even when the staleness command (D11) would print nothing. Each sync is an outward-facing publish, which the spec's own D10 reasoning treats as needing confirmation. | `spec §The skill` (`refresh` step 3) ↔ `spec §D11`, `§D10` | Run `sync` in `refresh` only when the staleness command prints output. |
| Suggestion / High | design | The `ds-patterns` key table says `name` "matches a row name in part 2 or 3", but `ds-count.py` does not check it. So the block and the tables can drift apart without notice. | `spec §The inventory` (key table) ↔ `spec §ds-count.py` (exit rules) | Add the name check to the script's refusals, or call the match advisory. |
| Suggestion / High | editorial | The handoff README also lists the shared docs, and the spec's two-place edit leaves it out. | `plugins/my/skills/handoff/README.md:378`; `spec §Files` | Add `handoff/README.md` to §Files and to the shared-doc edit. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Fit: the problem is real and evidenced | zitamu row 74b's "no shared field component exists" (`agent-request-list-page-spec.md:369`); six extractions afterwards (`component-extraction-audit.md:18`) | Strong |
| Contracts: counts have one owner and one home | `spec §D4`; the withdrawn count in zitamu's audit (`2026-09-18-design-system-audit.md:49`) shows the failure being fixed | Strong |
| Boundaries: the skill advises and routes, writes no component code | `spec §D3`; it matches "From report to roadmap" in `global/rules/docs-layout.md:31-55` | Strong |
| Fit: the alternatives are real | Option C's `design:design-system` exists with `audit \| document \| extend` modes (installed plugin `design/skills/design-system/SKILL.md`); the spec states what it lacks | Moderate |
| Fit: reuses existing hooks rather than new ones | `refresh` rides on handoff's "Set the `done` marks as the project's rules say" (`handoff/SKILL.md:981`, `:1052`); the Sources hash sits under `docs/`, so the fold guard covers it (`git-fold-fixups.py:28`, `:48`) | Moderate |
| Failures: an auto run never publishes, and a stale artifact is detectable | `spec §D10`, `§D11` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Grounding/contracts: counts not stable across checkouts | 72 globbed vs 64 tracked `.vue` files in zitamu | Medium |
| Contracts: criterion 6 bullet vs row 59 timing | `spec §Edits` ↔ `global/methods/my.md:84` | Medium |
| Flow gaps: first project, new app, `none yet` | `spec §The skill`, `§D11` | Medium |
| State ownership: part 3 and extraction rows fall outside every mode | `spec §D5`, `§D6` | Medium |
| Contracts: `refresh` input and auto-run signal undefined | `spec §The skill` | Medium |

## Not Applicable

- Criterion 3, off-path events: the spec adds no product UI; it changes skills, method text and a script.
- Criterion 6, Visual Language section and its per-element users: the spec adds no UI, so the section's absence is correct.

## Needs Investigation

- **Can a Design canvas use a Design System artifact's tokens?** The UI Design paragraph says "the canvas is built on the project's Design System artifact", and the spec's Goal depends on that. The repo cannot show whether the Artifact tool's Design type can reference a Design System artifact, or whether the board must copy the tokens in by hand. The spike (D8) may have shown this. A line in the spec saying how the spike linked the two would settle it.
- **The `from-code.md` guide and the re-sync merge rules** (`sync` steps 1–2) belong to the platform and are not in the repo. Running `sync` once on the spike artifact, as the spec's own testing strategy already plans, would confirm them.

## Reasoning

The System Model has clear owners for most state: counts belong to the script, words to the skill, and the artifact link to `sync`. The approach fits the repo's report → row → spec chain. The Warnings sit at the edges of the model. One is the file set the script reads. Another is the call into `refresh`, which has no defined input. A third is the timing between row 59's "build it in this row" and an inventory that only learns of the component after the merge. The last is a set of lifecycle gaps: a first project, extraction rows, and retiring part 3 rows. None of these needs a different approach, but each needs the author to decide a behaviour. So the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High. The two High-confidence Warnings rest on a glob run against zitamu and on a direct conflict between two spec sections and `my.md:84`.
**Recommendation:** Decide the script's file set and the criterion 6 exemption for parts the spec itself builds. Define `refresh`'s arguments and the `none yet` / new-app flow. State the size. Then fix the README sweep miss and rerun `my:spec-review`.
