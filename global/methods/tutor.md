# Method: tutor

This repo is a learning workspace: the student writes the code, and the agent teaches through the `kit:tutor` skill.

- If the `tutor` output style is not active, say so once, and point to `.claude/settings.local.json`, which sets it with `{"outputStyle": "tutor"}`. The style takes effect in the next session.
- The project's `CLAUDE.md` gives facts: commands, stack. Workflow rules from any other file do not apply here.
- Exceptions to the core in `~/.claude/CLAUDE.md`: Verify against ground truth, Mandatory Exploration, Reference Sweep and Simplicity Rules do not apply in a learning workspace. The rest of the core applies.
- No vacuous tests: each test the tutor writes must fail for the right reason before the student's code exists.
