---
name: briefing
description: >
  Use when authoring a briefing — a plain-English, decision-oriented write-up of
  technical work for a NON-technical audience (stakeholders, reviewers, end
  users, funders, execs). Trigger on "write a briefing", "brief the
  stakeholders", "explain X for non-technical readers", "stakeholder one-pager",
  or whenever someone needs a derived plain-English view of engineer-facing docs
  (run/results logs, plans, specs, commits). Owns briefing structure,
  source-grounding discipline, and the docs/briefings/ convention. NOT for
  dev-facing "explain this spec so I can build it" (different register) and NOT
  for CHANGELOG/ROADMAP edits.
---

# Briefing Authoring

A briefing is a **derived, plain-English view** of engineer-facing source docs,
for someone who decides about the work but doesn't read code or logs. It answers
a specific moment — a result landed, a decision is pending, an ask is needed —
not a status dump.

The craft is three disciplines, not a template. Get them right and the sections
write themselves. Prose mechanics and the polish pass live in **`STYLE.md`**
(bundled alongside this skill) — read it before drafting.

## The three disciplines

1. **A derived view, never the source of truth.** Name the companion doc(s) at
   the top and defer to them for detail. *Precondition, checked at invocation:*
   the ground-truth doc must already exist. If it doesn't, stop — you'd be
   inventing, not deriving. Say so and redirect (brief the plan, or wait for the
   result to be written).

2. **Every number traces to a cited source.** The dominant failure is pretty
   prose that distorts facts. Find each figure in the source and carry it across
   unchanged. Round honestly and flag it (`~52%`, not a false-precision `51.7%`).
   Never invent a number to make a sentence flow.

3. **Honesty over hype.** Movement inside the noise band is not a result — say
   so. Name what the work does **not** fix or mean; those sections earn the
   trust. Report your own mistakes plainly. No cheerleading, no "leverage", no
   "comprehensive".

## What event are you briefing?

You were triggered, so *whether* is settled. Classify the **event** — it sets the
shape and the source doc:

1. **A result landed (default).** Source = the run's results/log doc. Sequence is
   **run → log → brief**.
2. **A decision needs sign-off** — a re-prioritisation, a parked option, a fork.
   Source = the plan/spec. Only when the plan encodes a *stakeholder* choice, not
   internal execution detail.
3. **A long-running job, at kickoff** — the one case that precedes results.
   "We've started, here's the approach and why" is the event. Source = the
   plan/recipe. Then **append dated updates to the same file**; don't start a new
   briefing.

If none fits, recheck the Discipline 1 precondition before writing.

## Before you write

1. **Name the audience and its literacy** in the metadata, so register and jargon
   budget are deliberate. Multiple audiences → tag each ask (see `STYLE.md`, a sibling to this file).
2. **Gather the source docs** — results/log, plan/spec, commit. These are your
   ground truth and your companion links.
3. **Extract every claim with its source** before writing prose. Discipline 2,
   made operational.

## Structure (default shape — adapt to the event)

Not every briefing needs every section; a short update may be TL;DR + one
decision. Let the event decide.

1. **Title** — a narrative line, not a label.
2. **Metadata** — `Date`, `Audience`, and **Companion / Full detail** links to
   the source docs.
3. **`## TL;DR`** — headline + 2–4 load-bearing bullets. A reader who stops here
   still gets the decision or ask.
4. **Body** — the plain-English translation. One concern per `##` section.
5. **What this does NOT mean / fix** — bound the scope; pre-empt wrong
   conclusions. Often the most valuable section.
6. **The honest caveat** — sample size, noise floor, what's still uncertain.
7. **The ask / decision** — audience-tagged, priority-ordered, concrete. End
   here.
8. **Appendix** — exact values, "skip unless curious".
9. **Dated `## Addendum`** — append as things evolve; never silently rewrite a
   shipped briefing.

## Polish pass (optional)

Discipline 3 keeps slop out at write time; this is a safety net. After drafting,
run a de-slop / humanizing pass if you have one. Two briefing-specific guardrails
in `STYLE.md` — don't flatten the structured bullets/tables, and don't strip real
caveats or numbers.

## Conventions

- **Location:** if the host project already has a briefings location/format,
  follow it. Otherwise default to `docs/briefings/YYYY-MM-DD-<slug>.md`. Engineer
  docs stay wherever they already live; don't invent new trees.
- **Companion linking:** always link back to the source doc, with relative paths.

## Common mistakes

- **Distorting a number to make prose flow.** The cardinal sin.
- **A status dump instead of an answer.** If it doesn't end on a decision or ask,
  ask what it's for.
- **Burying the bad news.** "What this does NOT fix" is where trust is earned.
- **Celebrating noise.** Movement inside the noise band isn't a result.
- **Untagged asks** when multiple audiences must act.
- **Silently rewriting a shipped briefing** instead of appending an addendum.
- **The dev-narration register.** If a sentence assumes the reader reads code or
  logs, translate it or cut it.
