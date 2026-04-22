from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class MatchResult:
    platform: str
    track_name: str
    artist_name: str
    album_name: Optional[str]
    duration_ms: Optional[int]
    url: str
    confidence: float
