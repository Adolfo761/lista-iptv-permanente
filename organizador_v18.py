import re
import os

INPUT_FILE = "playlist.m3u"
OUTPUT_FILE = "playlist_v18.m3u"

# CONFIGURACIÓN DE NOMBRES
# 1. Dominicana sigue siendo la REINA (#1)
DOMINICANA_OFICIAL = "1. 🇩🇴 REPUBLICA DOMINICANA" 

# 2. Adultos se convierte en "PELICULAS Y SERIES" para disimular
#    (Usamos "VOD:" opcional por si la app lo detecta y lo mueve de pestaña)
ADULTOS_OFICIAL = "PELICULAS Y SERIES" 

# 3. El resto se queda con su nombre natural (quitamos los números 2. y 3. anteriores)

def main():
    print("🚀 Iniciando V18 (Mover Adultos a Películas)...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: No encuentro {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    raw_entries = re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)
    channels = []

    print(f"🔄 Procesando {len(raw_entries)} canales...")

    for entry in raw_entries:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        
        # 1. LIMPIEZA DE PREFIJOS ANTERIORES
        # Recuperamos el nombre original quitando 1., 2., 3., TV:, etc.
        current_group = "SIN GRUPO"
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        if group_match: 
            raw_group = group_match.group(1).strip()
            # Quitamos basura de versiones anteriores
            clean_group = re.sub(r'^(0[0-9]\.|[1-3]\.|TV:|~|\.|ZZ|\|\||VOD:)\s*', '', raw_group).strip()
            # Quitamos emojis viejos al inicio si los hubiera
            clean_group = re.sub(r'^(📺|🔞|🇩🇴|⚽)\s*', '', clean_group).strip()
            current_group = clean_group
        
        name = extinf.split(',')[-1].strip()
        
        # 2. CLASIFICACIÓN
        new_group = current_group

        # A) DOMINICANA (Prioridad Top)
        if any(x in current_group.upper() for x in ["DOMINICANA", "RD", "DO", "REPUBLICA"]):
            new_group = DOMINICANA_OFICIAL
        
        # B) ADULTOS -> SE MUEVEN A "PELICULAS Y SERIES"
        elif any(x in current_group.upper() for x in ["ADULT", "XXX", "🔞", "PORN", "ZONA ADULTOS"]) or "(+18)" in name:
            new_group = ADULTOS_OFICIAL
        
        # C) RESTO (Argentina, Deportes, Varios...)
        else:
            # Los dejamos limpios. Opcional: Agregar "TV:" si te gusta, 
            # pero mejor dejarlo natural para que se ordenen alfabéticamente.
            # Si es Varios, le ponemos emoji para que se vea bien
            if "VARIOS" in current_group.upper():
                new_group = "📺 VARIOS"
            else:
                new_group = f"TV: {current_group}"

        # 3. APLICAR
        if 'group-title="' in extinf:
            extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
        else:
            extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')

        channels.append({'group': new_group, 'name': name, 'full_text': f"{extinf}\n{url}"})

    # ORDENAMIENTO:
    # 1. 🇩🇴 REPUBLICA... (El '1.' gana a todo)
    # Luego alfabéticamente: A (Argentina) ... P (Peliculas) ... V (Varios)
    print("📊 Ordenando Alfabéticamente...")
    channels.sort(key=lambda x: (x['group'], x['name']))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for c in channels:
            f.write(c['full_text'] + "\n")

    print(f"✅ ¡Listo! Adultos ocultos en: '{ADULTOS_OFICIAL}'")

if __name__ == "__main__":
    main()
