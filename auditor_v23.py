import re
import os
import requests
import concurrent.futures
import time

# --- CONFIGURACIÓN ---
INPUT_FILE = "playlist.m3u"
OUTPUT_FILE = "playlist_active.m3u"
TIMEOUT_SEC = 2.5  # Si tarda más de 2.5 seg, se considera "LENTO/MUERTO"
MAX_WORKERS = 50   # 50 Verificaciones simultáneas

def parse_m3u(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    return re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)

def check_channel(entry):
    """
    Verifica si un canal está vivo y responde rápido.
    Retorna: (entry, True/False)
    """
    lines = entry.strip().split('\n')
    url = lines[1].strip() if len(lines) > 1 else ""
    
    if not url: return (entry, False)

    try:
        # Usamos stream=True para no descargar el video, solo conectar
        # Usamos GET porque algunos servidores bloquean HEAD
        with requests.get(url, timeout=TIMEOUT_SEC, stream=True, allow_redirects=True) as r:
            if r.status_code in [200, 206, 302]:
                return (entry, True)
    except:
        pass # Cualquier error (timeout, 404, conexión rechazada) es muerte
    
    return (entry, False)

def main():
    print("🚀 INICIANDO AUDITORÍA Y DEPURACIÓN (V23)...")
    print(f"⏱️  Criterio de eliminación: > {TIMEOUT_SEC} segundos de respuesta.")
    
    # 1. Cargar Canales
    entries = parse_m3u(INPUT_FILE)
    total = len(entries)
    print(f"📦 Analizando {total} canales...")

    active_channels = []
    dead_count = 0

    # 2. Ejecutar Auditoría Multihilo
    print("⚡ Verificando conexiones (Esto tomará unos minutos)...")
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Mapear cada canal a una tarea futura
        future_to_channel = {executor.submit(check_channel, item): item for item in entries}
        
        # Procesar a medida que terminan
        completed = 0
        for future in concurrent.futures.as_completed(future_to_channel):
            entry, is_alive = future.result()
            completed += 1
            
            if is_alive:
                active_channels.append(entry)
            else:
                dead_count += 1
            
            # Barra de progreso simple
            if completed % 100 == 0:
                print(f"   ... Procesados: {completed}/{total} | Vivos: {len(active_channels)} | Muertos: {dead_count}", end='\r')

    elapsed = time.time() - start_time
    print(f"\n🏁 Auditoría finalizada en {elapsed:.2f} segundos.")

    # 3. Guardar Resultados
    # Mantenemos el orden original (o lo que queda de él)
    # Si quieres re-ordenar alfabéticamente después, avísame.
    # Por ahora respetamos el orden que ya tenías (Dom -> TV -> Adultos).
    
    print(f"📊 RESULTADOS:")
    print(f"   ❌ Eliminados (Muertos/Lentos): {dead_count}")
    print(f"   ✅ Aprobados (Rápidos): {len(active_channels)}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in active_channels:
            f.write(item.strip() + "\n")

    print(f"💾 Lista limpia guardada en: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
