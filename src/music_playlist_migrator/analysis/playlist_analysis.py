"""Funciones de análisis para playlists migradas."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from music_playlist_migrator.reporting.csv_exporter import export_tracks_csv


TrackRow = Mapping[str, Any]


def _split_genres(genres_value: Any) -> list[str]:
    if genres_value is None:
        return []
    if isinstance(genres_value, str):
        return [genre.strip() for genre in genres_value.split(",") if genre.strip()]
    if isinstance(genres_value, list):
        return [str(genre).strip() for genre in genres_value if str(genre).strip()]
    return []


def _extract_energy(audio_features: Any) -> float | None:
    if not isinstance(audio_features, Mapping):
        return None
    energy = audio_features.get("energy")
    if energy is None:
        return None
    try:
        return float(energy)
    except (TypeError, ValueError):
        return None


def _extract_bpm(audio_features: Any) -> float | None:
    if not isinstance(audio_features, Mapping):
        return None
    tempo = audio_features.get("tempo")
    if tempo is None:
        return None
    try:
        return float(tempo)
    except (TypeError, ValueError):
        return None


def _energy_level(energy: float | None) -> str | None:
    if energy is None:
        return None
    if energy < 0.40:
        return "low"
    if energy <= 0.70:
        return "mid"
    return "high"


def _dominant_bpm_range(bpm_values: list[float]) -> str | None:
    if not bpm_values:
        return None

    # Agrupación de BPM en bins de 10 para encontrar el rango predominante.
    bins = Counter(int(bpm // 10) * 10 for bpm in bpm_values)
    top_bin, _ = bins.most_common(1)[0]
    return f"{top_bin}-{top_bin + 9}"


def analyze_playlist(
    rows: Iterable[TrackRow],
    *,
    csv_output_path: str | Path,
    json_output_path: str | Path = "output/analysis_summary.json",
    include_energy_classification: bool = True,
) -> dict[str, Any]:
    """Genera análisis de una playlist y persiste CSV + JSON de resumen.

    Se espera que cada fila incluya, cuando exista, metadata de Spotify con una
    estructura similar a:
    - artist / artists
    - spotify_metadata.genres
    - spotify_match (bool)
    - audio_features.{tempo, energy}
    """

    materialized_rows = [dict(row) for row in rows]

    # Exportar CSV solicitado.
    export_tracks_csv(materialized_rows, csv_output_path)

    artist_counter: Counter[str] = Counter()
    genre_counter: Counter[str] = Counter()
    energy_counter: Counter[str] = Counter()
    bpm_values: list[float] = []

    for row in materialized_rows:
        artists_raw = row.get("artists") or row.get("artist")
        if isinstance(artists_raw, str):
            artists = [a.strip() for a in artists_raw.split(",") if a.strip()]
        elif isinstance(artists_raw, list):
            artists = [str(a).strip() for a in artists_raw if str(a).strip()]
        else:
            artists = []
        artist_counter.update(artists)

        spotify_metadata = row.get("spotify_metadata")
        if isinstance(spotify_metadata, Mapping):
            genre_counter.update(_split_genres(spotify_metadata.get("genres")))

        spotify_match = bool(row.get("spotify_match"))
        bpm = _extract_bpm(row.get("audio_features")) if spotify_match else None
        row["estimated_bpm"] = bpm
        bpm_values.extend([bpm] if bpm is not None else [])

        if include_energy_classification:
            energy = _extract_energy(row.get("audio_features")) if spotify_match else None
            level = _energy_level(energy)
            row["energy_level"] = level
            if level is not None:
                energy_counter[level] += 1

    summary: dict[str, Any] = {
        "track_count": len(materialized_rows),
        "frequent_artists": dict(artist_counter.most_common(15)),
        "dominant_genres": dict(genre_counter.most_common(15)),
        "estimated_bpm": {
            "values": [round(bpm, 2) for bpm in bpm_values],
            "average": round(sum(bpm_values) / len(bpm_values), 2) if bpm_values else None,
        },
        "patrones_de_gusto": {
            "top_artistas": [
                {"artist": artist, "count": count}
                for artist, count in artist_counter.most_common(5)
            ],
            "rango_bpm_predominante": _dominant_bpm_range(bpm_values),
            "distribucion_energia": dict(energy_counter) if include_energy_classification else None,
        },
    }

    json_path = Path(json_output_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # Re-exportar CSV con columnas derivadas (estimated_bpm / energy_level).
    export_tracks_csv(materialized_rows, csv_output_path)

    return summary
