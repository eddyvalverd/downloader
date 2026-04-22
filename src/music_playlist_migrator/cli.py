"""CLI entrypoint for music playlist migrator."""

from __future__ import annotations

import argparse

from music_playlist_migrator.pipeline import InvalidPlaylistUrlError, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="music-playlist-migrator",
        description="Migra playlists y genera un reporte CSV.",
    )
    parser.add_argument(
        "--playlist-url",
        required=True,
        help="URL de la playlist de YouTube Music.",
    )
    parser.add_argument(
        "--output-csv",
        default="output/playlist_report.csv",
        help="Ruta del CSV de salida (default: output/playlist_report.csv).",
    )
    parser.add_argument(
        "--include-apple",
        action="store_true",
        help="Incluye procesamiento adicional para Apple Music.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        output_path = run_pipeline(
            playlist_url=args.playlist_url,
            output_csv=args.output_csv,
            include_apple=args.include_apple,
        )
    except InvalidPlaylistUrlError as exc:
        parser.error(str(exc))

    print(f"Reporte generado: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
