# Web engine

The web engine is independent from the Android Kotlin engine.

A browser cannot execute the Android app's Kotlin services or directly reuse Android storage integrations. Browser-safe operations belong in this area; extraction or processing that requires native binaries, Python packages, secrets, or long-running work will need a secured backend or a handoff to the Android app.

No extractor is implemented at scaffold stage.
