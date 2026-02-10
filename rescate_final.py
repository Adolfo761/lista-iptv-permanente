import re
import os

# Usamos el archivo que acabamos de resucitar
INPUT_FILE = "playlist.m3u"
OUTPUT_FILE = "playlist_fixed.m3u"

# NOMBRES SIMPLES (TEXTO PLANO = CERO ERRORES)
DOMINICANA_OFICIAL = "00 DOMINICANA" 
ADULTOS_OFICIAL = "ZZ ZONA ADULTOS" 
VARIOS_OFICIAL = "TV VARIOS"

def main():
    print("🚑 Ejecutando RESCATE FINAL...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: No encuentro {INPUT_FILE}. Asegúrate de haber hecho el 'cp'.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Asegurar cabecera M3U
    if not content.startswith("#EXTM3U"):
        content = "#EXTM3U\n" + content

    raw_entries = re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)
    print(f"🔄 Procesando {len(raw_entries)} canales...")

    channels = []
    for entry in raw_entries:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        
        # Detectar Info
        current_group = "SIN GRUPO"
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        if group_match: current_group = group_match.group(1).strip()
        name = extinf.split(',')[-1].strip()
        
        # --- RENOMBRADO SEGURO ---
        new_group = current_group

        # 1. Dominicana
        if any(x in current_group.upper() for x in ["DOMINICANA", "RD", "DO", "DOM"]):
            new_group = DOMINICANA_OFICIAL
        
        # 2. Adultos
        is_adult = False
        if any(x in current_group.upper() for x in ["ZZ", "OJO", "ADULT", "XXX", "🔞", "PORN", "ZONA", "||"]): is_adult = True
        if "(+18)" in name.upper() or "+18" in name: is_adult = True
        
        if is_adult:
            new_group = ADULTOS_OFICIAL

        # 3. Varios
        if "VARIOS" in current_group.upper():
            new_group = VARIOS_OFICIAL

        # Aplicar cambios
        if new_group != current_group:
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')

        channels.append({'group': new_group, 'name': name, 'full_text': f"{extinf}\n{url}"})

    # Ordenar (00 va primero, ZZ va ultimo)
    channels.sort(key=lambda x: (x['group'], x['name']))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for c in channels:
            f.write(c['full_text'] + "\n")

    print(f"✅ ¡LISTA REPARADA! Guardada en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
