# API routes

Implemented in server/kirindl_server/main.py:

- GET /api/v1/health — health check.
- POST /api/v1/tasks — create a task from a URL and selected engine.
- GET /api/v1/tasks/{id} — poll task state and progress.
- DELETE /api/v1/tasks/{id} — request cancellation.
- GET /api/v1/tasks/{id}/download — retrieve a completed file or ZIP.

Request body example:

    {"url":"https://example.com/media","engine":"auto"}

Task state is persisted in the SQLite database at KIRINDL_DATA_DIR/tasks.sqlite3. Download output is stored under the same persistent data directory. A completed task survives a process restart when its volume is retained; an interrupted active task is marked failed and must be resubmitted.

The browser must be configured with the backend HTTPS base URL in public/kirindl-config.js. The backend code is implemented but is not deployed as a public instance yet.
