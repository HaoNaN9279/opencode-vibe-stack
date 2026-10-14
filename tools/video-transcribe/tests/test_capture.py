"""Tests for frame capture orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from video_transcribe import capture
from video_transcribe.capture import FrameManifest, capture_frames
from video_transcribe.errors import JobError
from video_transcribe.paths import Job, JobMeta


def _make_job(tmp_path: Path) -> Job:
    meta = JobMeta(title="t", slug="t", video="t.mp4")
    job = Job.create(tmp_path / "t", meta)
    job.video_path.write_bytes(b"video")
    return job


def test_capture_writes_frames_and_manifest(tmp_path: Path, monkeypatch) -> None:
    job = _make_job(tmp_path)
    job.marks_path.write_text(
        json.dumps({"marks": [{"time": 30, "alt": "b"}, {"time": 5, "alt": "a"}]}),
        encoding="utf-8",
    )

    captured: list[Path] = []

    def fake_capture(video, time_seconds, out_png):
        out_png.parent.mkdir(parents=True, exist_ok=True)
        out_png.write_bytes(b"png")
        captured.append(out_png)

    monkeypatch.setattr(capture, "capture_frame", fake_capture)

    manifest = capture_frames(job)

    assert [f.frame for f in manifest.frames] == [
        "frames/frame_0001.png",
        "frames/frame_0002.png",
    ]
    # 按时间排序：先 5 秒
    assert manifest.frames[0].alt == "a"
    assert (job.frames_dir / "frame_0001.png").is_file()
    reloaded = FrameManifest.load(job.frames_manifest_path)
    assert len(reloaded.frames) == 2


def test_capture_missing_marks_raises(tmp_path: Path) -> None:
    job = _make_job(tmp_path)
    with pytest.raises(JobError):
        capture_frames(job)


def test_capture_empty_marks_raises(tmp_path: Path) -> None:
    job = _make_job(tmp_path)
    job.marks_path.write_text(json.dumps({"marks": []}), encoding="utf-8")
    with pytest.raises(JobError):
        capture_frames(job)


def test_recapture_removes_stale_frames(tmp_path: Path, monkeypatch) -> None:
    job = _make_job(tmp_path)

    def fake_capture(video, time_seconds, out_png):
        out_png.parent.mkdir(parents=True, exist_ok=True)
        out_png.write_bytes(b"png")

    monkeypatch.setattr(capture, "capture_frame", fake_capture)

    job.marks_path.write_text(
        json.dumps({"marks": [{"time": 5, "alt": "a"}, {"time": 20, "alt": "b"}]}),
        encoding="utf-8",
    )
    capture_frames(job)
    assert (job.frames_dir / "frame_0002.png").is_file()

    # Re-capture with fewer marks: the stale second frame must be removed.
    job.marks_path.write_text(
        json.dumps({"marks": [{"time": 5, "alt": "a"}]}), encoding="utf-8"
    )
    capture_frames(job)

    assert (job.frames_dir / "frame_0001.png").is_file()
    assert not (job.frames_dir / "frame_0002.png").exists()
