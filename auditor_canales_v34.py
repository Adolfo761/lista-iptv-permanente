import re
import os
import requests
import concurrent.futures
import time

# --- CONFIGURACIÓN ---
INPUT_FILE = "playlist.m3u"
OUTPUT_FILE = "playlist_v34.m3u"
TIMEOUT_SEC = 2.0  # TIEMPO MÁXIMO DE ESPERA (Si tarda más, se borra)
MAX_WORKERS = 50   # Conexiones simultáneas

# Cabeceras para simular ser un reproductor real (evita bloqueos)
HEADERS = {
    'User-Agent': 'IPTVSmartersPro/1.0',
    'Accept': '*/*'
}

def parse_m3u(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    return re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)

def check_channel(entry):
    lines = entry.strip().split('\n')
    url = lines[1].strip() if len(lines) > 1 else ""
    
    if not url: return (entry, False)

    try:
        # Usamos stream=True para no descargar el video, solo conectar
        with requests.get(url, headers=HEADERS, timeout=TIMEOUT_SEC, stream=True, allow_redirects=True, verify=False) as r:
            if r.status_code in [200, 206, 302, 301]:
                return (entry, True)
    except:
        pass # Timeout, Error de conexión, DNS fallido -> ELIMINAR
    
    return (entry, False)

def main():
    print("🚀 INICIANDO AUDITORÍA DE VELOCIDAD (V34)...")
    print(f"⏱️  Umbral de eliminación: > {TIMEOUT_SEC} segundos.")
    
    # 1. Cargar Canales
    entries = parse_m3u(INPUT_FILE)
    total = len(entries)
    print(f"📦 Total de Canales a auditar: {total}")

    active_channels = []
    dead_count = 0
    completed = 0

    print("⚡ Verificando señal en vivo...")
    start_time = time.time()
    
    # Desactivar advertencias de SSL inseguro (común en IPTV)
    requests.packages.urllib3.disable_warnings()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_channel = {executor.submit(check_channel, item): item for item in entries}
        
        for future in concurrent.futures.as_completed(future_to_channel):
            entry, is_alive = future.result()
            completed += 1
            
            if is_alive:
                active_channels.append(entry)
            else:
                dead_count += 1
            
            # Barra de progreso
            if completed % 100 == 0:
                print(f"   Procesados: {completed}/{total} | ✅ Rápidos: {len(active_channels)} | ❌ Lentos/Muertos: {dead_count}", end='\r')

    elapsed = time.time() - start_time
    print(f"\n🏁 Auditoría finalizada en {elapsed:.2f} segundos.")

    # 3. Guardar Resultados
    print(f"📊 GUARDANDO LISTA DEPURADA...")
    
    # Mantenemos el orden original (asumimos que ya estaba ordenado)
    # Si quieres reordenar alfabéticamente, avísame.
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in active_channels:
            f.write(item.strip() + "\n")

    print(f"💾 Lista Premium guardada en: {OUTPUT_FILE}")
    print(f"   🗑️ Se eliminaron {dead_count} canales inestables.")

if __name__ == "__main__":
    main()
