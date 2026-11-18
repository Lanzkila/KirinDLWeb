FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    KIRINDL_DATA_DIR=/data \
    KIRINDL_RETENTION_SECONDS=86400 \
    KIRINDL_CLEANUP_INTERVAL_SECONDS=300 \
    HOME=/tmp \
    XDG_CACHE_HOME=/tmp/.cache

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY server/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/requirements.txt

COPY server/kirindl_server /app/kirindl_server
RUN mkdir -p /data && useradd --create-home --uid 10001 kirindl \
    && chown -R kirindl:kirindl /data /app
USER kirindl

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/api/v1/health', timeout=3)" || exit 1
# This API trusts proxy headers only in the isolated deployment topology:
# publish Caddy, never this container's port directly.
CMD ["sh", "-c", "exec uvicorn kirindl_server.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips='*' --timeout-graceful-shutdown 30"]
