# CLAUDE.local.md

This file guides Claude Code in this repository. Since 2026-10-07 we own the
whole checkout: the web app, the API and the infra.

## Hard constraint

Never edit or write to `CLAUDE.md` in the project root. You may read it. My
instructions live in `CLAUDE.local.md` (this file) only.

## Scope

Older documents might say "the web team cannot edit `api/`". Read those as history, not as a rule.

- `openapi/openapi.yaml` is the API contract. An API change that touches a
  path it lists updates it in the same branch.
- An API change to stored data, permissions or a response shape is Large
  under the global size rules.

## Project facts

- **Method:** my
- **Commit scopes:** `web`, `api`, `infra`
- **Test command:** `npm test` for `web/`, `make test-api` for `api/`
- **Plans index:** `docs/plans/README.md`
- **Remote:** origin (gitlab.indigital.gr)

@~/.claude/methods/my.md

## What this is

zitamu.gr is a reverse real-estate marketplace for Greece. Buyers post demand
profiles. Verified sellers and agents browse that demand and make the first
contact. The brand is always lowercase (`web/utils/brand.ts`).

Read `docs/ONBOARDING.md` first. It covers the UI redesign, the design tokens,
and how the landing is measured against the designer's mocks.
`docs/ARCHITECTURE.md` and `progress.md` are out of date. Trust the code and
`CHANGELOG.md` over both.

## Commands

Everything runs in Docker. The host is a shared server, so do not use `sudo`,
host package installs or `docker system prune`.

```bash
make setup        # first run on a clone
make up           # dev stack; web on :54300 (LAN-reachable), Mailpit :54025
make db           # migrate + taxonomy and areas + demo accounts + dev listings + cache clear; safe to rerun
make seed-demo    # buyer@demo.test / seller@demo.test / agent@demo.test, password "password"
make seed-listings # 40 sale listings, agent1-4 / seller1-6 @listings.test; photos if assets/properties/ exists
make test-web     # npm test = typecheck + vitest (node) + vitest (Nuxt environment)
make test-api     # the API suite, on isolated sqlite; never touches dev data
make lint-api     # Laravel Pint; lint-api-check only checks
make e2e          # Playwright against a separate `realestate_e2e` stack (about 3.5 minutes)
make tiles        # fetch the self-hosted map tiles (gitignored)
```

`make setup` and `make up` never migrate. On a fresh clone or a recreated
`realestate_pgdata` volume, every API call that reads data returns 500
(`relation ... does not exist`) until `make db` runs. The listing photos in the gitignored `assets/properties/` come from another agency's site with no licence: never commit or deploy them.
`make up` creates the `storage:link` that serves listing photos when it is
missing.

Run a single web test in the web container. `run --rm` skips the
install-on-start step, so `web/node_modules` must already exist (`make up`
creates it). With the stack up, `exec web` works too.

```bash
docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm web npx vitest run tests/status.spec.ts
docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm web npx vitest run -c vitest.nuxt.config.ts tests/nuxt/landing.spec.ts
docker compose -f infra/docker-compose.yml --env-file infra/.env run --rm web npm run typecheck
```

- `web/tests/*.spec.ts` are pure-logic node tests (`vitest.config.ts`).
- `web/tests/nuxt/*.spec.ts` mount real components in a Nuxt runtime, with the
  API stubbed through `registerEndpoint` (`vitest.nuxt.config.ts`).
- `web/e2e/` is Playwright. From the main checkout it runs through `make e2e`.
  E2E does not run in CI, so run it locally before pushing UI changes.
- **From a worktree, never run `make e2e` or `make` at all.** Serve the
  worktree with `web/scripts/preview.sh`. Run e2e against it with
  `web/scripts/e2e-worktree.sh <worktree path>`. Every plan that uses a
  worktree calls these two scripts. `e2e-worktree.sh --no-journeys <path>` runs only the browser checks, in about half the time. Tag a new journey test
  `{ tag: '@journey' }`.
- **A branch that changes `api/`** runs e2e with
  `web/scripts/e2e-worktree.sh --api <path>`, which also serves the worktree's
  `api/`. It mounts the main checkout's `vendor/` and `.env`, so the branch must
  add no Composer package. Run the API tests and Pint against the worktree's
  code with `web/scripts/api-worktree.sh <worktree path> php artisan test`
  (or `./vendor/bin/pint --test`). It uses the same settings as
  `make test-api`.
- To rerun one e2e test, run it against a running preview (`:54310`). It takes
  seconds.

