import re
import os

FILE_TV = "playlist.m3u"
FILE_VOD = "vod.m3u"
OUT_TV = "playlist_v22.m3u"
OUT_VOD = "vod_v22.m3u"

# NOMBRES DE GRUPO
GRP_PLUTO = "TV: 🪐 PLUTO TV"
GRP_CINE = "TV: 🎬 CINE PREMIUM"

def parse_m3u(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    return re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)

def main():
    print("🚀 Iniciando RESCATE QUIRÚRGICO V22...")
    tv_items = parse_m3u(FILE_TV)
    vod_items = parse_m3u(FILE_VOD)
    
    rescued_count = 0
    new_vod_list = []

    # Patrones prohibidos (Indican que es pelicula o serie, NO canal)
    # Buscamos (19xx) o (20xx) y S01, E01, etc.
    patron_vod = re.compile(r'\(\d{4}\)|S\d+|E\d+|CAPITULO|TEMPORADA', re.IGNORECASE)

    print("🕵️‍♂️ Analizando VOD con filtro estricto...")

    for entry in vod_items:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        name = extinf.split(',')[-1].strip().upper()
        
        # FILTROS
        es_vod_puro = patron_vod.search(name) # Si tiene año o episodio -> ES VOD
        
        # DETECCIONES POSITIVAS (Solo si NO es VOD puro)
        es_pluto = "PLUTO" in name and not es_vod_puro
        # Los canales de cine buenos en tu lista empiezan con "CINE -" o "24/7"
        es_cine_tv = ("CINE -" in name or "24/7" in name) and not es_vod_puro

        # DECISIÓN
        if es_pluto:
            # Es un canal Pluto en vivo
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{GRP_PLUTO}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{GRP_PLUTO}"')
            tv_items.append(f"{extinf}\n{url}")
            rescued_count += 1
            # print(f"   ✅ Pluto rescatado: {name}")

        elif es_cine_tv:
            # Es un canal de Cine (HBO, TNT, etc)
            if 'group-title="' in extinf:
                extinf = re.sub(r'group-title="[^"]*"', f'group-title="{GRP_CINE}"', extinf)
            else:
                extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{GRP_CINE}"')
            tv_items.append(f"{extinf}\n{url}")
            rescued_count += 1
            print(f"   ✅ Canal Cine rescatado: {name}")

        else:
            # Se queda en VOD (Películas, Series, Adultos, Star Wars, etc.)
            new_vod_list.append(entry)

    # GUARDAR
    tv_items.sort(key=lambda x: x.split(',')[0]) 

    with open(OUT_TV, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in tv_items: f.write(item.strip() + "\n")

    with open(OUT_VOD, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in new_vod_list: f.write(item.strip() + "\n")

    print(f"🏆 FIN. Se rescataron {rescued_count} canales REALES.")
    print("   (Star Wars, Películas y Series se quedaron en su lugar)")

if __name__ == "__main__":
    main()
