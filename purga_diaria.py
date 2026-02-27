#!/usr/bin/env python3
"""
purga_diaria.py
Purga diaria de la lista Live TV (playlist.m3u).
Verifica canales con ThreadPoolExecutor + requests (30 hilos, timeout 3s).
Autor: Hablando Claro VIP - Nube
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────
PLAYLIST_FILE   = Path("playlist.m3u")
TIMEOUT_SECS    = 3
MAX_WORKERS     = 30
HEADERS         = {
    "User-Agent": "Mozilla/5.0 (compatible; IPTV-PurgaDiaria/1.0)",
}

# ──────────────────────────────────────────────
# PARSEO M3U
# ──────────────────────────────────────────────
def parse_m3u(filepath: Path) -> tuple[str, list[tuple[str, str]]]:
    """
    Lee un archivo .m3u y devuelve (header, lista de (meta, url)).
    Preserva la línea #EXTM3U original como cabecera.
    """
    if not filepath.exists():
        print(f"[ERROR] Archivo no encontrado: {filepath}")
        sys.exit(1)

    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines   = content.splitlines()

    header  = "#EXTM3U"
    entries: list[tuple[str, str]] = []

    i = 0
    if lines and lines[0].startswith("#EXTM3U"):
        header = lines[0].strip()
        i = 1

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            meta = line
            j = i + 1
            # saltar líneas de comentario adicionales
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

    return header, entries


# ──────────────────────────────────────────────
# VERIFICACIÓN HTTP CON requests
# ──────────────────────────────────────────────
def check_channel(url: str) -> tuple[str, bool]:
    """
    Verifica si un canal responde con status 200.
    Primero intenta HEAD; si falla con 403/405 reintenta con GET.
    Devuelve (url, is_alive).
    """
    try:
        resp = requests.head(
            url,
            timeout=TIMEOUT_SECS,
            headers=HEADERS,
            allow_redirects=True,
            verify=False
        )
        if resp.status_code == 200:
            return (url, True)
        elif resp.status_code in (403, 405):
            # Reintentar con GET (stream=True para no descargar el cuerpo completo)
            resp2 = requests.get(
                url,
                timeout=TIMEOUT_SECS,
                headers=HEADERS,
                allow_redirects=True,
                verify=False,
                stream=True
            )
            resp2.close()
            return (url, resp2.status_code == 200)
        else:
            return (url, False)
    except requests.exceptions.Timeout:
        return (url, False)
    except requests.exceptions.RequestException:
        return (url, False)


def audit_channels(url_list: list[str]) -> set[str]:
    """
    Verifica todos los canales en paralelo con ThreadPoolExecutor.
    Devuelve el conjunto de URLs vivas.
    """
    alive: set[str] = set()
    total = len(url_list)
    done  = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_channel, url): url for url in url_list}

        for future in as_completed(futures):
            url, is_alive = future.result()
            done += 1
            if is_alive:
                alive.add(url)
            # Progreso cada 50 canales
            if done % 50 == 0 or done == total:
                print(f"  Progreso: {done}/{total} — Vivos: {len(alive)}", flush=True)

    return alive


# ──────────────────────────────────────────────
# ESCRITURA DE RESULTADOS
# ──────────────────────────────────────────────
def rebuild_playlist(header: str, entries: list[tuple[str, str]], alive_urls: set[str]) -> str:
    """Reconstruye playlist.m3u conservando solo los canales vivos."""
    lines = [header]
    for meta, url in entries:
        if url in alive_urls:
            lines.append(meta)
            lines.append(url)
    return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    # Suprimir advertencias SSL de requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("=" * 60)
    print(" PURGA DIARIA — Live TV (playlist.m3u)")
    print("=" * 60)

    inicio = time.time()

    # 1. Leer playlist.m3u
    print(f"\n[1/3] Leyendo {PLAYLIST_FILE}...")
    header, entries = parse_m3u(PLAYLIST_FILE)
    print(f"  Total canales: {len(entries)}")

    if not entries:
        print("[WARN] playlist.m3u vacío. Nada que purgar.")
        sys.exit(0)

    # 2. Verificar canales
    print(f"\n[2/3] Verificando {len(entries)} canales ({MAX_WORKERS} hilos, timeout {TIMEOUT_SECS}s)...")
    url_list = [url for _, url in entries]
    alive    = audit_channels(url_list)

    total_ok      = len(alive)
    total_offline = len(entries) - total_ok
    print(f"\n  ✔ Vivos:    {total_ok}")
    print(f"  ✘ Offline:  {total_offline}")

    # 3. Sobrescribir playlist.m3u con los canales vivos
    print(f"\n[3/3] Guardando playlist.m3u depurada...")
    new_content = rebuild_playlist(header, entries, alive)
    PLAYLIST_FILE.write_text(new_content, encoding="utf-8")
    print(f"  ✔ playlist.m3u sobrescrita con {total_ok} canales vivos.")

    elapsed = time.time() - inicio
    print("\n" + "=" * 60)
    print(" PURGA COMPLETADA")
    print(f"  Canales conservados: {total_ok}")
    print(f"  Canales eliminados:  {total_offline}")
    print(f"  Tiempo total:        {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
