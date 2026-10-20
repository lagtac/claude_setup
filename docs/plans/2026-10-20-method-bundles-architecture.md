# Architecture brief: methods as bundles

**Status:** approved, 2026-10-20. Candidate A (a method is a plugin), chosen by the user; brainstorming writes the spec next. It replaces the Decision of `docs/plans/2026-10-18-launch-method-switch-architecture.md`.

## How to read this brief

1. This brief. It answers the user's question of 2026-10-20: why can't method switching itself be a skill or a plugin?
2. The user's intent, stated 2026-10-20 (the description this brief was built from, kept in full only in the session scratchpad):
   - Agents serve more kinds of work than coding: emails, tutoring and learning, market research.
   - No kind of work is locked into one workflow; `my` and `superpowers` are two development workflows among several.
   - a. A new session starts bare and assumes nothing before it has read the directory.
   - b. The global configuration is light: it does not load every installed plugin and skill.
   - c. A fast, simple audit finds skills that overlap when loaded together.
   - d. A directory can name its method exactly. With none named, the user loads and unloads plugins and skills by name, with autocomplete.
   - e. A method is a bundle of plugins and skills that work together, strict or loose as its author wants.
3. `docs/plans/2026-10-18-launch-method-switch-architecture.md`: the first brief for row 68 (candidate D, a launcher named `claude`). Its forces, flag tests 1–16 and evaluation still hold as evidence. Its Decision is replaced here.
4. `docs/plans/2026-10-12-swappable-methods-architecture.md`: the brief behind today's switch (import line, plugin keys, guard), shipped as row 16.
5. `global/methods/my.md`, `global/methods/tutor.md`, `global/rules/docs-layout.md`, `global/rules/plan-format.md`, `global/output-styles/plain.md`: today's rules.
6. `plugins/kit/skills/setup/SKILL.md`, `plugins/kit/hooks/method-guard.py`: today's per-project switch and its guard.
7. `.claude-plugin/marketplace.json`: the marketplace where method plugins would live.
8. Claude Code docs, checked 2026-10-20: `code.claude.com/docs/en/output-styles` (`force-for-plugin`, `keep-coding-instructions`), `…/plugins/dependencies`, `…/plugins/cli-reference` (`/reload-plugins`, `plugin enable|disable|update|details`), `…/cli-reference` (`--settings`), `…/settings`, `…/skills` (`skillOverrides`), `…/memory` (`claudeMdExcludes`).

## Forces

The standard forces were written for server systems. Each is mapped onto an instruction system; the mapping is in the Force column.

| # | Force | Value | Label | Source or reason |
|---|---|---|---|---|
| 1 | Load | More than 6 Claude sessions at once; several share one checkout (3 in claude-setup on 2026-10-19); `my:handoff` starts more. | stated | User answer 2026-10-18; `ListAgents` 2026-10-19 |
| 2 | Data volume and growth | Many methods over time (more than 8). Today 17 plugins and 142 skills are installed and loaded; `my.md` is 30,937 chars, plus 13,096 in its two path-scoped rule files. | stated | User answer 2026-10-18; `/context`; `wc -c` |
| 3 | Latency (here: the effort to switch or load) | One command to choose a session's method. Load or unload a plugin or skill by name, with autocomplete. No file edit by hand, no commit. | stated | User points d and "switch for an afternoon" |
| 4 | Availability (here: the method is in force) | A directory that names a method has it in force from the first turn, with no model decision. A directory that names none starts bare. Terminal and tmux only. | stated | User points a and d; answer 2026-10-18 |
| 5 | Consistency | Within one session, rules and plugins belong to the same method. A method chosen at launch is isolated: it changes no other session. A switch made during a session may use the harness's own commands and so apply to the whole directory, for every session in it. | stated | User answer 2026-10-20 ("Isolated at launch only"), after asking for "the most simple mechanism that doesn't go against the capabilities of the harness" |
| 6 | Security and compliance | Nothing new: the existing hooks and the core's "ask before outward actions" rule are enough, also for non-coding methods. | stated | User answer 2026-10-20 |
| 7 | Team and operations | One developer | stated | `global/methods/my.md` Git Workflow |
| 8 | Rate of change | Rules change often; methods are added; Claude Code updates every few days (2.1.302 to 2.1.304 in two days). | stated | User 2026-10-18; `claude --version` |
| 9 | Cost | Context tokens matter: a bare session loads few plugins. Today about 10k tokens of skill listings and about 30k of deferred MCP tool names load. Money does not matter. | stated | User point b; `/context` |
| 10 | Fixed constraints | Rely on documented Claude Code features only. Documented (checked 2026-10-20): `--settings <file-or-json>` for one session; `--append-system-prompt-file`; `claudeMdExcludes`; `enabledPlugins` per scope and through `--settings`; plugin `output-styles/` named `<plugin>:<name>`, with `force-for-plugin` and `keep-coding-instructions`; `/reload-plugins`; `claude plugin enable/disable/update --scope`; settings files are watched; `/output-style` saves to `.claude/settings.local.json`; `skillOverrides` and `/skills` (they do not affect plugin skills); plugin `dependencies`; `claude plugin details`; a resumed conversation reuses its recorded system prompt until compaction. Documented as not supported: a plugin `CLAUDE.md`. Not found in the docs: plugin `rules/`, a script named `claude` before the real binary on `PATH`. Other limits: one output style per session; hook text capped at 10,000 chars; superpowers is third-party; subagents read no `CLAUDE.md`. | stated | User answer 2026-10-20 ("Documented only"); docs check 2026-10-20; tests 1–27 |

## Collapse gate

Three candidates. Forces 1 (one machine) and 7 (one developer) would allow one. But force 4 asks that the method be in force from the first turn with no model decision, the instruction-system form of a strict uptime target. And force 5 needs two scopes of switching (one session at launch, the whole directory during a session) that must agree.

Candidate B came back as a near-copy of A. The 2026-10-18 choice, D, is weighed again as the description asks.

Skipped shapes:

- Queue and background workers: would need slow work to move off the launch; there is none.
- Event-driven: would suit a method chosen by session events (start, resume, compaction). The documented hook events can neither enable plugins nor set a style, and hook text is capped at 10,000 chars (force 10).
- Client-heavy or offline-first: would need a remote server; there is none.
- Managed or serverless services: would need entry points outside the terminal; force 4 allows the terminal only.

