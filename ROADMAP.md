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
  examples, not adopted. `e7d6a3b` →
  [`docs/harness-runtime-contract-DRAFT.md`](docs/harness-runtime-contract-DRAFT.md).
- 📋 **Adopt the runtime-command contract** — promote gate *logic*
  (`e2e-gate`/`review-gate`/`require-*`) into the plugin; have it read
  `<repo>/.claude/harness.json`. ⚠ rewrites safety machinery → **re-run the live
  e2e rehearsal**. Gate on a real project #2 validating the schema (rule of three).
- 💭 **Split `my` → core + opt-in packs** (`my-laravel`, `my-clinical`) — core
  keeps the `my:` namespace (no migration for universal items); only stack/domain
  agents move. Trigger: a genuinely new project. Caveat: plugin enablement is
  global-only, so packs need stack-conditioned triggers for per-repo behavior.
- 💭 **`/harness-init` bootstrap** — drops `.claude/settings.json` hook wiring +
  empty `harness.json` + docs/plans·ROADMAP·CHANGELOG stubs into a fresh repo.

## Other

Historical, self-contained efforts are tracked as dated specs in `docs/plans/`
(code-review consolidation, planning-standards single-source, briefing skill,
Opus prompt tuning, …) — not re-indexed here unless they spawn open follow-ups.
