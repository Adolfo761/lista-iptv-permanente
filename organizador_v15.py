import re
import os

# Usamos playlist.m3u (que ya sabemos que existe y funciona)
INPUT_FILE = "playlist.m3u"
OUTPUT_FILE = "playlist_v15.m3u"

# NOMBRES ESTRATÉGICOS
# 1. Dominicana: Usamos el mismo formato que Deportes para que se vea bien.
#    El truco: Le ponemos un espacio invisible (u200B) al principio para que suba al #1.
DOMINICANA_OFICIAL = "\u200BTV: 🇩🇴 REPUBLICA DOMINICANA" 

# 2. Adultos: Usamos el formato TV: pero con ZZZ para que baje.
#    Visualmente dirá "TV: ZONA ADULTOS", pero internamente será ZZZ.
ADULTOS_OFICIAL = "TV: ZZZ 🔞 ZONA ADULTOS" 

# 3. Varios
VARIOS_OFICIAL = "TV: 📺 VARIOS"

def main():
    print("🚀 Iniciando V15 (Estética + Orden)...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: No encuentro {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Asegurar cabecera
    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content

    raw_entries = re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)
    channels = []

    print(f"🔄 Procesando {len(raw_entries)} canales...")

    for entry in raw_entries:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        
        # Info
        current_group = "SIN GRUPO"
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        if group_match: current_group = group_match.group(1).strip()
        name = extinf.split(',')[-1].strip()
        
        # --- RENOMBRADO ---
        new_group = current_group

        # 1. Dominicana (Cualquier variación)
        if any(x in current_group.upper() for x in ["DOMINICANA", "RD", "DO", "00 DOMINICANA"]):
            new_group = DOMINICANA_OFICIAL
        
        # 2. Adultos (Caza total)
        is_adult = False
        if any(x in current_group.upper() for x in ["ZZ", "OJO", "ADULT", "XXX", "🔞", "PORN", "ZONA", "||"]): is_adult = True
        if "(+18)" in name.upper() or "+18" in name: is_adult = True
        
        if is_adult:
            new_group = ADULTOS_OFICIAL

        # 3. Varios
        if "VARIOS" in current_group.upper():
            new_group = VARIOS_OFICIAL

        # Aplicar
        if new_group != current_group:
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')

        channels.append({'group': new_group, 'name': name, 'full_text': f"{extinf}\n{url}"})

    # --- ORDENAMIENTO ---
    # Ordenamos por el texto del grupo.
    # El espacio invisible \u200B hará que Dominicana sea "menor" que la letra A de Argentina -> Se va arriba.
    # La ZZZ hará que Adultos sea "mayor" que la V de Varios -> Se va abajo.
    print("📊 Ordenando lista...")
    channels.sort(key=lambda x: (x['group'], x['name']))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for c in channels:
            f.write(c['full_text'] + "\n")

    print(f"✅ ¡Listo! Guardado en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
