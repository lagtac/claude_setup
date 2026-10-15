---
paths:
  - "web/**/*.{vue,css}"
  - "web/scripts/style-diff.mjs"
---

# Checking "no visual change"

Check "no visual change" with `web/scripts/style-diff.mjs`, not screenshots,
and do not write a new diff script.

- It reads `getComputedStyle` for every element of every view on main
  (`:54300`) and the preview (`:54310`), at 390 and 1280 pixels, in light and
  dark. It subtracts what changes between two loads of main.
- It finds the pages in `pages/` itself. `--pages` narrows a run. The command
  and the options are in the script's header.
- A full run takes about 11 minutes, so start it in the background.
- The dev stack must serve current `main`. After a merge that adds a package,
  run `npm ci` in the `web` container (row 126).
