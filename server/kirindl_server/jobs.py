from __future__ import annotations

import shutil
import subprocess
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


class TaskCancelled(Exception):
    pass


class TaskManager:
    """Single-process task manager for one backend instance.

    Job state is intentionally in memory for this first deployable adapter.
    Run a single Uvicorn worker. A durable queue/database is a later scale-out
    step; do not run multiple replicas against this in-memory registry.
    """

    ACTIVE_STATES = {"queued", "downloading", "processing", "merging"}

    def __init__(
        self,
        data_dir: str | Path,
        max_workers: int = 2,
        max_active_tasks: int = 3,
        max_download_bytes: int = 2 * 1024 * 1024 * 1024,
        task_timeout_seconds: int = 3600,
        retention_seconds: int = 24 * 60 * 60,
    ) -> None:
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_active_tasks = max_active_tasks
        self.max_download_bytes = max_download_bytes
        self.task_timeout_seconds = task_timeout_seconds
        self.retention_seconds = retention_seconds
        self._lock = threading.RLock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="kirindl-worker")

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def create(self, url: str, engine: str) -> dict[str, Any]:
        with self._lock:
            self._prune_expired()
            active = sum(1 for job in self._jobs.values() if job["status"] in self.ACTIVE_STATES)
            if active >= self.max_active_tasks:
                raise RuntimeError("The download queue is currently full. Try again later.")

            task_id = uuid.uuid4().hex
            job_dir = self.data_dir / task_id
            job_dir.mkdir(parents=True, exist_ok=False)
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
                "created_at": time.time(),
                "updated_at": time.time(),
                "directory": str(job_dir),
                "output_path": None,
                "cancel_requested": False,
                "process": None,
            }
            self._jobs[task_id] = job
            self._executor.submit(self._run, task_id)
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
            if not path.is_file() or self.data_dir not in path.parents:
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
            process = job.get("process")
            if process is not None and process.poll() is None:
                process.terminate()
            job["updated_at"] = time.time()
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
            job = self._jobs[task_id]
            job.update(changes)
            job["updated_at"] = time.time()

    def _update_progress(self, task_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[task_id]
            job["progress"].update(changes)
            job["updated_at"] = time.time()

    def _check_cancelled(self, task_id: str) -> None:
        with self._lock:
            if self._jobs[task_id]["cancel_requested"]:
                raise TaskCancelled("The download was cancelled.")

    def _job_directory(self, task_id: str) -> Path:
        return Path(self._jobs[task_id]["directory"])

    def _run(self, task_id: str) -> None:
        started = time.monotonic()
        requested_engine = self._jobs[task_id]["requested_engine"]
        try:
            self._update(task_id, status="downloading")
            self._update_progress(task_id, phase="downloading")
            if requested_engine in {"auto", "yt-dlp"}:
                self._update(task_id, engine="yt-dlp")
                try:
                    self._run_yt_dlp(task_id, started)
                except TaskCancelled:
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
            self._update(
                task_id,
                status="completed",
                filename=output_path.name,
                file_count=len(output_files),
                file_size=output_path.stat().st_size,
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
            self._update(task_id, status="cancelled", error="The download was cancelled.")
            self._update_progress(task_id, phase="cancelled")
            self._clean_job_directory(task_id)
        except Exception as exc:
            message = str(exc).strip() or "The extractor could not process this URL."
            self._update(task_id, status="failed", error=message[:500])
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
            result = downloader.extract_info(self._jobs[task_id]["url"], download=True)
        if result is None:
            raise RuntimeError("yt-dlp did not return media information.")
        self._update(task_id, status="processing")
        self._update_progress(task_id, phase="processing")

    def _run_gallery_dl(self, task_id: str, started: float) -> None:
        output_dir = self._job_directory(task_id)
        log_path = output_dir / "gallery-dl.log"
        command = [
            "gallery-dl",
            "--no-input",
            "--no-colors",
            "--directory",
            str(output_dir),
            self._jobs[task_id]["url"],
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
            while process.poll() is None:
                self._check_cancelled(task_id)
                if time.monotonic() - started > self.task_timeout_seconds:
                    process.terminate()
                    raise TimeoutError("The gallery download exceeded the configured time limit.")
                files = self._find_output_files(task_id)
                count = len(files)
                size = sum(item.stat().st_size for item in files)
                if size > self.max_download_bytes:
                    process.terminate()
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
        directory = self._job_directory(task_id)
        ignored = {".part", ".ytdl", ".json", ".log", ".temp"}
        return sorted(
            item for item in directory.rglob("*")
            if item.is_file()
            and item.suffix.lower() not in ignored
            and not item.name.endswith((".part", ".ytdl", ".temp"))
            and item.name != "gallery-dl.log"
        )

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

    def _prune_expired(self) -> None:
        cutoff = time.time() - self.retention_seconds
        expired = [
            task_id for task_id, job in self._jobs.items()
            if job["updated_at"] < cutoff and job["status"] not in self.ACTIVE_STATES
        ]
        for task_id in expired:
            job = self._jobs.pop(task_id, None)
            if job:
                shutil.rmtree(job["directory"], ignore_errors=True)
