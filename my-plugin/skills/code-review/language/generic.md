### Generic Review Checklist

Language-agnostic items. Apply each to the diff. Mark genuinely-inapplicable items as N/A with a reason.

1. **Code is simple and readable.** No unnecessary cleverness; intent is clear from the code or a minimal comment.
2. **Functions and variables are well-named.** Names match what the code actually does, not what it used to do.
3. **No duplicated code.** Three similar lines are fine; a fourth suggests an abstraction is warranted.
4. **Proper error handling.** Errors at system boundaries are handled or propagated meaningfully — not swallowed, not stringified into oblivion.
5. **No exposed secrets or API keys.** No tokens, passwords, or credentials in the diff (including test fixtures).
6. **Input validation at trust boundaries.** User input, external API responses, and file/IPC inputs are validated before use. Internal call sites need not validate.
7. **Test coverage is adequate.** New behavior has tests; changed behavior has updated tests; tests verify real behavior, not mocks of the code under test.
8. **Performance is reasonable.** No obvious O(n²) where O(n) suffices; no synchronous I/O in hot paths; no N+1 queries.
9. **No bandaid fixes.** The diff treats root causes, not symptoms. A try/except that hides the real bug is a bandaid.
10. **No backwards-compatibility hacks.** Renamed-but-still-exported symbols, dead `// removed` comments, and dual code paths "for migration" are debt unless explicitly justified.
11. **No fallback logic masking issues.** Fallbacks that silently substitute defaults when the real path fails make incidents harder to diagnose. Either fail loudly or document the fallback.
12. **Separation of concerns is maintained.** Layers don't reach across each other (e.g., HTTP handlers running raw SQL, UI components mutating global state).