- `--network host` matters: Vite blocks any hostname but localhost.

  ```bash
  docker run --rm --network host -u $(id -u):$(id -g) -e HOME=/tmp \
    -e PLAYWRIGHT_BASE_URL=http://127.0.0.1:54310 -v <worktree>/web:/app -w /app \
    mcr.microsoft.com/playwright:v1.55.1-noble \
    npx --no-install playwright test e2e/landing.spec.ts -g "<test name>" --reporter=line
  ```

  It runs against the dev server and the dev database, so tests that need the
  e2e seed data fail here and pass only in the full suite.

## Frontend rules

Each rule exists because it was broken once. The reasons are in
`docs/DEPENDENCIES.md` and the maintainer notes in `README.md`.

- **Run every npm command in the web container.** CI uses npm 10.8.2, and a
  newer host npm writes lockfiles CI rejects.
- **Never run `npm audit fix`.** Adding a dependency needs approval. Do not
  remove the pins that `docs/DEPENDENCIES.md` explains: `vue` and `vue-router`
  in dependencies, `vue-tsc` at `3.3.6`, TypeScript below 7, and the `overrides`
  floors.
- **The typechecker has gone silent before.** After a toolchain bump, plant a
  type error and confirm the typecheck fails. CI runs
  `web/scripts/typecheck-canary.sh` for the same reason.
- **Playwright role-name selectors match case-insensitive substrings.** Use
  `exact: true`. The footer repeats the header's routes, so scope landing
  locators to `getByRole('banner')` or `getByRole('contentinfo')`.
- **Every audit slug needs a label.** When the API adds an `AuditLog::record`
  slug, add it to the `auditActions` map in `web/pages/admin.vue`. An unmapped
  slug renders raw and cannot be filtered.
- **Record photo provenance** in `docs/PHOTOS.md` before renaming a jpg, png or
  webp asset.

## Product decisions not to re-litigate

These shape screens and flows, so the UI must respect them.

- One account, one role (buyer, seller or agent), fixed at signup. There is no
  role switching and no "become a seller" flow.
- No admin access to content. No screen may show the admin a buyer's search
  criteria or conversations. This is a product promise.
- Verification is commercial. An active subscription is what verifies a
  professional.
- A buyer's identity stays hidden until they accept a seller-initiated contact
  request. One contact request exists per (seller, demand) pair. The buyer can
  undo a decline for 14 days, and meanwhile the seller still sees the request
  as pending. After that, or once the property is gone, the decline is final
  (row 30).
- A contact request shows the buyer every fact about the listing that helps
  them decide, so that only seeing the property is left. The platform never
  shares what locates it: the exact address, the exact map location and the
  electronic building ID. The seller gives those in the chat when they arrange
  a visit (the user decided this on 2026-10-14; row 76).
