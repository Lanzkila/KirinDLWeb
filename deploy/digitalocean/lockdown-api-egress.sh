#!/usr/bin/env bash
set -euo pipefail

# Paired with deploy/digitalocean/compose.yaml:
# API container: 172.31.240.3
# Caddy container: 172.31.240.2
API_CONTAINER_IP=172.31.240.3/32
CADDY_CONTAINER_IP=172.31.240.2/32
DOCKER_SUBNET=172.31.240.0/24

if ! command -v iptables >/dev/null 2>&1; then
  echo "iptables is required; install/start Docker before enabling this guard." >&2
  exit 1
fi
if ! iptables -w -nL DOCKER-USER >/dev/null 2>&1; then
  echo "Docker's DOCKER-USER chain is not present. Is the Docker daemon running?" >&2
  exit 1
fi

# Allow only reply packets for the reverse-proxy connection Caddy opened to
# Uvicorn. The API process cannot initiate a new connection to the Caddy IP.
iptables -w -N KIRINDL_API_EGRESS 2>/dev/null || true
iptables -w -F KIRINDL_API_EGRESS
iptables -w -A KIRINDL_API_EGRESS \
  -d "$CADDY_CONTAINER_IP" \
  -p tcp --sport 8000 \
  -m conntrack --ctstate ESTABLISHED,RELATED \
  -j ACCEPT

# Deny private, shared-address, local, link-local, reserved and all addresses
# on the private Compose subnet. Public internet traffic returns to Docker's
# normal forwarding policy and is still constrained by the cloud firewall.
for cidr in \
  0.0.0.0/8 \
  10.0.0.0/8 \
  100.64.0.0/10 \
  127.0.0.0/8 \
  169.254.0.0/16 \
  172.16.0.0/12 \
  192.0.0.0/24 \
  192.0.2.0/24 \
  192.168.0.0/16 \
  198.18.0.0/15 \
  198.51.100.0/24 \
  203.0.113.0/24 \
  224.0.0.0/4 \
  240.0.0.0/4 \
  255.255.255.255/32 \
  "$DOCKER_SUBNET"
do
  iptables -w -A KIRINDL_API_EGRESS -d "$cidr" -j DROP
done
iptables -w -A KIRINDL_API_EGRESS -j RETURN

iptables -w -C DOCKER-USER -s "$API_CONTAINER_IP" -j KIRINDL_API_EGRESS 2>/dev/null || \
  iptables -w -I DOCKER-USER 1 -s "$API_CONTAINER_IP" -j KIRINDL_API_EGRESS

# Also block API-container attempts to reach host INPUT services such as the
# bridge gateway. Outbound DNS is pinned to public resolvers in Compose.
iptables -w -C INPUT -s "$API_CONTAINER_IP" -j DROP 2>/dev/null || \
  iptables -w -I INPUT 1 -s "$API_CONTAINER_IP" -j DROP
