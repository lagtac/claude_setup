#!/usr/bin/env bash
# Set or report the **Verbosity: <level>** directive in a CLAUDE.md file.
# Usage: set-verbosity.sh [min|medium|off] [--global] [--create]
#   No level     → report current verbosity (project + global, or global alone with --global).
#   With level   → write the directive in the project (or global with --global) CLAUDE.md.
#   --create     → permit creating a missing project CLAUDE.md (never global).
# Exit codes: 0 ok, 1 error, 2 needs --create confirmation.

set -euo pipefail

level=""
global=0
create=0

for arg in "$@"; do
  case "$arg" in
    --global) global=1 ;;
    --create) create=1 ;;
    min|medium|off) level="$arg" ;;
    -h|--help)
      sed -n '2,7p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    "") ;;
    *)
      echo "Verbosity must be one of: min, medium, off. Got: $arg" >&2
      exit 1
      ;;
  esac
done

global_file="$HOME/.claude/CLAUDE.md"

if [[ $global -eq 1 ]]; then
  target="$global_file"
else
  dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    if [[ -e "$dir/.git" || -f "$dir/composer.json" || -f "$dir/package.json" || -f "$dir/pyproject.toml" ]]; then
      break
    fi
    dir="$(dirname "$dir")"
  done
  if [[ "$dir" == "/" ]]; then
    echo "Could not find project root (no .git/composer.json/package.json/pyproject.toml above $PWD)." >&2
    exit 1
  fi
  target="$dir/CLAUDE.md"
fi

current_level() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  grep -m1 -oE '^\*\*Verbosity: (min|medium|off)\*\*' "$file" 2>/dev/null \
    | sed -E 's/^\*\*Verbosity: (min|medium|off)\*\*/\1/' || true
}

# Report mode
if [[ -z "$level" ]]; then
  if [[ $global -eq 1 ]]; then
    if [[ ! -f "$target" ]]; then
      echo "Global: file not found ($target)"
      exit 0
    fi
    g=$(current_level "$target")
    if [[ -z "$g" ]]; then
      echo "Global: no directive ($target)"
    else
      echo "Global: $g ($target)"
    fi
    exit 0
  fi
  g=""
  [[ -f "$global_file" ]] && g=$(current_level "$global_file")
  if [[ -f "$target" ]]; then
    p=$(current_level "$target")
    if [[ -n "$p" ]]; then
      echo "Project: $p ($target)"
    else
      echo "Project: none — inherits global"
    fi
  else
    echo "Project: none — inherits global"
  fi
  if [[ -n "$g" ]]; then
    echo "Global:  $g ($global_file)"
  else
    echo "Global:  not set"
  fi
  exit 0
fi

# Write mode: missing target
if [[ ! -f "$target" ]]; then
  if [[ $global -eq 1 ]]; then
    echo "Global CLAUDE.md not found at $target. Refusing to create." >&2
    exit 1
  fi
  if [[ $create -eq 0 ]]; then
    echo "Project CLAUDE.md not found at $target. Re-run with --create to create it." >&2
    exit 2
  fi
  printf '# Project Notes\n\n**Verbosity: %s**\n' "$level" > "$target"
  echo "Created $target with verbosity: $level."
  exit 0
fi

# Count existing directives
match_count=$(grep -cE '^\*\*Verbosity: ' "$target" || true)

if [[ "$match_count" -gt 1 ]]; then
  echo "Multiple Verbosity directives found in $target — resolve manually:" >&2
  grep -nE '^\*\*Verbosity: ' "$target" >&2
  exit 1
fi

old_level=$(current_level "$target")

if [[ "$match_count" -eq 1 ]]; then
  awk -v level="$level" -v is_global="$global" '
    /^\*\*Verbosity: (min|medium|off)\*\*/ {
      rest = ""
      if (is_global == 1 && match($0, / \*\(.*\)\*$/)) {
        rest = substr($0, RSTART, RLENGTH)
      }
      print "**Verbosity: " level "**" rest
      next
    }
    { print }
  ' "$target" > "$target.tmp"
  mv "$target.tmp" "$target"
  echo "Set verbosity in $target: ${old_level:-absent} → $level."
  exit 0
fi

# No directive found — insert.
if [[ $global -eq 1 ]]; then
  echo "No directive found in global $target. Refusing to insert — investigate first." >&2
  exit 1
fi

if grep -qE '^## ' "$target"; then
  awk -v level="$level" '
    !inserted && /^## / {
      print
      print ""
      print "**Verbosity: " level "**"
      inserted = 1
      next
    }
    { print }
  ' "$target" > "$target.tmp"
elif head -n1 "$target" | grep -q '^---$'; then
  awk -v level="$level" '
    NR == 1 && /^---$/ { print; in_fm = 1; next }
    in_fm && /^---$/ {
      print
      print ""
      print "**Verbosity: " level "**"
      in_fm = 0
      next
    }
    { print }
  ' "$target" > "$target.tmp"
else
  { printf '**Verbosity: %s**\n\n' "$level"; cat "$target"; } > "$target.tmp"
fi
mv "$target.tmp" "$target"
echo "Set verbosity in $target: absent → $level."
