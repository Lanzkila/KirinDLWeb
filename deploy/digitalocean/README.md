# KirinDL Web Engine — DigitalOcean deployment

This prepared deployment uses one Ubuntu 24.04 Droplet in Singapore, Docker Compose, Caddy-managed HTTPS, a persistent data directory and a DigitalOcean Cloud Firewall.

## Why DigitalOcean

The extractor accepts URLs and can follow redirects or contact secondary hosts. Application URL checks alone are not enough for a public extractor service. This deployment combines DigitalOcean Cloud Firewall egress rules with a host-side Docker egress guard. The API container cannot reach private, loopback, link-local, reserved, Droplet-self, Docker bridge-gateway or sibling-container addresses. The host guard allows only established API replies to Caddy on the private network; Caddy can initiate the reverse-proxy connection to API port 8000. DigitalOcean documents that Cloud Firewall deny rules take precedence over matching allow rules and that the firewall blocks traffic not expressly permitted. The service is free. See the references below.

## 1. Create the Droplet

Create an Ubuntu 24.04 Droplet with:

- Region: Singapore (`sgp1`)
- Plan: Basic, 1 vCPU / 2 GiB RAM / 50 GiB SSD / 2,000 GiB transfer
- Current listed price: USD $12/month
- Authentication: SSH key preferred

This is a starter single-worker configuration, not a high-throughput service. Prices and region/plan availability can change; check the provider page at creation time.

## 2. Create the firewall before exposing the service

Create a DigitalOcean personal access token with permissions to read Droplets and create Cloud Firewalls. Then, from a machine with Python 3.10+, run:

    export DIGITALOCEAN_TOKEN="your-personal-access-token"
    export DO_DROPLET_ID="your-droplet-id"
    export DO_SSH_ALLOWED_CIDR="your-current-public-ip/32"
    python3 deploy/digitalocean/create-firewall.py

For an IPv6 SSH address use `/128`. The script refuses a broad SSH range such as `0.0.0.0/0`.

The firewall allows inbound SSH only from that address, plus public HTTP/HTTPS for Caddy. Outbound traffic is limited to DNS, NTP, HTTP and HTTPS; private/local/link-local/reserved/self IPs are explicitly denied. Deny rules take precedence over allows. Review the created firewall in the DigitalOcean Control Panel before deploying.

If your home public IP changes, update the firewall's SSH source before reconnecting. Do not remove the egress deny rules while the downloader is public.

## 3. Point a domain to the Droplet

Use a domain you control, for example `api.your-domain.example`. Create an A record pointing to the Droplet's public IPv4 address. Wait until DNS resolves before starting Caddy. Add an AAAA record only if you intentionally configure and test IPv6 on the Droplet.

Caddy obtains and renews HTTPS certificates automatically after ports 80 and 443 are reachable.

## 4. Bootstrap Docker and the app

Check out the repository on the Droplet, then run:

    sudo bash deploy/digitalocean/bootstrap-droplet.sh

The script installs Docker, places the repository at `/opt/kirindl`, creates the persistent data directory and copies the example environment file with restrictive permissions.

Edit:

    sudo nano /opt/kirindl/deploy/digitalocean/.env

Set at least:

- `KIRINDL_API_DOMAIN` to the real DNS hostname.
- `KIRINDL_TURNSTILE_SECRET` to the private Cloudflare Turnstile secret.
- `KIRINDL_TURNSTILE_HOSTNAMES` to your GitHub Pages hostname or a domain you control.
- `KIRINDL_ALLOWED_ORIGINS` to the exact website origins.

Then deploy:

    cd /opt/kirindl/deploy/digitalocean
    sudo ./deploy.sh

Check logs:

    sudo docker compose logs -f

Health check:

    curl https://api.your-domain.example/api/v1/health

## 5. Configure Cloudflare Turnstile

Create a Turnstile widget for the browser hostnames (for example `lanzkila.github.io`) using the action `download`.

- Put the **sitekey** in `public/kirindl-config.js` as `turnstileSiteKey`. This is a public browser key.
- Put the **secret key** only in `deploy/digitalocean/.env` as `KIRINDL_TURNSTILE_SECRET`.
- Keep `KIRINDL_REQUIRE_TURNSTILE=true` in production.

The API checks every task-creation token with Cloudflare Siteverify and validates the expected hostname and `download` action. Tokens are short-lived and single-use. Never put the secret key in frontend JavaScript or commit it. Do not add shared hosting domains such as `raw.githack.com` to the accepted hostnames; use only GitHub Pages for this account or a domain you control.

## 6. Connect the web preview

After the API hostname and Turnstile widget are ready, edit `public/kirindl-config.js`:

- `apiBase`: `https://` plus the API hostname, with no trailing slash.
- `turnstileSiteKey`: the widget's public sitekey.

Commit this public config update. Do not add the Turnstile secret to the repository.

## Operating limits and safety

- One Uvicorn worker, one extractor worker and one active download at a time on the starter Droplet.
- Each task is limited to 2 GiB output; the backend also checks free disk space before and during downloads.
- Output and SQLite state live in `/opt/kirindl/deploy/digitalocean/data`; old tasks are pruned after 24 hours by default.
- The API container has no published host port, runs as a non-root user, drops Linux capabilities and uses a read-only root filesystem. Caddy is the only public web entrypoint. A persistent DOCKER-USER/INPUT rule set blocks the API container from host services and private networks while allowing established replies to Caddy; API DNS uses explicit public resolvers.
- The Cloud Firewall egress policy is part of the SSRF boundary. Do not expose the API directly on port 8000, change its fixed Compose IP/subnet without updating the host guard, or remove the private-network deny rules.
- Turnstile and per-client rate limiting reduce automated abuse but do not provide user accounts or per-user task ownership.
- This setup is single-instance; do not scale it horizontally while using SQLite and local disk.
- Test yt-dlp, FFmpeg merge, gallery-dl, output download, cancellation and cleanup with sources you are authorised to access before announcing the service publicly.

## References

- DigitalOcean Droplet pricing: https://www.digitalocean.com/pricing/droplets
- DigitalOcean regional availability: https://docs.digitalocean.com/platform/regional-availability/
- Cloud Firewall rules: https://docs.digitalocean.com/products/networking/firewalls/how-to/configure-rules/
- Cloudflare Turnstile server-side validation: https://developers.cloudflare.com/turnstile/get-started/server-side-validation/

## Update deployment

From the Droplet after syncing a reviewed commit:

    cd /opt/kirindl
    git pull --ff-only
    cd deploy/digitalocean
    sudo ./deploy.sh

For a deployment rollback, check out the previous reviewed commit and run `sudo ./deploy.sh` again. SQLite and downloads remain under the data directory.
