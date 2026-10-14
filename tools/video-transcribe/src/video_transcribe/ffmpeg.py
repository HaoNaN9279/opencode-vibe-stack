"""FFmpeg integration and helpers.

FFmpeg is provided by the ``imageio-ffmpeg`` wheel, which ships a private
binary inside the tool's virtual environment. The system ``PATH`` is never
consulted, so no global environment variable is modified or polluted.

An explicit binary can be forced via the ``VIDEO_TRANSCRIBE_FFMPEG``
environment variable, which is useful for testing.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from video_transcribe.errors import AudioExtractionError, FrameCaptureError

_ENV_OVERRIDE = "VIDEO_TRANSCRIBE_FFMPEG"


def get_ffmpeg() -> str:
    """Locate the private ffmpeg executable.

    Resolution order:

    1. ``VIDEO_TRANSCRIBE_FFMPEG`` environment variable (if it is a file).
    2. The binary bundled with ``imageio-ffmpeg``.

    Returns:
        Absolute path to the ffmpeg executable.
    """
    override = os.environ.get(_ENV_OVERRIDE)
    if override and Path(override).is_file():
        return override

    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(cmd: list[str], *, error_cls: type[Exception], message: str) -> None:
    """Run a subprocess command, raising ``error_cls`` on failure."""
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError as exc:
        raise error_cls(f"Executable not found: {cmd[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        raise error_cls(f"{message}: {stderr or exc}") from exc


def extract_audio(video_path: Path, out_wav: Path) -> None:
    """Extract mono 16 kHz PCM audio from *video_path*.

    Args:
        video_path: Source video file.
        out_wav: Destination WAV file (parent created if missing).

    Raises:
        AudioExtractionError: If ffmpeg fails.
    """
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        get_ffmpeg(),
        "-y",
        "-loglevel", "error",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(out_wav),
    ]
    _run(cmd, error_cls=AudioExtractionError, message=f"Failed to extract audio from {video_path}")


def capture_frame(video_path: Path, time_seconds: float, out_png: Path) -> None:
    """Capture a single video frame at *time_seconds*.

    Args:
        video_path: Source video file.
        time_seconds: Timestamp (seconds) to seek to.
        out_png: Destination PNG file (parent created if missing).

    Raises:
        FrameCaptureError: If ffmpeg fails.
    """
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        get_ffmpeg(),
        "-y",
        "-loglevel", "error",
        "-ss", f"{max(time_seconds, 0.0):.3f}",
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(out_png),
    ]
    _run(
        cmd,
        error_cls=FrameCaptureError,
        message=f"Failed to capture frame at {time_seconds:.3f}s from {video_path}",
    )
