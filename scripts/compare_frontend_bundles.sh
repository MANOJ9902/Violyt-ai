#!/bin/bash
# Compare the running (old) bundle against the freshly built one before switching.

probe() {
  local img="$1" label="$2"
  echo "--- $label ---"
  sudo docker run --rm --entrypoint sh "$img" -c '
    echo -n "  api_origin_65.0.82.127: "; grep -rl "65.0.82.127" /app/.next 2>/dev/null | wc -l
    echo -n "  localhost:8000        : "; grep -rl "localhost:8000" /app/.next 2>/dev/null | wc -l
    echo -n "  axios timeout 600000  : "; grep -rl "600000" /app/.next/static 2>/dev/null | wc -l
    echo -n "  axios timeout 1200000 : "; grep -rl "1200000" /app/.next/static 2>/dev/null | wc -l
    echo -n "  20 min message        : "; grep -rl "Timed out waiting for the pipeline (20 min)" /app/.next 2>/dev/null | wc -l
    echo -n "  10 min message        : "; grep -rl "Timed out waiting for the pipeline (10 min)" /app/.next 2>/dev/null | wc -l
  '
}

probe violyt-frontend:rollback "OLD (currently running)"
echo
probe violyt-frontend:local "NEW (just built)"
