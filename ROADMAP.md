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

## my-plugin hygiene

Follow-ups spawned by the planner retirement. Spec:
[`docs/plans/2026-09-11-retire-planner-path-spec.md`](docs/plans/2026-09-11-retire-planner-path-spec.md)
(see its "Out of scope").

- ✅ **Retire the planner path** — deleted `/my:plan`, the `my:planner` agent and
  `/my:task`; Superpowers owns planning. Plan template moved to the lazy
  `GLOBAL-rules/plan-format.md`. Supersedes the unexecuted
  [`2026-05-28-single-source-planning-standards.md`](docs/plans/2026-05-28-single-source-planning-standards.md).
- 💭 **`clean-plans` scans abolished paths** — discovers from
  `docs/superpowers/plans/` and `docs/superpowers/specs/`, which `GLOBAL-CLAUDE.md`
  overrides to `docs/plans/`. Bug fix, one file.
- 💭 **`tune-claude-instructions` is a model behind** — scoped to "Opus 4.7+"
  in 8 places, and missing the subagent tool-filtering lesson it should own
  (learned in `2c459be`).
- 💭 **Plugin docs drift** — `README.md` documents none of the 9 skills;
  `plugin.json` still describes the plugin as "commands and agents", omitting
  skills and hooks.
- 💭 **`summarizer` plan-path convention** — writes
  `$planDirectory/{name}-plan.md`, contradicting the mandated
  `YYYY-MM-DD-<slug>.md` naming.

## Design workflow

- 🚧 **`my:architect`** — forces-first architecture brief before brainstorming:
  labelled forces, collapse gate, parallel candidates, evaluation and estimate
  scripts. Spec:
  [`docs/plans/2026-09-17-architect-skill-spec.md`](docs/plans/2026-09-17-architect-skill-spec.md),
  plan: [`docs/plans/2026-09-17-architect-skill.md`](docs/plans/2026-09-17-architect-skill.md).

## Other

Historical, self-contained efforts are tracked as dated specs in `docs/plans/`
(code-review consolidation, planning-standards single-source, briefing skill,
Opus prompt tuning, …) — not re-indexed here unless they spawn open follow-ups.
