# KirinDL Web — Progress 1–9

Last recorded: 2026-11-18  
Repository: [Lanzkila/KirinDLWeb](https://github.com/Lanzkila/KirinDLWeb)  
Android repository: [Lanzkila/KirinDL](https://github.com/Lanzkila/KirinDL)

This is the working project memory for the nine development stages. Update the status and notes here whenever a stage changes. Do not treat a planned item as implemented merely because its folder or placeholder file exists.

## Project decisions to preserve

1. **Separate repositories:** the website is developed in `KirinDLWeb`. The existing Android repository remains the source of the native app and its download engines.
2. **No unnecessary Android changes:** do not refactor, move, or rebuild the Android app for web work. Add only a small, reviewed bridge integration when it becomes necessary and after the protocol is agreed.
3. **Web-first design direction:** the migrated Sites Pages design is temporary. Keep it for now, but the eventual downloader website may have its own navigation, layout, and visual identity; it does not need to copy the Android app UI.
4. **PipePipe-inspired modularity:** use separate repositories and Git submodules for stable, independently maintained modules when they genuinely exist. Git submodules organize source code; they are not the runtime App–Web communication mechanism.
5. **Be precise about capability:** GitHub Pages hosts the static frontend only. It cannot run a persistent yt-dlp process or a long-lived downloader backend.

## Progress 1–9

### 1. Migrate the existing KirinDL Sites Pages into KirinDLWeb

**Status: COMPLETE**

- Copied the existing homepage design from the Android repository's Sites Pages into the new web repository.
- Migrated `404.html`, `pages/contact.html`, `pages/issues.html`, `pages/privacy.html`, and `pages/support.html`.
- Migrated `pages-assets/main.js`, `pages-assets/style.css`, and the original `pages-assets/favicon.png`.
- Added the website configuration, `robots.txt`, and a sitemap for the new `KirinDLWeb` Pages URL.
- Kept the old public page paths working by making the build publish the four information pages at the site root while retaining their source files under `pages/`.
- Adjusted the homepage copy and primary call to action for the web platform while keeping the existing visual design for now.
- Updated the build and local development server to include the migrated pages and static assets.
- The original `Lanzkila/KirinDL` repository was not modified by this migration.

Commit: `42672a0fbd62b43fdab86e2b63e9a794d813d152` — `feat: migrate existing KirinDL Pages website`.

### 2. Establish the independent web application foundation

**Status: PARTIAL / SCAFFOLD EXISTS**

- Added a starter browser application under `src/`.
- Added a basic router and placeholder pages for Home, Downloader, History, Tools, and Settings.
- Added responsive starter styles and a basic local development server/build script.
- The starter app under `src/` is **not yet the migrated Sites Pages homepage**. The existing migrated static site remains the published presentation for now.
- Do not replace the temporary migrated homepage with the starter shell until the user is ready to redesign the website.

Remaining: decide the intended production frontend architecture and gradually replace or reuse the starter shell when the web-specific redesign begins.

### 3. Build the real web downloader workflow

**Status: NOT STARTED**

Target workflow:

- Accept and validate a media URL.
- Fetch media metadata and thumbnails.
- Display available formats, resolution, audio, subtitles, and other supported choices.
- Let the user configure a task and submit it.
- Show useful errors and unsupported-site messages.

The current Downloader page is only a disabled placeholder. It does not fetch media information or download anything.

### 4. Implement browser/web extraction and processing adapters

**Status: NOT STARTED**

- Define a web-compatible extractor/metadata adapter boundary under `engine/`.
- Determine which tasks can run in the browser and which need a backend.
- Do not assume the Android Kotlin engine, Android storage integrations, or packaged native binaries can run inside a normal browser.
- Check the licensing and runtime compatibility of any reused extractor code before importing it.

The current `engine/` files are documentation placeholders only; no extractor or media processor is implemented.

### 5. Add task queue, progress, history, and settings persistence

**Status: NOT STARTED**

Planned capabilities:

- Web task queue and progress.
- Pause/cancel/retry where the selected execution backend supports them.
- Web download history.
- Web-specific preferences and defaults.
- Optional App–Web history/settings synchronization only after an explicit shared-data contract and secure storage design exist.

The current History and Settings pages are placeholders. No task database or cross-platform synchronization exists.

### 6. Define and deploy a secure backend where required

**Status: NOT STARTED**

- Decide whether web extraction requires server-side execution for selected sites or formats.
- Define authenticated APIs, queue/job isolation, timeouts, rate limits, resource limits, storage cleanup, and abuse controls.
- Keep secrets, cookies, signing keys, and privileged credentials out of the browser and GitHub Pages.
- Choose and deploy a server-capable host separately from the static GitHub Pages frontend.

The `server/` directory currently documents the boundary only. No backend, worker, or downloader API is deployed.

### 7. Implement the KirinDL App–Web bridge

**Status: SPECIFICATION STARTED; RUNTIME INTEGRATION NOT IMPLEMENTED**

- A versioned message-envelope draft exists in `src/core/protocol/bridge.js`.
- The draft documentation is in `docs/bridge/protocol.md`.
- Planned messages include app navigation, download request handoff, task status, and capability negotiation.
- Choose the correct transport for each direction. Verified Android App Links/deep links can hand a user action from the website to the installed app. A server API or explicit authenticated transport is needed for shared remote data.
- Do not expose a broad JavaScript interface to arbitrary website origins.
- Confirm Android package identity, signing certificate fingerprints, domain ownership, and supported URL routes before writing `assetlinks.json` or Android intent filters.
- Only make the minimum bridge-specific changes in the Android repository after the design is reviewed.

Important: the existing Android app already accepts shared HTTP/HTTPS URLs in its download activities, but that alone is not a verified KirinDLWeb bridge. The new protocol is not connected to the app yet.

### 8. Split stable components into PipePipe-style modules

**Status: PLANNED; NO SUBMODULES YET**

- Keep components in this repository while their interfaces are changing.
- Extract a component into its own repository only when it has a stable responsibility, public contract, tests, ownership, and a clear license.
- Add real Git submodules under `modules/` only after their repositories exist.
- Pin reviewed submodule commits and document the update procedure.

The `modules/README.md` describes this approach. There is no `.gitmodules` file and no submodule is currently connected.

Remember: PipePipe's Git submodules are a source-code organization pattern, not the live communication bridge between the Android app and website.

### 9. Testing, security review, and production deployment

**Status: INITIAL CI/PAGES PIPELINE PASSED; PRODUCT VALIDATION REMAINS**

Already present:

- GitHub Actions CI workflow runs the current unit test and static build.
- GitHub Pages deployment workflow is configured.
- The scaffold CI and migrated-site CI runs completed successfully.
- The migrated-site Pages deployment completed successfully.

Still required:

- Browser checks for homepage, 404, Contact, Issues, Privacy, and Support pages.
- Check all asset paths, navigation links, mobile layout, cache behavior, and external GitHub API errors.
- Add meaningful unit/integration/e2e coverage for downloader and bridge behavior as those features are implemented.
- Security review for URL validation, backend job isolation, authentication, file handling, and bridge origins.
- Re-test the full production deployment after each important feature is added.

A successful static build or Pages deployment does not mean the downloader, backend, or App–Web bridge is operational.

## Current next step

Keep the migrated Sites Pages design as the temporary published website. Before starting the downloader implementation, review the migrated pages in a browser and correct any migration regressions. Then proceed to the web-specific downloader UI when the user is ready.

## Update instructions for future work

Whenever development continues:

1. Read this file first.
2. Update the relevant progress number and status after actual code or tests confirm the change.
3. Record commit IDs and CI/deployment results when available.
4. Keep incomplete work clearly marked as partial or not started.
5. Preserve the repository separation and design decisions above.
