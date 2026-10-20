---
name: roadmap-management
description: >
  Use when updating ROADMAP.md — adding a feature, promoting between status
  tiers (💭 → 📋 → 🚧 → ✅), splitting or reframing a row, or marking
  something shipped. Trigger on phrases like "update the roadmap", "mark X
  as shipped", "X is done", "move X to in progress", "we just merged Y", or
  whenever a feature transitions lifecycle stages. Owns the roadmap;
  delegates the CHANGELOG half of a 🚧 → ✅ promotion to the
  `changelog-management` skill.
---

# Roadmap Management

A roadmap is **forward-looking** — what's next, in flight, or shipped recently. A CHANGELOG is **backward-looking** — what reached `main` and changed contract or behaviour. They couple at one moment: the integration (squash-merge by default) that promotes a row from 🚧 to ✅. At that moment both files update in the same commit (rule 6).

This skill owns the roadmap. The companion `changelog-management` skill owns the CHANGELOG. When a 🚧 → ✅ promotion happens, this skill drives the commit and delegates the CHANGELOG half to `changelog-management`.

## Adapting to the project

This skill works for any software project. The paths, git workflow, and legend below are **defaults**, not law. Resolve a project's real conventions in this order, and never impose one the project contradicts:

1. **Match what exists.** If `ROADMAP.md` is already present, follow its format, legend, and section scheme.
2. **Read the project's `CLAUDE.md`** (and `CLAUDE.local.md` when present). It documents the roadmap's file name and location, the spec/plan location, git workflow (worktrees or not, default/release branch name, squash vs PR vs direct merge), and dev-report destination. Honour those over every default in this skill, including the commit rules. A project may keep more than one roadmap (for example a technical one and a product one); edit the one the project names for this kind of change, and ask if it names none.
3. **Fall back to the defaults** in this skill (`docs/plans/`, squash-merge to `main`, the legend below, `docs/dev-reports/`).
4. **Ask when ambiguous** — e.g. project type, or where specs live if the project documents nothing. Don't guess a convention into existence.

If no `ROADMAP.md` exists and the user wants one, offer to create it (default legend + a one-line intro); don't silently scaffold.

## Files

- `ROADMAP.md` — project root by default, or the file the project's `CLAUDE.md` names (for example `docs/frontend-roadmap.md`). Everywhere below, `ROADMAP.md` means that file. Living index of features. Owned by this skill.
- spec/plan docs — `docs/plans/` by default; use the project's documented location. Linked from roadmap rows.
- `CHANGELOG.md` — project root. Touched only via `changelog-management` (delegated at rule 6).
- internal-work destination — `docs/dev-reports/` by default; refactors / tests / lint / internal docs. Owned by `changelog-management` rule 2.

## Status legend

Default — match a project's own legend if its `ROADMAP.md` already uses one:

`✅ shipped` · `🚧 in progress` · `📋 planned` · `💭 discussed, not scheduled`

## Decision table

Look up the situation, then jump to the rule. Bold rows are the easy ones to get wrong.

| Situation | Files touched | Rule |
|---|---|---|
| Idea raised but user hasn't agreed yet | None — wait | — |
| User agreed to add an idea | ROADMAP only — new row, status `💭`, no link | 3 |
| Spec landed at `docs/plans/...-spec.md` | ROADMAP only — `💭 → 📋`, link spec | 4 |
| Plan landed + work started | ROADMAP only — `📋 → 🚧`, link plan | 5 |
| **Integration to the main/release branch just landed** (squash, PR, or direct merge) | **ROADMAP + CHANGELOG in the same commit** — `🚧 → ✅` and add changelog entry | 6 |
| Scope or framing changed mid-flight | ROADMAP only — edit row in place, note pivot | 7 |
| One row growing into multiple sub-tasks | ROADMAP only — suffixed numbering (`1`, `1b`, `1c`) | 7 |
| **One row blocks another** | ROADMAP only — express as order, never as a graph | 12 |
| Speculative `💭` / `📋` row now off-table | ROADMAP only — delete row | 7 |
| Already-shipped feature later removed from `main` | The ✅ row **stays**; CHANGELOG gets the `### Removed` entry | 7 + `changelog-management` |
| **Any CHANGELOG-only edit** (deploy change, hotfix, removal, behaviour change with no roadmap row) | CHANGELOG only — use **`changelog-management`** | `changelog-management` |
| **Refactor, test, lint, formatting, internal-only docs** | **Neither** — write to `docs/dev-reports/` | `changelog-management` rule 2 |
| Plan file renamed or moved | Both files where the path is linked | 8 |

