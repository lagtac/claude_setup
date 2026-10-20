# Review: docs/plans/2026-10-20-method-bundles-spec.md

**Status:** review of docs/plans/2026-10-20-method-bundles-spec.md, 2026-10-20. Problematic, on an untested `superpowers@synced` dependency. Answered in the spec on 2026-10-21: a test showed the dependency is met (spec §Context); the editorial findings are fixed; the seven design findings are decisions D2, D13 and D14 to D18; the three open items were tested (spec §Context).

## Spec Summary

The spec turns each method (`my`, `tutor`, `sp`) into a plugin in this marketplace. A forced output style holds the method's rules, and `plugin.json` `dependencies` lists its plugins. A folder's `enabledPlugins` keys name its method. The import line, `global/methods/`, the global output styles and the path-scoped `docs-layout.md` and `plan-format.md` go away. The core `global/CLAUDE.md` is split, and its development rules move to a path-scoped `global/rules/engineering.md`. Batch 1 also rewrites the start check (`method-guard.py`) and `/kit:setup`. Batch 2 adds `claude-method <m>` for one session, `/kit:method <m>` for a switch during a session, and the new `my:handoff` launch lines.

## System Model

The caller sweeps in this review were text-only (`grep`). This reviewer had no symbol-reference tool.

| Component | Owns | Depends on | New / existing (verified at) |
|---|---|---|---|
| `my` method plugin | The `my` rules (forced style folding `my.md`, `docs-layout.md`, `plan-format.md`); its plugin set (`dependencies: ["superpowers@synced"]`) | `superpowers@synced`; Claude Code forced-style and dependency loading | Existing `plugins/my/.claude-plugin/plugin.json:1`; style and field new |
| `tutor` method plugin | The tutor rules (style); the `tutor` skill moved from `kit` | None declared (but see the `modern-web-guidance` finding) | New; the skill is existing at `plugins/kit/skills/tutor/SKILL.md:1` |
| `sp` method plugin | A short style; `dependencies: ["superpowers@synced"]` | `superpowers@synced` | New |
| `marketplace.json` | Which plugins are methods (`"category": "method"`) | none | Existing `.claude-plugin/marketplace.json:1` |
| Core `global/CLAUDE.md` | Rules for every session: Precedence, Important, Communication (with `plain`), Critical Thinking, HTTP | none | Existing `global/CLAUDE.md:1` |
| `global/rules/engineering.md` | Code, Engineering standards, Mandatory Exploration, Reference Sweep, Simplicity Rules | Path-scoped rule loading (also on file creation: untested) | New |
| `claude-method` script | The off-set logic (spec claims it is the one owner); the `--settings` JSON | `known_marketplaces.json`, `marketplace.json`, each method's `plugin.json` | New (`plugins/kit/bin/` exists, `plugins/kit/bin/` on session `PATH`) |
| `/kit:method` skill | Nothing; it turns keys into `claude plugin enable/disable --scope local` calls | `claude-method --json`; `claude plugin` CLI; the user's `/reload-plugins` | New |
| Start check `method-guard.py` | The three warnings | `marketplace.json` (method list), three settings files, `CLAUDE.md`/`CLAUDE.local.md` | Existing `plugins/kit/hooks/method-guard.py:1` |
| `/kit:setup` | Writes a folder's default method; removes the old import, `**Method:**` line, `outputStyle` key | Method list and dependencies (read by the skill itself); the `my` style for the facts | Existing `plugins/kit/skills/setup/SKILL.md:14` |
| `my:handoff` launch lines | How stages start | `claude` (batch 1), `claude-method` (batch 2) | Existing `plugins/my/skills/handoff/SKILL.md:319,330,345,354` |
| Settings files (user, project, local, `--settings`) | `enabledPlugins` per scope | none | Existing `~/.claude/settings.json`, `.claude/settings.json` |
| Design-router gate (not in the spec, affected) | Refuses skills of installed plugins absent from its list | `plugins/kit/skills/design-router/plugins.json` | Existing `plugins/kit/hooks/design-router-gate.py:136-140` |
| Tutor SessionStart hook | Tells Claude to invoke `kit:tutor` in a learning workspace | `docs/learning/curriculum.md` | Existing `plugins/kit/hooks/hooks.json:5-13`; deleted |

