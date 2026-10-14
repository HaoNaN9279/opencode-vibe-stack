"""Frame capture: turn ``marks.json`` into extracted images + a manifest."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from video_transcribe.errors import JobError
from video_transcribe.ffmpeg import capture_frame
from video_transcribe.marks import Marks
from video_transcribe.paths import Job


@dataclass
class Frame:
    """A captured frame paired with its timestamp and caption metadata."""

    time: float
    frame: str
    alt: str
    note: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Frame":
        """Build a :class:`Frame` from a decoded mapping."""
        return cls(
            time=float(data.get("time", 0.0)),
            frame=str(data.get("frame", "")),
            alt=str(data.get("alt", "")),
            note=str(data.get("note", "")),
        )


@dataclass
class FrameManifest:
    """The list of captured frames, persisted to ``frames/manifest.json``."""

    frames: list[Frame] = field(default_factory=list)

    def save(self, path: Path) -> None:
        """Write the manifest as JSON to *path*."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"frames": [asdict(frame) for frame in self.frames]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "FrameManifest":
        """Load a manifest from *path*.

        Raises:
            JobError: If the manifest is missing or invalid.
        """
        if not path.is_file():
            raise JobError(
                f"Frame manifest not found: {path}\nRun the 'capture' command first."
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise JobError(f"Invalid frame manifest: {exc}") from exc
        raw = data.get("frames", []) if isinstance(data, dict) else data
        return cls(frames=[Frame.from_dict(item) for item in raw])


def capture_frames(job: Job) -> FrameManifest:
    """Capture one frame per mark in ``marks.json``.

    Frames are named ``frame_0001.png`` … in chronological order and stored
    under ``<job>/frames/``. A manifest is written to
    ``<job>/frames/manifest.json``.

    Args:
        job: The job to process.

    Returns:
        The resulting :class:`FrameManifest`.

    Raises:
        JobError: If ``marks.json`` is missing or has no marks.
        FrameCaptureError: If ffmpeg fails.
    """
    marks = Marks.load(job.marks_path)
    ordered = marks.sorted()
    if not ordered:
        raise JobError(f"No marks defined in {job.marks_path}")

    video_path = job.video_path
    frames_dir = job.frames_dir
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Remove frames from any previous run so re-capture overwrites cleanly.
    for stale in frames_dir.glob("frame_*.png"):
        stale.unlink()

    frames: list[Frame] = []
    for index, mark in enumerate(ordered, start=1):
        filename = f"frame_{index:04d}.png"
        capture_frame(video_path, mark.time, frames_dir / filename)
        frames.append(
            Frame(
                time=mark.time,
                frame=f"frames/{filename}",
                alt=mark.alt,
                note=mark.note,
            )
        )

    manifest = FrameManifest(frames=frames)
    manifest.save(job.frames_manifest_path)
    return manifest
