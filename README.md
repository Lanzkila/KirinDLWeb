# KirinDL Web

The independent web platform for KirinDL.

This repository is separate from the Android application repository. The existing KirinDL Sites Pages design remains the temporary production homepage while the web-specific downloader interface is reviewed.

## Project status

Existing information pages migrated; Part 1 web interface preview created; downloader and bridge are not connected yet.

The migrated Contact, Issues, Privacy and Support pages remain available. The new Part 1 layout is in preview.html, with styles and interactions under public/.

- Part 1 source preview: preview.html
- Raw.githack development preview: https://raw.githack.com/Lanzkila/KirinDLWeb/main/preview.html
- Web redesign plan: docs/roadmap/web-redesign-plan.txt
- Verified progress 1–9 roadmap: docs/roadmap/progress-1-9.md

The preview includes a hamburger menu with Remember Last Page, centered Login/Register dialog with Material 3 SVG icons, a glowing URL input and engine selector. Home initially shows only the input card. Submitting a valid link triggers a simulated Video/Audio 0–100% sequence, Processing and Merging, then temporarily hands the source URL to a Downloads result card before returning to the input-only view. This is UI simulation only; no media extraction, real download, authentication or Android bridge is connected yet.

## Repository layout

    KirinDLWeb/
    ├── .github/workflows/       CI and GitHub Pages deployment
    ├── docs/                    Architecture, bridge and development notes
    ├── engine/                  Web engine contracts and future adapters
    ├── modules/                 Reserved for future Git submodules
    ├── pages/                   Migrated information pages
    ├── pages-assets/            Migrated site assets
    ├── preview.html             Part 1 web-specific UI preview
    ├── public/                  Web platform public assets
    ├── scripts/                 Development server and static build
    ├── server/                  Future backend service boundary
    ├── src/                     Browser workspace scaffold
    └── tests/                   Unit tests

## Local development

Requirements: Node.js 22 or newer.

    npm run dev

Open the local URL printed by the server. The Part 1 preview is available at /preview.html.

Run checks and create the static site build:

    npm test
    npm run build

The deployable site is written to dist/.

## Modular repository approach

The project follows the separation principle used by projects such as PipePipe: stable components may later become independently maintained repositories and be connected as Git submodules.

No submodule is declared yet because the target module repositories and their stable URLs have not been created. See docs/architecture/modules.md.

## App–Web integration

The bridge protocol is still a specification, not a live connection. The Android source and native download engines remain in Lanzkila/KirinDL. Any Android changes will be limited to a separately reviewed bridge integration.

See docs/bridge/protocol.md.

## Platform boundaries

- GitHub Pages hosts this static website; it does not run a long-lived downloader backend.
- Browser code cannot execute the Android Kotlin engine or access Android private storage.
- Browser-compatible features will run in the browser; tasks needing server resources require a separately deployed and secured backend or handoff to the Android app.
- Do not place API secrets, extractor cookies, signing keys or privileged credentials in the web frontend.
- Login/Register in the Part 1 preview is a visual prototype. Do not use real credentials.

## Website migration

The informational Pages were migrated from the existing KirinDL repository. The Android source repository was left unchanged. The current published homepage is temporary and will only be replaced after the new web-specific preview is reviewed.
