---
name: set-verbosity
description: >
  Use when the user wants to change or check the Output Discipline verbosity
  level (`min`, `medium`, or `off`) in a CLAUDE.md file, either for the
  current project or globally. Trigger on requests like "set verbosity to
  min", "make output minimal", "switch to off verbosity for this project",
  "what is my current verbosity", or invocation via /set-verbosity.
argument-hint: "[min|medium|off] [--global]"
disable-model-invocation: true
allowed-tools: Bash
---

# Set Verbosity

This skill is a thin wrapper around `set-verbosity.sh`, which handles all parsing, validation, file location, and editing. Do not duplicate or replicate its logic.

## Run

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/set-verbosity/set-verbosity.sh" $ARGUMENTS
```

Forward the script's stdout to the user verbatim. The script's exit codes mean:

- **0** — success (set or reported). Done.
- **1** — error (bad level, missing global file, multiple directives, no project root). Show the stderr message and stop.
- **2** — project CLAUDE.md does not exist. The script's stderr explains this. Ask the user whether to create it; if yes, re-run the same invocation with `--create` appended. If no, stop.

## What the script does

- Parses `[min|medium|off]` (positional, optional) and `--global` (flag).
- No level → report mode (project + global, or global alone with `--global`).
- With level → write or replace the `**Verbosity: <level>**` line in the target CLAUDE.md.
- Locates project CLAUDE.md by walking up from `$PWD` for `.git`, `composer.json`, `package.json`, or `pyproject.toml`.
- Preserves the trailing `*(global default)*` italic comment when editing the global file.
- Refuses to create a missing global CLAUDE.md or insert a directive into one that lacks one.
- Refuses when multiple directives are found and asks the user to resolve.

