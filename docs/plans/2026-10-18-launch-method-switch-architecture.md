# Architecture brief: launch method switch

**Status:** superseded, 2026-10-20. Its Decision (candidate D, a launcher named `claude`) is replaced by candidate A in `docs/plans/2026-10-20-method-bundles-architecture.md`; its forces and flag tests 1–16 still hold as evidence.

## How to read this brief

1. This brief.
2. `docs/plans/2026-10-12-swappable-methods-architecture.md`: the brief this one partly replaces. Its "Switch", "Always-on rules of our method", "Guard" and "Setup" Decision bullets are replaced here. Its "Packaging" and "Neutral core" bullets stay. Its "Lazy rules" bullet changes: the gate becomes a settings exclude.
3. `global/methods/my.md` and `global/methods/tutor.md` (symlinked as `~/.claude/methods/`): the method files.
4. `plugins/kit/skills/setup/SKILL.md`: today's two-part switch, written per project.
5. `plugins/kit/hooks/method-guard.py` and `plugins/kit/hooks/hooks.json`: the guard that checks the two parts agree.
6. `global/rules/docs-layout.md` and `global/rules/plan-format.md`: path-scoped rules whose first line gates them on the import line.
7. `plugins/my/skills/handoff/SKILL.md` (line 318 on): how `my:handoff` starts new sessions.

The spec written next lists this brief first in its own "How to read this spec".

The description, in the user's words: "Method switch at launch. Replace the per-project committed switch (import line in CLAUDE.md + enabledPlugins in .claude/settings.json + method guard) with a per-session switch chosen when claude starts: a wrapper passes --append-system-prompt-file <method file> and --settings with enabledPlugins. A project keeps only a default method as one fact. Must allow switching method for one session (an afternoon). Methods in scope: my, tutor, superpowers (superpowers workflow without the my layer), plain (core only). Builds on and partly supersedes docs/plans/2026-10-12-swappable-methods-architecture.md. Out of scope: the size table (another session is removing it; it edits global/methods/my.md and merges first), and moving design-system/roadmap/changelog skills to kit (separate Medium row)."

The flag tests behind force 10 and the evaluation are copied in full under "Reversibility and checks".

## Forces

The standard forces were written for server systems. Each is mapped onto an instruction system; the mapping is in the Force column.

| # | Force | Value | Label | Source or reason |
| --- | --- | --- | --- | --- |
| 1 | Load | More than 6 Claude sessions at once (tmux windows, `my:handoff` stages, parallel auto runs). 10 repos import a method today (9 `my`, 1 `tutor`), plus 1 worktree. | stated | User answer; `grep` for `@~/.claude/methods/` in every `CLAUDE.md` under `~` |
| 2 | Data volume and growth | Many methods over time (more than 8). Today: `my.md` 26,958 chars, `tutor.md` about 1,000; `docs-layout.md` + `plan-format.md` about 12,000 more, loaded when a `docs/plans/` file is touched. | stated | User answer; `wc -c` |
| 3 | Latency target (here: the effort to switch) | Switching method for one session takes one command: no file edit, no commit, no new approval. | stated | User: "possible to switch to another method for an afternoon", "simplify it" |
| 4 | Availability (here: the method is in force) | Deterministic: rules and plugins load without the model deciding to invoke anything. Sessions that must carry a method start from the terminal (tmux) only; IDE, desktop, web and resume were not chosen. | stated | User answer; 2026-10-12 brief force 4 |
| 5 | Consistency | Each rule has one source. Within one session, the rules and the plugins belong to the same method. | stated | 2026-10-12 brief force 5; flag tests 5 and 15 show resume can split them |
| 6 | Security and compliance | Nothing beyond the existing hooks, such as `block-autorun-push.py` | inferred | `plugins/my/hooks/hooks.json` |
| 7 | Team and operations | One developer | stated | `~/.claude/methods/my.md`: "I am the sole developer" |
| 8 | Rate of change | Rules change often; methods are added, and now switched per session. | stated | User messages; 2026-10-12 brief force 8 |
| 9 | Cost | unknown, assumed: tokens per session matter somewhat, money does not | assumed | No statement |
| 10 | Fixed constraints | A bare `claude` (no wrapper) must load the project's default method; the wrapper is needed only to switch. Tested on Claude Code 2.1.302: `--append-system-prompt-file` loads a file whole (tested to 134,837 chars); `--settings` `enabledPlugins` merges per key and wins over project settings in both directions; `--settings` can set `outputStyle`; resume reuses the saved system prompt and ignores the flag, but plugins come from the new launch; `claudeMdExcludes` in `--settings` skips an imported file (path as written, `~` expanded, globs allowed) and a rule file in `~/.claude/rules/`; an `appendSystemPrompt` setting does nothing. Hook text is capped at 10,000 chars per string. Outside `@` imports need approval once per project. Plugins cannot ship `CLAUDE.md`. Superpowers is third-party. Subagents read no `CLAUDE.md`. `my:handoff` starts sessions with `claude -n <name> <plugin-dir flags> <mode flag> …`. `~/.local/bin` is first in `PATH`, and the installer rewrites `~/.local/bin/claude` on every update. | stated | User answer; flag tests 1–16 below; 2026-10-12 brief force 10; `plugins/my/skills/handoff/SKILL.md:318` |

## Collapse gate

Three candidates. Force 1 (one machine) and force 7 (one developer) would allow one. But force 4 asks for deterministic loading, the instruction-system equivalent of a strict uptime target, and force 10 needs two ways in (a bare `claude` and the switch) that must agree.

Skipped shapes:

- Queue and background workers: would need slow work to move off the launch; there is none.
- Pipeline or batch processing: would suit a build step that compiles method files (force 8); nothing needs compiling.
- Client-heavy or offline-first: would need a remote server; there is none.
- Managed or serverless services: would need entry points outside the terminal; force 4 allows the terminal only.

## Candidates

### Candidate A: simplest design

