#!/bin/sh
# Retired-content gate for the S14 closeout deck.
#
# The per-shape noise constant that used to gate the fourth conjunct was retired on
# 2026-08-14. By owner ruling of 2026-08-18 retired material is DELETED, not annotated.
# This gate fails if it — or any paraphrase that restates it without naming it — comes back.
#
# The pattern lives HERE and nowhere else, so that documents can describe the rule without
# tripping it. This script excludes itself from the scan.
#
#   usage:  sh pic/check_retired.sh          (run from reports/)
#   exit 0 = clean, exit 1 = retired content present
set -u

PATTERN='eta_s|η_s|η_large|η_medium|η_tiny|pinned constant|pinned margin|empirical margin|tolerance band|noise margin|288×|4\.6×|0\.0041953|0\.1228459|0\.4465998'

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SELF="$ROOT/pic/check_retired.sh"
rc=0

for f in "$ROOT"/outline.md "$ROOT"/outline.zh-Hant.md "$ROOT"/outline_compact.md \
         "$ROOT"/pic/README.md "$ROOT"/pic/*.py; do
    [ -f "$f" ] || continue
    [ "$f" = "$SELF" ] && continue
    n=$(grep -icE "$PATTERN" "$f" 2>/dev/null || true)
    if [ "${n:-0}" -gt 0 ]; then
        printf 'FAIL  %-28s %s hit(s)\n' "${f#"$ROOT"/}" "$n"
        grep -inE "$PATTERN" "$f" | cut -c1-120 | sed 's/^/        /'
        rc=1
    fi
done

[ "$rc" -eq 0 ] && echo "clean — no retired-metric content in outline.md, outline.zh-Hant.md, outline_compact.md, pic/README.md, pic/*.py"
exit "$rc"
