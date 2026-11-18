# Architecture overview

## Platform split

- **KirinDL Android** owns the native Android UI, native download services, app storage, notifications, and platform-specific engines.
- **KirinDLWeb** owns the browser UI, browser-compatible features, and web integration contracts.
- **Backend (future)** owns only the operations that cannot safely or practically run in the browser.

## Runtime flow

The browser UI calls browser services directly where possible. Operations requiring server resources go through a secured backend. Users may hand a supported request to the installed Android app through a verified and explicitly configured app link once both sides implement the same protocol.

## Repository boundary

This repository does not modify or vendor the Android application source. Cross-platform data is defined through neutral schemas and message contracts.
