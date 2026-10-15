---
paths:
  - "**/*.{md,mdx}"
---

# Markdown Commands

Run these on the `.md` files you created or edited, never on `"**/*.md"`.

- **Lint:** `markdownlint-cli2 --config <config> <files>`
- **Fix:** `markdownlint-cli2 --config <config> --fix <files>`

`<config>` is the project's own markdownlint config, or
`~/.config/markdownlint-cli2/.markdownlint-cli2.jsonc` when it has none.
