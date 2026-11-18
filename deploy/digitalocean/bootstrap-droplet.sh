#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo: sudo bash deploy/digitalocean/bootstrap-droplet.sh"
  exit 1
fi

if ! grep -qiE 'ubuntu.*(22\.04|24\.04)' /etc/os-release; then
  echo "This setup is prepared for Ubuntu 22.04 or 24.04."
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl git

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

APP_DIR=/opt/kirindl
mkdir -p "$APP_DIR"
if [[ ! -d "$APP_DIR/.git" ]]; then
  git clone --depth 1 https://github.com/Lanzkila/KirinDLWeb.git "$APP_DIR"
else
  git -C "$APP_DIR" pull --ff-only
fi

cd "$APP_DIR"

# Install a persistent Docker egress guard. The API container has a fixed IP
# on a private Compose network; it may reach public internet destinations only.
install -m 0755 "$APP_DIR/deploy/digitalocean/lockdown-api-egress.sh" /usr/local/sbin/kirindl-api-egress-guard
install -m 0644 "$APP_DIR/deploy/digitalocean/kirindl-api-egress-guard.service" /etc/systemd/system/kirindl-api-egress-guard.service
systemctl daemon-reload
systemctl enable --now kirindl-api-egress-guard.service

DATA_DIR="$APP_DIR/deploy/digitalocean/data"
mkdir -p "$DATA_DIR"
chown -R 10001:10001 "$DATA_DIR"
chmod 750 "$DATA_DIR"

ENV_FILE="$APP_DIR/deploy/digitalocean/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cp "$APP_DIR/deploy/digitalocean/.env.example" "$ENV_FILE"
fi
chmod 600 "$ENV_FILE"

echo
echo "Docker is installed. Deployment files are in $APP_DIR/deploy/digitalocean."
echo "Edit $ENV_FILE and set:"
echo "  - KIRINDL_API_DOMAIN to your real DNS hostname"
echo "  - KIRINDL_TURNSTILE_SECRET to the private Cloudflare Turnstile secret"
echo "Then run: cd $APP_DIR/deploy/digitalocean && sudo ./deploy.sh"
