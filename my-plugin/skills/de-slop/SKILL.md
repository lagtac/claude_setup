---
name: de-slop
description: Rewrite text so it reads as if a person wrote it — stripping AI phrase tells (filler openers, hedge stacks, corporate vocabulary) and the structural tells that survive a phrase scrub (uniform sentence length, symmetric lists, antithesis tics, recap endings). Use when the user asks to de-slop, humanize, tighten, or remove AI-sounding language from a passage they've pasted or referenced.
---

# De-Slop

The goal is text a reader would take for human writing. Not shorter, not more
polished — human.

That is a harder target than "remove the bad phrases", and it changes where the
work is. A passage can contain none of the banned vocabulary and still be
unmistakably machine-made, because what gives it away is shape and rhythm: every
sentence the same length, every list perfectly parallel, every section closing
with a tidy restatement of itself. Layer 1 below catches the words. Layer 2
catches what's left, and Layer 2 is usually where the tell is.

**Input:** The text to clean, supplied inline in the user's message (pasted or quoted) or as a referenced file path.

**Where the result goes:** print it, in the format under Output. When the input was a file, edit that file only if the user asked for the file to be changed; otherwise print the result and leave the file alone.

## The line you may not cross

Sounding human tempts a rewriter to *add*. An aside, a blunt opinion, a "this
bit me once", a rough edge left in on purpose — those all read human, and all of
them are fabrication when the text is someone else's document.

**You edit. You do not invent.**

In scope, because it's editing what's there:

- varying sentence length, including letting one sentence be very short
- breaking parallel grammar in a list, or dropping an item that only restates another
- deleting the closing sentence that recaps the paragraph above it
- rewriting an "it's not X — it's Y" construction as a plain statement
- foregrounding the case that matters instead of giving every case equal weight
- restoring specifics that are *already in the source* but got abstracted away

Out of bounds, because it's writing new material:

- opinions, jokes, or anecdotes the author never expressed
- numbers, names, or dates not present in the source
- hedges and caveats the author didn't write
- personality grafted on, or errors introduced on purpose to look casual

If the input has no personality, the output has none either. Flat but human is
the honest result. A voice you made up is not.

## Layer 1 — phrase tells

**Filler openers / sycophancy**
- "Certainly!", "Absolutely!", "Great question!", "Of course!", "Sure!"
- "I'd be happy to…", "I'd be glad to…"
- "Let me explain…", "Let me break this down…", "Let's dive in!"

**Hedge stacking**
- "It's worth noting that…", "It's important to remember that…"
- "It's crucial to understand…", "It's essential to…"
- "Please note that…", "Keep in mind that…"

**Empty connectors and transitions**
- "Furthermore", "Moreover", "Additionally" (when they add no logic)
- "In conclusion", "To summarize", "All in all"
- "At the end of the day", "When all is said and done"

**Corporate filler vocabulary**
- utilize → use
- leverage → use
- facilitate → help, enable
- navigate → handle, deal with
- demonstrate → show
- implement → do, build, set up
- comprehensive, robust, holistic, nuanced, multifaceted
- innovative, cutting-edge, state-of-the-art
- "plays a crucial role in", "is instrumental in"

**Redundant qualifiers**
- "very unique", "truly remarkable", "quite frankly"
- "in terms of", "with regard to", "in the context of"
- "in today's fast-paced world", "in the modern era"

**Verbose constructions**
- Turning verbs into noun phrases: "provides assistance" → "helps"
- "It is important that X" → just say X
- "The reason for this is that" → "because"
- "In order to" → "to"
- "Due to the fact that" → "because"
- Passive voice where active is natural

**Filler phrases that add zero meaning**
- "Shed light on", "delve into", "embark on a journey"
- "tapestry of", "realm of", "landscape of"
- "At its core…", "Fundamentally speaking…"
- "This begs the question…" (almost always misused)

## Layer 2 — shape and rhythm tells

These survive a phrase scrub. Check for them even when Layer 1 came up empty.

