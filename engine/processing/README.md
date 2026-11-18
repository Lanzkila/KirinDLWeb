# Processing

The backend task manager orchestrates:
- yt-dlp video/audio stream selection and downloads
- FFmpeg-assisted merging through yt-dlp postprocessors
- gallery-dl image collection downloads
- ZIP bundling when a gallery task produces multiple files
- task lifecycle, cancellation requests, output-size and runtime limits

Implementation: server/kirindl_server/jobs.py

FFmpeg and extractor jobs run on the backend host, never in a normal browser or GitHub Pages worker. A durable queue and persistent task database are still future work.
