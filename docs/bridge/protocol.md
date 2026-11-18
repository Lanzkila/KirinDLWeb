# App–Web bridge protocol

## Status

Specification only. The Android app and browser currently do not communicate through this protocol.

## Message envelope

Messages use a versioned JSON envelope:

```json
{
  "channel": "kirindl",
  "version": 1,
  "type": "download.request",
  "payload": {}
}
```

## Initial message types

- `app.open` — request navigation to a supported app destination.
- `download.request` — hand a validated URL and explicitly selected options to the app.
- `download.status` — represent a task status returned by an authorized transport.
- `capabilities.request` / `capabilities.response` — negotiate supported features.

## Security requirements

- Accept only known message types and protocol versions.
- Validate URL schemes and payload sizes on both sides.
- Never trust browser-provided file paths or arbitrary command strings.
- Require a user gesture before handing off a request.
- Do not expose privileged Android interfaces to arbitrary websites.
- Prefer verified HTTPS App Links for website-to-app navigation.
- A custom WebView JavaScript bridge, if ever required, must be origin-restricted and narrowly scoped.

The Android package identity, signing certificate fingerprints, production domain, and supported navigation paths must be confirmed before configuring `assetlinks.json` or Android intent filters.