| From → To | What passes | Owner of what passes |
|---|---|---|
| Method `plugin.json` → `claude-method` | The `dependencies` list, read at run time | Method plugin |
| `marketplace.json` → `claude-method`, start check, `/kit:setup` | The method list (`category`) | `marketplace.json` |
| `claude-method` → `claude` | `exec` with one `--settings` JSON (method set on, off set off) | `claude-method` |
| `claude-method --json` → `/kit:method` | The settings keys | `claude-method` |
| `/kit:method` → `.claude/settings.local.json` | `claude plugin enable/disable --scope local` per key | `/kit:method` (writes); Claude Code (file) |
| User → Claude Code | `/reload-plugins` | User |
| `/kit:setup` → project `.claude/settings.json`, `CLAUDE.md`, local settings | Method keys on; other methods' keys removed; import and `outputStyle` removed | `/kit:setup`. It computes the off set itself, so this is a second owner of the off-set logic |
| Claude Code → method plugin | The forced style into the system prompt; the dependency check at load | Claude Code |
| Settings files → start check → session | `enabledPlugins`; warning text (`systemMessage`, `additionalContext`) | Settings files / start check |
| `my:handoff` → new session | The launch command (`claude` in batch 1, `claude-method my` in batch 2) | `my:handoff` |
| `engineering.md` → session | Rule text, loaded when a matching path is read | Claude Code path-scoped rules |
| Tutor style → `tutor:tutor` skill → design-router gate | A Skill call that the PreToolUse gate judges | Not stated in the spec |

## Grounding

- `spec §Dependencies` ("Row 70 merges first") ↔ `ROADMAP.md:224` (✅ 70, "Shipped in `5dfd634`"). Row 70 has already merged. Its core edit, `## Design work` at `global/CLAUDE.md:21-23`, is not in the spec's split (see Issues).
- `spec §The core and engineering.md` lists everything the core keeps and everything that moves. `global/CLAUDE.md:21-23` (`## Design work`) and `global/CLAUDE.md:73-78` (the HTML comment about language rules) appear in neither list.
- `spec §Files` / `§Batches` ("every reference in Files") ↔ references to moved or deleted files that the Files table does not list:
  - `plugins/my/skills/clean-plans/SKILL.md:22` (`~/.claude/rules/docs-layout.md`);
  - `plugins/my/README.md:72,134,153` (`docs-layout.md`);
  - `README.md:146` (`kit:tutor`), `README.md:186` (`global/rules/docs-layout.md`), `README.md:251-253` (the tutor hook; the spec cites 255–257, which is the method-guard text);
  - `projects/real-estate-webapp/claude-local.md:238` (`docs-layout.md`);
  - `plugins/kit/skills/tutor/method.md:4` (`kit:tutor`);
  - `plugins/kit/skills/tutor/SKILL.md:110-115,136,158-162` (the `outputStyle: "tutor"` setup and the start check);
  - `global/git-hooks/pre-commit:2` and `global/git-hooks/pre-push:2` (comments pointing at `docs-layout.md`);
  - `ROADMAP.md` rows that name `global/methods/my.md`, `plan-format.md` or `docs-layout.md` as the file they will edit (for example `ROADMAP.md:52-55`, `:75`, `:298-304`, `:474-478`).
- `spec §Files` omits `plugins/kit/skills/design-router/plugins.json`, which must list `tutor` and `sp` (see Issues).
- `spec §Method plugins`, rule 2 ("line 219 and line 279 (`plan-format.md`)") ↔ `global/methods/my.md:219`. Line 219 points at `docs-layout.md` ("step 2 in `docs-layout.md`"), not at `plan-format.md`.
- `spec §Method plugins` ("About 44,000 characters") ↔ `wc -c`: 29,666 + 11,049 + 1,686 = 42,401 today. This is close enough as an estimate. It is not a finding.
- These references were checked and hold:
  - `my.md` lines 3, 8, 122, 215, 217, 279;
  - `docs-layout.md:139`, and the "Applies only" lines at `docs-layout.md:9` and `plan-format.md:8`;
  - `tutor/SKILL.md:21`, `status/SKILL.md:60`, `handoff/README.md:267`;
  - the handoff launch lines 319, 330, 345, 354;
  - `CLAUDE.md:3,23,29`, and `claude-local.md:22,28` (`CLAUDE.local.md` is a symlink to it);
  - the nine `my` repos and `mv3-tab-notes` with `outputStyle: "tutor"`;
  - the `claude-setup` entry and its `installLocation` in `known_marketplaces.json`;
  - `~/bin/git-fold-fixups.py`, which is a symlink;
  - the session `PATH`, which holds `plugins/my/bin` and `plugins/kit/bin` from the repo (this supports in-place loading).

