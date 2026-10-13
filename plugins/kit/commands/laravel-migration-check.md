---
description: Validate Laravel migrations for safety, performance, and rollback
---

Review Laravel migrations for data loss, rollback safety, locking and integrity. This command is **read-only**: it reports, it changes nothing.

## Rules

- **Never run a migration.** Do not run `migrate`, `migrate:rollback`, `migrate:fresh`, `migrate:refresh`, `db:wipe` or `db:seed`. They change a real database, and this command cannot know which database `.env` points at. The only allowed artisan call is `php artisan migrate --pretend`, which prints the SQL without running it, and `php artisan migrate:status`.
- **Never print `.env` values.** Name the keys you read, not their values.
- **Items you cannot check from the code** (a backup exists, a downtime window is approved, the migration was tested on real data) are answered `Not verifiable here — <what the user must confirm>`. Never mark them passed.

## Which files

- If arguments are given, they are the migration files or a directory: **$ARGUMENTS**
- If none are given, review the migrations not yet run: `php artisan migrate:status` (the `Pending` rows). If that fails, for example because no database is reachable, review the migration files under `database/migrations/` that are uncommitted or changed on this branch (`git status --porcelain database/migrations`, `git diff --name-only <default-branch>...HEAD -- database/migrations`).
- If that finds no files, report `No migrations to check.` and stop.

## Process

Hand the review to the `kit:laravel-fullstack-expert` agent: use the Agent tool with `subagent_type: "kit:laravel-fullstack-expert"`. Its prompt contains the absolute path of each file, the Rules above, the checklist and the report template below, and this line: "Use the report template in this prompt instead of your default output format." Then print the agent's report unchanged.

The agent reads every file in full, and the models each migration touches (`app/Models/`). For each table the migration alters, it estimates the table size from the code (seeders, factories, comments) or marks it `unknown`.

## Checklist

Answer **every** item for **every** file, with `Pass`, `Fail`, `N/A — <reason>` or `Not verifiable here — <what to confirm>`. Do not skip items that look irrelevant.

1. `down()` reverses `up()` exactly (same columns, indexes, foreign keys, in reverse order).
2. No data loss without an explicit copy step: dropped columns or tables, narrowed types, `change()` that truncates.
3. Foreign keys: the referenced column exists, is indexed, and `onDelete` / `onUpdate` behaviour is intended.
4. Existing rows: a new `NOT NULL` column has a default or a backfill; a new unique index cannot fail on existing duplicates.
5. Locking: operations that rewrite or lock a large table (adding a column with a default on older MySQL, changing a type, adding an index without an online algorithm).
6. Indexes exist for the new columns used in `where`, `join` or `orderBy` in the code.
7. Data transformations inside the migration are idempotent and handle `NULL`.
8. Order: the migration's timestamp runs after the migrations it depends on.
9. Backup and downtime: always `Not verifiable here`, with what the user must confirm.

## Report template

```markdown
## Migration check

### <file name>

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | down() reverses up() | Pass / Fail / N/A — … / Not verifiable here — … | `file:line` |

**Reasoning:** [2–4 sentences linking the failed items to the verdict]
**Verdict:** Safe / Safe with conditions / Unsafe — [the conditions, or what must change]

[Repeat per file.]

### Before running in production
- [Every "Not verifiable here" item, as a question for the user]
```
