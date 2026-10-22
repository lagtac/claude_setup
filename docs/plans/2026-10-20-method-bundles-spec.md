# Spec: methods as plugins

**Status:** current, 2026-10-22. Batch 1 merged in `1a6d653`. Row 68; reviewed in `docs/plans/2026-10-20-method-bundles-spec-review.md`, approved by the user.

**Route:** architectural with plan. The change moves the rules that nine projects follow and
retires the import line they use to load them. That is a public contract, and it is hard to
reverse. `my:architect` ran first: its brief is listed first below.

## How to read this spec

1. `docs/plans/2026-10-20-method-bundles-architecture.md`. The architecture brief: the forces,
   candidates A to D, the Decision (candidate A), tests 17 to 27 and spikes 1 to 3. This spec
   starts from its Decision and answers its "Open for brainstorming" list.
2. `docs/plans/2026-10-18-launch-method-switch-architecture.md`. The superseded brief. Its forces
   and flag tests 1 to 16 still hold as evidence.
3. `ROADMAP.md`, row 68 "Methods as plugins" and the "Order of work" section, step 3.
4. `global/methods/my.md`, `global/methods/tutor.md`, `global/rules/docs-layout.md`,
   `global/rules/plan-format.md`, `global/output-styles/plain.md`,
   `global/output-styles/tutor.md`. The rule files this spec moves.
5. `global/CLAUDE.md`. The core, which this spec splits.
6. `plugins/kit/hooks/method-guard.py`, `plugins/kit/hooks/hooks.json`,
   `plugins/kit/skills/setup/SKILL.md`, `plugins/kit/skills/tutor/`. The kit parts this spec
   rewrites or moves.
7. `plugins/my/skills/handoff/SKILL.md`, lines 300 to 360 (the launch lines).
8. `docs/plans/2026-10-20-design-router-spec.md` (row 70, merged). It edited `my.md` and `docs-layout.md`
   before this row moves them.
9. `docs/plans/2026-10-20-method-bundles-spec-review.md`. The spec review, and the findings the
   Decisions table answers.