## Candidates

### Candidate A: simplest design

**Reason:** Always included: the simplest design that could meet the forces.
**Contrast:** vs B: none of the four axes differ after return; vs C: processes (C adds a build step) and data ownership (C derives its outputs from sources).
**Labels:** none

#### Summary

Claude Code is the only process. Its own settings files (user, project, local, and the `--settings` flag) are the only data store. Each method is one plugin in the claude-setup marketplace. Its rules ship as a plugin output style with `force-for-plugin: true`, and the plugins it needs are listed in `plugin.json` `dependencies`. Choosing a method means writing `enabledPlugins` keys at the right scope: project settings for the directory default; local settings plus `/reload-plugins` for a switch during a session; `--settings` on the command line for an afternoon.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Method plugin (`my`, `tutor`, `superpowers` as a bundle on `superpowers@synced`; `plain` means no method plugin) | Bundles the rules (forced style; `keep-coding-instructions: false` for non-coding methods) and the plugin set (`dependencies`) | The method's rules and plugin list | Plugin folder |
| User settings | Every method plugin and heavy plugin off; only `kit` and the language servers on; no `outputStyle` | What a bare session loads | Settings file |
| Project settings `.claude/settings.json` | The directory's default method | The default method | Committed settings file |
| Local settings `.claude/settings.local.json` | Kept or mid-session switch, and single plugins loaded or unloaded by name | The directory's current override | Uncommitted settings file |
| `claude-method <m> [args]` | Builds `--settings` JSON (the method and its dependencies on, every other method off) and runs `exec claude` | none | Script, about 15 lines |
| `kit:method <m> [--project]` | Runs `claude plugin enable/disable --scope local` (or writes project scope), then tells the user to submit `/reload-plugins` | none | Skill |
| `kit:skill-overlap` | Lists skills that clash in name or description within the enabled set; flags two method plugins on at once | none | Read-only script |
| Core `global/CLAUDE.md` | Takes in `plain`'s 2,412 chars, because a session has one style slot | The core rules | Memory file |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| Claude Code → user, project and local settings | Merged `enabledPlugins` at launch and on reload | sync | Unreadable file: Claude Code reports it; the session starts bare |
| `claude-method` → `claude` | `exec` with one `--settings` JSON | sync | Unknown method: list the methods, exit 1 |
| `kit:method` → local settings | `claude plugin enable/disable --scope local` | sync | Command fails: the skill shows the error; nothing has changed |
| User → Claude Code | `/reload-plugins` | sync | Not submitted: the old plugins and the old style stay until the next launch |
| Claude Code → method plugin | Its forced style goes into the system prompt; its dependencies must already be on | sync | A dependency is off: the plugin is disabled at load with `dependency-unsatisfied` (spike 1) |
| `my:handoff` → new session | `claude-method my -n <name> …` | sync | Script missing: print the command |
| `kit:skill-overlap` → `claude plugin details` | Skill names and descriptions | sync | Prints a warning; never blocks |

### Candidate B: separate deployables, each owning its own data

