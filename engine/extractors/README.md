# Extractor adapters

Implemented backend adapters:
- yt-dlp Python API for supported video/audio sources, using stream progress and postprocessor hooks.
- gallery-dl CLI adapter for supported image galleries and collections, tracking completed files and packaging multi-file results into ZIP.

Implementation: server/kirindl_server/jobs.py
API lifecycle: server/kirindl_server/main.py

The browser submits the URL and engine selection to the backend API. Extraction and processing never run in the GitHub Pages browser runtime.

Do not copy Android extractor code here without checking runtime compatibility and licensing. Source-site support depends on current upstream extractor versions and may change.
