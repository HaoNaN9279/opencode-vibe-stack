"""Tests for job paths and naming."""

from __future__ import annotations

from pathlib import Path

import pytest

from video_transcribe.errors import JobError
from video_transcribe.paths import Job, JobMeta, slugify


def test_slugify_replaces_invalid_characters() -> None:
    assert slugify('a/b:c*?"<>|') == "a_b_c______"


def test_slugify_keeps_unicode_and_trims() -> None:
    assert slugify("  教程 第1集  ") == "教程 第1集"


def test_slugify_caps_length() -> None:
    result = slugify("x" * 500, max_length=40)
    assert len(result) == 40


def test_slugify_empty_falls_back() -> None:
    assert slugify("...") == "video"


def test_job_create_and_load_roundtrip(tmp_path: Path) -> None:
    meta = JobMeta(title="标题", slug="标题", url="http://x", video="标题.mp4")
    job = Job.create(tmp_path / "标题", meta)

    assert (tmp_path / "标题" / "job.json").is_file()

    loaded = Job.load(tmp_path / "标题")
    assert loaded.meta.title == "标题"
    assert loaded.meta.url == "http://x"
    assert loaded.meta.created_at  # auto-filled


def test_job_load_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(JobError):
        Job.load(tmp_path / "nope")


def test_derived_paths(tmp_path: Path) -> None:
    meta = JobMeta(title="t", slug="t", video="t.mp4")
    job = Job.create(tmp_path / "t", meta)

    assert job.video_path == tmp_path / "t" / "t.mp4"
    assert job.audio_path.name == "t.wav"
    assert job.transcript_path.name == "transcript.json"
    assert job.marks_path.name == "marks.json"
    assert job.frames_dir.name == "frames"
    assert job.frames_manifest_path.name == "manifest.json"
    assert job.markdown_path.name == "t.md"


def test_video_path_scans_when_meta_missing(tmp_path: Path) -> None:
    root = tmp_path / "t"
    (root).mkdir()
    (root / "job.json").write_text('{"title": "t", "slug": "t"}', encoding="utf-8")
    (root / "t.webm").write_bytes(b"x")

    job = Job.load(root)
    assert job.video_path.suffix == ".webm"
