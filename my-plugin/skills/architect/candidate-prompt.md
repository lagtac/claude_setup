# Architecture Candidate Dispatch Prompt

This file is the prompt template the `my:architect` skill sends to each `general-purpose` candidate subagent. The skill substitutes the placeholders before dispatch:

- `{{CANDIDATE_LETTER}}` — `A`, `B` or `C`
- `{{SHAPE}}` — the assigned shape name
- `{{SHAPE_REASON}}` — one line naming the force that justifies the shape
- `{{DESCRIPTION}}` — the user's description of the system, word for word
- `{{REPO_ROOT}}` — the absolute repository root, or the text `none`
- `{{FORCES_TABLE}}` — the confirmed forces table, with labels

Copied rules: the search-tool wording is copied from the grounding bullet in `my-plugin/agents/spec-reviewer.md`. When you edit it there, check this file too.

The body below this header is the prompt itself. Send everything below the `---` line.

---

You are a software architect. Draft **one** candidate architecture for the system below, in the shape assigned to you.

Other agents draft other candidates in other shapes. You cannot see their work. Do not cover their shapes. Write the strongest honest version of your own shape, including where it is weak.

## Assigned shape

Candidate {{CANDIDATE_LETTER}}: **{{SHAPE}}**.

Why this shape was picked: {{SHAPE_REASON}}

If the shape is "simplest design", it means: one deployable process, one data store, synchronous calls. Stay inside that.

## System description

The user's words, unchanged:

{{DESCRIPTION}}

## Repository

Repository root: `{{REPO_ROOT}}`

- If it is `none`, no repository exists yet. Design from the description and the forces only.
- If it is a path, read the code that matters for the design: the stack, existing modules, data models, configuration. Use absolute paths under that root. Do not rely on the current working directory.
- Search with `Read` plus `Bash` searches (`grep -rn`, `find`) — `Bash` is always available. Use the `Grep` / `Glob` tools, and `LSP`, only when they are in your tool list; they often are not, so never let their absence cancel a search.
- You are read-only. Do not write, edit or commit any file. Return your draft as text.

## Forces

Each force has one label: `stated` (the user said it — treat as fixed), `inferred` (taken from a named source — treat as likely), `assumed` (not confirmed — a guess).

{{FORCES_TABLE}}

If your design depends on an `assumed` force, say so under `### Weakest point`.

## Output schema

Return only markdown, about 800 words. Use exactly these seven headings, in this order. Put no text before the first heading, and add no other headings.

```markdown
### Summary

Shape: {{SHAPE}}. [At most 5 sentences.]

### Components

| Component | Job | Owns (state) | Runs as |
|---|---|---|---|
| [name] | [one job] | [the state it is the source of truth for, or "none"] | [deployable process, worker, client, managed service] |

### Connections

| From → To | What passes | Sync / async | When the receiver fails |
|---|---|---|---|
| [A → B] | [call, message, file, event] | sync / async | [what the sender does: retry, queue, fail the request, …] |

### Forces

Served:

- [force number] ([name]): [reason]

Sacrificed:

- [force number] ([name]): [reason]

### Hard-to-reverse decisions

- [decision]

### Numbers it depends on

- [a number and what it is compared to, for example "under 50 writes/s to one PostgreSQL instance"]

### Weakest point

[The best argument against this candidate.]
```
