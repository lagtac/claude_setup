# Briefing Style

Drafting-time reference for the `briefing` skill, loaded alongside it. SKILL.md
owns the disciplines, the event classifier, and structure; this file owns how the
sentences read.

## Match the host project first

If the project already has briefings (a `docs/briefings/` dir or similar), skim
one before drafting and match its established voice, headings, and table style.
The rules below are the defaults when the project has no house style to follow.

## Style rules

Each rule has a short example. Hold to the rule; adapt the example to the
material.

- **Title is a narrative sentence joining the situation to the ask** — colon or
  `&`, never a noun-label. *"Where we stand: the migration shipped, one report is
  still wrong, and we need a rollout call"* beats *"Migration Update"*.
- **Bold marks only the load-bearing skim-word** — the ask's noun, the direction,
  the absolute — not decoration. *"This is a **billing bug, not data loss**"*;
  *"the fix is **yours to approve**"*. TL;DR and scope bullets open with a bold
  verdict-phrase and a period: *"**Throughput: fixed.** …"*.
- **Translate every term of art on first use, in the sentence.** *"idempotency
  key" → "a tag that stops the same request being counted twice."*
- **One correct analogy per concept, reused.** Pick it once and keep it
  throughout; it must be accurate, not just vivid.
- **Tag a heading with its audience when that section asks a group to act**, and
  let the tag carry priority/timing — *"## Needs sign-off (execs — first)"*.
- **Render change as a comparison table with verdict cells** — columns name the
  two states; the right cell carries a verdict (e.g. ✅ + a bold phrase), not a
  raw number alone. Right-align numeric columns (`---:`).
- **Asks are a numbered, priority-ordered, time-tagged list**, each leading with
  its timeframe in bold — *"1. **This week — …**"*.
- **Quote user-facing copy verbatim** (as a blockquote) so reviewers approve the
  exact wording. For localized strings, give the original then an italic gloss.
- **Use a `>` callout for a single do-not warning** that must not be missed.
- **Em-dash is the mid-sentence pivot** for a consequence or qualifier.
- **End on the decision, ownership explicit** — *"that call is yours."*

**Length:** shorter than the source, but not aggressively short — clarity beats
brevity. A confused stakeholder costs more than a long paragraph.

## Polish-pass guardrails

If you run a de-slop / humanizing pass over the draft, two guardrails — the pass
doesn't know it's looking at a briefing:

- **Phrase-level only.** Apply delete / compress / swap, but **not** any
  "bullets → prose" step. TL;DR bullets, comparison tables, and tagged asks are
  built for skim-ability; flattening them defeats the format.
- **Caveats and numbers are content, not hedges.** Approximations (`~52%`),
  noise-floor warnings, and sample-size caveats are load-bearing honesty. Don't
  let a polish pass false-precision a sourced number or delete a real caveat.
