FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    KIRINDL_DATA_DIR=/data

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
CMD ["uvicorn", "kirindl_server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
