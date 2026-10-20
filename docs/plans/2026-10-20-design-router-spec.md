# Spec: the design router decides which design skill runs

**Status:** draft, 2026-10-20. Row 70; waiting for the user's approval.

**Route:** architectural with plan. A gate that refuses skill calls in every project is a change
to permissions, which is the risk line in `global/methods/my.md`. `my:architect` was skipped with
the user's approval on 2026-10-20. Its trigger matches, because the gate is a new subsystem with
a contract. But brainstorming had already compared the options, and the method runs
`my:architect` before brainstorming, never during it.

## How to read this spec

1. `ROADMAP.md`, rows 69 ("Shared skills move to `kit`") and 70 ("Choose the design skill"). This
   spec is row 70's answer, and it changes row 69's premise.
2. `docs/plans/2026-10-16-design-system-skill-spec.md`. The skill whose rules this spec removes
   from the method.
3. `docs/plans/2026-10-18-brainstorming-routes-spec.md`, section "Risk": the two limits row 67
   left for row 70 ("The design-system audit's timing is unclear" and "A bounded UI change skips
   the UI checks").
4. `docs/plans/2026-10-20-method-bundles-architecture.md`, sections "Candidate A" and "Decision".
   Row 68's approved brief: `kit` stays always on, the core stays always loaded, and the user
   scope turns heavy plugins off.
5. `global/methods/my.md`, sections "Pick the route" (the trigger table, line 117), "Spec → Plan
   two-artifact flow" (step 1) and "UI Design". The rules this spec changes.
6. `global/rules/docs-layout.md`, step 13 of "One feature, four commits on `main`".
7. `plugins/kit/hooks/hooks.json` and `plugins/kit/hooks/method-guard.py`. The pattern the gate
   follows.
8. `plugins/kit/tests/test_neutral_core.py`. The test that keeps `kit` free of method names.
9. The skills the router names, under
   `~/.claude/plugins/synced/<account>/<plugin id>/skills/`: the `design` plugin (7 skills) and
   the `design-skills` plugin (10 skills), and `frontend-design` from `claude-plugins-official`.

## Context

Three plugins of design skills are installed: `design` (7 skills), `design-skills` (10) and
`design-superpowers` (9). Several do the same job: three critique skills, two accessibility
skills, two copy skills, two research skills, and four design-system skills. Each can start on
its own when Claude matches its description to the task. So the skill that runs is chance, not a
choice.

The method calls `my:design-system`, and its rules in `my.md`, `docs-layout.md`, `my:handoff` and
`my:spec-review` depend on its inventory, `docs/DESIGN-SYSTEM.md`. The user has not used it on a
real project yet. On 2026-10-19 the user asked to stop Claude from starting it, and to remove its
rules from the method.

Facts checked in Claude Code 2.1.303 and 2.1.304 on 2026-10-19 and 2026-10-20:

- F1. `skillOverrides` in user, project or local settings does not reach plugin skills. Only
  admin settings reach them, and only for the `synced` marketplace.
- F2. A `deny` rule `Skill(<plugin>:*)` blocks every skill of that plugin for Claude.
  `Skill(<plugin>)` without `:*` blocks nothing.
- F3. An `ask` rule on `Skill` has no effect, in auto mode or in default mode.
- F4. A command the user types runs even under a `deny` rule. A slash command given as a new
  session's first prompt counts as typed, also in an interactive session in tmux.
- F5. A `PreToolUse` hook with the matcher `Skill` receives `{"skill": "<name>"}` and can refuse
  the call with `permissionDecision: "deny"`, also in auto mode. A typed command never reaches it.
- F6. A skill's description alone does not make it start reliably. The method says so for recent
  models.
- F7. The `PreToolUse` input also holds `session_id`, `transcript_path`, `permission_mode` and
  `cwd`. A subagent's call carries its parent's `session_id`, plus `agent_id` and `agent_type`.
  A test gate that let a call through only when a ticket file named the session and the skill
  refused the first call, let the second through and deleted the ticket, and refused the third.
- F8. Commands run by Claude see `CLAUDE_CODE_SESSION_ID`, the same ID as the hook's
  `session_id`, and `CLAUDE_CODE_SESSION_ATTENDED`: `1` in an interactive session, `0` in a
  headless run. A subagent sees its parent's values.

A subagent read the five pairs of overlapping skills in full on 2026-10-20 (D5).

## Goal

1. No third-party design skill starts unless the router or the user chose it.
2. One skill, `kit:design-router`, decides which design skill does each job, and starts whenever
   design work comes up, in every project.
3. Where two skills compete for a job, the user can try both on real work, and the winner is kept
   per project.
4. The method no longer depends on `my:design-system`.

## Out of scope

- Whether `my:design-system` moves to `kit` or is deleted. Row 69 decides that.
- Moving method rules into plugins. Row 68 does that, and it starts from the text this spec
  leaves.
- Writing or changing any design skill.
- Per-skill rules inside one plugin (see Risk R3).

## Decisions

- **D1. A gate, not `deny` rules.** A `PreToolUse` hook in `kit` refuses Claude's skill calls by
  plugin (F5). It replaces hand-written `deny` rules in user settings, and a session-start check
  that they exist. It runs only when Claude calls a skill. It ships with `kit`, so every machine
  with `kit` has it. A typed command passes (F4, F5).
- **D2. The router starts the skill itself, with a one-time ticket.** Before it calls a skill, the
  router runs `design-router-ticket.py <skill>`, which writes a ticket for this session and this
  skill. The gate lets a call through when it finds a fresh ticket for that session and skill, and
  deletes it (F7, F8). A call with no ticket is refused, so a skill that starts because its
  description matched is still refused. For an undecided job, the router asks "A, B, or both?"
  when a user can answer. When none can, it takes the project's winner, or else option A, and
  says so. This replaces "the router names, the user types": typing was a workaround after `ask`
  rules turned out to have no effect (F3), and the user's request was a router that decides.
- **D3. "Both" runs in two subagents.** Each subagent runs one skill on the same brief, with its
  own ticket (F7). Each has its own context, so neither sees the other's result. Each returns its
  result as its answer and changes no file. The router compares the two. Subagents run in the
  session's permission mode and always return, so nothing waits unseen in another window.
- **D4. Decided and undecided jobs.** The router's table gives each job a fixed ID and a default:
  one skill (decided) or two (undecided). A project file `.claude/design-router.json` overrides
  the default per job. It is committed with the project's normal flow; the router writes it but
  never commits.
- **D5. The first table.** From the 2026-10-20 reading:
  - Accessibility: `design-skills:accessibility-audit`. It uses WCAG 2.2, checks live HTML and
    code, and needs no connector. `design:accessibility-review` lists rule 2.5.5 (44×44 targets)
    as AA; in WCAG 2.1 it is AAA.
  - Design system in code: `design:design-system`. Its audit checks code for raw values and names,
    and its `document` and `extend` modes write component specs. The audit in
    `design-skills:design-systems` is a team workshop.
  - Token design from scratch: `design-skills:design-systems`, the only one with three-tier tokens
    and dark-theme overrides.
  - Critique, copy and research planning stay undecided.
- **D6. The trigger lives in the core.** One section in `global/CLAUDE.md` sends all design work
  to the router. The gate applies everywhere, so the trigger must too; a method row would reach
  only projects of that method. `my.md` names jobs and the router, never a third-party design
  skill. The Artifact tool's Design type and `artifact-diagramming` stay in `my.md`.
- **D7. Unknown plugins are refused.** A prefix that names an installed plugin missing from
  `plugins.json` is refused, with the steps to review it. The user chose this over "allow with a
  note". A prefix that names no installed plugin passes: project skills in subfolders appear as
  `<folder>:<name>`, and claude.ai skill sets use their own prefixes.
- **D8. The gate fails open.** A missing or broken `plugins.json`, or a crash, refuses nothing. A
  broken list must not block every plugin skill in every project. `kit`'s own skills are never
  refused, so the router can always run.
- **D9. `frontend-design` is routed.** It rarely starts on its own today, but a competing skill may
  arrive. Every third-party design skill follows the same rule.
- **D10. The `my:design-system` rules leave the method.** Its `deny` rule stays in the user's
  settings, because `kit` must not name a `my` skill. Row 69 decides the rest.

## Design

### `kit:design-router`

`plugins/kit/skills/design-router/SKILL.md`. Its description lists the jobs below, so it can also
start on its own in a project whose core line is missing. It names no method, no `docs/plans`
and no `my:` skill.

Steps each time it runs:

1. **Name the job.** Match the request to one row of the table. If no row fits, say so in one
   line, and do the work without a design skill.
2. **Look up the choice.** Read `.claude/design-router.json` at the project root, if it exists.
   Its entry for the job wins when it names a skill in that job's row. An entry for an ID the
   table lacks, or for a skill not in the row, is reported in one line and ignored.
3. **Check the skill is here.** If the chosen skill is not in this session's skill list, say which
   plugin is off and stop. Under row 68, the user scope may turn design plugins off.
4. **Decided job:** say in one line which skill and why. Run `design-router-ticket.py <skill>`,
   then call the skill with the arguments filled in.
5. **Undecided job:**
   - When a user can answer, ask "A, B, or both?", with one line on each skill. For A or B, go on
     as in step 4. For both, see "Both" below.
   - When no user can answer, take the project's winner, or else A, go on as in step 4, and say
     which skill ran and that the job is undecided. No user can answer in a headless run
     (`CLAUDE_CODE_SESSION_ATTENDED=0`), in a subagent, or in a run whose prompt says it runs
     without the user, such as an auto hand-off.
6. **Chain:** when a job needs several skills, list them in order, numbered, and treat each as
   above.

If the ticket script fails, say so, and print the command for the user to type instead.

A skill with no plugin prefix, such as `artifact-diagramming` or `dataviz`, and the Artifact
tool's Design type, are started directly: the gate never refuses them.

The line before a decided job's call, for example:

```text
Accessibility audit with design-skills:accessibility-audit: WCAG 2.2 checks on live HTML and code. It names VoiceOver and NVDA only; on Linux, test with Orca.
```

**The table.** The ID is the key in `.claude/design-router.json`.

| ID | Job | Skill or skills | State |
| --- | --- | --- | --- |
| `visual-direction` | Visual direction, typography, a look that avoids template defaults | `frontend-design:frontend-design` | decided |
| `critique` | Critique a screen, canvas or flow | A `design:design-critique`, B `design-skills:design-critique` | undecided |
| `accessibility` | Accessibility audit | `design-skills:accessibility-audit` | decided |
| `copy` | Interface copy: buttons, errors, empty states | A `design:ux-copy`, B `design-skills:ux-writing` | undecided |
| `research-plan` | Plan user research or a usability test | A `design:user-research`, B `design-skills:ux-research` | undecided |
| `system-audit` | Audit, document or extend a design system in code | `design:design-system` | decided |
| `tokens` | Design a token system from scratch | `design-skills:design-systems` | decided |
| `interaction` | Interactions, states, motion | `design-skills:interaction-design` | decided |
| `polish` | Polish a working screen | `design-skills:design-elevation` | decided |
| `handoff` | Developer handoff spec | `design:design-handoff` | decided |
| `research-synthesis` | Sum up research findings | `design:research-synthesis` | decided |
| `journey-map` | Journey map, service blueprint | `design-skills:journey-mapping` | decided |
| `strategy` | Product strategy, competitor analysis | `design-skills:ux-strategy` | decided |
| `draw` | Draw a screen, state or flow | the Artifact tool's Design type | open |
| `diagram` | Diagram a mechanism | `artifact-diagramming` | open |
| `chart` | Chart or dashboard | `dataviz` | open |

A single-skill row is "decided" because no other skill that is turned on does that job.
`product-management` (with `competitive-brief` and `synthesize-research`) and `data` (with chart
and dashboard skills) are installed but turned off, and `excluded` in `plugins.json`, so the gate
refuses them if they are turned on. Two skills are
never named: `design:accessibility-review` (D5) and `design-skills:design-ops`, which runs team
processes while the user works alone.

The undecided rows carry what a trial should look for, from D5:

- `critique`: whether B's principle names lead to better fixes or only more text, and whether A's
  design-system check works without Figma.
- `copy`: whether B's US English rules for casing and dates misfire on a UI in another language,
  and whether A's table of alternatives speeds up the choice.
- `research-plan`: whether B's team sections drop out cleanly, and whether A gives enough to act
  on.

### Both

1. Write the brief: the job, the material (paths, links, the request in the user's words), and
   three rules: use only the named skill; do not invoke `kit:design-router`; change no file, and
   return the result as the answer.
2. Start two subagents in one message, one per skill. Each prompt holds the brief and tells the
   subagent to run `design-router-ticket.py <its skill>`, then call that skill. The tickets are
   per skill, so both can wait at once.
3. When both answer, compare the two results against the trial points of that row. Say which is
   better and why.
4. Ask which skill won. Write `{"<job ID>": "<winner>"}` into `.claude/design-router.json`,
   keeping the other entries, and tell the user the file needs a commit. Never commit it.

Both results come back into the session's context, so "both" costs the two skills' text and two
results there.

### The ticket

`plugins/kit/bin/design-router-ticket.py <skill>`, on `PATH` like the other scripts in `kit`'s
`bin/`. It writes an empty file `~/.cache/design-router/tickets/<session id>/<skill>`, with the
session ID from `CLAUDE_CODE_SESSION_ID`. It exits 1 with one message when that variable is empty
or the file cannot be written. One file per skill lets two tickets wait at once.

A ticket is fresh for 5 minutes after it is written. The gate deletes a stale ticket it finds and
refuses the call. So a ticket the router wrote but never used cannot let a later accidental start
through.

### `plugins.json`

`plugins/kit/skills/design-router/plugins.json`: one object, plugin name to state. The name is
the skill prefix before `:`, which is all the gate sees.

| State | Meaning |
| --- | --- |
| `routed` | The router names its skills. The gate refuses them. |
| `excluded` | A design plugin the router does not use. The gate refuses it. It should stay off. |
| `not-design` | No design skills. The gate lets it through. |

The first version lists every prefix in the skill list of the session on 2026-10-20, plus every
plugin in `~/.claude/plugins/installed_plugins.json` and under `~/.claude/plugins/synced/`:
`routed` for `design`, `design-skills` and `frontend-design`; `excluded` for
`design-superpowers`, `product-management` and `data`; `not-design` for the rest.

### The gate

`plugins/kit/hooks/design-router-gate.py`, registered in `plugins/kit/hooks/hooks.json` for
`PreToolUse` with the matcher `Skill`, timeout 10 seconds. It reads the hook's JSON on stdin.

| Input | Output |
| --- | --- |
| No `tool_input.skill`, or a name with no `:` | nothing |
| Prefix `kit` | nothing |
| A fresh ticket `tickets/<session_id>/<skill>` exists | delete it; nothing |
| Prefix `routed` | refuse: `<skill> is a design skill: invoke kit:design-router, which starts it.` |
| Prefix `excluded` | refuse: `<plugin> is excluded from the design router: tell the user, who can type the command or turn the plugin off.` |
| Prefix `not-design` | nothing |
| Prefix not in the list, and an installed plugin | refuse: `<plugin> is not reviewed for design skills: tell the user to add it to plugins.json in kit's design-router skill, commit, then run claude plugin update kit@claude-setup and /reload-plugins; or to type the command.` |
| Prefix not in the list, and no installed plugin | nothing |
| `plugins.json` missing or not valid JSON | `{"systemMessage": "Design router gate: cannot read <path>; it lets every skill through."}`, with no decision |
| Any other error | nothing; exit 0 |

A hook's stderr is not shown when it exits 0, so the note goes in `systemMessage`, which the user
sees.

"Refuse" prints
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "<text>"}}`.
The gate never prints `allow`, because that would skip the user's permission prompts. It always
exits 0. It finds `plugins.json` through `$CLAUDE_PLUGIN_ROOT`. The installed plugins are the keys of
`.plugins` in `~/.claude/plugins/installed_plugins.json`, by the name before `@`, and the `name`
in each `~/.claude/plugins/synced/*/*/.claude-plugin/plugin.json`. Tickets live under
`~/.cache/design-router/tickets/`. A test may point these elsewhere with `DESIGN_ROUTER_PLUGINS`,
`DESIGN_ROUTER_PLUGIN_HOME` (in place of `~/.claude/plugins`) and `DESIGN_ROUTER_TICKETS`.

### Row 67's two limits

- **When the audit runs.** The method no longer runs `my:design-system audit`, so its timing no
  longer matters.
- **The checks a bounded UI change skips.** The core line sends a bounded change's design work to
  the router like any other, so a critique or an accessibility audit can run on it. It still has
  no spec, so no Visual Language section and no check of its shared components. That stays a
  known limit, as before.

### The core line

`global/CLAUDE.md` gets a section "Design work", after "Code":

> Before any design work — a screen, a flow, visual direction, interface copy, an accessibility
> check, a design system, user research — invoke `kit:design-router`. It names the skill for the
> job. Do not call a design skill directly; the gate refuses it.

`test_core_names_no_method` allows a `kit:` name.

### `global/methods/my.md`

- Delete the trigger-table row "UI work (a screen, a state or a component) in an architectural
  change, with or without a plan, in a project with no `docs/DESIGN-SYSTEM.md`".
- In step 1 of "Spec → Plan two-artifact flow", delete the clause "the spec reads
  `docs/DESIGN-SYSTEM.md` first … as a shared component". The rest of the Visual Language rule
  stays.
- In "UI Design", the `frontend-design` bullet becomes: "**Aesthetic direction** — typography,
  and choices that do not read as templated defaults. `kit:design-router` names the skill."
- Delete the paragraph "The canvas is built on the project's Design System artifact …", and the
  sentence "The same step refreshes the inventory: see step 13 …".

### Other edits

| File | Edit |
| --- | --- |
| `global/rules/docs-layout.md` | Delete step 13's `my:design-system refresh` lines. |
| `plugins/my/skills/handoff/SKILL.md` | Take `docs/DESIGN-SYSTEM.md` off the shared-doc lists (stop-point row 19 and the "Parallel runs" step). |
| `plugins/my/skills/handoff/README.md` | The same, in the "Shared docs" bullet. |
| `plugins/my/skills/spec-review/spec-reviewer-prompt.md` | Delete the four lines that check a Visual Language section against `docs/DESIGN-SYSTEM.md`. |
| `plugins/my/skills/design-system/SKILL.md` | Line 176: "That row's canvas uses `frontend-design`" becomes "takes its visual direction through `kit:design-router`". |
| `plugins/kit/tests/test_neutral_core.py` | A `my` name matches only as a whole name: not after `:` or a letter, digit or `-`, and not before a letter, digit or `-`. |
| `README.md` | An entry for `kit:design-router` and its gate. The `my:design-system` entry says the method no longer calls it. |
| `ROADMAP.md` | Row 70 becomes 🚧 and links this spec. Row 69's `design-system` part: its rules left the method in row 70; row 69 decides whether the skill moves to `kit` or is deleted. |
| `CHANGELOG.md` | An entry at the `done` mark. |

The saved patch from 2026-10-19 holds the deletions, but it was made before row 67 merged. The
plan redoes them by hand on the current text.

### The user's settings

Outside the repo, by hand, at the `done` mark: turn off `design-superpowers@synced` in
`~/.claude/settings.json`. The `deny` rule for `my:design-system`, set on 2026-10-19, stays.

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `cd plugins/kit && python3 -m unittest discover tests`, `cd plugins/my && python3 -m unittest discover tests`

## Files

| File | New or changed |
| --- | --- |
| `plugins/kit/skills/design-router/SKILL.md` | New |
| `plugins/kit/skills/design-router/plugins.json` | New |
| `plugins/kit/hooks/design-router-gate.py` | New |
| `plugins/kit/bin/design-router-ticket.py` | New |
| `plugins/kit/tests/test_design_router.py` | New |
| `plugins/kit/hooks/hooks.json` | Changed |
| `plugins/kit/tests/test_neutral_core.py` | Changed |
| `global/CLAUDE.md` | Changed |
| `global/methods/my.md` | Changed |
| `global/rules/docs-layout.md` | Changed |
| `plugins/my/skills/handoff/SKILL.md` | Changed |
| `plugins/my/skills/handoff/README.md` | Changed |
| `plugins/my/skills/spec-review/spec-reviewer-prompt.md` | Changed |
| `plugins/my/skills/design-system/SKILL.md` | Changed |
| `README.md` | Changed |
| `ROADMAP.md`, `CHANGELOG.md` | Changed at the spec commit and the `done` mark |

## Trade-offs

- **How a chosen skill starts.**
  - A prompt per call (`ask` rule): cannot work (F3).
  - The router reads the skill's file and follows it: goes around the user's own block, and the
    file paths hold IDs that change on updates.
  - The user types the command: no code, and every start is the user's own. It costs one typed
    line per job, and it cannot work where no user can type.
  - A one-time ticket that the router writes before its own call: chosen (D2). The router
    decides, as the user first asked, also where no user can answer. It stops accidental starts,
    not a session that writes a ticket on purpose (R10).
- **How the block is enforced.**
  - `deny` rules in user settings: no code, but set by hand on each machine, and they need a check
    that they exist.
  - A gate in `kit`: chosen (D1). It runs only on skill calls and ships with `kit`. It fails open
    (D8).
- **Where the trigger lives.**
  - A row in `my.md`: reaches only `my` projects, while the gate applies everywhere.
  - A hook on every prompt that looks for design words: guesses wrong both ways, and runs on every
    message.
  - The core: chosen (D6).
- **Unknown plugins.** Refused (chosen, D7), or allowed with a note. Refusing can block a new
  plugin's skills for Claude until it is reviewed. Typed commands still work.
- **Where a winner is kept.** The `kit` table (one place, but every project shares one answer, and
  writing it from another project means a commit in this repo), or a file per project (chosen,
  D4). A winner from one project does not carry over; when the same skill wins in several, move it
  into the table.
- **Choosing pairs up front or by trial.** Reading decided two of five pairs and corrected one job
  split. Only trials on real work can settle the other three, so they stay undecided.

## Dependencies

- Row 67, merged in `f03b0e3`. This spec edits the text it left in `my.md`.
- Row 68 (methods as plugins) will move `my.md` into a plugin output style, and `docs-layout.md`
  into a skill. It must start from the text this spec leaves. Its planned `kit:skill-overlap`
  reports clashing skills; the router decides between them, so they do not overlap.
- Row 69 decides `my:design-system`'s place.
- Claude Code 2.1.304 or later: the `PreToolUse` hook input and the `deny` decision (F5).
- Python 3, standard library only. No new dependency.

## Risk

- **R1. The gate fails open.** A crash, a timeout or a broken `plugins.json` lets every skill run,
  which is today's behaviour. Detect: the tests, and the `systemMessage` for a broken file.
- **R2. Names, not marketplaces.** The gate sees only the prefix. Two plugins with the same name
  from different marketplaces share one entry.
- **R3. Whole plugins.** A state covers a whole plugin. A future plugin that mixes design skills
  with others would have all its skills refused. None of the three routed plugins mixes today.
- **R4. New plugins are refused.** A plugin installed later is refused for Claude until it is
  reviewed, which takes an edit, a commit and a plugin update; the refusal text says so. A new
  claude.ai skill set is not a plugin, so it passes unreviewed.
- **R5. A removed or turned-off plugin.** The router checks its chosen skill is in the session
  (step 3). A project file that names a removed skill is reported and ignored.
- **R6. "Both" relies on the brief.** Each subagent is told to change no file. One that ignores
  it can still edit project files, and two could edit the same file.
- **R7. The core line is an instruction.** A session can skip the router. The gate then refuses
  the design skill, and its text points to the router.
- **R8. Hard to reverse: nothing.** Every part is a file in this repo or one settings key.
  Blast radius: every session on this machine, through `kit`'s hook and the core.
- **R9. The table is a snapshot.** Picks come from reading the skills, not from use. The undecided
  rows and the project file let real work correct them.
- **R10. A ticket is not a lock.** Claude can run the ticket script without the router. The gate
  stops a skill that starts because its description matched, which writes no ticket first; it
  does not stop a session that means to go around it.
- **R11. The ticket write may ask for permission.** It writes under `~/.cache`, outside the
  project. In default mode that may prompt; the rehearsal checks it. The script lives in `kit`'s
  `bin/`, so one allow rule for it covers every project.
- **R12. Without a user, an undecided job runs option A.** That can be the weaker skill. The
  router says so, and the project file corrects it once a trial picks a winner.
- **R13. The project file is in a protected folder.** Writing `.claude/design-router.json` may ask
  for permission. It happens once per winner.

Manual steps: the user setting at the `done` mark, and the rehearsal below.

## Testing strategy

`plugins/kit/tests/test_design_router.py`, run with `cd plugins/kit && python3 -m unittest
discover tests`. The gate tests run the real script with `subprocess`, feeding it the JSON that
Claude Code sends, and point it at a fixture list with `DESIGN_ROUTER_PLUGINS`.

| Test | Asserts |
| --- | --- |
| `test_routed_is_refused` | `design-skills:design-critique` → `permissionDecision` is `deny`, reason names `kit:design-router` |
| `test_excluded_is_refused` | `design-superpowers:design` → `deny`, reason says excluded |
| `test_unknown_plugin_is_refused` | `newplug:thing`, with `newplug` installed in the fixture home → `deny`, reason names `plugins.json` and `claude plugin update` |
| `test_unknown_prefix_passes` | `somefolder:thing`, no such plugin installed → empty stdout |
| `test_not_design_passes` | `superpowers:brainstorming` → empty stdout, exit 0 |
| `test_no_prefix_passes` | `dataviz` → empty stdout |
| `test_kit_passes` | `kit:design-router` with `kit` absent from the list → empty stdout |
| `test_missing_list_fails_open` | list path does not exist → stdout has no `permissionDecision`, its `systemMessage` names the path, exit 0 |
| `test_broken_list_fails_open` | list is not JSON → the same |
| `test_ticket_lets_one_call_through` | a ticket for the session and skill → empty stdout, and the ticket is gone; the same call again → `deny` |
| `test_ticket_is_per_session` | a ticket under another session ID → `deny` |
| `test_ticket_is_per_skill` | a ticket for another skill → `deny` |
| `test_stale_ticket_is_refused` | a ticket older than 5 minutes → `deny`, and the ticket is gone |
| `test_ticket_script_writes` | `design-router-ticket.py design-skills:ux-writing` with `CLAUDE_CODE_SESSION_ID` set → the file exists under that ID |
| `test_ticket_script_needs_session` | the same with the variable empty → exit 1, no file |
| `test_never_allows` | across all cases, stdout never contains `"allow"` |
| `test_hooks_json_registers_gate` | `hooks.json` has a `PreToolUse` entry, matcher `Skill`, command naming `design-router-gate.py` |
| `test_list_states_are_valid` | every value in the real `plugins.json` is `routed`, `excluded` or `not-design` |
| `test_table_ids_unique` | the IDs in the router's table are unique |
| `test_table_skills_known` | every skill in the table has a `routed` prefix, or is `artifact-diagramming`, `dataviz` or the Design type |
| `test_every_routed_plugin_used` | every `routed` plugin has a skill in the table |
| `test_undecided_rows_have_two` | each undecided row names exactly two skills; each decided row one |

`test_neutral_core.py` gains `test_whole_name_match`: `design:design-system` and
`design-skills:design-systems` pass; a bare `design-system` in a `kit` file still fails. The
router's job IDs avoid `my` names for the same reason: the design-system job is `system-audit`.

Each test fails before its code exists: the gate tests on the missing script, the table tests on
the missing `SKILL.md`.

**Rehearsal**, by hand before the `done` mark, with the branch's `kit` loaded through
`--plugin-dir`:

1. Claude calls `design-skills:ux-writing` → refused with the router text.
2. The user types `/design-skills:ux-writing` → it runs.
3. The router on an accessibility request → it writes the ticket and starts
   `design-skills:accessibility-audit` itself. Record whether the ticket write asked for
   permission (R11).
4. The same in `claude -p` → it runs with no user, and an undecided job takes option A.
5. Every prefix in `/context` is in `plugins.json`.
6. The router on a critique request in a scratch project, answering "both" → two subagents run,
   each with its own ticket, neither changes a file, and the router compares them and writes
   `.claude/design-router.json`. Record whether that write asked for permission (R13).

## Open questions

None. The three undecided pairs are settled by use, not by this spec.
