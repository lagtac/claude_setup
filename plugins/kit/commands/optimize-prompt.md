---
description: Analyze and optimize a prompt template using the 10 golden rules
---

# Prompt Optimizer

Analyze the prompt below and rewrite it so a current Claude model (Fable 5.1, Opus 5 and later) produces the intended result on the first try. These models follow a prompt literally and closely. They do what it says, not what the author meant. So the work is removing guesses: missing goals, vague scope, unstated formats and instructions that contradict each other.

## Input Prompt to Analyze

$ARGUMENTS

If the input above is empty, print `Usage: /kit:optimize-prompt <prompt text, or a path to a file holding it>` and stop. If it is a path to an existing file, analyze that file's contents.

---

## Your Analysis Process

### Step 1: Initial Assessment

Rate the prompt against **every** rule below: ✅ Good, ⚠️ Needs work, ❌ Missing, or N/A with a one-line reason. A short question does not need a template or a decomposition. Mark such rules N/A instead of forcing them.

### Step 2: Detailed Analysis

For each ⚠️ or ❌ rule, write what is missing, what a literal model would do because of it, and the concrete fix. Quote the passage you are judging.

### Step 3: Optimized Prompt

Rewrite the prompt. Keep the author's goal, facts and constraints. Add only what a reader would otherwise have to guess, and mark every assumption you had to make with `[ASSUMED: …]` so the author can confirm it.

---

## The 10 Golden Rules

### Rule 1: State the goal and the reason

The model generalizes from the reason. "Keep answers under 100 words, because they are read on a phone" also shapes choices the rule never named. **Check:** Does the prompt say what the result is for, and why each important constraint exists?

### Rule 2: Name the task explicitly

Action verb, object, quantity, audience. **Bad:** "I need blog ideas". **Good:** "Write 10 blog post titles about X for readers who Y." **Check:** Could two readers carry the prompt out in materially different ways?

### Rule 3: Define the scope and its edges

List what to cover and what to leave out. A literal model covers exactly what is listed and nothing else. **Check:** Are the dimensions, files or sections to cover enumerated? Is out-of-scope stated?

### Rule 4: Supply the context instead of assuming it

Name files, paths, data, versions and prior decisions. The model cannot see what the author knows. **Check:** Does the prompt rely on context it does not contain ("the usual format", "our conventions")?

### Rule 5: Specify the output with a template

Show the actual skeleton: headings, table columns, JSON schema. A prose description of a format is followed loosely. A template is followed exactly. **Check:** Is there a literal template for structured output?

### Rule 6: Say how to decide in unclear cases

Give the tie-breaker, the default and when to stop and ask. Without one, the model guesses silently. **Check:** For each judgment call, does the prompt say what to do when it is unclear?

### Rule 7: Remove contradictions and state precedence

Two instructions that cannot both hold make the model pick one, unpredictably. Examples also count as instructions: an example that breaks a rule wins over the rule. **Check:** Do any two instructions, or an instruction and an example, conflict? When rules may collide, is the order of precedence stated?

### Rule 8: Ask for reasoning where judgment matters, in the output order

For a verdict or recommendation, require the evidence and reasoning to be written **before** the conclusion, as a section of the output. "Be thorough" or "think hard" asks for nothing specific. **Check:** Does any judgment in the output come before the reasoning that supports it?

### Rule 9: Use a calm, direct tone

Current models respond strongly to emphasis. ALL CAPS, "CRITICAL" and "you MUST" make them apply the rule too broadly. A plain sentence with a reason works better. A persona ("you are a world-class expert") adds little. Describe the task and the standard instead. **Check:** Is emphasis reserved for the one or two rules that truly override the rest?

### Rule 10: Split work that is too large

For a task with independent parts, or more than one deliverable, split it into ordered steps with a check between them, or into separate prompts. **Check:** Does the prompt ask for several deliverables at once without an order?

---

## Output Format

Present your analysis in this structure:

```
## 📊 PROMPT SCORECARD

| Rule | Rating | Notes |
|------|--------|-------|
| 1. Goal and reason | [✅/⚠️/❌/N/A] | [brief note] |
| 2. Explicit task | [✅/⚠️/❌/N/A] | [brief note] |
| 3. Scope and edges | [✅/⚠️/❌/N/A] | [brief note] |
| 4. Context supplied | [✅/⚠️/❌/N/A] | [brief note] |
| 5. Output template | [✅/⚠️/❌/N/A] | [brief note] |
| 6. Unclear cases | [✅/⚠️/❌/N/A] | [brief note] |
| 7. No contradictions | [✅/⚠️/❌/N/A] | [brief note] |
| 8. Reasoning before verdict | [✅/⚠️/❌/N/A] | [brief note] |
| 9. Calm, direct tone | [✅/⚠️/❌/N/A] | [brief note] |
| 10. Split large work | [✅/⚠️/❌/N/A] | [brief note] |

**Overall Score**: X/Y applicable rules satisfied (Y = rules not marked N/A)

---

## 🔍 KEY IMPROVEMENTS NEEDED

[The 2-4 most impactful improvements, each with the quoted passage and what a literal model would do with it]

---

## ✨ OPTIMIZED PROMPT

[The fully rewritten, optimized prompt goes here]

---

## 💡 WHY THIS VERSION IS BETTER

[Brief explanation of the key changes and their expected impact. List every [ASSUMED: …] the author should confirm.]
```

---

## Special Instructions

1. **Be direct about what is missing.** Name the gap and its effect; skip praise.
2. **Preserve intent.** The optimized prompt must achieve the same goal. Do not add requirements the author did not have.
3. **Scale to the prompt.** A one-line question gets a short answer and many N/A rows; a system prompt gets the full treatment.
4. **Show, don't tell.** The optimized prompt should itself follow the rules.

---

## Export

After showing the analysis, save the optimized prompt with the Write tool:

1. **Folder:** `docs/optimized-prompts/` under the project root (`git rev-parse --show-toplevel`, or the current directory outside a repository). Create it if it does not exist.
2. **Filename:** `YYYY-MM-DD-<topic>.md`, today's date and 2–4 kebab-case words for the topic, e.g. `2026-09-19-refactor-hand-limit-popup.md`. If the name exists, append `-2`, then `-3`.
3. **Contents:** only the optimized prompt (the "✨ OPTIMIZED PROMPT" section), without the scorecard or analysis.

Print the saved path as the last line.