**Reason:** Force 2 (many methods) and force 5 (one method's rules and plugins belong together): each method ships as its own plugin, which owns its rules, its plugin set and its style.
**Contrast:** vs A: none of the four axes differ after return; vs C: processes and data ownership.
**Labels:** near-copy of candidate A

#### Summary

Each method is its own plugin in the claude-setup marketplace: `my`, `tutor`, and a thin `sp` wrapper for the superpowers workflow. `plain` gets no plugin. A method plugin owns its rules (`output-styles/<m>.md`), its plugin set (`dependencies`) and its skills and hooks. Choosing a method always means setting two keys, `enabledPlugins["<m>@claude-setup"]` and `outputStyle: "<m>:<m>"`, in project settings, in `--settings`, or in `settings.local.json`. `docs-layout.md` and `plan-format.md` become skills of `my`.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Method plugin `my` | The strict dev workflow | Its rules (about 31k chars), its dependencies (`superpowers`), its skills, agents and hooks, and its rule skills `my:docs-layout` and `my:plan-format` | Plugin, cached by commit hash |
| Method plugin `tutor` | Learning work | Its style (`keep-coding-instructions: false`) and the tutor skill, moved from `kit` | Plugin |
| Method plugin `sp` | Superpowers without the `my` layer | A short style and `dependencies: ["superpowers"]` | Plugin |
| Marketplace `marketplace.json` | Registry of methods | Which plugins are methods (`category: "method"`) | File |
| Core `global/CLAUDE.md` | Rules for every session | Core rules plus the `plain` rules | User memory file |
| `kit` (user scope, always on) | Neutral tools | `kit:method`, `kit:overlap`, the guard, `kit:setup` | Plugin |
| Directory settings | The default method | The two keys | `.claude/settings.json` |
| `cm <m> [args]` | Switch for one session | none (builds its JSON from the marketplace) | Client script, about 15 lines |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| Bare `claude` → directory settings | The two keys | sync | No keys: bare session, core rules only |
| `cm` → `claude` | `--settings` with the chosen method on, the others off, and `outputStyle` | sync | Unknown name: list the methods, exit 1 |
| Method plugin → its dependencies | Enables them on load | sync | A dependency is missing: Claude Code reports it |
| `kit:method <m>` → `settings.local.json` | Kept switch | async: the style applies next turn, the plugins only after `/reload-plugins` | The user does not reload: new rules run with old plugins; the guard warns |
| Resume → session | The recorded system prompt, plus the directory default's plugins | sync | `cm <m> --resume <id>` relaunches with the same flags |
| `my:handoff` → new `claude` | Copies the `--settings` value from `ps` | sync | Value missing: the stage starts in the directory default |
| Guard (SessionStart) → settings and marketplace | At most one method plugin on, matching the style's prefix | sync | Warns, exits 0 |
| `kit:overlap <m>` → `claude plugin details` | Each plugin in the method's closure | sync | A call fails: that plugin is reported unchecked |

### Candidate C: pipeline or batch processing

**Reason:** Force 8 (rules change often) and force 9 (context tokens; point c's overlap audit): a build step generates each method's bundle and the overlap report from one source, before any session starts.
**Contrast:** vs A: processes and data ownership; vs B: processes and data ownership.
**Labels:** none

#### Summary

Each method has one source: its rules file and a small manifest naming its plugins, its `keep-coding-instructions` value and the rule files it keeps. A build script, run by the repo's pre-commit hook and on demand, compiles every manifest into a merged output style (the method's rules plus `plain`), a settings fragment (`outputStyle`, every plugin on or off, `claudeMdExcludes`) and a generated command. One build also writes the overlap report and a shell completion file. The outputs go into folders that are live symlinks into the repo, not into a plugin, so a build takes effect with no plugin update.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Method sources `global/methods/<m>.md` + `<m>.method.json` | Rules and the bundle definition | The truth for every method | Committed files |
| `global/methods/build.py` | Validate manifests, merge each style with `plain.md`, emit fragments, commands, completion, overlap report, source hash | none | Batch script (pre-commit, manual) |
| Built outputs (`global/output-styles/m-<m>.md`, `global/methods/build/<m>.settings.json`, `overlap.md`, `completion.bash`, `stamp`) | What sessions load | Derived only (gitignored, rebuilt) | Files |
| Generated commands `~/.claude/skills/method-<m>/` | Mid-session switch: copy the fragment into `settings.local.json`, then ask for `/reload-plugins` | none | Skill |
| `cm <m> [args]` | One-session switch with `--settings …/build/<m>.settings.json` | none | Client (shell, tmux) |
| Directory default | The project's committed `.claude/settings.json`, holding the fragment's keys | The project's default method | Committed file |
| Stale-bundle hook (replaces `method-guard.py`) | Compares `stamp` with the source hash, and the project keys with the fragment | none | SessionStart hook |
| Overlap audit, live mode | Audits the plugins enabled right now | none | On-demand script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| pre-commit → `build.py` | Changed source paths | sync | Bad manifest or a new overlap: block the commit |
| `build.py` → output folders | Files written to a temp path, then renamed | sync | Old outputs stay; `stamp` stays old, so the hook warns |
| `build.py` → `claude plugin details` | Skill names, descriptions, token cost | sync | Format changed: the audit marks itself incomplete |
| `cm` → `claude` | `--settings` path, `CLAUDE_METHOD` env | sync | Unknown method: list methods, exit 1 |
| `my:handoff` → new `claude` | Same `--settings` path, read from `CLAUDE_METHOD` | sync | Variable unset: the stage starts on the directory default |
| `/method-<m>` → `settings.local.json` | Fragment keys | sync | Write fails: report; the style applies next turn, plugins after `/reload-plugins` |
| Hook → session | Warning text under 2,000 chars | sync | Fails open |

### Candidate D: launcher named `claude`

**Reason:** Weighed again as the description asks. It was the 2026-10-18 Decision.
**Contrast:** vs A: processes (a launcher in front of the binary) and data ownership (methods are files, not plugins); vs C: data ownership and communication (no build stage).
**Labels:** carried over; no new draft. Its Components and Connections tables are in the 2026-10-18 brief, section "Candidate D".

#### Summary

A script named `claude` sits in its own folder, placed before `~/.local/bin` in `PATH` in both the shell and tmux. It reads the method from `CLAUDE_METHOD` if set, else from the project's one line naming its default. Then it execs the real `claude` with `--append-system-prompt-file <m>.md` and `--settings <m>.settings.json`, and exports `CLAUDE_METHOD`. Projects keep no import line and no plugin keys.

## Evaluation

### Data ownership

| State | A | B | C | D |
|---|---|---|---|---|
| A method's rules | Its plugin's forced style | Its plugin's style | Source `.md`; the style is derived | `global/methods/<m>.md` |
| A method's plugin set | `plugin.json` `dependencies`; **two owners** if the switch script keeps its own copy (it must read `plugin.json` instead) | `dependencies`; `cm` also lists methods to turn off | The manifest; **copies** in every project's settings | `<m>.settings.json` |
| `docs-layout.md`, `plan-format.md` | Folded into the `my` style | `my` skills | Kept global, gated by `claudeMdExcludes` | Kept global, gated by `claudeMdExcludes` |
| `plain` rules | Core `CLAUDE.md` | Core `CLAUDE.md` | `plain.md`, merged into each style by the build | User-scope style, unchanged |
| A directory's default | One `enabledPlugins` key | Two keys | Several copied keys | One method line |
| A kept switch | `settings.local.json` | `settings.local.json` | `settings.local.json` | none |
| A one-session switch | Launch flags only | Launch flags only | Launch flags only | Launch flags and `CLAUDE_METHOD` |

No state has zero owners. Multiple owners: A's plugin set if the switch script copies it (avoided by reading `plugin.json` at run time); C's directory defaults (copies of build outputs in 10 repos).

### Scenarios

| Scenario | A | B | C | D |
|---|---|---|---|---|
| 1. Normal path at peak: 7 sessions, 3 in one checkout; one starts as `tutor` for an afternoon | holds: `--settings` touches one process | holds | holds | holds |
| 2. A kept switch during a session in the shared checkout | holds: the other sessions follow at their next `/reload-plugins`, rules and plugins together (spike 2), as force 5 allows | breaks at "`settings.local.json` → watched": the neighbours get the new rules on their next turn (test 27) but their plugins only at reload | breaks, as B | fails force 3: no switch during a session |
| 3. The most frequent change: edit `my`'s rules | breaks at "plugin cache": sessions load the cached copy, 31 commits behind `HEAD` on 2026-10-20; an edit needs a commit plus `claude plugin update` (spike 3) | breaks, as A | holds: the build writes to symlinked user folders | holds: the file is live |
| 4. Growth after 3 years: 12 methods, 30 plugins | holds: one plugin per method; the switch JSON lists every method once | holds | holds; the build grows linearly | holds |
| 5. A bare resume after an afternoon switch | holds, on one test: resumed without the plugin, the model followed the current style (`plain`) and reported the old style only in history (spike 2, S2H). The docs say the recorded system prompt is reused until compaction, so the old text may still be there | holds, as A | holds, as A | breaks: old rules in the recorded prompt, default plugins |
| 6. A Claude Code update | holds: documented features only | holds | partial: the audit parses `claude plugin details` output | fails force 10: relies on the installer's `PATH` layout |

Force 6 is "nothing new", so no abuse scenario.

### Pre-mortem

#### Candidate A

1. Rule edits never reach sessions, because the plugin cache was not updated after a commit.
2. A switch turns a method on without its dependencies, and the method is disabled at load (spike 1).
3. Two method plugins end up on at once; the first loaded wins silently, and nobody runs the overlap audit.

#### Candidate B

1. A switch in one session gives its neighbours new rules with old plugins.
2. The rule skills `my:docs-layout` and `my:plan-format` are not called, because a path match became a model choice.
3. The plugin cache, as A.

#### Candidate C

1. A build not run after an uncommitted edit or a plugin update leaves stale outputs; the hook only warns.
2. A Claude Code update changes the `claude plugin details` format, and the audit goes silent.
3. Copies of the fragments in 10 repos drift, or `claudeMdExcludes` arrays merge across scopes in a way the design did not expect.

#### Candidate D

1. An update changes the installer's layout, and the launcher stops being first in `PATH`.
2. Sessions started outside the launcher (an IDE, another tool) start with no method.
3. Point d and point e stay unmet: no load by name during a session, and a method is a file pair, not a bundle.

### Comparison

| Force | A | B | C | D |
|---|---|---|---|---|
| 1 Load | meets: no writes at launch | meets | meets | meets |
| 2 Growth | meets: one plugin per method | meets | meets: one manifest per method | meets |
| 3 Effort to switch | meets: `claude-method <m>`, or `kit:method <m>` plus `/reload-plugins`; `/plugin` autocompletes names | meets | meets | partial: launch only |
| 4 In force | meets: the forced style loads with the plugin | meets | meets | meets |
| 5 Consistency | meets: rules follow plugins at every reload | partial: neighbours split until reload | partial, as B | partial: resume splits |
| 6 Security | meets | meets | meets | meets |
| 7 One developer | meets: one script, one skill | meets | partial: a build to run and keep fresh | meets |
| 8 Rate of change | partial: rules are cached; an edit needs a commit and an update | partial, as A | meets for rules; partial for the harness | meets |
| 9 Cost | partial: bare sessions are light; `my` sessions carry about 3,300 more tokens | meets: rule skills load on demand | meets | meets |
| 10 Documented only | meets | meets | partial: parses tool output | fails: `PATH` shadowing is not documented |

## Decision

**Candidate A**, chosen by the user on 2026-10-20. A method is a plugin. Its rules are its output style with `force-for-plugin: true`, and its plugin set is its `dependencies`. Choosing a method is a settings write at the right scope:

- **Directory default:** the method plugin's key, with its dependencies, in the project's `.claude/settings.json`.
- **One session ("an afternoon"):** `claude-method <m>`, which passes `--settings` with the method and its dependencies on and every other method off, with their dependencies (Open item). It writes nothing, so it touches no other session.
- **During a session:** `kit:method <m>` writes `settings.local.json` through `claude plugin enable/disable --scope local`; the user submits `/reload-plugins`. This reaches every session in the directory at its next reload, as force 5 allows.
- **Bare:** the user scope turns on only `kit` and the language servers. With no method plugin on, a session has the core rules only.

This answers the user's question: switching does not need a `methods/` folder, because the method is a plugin and switching is a documented settings write. Rules and plugins cannot disagree, because the style comes and goes with its plugin (spike 2).

Rejected:

- **B** lost because writing `outputStyle` as its own key splits a neighbour's rules from its plugins until it reloads, and because turning the rule files into skills makes their loading a model choice.
- **C** lost on force 7 and force 10: it adds a build that must stay fresh and parses tool output. It is the only candidate whose rules stay live without a plugin update, so if the plugin cache proves too slow (Open item), its build-to-symlinked-folders idea is the fallback.
- **D** lost on force 10 (the `PATH` launcher is not documented) and on points d and e (no switch during a session; a method is a file pair, not a bundle).

## Reversibility and checks

| Decision | Label | Check |
|---|---|---|
| Method rules ship as a forced plugin output style | hard | estimate 1; spike 2 |
| A method's plugin set is its `plugin.json` `dependencies` | hard | spike 1 |
| A directory's default becomes plugin keys in `.claude/settings.json`; the import lines leave 10 repos and 1 worktree | hard | no quantity to check: a one-time migration of a counted set (10 + 1) |
| `docs-layout.md` and `plan-format.md` fold into the `my` style | medium | estimate 1 |
| `plain` moves into the core `CLAUDE.md` | medium | estimate 1 (603 tokens, already loaded today as the user style) |
| `method-guard.py`, `global/methods/` and today's `/kit:setup` retire | medium | no quantity to check |
| `claude-method` script and its name | cheap | none |
| `kit:method` skill | cheap | none |
| `kit:skill-overlap` | cheap | none |
| A bare user scope (`kit` and language servers only) | cheap | none |

```python
"""Estimate: size and token cost of the `my` method as one forced output style (candidate A).

Inputs: the files on main today. Capacity: the largest style loaded whole (test 18).
Tokens: chars / 4, a rough rule for English prose.
"""
import os

REPO = "/home/dchris/projects/claude-setup"
FILES = {
    "my.md (rules)": "global/methods/my.md",
    "docs-layout.md (path-scoped today)": "global/rules/docs-layout.md",
    "plan-format.md (path-scoped today)": "global/rules/plan-format.md",
    "plain.md (moves to the core)": "global/output-styles/plain.md",
}
TESTED = 154_808  # chars, test 18 (heron:big)
size = {k: os.path.getsize(os.path.join(REPO, p)) for k, p in FILES.items()}
for k, v in size.items():
    print(f"{k:40} {v:>7,} chars")
style = sum(v for k, v in size.items() if not k.startswith("plain"))
print(f"\nmy style = my.md + docs-layout + plan-format = {style:,} chars")
print(f"tested capacity {TESTED:,} chars; capacity / style = {TESTED / style:.1f}x (near a limit if < 2x)")
always_today = size["my.md (rules)"]
always_a = style
print(f"\nalways-on in a my session: today {always_today:,} chars (~{always_today // 4:,} tokens), "
      f"A {always_a:,} chars (~{always_a // 4:,} tokens); "
      f"extra ~{(always_a - always_today) // 4:,} tokens per my session")
print(f"every session gains plain in the core: ~{size['plain.md (moves to the core)'] // 4:,} tokens "
      f"(today it is already loaded as the user-scope style)")
```

```text
my.md (rules)                             30,937 chars
docs-layout.md (path-scoped today)        11,410 chars
plan-format.md (path-scoped today)         1,686 chars
plain.md (moves to the core)               2,412 chars

my style = my.md + docs-layout + plan-format = 44,033 chars
tested capacity 154,808 chars; capacity / style = 3.5x (near a limit if < 2x)

always-on in a my session: today 30,937 chars (~7,734 tokens), A 44,033 chars (~11,008 tokens); extra ~3,274 tokens per my session
every session gains plain in the core: ~603 tokens (today it is already loaded as the user-scope style)
```

Not near a limit.

**Tests 17–27** (Claude Code 2.1.304, throwaway plugin with `--plugin-dir`, empty fixture repo):

- 17, 18: a plugin style named `<plugin>:<style>` loads at launch; 154,808 chars load whole.
- 19, 20: `claude plugin enable|disable --scope local` writes `<dir>/.claude/settings.local.json`; the running session changes only after `/reload-plugins`, in both directions.
- 21, 26: the model can run `claude plugin enable` itself, but only the user can submit `/reload-plugins`; Claude Code offers it in the input box.
- 22–24: `/output-style` during a session saves to `settings.local.json`; the style arrives with the next message; the old text stays in history.
- 25, 27: an `outputStyle` key written by any process applies on the next turn with no reload, in every session of that directory.

**Spike 1** (dependencies): a method plugin depending on `my@claude-setup`, loaded with `my` off, was disabled with `dependency-unsatisfied: Dependency "my@claude-setup" is disabled — enable it or remove the dependency`. With `my` on, it loaded and its forced style applied. Enabling a method does not enable its dependencies: every switch writes their keys too.

**Spike 2** (forced style, reload, resume):

- Two forced styles: the first plugin loaded wins, with no warning, in either order.
- A `--plugin-dir` plugin can be turned off with `"<name>@inline": false`.
- Plugin off plus `/reload-plugins`: the forced style goes (NONE). Plugin on plus reload: it comes back. A settings change without a reload changes nothing. Rules and plugins change together.
- Resume without the plugin: the session gets the current style (`plain`) with the new message; the old style stays only in history.
- Limit: the init event reports the `outputStyle` setting (`plain`), not the forced style. A check must ask the model or read the plugin list.

**Spike 3** (plugin cache): `claude plugin update my@claude-setup --scope user` (and `kit`) moved the cache from `163b6f8` to `da05a34` (`HEAD`), "Restart to apply changes". Committed changes only; running sessions keep their version until they restart.

## Open for brainstorming

- Keeping rules fresh: run `claude plugin update` after each commit (a git hook in `global/git-hooks/`), turn on marketplace auto-update, or load `--plugin-dir` in claude-setup itself. Uncommitted rule edits reach no session in any of these.
- The dependency keys: `claude-method` and `kit:method` read `dependencies` from the method's `plugin.json` at run time, so the plugin list has one owner. How they find the installed `plugin.json`.
- `superpowers@synced` is in another marketplace: the `superpowers` method plugin needs the cross-marketplace allowlist, or the user enables `superpowers` once at the same scope.
- `docs-layout.md` and `plan-format.md`: fold into the `my` style (about 3,300 tokens more per `my` session, the Decision), or keep them as global rule files that every other method excludes with `claudeMdExcludes`.
- The core's development rules (LSP, commits, engineering standards): stay in the core, or move into the development methods so a non-coding session starts bare (point a).
- `plain` into the core: the exact text, and the line in `global/CLAUDE.md` that now points at the style.
- `keep-coding-instructions` per method: `false` for `tutor` and other non-coding methods.
- Switching away leaves the old method's dependencies on. A `my` directory holds `my@claude-setup` and `superpowers@synced` as separate keys (spike 1), so `claude-method tutor` or `kit:method tutor` that turns only `my` off leaves `superpowers` and its start-up hook in a tutor session. A switch must turn off every other method's dependencies, except the chosen method's own. Open: what happens to a plugin the user enabled by name on purpose that is also another method's dependency.
- Two method plugins on at once: the first loaded wins silently. A check at session start, or only the overlap audit.
- The overlap audit (point c): what counts as an overlap, where it runs, and its own roadmap row. `skillOverrides` does not affect plugin skills, so for plugin skills the unit is the whole plugin.
- The name `claude-method`, how `my:handoff` passes the method on to the sessions it starts, and how a resume should be typed.
- The bare user scope: which plugins stay on, and the claude.ai MCP connectors that `enabledPlugins` cannot turn off.
- Migration: 10 repos and 1 worktree lose their import line and plugin keys; `method-guard.py`, `global/methods/` and `/kit:setup` change or retire; row 69 (shared skills to `kit`) and the `tutor` skill's new home.

## Appendix: candidate drafts

### Candidate A

#### Summary

Shape: simplest design. Claude Code is the only process. Its own settings files (user, project, local, and the `--settings` flag) are the only data store. Each method is one plugin in the claude-setup marketplace (`"category": "method"`). Its rules ship as a plugin output style with `force-for-plugin: true`, and the plugins it needs are listed in `plugin.json` `dependencies`. Turning the plugin on puts the rules into the system prompt at launch, with no model decision. Choosing a method means writing `enabledPlugins` keys at the right scope: the directory default goes in project settings; a kept or mid-session switch goes in local settings followed by `/reload-plugins`; an "afternoon" switch uses `--settings` on the command line, built by one script with no state of its own. The user asked whether switching could itself be a plugin or skill. Answer: the method is a plugin, and switching is a settings write.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Method plugin (`my`, `tutor`, `superpowers`, a bundle on `superpowers@synced`; `plain` means no method plugin) | Bundles the rules (style, `force-for-plugin`; `keep-coding-instructions: false` for non-coding methods) and the plugin set (`dependencies`) | The method's rules and plugin list | Plugin folder |
| User settings | Turn every method plugin and heavy plugin off; leave only `kit` and the LSPs on; set no `outputStyle` | What a bare session loads | Settings file |
| Project settings `.claude/settings.json` | The directory's default method | The default method | Committed settings file |
| Local settings `.claude/settings.local.json` | Kept or mid-session switch, and loading or unloading single plugins by name | The directory's current override | Uncommitted settings file |
| `claude-method <m> [args]` | Builds `--settings` JSON (chosen method and its dependency keys on, every other method off) and runs `exec claude` | none | Script, about 15 lines |
| `kit:method <m> [--project]` | Runs `claude plugin enable/disable --scope local` (or writes project scope), then tells the user to submit `/reload-plugins` | none | Skill |
| `kit:skill-overlap` | Lists skills that clash in name or description within the enabled set; flags two method plugins on at once | none | Read-only script, also run as a unit test per method |
| Core `global/CLAUDE.md` | Takes in `plain`'s 2.4k chars, because only one style can be active per session | The core rules | Memory file |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| Claude Code → user, project and local settings | Merged `enabledPlugins` at launch and on reload | sync | Unreadable file: Claude Code reports it; the session starts bare |
| `claude-method` → `claude` | `exec` with one `--settings` JSON | sync | Unknown method: list the methods, exit 1 |
| `kit:method` → local settings | `claude plugin enable/disable --scope local` | sync | Command fails: the skill shows the error; nothing has changed |
| User → Claude Code | `/reload-plugins` | sync | Not submitted: the old plugins stay loaded until the next launch |
| Claude Code → method plugin | Its forced style goes into the system prompt; its dependencies load | sync | A dependency is off or missing: the plugin is disabled at load, with an error |
| `my:handoff` → new session | `claude-method my -n <name> …` | sync | Script missing: print the command |
| `kit:skill-overlap` → `claude plugin details` | Skill names and descriptions | sync | Prints a warning; never blocks |

#### Forces

Served:

- 1 (Load): no writes at launch. Writes to local settings are rare and made by a person.
- 2 (Growth): a new method is one plugin entry in the marketplace, with no edit to any project.
- 3 (Switch effort): one command for each kind of switch. Names are found through `/plugin` and `claude-method` with no argument.
- 4 (In force): the style is forced into the system prompt at launch, so no skill call is needed. A bare session loads no method.
- 5 (Consistency): `--settings` applies to one process only. A local write applies to the whole directory, which the force allows.
- 9 (Cost): a bare session loads only `kit` and the LSPs.
- 10 (Fixed constraints): every mechanism used is documented: `force-for-plugin`, `dependencies`, `--settings`, `--scope local`, `/reload-plugins`.

Sacrificed:

- 4 and 9 for `my`: `docs-layout.md` and `plan-format.md` fold into the `my` style, because a plugin cannot ship `rules/`. They then load always in `my` sessions instead of only when a `docs/plans/` file is read. That costs about 13k chars.
- a, partly ("starts bare"): the core `CLAUDE.md` still holds about 2.5k chars of development rules (LSP, commits, engineering standards). Moving them into each development style would mean keeping copies in several places.
- d, partly: `skillOverrides` does not affect plugin skills, so the smallest unit you can load or unload is a whole plugin.
- 5, partly: after a mid-session switch, the old style's text stays in the history (test 24). With 3 or more sessions in one checkout, a local switch moves all of them; the last write to `settings.local.json` wins.

#### Hard-to-reverse decisions

- Removing the import lines and `enabledPlugins` blocks from 10 repos and 1 worktree, and replacing them with one method key per project.
- Retiring `method-guard.py`, `global/methods/`, and today's `/kit:setup`.
- Method rules become output styles. Every method then competes for the one style slot, and `plain` stops being a style.

#### Numbers it depends on

- `my` style about 44k chars (30,937 + 11,410 + 1,686), compared with 154,808 chars loaded whole in test 18.
- More than 8 methods: one `false` key each in the `--settings` JSON. That is trivial.
- Bare session skill listings drop well below today's 142 skills (about 10k tokens). Some of the roughly 30k tokens of MCP tool names may come from claude.ai connectors, which `enabledPlugins` cannot turn off. I do not claim that cost goes away.
- More than 6 sessions with no shared writes at launch.

#### Weakest point

The design rests on two harness behaviours that are documented but have not been tested here.

1. **Do dependencies turn on by themselves?** The docs say that installing a bundle installs its dependencies, and that a dependent plugin is disabled when a dependency is off. They do not say that turning a method on also turns its dependencies on. So `claude-method` and `kit:method` copy the dependency keys from `plugin.json`. That makes a second copy of the plugin list, which can drift. Status: assumed.
2. **Does `force-for-plugin` apply after `/reload-plugins`, and on resume?** Status: untested. A bare resume of a session switched for one afternoon keeps its saved prompt but reloads the directory's default plugins (tests 5, 11, 15). That session then has rules from one method and plugins from another, with nothing to warn. "First loaded wins" also hides two method plugins that are on at once; only the overlap audit catches it.

`superpowers@synced` comes from another marketplace, so the bundle needs that marketplace on its cross-marketplace allowlist.

### Candidate B

#### Summary

Shape: separate deployables, each owning its own data. Each method is its own plugin in the `claude-setup` marketplace: `my`, `tutor`, and a thin `sp` wrapper for the superpowers workflow (superpowers is third-party, so no files can be added to it). The `plain` method gets no plugin, so a bare session is the `plain` method. A method plugin owns three things: its rules, shipped as `output-styles/<m>.md` (the only plugin channel that reaches the system prompt at launch with no model decision); its plugin set, through `dependencies` in `plugin.json`; and its own skills and hooks. Choosing a method always means setting the same two keys, `enabledPlugins["<m>@claude-setup"]` and `outputStyle: "<m>:<m>"`. Only the place they are written changes: project settings for a directory default, `--settings` for one session, or `settings.local.json` for a switch during a session that is kept.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Method plugin `my` | The strict dev workflow | Its rules (`output-styles/my.md`, about 31k chars), its dependencies (`superpowers`), its skills, agents and hooks, and its rule skills `my:docs-layout` and `my:plan-format` (the former path-scoped rule files) | Plugin, cached by commit hash |
| Method plugin `tutor` | Learning work | Its style (with `keep-coding-instructions: false`) and the tutor skill, which moves here from `kit` | Plugin |
| Method plugin `sp` | Superpowers without the `my` layer | A short style and `dependencies: ["superpowers"]` | Plugin |
| Marketplace `marketplace.json` | Registry of methods | Which plugins are methods (`category: "method"`) | File |
| Core `global/CLAUDE.md` | Rules for every session | Core rules, plus the `plain` readability rules, which move in here because a session has only one style | User memory file |
| `kit` (user scope, always on) | Neutral tools | `kit:method` and `kit:overlap` (new), the guard, and `kit:setup` (changed) | Plugin |
| Directory settings | The default method | The two keys | `.claude/settings.json` |
| `cm <m> [args]` | Switch for one session | none (builds its JSON from the marketplace) | Client script, about 15 lines, not named `claude` |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| Bare `claude` → directory settings | The two keys | sync | No keys: bare session, core rules only |
| `cm` → `claude` | `--settings '{enabledPlugins: chosen on, other methods off; outputStyle}'` | sync | Unknown name: list the methods, exit 1 |
| Method plugin → its dependencies | Enables them on load | sync | A dependency is missing: Claude Code reports it, and the rules still load |
| `kit:method <m>` → `claude plugin enable/disable --scope local` and `outputStyle` in `settings.local.json` | Kept switch | async: the style applies next turn, the plugins only after the user submits `/reload-plugins` | The user does not reload: new rules run with old plugins; the guard warns |
| Resume → session | The recorded system prompt (the old style), plus the plugins of the directory default | sync | Split after a one-session switch: `cm <m> --resume <id>` relaunches with the same flags |
| `my:handoff` → new `claude` | It copies the `--settings` value from `ps`, as it already copies `--plugin-dir` | sync | Value missing: the stage starts in the directory default |
| Guard (SessionStart) → settings and marketplace | Checks that at most one method plugin is on and that it matches the style's plugin prefix | sync | Warns, exits 0 |
| `kit:overlap <m>` → `claude plugin details` | Each plugin in the method's closure | sync | A detail call fails: report that plugin as unchecked |

#### Forces

Served:

- 2 (many methods): adding a method means adding one plugin folder and one marketplace entry. No shared methods folder grows.
- 4 (method in force): the directory keys load the style into the system prompt from the first turn, with no model decision. With no keys, the session is bare.
- 5 (consistency): a method's rules, plugins and skills ship together in one unit. A launch switch changes only that process.
- 9 (cost) and point b: user scope enables only `kit` and the language servers. Each method pulls in its own set. The overlap audit (point c) runs per method closure, because the method is the unit of loading.
- Point e: a method plugin can be strict (`my`) or loose (`sp`).
- 3 (effort to switch): `cm tutor`, or `/kit:method tutor` plus `/reload-plugins`. Plugin and skill names come from the harness's own `/plugin` menu and autocomplete.

Sacrificed:

- 8 (rate of change): rules are no longer live files. See Weakest point.
- 5, during a session: a kept switch applies to every session in the directory (test 27). Until the user reloads, the rules and the plugins disagree.
- Free choice of output style: inside a method, the style slot is taken by that method's rules.

#### Hard-to-reverse decisions

- Rules travel as output styles. `plain` moves into the core, which ends today's split where `plain.md` owns readability and `CLAUDE.md` holds only a fallback line.
- `docs-layout.md` and `plan-format.md` become skills of `my`. They load when the model calls them, not when a `docs/plans/` file is touched.
- The import lines leave 10 repos and 1 worktree. In their place, `<m>@claude-setup` and `<m>:<m>` are written into each repo's settings.
- A method's identity is its plugin name in this marketplace. A third-party method needs a wrapper plugin here.

#### Numbers it depends on

- `my` style: about 31k chars of rules. That is well under the 154,808 chars loaded whole in test 18. The rule skills add about 13k chars, on demand.
- `plain` adds 2,412 chars to the core for every session.
- More than 8 methods means more than 8 entries in one marketplace. Each commit gives every plugin a new version.
- `installed_plugins.json` today: the `claude-setup` plugins are pinned to commit `163b6f8` (updated 2026-10-16), while HEAD is `da05a34`.
- More than 6 sessions, 3 in one checkout: a kept switch reaches all 3.

#### Weakest point

This design turns live rules into a cached snapshot. Today `my.md` is a symlink, so an edit applies to the next session that starts. Under this design, the rules live in a plugin that Claude Code copies into a cache by commit hash, and the cache is already 4 days and several commits behind HEAD. Every rules edit would then need a commit plus `claude plugin update`, or a `--plugin-dir` on every launch. Force 8 says rules change often. So the main thing this design improves is also the thing the user edits most, and it gets harder to edit.

Second, the design leans on an **assumed** behaviour. It needs disabling a method plugin to also turn off the plugins it pulled in through `dependencies`, with `superpowers` the main case. This is not tested. `claude plugin disable --help` does not settle it. If dependencies stay on, then `sp` → `tutor` leaves `superpowers` loaded. `cm` would then have to turn off every other method's dependencies by name, and the plugin would no longer fully own its plugin set.

Third, the lazy rule files lose their trigger. A path match becomes a model choice.

Fourth, rules carried in the output style make the resume split visible: the old rules come back with the default's plugins.

### Candidate C

#### Summary

Shape: pipeline or batch processing. Each method has one source: its rules file, plus a small manifest naming its plugins, its `keep-coding-instructions` value and the path-scoped rule files it keeps. A build script, run by the repo's pre-commit hook and on demand, compiles every manifest into three outputs per method: a merged output style (the method's rules plus `plain`), a settings fragment (`outputStyle`, every plugin listed on or off, and `claudeMdExcludes`) and a generated user command. One build also writes the overlap report and a shell completion file. The outputs go into folders that are already live symlinks into the repo (`~/.claude/output-styles`, `~/.claude/methods`), not into a plugin, so a build takes effect with no plugin update. That matters because `~/.claude/plugins/cache/claude-setup/` holds copies. Sessions only consume finished files. Nothing in this design asks the model to decide which method is in force.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Method sources `global/methods/<m>.md` + `<m>.method.json` | Rules and the bundle definition | The truth for every method | Committed files |
| `global/methods/build.py` | Validate manifests, merge each style with `plain.md`, emit fragments, commands, completion, overlap report, source hash | none (pure function of sources plus the installed plugin list) | Batch script (pre-commit, manual) |
| Built outputs: `global/output-styles/m-<m>.md`, `global/methods/build/<m>.settings.json`, `base.settings.json`, `overlap.md`, `completion.bash`, `stamp` | What sessions load | Derived only (gitignored, rebuilt) | Files |
| Generated user commands `~/.claude/skills/method-<m>/` (`disable-model-invocation: true`) | Mid-session switch: copy the fragment into `.claude/settings.local.json`, then tell the user to submit `/reload-plugins` | none | Skill |
| `cm <m> [args]` shell function | One-session switch: `CLAUDE_METHOD=<m> claude --settings …/build/<m>.settings.json "$@"` | none | Client (shell, tmux) |
| Directory default | The project's committed `.claude/settings.json`, holding the fragment's keys | The project's default method | Committed file |
| Stale-bundle hook (replaces `method-guard.py`) | At session start, compare `stamp` with the source hash, and the project keys with the fragment named by its `outputStyle` | none | SessionStart hook |
| Overlap audit, live mode (`build.py --audit-live`) | Audit the plugins enabled right now after an ad-hoc load or unload | none | On-demand script |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| pre-commit → `build.py` | Changed source paths | sync | Bad manifest or a new unallowed overlap: block the commit (bypass with `--no-verify`) |
| `build.py` → output folders | Files written to a temp path, then renamed | sync | Old outputs stay in place; `stamp` stays old, so the hook warns |
| `build.py` → `claude plugin details` / plugin folders | Skill names, descriptions, token cost | sync | Format changed: audit marks itself incomplete, build still emits bundles |
| `cm` → `claude` | `--settings` path, `CLAUDE_METHOD` env | sync | Unknown method: list methods from completion file, exit 1 |
| `my:handoff` → new `claude` | Same `--settings` path, read from `CLAUDE_METHOD` | sync | Variable unset: stage starts on directory default (stated in the launch line) |
| `/method-<m>` → `settings.local.json` | Fragment keys | sync | Write fails: report; style applies next turn, plugins after `/reload-plugins` |
| Hook → session | Warning text under 2,000 chars | sync | Fails open |

