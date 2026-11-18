# KirinDL Web

The independent web platform for [KirinDL](https://github.com/Lanzkila/KirinDL).

This repository is intentionally separate from the Android application repository. The existing KirinDL Sites Pages design has been copied here as a temporary web presentation so it can continue to work independently while the browser downloader is developed.

## Project status

**Website pages migrated; downloader and bridge are not connected yet.**

The current homepage and informational pages retain the existing KirinDL Pages design. The page source is kept under `pages/`, shared visual assets under `pages-assets/`, and the static build publishes the old page URLs at the repository root. The design can be reworked later without changing the Android app.

The separate browser workspace scaffold remains under `src/` for later development. It is not yet the active homepage.

## Repository layout

```text
KirinDLWeb/
├── .github/workflows/       # CI and GitHub Pages deployment
├── docs/                    # Architecture, bridge and development notes
├── engine/                  # Web engine contracts and future adapters
├── modules/                 # Reserved for future Git submodules
├── pages/                   # Migrated Contact, Issues, Privacy and Support pages
├── pages-assets/            # Migrated site CSS, JavaScript and favicon
├── public/                  # Web platform public assets
├── scripts/                 # Development server and static build
├── server/                  # Future backend service boundary
├── src/                     # Future browser downloader workspace
└── tests/                   # Unit tests
```

## Local development

Requirements: Node.js 22 or newer.

```bash
npm run dev
```

Open the local URL printed by the server.

Run checks and create the static site build:

```bash
npm test
npm run build
```

The deployable site is written to `dist/`.

## Modular repository approach

The project follows the separation principle used by projects such as PipePipe: stable components may later become independently maintained repositories and be connected as Git submodules.

No submodule is declared yet because the target module repositories and their stable URLs have not been created. See [the modular layout notes](docs/architecture/modules.md).

## App–Web integration

The bridge protocol is still a specification, not a live connection. The Android source and native download engines remain in [Lanzkila/KirinDL](https://github.com/Lanzkila/KirinDL). Any Android changes will be limited to a separately reviewed bridge integration.

See [the bridge protocol](docs/bridge/protocol.md).

## Platform boundaries

- GitHub Pages hosts this static website; it does not run a long-lived downloader backend.
- Browser code cannot execute the Android Kotlin engine or access Android private storage.
- Browser-compatible features will run in the browser; tasks needing server resources will require a separately deployed and secured backend or a handoff to the Android app.
- Do not place API secrets, extractor cookies, signing keys or privileged credentials in the web frontend.

## Website migration

The visual design and informational Pages were migrated from the existing KirinDL repository. The source repository was left unchanged. The current presentation is temporary and may be redesigned specifically for the web platform later.
