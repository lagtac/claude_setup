---
name: de-slop
description: Remove AI linguistic artifacts (filler openers, hedge stacks, corporate vocabulary, padded structures) from text the user provides. Use when the user asks to de-slop, clean up, tighten, or remove AI-sounding language from a passage they've pasted or referenced.
---

# De-Slop

Remove AI linguistic artifacts from text. The goal is a terser, more natural result — not a polished rewrite.

**Input:** The text to clean, supplied inline in the user's message (pasted or quoted) or as a referenced file path.

## What AI slop looks like

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

**AI sentence structures**
- Starting every paragraph with "This" or "These"
- Overuse of em-dashes to pad sentences
- Passive voice where active is natural
- Turning verbs into noun phrases: "provides assistance" → "helps"
- "It is important that X" → just say X
- "The reason for this is that" → "because"
- "In order to" → "to"
- "Due to the fact that" → "because"

**Structural tells**
- Bullet points for everything, including things that read fine as prose
- Nested bullets three levels deep for simple information
- Bold headers on every paragraph in a conversational response
- Numbered steps for non-sequential content

**Filler phrases that add zero meaning**
- "Shed light on", "delve into", "embark on a journey"
- "tapestry of", "realm of", "landscape of"
- "At its core…", "Fundamentally speaking…"
- "This begs the question…" (almost always misused)

---

## Process

### 1. Scan

Read the text and identify all slop patterns. Don't start rewriting yet — mentally catalogue what's wrong:
- Which phrases are filler?
- Which sentences are padded?
- What can be deleted outright (not replaced)?
- What word swaps are needed?
- Is the structure (bullets, headers) appropriate or imposed?

### 2. Rewrite

Apply changes with this priority order:
1. **Delete** — remove filler openers, hedge stacks, empty transitions, redundant qualifiers entirely
2. **Compress** — merge verbose constructions into shorter ones
3. **Swap** — replace corporate vocabulary with plain words
4. **Restructure** — convert unnecessary bullet lists to prose only if it genuinely reads better; don't add structure that wasn't there

**Do not:**
- Change the meaning or factual content
- Add new ideas or elaborations
- Make it longer
- Over-correct into a completely different voice
- Strip personality — only strip artificiality

### 3. Output

Return two things:

**Cleaned text** — the rewritten version, no commentary inline.

**Change log** — a compact bulleted list of what was changed and why. Keep it short: categories of changes, not line-by-line explanations.

Format:
```
[cleaned text]

---
**Changes:** [bullet list of change types applied]
```

If the text is already clean (no significant slop detected), say so briefly and return the original unchanged.

---

## Examples

**Input:**
> Certainly! It's important to note that in today's fast-paced technological landscape, leveraging the right tools is crucial. Furthermore, it's worth mentioning that our comprehensive solution utilizes cutting-edge methodologies to facilitate seamless collaboration across teams.

**Output:**
> Using the right tools matters. Our solution helps teams collaborate.
>
> ---
> **Changes:** Removed opener ("Certainly!"), hedge stack ("it's important to note"), filler phrase ("in today's fast-paced technological landscape"), replaced "leveraging/utilize/facilitate" with plain verbs, cut redundant qualifiers ("comprehensive", "cutting-edge", "seamless").

---

**Input:**
> In order to implement the feature, you will need to navigate to the settings panel. Due to the fact that this panel plays a crucial role in configuration, it is important that you carefully review all of the available options.

**Output:**
> To add the feature, go to the settings panel and review the options.
>
> ---
> **Changes:** "In order to" → "To", "navigate to" → "go to", "due to the fact that" → cut, "plays a crucial role" → cut, "it is important that you carefully" → cut, merged two sentences.
