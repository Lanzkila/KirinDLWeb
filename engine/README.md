# Web engine

KirinDL Web now has separate server-side extractor adapters in server/kirindl_server/.

- yt-dlp handles supported video/audio sources and exposes stream progress and post-processing stages.
- gallery-dl handles supported image galleries/collections and tracks completed files.
- The FastAPI task API exposes task creation, polling, cancellation and output download.
- FFmpeg is installed in the backend Docker image for media merging.

The browser cannot execute Android Kotlin services or native Python/FFmpeg binaries. The frontend calls the separately hosted API. GitHub Pages remains static.

The engine API is implemented but not deployed as a public service yet. See server/README.md for run/deploy requirements.
