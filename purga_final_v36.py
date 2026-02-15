import re
import os

FILE_TV = "playlist.m3u"
FILE_VOD = "vod.m3u"
OUT_TV = "playlist_v36.m3u"
OUT_VOD = "vod_v36.m3u"

# LISTA NEGRA ESPECÍFICA (Basada en tus capturas de TiviMate)
OBJETIVOS = [
    "CAM SODA", "FAKEHUB", "VICTORIA VOXXX", "ISIAH MAXWELL", 
    "CÓMO CONECTAR SU SISTEMA DE CINE", "SAN JUAN BOSCO", 
    "VOXXX", "SODA", "FAKEHUB", "LOVELOCK"
]

def parse_m3u(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if not content.startswith("#EXTM3U"): content = "#EXTM3U\n" + content
    return re.findall(r'(#EXTINF:.*?\n.*?)(?=\n#EXTINF:|$)', content, re.DOTALL)

def main():
    print("🚀 INICIANDO PURGA FINAL V36 (EL FRANCOTIRADOR)...")
    
    items_tv = parse_m3u(FILE_TV)
    items_vod = parse_m3u(FILE_VOD)
    
    print(f"📦 TV Actual: {len(items_tv)}")
    
    clean_tv = []
    transferred_to_vod = []
    eliminated_count = 0

    for entry in items_tv:
        lines = entry.strip().split('\n')
        extinf = lines[0]
        url = lines[1] if len(lines) > 1 else ""
        name = extinf.split(',')[-1].strip().upper()
        
        # BUSCAR LOS 7 INFILTRADOS
        found = False
        for obj in OBJETIVOS:
            if obj in name:
                found = True
                eliminated_count += 1
                
                # Clasificar al mover
                new_group = "VOD: VARIOS"
                if "CÓMO CONECTAR" in name or "JUAN BOSCO" in name:
                    new_group = "PELICULAS: GENERAL"
                else:
                    new_group = "ZONA ADULTOS (+18) 🔞"

                # Modificar grupo
                if 'group-title="' in extinf:
                    extinf = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', extinf)
                else:
                    extinf = extinf.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{new_group}"')
                
                transferred_to_vod.append(f"{extinf}\n{url}")
                print(f"   🔫 Eliminado de TV: {name}")
                break
        
        if not found:
            clean_tv.append(entry)

    # UNIR Y GUARDAR
    final_vod = items_vod + transferred_to_vod

    with open(OUT_TV, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in clean_tv: f.write(item.strip() + "\n")

    with open(OUT_VOD, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for item in final_vod: f.write(item.strip() + "\n")

    print(f"✅ ¡PURGA FINALIZADA!")
    print(f"   🗑️ Elementos eliminados: {eliminated_count}")
    print(f"   📺 TV Limpia: {len(clean_tv)}")

if __name__ == "__main__":
    main()
