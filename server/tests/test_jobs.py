from __future__ import annotations

import shutil
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from kirindl_server.jobs import TaskManager


def make_manager(path: Path, **kwargs) -> TaskManager:
    options = {
        "max_workers": 1,
        "max_active_tasks": 3,
        "cleanup_interval_seconds": 3600,
    }
    options.update(kwargs)
    return TaskManager(data_dir=path, **options)


def use_idle_worker(manager: TaskManager) -> None:
    # Keep worker execution deterministic; these tests exercise the registry.
    manager._run = lambda task_id: None  # type: ignore[method-assign]


def test_completed_task_and_output_survive_manager_restart(tmp_path):
    manager = make_manager(tmp_path)
    use_idle_worker(manager)
    task = manager.create("https://example.com/media", "yt-dlp")
    task_id = task["id"]
    task_dir = tmp_path / task_id
    output = task_dir / "result.mp4"
    output.write_bytes(b"media")

    manager._update(
        task_id,
        status="completed",
        filename=output.name,
        file_count=1,
        file_size=output.stat().st_size,
        output_path=str(output),
        download_url=f"/api/v1/tasks/{task_id}/download",
    )
    manager._update_progress(task_id, phase="completed", video_percent=100, audio_percent=100)
    manager.close()

    restored = make_manager(tmp_path)
    try:
        result = restored.get(task_id)
        assert result is not None
        assert result["status"] == "completed"
        assert result["filename"] == "result.mp4"
        assert restored.get_download_path(task_id) == (output, "result.mp4")
    finally:
        restored.close()


def test_interrupted_active_task_is_recovered_as_failed(tmp_path):
    manager = make_manager(tmp_path)
    use_idle_worker(manager)
    task = manager.create("https://example.com/media", "gallery-dl")
    task_id = task["id"]
    manager.close()

    restored = make_manager(tmp_path)
    try:
        result = restored.get(task_id)
        assert result is not None
        assert result["status"] == "failed"
        assert "backend restarted" in result["error"].lower()
        assert result["progress"]["phase"] == "failed"
    finally:
        restored.close()


def test_expired_task_record_and_files_are_pruned(tmp_path):
    manager = make_manager(tmp_path, retention_seconds=60)
    use_idle_worker(manager)
    task = manager.create("https://example.com/media", "yt-dlp")
    task_id = task["id"]
    task_dir = tmp_path / task_id
    (task_dir / "output.mp4").write_bytes(b"media")

    with manager._lock:
        job = manager._jobs[task_id]
        job["status"] = "failed"
        job["updated_at"] = time.time() - 120
        manager._persist(job)

    try:
        manager._prune_expired()
        assert manager.get(task_id) is None
        assert not task_dir.exists()
    finally:
        manager.close()


def test_download_path_cannot_escape_data_directory(tmp_path):
    manager = make_manager(tmp_path)
    use_idle_worker(manager)
    task = manager.create("https://example.com/media", "yt-dlp")
    task_id = task["id"]
    outside = tmp_path.parent / "outside-output.mp4"
    outside.write_bytes(b"not allowed")
    manager._update(
        task_id,
        status="completed",
        filename=outside.name,
        output_path=str(outside),
    )
    try:
        assert manager.get_download_path(task_id) is None
    finally:
        manager.close()
        outside.unlink(missing_ok=True)


def test_public_task_does_not_expose_internal_paths_or_processes(tmp_path):
    manager = make_manager(tmp_path)
    use_idle_worker(manager)
    try:
        task = manager.create("https://example.com/media", "yt-dlp")
        assert "directory" not in task
        assert "output_path" not in task
        assert "process" not in task
        assert "future" not in task
    finally:
        manager.close()


def test_active_task_limit_is_enforced(tmp_path):
    manager = make_manager(tmp_path, max_active_tasks=1)
    use_idle_worker(manager)
    try:
        manager.create("https://example.com/one", "yt-dlp")
        with pytest.raises(RuntimeError, match="queue is currently full"):
            manager.create("https://example.com/two", "yt-dlp")
    finally:
        manager.close()


def test_task_is_rejected_when_storage_reserve_is_too_low(tmp_path, monkeypatch):
    manager = make_manager(
        tmp_path,
        max_download_bytes=10,
        minimum_free_bytes=5,
    )
    use_idle_worker(manager)
    usage = SimpleNamespace(total=100, used=98, free=2)
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: usage)
    try:
        with pytest.raises(RuntimeError, match="low on free disk space"):
            manager.create("https://example.com/media", "yt-dlp")
        assert manager.get("no-such-task") is None
    finally:
        manager.close()
