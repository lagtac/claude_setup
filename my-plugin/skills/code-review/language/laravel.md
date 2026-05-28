### Laravel Review Checklist

Laravel-flavoured items. Apply each to the diff. Mark genuinely-inapplicable items as N/A with a reason.

1. **Code is simple and readable.** Intent is clear from the code; no clever one-liners where a named method would do.
2. **Functions, variables, and Eloquent relations are well-named.** Names match current behaviour, not historical artefacts; relation methods read naturally (`$user->posts`, not `$user->getPostsList()`).
3. **No exposed secrets.** No API keys, tokens, DB credentials, or `.env` values in the diff — including test fixtures, seeders, and config defaults.
4. **Input validation via FormRequest.** State-changing controllers use a dedicated `FormRequest` with explicit rules; inline `$request->validate()` is acceptable only for trivial single-field cases. No unvalidated user input reaching models.
5. **Authorization via Policies or Gates.** Access checks use `authorize()`, `Gate::allows()`, or policy methods — not ad-hoc `if ($user->role === 'admin')` scattered through controllers.
6. **CSRF protection on state-changing routes.** `POST`/`PUT`/`PATCH`/`DELETE` routes sit inside the `web` middleware group or explicitly include `VerifyCsrfToken`; any exception in `$except` is justified.
7. **No Eloquent N+1 queries.** Loops over collections that access related models eager-load via `with()`; no `->count()`, `->first()`, or relation traversal inside iteration without it.
8. **Blade output is escaped.** `{{ }}` for any user-influenced data; `{!! !!}` only for content from a trusted source (sanitised HTML, internal config) and the source is obvious from context.
9. **Vite for asset bundling.** Frontend assets loaded via `@vite([...])` in Blade; no raw `<script src="/build/...">` or hand-rolled paths into `public/build/`.
10. **Livewire patterns are sound.** `wire:model.live` is reserved for inputs that genuinely need live updates (debounced where appropriate); sensitive data isn't hydrated into public properties; `wire:click` is on real interactive elements (`<button>`, `<a>`), not `<div>`s.
11. **Queue jobs are production-ready.** Jobs declare `$tries` and `$backoff`, implement `failed()` for terminal handling, and are idempotent against retries (no double-charging, double-emailing, or duplicate inserts).
12. **Accessibility basics.** `<img>` has meaningful `alt`; interactive non-button elements carry appropriate ARIA roles/labels; semantic tags (`<button>`, `<nav>`, `<main>`) used over styled `<div>`s.
13. **Error handling at boundaries.** External HTTP calls, queue dispatches, and filesystem operations either handle failure explicitly or let exceptions propagate to the framework handler — not swallowed into `null` or stringified logs.
14. **Test coverage is adequate.** New routes, jobs, policies, and Livewire components have feature/unit tests; tests use real DB transactions (`RefreshDatabase`) and assert behaviour, not mock returns.
15. **No bandaid fixes or fallback masking.** A `try/catch` that returns a default on failure must be justified; silent fallbacks (cache miss → empty array → "works") hide incidents. Fail loudly or document why not.
16. **Separation of concerns.** Controllers stay thin (validate, authorize, delegate); business logic lives in services, actions, or models — not in Blade, not in routes, not in middleware. Pint and PHPStan pass on the diff.
