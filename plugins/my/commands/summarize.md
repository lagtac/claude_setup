---
description: Compare a plan/review against the actual git diff
---

Write an implementation summary for: **$ARGUMENTS**

If the argument is empty, print `Usage: /my:summarize <plan path, filename or slug>` and stop.

Use the Agent tool with `subagent_type: "my:summarizer"` and `description: "Implementation summary"`. Its prompt holds the argument word for word, and the absolute repository root from `git rev-parse --show-toplevel`. Wait for its result.

The agent writes the summary file and returns its path and text. Print the path, then the summary text unchanged. If the agent reports that no source file matched, print its message and stop.
