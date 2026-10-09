#!/usr/bin/env bash
# Usage:  bash demo/make_gif.sh
# 1. Runs the real tool inside Docker (pty) and records it to demo/demo.cast (record.py)
# 2. Renders the cast to demo/demo.gif with asciinema's `agg`
# Reads ONLY OPENROUTER_API_KEY and DEMO_MODEL from the environment or the repo's .env
# (.env also holds publish tokens, so it is never passed wholesale to a container).
set -euo pipefail
cd "$(dirname "$0")/.."

read_env() {
  [ -f .env ] || return 0
  grep -E "^$1=" .env | tail -n1 | cut -d= -f2- | tr -d '\r"' | sed "s/^'//; s/'\$//" || true
}
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-$(read_env OPENROUTER_API_KEY)}"
DEMO_MODEL="${DEMO_MODEL:-$(read_env DEMO_MODEL)}"
: "${OPENROUTER_API_KEY:?Set OPENROUTER_API_KEY in the environment or .env}"
export OPENROUTER_API_KEY DEMO_MODEL

# Git Bash would rewrite the /data part of the mount into a Windows path; turn that off.
export MSYS_NO_PATHCONV=1
HOST_DEMO="$(pwd -W 2>/dev/null || pwd)/demo"

docker build -t stv-vhs -f demo/Dockerfile .
docker run --rm -e OPENROUTER_API_KEY -e DEMO_MODEL -v "$HOST_DEMO:/vhs" --entrypoint bash stv-vhs \
  -c "bash /vhs/setup_repo.sh && cd /tmp/demo-app && python3 /vhs/record.py /vhs/demo.cast"
docker run --rm -v "$HOST_DEMO:/data" ghcr.io/asciinema/agg \
  --idle-time-limit 2 --last-frame-duration 6 --font-size 16 --theme dracula /data/demo.cast /data/demo.gif
echo "Done: demo/demo.gif"
