# Architecture brief: swappable methods

**Status:** approved, 2026-10-12. A mix of candidates B and A, chosen by the user; brainstorming writes the spec next.

## How to read this brief

1. This brief.
2. `global/CLAUDE.md` (symlinked as `~/.claude/CLAUDE.md`): the file being split. Its "Learning workspaces" section is the precedent: it already lists the sections `my:tutor` replaces.
3. `global/rules/docs-layout.md` and `global/rules/plan-format.md` (symlinked as `~/.claude/rules/`): the path-scoped rules that stay lazy.
4. `plugins/my/hooks/hooks.json`: the SessionStart marker hook for `my:tutor`, the pattern the guard hook follows.
5. `plugins/my/skills/*/SKILL.md`, `plugins/my/skills/handoff/README.md`, `plugins/my/agents/code-reviewer.md`: the skills and agents that cite rules in `global/CLAUDE.md` by section name.
6. `docs/reports/2026-10-12-handoff-instructions-audit.md`: the source of force 2 and of the "single source of truth" wording in force 5.
7. `https://github.com/mattpocock/skills` (`.claude-plugin/plugin.json`, `skills/engineering/setup-matt-pocock-skills/SKILL.md`): the outside method used to test compatibility.
8. Claude Code docs used for force 10: `https://code.claude.com/docs/en/memory.md`, `plugins/loading.md`, `plugins/components.md`, `hooks.md`, `headless.md`.

The spec written next lists this brief first in its own "How to read this spec".

The description, in the user's words: "we have created a layered idiomatic workflow built around the superpowers plugin. it is comprised of the skills in the `my:` plugin such as `my:handoff` and `my:architect`. the global CLAUDE.md references superpowers directly and also contains sets of rules that integrate with the rest of the skills. all this makes trying out alternative methods and skills next to impossible unless a global claude is rewritten everytime i want to try something new. (1) extract the explicit rules that are coupled with specific skills to a new set of skills; this would apply to the git workflow and the coding task size match, maybe other things as well. (2) this new set of skills then along with our existing skills comprise a whole method that can be invoked for one project but can also be replaced by a different set of skills. (3) we write a `scaffold` skill that prepares or adapts a project claude.md to this workflow."

Note on idea (1): the brief does not move always-on rules into skills. A skill loads only when the model calls it, and force 4 requires deterministic activation. The method's skills still belong to the method; its always-on rules live in a file that always loads.

## Forces

The standard forces were written for server systems. Each is mapped onto an instruction system; the mapping is in the Force column.

| # | Force | Value | Label | Source or reason |
| --- | --- | --- | --- | --- |
| 1 | Load | Two or three methods live at the same time across 13 projects with a `CLAUDE.md`; several sessions at once (parallel auto runs) | stated | User answer; `~/projects/*/CLAUDE.md` |
| 2 | Data volume and growth | Rules loaded per session today: 30,121 chars (`global/CLAUDE.md`), plus 12,023 chars (`docs-layout.md` + `plan-format.md`) when a `docs/plans/` file is touched; `my:handoff` SKILL.md alone is 8,400 words | inferred | `wc`; estimate 1; the audit report |
| 3 | Latency target (here: text loaded at session start) | No limit: correct activation matters more than length | stated | User answer |
| 4 | Availability (here: the method is in force) | Deterministic: a hook or an always-loaded file switches the method on; the model never has to decide to invoke a skill | stated | User answer; `global/CLAUDE.md` "Auto-dispatch of skills is unreliable on Opus 4.7+" |
| 5 | Consistency | Each rule has one source. The project `CLAUDE.md` holds facts only (scopes, test command, plans index, remote, method name, optional "Parallel runs"); no copies of method rules | stated | User answer |
| 6 | Security and compliance | Nothing beyond existing hooks (`block-autorun-push.py`) | inferred | `plugins/my/hooks/hooks.json` |
| 7 | Team and operations | One developer | stated | `global/CLAUDE.md` "I am the sole developer" |
| 8 | Rate of change | Rules change often (13 commits to `global/` in 30 days, 97 repo commits); methods are swapped whenever the user wants to try something new | stated | User message; `git log` |
| 9 | Cost | unknown, assumed: tokens per session matter somewhat, money does not | assumed | No statement |
| 10 | Fixed constraints | Plugins in a marketplace at the repo root; `~/.claude/CLAUDE.md` and `~/.claude/rules` symlink into `global/`; superpowers is third-party and cannot be edited; subagents read no `CLAUDE.md`; plugins cannot ship `CLAUDE.md` or `rules/`; project `enabledPlugins` overrides user scope; plugin SessionStart hooks inject at most 10,000 chars per string; a project `CLAUDE.md` may `@import` `~/` files after a once-per-project approval; a symlinked `.claude/rules/` target outside the project needs the same approval and its `paths:` rules never load; outside methods (superpowers, `mattpocock-skills`) ship as plugins | inferred | `claude-code-guide` check of the docs listed above; spike 1; repo files |

## Collapse gate

`Three candidates.` Forces 1, 3, 7 and 10 allowed one candidate (2–3 methods, no latency limit, one developer, nothing forcing a second store). Force 4 did not: deterministic activation is a strict target, not "an hour of downtime is acceptable".

Shapes not used:

- Queue and background workers: would need rule delivery that can lag behind the session (force 3 or 4 relaxed); neither is.
- Pipeline or batch processing: would need rules built in stages from sources (force 8 with generated outputs); no generation step is needed.
- Client-heavy or offline-first: would need sessions on machines without the repo (force 10); there is one machine.
- Managed or serverless services: would need a hosted component (force 9 with a budget); none is wanted.

## Candidates

### Candidate A: simplest design

**Reason:** Always included: the simplest design that could meet the forces.
**Contrast:** vs B: process count (one plugin vs several) and data ownership (global method file vs per-plugin rules). vs C: communication (load at start vs per event) and computation (none vs a dispatcher script).
**Labels:** none

