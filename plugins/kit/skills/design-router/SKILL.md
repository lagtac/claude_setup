---
name: design-router
description: Decide which design skill does a design job, and start it. Use before any design work, in any project - visual direction, a critique of a screen, canvas or flow, an accessibility audit, interface copy, planning user research, auditing or extending a design system in code, designing tokens, interactions and motion, polishing a screen, a developer handoff spec, a research synthesis, a journey map, product strategy, drawing a screen, a diagram, a chart. A gate refuses Claude's direct calls to design skills, so this skill is the way to start one. NOT for the design work itself - the skill it starts does that.
---

# Design router

Several design plugins hold skills that do the same job. This skill picks one
skill per job and starts it. A gate (the `design-router-gate.py` hook in
`kit`) refuses Claude's calls to design skills unless this skill wrote a
one-time ticket for the call first. A command the user types always runs.

## Steps

Each time this skill runs:

1. **Name the job.** Match the request to one row of the table below. If no
   row fits, say so in one line, and do the work without a design skill.
2. **Look up the choice.** Read `.claude/design-router.json` at the project
   root, if it exists. Its entry for the job wins when it names a skill in
   that job's row. Report an entry for an ID the table lacks, or for a skill
   not in the row, in one line, and ignore it.
3. **Check the skill is here.** If the chosen skill is not in this session's
   skill list, say which plugin is off and stop. The user may have turned
   design plugins off in this scope.
4. **Decided job:** say in one line which skill and why. Run
   `design-router-ticket.py <skill>`, then call the skill with the arguments
   filled in.
5. **Undecided job:**
   - When a user can answer, ask "A, B, or both?", with one line on each
     skill. For A or B, go on as in step 4. For both, see "Both" below.
   - When no user can answer, take the project's winner, or else A, go on as
     in step 4, and say which skill ran and that the job is undecided. No user
     can answer in a headless run (`printenv CLAUDE_CODE_SESSION_ATTENDED`
     prints `0`), in a subagent, or in a run whose prompt says it runs
     without the user, such as an auto hand-off.
6. **Chain:** when a job needs several skills, list them in order, numbered,
   and treat each as above.

If the ticket script fails, say so, and print the command for the user to
type instead: `/<skill> <arguments>`. If the gate still refuses the call
after the ticket, do not invoke `kit:design-router` again: say so, and print
the same command.

A skill with no plugin prefix, such as `artifact-diagramming` or `dataviz`,
and the Artifact tool's Design type, are started directly: the gate never
refuses them.

The line before a decided job's call, for example:

```text
Accessibility audit with design-skills:accessibility-audit: WCAG 2.2 checks on live HTML and code. It names VoiceOver and NVDA only; on Linux, test with Orca.
```

## The table

The ID is the key in `.claude/design-router.json`.

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

A single-skill row is "decided" because no other skill that is turned on does
that job. "Open" rows name a tool that no plugin owns; the gate never refuses
them. The `product-management` and `data` plugins are installed but turned
off, and `excluded` in `plugins.json`, so the gate refuses them if they are
turned on; so is `design-superpowers`. Two skills are never named:
`design:accessibility-review`, which lists rule 2.5.5 (44×44 targets) as AA
while WCAG 2.1 has it as AAA, and `design-skills:design-ops`, which runs team
processes while the user works alone.

The undecided rows carry what a trial should look for:

- `critique`: whether B's principle names lead to better fixes or only more
  text, and whether A's design system check works without Figma.
- `copy`: whether B's US English rules for casing and dates misfire on a UI in
  another language, and whether A's table of alternatives speeds up the
  choice.
- `research-plan`: whether B's team sections drop out cleanly, and whether A
  gives enough to act on.

## Both

1. Write the brief: the job, the material (paths, links, the request in the
   user's words), and three rules: use only the named skill; do not invoke
   `kit:design-router`; change no file, and return the result as the answer.
2. Start two subagents in one message, one per skill. Each prompt holds the
   brief and tells the subagent to run `design-router-ticket.py <its skill>`,
   then call that skill. The tickets are per skill, so both can wait at once.
3. When both answer, compare the two results against the trial points of that
   row. Say which is better and why.
4. Ask which skill won. Write `{"<job ID>": "<winner>"}` into
   `.claude/design-router.json`, keeping the other entries, and tell the user
   the file needs a commit. Never commit it.

Both results come back into the session's context, so "both" costs the two
skills' text and two results there.

## The project file

`.claude/design-router.json` at the project root holds one object, job ID to
skill, for example `{"critique": "design-skills:design-critique"}`. An entry
overrides the table's default for that job in this project. This skill writes
it after a "both" trial, and never commits it: the project's normal flow
does.
