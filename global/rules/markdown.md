---
paths:
  - "**/*.{md,mdx}"
---

# Markdown Commands

Lint the `.md` files you created or edited, never `"**/*.md"`:
`markdownlint-cli2 --config <config> <files>`. Report what it finds. Never
pass `--fix`: the user formats docs in nvim when they want to.

`<config>` is the project's own markdownlint config, or
`~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc` when it has none.
