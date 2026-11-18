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
- Preview includes hamburger navigation, Remember Last Page, Material 3 SVG Login/Register icons, a glowing URL input and engine selector.
- Home initially shows only the URL input card. The process panel appears only after a valid URL is submitted, simulates Video/Audio progress and Processing/Merging, then hands the submitted URL to a temporary Downloads result card before returning to the clean input screen.
- The hamburger popover and Login/Register dialog are centered across desktop and mobile layouts.
- All progress values and result handoff are UI simulation only. It does not fetch metadata, extract media, download files, authenticate accounts or connect to Android.
- Migrated Sites Pages production homepage is intentionally retained until the user reviews the preview.

### 3. Build the real web downloader workflow

Status: PARTIAL — TASK API AND DOWNLOAD FLOW IMPLEMENTED; PUBLIC BACKEND NOT DEPLOYED

Target workflow:
- Accept and validate a media URL.
- Fetch media metadata and thumbnails.
- Display available formats, resolution, audio, subtitles and supported choices.
- Let the user configure and submit a task.
- Show useful errors and unsupported-site messages.

The frontend now submits real tasks to the backend when apiBase is configured, polls task progress, and exposes the completed output file. The hosted preview has no public backend configured yet, so live download execution is not available from GitHub Pages at this stage.

### 4. Implement browser/web extraction and processing adapters

Status: PARTIAL — SERVER-SIDE yt-dlp AND gallery-dl ADAPTERS IMPLEMENTED

- Define a web-compatible extractor/metadata adapter boundary under engine/.
- Determine which tasks can run in the browser and which need a backend.
- Do not assume Android Kotlin engine, Android storage integrations or packaged native binaries can run in a normal browser.
- Check licensing and runtime compatibility before importing extractor code.

The backend adapters live in server/kirindl_server/jobs.py. yt-dlp handles supported video/audio sources and progress hooks; gallery-dl handles supported galleries and file counting. FFmpeg is installed in the backend Docker image for merging. Live source-site testing is still required after deployment.

### 5. Add task queue, progress, history, and settings persistence

Status: NOT STARTED

Planned capabilities:
- Web task queue and progress.
- Pause/cancel/retry where the execution backend supports them.
- Web download history and web-specific preferences.
- Optional App–Web history/settings sync only after a shared-data contract and secure storage design exist.

The Part 1 preview now demonstrates a temporary progress panel and a temporary Downloads URL handoff, but both are simulated. No real task queue, history, media output, or cross-platform sync exists.

### 6. Define and deploy a secure backend where required

Status: PARTIAL — API AND CONTAINER IMPLEMENTED; NOT PUBLICLY DEPLOYED

- Decide whether web extraction requires server-side execution.
- Define authenticated APIs, queue/job isolation, timeouts, rate limits, resource limits, cleanup and abuse controls.
- Keep secrets, cookies, signing keys and privileged credentials out of the browser and GitHub Pages.
- Choose a server-capable host separately from the static frontend.

The FastAPI service, task API, in-memory task manager, Dockerfile, CORS controls, per-client task rate limit, URL/IP validation, task timeout, output size limit and cancellation endpoint are implemented under server/. No public backend host has been configured or deployed. Task state is in-memory and the service is intended for one Uvicorn worker/replica until a durable queue is added. Login/Register remains UI-only.

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

Status: PART 1 CI AND PAGES DEPLOYMENT PASSED; VISUAL REVIEW PENDING

Already present:
- GitHub Actions CI runs JavaScript checks, frontend unit tests, static build and Python backend tests.
- GitHub Pages deployment workflow is configured.
- Previous scaffold/migration CI and Pages deployment runs succeeded.

Part 1 validation still required:
- Confirm build copies preview.html and its assets.
- Review the preview in a real browser on desktop and mobile.
- Check hamburger, Remember Last Page, Login/Register modal/tabs, URL validation, clipboard permission, reduced-motion and keyboard accessibility.
- Check Raw.githack preview and cache.
- Keep production homepage unchanged until visual review is accepted.

Later testing:
- Add meaningful unit/integration/e2e coverage for downloader and bridge behavior.
- Review URL validation, backend isolation, authentication, file handling and bridge origins.
- Re-test production deployment after important changes.

A successful static build or Pages deployment does not mean downloader, backend, or App–Web bridge is operational.

## Current next step

Open the updated Part 1 preview and review the centered menus, Material 3 SVG account icons, clean input-only home, simulated progress sequence and temporary Downloads handoff. Apply visual corrections based on user feedback before promoting the new design to the production homepage.

Preview source: preview.html
Raw.githack development URL: https://raw.githack.com/Lanzkila/KirinDLWeb/main/preview.html
Part 1 implementation commit: 233d629cc078823f76c0aabd3e2f3d0106b1a84a

## Update instructions

1. Read this file before continuing development.
2. Update status only after code or tests confirm the change.
3. Record commit IDs and CI/deployment results.
4. Keep incomplete work clearly marked partial or not started.
5. Preserve repository separation and the decisions above.


### Part 1 follow-up — centered account menus and temporary task flow

- Updated the preview so Home initially shows only the URL input card.
- Centered the hamburger popover and Login/Register dialog on both phone and laptop viewports.
- Replaced account glyphs with Material 3 style inline SVG icons for the account action, Login and Register tabs.
- Added a front-end demonstration flow: valid URL submission shows Video/Audio percentages, then Processing and Merging; the progress panel is replaced by a temporary Downloads handoff card containing the submitted URL; the UI then resets to the input-only view.
- These are simulated UI states only; a live downloader, file output, extraction API and authentication service are not implemented.


### Part 1 follow-up — SVG navigation, restored footer and component folders

- Split preview UI into dedicated directories under public/components/: hamburger, login-register, footer and downloader.
- Each interactive component has its own JavaScript file; component-specific CSS is stored beside it.
- Replaced navigation arrows in hamburger menus with inline SVG paths; chevrons rotate around their own center.
- Restored the footer for both desktop and mobile layouts.
- On phones, hamburger and account buttons show icons only; accessible aria-labels retain their meaning.
- The production homepage and Android repository remain unchanged.


### Part 1 follow-up — bottom footer, URL icons and live engine connection

- Footer layout now uses a full-height flex column so it is pushed to the viewport bottom on desktop and mobile without fixed positioning.
- Removed the Remember Last Page / Resume card from the hamburger menu.
- Replaced the URL leading arrow, engine dropdown chevron and submit arrow with aligned SVG icons.
- Removed the simulated progress sequence. The browser now calls POST /api/v1/tasks, polls GET /api/v1/tasks/{id}, can request DELETE cancellation, and displays the real output-file endpoint returned by the server.
- Added a gallery-dl item-count state; yt-dlp uses the backend stream and postprocessor progress hooks.
- Added a local API config file. Localhost previews target http://127.0.0.1:8000; hosted previews remain disconnected until a backend HTTPS URL is set.
- Implemented FastAPI service, yt-dlp and gallery-dl adapters, task manager, Dockerfile, dependencies, API tests and URL safety tests.
- CI now runs Python backend tests. The backend has not yet been deployed publicly, and real downloads still need host-specific live validation.


### Engine verification notes

- Frontend no longer animates synthetic progress. It submits tasks to the configured backend and polls server-reported state.
- Backend Python tests passed in GitHub Actions: URL safety cases and the API health endpoint.
- GitHub Pages build/deployment passed for the engine commit.
- No public backend has been deployed, so actual site extraction, FFmpeg merging and downloaded output have not yet been tested against live source URLs.
- Detailed metadata/format analysis, durable queue/database, user accounts and backend deployment remain outstanding.
