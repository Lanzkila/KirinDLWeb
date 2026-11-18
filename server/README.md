# KirinDL Web Engine API

This is the server-side execution engine for the independent KirinDL Web frontend. It is separate from the Android Kotlin engine and is not hosted by GitHub Pages.

## Engines

- **yt-dlp** handles supported video/audio URLs, selects available video/audio streams, uses FFmpeg for compatible merging, and reports progress through yt-dlp progress and postprocessor hooks.
- **gallery-dl** handles supported image galleries and collections. Completed files are bundled into a ZIP when the extractor returns multiple files.
- **auto** tries yt-dlp first, then falls back to gallery-dl if yt-dlp cannot handle the submitted URL.

Official references:
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- gallery-dl: https://gdl-org.github.io/docs/

## API routes

- GET /api/v1/health — service health.
- POST /api/v1/tasks — create a download task. JSON body: {"url":"https://…","engine":"auto|yt-dlp|gallery-dl"}. Returns HTTP 202 and a task id.
- GET /api/v1/tasks/{id} — read task status and progress.
- DELETE /api/v1/tasks/{id} — request task cancellation.
- GET /api/v1/tasks/{id}/download — retrieve the completed file or ZIP archive.

Task states: queued, downloading, processing, merging, completed, failed, cancelled. Progress contains video/audio percentages and gallery item counts where available.

## Run locally without hosting

No cloud account or public server is needed for local testing. The website and downloader backend run as two local services on the same computer.

Requirements: Node.js 22 or newer, plus either Docker or Python 3.12. Docker is recommended because the image already includes FFmpeg.

### 1. Start the backend

From the repository root, using Docker:

    docker build -f server/Dockerfile -t kirindl-web-engine .
    docker run --rm -p 8000:8000 -v kirindl-downloads:/data -e KIRINDL_DATA_DIR=/data kirindl-web-engine

Or run it directly with Python:

    python -m venv .venv
    . .venv/bin/activate
    pip install -r server/requirements-dev.txt
    KIRINDL_DATA_DIR=./.downloads uvicorn kirindl_server.main:app --app-dir server --reload

For the Python option, install the FFmpeg executable separately and make sure it is available on PATH if you want video/audio merging.

Check the backend at http://127.0.0.1:8000/api/v1/health. Interactive API documentation is at http://127.0.0.1:8000/docs.

### 2. Start the website

Open a second terminal at the repository root and run:

    npm run dev

Open http://127.0.0.1:4173/preview.html. The local frontend configuration automatically points to http://127.0.0.1:8000, and the backend's default CORS allowlist includes this local development origin. No apiBase edit or hosting setup is needed.

Turnstile is disabled for local development unless KIRINDL_REQUIRE_TURNSTILE=true and a valid sitekey/secret pair is configured.

The local website server binds to loopback, so it is intended for testing on the same computer, not for public access. Real downloads still depend on the source site being supported and reachable from that computer.

## Configure the website

- Local preview needs no configuration change: public/kirindl-config.js selects http://127.0.0.1:8000 automatically when the page is opened from localhost or 127.0.0.1.
- For a public website, set apiBase to the HTTPS base URL of the deployed backend, with no trailing slash.
- The public config may contain the Cloudflare Turnstile sitekey, but never the Turnstile secret or KIRINDL_API_TOKEN.

GitHub Pages and other static hosts cannot run yt-dlp, gallery-dl or FFmpeg. Public live downloading therefore requires a separately deployed backend; this is intentionally outside the local-development steps above.

## Persistence and worker model

- SQLite task records are stored at KIRINDL_DATA_DIR/tasks.sqlite3.
- Download files and task directories are stored under the same persistent data volume.
- Completed tasks and their download paths survive a process restart when the volume is retained.
- A task interrupted by a server restart is restored as failed with a clear retry message. Extractor processes are not resumed.
- Retention cleanup runs periodically (default: every 300 seconds) and removes expired task rows and their output directories (default retention: 24 hours).
- The worker pool is bounded (default: 2 workers) and the active-task cap defaults to 3.
- A free-space guard runs before accepting a task and during extractor progress. It preserves enough headroom for the output cap, temporary archive packaging and the configured reserve.
- SQLite persistence does not make the worker pool distributed. Run exactly one Uvicorn worker and one backend replica. Add a distributed queue/worker service before horizontal scaling.

## Security and operating limits

- Only HTTP and HTTPS source URLs are accepted. URLs with credentials, local/private/reserved DNS answers and non-standard ports are rejected.
- CORS is restricted to configured frontend origins.
- Task creation is rate-limited per client; concurrent tasks, runtime, output size and minimum free disk space are capped.
- Optional KIRINDL_API_TOKEN support is intended for private deployments or a trusted gateway. Do not ship a static shared token to a public browser.
- Cloudflare Turnstile can be enabled with KIRINDL_REQUIRE_TURNSTILE=true and a server-side KIRINDL_TURNSTILE_SECRET. Every task-creation token is checked with Siteverify and the expected hostname and action. The browser sitekey is public; the secret must stay on the server.
- DNS checks are a first-line SSRF guard only. Before public exposure, enforce outbound network egress rules at the hosting/network layer to block loopback, private, link-local and metadata-service destinations after redirects and secondary extractor requests as well.
- The public API has no per-user account system or task ownership yet. Deploy behind abuse controls; do not expose untrusted traffic until egress and rate limits are validated.
- Use persistent storage; ephemeral container storage loses task history and output files when the host replaces the container.
- Respect source-site terms and copyright rules. Only download media you are authorised to access.

## Current status

The backend code, persistent task manager, Turnstile verifier, storage guard and automated tests are implemented. The DigitalOcean deployment files are prepared, but no public backend instance has been provisioned or deployed. Live source-site downloads, FFmpeg merging and gallery ZIP output still require a real hosted instance and source validation.

See [DigitalOcean deployment](../deploy/digitalocean/README.md).
