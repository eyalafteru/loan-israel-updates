#!/bin/bash
# Commit-msg hook — ensures memory-bank is updated when code changes are committed.
# Bypass: WIP: prefix, [skip-memory] tag, or --no-verify

if [ -n "$1" ] && [ -f "$1" ]; then
  if grep -qiE '^WIP:|\[skip-memory\]' "$1"; then
    exit 0
  fi
fi

STAGED=$(git diff --cached --name-only)
[ -z "$STAGED" ] && exit 0

# Extensions relevant for this project
CODE_FILES=$(echo "$STAGED" | grep -E '\.(js|py|css|html|bat|csv)$' | wc -l)
[ "$CODE_FILES" -eq 0 ] && exit 0

MEMORY_UPDATED=$(echo "$STAGED" | grep -E '(activeContext\.md|memory-bank/sessions/)' | wc -l)

if [ "$MEMORY_UPDATED" -eq 0 ]; then
  echo ""
  echo "============================================"
  echo "  MEMORY BANK: session update required"
  echo "============================================"
  echo "  You changed $CODE_FILES code file(s) but did not update"
  echo "  the memory bank. Create a session file or update activeContext.md."
  echo ""
  echo "  Bypass: WIP: prefix | [skip-memory] tag | --no-verify"
  echo "============================================"
  exit 1
fi

exit 0
