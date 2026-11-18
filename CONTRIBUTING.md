# Contributing

## Current scope

KirinDLWeb is at scaffold stage. Keep changes focused on the web platform and its documented interfaces.

## Boundaries

- Do not copy or modify Android Kotlin files in this repository.
- Do not add credentials, cookies, signing keys, private URLs, or personal data.
- Do not claim a downloader or App–Web bridge is operational until it has an implementation and tests.
- Keep browser-only code under `src/services` and backend-only code under `server`.
- Add a contract and tests before introducing a new bridge message.

## Checks

```bash
npm test
npm run build
```

## Modular components

A directory becomes a Git submodule only after its standalone repository exists, its public interface, tests, ownership, and license are documented. Do not add placeholder submodule URLs.
