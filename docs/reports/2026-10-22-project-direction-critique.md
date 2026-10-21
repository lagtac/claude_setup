# Critique: where this project should go next

**Status:** current, 2026-10-22. Four findings (D1 to D4) on the direction of the harness; the user set rows 68, 69 and 74 as the priorities on 2026-10-21, and D1, D2 and D4 are not routed yet.

## How to read this report

| Document | Path | Why |
| --- | --- | --- |
| Workflow speed audit | [`docs/reports/2026-10-18-workflow-speed-audit.md`](2026-10-18-workflow-speed-audit.md) | The measured source for D1: where session time goes on zitamu. |
| Scriptable steps audit | [`docs/reports/2026-10-14-scriptable-skill-steps.md`](2026-10-14-scriptable-skill-steps.md) | The audit that row 74 repeats on more files (D3). |
| Roadmap | [`ROADMAP.md`](../../ROADMAP.md) | Holds the order of work. This report holds no order. |

Asked by the user on 2026-10-21: "can you think of a direction for this
project?" The answer was given in chat and is kept here so later sessions can
read it.

## Verdict

**Spend effort where the user's time goes, and stop the method from
growing.** The steps of the method are not what slows a row down; waiting
for the user is. Meanwhile the project mostly works on itself, and its
instruction text grows every week.

## Evidence, as measured on 2026-10-21

- Session time on zitamu: 56% waiting for the user, 18% the model working
  (speed audit, W1).
- Commits on `main` since 2026-09-21: 126 `docs`, 29 `feat`, 12 `fix`.
- Instruction text: about 37,000 words in the rules and the `my` skills.
  `my:handoff` `SKILL.md` alone holds about 10,900, and
  `global/methods/my.md` about 4,700. Most incidents end as a new paragraph;
  rules are rarely removed.
- Roadmap: 35 rows shipped, 32 open (2026-10-22). Most open rows refine
  `my:handoff`.
- Reviews earn their place: 90% of serious findings are caught before the
  code exists (speed audit, W4). Any change of direction keeps specs and
  reviews.

## Findings

### D1. The user's attention is the scarce resource

The rows that cut waits for the user exist but sit late in the order: 61
(approval starts the auto run), 55 (which decisions go back to the user), 53
and 54 (drafting and fixing while the user is away). A next step after them:
one place, such as a section of `my:status`, that collects every open
question from every session, so the user answers them in one sitting.

### D2. Hold the instruction text flat

Set a word budget per skill and rule file. A new rule then replaces or
removes text. Row 30 (split `my:handoff` so a stage loads only its own text)
need not wait for row 29.

### D3. Turn deterministic prose into scripts

Steps that fixed rules decide belong in tested scripts, not prose. This
shrinks text (D2) and makes behaviour testable. Rows 42 to 52 hold the
first audit's findings; row 74 repeats the audit on the method and rules
files too.

### D4. Judge the method by zitamu, and decide the outcome in advance

Run rows 72 and 29 on schedule, and say before the result what it changes.
For example: if two approved specs rarely wait at once, delete the row queue
and parallel runs instead of refining them. That would remove a large part
of `my:handoff` and rows 39, 42 and 56.

## The case against

- Live bugs (rows 33, 37 and 56) still come first.
- Row 68 is specced and planned; finishing it is reasonable.
- A word budget can push rules toward terse text, against the `plain`
  style. The budget must come from removing rules, not compressing them.
- Making the harness useful to others (row 17, row 68) is the other
  direction. Nothing shows anyone else uses it yet.

## Where these went

| Finding | Route |
| --- | --- |
| D1 | Not routed. Rows 61, 55, 53 and 54 keep their place in the order; the user did not move them up. The question collector has no row. |
| D2 | Not routed. No row for a word budget; row 30 still waits for row 29. |
| D3 | Row 74 "Find more prose that scripts can replace", third in the order, after rows 68 and 69 (user, 2026-10-21). |
| D4 | Not routed. Rows 72 and 29 keep their place; no stop rule is written. |

The user's priorities, set on 2026-10-21: row 68, then row 69, then row 74,
behind the `my:handoff` bugs 33, 37 and 56. Rows 33 and 37 shipped on
2026-10-22.
