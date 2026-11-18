# KirinDL Web — Progress 1–9

Last recorded: 2026-11-18
Repository: Lanzkila/KirinDLWeb
Android repository: Lanzkila/KirinDL

This is the working project memory for the nine development stages. Update the status and notes here whenever a stage changes. Do not treat a planned item as implemented merely because its folder or placeholder file exists.

## Project decisions to preserve

1. Separate repositories: the website is developed in KirinDLWeb. The existing Android repository remains the source of the native app and its download engines.
2. No unnecessary Android changes: do not refactor, move, or rebuild the Android app for web work. Add only a small, reviewed bridge integration when it becomes necessary and after the protocol is agreed.
3. Web-first design: the migrated Sites Pages design is temporary. Keep it until the new web-specific preview is reviewed; the eventual downloader website may have its own navigation, layout, and visual identity and does not need to copy the Android app UI.
4. PipePipe-inspired modularity: use separate repositories and Git submodules for stable, independently maintained modules when they genuinely exist. Git submodules organize source code; they are not the runtime App–Web communication mechanism.
5. Capability boundary: GitHub Pages hosts the static frontend only. It cannot run a persistent yt-dlp process or a long-lived downloader backend.

## Progress 1–9

### 1. Migrate the existing KirinDL Sites Pages into KirinDLWeb

Status: COMPLETE

- Copied the existing homepage design from the Android repository's Sites Pages into the new web repository.
- Migrated 404.html and the Contact, Issues, Privacy, and Support pages.
- Migrated the original Pages assets.
- Added website configuration, robots.txt, and sitemap.
- Kept the old public page paths working through the static build.
- The original Lanzkila/KirinDL repository was not modified.

Commit: 42672a0fbd62b43fdab86e2b63e9a794d813d152 — feat: migrate existing KirinDL Pages website.

### 2. Establish the independent web application foundation

Status: PARTIAL / SCAFFOLD + PART 1 UI PREVIEW

- Added the starter browser application under src/.
- Added a basic router and placeholder pages for Home, Downloader, History, Tools, and Settings.
- Added responsive starter styles, local development server and static build.
- Added a separate web-specific Part 1 preview at preview.html, with styles and interactions under public/.
- The preview is a separate web design. The original production homepage remains unchanged until visual review is accepted.
- The hamburger menu no longer contains the Resume/Remember Last Page card.
- The production homepage and Android repository are unchanged.

### 3. Build the real web downloader workflow

Status: PARTIAL — TASK API AND DOWNLOAD FLOW IMPLEMENTED; PUBLIC BACKEND NOT DEPLOYED

Target workflow:
- Accept and validate a media URL.
- Fetch media metadata and thumbnails.
- Display available formats, resolution, audio, subtitles and supported choices.
- Let the user configure and submit a task.
- Show useful errors and unsupported-site messages.

The frontend submits real tasks to the backend when apiBase is configured, polls task progress, and exposes the completed output file. The hosted preview has no public backend configured yet, so live download execution is not available from GitHub Pages.

### 4. Implement browser/web extraction and processing adapters

Status: PARTIAL — SERVER-SIDE yt-dlp AND gallery-dl ADAPTERS IMPLEMENTED

- yt-dlp handles supported video/audio sources and reports progress using hooks.
- gallery-dl handles supported image galleries and counts downloaded items.
- FFmpeg is installed in the backend Docker image for compatible audio/video merging.
- Auto mode tries yt-dlp and falls back to gallery-dl if the first engine cannot process the URL.
- Live source-site testing remains pending until a backend host is deployed.

### 5. Add task queue, progress, history, and settings persistence

Status: PARTIAL — SQLITE TASK RECORDS AND RETENTION CLEANUP IMPLEMENTED

- Task status and progress snapshots are persisted in SQLite under KIRINDL_DATA_DIR.
- Completed output paths remain available across a process restart when persistent storage is mounted.
- A task interrupted by a restart is recovered as failed, with a clear resubmission message; live extractor sessions are not resumed.
- A background cleanup thread removes expired task records and output directories.
- The worker pool is still in-process and single-instance; this is not yet a distributed queue, web history UI or settings sync.

### 6. Define and deploy a secure backend where required

Status: PARTIAL — API, CONTAINER, PERSISTENCE AND TESTS IMPLEMENTED; PUBLIC DEPLOYMENT PENDING

- FastAPI routes cover health, task creation, status, cancellation and file download.
- yt-dlp and gallery-dl adapters are implemented.
- Docker installs FFmpeg, runs as a non-root user, and includes a health check.
- SQLite task persistence, task retention cleanup, bounded worker concurrency, timeout and output-size controls are implemented.
- URL validation rejects credentials, private/local/reserved DNS answers and non-standard ports.
- CORS and task-creation rate limits are configured.
- No public backend host has been selected or deployed.
- Outbound network egress controls are still required before public exposure because extractors can follow redirects and contact secondary hosts.
- No user account/authentication or per-user task ownership is implemented. A static shared API token must not be placed in the frontend.

