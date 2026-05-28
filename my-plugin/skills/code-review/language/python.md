### Python Review Checklist

Python-flavoured items. Apply each to the diff. Mark genuinely-inapplicable items as N/A with a reason.

1. **Code is simple and readable.** Idiomatic Python; no clever one-liners where a named loop is clearer; intent obvious from the code.
2. **Symbols are well-named.** `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE` for constants; names reflect current behaviour, not history.
3. **Type hints on public surfaces.** Public functions, methods, and dataclass fields have parameter and return annotations; no implicit `Any` leaks via untyped `**kwargs` or bare containers.
4. **mypy discipline.** No `# type: ignore` without a comment explaining why; `from __future__ import annotations` present where forward refs or recursive types appear.
5. **ruff cleanliness.** No unused imports, mutable default arguments (`def f(x=[])`), shadowed builtins, or unreachable branches.
6. **Exception breadth is controlled.** No bare `except:` or `except Exception:` without re-raise; `try` blocks wrap only the failing call; failures aren't swallowed into `None`/sentinel returns.
7. **Async pitfalls.** Coroutines are awaited; no blocking I/O (`requests`, `time.sleep`, sync `open()`, sync DB drivers) inside `async def`; no nested `asyncio.run()`; async context managers entered with `async with`.
8. **Pytest coverage is adequate.** New behaviour has tests; tests don't mock the unit under test; fixtures used over `setUp`; `@pytest.mark.parametrize` used instead of copy-pasted cases.
9. **Dataclass / Pydantic discipline.** No mutable defaults without `field(default_factory=...)`; value objects use `frozen=True`; validators are pure (no mutation/IO); pydantic v1 and v2 APIs not mixed in the same model.
10. **Package boundaries are clean.** No relative imports crossing package roots; no circular imports; `__init__.py` stays declarative (no side-effecting work at import time); production modules don't import from `tests/`.
11. **Input validation at trust boundaries.** User input, external API responses, env vars, and deserialised payloads are validated (pydantic, manual checks) before use; internal call sites need not re-validate.
12. **No exposed secrets.** No tokens, passwords, connection strings, or API keys in source or test fixtures; secrets come from env or a secrets manager.
13. **Performance is reasonable.** No accidental O(n²) (e.g., `in` against a list in a loop where a `set` works); generators used for large iterables; no N+1 ORM queries; no sync I/O in hot async paths.
14. **No bandaid fixes.** The diff addresses root causes; a `try/except` that hides a real bug, a `getattr(..., default)` papering over a missing attribute, or a sleep "fixing" a race is a bandaid.
15. **No fallback logic masking issues.** Silent defaults when the real path fails (env-var fallbacks, swallowed import errors, `or` chains hiding `None`) either fail loudly or are documented.
16. **Separation of concerns is maintained.** Web handlers don't run raw SQL, models don't render templates, CLI entry points don't hold business logic; side effects are pushed to the edges.
