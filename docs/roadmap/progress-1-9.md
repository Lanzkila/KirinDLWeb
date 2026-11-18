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
- Preview includes hamburger navigation, Remember Last Page, Login/Register UI, glowing URL input, engine selector, progress layout and Downloads panel.
- Preview validates URL syntax and demonstrates interface interactions only. It does not fetch metadata, extract media, download files, authenticate accounts or connect to Android.
- Migrated Sites Pages production homepage is intentionally retained until the user reviews the preview.

### 3. Build the real web downloader workflow

Status: NOT STARTED

Target workflow:
- Accept and validate a media URL.
- Fetch media metadata and thumbnails.
- Display available formats, resolution, audio, subtitles and supported choices.
- Let the user configure and submit a task.
- Show useful errors and unsupported-site messages.

The Part 1 preview includes an enabled URL field and basic http/https syntax validation only. It does not fetch media information or download anything.

### 4. Implement browser/web extraction and processing adapters

Status: NOT STARTED

- Define a web-compatible extractor/metadata adapter boundary under engine/.
- Determine which tasks can run in the browser and which need a backend.
- Do not assume Android Kotlin engine, Android storage integrations or packaged native binaries can run in a normal browser.
- Check licensing and runtime compatibility before importing extractor code.

The engine files are documentation placeholders only; no extractor or processor is implemented.

### 5. Add task queue, progress, history, and settings persistence

Status: NOT STARTED

Planned capabilities:
- Web task queue and progress.
- Pause/cancel/retry where the execution backend supports them.
- Web download history and web-specific preferences.
- Optional App–Web history/settings sync only after a shared-data contract and secure storage design exist.

The Part 1 UI shows idle placeholders (Video 0%, Audio 0%, Processing Waiting, Merging Waiting) and an empty Downloads panel. No task queue, history, or cross-platform sync exists.

### 6. Define and deploy a secure backend where required

Status: NOT STARTED

- Decide whether web extraction requires server-side execution.
- Define authenticated APIs, queue/job isolation, timeouts, rate limits, resource limits, cleanup and abuse controls.
- Keep secrets, cookies, signing keys and privileged credentials out of the browser and GitHub Pages.
- Choose a server-capable host separately from the static frontend.

The server directory documents the boundary only. No backend, worker, or downloader API is deployed. Login/Register is a UI preview only; it does not transmit or save credentials.

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

Status: INITIAL CI/PAGES PIPELINE PASSED; PART 1 BUILD VALIDATION PENDING

Already present:
- GitHub Actions CI runs the current unit tests and static build.
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

Open the Part 1 preview and review the header, navigation, input form, progress panel, and Downloads placement. Apply visual corrections based on user feedback before promoting the new design to the production homepage.

Preview source: preview.html
Raw.githack development URL: https://raw.githack.com/Lanzkila/KirinDLWeb/main/preview.html

## Update instructions

1. Read this file before continuing development.
2. Update status only after code or tests confirm the change.
3. Record commit IDs and CI/deployment results.
4. Keep incomplete work clearly marked partial or not started.
5. Preserve repository separation and the decisions above.
