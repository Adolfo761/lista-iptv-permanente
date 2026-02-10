import re
import os

INPUT_FILE = "playlist.m3u"
OUTPUT_FILE = "playlist_v20.m3u"

# CONFIGURACIÓN DE NOMBRES
# 1. El #1 indiscutible
DOMINICANA_OFICIAL = "01. 🇩🇴 REPUBLICA DOMINICANA" 

# 2. Nombre CLARO que empieza por Z para ir al final naturalmente
ADULTOS_OFICIAL = "ZONA ADULTOS (+18) 🔞" 

def main():
    print("🚀 Iniciando V20 (Revertir y Renombrar)...")
    
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
        
        # LIMPIEZA DE PREFIJOS VIEJOS
        current_group = "SIN GRUPO"
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        if group_match: 
            raw_group = group_match.group(1).strip()
            # Quitamos basura vieja (1., 2., 3., TV:, ZZZ, ~, etc)
            clean_group = re.sub(r'^(0[0-9]\.|[1-3]\.|TV:|~|\.|ZZ|ZZZ|\|\||VOD:)\s*', '', raw_group).strip()
            # Quitamos emojis del inicio
            clean_group = re.sub(r'^(📺|🔞|🇩🇴|⚽)\s*', '', clean_group).strip()
            current_group = clean_group
        
        name = extinf.split(',')[-1].strip()
        
        # CLASIFICACIÓN
        new_group = current_group

        # 1. DOMINICANA
        if any(x in current_group.upper() for x in ["DOMINICANA", "RD", "DO", "REPUBLICA"]):
            new_group = DOMINICANA_OFICIAL
        
        # 2. ADULTOS (Los juntamos todos bajo el nuevo nombre claro)
        elif any(x in current_group.upper() for x in ["ADULT", "XXX", "🔞", "PORN", "ZONA", "PELICULAS Y SERIES"]) or "(+18)" in name:
            new_group = ADULTOS_OFICIAL
        
        # 3. RESTO (TV: ...)
        else:
            if "VARIOS" in current_group.upper():
                new_group = "TV: 📺 VARIOS"
            else:
                new_group = f"TV: {current_group}"

        # APLICAR
        if 'group-title="' in extinf:
            extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
        else:
            extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')

        channels.append({'group': new_group, 'name': name, 'full_text': f"{extinf}\n{url}"})

    # ORDENAMIENTO ALFABÉTICO NATURAL
    # 0... va antes que T...
    # T... va antes que Z...
    print("📊 Ordenando Alfabéticamente...")
    channels.sort(key=lambda x: (x['group'], x['name']))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for c in channels:
            f.write(c['full_text'] + "\n")

    print(f"✅ ¡Listo! Carpeta renombrada a: '{ADULTOS_OFICIAL}'")

if __name__ == "__main__":
    main()