#### Summary

Shape: simplest design. `global/CLAUDE.md` is cut in two. A method-neutral core stays global: Communication, Critical Thinking, Code, HTTP Requests, Conventional Commits, and "no new dependencies". Everything coupled to a skill set moves into one file per method, `global/methods/<name>.md`, symlinked as `~/.claude/methods/`. Examples of that coupled text: Superpowers Integration, the size table, Code Review Routing, UI Design, Git Workflow, Planning Standards, and the path-scoped `docs-layout.md` and `plan-format.md`. Each project switches its method on with one line in its own `CLAUDE.md`, `@~/.claude/methods/<name>.md`, under a facts-only block that a new `my:scaffold` skill writes. No new plugin, hook or registry is added: the import line is the only switch, and Claude Code loads it before the first turn.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Neutral core (`global/CLAUDE.md`, trimmed) | Rules that hold under every method | The method-neutral rules | File loaded by Claude Code at session start |
| Method file (`global/methods/superpowers-my.md`, later `tutor.md`, `<trial>.md`) | The whole rule set of one method, with its own `@` imports of `methods/superpowers-my/docs-layout.md` and `plan-format.md` | That method's rules, one source each | File, loaded through the project import |
| Project `CLAUDE.md` | Facts plus the method switch | The method name (the import line), scopes, test command, plans index, remote, optional "Parallel runs" | File |
| Project `.claude/settings.json` | Turns off plugins the method does not use (for example `superpowers: false` for a trial method) | Plugin enablement for that project | File, read by Claude Code |
| `my:` plugin (unchanged location) | Skills and hooks of the superpowers-my method | Skill text, hooks | Plugin |
| `my:scaffold` skill (new, inside `plugins/my`) | Writes or adapts the facts block and the import line; proposes the `enabledPlugins` lines | none | Skill, run on request |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Claude Code → project `CLAUDE.md` → method file | `@` import, expanded at session start | sync | If the file is missing or the user declines the one-time import approval, the session runs with no method and gives no warning |
| Method file → its own rules files | Nested `@` import (depth limit 5) | sync | Same as above |
| Claude Code → `.claude/settings.json` | `enabledPlugins` | sync | A missing entry falls back to the user-scope plugins, so superpowers' own SessionStart hook still fires |
| `my:scaffold` → project `CLAUDE.md` | File edit, after the user approves | sync | The skill stops and shows the diff |
| `my:` skills → project `CLAUDE.md` | They read facts ("Parallel runs", scopes) | sync | They keep their current defaults |
| `my:handoff` subagents → none | A subagent reads no `CLAUDE.md`; the prompt carries what it needs | sync | Unchanged from today |

### Candidate B: separate deployables, each owning its own data

**Reason:** Force 1 (two or three methods live at once) and force 8 (methods swapped often): each method is its own plugin, chosen per project in `.claude/settings.json`.
**Contrast:** vs A: as above. vs C: communication (all rules at session start vs per event) and data ownership of the method choice (`enabledPlugins` vs a marker line read by a dispatcher).
**Labels:** none

#### Summary

