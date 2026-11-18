#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env and configure it first."
  exit 1
fi
if grep -qE 'api\.example\.com|replace-with-your-cloudflare-turnstile-secret' .env; then
  echo "Configure KIRINDL_API_DOMAIN and KIRINDL_TURNSTILE_SECRET in .env first."
  exit 1
fi

docker compose config --quiet
docker compose up -d --build
docker compose ps
