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

## Run locally

Requirements: Docker with network access.

From the repository root:

    docker build -f server/Dockerfile -t kirindl-web-engine .
    docker run --rm -p 8000:8000 -v kirindl-downloads:/data --env-file server/.env.example kirindl-web-engine

Open http://localhost:8000/api/v1/health. Interactive API documentation is at /docs.

For development without Docker:

    python -m venv .venv
    . .venv/bin/activate
    pip install -r server/requirements-dev.txt
    KIRINDL_DATA_DIR=./.downloads uvicorn kirindl_server.main:app --app-dir server --reload

## Configure the website

Edit public/kirindl-config.js and set apiBase to the HTTPS base URL of the deployed backend, with no trailing slash. For a local backend, http://127.0.0.1:8000 is used automatically when the site is opened from localhost. Never place KIRINDL_API_TOKEN or any server secret in the public frontend.

The backend must be deployed to a server/container host that supports Python, FFmpeg, a persistent writable volume and outbound HTTPS. The GitHub Pages frontend cannot run yt-dlp, gallery-dl or FFmpeg.

## Persistence and worker model

- SQLite task records are stored at KIRINDL_DATA_DIR/tasks.sqlite3.
- Download files and task directories are stored under the same persistent data volume.
- Completed tasks and their download paths survive a process restart when the volume is retained.
- A task interrupted by a server restart is restored as failed with a clear retry message. Extractor processes are not resumed.
- Retention cleanup runs periodically (default: every 300 seconds) and removes expired task rows and their output directories (default retention: 24 hours).
- The worker pool is bounded (default: 2 workers) and the active-task cap defaults to 3.
- SQLite persistence does not make the worker pool distributed. Run exactly one Uvicorn worker and one backend replica. Add a distributed queue/worker service before horizontal scaling.

## Security and operating limits

- Only HTTP and HTTPS source URLs are accepted. URLs with credentials, local/private/reserved IP targets, and non-standard ports are rejected.
- CORS is restricted to configured frontend origins.
- Task creation is rate-limited per client; concurrent tasks, runtime and download size are capped.
- Optional KIRINDL_API_TOKEN support is intended for private deployments or a trusted gateway. Do not ship a static shared token to a public browser.
- DNS checks are a first-line SSRF guard only. Before public exposure, enforce outbound network egress rules at the hosting/network layer to block loopback, private, link-local and metadata-service destinations after redirects and secondary extractor requests as well. Do not treat DNS validation alone as complete SSRF protection.
- The public API has no per-user account system or task ownership yet. Deploy behind appropriate abuse controls and do not enable untrusted public traffic until egress and rate-limit behavior have been validated for the host.
- Use persistent storage; ephemeral container storage will lose completed output files and task history when the host replaces the container.
- Respect source-site terms and copyright rules. Only download media you are authorised to access.

## Current status

The backend code and automated tests are implemented, including SQLite task persistence and retention cleanup. No public backend instance has been deployed because no hosting target has been configured. Live source-site downloads, FFmpeg merging and gallery ZIP output still require host deployment and real-source validation.