## Issues Surfaced

| Severity / Confidence | Class | Issue | Evidence | Fix |
|---|---|---|---|---|
| Critical / Medium | design | `my` and `sp` depend on `superpowers@synced`. `synced` is not a marketplace: it is missing from `known_marketplaces.json`, and the synced plugins live under `~/.claude/plugins/synced/`. The dependencies doc (fetched 2026-10-20, section "Dependencies when your plugin loads from claude.ai") says a `@synced` plugin has "no marketplace", and that "a claude.ai plugin meets the entry only when your plugin also loads from claude.ai". `my@claude-setup` loads from a directory marketplace. Spike 1 tested only a dependency inside the same marketplace. The brief's open item on cross-marketplace dependencies (`allowCrossMarketplaceDependenciesOn`) is not answered. If the dependency is unmet, `my` is disabled with `dependency-unsatisfied` in all nine repos at the merge, because the plugins load in place. Unlike the `engineering.md` check, this one has no stop-and-ask. | `~/.claude/plugins/known_marketplaces.json` (no `synced` entry); `.claude/settings.json:3` (`superpowers@synced`); `spec §Method plugins` ↔ brief `docs/plans/2026-10-20-method-bundles-architecture.md:342` | Decision for the author. Make a spike on `my → superpowers@synced` the first task, with a stop-and-ask, as for `engineering.md`. Fallbacks: install `superpowers` from its own marketplace and add that marketplace to `allowCrossMarketplaceDependenciesOn`; or drop the `dependencies` field and keep the plugin set as keys `/kit:setup` writes. |
| Warning / High | design | The core split drops `## Design work`, the rule that sends all design work to `kit:design-router`. Row 70 added it, and `test_core_sends_design_work_to_router` asserts it. Neither the "core keeps" list nor the `engineering.md` list places it. | `global/CLAUDE.md:21-23`; `plugins/kit/tests/test_neutral_core.py:67-70`; `spec §The core and engineering.md` | Decide where it goes: the core (every kind of work) or `engineering.md` (path-scoped). Also update D2 and the test row. |
| Warning / High | design | Rollout step 2 turns off plugins that current work depends on, and no method lists them as dependencies. (1) `mv3-tab-notes` needs `modern-web-guidance:*`. Today that plugin is unnamed, so it counts as on. After step 2 it is off, and `tutor` has no dependencies. (2) `design@synced`, `design-skills@synced` and `frontend-design` go off at user scope. Those are the plugins `kit:design-router` routes to, so the router stops with "plugin is off" in every repo. Neither D5 nor the Risk section covers this. | `~/projects/mv3-tab-notes/docs/learning/curriculum.md:40-41`; `~/.claude/settings.json` `enabledPlugins` (`frontend-design: true`; `design`, `design-skills`, `modern-web-guidance` unnamed); `plugins/kit/skills/design-router/plugins.json:2-4`; `plugins/kit/skills/design-router/SKILL.md:24-25`; `spec §Decisions D5` ↔ `§Batches and rollout` step 2 | Decision for the author: add these to the methods' `dependencies`, have each project turn them on, or keep the design plugins on at user scope. Then add a Risk line. |
| Warning / High | design | The moved `tutor` skill still writes `"outputStyle": "tutor"` (setup step 6). It hands over with plain `claude` (step 10), and its session start checks for the style through that key (Start step 2). Under the spec, `/kit:setup` step 3 removes that key, and the global `tutor` style is deleted. The spec edits only line 21. The spec also drops `/kit:setup`'s `[<project path>]` argument without saying so. The tutor skill's setup cases create workspaces in other folders, so they need that argument, or need to write the `tutor@claude-setup` key themselves. | `plugins/kit/skills/tutor/SKILL.md:110-115,136,158-162`; `plugins/kit/skills/tutor/method.md:4`; `plugins/kit/skills/setup/SKILL.md:5-7`; `spec §Method plugins` rule 9 ↔ `§/kit:setup` step 3 ↔ `§Trade-offs` | Decide the tutor setup contract: the skill writes the project key, or the skill calls `/kit:setup tutor <path>`. Then list every edited line. |
| Warning / High | design | The spec says the off-set logic "has one owner" (`claude-method --json`). But `/kit:setup` step 2 computes the same set, "every other method and its dependencies, except the chosen method's own", in batch 1, before `claude-method` exists. The start check also reads the method list from `marketplace.json` on its own. That makes three readers and two owners of the off-set rule. | `spec §Choosing and switching` ("so the off-set logic has one owner") ↔ `§/kit:setup` step 2 ↔ `§The start check` | Decision for the author: move the method-list and off-set code into batch 1 as one kit script that the start check and `/kit:setup` call, or accept two owners and say so. |
| Warning / Medium | design | A `/kit:method` switch leaves keys in `.claude/settings.local.json` that outrank the folder default for good. No command clears them. `/kit:setup` only removes `outputStyle` from the local file. So `/kit:setup tutor`, run after an earlier `/kit:method my`, leaves `my` on locally, and two methods load. | `spec §Choosing and switching` ("until the user turns it on again"); `spec §/kit:setup` steps 1–3 | Decide whether `/kit:setup` also clears method keys from the local file, and whether `/kit:method` has a "back to the folder default" form. |
| Warning / High | design | The design-router gate refuses every skill of an installed plugin that is missing from `plugins.json`. Today `kit:tutor` passes because of its `kit` prefix. After the move it is `tutor:tutor`. If rollout step 1's fallback installs `tutor`, the gate refuses the call that the tutor style makes before its first reply. `plugins.json` and the Files table name neither `tutor` nor `sp`. | `plugins/kit/hooks/design-router-gate.py:136-140`; `plugins/kit/skills/design-router/plugins.json`; `spec §Batches and rollout` step 1 | Add `"tutor": "not-design"` and `"sp": "not-design"` to `plugins.json` in batch 1, and add a row to Files. |
| Warning / Medium | design | Row 71's drafted spec rewrites the same core Precedence paragraph. It also edits `global/methods/my.md` and `global/methods/tutor.md`, which this spec deletes. Its wording keys on a "method file headed `# Method: <name>`", which no longer exists under candidate A. This spec lists row 71 in neither Dependencies nor How to read. | `ROADMAP.md:271-278`; `docs/plans/2026-10-18-project-precedence-spec.md:105-139`; `spec §The core and engineering.md` (Precedence) | Decision for the author: order 71 against 68, and say which Precedence text wins. |
| Warning / High | editorial | The Files table misses references to moved or deleted files. The full list is under Grounding: `clean-plans/SKILL.md:22`, `plugins/my/README.md:72,134,153`, `README.md:146,186,251-253`, `claude-local.md:238`, `tutor/method.md:4`, the git-hook comments, and the ROADMAP rows that name the deleted files. Batch 1 claims "every reference in Files". | See `## Grounding` | Add the rows, or state that the plan's reference sweep owns the full list. Fix the README line ranges. |
| Suggestion / High | editorial | Dependencies still says "Row 70 merges first", but row 70 has shipped. | `ROADMAP.md:224`; `spec §Dependencies` | Say that row 70 is merged, and that batch 1 starts from its text. |
| Suggestion / High | editorial | The Risk section says `mv3-tab-notes` loses only its start hook at the merge. It also loses its `tutor` style, because `global/output-styles/` is deleted and the `tutor` plugin is off there until rollout step 5. | `~/projects/mv3-tab-notes/.claude/settings.local.json` (`outputStyle: "tutor"`); `spec §Risk` ↔ `§Deleted` | Name both losses in Risk. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Fit with what exists | It uses only Claude Code's own channels: forced style, `enabledPlugins` at each scope, `--settings`, `claude plugin --scope local`. There is no new process and no build step. In-place loading is consistent with the session `PATH` (`plugins/*/bin` from the repo). | Strong |
| Contracts and flow | Rules and plugins load and unload together, because the style belongs to its plugin (brief spike 2). This removes today's import-versus-keys split, which needed `method-guard.py`. | Strong |
| Failures and interactions | The spec handles these explicitly: two forced styles (start check 1 and the `--plugin-dir` rule); `--settings` refused with exit 2; the start check keeps its read-only, exit-0 contract; the `engineering.md` load-on-create check is a first task with a stop-and-ask. | Moderate |
| Grounding | The `my.md` and `docs-layout.md` line pointers, the handoff launch lines, the repo list and the settings state were all checked, and they hold. | Moderate |
| Spec rules | How to read comes first, with paths. Risk, Dependencies and Trade-offs are present. There is no UI, so there is no Visual Language section. | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Failures and interactions | The cross-marketplace `@synced` dependency is untested, and the docs suggest it is unmet. Because the plugins load in place, a failure lands on all `my` repos at the merge. | High |
| Boundaries | The off-set logic and the method list have up to three implementations: `claude-method`, `/kit:setup` and the start check. | Medium |
| Fit with what exists | The spec does not account for row 70's core section, the design-router gate, or the plugins that the router and the tutor curriculum use. | Medium |
| Contracts and flow | The tutor skill's own setup contract (`outputStyle`, hand-over with `claude`) contradicts the new flow. | Medium |
| Failures and interactions | Batch 1 claims to work alone. But `my:handoff` still copies `--plugin-dir` flags onto plain `claude`, so a handoff from a `--plugin-dir` session in a `my` folder loads two `my` styles until batch 2. No such session runs today. | Low |

