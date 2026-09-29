---
paths:
  - "**/*.php"
  - "**/composer.json"
  - "**/artisan"
---

# PHP (Laravel / Sail) Commands

- **Run artisan:** `sail artisan <command>`
- **Run tests:** `sail artisan test` or `sail artisan test --filter=<name>`
- **Serve:** `sail up -d`
- **Composer:** `sail composer <command>`
- **Lint (Pint):** `sail pint` or `sail pint --test` (dry-run)
- **Lint (CS Fixer):** `sail php-cs-fixer fix` or `sail php-cs-fixer fix --dry-run`
