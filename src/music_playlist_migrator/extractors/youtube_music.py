from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from pytube import YouTube
from ytmusicapi import YTMusic

from music_playlist_migrator.models import Track


def _extract_playlist_id(playlist_url: str) -> str:
    if not isinstance(playlist_url, str) or not playlist_url.strip():
        raise ValueError("Invalid YouTube Music playlist URL: URL must be a non-empty string.")

    parsed = urlparse(playlist_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Invalid YouTube Music playlist URL: expected an http(s) URL.")

    query = parse_qs(parsed.query)
    playlist_id = (query.get("list") or [None])[0]
    if not playlist_id:
        raise ValueError(
            "Invalid YouTube Music playlist URL: missing playlist id (query parameter 'list')."
        )
    return playlist_id


def _normalize_duration(track_data: dict) -> int | None:
    duration = track_data.get("duration_seconds")
    if isinstance(duration, int):
        return duration

    duration_text = track_data.get("duration")
    if isinstance(duration_text, str) and duration_text:
        parts = duration_text.split(":")
        if all(part.isdigit() for part in parts):
            total = 0
            for part in parts:
                total = total * 60 + int(part)
            return total
    return None


def _fallback_metadata(video_id: str | None) -> tuple[str | None, list[str], int | None]:
    if not video_id:
        return None, [], None

    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        title = yt.title or None
        artists = [yt.author] if yt.author else []
        duration_seconds = yt.length if isinstance(yt.length, int) else None
        return title, artists, duration_seconds
    except Exception:
        return None, [], None


def fetch_playlist_tracks(playlist_url: str) -> list[Track]:
    """Fetch tracks from a YouTube Music playlist URL."""
    playlist_id = _extract_playlist_id(playlist_url)

    ytmusic = YTMusic()

    try:
        playlist_data = ytmusic.get_playlist(playlist_id, limit=None)
    except Exception as exc:
        message = str(exc).lower()
        if any(word in message for word in ("private", "forbidden", "permission", "login", "unavailable")):
            raise PermissionError(
                "Playlist is private or not accessible with current YouTube Music credentials."
            ) from exc
        raise

    if not isinstance(playlist_data, dict):
        raise PermissionError("Playlist is private or not accessible.")

    raw_tracks = playlist_data.get("tracks") or []
    if not isinstance(raw_tracks, list):
        raise PermissionError("Playlist is private or not accessible.")

    tracks: list[Track] = []
    for raw_track in raw_tracks:
        raw_track = raw_track or {}
        source_id = raw_track.get("videoId")

        is_available = raw_track.get("isAvailable")
        is_unavailable = bool(is_available is False or not source_id)

        title = raw_track.get("title")
        artists = [artist.get("name") for artist in (raw_track.get("artists") or []) if artist.get("name")]
        duration_seconds = _normalize_duration(raw_track)

        album_raw = raw_track.get("album")
        album = album_raw.get("name") if isinstance(album_raw, dict) else None

        if not title or not artists or duration_seconds is None:
            fb_title, fb_artists, fb_duration = _fallback_metadata(source_id)
            title = title or fb_title
            artists = artists or fb_artists
            duration_seconds = duration_seconds if duration_seconds is not None else fb_duration

        tracks.append(
            Track(
                source_id=source_id,
                title=title,
                artists=artists,
                duration_seconds=duration_seconds,
                album=album,
                is_unavailable=is_unavailable,
            )
        )

    return tracks
