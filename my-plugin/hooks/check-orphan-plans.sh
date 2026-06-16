#!/usr/bin/env bash
# SessionStart guard: surface orphaned plans in docs/plans/ so a forgotten,
# uncommitted, or mis-named plan can never sit undiscovered again.
#
# Flags a plan as an orphan when it is either:
#   - untracked  (exists in the working tree but never committed -> invisible
#     to git history; this is exactly how humble-floating-wave.md was lost), or
#   - undated    (name does not follow the mandated YYYY-MM-DD-<slug> convention).
#
# Emits a Claude Code SessionStart additionalContext line when orphans exist;
# stays silent (exit 0, no output) otherwise. Run with --text for a plain-text
# report when testing by hand.

set -euo pipefail

root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$root" || exit 0
[ -d docs/plans ] || exit 0

shopt -s nullglob
undated=()
untracked=()
for f in docs/plans/*.md; do
    name=$(basename "$f")
    [[ "$name" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}- ]] || undated+=("$name")
    git ls-files --error-unmatch "$f" >/dev/null 2>&1 || untracked+=("$name")
done

[ ${#undated[@]} -eq 0 ] && [ ${#untracked[@]} -eq 0 ] && exit 0

join() { local out; out=$(printf '%s, ' "$@"); echo "${out%, }"; }
msg="⚠ Orphaned plans in docs/plans/ (commit them, or rename to YYYY-MM-DD-<slug>)."
[ ${#untracked[@]} -gt 0 ] && msg+=" Untracked: $(join "${untracked[@]}")."
[ ${#undated[@]} -gt 0 ] && msg+=" Undated: $(join "${undated[@]}")."

if [ "${1:-}" = "--text" ]; then
    echo "$msg"
    exit 0
fi

# JSON-escape the message (handles the literal double quotes / backslashes that
# could appear in a filename) and emit as SessionStart additionalContext.
esc=${msg//\\/\\\\}
esc=${esc//\"/\\\"}
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$esc"
