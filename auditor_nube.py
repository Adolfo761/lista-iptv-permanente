#!/usr/bin/env python3
"""
auditor_nube.py
Auditoría asíncrona de listas IPTV en la nube.
Verifica el estado HTTP de cada enlace y separa Live (m3u8) de VOD (mp4/mkv/etc).
Autor: Hablando Claro VIP - Nube
"""

import asyncio
import re
import sys
from pathlib import Path

import aiohttp

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────
TIMEOUT_SECS     = 5
CONNECTOR_LIMIT  = 500
VOD_FILE         = Path("vod.m3u")
PLAYLIST_FILE    = Path("playlist.m3u")

LIVE_EXTENSIONS  = {".m3u8"}
VOD_EXTENSIONS   = {".mp4", ".mkv", ".avi", ".ts", ".mov", ".wmv", ".flv", ".webm"}

# ──────────────────────────────────────────────
# PARSEO M3U
# ──────────────────────────────────────────────
def parse_m3u(filepath: Path) -> list[tuple[str, str]]:
    """
    Lee un archivo .m3u y devuelve lista de (metadata_line, url).
    Preserva las líneas #EXTINF junto con su URL.
    """
    entries: list[tuple[str, str]] = []
    if not filepath.exists():
        print(f"[WARN] Archivo no encontrado: {filepath}")
        return entries

    lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            meta = line
            # La siguiente línea no comentada es la URL
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("#"):
                j += 1
            if j < len(lines):
                url = lines[j].strip()
                if url:
                    entries.append((meta, url))
                i = j + 1
            else:
                i += 1
        else:
            i += 1
    return entries


def get_header(filepath: Path) -> str:
    """Extrae la cabecera #EXTM3U del archivo si existe."""
    if not filepath.exists():
        return "#EXTM3U"
    first_line = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
    if first_line and first_line[0].startswith("#EXTM3U"):
        return first_line[0].strip()
    return "#EXTM3U"


def classify_url(url: str) -> str:
    """Clasifica una URL como 'live', 'vod' o 'unknown'."""
    url_lower = url.lower().split("?")[0]  # ignorar query params
    for ext in LIVE_EXTENSIONS:
        if url_lower.endswith(ext):
            return "live"
    for ext in VOD_EXTENSIONS:
        if url_lower.endswith(ext):
            return "vod"
    return "live"  # si no tiene extensión conocida, tratar como live


# ──────────────────────────────────────────────
# VERIFICACIÓN ASÍNCRONA HTTP
# ──────────────────────────────────────────────
async def check_url(session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore) -> tuple[str, bool]:
    """
    Verifica si una URL responde con status 200.
    Primero intenta HEAD; si recibe 403/405 reintenta con GET.
    Devuelve (url, is_alive).
    """
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECS)
    async with semaphore:
        try:
            async with session.head(url, timeout=timeout, allow_redirects=True, ssl=False) as resp:
                if resp.status == 200:
                    return (url, True)
                elif resp.status in (403, 405):
                    # Reintentar con GET
                    async with session.get(url, timeout=timeout, allow_redirects=True, ssl=False) as resp2:
                        return (url, resp2.status == 200)
                else:
                    return (url, False)
        except (aiohttp.ClientError, asyncio.TimeoutError, Exception):
            return (url, False)


async def audit_urls(url_list: list[str]) -> set[str]:
    """
    Audita una lista de URLs de forma asíncrona.
    Devuelve el conjunto de URLs vivas (status 200).
    """
    alive: set[str] = set()
    connector = aiohttp.TCPConnector(limit=CONNECTOR_LIMIT, ssl=False)
    semaphore  = asyncio.Semaphore(CONNECTOR_LIMIT)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; IPTV-Auditor/1.0)",
    }

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [check_url(session, url, semaphore) for url in url_list]

        total = len(tasks)
        done  = 0
        for coro in asyncio.as_completed(tasks):
            url, is_alive = await coro
            done += 1
            if is_alive:
                alive.add(url)
            # Progreso cada 100 URLs
            if done % 100 == 0 or done == total:
                print(f"  Progreso: {done}/{total} — Vivos: {len(alive)}", flush=True)

    return alive


