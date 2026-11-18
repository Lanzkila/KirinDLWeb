# Workers

The first backend version uses a bounded in-process ThreadPoolExecutor in server/kirindl_server/jobs.py.

- Default worker concurrency: 2.
- Default active-task cap: 3.
- Default task timeout: 3600 seconds.
- Default output limit: 2 GiB per task.
- A single Uvicorn worker and one backend replica are required because task state is held in process memory.

This is an initial single-instance worker implementation, not a durable distributed queue. Add Redis/Celery or another persistent queue plus a task database before horizontal scaling.
