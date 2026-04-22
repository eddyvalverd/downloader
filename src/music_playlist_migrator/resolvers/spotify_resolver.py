from __future__ import annotations

import os
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Optional

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from music_playlist_migrator.models import MatchResult


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


def _compute_confidence(track: dict[str, Any], candidate: dict[str, Any]) -> float:
    title_score = _string_similarity(track.get("name", ""), candidate.get("name", ""))
    source_artist = ", ".join(track.get("artists", []) if isinstance(track.get("artists"), list) else [track.get("artist", "")])
    candidate_artist = ", ".join(artist.get("name", "") for artist in candidate.get("artists", []))
    artist_score = _string_similarity(source_artist, candidate_artist)
    duration_score = _duration_score(track.get("duration_ms"), candidate.get("duration_ms"))
    return round((title_score * 0.5) + (artist_score * 0.35) + (duration_score * 0.15), 4)


def _get_spotify_client() -> spotipy.Spotify:
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Missing Spotify credentials. Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET.")

    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)


def search_spotify_equivalent(track: dict[str, Any]) -> Optional[MatchResult]:
    """Search for the most likely Spotify equivalent track.

    Expected track format:
        {
            "name": "Track title",
            "artists": ["Artist 1", "Artist 2"],
            "duration_ms": 201000,
        }
    """
    client = _get_spotify_client()

    artists = track.get("artists") or [track.get("artist", "")]
    artist_query = " ".join([a for a in artists if a])
    query = f"track:{track.get('name', '')} artist:{artist_query}".strip()

    response = client.search(q=query, type="track", limit=8)
    items = response.get("tracks", {}).get("items", [])
    if not items:
        return None

    best_candidate = max(items, key=lambda candidate: _compute_confidence(track, candidate))
    confidence = _compute_confidence(track, best_candidate)

    artists_joined = ", ".join(artist.get("name", "") for artist in best_candidate.get("artists", []))
    return MatchResult(
        platform="spotify",
        track_name=best_candidate.get("name", ""),
        artist_name=artists_joined,
        album_name=best_candidate.get("album", {}).get("name"),
        duration_ms=best_candidate.get("duration_ms"),
        url=best_candidate.get("external_urls", {}).get("spotify", ""),
        confidence=confidence,
    )