**Reason:** Always included: the simplest design that could meet the forces.
**Contrast:** vs B: data ownership differs (B keeps a session record); vs C: data ownership and processes differ (C adds a log and a hook). Both pairs pass before dispatch.
**Labels:** none

#### Summary

A bare `claude` loads the project's default exactly as today: the import line brings in the rules, and project `enabledPlugins` turns on the plugins. To switch, `claude-as <method> [claude args…]` runs `exec claude --settings ~/.claude/methods/<m>.settings.json [--append-system-prompt-file ~/.claude/methods/<m>.md] "$@"`. It reads nothing and writes nothing. Each static settings file sets every method plugin on or off and lists every method import in `claudeMdExcludes`. `my:handoff` copies the two flag pairs from `ps`.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Methods folder `global/methods/` | One `<m>.md` (optional) and one `<m>.settings.json` per method | The rules and plugin set of every method | Files |
| `claude-as` | Turns a method name into two path flags, then execs `claude` | none | Client script, about 10 lines |
| Project import line + `enabledPlugins` | The default method for a bare `claude` | The project's default | Committed files |
| `/kit:setup <m>` | Writes the import line, copies `enabledPlugins` from the settings file | none | Skill |
| Slim method guard | Checks the committed files agree; never reads flags | none | Hook |
| `my:handoff` launch step | Copies the two flag pairs from `ps` | none | Skill text |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| User or tmux → `claude-as` | Method name plus claude args | sync | Unknown method: list methods, exit 1 |
| `claude-as` → `claude` | `exec` with two file paths | sync | Claude Code reports an unreadable file |
| `claude` → project files | `CLAUDE.md` minus excluded imports | sync | A non-canonical import escapes the exclude: two methods load |
| `my:handoff` → new `claude` | Copied flag pairs | sync | Missing pairs: the stage starts in the default method, silently |
| Guard → project files | Two committed files | sync | Fails open with a warning |

### Candidate B: separate deployables, each owning its own data

