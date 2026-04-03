---
description: Push with pre-push checks
---

# Push instructions

1. Run `git status` to confirm all intended changes are committed
2. Run `git log --oneline @{u}..HEAD 2>/dev/null` to show what will be pushed (skip if no upstream)
3. Push to the remote
