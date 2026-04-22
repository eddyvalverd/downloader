from __future__ import annotations

import os
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Optional

import requests

from music_playlist_migrator.models import MatchResult


_APPLE_MUSIC_API = "https://api.music.apple.com/v1/catalog/us/search"
_NOISE_PATTERNS = [
    re.compile(r"\((official\s+)?video\)", re.IGNORECASE),
    re.compile(r"\((official\s+)?visualizer\)", re.IGNORECASE),
    re.compile(r"\((official\s+)?audio\)", re.IGNORECASE),
    re.compile(r"\[(official\s+)?video\]", re.IGNORECASE),
    re.compile(r"\[(official\s+)?visualizer\]", re.IGNORECASE),
    re.compile(r"\[(official\s+)?audio\]", re.IGNORECASE),
    re.compile(r"\b(official\s+music\s+video|official\s+video|visualizer|lyrics?)\b", re.IGNORECASE),
]


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    for pattern in _NOISE_PATTERNS:
        normalized = pattern.sub(" ", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _string_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize_text(left), _normalize_text(right)).ratio()


def _duration_score(source_ms: Optional[int], candidate_ms: Optional[int]) -> float:
    if not source_ms or not candidate_ms:
        return 0.5
    delta = abs(source_ms - candidate_ms)
    if delta <= 1_500:
        return 1.0
    if delta <= 5_000:
        return 0.8
    if delta <= 12_000:
        return 0.5
    return 0.0


def _compute_confidence(track: dict[str, Any], attributes: dict[str, Any]) -> float:
    title_score = _string_similarity(track.get("name", ""), attributes.get("name", ""))
    source_artist = ", ".join(track.get("artists", []) if isinstance(track.get("artists"), list) else [track.get("artist", "")])
    artist_score = _string_similarity(source_artist, attributes.get("artistName", ""))
    duration_score = _duration_score(track.get("duration_ms"), attributes.get("durationInMillis"))
    return round((title_score * 0.5) + (artist_score * 0.35) + (duration_score * 0.15), 4)


def _apple_headers() -> dict[str, str]:
    token = os.getenv("APPLE_MUSIC_TOKEN")
    if not token:
        raise ValueError("Missing Apple Music token. Set APPLE_MUSIC_TOKEN.")
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def search_apple_equivalent(track: dict[str, Any]) -> Optional[MatchResult]:
    """Search for the most likely Apple Music equivalent track."""
    artists = track.get("artists") or [track.get("artist", "")]
    artist_query = " ".join([a for a in artists if a])
    term = f"{track.get('name', '')} {artist_query}".strip()

    response = requests.get(
        _APPLE_MUSIC_API,
        headers=_apple_headers(),
        params={"term": term, "types": "songs", "limit": 8},
        timeout=10,
    )
    response.raise_for_status()

    results = response.json().get("results", {}).get("songs", {}).get("data", [])
    if not results:
        return None

    best = max(results, key=lambda item: _compute_confidence(track, item.get("attributes", {})))
    attrs = best.get("attributes", {})
    confidence = _compute_confidence(track, attrs)

    return MatchResult(
        platform="apple_music",
        track_name=attrs.get("name", ""),
        artist_name=attrs.get("artistName", ""),
        album_name=attrs.get("albumName"),
        duration_ms=attrs.get("durationInMillis"),
        url=attrs.get("url", ""),
        confidence=confidence,
    )
