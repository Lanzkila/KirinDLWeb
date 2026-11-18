from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
import zipfile
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class TaskCancelled(Exception):
    pass


class TaskStorageError(RuntimeError):
    """Raised when a new task would risk exhausting persistent storage."""


class TaskManager:
    """SQLite-backed task registry with a bounded, single-process worker pool.

    Task records survive a process restart. Active downloads are not resumed:
    they are recovered as failed because extractor sessions cannot be safely
    reconstructed. Run one Uvicorn worker/replica until workers are separated
    into a dedicated queue service.
    """

    ACTIVE_STATES = {"queued", "downloading", "processing", "merging"}
    IGNORED_SUFFIXES = {
        ".part", ".ytdl", ".temp", ".json", ".log",
        ".description", ".vtt", ".srt", ".ass", ".lrc",
    }

    def __init__(
        self,
        data_dir: str | Path,
        max_workers: int = 2,
        max_active_tasks: int = 3,
        max_download_bytes: int = 2 * 1024 * 1024 * 1024,
        task_timeout_seconds: int = 3600,
        retention_seconds: int = 24 * 60 * 60,
        cleanup_interval_seconds: int = 300,
        minimum_free_bytes: int = 512 * 1024 * 1024,
    ) -> None:
        if max_workers < 1 or max_active_tasks < 1:
            raise ValueError("Worker and active-task limits must be positive.")
        if max_download_bytes < 1 or task_timeout_seconds < 1:
            raise ValueError("Download size and timeout limits must be positive.")
        if retention_seconds < 1 or cleanup_interval_seconds < 1 or minimum_free_bytes < 0:
            raise ValueError("Retention, cleanup and storage-reserve settings are invalid.")

        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path = self.data_dir / "tasks.sqlite3"
        self.max_active_tasks = max_active_tasks
        self.max_download_bytes = max_download_bytes
        self.task_timeout_seconds = task_timeout_seconds
        self.retention_seconds = retention_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.minimum_free_bytes = minimum_free_bytes
        self._lock = threading.RLock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._stop_cleanup = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="kirindl-worker")

        self._initialize_database()
        self._load_persisted_jobs()

        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="kirindl-retention-cleanup",
            daemon=True,
        )
        self._cleanup_thread.start()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=15000")
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )

    def _serialize_job(self, job: dict[str, Any]) -> str:
        durable = {key: value for key, value in job.items() if key not in {"process", "future"}}
        return json.dumps(durable, ensure_ascii=False, separators=(",", ":"))

    def _persist(self, job: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (id, payload) VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET payload = excluded.payload
                """,
                (job["id"], self._serialize_job(job)),
            )

    def _load_persisted_jobs(self) -> None:
        now = time.time()
        with self._connect() as connection:
            rows = connection.execute("SELECT id, payload FROM tasks").fetchall()

        with self._lock:
            for row in rows:
                try:
                    job = json.loads(row["payload"])
                    if not isinstance(job, dict) or job.get("id") != row["id"]:
                        continue
                    job["process"] = None
                    job["future"] = None
                    if job.get("status") in self.ACTIVE_STATES:
                        job["status"] = "failed"
                        job["error"] = "The backend restarted while this task was running. Please submit it again."
                        job.setdefault("progress", {})["phase"] = "failed"
                        job["updated_at"] = now
                    output_path = job.get("output_path")
                    if job.get("status") == "completed" and output_path:
                        stored_path = Path(output_path).resolve()
                        if self.data_dir not in stored_path.parents or not stored_path.is_file():
                            job["status"] = "failed"
                            job["error"] = "The completed output file is no longer available. Please submit it again."
                            job["output_path"] = None
                            job["download_url"] = None
                            job["updated_at"] = now
                    self._jobs[job["id"]] = job
                    self._persist(job)
                except (KeyError, TypeError, ValueError, OSError, sqlite3.Error):
                    continue

    def close(self) -> None:
        self._stop_cleanup.set()
        self._cleanup_thread.join(timeout=2)
        with self._lock:
            for job in self._jobs.values():
                if job.get("status") in self.ACTIVE_STATES:
                    job["cancel_requested"] = True
                    process = job.get("process")
                    if process is not None and process.poll() is None:
                        self._terminate_process(process)
                    self._persist(job)
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _ensure_storage_space(self) -> None:
        # Gallery ZIP packaging temporarily coexists with the source files.
        # Keep enough headroom for the configured output cap plus a reserve.
        required_free = (self.max_download_bytes * 2) + self.minimum_free_bytes
        try:
            free_bytes = shutil.disk_usage(self.data_dir).free
        except OSError as exc:
            raise TaskStorageError("The backend storage volume is unavailable.") from exc
        if free_bytes < required_free:
            raise TaskStorageError(
                "The backend is low on free disk space. Older downloads must expire before another task can start."
            )

    def create(self, url: str, engine: str) -> dict[str, Any]:
        with self._lock:
            self._prune_expired()
            self._ensure_storage_space()
            active = sum(1 for job in self._jobs.values() if job["status"] in self.ACTIVE_STATES)
            if active >= self.max_active_tasks:
                raise RuntimeError("The download queue is currently full. Try again later.")

            task_id = uuid.uuid4().hex
            job_dir = self.data_dir / task_id
            job_dir.mkdir(parents=True, exist_ok=False)
            now = time.time()
            job: dict[str, Any] = {
                "id": task_id,
                "url": url,
                "requested_engine": engine,
                "engine": engine,
                "status": "queued",
                "progress": {
                    "video_percent": 0,
                    "audio_percent": 0,
                    "items_completed": 0,
                    "items_total": None,
                    "phase": "queued",
                },
                "filename": None,
                "file_count": 0,
                "file_size": None,
                "download_url": None,
                "error": None,
                "created_at": now,
                "updated_at": now,
                "directory": str(job_dir),
                "output_path": None,
                "cancel_requested": False,
                "process": None,
                "future": None,
            }
            self._jobs[task_id] = job
            self._persist(job)
            try:
                job["future"] = self._executor.submit(self._run, task_id)
            except Exception:
                self._jobs.pop(task_id, None)
                with self._connect() as connection:
                    connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                shutil.rmtree(job_dir, ignore_errors=True)
                raise
            return self._public_copy(job)

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(task_id)
            return self._public_copy(job) if job else None

    def get_download_path(self, task_id: str) -> tuple[Path, str] | None:
        with self._lock:
            job = self._jobs.get(task_id)
            if not job or job["status"] != "completed" or not job.get("output_path"):
                return None
            path = Path(job["output_path"]).resolve()
            if self.data_dir not in path.parents or not path.is_file():
                return None
            return path, str(job["filename"] or path.name)

    def cancel(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(task_id)
            if not job:
                return None
            if job["status"] not in self.ACTIVE_STATES:
                return self._public_copy(job)

            job["cancel_requested"] = True
            future: Future[Any] | None = job.get("future")
            if job["status"] == "queued" and future is not None and future.cancel():
                job["status"] = "cancelled"
                job["error"] = "The download was cancelled."
                job["progress"]["phase"] = "cancelled"
                self._clean_job_directory(task_id)
            process = job.get("process")
            if process is not None and process.poll() is None:
                self._terminate_process(process)
            job["updated_at"] = time.time()
            self._persist(job)
            return self._public_copy(job)

    def _public_copy(self, job: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": job["id"],
            "url": job["url"],
            "engine": job["engine"],
            "status": job["status"],
            "progress": dict(job["progress"]),
            "filename": job["filename"],
            "file_count": job["file_count"],
            "file_size": job["file_size"],
            "download_url": job["download_url"],
            "error": job["error"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        }

    def _update(self, task_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs.get(task_id)
            if job is None:
                return
            job.update(changes)
            job["updated_at"] = time.time()
            self._persist(job)

    def _update_progress(self, task_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs.get(task_id)
            if job is None:
                return
            job["progress"].update(changes)
            job["updated_at"] = time.time()
            self._persist(job)

    def _check_cancelled(self, task_id: str) -> None:
        with self._lock:
            job = self._jobs.get(task_id)
            if job is None or job["cancel_requested"]:
                raise TaskCancelled("The download was cancelled.")

    def _job_directory(self, task_id: str) -> Path:
        with self._lock:
            job = self._jobs[task_id]
            return Path(job["directory"])

    def _run(self, task_id: str) -> None:
        started = time.monotonic()
        with self._lock:
            job = self._jobs.get(task_id)
            if job is None:
                return
            requested_engine = job["requested_engine"]
        try:
            self._check_cancelled(task_id)
            self._update(task_id, status="downloading")
            self._update_progress(task_id, phase="downloading")
            if requested_engine in {"auto", "yt-dlp"}:
                self._update(task_id, engine="yt-dlp")
                try:
                    self._run_yt_dlp(task_id, started)
                except (TaskCancelled, TaskStorageError):
                    raise
                except Exception:
                    if requested_engine != "auto":
                        raise
                    self._check_cancelled(task_id)
                    self._clean_job_directory(task_id)
                    self._update(task_id, engine="gallery-dl", status="downloading")
                    self._update_progress(
                        task_id,
                        video_percent=0,
                        audio_percent=0,
                        items_completed=0,
                        items_total=None,
                        phase="gallery-download",
                    )
                    self._run_gallery_dl(task_id, started)
            else:
                self._update(task_id, engine="gallery-dl")
                self._run_gallery_dl(task_id, started)

            self._check_cancelled(task_id)
            output_files = self._find_output_files(task_id)
            if not output_files:
                raise RuntimeError("The extractor finished but did not produce a downloadable file.")
            total_size = sum(item.stat().st_size for item in output_files)
            if total_size > self.max_download_bytes:
                raise RuntimeError("The resulting download exceeded the configured size limit.")

            output_path = self._prepare_output(task_id, output_files)
            self._check_cancelled(task_id)
            output_size = output_path.stat().st_size
            if output_size > self.max_download_bytes:
                raise RuntimeError("The packaged download exceeded the configured size limit.")
            self._update(
                task_id,
                status="completed",
                filename=output_path.name,
                file_count=len(output_files),
                file_size=output_size,
                output_path=str(output_path),
                download_url=f"/api/v1/tasks/{task_id}/download",
                error=None,
            )
            self._update_progress(
                task_id,
                video_percent=100,
                audio_percent=100,
                phase="completed",
                items_completed=len(output_files),
                items_total=len(output_files),
            )
        except TaskCancelled:
            self._update(task_id, status="cancelled", error="The download was cancelled.", process=None)
            self._update_progress(task_id, phase="cancelled")
            self._clean_job_directory(task_id)
        except Exception as exc:
            message = str(exc).strip() or "The extractor could not process this URL."
            self._update(task_id, status="failed", error=message[:500], process=None)
            self._update_progress(task_id, phase="failed")
        finally:
            self._update(task_id, process=None)

    def _run_yt_dlp(self, task_id: str, started: float) -> None:
        try:
            import yt_dlp
        except ImportError as exc:
            raise RuntimeError("yt-dlp is not installed on the backend.") from exc

        output_dir = self._job_directory(task_id)
        manager = self

        def progress_hook(event: dict[str, Any]) -> None:
            manager._check_cancelled(task_id)
            manager._ensure_storage_space()
            if time.monotonic() - started > manager.task_timeout_seconds:
                raise TimeoutError("The download exceeded the configured time limit.")
            status = event.get("status")
            info = event.get("info_dict") or {}
            vcodec = info.get("vcodec")
            acodec = info.get("acodec")
            has_video = bool(vcodec and vcodec != "none")
            has_audio = bool(acodec and acodec != "none")
            total = event.get("total_bytes") or event.get("total_bytes_estimate")
            downloaded = event.get("downloaded_bytes") or 0
            percent = min(100, max(0, round(downloaded * 100 / total))) if total else None

            changes: dict[str, Any] = {"phase": "downloading"}
            if percent is not None:
                if has_video:
                    changes["video_percent"] = percent
                if has_audio:
                    changes["audio_percent"] = percent
                if not has_video and not has_audio:
                    changes["video_percent"] = percent
                    changes["audio_percent"] = percent
            if status == "finished":
                if has_video:
                    changes["video_percent"] = 100
                if has_audio:
                    changes["audio_percent"] = 100
                if not has_video and not has_audio:
                    changes["video_percent"] = 100
                    changes["audio_percent"] = 100
            manager._update_progress(task_id, **changes)

        def postprocessor_hook(event: dict[str, Any]) -> None:
            manager._check_cancelled(task_id)
            processor = str(event.get("postprocessor") or "").lower()
            phase = "merging" if "merger" in processor else "processing"
            manager._update(task_id, status=phase)
            manager._update_progress(task_id, phase=phase)

        options = {
            "format": "bestvideo*+bestaudio/best",
            "outtmpl": str(output_dir / "%(title).160B [%(id)s].%(ext)s"),
            "noplaylist": True,
            "merge_output_format": "mkv",
            "restrictfilenames": True,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 20,
            "retries": 2,
            "fragment_retries": 2,
            "max_filesize": self.max_download_bytes,
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [postprocessor_hook],
        }
        with yt_dlp.YoutubeDL(options) as downloader:
            result = downloader.extract_info(self._get_job_url(task_id), download=True)
        if result is None:
            raise RuntimeError("yt-dlp did not return media information.")
        self._update(task_id, status="processing")
        self._update_progress(task_id, phase="processing")

    def _get_job_url(self, task_id: str) -> str:
        with self._lock:
            return str(self._jobs[task_id]["url"])

    @staticmethod
    def _terminate_process(process: subprocess.Popen[Any]) -> None:
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

    def _run_gallery_dl(self, task_id: str, started: float) -> None:
        output_dir = self._job_directory(task_id)
        log_path = output_dir / "gallery-dl.log"
        command = [
            "gallery-dl",
            "--no-input",
            "--no-colors",
            "--directory",
            str(output_dir),
            self._get_job_url(task_id),
        ]
        with log_path.open("w", encoding="utf-8", errors="replace") as log_file:
            process = subprocess.Popen(
                command,
                cwd=str(output_dir),
                stdout=subprocess.DEVNULL,
                stderr=log_file,
                stdin=subprocess.DEVNULL,
            )
            self._update(task_id, process=process, status="downloading")
            try:
                while process.poll() is None:
                    self._check_cancelled(task_id)
                    self._ensure_storage_space()
                    if time.monotonic() - started > self.task_timeout_seconds:
                        raise TimeoutError("The gallery download exceeded the configured time limit.")
                    files = self._find_output_files(task_id)
                    count = len(files)
                    size = sum(item.stat().st_size for item in files)
                    if size > self.max_download_bytes:
                        raise RuntimeError("The gallery download exceeded the configured size limit.")
                    self._update_progress(
                        task_id,
                        phase="gallery-download",
                        items_completed=count,
                        video_percent=0,
                        audio_percent=0,
                    )
                    time.sleep(0.5)
                exit_code = process.wait(timeout=5)
            except Exception:
                self._terminate_process(process)
                raise
            finally:
                self._update(task_id, process=None)

        if exit_code != 0:
            detail = ""
            try:
                detail = log_path.read_text(encoding="utf-8", errors="replace")[-1200:]
            except OSError:
                pass
            raise RuntimeError(detail.strip() or f"gallery-dl exited with status {exit_code}.")
        self._update(task_id, status="processing")
        self._update_progress(task_id, phase="processing")

    def _find_output_files(self, task_id: str) -> list[Path]:
        directory = self._job_directory(task_id).resolve()
        result: list[Path] = []
        for item in directory.rglob("*"):
            if not item.is_file() or item.is_symlink() or item.suffix.lower() in self.IGNORED_SUFFIXES:
                continue
            try:
                resolved = item.resolve()
                resolved.relative_to(directory)
            except (OSError, ValueError):
                continue
            result.append(resolved)
        return sorted(result)

    def _prepare_output(self, task_id: str, files: list[Path]) -> Path:
        if len(files) == 1:
            return files[0]
        directory = self._job_directory(task_id)
        archive = directory / "KirinDL-downloads.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as output:
            for item in files:
                output.write(item, arcname=str(item.relative_to(directory)))
        return archive

    def _clean_job_directory(self, task_id: str) -> None:
        directory = self._job_directory(task_id)
        if directory.exists():
            shutil.rmtree(directory, ignore_errors=True)

    def _cleanup_loop(self) -> None:
        while not self._stop_cleanup.wait(self.cleanup_interval_seconds):
            try:
                with self._lock:
                    self._prune_expired()
            except (OSError, sqlite3.Error):
                continue

    def _prune_expired(self) -> None:
        cutoff = time.time() - self.retention_seconds
        expired = [
            task_id for task_id, job in self._jobs.items()
            if job["updated_at"] < cutoff and job["status"] not in self.ACTIVE_STATES
        ]
        if not expired:
            return
        with self._connect() as connection:
            for task_id in expired:
                job = self._jobs.pop(task_id, None)
                if job:
                    shutil.rmtree(job["directory"], ignore_errors=True)
                    connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
