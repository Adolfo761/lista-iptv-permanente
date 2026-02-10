import re
import os

INPUT_FILE = "playlist.m3u"
OUTPUT_FILE = "playlist_v16.m3u"

# ESTRATEGIA DE PUNTUACIÓN (ANCLAS)
# El punto (.) obliga a ir al INICIO.
DOMINICANA_OFICIAL = ".TV: 🇩🇴 REPUBLICA DOMINICANA" 

# La tilde (~) obliga a ir al FINAL (código ASCII 126).
ADULTOS_OFICIAL = "~TV: 🔞 ZONA ADULTOS" 

# Varios se queda normal para estar en el medio
VARIOS_OFICIAL = "TV: 📺 VARIOS"

def main():
    print("🚀 Iniciando V16 (Estrategia de Puntos y Tildes)...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: No encuentro {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    raw_entries = re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)
    channels = []

    print(f"🔄 Re-etiquetando {len(raw_entries)} canales...")

    for entry in raw_entries:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        
        current_group = "SIN GRUPO"
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        if group_match: current_group = group_match.group(1).strip()
        name = extinf.split(',')[-1].strip()
        
        new_group = current_group

        # 1. Dominicana
        if any(x in current_group.upper() for x in ["DOMINICANA", "RD", "DO", "00", "REPUBLICA"]):
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

        if new_group != current_group:
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')

        channels.append({'group': new_group, 'name': name, 'full_text': f"{extinf}\n{url}"})

    # ORDENAMIENTO ESTÁNDAR A-Z
    # El punto (.) ganará a la T (TV) y la Tilde (~) perderá.
    print("📊 Ordenando por Puntuación ASCII...")
    channels.sort(key=lambda x: (x['group'], x['name']))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for c in channels:
            f.write(c['full_text'] + "\n")

    print(f"✅ ¡Listo!")

if __name__ == "__main__":
    main()
