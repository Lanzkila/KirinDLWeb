#!/usr/bin/env python3
"""Create a DigitalOcean Cloud Firewall with explicit egress and SSRF blocks.

Required environment:
  DIGITALOCEAN_TOKEN  DigitalOcean token with firewall and Droplet read access
  DO_DROPLET_ID       Numeric ID of the target Droplet
  DO_SSH_ALLOWED_CIDR Current public SSH IP as /32 or /128
Optional:
  DO_FIREWALL_NAME    Defaults to kirindl-engine-firewall
"""

from __future__ import annotations

import ipaddress
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE = "https://api.digitalocean.com/v2"


def api_request(token: str, method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        API_BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DigitalOcean API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach DigitalOcean API: {exc}") from exc
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def droplet_public_addresses(token: str, droplet_id: int) -> list[str]:
    payload = api_request(token, "GET", f"/droplets/{droplet_id}")
    networks = payload.get("droplet", {}).get("networks", {})
    addresses: list[str] = []
    for family in ("v4", "v6"):
        for item in networks.get(family, []):
            if item.get("type") == "public" and item.get("ip_address"):
                parsed = ipaddress.ip_address(item["ip_address"])
                addresses.append(f"{parsed}/{parsed.max_prefixlen}")
    if not addresses:
        raise RuntimeError("No public Droplet IP was returned. Check the Droplet ID.")
    return addresses


def main() -> int:
    token = os.getenv("DIGITALOCEAN_TOKEN", "").strip()
    droplet_id = os.getenv("DO_DROPLET_ID", "").strip()
    ssh_cidr = os.getenv("DO_SSH_ALLOWED_CIDR", "").strip()
    firewall_name = os.getenv("DO_FIREWALL_NAME", "kirindl-engine-firewall").strip()

    if not token or not droplet_id or not ssh_cidr:
        print("Set DIGITALOCEAN_TOKEN, DO_DROPLET_ID and DO_SSH_ALLOWED_CIDR.", file=sys.stderr)
        return 2

    try:
        numeric_id = int(droplet_id)
        ssh_network = ipaddress.ip_network(ssh_cidr, strict=False)
    except ValueError as exc:
        print(f"Invalid Droplet ID or SSH CIDR: {exc}", file=sys.stderr)
        return 2
    if ssh_network.prefixlen != ssh_network.max_prefixlen:
        print("SSH CIDR must be a single address (/32 for IPv4 or /128 for IPv6).", file=sys.stderr)
        return 2

    own_public_addresses = droplet_public_addresses(token, numeric_id)
    any_ip = ["0.0.0.0/0", "::/0"]

    inbound = [
        {
            "protocol": "tcp",
            "ports": "22",
            "action": "allow",
            "sources": {"addresses": [str(ssh_network)]},
        },
        {
            "protocol": "tcp",
            "ports": "80",
            "action": "allow",
            "sources": {"addresses": any_ip},
        },
        {
            "protocol": "tcp",
            "ports": "443",
            "action": "allow",
            "sources": {"addresses": any_ip},
        },
        {
            "protocol": "udp",
            "ports": "443",
            "action": "allow",
            "sources": {"addresses": any_ip},
        },
    ]

    # Deny private, shared-address, loopback, link-local, reserved, multicast
    # and the Droplet's own public IP before broader egress allows are applied.
    blocked_destinations = [
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.0.0.0/24",
        "192.0.2.0/24",
        "192.88.99.0/24",
        "192.168.0.0/16",
        "198.18.0.0/15",
        "198.51.100.0/24",
        "203.0.113.0/24",
        "224.0.0.0/4",
        "240.0.0.0/4",
        "255.255.255.255/32",
        "::/96",
        "::ffff:0:0/96",
        "64:ff9b::/96",
        "64:ff9b:1::/48",
        "100::/64",
        "2001::/23",
        "2001:db8::/32",
        "2002::/16",
        "fc00::/7",
        "fe80::/10",
        "ff00::/8",
        *own_public_addresses,
    ]
    outbound = [
        {
            "protocol": "all",
            "ports": "0",
            "action": "deny",
            "destinations": {"addresses": [cidr]},
        }
        for cidr in blocked_destinations
    ]
    outbound.extend([
        {
            "protocol": "tcp",
            "ports": "80",
            "action": "allow",
            "destinations": {"addresses": any_ip},
        },
        {
            "protocol": "tcp",
            "ports": "443",
            "action": "allow",
            "destinations": {"addresses": any_ip},
        },
        {
            "protocol": "udp",
            "ports": "53",
            "action": "allow",
            "destinations": {"addresses": any_ip},
        },
        {
            "protocol": "tcp",
            "ports": "53",
            "action": "allow",
            "destinations": {"addresses": any_ip},
        },
        {
            "protocol": "udp",
            "ports": "123",
            "action": "allow",
            "destinations": {"addresses": any_ip},
        },
    ])

    # Stay below the provider's per-firewall rule cap.
    if len(inbound) + len(outbound) > 50:
        raise RuntimeError("Firewall rule count exceeds the provider limit.")

    body = {
        "name": firewall_name,
        "droplet_ids": [numeric_id],
        "inbound_rules": inbound,
        "outbound_rules": outbound,
    }
    result = api_request(token, "POST", "/firewalls", body)
    firewall_info = result.get("firewall", {})
    print("Cloud Firewall created and attached.")
    print("ID:", firewall_info.get("id", "(not returned)"))
    print("Name:", firewall_info.get("name", firewall_name))
    print("Inbound: SSH from", ssh_network, "; public HTTP and HTTPS.")
    print("Outbound: DNS, NTP, HTTP and HTTPS only.")
    print("Private, local, shared-address, link-local, reserved and Droplet-self destinations are denied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
