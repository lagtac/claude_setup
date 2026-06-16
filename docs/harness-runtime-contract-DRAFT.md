# Harness Runtime-Command Contract — DRAFT (not adopted)

**Status:** DRAFT. No code reads this yet. It is the schema that the gate logic
(`e2e-gate`, `review-gate`, `require-impl-review`, `require-seam-e2e`) will read
from a repo-local file *once promoted into the plugin* — deferred until a second
project validates it (rule of three; see
`docs/plans/2026-06-16-harness-generalization-audit.md`).

## Why
Today's gates hardcode this project's stack: `docker compose run node pnpm`,
`./scripts/dartisan`, `pnpm test:e2e`, `resources/js/annotator`, `/login`. That
coupling is why they don't travel. The fix is the same `logic + injected-config`
split already proven by `seam-digest.sh` (logic) × `SEAM_PATHS` (override):
generic logic in the plugin, per-repo specifics in one file the scripts read via
`$CLAUDE_PROJECT_DIR` (verified idiomatic — no native per-repo plugin config
exists).

## Location (when adopted)
`<repo>/.claude/harness.json`. Open question retained: merge into
`.claude/settings.local.json` vs standalone — decide at adoption.

## Schema
| Key | Type | Meaning | Consumed by |
|---|---|---|---|
| `integration_branch` | string | branch the gates guard (commits *to* it are gated) | require-impl-review, require-seam-e2e |
| `impl_globs` | string[] | paths that count as "implementation" landing on the branch | require-impl-review |
| `review_glob` | string | path pattern a review artifact must match in the same change | require-impl-review |
| `seam_globs` | string[] | the contract "seam" — editor/producer + receivers + e2e fixtures | seam-digest, require-seam-e2e |
| `run.build` | string | build assets so the app serves current code | e2e-gate |
| `run.serve_check` | string | command that exits 0 iff the app is up (post-build) | e2e-gate |
| `run.db_seed` | string | seed the e2e fixture | e2e-gate |
| `run.test` | string | frontend/unit test command (review-gate) | review-gate |
| `run.test_e2e` | string | the real-gesture e2e suite (deterministic) | e2e-gate |

Notes:
- `run.*` are opaque shell strings — the contract is "named commands," not their
  implementation, so docker wrappers here become plain `npm`/`pytest`/`go test`
  elsewhere with no logic change.
- Gates must **degrade to skip, not block**, when `harness.json` is absent or a
  `run.*` key is missing — a new repo without the file must not be un-committable.

## Worked example — annotator (reverse-engineered from current gates)
```json
{
  "integration_branch": "main",
  "impl_globs": ["resources/js/annotator/**"],
  "review_glob": "docs/plans/*impl-review*.md",
  "seam_globs": [
    "resources/js/annotator/**",
    "app/Http/Requests/StoreAnnotationRequest.php",
    "app/Http/Requests/UpdateAnnotationRequest.php",
    "app/Http/Controllers/AnnotationController.php",
    "app/Http/Controllers/BatchController.php",
    "app/Http/Controllers/BatchItemController.php",
    "app/Http/Controllers/ImageController.php",
    "app/Http/Controllers/PatientController.php",
    "routes/web.php",
    "database/seeders/E2eFixtureSeeder.php"
  ],
  "run": {
    "build":       "docker compose run --rm -w /var/www/html node pnpm run build",
    "serve_check": "curl -fsS -o /dev/null --max-time 10 http://localhost/login",
    "db_seed":     "./scripts/dartisan db:seed --class=E2eFixtureSeeder --force",
    "test":        "./scripts/dpnpm test",
    "test_e2e":    "pnpm test:e2e"
  }
}
```

## Hypothetical second example — a plain Node/Python service (sketch, to stress the schema)
```json
{
  "integration_branch": "main",
  "impl_globs": ["src/**"],
  "review_glob": "docs/plans/*impl-review*.md",
  "seam_globs": ["src/api/**", "src/schemas/**", "tests/e2e/**"],
  "run": {
    "build":       "npm run build",
    "serve_check": "curl -fsS -o /dev/null localhost:3000/health",
    "db_seed":     "npm run seed:e2e",
    "test":        "npm test",
    "test_e2e":    "npx playwright test"
  }
}
```
This sketch is the n=2 the schema needs before freezing — adopt only after a real
second project exercises it.
