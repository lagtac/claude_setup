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

## Other

Historical, self-contained efforts are tracked as dated specs in `docs/plans/`
(code-review consolidation, planning-standards single-source, briefing skill,
Opus prompt tuning, …) — not re-indexed here unless they spawn open follow-ups.