#### Forces

Served:

- 8 (rate of change): a rules edit lands in every bundle at the next commit. A new method is one manifest. `plain` is merged into each style by the build, never by hand.
- 9 (cost): the base fragment keeps a bare session to kit plus the LSPs. The build measures each bundle's listing cost, and the report shows overlaps before any session pays for them.
- 4 (availability): a directory default is a committed settings file holding a style name and plugin keys. Both are in force from turn one, with no model decision. A directory with no settings starts on the base fragment.
- 3 (effort): `cm tutor` for one session, `/method-tutor` (autocompleted) to keep a switch. Both are generated, so no file is edited by hand.
- 5 (consistency at launch): rules and plugins come from one fragment, so they cannot disagree. `--settings` is session-scoped.
- 2 (growth): one manifest per method, and every output scales linearly.

Sacrificed:

- 5 on resume: a session started with `cm tutor` resumes with the tutor style it saved but the directory's plugins (tests 5, 11, 15).
- 8 (Claude Code's own rate of change): the audit parses harness output that may change every few days.
- Point d, partly: ad-hoc loads bypass the pipeline. The live audit runs only when the user asks for it.
- Simplicity: one more moving part (a build) and one more kind of failure (outputs that no longer match their sources).

#### Hard-to-reverse decisions

- Method rules travel as an output style, not as a `CLAUDE.md` import. Every project's import line goes away, and `plain` stops being a separate user-scope style.
- Project defaults become copies of build outputs in committed `.claude/settings.json` across 10 repos, so a manifest change means re-copying them (the hook detects this).
- The manifest format becomes the contract every future method author writes to.

#### Numbers it depends on

- Merged `my` style: `my.md` 30,937 + `plain.md` 2,412 = about 33,300 chars, against 154,808 loaded whole (test 18).
- `docs-layout.md` + `plan-format.md` = about 13,100 chars, kept path-scoped. If they had to be folded into the style instead, it would grow to about 46,400 chars, still under the tested limit.
- Build time: 8 to 20 manifests and about 150 skill descriptions. Under 2 s, so it is acceptable in pre-commit.
- More than 6 live sessions: a rebuild touches files they read. The atomic rename keeps readers safe, but whether a running session picks up rewritten style text is untested (test 27 covered a key change only).
- Hook output under 2,000 chars, against the 10,000-char cap.

#### Weakest point

The outputs are a cache, and every cache needs a way to know when it is stale. Pre-commit covers commits. An uncommitted edit, a plugin update or a Claude Code update leaves bundles stale until the hook warns, and the hook only warns; it does not fix. The ad-hoc path (point d) cannot be covered at all: what the user loads by hand never passes through the build, so the build-time audit serves point c only for named methods.

The design also rests on two untested behaviours:

1. **How `claudeMdExcludes` merges across scopes.** The base fragment must exclude `docs-layout.md` and `plan-format.md`, and the `my` fragment must bring them back. That works only if `--settings` replaces the array. Test 4 covered an object key, not an array. Run this test first. If the arrays concatenate instead, fold the 13,100 chars into the `my` style and pay that token cost in every `my` session.
2. **Whether running sessions see a rewritten style file.**

The audit also has a limit. `skillOverrides` does not affect plugin skills, so the audit can only recommend dropping whole plugins. For example, the two `product-management` brainstorm skills go only if the whole plugin goes.

Last, the resume split is unchanged from today, and the pipeline does nothing to fix it.

### Candidate D

No new draft. The 2026-10-18 brief holds D's Summary, Components and Connections (section "Candidate D") and its evaluation.
