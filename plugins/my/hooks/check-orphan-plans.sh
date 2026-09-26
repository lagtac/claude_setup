#!/usr/bin/env bash
# SessionStart guard: surface orphaned plans in docs/plans/ so a forgotten,
# uncommitted, or mis-named plan can never sit undiscovered again.
#
# Flags a plan as an orphan when it is either:
#   - untracked  (exists in the working tree but never committed -> invisible
#     to git history; this is exactly how humble-floating-wave.md was lost), or
#   - undated    (name does not follow the mandated YYYY-MM-DD-<slug> convention).
#
# When the project keeps an index at docs/plans/README.md that opts in with the
# line `<!-- plans-index: strict -->`, it also flags a plan that is:
#   - unindexed  (its file name does not appear in README.md), or
#   - statusless (it has no `**Status:**` line, optionally inside a `> ` quote).
# Projects without that marker are not affected, even if they keep a README
# of their own design (some generate theirs, or keep status in ROADMAP.md).
#
# Reports (critiques, audits) may live in docs/reports/. Its files get the same
# checks, and the docs/plans/README.md index lists them too.
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
unindexed=()
statusless=()
index=docs/plans/README.md
strict=0
[ -f "$index" ] && grep -qF '<!-- plans-index: strict -->' "$index" && strict=1
for f in docs/plans/*.md docs/reports/*.md; do
    name=$(basename "$f")
    # README.md is a conventional index, not a dated plan -- never an orphan.
    [ "$name" = "README.md" ] && continue
    [[ "$name" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}- ]] || undated+=("$name")
    git ls-files --error-unmatch "$f" >/dev/null 2>&1 || untracked+=("$name")
    if [ "$strict" = 1 ]; then
        grep -qF -- "$name" "$index" || unindexed+=("$name")
        grep -qE '^(> )?\*\*Status:\*\*' "$f" || statusless+=("$name")
    fi
done

[ ${#undated[@]} -eq 0 ] && [ ${#untracked[@]} -eq 0 ] \
    && [ ${#unindexed[@]} -eq 0 ] && [ ${#statusless[@]} -eq 0 ] && exit 0

join() { local out; out=$(printf '%s, ' "$@"); echo "${out%, }"; }
msg=""
if [ ${#undated[@]} -gt 0 ] || [ ${#untracked[@]} -gt 0 ]; then
    msg="⚠ Orphaned plans in docs/plans/ or docs/reports/ (commit them, or rename to YYYY-MM-DD-<slug>)."
    [ ${#untracked[@]} -gt 0 ] && msg+=" Untracked: $(join "${untracked[@]}")."
    [ ${#undated[@]} -gt 0 ] && msg+=" Undated: $(join "${undated[@]}")."
fi
if [ ${#unindexed[@]} -gt 0 ] || [ ${#statusless[@]} -gt 0 ]; then
    [ -n "$msg" ] && msg+=" "
    msg+="⚠ Plans out of step with docs/plans/README.md (add a row, or a **Status:** line)."
    [ ${#unindexed[@]} -gt 0 ] && msg+=" Not in the index: $(join "${unindexed[@]}")."
    [ ${#statusless[@]} -gt 0 ] && msg+=" No status line: $(join "${statusless[@]}")."
fi

if [ "${1:-}" = "--text" ]; then
    echo "$msg"
    exit 0
fi

# JSON-escape the message (handles the literal double quotes / backslashes that
# could appear in a filename) and emit as SessionStart additionalContext.
esc=${msg//\\/\\\\}
esc=${esc//\"/\\\"}
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$esc"