**1. Uniform sentence length.** The single strongest tell. Machine prose sits in
a narrow band, roughly twelve to twenty words, sentence after sentence. Human
prose swings: a long winding one, then four words. Fix by merging and splitting
until the lengths vary — not by shortening everything.

**2. Symmetry.** Bullets of near-identical length, sections of identical depth,
lists where every item is the same part of speech in the same grammatical mould.
Real notes are lopsided; one point gets three sentences because it needed them.

**3. The antithesis reflex.** "Not X — Y." "It's not just X, it's Y." "This
isn't about X. It's about Y." Once in a piece is rhetoric. Three times is a tic.
Most of them are a plain statement wearing a costume.

**4. Tricolon by default.** Three items because three sounds complete, not
because there are three. Cut it to two when the third only restates the others —
but if all three are distinct facts, keep the facts and break the parallel
grammar instead. Deleting a fact to improve rhythm is out of bounds.

**5. Every section resolving.** A closing sentence that restates what was just
said, on every section, without exception. Humans leave threads hanging and move
on. The recap sentence is nearly always deletable.

**6. Even coverage instead of commitment.** Every case, caveat and alternative
weighted the same, as though the author had no view about which mattered. Where
the source does show an emphasis — the point it returns to, the one it spends
paragraphs on — carry that emphasis into the rewrite instead of flattening it.
Where the source is genuinely flat, leave the ordering alone; deciding what
matters is the author's call, not yours.

**7. Specifics abstracted away.** "Significantly faster" where the source said
"cut it from 300ms to 40ms". "The team" where the source named someone. Put back
what the source contains. Do not supply what it doesn't.

**8. Metronomic em-dashes.** The tell is regularity, not the character itself:
one per sentence, always in the same mid-sentence slot. A well-placed em-dash is
good writing. Five in a row in the same position is a machine's default.

**9. Structure imposed on material that doesn't need it.** Bullets for what
reads fine as a paragraph, nesting three levels deep for a flat list, a bold
header over every paragraph of a conversational answer, numbered steps for
things that happen in no particular order, every paragraph opening on "This" or
"These". Formatting here is doing the job of a machine reaching for a template,
not a writer organising an argument. Unwind it — but read the guardrail below
first, because on some documents that structure is the point.

## Process

### 1. Scan twice

First pass for Layer 1 — mark the phrases to delete or swap. Second pass for
Layer 2, and read it as shape rather than words: how long are the sentences, are
the lists symmetric, does each section end with its own summary, are there
specifics.

Layer 2 needs its own pass. Looked for while you're editing phrases, it gets
missed.

### 2. Rewrite

1. **Delete** — filler openers, hedge stacks, empty transitions, redundant qualifiers, recap sentences
2. **Simplify** — verbose constructions become direct ones ("due to the fact that" → "because"). Shorter is a side effect of saying it plainly, never the target.
3. **Swap** — corporate vocabulary for plain words
4. **Re-rhythm** — merge and split sentences until the lengths vary, break symmetric lists, unwind the antithesis constructions
5. **Restructure** — bullets into prose only where prose genuinely reads better, and never on a skim-formatted document (see guardrails)

**Do not:**
- Change the meaning or factual content
- Add anything not in the source — see *The line you may not cross*
- Pad it back out with different filler
- **Compress past the point of clarity.** If cutting a word leaves a sentence only its own author could follow, keep the word. A definition, a worked example, and the noun a pronoun refers back to are not padding — they are what makes the text readable by someone who does not already know the answer. Uniform compression is itself an AI tell.
- Over-correct into a different voice
- Strip personality — only strip artificiality

### 3. Check

Run these against the output before returning it. They are the falsifiable
version of "does this read human".

- Is there at least one sentence under about eight words? Are any two neighbouring sentences within a word or two of each other, repeatedly?
- Does any list still have items of matching length and matching grammar, in a document that isn't a table or a checklist?
- How many "not X — Y" constructions are left? More than one in a few hundred words is a tic.
- Does every section still end by restating itself?
- Are the em-dashes clustered one-per-sentence in the same position?
- **Did anything reach the output that wasn't in the input?** An opinion, an anecdote, a number, a hedge. If so, take it out — this check outranks all the others.

