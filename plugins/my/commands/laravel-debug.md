---
description: Laravel-specific debugging with systematic diagnostics
---

Find the root cause of a Laravel problem, then propose a fix. The problem: **$ARGUMENTS**

If no problem is given, ask the user to describe it (the symptom, where it shows, since when) and stop.

## Process

Hand the diagnosis to the `my:laravel-fullstack-expert` agent: use the Agent tool with `subagent_type: "my:laravel-fullstack-expert"`. Its prompt contains, word for word: the problem above, the absolute project root (`git rev-parse --show-toplevel`), the Rules, the Diagnostic stages and the report template below, and this line: "Use the report template in this prompt instead of your default output format."

When the agent returns, print its report. Then ask the user whether to apply the proposed fix. Apply it only after a yes, and then run the check the report names.

## Rules

- **Diagnose, do not change.** The agent edits no file and runs nothing that writes: no `migrate` of any kind, no `db:seed`, no `queue:work` against a real queue, no `composer update`. Read-only commands are fine: `route:list`, `migrate:status`, `config:show`, `tinker --execute` with a read-only query, `tail` on logs.
- **Never print `.env` values**, and never paste secrets from logs. Name the key, not its value.
- **Evidence first.** Every claim in the report cites a `file:line`, a log line, or a command and its output.

## Diagnostic stages

Work through the stages in order. At each stage, write what you checked and what it showed before moving on. Stop at the stage that explains the symptom, and say why the later stages are not needed.

1. **Reproduce.** Find the exact request, command or job that fails. Read the newest entries in `storage/logs/laravel.log` (`tail -n 200`) and match the error to the symptom.
2. **Health.** `php artisan migrate:status` (pending migrations), configuration and route cache state, required services (database, queue, cache) reachable.
3. **Trace the request.** Route (`php artisan route:list --path=<uri>`) → middleware → controller or job → model and relationships → view or resource. Read each file on the path.
4. **Isolate.** Name the smallest input that triggers the problem, and the one change that removes it.

Common areas, to check when the stage leads there: route model binding, middleware order, N+1 or missing eager loads, mass-assignment guards, policies and gates, stale config or view cache, queue serialization, CORS and CSRF on API routes, Vite asset paths.

## Report template

```markdown
## Diagnosis

**Symptom:** [one line, as the user described it]
**Reproduced:** yes / no — [how]

### What was checked
1. [stage] — [what was checked] → [what it showed, with evidence]

### Root cause
[2–4 sentences, with `file:line`. If unsure, say so and give the two most likely causes.]

### Proposed fix
[The change, as a diff or a short code block, with the files it touches.]

### How to confirm the fix
[The exact command, request or test that shows the fix works.]
```
