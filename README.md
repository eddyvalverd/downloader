# music-playlist-migrator

Estructura mínima para iniciar un migrador de playlists.

## Uso

```bash
python -m music_playlist_migrator.cli --playlist-url "<url>"
```

### Opciones

- `--playlist-url` (requerido): URL de la playlist de YouTube Music.
- `--output-csv` (opcional): ruta de salida del CSV. Default: `output/playlist_report.csv`.
- `--include-apple` (flag opcional): activa procesamiento para Apple Music.

## Validación de URL

La CLI valida que la URL:

- use esquema `http` o `https`,
- pertenezca al dominio `music.youtube.com`,
- apunte a la ruta `/playlist`.

Si no cumple, devuelve un error legible.