**Reason:** Force 2 (many methods) and force 5 (one method's rules and plugins agree): each method ships as its own unit that owns its rules and its plugin set.
**Contrast:** vs A: data ownership only, after return; vs C: data ownership only, after return.
**Labels:** near-copy of candidate A

#### Summary

Each method is one package: `global/methods/<name>.md` and `<name>.json` (its `--settings` piece). A generic wrapper, `claude-method <name>`, lists the packages, passes the chosen pair as flags, and writes a session record in that method's state folder. A bare `claude` loads the default through the import line plus plugin keys copied from the package and checked by the guard.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Method package (`<name>.md` + `<name>.json`) | Defines one method | Its rules text and plugin set | Files |
| `claude-method` wrapper | Starts a session on a chosen method | none | Script on PATH |
| Session record (`$XDG_STATE_HOME/claude-method/<name>/<uuid>`) | Which method a session started with | Active method, per session | Write-once file |
| Project import line | Default method for a bare `claude` | The project's default | Memory file |
| Project `enabledPlugins` | Default's plugins | none: a copy | Settings file |
| Generic guard | Finds drift and splits | none | Hook |
| Generic `/kit:setup <name>` | Writes the import line, copies plugin keys | none | Skill |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| Wrapper → packages | Lists and reads the pair | sync | Unknown name: list names, exit 1 |
| Wrapper → `claude` | Rules file, settings (chosen keys on, others off, default import excluded), `--session-id`, `CLAUDE_METHOD` | sync | Chosen equals default: only the session ID |
| Wrapper → session record | Method and uuid | sync | Warns, still starts |
| `claude-method resume <id>` → `claude --resume` | Method from the record, plugin flags again | sync | No record: resumes bare, warns |
| Guard → record, packages, project settings | Bare resume of a switched session; drifted keys | sync | Warns, exits 0 |
| `my:handoff` → wrapper | `claude-method my -- -n <name> …` | sync | Wrapper missing: prints the command |

### Candidate C: event-driven

**Reason:** Force 4 (deterministic, terminal only) and force 10 (resume keeps the system prompt but drops flag plugins): session events carry the method choice, so every way a session starts reacts the same way.
**Contrast:** vs A: data ownership only, after return; vs B: data ownership only, after return.
**Labels:** near-copy of candidate A

#### Summary

Every session start produces one method event `{method, origin, session_id}`, with origin `launch`, `default` or `ledger`. Hooks carry only the method's name, never its rules. Rules reach the model through the import (bare `claude`) or the flag (launcher `cm`). Each part reads the method from the event line or `CLAUDE_METHOD`, never from the import line.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Launcher `cm` | `cm <method>` → `claude` with the flags and `CLAUDE_METHOD`; `cm resume <id>` | none | Client script |
| Method manifest `methods.json` | Maps each method to rules file and plugin map | Which plugins and rules make up each method | File |
| Method files `<m>.md` | Always-on rules | Rule text | Files |
| Project import line | Default method for a bare `claude` | The project's default | Line in `CLAUDE.md` |
| Project `enabledPlugins` | Default's plugins | none: generated by setup | Settings file |
| SessionStart router | Appends the event to the log, prints "Active method: X", checks drift and splits | none | Hook |
| Session ledger `method-ledger.jsonl` | Append-only log of method events | Which method each session started with | File |
| `my:handoff` | Starts stages as `cm $CLAUDE_METHOD -n …` | none | Skill |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| `cm` → manifest | File read | sync | Unknown method: error, no start |
| `cm` → Claude Code | Flags plus env | sync | Rejected flag: session never starts |
| Claude Code → router | Hook JSON | sync | Crash: rules and plugins still loaded; only the line and log entry are lost |
| Router → ledger | One line, about 150 bytes | sync | Warn, carry on |
| Lazy rules → event line | The model reads the gate | sync | Line missing: rule ignored |
| `my:handoff` → `cm` | Command line in `tmux new-window` | sync | `cm` missing: prints the command |

### Candidate D: launcher named `claude`

**Reason:** Raised during evaluation, no subagent draft. The description's "A project keeps only a default method as one fact" is met by none of A, B or C. D meets it by making the command the user types the loader.
**Contrast:** vs A, B and C: data ownership (the default is one line, not an import plus copied plugin keys) and processes (the launcher replaces the bare binary on `PATH`).
**Labels:** none

#### Summary

A script named `claude` sits in its own folder, placed before `~/.local/bin` in `PATH` in both the shell and tmux. It reads the method from `CLAUDE_METHOD` if set, else from the project's one line naming its default method. Then it execs the real `~/.local/bin/claude` with `--append-system-prompt-file <m>.md` and `--settings <m>.settings.json`, and exports `CLAUDE_METHOD`. Subcommands such as `claude update`, `claude mcp` and `--version` pass through with no flags added. Projects keep no import line and no plugin keys, so no guard is needed.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Methods folder `global/methods/` | One `<m>.md` (optional for `plain`) and one `<m>.settings.json` per method: `enabledPlugins`, `outputStyle` where the method has one, and `claudeMdExcludes` for `docs-layout.md` and `plan-format.md` in every method but `my` | The rules and plugin set of every method | Files |
| Project method line | Names the project's default method | The project's default | One committed line |
| Launcher `claude` (own folder, first in `PATH`) | Picks the method, execs the real `claude` with the two flags, exports `CLAUDE_METHOD`; passes subcommands through | none | Client script |
| Session-start check (kit) | Warns when `CLAUDE_METHOD` is unset, so the session started without the launcher | none | Hook |
| `/kit:setup <m>` | Writes the method line; removes the old import line and plugin keys | none | Skill |
| `my:handoff` | Passes `CLAUDE_METHOD=<m>` inline, as it passes `MY_AUTORUN` today | none | Skill text |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| Shell or tmux → launcher | Args plus env | sync | Launcher not first in `PATH`: the real `claude` runs with no method; the session-start check warns |
| Launcher → project method line | One line read | sync | No line: core only (`plain`), and the launcher says so |
| Launcher → methods folder | Reads the pair | sync | Unknown method: list methods, exit 1, start nothing |
| Launcher → real `claude` | `exec` with two flags and `CLAUDE_METHOD` | sync | A flag rejected after an update: the session does not start, visibly |
| Bare `claude --resume` → launcher | Same path; method from env or project line | sync | Resuming a switched session without `CLAUDE_METHOD`: switched rules (saved prompt) with default plugins, silently |
| `my:handoff` → launcher | `CLAUDE_METHOD=<m> claude -n <name> …` | sync | Env missing: the stage starts in the project default |
| A process inside a session → launcher | A `claude` started from the Bash tool, a `!` command or a test's `claude -p` inherits `CLAUDE_METHOD` | sync | It gets the parent session's method, not the target project's default |

## Evaluation

Shared facts first. The tests run after dispatch (9–16 below) answer items all three drafts listed as unverified: globs work, `outputStyle` works, rule files can be excluded, resume adds no second copy, and plugin keys merge. They change every candidate the same way:

- **Lazy rules can be gated without the model.** Each non-`my` method's settings exclude `docs-layout.md` and `plan-format.md` by name. A glob such as `rules/*.md` would also drop `markdown.md` and `python.md`. All three drafts listed the model-read gate as sacrificed; that cost goes away. Projects with no method keep the "Applies only…" sentence as a fallback, reworded so it does not depend on an import line.
- **Resume freezes the rules.** A resumed session keeps its saved system prompt. Only the plugins follow the new launch.

### Data ownership

| State | A | B | C | D |
|---|---|---|---|---|
| Rules of a method | `<m>.md` | `<name>.md` | `<m>.md` | `<m>.md` |
| Plugin set of a method | `<m>.settings.json`, **plus a copy in each project's `enabledPlugins`** | `<name>.json`, **plus a project copy** | `methods.json`, **plus a project copy** | `<m>.settings.json` only |
| Project default | Import line, **and the plugin copy, and today's `**Method:**` fact** | Same as A | Same as A | One method line |
| Active method of a session | **No owner** (only in flags) | Session record | Ledger | `CLAUDE_METHOD` in the process environment |

Flags: A, B and C keep the project default in more than one place; a guard keeps the copies in agreement. A gives the active method no owner, so nothing can detect a split.

### Scenarios

1. **Normal path at peak: 8 sessions, some switched, some `my:handoff` stages.** A holds, but a handoff stage that misses a copied flag starts in the default, silently. B holds (one record file per session). C holds (appends under 4,096 bytes are atomic). D holds; handoff passes `CLAUDE_METHOD` inline.
2. **External dependency fails: a Claude Code update changes an undocumented behaviour.** A, B and C break silently if exclude matching changes: a switched session loads two methods. D excludes no method file (there is no import line), only the two lazy rule files in non-`my` methods. If exclude matching changes, a non-`my` session silently gets `docs-layout.md` and `plan-format.md`, but never a second method. D breaks visibly if a flag is rejected. All four break silently if the resume snapshot changes. D also breaks if the installer starts warning about, or fixing, the `PATH` order.
3. **Most frequent change: edit `my.md`, or add a method.** All hold. Files are read at each launch; running sessions keep their snapshot. A new method is one file pair in A, B and D, and a manifest entry in C. A, B and D need no project edit.
4. **Data volume after 3 years: more than 8 methods, `my.md` much larger.** All hold. The flag loaded 134,837 chars (spike 1), five times today's `my.md`. C's ledger stays under 10 MB.
5. **Security: the push guard.** All hold. `block-autorun-push.py` runs with the `my` plugin; auto runs exist only under `my`, and `my:handoff` starts them in `my`.
6. **Bare resume of a switched session** (weighted low: force 4 leaves resume out). Test 15: in A, B and C the project default comes back, both rules and plugins, so a session switched to another method carries two methods. A is silent; B and C warn. In D the switched rules stay (saved prompt) with the default plugins, silently, and never two methods at once.

### Pre-mortem

A, failed one year on:

1. A Claude Code update changed how `claudeMdExcludes` matches paths; switched sessions loaded two methods for weeks.
2. Bare resumes of switched sessions mixed methods, and nothing recorded which method a session started with.
3. A method's plugin set changed and the project copies drifted; the guard's warning was ignored.

B, failed one year on:

1. The `resume` subcommand was forgotten; `claude --resume` was typed anyway.
2. Package files and project copies drifted.
3. The record folders and resume command cost upkeep for one rare case.

C, failed one year on:

1. The router, ledger and event line were kept up for one rare case.
2. The event line format and `CLAUDE_METHOD` hardened into a contract nobody wanted to change.
3. The router lived in `kit` and disappeared in any session that left `kit` out.

D, failed one year on:

1. The installer or a new shell setup put `~/.local/bin` first again; sessions ran with no method until the warning was noticed.
2. A new Claude Code subcommand got method flags added and failed.
3. The real `claude` was hidden, so a bug report or a doctor check described the launcher, not Claude Code.

The top cause shared by all four: each depends on behaviour Claude Code does not document. The binary updated itself on 2026-10-17.

### Comparison

| Force | A | B | C | D |
|---|---|---|---|---|
| 1 Load | meets: no shared writes | meets: write-once files | meets: atomic appends | meets: no shared writes |
| 2 Growth | meets: a file pair per method | meets | meets: a manifest entry | meets: a file pair per method |
| 3 Switch effort | meets | meets | meets | meets |
| 4 Deterministic | meets | meets | meets | partial: a session started outside the launcher gets no method; the check warns |
| 5 Consistency | partial: default in two places; silent split on bare resume | partial: same, warns | partial: same, warns | meets one fact; partial on bare resume, never two methods |
| 6 Security | meets | meets | meets | meets |
| 7 Team | meets: fewest parts | partial: records and a resume command | partial: hook, log and manifest | meets, but `PATH` must be set in the shell and tmux |
| 8 Rate of change | meets | meets | meets | meets |
| 9 Cost (assumed) | neutral | neutral | neutral | neutral |
| 10 Fixed constraints | meets: bare `claude` unchanged | meets | meets | partial: holds only if "bare `claude`" means typing `claude`; hides the real binary; subcommands must pass through |

## Decision

**Candidate D: a launcher named `claude`.** Chosen by the user. It is the only candidate that removes both committed switches and the guard, which is what the user asked for ("the switching mechanism sounds volatile and more complicated than it needs to be"). It is also less exposed to undocumented behaviour: it excludes only the two lazy rule files, never a method file, so a change in exclude matching cannot load two methods at once. It reads "a bare `claude` must load the project default" as "typing `claude`"; the user chose it with that reading in the option text.

Rejected:

- **A:** keeps the default in two committed places with a guard, the part the user wanted gone. Also exposed to exclude matching. The simpler choice if the real binary must not be hidden.
- **B:** adds a record and a resume command mainly to detect a bare resume, an entry point force 4 leaves out.
- **C:** adds a hook, a log and a manifest for the same case.

Replaces, in the 2026-10-12 brief: the "Switch", "Always-on rules of our method", "Guard" and "Setup" bullets. The "Lazy rules" gate becomes a settings exclude. "Packaging" and "Neutral core" stay.

Order: row 68 in `ROADMAP.md`, under `## Order of work`.

## Reversibility and checks

| Decision | Label | Check |
|---|---|---|
| The project default as one method line, replacing the import line and plugin keys in 10 repos and 1 worktree | hard | no quantity to check: a data format across repos; the migration is the cost |
| All method rules arrive through `--append-system-prompt-file` | hard | estimate 1 and spike 1 |
| `CLAUDE_METHOD` as the contract between the launcher, the session-start check and `my:handoff` | hard | no quantity to check: a contract between parts |
| Each method as a pair `<m>.md` + `<m>.settings.json` | hard | no quantity to check: a format the launcher and setup read |
| A launcher named `claude` in a folder before `~/.local/bin` | medium | no quantity to check; test 13 shows today's `PATH` order |
| Lazy rules gated by `claudeMdExcludes` in the method settings | medium | test 12 |
| The subcommand pass-through list | cheap | none |

Estimate 1, the method file against the largest tested size:

```python
"""Estimate: when does my.md outgrow the largest system-prompt file tested?

Inputs: the size of global/methods/my.md at each commit (git history), and the
largest file loaded whole through --append-system-prompt-file (flag test 1).
"""
import subprocess
from datetime import datetime

REPO = "/home/dchris/projects/claude-setup"
PATH = "global/methods/my.md"
TESTED = 27_006  # chars, flag test 1

log = subprocess.run(
    ["git", "-C", REPO, "log", "--format=%H %cI", "--", PATH],
    capture_output=True, text=True, check=True,
).stdout.split("\n")
points = []
for line in filter(None, log):
    sha, when = line.split()
    blob = subprocess.run(["git", "-C", REPO, "show", f"{sha}:{PATH}"],
                          capture_output=True, text=True)
    if blob.returncode == 0:
        points.append((datetime.fromisoformat(when), len(blob.stdout)))
points.sort()
first, last = points[0], points[-1]
days = max((last[0] - first[0]).total_seconds() / 86400, 1)
rate = (last[1] - first[1]) / days
print(f"commits measured: {len(points)}")
print(f"first: {first[0]:%Y-%m-%d} {first[1]:,} chars; last: {last[0]:%Y-%m-%d} {last[1]:,} chars")
print(f"growth: ({last[1]:,} - {first[1]:,}) / {days:.1f} days = {rate:,.0f} chars/day")
print(f"tested limit: {TESTED:,} chars; current / tested = {last[1] / TESTED:.2f}")
if rate > 0:
    print(f"days until 2x tested ({2 * TESTED:,}): {(2 * TESTED - last[1]) / rate:,.0f}")
```

```text
commits measured: 6
first: 2026-10-13 23,996 chars; last: 2026-10-16 26,857 chars
growth: (26,857 - 23,996) / 3.3 days = 878 chars/day
tested limit: 27,006 chars; current / tested = 0.99
days until 2x tested (54,012): 31
```

Near a limit, so spike 1 ran. **Spike 1 result:** a 134,837-char file (`my.md` five times, a codeword at the end) loaded whole through `--append-system-prompt-file`. The codeword came back in print mode and in an interactive tmux session. At 878 chars a day, `my.md` reaches that size in about 120 days; the growth rate was measured over 3 days of heavy editing, so the real time is probably longer.

Flag tests, Claude Code 2.1.302, 2026-10-18. Fixture: an empty folder unless named. Method file: `my.md` plus a codeword line (27,006 chars).

1. `claude -p --append-system-prompt-file method.md "Reply with only the codeword…"` → `PELICAN-7731`. The whole file loads; no 10,000-char cap.
2. `--settings '{"enabledPlugins":{"my@claude-setup":true,"superpowers@synced":true}}'` → the init event lists `my` and `superpowers`; skills include `my:architect`. With `false` or no flag: neither loads.
3. Interactive (tmux), both flags → `PELICAN-7731`; the slash menu listed `/my:architect (my)` and `/superpowers:brainstorming (superpowers)`.
4. In claude-setup, whose `.claude/settings.json` sets both keys `true`: flag `true` → both load; flag `false` → neither loads.
5. Session started with both flags, then `claude -p --resume <id>` with no flags → `PELICAN-7731`, `my` not loaded.
6. Fixture `CLAUDE.md` (fact ALPHA-11) importing `@./methodx.md` (BETA-22): baseline → both; `claudeMdExcludes` `<abs>/methodx.md` → ALPHA-11 only; `<abs>/CLAUDE.md` → NONE.
7. `--settings '{"appendSystemPrompt":"… GAMMA-33"}'` → GAMMA-33 absent. `--setting-sources user` → project `CLAUDE.md` not loaded.
8. In claude-setup (approved `@~/.claude/methods/my.md`): baseline → "Method: my" present; exclude `/home/dchris/.claude/methods/my.md` → method gone, Project facts kept; exclude the symlink target `/home/dchris/projects/claude-setup/global/methods/my.md` → method still present. In a fixture that never approved an outside import, `claude -p` skips it silently.
9. Globs: `["/home/dchris/.claude/methods/*.md"]` and `["**/.claude/methods/*.md"]` → "Method: my" absent in both.
10. `--settings '{"outputStyle":"tutor"}'` → init event `output_style: tutor` (default `plain`).
11. Session started with `method.md` (PELICAN-7731); `--resume <id>` with the same file → the sentence appears once; with a different file (HERON-4402) → only PELICAN-7731.
12. In claude-setup, after reading a `docs/plans/` file: baseline → "Where design documents live" present (twice); `claudeMdExcludes` `["/home/dchris/.claude/rules/*.md"]` → absent (twice).
13. `PATH` starts with `~/.local/bin`; `~/.local/bin/claude -> ~/.local/share/claude/versions/2.1.302`, rewritten on each update. tmux's global `PATH` also starts with it.
14. Test 2 named only `my` and `superpowers`, and `kit` and the other user-scope plugins still loaded: keys merge.
15. In claude-setup: session started with my.md excluded and both plugins `false`; bare `claude -p --resume <id>` → `my` plugin loaded, "Method: my" in context.
16. Spike 1, above.

## Open for brainstorming

- Force 9 (cost): unknown, assumed tokens per session matter somewhat.
- Where the one method line lives: a file such as `.claude/method`, or the `**Method:**` line already in each `## Project facts` block.
- How a switch is typed: `CLAUDE_METHOD=tutor claude`, a short alias, or a launcher option that the launcher strips before calling the real binary.
- The subcommand pass-through list, and how it stays current when Claude Code adds subcommands.
- The `PATH` setup: the launcher's folder, the shell files and the tmux environment, and whether the installer warns about the order.
- Whether headless `claude -p` runs, such as the skill tests, should get the project default through the launcher.
- `CLAUDE_METHOD` leaks into child processes: a `claude` started from inside a switched session (the Bash tool, a `!` command, a test's `claude -p` in a fixture) gets the parent's method. Decide whether the launcher clears it for children, or whether only an explicit switch sets it.
- What remains of row 48, folded into row 68: a one-line hint in a git repo that names no method, and a way to silence it for repos that should stay without one.
- A bare resume of a switched session: accept the silent split, or have the launcher refuse `--resume` without `CLAUDE_METHOD`.
- Turning the flag tests into a check to rerun after each Claude Code update.
- What the `superpowers` and `plain` method files hold, including the git rules that live in `my.md` today.
- Migrating the 10 repos and 1 worktree, and the wording of the "Applies only…" fallback sentence in the two rule files.

## Appendix: candidate drafts

### Candidate A

#### Summary

Shape: simplest design. A bare `claude` loads the project's default exactly as today: the import line `@~/.claude/methods/<m>.md` brings in the rules, and project `enabledPlugins` turns on the plugins. To switch, a new executable on PATH, `claude-as <method> [claude args…]`, runs `exec claude --settings ~/.claude/methods/<m>.settings.json [--append-system-prompt-file ~/.claude/methods/<m>.md] "$@"`. It reads nothing and writes nothing. Each static settings file sets every method plugin on or off and lists every method import in `claudeMdExcludes`. So the default method drops out whatever it is, and the chosen method comes in through the flag. `my:handoff` copies the two flag pairs from `ps`, the same way it already copies `--plugin-dir`, so each stage it launches stays in the switched method.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Methods folder `global/methods/` (symlinked as `~/.claude/methods/`) | Holds one `<m>.md` (rules, optional) and one `<m>.settings.json` (plugins and excludes) per method. `plain` has a settings file only. `superpowers` has a few lines of rules at most. | The rules and the plugin set of every method, and the list of which methods exist | Data store (files) |
| `claude-as` (`global/bin/`, symlinked into `~/.local/bin`) | Turns a method name into two path flags, then execs the real `claude` | none | Client script, about 10 lines |
| Project `CLAUDE.md` import line and `.claude/settings.json` `enabledPlugins` | The default method for a bare `claude` | The project's default | Committed files |
| `/kit:setup <m>` | Writes the import line, and copies `enabledPlugins` from `<m>.settings.json`. Drops the redundant `**Method:**` fact. | none | Skill |
| Slim method guard (kit SessionStart) | Checks only committed files: the import line is in canonical form, and project `enabledPlugins` matches the import's settings file. It never reads flags, so switched sessions raise no false alarm. | none | Hook |
| `my:handoff` launch step | Copies the `--settings` and `--append-system-prompt-file` pairs from `ps -o args= -p $CLAUDE_PID` | none | Skill text |

Text that tells which method is in force must work in both load paths, so it keys on the method file's own heading (`# Method: my`), not on "the project imports". This covers `docs-layout.md:9`, `plan-format.md:8`, the Precedence line in `global/CLAUDE.md`, the opening line of `my.md` and the assertion in `test_neutral_core.py`.

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| User or tmux → `claude-as` | Method name plus claude args | sync | Unknown method (no settings file): print the list of methods and exit 1. Nothing starts. |
| `claude-as` → `claude` | `exec` with two file paths | sync | Claude Code reports an unreadable file. No state is left behind. |
| `claude` → methods folder | Reads the settings file and the prompt file once at start | sync | If the session starts, the rules are in its snapshot |
| `claude` → project files | Reads `CLAUDE.md`, minus the excluded imports | sync | A non-canonical import is not excluded: two methods load at once (the guard catches this in a bare session) |
| `my:handoff` → new `claude` | Copied flag pairs (paths, no quotes) | sync | Missing pairs: the stage starts in the default method. Nothing warns. |
| Guard → project files | Reads two committed files | sync | Fails open with a warning, as today |

#### Forces

Served:

- 3 (effort to switch): one command. No file edit, no commit. Appended files need no import approval.
- 4 (method in force): both flags load before the first turn. The model decides nothing.
- 1 (load, more than 6 sessions): no shared state and no lock. Each session carries its own flags.
- 7 (one developer): a short script plus JSON files. Nothing runs between sessions.
- 8 (rate of change): a new method is a new file pair.
- 10 (constraints): bare `claude` is untouched, and the real binary is not shadowed. Only tested mechanisms are used.
- 6 (security): the existing hooks are kept, and the push guard still runs with `my`.

Sacrificed:

- 5 (consistency, "one fact"): the default lives in two committed places. The plugin half is copied from the method's settings file by setup, and the guard checks they agree. This cannot be avoided: a hook carries at most 10,000 chars, and plugins cannot ship CLAUDE.md.
- 5 (consistency, resume): a bare `claude --resume` of a switched session keeps the switched rules but goes back to the default plugins. The fix is to resume through `claude-as <same m>`. Whether passing the prompt file again on resume doubles it is untested.
- 5 (one source for the exclude list): if `claudeMdExcludes` takes no glob, every settings file repeats the full exclude list.

#### Hard-to-reverse decisions

- The executable name `claude-as` and its argument order, typed by hand and depended on by `my:handoff`.
- Method name = file stem = settings file stem, for all methods.
- The canonical import form `@~/.claude/methods/<m>.md`. Exclusion matches only that form, with `~` expanded (flag test 8).
- `# Method: <m>` as the marker in context that lazy rules and other text key on.
- Handoff inherits the method through flags copied from `ps`, not through a recorded state.

#### Numbers it depends on

- `my.md` is 26,958 chars. The tested file was 27,006 chars and loaded whole. Larger files are untested.
- The hook cap of 10,000 chars per string is why the rules cannot come from a hook.
- More than 8 methods means 8 or more file pairs. The exclude list holds one path of about 40 chars per method: one glob line if globs work, otherwise N×N lines across the settings files.
- More than 6 sessions at once, no contention: nothing is written.
- 10 projects plus 1 worktree with a default today. Each needs `/kit:setup` run again only for the guard's matching check, not for any change in how the default loads.
- Force 9 (tokens, assumed): the design does not depend on it. Appended text and imported text are the same size.

#### Weakest point

The switch is held only by launch flags, and three paths lose them without a word. First, a bare `--resume` splits rules from plugins. Second, a handoff step that misses one flag pair starts the next stage in the default method. Third, an import written in a non-canonical form escapes the exclude, so two methods load at once in switched sessions, which the guard does not see because it ignores flags. Nothing records which method a session was started with, so nothing can detect these cases. Separately, the "one fact" default is really two committed pieces, and a guard keeps them in agreement. That is the part of the old per-project switch the user wanted gone. This candidate keeps it because a bare `claude` gives it no other native loader. Whether `claudeMdExcludes` accepts a glob is unverified, and the cost of the exclude list as methods grow depends on it.

### Candidate B

#### Summary

Shape: separate deployables, each owning its own data. Each method is one package: `global/methods/<name>.md` (its rules, path unchanged) and a sibling `<name>.json` (its `--settings` piece: `enabledPlugins` and, for tutor, `outputStyle`). A generic wrapper, `claude-method <name> [claude args]`, knows no method names. It finds packages by listing the directory, passes the chosen package's two files as flags, and records the session's method in that method's own state folder. A bare `claude` loads the project default through the import line that exists today, plus plugin keys in the project's settings that are copied from the package and checked by the guard.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Method package `my`, `tutor`, `superpowers`, `plain` (`global/methods/<name>.md` + `<name>.json`) | Defines one method | Its rules text and its plugin set. `plain` has an empty `.md` and an empty `.json` | Files the wrapper or the import reads |
| `claude-method` wrapper (`global/bin/`, linked into `~/.local/bin`) | Starts a session on a chosen method | none (it reads packages, writes a record) | Script on the user's and the tmux server's PATH |
| Session record (`$XDG_STATE_HOME/claude-method/<name>/<session-uuid>`) | Says which method a session started with | Which method is active, per session | One write-once file per session |
| Project `CLAUDE.md` / `CLAUDE.local.md` import line | Sets the default method for a bare `claude` | The project's default method (the one fact) | Memory file |
| Project `.claude/settings.json` `enabledPlugins` | Turns on the default's plugins for a bare `claude` | none: a copy of the default package's keys | Settings file |
| Generic guard (kit, SessionStart, also on resume) | Finds drift and splits | none | Hook, user scope |
| Generic `/kit:setup <name>` | Writes the import line and copies the plugin keys | none | Skill |
| Lazy rules (`docs-layout.md`, `plan-format.md`) | Path-scoped `my` rules | Owned by the `my` package; linked into `~/.claude/rules/` | Rules files |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| Wrapper → packages | Lists `global/methods/*.json`, reads the chosen pair | sync | Unknown name: prints the names it found, exits 1, starts nothing |
| Wrapper → project `CLAUDE.md` + `CLAUDE.local.md` | Reads the default's import line and expands `~` | sync | No import found: no exclude is passed, and the wrapper says so |
| Wrapper → `claude` | `--append-system-prompt-file <name>.md`. `--settings` = the chosen keys `true`, the union of every other package's keys `false`, and `claudeMdExcludes` = [the default import path as written]. Also `--session-id <uuid>` and `CLAUDE_METHOD` | sync (exec) | Chosen equals default: passes only the session ID. No rules or plugin flags, so nothing loads twice |
| Wrapper → session record | Writes method name and uuid | sync | Write fails: warns and still starts the session |
| `claude-method resume <id>` → record → `claude --resume` | Looks up the method and passes its plugin flags again | sync | No record: resumes bare and warns |
| Guard → record, packages, project settings | Bare resume of a switched session, or project keys that differ from the default package | sync | Warns with the fix command. Exits 0 every time |
| `my:handoff` → wrapper | `claude-method my -- -n <name> <mode flag> …`, with `MY_AUTORUN` passed through | sync | Wrapper not on PATH: prints the command (the existing fallback) |

#### Forces

Served:

- 2 (Data volume and growth): adding a method means adding two files. The wrapper, guard and setup need no change and hold no table of method names.
- 3 (Effort to switch): one command, `claude-method tutor`. No file edit, no commit, and no new approval, because neither flag needs one.
- 4 (Method is in force): the rules arrive as a flag or an import, and the plugins come from settings. The model invokes nothing.
- 5 (Consistency), inside a switched session: the rules and the plugins come from one package by construction.
- 1 (Load): sessions share no mutable state. Each record file is written once per session.
- 9 (Cost): neutral. Because the default import is excluded, a switched session never loads two methods. The design does not lean on this assumed force.

Sacrificed:

- 5 (Consistency), across packages: the appended file almost certainly does not expand `@` imports. So each package must be one flat file, and rules two methods share must be copied. For example, Git Workflow would sit in both `my` and `superpowers`.
- The user's "one fact" requirement cannot be met. A bare `claude` gets plugins only from settings files, so the project commits a second, derived fact: the plugin keys. The guard can find drift but cannot prevent it.
- 4 (Method is in force), for lazy rules: today's gate ("the project imports my.md") is wrong both ways under a switch. A tutor session in a `my` project would apply docs-layout, and a `my` session in a tutor project would ignore it. Gating on a `# Method: my` heading is judged by the model, so it is soft.
- 7 (Team and operations): more parts to run: a wrapper, a settings piece per method, a record folder, and a resume command to remember.

#### Hard-to-reverse decisions

- The package format, a `<name>.md` and `<name>.json` pair found by listing the directory. Setup, the guard and the wrapper all depend on it.
- The wrapper's command form. `my:handoff`, scripts and habit build on it.
- Lazy rules gated on the session's method heading instead of the import line.
- The session record, keyed by the `--session-id` the wrapper picks.

#### Numbers it depends on

- A 27,006-char method file loads whole through `--append-system-prompt-file` (tested), against today's `my.md` of 26,958 chars.
- More than 8 packages: the guard and the wrapper list them in well under the 10 s hook timeout.
- 10 repos + 1 worktree keep their import lines unchanged. Each gets plugin keys checked against its package.
- Not verified yet, to check before the spec: whether `--resume` keeps the same session ID in the hook input; whether `outputStyle` works through `--settings`; whether the appended file expands `@` imports; whether `claudeMdExcludes` covers files in `~/.claude/rules/`. `--session-id <uuid>` does exist (`claude --help`).

#### Weakest point

The ownership boundary in this shape leaks at both ends. On the bare path, the project has to hold a copy of the package's plugin keys, so the package is not the only source. On the switched path, the package has to be one flat file, so shared rules are copied between packages and force 5's "one source" breaks as methods grow. A resume without the wrapper still splits rules from plugins. The guard only reports that split; it cannot fix it. The lazy-rule gate depends on the model's judgment until someone shows that `claudeMdExcludes` reaches user rules.

### Candidate C

#### Summary

Shape: event-driven. Every session start produces one **method event**: `{method, origin, session_id}`. The origin is `launch` (the launcher `cm <method>` ran), `default` (a bare `claude` read the project's import line) or `ledger` (a resume, looked up by session ID). Hooks carry only the method's **name**, never its rules. This is the difference from the rejected 2026-10-12 Candidate C. Rule text reaches the model only through the CLAUDE.md import (bare `claude`) or `--append-system-prompt-file` (launcher), because `my.md` is 27,000 chars and hook text is capped at 10,000. Each part (lazy rules, guard, tutor marker, handoff, push guard) reads the method from the event line or the launcher's `CLAUDE_METHOD` env var, never from the project's import line.

#### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| Launcher `cm` (`global/bin/cm`, linked into `~/.local/bin`, on PATH because tmux runs no alias) | Turns `cm <method> [claude args]` into `claude --append-system-prompt-file <rules> --settings '{enabledPlugins, claudeMdExcludes:[every ~/.claude/methods/*.md, ~ expanded]}'` with `CLAUDE_METHOD=<m>` set. `cm resume <id>` relaunches with the method found in the ledger | none | client script |
| Method manifest (`global/methods/methods.json`) | Maps each method (my, tutor, superpowers, plain, and later ones) to a rules file (or none) and an `enabledPlugins` map that always keeps `kit` on | which plugins and rules make up each method | file |
| Method files (`global/methods/<m>.md`) | Always-on rules of one method | the rule text | files |
| Project default: the import line `@~/.claude/methods/<m>.md` | Names the default method and loads its rules for a bare `claude` | the project's default method | line in project CLAUDE.md |
| Project `enabledPlugins` | Turns on the default method's plugins for a bare `claude` | none: `/kit:setup` generates it from the manifest | `.claude/settings.json` |
| SessionStart router (kit, matcher `startup\|resume\|clear\|compact`); replaces `method-guard.py` and absorbs the tutor marker | Works out the event, appends it to the ledger, prints one line "Active method: X (origin)". For origin `default` it checks that the import and `enabledPlugins` agree. On a resume it compares the ledger with the current launch and warns about a split | none | hook process |
| Session ledger (`~/.claude/state/method-ledger.jsonl`) | Append-only log of method events | which method each session ID started with | file |
| Gate lines in `docs-layout.md` and `plan-format.md` | Today: "applies when CLAUDE.md imports my.md". New wording: "applies when the Active method line says my" | none | path-scoped rule files |
| `my:handoff` | Starts each stage as `cm $CLAUDE_METHOD -n …` when the env var is set, else as a bare `claude -n …` | none | skill |
| `block-autorun-push.py` | Unchanged. It is the existing example of the pattern: it reads `MY_AUTORUN` from the launch environment | none | hook |
| `/kit:setup <m>` | Writes the import line and generates `enabledPlugins` from the manifest | none | skill |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| `cm` → Manifest | file read | sync | Unknown method or missing rules file: print an error and do not start `claude` |
| `cm` → Claude Code | flags plus the env var | sync | Claude Code rejects a flag: the session never starts, and the user sees the error |
| Claude Code → Router | hook JSON (`source`, `session_id`, `cwd`) | sync | Timeout or crash: the session still has its rules and plugins from the flags or the files. Only the event line, the drift warning and the ledger entry are lost |
| Router → Ledger | one appended line (about 150 bytes) | sync | Write fails: warn in the context, carry on |
| Router → Model | `additionalContext`, at most 2,000 chars | sync | n/a |
| Lazy rules → event line | the model reads the gate | sync | Line missing: the rule is ignored, so lazy rules fail closed |
| `my:handoff` → `cm` | command line in `tmux new-window` | sync | `cm` not found: the existing fallback prints the command |

#### Forces

Served:

- 3 (switch effort): one command, `cm tutor`. No file edit, no commit, and no new approval, because the appended file is not an `@` import.
- 4 (deterministic): rules arrive through a flag or the import, and plugins through `enabledPlugins`. The router is a hook, so nothing waits for the model to call a skill.
- 1 (load): no shared switch to change. The method lives in each process's flags and env, and the ledger is append-only.
- 8 (rate of change): a new method is one manifest entry plus one file, with no edit in any project.
- 10 (fixed constraints): a bare `claude` works unchanged. Excluding every method path means `cm` never needs to know the project's default.

Sacrificed:

- 5 (consistency) on resume: a resume without `cm` keeps the old system prompt but loads the default plugins. The router detects this and points to `cm resume <id>`. It cannot repair the session.
- 5 (consistency) for the default: one fact, but stored in two places. The import line is the fact. `enabledPlugins` is generated from it and checked at startup, but it is still a second committed file.
- 4 (deterministic) for lazy rules: the gate is the model reading a line, as it is today.

#### Hard-to-reverse decisions

- The event line format and the `CLAUDE_METHOD` name become a contract between the router, the gate lines, handoff and any later method.
- Muscle memory and the handoff launch strings both depend on `cm`.
- A switched session's rules move into the system prompt snapshot, so a method cannot change inside a running session.

#### Numbers it depends on

- A method file under the tested 27,006 chars that loaded whole. No larger file was tested.
- Each ledger line under 4,096 bytes (PIPE_BUF, the size up to which a Linux append is atomic), so more than 6 sessions can write at once without mixing lines. About 50 sessions a day is under 3 MB a year.
- `docs-layout.md` is 10,987 chars, over the 10,000 hook cap. It stays a file and cannot become a hook string.
- Not tested yet:
  - whether `--settings` `enabledPlugins` merges per key or replaces the whole map (kit is on only at user scope);
  - whether `--settings` can set `outputStyle` (tutor needs this);
  - whether `claudeMdExcludes` applies to `~/.claude/rules/*`.

#### Weakest point

The choice is static. Only one event really needs a reaction, the resume, and the reaction is a warning, not a fix. The ledger, the router and the event line add three moving parts mainly to detect that one case. A plain launcher that copies its own flags into handoff (handoff already copies `--plugin-dir` from `ps`) gets most of the value with fewer parts. Two more problems:

- The gate on the lazy rules is still read by the model.
- If `--settings` replaces the whole plugin map, every launcher session needs the full plugin list in the manifest, and the router (in kit) disappears whenever kit is left out.

### Candidate D

No subagent draft. Candidate D was raised during evaluation; its Summary, Components and Connections are under "Candidates" above.
