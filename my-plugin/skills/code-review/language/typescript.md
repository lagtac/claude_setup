### TypeScript Review Checklist

TypeScript-flavoured items. Apply each to the diff. Mark genuinely-inapplicable items as N/A with a reason.

1. **Code is simple and readable.** No unnecessary cleverness; intent is clear from the code or a minimal comment.
2. **Symbols are well-named.** Functions, variables, types, and components match what the code actually does, not what it used to do.
3. **No exposed secrets.** No tokens, API keys, or credentials in source, `.env` examples, or test fixtures.
4. **Input validation at trust boundaries.** Request bodies, query params, external API responses, and `JSON.parse` results are validated (zod, io-ts, manual guards) before use — `as Foo` is not validation.
5. **`any` leaks and unsafe casts.** Reject explicit `any`, `as unknown as X` laundering, and `@ts-ignore` / `@ts-expect-error` without a reason comment explaining what's suppressed and why.
6. **Null/undefined narrowing.** Non-null assertions (`!`) need justification; optional chaining shouldn't paper over a missing existence check; `Array.find()`, `Map.get()`, and `Record` lookups return `T | undefined` and must be handled.
7. **Type widening.** Watch for `let x = []` inferring `any[]`, generics defaulting to `{}`/`unknown` when a narrower type exists, and `as const` missing on literal config.
8. **Exhaustive switch / discriminated unions.** Switches over a union end with `default: assertNever(x)` (or equivalent); adding a variant must surface as a type error, not a silent fallthrough.
9. **Async error propagation.** No floating promises (missing `await` or `.catch`), no `try/catch` around `await` that logs and swallows, no `async` functions whose rejections nobody observes.
10. **React hooks rules.** Hooks only at the top level of components/custom hooks — never inside conditionals, loops, or callbacks. `useEffect`/`useCallback`/`useMemo` dependency arrays are complete and stable.
11. **React rendering correctness.** List items have stable keys (not array indices for reorderable lists); inputs are consistently controlled or uncontrolled; state is updated immutably, never mutated in place.
12. **Error handling at boundaries.** Errors at fetch/IO/parse boundaries are handled or propagated meaningfully — not stringified, not swallowed into a toast-and-continue.
13. **ESLint / Prettier conventions.** No violations the project enforces: unused vars/imports, `no-console` in production code, `react-hooks/exhaustive-deps`, `react-hooks/rules-of-hooks`, formatting drift.
14. **Test coverage is adequate.** New behavior has tests; changed behavior has updated tests; tests exercise real code paths rather than asserting on mocks of the unit under test.
15. **No bandaid fixes or silent fallbacks.** The diff treats root causes; `?? defaultValue`, empty `catch`, and "if undefined just return" patterns must be deliberate, not cover for an upstream bug.
16. **Separation of concerns.** Components don't run data-layer code directly, hooks don't reach into the DOM, server handlers don't mutate UI state — layer boundaries hold.