If a request fits no row, ask the user — premature roadmap entries and speculative changelog lines are noise.

## Rules

The rules are sequential and keyed by the decision table above.

### 1. Read ROADMAP.md before editing it

Open `ROADMAP.md` and find the area section the row belongs to (the `##` sections the file already has) plus the row's existing numbering context. Don't open `CHANGELOG.md` from this skill — if the edit pairs with a CHANGELOG entry (rule 6), `changelog-management` owns that file.

**Old rows.** While you read, check the open rows (💭, 📋, 🚧). If some of them do not follow rule 11's order — most often, the body does not open with the kind of work, such as `bug in …` or `feature in …` — ask the user once, before the requested edit: "N open rows do not follow the row order, so they are hard to read cold. Rewrite them now, in a separate commit?" Ask at most once per session.

- **On yes:** rewrite every open row to rule 11's order, in one commit of its own (`docs: rewrite ROADMAP rows in the row order`), before the requested edit. Read a row's linked document when the row alone does not say its kind or what the user sees. Never drop a fact that no linked document holds (rule 11). Keep every number. Change a title only when it names an internal step and not what changes for the user, and then update every place in `## Order of work` that quotes it. ✅ rows stay as they are: they are records.
- **On no:** do the requested edit only. The trim trigger in rule 11 still moves each row you touch.

### 2. Identify the lifecycle transition

Look up the user's request in the decision table above and jump to the rule it points to. The table is the source of truth for which files to touch — don't edit anything until the situation matches a row.

### 3. New row — idea → 💭

A new row goes in only **after** the user has agreed to the idea in conversation. Casual mentions and brainstorm tangents do not earn a row.

- Pick the area section that fits (or propose a new `## Section` if none does — confirm with the user).
- Choose the next free number, in the scheme the roadmap already uses: per table, the section's next `#`; with one sequence for the whole file, the next number the roadmap names (raise it by one in the same edit), or else the highest number in the file plus one. Use a suffix form like `1b`, `1c` when the row clearly extends a previous one. Never change or reuse a number, also when a row ships or is deleted.
- In a bullet roadmap, the number goes between the icon and the title: `- 💭 12 **<Short Name>** — …`. `my:status` reads it there.
- Status: `💭`. Spec/plan column: `—`. No link required at this stage.
- Title format: `**<Short Name>** — <body>`. The short name says what changes, in the words a user of the tool would use, not the name of an internal step. The body follows the order in rule 11.
- Place it in the order. If the roadmap has an `## Order of work` section (rule 12), ask the user where the new row goes, or whether it stays unordered, and write the answer in the same edit. Never guess a position: the order is the user's decision.

### 4. Promote 💭 → 📋 — spec landed

