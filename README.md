# KirinDL Web

The independent web platform for KirinDL. This repository remains separate from the Android application repository.

## Project status

The migrated information pages remain available. A web-specific downloader preview is in preview.html. The web engine API has been implemented in server/ but has not yet been deployed to a public backend host.

- Part 1 preview: https://raw.githack.com/Lanzkila/KirinDLWeb/main/preview.html
- Web redesign plan: docs/roadmap/web-redesign-plan.txt
- Progress 1–9: docs/roadmap/progress-1-9.md
- Backend API and run guide: server/README.md

The web UI now submits tasks to a real backend API when apiBase is configured. It no longer simulates download progress. On a hosted Pages preview with no API configured, it displays a clear backend-not-configured message.

## Repository layout

    KirinDLWeb/
    ├── docs/                    Architecture, bridge and development notes
    ├── engine/                  Web engine contracts and adapters map
    ├── pages/                   Migrated information pages
    ├── pages-assets/            Migrated site assets
    ├── preview.html             Web-specific downloader preview
    ├── public/                  Frontend modules and public config
    ├── server/                  FastAPI backend, yt-dlp and gallery-dl adapters
    ├── scripts/                 Development server and static build
    └── tests/                   Frontend unit tests

## Local development

Requirements: Node.js 22+ and Python 3.12+ (or Docker).

Start the frontend:

    npm run dev

Build/test the frontend:

    npm test
    npm run build

Start the backend locally:

    python -m venv .venv
    . .venv/bin/activate
    pip install -r server/requirements-dev.txt
    KIRINDL_DATA_DIR=./.downloads uvicorn kirindl_server.main:app --app-dir server --reload

Or use Docker from the repository root:

    docker build -f server/Dockerfile -t kirindl-web-engine .
    docker run --rm -p 8000:8000 -v kirindl-downloads:/data --env-file server/.env.example kirindl-web-engine

For local preview, public/kirindl-config.js defaults to the local backend URL. For production, set apiBase there to the HTTPS URL of the deployed backend.

## Backend capabilities and boundaries

- yt-dlp handles supported video/audio media.
- gallery-dl handles supported image galleries and packages multiple outputs into ZIP.
- FFmpeg is installed in the backend Docker image for media merging.
- The backend exposes task creation, status, cancellation and file download endpoints.
- GitHub Pages only serves static frontend content. It cannot run yt-dlp, gallery-dl or FFmpeg.
- The backend is implemented but has not been deployed to a public server. Public live downloads will not work until a backend host is configured.
- Never put the server API token, cookies or other secrets in frontend JavaScript.
- The Android repository is untouched; this web engine is an independent runtime.

See server/README.md for security limits and deployment notes.
