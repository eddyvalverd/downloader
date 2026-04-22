# Downloader de playlists (metadatos)

Herramienta para extraer y analizar **metadatos** de playlists musicales desde YouTube Music, con enriquecimiento opcional desde Spotify y Apple Music.

## Requisitos

- Python **3.11+**
- `pip`

## Instalación

```bash
pip install -r requirements.txt
```

## Variables de entorno

Configura las credenciales antes de ejecutar el script.

### Spotify

```bash
export SPOTIFY_CLIENT_ID="tu_client_id"
export SPOTIFY_CLIENT_SECRET="tu_client_secret"
```

### Apple Music

```bash
export APPLE_MUSIC_DEVELOPER_TOKEN="tu_developer_token"
export APPLE_MUSIC_USER_TOKEN="tu_user_token"
export APPLE_MUSIC_STOREFRONT="us"
```

> En Windows (PowerShell): usa `$env:NOMBRE_VARIABLE="valor"`.

## Ejemplo de uso (playlist real de YouTube Music)

```bash
python main.py \
  --playlist-url "https://music.youtube.com/playlist?list=OLAK5uy_mKJgKT-Y4Ea3K2tUZ6KEOl0iyP_omgotw" \
  --output-csv "salida/tracks.csv" \
  --analysis-json "salida/analysis.json"
```

## Errores comunes

### 1) URL inválida

**Síntoma:** el programa devuelve error de validación o no encuentra la playlist.

**Qué revisar:**
- Que la URL sea de YouTube Music y contenga `playlist?list=`.
- Que no esté truncada por copiar/pegar.

### 2) Playlist privada

**Síntoma:** el programa no puede leer pistas o devuelve acceso denegado.

**Qué revisar:**
- Que la playlist sea pública o no listada.
- Que estés autenticado correctamente si el flujo lo requiere.

### 3) Credenciales ausentes

**Síntoma:** errores de autenticación contra Spotify/Apple Music.

**Qué revisar:**
- Variables de entorno cargadas en la misma sesión de terminal.
- Tokens vigentes (sin expirar) y con permisos correctos.

## Ejemplo de salida CSV

```csv
position,title,artist,album,isrc,source_url
1,Take My Breath,The Weeknd,Dawn FM,USUG12102914,https://music.youtube.com/watch?v=...
2,Bad Romance,Lady Gaga,The Fame Monster,USUM70918596,https://music.youtube.com/watch?v=...
3,Don't Let Me Down,The Chainsmokers feat. Daya,Collage,USQX91600801,https://music.youtube.com/watch?v=...
```

## Ejemplo resumido de análisis JSON

```json
{
  "playlist": {
    "url": "https://music.youtube.com/playlist?list=OLAK5uy_mKJgKT-Y4Ea3K2tUZ6KEOl0iyP_omgotw",
    "tracks_total": 24
  },
  "quality": {
    "with_isrc": 22,
    "without_isrc": 2,
    "coverage_pct": 91.67
  },
  "top_artists": [
    { "name": "The Weeknd", "tracks": 4 },
    { "name": "Lady Gaga", "tracks": 2 },
    { "name": "The Chainsmokers", "tracks": 2 }
  ]
}
```

## Nota de cumplimiento legal

Este proyecto se limita a procesar **metadatos y enlaces oficiales**. No descarga, almacena ni redistribuye audio/video protegido por derechos de autor.