## Not Applicable

- Criterion 3, off-path UI events: the spec adds no UI.
- Criterion 6, Visual Language: the spec adds no UI, so the section is correctly absent.

## Needs Investigation

- **`claude plugin enable/disable --scope local` on a `@synced` key, or on a plugin that is not installed.** `/kit:method` runs one command per key, including `superpowers@synced`, and the off set includes `tutor@claude-setup` and `sp@claude-setup`, which may not be installed. If either command errors, `/kit:method` stops partway on every switch. Resolve this with one run of each command in a scratch folder.
- **`outputStyle: "plain"` between the merge and rollout step 2.** The style file disappears and the `~/.claude/output-styles` symlink dangles. It is unclear whether Claude Code falls back without notice or errors at start in every folder. Resolve this with one headless run after removing the file in a scratch `HOME`.
- **The context numbers.** "A bare session loads 18 plugins, 87 skills and 15 MCP servers" (spec §Context) differs from the brief's "17 plugins and 142 skills" (brief force 2). It was not checked which session each figure came from.

## Reasoning

The System Model is coherent. Each method plugin owns its rules and its plugin set, and settings files are the only state. That is the main argument for the design. But the one link everything rests on, a `my@claude-setup` plugin depending on `superpowers@synced`, is untested across marketplaces, and the fetched docs say a claude.ai plugin meets a dependency only for a plugin that also loads from claude.ai. Because the plugins load in place, a failure reaches every `my` repo at the merge. The other findings are gaps that fixes can close: row 70's core section, the router and tutor plugins switched off, the tutor skill's setup, a second owner of the off-set logic, and missing Files rows. They do not challenge the approach.

## Verdict

**Assessment:** Problematic
**Confidence:** Medium. The Critical finding rests on the docs' wording and on the missing marketplace entry, not on a run. One headless run settles it either way.
**Recommendation:** Before the plan, run one spike: a scratch folder with `my@claude-setup` and `superpowers@synced` on, `my`'s `plugin.json` given `dependencies: ["superpowers@synced"]`, and a check of the init event's plugin list. If `my` is disabled, ask the user how the method should carry `superpowers`. Then decide on the `Design work` placement, the design and `modern-web-guidance` plugins under D5, the tutor setup contract, the off-set owner and row 71, and fix the editorial rows.