# ──────────────────────────────────────────────
# ESCRITURA DE RESULTADOS
# ──────────────────────────────────────────────
def rebuild_m3u(header: str, entries: list[tuple[str, str]], alive_urls: set[str]) -> str:
    """Reconstruye el contenido .m3u filtrando solo las URLs vivas."""
    lines = [header]
    for meta, url in entries:
        if url in alive_urls:
            lines.append(meta)
            lines.append(url)
    return "\n".join(lines) + "\n"


def append_live_to_playlist(playlist_path: Path, live_entries: list[tuple[str, str]], alive_live: set[str]):
    """
    Agrega al final de playlist.m3u los canales live funcionales,
    evitando duplicados si la URL ya existe en el archivo.
    """
    if not live_entries:
        print("[INFO] No hay canales Live nuevos para agregar a playlist.m3u")
        return

    # Leer URLs existentes en playlist.m3u
    existing_urls: set[str] = set()
    if playlist_path.exists():
        for line in playlist_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                existing_urls.add(line)

    new_entries = [(m, u) for m, u in live_entries if u in alive_live and u not in existing_urls]

    if not new_entries:
        print("[INFO] Todos los canales Live ya existen en playlist.m3u — sin cambios.")
        return

    with playlist_path.open("a", encoding="utf-8") as f:
        f.write("\n")
        for meta, url in new_entries:
            f.write(meta + "\n")
            f.write(url + "\n")

    print(f"[OK] {len(new_entries)} canales Live añadidos a playlist.m3u")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
async def main():
    print("=" * 60)
    print(" AUDITOR NUBE — Verificación asíncrona de IPTV")
    print("=" * 60)

    # 1. Parsear vod.m3u
    print(f"\n[1/4] Leyendo {VOD_FILE}...")
    vod_entries = parse_m3u(VOD_FILE)
    print(f"  Total entradas en vod.m3u: {len(vod_entries)}")

    if not vod_entries:
        print("[WARN] vod.m3u vacío o no encontrado. Abortando.")
        sys.exit(0)

    # 2. Separar live (.m3u8) de VOD reales
    live_entries: list[tuple[str, str]] = []
    vod_entries_real: list[tuple[str, str]] = []

    for meta, url in vod_entries:
        kind = classify_url(url)
        if kind == "live":
            live_entries.append((meta, url))
        else:
            vod_entries_real.append((meta, url))

    print(f"  → Live (.m3u8 / sin extensión): {len(live_entries)}")
    print(f"  → VOD reales (.mp4/.mkv/etc):   {len(vod_entries_real)}")

    # 3. Auditar VOD
    print(f"\n[2/4] Auditando {len(vod_entries_real)} enlaces VOD...")
    vod_urls   = [u for _, u in vod_entries_real]
    alive_vod  = await audit_urls(vod_urls) if vod_urls else set()
    print(f"  ✔ VOD vivos:   {len(alive_vod)}/{len(vod_urls)}")

    # 4. Auditar Live
    print(f"\n[3/4] Auditando {len(live_entries)} enlaces Live...")
    live_urls   = [u for _, u in live_entries]
    alive_live  = await audit_urls(live_urls) if live_urls else set()
    print(f"  ✔ Live vivos:  {len(alive_live)}/{len(live_urls)}")

    # 5. Guardar resultados
    print(f"\n[4/4] Guardando resultados...")

    # Sobrescribir vod.m3u con solo los VOD reales que funcionan
    vod_header  = get_header(VOD_FILE)
    new_vod_content = rebuild_m3u(vod_header, vod_entries_real, alive_vod)
    VOD_FILE.write_text(new_vod_content, encoding="utf-8")
    print(f"  ✔ vod.m3u actualizado ({len(alive_vod)} entradas vivas)")

    # Añadir live funcionales al final de playlist.m3u (sin duplicados)
    append_live_to_playlist(PLAYLIST_FILE, live_entries, alive_live)

    print("\n" + "=" * 60)
    print(" AUDITORÍA COMPLETADA")
    print(f"  VOD funcionales:  {len(alive_vod)}")
    print(f"  Live funcionales: {len(alive_live)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
