#!/usr/bin/env bash
set -euo pipefail

# start.sh - Launcher for ai-doc-assistant
# Usage: ./start.sh [-d|--detach] [-f|--follow] [--no-build]
# -d / --detach : start containers in background (default)
# -f / --follow : run in foreground and stream logs
# --no-build : skip rebuilding images
#
# The script prefers `docker compose` (modern) and falls back to `docker-compose` if needed.
# Ensure any required environment variables are provided (this repo uses .env for backend).

# Determine docker compose command
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  DCMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DCMD="docker-compose"
else
  echo "Error: neither 'docker compose' nor 'docker-compose' found. Install Docker and Docker Compose."
  exit 1
fi

# Warn if .env not present
if [ ! -f .env ]; then
  echo "Warning: .env file not found in project root. Backend may require environment variables (LLM keys, etc)."
fi

# Defaults
DETACH=true
FOLLOW=false
NOBUILD=false

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--detach)
      DETACH=true; shift ;;
    -f|--follow)
      FOLLOW=true; shift ;;
    --no-build)
      NOBUILD=true; shift ;;
    *)
      echo "Unknown option: $1"; exit 1 ;;
  esac
done

BUILD_FLAGS="--build --remove-orphans"
if [ "$NOBUILD" = true ]; then
  BUILD_FLAGS=""
fi

if [ "$FOLLOW" = true ]; then
  echo "Starting services (foreground) via: $DCMD up $BUILD_FLAGS"
  exec $DCMD up $BUILD_FLAGS
else
  echo "Starting services (detached) via: $DCMD up $BUILD_FLAGS -d"
  $DCMD up $BUILD_FLAGS -d
  echo "Services started in background."
  echo "View status: $DCMD ps"
  echo "Follow logs: $DCMD logs -f"
fi

exit 0
