# Harness Roadmap

Living index of work on the Claude harness (global instructions, `my` plugin,
rules, hooks). Keep it short — details live in the linked `docs/plans/` docs.
Most history is tracked only as dated `docs/plans/` files; this file exists so
deferred follow-ups don't get buried inside one of them.

**Status legend:** ✅ shipped · 🚧 in progress · 📋 planned · 💭 discussed, not scheduled

---

## Harness generalization

Make the harness reusable in new projects without forking copies. Spec:
[`docs/plans/2026-06-16-harness-generalization-audit.md`](docs/plans/2026-06-16-harness-generalization-audit.md).

- ✅ **Global orphan-plan hook** — promoted `check-orphan-plans.sh` into the `my`
  plugin (SessionStart, all repos). `150bb44`; annotator-local copy removed
  (`0ec215c`).
- ✅ **Runtime-command contract — DRAFT** — schema + annotator + Node/Python
  examples, written down but not adopted. `e7d6a3b` →
  [`docs/harness-runtime-contract-DRAFT.md`](docs/harness-runtime-contract-DRAFT.md).
- 💭 **Generalize the gates — deferred, no second consumer yet.** Promoting the
  gate logic (`e2e-gate`/`review-gate`/`require-*`) into the plugin behind a
  per-repo `.claude/harness.json`, the core + stack/domain pack split, and a
  `/harness-init` bootstrap are all designed in the spec but blocked on one
  trigger: a real project adopting the gates. Today they live in exactly one
  subproject (`diagoradisa-annotator`); no other repo — Laravel or Python — pulls
  on them. Rule of three: don't crystallize the `harness.json` schema on n=1, and
  adoption ⚠ rewrites safety machinery → re-run the live e2e rehearsal first.

## `my` plugin hygiene

Follow-ups spawned by the planner retirement. Spec:
[`docs/plans/2026-09-11-retire-planner-path-spec.md`](docs/plans/2026-09-11-retire-planner-path-spec.md)
(see its "Out of scope").

- ✅ **Retire the planner path** — deleted `/my:plan`, the `my:planner` agent and
  `/my:task`; Superpowers owns planning. Plan template moved to the lazy
  `global/rules/plan-format.md`. Supersedes the unexecuted
  [`2026-05-28-single-source-planning-standards.md`](docs/plans/2026-05-28-single-source-planning-standards.md).
- ✅ **`clean-plans` scans abolished paths** — now scans only `docs/plans/`
  and names plans with no `-plan` suffix. `d58da69`.
- ✅ **`tune-claude-instructions` is a model behind** — wording no longer pins
  Opus 4.7; adds a tool check for tools subagents never get. `6958704`.
- ✅ **Plugin docs drift** — `README.md` documents all skills, agents and hooks;
  `plugin.json` names skills and hooks. `965d423`.
- ✅ **`summarizer` plan-path convention** — reads and writes dated files in
  `docs/plans/`, and reads the diff itself. `dd45902`;
  the same `$planDirectory` fix for `optimize-prompt` in `60f6b67`.

## Design workflow

- ✅ **`my:architect`** — forces-first architecture brief before brainstorming:
  labelled forces, collapse gate, parallel candidates, evaluation and estimate
  scripts. Shipped in `3d9a7f9`; `global/CLAUDE.md` now runs it before
  brainstorming for new systems and contract changes. Spec:
  [`docs/plans/2026-09-17-architect-skill-spec.md`](docs/plans/2026-09-17-architect-skill-spec.md),
  plan: [`docs/plans/2026-09-17-architect-skill.md`](docs/plans/2026-09-17-architect-skill.md).
- ✅ **`my:handoff`** — the plan, code and review stages run in their own
  top-level sessions, opened in tmux windows, so each stage reads the real
  `CLAUDE.md` rules. Shipped in `88afd8a`; the review stage was added on
  2026-09-29. Spec:
  [`docs/plans/2026-09-21-handoff-spec.md`](docs/plans/2026-09-21-handoff-spec.md),
  plan: [`docs/plans/2026-09-21-handoff.md`](docs/plans/2026-09-21-handoff.md).
  `my:soundness-review --plan-only` shipped in `7740bf7`, so a busy `main`
  no longer stops the plan stage. Spec:
  [`docs/plans/2026-09-30-soundness-plan-only-spec.md`](docs/plans/2026-09-30-soundness-plan-only-spec.md),
  plan: [`docs/plans/2026-09-30-soundness-plan-only.md`](docs/plans/2026-09-30-soundness-plan-only.md).
- ✅ **`my:tutor`** — a learning mode: the student writes the code, the tutor
  sets exercises, gives hints and keeps notes in `docs/learning/`, with the
  `tutor` output style. Shipped in `1e69584`; known limits are in the spec's
  Risk section. Spec:
  [`docs/plans/2026-10-06-tutor-spec.md`](docs/plans/2026-10-06-tutor-spec.md).

## Workflow efficiency

Findings of
[`docs/reports/2026-10-09-workflow-efficiency-critique.md`](docs/reports/2026-10-09-workflow-efficiency-critique.md).
Rows are unordered unless a row says what it waits for. S2 and S3 got no row;
the report says why.

- ✅ **Trigger table contradictions** — fix: the "Invoke first" rows for
  integrating and reviewing now name the Git Workflow steps and the
  end-of-branch reviews. Report C1, C2.
- ✅ **UI rule has a Small case** — a Small change that adds no screen or state
  needs no design canvas. Report S1.
- 💭 **Fold script for docs fixups** — the fixup, `branch --contains` and
  autosquash steps become one script that refuses with a reason. Report G1.
- 💭 **Git steps leave the always-loaded file** — move Git Workflow steps 1 to
  14 into a path-scoped rule or `my:handoff`, keeping a pointer. Waits for the
  fold script row. Report G2.

## Other

Historical, self-contained efforts are tracked as dated specs in `docs/plans/`
(code-review consolidation, planning-standards single-source, briefing skill,
Opus prompt tuning, …) — not re-indexed here unless they spawn open follow-ups.