Verify a spec file exists at `docs/plans/YYYY-MM-DD-<slug>-spec.md` (or the project's documented spec path). If it doesn't, refuse the promotion — `📋` means "spec is written," not "we plan to write a spec."

- Update the status cell to `📋`.
- Add a markdown link to the spec in the Spec / Plan column: `[spec](docs/plans/YYYY-MM-DD-<slug>-spec.md)`.
- In a project that routes its work, replace `route not set` with the route brainstorming picked (rule 11).
- If the row body needs to grow (e.g., the spec materially reframed the feature), edit the short name and the row body to match — never leave the row contradicting its linked spec.

### 5. Promote 📋 → 🚧 — plan written and work started

Two preconditions, both required:

- A plan file exists (default `docs/plans/YYYY-MM-DD-<slug>.md`; use the project's location).
- Implementation has actually started in an isolated workspace appropriate to the project's git workflow. If the project uses worktrees (see its CLAUDE.md), a worktree exists; if it uses branches, the feature branch exists; if it legitimately works on the main branch, "started" is enough. The point is real work underway — not a worktree per se. Don't withhold 🚧 in a project that doesn't use worktrees.

Then:

- Status → `🚧`.
- Spec / Plan column → `[spec](...), [plan](...)`. Keep both links if both exist.
- Do **not** touch the CHANGELOG yet. In-progress work has not changed any contract.

### 6. Promote 🚧 → ✅ — integrated to the main/release branch (couples with CHANGELOG)

This is the only transition that touches both files. **Both edits go in the same commit.**

Preconditions:

- The integration to the project's main/release branch has already happened — squash-merge, PR merge, or direct, whatever the project uses (verify with `git log` on that branch if uncertain — do not pre-emptively mark ✅ before it lands).
- The plan/spec links in the Spec / Plan column still resolve.

Roadmap edit:

- Status → `✅`.
- In a project that routes its work, a row that still says `route not set` gets its route here: a bounded change has no spec, so no 📋 edit set it (rule 11).
- Update the row body if the implementation diverged from the plan (this is common — the row should describe what shipped, not what was planned). Keep it in rule 11's order (kind, place and route; what the user sees; the fix; verdict; pointer); deep narrative belongs in the CHANGELOG and the linked docs, not the row (rule 11).

CHANGELOG edit (in the **same commit**): hand off to the `changelog-management` skill for scope, structure, dating, and linking. Both edits land in one commit (rule 9 below).

Commit message:

```
docs: mark <feature> shipped on roadmap and changelog
```

If multiple shipments land in one go, list them in the body.

### 7. Reframes, splits, deletions

- **Reframe** (scope or framing changed mid-flight): edit the row in place. Add one short clause to the row body explaining the pivot ("originally framed as X; reframed to Y after Z became clear"). Do **not** re-date the row.
- **Split** (one row grew into multiple sub-tasks): keep the parent's number, give children suffixed numbers (`1`, `1b`, `1c`). Match the existing pattern in the file — do not invent new numbering schemes.
- **Delete a 💭 / 📋 row**: allowed when the row is speculative and the user has agreed it's off the table. Note the deletion briefly in the next CHANGELOG entry's `### Removed` (or `### Docs`) section if a follow-up reader would otherwise wonder where it went.
- **Delete a ✅ row**: don't. Shipped rows are historical record. They stay even if the feature was later removed — note the removal as a fresh CHANGELOG entry under `### Removed`.

### 8. Linking discipline (roadmap side)

- Every roadmap row in `📋`, `🚧`, or `✅` status **must** link to its spec and/or plan. A row without a link is by definition `💭`.
- **Same-repo targets → relative `.md` paths** (`docs/plans/YYYY-MM-DD-<slug>.md`); never hardcode `.html`. A relative `.md` link renders on the Git host's web UI (GitHub/GitLab serve the rendered Markdown), resolves in the repo, and opens in editors. If the project also exports docs to standalone HTML, the `.md`→`.html` extension is rewritten at *build* time — so authoring `.html` in source breaks the hosted and raw-repo views to "fix" a view the build already handles. Keep source links `.md`.
- **Out-of-repo / cross-repo targets → absolute web URLs**, not relative `../other-repo/...` paths. A path that climbs out of the repo only resolves on a local checkout that happens to have the sibling repo beside it — it is dead on the Git host's web UI and in any exported HTML. Link the hosted URL instead (e.g. `https://<git-host>/<group>/<repo>/-/blob/<default-branch>/<path>`); verify the target's default branch rather than assuming `main`/`master`.
- If a plan is **moved, archived (e.g. into `docs/plans/archive/`), or renamed** (per the `clean-plans` skill), repoint *every* link to it — a move silently breaks the link in all views, the Git host included. Run `git grep` on the old path across `ROADMAP.md`, `CHANGELOG.md`, and `docs/`. CHANGELOG-side updates are owned by `changelog-management`.

CHANGELOG-side linking lives in `changelog-management`. The two files are tied together by their shared link down to `docs/plans/`, not to each other directly.

### 9. Commit discipline (roadmap side)

- Roadmap-only edits (rules 3–5, 7): one commit. Message: `docs: <verb> ROADMAP for <feature>`.
- Roadmap + CHANGELOG paired edits (rule 6): **one commit**, never two. Message: `docs: mark <feature> shipped on roadmap and changelog`. Splitting them breaks atomicity — a reader bisecting `main` should never see a ✅ row whose CHANGELOG entry hasn't landed yet, or vice versa.
- CHANGELOG-only edits: see `changelog-management` rule 9.

Use Conventional Commits in all cases (project rule).

### 10. Cross-check the row you just touched

Edit-scoped only — no full-file audits:

- The status reflects reality (the integration has actually landed for ✅; plan file actually exists for 🚧; spec file actually exists for 📋).
- The Spec / Plan column links resolve.
- The row body is still index-level and in rule 11's order (kind, place and route; what the user sees; the fix; verdict; pointer) — you didn't append numbers, SHAs, or play-by-play that a linked doc already owns (rule 11).
- The markdown table is still well-formed (no broken pipes, no missing cells).

Skip broad audits (stale-💭 sweeps, orphan-row scans, full-file link greps). Run those only when the user explicitly asks for a roadmap audit.

### 11. Row-body content discipline — index, not archive

A roadmap row is an **index entry**, not the record of the work. The linked spec / plan / experiment-log / briefing is the source of truth; the row points at it. The same fact must not be maintained in both places — when the linked doc is later corrected, a duplicated row silently goes stale and ends up contradicting its own link.

Keep in the row body, in this order, so that a reader who opens the roadmap cold knows what the row is without opening a link. Target: one sentence each for the first three parts, then the verdict and the pointer as short fragments (≤ ~5 lines in all):

- **Kind, place and route** — the kind of work (`bug`, `feature`, `rule` for a change to instruction text, or another kind the roadmap already uses), where it happens (the skill, file or area), and the route when it is already known. In a project that routes its work (spike, bounded, architectural in the `my` method): a row of kind `bug` names no route, even when its fix may touch the risk line; a row that hits the risk line (a change to stored data or its shape, permissions, a message or public contract, or something hard to reverse) names `architectural with plan`; every other row names `route not set` until brainstorming picks its route (rules 4 and 6). A bug that brainstorming routed follows rules 4 and 6 for the route it got. A row routed to a spike gets `spike` in the edit that links the spike file, since no spec or merge follows. In a project that does not route its work, leave the route out. Examples: `bug in my:handoff.` and `feature in my:status, route not set.`
- **What the user sees** — for a bug, what goes wrong for the person using the tool; for a feature, what they can do once it ships. Start from that effect, not from its cause in the code. Replace or define every term a reader may not know.
- **The fix or the goal** — one sentence. When no linked document holds the facts a fixer needs (the cause, the chosen approach), this sentence keeps them, because the row is their only record.
- **Current bottom line** — one line: shipped / NO-GO / blocked-on-X. Include a single figure *only when that figure is itself the verdict* (e.g. a NO-GO whose crux is "background-FP 51 vs 12") — one decisive number, not a metrics dump.
- **A pointer** — "detail in the linked X" when the row links somewhere.

Push to the linked doc, never copied into the row:

- Metrics and numbers (mAP, AUC, counts, thresholds, dates beyond the row's own status), commit SHAs, per-phase / per-experiment play-by-play, mechanism explanations, full verdict reasoning, supersession chains.

The one exception: a cause or a chosen approach that no linked document holds stays in the fix sentence, as above.

**Trim trigger** (applies whenever you write or edit a body — rules 3–7): if the body would run past the target above (~5 lines), or you're about to paste a figure or SHA that already lives in a linked doc, **compress instead of appending**. When you touch a row that has already accumulated history, trim it to the order above (kind, effect, fix, verdict, pointer) in the *same* edit — never add one more clause to an already-oversized cell. (Markdown table cells can't contain paragraph breaks, so an over-long cell can't even be reformatted into readable prose — the only available fix is less content.)

Why this is a rule and not a style preference: the row and the linked doc are two copies of one fact, and only the linked doc is maintained as ground truth. Most `ROADMAP.md` files state this contract in their own intro ("Keep this short — details live in the linked docs"). Enforce it on every edit, not just new rows.

### 12. Dependencies are expressed as order, not as a graph

A roadmap says what and roughly when. Blocking relations are execution detail — a tracker's job (GitLab issue relations, Jira "is blocked by"), where they are structural rather than narrated. A roadmap absorbs a dependency by **making it an order**: if A blocks B, B sits in a later tier. Do not build a `Depends on` column. A roadmap that needs a real graph is telling you the work belongs in issues.

What to write instead, in escalating order of need:

- **Nothing.** If the priority/status tiers already put the blocker first, the dependency is expressed. Stop here — a prose edge that only restates the tier is pure decay surface.
- **One clause, one direction.** Where an edge genuinely changes the order, name the blocker *from the blocked row*: `Blocked by row 4b.` For a blocker outside the roadmap, such as a client's answer or a missing file, write `Waits for <what>.` in the same place. Never mix directions — "raises the ceiling on row 5" in one row and "the keying half is row 4b" in another forces the reader to parse each sentence for which way the arrow runs.
- **An `## Order of work` section**, once more than a couple of edges exist. Bullets of the form `**4b, then 7, then 4c.** <the constraint that forces it>` — state the *reason* (shared migration, structural prerequisite), not just the sequence. Close with the contract that anything unnamed is unordered, so the section never has to list rows it has nothing to say about.

Two failure modes to watch:

- **Split-rot.** When rule 7 splits a row, inherited edge clauses keep pointing at numbers that no longer mean what they meant. A split keeps the parent's number, so an edge that now means a child still names the parent. Re-read every prose edge that names the parent, and point it at the parent or the child it now means.
- **Two live orderings.** When a durable doc elsewhere already sequences the work — an action plan's phases, a code review's "suggested order of work", a spec's phasing — do not maintain a second copy. Keep one live, and leave a dated supersession note on the other pointing at it (rule 8's linking discipline applies).

## Common mistakes

- Promoting 📋 → 🚧 just because a workspace was created — the plan file must exist first.
- Promoting 🚧 → ✅ before the integration has actually landed on the main/release branch (`git log` not yet showing it).
- Editing only the roadmap on a shipment, forgetting the CHANGELOG entry — or vice versa. The same-commit rule (9) is the safety net.
- Putting a refactor or a test addition in CHANGELOG. It belongs in `docs/dev-reports/` (see `changelog-management` rule 2).
- Deleting a ✅ row when the feature was later removed. Add a `### Removed` CHANGELOG entry instead; the historical row stays.
- Adding a 💭 row for a casual brainstorm tangent. Wait for explicit user agreement first.
- Narrating a dependency the priority tier already implies, adding a `Depends on` column, or leaving an edge pointing at a parent row whose work a split moved to a child (rule 12).
- Pasting metrics, commit SHAs, or per-phase history into a row body that the linked doc already records, or appending one more clause to an already-bloated cell. The row points at detail; it doesn't duplicate it (rule 11).
- Hardcoding `.html` in a link, or pointing at a cross-repo file with a relative `../other-repo/...` path. The first breaks the Git host's rendered view; the second is dead anywhere but a local checkout. Same-repo → relative `.md`; cross-repo → absolute URL (rule 8).
