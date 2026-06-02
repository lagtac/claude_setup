---
name: briefing
description: >
  Use when authoring a briefing — a plain-English, decision-oriented write-up of
  technical work for a NON-technical audience (stakeholders, clinical reviewers,
  annotators, funders, regulators). Trigger on "write a briefing", "brief the
  stakeholders", "explain X for non-technical readers", "stakeholder one-pager",
  "summarise this experiment/plan for clinicians", or whenever someone needs a
  derived plain-English view of engineer-facing docs (experiment-log entries,
  plans, specs, commits). Owns briefing structure, source-grounding discipline,
  and the docs/briefings/ convention. NOT for dev-facing "explain this spec to
  me so I can build it" (different register) and NOT for CHANGELOG/ROADMAP edits.
---

# Briefing Authoring

A briefing is a **derived, plain-English view** of engineer-facing source
documents, written for someone who makes decisions about the work but does not
read code or experiment logs. It exists to answer a specific moment — a result
landed, a decision is pending, an ask is needed — not to dump status.

The craft is not a section template. It is three disciplines; get these right and
the sections write themselves. Get them wrong and you produce a briefing that
reads beautifully and lies.

## The three disciplines (read before writing)

### 1. A briefing is a derived view, never the source of truth

Name the engineer-facing companion doc(s) at the top and defer to them for full
detail. The briefing simplifies; the companion is authoritative. A reader who
wants the real numbers must be one click away from them. If there is no
ground-truth doc to derive from, you are not writing a briefing — you are
inventing claims. Stop and find the source.

### 2. Every number traces to a cited source

