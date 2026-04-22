"""Pipeline orchestration for playlist migration."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


class InvalidPlaylistUrlError(ValueError):
    """Raised when the provided playlist URL is not a valid YouTube Music URL."""


def _validate_youtube_music_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise InvalidPlaylistUrlError(
            "La URL de la playlist debe iniciar con http:// o https://."
        )

    if parsed.netloc not in {"music.youtube.com", "www.music.youtube.com"}:
        raise InvalidPlaylistUrlError(
            "La URL no pertenece a YouTube Music (dominio esperado: music.youtube.com)."
        )

    if not parsed.path.startswith("/playlist"):
        raise InvalidPlaylistUrlError(
            "La URL de YouTube Music debe apuntar a una playlist (ruta /playlist)."
        )



def run_pipeline(playlist_url: str, output_csv: str, include_apple: bool = False) -> Path:
    """Run playlist migration pipeline and generate a CSV report."""
    _validate_youtube_music_url(playlist_url)

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        "playlist_url,include_apple,status",
        f'"{playlist_url}",{str(include_apple).lower()},"pending"',
    ]
    output_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return output_path