### 7. Implement the KirinDL App–Web bridge

Status: SPECIFICATION STARTED; RUNTIME INTEGRATION NOT IMPLEMENTED

- A versioned message-envelope draft exists in src/core/protocol/bridge.js.
- Protocol documentation is in docs/bridge/protocol.md.
- Planned messages include app navigation, download handoff, task status, and capability negotiation.
- Choose and verify an appropriate transport for each direction.
- Do not expose a broad JavaScript interface to arbitrary website origins.
- Confirm package identity, signing fingerprints, domain ownership and URL routes before adding Android App Links.
- Only make minimum bridge-specific Android changes after review.

Existing Android URL receiving is not a verified KirinDLWeb bridge. The new protocol is not connected to the app.

### 8. Split stable components into PipePipe-style modules

Status: PLANNED; NO SUBMODULES YET

- Keep components here while interfaces are changing.
- Extract a component only when it has a stable responsibility, public contract, tests, ownership and clear license.
- Add Git submodules only after their repositories exist.
- Pin reviewed submodule commits and document updates.

There is no .gitmodules file and no submodule is connected.

### 9. Testing, security review, and production deployment

Status: BACKEND AUTOMATED TESTS EXPANDED; PUBLIC DEPLOYMENT AND LIVE ENGINE TESTS PENDING

- GitHub Actions CI runs frontend checks/build and Python backend tests.
- Backend tests cover health, API request validation, unsafe URL rejection, persistence across manager restarts, interrupted task recovery, retention cleanup, output path isolation and active task limits.
- Real source-site downloads, FFmpeg merges and gallery ZIP output must be tested after a host is configured.
- Before public exposure, configure persistent storage, outbound network egress rules, CORS origins and abuse controls.
- GitHub Pages deploys only the static frontend; it does not run the downloader engine.

## Current next step

Finish backend deployment preparation and choose a server/container host. Do not proceed to metadata/format inspection or further downloader UI stages until the backend CI passes and a backend instance can be health-checked. After deployment, run real source-site tests for yt-dlp, FFmpeg merging, gallery-dl ZIP output, progress, cancellation and file retention.

Preview source: preview.html
Raw.githack development URL: https://raw.githack.com/Lanzkila/KirinDLWeb/main/preview.html

## Update instructions

1. Read this file before continuing development.
2. Update status only after code or tests confirm the change.
3. Record commit IDs and CI/deployment results.
4. Keep incomplete work clearly marked partial or not started.
5. Preserve repository separation and the decisions above.

### Backend hardening follow-up

- Added SQLite persistence for task records and progress snapshots under KIRINDL_DATA_DIR.
- Completed output paths survive process restarts when the configured volume is persistent.
- Interrupted active tasks are recovered as failed, not falsely shown as running or silently resumed.
- Added periodic background cleanup for expired task records and output directories.
- Improved queued-task cancellation and child-process termination/reaping for gallery-dl.
- Added storage-path validation and excludes internal process/future/path details from API responses.
- Added backend tests for restart recovery, task retention, output path isolation, queue limits and API request validation.
- Docker image includes a health check, one-worker startup and non-root execution.
- Backend remains single-instance; public deployment and live extractor tests are still pending.


### Production security and deployment follow-up

- The DigitalOcean starter deployment uses a private Docker bridge with a fixed API address and Caddy as the only published HTTP(S) service.
- A host-side Docker egress guard blocks API-container connections to host services, private/loopback/link-local/reserved destinations, the rest of the private Compose subnet and other container addresses. Only established replies from API port 8000 back to the Caddy container are allowed.
- The Cloud Firewall also blocks IPv4 private/shared/local/link-local/reserved ranges and IPv6 local, unique-local, NAT64, 6to4 and special-purpose ranges before permitting DNS/NTP/HTTP/HTTPS egress.
- The Turnstile hostname allowlist excludes shared preview hosts. Use the account's GitHub Pages hostname or a custom domain under the owner's control; do not trust raw.githack.com as a production challenge hostname.
- Backend storage checks preserve headroom for the output cap, ZIP packaging and a separate free-space reserve.
- CI now checks Python and shell syntax, Docker Compose configuration, backend tests, Docker image build and a read-only container health check.
- Deployment scripts are prepared but not executed against a cloud account. The public backend URL, Droplet ID, operator SSH IP, DNS domain and Turnstile keys are still unconfigured.
