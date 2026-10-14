"""Tests for ffmpeg command construction."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from video_transcribe import ffmpeg
from video_transcribe.errors import AudioExtractionError


def test_extract_audio_builds_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(ffmpeg, "get_ffmpeg", lambda: "ffmpeg-x")
    calls: list[list[str]] = []
    monkeypatch.setattr(ffmpeg.subprocess, "run", lambda cmd, **kw: calls.append(cmd))

    out = tmp_path / "audio" / "a.wav"
    ffmpeg.extract_audio(tmp_path / "v.mp4", out)

    assert calls[0][0] == "ffmpeg-x"
    assert "-vn" in calls[0]
    assert "pcm_s16le" in calls[0]
    assert str(out) == calls[0][-1]


def test_capture_frame_builds_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(ffmpeg, "get_ffmpeg", lambda: "ffmpeg-x")
    calls: list[list[str]] = []
    monkeypatch.setattr(ffmpeg.subprocess, "run", lambda cmd, **kw: calls.append(cmd))

    out = tmp_path / "frame.png"
    ffmpeg.capture_frame(tmp_path / "v.mp4", 12.5, out)

    assert calls[0][0] == "ffmpeg-x"
    assert "-ss" in calls[0]
    assert "12.500" in calls[0]
    assert str(out) == calls[0][-1]


def test_extract_audio_failure_raises(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(ffmpeg, "get_ffmpeg", lambda: "ffmpeg-x")

    def boom(cmd, **kw):
        raise subprocess.CalledProcessError(1, cmd, stderr=b"nope")

    monkeypatch.setattr(ffmpeg.subprocess, "run", boom)

    with pytest.raises(AudioExtractionError):
        ffmpeg.extract_audio(tmp_path / "v.mp4", tmp_path / "a.wav")