10. Claude Code docs, fetched 2026-10-20: `code.claude.com/docs/en/output-styles`,
   `/en/plugins-reference`, `/en/plugins/dependencies`, `/en/plugins/loading` (section "In-place
   and copied plugins"), `/en/plugin-marketplaces`.

## Context

The user stated the intent on 2026-10-20. Work with Claude is not only coding: it is also email,
tutoring, research and market analysis. Each kind of work may use one of several workflows. So:

- a new session starts bare and assumes no kind of work;
- the user scope stays light and does not load every plugin;
- a fast audit finds skills that overlap when loaded together;
- a folder's own settings can name its method; without one, the user loads and unloads plugins by
  name, with autocomplete;
- a method is a bundle of plugins and skills, as strict or as loose as its author wants.

Today a project picks a method in two places. Its `CLAUDE.md` imports a rules file, such as
`@~/.claude/methods/my.md`, and its `.claude/settings.json` turns the method's plugins on. A
session start hook, `method-guard.py`, warns when the two disagree. A bare session loads 18
plugins, 87 skills and 15 MCP servers, because the user scope turns most plugins on.

The brief chose candidate A: **a method is a plugin.** Its rules are an output style that the
plugin forces on, and its plugin set is the plugin's `dependencies`.

Three facts from the harness shape the design. All are documented and were tested on Claude Code
2.1.304.

- **A forced style.** A plugin's `output-styles/<name>.md` with `force-for-plugin: true` applies
  whenever the plugin is on, and overrides the `outputStyle` setting. With two forced styles, the
  first plugin loaded wins, with no warning (spike 2).
- **Dependencies do not turn on by themselves.** A plugin whose dependency is off is disabled with
  `dependency-unsatisfied`. Turning a plugin on does not turn its dependencies on (spike 1).
- **This marketplace loads in place.** `claude-setup` is a marketplace added from a local folder,
  and its plugins use relative paths. Claude Code loads such plugins from the folder itself, not
  from the cache. An edit reaches the next session that starts, or the next `/reload-plugins`. The
  docs say so ("In-place and copied plugins"), and this session's `PATH` holds
  `/home/dchris/projects/claude-setup/plugins/my/bin`. Spike 3 moved a cache entry that sessions
  do not read.

Three more facts were tested on 2026-10-20, after the spec review asked about them:

- **A dependency on `superpowers@synced` is met for a plugin from a local-folder marketplace.** A
  throwaway marketplace with one plugin depending on `superpowers@synced` loaded it, and its
  forced style applied. With `superpowers@synced` off, Claude Code disabled the plugin with
  `dependency-unsatisfied`. The docs' sentence "A claude.ai plugin meets the entry only when your
  plugin also loads from claude.ai" does not hold for this case on 2.1.304.
- **`claude plugin enable` and `claude plugin disable` with `--scope local`** work on a
  `@synced` key. They also accept a name that does not exist, with no check, so a caller must pass
  only names it read from a manifest.
- **An `outputStyle` that names a missing style** does not stop a session: it starts with no
  error.

## Goal

- Each method is a plugin in this marketplace with `"category": "method"`: `my`, `tutor` and `sp`.
  `none` means no method.
- A folder's method is a set of `enabledPlugins` keys in its `.claude/settings.json`. No import
  line.
- `claude-method <m>` starts one session with another method. `/kit:method <m>` switches the
  folder during a session.
- The user scope keeps only `kit`, the three language servers and the Claude Code tooling.
- The core `global/CLAUDE.md` holds only rules for every kind of work. The development rules load
  only when code is read.

## Out of scope

- **The overlap audit** (the user's point c). It gets its own roadmap row, placed with the user's
  agreement. This spec adds only one overlap check: two methods on at once.
- **Row 69**, which moves the shared skills from `my` to `kit`.
- **New methods** beyond `my`, `tutor` and `sp`.
- **The claude.ai connectors**, which are not plugins, so `enabledPlugins` cannot turn them off.
- **The `pre-commit` and `pre-push` hooks** in this repo. The user chose on 2026-10-20 not to
  turn them on here.

## Decisions

D1 to D13 were approved by the user during brainstorming on 2026-10-20. D14 to D18, and the changes to D2 and D13, answer the spec review's design findings (user, 2026-10-21).

| # | Decision | Why |
|---|---|---|
| D1 | `docs-layout.md` and `plan-format.md` fold into the `my` style. | A plugin cannot ship rule files. About 3,300 more tokens in each `my` session (brief, estimate 1). |
| D2 | The development rules move to a path-scoped `global/rules/engineering.md`. The core keeps precedence, commits, dependencies, communication, critical thinking, design work and HTTP. | A writing or research session starts without coding rules (point a). Design work is not only about code (user, 2026-10-21). |
| D3 | A switch turns off every other method and its dependencies, except the chosen method's own. | Otherwise `superpowers` stays on in a `tutor` session. |
| D4 | The overlap audit is its own row. The start check warns only about two methods on at once. | Keeps this row to the switch. |
| D5 | The bare user scope keeps `kit`, `vue-lsp`, `php-lsp`, `pyright-lsp`, `claude-md-management`, `claude-code-setup` and `hookify`. | The Claude Code tooling is used in every kind of work. |
| D6 | The command is named `claude-method`. | Not `claude`, so the real binary is never shadowed. |
| D7 | Repos move when opened: the start check flags an old import line and suggests `/kit:setup`. | No sweep over dormant repos. |
| D8 | The superpowers-only method is named `sp`. | A plugin named `superpowers` would share the `superpowers:` skill prefix. |
| D9 | `none` names "no method". | It replaces `plain`, which stops being a style. |
| D10 | `/kit:setup` removes other methods' keys instead of writing `false`. | More than 8 methods would add a line per method to every repo. The user scope keeps them off. |
| D11 | No `post-commit` hook. | It was chosen to refresh a plugin cache. This marketplace loads in place, so edits reach new sessions without it (user, 2026-10-20). |
| D12 | Supervised, no Delegation section. | The rollout has manual steps, and the change deletes rule files every session reads. |
| D13 | Two batches, two branches, one spec and one plan. `claude-method` is in batch 1. | About 10 new files: too much for one review. `/kit:setup` and the start check call `claude-method`, so the method list and the off set have one owner from the start (user, 2026-10-21). |
| D14 | The bare user scope is strict. The design plugins (`design@synced`, `design-skills@synced`, `frontend-design`) and `modern-web-guidance` go off with the rest. The user turns one on by name when needed. | Point b: the user scope stays light (user, 2026-10-21). `kit:design-router` already says which plugin is off and stops. |
| D15 | The tutor skill sets up a new workspace by calling `/kit:setup tutor <path>`. `/kit:setup` keeps its `[<project path>]` argument. | One skill writes method keys (user, 2026-10-21). |
| D16 | `/kit:method default` clears the local method keys. `/kit:setup` clears them too when it sets a new default. | Local keys outrank the folder default, so leftover keys would load two methods (user, 2026-10-21). |
| D17 | `tutor` and `sp` are added to the design router's list as `not-design`. | The router's gate refuses a skill of an installed plugin it does not list (user, 2026-10-21). |
| D18 | Row 71 comes after this row, and its spec is redrafted against this row's Precedence text. | Row 71's draft edits `global/methods/`, which this row deletes (user, 2026-10-21). |

## Design

### Method plugins

Each method is a folder in `plugins/` with `"category": "method"` in its `marketplace.json`
entry. A method's plugin set is the `dependencies` field of its own `.claude-plugin/plugin.json`.
That field is the only source, and `claude-method` is the only code that reads it. `/kit:setup`,
`/kit:method` and the start check call `claude-method`. `/kit:setup` writes the keys into a
project's settings, and nobody edits them by hand.

| Method | Files | `dependencies` | Style |
|---|---|---|---|
| `my` | `plugins/my/output-styles/my.md` (new); `plugin.json` gains the field | `["superpowers@synced"]` | `my.md`, then `docs-layout.md`, then `plan-format.md`, as on `main` when the code starts. About 42,000 characters. |
| `tutor` | `plugins/tutor/.claude-plugin/plugin.json`, `plugins/tutor/output-styles/tutor.md` (new); `plugins/kit/skills/tutor/` moves to `plugins/tutor/skills/tutor/` | none | `global/output-styles/tutor.md`, then `global/methods/tutor.md` |
| `sp` | `plugins/sp/.claude-plugin/plugin.json`, `plugins/sp/output-styles/sp.md` (new) | `["superpowers@synced"]` | A short paragraph: the method's name, and that superpowers' skills run as superpowers defines them. |

Every style has this frontmatter, with its own name and description:

```yaml
---
name: my
description: The my method's rules
force-for-plugin: true
keep-coding-instructions: true
---
```

All three keep `keep-coding-instructions: true`, because `tutor` teaches code. `false` waits for
the first method that is not about code.

**Rules for the moved text.** The final text depends on row 70, which edits `my.md` and
`docs-layout.md` first. So the spec gives rules, not the text:

1. Move the text as it is on `main` when batch 1 starts. Change only what the rules below name.
2. A pointer to another moved file becomes a pointer to a section of the same style. In `my.md`
   these are line 8 (`global/rules/docs-layout.md`), line 122 (`~/.claude/rules/docs-layout.md`),
   line 215 (`~/.claude/rules/docs-layout.md`, and "That rule loads when a file in `docs/plans/` is
   read … read it if it has not loaded", which goes), line 219 (`docs-layout.md`) and line 279
   (`plan-format.md`).
   In `docs-layout.md`, line 139 (`~/.claude/methods/my.md`). Line numbers are from `main` on
   2026-10-20; the plan's reference sweep finds them again.
3. The line "Applies only in projects whose `CLAUDE.md` imports `~/.claude/methods/my.md`. Ignore
   it otherwise." goes, from both rule files. The style loads only in `my` sessions.
4. The `paths:` frontmatter of the two rule files goes.
5. `my.md` line 3 ("A project uses them by importing this file") says instead that the `my`
   plugin forces them on.
6. `my.md` line 217 asks that Project facts "names the method". That clause goes (see
   `/kit:setup`).
7. Pointers to the core's moved sections ("Engineering standards in `~/.claude/CLAUDE.md`",
   "Mandatory Exploration (in the core)", "the core's Reference Sweep", "the core's Simplicity
   Rules") point at `~/.claude/rules/engineering.md`.
8. In the tutor style, step 2 ("Read `~/.claude/output-styles/plain.md`") goes, because the core
   now holds those rules. `kit:tutor` becomes `tutor:tutor`. The line "If the `tutor` output style
   is not active …" goes. The exceptions line becomes: "Exceptions to the core and to
   `~/.claude/rules/engineering.md`: Verify against ground truth, Mandatory Exploration, Reference
   Sweep and Simplicity Rules do not apply in a learning workspace." `engineering.md` loads in a
   tutor session when a `.js` file is read, so the exception must name it.
9. In `plugins/tutor/skills/tutor/SKILL.md`:
   - line 21 points at the tutor style, not at `~/.claude/methods/tutor.md`;
   - setup step 6 no longer writes `"outputStyle": "tutor"`. A new step calls
     `/kit:setup tutor <workspace path>`, which writes the method keys and commits (D15).
     `.claude/settings.local.json` still gets its ignore entry;
   - the hand-over (step 10) says the method loads from the folder's settings, so a plain
     `cd <workspace> && claude` is enough;
   - the session's step 2, which checks for the style, goes: the forced style loads whenever the
     plugin is on.
   `plugins/tutor/skills/tutor/method.md` line 4 says `tutor:tutor`.

### The core and `engineering.md`

`global/CLAUDE.md` keeps:

- **Precedence**, rewritten: "this file, the rule files in `~/.claude/rules/`, and the active
  method's rules (the output style its plugin forces on) are the highest authority: when plan
  mode, a skill or a system default conflicts, follow them. The rules in this file and in
  `~/.claude/rules/` hold under every method. A method may add rules. It may name an exception to
  a rule in this file or in `~/.claude/rules/engineering.md` only by naming the rule."
- **Important** (commits, dependencies).
- **Communication.** The line that points at the `plain` style is replaced by the text of
  `global/output-styles/plain.md`, without its frontmatter. "Challenge assumptions" stays.
- **Critical Thinking**, as its own `##` section.
- **Design work** (row 70's section: call `kit:design-router` before any design work). Design work
  happens outside code too, and `kit` is always on.
- **HTTP Requests.**
- The HTML comment at the end about language rules.

`global/rules/engineering.md` (new) takes, word for word: `## Code`, the "Engineering standards"
intro with "Verify against ground truth", "Mandatory Exploration", "Reference Sweep" and
"Simplicity Rules". Its frontmatter:

```yaml
---
paths:
  - "**/*.{py,js,ts,jsx,tsx,mjs,cjs,vue,php,sh,go,rs,java,rb,lua,sql,css,scss,html}"
  - "**/{package.json,composer.json,pyproject.toml,Dockerfile}"
  - "**/docs/plans/*.md"
---
```

**The first task is a test of this.** Path-scoped rules load when Claude reads a matching file.
The docs do not say whether they load when Claude creates a new file. The plan's first task puts
a rule with a codeword in a test repo's `.claude/rules/`, asks a headless session to create
`new.py`, then asks for the codeword. If the rule does not load on create, stop and ask the user:
D2 was picked on the assumption that it does.

### Choosing and switching

All three ways write `enabledPlugins` keys.

| Way | Scope | Writes | Applies to |
|---|---|---|---|
| Folder default | project, `.claude/settings.json`, committed | The method and its dependencies `true` | Every session started in that folder |
| `claude-method <m> [claude args]` | one process, through `--settings` | The method and its dependencies `true`; the off set `false` | That session only |
| `/kit:method <m>` | local, `.claude/settings.local.json` | The same keys, through `claude plugin enable` and `claude plugin disable` with `--scope local` | Every session in the folder, after the user submits `/reload-plugins` |

**The off set** is every other method and its dependencies, minus the chosen method and its
dependencies. `claude-method sp` keeps `superpowers@synced` on although `my` also depends on it.
A plugin the user turned on by name that is another method's dependency also goes off: for one
session under `claude-method`, and until the user turns it on again under `/kit:method`.

**`claude-method`** is `plugins/kit/bin/claude-method`, a Python 3 script with no packages
outside the standard library. A symlink `~/bin/claude-method` puts it on the shell's `PATH`, as
`~/bin/git-fold-fixups.py` does today. Inside a session it is on `PATH` as a kit script.

- It finds the marketplace folder in `~/.claude/plugins/known_marketplaces.json`, entry
  `claude-setup`, field `installLocation`. It reads `.claude-plugin/marketplace.json` there, and
  each method's `plugin.json`.
- `claude-method` with no argument lists the methods with their descriptions and exits 0.
- `claude-method <unknown>` lists them and exits 1.
- `claude-method --json <m>` prints the settings JSON and exits 0. `/kit:setup` and `/kit:method`
  use it.
- `claude-method --methods` prints one JSON object that maps each method key to its list of
  dependency keys, and exits 0. The start check and `/kit:setup` use it to find every method and
  dependency key.
- The plugin keys come only from manifests, because `claude plugin enable` accepts a name that
  does not exist.
- `claude-method <m> <args…>` runs `claude --settings '<json>' <args…>` with `exec`.
- `none` turns every method and every dependency off.
- **A `--plugin-dir` in the args.** When one names a folder whose `plugin.json` name is a method
  `<p>`, the script sets `<p>@claude-setup` to `false`. The folder's copy, named `<p>@inline`,
  then loads alone. Without this, two `my` styles load and the first one wins silently.
- **A `--settings` in the args** is refused with exit 2 and a message. Claude Code's merge of two
  `--settings` flags is not documented.
- No marketplace entry, or an unreadable file: a message naming the file, exit 1.

**`/kit:method <m>`** is a new skill, `plugins/kit/skills/method/SKILL.md`, with
`disable-model-invocation: true`: only the user switches the method. It runs
`claude-method --json <m>`, then one `claude plugin enable <key> --scope local` or
`claude plugin disable <key> --scope local` per key. It shows each command's result. If one
fails, it stops and says which keys changed. It ends by asking the user to submit
`/reload-plugins`, which Claude cannot submit (test 21).

`/kit:method default` removes every method key and every dependency key (from
`claude-method --methods`) from `.claude/settings.local.json`, so the folder default applies
again. It edits the file directly, because `claude plugin` can set a key but not remove one. It
leaves every other key alone, then asks for `/reload-plugins` (D16).

**Resume.** `claude-method <m> --resume <id>` passes the flag on. A bare `claude --resume`
resumes into the folder's default. Rules and plugins change together on reload and resume
(spike 2), so the resumed session is consistent; it runs the default method.

**`my:handoff`.** The launch lines at `plugins/my/skills/handoff/SKILL.md` lines 319, 330, 345
and 354 change `claude -n <name> <plugin-dir flags> …` to
`claude-method my -n <name> <plugin-dir flags> …`. A stage then runs `my` in any folder. The
`--plugin-dir` rule above keeps a copied `--plugin-dir plugins/my` from loading `my` twice.

### The start check

`plugins/kit/hooks/method-guard.py` is rewritten in place, and keeps its contract: it reads files
only, prints at most 2,000 characters as one JSON object (`systemMessage` and
`additionalContext`), and always exits 0. It reads:

- the method list and dependencies, from `$CLAUDE_PLUGIN_ROOT/bin/claude-method --methods`. If the
  call fails, the check prints one warning naming the error and exits 0;
- `enabledPlugins` from `~/.claude/settings.json`, `<root>/.claude/settings.json` and
  `<root>/.claude/settings.local.json`, a later file winning per key. A key no file names counts
  as on for an `@synced` plugin and as off for any other;
- `<root>/CLAUDE.md` and `<root>/CLAUDE.local.md`.

It warns in three cases:

1. Two or more methods are on: "Claude Code applies only the first style it loads". It names them.
2. A method is on but a dependency is off or missing. It names the key and says to run
   `/kit:setup <m>`.
3. A line `@~/.claude/methods/<m>.md` is still in `CLAUDE.md` or `CLAUDE.local.md`. It says to
   run `/kit:setup <m>`.

It cannot see `--settings` or `--plugin-dir`, so it judges the folder's files, not one session's
flags. Its old checks (import approval and the rest) go, because there is no import.

The other SessionStart hook in `hooks.json`, which finds `docs/learning/curriculum.md` and tells
the model to call `kit:tutor`, is deleted. A learning workspace sets `tutor` as its default.

### `/kit:setup`

`plugins/kit/skills/setup/SKILL.md` is rewritten for `/kit:setup <m> [<project path>]`, where
`<m>` is a method or `none`, and the path defaults to the current repo root, as today. It takes
the keys from `claude-method --json <m>` and `claude-method --methods`. In the repo, it:

1. writes the method and its dependencies as `true` in `.claude/settings.json`;
2. removes the keys of every other method and its dependencies, except the chosen method's own;
3. removes every method and dependency key from `.claude/settings.local.json`, and an
   `outputStyle` key there that names `plain` or `tutor` (D16);
4. removes the `@~/.claude/methods/<m>.md` line from `CLAUDE.md` or `CLAUDE.local.md`;
5. removes the `**Method:**` line from "Project facts". The settings file now names the method.

For `my` it keeps today's steps 1 and 2 (find the facts, find copied rules), reading the `my`
style instead of `global/methods/my.md`. It shows one diff, asks, writes, and commits, as today.
Its "Steps for `tutor`" section becomes the same flow with no facts block.

### Which repos move, and when

| Repo | Moves |
|---|---|
| `claude-setup` | In batch 1: its `CLAUDE.md` loses line 29 (the import) and line 23 (`**Method:**`). Its keys are already on. |
| zitamu (`real-estate-webapp`) | In batch 1: its local file is `projects/real-estate-webapp/claude-local.md` in this repo, which loses line 28 (the import) and line 22 (`**Method:**`). Its keys are already on. |
| `mv3-tab-notes` | In the rollout, after batch 1 merges: `/kit:setup tutor`. It has no project keys and an `outputStyle: "tutor"` in its local settings. |
| maritime, mv3-starter, niche-research, diagoradisa-annotator, diagoradisa-palmist, grispy-ext, grispy-site | When next opened, through start check 3. Their keys are already on, so they run `my` from the merge on. Their old line points at a missing file, which Claude Code skips: a headless run with `@~/.claude/methods/does-not-exist.md` in `CLAUDE.md` read the rest of the file with no error (2.1.304, 2026-10-20). |

### Deleted

- `global/methods/` (`my.md`, `tutor.md`), `global/rules/docs-layout.md`,
  `global/rules/plan-format.md`, `global/output-styles/` (`plain.md`, `tutor.md`).
- `plugins/kit/tests/test_method_guard.py`'s import cases, replaced (see Testing strategy).
- The tutor SessionStart hook in `plugins/kit/hooks/hooks.json`.
- By hand, in the rollout: the symlinks `~/.claude/methods` and `~/.claude/output-styles`.
  `~/.claude/rules` stays.

### Batches and rollout

**Batch 1: methods become plugins.** The three method plugins, the core and `engineering.md`,
`claude-method` and its test, the start check, the tutor hook's removal, `/kit:setup`, the tutor
skill's setup, the `marketplace.json` entries, the design router's list, the moves of
`claude-setup` and zitamu, and every reference in Files. It works alone: a folder's settings pick
its method, and `my:handoff` keeps launching `claude`, which picks the folder's method.

**Rollout after batch 1 merges,** by hand, in this order:

1. Check that `tutor@claude-setup` and `sp@claude-setup` load when a project's settings turn them
   on, with no `claude plugin install`. The loading docs say a relative-path plugin does. If not,
   install each and check that the user scope still keeps it off.
2. Edit `~/.claude/settings.json`: remove `"outputStyle": "plain"`, and set every plugin outside
   D5's list to `false`, the synced ones and the design plugins included (D14).
3. Remove the `~/.claude/methods` and `~/.claude/output-styles` symlinks.
4. Restart running sessions.
5. Run `/kit:setup tutor` in `mv3-tab-notes`. Its curriculum uses `modern-web-guidance`, which
   step 2 turned off: turn it on in that project by name when a lesson needs it.

**Batch 2: switching.** The `~/bin/claude-method` symlink, `/kit:method`, and the `my:handoff`
launch lines.

## Files

| File | Batch | Change |
|---|---|---|
| `plugins/my/output-styles/my.md` | 1 | New: the `my` style |
| `plugins/my/.claude-plugin/plugin.json` | 1 | Add `dependencies`; description names the style |
| `plugins/tutor/.claude-plugin/plugin.json` | 1 | New |
| `plugins/tutor/output-styles/tutor.md` | 1 | New: the `tutor` style |
| `plugins/tutor/skills/tutor/` | 1 | Moved from `plugins/kit/skills/tutor/`; line 21 edited |
| `plugins/sp/.claude-plugin/plugin.json` | 1 | New |
| `plugins/sp/output-styles/sp.md` | 1 | New: the `sp` style |
| `.claude-plugin/marketplace.json` | 1 | `my` gets `"category": "method"`; `tutor` and `sp` added; `my` and `kit` descriptions updated |
| `global/CLAUDE.md` | 1 | Split as above |
| `global/rules/engineering.md` | 1 | New |
| `global/methods/`, `global/rules/docs-layout.md`, `global/rules/plan-format.md`, `global/output-styles/` | 1 | Deleted |
| `plugins/kit/hooks/method-guard.py` | 1 | Rewritten |
| `plugins/kit/hooks/hooks.json` | 1 | Tutor hook deleted |
| `plugins/kit/skills/setup/SKILL.md` | 1 | Rewritten |
| `plugins/kit/bin/claude-method` | 1 | New |
| `plugins/kit/tests/test_claude_method.py` | 1 | New |
| `plugins/kit/skills/design-router/plugins.json` | 1 | Add `"tutor": "not-design"` and `"sp": "not-design"` |
| `plugins/tutor/skills/tutor/SKILL.md` | 1 | Lines 21, 110 to 115, 136 and 158 to 162 (rule 9) |
| `plugins/kit/.claude-plugin/plugin.json` | 1 | Description: no tutor, the new guard |
| `plugins/kit/tests/test_method_guard.py` | 1 | Rewritten |
| `plugins/kit/tests/test_neutral_core.py` | 1 | Updated |
| `plugins/my/skills/status/SKILL.md` | 1 | Line 60 points at the `my` style |
| `plugins/my/skills/handoff/README.md` | 1 | Line 267 points at the `my` style |
| `plugins/my/README.md` | 1 | Lines 19 to 28 and 91: the method is the plugin and its style |
| `README.md` | 1 | Lines 9 to 20, 91 to 100, 146 (`kit:tutor`), 152, 186 (`docs-layout.md`), 251 to 253 (the tutor hook), 255 to 257 (the guard) |
| `plugins/my/skills/clean-plans/SKILL.md` | 1 | Line 22 points at the `my` style |
| `plugins/my/README.md` | 1 | Lines 72, 134 and 153 (`docs-layout.md`) |
| `plugins/tutor/skills/tutor/method.md` | 1 | Line 4: `kit:tutor` becomes `tutor:tutor` |
| `global/git-hooks/pre-commit`, `global/git-hooks/pre-push` | 1 | Line 2 comments point at the `my` style |
| `ROADMAP.md` | 1 | Rows that name `global/methods/my.md`, `docs-layout.md` or `plan-format.md` as a file to edit (lines 52 to 55, 75, 298 to 304, 474 to 478 on 2026-10-20) name the `my` style |
| `CLAUDE.md` | 1 | Lines 3, 23 and 29; the plugin list |
| `projects/real-estate-webapp/claude-local.md` | 1 | Lines 22, 28 and 238 |
| `plugins/kit/skills/method/SKILL.md` | 2 | New |
| `plugins/my/skills/handoff/SKILL.md` | 2 | Launch lines |
| `README.md` | 2 | `claude-method`, `/kit:method` |

Old documents in `docs/plans/` and `docs/reports/` keep their old paths: they record what was true
when they were written. This table is the sweep of 2026-10-20. The plan's Reference Sweep runs
again on the text as it is when batch 1 starts, and owns the final list.

## Trade-offs

- **Option A, rules as a forced plugin style** (chosen in the brief). Pros: rules and plugins load
  and unload together; one unit per method; nothing new to run. Cons: one style per session, so
  `plain` moves into the core; `docs-layout.md` loads in every `my` session, about 3,300 tokens
  more.
- **Option B, keep the rule files path-scoped and exclude them elsewhere with
  `claudeMdExcludes`.** Pros: no extra tokens. Cons: every other method must list the exclusion,
  and the merge of `claudeMdExcludes` across scopes is untested.
- **Starting a new learning project** needs the `tutor` plugin on first, because `tutor:tutor` no
  longer lives in `kit`: `claude-method tutor` in the new folder, then `/kit:setup tutor`.
- **A start check that cannot see flags.** It judges the folder's files only. `claude-method`
  makes this safe by always writing one method and its full set.

## Dependencies

- **Rows 33, 37 and 56 merge first.** They fix `my:handoff`'s launch lines, which batch 2 edits.
- **Row 62 merges first.** It edits `global/output-styles/plain.md`, which batch 1 moves.
- **Row 70 has merged** (`5dfd634`). It edited `my.md`, `docs-layout.md` and the core. Its spec
  says this row "must start from the text this spec leaves". One line there is out of date: it
  says this row turns
  `docs-layout.md` into a skill (candidate B). Under candidate A the file folds into the `my`
  style. That spec belongs to another session and is not edited here.
- **Row 69 comes after.** It renames skills in files this row edits.
- **Row 71 comes after** (D18). Its drafted spec, `docs/plans/2026-10-18-project-precedence-spec.md`,
  rewrites the same Precedence paragraph and edits `global/methods/`. It is
  redrafted against this row's Precedence text.
- **Claude Code 2.1.304 or later**: `force-for-plugin`, `dependencies`, in-place loading.
- No new packages.

## Risk

- **Blast radius: every session.** The core changes for every session. The `my` rules change for
  the nine `my` repos at the merge, because the plugin loads in place. `mv3-tab-notes` loses its
  tutor start hook and its `tutor` style at the merge, until rollout step 5: the style file is
  deleted, and the `tutor` plugin is not on there yet.
- **Hard to reverse:** the import lines leave `claude-setup` and zitamu in batch 1, and the
  other repos when opened. Going back means restoring `global/methods/` from git and running the
  old `/kit:setup` in each repo.
- **Two forced styles win silently.** Start check 1 catches it in files; `claude-method`'s
  `--plugin-dir` rule catches it in flags. A plain `claude --plugin-dir plugins/my` in a `my`
  folder still loads two; the user must add `--settings` to turn the folder's copy off.
- **`engineering.md` may not load on file creation.** The first task tests it.
- **Missing dependency keys** in older projects disable the method, with a visible error and
  start check 2.
- **The off set turns off a plugin the user enabled on purpose** if it is another method's
  dependency.
- **The strict bare scope turns off the design plugins** (D14). Until the user turns one on by
  name, `kit:design-router` stops in every repo and names the plugin that is off. The same holds
  for `modern-web-guidance` in `mv3-tab-notes`.
- **The start check depends on `claude-method`.** If the script fails, the check warns and
  judges nothing; the session still starts.
- **Old text stays in history after a mid-session switch** (test 24). Known limit.
- **Manual steps:** the rollout, and the `~/bin/claude-method` symlink in batch 2.

## Testing strategy

Every code change starts with a failing test. Headless runs on a branch load the branch's copy
with `--plugin-dir <worktree>/plugins/<p>` and turn the main checkout's copy off with
`--settings '{"enabledPlugins":{"<p>@claude-setup":false}}'`: a session in a worktree loads this
marketplace's plugins from the main checkout.

| Part | Test |
|---|---|
| Path-scoped rule on create | First task, as in "The core and `engineering.md`". |
| `method-guard.py` | `test_method_guard.py`: one case per warning; all well (no output); an unreadable settings file (exit 0, a warning naming it); an `@synced` key missing counts as on; `claude-method` failing (exit 0, one warning). |
| The core | `test_neutral_core.py`: the core holds the `plain` rules, Critical Thinking and Design work (the existing `test_core_sends_design_work_to_router` stays); it does not hold Mandatory Exploration, Reference Sweep or Simplicity Rules; `engineering.md` has a `paths:` header; kit names no method's skill. |
| The `my` style | A headless run in a test folder whose settings turn `my` on: the init event's `plugins` list holds `my` and `superpowers`. A unit test checks the style's frontmatter keys and that no "Applies only in projects whose" line is left. |
| `/kit:setup`, `/kit:method` | Headless runs on a test repo, checking the settings files they leave. |
| `claude-method` | `test_claude_method.py` with a fake `known_marketplaces.json` and fake methods: on and off sets; a shared dependency stays on; `none`; unknown name exits 1; no argument lists; `--json`; `--methods`; a `--plugin-dir` naming a method turns its `@claude-setup` key off; a `--settings` in the args exits 2. End to end: a fake `claude` first on `PATH` prints its arguments. |
| `/kit:method default`, `/kit:setup` on local keys | Headless runs: a local file with `my` keys and an unrelated key; after the command, only the unrelated key is left. |
| The switch for real | `claude-method sp -p … --output-format stream-json --verbose`: the init event lists `sp` and `superpowers`, not `my`. |
| Rollout step 1 | Run by hand, its result written into the plan. |

## Open questions

None.