- «Επαγγελματίας Real Estate» alone, as one term that covers agencies and
  builders, is a rule for UI labels: buttons, cards, menus, hints. Content
  pages (`/faq`, `/pricing`'s prose, `/terms`, articles) keep the bracket
  «(μεσιτικά γραφεία και κατασκευαστικές εταιρείες)» (the user decided this
  on 2026-10-14; row 28).

## Web architecture

- **The browser talks only to its own origin.** Nitro proxies `/api/**` to the
  API container, and the proxy target is read at build time.
- **Auth** keeps the Sanctum bearer token in localStorage
  (`composables/useAuth.ts`). `apiFetch` owns the 401 handling.
- **The production CSP** in `nuxt.config.ts` (`connect-src 'self'`,
  `script-src 'self'`) is the control that makes the localStorage token
  acceptable. Do not loosen it. It also blocks any third-party script.
- **i18n uses no library.** Each page holds an inline
  `copy = { el: {...}, en: {...} }` object and reads it through
  `const t = computed(() => copy[locale.value])`. `useLocale()` stores the
  choice in a `locale` cookie, which is written only after the visitor picks a
  language. Every user-facing string ships in both languages.
- **Pure logic** lives in `utils/*.ts` and is unit-tested from `tests/`. Shared
  state lives in `composables/`. `utils/legal.ts` is the only source of company
  details. A source-literal test fails if the landing footer retypes them.
- **Styling.** Every colour comes from `--z-*` tokens in
  `assets/css/tokens.css`. Light is the authoritative theme and dark is derived.
  The light palette appears twice, under `prefers-color-scheme` and under
  `[data-theme='light']`. `tests/tokens.spec.ts` fails when those two blocks
  differ, when a used `--z-*` variable is undefined, or when a status tone falls
  below 4.5:1 contrast. Status pill tones come from `utils/status.ts`, keyed on
  API status codes. The shared primitives are the `Z*` components in
  `components/`.
- **The landing** (`pages/index.vue`) is measured against the designer's mocks,
  not judged by eye (`docs/ONBOARDING.md` §4). It deliberately trades WCAG AA
  contrast for fidelity to the mock. App screens keep the shades that pass.
- **Map tiles** are self-hosted and served by nginx at `/tiles/`, not by Nitro.
  A build hook strips them from the Nitro output.

## SEO

- **Both languages share one URL.** The language comes from the `locale` cookie,
  so a crawler always receives the Greek render. There are no `/el` or `/en`
  routes, no `hreflang` and no canonical links. Changing this is a product
  decision, so ask before starting it.
- **Head tags.** `app.vue` sets the `titleTemplate` and `<html lang>`. Public
  pages set their title with `useHead`. Only `pages/index.vue` sets a
  description and Open Graph tags (`useSeoMeta`).
- **Crawl files** are the hand-maintained `public/robots.txt` and
  `public/sitemap.xml`. Keep both in step with `pages/` when a public page is
  added. The sitemap has no `<lastmod>` on purpose.
- **Do not add a blanket `X-Robots-Tag` or a `noindex`.** The site-wide noindex
  was removed on 2026-07-28 on purpose.
- **Crawlers see only server-rendered content.** Anything inside `<ClientOnly>`
  or rendered after hydration is missing. Check SEO-relevant content with `curl`
  against the page.
- **No analytics or tracking scripts.** The site needs no cookie banner only
  because it sets just two preference cookies (`docs/COOKIES.md`), and the CSP
  blocks such scripts anyway.

## Documents

The global rules place plans, specs, reviews and reports. Only the zitamu
specifics are here.

- `docs/plans/README.md` is the index, kept by the rules in
  `docs-layout.md`. Reviews written by `my:spec-review` or
  `my:soundness-review` get a row too. When a change is part of the history,
  add a line to the index's "How we got here".
- The technical roadmap is `ROADMAP.md` at the project root. It covers
  `web/`, `api/` and `infra/`, and was `docs/frontend-roadmap.md` until
  2026-10-09. The product roadmap, grouped by outcome, is
  `docs/roadmap-notebook-185.md`: what the client agreed. Its open items point
  to their `ROADMAP.md` rows.
- **The page critique action plan is frozen** (the user decided on
  2026-10-09). Its decisions 1 to 85 are a reference, and nothing is added to
  it. A client's new list or a new report becomes `ROADMAP.md` rows directly.
  A decision for the whole product goes into "Product decisions not to
  re-litigate" above.
- **To answer "what next":** read "Order of work" and take the first named row
  that waits for nothing. Check it against active work (`git worktree list`,
  then the files each open branch changes). If a row disagrees with the code
  on `main`, fix the row first. When nothing named is free, list the open rows
  that wait for nothing, split into features and fixes, and ask.
- **Kostas commits to `main` outside this workflow.** After a pull that brings
  his commits, review them and bring `ROADMAP.md`, `CHANGELOG.md` and
  `openapi/openapi.yaml` up to date with them before the next deploy.

## Conventions

- **Greek is canonical.** Greek copy must read as if a native wrote it for a
  Greek product. Use plain punctuation and no em dashes.
- A commit body explains why. Do not add trailers such as `Co-Authored-By`.
  No commit in this repo's history has one.
- Features, refactors, and bug fixes add an entry under `[Unreleased]` in
  `CHANGELOG.md`, headed `### <Type>: <sentence> (<scope>)` like the existing
  entries, for example `(web)`, with prose that says why. Test-only changes,
  chores, doc edits, and config tweaks do not need an entry.
- `.editorconfig`: 2 spaces for js, ts, vue, json and yml.

## Workflow

- **The end-of-branch checks** apply to every code branch, Small ones
  included (the user decided this on 2026-09-29 and 2026-10-09): run the
  full e2e suite first (`web/scripts/e2e-worktree.sh <path>`), then add
  `/security-review` (`docs/ONBOARDING.md` §3.3) to the reviews that
  `my.md` lists. A Small change records the e2e result in its squash
  commit body.
- **The git hooks** `.git/hooks/pre-commit` and `pre-push` are symlinks to
  `~/projects/claude-setup/global/git-hooks/`, so edit them there.