Shape: separate deployables, each owning its own data. Each method is its own plugin in the `claude-setup` marketplace, for example `plugins/sp-method/` (today's superpowers workflow) and later `plugins/<other>-method/`. Each plugin owns its rule text, skills, agents, hooks and `bin/` scripts. The method's rules come in through the plugin's own SessionStart hooks, so no CLAUDE.md copy is needed. A project picks its method in `.claude/settings.json` `enabledPlugins`: it enables one method plugin and sets the others to `false`. `global/CLAUDE.md` shrinks to the rules that do not depend on any method. A small `my` core plugin keeps the method-neutral skills, plus a guard that checks exactly one method is enabled.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| `global/CLAUDE.md` (cut down) | Rules for every project: Communication, Code, HTTP, Critical Thinking, no new deps, Conventional Commits | Method-neutral rules (about 4.5k chars: lines 1–33 and 130–162 today, minus Learning workspaces) | Always-loaded file |
| `my` core plugin | Neutral skills (de-slop, md-tables, briefing, dev-reports, tutor), `block-autorun-push.py`, the method guard hook | Neutral skills; the `*-method@claude-setup` naming rule | Plugin |
| `sp-method` plugin | The current method: handoff, architect, spec-review, soundness-review, status, roadmap/changelog skills, `my:code-reviewer`/`spec-reviewer` agents, `handoff-lock.py`, `git-fold-fixups.py`, `status-scan.py` | `rules/*.md`: Size table, Superpowers Integration, Code Review Routing, Git Workflow, docs-layout, plan-format, UI Design (about 33k chars) | Plugin with SessionStart and PreToolUse hooks |
| `sp-method` scaffold skill | Writes or adapts the project's facts section and `enabledPlugins` block | The facts schema that this method needs | Skill inside `sp-method` |
| Other method plugins | Same layout, with different rules and skills | Their own rules, skills and facts schema | Plugin |
| superpowers (third party) | Brainstorming, writing-plans, TDD and so on | Its own skills | Plugin, enabled per project next to `sp-method` |
| Project `.claude/settings.json` | Picks the method | Which method plugin is on, and whether superpowers is on | Config file |
| Project `CLAUDE.md` | Facts only: scopes, test command, plans index, remote, method name, optional "Parallel runs" | Project facts | Always-loaded file |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Claude Code → method SessionStart hooks | Session start event; the hook `cat`s one rules file per hook entry into `additionalContext` | sync | If a hook errors, that part of the rules is missing without notice. The guard hook prints a checksum line ("sp-method rules: 4/4 parts loaded"). |
| Claude Code → core guard hook | Reads user and project `enabledPlugins` and counts the `*-method` keys that are on | sync | 0 or 2+ methods on: injects "No single method is active; run the scaffold" and stays out of the way |
| Method PreToolUse hook (Read/Write on `docs/plans/`) → session | docs-layout and plan-format text, the job the path-scoped `rules/` load does today | sync | Same as the first row; the rules are missing for that call |
| Project `CLAUDE.md` → method skills | Facts (scopes, test command) | sync (read by the model) | Skills ask the user; the scaffold fills the gap |
| `sp-method` skills → `my` core skills | A call by name, for example `my:de-slop` | sync | Skill not found: the method stops and names the missing plugin |
| `sp-method` → superpowers | A call by name, `superpowers:brainstorming` | sync | If superpowers is off, the guard warns, because `sp-method` lists it as required in its README and the scaffold enables it |
| Scaffold → project files | Edits `CLAUDE.md` and `.claude/settings.json` | sync, with user approval | Shows the diff and writes nothing until the user says yes |

### Candidate C: event-driven

**Reason:** Force 4 (deterministic activation) and force 2 (much rule text under a 10,000-char hook cap): rules are injected by hooks on the events they govern.
**Contrast:** vs A and vs B: as above.
**Labels:** none

#### Summary

Shape: event-driven. A method is a plugin (for example `plugins/method-sp/`, holding today's `my:` workflow) that ships its skills, a folder of rule fragments, and one `hooks.json` whose hooks all call one dispatcher script. On each event (SessionStart, a `Skill` tool call, a `Write`/`Edit`/`Read` under `docs/plans/`, a Bash `git commit` / `git merge --squash` / `git worktree add`, SubagentStart, and compaction), the dispatcher reads the project marker (a `Method: sp` line in the project CLAUDE.md, or `.claude/method`). It prints the fragment for that event only if the marker names its method, and stays silent otherwise. Global CLAUDE.md keeps only the rules that hold under every method: Communication, Code, Critical Thinking, HTTP, and the no-new-dependencies rule. Swapping a method means changing one marker line, and every method plugin stays installed.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Project marker | Names the active method for a repo | Which method is active in the project | File in the project (CLAUDE.md "Method:" line or `.claude/method`) |
| Method plugin (`method-sp`, later `method-x`) | Ships skills, rule fragments and hooks for one method | The method's rules, each in exactly one fragment | Claude Code plugin in the marketplace |
| Rule fragments (`fragments/<event>.md`) | Hold the text for one event: `session.md` (size table, worktree rule), `skill-brainstorming.md` (Spec → Plan flow, discovery authority), `docs-plans.md` (docs-layout, plan-format), `commit.md`, `merge.md`, `review.md`, `subagent.md` | The rule text | Files inside the plugin |
| Dispatcher (`method-hook.py`) | Matches event to marker to fragment, and enforces the 10,000-char cap with a test | None (stateless) | Hook command, runs once per event |
| Global CLAUDE.md (reduced) | Method-independent standards | Communication, Code, Critical Thinking, HTTP, dependencies | Always-loaded file (symlink) |
| Project CLAUDE.md | Facts: scopes, test command, plans index, remote, method name, "Parallel runs" | Project facts | Always-loaded file |
| `scaffold` skill (per method) | Writes or adapts the project CLAUDE.md facts and the marker; removes copied rules | None | Skill in the method plugin |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Claude Code → Dispatcher | Hook JSON (event, tool input, cwd) | sync | Hook times out or errors: Claude Code goes on without the fragment. The session runs with no method rules, silently. |
| Dispatcher → Project marker | File read | sync | No marker: inject a one-line "no method set, run `<method>:scaffold`". Unknown name: say so. |
| Dispatcher → Rule fragment | File read, then `additionalContext` | sync | Fragment missing or over the cap: print an error line as context so the model sees it. A CI test blocks over-cap fragments. |
| Dispatcher (SubagentStart) → Subagent | `subagent.md` (commit-ID rule, Risk-is-not-a-finding) | sync | Same as above. Today this text is pasted into each review prompt by hand. |
| SessionStart `compact` → Model | `session.md` again | sync | Without it, fragments injected earlier are lost after compaction. |
| `scaffold` → Project CLAUDE.md | Edited file plus marker | sync | User reviews the diff and approves before writing. |

## Evaluation

### Data ownership

- **A:** the active method is named twice: the import line in the project `CLAUDE.md` and, for plugins such as superpowers, `enabledPlugins`. Two owners; they can disagree.
- **B:** the active method has one owner (`enabledPlugins`). Shared skills (`soundness-review`, `spec-review`, `status`) have one owner, `sp-method`, so a second method must depend on it or fork them.
- **C:** the active method has one owner (the marker). "Which plugins are on" is user scope and always "all", so it owns nothing per project.
- **All:** project facts are owned by the project `CLAUDE.md`. Rule text is owned by one file each. No state has zero owners.

### Scenarios

1. **Normal path at peak (force 1):** three sessions in three projects start at once, two on our method and one on Pocock's.
   - A: holds for our projects. **Breaks** for the Pocock project: superpowers' SessionStart hook and `my`'s squash-merge hook still fire there.
   - B: holds; each project loads only its enabled plugins.
   - C: holds for our method. The Pocock project holds only if `mattpocock-skills` is not expected to ship our dispatcher; it is not, so it gets no rules from us, which is correct.
2. **A dependency fails (force 4):**
   - A: the import was never approved, or the path is wrong. **Breaks silently**: spike 1 showed a headless `claude -p` session skips an unapproved external import with no message.
   - B: one SessionStart hook times out. **Breaks silently** for that slice of the rules.
   - C: the dispatcher errors. **Breaks silently** for that event.
3. **Most frequent change (force 8):** edit a rule.
   - A: edit one file in `global/`; the next session has it. Holds.
   - B: edit one file in the plugin; the next session after the plugin refresh has it. Holds.
   - C: edit one fragment. Holds, unless the rule has to move to another event, which changes when it applies without notice.
4. **Data volume after 3 years (force 2):** the method text doubles to about 60,000 chars.
   - A: holds; memory imports have no per-file cap. The combined-size warning threshold is undocumented.
   - B: **breaks** one part past 10,000 chars into a 2,000-char preview unless split again.
   - C: holds per fragment; the SessionStart fragment hits the same cap as B.
5. **Try a new outside method in one project (force 8, the user's goal):**
   - A: **partial.** The rules swap with one import line, but superpowers and the `my` hooks must be turned off by hand.
   - B: holds; flip `enabledPlugins` in one project.
   - C: **breaks**; the outside method ships no fragments and reads no marker.

Force 6 is "none beyond existing hooks", so no abuse case was traced.

### Pre-mortem

- **A:** (1) a project was never approved, and headless runs worked without the method for weeks; (2) the neutral-core boundary was drawn wrong, so a method rule now governs every method; (3) a Pocock project kept superpowers on and the two processes fought.
- **B:** (1) a rules part grew past 10,000 chars and was cut to a preview without notice; (2) a second method forked `soundness-review` and the copies drifted; (3) the rename of every `my:` method skill broke references in docs and memory.
- **C:** (1) commit rules arrived after the commit; (2) the size rule, injected at session start, had fallen out of focus by the time it applied; (3) a hook feature the design depended on (context on PreToolUse or SubagentStart) changed.

### Comparison

| Force | A | B | C |
| --- | --- | --- | --- |
| 1 Load | partial: outside methods run with our plugins still on | meets | meets |
| 2 Data volume | partial: ~42k chars when `docs/plans/` is touched, as today | partial: same text, split under the hook cap | partial: most text still lands at session start |
| 3 Latency | meets | meets | meets |
| 4 Availability | partial: silent miss before approval; a guard hook can detect it | partial: silent miss when a hook fails | fails: many rules have no event, some arrive late |
| 5 Consistency | partial: method named in two places | meets for rules; partial for shared skills | meets |
| 6 Security | meets | meets | meets |
| 7 Team | meets: Markdown only | partial: 3+ plugins, renames, hook scripts | partial: dispatcher and event map |
| 8 Rate of change | meets | meets | partial: moving a rule between events is silent |
| 9 Cost | partial | partial | partial |
| 10 Fixed constraints | meets: native memory loading | partial: works around the hook cap | partial: rests on unconfirmed hook features |

## Decision

**A mix of B's packaging and A's rule loading, plus a guard hook.** Chosen by the user after a compatibility check against `mattpocock-skills` and superpowers, and a second choice on how rules load.

- **Switch:** the project's `.claude/settings.json` `enabledPlugins`. It works the same for our method and for outside methods, which all ship as plugins. A project on another method turns ours and superpowers off. Which scope turns them on by default is open (see "Open for brainstorming").
- **Packaging:** `my` splits into a neutral plugin (skills every method can use, such as `de-slop`, `md-tables`, `briefing`) and a method plugin (the current workflow's skills, agents, hooks and scripts, such as `handoff`, `spec-review`, `soundness-review`, `architect`, `status`). The method plugin's skills are renamed with its prefix.
- **Always-on rules of our method:** one file, `global/methods/<name>.md` (symlinked under `~/.claude/methods/`), imported by one line in the project `CLAUDE.md`. Approved once per project.
- **Lazy rules:** `docs-layout.md` and `plan-format.md` stay in `~/.claude/rules/` with their `paths:` lines. Each opens with a line telling projects that do not name this method to ignore it.
- **Neutral core:** `global/CLAUDE.md` keeps only rules that hold under every method (about 2,600 chars by estimate 1, before the boundary is settled in brainstorming). Its "Precedence" paragraph stops naming method rules as non-overridable.
- **Guard:** the method plugin's SessionStart hook checks that the project `CLAUDE.md` holds the import line and that the import is approved, and injects a warning when it is not.
- **Setup:** each method has its own setup skill, as `setup-matt-pocock-skills` does. Ours writes the facts block, the import line and the `enabledPlugins` lines, after the user approves the diff.

Rejected:

- **A alone:** leaves superpowers and the `my` hooks on in projects that use an outside method (scenario 1, 5).
- **B as drafted:** delivers about 33,000 chars of rules through hook strings capped at 10,000 each, with silent truncation (scenario 4).
- **C:** outside methods cannot take part (scenario 5), and many rules have no event to attach to (force 4).

## Reversibility and checks

| Decision | Label | Check |
| --- | --- | --- |
| Split `my` into a neutral and a method plugin; rename the method skills | hard | no quantity to check: the cost is references, counted below, not load |
| Method file location and the import line in project `CLAUDE.md` files | hard | estimate 1; spike 1 |
| `enabledPlugins` in project `.claude/settings.json` as the switch | medium | none: settings are edited per project and reversible |
| Where the neutral-core boundary sits | medium | none: decided section by section in brainstorming |
| Guard hook reads the approval flag `hasClaudeMdExternalIncludesApproved` in `~/.claude.json` | medium | the key is undocumented and may change; the guard must fail open with a warning |
| `docs-layout.md` and `plan-format.md` stay lazy with a method line | cheap | none |
| One setup skill per method | cheap | none |

References to the method skills that the rename touches (files under `global/`, `plugins/` and the project memory that name each token): `my:handoff` 8, `my:spec-review` 8, `my:soundness-review` 7, `my:architect` 5, `my:code-reviewer` 4, `my:tutor` 4, `my:spec-reviewer` 3, `my:roadmap-management` 3, `my:status` 2, `my:changelog-management` 1. No project `CLAUDE.md` under `~/projects/` names them. Committed reports in `docs/plans/` keep the old names.

Estimate 1, text loaded at session start:

```python
# Estimate: characters loaded at session start, today vs. after the split.
import pathlib, re
root = pathlib.Path('/home/dchris/projects/claude-setup')
g = (root/'global/CLAUDE.md').read_text()
dl = len((root/'global/rules/docs-layout.md').read_text())
pf = len((root/'global/rules/plan-format.md').read_text())
# Sections that stay global (method-neutral), by heading.
keep = ['# Instructions', '## Communication', '## Code', '## HTTP Requests']
parts = re.split(r'(?m)^(?=#{1,4} )', g)
neutral = sum(len(p) for p in parts if any(p.startswith(k + '\n') for k in keep))
# Critical Thinking, Conventional Commits lines and no-deps also stay; add Critical Thinking.
neutral += sum(len(p) for p in parts if p.startswith('### Critical Thinking'))
method = len(g) - neutral
print(f'inputs: global/CLAUDE.md={len(g)} chars, docs-layout={dl}, plan-format={pf}')
print(f'formula: after = neutral + method file (+ docs-layout + plan-format if imported eagerly)')
print(f'today, no docs/plans touched: {len(g)}; touched: {len(g)+dl+pf}')
print(f'after, neutral core only (outside method): {neutral}')
print(f'after, our method, lazy rules kept in ~/.claude/rules: {neutral+method}; touched: {neutral+method+dl+pf}')
print(f'after, our method, rules imported eagerly: {neutral+method+dl+pf}')
print('compared to: per-file warning ~40,000 chars (folklore; combined threshold undocumented); today the touched case already loads', len(g)+dl+pf)
```

```text
inputs: global/CLAUDE.md=30121 chars, docs-layout=10441, plan-format=1582
formula: after = neutral + method file (+ docs-layout + plan-format if imported eagerly)
today, no docs/plans touched: 30121; touched: 42144
after, neutral core only (outside method): 2556
after, our method, lazy rules kept in ~/.claude/rules: 30121; touched: 42144
after, our method, rules imported eagerly: 42144
compared to: per-file warning ~40,000 chars (folklore; combined threshold undocumented); today the touched case already loads 42144
```

The neutral-core figure counts only `# Instructions`, `## Communication`, `## Code`, `## HTTP Requests` and `### Critical Thinking`; it grows when brainstorming moves more sections into the core. With the chosen loading, our method projects load the same text as today (30,121 chars, 42,144 when `docs/plans/` is touched). That is near the ~40,000-char figure often quoted for the size warning, but the docs give no combined threshold, and today's setup already loads the same amount.

Spike 1 (run; code thrown away):

- An external `@import` from a project `CLAUDE.md`, never approved, run with `claude -p`: **not loaded, no message.** The control (the same 41,417-char file imported from inside the project) loaded.
- A SessionStart hook that writes a file into the project's `.claude/rules/`: the file loads from the **next** session, not the current one. Claude Code reads project rules before the hook runs.
- A `paths:` rule in the project's `.claude/rules/` loaded only after a matching file was read.
- The approval is stored per project path in `~/.claude.json` (`hasClaudeMdExternalIncludesApproved`). `my:handoff` opens every stage at the repo root, so one approval covers its sessions.
- Whether a size warning appears at 42,000 chars was not observable from a headless session.

## Open for brainstorming

- Force 9 (cost): unknown, assumed tokens matter somewhat.
- The neutral-core boundary, section by section. Candidates to place: Mandatory Exploration, Reference Sweep, Simplicity Rules, Test Standards, UI Design, "Before any review" (LSP mapping).
- The method's name, the two plugins' names, and which skills go where (`roadmap-management`, `changelog-management`, `status`, `tutor`, `clean-plans`, `commit`, `push`).
- Whether `my:tutor` becomes a method of its own, replacing the "Learning workspaces" override list.
- Whether superpowers stays on at user scope (today's projects unchanged) or turns on per project.
- Whether other agent tools (Codex, Copilot through `AGENTS.md`) must be able to use our method; the `@import` and the hooks are Claude Code only.
- The combined memory-size warning: threshold undocumented; spike 1 could not observe it headless.
- What the guard does when the import is unapproved: warn only, or also inject a pointer to the method file.
- Headless `claude -p` runs in a never-approved project skip the method; whether any script needs it.

## Appendix: candidate drafts

### Candidate A

#### Summary

Shape: simplest design. `global/CLAUDE.md` is cut in two. A method-neutral core stays global: Communication, Critical Thinking, Code, HTTP Requests, Conventional Commits, and "no new dependencies". Everything coupled to a skill set moves into one file per method, `global/methods/<name>.md`, symlinked as `~/.claude/methods/`. Examples of that coupled text: Superpowers Integration, the size table, Code Review Routing, UI Design, Git Workflow, Planning Standards, and the path-scoped `docs-layout.md` and `plan-format.md`. Each project switches its method on with one line in its own `CLAUDE.md`, `@~/.claude/methods/<name>.md`, under a facts-only block that a new `my:scaffold` skill writes. No new plugin, hook or registry is added: the import line is the only switch, and Claude Code loads it before the first turn.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Neutral core (`global/CLAUDE.md`, trimmed) | Rules that hold under every method | The method-neutral rules | File loaded by Claude Code at session start |
| Method file (`global/methods/superpowers-my.md`, later `tutor.md`, `<trial>.md`) | The whole rule set of one method, with its own `@` imports of `methods/superpowers-my/docs-layout.md` and `plan-format.md` | That method's rules, one source each | File, loaded through the project import |
| Project `CLAUDE.md` | Facts plus the method switch | The method name (the import line), scopes, test command, plans index, remote, optional "Parallel runs" | File |
| Project `.claude/settings.json` | Turns off plugins the method does not use (for example `superpowers: false` for a trial method) | Plugin enablement for that project | File, read by Claude Code |
| `my:` plugin (unchanged location) | Skills and hooks of the superpowers-my method | Skill text, hooks | Plugin |
| `my:scaffold` skill (new, inside `plugins/my`) | Writes or adapts the facts block and the import line; proposes the `enabledPlugins` lines | none | Skill, run on request |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Claude Code → project `CLAUDE.md` → method file | `@` import, expanded at session start | sync | If the file is missing or the user declines the one-time import approval, the session runs with no method and gives no warning |
| Method file → its own rules files | Nested `@` import (depth limit 5) | sync | Same as above |
| Claude Code → `.claude/settings.json` | `enabledPlugins` | sync | A missing entry falls back to the user-scope plugins, so superpowers' own SessionStart hook still fires |
| `my:scaffold` → project `CLAUDE.md` | File edit, after the user approves | sync | The skill stops and shows the diff |
| `my:` skills → project `CLAUDE.md` | They read facts ("Parallel runs", scopes) | sync | They keep their current defaults |
| `my:handoff` subagents → none | A subagent reads no `CLAUDE.md`; the prompt carries what it needs | sync | Unchanged from today |

#### Forces

Served:

- 4 (Availability): an approved import loads every time. The model never decides to invoke anything, and the "Auto-dispatch is unreliable" problem cannot happen at the activation step.
- 5 (Consistency): each rule has one home, its method file. The project file holds facts and one import line. "Learning workspaces" stops being a list of overrides: a tutor project imports `methods/tutor.md` instead.
- 3 (Latency): there is no 10,000-char hook cap to work around, so method files can be any length.
- 7 (Team): one developer. Plain Markdown files, no code to maintain.
- 8 (Rate of change): editing a method edits one file, and the symlink means no plugin release. To try a method, the user copies a file and changes one line in one project.

Sacrificed:

- 5, in part: the method is named in two places, the import line and `enabledPlugins`. These can drift apart, for example a trial method still running with superpowers enabled.
- 9 (Cost): the path-scoped lazy loading of `docs-layout.md` and `plan-format.md` is lost, because both now load in every session of a method project.
- 1 (Load): the `my:` hooks (squash-merge → roadmap, orphan plans) stay global, and they fire in projects under other methods unless `my` is disabled there. Disabling it also removes the method-neutral skills.
- Skills stay coupled to the superpowers-my method. For example, `plugins/my/skills/status/SKILL.md` cites "Assessing branch redundancy in `global/CLAUDE.md`", and that text moves. So these skills are not reusable by a second method without edits.

#### Hard-to-reverse decisions

- The file layout `~/.claude/methods/<name>.md` and its import line, written into 13 project `CLAUDE.md` files. Moving it later means editing every project and approving each import again. This is reversible, but tedious.
- What counts as "neutral core" versus "method". Rules placed in the core apply to every future method without being asked.
- `my:` skills cite rules by section name in the method file. Renaming sections breaks those references silently.

#### Numbers it depends on

- `global/CLAUDE.md` is 30,240 chars today. The core shrinks to about 4,000. The superpowers-my method file plus its rules is about 26,000 + 10,451 + 1,586, so about 38,000 chars loaded in every session of a method project. That is close to Claude Code's large-memory warning of about 40,000 chars. I have not checked whether imported text counts toward it.
- 13 projects × 1 import approval each: a one-time cost per project and per new method path.
- 2–3 methods live at once: a handful of files. That needs no registry.
- Running auto runs read the method once per session. A method edit reaches the next handed-off stage, not the running one.

#### Weakest point

Activation is deterministic only after the one-time import approval. If that approval is declined, missed in a headless `claude -p` handoff session, or the path is mistyped, the method is absent and nothing says so. The session falls back to the neutral core, with superpowers still enabled, and runs with no method. Handoff stages may hit this, because they run in new sessions. A SessionStart hook could check that the method loaded, but this shape does not include one.

A second point: "swapping a method" is really two edits, the import line and `enabledPlugins`. The `my:` plugin still couples its hooks and skills to one method. So option 2 from the user's message (replace the whole method) is only half met: the rules swap cleanly, but the skills and hooks do not.

The token-cost judgement rests on force 9, which is assumed: an always-eager ~38k-char load is acceptable only if tokens "matter somewhat" and not more.

### Candidate B

#### Summary

Shape: separate deployables, each owning its own data. Each method is its own plugin in the `claude-setup` marketplace, for example `plugins/sp-method/` (today's superpowers workflow) and later `plugins/<other>-method/`. Each plugin owns its rule text, skills, agents, hooks and `bin/` scripts. The method's rules come in through the plugin's own SessionStart hooks, so no CLAUDE.md copy is needed. A project picks its method in `.claude/settings.json` `enabledPlugins`: it enables one method plugin and sets the others to `false`. `global/CLAUDE.md` shrinks to the rules that do not depend on any method. A small `my` core plugin keeps the method-neutral skills, plus a guard that checks exactly one method is enabled.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| `global/CLAUDE.md` (cut down) | Rules for every project: Communication, Code, HTTP, Critical Thinking, no new deps, Conventional Commits | Method-neutral rules (about 4.5k chars: lines 1–33 and 130–162 today, minus Learning workspaces) | Always-loaded file |
| `my` core plugin | Neutral skills (de-slop, md-tables, briefing, dev-reports, tutor), `block-autorun-push.py`, the method guard hook | Neutral skills; the `*-method@claude-setup` naming rule | Plugin |
| `sp-method` plugin | The current method: handoff, architect, spec-review, soundness-review, status, roadmap/changelog skills, `my:code-reviewer`/`spec-reviewer` agents, `handoff-lock.py`, `git-fold-fixups.py`, `status-scan.py` | `rules/*.md`: Size table, Superpowers Integration, Code Review Routing, Git Workflow, docs-layout, plan-format, UI Design (about 33k chars) | Plugin with SessionStart and PreToolUse hooks |
| `sp-method` scaffold skill | Writes or adapts the project's facts section and `enabledPlugins` block | The facts schema that this method needs | Skill inside `sp-method` |
| Other method plugins | Same layout, with different rules and skills | Their own rules, skills and facts schema | Plugin |
| superpowers (third party) | Brainstorming, writing-plans, TDD and so on | Its own skills | Plugin, enabled per project next to `sp-method` |
| Project `.claude/settings.json` | Picks the method | Which method plugin is on, and whether superpowers is on | Config file |
| Project `CLAUDE.md` | Facts only: scopes, test command, plans index, remote, method name, optional "Parallel runs" | Project facts | Always-loaded file |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Claude Code → method SessionStart hooks | Session start event; the hook `cat`s one rules file per hook entry into `additionalContext` | sync | If a hook errors, that part of the rules is missing without notice. The guard hook prints a checksum line ("sp-method rules: 4/4 parts loaded"). |
| Claude Code → core guard hook | Reads user and project `enabledPlugins` and counts the `*-method` keys that are on | sync | 0 or 2+ methods on: injects "No single method is active; run the scaffold" and stays out of the way |
| Method PreToolUse hook (Read/Write on `docs/plans/`) → session | docs-layout and plan-format text, the job the path-scoped `rules/` load does today | sync | Same as the first row; the rules are missing for that call |
| Project `CLAUDE.md` → method skills | Facts (scopes, test command) | sync (read by the model) | Skills ask the user; the scaffold fills the gap |
| `sp-method` skills → `my` core skills | A call by name, for example `my:de-slop` | sync | Skill not found: the method stops and names the missing plugin |
| `sp-method` → superpowers | A call by name, `superpowers:brainstorming` | sync | If superpowers is off, the guard warns, because `sp-method` lists it as required in its README and the scaffold enables it |
| Scaffold → project files | Edits `CLAUDE.md` and `.claude/settings.json` | sync, with user approval | Shows the diff and writes nothing until the user says yes |

#### Forces

Served:

- 1 (Load): two or three methods live side by side. Each project enables its own plugin, and enabling a plugin at project scope overrides the user scope. Parallel sessions in different projects each load their own method.
- 4 (Availability): hooks inject the rules on every startup, clear and compact. The model never decides whether to load them. The guard makes a missing or doubled method visible.
- 5 (Consistency): each rule lives in exactly one plugin's `rules/` file. The project CLAUDE.md holds facts only, and the scaffold owns that schema.
- 8 (Rate of change): to try a method, copy a plugin directory, edit it, and flip one key in one project. The global file and the other projects stay as they are. The marketplace's commit-hash versioning gives every edit a new version.
- 10 (Fixed constraints): this uses only the plugin features the docs confirm (hooks, skills, agents, `bin/`). It uses no plugin CLAUDE.md or `rules/` files, which plugins cannot ship.

Sacrificed:

- 2/9 (Data volume, cost): the same text of about 33k chars is still injected, cut into four or more strings under 10k each. A string over 10k is cut down to a 2k preview. Nothing gets smaller, and each part must stay under the cap.
- 5 (Consistency, partly): if two methods both want soundness-review and want it to differ, the skill gets forked. Otherwise one method depends on the other's plugin.
- 7 (Operations): more moving parts for one developer to maintain: 3+ plugins, hook scripts, a guard, and a scaffold per method.

#### Hard-to-reverse decisions

- Skill names change: `my:handoff` becomes `sp-method:handoff`. Every reference in the skills, the reports in `docs/plans` and the hooks has to be swept, and old reports keep the old names.
- Rules move from `~/.claude` symlinks into plugin files that reach the session through hooks. The session sees them as hook context, not as memory. `/memory` no longer shows them, and the "edit `global/`" habit stops applying to them.
- Superpowers is enabled per project instead of globally. Leaving it on globally would leak its skills into projects that use other methods.
- The `*-method` naming rule that the guard depends on.

#### Numbers it depends on

- The largest method rule part has to stay under the 10,000-char hook cap. Superpowers Integration is 14,096 chars today, so it must be split in two. docs-layout is 10,451, which is over the cap, so it must be split too.
- Today about 33k chars are method-coupled out of about 44k chars loaded. After the move, global keeps about 6–11k.
- 13 projects have a CLAUDE.md, but only 1 has a `.claude/settings.json`. The scaffold must create 12 settings files before any project has a deterministic method.
- At most 3 methods are live at once (force 1). Above that, the cost of forking shared skills grows.

#### Weakest point

Delivering the rules through hooks is a workaround for "plugins cannot ship CLAUDE.md". The rules go in as many strings, each under 10k, with no feedback when one is cut. A hook that fails or times out drops a slice of the method without notice, and the guard's checksum only catches a hook that did not run. Splitting into plugins also does not make shared skills shared. soundness-review, spec-review and status are just as tangled with the current method as handoff is. In practice a second method would fork them or would depend on `sp-method`, and that brings back the coupling this shape exists to remove. The cost force (9) is `assumed`. If tokens matter more than assumed, injecting 33k chars every session through hooks is no better than today.

### Candidate C

#### Summary

Shape: event-driven. A method is a plugin (for example `plugins/method-sp/`, holding today's `my:` workflow) that ships its skills, a folder of rule fragments, and one `hooks.json` whose hooks all call one dispatcher script. On each event (SessionStart, a `Skill` tool call, a `Write`/`Edit`/`Read` under `docs/plans/`, a Bash `git commit` / `git merge --squash` / `git worktree add`, SubagentStart, and compaction), the dispatcher reads the project marker (a `Method: sp` line in the project CLAUDE.md, or `.claude/method`). It prints the fragment for that event only if the marker names its method, and stays silent otherwise. Global CLAUDE.md keeps only the rules that hold under every method: Communication, Code, Critical Thinking, HTTP, and the no-new-dependencies rule. Swapping a method means changing one marker line, and every method plugin stays installed.

#### Components

| Component | Job | Owns (state) | Runs as |
| --- | --- | --- | --- |
| Project marker | Names the active method for a repo | Which method is active in the project | File in the project (CLAUDE.md "Method:" line or `.claude/method`) |
| Method plugin (`method-sp`, later `method-x`) | Ships skills, rule fragments and hooks for one method | The method's rules, each in exactly one fragment | Claude Code plugin in the marketplace |
| Rule fragments (`fragments/<event>.md`) | Hold the text for one event: `session.md` (size table, worktree rule), `skill-brainstorming.md` (Spec → Plan flow, discovery authority), `docs-plans.md` (docs-layout, plan-format), `commit.md`, `merge.md`, `review.md`, `subagent.md` | The rule text | Files inside the plugin |
| Dispatcher (`method-hook.py`) | Matches event to marker to fragment, and enforces the 10,000-char cap with a test | None (stateless) | Hook command, runs once per event |
| Global CLAUDE.md (reduced) | Method-independent standards | Communication, Code, Critical Thinking, HTTP, dependencies | Always-loaded file (symlink) |
| Project CLAUDE.md | Facts: scopes, test command, plans index, remote, method name, "Parallel runs" | Project facts | Always-loaded file |
| `scaffold` skill (per method) | Writes or adapts the project CLAUDE.md facts and the marker; removes copied rules | None | Skill in the method plugin |

#### Connections

| From → To | What passes | Sync / async | When the receiver fails |
| --- | --- | --- | --- |
| Claude Code → Dispatcher | Hook JSON (event, tool input, cwd) | sync | Hook times out or errors: Claude Code goes on without the fragment. The session runs with no method rules, silently. |
| Dispatcher → Project marker | File read | sync | No marker: inject a one-line "no method set, run `<method>:scaffold`". Unknown name: say so. |
| Dispatcher → Rule fragment | File read, then `additionalContext` | sync | Fragment missing or over the cap: print an error line as context so the model sees it. A CI test blocks over-cap fragments. |
| Dispatcher (SubagentStart) → Subagent | `subagent.md` (commit-ID rule, Risk-is-not-a-finding) | sync | Same as above. Today this text is pasted into each review prompt by hand. |
| SessionStart `compact` → Model | `session.md` again | sync | Without it, fragments injected earlier are lost after compaction. |
| `scaffold` → Project CLAUDE.md | Edited file plus marker | sync | User reviews the diff and approves before writing. |

#### Forces

Served:

- 4 (Availability): every rule arrives through a hook on its event. The model never decides to load a method. The "invoke X first" triggers become injected text at the moment the Skill tool or a file write fires.
- 2 (Data volume) and 10 (10,000-char cap): about 30k chars of global rules plus 10.4k of docs-layout are split per event. No single injection nears the cap. Sessions that never touch `docs/plans/` or merge never load those parts.
- 5 (Consistency): each rule lives in one fragment. Project CLAUDE.md keeps facts only. Global keeps only method-free rules.
- 8 (Rate of change): editing a rule means editing one small fragment. Trying a new method means a new plugin plus one marker edit, with no rewrite of global CLAUDE.md.
- 1 (Load): the marker is read on each event, so 13 projects and parallel sessions each get their own method with no shared state.

Sacrificed:

- 3 (Latency): each event costs one Python start. That is small, and this force allows it anyway.
- Rule visibility: no one file shows the whole method in force. Ordering rules ("pick a size before brainstorming") rely on SessionStart text the model may have pushed out of focus by the time it acts.
- 9 (Cost): fragments can be injected several times per session, such as `docs-plans.md` on each plan write, unless the dispatcher deduplicates. Deduplicating needs per-session state, which this design avoids. This is minor because cost is assumed to matter only somewhat.

#### Hard-to-reverse decisions

- Marker format and location (CLAUDE.md line vs `.claude/method`). All 13 projects and every method's dispatcher read it.
- Event-to-fragment map: which rule fires on which event. A rule placed on the wrong event is absent exactly when it is needed. Moving rules later changes behaviour silently.
- Moving `global/rules/docs-layout.md` and `plan-format.md` out of `~/.claude/rules` (path-triggered by Claude Code) into hook-injected fragments. This swaps a native mechanism for a home-made one.
- All method plugins enabled at user scope, with the marker choosing between them. The alternative, project `enabledPlugins` as the marker, removes the dispatcher check but puts method choice in settings files.

#### Numbers it depends on

- Each fragment is under 10,000 chars. Superpowers Integration alone is about 14k today and must split across at least 2 events. Git Workflow (6.1k) and docs-layout (10.4k) also need splitting.
- Reduced global CLAUDE.md is under about 8k chars, down from 30.2k.
- About 6 to 8 event types cover every method-coupled rule. Each new rule must map to one.
- Dispatcher runs under 200 ms per event against a 10 s hook timeout. Several fire per commit.
- PreToolUse on the `Skill` tool, PostToolUse, and SubagentStart all accept `additionalContext`. Force 10 confirms this only for SessionStart. This must be checked before the design is chosen.

#### Weakest point

Many rules have no event. Size the change, challenge assumptions, "a bug starts with systematic-debugging", "no silent reinterpretation" and splitting a mixed row must all hold before any tool call. So in practice they all land in the SessionStart fragment, and this design then becomes "one SessionStart blob plus some late reminders". The late reminders also arrive after the moment they govern. For example, the commit rule ("read `git diff --cached`") injected on PostToolUse `git commit` comes after the commit. On PreToolUse it can only add context or block, and blocking every commit to inject text is heavy. A rule that arrives as `additionalContext` mid-task is also weaker than a standing instruction: the model reads it as a hint, not as the system prompt. Finally, the design rests on unconfirmed hook capabilities (Skill-tool matchers, `additionalContext` on PreToolUse and SubagentStart). It also rests on the assumed force 9: repeated injections are acceptable only if tokens matter "somewhat". If either fails, the event map collapses back to SessionStart, and the 10,000-char cap then forces the same split problem this shape was chosen to avoid.
