# Plan: `my:briefing` — a skill for authoring effective briefings

## Context

The diagoradisa-ml project has accumulated a consistent, high-quality corpus of
**stakeholder briefings** in `docs/briefings/` (four to date, May–June 2026).
They share a strong, deliberate house style: plain-English translations of
technical work for non-technical decision-makers (clinical reviewers,
annotators, funders), each derived from — and linking back to — engineer-facing
ground-truth docs (`experiment-log/`, `docs/plans/`, commit SHAs).

Right now that style lives only in the author's head and the example files.
There is no skill that captures *how* to write one, so each briefing is
re-derived from scratch and the discipline (source-grounding, anti-hype honesty,
audience-tagged asks) is easy to drop under time pressure. This plan creates a
reusable skill that encodes the corpus's craft.

**Decisions (confirmed with user):**
- **Scope:** global `my`-plugin skill (`my:briefing`), reusable across the
  sibling Laravel projects (annotator, palmist), not project-local. Conventions
  become *defaults*; the one inline example is abstracted (diagoradisa corpus
  paths won't resolve in other repos, so they're cited as exemplars, not
  hard-coded structure).
- **Validation:** one trial briefing against a real source doc, reviewed
  together. No quantitative eval loop — skill-creator's own guidance carves
  subjective writing skills out of the benchmark machinery.

## What makes these briefings effective (the distillation)

From reading all four briefings end-to-end, the craft is **not** primarily a
section checklist (TL;DR / table / caveat / bottom-line). Those fall out
naturally once three deeper disciplines are in place. The skill leads with the
disciplines, or it produces briefings that *look* right and quietly distort:

1. **A briefing is a derived view, never the source of truth.** Every one names
   its companion engineer doc up top and defers to it for full numbers. This is
   the literal meaning of "based on documentation" and mirrors the project's
   doc-scope discipline.
2. **Every number traces to a cited companion doc.** `~52% vs ~42%`, `36`
   confusions, `~60%` fewer false alarms — the dominant failure mode of
   "generate a briefing from docs" is prettifying the prose while distorting the
   facts. Source-grounding per claim is the verification spine.
3. **Anti-hype honesty.** "Don't celebrate a 1-point movement," "both scares
   were false alarms," "we caught ourselves grading on the wrong exam," and the
   recurring *"what this does NOT fix / does NOT mean"* sections. Without this
   encoded explicitly, generated briefings drift to corporate cheerleading.

Plus one structural truth: **briefings are event-driven and decision-oriented**,
not periodic status dumps. Each answers a specific moment and ends on a decision
or an audience-tagged ask: *what happened → what we decided → what we need from
you*.

Recurring surface conventions (these are the *defaults* the skill documents):
metadata block (Date / Audience / Companion links); `## TL;DR`; plain-English
body with domain analogies and concrete before/after tables; *"What this does
NOT mean / fix"*; *"The honest caveat"* (sample-size / noise-floor honesty);
audience-tagged asks in priority order; *"Appendix … skip unless curious"* for
parameter detail; dated **Addendum / Update** sections appended as the situation
evolves; verbatim bilingual (Greek+English) text for clinician-facing UI copy.

> Note: this is a **different register** from the `feedback-human-narration-style`
> memory. That style is dev-oriented ("explain this spec so I can act on it") for
> the author himself; briefings target non-technical stakeholders. They overlap
> (plain English, before/after tables) but the audience differs — the skill cites
> the four-briefing corpus as its model, not that memory.

## Files to Create

- `~/projects/claude-setup/my-plugin/skills/briefing/SKILL.md` — single file, no
  bundled scripts/templates/references. Matches the house format of the existing
  `my` skills (`changelog-management`, `roadmap-management`): pushy YAML
  description, principles-first body, numbered rules with rationale, a
  conventions block, and a "Common mistakes" section.

No other files change. (On execution, per the user's CLAUDE.md, a durable copy of
this plan lands in `~/projects/claude-setup/docs/plans/2026-06-02-briefing-skill.md`
— the repo that owns the new skill.)

## Proposed SKILL.md (full draft for review)

```markdown
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
```

## Trade-offs / Alternatives

- **Project-local vs global (chosen: global).** Project-local would let the skill
  hard-code diagoradisa's audiences and `experiment-log` companions and cite the
  corpus by resolvable path. Global makes it reusable for annotator/palmist at
  the cost of demoting those specifics to "defaults" and abstracting the example.
  User chose global; the draft above reflects that (conventions framed as
  defaults, corpus cited as exemplar).
- **Single SKILL.md vs bundled references/templates (chosen: single).** A writing
  skill is principle-driven, not procedure-driven; a `references/` split or a
  fill-in template would add surface without adding craft and risks producing
  formulaic briefings. One file, principles-first.
- **Eval loop vs one trial (chosen: one trial).** Subjective output — quantitative
  assertions would mostly be vacuous ("has a TL;DR section"). A single real trial
  reviewed together is the higher-signal check.

## Dependencies

- None new. Writes one Markdown file into the existing `my-plugin/skills/` tree.
  No code, no packages, no config.

## Risk

- **Low / fully reversible.** The only artifact is a new skill file; worst case it
  triggers when unwanted or gives mediocre guidance — deleted or edited in one
  step. No blast radius on any running system.
- **Over-triggering** is the realistic risk: the description must *not* fire on
  the dev-narration "explain this spec to me" register or on CHANGELOG/ROADMAP
  edits. The draft description names both exclusions explicitly; the trial run
  plus normal use will confirm.
- **Plugin reload:** a new skill in `my-plugin` is picked up on the next session
  / plugin reload, not necessarily mid-session. Note for the trial run.

## Testing Strategy (the one trial briefing)

1. **Author the skill** at the path above.
2. **Pick a real source doc** with no existing briefing — e.g. a recent
   `docs/experiment-log/` entry in diagoradisa-ml — to act as ground truth.
3. **Invoke the skill** to draft a briefing from it (a fresh subagent with the
   skill loaded, so it isn't running on this conversation's context).
4. **Verify against the disciplines, not vibes:**
   - Every number in the draft traces to a line in the source doc (spot-check
     each figure).
   - There is a companion link back to the source.
   - There is a "what this does NOT fix/mean" and an honest-caveat section.
   - It ends on a decision or an audience-tagged ask.
   - Register is non-technical; no undefined jargon.
5. **Review together**, refine the SKILL.md once based on what the draft got
   wrong, and stop. No benchmark, no iteration loop unless the trial reveals a
   systemic gap.

## Open Questions

- Durable plan location: `~/projects/claude-setup/docs/plans/` (the repo that
  owns the skill) vs diagoradisa-ml's. Defaulting to claude-setup since that's
  where the artifact lives; will confirm on execution if that dir doesn't exist.
- Should the skill optionally write a paired CHANGELOG/ROADMAP note when a
  briefing accompanies a shipment? Leaving out for now — those skills already own
  that; the briefing skill just links to their output. Flag only if the trial
  surfaces friction.
```
