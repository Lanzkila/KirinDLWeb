# KirinDL Web

The independent web platform for [KirinDL](https://github.com/Lanzkila/KirinDL).

This repository is intentionally separate from the Android application repository. The web client, browser-specific services, web engine adapters, backend contracts, and App–Web bridge documentation live here.

## Project status

**Scaffold stage.** This commit establishes the folder layout and a small static web shell. It does not yet download media, run yt-dlp, host a backend, or connect to the Android app. Those integrations will be added and tested in separate steps.

## Repository layout

```text
KirinDLWeb/
├── .github/workflows/       # CI and GitHub Pages deployment
├── docs/                    # Architecture, bridge and development notes
├── engine/                  # Web engine contracts and future adapters
├── modules/                 # Reserved for Git submodules when repos exist
├── public/                  # Static public assets
├── scripts/                 # Build helpers
├── server/                  # Backend service boundaries (not implemented)
├── src/
│   ├── app/                 # App entry point and hash router
│   ├── components/          # Reusable interface components
│   ├── core/                # Shared data types and protocol contracts
│   ├── pages/               # Home, download, history, settings and tools
│   ├── services/            # Browser and app integration adapters
│   └── styles/              # Global styles
└── tests/                   # Unit and integration tests
```

## Local development

Requirements: Node.js 22 or newer.

```bash
npm run dev
```

Then open the local URL printed by the server.

Run checks and create the static site build:

```bash
npm test
npm run build
```

The distributable website is written to `dist/`.

## Modular repository approach

The layout follows the separation principle used by projects such as PipePipe: components can become independently maintained repositories and later be connected as Git submodules. No submodule is declared yet because the future module repositories and their stable URLs have not been created.

See [the modular layout notes](docs/architecture/modules.md).

## App–Web integration

The bridge protocol is being designed separately from its transport. The current code contains only a versioned message contract; it does not claim that the Android application is already connected.

See [the bridge protocol](docs/bridge/protocol.md).

## Important boundaries

- The Android source and native download engines remain in [Lanzkila/KirinDL](https://github.com/Lanzkila/KirinDL).
- Browser code must not receive Android private storage paths, signing keys, cookies, or other secrets.
- A browser frontend cannot directly run the Android Kotlin engine.
- Server-side extraction or processing requires a separately deployed backend and suitable security controls.
- GitHub Pages can host the static frontend, not a long-running downloader backend.

## License

The web-specific license and attribution policy will be finalized before importing or adapting existing website assets and code.
