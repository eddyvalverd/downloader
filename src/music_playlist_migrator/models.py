from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Track:
    source_id: str | None
    title: str | None
    artists: list[str]
    duration_seconds: int | None
    album: str | None
    is_unavailable: bool = False