### 4. Output

**Cleaned text** — the rewritten version, no commentary inline.

**Change log** — a compact bulleted list of what changed and why, by category rather than line by line. Say which layer the work was in; "no phrase tells, all shape" is useful information for the author.

Format:
```
[cleaned text]

---
**Changes:** [bullet list of change types applied]
```

## Guardrails

**Skim-formatted documents.** Briefings, changelogs, roadmaps, READMEs, release
notes, tables, checklists. This is the exception to Layer 2 #9: their bullets and
parallel structure are a format choice made for readers who skim, not an AI tell.
The distinction is whether the format serves the reader or came from a template —
a comparison table and a three-deep nest of one-line bullets are not the same
thing. On these, apply Layer 1 and
the sentence-rhythm work; leave the bullets, tables and deliberate parallelism
alone. Flattening a comparison table into a paragraph is a downgrade even when
the paragraph reads more human.

**Load-bearing hedges.** An approximation (`~52%`), a sample-size caveat, a
noise-floor warning: those are honesty, not hedging. Cut "it's important to note
that", keep the caveat that follows it.

**Already clean is a result.** Say so and return the text unchanged. It's common
for anything written carefully, and inventing changes to look useful is the
worst outcome this skill can produce.

## Examples

### Phrase tells

**Input:**
> Certainly! It's important to note that in today's fast-paced technological landscape, leveraging the right tools is crucial. Furthermore, it's worth mentioning that our comprehensive solution utilizes cutting-edge methodologies to facilitate seamless collaboration across teams.

**Output:**
> Using the right tools matters. Our solution helps teams collaborate.
>
> ---
> **Changes:** Layer 1 only. Removed opener ("Certainly!"), hedge stack ("it's important to note"), filler phrase ("in today's fast-paced technological landscape"), replaced "leveraging/utilize/facilitate" with plain verbs, cut redundant qualifiers ("comprehensive", "cutting-edge", "seamless").

### Shape tells, with no phrase tells at all

This is the case the skill exists for. Nothing here is on the Layer 1 list.

**Input:**
> The migration ran on Tuesday and completed without errors. The new index reduced query time, improved throughput, and lowered CPU load. This was not a small change — it touched every read path in the service. The team monitored the rollout closely, reviewed the metrics carefully, and confirmed the results independently. The outcome was a faster, cheaper, more predictable system.

**Output:**
> The migration ran Tuesday and finished clean. Query time and CPU load both dropped, and throughput went up with them. It touched every read path in the service, so the team watched the metrics through the rollout and confirmed the results independently before calling it done.
>
> ---
> **Changes:** No phrase tells — all Layer 2. Sentence lengths were 12–18 words throughout; now they vary. Broke two tricolons (all six facts kept, parallel grammar dropped). Removed the "not X — Y" construction. Cut the closing sentence, which only restated the four above it. The source gives no figures, so none were added.

**Invented a voice, and wrong:**
> Migration day. Ugh — every read path in the service, which is the kind of thing that keeps you up at night. It landed clean though, and honestly the index did more than I expected.

This reads human because it reads like *someone*, and that someone isn't the
author. Nobody said they lost sleep, and nobody said the result beat their
expectations. Personality you supply is fabrication no matter how well it scans.

### The clarity floor

**Input:** *(slop wrapped around a definition the reader needs)*
> It's important to note that the bundle — which is to say, the JavaScript file the build actually produces — gets injected into the page. Furthermore, it is crucial to understand that this means shared code ends up in there as well.

**Output:**
> The bundle — the JavaScript file the build produces — is injected into the page, so shared code ends up there too.
>
> ---
> **Changes:** Removed hedge stacks ("it's important to note", "it is crucial to understand"), empty connector ("Furthermore"), and "which is to say"; merged two sentences.

**Over-corrected, and wrong:**
> The bundle is injected, so shared code ends up there.

This is shorter and it is worse. The clause defining *bundle* was not padding —
without it the sentence only works for a reader who already knew the term.
Removing slop and removing meaning look similar from inside the edit; the test
is whether someone lacking the author's context can still follow the result.
