# Workers

The backend uses a bounded in-process ThreadPoolExecutor in server/kirindl_server/jobs.py.

- Default worker concurrency: 2.
- Default active-task cap: 3.
- Default task timeout: 3600 seconds.
- Default output limit: 2 GiB per task.
- Task records are persisted in SQLite under KIRINDL_DATA_DIR/tasks.sqlite3.
- Completed output directories are retained for 24 hours by default; a background cleanup thread prunes expired files and rows every 300 seconds.
- Cancellation checks run in the extractor hooks and the gallery-dl child process is terminated and reaped on cancellation or timeout.

Important deployment constraints:

- Use one Uvicorn worker and one backend replica. The thread pool is in-process; SQLite durability does not make it a distributed queue.
- Active extractor sessions do not resume after a process restart. Their durable task records are recovered as failed, while completed files remain available if the volume persists.
- Mount persistent storage at KIRINDL_DATA_DIR. Ephemeral filesystem storage loses task history and output files when the container is replaced.
- Add a separate distributed queue/worker service before horizontal scaling.