The dominant failure mode is prettifying prose while distorting facts. Before you
write a number — accuracy, counts, percentages, sample sizes — locate it in the
source doc and carry it across unchanged. Round honestly and say so (`~52%`, not
a false-precision `51.7%` the source doesn't support). Never invent a number to
make a sentence flow. When you approximate, the approximation must be defensible
against the cited companion.

### 3. Honesty over hype

These briefings earn trust by refusing the triumphant narrative. Encode it
explicitly:

- A small movement inside the noise band is not a result. Say so ("a 1-point
  change on a 10-sample disease is noise, not progress").
- Name what the work does **not** fix and what it does **not** mean — these
  sections do more work than the good news.
- Report your own mistakes plainly ("we were grading on the wrong exam").
- No corporate cheerleading, no "leverage", no "comprehensive". Plain, direct,
  occasionally blunt.

## When to write one

A briefing is **event-gated, not phase-gated.** Don't peg it to a fixed point in
the work (after planning, after implementation); peg it to a decision-worthy
event that has *already produced a ground-truth doc*. Discipline 1 forces this: a
briefing is a derived view, so the source artifact must exist first — the briefing
always lags the thing it summarises.

Two reliable trigger points:

1. **Post-results — the default.** A run finished, a verdict landed, an ask
   emerged. Wait until the runtime ground-truth doc exists, then derive from it.
   The natural sequence is **run → assess/log → brief**: the experiment-log entry
   (e.g. what `stoma assess --log` writes) is the companion the briefing defers
   to. Briefing before the result is durably written means inventing claims.
2. **Post-planning — only when the plan encodes a stakeholder decision.** A
   re-prioritisation, a parked option, a fork that needs sign-off. Source = the
   spec/plan. If the plan is purely internal execution detail, there's nothing to
   brief yet.

Two anti-patterns:

- **Pre-planning briefings** — almost never. Nothing grounded to derive from. The
  rare exception is presenting a fork for sign-off, and even then you're briefing
  a decision doc, not a phase.
- **Mid-implementation status dumps** — wait for the result. The one exception is
  the kickoff of something long-running and expensive (a multi-hour training run),
  where "we've started, here's the recipe and why" is itself the event — and you
  then *append dated updates* to that same briefing as results arrive, rather than
  starting a new one.

## Before you write

1. **Identify the triggering event.** What just happened, or what decision is
   pending? A briefing has a job. One sentence: *the result / the bug / the
   verdict / the ask.*
2. **Identify the audience(s) and their literacy.** Stakeholder with no ML
   background? Clinicians? Annotators who need a protocol change? State it in the
   metadata so register and jargon-budget are set deliberately. Different asks
   for different audiences get **tagged** (see below).
3. **Gather the source docs.** The experiment-log entry, the plan/spec, the
   commit. These are your ground truth and your companion links.
4. **Extract claims with their sources.** Pull every number and factual claim
   into view *with where it came from* before prose. This is discipline 2 made
   operational.

## Structure (the default shape — adapt to the event)

The order below is the shape these briefings converge on. Not every briefing
needs every section; a short status update may be TL;DR + one decision. Let the
event decide.

1. **Title** — a narrative line, not a label. "Where we stand: a training-recipe
   bug, an unused safety net, and a cheaper path" beats "Training Update".
2. **Metadata block** — `Date`, `Audience` (state the ML-background assumption),
   and **Companion / Full detail** links to the engineer-facing source docs.
3. **`## TL;DR`** — the headline and the 2–4 load-bearing points, as bullets.
   A reader who stops here should still come away with the decision or the ask.
4. **Body** — the plain-English translation (see next section). One concern per
   section, descriptive `##` headings.
5. **What this does NOT mean / does NOT fix** — bound the scope; pre-empt the
   wrong conclusion. Frequently the most valuable section.
6. **The honest caveat** — sample-size limits, noise floor, what is still
   uncertain, what would change the conclusion.
7. **The ask / the decision** — audience-tagged ("annotators — first"), in
   **priority order**, concrete and actionable. End on what you need or what was
   decided.
8. **Appendix** — parameter tables, exact values, "skip unless curious".
9. **Dated `## Addendum` / `## Update` sections** — append as the situation
   evolves; never silently rewrite a shipped briefing. Each addendum is dated and
   says what changed.

## Writing the plain-English translation

- **Translate every term of art.** "Mosaic augmentation" → "a common trick that
  mixes two training photos into one." Define on first use, in the sentence.
- **Use analogies grounded in the domain.** Train/test leakage → "giving a
  student the answers before the exam." Background images → "teaching it to say
  'nothing here.'" The analogy must be *correct*, not just vivid.
- **Concrete beats abstract.** Real numbers, real class names, real examples.
  "misses more than 2 of every 3 cases" lands; "suboptimal recall" does not.
- **Before/After tables** for behavioural or numeric change. Old value, new
  value, one-line "what it does".
- **Carry UI-facing copy verbatim**, including bilingual text (e.g. the Greek
  clinician-facing strings), so reviewers approve the exact wording users see.
- **Shorter than the source, but not aggressively short** — clarity outranks
  brevity. A confused stakeholder is more expensive than a long paragraph.

## Polish pass (optional final step)

Discipline 3 already keeps slop out at write time, so this is a safety net, not
the main mechanism. Once the draft is written, run it through `my:de-slop` (pass
the briefing's file path) to catch residual corporate vocabulary, filler openers,
and padded constructions. Two guardrails, because de-slop doesn't know it's
looking at a briefing:

- **Phrase-level only — skip restructuring.** Apply de-slop's delete / compress /
  swap, but **not** its "convert bullets to prose" step. A briefing's TL;DR
  bullets, before/after tables, and audience-tagged asks are deliberately
  structured for stakeholder skim-ability; flattening them to prose defeats the
  format.
- **Caveats and numbers are content, not hedges.** de-slop strips hedge stacks,
  but a briefing's epistemic honesty is load-bearing: approximations (`~52%`,
  "between 65% and 100%"), noise-floor warnings ("this is noise, not a result"),
  and single-run/sample-size caveats must survive untouched. Don't let a polish
  pass false-precision a sourced number or delete a real caveat.

## Conventions (defaults — adapt per project)

- **Location & name:** `docs/briefings/YYYY-MM-DD-<slug>.md`. This is the
  stakeholder-facing surface; engineer docs stay in `.claude/docs/` /
  `docs/experiment-log/` / `docs/plans/`. Don't invent `docs/features/` etc.
- **Audience taxonomy** (state the relevant one in the metadata): non-technical
  stakeholder, clinical reviewer, annotator, funder, regulatory-adjacent reader.
- **Companion linking:** always link back to the experiment-log entry, plan/spec,
  or commit the briefing derives from. Relative paths.
- **Exemplar corpus** (the model for this skill, in diagoradisa-ml — paths are
  project-specific, cited as reference not template):
  `docs/briefings/2026-05-21-post-training-stakeholder-asks.md` (audience-tagged
  asks, clinical depth) and `docs/briefings/2026-06-01-dataset-changes-status.md`
  (a clean honesty/anti-hype example).

## Common mistakes

- **Distorting a number to make the prose flow.** The cardinal sin. Re-check
  every figure against its source before finishing.
- **Writing a status dump instead of answering an event.** If it doesn't end on
  a decision or an ask, ask what it's *for*.
- **Burying or omitting the bad news.** "What this does NOT fix" is not optional
  garnish; it's where trust is earned.
- **Celebrating noise.** A movement inside the noise band is not a result.
- **No companion link / unsourced claims.** A briefing with nothing to derive
  from is invention. Find the ground-truth doc first.
- **Untagged asks.** When multiple audiences must act, say who does what, in
  priority order.
- **Silently rewriting a shipped briefing.** Append a dated addendum instead.
- **Slipping into the dev-narration register.** Briefings are for non-technical
  readers; "as a dev you'd…" framing belongs elsewhere.
