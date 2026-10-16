---
name: briefing
description: >
  Use when authoring a briefing — a plain-English, decision-oriented write-up of
  technical work for a NON-technical audience (stakeholders, reviewers, end
  users, funders, execs). Trigger on "write a briefing", "brief the
  stakeholders", "explain X for non-technical readers", "stakeholder one-pager",
  "client update", "what shipped since", or whenever someone needs a derived
  plain-English view of engineer-facing docs (run/results logs, plans, specs,
  changelog, commits). Owns briefing structure, source-grounding discipline,
  and the docs/briefings/ convention. NOT for developer reports from git
  history (kit:dev-reports), NOT for dev-facing "explain this spec so I can
  build it" (different register), and NOT for CHANGELOG/ROADMAP edits.
---

# Briefing Authoring

A briefing is a **derived, plain-English view** of engineer-facing source docs,
for someone who decides about the work but doesn't read code or logs. It answers
a specific moment — a result landed, a decision is pending, an ask is needed —
not a status dump.

The craft is three disciplines, not a template. Get them right and the sections
write themselves. Prose mechanics and the polish pass live in **`STYLE.md`**
(bundled alongside this skill) — read it before drafting.

## Scope

**In:** one Markdown write-up for a reader who decides about the work but does
not read code, for one of the five events below.

**Out — use something else:**

- **A developer summary of git history** → `kit:dev-reports`. Its report can
  be the source for event 4; it is never the briefing.
- **Explaining a spec to the developer who builds it** → a different register;
  this skill does not cover it.
- **CHANGELOG and ROADMAP edits** → the project's own rules for those files.
  The briefing cites them; it does not edit them.
- **Making text sound less machine-written** → `kit:de-slop`. This skill calls
  it only as the optional polish pass.
- **The deck, the shared editable copy, the demo video** → build them from the
  finished briefing with whatever tool the host offers. The briefing stays the
  source, and its metadata links to each of them.

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
   so. The noise band is the run-to-run variation, confidence interval or error
   margin the source states. If the source states none, do not present a change
   as a result: say that the variation between runs is not known. Name what
   the work does **not** fix or mean; those sections earn the trust. Report
   your own mistakes plainly. No cheerleading, no "leverage", no
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
4. **Changes since a fixed point** — what shipped or changed between an anchor
   the reader already knows and now. Anchor, in order of preference: the last
   briefing to this reader, the last deploy or release, the date of the
   reader's own request list, a contract or milestone date. Name the anchor in
   the first lines, so the reader knows where "since" starts. Source = the
   project's changelog and roadmap rows for that range. If the project keeps
   neither, run `kit:dev-reports` for the range first and use its report.
5. **Where the product stands** — a first briefing to a reader, with no anchor
   for event 4. Describe the current state, not a history: what works today,
   what is still open, what comes next. Source = the roadmap (built and open
   rows) and the live product. Never start from the first commit; a full
   history is a status dump.

Events 4 and 5 still end on an ask: what the reader should check, decide or
send back. If none fits, recheck the Discipline 1 precondition before writing.

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
run the `kit:de-slop` skill on the draft, if it is installed. Pass it the two
briefing-specific guardrails in `STYLE.md` — don't flatten the structured
bullets/tables, and don't strip real caveats or numbers.

## Before you hand it over

Check every number in the briefing against the claim list from "Before you
write", step 3. Each one must appear in a cited source with the same value, or
be an honest rounding of it marked `~`. Remove or fix any that fail. This check
runs after the polish pass, because a polish pass can change a number.

## Conventions

- **Location:** if the host project already has a briefings location/format,
  follow it. Otherwise default to `docs/briefings/YYYY-MM-DD-<slug>.md`. Engineer
  docs stay wherever they already live; don't invent new trees.
- **Companion linking:** always link back to the source doc, with relative paths.

## Common mistakes

- **Distorting a number to make prose flow.** The cardinal sin.
- **A status dump instead of an answer.** If it doesn't end on a decision or ask,
  ask what it's for. Events 4 and 5 report status, but they still end on an ask.
- **Burying the bad news.** "What this does NOT fix" is where trust is earned.
- **Celebrating noise.** Movement inside the noise band isn't a result.
- **Untagged asks** when multiple audiences must act.
- **Silently rewriting a shipped briefing** instead of appending an addendum.
- **The dev-narration register.** If a sentence assumes the reader reads code or
  logs, translate it or cut it.
