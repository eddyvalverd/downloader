"""Utilidades para exportar pistas a CSV."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Mapping



def export_tracks_csv(rows: Iterable[Mapping[str, Any]], output_path: str | Path) -> Path:
    """Exporta una colección de pistas a un archivo CSV.

    Args:
        rows: Iterable de diccionarios con los datos de cada pista.
        output_path: Ruta del archivo CSV de salida.

    Returns:
        La ruta final escrita en disco.
    """

    materialized_rows = list(rows)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if not materialized_rows:
        destination.write_text("", encoding="utf-8")
        return destination

    fieldnames: list[str] = []
    seen_fields: set[str] = set()
    for row in materialized_rows:
        for key in row.keys():
            if key not in seen_fields:
                seen_fields.add(key)
                fieldnames.append(key)

    with destination.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized_rows)

    return destination
